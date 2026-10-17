"""АБК-2 (удлинённый V.2): walls/doors/furniture from the digitised raster, facade/roof/trusses from Итог1 -> abk2.json"""
import json, math
R=json.load(open('v2_raw.json')); S=R['S']; left,top,right,bot=R['left'],R['top'],R['right'],R['bot']
LEN=19*3.1+2*0.17; WID=13.0+2*0.17
def mx(x): return round((x-left)*S,3)
def my(y): return round((bot-y)*S,3)
walls=[]
EXT=0.17; INT=0.10
def is_ext_h(c): return c[1]<top+40 or c[3]>bot-40
def is_ext_v(c): return c[0]<left+40 or c[2]>right-40
for c in R['hsegs']:
    t=EXT if is_ext_h(c) else INT; yc=(my(c[1])+my(c[3]))/2
    if c[1]<top+40: yc=WID-EXT/2
    if c[3]>bot-40: yc=EXT/2
    walls.append({'rect':[mx(c[0]),round(yc-t/2,3),mx(c[2]),round(yc+t/2,3)],'src':'h'})
for c in R['vsegs']:
    t=EXT if is_ext_v(c) else INT; xc=(mx(c[0])+mx(c[2]))/2
    if c[0]<left+40: xc=EXT/2
    if c[2]>right-40: xc=LEN-EXT/2
    walls.append({'rect':[round(xc-t/2,3),my(c[3]),round(xc+t/2,3),my(c[1])],'src':'v'})
for c in R.get('glass_v',[]):
    xc=(mx(c[0])+mx(c[2]))/2; walls.append({'rect':[round(xc-0.01,3),my(c[3]),round(xc+0.01,3),my(c[1])],'src':'v','material':'glass'})
for c in R.get('glass_h',[]):
    yc=(my(c[1])+my(c[3]))/2; walls.append({'rect':[mx(c[0]),round(yc-0.01,3),mx(c[2]),round(yc+0.01,3)],'src':'h','material':'glass'})
# clamp to the outline
for w in walls:
    r=w['rect']; r[0]=max(0,r[0]); r[1]=max(0,r[1]); r[2]=min(LEN,r[2]); r[3]=min(WID,r[3])
def wall_of(x,y,pad=0.25):
    best=None
    for i,w in enumerate(walls):
        r=w['rect']
        if r[0]-pad<=x<=r[2]+pad and r[1]-pad<=y<=r[3]+pad:
            d=max(r[0]-x,0,x-r[2])+max(r[1]-y,0,y-r[3])
            if best is None or d<best[0]: best=(d,i)
    return None if best is None else best[1]
# corridor walls = the two long interior horizontal walls; rooms = spans between vertical partitions touching them
hw=[w for w in walls if w['src']=='h' and 0.5<w['rect'][1]<WID-0.5 and w['rect'][2]-w['rect'][0]>3]
ys=sorted(set(round((w['rect'][1]+w['rect'][3])/2,1) for w in hw)); print('interior h-wall levels',ys)
cor_s=min(ys,key=lambda y:abs(y-5.62)); cor_n=min(ys,key=lambda y:abs(y-7.72))   # corridor B–C: 5.45+0.17 .. 7.72
print('corridor walls',cor_s,cor_n)
vx=sorted(set(round((w['rect'][0]+w['rect'][2])/2,2) for w in walls if w['src']=='v'))
hall=(EXT+3.1*11, EXT+3.1*16)
doors=[]; porches=[]
gap_doors=[]
for d in R['doors']:
    a,bb_=d['a'],d['b']
    if not d['horiz']: continue
    x0,x1=mx(a[2]),mx(bb_[0]); yc=(my(a[1])+my(a[3]))/2
    if abs(yc-cor_s)>0.3 and abs(yc-cor_n)>0.3 and not (8.7<yc<9.0): continue
    t=INT; wi=len(walls); walls.append({'rect':[x0,round(yc-t/2,3),x1,round(yc+t/2,3)],'src':'gap'})
    sw=1 if yc>WID/2 or (8.7<yc<9.0) else -1
    doors.append({'wall':wi,'from':x0,'to':x1,'height':2.1,'axis':'x','leaf':round(x1-x0,2),'hinge':[x0,round(yc,3)],'swing_to':[x0,round(yc+sw*(x1-x0),3)]}); gap_doors.append((x0,x1,yc))
print('gap doors',len(gap_doors))
def wall_at(x,y):
    best=None
    for i,w in enumerate(walls):
        r=w['rect']
        if r[0]-0.05<=x<=r[2]+0.05 and r[1]-0.12<=y<=r[3]+0.12 and w['src']=='h':
            if best is None or (r[2]-r[0])>(walls[best]['rect'][2]-walls[best]['rect'][0]): best=i
    return best
