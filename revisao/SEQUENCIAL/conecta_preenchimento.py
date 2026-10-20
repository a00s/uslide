"""Join nearby concentric fill runs only where a full bead fits the solid base."""
from pathlib import Path
import json,re,math
from shapely.geometry import Polygon,LineString
from shapely.affinity import translate
s=Path('revisao/SELAGEM/base_arredondada_2d.scad').read_text()
pts=json.loads(re.search(r'points=(\[.*?\]),paths=',s).group(1))
paths=json.loads(re.search(r'paths=(\[.*\])\);',s).group(1))
base=translate(Polygon([pts[i] for i in paths[0]],[[pts[i] for i in path] for path in paths[1:]]),110,110)
fill={'Bottom surface','Top surface','Internal solid infill'}
def params(move):return {k:float(v) for k,v in re.findall(r'([XYZEF])(-?[\d.]+)',move)}
def connect(ordered):
 result=[];added=[];length=0.;extra=0.;before=sum(r['phase']==0 for r in ordered)
 for r in ordered:
  if result:
   prev=result[-1];m0=prev['moves'][-1];m1=r['moves'][0]
   if prev['phase']==r['phase']==0 and m0[2]==m1[2] and m0[3] in fill and m1[3] in fill:
    p=params(m0[0]);q=r['start'];a=(p['X'],p['Y']);b=(q['X'],q['Y']);d=math.dist(a,b)
    w=min(float(m0[4]),float(m1[4]));h=.2 if m1[2]==.2 else .08
    safe=base.buffer(-(w/2-.01))
    if d<=1.5 and (d<1e-7 or safe.covers(LineString([a,b]))):
     moves=list(prev['moves'])
     if d>1e-7:
      e=d*(h*(w-h)+math.pi*h*h/4)/(math.pi*1.75**2/4)
      cmd=f'G1 X{b[0]:.5f} Y{b[1]:.5f} Z{q["Z"]:.5f} E{e:.8f} F{min(p["F"],params(m1[0])["F"],900):.3f} ; CONNECTED_FILL'
      moves.append((cmd,m1[1],m1[2],m1[3],str(w)));added.append(cmd);length+=d;extra+=e
     moves.extend(r['moves']);result[-1]={**prev,'moves':moves};continue
  result.append({**r,'moves':list(r['moves'])})
 return result,added,{'base_runs_before':before,'base_runs_after':sum(r['phase']==0 for r in result),'continuous_fill_links':len(added),'added_link_length_mm':length,'added_filament_mm':extra,'maximum_link_mm':1.5,'full_bead_within_base':True}
