from pathlib import Path
import subprocess,io
import json,numpy as np,trimesh,manifold3d as md
P=Path(__file__).resolve().parent
D={};report={}
for label,path in [('antes',P/'TPU_antes_remover_travessa.stl'),('agora',P.parent/'SELAGEM/U-Slide_selado.stl')]:
 m=trimesh.load(path);body=md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)))
 D[label]=[q.tolist() for q in body.slice(.42).to_polygons()];vols={}
 for side,name in [(-1,'esquerdo'),(1,'direito')]:
  x0=30 if side==1 else -30.6
  region=md.Manifold.cube([.6,5,.049]).translate([x0,2.825,.401])
  vols[name]=abs((body^region).volume())
 report[label]=vols
baseline=trimesh.load(io.BytesIO(subprocess.check_output(['git','show','990a72d:revisao/SELAGEM/U-Slide_selado.stl'])),file_type='stl')
base_old=md.Manifold(md.Mesh(np.asarray(baseline.vertices,dtype=np.float32),np.asarray(baseline.faces,dtype=np.uint32)))
base_region=md.Manifold.cube([120,30,.399]).translate([-60,-15,0])
a=base_old^base_region;b=body^base_region
report['restored_floor_vs_original_D_difference_mm3']=abs((a-b).volume())+abs((b-a).volume())
assert report['restored_floor_vs_original_D_difference_mm3']<.00001,report
assert all(v<1e-7 for v in report['agora'].values()),report
(P/'travessa_cortes.json').write_text(json.dumps(D));(P/'travessa_removida_info.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
