import sys, ezdxf, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration
doc=ezdxf.readfile('abk2.dxf'); msp=doc.modelspace()
def ref(e):
    if e.dxftype()=='INSERT': return e.dxf.name
    if e.dxftype()=='DIMENSION': return e.dxf.get('geometry','')
    return None
bad=[e for e in msp if e.dxftype() in ('INSERT','DIMENSION') and (ref(e) or '') not in doc.blocks]
for e in bad: msp.delete_entity(e)
print('dropped refs to missing blocks:', len(bad))
x0,y0,x1,y1=[float(v) for v in sys.argv[1:5]]; out=sys.argv[5]; px=int(sys.argv[6]) if len(sys.argv)>6 else 3000
w=x1-x0; h=y1-y0; dpi=100
fig=plt.figure(figsize=(px/dpi, px*h/w/dpi), dpi=dpi); ax=fig.add_axes([0,0,1,1]); ax.set_axis_off()
ctx=RenderContext(doc); ctx.set_current_layout(msp)
be=MatplotlibBackend(ax)
cfg=Configuration(min_lineweight=0.05, lineweight_scaling=0.3)
Frontend(ctx, be, config=cfg).draw_layout(msp, finalize=False)
ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal')
fig.savefig(out, dpi=dpi, facecolor=ctx.current_layout_properties.background_color); print('saved',out)
