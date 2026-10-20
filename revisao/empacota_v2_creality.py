#!/usr/bin/env python3
"""Package the existing U-Slide plate as a native Creality Print project."""
from pathlib import Path
import json, zipfile, xml.etree.ElementTree as ET
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT=Path(__file__).resolve().parent.parent
REV=Path(__file__).resolve().parent
FINAL=REV/'U-Slide_K1C_V2_transicao_coberta.3mf'
BASE_PROJECT=Path('/home/x/Documents/impressora3d/corpo_integrado.3mf')
PRESETS=Path('/home/x/.config/Creality/Creality Print/7.3')
PROFILE='TPU 85A saraya profile oficial'
PROCESS='0.08mm Standard @Creality K1C 0.4 nozzle'
APPVER='7.3.0'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
def tag(name): return f'{{{NS}}}{name}'

# Rebuild a simple top view of the print layout for Creality's plate thumbnail.
with zipfile.ZipFile(FINAL) as z:
    model=ET.fromstring(z.read('3D/3dmodel.model'))
    names_cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
    mesh_rows=[]
    for obj in model.findall('.//'+tag('resources')+'/'+tag('object')):
        oid=obj.get('id')
        vs=[(float(v.get('x')),float(v.get('y')),float(v.get('z'))) for v in obj.findall('.//'+tag('mesh')+'/'+tag('vertices')+'/'+tag('vertex'))]
        fs=[tuple(int(t.get('v'+str(i))) for i in (1,2,3)) for t in obj.findall('.//'+tag('mesh')+'/'+tag('triangles')+'/'+tag('triangle'))]
        mesh_rows.append((oid,vs,fs))
labels={o.get('id'):next((m.get('value') for m in o.findall('metadata') if m.get('key')=='name'),f'Objeto {o.get("id")}') for o in names_cfg.findall('object')}
colors={'1':'#69a9b5','2':'#e36b56','3':'#e36b56','4':'#52565a','5':'#52565a'}
fig,ax=plt.subplots(figsize=(5,5),dpi=120)
for oid,vs,fs in mesh_rows:
    polys=[[(vs[i][0],vs[i][1]) for i in face] for face in fs]
    ax.add_collection(PolyCollection(polys,facecolors=colors.get(oid,'#6688aa'),edgecolors='none',alpha=.92))
ax.set(xlim=(0,220),ylim=(0,220),aspect='equal')
ax.set_facecolor('#eeeeee');fig.patch.set_facecolor('white');ax.axis('off')
fig.savefig('/tmp/uslide_plate_top.png',bbox_inches='tight',pad_inches=.05)
plt.close(fig)
plate_png=Path('/tmp/uslide_plate_top.png').read_bytes()
# small cover thumbnail required by Creality Print projects
im=Image.open('/tmp/uslide_plate_top.png').convert('RGBA');im.thumbnail((256,256));im.save('/tmp/uslide_plate_small.png')
small_png=Path('/tmp/uslide_plate_small.png').read_bytes()

# Start with a project exported by this Creality Print installation for a K1C.
with zipfile.ZipFile(BASE_PROJECT) as z:
    project=json.loads(z.read('Metadata/project_settings.config'))
# Resolve the user's TPU preset (K1C Generic TPU parent + user's overrides).
profile_file=PRESETS/'user/2647564910/filament'/f'{PROFILE}.json'
user=json.loads(profile_file.read_text())
parent=PRESETS/'system/Creality/filament'/f"{user['inherits']}.json"
effective=json.loads(parent.read_text())
effective.update(user)
effective.update({'name':PROFILE,'filament_settings_id':[PROFILE], 'from':'project','inherits':''})
# Project preset bundles store per-filament settings as single-entry arrays.
metadata_keys={'name','from','version','inherits','compatible_printers_condition','compatible_prints_condition','material_flow_temp_graph'}
for k,val in effective.items():
    if k not in project or k in metadata_keys: continue
    current=project[k]
    if isinstance(current,list):
        project[k]=val if isinstance(val,list) else [str(val)]
    elif isinstance(current,str):
        project[k]=val[0] if isinstance(val,list) and val else str(val)
project.update({
    'printer_settings_id':'Creality K1C 0.4 nozzle',
    'printer_model':'Creality K1C', 'printer_variant':'0.4',
    'printer_technology':'FFF',
    # Keep the display label aligned with the actual inherited process preset.
    'default_print_profile':project.get('print_settings_id','0.24mm Standard @Creality K1C 0.4 nozzle'),
    'default_filament_profile':[PROFILE],
    'filament_settings_id':[PROFILE],
    'filament_type':['TPU'], 'filament_vendor':['Generic'],
    'filament_colour':['#49AFA4'], 'default_filament_colour':['#49AFA4'],
    'filament_ids':['00001'], 'filament_diameter':['1.75'],
    'filament_map_mode':'AutoForSaving','filament_map':['1'],
    'nozzle_diameter':['0.4'],
})
# Keep the project-level slicer settings consistent with the inherited user
# filament profile instead of retaining the generic values from the seed file.
for k in ('material_flow_temp_graph','nozzle_temperature','nozzle_temperature_initial_layer',
          'nozzle_temperature_range_low','nozzle_temperature_range_high',
          'filament_max_volumetric_speed','filament_flow_ratio','hot_plate_temp',
          'hot_plate_temp_initial_layer','cool_plate_temp','cool_plate_temp_initial_layer'):
    if k in effective:
        val=effective[k]
        if isinstance(project.get(k),list):
            project[k]=val if isinstance(val,list) else [str(val)]
        else:
            project[k]=val[0] if isinstance(val,list) and val else str(val)
