from pathlib import Path
import json,re,numpy as np
from shapely.geometry import shape,Polygon,box,LineString,mapping
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent
original=shape(json.loads((P/'canal_original.json').read_text()))
def borders(y):
 cut=original.intersection(LineString([(-60,y),(60,y)]));parts=list(cut.geoms) if hasattr(cut,'geoms') else [cut]
 right=[g for g in parts if g.bounds[0]>0][0]
 return right.bounds[0],right.bounds[2]
x0,x1=borders(1.0);u0,u1=borders(1.05)
def bez(x,slope,endx):
 q=np.array([[x,1.],[x-slope*.6,.4],[endx,-.2],[endx,-.8]])
 return np.array([((1-t)**3*q[0]+3*(1-t)**2*t*q[1]+3*(1-t)*t*t*q[2]+t**3*q[3]) for t in np.linspace(0,1,33)])
ci=bez(x0,(u0-x0)/.05,20.5);co=bez(x1,(u1-x1)/.05,25.5)
a=np.linspace(0,-np.pi/2,65)
ai=np.column_stack([17+3.5*np.cos(a),-.8+3.5*np.sin(a)])
ao=np.column_stack([17+8.5*np.cos(a),-.8+8.5*np.sin(a)])
mirror=lambda q:q*np.array([-1,1])
pts=np.concatenate([ci,ai,mirror(ai[::-1]),mirror(ci[::-1]),mirror(co),mirror(ao),ao[::-1],co[::-1]])
lower=Polygon(pts).buffer(0)
channel=unary_union([original.intersection(box(-60,1,60,20)),lower])
assert channel.geom_type=='Polygon' and channel.is_valid
# Original file is retained as the exact outline / reference, not overwritten.
s=(P/'base_original_2d.scad').read_text();coords=json.loads(re.search(r'points=(\[.*?\]), paths=',s).group(1));outer=Polygon(coords[:12])
plate=orient(outer.difference(channel),sign=1);assert plate.geom_type=='Polygon' and len(plate.interiors)==1
points=[];paths=[]
for ring in [plate.exterior,*plate.interiors]:
 q=np.asarray(ring.coords)[:-1].round(7).tolist();paths.append(list(range(len(points),len(points)+len(q))));points.extend(q)
(P/'base_arredondada_2d.scad').write_text('// Canal U com curvas concentricas R3.5/R8.5 e largura nominal de 5 mm.\n// Interface com os pocos preservada exatamente para y>=1 mm.\nmodule original_base_2d() { polygon(points='+json.dumps(points)+',paths='+json.dumps(paths)+'); }\n')
(P/'canal_arredondado.json').write_text(json.dumps(mapping(channel)))
p=P/'U-Slide_selado.scad';s=p.read_text().replace('include <base_original_2d.scad>','include <base_arredondada_2d.scad>');p.write_text(s)
print('Curvas internas R3.5 mm, externas R8.5 mm; canal nominal 5 mm; boca dos pocos preservada.')
