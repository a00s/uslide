from pathlib import Path
import zipfile,json,xml.etree.ElementTree as ET
import trimesh,numpy as np
P=Path(__file__).resolve().parent;final=P.parents[1]/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
with zipfile.ZipFile(final) as z:data={n:z.read(n) for n in z.namelist()}
d=json.loads(data['Metadata/project_settings.config']);name='eSUN TPU-LW — tampas experimentais 250C'
f=json.loads(data['Metadata/filament_settings_1.config'])
settings={'filament_settings_id':name,'filament_type':'TPU','filament_vendor':'eSUN','nozzle_temperature':'250','nozzle_temperature_initial_layer':'250','nozzle_temperature_range_low':'210','nozzle_temperature_range_high':'270','filament_flow_ratio':'0.70','filament_density':'1.15','filament_max_volumetric_speed':'1.5','filament_retraction_length':'0','filament_retraction_speed':'0','filament_deretraction_speed':'0','filament_retract_when_changing_layer':'0','filament_wipe':'0','activate_chamber_temp_control':'0','chamber_temperature':'0','hot_plate_temp':'45','hot_plate_temp_initial_layer':'45','cool_plate_temp':'45','cool_plate_temp_initial_layer':'45','eng_plate_temp':'45','eng_plate_temp_initial_layer':'45','textured_plate_temp':'45','textured_plate_temp_initial_layer':'45','fan_min_speed':'100','fan_max_speed':'100','close_fan_the_first_x_layers':'2','additional_cooling_fan_speed':'0','enable_pressure_advance':'0','slow_down_for_layer_cooling':'0'}
for k,v in settings.items():f[k]=[v]
f['name']=name;f['inherits']='Generic TPU @Creality K1C 0.4 nozzle';f['filament_notes']=['Experimental starting point: 250 C, 70% flow. eSUN foaming depends on temperature/flow; no gas permeability validation. Print one cap per job.']
if len(d['filament_settings_id'])==2:
 for k,v in list(d.items()):
  if isinstance(v,list) and len(v)==2:v.append(v[0])
 d['inherits_group'].insert(3,f['inherits']);d['different_settings_to_system'].insert(3,'')
for k,v in f.items():
 if k in d and isinstance(d[k],list) and len(d[k])==3:d[k][2]=v[0] if isinstance(v,list) and len(v)==1 else v
for k,v in settings.items():
 if k in d and isinstance(d[k],list) and len(d[k])==3:d[k][2]=v
for k,v in [('filament_colour','#DCE2E8'),('default_filament_colour','#DCE2E8'),('filament_ids','00003')]:
 if k in d and isinstance(d[k],list):d[k][2]=v
d['different_settings_to_system'][3]=';'.join(sorted(settings))
data['Metadata/project_settings.config']=json.dumps(d,ensure_ascii=False,indent=2).encode();data['Metadata/filament_settings_3.config']=json.dumps(f,ensure_ascii=False,indent=2).encode()
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns);tag=lambda s:'{'+ns+'}'+s
model=ET.fromstring(data['3D/3dmodel.model']);resources=model.find(tag('resources'));build=model.find(tag('build'));cfg=ET.fromstring(data['Metadata/model_settings.config'])
for parent in [resources,build]:
 for child in list(parent):
  if int(child.get('id',child.get('objectid','0'))) in (6,7):parent.remove(child)
for obj in cfg.findall('object'):
 if obj.get('id') in ('6','7'):cfg.remove(obj)
for plate in cfg.findall('plate'):
 if any(m.get('key')=='plater_id' and m.get('value') in ('3','4') for m in plate.findall('metadata')):cfg.remove(plate)
for oid,pid,label in [(6,3,'esquerda'),(7,4,'direita')]:
 mesh=trimesh.load(P/f'Tampa_{label}_imprimir.stl');o=ET.SubElement(resources,tag('object'),id=str(oid),type='model');me=ET.SubElement(o,tag('mesh'));vs=ET.SubElement(me,tag('vertices'));fs=ET.SubElement(me,tag('triangles'))
 for q in mesh.vertices:ET.SubElement(vs,tag('vertex'),dict(zip('xyz',[str(v) for v in q])))
 for face in mesh.faces:ET.SubElement(fs,tag('triangle'),{f'v{i+1}':str(v) for i,v in enumerate(face)})
 ET.SubElement(build,tag('item'),objectid=str(oid),transform=f'1 0 0 0 1 0 0 0 1 {110+((pid-1)%2)*264} {110-((pid-1)//2)*264} 0',printable='1')
 obj=ET.SubElement(cfg,'object',id=str(oid))
 opts={'name':f'Tampa {label} — eSUN TPU-LW — teto na mesa','extruder':'3','layer_height':'0.08','wall_loops':'2','sparse_infill_density':'100%','enable_support':'0','brim_type':'no_brim','outer_wall_speed':'25','inner_wall_speed':'25','internal_solid_infill_speed':'25','top_surface_speed':'25','sparse_infill_speed':'25','initial_layer_speed':'15','initial_layer_infill_speed':'15'}
 for k,v in opts.items():ET.SubElement(obj,'metadata',key=k,value=v)
 plate=ET.SubElement(cfg,'plate')
 for k,v in {'plater_id':str(pid),'plater_name':f'0{pid} — TPU-LW: tampa {label}, imprimir sozinha','locked':'false'}.items():ET.SubElement(plate,'metadata',key=k,value=v)
 ins=ET.SubElement(plate,'model_instance')
 for k,v in {'object_id':str(oid),'instance_id':'0','identify_id':str(1000+oid)}.items():ET.SubElement(ins,'metadata',key=k,value=v)
 bbox=np.r_[mesh.bounds[0,:2]+110,mesh.bounds[1,:2]+110].tolist()
 data[f'Metadata/plate_{pid}.json']=json.dumps({'bbox_all':bbox,'bbox_objects':[{'area':float(np.prod(mesh.extents[:2])),'bbox':bbox,'id':1000+oid,'layer_height':.08,'name':opts['name']}],'bed_type':'hot_plate','filament_colors':['#DCE2E8'],'filament_ids':['00003'],'first_extruder':2,'is_seq_print':False,'nozzle_diameter':.4,'version':2}).encode()
if (P/'tampa_preview.png').exists():
 for plate in cfg.findall('plate'):
  pid=next((m.get('value') for m in plate.findall('metadata') if m.get('key')=='plater_id'),None)
  if pid in ('3','4'):
   data[f'Metadata/plate_{pid}.png']=(P/'tampa_preview.png').read_bytes()
   ET.SubElement(plate,'metadata',key='thumbnail_file',value=f'Metadata/plate_{pid}.png')
data['3D/3dmodel.model']=ET.tostring(model,encoding='utf-8',xml_declaration=True);data['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
tmp=final.with_suffix('.tmp')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in data.items():z.writestr(n,v)
tmp.replace(final);print('Tampas nos pratos 03 e 04; TPU 85A e case PLA preservados.')