# Match the 0.08 mm K1C process shown in the user's Creality Print screenshot.
process_file=PRESETS/'system/Creality/process'/f'{PROCESS}.json'
process=json.loads(process_file.read_text())
process_meta={'name','from','version','inherits','type','setting_id','instantiation',
              'compatible_printers','print_settings_id'}
for k,val in process.items():
    if k in process_meta or k not in project: continue
    if isinstance(project[k],list):
        project[k]=val if isinstance(val,list) else [str(val)]
    elif isinstance(project[k],str):
        project[k]=val[0] if isinstance(val,list) and val else str(val)
    else:
        project[k]=val
project['print_settings_id']=PROCESS
project['default_print_profile']=PROCESS
project_bytes=(json.dumps(project,ensure_ascii=False,indent=2)+'\n').encode()
profile_meta={'name','from','version','inherits','compatible_printers_condition','compatible_prints_condition','material_flow_temp_graph'}
profile_internal={'type','filament_id','setting_id','instantiation','base_id','is_custom_defined'}
profile_export={k:v for k,v in effective.items() if k not in profile_internal}
for k,v in list(profile_export.items()):
    if k not in profile_meta and not isinstance(v,list):
        profile_export[k]=[str(v)]
profile_export.update({'name':PROFILE,'from':'project','inherits':'','filament_settings_id':[PROFILE]})
profile_bytes=(json.dumps(profile_export,ensure_ascii=False,indent=2)+'\n').encode()

# Add native Creality object and single-plate metadata without moving any mesh.
for obj in names_cfg.findall('object'):
    oid=obj.get('id')
    if not any(m.get('key')=='extruder' for m in obj.findall('metadata')):
        ET.SubElement(obj,'metadata',{'key':'extruder','value':'1'})
    # Creality's native projects declare each mesh as a normal part. This keeps
    # the five independent bodies editable and printable after loading.
    if obj.find('part') is None:
        part=ET.SubElement(obj,'part',{'id':'1','subtype':'normal_part'})
        obj_name=next((m.get('value') for m in obj.findall('metadata') if m.get('key')=='name'),f'Objeto {oid}')
        ET.SubElement(part,'metadata',{'key':'name','value':obj_name})
        ET.SubElement(part,'metadata',{'key':'matrix','value':'1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'})
        ET.SubElement(part,'metadata',{'key':'source_object_id','value':'0'})
        ET.SubElement(part,'metadata',{'key':'source_volume_id','value':'0'})
        for axis in 'xyz': ET.SubElement(part,'metadata',{'key':f'source_offset_{axis}','value':'0'})
        ET.SubElement(part,'mesh_stat',{'edges_fixed':'0','degenerate_facets':'0','facets_removed':'0','facets_reversed':'0','backwards_edges':'0'})
if names_cfg.find('plate') is not None:
    for node in list(names_cfg.findall('plate')): names_cfg.remove(node)
plate=ET.SubElement(names_cfg,'plate')
for key,value in [('plater_id','1'),('plater_name',''),('locked','false'),('thumbnail_file','Metadata/plate_1.png'),('thumbnail_no_light_file','Metadata/plate_no_light_1.png'),('top_file','Metadata/top_1.png'),('pick_file','Metadata/pick_1.png')]:
    ET.SubElement(plate,'metadata',{'key':key,'value':value})
# Each physical object is listed as an instance on this Creality plate.
for idx,(oid,_,_) in enumerate(mesh_rows):
    inst=ET.SubElement(plate,'model_instance')
    for key,value in [('object_id',oid),('instance_id','0'),('identify_id',str(1001+idx))]:
        ET.SubElement(inst,'metadata',{'key':key,'value':value})
# Creality stores build placement in the mesh-space transform and assemble Z.
# Keep the centered mesh in 3MF and place it once via build; initialize assemble
# with identity until the first slice (the native app resets it on load).
for node in list(names_cfg.findall('assemble')): names_cfg.remove(node)
assemble=ET.SubElement(names_cfg,'assemble')
for oid,_,_ in mesh_rows:
    ET.SubElement(assemble,'assemble_item',{'object_id':oid,'instance_id':'0','transform':'1 0 0 0 1 0 0 0 1 0 0 0','offset':'0 0 0'})
