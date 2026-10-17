"""Builds territory-3d/data/site.json from the vector classes extracted from the Civil 3D PDF."""
import json, math, sys
cl = json.load(open('../pdf/classes.json'))
OUT = sys.argv[1]

# ---- scale & frame ------------------------------------------------------
S = 25.4/72                # m per PDF point: sheet is 1:1000 (2.5 m stall pitch = 7.09 pt, stall depth 5.4 m, aisle 7.8 m)
# texture crop (pdftoppm -r 200 -x 728 -y 292 -W 1467 -H 2917)
TX0, TY0 = 728*72/200, 292*72/200
TX1, TY1 = (728+1467)*72/200, (292+2917)*72/200
def M(pt):  # PDF (x, top) -> site metres (X east, Y north)
    x, y = pt
    return [round((x-TX0)*S, 3), round((TY1-y)*S, 3)]
def poly(pts):
    p = [M(q) for q in pts]
    if len(p) > 1 and p[0] == p[-1]: p = p[:-1]
    # drop near-duplicate consecutive points
    out = []
    for q in p:
        if not out or math.dist(out[-1], q) > 0.05: out.append(q)
    return out
def bbox(pts):
    xs=[a for a,b in pts]; ys=[b for a,b in pts]; return (min(xs),min(ys),max(xs),max(ys))
def rect(x0,y0,x1,y1): return poly([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])

# ---- buildings: label -> source polygon (PDF bbox used to find it) -------
EXPL = {
 '1':'Административно-бытовой корпус №1','2.1':'Административно-бытовой корпус №2','2.2':'Административно-бытовой корпус №3',
 '3':'Столовая №1 со встроенным медицинским пунктом','4':'Столовая №2','5.1':'Трансформаторная подстанция №1','5.2':'Трансформаторная подстанция №2',
 '6.1':'Комплекс ДГУ с топливным баком','7':'Лаборатория','8':'Накопительная ёмкость бытовых стоков (4 м³)','9':'Резервуары противопожарного запаса воды',
 '10.1':'Контрольно-пропускной пункт №1','10.2':'Контрольно-пропускной пункт №2','10.3':'Контрольно-пропускной пункт (проходная)','11':'Резервуары с водой',
 '12':'Накопительная ёмкость бытовых стоков','13.1':'Закрытый склад','13.2':'Закрытый склад','14':'Бытовой корпус',
 '15.1':'Здание для проживания рабочего персонала','15.2':'Здание для проживания рабочего персонала','15.3':'Здание для проживания рабочего персонала','15.4':'Здание для проживания рабочего персонала'}
# (label, class, bbox-of-source-polygon in PDF pt, type, nominal height m)
SRC = [
 ('1','building',(577.8,201.6,708.1,249.8),'building',6.6),
 ('2.1','building',(578.5,303.4,621.5,473.5),'building',6.6),
 ('2.2','building',(664.8,302.0,707.8,445.9),'building',6.6),
 ('3','building',(460.9,302.3,506.4,410.5),'building',4.0),
 ('4','black_06',(308.2,893.6,384.6,970.2),'building',4.0),
 ('5.1','black_06',(751.3,478.0,770.2,501.1),'tech',3.0),
 ('5.2','black_06',(374.4,681.5,400.2,692.0),'tech',3.0),
 ('6.1','black_06',(751.3,428.2,770.5,438.4),'tech',2.6),
 ('7','building',(360.6,303.2,395.3,467.6),'building',4.0),
 ('10.1','black_06',(308.6,179.9,322.1,193.0),'kpp',3.0),
 ('10.2','black_06',(309.8,1057.8,323.9,1071.5),'kpp',3.0),
 ('10.3','black_06',(440.4,698.8,457.2,705.5),'kpp',3.0),
 ('13.1','black_06',(556.3,553.7,601.1,644.4),'warehouse',5.0),
 ('13.2','black_06',(657.7,553.4,702.5,644.2),'warehouse',5.0),
 ('14','black_06',(744.7,696.0,761.8,721.4),'building',3.0),
 ('15.1','building',(449.9,762.2,489.5,1009.7),'dorm',9.0),
 ('15.2','building',(534.8,761.9,574.6,1009.2),'dorm',9.0),
 ('15.3','building',(618.6,760.0,661.1,1010.2),'dorm',9.0),
 ('15.4','building',(703.7,759.5,746.3,1009.8),'dorm',9.0),
]
def find(cls, bb):
    best=None
    for o in cl[cls]:
        b=bbox(o['pts'])
        if all(abs(b[i]-bb[i])<1.0 for i in range(4)): 
            if best is None or len(o['pts'])>len(best['pts']): best=o
    assert best, (cls,bb); return best
buildings=[]
for lab,cls,bb,typ,h in SRC:
    o=find(cls,bb); p=poly(o['pts'])
    w=(bb[2]-bb[0])*S; d=(bb[3]-bb[1])*S
    buildings.append({'id':lab,'name':EXPL[lab],'type':typ,'footprint':p,'size_m':[round(w,1),round(d,1)],'height_m':h})
