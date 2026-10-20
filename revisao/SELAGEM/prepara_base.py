from pathlib import Path
import trimesh,json,numpy as np
from shapely.geometry import Polygon,mapping
from shapely.geometry.polygon import orient
here=Path(__file__).resolve().parent
mesh=trimesh.load(here.parent/'V3_SAPATO/original_body_K1C.stl')
loops=mesh.section([0,0,1],[0,0,.2]).discrete
polys=sorted([Polygon(p[:,:2]).simplify(.0001,preserve_topology=True) for p in loops],key=lambda p:p.area,reverse=True)
plate=orient(Polygon(polys[0].exterior.coords,[polys[1].exterior.coords]),sign=1)
coords=[];paths=[]
for ring in [plate.exterior,*plate.interiors]:
 p=list(ring.coords)[:-1];paths.append(list(range(len(coords),len(coords)+len(p))));coords.extend([[round(x,6),round(y,6)] for x,y in p])
(here/'base_original_2d.scad').write_text('// Contorno e canal U extraidos da malha original; base nominal plana de 0,4 mm.\nmodule original_base_2d() { polygon(points='+json.dumps(coords)+', paths='+json.dumps(paths)+'); }\n')
(here/'canal_original.json').write_text(json.dumps(mapping(polys[1])))
print('plate outer area',polys[0].area,'channel area',polys[1].area,'vertices',len(coords))
