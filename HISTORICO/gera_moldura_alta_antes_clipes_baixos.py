"""Two-piece PC handling cradle with annular well retainers and two integral split press-in pins.
Nominal geometric assembly only; heat bonding happens before PC installation.
"""
from pathlib import Path
import json
import manifold3d as md
import numpy as np,trimesh
P=Path(__file__).resolve().parent
CASE_MATERIAL="PLA" # prototype; set PC for the final material
BEAD_R=2.55 if CASE_MATERIAL=="PLA" else 2.60

def box(x0,y0,z0,x1,y1,z1):return md.Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
def cyl(x,y,z,r,h):return md.Manifold.cylinder(h,r,r,64).translate([x,y,z])
def union(ss):
 s=ss[0]
 for a in ss[1:]:s=s+a
 return s

def export(s,path):
 assert s.status()==md.Error.NoError
 a=s.to_mesh();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=True);assert m.is_watertight
 m.export(path);return m

# Lower tray supports only the edges of the slide, leaving an open optical window.
# Nominal lower glass bottom=-0.9; no layer is inserted between glass and TPU.
base=union([box(-39.4,-14.2,-4.1,39.4,-11.2,-.9),box(-39.4,11.2,-4.1,39.4,14.2,-.9),box(-39.4,-14.2,-4.1,-35.8,14.2,-.9),box(35.8,-14.2,-4.1,39.4,14.2,-.9)])
base=base+box(-39.4,-14.2,-.9,39.4,-12.9,-.15)+box(-39.4,12.9,-.9,39.4,14.2,-.15)
# Corner stops only at dry outside corners; leave central end slots for TPU antennas.
for side in [-1,1]:
 for y in [-12.9,12.9]:
  x0,x1=(-39.4,-38.3) if side<0 else (38.3,39.4)
  base=base+box(x0,y-.8,-.9,x1,y+.8,-.15)
# Approved cradle, local rear holes changed to integral-pin sockets.
for x in [-33.,33.]:
 base=base+box(x-4,12.,-4.1,x+4,20.5,-.9)
 base=base-cyl(x,17.,-4.2,2.5,4.)  # 5.0 mm throat
 base=base-cyl(x,17.,-4.2,2.8,1.15)  # underside relief up to z=-3.05

# Upper PC part: 2 open annuli over well rims, connected by a low rear rail.
# Annular bore radius=4.05 > wet well radius3.9: no deliberate contact with fluid.
# Exterior opening remains accessible to pipette and does not cap the wells.
upper=[box(-37.,13.0,.53,37.,15.5,2.13)]
for side in [-1,1]:
 x=side*33.
 # D profile follows the front wall, growing only outward/backward.
 local_outer=cyl(0,0,10.,5.4,1.4)^box(-7,-7,9.9,3.,7,11.5)
 local_inner=cyl(0,0,9.9,4.05,1.7)^box(-7,-7,9.8,2.55,7,11.7)
 ring=(local_outer-local_inner).rotate([0,0,0 if side<0 else 180]).translate([x,5.325,0])
 upper.append(ring)
 # Twin uprights outside the rear glass edge; top crosshead reaches ring rear arc.
 upper.extend([box(x-2.7,11.8,.53,x+2.7,14.0,10.2),box(x-2.7,9.3,10.,x+2.7,14.0,11.4)])
 # Broad pad on a verified TPU-backed coverglass area, beside each reservoir.
 # The web stays behind y=9.1 and clears the shoe shoulder.
 cx=side*26.4
 # Small X-direction flexures preload only TPU-backed coverglass areas.
 if side<0:
  upper.append(box(-34.,10.3,.8,-31.4,14.,2.13))
  upper.append(box(-31.6,10.0,.8,-25.2,11.8,1.4))
 else:
  upper.append(box(31.4,10.3,.8,34.,14.,2.13))
  upper.append(box(25.2,10.0,.8,31.6,11.8,1.4))
 upper.append(box(cx-.85,10.0,.50,cx+.85,11.8,1.01))
