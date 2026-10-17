import sys, json, collections
import pdfplumber
pdf = pdfplumber.open(sys.argv[1]); p = pdf.pages[0]
X0,Y0,X1,Y1 = 240, 95, 800, 1165
def inplan(o): return o['x0']>=X0 and o['x1']<=X1 and o['top']>=Y0 and o['bottom']<=Y1
def col(c): 
    v=c.get('stroking_color') if c.get('stroke') else c.get('non_stroking_color')
    if v is None: return None
    if isinstance(v,(int,float)): v=(v,v,v)
    return tuple(round(float(x),3) for x in v)
PURPLE=(0.408,0.196,0.424); DRED=(0.361,0.0,0.071); MAG=(0.867,0.0,0.867); GRAY=(0.451,0.451,0.451)
classes=collections.defaultdict(list)
for o in p.curves+p.lines+p.rects:
    if not inplan(o): continue
    c=col(o); lw=round(o.get('linewidth',0),2)
    if o['object_type']=='line': pts=[(o['x0'],o['top']),(o['x1'],o['bottom'])] if True else None
    pts=o.get('pts')
    if o['object_type']=='line':
        # pdfplumber line pts
        pts=o.get('pts')
    pts=[(round(x,2),round(y,2)) for x,y in pts]
    key=None
    if c==PURPLE and lw>=1.0: key='building'
    elif c==DRED: key='curb'
    elif c==MAG: key='arrow'
    elif c==GRAY and lw==0.48: key='hatch'
    elif c==(0,0,0) and lw in (0.84,1.08,0.72): key='black_thick'
    elif c==(0,0,0) and lw==0.6: key='black_06'
    elif c==(0,0,0) and lw==0.24: key='black_024'
    elif c==(1,1,1): key='white'
    elif c==(0,0,0) and lw==0: key='black_0'
    else: key='other_%s_%s'%(c,lw)
    classes[key].append({'t':o['object_type'],'fill':bool(o.get('fill')),'pts':pts})
for k,v in sorted(classes.items(), key=lambda kv:-len(kv[1])): print(k,len(v))
json.dump(classes, open(sys.argv[2],'w'))
# SVG preview of key classes
colors={'building':'#8a2be2','curb':'#c00','black_thick':'#000','black_06':'#0a0','white':'#09f','hatch':'#ddd','black_024':'#f80','arrow':'#f0f'}
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%d %d %d %d" width="1120" height="2140"><rect x="%d" y="%d" width="%d" height="%d" fill="#fff"/>'%(X0,Y0,X1-X0,Y1-Y0,X0,Y0,X1-X0,Y1-Y0)]
for k in ['hatch','white','black_024','black_06','curb','black_thick','building']:
    for o in classes.get(k,[]):
        d='M'+' L'.join('%s %s'%pt for pt in o['pts'])
        svg.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s"/>'%(d,colors[k],0.3 if k in('hatch','white') else 0.8))
svg.append('</svg>')
open(sys.argv[3],'w').write('\n'.join(svg))
