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
 offset=WALL*2**.5
 inner=md.Manifold.batch_hull([extrude(dshape(3.9,2.4),9.72).translate([0,0,.39]),diamond(3.0,BOTTOM+offset,PEAK-offset,2.1,3.0)])
 # Full coverslip insertion zone stays open: base top to roof underside.
 slot=md.Manifold.cube([60,40,GAP+.002]).translate([3,-20,BASE-.001])
 return outer-inner-slot
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
 a=s.to_mesh();m=trimesh.Trimesh(np.array(a.vert_properties[:,:3]),np.array(a.tri_verts),process=True);m.export(path)
 print(path.name,'components',len(m.split()),'watertight',m.is_watertight)
export(body,P/'U-Slide_selado.stl');export(body,P/'TPU_montado.stl');export(supports,P/'apoios_cortar.stl');export(body+supports,P/'U-Slide_para_imprimir.stl')
(P/'sapato_losango_info.json').write_text(json.dumps({'base_mm':BASE,'coverslip_slot_mm':GAP,'assumed_glass_mm':.13,'slot_roof_z':BOTTOM,'diamond_peak_z':PEAK,'wall_nominal_mm':WALL,'supports':2,'supports_from':'build plate through U opening','support_release_gap_mm':.16,'assembly':'slide, TPU base, coverslip, upper TPU shoe; heat bond after assembly','seal_verified':False},indent=2))
