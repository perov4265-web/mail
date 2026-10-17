import json, math, collections, subprocess
from PIL import Image, ImageDraw
cl=json.load(open('../pdf/classes.json')); raw=json.load(open('../pdf/signs_raw.json'))
def bbox(p): xs=[a for a,b in p]; ys=[b for a,b in p]; return (min(xs),min(ys),max(xs),max(ys))
# candidate leader segments: 2-point black lines, length 4..40
segs=[]
for k in ['black_0','black_024','black_06','black_thick']:
    for o in cl[k]:
        p=o['pts']
        if len(p)==2:
            L=math.dist(p[0],p[1])
            if 4<L<45: segs.append((p[0],p[1],k))
        elif 2<len(p)<=4 and not o['fill']:
            for i in range(len(p)-1):
                L=math.dist(p[i],p[i+1])
                if 4<L<45: segs.append((p[i],p[i+1],k))
print('segs',len(segs))
def inb(pt,b,d): return b[0]-d<=pt[0]<=b[2]+d and b[1]-d<=pt[1]<=b[3]+d
out=[]
for i,c in enumerate(raw['clusters']):
    b=c['bbox']; cand=[]
    for a,e,k in segs:
        ia,ie=inb(a,b,1.5),inb(e,b,1.5)
        if ia and not ie: cand.append((e,a,k,math.dist(a,e)))
        elif ie and not ia: cand.append((a,e,k,math.dist(a,e)))
    # follow a chain: leader may bend once
    post=None; chain=[]
    if cand:
        cand.sort(key=lambda t:-t[3]); e,a,k,L=cand[0]; chain=[a,e]; post=e
        for _ in range(2):
            nxt=[(q,) for a2,e2,k2 in segs for q in ([e2] if math.dist(a2,post)<0.6 and not inb(e2,b,1.5) and math.dist(e2,chain[-2])>1 else ([a2] if math.dist(e2,post)<0.6 and not inb(a2,b,1.5) and math.dist(a2,chain[-2])>1 else []))]
            if nxt: post=nxt[0][0]; chain.append(post)
            else: break
    c['post']=[round(v,1) for v in post] if post else None; c['chain']=[[round(v,1) for v in q] for q in chain]; c['i']=i
    out.append(c)
    print(i,c['bbox'],c['cols'],'post',c['post'],'chain',len(chain))
json.dump(out,open('../pdf/signs_posts.json','w'))
# contact sheet at 300 dpi
R=300/72
subprocess.run(['pdftoppm','-r','300','-png','-x',str(int(240*R)),'-y',str(int(100*R)),'-W',str(int(560*R)),'-H',str(int(1065*R)),
  '/root/.claude/uploads/b88ed1fb-3089-5143-8750-3ece00bcac1a/6a6f185e-2_5222266510621318180.pdf','../pdf/hi'],check=True)
im=Image.open('../pdf/hi-1.png'); ox,oy=240,100
cell=170; cols=8; rows=math.ceil(len(out)/cols)
sheet=Image.new('RGB',(cols*cell,rows*cell),'white'); d=ImageDraw.Draw(sheet)
for c in out:
    b=c['bbox']; pts=[(b[0],b[1]),(b[2],b[3])]+([tuple(c['post'])] if c['post'] else [])
    x0=min(p[0] for p in pts)-3; y0=min(p[1] for p in pts)-3; x1=max(p[0] for p in pts)+3; y1=max(p[1] for p in pts)+3
    crop=im.crop((int((x0-ox)*R),int((y0-oy)*R),int((x1-ox)*R),int((y1-oy)*R)))
    crop.thumbnail((cell-10,cell-24)); i=c['i']; X=(i%cols)*cell; Y=(i//cols)*cell
    sheet.paste(crop,(X+5,Y+20)); d.text((X+4,Y+2),'#%d %s'%(i,'post' if c['post'] else 'NO POST'),fill='red')
    d.rectangle((X,Y,X+cell-1,Y+cell-1),outline='#ccc')
sheet.save('../pdf/signs_sheet.png'); print(sheet.size)
