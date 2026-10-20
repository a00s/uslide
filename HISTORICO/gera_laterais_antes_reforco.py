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
 a=s.to_mesh();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=False)
 assert m.is_watertight,(name,s.status())
 m.export(P/name);return m
# Two full-width end clamps. Upper footprint follows the user's shaded sketch.
# Keep a broad pressure surface, relieved around the well and the U channel.
from shapely.ops import unary_union
import re
source=(P.parent/'SELAGEM/base_arredondada_2d.scad').read_text()
pts=json.loads(re.search(r'points=(\[.*?\]),paths=',source).group(1))
paths=json.loads(re.search(r'paths=(\[.*\])\);',source).group(1))
channel=unary_union([Polygon([pts[i] for i in q]) for q in paths[1:]])
from shapely.affinity import scale
# Smooth clearance around the skirt and shoe; no jagged mesh-derived perimeter.
well=scale(Point(33,5.325).buffer(1,resolution=80),5.25,6.50)
shoe=box(25.0,1.0,33.0,9.65)
channel=unary_union([Polygon([pts[i] for i in q]) for q in paths[1:] if Polygon([pts[i] for i in q]).area>5])
clearance=unary_union([well,shoe,channel.buffer(.35)]).simplify(.005,preserve_topology=True)
# Extend all obstacles toward the entry (inner end) to permit sliding assembly.
from shapely.affinity import translate
clearance=unary_union([translate(clearance,xoff=-d) for d in np.linspace(0,15,61)])
footprint=box(26, -12.7,39.3,12.7).difference(clearance)
# Broad jaws span exactly the slide width, with a ramp at the entering edge.
profile=Polygon([(26,-1.54),(39.3,-1.54),(39.3,-.9),(27.2,-.9),(26,-1.12)])
bottom=md.CrossSection([list(orient(profile,1).exterior.coords)[:-1]]).extrude(25.4).transform([[1,0,0,0],[0,0,1,-12.7],[0,1,0,0]])
wall=cube(38.5,39.3,-12.7,12.7,-1.54,2.84)
upper=md.Manifold()
for poly in getattr(footprint,'geoms',[footprint]):
 if poly.area>.01: upper=upper+ext(poly,.52,.80)
# Beveled underside at the entry: gradual insertion rather than a sharp ledge.
wedge=md.CrossSection([[(25.99,.519),(27.3,.519),(25.99,.82)]]).extrude(26).transform([[1,0,0,0],[0,0,1,-13],[0,1,0,0]])
upper=upper-wedge
ring=Point(33,5.325).buffer(6,resolution=80).difference(Point(33,5.325).buffer(4.8,resolution=80)).intersection(box(33,-10,45,20))
annulus=ext(ring,2.2,.64)
handlepoly=box(38.8,-12.7,44.8,12.7).buffer(.8,quad_segs=12).buffer(-.8,quad_segs=12)
handle=ext(handlepoly,-1.54,1.28)
s=(bottom+wall+upper+annulus+handle).simplify(0.001)
for side,label in [(1,'direito'),(-1,'esquerdo')]:
 part=s if side==1 else s.mirror([1,0,0])
 m=save(part,f'Clipe_U_{label}_montado.stl')
 # Broad lower jaw on bed. Add removable supports in slicer, never built-in.
 printed=part.translate([-side*35.4,0,1.54])
 save(printed,f'Clipe_U_{label}_imprimir.stl')
(P/'clipes_u_info.json').write_text(json.dumps({'design':'two full slide-width 25.4mm end clamps, broad relieved upper plate, half-ring and handle','nominal_stack_mm':[1.43,1.46],'minimum_jaw_gap_mm':1.42,'preload_mm':[.01,.04],'ring_inner_radius_mm':4.8,'ring_outer_radius_mm':6,'ring_z_mm':[2.2,2.84],'under_slide_mm':.64,'jaw_width_mm':25.4,'upper_plate_thickness_mm':.8,'assembly':'Cold assembly. Remove TPU antennas first. Gently open jaws and slide fitting onto short end. Do not force glass. Ring remains open toward channel.','print':'lower jaw on bed; supports not modeled; add removable slicer supports under upper plate and half-ring','physical_fit_validated':False},indent=2))
print('Generated two mirrored side handles with half-ring and direct sandwich clamp.')
