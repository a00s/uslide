from pathlib import Path
import zipfile,json,xml.etree.ElementTree as ET,shutil,struct,io
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
FINAL=ROOT/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
SEED=ROOT/'HISTORICO/U-Slide_K1C_TPU_antes_moldura_PC.3mf'
if not SEED.exists():shutil.copy2(FINAL,SEED)
PRE=Path('/home/x/.config/Creality/Creality Print/7.3')
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',NS)
tag=lambda n:'{'+NS+'}'+n
with zipfile.ZipFile(SEED) as z:files={n:z.read(n) for n in z.namelist()}
model=ET.fromstring(files['3D/3dmodel.model']);resources=model.find(tag('resources'));build=model.find(tag('build'))
cfg=ET.fromstring(files['Metadata/model_settings.config'])
for name,value in {'Application':'Creality_Print V7.3.0.6151 Release','BambuStudio:3mfVersion':'1'}.items():
 existing=next((m for m in model.findall(tag('metadata')) if m.get('name')==name),None)
 if existing is None:existing=ET.Element(tag('metadata'),{'name':name});model.insert(0,existing)
 existing.text=value
files['Metadata/creality.config']=files['Metadata/creality.config'].replace(b'value="7.3.0"',b'value="7.3.0.6151"')

clip_path=HERE/'Clipe_PC_imprimir.stl';raw=clip_path.read_bytes();N=struct.unpack_from('<I',raw,80)[0]
v=[];f=[];lookup={}
for i in range(N):
 vals=struct.unpack_from('<12fH',raw,84+50*i);face=[]
 for j in range(3):
  point=tuple(round(x,6) for x in vals[3+3*j:6+3*j])
  if point not in lookup:lookup[point]=len(v);v.append(point)
  face.append(lookup[point])
 f.append(face)
v=np.array(v)
# Creality PartPlate uses 20% logical plate gap: plate 2 origin (264,0).
# Reference: src/slic3r/GUI/PartPlate.cpp LOGICAL_PART_PLATE_GAP=1/5.
for oid,shift in [(4,-25),(5,25)]:
 obj=ET.SubElement(resources,tag('object'),{'id':str(oid),'type':'model'})
 mesh=ET.SubElement(obj,tag('mesh'));vs=ET.SubElement(mesh,tag('vertices'));ts=ET.SubElement(mesh,tag('triangles'))
 for x,y,z in v:ET.SubElement(vs,tag('vertex'),{'x':f'{x+shift:.6f}','y':f'{y:.6f}','z':f'{z:.6f}'})
 for face in f:ET.SubElement(ts,tag('triangle'),{f'v{i+1}':str(q) for i,q in enumerate(face)})
 ET.SubElement(build,tag('item'),{'objectid':str(oid),'transform':'1 0 0 0 1 0 0 0 1 374 110 0','printable':'1'})
 ob=ET.SubElement(cfg,'object',{'id':str(oid)})
 for key,value in {'name':f'Clipe PC {oid-3} — imprimir deitado de lado','extruder':'2','layer_height':'0.2','wall_loops':'4','sparse_infill_density':'100%','enable_support':'0','brim_type':'outer_only','brim_width':'3','brim_object_gap':'0.1'}.items():ET.SubElement(ob,'metadata',{'key':key,'value':value})
for plate in cfg.findall('plate'):
 for m in plate.findall('metadata'):
  if m.get('key')=='plater_name':m.set('value','01 — TPU 85A: corpo e argolas')
plate=ET.SubElement(cfg,'plate')
for key,value in {'plater_id':'2','plater_name':'02 — PC: dois clipes','locked':'false','thumbnail_file':'Metadata/plate_2.png','thumbnail_no_light_file':'Metadata/plate_no_light_2.png','top_file':'Metadata/top_2.png','pick_file':'Metadata/pick_2.png'}.items():ET.SubElement(plate,'metadata',{'key':key,'value':value})
for oid in [4,5]:
 inst=ET.SubElement(plate,'model_instance')
 for k,val in {'object_id':str(oid),'instance_id':'0','identify_id':str(1000+oid)}.items():ET.SubElement(inst,'metadata',{'key':k,'value':val})
