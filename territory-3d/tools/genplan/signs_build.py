import json, math
cl=json.load(open('../pdf/classes.json')); raw=json.load(open('../pdf/signs_posts.json'))
S=25.4/72; TX0=728*72/200; TY1=(292+2917)*72/200
def M(pt): return [round((pt[0]-TX0)*S,3), round((TY1-pt[1])*S,3)]
def bbox(p): xs=[a for a,b in p]; ys=[b for a,b in p]; return (min(xs),min(ys),max(xs),max(ys))
# leaders: thick black (0.84 pt) 2-point segments from the post mark (a few pt off the plate) to the install dot
segs=[]
for o in cl['black_thick']:
    p=o['pts']
    if len(p)==2 and 3<math.dist(p[0],p[1])<80: segs.append((tuple(p[0]),tuple(p[1])))
    elif len(p)<=4 and not o['fill']:
        for i in range(len(p)-1):
            if 3<math.dist(p[i],p[i+1])<80: segs.append((tuple(p[i]),tuple(p[i+1])))
def dist_box(pt,b):
    dx=max(b[0]-pt[0],0,pt[0]-b[2]); dy=max(b[1]-pt[1],0,pt[1]-b[3]); return math.hypot(dx,dy)
def leader_end(b):
    best=None
    for a,e in segs:
        da,de=dist_box(a,b),dist_box(e,b)
        near,far,dn=(a,e,da) if da<de else (e,a,de)
        if dn<=7.0 and (best is None or dn<best[0]): best=(dn,far,near)
    return best
# classification by cluster index (from the contact sheet)
PLATES={1:['2.5','3.24-5'],2:['6.4','5.19.2'],3:['6.4'],4:['5.19.1'],5:['5.19.2'],6:['5.19.1'],7:['2.4','5.19.1'],8:['2.4'],9:['3.28'],
 10:['2.4'],11:['2.4'],12:['5.19.1'],13:['2.4'],14:['5.19.1'],15:['5.19.1','2.4'],16:['3.24-20','2.1'],18:['6.4'],19:['5.19.1','2.4'],20:['6.4'],
 21:['2.4'],22:['5.19.1'],23:['5.19.1'],24:['6.4'],25:['5.19.1'],26:['2.4'],27:['2.4'],28:['5.19.1'],29:['5.19.1'],30:['2.4','5.x','5.19.1'],
 31:['2.4'],32:['5.19.1'],33:['2.4'],34:['5.19.1'],35:['3.24-20','2.1'],37:['5.19.1','5.x','3.24-20'],38:['3.28'],39:['3.28'],40:['2.4','5.19.1'],
 41:['6.4','5.19.1'],43:['2.1','3.24-20'],44:['2.4','5.19.1'],45:['3.28'],46:['3.28'],47:['6.4','5.19.1'],48:['2.5','3.24-5'],49:['6.4']}
MERGE={17:16,36:35,42:43}
NAMES={'2.5':'Движение без остановки запрещено','3.24-5':'Ограничение скорости 5 км/ч','3.24-20':'Ограничение скорости 20 км/ч','6.4':'Парковка',
 '5.19.1':'Пешеходный переход','5.19.2':'Пешеходный переход','2.4':'Уступите дорогу','3.28':'Стоянка запрещена','2.1':'Главная дорога','5.x':'Информационный знак'}
by={c['i']:c for c in raw}
signs=[]
for i,plates in PLATES.items():
    c=by[i]; b=c['bbox'][:]
    for j,k in MERGE.items():
        if k==i:
            bb=by[j]['bbox']; b=[min(b[0],bb[0]),min(b[1],bb[1]),max(b[2],bb[2]),max(b[3],bb[3])]
    center=((b[0]+b[2])/2,(b[1]+b[3])/2)
    post=None; L=leader_end(b)
    if L: post=L[1]
    src='выноска' if post else 'символ'
    if not post: post=center
    signs.append({'id':'S%02d'%i,'plates':plates,'names':[NAMES[p] for p in plates],'pos':M(post),'placement':src,'symbol_pos':M(center)})
site=json.load(open('/home/user/mail/territory-3d/data/site.json'))
site['signs']={'post_height_m':3.0,'post_dia_m':0.076,'plate_size_m':0.7,'top_plate_center_m':2.6,'items':signs,
 'note':'Положение — чёрная точка выноски на плане (где выноски нет — по символу); щиты двусторонние, ориентация по ближайшей стрелке движения'}
json.dump(site,open('/home/user/mail/territory-3d/data/site.json','w'),ensure_ascii=False,indent=1)
print(len(signs),'signs;', sum(1 for s in signs if s['placement']=='выноска'),'by leader'); print([ (x['id'],x['placement']) for x in signs if x['placement']!='выноска'])
