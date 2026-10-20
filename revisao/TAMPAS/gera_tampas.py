from pathlib import Path
import numpy as np,trimesh,manifold3d as md,json
from shapely.geometry import Point,box
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent
ROOF=1.2;HEIGHT=9.2;TOP=11.6;RI=4.65;RO=6.7

def extrude(p,h):
 p=orient(p,1);return md.CrossSection([list(p.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in p.interiors]).extrude(h)
def cube(x,y,z,dx,dy,dz):return md.Manifold.cube([dx,dy,dz]).translate([x,y,z])
def dshape(r,front):return Point(0,0).buffer(r,resolution=80).intersection(box(-10,-10,front,10))
# Roof and broad grip on bed. Longer skirt grips well below its rim.
outer=dshape(RO,4.8);inner=dshape(RI,3.15)
cap=extrude(outer,HEIGHT)-extrude(inner,HEIGHT).translate([0,0,ROOF])
# Flared entrance, made as a short loft, guides the soft cap onto the well.
entrance=md.Manifold.batch_hull([extrude(inner,.01).translate([0,0,HEIGHT-.36]),extrude(dshape(4.9,3.4),.01).translate([0,0,HEIGHT])])
cap=cap-entrance
# Clear the full diamond shoe below the well rim.
cap=cap-cube(1.8,-9,1.60,9,18,HEIGHT)
# Protected vent; baffle remains above the rim, away from the wet interior.
cap=cap-cube(-7.2,-.4,1.2,2.9,.8,.6)
cap=cap+cube(-4.6,-1.5,1.15,.55,3,.35)
# Three stops rest on rim, roof 0.4mm above rim.
for angle in [140,220,290]:
 x=4.2*np.cos(np.radians(angle));y=4.2*np.sin(np.radians(angle))
 cap=cap+cube(x-.25,y-.25,1.15,.5,.5,.45)
# Three small compliant axial ribs: 0.05mm nominal radial interference.
ribs=md.Manifold()
for angle in [90,180,270]:
 x=4.7*np.cos(np.radians(angle));y=4.7*np.sin(np.radians(angle))
 main=extrude(Point(x,y).buffer(.25,resolution=24),HEIGHT-2.4).translate([0,0,1.7])
 taper=md.Manifold.batch_hull([extrude(Point(x,y).buffer(.25,resolution=24),.01).translate([0,0,HEIGHT-.71]),extrude(Point(x,y).buffer(.12,resolution=24),.01).translate([0,0,HEIGHT-.15])])
 ribs=ribs+main+taper
cap_without_ribs=cap
cap=cap+ribs
# Wide rear paddle, within the existing assembly width (Ymax13.5).
grip=box(-6,3.5,6,8.1).buffer(.65,quad_segs=16).buffer(-.65,quad_segs=16)
cap=(cap+extrude(grip,ROOF)).simplify(.00001)
def export(s,p):
 a=s.to_mesh();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=False)
 assert m.is_watertight and len(s.decompose())==1
 m.export(p);return m
for side,label in [(-1,'esquerda'),(1,'direita')]:
 s=cap if side<0 else cap.mirror([1,0,0]);export(s,P/f'Tampa_{label}_imprimir.stl')
 mounted=s.mirror([0,1,0]).rotate([180,0,0]).translate([side*33,5.325,TOP]);export(mounted,P/f'Tampa_{label}_montada.stl')
def load(p):
 m=trimesh.load(p);return md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)))
body=load(P.parent/'SELAGEM/U-Slide_selado.stl');retainer=load(P.parent/'CLIPES_LATERAIS/Clipe_U_esquerdo_montado.stl')+load(P.parent/'CLIPES_LATERAIS/Clipe_U_direito_montado.stl')
fits={}
for label in ['esquerda','direita']:
 s=load(P/f'Tampa_{label}_montada.stl')
 base=cap_without_ribs if label=='esquerda' else cap_without_ribs.mirror([1,0,0])
 base=base.mirror([0,1,0]).rotate([180,0,0]).translate([-33 if label=='esquerda' else 33,5.325,TOP])
 fits[label]={'TPU_overlap_including_intended_ribs_mm3':abs((s^body).volume()),'case_overlap_mm3':abs((s^retainer).volume()),'rigid_shell_TPU_overlap_without_ribs_mm3':abs((base^body).volume())}
info={'material':'PLA rigid cap on flexible TPU85A well','roof_mm':ROOF,'outer_radius_mm':RO,'inner_radius_mm':RI,'bore_radial_clearance_mm':.15,'retention_ribs':3,'rib_radial_interference_mm':.05,'rib_diameter_mm':.5,'entry_flare':True,'total_print_height_mm':HEIGHT,'engagement_below_rim_mm':7.6,'mounted_top_z_mm':TOP,'mounted_bottom_z_mm':TOP-HEIGHT,'grip_width_length_mm':[12,4.6],'mounted_ymax_mm':13.425,'mounted_x_abs_max_mm':39.7,'vent_width_height_mm':[.8,.6],'lower_front_shoe_relief':True,'internal_baffle':True,'fit':fits,'physical_retention_not_validated':True,'clip_vertical_clearance_mm':.28}
(P/'tampas_info.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
