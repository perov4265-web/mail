"""Write a copy of the plan PDF with the road-sign layer (plates, leaders, post marks, code labels) removed."""
import sys, math, json, collections
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
SRC, DST = sys.argv[1], sys.argv[2]
cl=json.load(open('../pdf/classes.json')); raw=json.load(open('../pdf/signs_posts.json'))
PH=1191.0
def bbox(p): xs=[a for a,b in p]; ys=[b for a,b in p]; return (min(xs),min(ys),max(xs),max(ys))
def dist_box(pt,b):
    dx=max(b[0]-pt[0],0,pt[0]-b[2]); dy=max(b[1]-pt[1],0,pt[1]-b[3]); return math.hypot(dx,dy)
def dist_seg(p,a,b):
    ax,ay=a; bx,by=b; px,py=p; L2=(bx-ax)**2+(by-ay)**2
    t=0 if L2==0 else max(0,min(1,((px-ax)*(bx-ax)+(py-ay)*(by-ay))/L2)); return math.hypot(px-(ax+t*(bx-ax)), py-(ay+t*(by-ay)))
clusters=[c['bbox'] for c in raw if c['bbox'][1]>105]
segs=[]
for o in cl['black_thick']:
    p=o['pts']
    if len(p)==2 and 3<math.dist(p[0],p[1])<80: segs.append((tuple(p[0]),tuple(p[1])))
    elif len(p)<=4 and not o['fill']:
        for i in range(len(p)-1):
            if 3<math.dist(p[i],p[i+1])<80: segs.append((tuple(p[i]),tuple(p[i+1])))
leaders=[]
for b in clusters:
    best=None
    for a,e in segs:
        da,de=dist_box(a,b),dist_box(e,b); near,far,dn=(a,e,da) if da<de else (e,a,de)
        if dn<=7.0 and (best is None or dn<best[0]): best=(dn,far,near)
    if best: leaders.append((best[2],best[1]))
print('clusters',len(clusters),'leaders',len(leaders))
def in_plate(pts): return any(all(dist_box(p,b)<=1.3 for p in pts) for b in clusters)
def in_leader(pts):
    for near,far in leaders:
        if all(dist_seg(p,near,far)<=1.6 for p in pts): return True
        if all(math.dist(p,near)<=7.0 for p in pts): return True   # post mark + hatch
        if all(math.dist(p,far)<=2.2 for p in pts): return True    # install dot
    return False
# ---- walk the content stream ----
r=PdfReader(SRC); w=PdfWriter(clone_from=r); page=w.pages[0]; cs=ContentStream(page.get_contents(), w)
ops=cs.operations
PAINT={b'b',b'B',b'f',b'F',b'f*',b'S',b's',b'b*',b'B*'}
FILLOPS={b'f',b'F',b'f*',b'b',b'B',b'b*',b'B*'}
def walk(decide):
    ctm=[1,0,0,1,0,0]; stack=[]; path=[]; out=[]; removed=0; cand=[]; lw=[1.0]
    def T(x,y): a,b,c,d,e,f=ctm; return (a*x+c*y+e, PH-(b*x+d*y+f))
    for idx,(operands,op) in enumerate(ops):
        if op==b'q': stack.append((ctm[:],lw[0]))
        elif op==b'Q': ctm,lw[0]=stack.pop() if stack else ([1,0,0,1,0,0],1.0)
        elif op==b'w': lw[0]=float(operands[0])
        elif op==b'cm':
            m=[float(v) for v in operands]; a,b,c,d,e,f=m; A,B,C,D,E,F=ctm
            ctm=[a*A+b*C, a*B+b*D, c*A+d*C, c*B+d*D, e*A+f*C+E, e*B+f*D+F]
        elif op in (b'm',b'l'): path.append(T(float(operands[0]),float(operands[1])))
        elif op==b'c':
            v=[float(x) for x in operands]; path += [T(v[0],v[1]),T(v[2],v[3]),T(v[4],v[5])]
        elif op==b're':
            x,y,w,h=[float(v) for v in operands]; path += [T(x,y),T(x+w,y),T(x+w,y+h),T(x,y+h)]
        elif op in PAINT or op==b'n':
            if path and op in PAINT and decide(path, idx, op, lw[0]*abs(ctm[0])): removed+=1; ops[idx]=(operands,b'n')
            path=[]
    return removed
# pass 1: code-label glyph runs (small filled paths near a plate)
glyphs=[]
def collect(path, idx, op, lwe):
    if op not in FILLOPS and lwe>0.9: return False
    b=bbox(path); w=b[2]-b[0]; h=b[3]-b[1]
    if (w<1.2 and h>2.5) or (h<1.2 and w>2.5): return False   # thin bars (post marks)
    if w<7 and h<7 and any(dist_box(((b[0]+b[2])/2,(b[1]+b[3])/2),c)<26 for c in clusters) and not in_plate(path) and not in_leader(path):
        glyphs.append((idx,((b[0]+b[2])/2,(b[1]+b[3])/2)))
    return False
walk(collect)
# group glyphs into runs; sign codes are short runs (<= 7 glyph paths incl. dots), long runs are words like "Пожарный проезд"
par=list(range(len(glyphs)))
def f(i):
    while par[i]!=i: par[i]=par[par[i]]; i=par[i]
    return i
for i in range(len(glyphs)):
    for j in range(i+1,len(glyphs)):
        if math.dist(glyphs[i][1],glyphs[j][1])<2.6: par[f(i)]=f(j)
runs=collections.defaultdict(list)
for i,(idx,c) in enumerate(glyphs): runs[f(i)].append(i)
code_idx=set()
for run in runs.values():
    xs=[glyphs[i][1][0] for i in run]; ys=[glyphs[i][1][1] for i in run]
    ext=(max(xs)-min(xs), max(ys)-min(ys))
    if len(run)>=3 and max(ext)<=22 and min(ext)<=7.5:   # short code label like "5.19.2" (several strokes); single fence squares, long words and wide labels stay
        code_idx.update(glyphs[i][0] for i in run)
print('glyph paths',len(glyphs),'runs',len(runs),'removed as codes',len(code_idx))
# pass 2: remove plates, leaders, marks, dots, code glyphs
def decide(path, idx, op, lwe): return idx in code_idx or in_plate(path) or in_leader(path)
n=walk(decide); print('painting ops neutralised',n)
page.replace_contents(cs)
w.write(DST); print('written',DST)
