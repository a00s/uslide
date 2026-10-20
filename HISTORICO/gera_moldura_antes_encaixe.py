"""Two-piece PC handling cradle with annular well retainers and two M3 screws.
Nominal geometric assembly only; heat bonding happens before PC installation.
"""
from pathlib import Path
import json
import manifold3d as md
import numpy as np,trimesh
P=Path(__file__).resolve().parent

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
# Two bolt lugs, outside long rear edge. M3 clearance and captive nut pocket.
for x in [-33.,33.]:
 base=base+box(x-4,12.,-4.1,x+4,20.5,-.9)
 base=base-cyl(x,17.,-5.,1.65,7.)
 nut=md.Manifold.cylinder(2.6,3.29,3.29,6).rotate([0,0,30]).translate([x,17.,-4.101])
 base=base-nut

# Upper PC part: 2 open annuli over well rims, connected by a low rear rail.
# Annular bore radius=4.0 > wet well radius3.9: no deliberate contact with fluid.
# Exterior opening remains accessible to pipette and does not cap the wells.
upper=[box(-37.,13.0,.53,37.,15.5,2.13)]
for side in [-1,1]:
 x=side*33.
 # D profile follows the front wall, growing only outward/backward.
 local_outer=cyl(0,0,10.,5.7,1.4)^box(-7,-7,9.9,3.,7,11.5)
 local_inner=cyl(0,0,9.9,4.,1.7)^box(-7,-7,9.8,2.55,7,11.7)
 ring=(local_outer-local_inner).rotate([0,0,0 if side<0 else 180]).translate([x,5.325,0])
 upper.append(ring)
 # Twin uprights outside the rear glass edge; top crosshead reaches ring rear arc.
 upper.extend([box(x-2.7,11.8,.53,x+2.7,14.0,10.2),box(x-2.7,9.3,10.,x+2.7,14.0,11.4)])
 # Broad pad on a verified TPU-backed coverglass area, beside each reservoir.
 # The web stays behind y=9.1 and clears the shoe shoulder.
 cx=side*26.4
 upper.extend([box(cx-1.2,9.1,.53,cx+1.2,15.5,1.73)])
top=union(upper)
for x in [-33.,33.]:
 # Low screw seat + three-sided guide wrapping existing lower lug.
 # .25 mm radial clearance, .4 mm above base bottom; no base change.
 top=top+box(x-5.65,15.5,.53,x+5.65,22.15,4.4)
 top=top+box(x-5.65,15.8,-3.7,x-4.25,22.15,1.)
 top=top+box(x+4.25,15.8,-3.7,x+5.65,22.15,1.)
 top=top+box(x-5.65,20.75,-3.7,x+5.65,22.15,1.)
 top=top-cyl(x,17.,-1.,1.65,6.)
# Keep the ring bore fully clear even where its rear crosshead meets it.
for side in [-1,1]:
 inner=(cyl(0,0,9.9,4.,1.7)^box(-7,-7,9.8,2.55,7,11.7)).rotate([0,0,0 if side<0 else 180]).translate([side*33.,5.325,0])
 top=top-inner
assert len(base.decompose())==1 and len(top.decompose())==1
bm=export(base,P/'Base_PC_aneis_montada.stl');tm=export(top,P/'Retentor_PC_aneis_montado.stl')
for m,name in [(bm,'Base_PC_aneis_imprimir.stl'),(tm,'Retentor_PC_aneis_imprimir.stl')]:
 m=m.copy();m.apply_translation([0,0,-m.bounds[0,2]]);m.export(P/name)
# Dry containment/collision audit uses nominal exact TPU, .9mm slide and .13mm cover.
body=trimesh.load(P.parent/'SELAGEM/U-Slide_selado.stl')
body_s=md.Manifold(md.Mesh(np.asarray(body.vertices,dtype=np.float32),np.asarray(body.faces,dtype=np.uint32)));assert body_s.status()==md.Error.NoError
slide=box(-38.1,-12.7,-.9,38.1,12.7,0);cover=box(-30,-12,.4,30,12,.53)
report={'design':'unchanged lower tray + lightweight upper rings, low M3 seats and U guides around existing lower lugs','nominal_stack_mm':{'slide':.9,'TPU':.4,'cover':.13},'PC_ring_center_mm':[[-33.,5.325],[33.,5.325]],'ring_bore_diameter_mm':8.,'ring_outer_diameter_mm':11.4,'ring_contact_height_mm':10.,'ring_contact':'well rim; opening remains accessible','cover_pad_x_mm':[-26.4,26.4],'cover_pad_y_range_mm':[9.1,12.0],'bolt_centers_mm':[[-33.,17.],[33.,17.]],'hardware':'2x M3x8 screws + 2x M3 nuts; tighten gradually by hand','M3_clearance_diameter_mm':3.3,'nut_hex_across_flats_mm':float(2*3.29*np.cos(np.pi/6)),'tray_slide_clearance_each_short_end_mm':.2,'open_bottom_window_mm':[71.6,22.4],'center_clear_above_channel_x_mm':[-25.2,25.2],'collision_mm3':{'base_TPU':(base^body_s).volume(),'retainer_TPU':(top^body_s).volume(),'base_slide':(base^slide).volume(),'retainer_cover':(top^cover).volume()},'fits_only_nominal_stack':False,'thickness_adjustment':'upper retainer floats vertically with screw adjustment for 0.8–1.0 mm slide; coverslip variation accommodated by TPU compression, not yet physically tested','front_ring_profile':'D shape: front aligned to original well face, no circular projection toward channel','thermal_bonding':'before assembling PC cradle','physical_validation':False,'guide_side_clearance_mm':.25,'guide_bottom_clearance_mm':.4,'screw_head_seat_height_mm':4.4,'base_geometry_changed':False}
(P/'moldura_aneis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
