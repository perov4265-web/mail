"""Digitise the raster plan of АБК-2 (V.2): walls, door openings, furniture."""
import cv2, numpy as np, json, collections
from PIL import Image
img=np.array(Image.open('v2img-000.png').convert('L')); H,W=img.shape
dark=(img<140).astype(np.uint8)
ch=cv2.morphologyEx(dark,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(3,31)))
cv_=cv2.morphologyEx(dark,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(31,3)))
wh=cv2.morphologyEx(ch,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(61,13)))
wv=cv2.morphologyEx(cv_,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(13,61)))
def comps(mask):
    n,lab,stats,cent=cv2.connectedComponentsWithStats(mask,connectivity=8)
    return [tuple(int(v) for v in (x,y,x+w,y+h)) for x,y,w,h,a in stats[1:]]
H0=comps(wh); V0=comps(wv)
print('raw comps h/v',len(H0),len(V0))
print('h sizes (w,h) sample', sorted([(c[2]-c[0],c[3]-c[1]) for c in H0], reverse=True)[:12])
print('v sizes (w,h) sample', sorted([(c[3]-c[1],c[2]-c[0]) for c in V0], reverse=True)[:12])
# outer rectangle = extents of the long wall bands
longh=[c for c in H0 if c[2]-c[0]>3000]; longv=[c for c in V0 if c[3]-c[1]>1200]
left=min(c[0] for c in longv); right=max(c[2] for c in longv); top=min(c[1] for c in longh); bot=max(c[3] for c in longh)
print('outer px',left,top,right,bot,'size px',right-left,bot-top)
LEN_M=19*3.1+2*0.17; WID_M=13.0+2*0.17
sx=LEN_M/(right-left); sy=WID_M/(bot-top); S=(sx+sy)/2; print('scale mm/px x,y',round(sx*1000,2),round(sy*1000,2))
inside=lambda c: c[0]>=left-30 and c[2]<=right+30 and c[1]>=top-30 and c[3]<=bot+30
hsegs=[c for c in H0 if inside(c) and (c[2]-c[0])*S>=0.9 and (c[3]-c[1])<=110]
vsegs=[c for c in V0 if inside(c) and (c[3]-c[1])*S>=0.9 and (c[2]-c[0])<=110]
print('wall segs h/v',len(hsegs),len(vsegs))
def gaps(segs, horiz):
    out=[]; bands=collections.defaultdict(list)
    for s in segs: bands[int(((s[1]+s[3])//2 if horiz else (s[0]+s[2])//2)//14)].append(s)
    for k,ss in bands.items():
        ss=sorted(ss,key=lambda s:s[0] if horiz else s[1])
        for a,b in zip(ss,ss[1:]):
            g=(b[0]-a[2]) if horiz else (b[1]-a[3])
            if 0.6/S<=g<=1.9/S: out.append({'a':a,'b':b,'horiz':horiz})
    return out
doors=gaps(hsegs,True)+gaps(vsegs,False); print('door gaps',len(doors))
walls=cv2.bitwise_or(wh,wv); wd=cv2.dilate(walls,cv2.getStructuringElement(cv2.MORPH_RECT,(21,21)))
thin=cv2.bitwise_and(dark,cv2.bitwise_not(wd)); thin[:top+12,:]=0; thin[bot-12:,:]=0; thin[:,:left+12]=0; thin[:,right-12:]=0
thin=cv2.morphologyEx(thin,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(9,9)))
furn=[c for c in comps(thin) if 0.35<=(c[2]-c[0])*S<=4.5 and 0.35<=(c[3]-c[1])*S<=4.5]
print('furniture comps',len(furn))
dbg=cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
for x0,y0,x1,y1 in hsegs+vsegs: cv2.rectangle(dbg,(x0,y0),(x1,y1),(0,0,255),3)
for d in doors:
    a,b=d['a'],d['b']
    if d['horiz']: cv2.rectangle(dbg,(a[2],a[1]-12),(b[0],a[3]+12),(0,170,0),4)
    else: cv2.rectangle(dbg,(a[0]-12,a[3]),(a[2]+12,b[1]),(0,170,0),4)
for x0,y0,x1,y1 in furn: cv2.rectangle(dbg,(x0,y0),(x1,y1),(255,0,0),2)
cv2.rectangle(dbg,(left,top),(right,bot),(0,200,200),2)
cv2.imwrite('v2_debug_crop.png',cv2.resize(dbg[top-60:bot+60,left-60:left+3700],None,fx=0.42,fy=0.42)); cv2.imwrite('v2_debug_crop2.png',cv2.resize(dbg[top-60:bot+60,left+3700:right+60],None,fx=0.42,fy=0.42))
# thin single-line partitions (tempered glass per the legend): long thin lines not inside thick wall bands
notw=cv2.bitwise_and(dark,cv2.bitwise_not(cv2.dilate(walls,cv2.getStructuringElement(cv2.MORPH_RECT,(25,25)))))
tv=cv2.morphologyEx(notw,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,int(1.8/S))))
th=cv2.morphologyEx(notw,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(int(1.8/S),1)))
gv=[c for c in comps(tv) if inside(c) and (c[3]-c[1])*S>=1.8 and (c[2]-c[0])<=12]
gh=[c for c in comps(th) if inside(c) and (c[2]-c[0])*S>=1.8 and (c[3]-c[1])<=12]
print('glass partitions v/h',len(gv),len(gh))
for x0,y0,x1,y1 in gv+gh: cv2.rectangle(dbg,(x0-4,y0-4),(x1+4,y1+4),(200,0,200),3)
cv2.imwrite('v2_debug_crop.png',cv2.resize(dbg[top-60:bot+60,left-60:left+3700],None,fx=0.42,fy=0.42)); cv2.imwrite('v2_debug_crop2.png',cv2.resize(dbg[top-60:bot+60,left+3700:right+60],None,fx=0.42,fy=0.42))
json.dump({'glass_v':gv,'glass_h':gh,'left':left,'top':top,'right':right,'bot':bot,'S':S,'hsegs':hsegs,'vsegs':vsegs,'doors':doors,'furn':furn},open('v2_raw.json','w'))
