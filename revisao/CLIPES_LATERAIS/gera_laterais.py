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
# Rounded transitions in the cutout remove sharp stress concentrators.
clearance=clearance.buffer(.6,quad_segs=16).buffer(-.6,quad_segs=16)
footprint=box(26,-12.7,40.1,12.7).difference(clearance)
# Broad jaws span exactly the slide width, with a ramp at the entering edge.
profile=Polygon([(26,-1.54),(40.1,-1.54),(40.1,-.9),(27.2,-.9),(26,-1.12)])
bottom=md.CrossSection([list(orient(profile,1).exterior.coords)[:-1]]).extrude(26.2).transform([[1,0,0,0],[0,0,1,-12.7],[0,1,0,0]])
wall=cube(38.5,40.1,-12.7,13.5,-1.54,2.12)
upper=md.Manifold()
for poly in getattr(footprint,'geoms',[footprint]):
 if poly.area>.01: upper=upper+ext(poly,.52,1.60)
# Beveled underside at the entry: gradual insertion rather than a sharp ledge.
wedge=md.CrossSection([[(25.99,.519),(27.3,.519),(25.99,.82)]]).extrude(26).transform([[1,0,0,0],[0,0,1,-13],[0,1,0,0]])
upper=upper-wedge
# Close the thin rear side with a solid external wall, OUTSIDE the glass.
# No raised annulus or shoulder remains: well clearance is the upper contour.
external_wall=cube(26,40.1,12.7,13.5,-1.54,2.12)
# Flush square exterior: no projecting tab, stair or corner bevel.
s=(bottom+wall+upper+external_wall).simplify(0.001)
for side,label in [(1,'direito'),(-1,'esquerdo')]:
 part=s if side==1 else s.mirror([1,0,0])
 m=save(part,f'Clipe_U_{label}_montado.stl')
 # External rear wall flat on bed. The sandwich slot grows vertically.
 printed=part.transform([[1,0,0,-side*35.4],[0,0,1,-.29],[0,-1,0,13.5]])
 save(printed,f'Clipe_U_{label}_imprimir.stl')
(P/'clipes_u_info.json').write_text(json.dumps({'design':'two broad clamps with closed external rear wall and upper well contour; no raised ring','nominal_stack_mm':[1.43,1.46],'minimum_jaw_gap_mm':1.42,'preload_mm':[.01,.04],'under_slide_mm':.64,'slide_width_mm':25.4,'total_width_mm':26.2,'upper_plate_thickness_mm':1.6,'back_wall_mm':1.6,'external_wall_y_mm':[12.7,13.5],'mounted_max_z_mm':2.12,'raised_ring':False,'external_tip_x_abs_mm':40.1,'assembled_length_mm':80.2,'handle_beyond_wall_mm':0,'outer_corner_bevel_mm':0,'assembly':'Cold assembly; remove antennas. Insert from short end, no forcing glass. Rear wall stays outside slide edge.','print':'rear external wall on bed, no supports, no brim','physical_fit_validated':False},indent=2))
print('Generated closed rear side, upper contour only, wall-down printing.')
