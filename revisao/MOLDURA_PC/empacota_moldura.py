from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET
import numpy as np,trimesh
P=Path(__file__).resolve().parent
src=P.parents[1]/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
out=src
with zipfile.ZipFile(src) as z:files={n:z.read(n) for n in z.namelist()}
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns);tag=lambda s:'{'+ns+'}'+s
m=ET.fromstring(files['3D/3dmodel.model']);r=m.find(tag('resources'));b=m.find(tag('build'));cfg=ET.fromstring(files['Metadata/model_settings.config'])
for o in list(r):
 if o.tag==tag('object') and int(o.get('id'))>=4:r.remove(o)
for o in list(b):
 if int(o.get('objectid'))>=4:b.remove(o)
for o in cfg.findall('object'):
 if int(o.get('id'))>=4:cfg.remove(o)
mesh=trimesh.load(P/'Moldura_PC_livre.stl');mesh.apply_translation([0,0,-mesh.bounds[0,2]]);mesh.export(P/'Moldura_PC_imprimir.stl')
o=ET.SubElement(r,tag('object'),{'id':'4','type':'model'});me=ET.SubElement(o,tag('mesh'));vs=ET.SubElement(me,tag('vertices'));fs=ET.SubElement(me,tag('triangles'))
for x,y,z in mesh.vertices:ET.SubElement(vs,tag('vertex'),{'x':str(x),'y':str(y),'z':str(z)})
for a,c,d in mesh.faces:ET.SubElement(fs,tag('triangle'),{'v1':str(a),'v2':str(c),'v3':str(d)})
ET.SubElement(b,tag('item'),{'objectid':'4','transform':'1 0 0 0 1 0 0 0 1 374 110 0','printable':'1'})
o=ET.SubElement(cfg,'object',{'id':'4'})
settings={'name':'Moldura PC lateral — base e travas','extruder':'2','layer_height':'0.12','wall_loops':'4','sparse_infill_density':'100%','enable_support':'1','support_type':'normal(auto)','support_on_build_plate_only':'1','support_top_z_distance':'0.24','support_bottom_z_distance':'0.24','support_interface_top_layers':'2','support_interface_spacing':'0.5','brim_type':'outer_only','brim_width':'3','brim_object_gap':'0.1'}
for k,v in settings.items():ET.SubElement(o,'metadata',{'key':k,'value':v})
for p in cfg.findall('plate'):
 ids=[a.get('value') for a in p.findall('metadata') if a.get('key')=='plater_id']
 if ids==['2']:
  for a in p.findall('model_instance'):p.remove(a)
  for a in p.findall('metadata'):
   if a.get('key')=='plater_name':a.set('value','02 — Moldura lateral PC')
  inst=ET.SubElement(p,'model_instance')
  for k,v in {'object_id':'4','instance_id':'0','identify_id':'1004'}.items():ET.SubElement(inst,'metadata',{'key':k,'value':v})
files['3D/3dmodel.model']=ET.tostring(m,encoding='utf-8',xml_declaration=True);files['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
# Old plate-2 thumbnails describe the previous clips and must not be reused.
for key in list(files):
 if ('plate_2' in key or 'top_2' in key or 'pick_2' in key or 'plate_no_light_2' in key):del files[key]
# Plate preview and local bounding metadata for the single retaining frame.
for name in ['plate_2.png','plate_no_light_2.png','top_2.png','pick_2.png','plate_2_small.png']:
 files['Metadata/'+name]=(P/'moldura_prato.png').read_bytes()
bb=np.r_[mesh.bounds[0,:2]+110,mesh.bounds[1,:2]+110].tolist()
files['Metadata/plate_2.json']=json.dumps({'bbox_all':bb,'bbox_objects':[{'id':1004,'area':float(np.prod(mesh.extents[:2])),'bbox':bb,'layer_height':.12,'name':'Moldura lateral PC'}],'bed_type':'hot_plate','filament_colors':['#D79738'],'filament_ids':['00021'],'first_extruder':1,'is_seq_print':False,'nozzle_diameter':.4,'version':2}).encode()
tmp=out.with_suffix('.moldura.3mf')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for n,d in files.items():z.writestr(n,d)
tmp.replace(out)
print(out)
