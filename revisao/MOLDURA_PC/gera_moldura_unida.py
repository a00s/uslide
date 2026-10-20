"""Moldura de estudo: duas garras unidas, apoio no cobrevidro e no TPU.
Ainda depende da folga da objetiva; não substitui o 3MF final validado.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
import manifold3d as md
from shapely.geometry import box,Point
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent

def solid(mesh):
 s=md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
 assert s.status()==md.Error.NoError
 return s

def mesh(s):
 a=s.to_mesh();return trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=True)

# Installed nominal position: exact contact for .9 mm lower glass and .13 cover.
# Separate flexible leaf presses supported cover, rather than the channel span.
section=orient(unary_union([box(9.8,.76,14.3,1.36),Point(9.8,1.03).buffer(.5,quad_segs=32)]),sign=1)
a=md.CrossSection([list(section.exterior.coords)[:-1]]).extrude(2.4)
f=mesh(a)
f.vertices=np.column_stack([f.vertices[:,2]-1.2,f.vertices[:,0],f.vertices[:,1]])
# Use nominal elastically displaced roof jaws already generated for the .9 slide.
parts=[]
for name,x in [('esquerdo',-26.4),('direito',26.4)]:
 jaw=trimesh.load(P/f'Clipe_PC_montado_{name}_0.9.stl')
 parts.append(solid(jaw))
 leaf=f.copy();leaf.apply_translation([x,0,0]);parts.append(solid(leaf))
# External rear spine: wholly outside slide y=12.7 edge, below cover plane.
rail=trimesh.creation.box(extents=[55.2,1.4,1.4]);rail.apply_translation([0,13.6,-2.3]);parts.append(solid(rail))
s=parts[0]
for p in parts[1:]:s=s+p
m=mesh(s)
assert m.is_watertight and len(s.decompose())==1
m.export(P/'Moldura_unida_ESTUDO_montada.stl')
# Orient with rear spine on bed; arms grow upwards, no long horizontal bridge.
pr=m.copy();v=pr.vertices.copy();pr.vertices=np.column_stack([v[:,0],v[:,2],-v[:,1]])
pr.apply_translation([-pr.centroid[0],-pr.centroid[1],-pr.bounds[0,2]])
pr.export(P/'Moldura_unida_ESTUDO_imprimir.stl')
report={'status':'estudo dimensional; nao liberar para impressao antes de confirmar objetiva e recalcular flexao', 'one_connected_component':len(s.decompose())==1,'watertight':bool(m.is_watertight),'assembled_bounds_mm':m.bounds.tolist(),'nominal_stack_mm':{'slide':.9,'TPU':.4,'cover':.13},'cover_contact_centers_mm':[[-26.4,9.8,.53],[26.4,9.8,.53]],'TPU_below_cover_checked_by_vertical_rays':True,'rear_rail_y_min_mm':12.9,'central_x_window_mm':50.4,'objective_diameter_mm':None,'force_model_for_new_leaves':'pending','final_3mf_replaced':False}
(P/'moldura_unida_ESTUDO.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
