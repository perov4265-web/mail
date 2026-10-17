import json, math, sys, collections
import pdfplumber
cl=json.load(open('../pdf/classes.json'))
def bbox(p): xs=[a for a,b in p]; ys=[b for a,b in p]; return (min(xs),min(ys),max(xs),max(ys))
# colored sign objects
objs=[]
for k in cl:
    if k.startswith('other_(0.0, 0.0, 1.0)') or k.startswith('other_(1.0, 0.0, 0.0)') or k.startswith('other_(1.0, 1.0, 0.0)'):
        col={'other_(0.0, 0.0, 1.0)_0.0':'blue','other_(1.0, 0.0, 0.0)_0.0':'red','other_(1.0, 1.0, 0.0)_0.0':'yellow'}[k]
        for o in cl[k]:
            b=bbox(o['pts'])
            if 240<b[0] and b[2]<800 and 100<b[1] and b[3]<1165 and (b[2]-b[0])<14 and (b[3]-b[1])<14:
                objs.append((col,b))
print('colored objs',len(objs))
# cluster by bbox proximity (union-find)
par=list(range(len(objs)))
def f(i):
    while par[i]!=i: par[i]=par[par[i]]; i=par[i]
    return i
def near(a,b,d=1.5): return not (a[2]+d<b[0] or b[2]+d<a[0] or a[3]+d<b[1] or b[3]+d<a[1])
for i in range(len(objs)):
    for j in range(i+1,len(objs)):
        if near(objs[i][1],objs[j][1]): par[f(i)]=f(j)
groups=collections.defaultdict(list)
for i in range(len(objs)): groups[f(i)].append(objs[i])
clusters=[]
for g in groups.values():
    bs=[b for c,b in g]; b=(min(x[0] for x in bs),min(x[1] for x in bs),max(x[2] for x in bs),max(x[3] for x in bs))
    cols=collections.Counter(c for c,_ in g)
    clusters.append({'bbox':[round(v,1) for v in b],'n':len(g),'cols':dict(cols)})
clusters.sort(key=lambda c:(c['bbox'][1],c['bbox'][0]))
print('clusters',len(clusters))
sz=collections.Counter((round(c['bbox'][2]-c['bbox'][0]),round(c['bbox'][3]-c['bbox'][1])) for c in clusters)
print('size hist',sz.most_common(20))
# small text chars near plan
pdf=pdfplumber.open(sys.argv[1]); p=pdf.pages[0]
small=[c for c in p.chars if c['size']<5.5 and 240<c['x0']<800 and 100<c['top']<1165]
print('small chars',len(small), collections.Counter(round(c['size'],1) for c in small))
# cluster chars into strings by proximity
par2=list(range(len(small)))
def f2(i):
    while par2[i]!=i: par2[i]=par2[par2[i]]; i=par2[i]
    return i
for i in range(len(small)):
    for j in range(i+1,len(small)):
        a,b=small[i],small[j]
        if abs(a['x0']-b['x0'])<4 and abs(a['top']-b['top'])<4: par2[f2(i)]=f2(j)
tg=collections.defaultdict(list)
for i in range(len(small)): tg[f2(i)].append(small[i])
texts=[]
for g in tg.values():
    g=sorted(g,key=lambda c:(c['x0'],c['top'])); 
    # orientation: chars stacked vertically => rotated; sort by top descending for rotated
    xs=[c['x0'] for c in g]; ts=[c['top'] for c in g]
    if (max(ts)-min(ts))>(max(xs)-min(xs)): g=sorted(g,key=lambda c:-c['top'])
    s=''.join(c['text'] for c in g)
    texts.append({'text':s,'x':round(sum(c['x0'] for c in g)/len(g),1),'y':round(sum(c['top'] for c in g)/len(g),1)})
print(collections.Counter(t['text'] for t in texts).most_common(40))
json.dump({'clusters':clusters,'texts':texts},open('../pdf/signs_raw.json','w'),ensure_ascii=False)
