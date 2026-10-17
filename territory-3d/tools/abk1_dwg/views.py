import ezdxf, collections, math
from ezdxf.math import BoundingBox
doc=ezdxf.readfile('abk2.dxf'); msp=doc.modelspace()
from ezdxf import bbox
# per-entity bboxes (fast path: skip DIMENSION/HATCH complexity by using ezdxf.bbox with cache)
cache=bbox.Cache()
items=[]
for e in msp:
    try:
        b=bbox.extents([e], cache=cache, fast=True)
    except Exception as ex: continue
    if not b.has_data: continue
    items.append((e, b))
print('bboxed', len(items))
# grid-cluster on 2 m cells, merge connected cells
CELL=3000.0
cells=collections.defaultdict(list)
for i,(e,b) in enumerate(items):
    x0,y0=b.extmin.x,b.extmin.y; x1,y1=b.extmax.x,b.extmax.y
    if (x1-x0)>150000 or (y1-y0)>150000: continue   # skip giant frame/sheet entities
    for cx in range(int(x0//CELL), int(x1//CELL)+1):
        for cy in range(int(y0//CELL), int(y1//CELL)+1): cells[(cx,cy)].append(i)
# union-find over neighbouring occupied cells
par={c:c for c in cells}
def f(c):
    while par[c]!=c: par[c]=par[par[c]]; c=par[c]
    return c
for (cx,cy) in list(cells):
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            n=(cx+dx,cy+dy)
            if n in cells: par[f((cx,cy))]=f(n)
groups=collections.defaultdict(set)
for c,ids in cells.items(): groups[f(c)].update(ids)
views=[]
for g,ids in groups.items():
    bb=BoundingBox()
    for i in ids: bb.extend(items[i][1])
    ents=[items[i][0] for i in ids]
    texts=[e.dxf.text for e in ents if e.dxftype()=='TEXT'][:12]+[e.text[:40] for e in ents if e.dxftype()=='MTEXT'][:6]
    lay=collections.Counter(e.dxf.layer for e in ents).most_common(5)
    views.append((len(ids), bb, lay, texts))
views.sort(key=lambda v:-v[0])
for n,bb,lay,texts in views[:40]:
    print('N=%d  x %.0f..%.0f  y %.0f..%.0f  size %.1f x %.1f m'%(n,bb.extmin.x,bb.extmax.x,bb.extmin.y,bb.extmax.y,(bb.extmax.x-bb.extmin.x)/1000,(bb.extmax.y-bb.extmin.y)/1000))
    print('    layers',lay); print('    texts',[t for t in texts if t.strip()][:10])
