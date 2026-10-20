from pathlib import Path
import json,numpy as np,trimesh,manifold3d as md
from shapely.geometry import shape,Polygon
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent;S=P.parent/'SELAGEM'
old=shape(json.loads((P/'canal_U_anterior.json').read_text()));new=shape(json.loads((P/'camara_D.json').read_text()))
delta=new.difference(old);added=md.Manifold()
for poly in getattr(delta,'geoms',[delta]):
 if poly.area<.000001:continue
 poly=orient(poly,1);added=added+md.CrossSection([list(poly.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in poly.interiors]).extrude(.4)
# Preserve original well-liquid preview; extend only the newly opened flat region.
# Read committed U geometry, so rerunning is idempotent.
import subprocess
for h in [1,5,9]:
 raw=subprocess.check_output(['git','show',f'HEAD:revisao/SELAGEM/liquido_{h}mm.stl'])
 import io
 m=trimesh.load(io.BytesIO(raw),file_type='stl')
 s=md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)))+added
 a=s.to_mesh();trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=False).export(S/f'liquido_{h}mm.stl')
info=json.loads((S/'verificacao_liquido.json').read_text());info['chamber_D_note']='Liquid meshes updated for visual preview only. Previous containment calculations refer to U revision, not recomputed for D.'
(S/'verificacao_liquido.json').write_text(json.dumps(info,indent=2))
