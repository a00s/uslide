from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,json,re,hashlib
import numpy as np,trimesh,manifold3d as md
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
p=json.loads((HERE/'parametros_clips.json').read_text());fea=json.loads((HERE/'flexao_clips.json').read_text())
def meshpath(path):
 m=trimesh.load(path);assert isinstance(m,trimesh.Trimesh) and m.is_watertight
 return m
def solid(m):
 s=md.Manifold(md.Mesh(np.asarray(m.vertices,np.float32),np.asarray(m.faces,np.uint32)))
 assert s.status()==md.Error.NoError
 return s
# Nominal, watertight assembly is the CAD reference; the earlier verified cut
# print differs by <0.0001 mm3. Recompute fluid directly (avoid STL slivers).
body=meshpath(HERE.parent/'SELAGEM/U-Slide_selado.stl');bs=solid(body);cover=solid(meshpath(HERE.parent/'SELAGEM/cobrevidro.stl'))
domain=md.Manifold.cube([82,30,10.2]).translate([-41,-15,-1.2]);bottom=md.Manifold.cube([76.2,25.4,.9]).translate([-38.1,-12.7,-.9])
water=None
for c in (domain-bs-bottom-cover).decompose():
 mm=c.to_mesh();tm=trimesh.Trimesh(mm.vert_properties[:,:3],mm.tri_verts,process=False)
 if tm.contains([[-33,5.325,.6]])[0]:water=c
assert water is not None and water.status()==md.Error.NoError

rows=[]
for t in [.8,.9,1.]:
 glass=md.Manifold.cube([76.2,25.4,t]).translate([-38.1,-12.7,-t])
 for side in ['esquerdo','direito']:
  m=meshpath(HERE/f'Clipe_PC_montado_{side}_{t:.1f}.stl');s=solid(m)
  bvol=max(0,(s^bs).volume());gvol=max(0,(s^glass).volume());cvol=max(0,(s^cover).volume());wvol=max(0,(s^water).volume())
  assert max(bvol,gvol,cvol,wvol)<.0001
  # Contact checks around both rounded anvils, near the high toe edge.
  xx=-27.5999 if side=='esquerdo' else 27.5999
  ys=np.linspace(4.7,5.55,171)
  qp=np.c_[np.full(len(ys),xx),ys,np.full(len(ys),p['foot_roof_contact_height_mm'])]
  closest,dists,_=trimesh.proximity.closest_point(m,qp)
  top_contact=float(dists.min())
  qg=np.c_[np.full(len(ys),xx),ys,np.full(len(ys),-t)]
  _,dists,_=trimesh.proximity.closest_point(m,qg);bottom_contact=float(dists.min())
  assert top_contact<.02 and bottom_contact<.02
  bounds=m.bounds
  assert bounds[1,2]<10 and (bounds[1,0]<=-25.19 or bounds[0,0]>=25.19)
  rows.append({'slide_thickness_mm':t,'side':side,'TPU_overlap_mm3':bvol,'bottom_glass_overlap_mm3':gvol,'coverslip_overlap_mm3':cvol,'liquid_overlap_mm3':wvol,'upper_contact_gap_mm':top_contact,'lower_contact_gap_mm':bottom_contact,'bounds_mm':bounds.tolist()})
