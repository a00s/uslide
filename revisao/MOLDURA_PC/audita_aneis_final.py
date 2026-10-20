from pathlib import Path
import zipfile,json,hashlib,xml.etree.ElementTree as ET,re
import numpy as np,trimesh,manifold3d as md
P=Path(__file__).resolve().parent;final=P.parents[1]/'FINAL_K1C/U-Slide_K1C_FINAL.3mf';seed=P.parents[1]/'HISTORICO/U-Slide_K1C_TPU_antes_moldura_PC.3mf'
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
def read(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  a=ET.fromstring(z.read('3D/3dmodel.model'));meshes={int(o.get('id')):ET.tostring(o.find('m:mesh',ns)) for o in a.findall('m:resources/m:object',ns)}
  return meshes,ET.fromstring(z.read('Metadata/model_settings.config')),json.loads(z.read('Metadata/project_settings.config'))
a,_,_=read(seed);b,cfg,settings=read(final);assert set(b)=={1,2,3,4,5};assert all(a[i]==b[i] for i in [1,2,3])
metadata={int(o.get('id')):{v.get('key'):v.get('value') for v in o.findall('metadata')} for o in cfg.findall('object')}
assert metadata[4]['enable_support']=='0' and metadata[5]['enable_support']=='1'
assert metadata[4]['layer_height']=='0.2' and metadata[5]['layer_height']=='0.16'
plates=cfg.findall('plate');assert len(plates)==2
native=json.loads(Path('/tmp/uslide_aneis_final/result.json').read_text());assert native['return_code']==0 and len(native['sliced_plates'])==2
sliced=[]
for i,material,temp,bed in [(1,'TPU',230,35),(2,'PC',260,100)]:
 lines=Path(f'/tmp/uslide_aneis_final/plate_{i}.gcode').read_text().splitlines();text='\n'.join(lines)
 tools=sorted(set(s for s in lines if re.fullmatch(r'T\d+',s)));assert tools==['T0']
 assert f'START_PRINT EXTRUDER_TEMP={temp} BED_TEMP={bed}' in text
 pos={k:0. for k in 'XYZ'};points=[];mode='';features={}
 for line in lines:
  if line.startswith(';TYPE:'):mode=line[6:]
  if not re.match(r'G[01] ',line):continue
  vals={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?\d*\.?\d+)',line.split(';')[0])}
  for k in 'XYZ':
   if k in vals:pos[k]=vals[k]
  if vals.get('E',0)>0:
   points.append([pos[k] for k in 'XYZ']);features[mode]=features.get(mode,0)+vals['E']
 pts=np.array(points);assert pts[:,:2].min()>=0 and pts[:,:2].max()<=220
 assert (sum(v for k,v in features.items() if k.startswith('Support'))>0)==(i==2)
 sliced.append({'plate':i,'material':material,'nozzle_C':temp,'bed_C':bed,'tools':tools,'extrusion_bounds_mm':[pts.min(0).tolist(),pts.max(0).tolist()],'statistics':[s for s in lines if s.startswith(('; total filament used [g]','; estimated printing time (normal mode)'))]})
def solid(path):
 m=trimesh.load(path);assert m.is_watertight;s=md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)));assert s.status()==md.Error.NoError;return s
base=solid(P/'Base_PC_aneis_montada.stl');top=solid(P/'Retentor_PC_aneis_montado.stl');body=solid(P.parent/'SELAGEM/U-Slide_selado.stl')
assert len(base.decompose())==1 and len(top.decompose())==1
slide=md.Manifold.cube([76.2,25.4,.9]).translate([-38.1,-12.7,-.9]);cover=md.Manifold.cube([60,24,.13]).translate([-30,-12,.4])
collisions={name:abs((x^y).volume()) for name,x,y in [('base_TPU',base,body),('retainer_TPU',top,body),('base_slide',base,slide),('retainer_cover',top,cover),('base_retainer',base,top)]};assert max(collisions.values())<1e-5
# Check nominal contact by a tiny trial displacement, not by empty volume overlap.
areas={}
for side in [-1,1]:
 region=md.Manifold.cube([18,35,20]).translate([(-42 if side<0 else 24),-10,-5])
 trial=top.translate([0,0,-.001])^region
 areas[str(side)]={'well_rim_mm2':(trial^body).volume()/.001,'cover_pad_mm2':(trial^cover).volume()/.001}
 assert min(areas[str(side)].values())>1
# No retainer crossing central objective area; rings stop at original front face.
center=md.Manifold.cube([50.399,25.4,15]).translate([-25.1995,-12.7,.54]);assert abs((top^center).volume())<1e-6
for side in [-1,1]:
 # At well heights, PC front must not extend inward past original well plane x=+-30.
 front=md.Manifold.cube([20,17.7,3]).translate([(-30 if side<0 else 10),-5,9.9])
 assert abs((top^front).volume())<1e-6
report={'final_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'objects':5,'plates':2,'TPU_and_original_rings_unchanged':True,'PC_parts':'handling base + D-shaped annular retainer','native_slicing':native,'sliced':sliced,'nominal_collision_volumes_mm3':collisions,'nominal_contact_area_estimates_mm2':areas,'central_objective_region_clear':True,'ring_front_not_beyond_original_well_face':True,'hardware':'2 M3x8 screws and 2 M3 nuts','physical_print_or_seal_test':False,'microscope_specific_clearance_verified':False,'limitation':'Prototype CAD and slicer verification only; pressure, PC creep, glass strength and actual leakage require physical trial.'}
(P/'verificacao_aneis_final.json').write_text(json.dumps(report,indent=2))
water=P.parent/'SELAGEM/verificacao_liquido.json';d=json.loads(water.read_text());d['final_artifact_audit']={'sha256':report['final_sha256'],'objects':5,'plates':2,'TPU_body_preserved':True,'actual_native_slicer_run_verified':True,'report':'../MOLDURA_PC/verificacao_aneis_final.json'};water.write_text(json.dumps(d,indent=2))
print(json.dumps(report,indent=2))
