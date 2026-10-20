"""Replace only the changed channel footprint; retain wells, lip and supports."""
from pathlib import Path
import json,re,numpy as np,trimesh,manifold3d as md
from shapely.geometry import shape,Polygon
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent
old=shape(json.loads((P/'canal_original.json').read_text()));new=shape(json.loads((P/'canal_arredondado.json').read_text()))
source=P.parents[1]/'HISTORICO/TPU_antes_canal_arredondado.stl'
m=trimesh.load(source)
body=md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32)))
def extrude(g,h):
 polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
 result=md.Manifold()
 for poly in polys:
  if poly.area<1e-9:continue
  poly=orient(poly,sign=1)
  rings=[list(poly.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in poly.interiors]
  result=result+md.CrossSection(rings).extrude(h)
 return result
# Rebuild the flat plate as one solid; retain the old well geometry above it.
clip=body^md.Manifold.cube([140,60,12]).translate([-70,-30,.4001])
a=clip.to_mesh();v=np.asarray(a.vert_properties[:,:3]).copy();v[np.abs(v[:,2]-.4001)<1e-5,2]=.399
wells=md.Manifold(md.Mesh(v.astype(np.float32),np.asarray(a.tri_verts,dtype=np.uint32)))
s=(P/'base_original_2d.scad').read_text();coords=json.loads(re.search(r'points=(\[.*?\]), paths=',s).group(1))
plate=Polygon(coords[:12]).difference(new)
body=wells+extrude(plate,.4)
def export(s,path):
 a=s.to_mesh();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=True);m.export(path)
export(body,P/'U-Slide_selado.stl');export(body,P/'TPU_montado.stl')
# Same six sacrificial supports; channel update stays below y=1mm, clear of them.
printed=body
for side in [-1,1]:
 for sy in [-1,1]:
  x=side*27.05;y=5.325+sy*2.9
  printed=printed+md.Manifold.cube([.4,.4,.132],center=False).translate([x-.2,y-.2,.399])
 x=side*25.75
 printed=printed+md.Manifold.cube([.4,.6,.531],center=False).translate([x-.2,5.025,0])
export(printed,P/'U-Slide_para_imprimir.stl')
(P/'canal_arredondado_info.json').write_text(json.dumps({'channel_nominal_width_mm':5.,'inner_bend_radius_mm':3.5,'outer_bend_radius_mm':8.5,'straight_channel_center_y_mm':-6.8,'well_interfaces_preserved_above_y_mm':1.,'manual_supports_preserved':6,'liquid_containment_recomputed':False},indent=2))
print('Corpo atualizado; apenas o contorno inferior do canal foi alterado.')
