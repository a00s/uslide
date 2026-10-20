"""Printable hollow diamond shoe with coverslip slot and table-based supports."""
from pathlib import Path
import json,re,numpy as np,trimesh,manifold3d as md
from shapely.geometry import Polygon,Point,box,shape
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent
BASE=.4;GAP=.4;BOTTOM=BASE+GAP;WALL=.6;HALFW=3.6;PEAK=BOTTOM+2*HALFW

def extrude(poly,h):
 poly=orient(poly,1)
 return md.CrossSection([list(poly.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in poly.interiors]).extrude(h)
def dshape(r,front):return Point(0,0).buffer(r,resolution=64).intersection(box(-10,-10,front,10))
def diamond(half,bottom,peak,rx,ry):
 mid=(bottom+peak)/2
 poly=Polygon([(0,bottom),(half,mid),(0,peak),(-half,mid)])
 prism=extrude(poly,40).transform([[0,0,1,-20],[1,0,0,0],[0,1,0,0]])
 from shapely.affinity import scale,translate
 ellipse=translate(scale(Point(0,0).buffer(1,resolution=64),rx,ry),4.8,0)
 return prism ^ extrude(ellipse,12)
def shoe():
 outer=md.Manifold.batch_hull([extrude(dshape(4.5,3),9.601).translate([0,0,.399]),diamond(HALFW,BOTTOM,PEAK,2.7,3.6)])
 # Build the cavity from inward offsets of the ACTUAL outer hull sections.
 # Hulling independent inner primitives used to leave a thick triangular nose.
 # Here 0.60 mm is the horizontal shell thickness; on inclined faces the
 # normal thickness is smaller, so this is a printing prototype, not a seal proof.
 layers=np.r_[.38,np.linspace(.3995,9.999,121),10.1]
 directions=np.column_stack([np.cos(np.linspace(0,2*np.pi,384,endpoint=False)),np.sin(np.linspace(0,2*np.pi,384,endpoint=False))])
 rings=[]
 for z in layers:
  sections=outer.slice(float(np.clip(z,.39901,9.999))).to_polygons()
  poly=Polygon(max(sections,key=len)).buffer(-WALL,join_style=2)
  q=np.asarray(orient(poly,1).exterior.coords)[:-1];edge=np.roll(q,-1,axis=0)-q
  # Ray / convex-polygon intersection, centered inside the reservoir.
  points=[]
  for direction in directions:
   den=direction[0]*edge[:,1]-direction[1]*edge[:,0]
   good=np.abs(den)>1e-10
   t=np.full(len(edge),np.inf);u=np.full(len(edge),np.inf)
   t[good]=(q[good,0]*edge[good,1]-q[good,1]*edge[good,0])/den[good]
   u[good]=(q[good,0]*direction[1]-q[good,1]*direction[0])/den[good]
   valid=good&(t>0)&(u>=-1e-7)&(u<=1+1e-7)
   distance=float(t[valid].min());points.append([distance*direction[0],distance*direction[1],float(z)])
  rings.extend(points)
 n=len(directions);verts=np.array(rings,dtype=np.float32);faces=[]
 for level in range(len(layers)-1):
  for j in range(n):
   a=level*n+j;b=level*n+(j+1)%n;c=(level+1)*n+j;d=(level+1)*n+(j+1)%n
   faces.extend([[a,b,c],[b,d,c]])
 for j in range(1,n-1):faces.extend([[0,j+1,j],[(len(layers)-1)*n,(len(layers)-1)*n+j,(len(layers)-1)*n+j+1]])
 inner=md.Manifold(md.Mesh(verts,np.array(faces,dtype=np.uint32)))
 # Cavity extends past both reservoir ends so no cap is retained.
 # Full coverslip insertion zone stays open: base top to roof underside.
 # Clear the entire transverse lower D-wall, not only the coverslip side.
 # The old x=3 start left a 0.6mm bar (x=2.4..3) across the well front.
 slot=md.Manifold.cube([60,40,GAP+.002]).translate([2.35,-20,BASE-.001])
 # Continuous dry-side skirt, replacing the two isolated buttresses.
 # Oval foot stays on the slide; front edge stops 0.3 mm before coverslip.
 from shapely.affinity import scale
 foot=scale(Point(0,0).buffer(1,resolution=64),5.0,6.2)
 flare=md.Manifold.batch_hull([
  extrude(foot,.12).translate([0,0,.24]),
  extrude(Point(0,0).buffer(4.55,resolution=64),.12).translate([0,0,2.0])])
 dry_zone=md.Manifold.cube([22.7,40,4]).translate([-20,-20,0])
 # Keep a simple open core; do not change the existing liquid cavity.
 core=extrude(Point(0,0).buffer(3.8,resolution=64),4).translate([0,0,-.1])
 skirt=(flare ^ dry_zone)-core-inner
 reinforced=(outer-inner-slot)+skirt
 return reinforced

s=(P/'base_arredondada_2d.scad').read_text();pts=json.loads(re.search(r'points=(\[.*?\]),paths=',s).group(1));paths=json.loads(re.search(r'paths=(\[.*\])\);',s).group(1))
plate=Polygon([pts[i] for i in paths[0]],[[pts[i] for i in path] for path in paths[1:]])
body=extrude(plate,BASE)
for side in [-1,1]:body=body+shoe().rotate([0,0,0 if side<0 else 180]).translate([side*33,5.325,0])
supports=md.Manifold()
# Feet lie wholly within the channel opening, not on the TPU sheet.
# Each narrow blade reaches the lower diamond point with a 0.16-mm release gap.
for side in [-1,1]:
 local=md.Manifold.cube([.65,1.0,.2]).translate([6.72,-.5,0])
 local=local+md.Manifold.cube([.35,.5,.44]).translate([6.90,-.25,.2])
 supports=supports+local.rotate([0,0,0 if side<0 else 180]).translate([side*33,5.325,0])
def export(s,path):
 s=s.simplify(.00001)
 assert s.status()==md.Error.NoError
 a=s.to_mesh();m=trimesh.Trimesh(np.array(a.vert_properties[:,:3]),np.array(a.tri_verts),process=False);assert m.is_watertight and len(m.faces)>0;m.export(path)
 print(path.name,'components',len(s.decompose()),'watertight',m.is_watertight)
export(body,P/'U-Slide_selado.stl');export(body,P/'TPU_montado.stl');export(supports,P/'apoios_cortar.stl');export(body+supports,P/'U-Slide_para_imprimir.stl')
(P/'sapato_losango_info.json').write_text(json.dumps({'base_mm':BASE,'coverslip_slot_mm':GAP,'assumed_glass_mm':.13,'slot_roof_z':BOTTOM,'lower_crossbar_removed':True,'slot_start_local_x_mm':2.35,'diamond_peak_z':PEAK,'wall_horizontal_mm':WALL,'wall_method':'inset actual outer sections, loft at 0.08-mm intervals','dry_root_reinforcement':{'type':'continuous oval dry-side skirt','foot_half_x_mm':5.0,'foot_half_y_mm':6.2,'top_z_mm':2.12,'coverslip_edge_setback_mm':.3,'cavity_preserved':True},'supports':2,'supports_from':'build plate through U opening','support_release_gap_mm':.16,'assembly':'slide, TPU base, coverslip, upper TPU shoe; heat bond after assembly','seal_verified':False},indent=2))