def add_door_x(x,y,w=0.9,swing=1):
    wi=wall_at(x,y)
    if wi is None: return False
    doors.append({'wall':wi,'from':round(x-w/2,3),'to':round(x+w/2,3),'height':2.1,'axis':'x','leaf':w,'hinge':[round(x-w/2,3),round(y,3)],'swing_to':[round(x-w/2,3),round(y+swing*w,3)]}); return True
# room doors: for each pair of consecutive partitions (incl. end walls) along each corridor wall, one door 0.9 m near the east partition
for yc,side in ((cor_n,'N'),(cor_s,'S')):
    # partitions that touch this corridor wall on the room side
    parts=[EXT/2]+[x for x in vx if any(abs((w['rect'][0]+w['rect'][2])/2-x)<0.03 and (w['rect'][3]>yc+0.5 if side=='N' else w['rect'][1]<yc-0.5) and (w['rect'][1]<yc+0.4 and w['rect'][3]>yc-0.4) for w in walls if w['src']=='v')]+[LEN-EXT/2]
    parts=sorted(set(parts))
    for p,q in zip(parts,parts[1:]):
        if q-p<1.5 or (hall[0]-0.3<p and q<hall[1]+0.3): continue
        if any(p<=(g0+g1)/2<=q and abs(gy-yc)<0.3 for g0,g1,gy in gap_doors): continue
        x=q-0.75 if side=='N' else p+0.75
        if not add_door_x(x,yc,0.9,1 if side=='N' else -1): add_door_x((p+q)/2,yc,0.9,1 if side=='N' else -1)
n_room=len(doors)
# entrances: corridor ends (axes 1 and 20), north entrance at bay 9 (x≈26.5), hall->corridor door at axis 17
def add_door_y(x,y,w,swing=1):
    best=None
    for i,wl in enumerate(walls):
        r=wl['rect']
        if r[1]-0.05<=y<=r[3]+0.05 and r[0]-0.3<=x<=r[2]+0.3 and wl['src']=='v' and (best is None or abs((r[0]+r[2])/2-x)<abs((walls[best]['rect'][0]+walls[best]['rect'][2])/2-x)): best=i
    if best is None: print('no v-wall at',x,y); return
    doors.append({'wall':best,'from':round(y-w/2,3),'to':round(y+w/2,3),'height':2.1,'axis':'y','leaf':w,'hinge':[round(x,3),round(y-w/2,3)],'swing_to':[round(x+swing*w,3),round(y-w/2,3)]})
yc=(cor_s+cor_n)/2
add_door_y(EXT/2,yc,1.5,1); add_door_y(LEN-EXT/2,yc,1.5,-1)
# hall end walls (axes 12 and 17): corridor runs through -> openings cor_s..cor_n without leaves
for xe in (hall[0], hall[1]):
    best=None
    for i,wl in enumerate(walls):
        r=wl['rect']
        if wl['src']=='v' and r[0]-0.8<=xe<=r[2]+0.8 and r[1]<=yc<=r[3]: best=i
    if best is None:
        parts=[i for i,wl in enumerate(walls) if wl['src']=='v' and abs((wl['rect'][0]+wl['rect'][2])/2-xe)<0.8]
        if parts:   # wall is split around the corridor: add a bridging piece that carries the opening (existing walls keep their indices)
            r0=walls[parts[0]]['rect']; walls.append({'rect':[r0[0],round(cor_s,3),r0[2],round(cor_n,3)],'src':'gap'}); best=len(walls)-1
    if best is not None:
        doors.append({'wall':best,'from':round(cor_s+0.05,3),'to':round(cor_n-0.05,3),'height':2.1,'axis':'y','leaf':0,'opening':True})
add_door_x(EXT+3.1*8+1.6,WID-EXT/2,1.5,-1)
porches=[{'rect':[-1.5,round(yc-1.2,3),0,round(yc+1.2,3)],'canopy':True,'canopy_h':2.5,'canopy_posts_y':round(yc-1.0,3),'entrance':'ось 1'},
         {'rect':[round(LEN,3),round(yc-1.2,3),round(LEN+1.5,3),round(yc+1.2,3)],'canopy':True,'canopy_h':2.5,'canopy_posts_y':round(yc-1.0,3),'entrance':'ось 20'},
         {'rect':[round(EXT+3.1*8+0.4,3),round(WID,3),round(EXT+3.1*8+2.8,3),round(WID+1.5,3)],'canopy':True,'canopy_h':2.5,'canopy_posts_y':round(WID+1.35,3),'entrance':'север, оси 9–10'}]
