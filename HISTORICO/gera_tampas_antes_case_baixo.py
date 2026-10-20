from pathlib import Path
import numpy as np,trimesh,manifold3d as md,json
from shapely.geometry import Point,box,Polygon
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent

def extrude(p,h):
 p=orient(p,1);return md.CrossSection([list(p.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in p.interiors]).extrude(h)
def cube(x,y,z,dx,dy,dz):return md.Manifold.cube([dx,dy,dz]).translate([x,y,z])
def dshape(r,front):return Point(0,0).buffer(r,resolution=64).intersection(box(-10,-10,front,10))
# Print upside down: closed roof on bed, open skirt upward. No bridges/support.
outer=dshape(6.75,4.25);inner=dshape(5.85,3.45)
cap=extrude(outer,3.2)-extrude(inner,2.5).translate([0,0,.8])
# Back notch clears the retainer's rear crosshead; an upper lip remains.
cap=cap-cube(-3.15,3.6,1.4,6.3,8,2.0)
# Protected lateral vent with a roof-attached baffle (air turns around its ends).
cap=cap-cube(-7.2,-.3,.8,1.65,.6,.4)
cap=cap+cube(-5.25,-1.35,.72,.6,2.7,.78)
# Three light landing pads rest on the case annulus, not the wet well interior.
for angle in [140,220,290]:
 x=4.8*np.cos(np.radians(angle));y=4.8*np.sin(np.radians(angle))
 cap=cap+cube(x-.35,y-.35,.72,.7,.7,.88)
# Flat rear handle, coplanar with roof, for lifting without pinching the well.
cap=cap+cube(-1.6,5.0,0,3.2,5.0,.8)
def export(s,p):
 a=s.to_mesh();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=True)
 assert m.is_watertight and len(m.split())==1
 m.export(p);return m
for side,label in [(-1,'esquerda'),(1,'direita')]:
 s=cap if side<0 else cap.mirror([1,0,0])
 export(s,P/f'Tampa_{label}_imprimir.stl')
 # Invert about X for use; mirror Y first so rear notch and handle stay rear.
 mounted=s.mirror([0,1,0]).rotate([180,0,0]).translate([side*33,5.325,13])
 export(mounted,P/f'Tampa_{label}_montada.stl')
# CAD fit against body and retainer in assembly coordinates.
def load(p):
 m=trimesh.load(p);return md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)))
body=load(P.parent/'SELAGEM/U-Slide_selado.stl');retainer=load(P.parent/'MOLDURA_PC/Retentor_PC_aneis_montado.stl')
fits={}
for label in ['esquerda','direita']:
 s=load(P/f'Tampa_{label}_montada.stl');fits[label]={'TPU_overlap_mm3':abs((s^body).volume()),'case_overlap_mm3':abs((s^retainer).volume())}
(P/'tampas_info.json').write_text(json.dumps({'material':'eSUN TPU-LW','roof_mm':.8,'outer_radius_mm':6.75,'inner_radius_mm':5.85,'radial_case_clearance_mm':.45,'mounted_top_z_mm':13,'vent_width_height_mm':[.6,.4],'internal_baffle':True,'back_case_clearance_notch':True,'retraction_mm':0,'print_one_at_time':True,'fit':fits,'gas_exchange_or_evaporation_validated':False},indent=2));print(json.dumps(fits,indent=2))
