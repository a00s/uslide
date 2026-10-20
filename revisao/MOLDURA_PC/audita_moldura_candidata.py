from pathlib import Path
import json,re,hashlib,zipfile,xml.etree.ElementTree as ET
import numpy as np,trimesh,manifold3d as md
P=Path(__file__).resolve().parent
candidate=P/'Moldura_PC_CANDIDATO.3mf';g=Path('/tmp/uslide_frame_check/plate_2.gcode');lines=g.read_text().splitlines()
mode='';pos={'X':0.,'Y':0.,'Z':0.};used={};points=[];tools=[]
for line in lines:
 if line.startswith(';TYPE:'):mode=line[6:]
 if re.fullmatch(r'T\d+',line):tools.append(line)
 if not re.match(r'G[01] ',line):continue
 vals={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?\d*\.?\d+)',line.split(';')[0])}
 for k in 'XYZ':
  if k in vals:pos[k]=vals[k]
 if vals.get('E',0)>0:
  used[mode]=used.get(mode,0)+vals['E'];points.append([pos[k] for k in 'XYZ'])
assert set(tools)=={'T0'}
pts=np.array(points);assert pts[:,:2].min()>=0 and pts[:,:2].max()<=220
# TPU geometry must be precisely unchanged, not inferred from filenames.
base=P.parents[1]/'HISTORICO/U-Slide_K1C_TPU_antes_moldura_PC.3mf'
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
def objects(path):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  a=ET.fromstring(z.read('3D/3dmodel.model'))
  return {int(o.get('id')):ET.tostring(o.find('m:mesh',ns)) for o in a.findall('m:resources/m:object',ns)}
a=objects(base);b=objects(candidate)
assert all(a[i]==b[i] for i in [1,2,3])
report={'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'final_not_replaced':True,'TPU_and_rings_meshes_unchanged':True,'native_slice_result':json.loads(Path('/tmp/uslide_frame_check/result.json').read_text()),'physical_tools':sorted(set(tools)),'extrusion_bounds_mm':[pts.min(0).tolist(),pts.max(0).tolist()],'extruded_filament_mm_by_feature':used,'support_filament_fraction':sum(v for k,v in used.items() if k.startswith('Support'))/sum(used.values()),'gcode_statistics':[s for s in lines if s.startswith(('; total filament used [g]','; estimated printing time (normal mode)'))],'unsupported_claims':['Microscope fit is unverified: objective diameter and available stage clearance missing.','PC spring forces are linear estimates, not measurements.','Whole-frame nonlinear contact and long-term PC creep not modeled.','No physical print or assembly test performed.'],'remaining_required_before_final':['objective and stage clearance confirmation','refine nominal contact clearances and root transition','verify new pressure leaves in layer preview']}
(P/'verificacao_moldura_candidata.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