print('room doors',n_room,'entrances',len(doors)-n_room)
# windows: one 1.0 m window per 3.1 m bay on both long facades (Итог1: sill +0.900, head +2.100)
windows=[]
for side,(yc) in (('S',EXT/2),('N',WID-EXT/2)):
    for i in range(19):
        xc=EXT+3.1*i+1.55; wi=wall_of(xc, yc, 0.3)
        if wi is None: continue
        r=walls[wi]['rect']
        if r[2]-r[0] < 1.2 or walls[wi]['src']=='gap': continue
        if hall[0]<xc<hall[1]: continue   # temple hall has no windows (photo survey)
        windows.append({'wall':wi,'from':round(xc-0.5,3),'to':round(xc+0.5,3),'sill':0.9,'head':2.1,'axis':'x'})
furn=[]
hall=(EXT+3.1*11, EXT+3.1*16)   # axes 12–17: temple hall
for c in R['furn']:
    r=[mx(c[0]),my(c[3]),mx(c[2]),my(c[1])]; w=r[2]-r[0]; d=r[3]-r[1]
    if hall[0]<(r[0]+r[2])/2<hall[1]: continue      # temple hall: columns are set explicitly below
    furn.append({'rect':r,'h':0.45 if max(w,d)<0.7 else 0.75,'name':'furn'})
# 8 columns in the temple hall: axes 13–16 on grid lines B and C (corridor lines), trusses keep the uniform 3.1 m pitch
columns=[[round(EXT+3.1*i,3), round(yc,3)] for i in range(12,16) for yc in (EXT+5.45, EXT+5.45+2.1)]
labels=[{'s':'Храм','p':[round((hall[0]+hall[1])/2,3),round(WID/2,3)]}]
# temple hall bounds snapped to the digitised end walls (inner faces)
def inner_face(xe, side):
    cands=[w['rect'] for w in walls if w['src']=='v' and abs((w['rect'][0]+w['rect'][2])/2-xe)<0.8]
    if not cands: return xe
    r=min(cands,key=lambda r:abs((r[0]+r[2])/2-xe)); return round((r[2]+0.01) if side=='x0' else (r[0]-0.01),3)
hall_in=(inner_face(hall[0],'x0'), inner_face(hall[1],'x1')); print('hall inner faces',hall_in)
abk={'id':'ABK-2','name':'Административно-бытовой корпус №2 (АБК-2, удлинённый V.2)','placement':{'building':'2.1','rotation_deg':270},
 'source':'планировка и мебель — «АБК 2 удлинённый V.2.pdf» (растр, оцифровка); фасады, кровля, фермы — «Итог1.pdf» (91VVF)',
 'size_m':[round(LEN,3),round(WID,3)],'levels':{'wall_h':3.0,'window_sill':0.9,'window_head':2.1,'door_h':2.1},'wall_thickness_m':EXT,
 'walls':walls,'windows':windows,'doors':doors,'furniture':furn,'labels':labels,'porches':porches,
 'temple':{'x0':hall_in[0],'x1':hall_in[1],'y0':EXT,'y1':round(WID-EXT,3),'sanctuary_depth':5.3,'altar_side':'y1','columns':columns,'finish':'wood_glass'},
 'roof':{'type':'gable','eave':3.45,'ridge':4.35,'bottom_chord':3.0,'overhang':0.3,'band':{'from':3.0,'to':4.35},'truss':{'pitch':3.1,'member':0.08,'panels':6,'purlins':5,'color':'#f2f1ec'}},
 'notes':['Оси 12–17 — храм: зал на всю ширину без окон (по фото), 8 колонн по осям 13–16 на линиях B и C; иконостас вдоль восточной стены, алтарь 5,3 м (колонны ряда C стоят у кромки солеи — по фото); выходы в коридор в торцах сразу за иконостасом; отделка колонн и поясов — дуб','Двери кабинетов — по одной в коридорной стене каждого помещения (положение по растру приближённое)','Сетка 20 осей × 3,1 м (58,9 м) × 13,0 м (5,45 + 2,1 + 5,45) — по «Итог1», удлинение по V.2','Стены 110/100 мм, верх стен +3,000, карниз +3,450, конёк +4,350, уклон 0,12 — по разрезу 1-1 «Итог1»','Окантовка кровли — как у АБК-1: сплошной пояс по периметру от верха стен +3,00 до конька +4,35, фермы и прогоны снаружи не видны','Окна 1000 мм, подоконник +0,900, верх +2,100 — по фасадам «Итог1»; расставлены по одному на пролёт (на растровом плане V.2 окна не показаны)','Планировка, двери и мебель оцифрованы с растрового плана V.2 (точность ≈ ±0,1 м)']}
json.dump(abk,open('/home/user/mail/territory-3d/data/abk2.json','w'),ensure_ascii=False,indent=1)
print('walls',len(walls),'doors',len(doors),'windows',len(windows),'furniture',len(furn),'porches',len(porches))