# point/underground objects (no closed outline on the plan): marker only
POINTS = [('8',(311.8,340)),('8',(750,190)),('9',(499,610)),('11',(386,602)),('12',(324,360)),('12',(766,374)),('12',(765,605)),('12',(765,657)),('12',(482,448))]
points=[{'id':l,'name':EXPL[l],'pos':M(p)} for l,p in POINTS]
# ТКО (waste) pads and sports grounds as zones
zones=[
 {'id':'TKO-1','name':'Площадка ТКО','polygon':rect(313,376,322,400)},
 {'id':'TKO-2','name':'Площадка ТКО','polygon':rect(433,335,453,342)},
 {'id':'TKO-3','name':'Площадка ТКО','polygon':rect(370,822,392,829)},
 {'id':'SPORT-1','name':'Спортивная площадка','polygon':rect(500,1043,590,1068)},
 {'id':'REST','name':'Площадка для отдыха','polygon':rect(600,1043,680,1068)},
 {'id':'SPORT-2','name':'Спортивная площадка','polygon':rect(690,1043,770,1068)},
 {'id':'RES-11','name':'Ограждённая площадка резервуаров 11','polygon':rect(358.6,571.4,416.3,632.6)},
]
# ---- curbs (road / pavement edges) -------------------------------------
curbs=[]
for o in cl['curb']:
    p=poly(o['pts'])
    if len(p)>=2: curbs.append(p)
# ---- plot boundary & fences --------------------------------------------
boundary = poly([(275.9,110.7),(776.4,110.7),(779.9,1146.8),(276.0,1131.9)])
fences = {
 'perimeter': [
   poly([(268,175),(268,1075)]),                      # west (between the two gates)
   poly([(334,188),(560,188),(560,178),(778,178)]),   # north (east of КПП 10.1)
   poly([(778,178),(778,1080)]),                      # east
   poly([(340,1072),(778,1080)]),                     # south (east of КПП 10.2)
   poly([(268,175),(298,175)]), poly([(268,1075),(298,1075)]),  # gate returns to КПП
 ],
 'internal': [
   poly([(455,700),(760,700),(760,710),(778,710)]),   # residential zone, north side
   poly([(413,695),(413,1073)]),                      # residential zone, west side
   poly([(358.6,571.4),(416.3,571.4),(416.3,632.6),(358.6,632.6),(358.6,571.4)]),  # reservoirs 11
 ],
 'gates': [
   {'id':'G-10.1','name':'Ворота КПП №1','polygon':rect(268,171,276,188)},
   {'id':'G-10.2','name':'Ворота КПП №2','polygon':rect(268,1057,276,1075)},
 ]}
# ---- parking inside the fence, by КПП 10.1: two perpendicular rows on a one-way aisle ----
PITCH=7.0857                      # 2.5 m
NROW=dict(x0=364.8, n=23, y_aisle=227.8, y_out=212.5)    # north row: aisle edge south, outer kerb north
SROW=dict(x0=334.0, n=26, y_aisle=250.0, y_out=265.3)    # south row: aisle edge north, outer kerb south
def row_stalls(r): 
    out=[]
    for i in range(r['n']):
        x=r['x0']+PITCH*i; out.append(poly([(x,r['y_aisle']),(x+PITCH,r['y_aisle']),(x+PITCH,r['y_out']),(x,r['y_out'])]))
    return out
def row_lines(r): return [poly([(r['x0']+PITCH*i,r['y_aisle']),(r['x0']+PITCH*i,r['y_out'])]) for i in range(r['n']+1)]
SHIFT=6                              # carports moved 6 stalls towards АБК-1 (east)
A_N=(SHIFT, SHIFT+11); A_S=(SHIFT, SHIFT+16)     # covered stalls (zone A) per row, [from, to)
ns, ss = row_stalls(NROW), row_stalls(SROW)
XN0=NROW['x0']+PITCH*A_N[0]; XN1=NROW['x0']+PITCH*A_N[1]; XS0=SROW['x0']+PITCH*A_S[0]; XS1=SROW['x0']+PITCH*A_S[1]
# truck/guest parking outside the fence (north strip, 19 angled 45° stalls) — marking only
TP=18.0; truck_lines=[poly([(387.6+TP*i,165.3),(415.44+TP*i,137.16)]) for i in range(20)]
parking={
 'name':'Парковка у КПП 10.1 (внутри ограждения), два ряда перпендикулярных мест вдоль одностороннего проезда',
 'aisle':rect(319.6,227.8,563.3,250.0),
 'lot':rect(319.6,212.5,563.3,265.3),
 'stall_lines':row_lines(NROW)+row_lines(SROW),
 'rows':[{'id':'N','stalls':NROW['n'],'depth_m':round((NROW['y_aisle']-NROW['y_out'])*S,2)},{'id':'S','stalls':SROW['n'],'depth_m':round((SROW['y_out']-SROW['y_aisle'])*S,2)}],
 'aisle_width_m':round((SROW['y_aisle']-NROW['y_aisle'])*S,2),
 'zones':[
  {'id':'P-A','name':'Зона A — навесы с двух сторон проезда (сдвинуты на 6 мест к АБК-1)','stalls':ns[A_N[0]:A_N[1]]+ss[A_S[0]:A_S[1]],'covered':True},
  {'id':'P-B','name':'Зона B — открытая, отделена габионами','stalls':ns[:A_N[0]]+ns[A_N[1]:]+ss[:A_S[0]]+ss[A_S[1]:],'covered':False},
 ],
 'truck_parking':{'name':'Стоянка за ограждением (косые места)','stall_lines':truck_lines}}