print('6 assembled fits checked; contact distances max:',max(max(x['upper_contact_gap_mm'],x['lower_contact_gap_mm']) for x in rows))
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
final=ROOT/'FINAL_K1C/U-Slide_K1C_FINAL.3mf';seed=ROOT/'HISTORICO/U-Slide_K1C_TPU_antes_moldura_PC.3mf'
with zipfile.ZipFile(final) as z,zipfile.ZipFile(seed) as old:
 assert z.testzip() is None
 r=ET.fromstring(z.read('3D/3dmodel.model'));r0=ET.fromstring(old.read('3D/3dmodel.model'))
 def get_mesh(r,oid):
  obj=r.find(f'./m:resources/m:object[@id="{oid}"]',ns)
  v=np.array([[float(q.get(k)) for k in 'xyz'] for q in obj.findall('./m:mesh/m:vertices/m:vertex',ns)])
  f=np.array([[int(q.get(k)) for k in ['v1','v2','v3']] for q in obj.findall('./m:mesh/m:triangles/m:triangle',ns)])
  return v,f
 for oid in [1,2,3]:
  v,f=get_mesh(r,oid);v0,f0=get_mesh(r0,oid);assert np.array_equal(v,v0) and np.array_equal(f,f0)
 pc_source=meshpath(HERE/'Clipe_PC_imprimir.stl')
 def canonical_triangles(v,f):
  return sorted(tuple(sorted(tuple(np.round(q,5)) for q in v[tri])) for tri in f)
 pc_tree=cKDTree(pc_source.vertices)
 pc_canonical=sorted(tuple(sorted(tri)) for tri in pc_source.faces)
 for oid in [4,5]:
  v,f=get_mesh(r,oid)
  vv=v.copy();vv[:,0]+=(25 if oid==4 else -25)
  dist,idx=pc_tree.query(vv)
  assert dist.max()<1e-5 and sorted(tuple(sorted(tri)) for tri in idx[f])==pc_canonical
  m=trimesh.Trimesh(v,f,process=False);assert m.is_watertight and len(m.split())==1
  assert abs(v[:,2].min())<1e-5 and abs(v[:,2].max()-2.4)<1e-5
  assert (v[:,:2].min(0)+110>=0).all() and (v[:,:2].max(0)+110<=220).all()
 cfg=json.loads(z.read('Metadata/project_settings.config'));plates=ET.fromstring(z.read('Metadata/model_settings.config')).findall('plate')
 assert len(plates)==2 and cfg['filament_type']==['TPU','PC']
 assert len(cfg['inherits_group'])==len(cfg['different_settings_to_system'])==4
 assert cfg['nozzle_temperature']==['230','260'] and cfg['hot_plate_temp']==['35','100']
 result=json.loads(Path('/tmp/uslide_all_check/result.json').read_text());assert result['return_code']==0 and len(result['sliced_plates'])==2
 slices=[]
 for i in [1,2]:
  g=Path(f'/tmp/uslide_all_check/plate_{i}.gcode').read_text()
  assert re.findall(r'^T\d+',g,re.M)==['T0']
  assert '; filament_type = TPU;PC' in g
  target='EXTRUDER_TEMP=230 BED_TEMP=35' if i==1 else 'EXTRUDER_TEMP=260 BED_TEMP=100'
  assert 'START_PRINT '+target in g
  grams=[float(x) for x in re.search(r'^; filament used \[g\] = (.*)$',g,re.M).group(1).split(',')]
  assert grams[i-1]>0 and grams[2-i]==0
  # Audit ALL emitted extrusion endpoints in actual machine coordinates.
  xyz=np.zeros(3);pts=[];relative_e=True
  for line in g.splitlines():
   line=line.split(';')[0].strip()
   if not re.match(r'^G[0123]\s',line):continue
   nums={k:float(v) for k,v in re.findall(r'([XYZEF])([-+]?(?:\d+(?:\.\d*)?|\.\d+))',line)}
   for a,k in enumerate('XYZ'):
    if k in nums:xyz[a]=nums[k]
   if nums.get('E',0)>0:pts.append(xyz.copy())
  pts=np.array(pts);assert np.all(pts[:,:2]>=0) and np.all(pts[:,:2]<=220)
  support=bool(re.search(r'^;TYPE:Support',g,re.M))
  assert not support
  slices.append({'plate':i,'filament':'TPU' if i==1 else 'PC','used_filament_g':grams[i-1],'layers':int(re.search(r'^; total layer number: (\d+)',g,re.M).group(1)),'extrusion_bounds_mm':[pts.min(0).tolist(),pts.max(0).tolist()],'support_toolpaths':support,'physical_tools':['T0'],'gcode_sha256':hashlib.sha256(g.encode()).hexdigest()})
report={'clip_count':2,'same_geometry_both_clips':True,'print_orientation':'C profile laid flat, 2.4 mm print height','print_supports':False,'optical_window_x_mm':[-25.2,25.2],'fits':rows,'linear_PC_estimate':fea,'TPU_and_original_rings_mesh_preserved':True,'slice_validation':slices,'native_project_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'physical_print_or_clamp_test_completed':False,'notes':'Linear elastic/contact geometry estimate only. No measured PC stiffness, creep, thermal bond or glass strength test. CLI logs toolpath outside during multi-plate pre-export validation; all emitted extrusion endpoints audited inside the 220x220 mm bed.'}
(HERE/'verificacao_clips_PC.json').write_text(json.dumps(report,indent=2))
water_report=HERE.parent/'SELAGEM/verificacao_liquido.json'
if water_report.exists():
 wr=json.loads(water_report.read_text());audit=wr.setdefault('final_artifact_audit',{})
 audit.update({'sha256':report['native_project_sha256'],'object_count':5,'plate_count':2,'actual_native_slicer_run_verified':True,'slicer_report':'../MOLDURA_PC/verificacao_clips_PC.json','PC_clip_addition_changes_TPU_or_rings':False})
 water_report.write_text(json.dumps(wr,indent=2))
print(json.dumps(slices,indent=2))
