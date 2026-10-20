from pathlib import Path
import trimesh,numpy as np,json,manifold3d as md
HERE=Path(__file__).resolve().parent
mesh=trimesh.load(HERE/'U-Slide_selado.stl')
def manifold(mesh):
 return md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
def export(m,path):
 s=m.to_mesh();trimesh.Trimesh(vertices=s.vert_properties[:,:3],faces=s.tri_verts,process=False).export(path)
def asmesh(m):
 s=m.to_mesh();return trimesh.Trimesh(vertices=s.vert_properties[:,:3],faces=s.tri_verts,process=False)
def box(size,center):return md.Manifold.cube(size).translate(np.array(center)-np.array(size)/2)
body=manifold(mesh)
bottom=box([76.2,25.4,.9],[0,0,-.45])
cover_t=.13
cover_top=.4+cover_t
cover=box([60,24,cover_t],[0,0,.4+cover_t/2])
# Verify removal from the REAL print mesh, then use that cleaned print mesh.
printed=manifold(trimesh.load(HERE/'U-Slide_para_imprimir.stl'))
base_slice=body ^ box([120,30,.4],[0,0,.2])
channel_clearance=box([60,24,.4],[0,0,.2])-base_slice
assembly_cut=cover+channel_clearance
cleaned=printed-assembly_cut
cut_difference=(cleaned-body).volume()+(body-cleaned).volume()
assert cut_difference < 0.0001, f'Cut print differs from intended assembly by {cut_difference} mm3'
print('cleaned print difference',cut_difference,'mm3; integrated support volume',(printed-body).volume())
support_added_volume=(printed-body).volume()
body=cleaned
export(body,HERE/'TPU_montado.stl')
print('TPU status',body.status(),'watertight',mesh.is_watertight,'components',len(body.decompose()))
print('glass/TPU overlap', (body^cover).volume())
results=[]
for gap in [0,.02,.12]:
 # A clearance cut ABOVE the fixed coverslip models an unsealed upper lip.
 # Both glasses retain their actual assembly positions; no glass penetrates TPU.
 clearance=box([60,24,gap],[0,0,cover_top+gap/2]) if gap else None
 simulated_body=body-clearance if gap else body
 solids=simulated_body+bottom+cover
 for fill in [1.,5.,9.,10.1]:
  domain=box([82,30,fill+1.2],[0,0,(fill-1.2)/2])
  free=domain-solids
  comps=free.decompose()
  seeds=np.array([[-33,5.325,.6],[33,5.325,.6],[0,-6.825,.2]])
  found=[]
  for c in comps:
   cm=asmesh(c)
   contains=cm.contains(seeds)
   if contains.any():found.append((c,contains))
  row={'gap_mm':gap,'fill_height_mm':fill,'component_count':len(comps),'wet_regions':[]}
  for c,contains in found:
   bb=c.bounding_box(); outside=bb[0]<=-40.999 or bb[3]>=40.999 or bb[1]<=-14.999 or bb[4]>=14.999 or bb[2]<=-1.1999
   row['wet_regions'].append({'volume_mm3':c.volume(),'bounds':list(bb),'contains_reservoirs_and_channel':contains.tolist(),'reaches_exterior':bool(outside)})
   if gap==0 and fill<=9. and all(contains):export(c,HERE/f'liquido_{int(fill)}mm.stl')
  row['no_escape']=bool(found) and all(not r['reaches_exterior'] for r in row['wet_regions'])
  row['connected']=any(all(r['contains_reservoirs_and_channel']) for r in row['wet_regions'])
  results.append(row)
  print('gap',gap,'fill',fill,'components',len(comps),'sealed',row['no_escape'],'connected',row['connected'],[r['contains_reservoirs_and_channel'] for r in row['wet_regions']],flush=True)
report={'method':'Exact polyhedral CSG free-space connected components, not CFD or thermal/adhesion simulation','gap_definition':f'Remove TPU within coverslip XY footprint, from z={cover_top} to z={cover_top}+gap. Both glasses remain fixed.','top_boundary':'Free-space domain capped at liquid fill height; intentionally open reservoir mouths at z=10 mm overflow at fill=10.1 mm.','bottom_glass_mm':[76.2,25.4,.9],'cover_glass_mm':[60,24,cover_t],'base_mm':.4,'integrated_support_count':6,'support_added_volume_mm3':support_added_volume,'cleaned_print_vs_design_difference_mm3':cut_difference,'body_watertight':bool(mesh.is_watertight),'body_components':len(body.decompose()),'body_glass_interference_mm3':(body^cover).volume(),'results':results}
# Thickness sensitivity: a thicker No.1 glass intersects the nominal 0.13 mm
# slot until the TPU conforms during assembly. Do not report that as a fitted test.
report['coverslip_fit_sensitivity']=[]
for thick in [.13,.145,.16]:
 test_glass=box([60,24,thick],[0,0,.4+thick/2])
 report['coverslip_fit_sensitivity'].append({'thickness_mm':thick,'rigid_interference_mm3':max(0,(body^test_glass).volume()),'extra_lip_lift_required_mm':max(0,thick-cover_t),'requires_thermal_or_elastic_adaptation':thick>cover_t})
report['lower_slide_thickness_checks']=[]
for thick in [.8,1.0]:
 glass=box([76.2,25.4,thick],[0,0,-thick/2])
 domain=box([82,30,6.2],[0,0,1.9])
 comps=(domain-body-glass-cover).decompose()
 wet=[c for c in comps if asmesh(c).contains([[-33,5.325,.6]])[0]]
 assert len(wet)==1
 bounds=wet[0].bounding_box()
 sealed=bounds[0]>-40.999 and bounds[3]<40.999 and bounds[1]>-14.999 and bounds[4]<14.999 and bounds[2]>-1.1999
 report['lower_slide_thickness_checks'].append({'thickness_mm':thick,'no_escape':bool(sealed)})
assert all(r['no_escape'] and r['connected'] for r in results if r['gap_mm']==0 and r['fill_height_mm']<=9)
assert all(not r['no_escape'] for r in results if r['gap_mm']>0 or r['fill_height_mm']>10)
assert all(r['no_escape'] for r in report['lower_slide_thickness_checks'])
(HERE/'verificacao_liquido.json').write_text(json.dumps(report,indent=2))
export(bottom,HERE/'vidro_inferior.stl');export(cover,HERE/'cobrevidro.stl')
