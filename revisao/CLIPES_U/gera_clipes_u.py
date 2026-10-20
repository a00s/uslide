"""Two identical low U spring clips directly on glass/TPU/coverslip, no cradle."""
from pathlib import Path
import json,numpy as np,trimesh,manifold3d as md
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent
points=[(10,-1.38),(14.2,-1.38),(14.2,1.06),(13.15,1.06),(11.9,.96),(10.75,.94),(10,1.12),(10,.64),(10.75,.46),(11.9,.48),(13.15,.58),(13.15,-.9),(10.6,-.9),(10,-.98)]
profile=orient(Polygon(points).buffer(.12,quad_segs=12).buffer(-.12,quad_segs=12),1)
clip=md.CrossSection([list(profile.exterior.coords)[:-1]]).extrude(5).transform([[0,0,1,-2.5],[1,0,0,0],[0,1,0,0]])
def export(s,p):
 a=s.to_mesh();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=True);assert m.is_watertight and len(m.split())==1;m.export(p);return m
def load(p):
 m=trimesh.load(p);return md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)))
body=load(P.parent/'SELAGEM/U-Slide_selado.stl');cover=md.Manifold.cube([60,24,.13]).translate([-30,-12,.4]);slide=md.Manifold.cube([76.2,25.4,.9]).translate([-38.1,-12.7,-.9]);fits={}
for x,label in [(-27,'esquerdo'),(27,'direito')]:
 s=clip.translate([x,0,0]);m=export(s,P/f'Clipe_U_{label}_montado.stl')
 # Side face on bed: U profile lies in XY, extruded width goes along Z.
 printed=clip.transform([[0,1,0,-12.1],[0,0,1,1.38],[1,0,0,2.5]])
 export(printed,P/f'Clipe_U_{label}_imprimir.stl')
 fits[label]={'TPU_intersection_mm3':abs((s^body).volume()),'slide_intersection_mm3':abs((s^slide).volume()),'cover_preload_overlap_mm3':abs((s^cover).volume())}
report={'design':'two identical closed-mouth U clips on rear long edge of sandwich; no PLA base','material':'PLA','nominal_slide_mm':.9,'TPU_mm':.4,'coverslip_mm':[.13,.16],'nominal_stack_mm':[1.43,1.46],'unloaded_min_jaw_gap_mm':1.36,'nominal_interference_mm':[.07,.10],'clip_width_mm':5,'lower_jaw_mm':.48,'upper_jaw_mm':.48,'mounted_under_slide_mm':.48,'contact_centers_x_mm':[-27,27],'slide_rear_edge_y_mm':12.7,'inner_root_y_mm':13.15,'mount':'slide clips onto the rear long edge; one near each coverslip end; do not grip reservoirs','print':'on side, U profile on bed, no supports or brim','source_case_reference':'../CASE_REFERENCIA/medidas_case.json','case_reference_used_as_base':False,'fit':fits,'physical_preload_or_microscope_clearance_validated':False,'limitations':'nominal dimensions only; unmeasured slide thickness changes clamping; do not force coverslip'}
(P/'clipes_u_info.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