files['3D/3dmodel.model']=ET.tostring(model,encoding='utf-8',xml_declaration=True)
files['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
# Flatten the installed PC profile, preserving its nozzle and bed temperatures.
def resolve(path,seen=None):
 d=json.loads(path.read_text());parent=d.get('inherits');base={}
 if parent:
  candidates=[PRE/'system/Creality/filament'/f'{parent}.json',PRE/'user/2647564910/filament'/f'{parent}.json']
  for p in candidates:
   if p.exists():base=resolve(p);break
 base.update(d);return base
pc=resolve(PRE/'user/2647564910/filament/PC CC3D generic.json')
project=json.loads(files['Metadata/project_settings.config'])
meta={'name','type','version','from','inherits','compatible_printers','compatible_printers_condition','compatible_prints','compatible_prints_condition','filament_settings_id','filament_id','setting_id','base_id','instantiation'}
for k,val in pc.items():
 if k in meta or k not in project:continue
 if isinstance(project[k],list):
  first=project[k][0] if project[k] else ''
  pcval=val[0] if isinstance(val,list) and val else str(val)
  project[k]=[first,pcval]
project.update({'default_filament_profile':['TPU 85A saraya profile oficial','PC CC3D generic'],'filament_settings_id':['TPU 85A saraya profile oficial','PC CC3D generic'],'filament_type':['TPU','PC'],'filament_vendor':['Generic','CC3D'],'filament_colour':['#49AFA4','#D79738'],'default_filament_colour':['#49AFA4','#D79738'],'filament_ids':['00001','00021'],'filament_map':['1','1'],'enable_prime_tower':'0'})
# Logical filament 2 still uses the K1C's single physical tool.
# The installed machine template otherwise expands the initial virtual slot to T1.
project['manual_filament_change']= '1'
project['machine_start_gcode']=project.get('machine_start_gcode','').replace('T[initial_no_support_extruder]','T0')
# The GUI/CLI preset merge uses one dirty-key group per process, filament and
# machine. The seed's PLA inheritance must not silently replace the TPU slot.
tpu=json.loads(files['Metadata/filament_settings_1.config'])
process_keys={'layer_height','initial_layer_print_height','wall_generator','wall_loops','outer_wall_speed','inner_wall_speed','sparse_infill_speed','internal_solid_infill_speed','top_surface_speed','initial_layer_speed','bridge_speed','default_acceleration','outer_wall_acceleration','inner_wall_acceleration','sparse_infill_density','enable_support','enable_prime_tower','support_type','support_threshold_angle','support_on_build_plate_only','support_top_z_distance','support_bottom_z_distance','support_interface_top_layers','support_interface_spacing'}
def dirty(d):return ';'.join(sorted(k for k in d if k in project and k not in meta))
project['inherits_group']=['0.20mm Standard @Creality K1C 0.4 nozzle','Generic TPU @Creality K1C 0.4 nozzle','Generic PC @Creality K1C 0.4 nozzle','']
project['different_settings_to_system']=[';'.join(sorted(process_keys)),dirty(tpu),dirty(pc),'machine_start_gcode;manual_filament_change']
files['Metadata/project_settings.config']=(json.dumps(project,ensure_ascii=False,indent=2)+'\n').encode()
internal={'type','filament_id','setting_id','instantiation','base_id','is_custom_defined'}
pc_export={k:v for k,v in pc.items() if k not in internal}
for k,val in list(pc_export.items()):
 if k not in meta and not isinstance(val,list):pc_export[k]=[str(val)]
pc_export.update({'name':'PC CC3D generic','from':'project','inherits':'','filament_settings_id':['PC CC3D generic']})
files['Metadata/filament_settings_2.config']=(json.dumps(pc_export,ensure_ascii=False,indent=2)+'\n').encode()
# Thumbnail and bounding metadata for the second plate, in its local coordinates.
fig,ax=plt.subplots(figsize=(5,5),dpi=120)
for dx in [-25,25]:
 vv=v.copy();vv[:,0]+=dx
 ax.add_collection(PolyCollection(vv[np.array(f),:2],facecolors='#d79738',edgecolors='none'))
ax.set(xlim=(-110,110),ylim=(-110,110),aspect='equal');ax.axis('off');fig.patch.set_facecolor('#eeeeee');out=io.BytesIO();fig.savefig(out,format='png',bbox_inches='tight',pad_inches=.05);plt.close(fig)
png=out.getvalue()
for n in ['plate_2.png','plate_no_light_2.png','top_2.png','pick_2.png']:files['Metadata/'+n]=png
thumb=Image.open(io.BytesIO(png));thumb.thumbnail((256,256));out=io.BytesIO();thumb.save(out,format='png');files['Metadata/plate_2_small.png']=out.getvalue()
boxes=[]
for i,dx in enumerate([-25,25]):
 xy=v[:,:2]+[110+dx,110];bb=np.r_[xy.min(0),xy.max(0)].tolist();boxes.append({'id':1004+i,'area':float(np.prod(xy.max(0)-xy.min(0))),'bbox':bb,'layer_height':.2,'name':f'Clipe PC {i+1}'})
plate_meta={'bbox_all':[min(q['bbox'][0] for q in boxes),min(q['bbox'][1] for q in boxes),max(q['bbox'][2] for q in boxes),max(q['bbox'][3] for q in boxes)],'bbox_objects':boxes,'bed_type':'hot_plate','filament_colors':['#D79738'],'filament_ids':['00021'],'first_extruder':1,'is_seq_print':False,'nozzle_diameter':.4,'version':2}
files['Metadata/plate_2.json']=json.dumps(plate_meta).encode()
tmp=FINAL.with_suffix('.clips.3mf')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for n,d in files.items():z.writestr(n,d)
with zipfile.ZipFile(tmp) as z:assert z.testzip() is None
tmp.replace(FINAL)
print(FINAL,'5 objects / 2 plates / TPU and PC slots')
print('temperatures',project.get('nozzle_temperature'),project.get('hot_plate_temp'))
