from pathlib import Path
import json,numpy as np,trimesh,manifold3d as md
from shapely.geometry import box,Point
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
HERE=Path(__file__).resolve().parent
body=trimesh.load(HERE.parent/'SELAGEM/TPU_montado.stl')
# A fixed section makes each clip printable on its side without supports.
# The contact is on the high/rear edge of the toe; the rest clears the taper.
x_inner=5.4;clip_width=2.4
world_x=-33+x_inner
rays=np.array([[world_x,5.325+dy,15] for dy in np.linspace(-.2,.2,5)])
loc,idx,tri=body.ray.intersects_location(rays,np.tile([0,0,-1.],(len(rays),1)))
H=float(loc[:,2].max())
preload=.15
upper_t=.80;lower_t=2.00;spine_t=1.60
upper_z=H-preload+.40+upper_t/2
lower_z=-2.20
pad_y=5.325
# Smooth profile corners; the two round anvils avoid sharp edges on TPU/glass.
def rounded(y0,z0,y1,z1,r=.25):
 return box(y0+r,z0+r,y1-r,z1-r).buffer(r,quad_segs=12)
profile=unary_union([
 rounded(-13.1,-3.2,14.5,-1.2,.3),
 rounded(12.9,-3.2,14.5,upper_z+upper_t/2,.35),
 rounded(4.0,upper_z-upper_t/2,14.5,upper_z+upper_t/2,.25),
 Point(pad_y,H-preload+.80).buffer(.80,quad_segs=32),
 Point(pad_y,-1.60).buffer(.70,quad_segs=32),
])
assert profile.geom_type=='Polygon' and len(profile.interiors)==0
profile=orient(profile,sign=1)
coords=np.asarray(profile.exterior.coords)[:-1]
# CrossSection XY=(slide Y, slide Z), extrusion Z becomes slide X.
cs=md.CrossSection([coords.tolist()]);solid=cs.extrude(clip_width)
mm=solid.to_mesh();flat=trimesh.Trimesh(mm.vert_properties[:,:3],mm.tri_verts,process=False)
# The flat C profile lies on the bed; exactly the same section for all layers.
print_mesh=flat.copy();print_mesh.apply_translation([-profile.centroid.x,-profile.centroid.y,0])
print_mesh.export(HERE/'Clipe_PC_imprimir.stl')
def installed(mesh,side):
 p=mesh.vertices.copy();y,z,x=p.T
 # Two identical sections, with the high edge towards the reservoir.
 sx=side*(33-x_inner-clip_width/2)
 q=np.column_stack([x-clip_width/2+sx,y-.2,z])
 m=trimesh.Trimesh(q,mesh.faces[:,::-1],process=True)
 # permutation (a,b,c)->(c,a,b) is even; keep original orientation.
 m=trimesh.Trimesh(q,mesh.faces,process=True)
 m.export(HERE/f'Clipe_PC_livre_{"esquerdo" if side<0 else "direito"}.stl')
 return m
left=installed(flat,-1);right=installed(flat,1)
params={'clip_width_x_mm':clip_width,'local_x_range_mm':[x_inner,x_inner+clip_width], 'clip_centers_x_mm':[-(33-x_inner-clip_width/2),33-x_inner-clip_width/2], 'foot_roof_contact_height_mm':H,'preload_at_0_9mm_slide_mm':preload,'slide_thickness_range_mm':[.8,1.0],'free_lower_anvil_top_mm':-.9,'upper_leaf_thickness_mm':upper_t,'lower_bar_thickness_mm':lower_t,'spine_thickness_mm':spine_t,'assembly_y_offset_mm':-.2,'pad_center_y_mm':pad_y,'upper_leaf_center_z_mm':upper_z,'lower_bar_center_z_mm':lower_z,'profile':coords.tolist(),'print_bounds_mm':print_mesh.bounds.tolist()}
(HERE/'parametros_clips.json').write_text(json.dumps(params,indent=2))
# A compact editable CAD representation, in the same support-free orientation.
(HERE/'Clipe_PC.scad').write_text('// Perfil C em PC. Imprimir deitado de lado: sem suportes.\n// Rebaixo livre 0.15 mm menor que o conjunto nominal; folhas flexionam ao encaixar.\nlinear_extrude(height='+str(clip_width)+') polygon(points='+json.dumps((coords-np.array([profile.centroid.x,profile.centroid.y])).round(6).tolist())+');\n')
print('roof H',H,'profile area',profile.area,'print bounds',print_mesh.bounds.tolist(),'watertight',print_mesh.is_watertight)
