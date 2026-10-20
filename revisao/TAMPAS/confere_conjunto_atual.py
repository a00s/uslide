from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E,numpy as np,trimesh,manifold3d as md
P=Path(__file__).resolve().parent
root=P.parents[1]
def load(p):
 m=trimesh.load(p);return m,md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)))
body,b=load(P.parent/'SELAGEM/U-Slide_selado.stl')
clips=[]
for side in ['esquerdo','direito']:
 clips.append(load(P.parent/f'CLIPES_LATERAIS/Clipe_U_{side}_montado.stl'))
with zipfile.ZipFile(root/'FINAL_K1C/U-Slide_K1C_FINAL.3mf') as z:
 ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
 r=E.fromstring(z.read('3D/3dmodel.model'));f=json.loads(z.read('Metadata/project_settings.config'))
 result={'TPU_intersection_note':'Intentional retention-rib contact; see tampas_info.json for shell-only clearance.','clip_source':'CLIPES_LATERAIS (current square flush exterior)','sides':{},'profile':{k:f.get(k) for k in ['nozzle_temperature','hot_plate_temp','filament_flow_ratio','filament_retraction_length']}}
 for oid,label in [(4,'esquerda'),(6,'direita')]:
  m,s=load(P/f'Tampa_{label}_montada.stl');printed,_=load(P/f'Tampa_{label}_imprimir.stl')
  o=r.find(f"m:resources/m:object[@id='{oid}']",ns)
  component=o.find('m:components/m:component',ns)
  if component is not None:
   path=component.get('{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path').lstrip('/')
   sub=E.fromstring(z.read(path));o=sub.find('m:resources/m:object',ns)
  v=np.array([[float(q.get(c)) for c in 'xyz'] for q in o.findall('m:mesh/m:vertices/m:vertex',ns)])
  from scipy.spatial import cKDTree
  expected=printed.vertices-printed.bounds.mean(axis=0)
  actual=v-(v.min(axis=0)+v.max(axis=0))/2
  deviation=max(cKDTree(expected).query(actual)[0].max(),cKDTree(actual).query(expected)[0].max())
  result['sides'][label]={'watertight':bool(m.is_watertight),'TPU_intersection_mm3':abs((s^b).volume()),'clips_intersection_mm3':sum(abs((s^c).volume()) for _,c in clips),'vertical_clearance_to_clips_mm':float(m.bounds[0,2]-max(cm.bounds[1,2] for cm,_ in clips)),'mounted_z_mm':m.bounds[:,2].tolist(),'native_3mf_geometry_matches_STL':bool(deviation<.0001),'native_3mf_max_vertex_deviation_mm':float(deviation)}
(P/'conferencia_conjunto_atual.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
