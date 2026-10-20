from pathlib import Path
import re,json,collections
src=Path('revisao/SEQUENCIAL/base_costura_traseira.gcode')
x=y=z=0.;layer=0;feature='';rows=[];groups=collections.defaultdict(list)
for line in src.read_text().splitlines():
 if line.startswith(';Z:'):layer=float(line[3:])
 if line.startswith(';TYPE:'):feature=line[6:]
 code=line.split(';')[0].strip();cmd=code.split()[0] if code else ''
 if cmd not in ('G1','G2','G3'):continue
 p={k:float(v) for k,v in re.findall(r'([XYZEFIJ])(-?[\d.]+)',code)}
 old=(x,y,z);x=p.get('X',x);y=p.get('Y',y);z=p.get('Z',z)
 if p.get('E',0)>0 and any(k in p for k in ['X','Y']):
  if layer>.44 and 81<x<85 and 111<y<120:
   rows.append({'z':layer,'type':feature,'start':old,'end':(x,y,z),'gcode':code});groups[layer].append(feature)
Path('revisao/SELAGEM/triangulo_trajetos.json').write_text(json.dumps(rows,indent=2))
print('Features near toe:',dict(collections.Counter(r['type'] for r in rows)))
for layer in [.84,1.,1.4,2.04,3.,4.04,5.,6.04,7.]:
 closest=min(groups,key=lambda z:abs(z-layer));print(closest,dict(collections.Counter(groups[closest])))