model_settings=ET.tostring(names_cfg,encoding='utf-8',xml_declaration=True)
creality='''<?xml version="1.0" encoding="UTF-8"?>\n<config>\n <metadata key="Company" value="Creality"/>\n <metadata key="Application" value="Creality_Print"/>\n <metadata key="AppVersion" value="7.3.0"/>\n <metadata key="AppStage" value="Release"/>\n <metadata key="FileVersion" value="1.0"/>\n <metadata key="FileType" value="Undefined"/>\n</config>\n'''
# Plate metadata for the current mesh layout.
boxes=[]
all_xy=[]
for idx,(oid,vs,fs) in enumerate(mesh_rows):
    # Creality's native project format stores XY placement in mesh coordinates.
    x0=min(v[0] for v in vs);x1=max(v[0] for v in vs)
    y0=min(v[1] for v in vs);y1=max(v[1] for v in vs)
    all_xy.extend([(x0,y0),(x1,y1)])
    boxes.append({'area':(x1-x0)*(y1-y0),'bbox':[x0,y0,x1,y1],'id':1001+idx,'layer_height':0.08,'name':labels.get(oid,f'Objeto {oid}')})
bbox=[min(x for x,y in all_xy),min(y for x,y in all_xy),max(x for x,y in all_xy),max(y for x,y in all_xy)]
plate_info={'bbox_all':bbox,'bbox_objects':boxes,'bed_type':'hot_plate','filament_colors':['#49AFA4'],'filament_ids':['00001'],'first_extruder':0,'is_seq_print':False,'nozzle_diameter':0.4,'version':2}
plate_json=(json.dumps(plate_info,ensure_ascii=False,separators=(',',':'))+'\n').encode()

# Zip archive replacement is atomic so a failed generation cannot damage the current final.
tmp=FINAL.with_suffix('.candidate.3mf')
content='''<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="config" ContentType="text/plain"/><Default Extension="json" ContentType="application/json"/></Types>'''
rels='''<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model" Id="rel0"/><Relationship Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail" Target="/Metadata/plate_1.png" Id="rel1"/><Relationship Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-middle" Target="/Metadata/plate_1.png" Id="rel2"/><Relationship Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-small" Target="/Metadata/plate_1_small.png" Id="rel3"/></Relationships>'''
with zipfile.ZipFile(FINAL) as src, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as dst:
    for name in src.namelist():
        if name=='Metadata/model_settings.config': dst.writestr(name,model_settings)
        elif name in {'Metadata/thumbnail.png','[Content_Types].xml','_rels/.rels','Metadata/plate_1.png','Metadata/plate_1_small.png','Metadata/plate_no_light_1.png','Metadata/top_1.png','Metadata/pick_1.png','Metadata/plate_1.json','Metadata/project_settings.config','Metadata/filament_settings_1.config','Metadata/creality.config'}: continue
        else: dst.writestr(name,src.read(name))
    dst.writestr('[Content_Types].xml',content)
    dst.writestr('_rels/.rels',rels)
    dst.writestr('Metadata/plate_1.png',plate_png)
    dst.writestr('Metadata/plate_1_small.png',small_png)
    dst.writestr('Metadata/plate_no_light_1.png',plate_png)
    dst.writestr('Metadata/top_1.png',plate_png)
    dst.writestr('Metadata/pick_1.png',plate_png)
    dst.writestr('Metadata/plate_1.json',plate_json)
    dst.writestr('Metadata/project_settings.config',project_bytes)
    dst.writestr('Metadata/filament_settings_1.config',profile_bytes)
    dst.writestr('Metadata/creality.config',creality)
# Swap only after successful zip and JSON/XML checks.
with zipfile.ZipFile(tmp) as z:
    assert z.testzip() is None
    assert json.loads(z.read('Metadata/project_settings.config'))['printer_settings_id']=='Creality K1C 0.4 nozzle'
    assert json.loads(z.read('Metadata/project_settings.config'))['filament_settings_id']==[PROFILE]
    assert json.loads(z.read('Metadata/project_settings.config'))['print_settings_id']==PROCESS
    assert json.loads(z.read('Metadata/project_settings.config'))['default_print_profile']==PROCESS
    cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
    model_check=ET.fromstring(z.read('3D/3dmodel.model'))
    object_count=len(model_check.findall('.//'+tag('resources')+'/'+tag('object')))
    assert len(cfg.findall('object/part'))==object_count
    assert len(cfg.findall('assemble/assemble_item'))==object_count
tmp.replace(FINAL)
print(FINAL)
print('Embedded printer: Creality K1C 0.4 nozzle; default filament:',PROFILE)
print('Embedded process:',PROCESS)
print('Objects:',len(mesh_rows),'plate instances:',len(ET.fromstring(model_settings).find('plate').findall('model_instance')))
