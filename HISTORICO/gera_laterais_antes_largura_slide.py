from pathlib import Path
import json,numpy as np,trimesh,manifold3d as md
from shapely.geometry import Point,box,Polygon
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent

def ext(poly,z,h):
 p=orient(poly,1)
 return md.CrossSection([list(p.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in p.interiors]).extrude(h).translate([0,0,z])
def cube(x0,x1,y0,y1,z0,z1):return md.Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
def save(s,name):
 a=s.to_mesh();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=True)
 assert m.is_watertight and len(m.split())==1,(name,s.status(),len(m.split()))
 m.export(P/name);return m
# Right end fitting, mounted: exterior half-ring is open toward the channel.
# Its split is deliberate: a closed ring could not slide over the well.
ring=Point(33,5.325).buffer(6,resolution=80).difference(Point(33,5.325).buffer(4.8,resolution=80)).intersection(box(33,-10,45,20))
annulus=ext(ring,2.2,.64)
# Broad bottom jaw, only at the end, with a ramp at the entering nose.
profile=Polygon([(28.5,-1.54),(39.3,-1.54),(39.3,-.9),(29.4,-.9),(28.5,-1.1)])
# Extrude profile along Y, preserving mounted Z.
bottom=md.CrossSection([list(orient(profile,1).exterior.coords)[:-1]]).extrude(13.5).transform([[1,0,0,0],[0,0,1,-1],[0,1,0,0]])
wall=cube(38.5,39.3,-1,12.5,-1.54,2.84)
# Spring tongue rests only on the rear corner of the cover, away from channel.
# Nose has extra clearance; minimum free gap is 1.40 mm for nominal 1.43-1.46 stack.
upper_profile=Polygon([(28, .78),(28.8,.50),(30,.50),(38.6,.65),(38.6,1.29),(30,1.14),(28.8,1.14),(28,1.42)])
upper=md.CrossSection([list(orient(upper_profile,1).exterior.coords)[:-1]]).extrude(1.8).transform([[1,0,0,0],[0,0,1,10.4],[0,1,0,0]])
# Rounded external handle, rigidly attached to back wall and bottom jaw.
handlepoly=box(38.8,.3,44.8,11.2).buffer(.8,quad_segs=12).buffer(-.8,quad_segs=12)
handle=ext(handlepoly,-1.54,1.28)
s=(bottom+wall+upper+annulus+handle).simplify(0.00001)
for side,label in [(1,'direito'),(-1,'esquerdo')]:
 part=s if side==1 else s.mirror([1,0,0])
 m=save(part,f'Clipe_U_{label}_montado.stl')
 # Broad lower jaw on bed. Add removable supports in slicer, never built-in.
 printed=part.translate([-side*36.4,-5.75,1.54])
 save(printed,f'Clipe_U_{label}_imprimir.stl')
(P/'clipes_u_info.json').write_text(json.dumps({'design':'two mirrored end handles, open low half-ring, lower jaw and upper cover spring tongue; no base','nominal_stack_mm':[1.43,1.46],'minimum_jaw_gap_mm':1.40,'preload_mm':[.03,.06],'ring_inner_radius_mm':4.8,'ring_outer_radius_mm':6,'ring_z_mm':[2.2,2.84],'under_slide_mm':.64,'upper_tongue_width_mm':1.8,'assembly':'Cold assembly. Remove TPU antennas first. Gently lift tongue, slide fitting onto short end, lower tongue. Do not force glass. Ring remains open toward channel.','print':'lower jaw on bed; supports not modeled; add removable slicer supports under upper tongue and half-ring','physical_fit_validated':False},indent=2))
print('Generated two mirrored side handles with half-ring and direct sandwich clamp.')