top=union(upper)
for x in [-33.,33.]:
 # Existing U guides align both parts before the pins enter their holes.
 top=top+box(x-5.65,15.5,.53,x+5.65,22.15,2.13)
 top=top+box(x-5.65,15.8,-3.7,x-4.25,22.15,1.)
 top=top+box(x+4.25,15.8,-3.7,x+5.65,22.15,1.)
 top=top+box(x-5.65,20.75,-3.7,x+5.65,22.15,1.)
 # C-section pin: tapered lead-in, small retaining bead in underside relief.
 pin=cyl(x,17.,-3.45,2.4,4.35)
 pin=pin+md.Manifold.cylinder(.45,2.1,BEAD_R,64).translate([x,17.,-3.9])
 pin=pin+cyl(x,17.,-3.45,BEAD_R,.4)
 pin=pin-cyl(x,17.,-4.,1.6,5.3)
 pin=pin-box(x-.9,17.,-4.,x+.9,20.5,1.3)
 top=top+pin
 # Keep the split and hollow open into the root: no screw, nut or insert.
 top=top-cyl(x,17.,-4.,1.6,5.3)
 top=top-box(x-.9,17.,-4.,x+.9,20.5,1.3)
# Keep the ring bore fully clear even where its rear crosshead meets it.
for side in [-1,1]:
 inner=(cyl(0,0,9.9,4.05,1.7)^box(-7,-7,9.8,2.55,7,11.7)).rotate([0,0,0 if side<0 else 180]).translate([side*33.,5.325,0])
 top=top-inner
# Relief follows the new hollow diamond shoe, but stops below the rim
# so the upper annulus retains contact at Z10. Glass-pad preload stays separate.
current=trimesh.load(P.parent/'SELAGEM/U-Slide_selado.stl')
current_s=md.Manifold(md.Mesh(np.asarray(current.vertices,dtype=np.float32),np.asarray(current.faces,dtype=np.uint32)))
relief=union([current_s.translate([dx,dy,dz]) for dx,dy,dz in [(0,0,.25),(.35,0,0),(-.35,0,0),(0,.35,0),(0,-.35,0)]])
relief=relief ^ box(-45,-15,.8,45,12,9.7)
top=top-relief
assert len(base.decompose())==1 and len(top.decompose())==1
bm=export(base,P/'Base_PC_aneis_montada.stl');tm=export(top,P/'Retentor_PC_aneis_montado.stl')
for m,name in [(bm,'Base_PC_aneis_imprimir.stl'),(tm,'Retentor_PC_aneis_imprimir.stl')]:
 m=m.copy();m.apply_translation([0,0,-m.bounds[0,2]]);m.export(P/name)
# Dry containment/collision audit uses nominal exact TPU, .9mm slide and .13mm cover.
body=trimesh.load(P.parent/'SELAGEM/U-Slide_selado.stl')
body_s=md.Manifold(md.Mesh(np.asarray(body.vertices,dtype=np.float32),np.asarray(body.faces,dtype=np.uint32)));assert body_s.status()==md.Error.NoError
slide=box(-38.1,-12.7,-.9,38.1,12.7,0);cover=box(-30,-12,.4,30,12,.53)
report={'design':'prototype cradle + relieved retainer for hollow diamond shoes and split pins','material':CASE_MATERIAL,
 'nominal_stack_mm':{'slide':.9,'TPU':.4,'cover':.13},'hardware':'none',
 'base_changes':'cradle preserved; rear M3/nut holes replaced by round pin sockets',
 'pin_centers_mm':[[-33.,17.],[33.,17.]],'pin_stem_diameter_mm':4.8,'hole_diameter_mm':5.,
 'retaining_bead_diameter_mm':2*BEAD_R,'pin_internal_diameter_mm':3.2,'pin_split_width_mm':1.8,
 'radial_retention_mm':BEAD_R-2.5,'pin_tip_z_mm':-3.9,'base_bottom_z_mm':-4.1,
 'underside_relief_diameter_mm':5.6,'retention_shoulder_z_mm':-3.05,
 'guide_side_clearance_mm':.25,'guide_bottom_clearance_mm':.4,
 'ring_contact_height_mm':10.,'free_cover_pad_height_mm':.50,'well_bore_radius_mm':4.05,'outer_ring_radius_mm':5.4,'shoe_relief_xy_mm':.35,'shoe_relief_z_mm':.25,'cover_pad_size_mm':[1.7,1.8],
 'expected_cover_flexure_opening_mm':[.03,.06],
 'force_adjustable':False,'physical_validation':False,
 'assembly':'install cold; align U guides; push upper rear pads until pins seat. Do not press glass.',
 'limitations':'nominal geometric fit, not validated FFF snap strength, retention force, creep or seal',
 'collision_mm3':{'base_TPU':(base^body_s).volume(),'retainer_TPU':(top^body_s).volume(),'base_slide':(base^slide).volume(),'retainer_cover_preload':(top^cover).volume(),'base_retainer':(base^top).volume()}}
(P/'moldura_aneis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
