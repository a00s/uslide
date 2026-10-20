from pathlib import Path
import json,zipfile,hashlib,xml.etree.ElementTree as ET
import trimesh,numpy as np,manifold3d as md
here=Path(__file__).resolve().parent
final=here.parents[1]/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
with zipfile.ZipFile(final) as z:
 assert z.testzip() is None
 model=ET.fromstring(z.read('3D/3dmodel.model'));objects=model.findall('./m:resources/m:object',ns)
 obj=model.find('./m:resources/m:object[@id="1"]',ns)
 vs=np.array([[float(v.attrib[k]) for k in ('x','y','z')] for v in obj.findall('./m:mesh/m:vertices/m:vertex',ns)])
 fs=np.array([[int(f.attrib[k]) for k in ('v1','v2','v3')] for f in obj.findall('./m:mesh/m:triangles/m:triangle',ns)])
 cfg=json.loads(z.read('Metadata/project_settings.config'))
 instances=ET.fromstring(z.read('Metadata/model_settings.config')).findall('./plate/model_instance')
 printed=trimesh.Trimesh(vs,fs,process=False)
 source=trimesh.load(here/'U-Slide_para_imprimir.stl')
 assert np.allclose(vs,source.vertices,atol=1e-6) and np.array_equal(fs,source.faces)
 assert printed.is_watertight and len(printed.split())==1
 assert len(objects)==len(instances)==3
 assert cfg['printer_settings_id']=='Creality K1C 0.4 nozzle'
 assert cfg['layer_height']=='0.1' and cfg['initial_layer_print_height']=='0.2'
 assert cfg['enable_support']=='0' and cfg['wall_generator']=='arachne'
 assert cfg['filament_type']==['TPU']
 for obj in objects:
  p=np.array([[float(v.attrib[k]) for k in ('x','y','z')] for v in obj.findall('./m:mesh/m:vertices/m:vertex',ns)])
  assert np.all(p[:,:2].min(0)+110>=0) and np.all(p[:,:2].max(0)+110<=220)
report_path=here/'verificacao_liquido.json';report=json.loads(report_path.read_text())
assert report['cover_glass_mm']==[60,24,.13]
assert report['integrated_support_count']==6
assert all(r['no_escape'] and r['connected'] for r in report['results'] if r['gap_mm']==0 and r['fill_height_mm']<=9)
assert all(not r['no_escape'] for r in report['results'] if r['gap_mm']>0 or r['fill_height_mm']>10)
assert report['cleaned_print_vs_design_difference_mm3']<.0001
report['final_artifact_audit']={'file':str(final.resolve()),'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'object_count':len(objects),'print_body_watertight':bool(printed.is_watertight),'print_body_connected_components':len(printed.split()),'final_body_matches_verified_print_source':True,'layer_height_mm':float(cfg['layer_height']),'automatic_support':False,'integrated_cut_supports':6,'wall_generator':cfg['wall_generator'],'actual_slicer_preview_verified':False,'physical_seal_verified':False}
report_path.write_text(json.dumps(report,indent=2))
print(json.dumps(report['final_artifact_audit'],indent=2))
print('FINAL folder:',[p.name for p in final.parent.iterdir()])
