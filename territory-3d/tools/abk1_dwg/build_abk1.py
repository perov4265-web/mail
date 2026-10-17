"""АБК-1: walls, windows, doors, furniture from the DWG plan -> territory-3d/data/abk1.json (metres, local origin SW corner)."""
import json, math, collections
E=json.load(open('plan_entities.json'))
MM=0.001
def bb(pts): xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return [min(xs),min(ys),max(xs),max(ys)]
walls=[]
for lay in ('PANEL','BIRLESIM ELEMANI'):
    for o in E.get(lay,[]):
        if o['t']=='PL' and len(o['pts'])>=4:
            b=bb(o['pts']); w=b[2]-b[0]; h=b[3]-b[1]
            if w<30 or h<30: continue
            if w>120 and h>120 and min(w,h)>200: continue       # not a panel (e.g. big shape)
            walls.append({'rect':[round(v*MM,3) for v in b],'src':lay})
# merge duplicate rects
seen=set(); uw=[]
for w in walls:
    k=tuple(w['rect'])
    if k in seen: continue
    seen.add(k); uw.append(w)
walls=uw
def wall_of(pt, pad=60):
    for i,w in enumerate(walls):
        r=[v/MM for v in w['rect']]
        if r[0]-pad<=pt[0]<=r[2]+pad and r[1]-pad<=pt[1]<=r[3]+pad: return i
    return None
# windows: PENCERE jamb lines crossing a wall (short lines ~ wall thickness)
jambs=collections.defaultdict(list)
for o in E.get('PENCERE',[]):
    if o['t']=='L':
        (x0,y0),(x1,y1)=o['pts']; L=math.hypot(x1-x0,y1-y0)
        if 80<=L<=130:
            c=((x0+x1)/2,(y0+y1)/2); wi=wall_of(c)
            if wi is not None:
                r=[v/MM for v in walls[wi]['rect']]; horiz=(r[2]-r[0])>=(r[3]-r[1])
                jambs[wi].append(round(c[0] if horiz else c[1]))
windows=[]
for wi,js in jambs.items():
    js=sorted(set(js)); r=walls[wi]['rect']; horiz=(r[2]-r[0])>=(r[3]-r[1])
    for i in range(0,len(js)-1,2):
        a,b=js[i],js[i+1]
        if 300<b-a<3000:
            windows.append({'wall':wi,'from':round(a*MM,3),'to':round(b*MM,3),'sill':1.0,'head':2.07,'axis':'x' if horiz else 'y'})
# doors: KAPI arcs: hinge = centre, width = radius; opening runs along the wall from the hinge
doors=[]
for o in E.get('KAPI',[]):
    if o['t']=='ARC':
        c=o['c']; r=o['r']; a0,a1=o['a']
        ends=[(c[0]+r*math.cos(math.radians(a)), c[1]+r*math.sin(math.radians(a))) for a in (a0,a1)]
        wi=wall_of(c, pad=120)
        if wi is None: continue
        wr=[v/MM for v in walls[wi]['rect']]; horiz=(wr[2]-wr[0])>=(wr[3]-wr[1])
        # the end lying along the wall axis
        end=min(ends, key=lambda e: abs(e[1]-c[1]) if horiz else abs(e[0]-c[0]))
        a=c[0] if horiz else c[1]; b=end[0] if horiz else end[1]
        doors.append({'wall':wi,'from':round(min(a,b)*MM,3),'to':round(max(a,b)*MM,3),'height':2.05 if r<1000 else 2.1,'axis':'x' if horiz else 'y','leaf':round(r*MM,2),
                      'hinge':[round(c[0]*MM,3),round(c[1]*MM,3)],'swing_to':[round(ends[1][0]*MM,3),round(ends[1][1]*MM,3)] if ends[1]!=end else [round(ends[0][0]*MM,3),round(ends[0][1]*MM,3)]})
# furniture / equipment: block inserts (bbox) and Equipment polylines
furn=[]
for lay in ('Equipment','0'):
    for o in E.get(lay,[]):
        if o['t']=='INS':
            b=o['bb']; w=(b[2]-b[0])*MM; d=(b[3]-b[1])*MM
            if w<0.05 or d<0.05 or w>6 or d>6: continue
            h=0.45 if max(w,d)<0.7 else 0.75
            furn.append({'rect':[round(v*MM,3) for v in b],'h':h,'name':o['name']})
        elif o['t']=='PL' and lay=='Equipment' and len(o['pts'])>=4:
            b=bb(o['pts']); w=(b[2]-b[0])*MM; d=(b[3]-b[1])*MM
            if 0.3<w<4 and 0.3<d<4: furn.append({'rect':[round(v*MM,3) for v in b],'h':0.75,'name':'equip'})
