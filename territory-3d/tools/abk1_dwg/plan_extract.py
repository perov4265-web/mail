import ezdxf, collections, json, math
from ezdxf import bbox
doc=ezdxf.readfile('abk2.dxf'); msp=doc.modelspace(); cache=bbox.Cache()
PX0,PY0,PX1,PY1=1910619,325541,1954194,340171   # plan outline (mm)
def inplan(b,m=300): return b.extmin.x>=PX0-m and b.extmax.x<=PX1+m and b.extmin.y>=PY0-m and b.extmax.y<=PY1+m
out=collections.defaultdict(list)
for e in msp:
    try: b=bbox.extents([e],cache=cache,fast=True)
    except Exception: continue
    if not b.has_data or not inplan(b): continue
    t=e.dxftype(); lay=e.dxf.layer
    if t=='LWPOLYLINE':
        pts=[(round(p[0]-PX0),round(p[1]-PY0)) for p in e.get_points('xy')]
        out[lay].append({'t':'PL','pts':pts,'closed':e.closed,'w':round(e.dxf.const_width or 0)})
    elif t=='LINE':
        out[lay].append({'t':'L','pts':[(round(e.dxf.start.x-PX0),round(e.dxf.start.y-PY0)),(round(e.dxf.end.x-PX0),round(e.dxf.end.y-PY0))]})
    elif t=='ARC':
        out[lay].append({'t':'ARC','c':(round(e.dxf.center.x-PX0),round(e.dxf.center.y-PY0)),'r':round(e.dxf.radius),'a':(round(e.dxf.start_angle),round(e.dxf.end_angle))})
    elif t=='CIRCLE':
        out[lay].append({'t':'C','c':(round(e.dxf.center.x-PX0),round(e.dxf.center.y-PY0)),'r':round(e.dxf.radius)})
    elif t=='INSERT':
        out[lay].append({'t':'INS','name':e.dxf.name,'p':(round(e.dxf.insert.x-PX0),round(e.dxf.insert.y-PY0)),'rot':round(e.dxf.rotation),'bb':[round(b.extmin.x-PX0),round(b.extmin.y-PY0),round(b.extmax.x-PX0),round(b.extmax.y-PY0)]})
    elif t in ('TEXT','MTEXT'):
        txt=e.dxf.text if t=='TEXT' else e.plain_text()
        out[lay].append({'t':'TX','s':txt.strip()[:40],'p':(round(e.dxf.insert.x-PX0),round(e.dxf.insert.y-PY0))})
json.dump(out,open('plan_entities.json','w'),ensure_ascii=False)
for lay,items in out.items():
    print('==',lay,len(items), collections.Counter(i['t'] for i in items))
    for i in items[:6]: print('   ',i)