# carports: one roof per row over zone A; 4 m at the aisle edge, 2 m at the outer kerb
def cols(r, x0, x1, y, step=2):
    xs=[]; x=x0
    while x<=x1+0.01: xs.append(M((x,y))); x+=PITCH*step
    if math.dist(xs[-1], M((x1,y)))>0.3: xs.append(M((x1,y)))
    return xs
carports=[
 {'id':'CP-N','name':'Навес, северный ряд (зона A, места %d–%d)'%(A_N[0]+1,A_N[1]),
  'roof':poly([(XN0,NROW['y_aisle']+1.0),(XN0,NROW['y_out']-1.0),(XN1,NROW['y_out']-1.0),(XN1,NROW['y_aisle']+1.0)]),
  'roof_height_front_m':4.0,'roof_height_back_m':2.0,'roof_thickness_m':0.12,'column_size_m':0.15,
  'columns_front':cols(NROW,XN0,XN1,NROW['y_aisle']),'columns_back':cols(NROW,XN0,XN1,NROW['y_out']),
  'note':'Односкатный стальной навес: 4 м у проезда, 2 м по дальнему краю; стойки через 2 места (5 м) по линиям разметки'},
 {'id':'CP-S','name':'Навес, южный ряд (зона A, места %d–%d)'%(A_S[0]+1,A_S[1]),
  'roof':poly([(XS0,SROW['y_out']+1.0),(XS0,SROW['y_aisle']-1.0),(XS1,SROW['y_aisle']-1.0),(XS1,SROW['y_out']+1.0)]),
  'roof_height_front_m':2.0,'roof_height_back_m':4.0,'roof_thickness_m':0.12,'column_size_m':0.15,
  'columns_front':cols(SROW,XS0,XS1,SROW['y_out']),'columns_back':cols(SROW,XS0,XS1,SROW['y_aisle']),
  'note':'Односкатный стальной навес: 4 м у проезда, 2 м по дальнему краю; стойки через 2 места (5 м) по линиям разметки'},
]
# gabion walls on both ends of the covered zone in each row (across the stall, aisle stays open)
gabions=[]
for gid,x,r,side in [('GB-N-W',XN0,NROW,'западный'),('GB-N-E',XN1,NROW,'восточный'),('GB-S-W',XS0,SROW,'западный'),('GB-S-E',XS1,SROW,'восточный')]:
    a=M((x,r['y_out'])); b=M((x,r['y_aisle'])); L=math.dist(a,b)
    gabions.append({'id':gid,'name':'Габионная стенка, %s торец навеса (%s ряд)'%(side,'северный' if 'N' in gid else 'южный'),
      'line':[a,b],'box_m':[1.0,0.3,0.6],'tiers':1,'count':int(round(L/1.0)),'length_m':round(L,2),
      'fill':'средний камень 70–150 мм, сетка сварная оцинкованная',
      'note':'Коробы 1000×600 (длина×высота), толщина 300 мм принята; по линии разметки на границе зон, проезд не перекрывается'})
site={
 'meta':{'title':'Жилой городок АО «НЭПТ» — схема генплана','source':'Civil 3D PDF (лист A2), векторная выгрузка',
   'units':'m','scale_m_per_pt':round(S,5),'scale_note':'масштаб листа 1:1000 (1 pt = 0,3528 м); проверено по шагу мест 2,5 м, глубине места 5,4 м и ширине проезда 7,8 м',
   'axes':'X — восток (вправо по листу), Y — север (вверх по листу); ось севера на листе отклонена, не учитывалась',
   'origin_pdf_pt':[round(TX0,2),round(TY1,2)],
   'texture':{'file':'textures/plan.jpg','x0':0,'y0':0,'x1':round((TX1-TX0)*S,3),'y1':round((TY1-TY0)*S,3)}},
 'boundary':boundary,'buildings':buildings,'points':points,'zones':zones,'curbs':curbs,'fences':fences,
 'parking':parking,'carports':carports,'gabions':gabions}
json.dump(site, open(OUT,'w'), ensure_ascii=False, indent=1)
print('buildings',len(buildings),'curbs',len(curbs),'plot',M((276,1147)),M((780,110)),'gabion len',L)