labels=[]  # the DWG carries only equipment tags (A/C, EF, FX), no room names
# entrances = gaps in the exterior wall panels (AL1 at both corridor ends, AL2 on the south facade); porch + canopy outside each
Lx,Ly=43.575,14.63
def gaps_on(side):
    spans=[]
    for w in walls:
        r=w['rect']
        if side=='W' and r[0]<0.2 and r[2]-r[0]<0.3: spans.append((r[1],r[3]))
        if side=='E' and r[2]>Lx-0.2 and r[2]-r[0]<0.3: spans.append((r[1],r[3]))
        if side=='S' and r[1]<0.2 and r[3]-r[1]<0.3: spans.append((r[0],r[2]))
        if side=='N' and r[3]>Ly-0.2 and r[3]-r[1]<0.3: spans.append((r[0],r[2]))
    spans.sort(); out=[]
    for p,q in zip(spans,spans[1:]):
        if 0.7<q[0]-p[1]<3.0: out.append((p[1],q[0]))
    return out
porches=[]
for side in 'WESN':
    for g0,g1 in gaps_on(side):
        c=(g0+g1)/2; w=g1-g0
        if side=='W': porches.append({'rect':[-1.5,round(c-1.2,3),0,round(c+1.2,3)],'canopy':True,'canopy_h':2.4,'canopy_posts_y':round(c-1.0,3),'entrance':'AL1','door_w':round(w,2)})
        if side=='E': porches.append({'rect':[Lx,round(c-1.2,3),Lx+1.5,round(c+1.2,3)],'canopy':True,'canopy_h':2.4,'canopy_posts_y':round(c-1.0,3),'entrance':'AL1','door_w':round(w,2)})
        if side=='S': porches.append({'rect':[round(c-1.2,3),-1.5,round(c+1.2,3),0],'canopy':True,'canopy_h':2.4,'canopy_posts_y':-1.35,'entrance':'AL2','door_w':round(w,2)})
        if side=='N': porches.append({'rect':[round(c-1.2,3),Ly,round(c+1.2,3),Ly+1.5],'canopy':True,'canopy_h':2.4,'canopy_posts_y':round(Ly+1.35,3),'entrance':'AL','door_w':round(w,2)})
print('entrances',[(p['entrance'],p['rect'],p['door_w']) for p in porches])
abk={'id':'ABK-1','placement':{'building':'1','rotation_deg':0},'porches_note':'крыльца 2,4×1,5 м с козырьками у входов AL1/AL2 — условно (план «SUNDURMA» в DWG)','name':'Административно-бытовой корпус №1 (АБК-1)','source':'Office_Building-1.dwg (модульное здание, панели 105 мм)',
 'size_m':[43.575,14.63],'levels':{'wall_h':2.4,'parapet_top':3.6,'roof_slab':0.2,'window_sill':1.0,'window_head':2.07,'door_h':2.05},
 'wall_thickness_m':0.105,'walls':walls,'windows':windows,'doors':doors,'furniture':furn,'labels':labels,
 'porches':porches,'roof':{'type':'flat_parapet','parapet_top':3.6},'notes':['Отметки +0.00 / +2.40 (верх стеновых панелей) / +3.60 (верх парапета) — с фасада DWG','Окна W3 850 мм, подоконник 1,0 м, верх 2,07 м — с фасада','Двери D2 840 мм; мебель — по блокам чертежа (габариты в плане, высоты условные)']}
json.dump(abk,open('/home/user/mail/territory-3d/data/abk1.json','w'),ensure_ascii=False,indent=1)
print('walls',len(walls),'windows',len(windows),'doors',len(doors),'furniture',len(furn),'labels',len(labels))
print('door widths',collections.Counter(round(d['to']-d['from'],2) for d in doors))
print('window widths',collections.Counter(round(w['to']-w['from'],2) for w in windows))
print('labels sample',[l['s'] for l in labels][:20])
