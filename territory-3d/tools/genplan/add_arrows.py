import json
cl=json.load(open('../pdf/classes.json')); S=25.4/72; TX0=728*72/200; TY1=(292+2917)*72/200
def M(pt): return [round((pt[0]-TX0)*S,2), round((TY1-pt[1])*S,2)]
site=json.load(open('/home/user/mail/territory-3d/data/site.json'))
arrows=[]
for o in cl['arrow']:
    if not o['fill'] and len(o['pts'])>=2:
        p=[M(q) for q in o['pts']]
        if sum(((p[i][0]-p[i+1][0])**2+(p[i][1]-p[i+1][1])**2)**.5 for i in range(len(p)-1))>1.0: arrows.append(p)
site['traffic_arrows']=arrows
json.dump(site,open('/home/user/mail/territory-3d/data/site.json','w'),ensure_ascii=False,indent=1); print('arrows',len(arrows))
