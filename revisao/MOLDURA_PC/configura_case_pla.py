from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET,hashlib
P=Path(__file__).resolve().parent
final=P.parents[1]/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
native=Path('/home/x/Applications/CrealityPrint-7.3.0/resources/profiles/Creality/filament/Generic PLA @Creality K1C 0.4 nozzle.json')
profile=json.loads(native.read_text());preset=profile['name'];name='PLA — clipes U diretos K1C'
with zipfile.ZipFile(final) as z:data={n:z.read(n) for n in z.namelist()}
d=json.loads(data['Metadata/project_settings.config']);before={k:v[0] for k,v in d.items() if isinstance(v,list) and len(v)>=2}
f={}
for k,v in profile.items():
 if k in ['type','from','instantiation','filament_id','setting_id','name','inherits','compatible_printers']:continue
 value=v if isinstance(v,list) else [v];f[k]=value
 if k in d and isinstance(d[k],list) and len(d[k])>=2:d[k][1]=value[0] if len(value)==1 else value
f['inherits']=preset;f['name']=name;f['filament_settings_id']=[name];f['filament_notes']=['PLA fit prototype; install after heat-bonded glass/TPU has cooled.']
d['filament_settings_id'][1]=name;d['inherits_group'][2]=preset
d['different_settings_to_system'][2]=';'.join(sorted(k for k in f if isinstance(f[k],list)))
data['Metadata/filament_settings_2.config']=json.dumps(f,ensure_ascii=False,indent=2).encode();data['Metadata/project_settings.config']=json.dumps(d,ensure_ascii=False,indent=2).encode()
r=ET.fromstring(data['Metadata/model_settings.config'])
for obj in r.findall('object'):
 if obj.get('id') in ('4','5'):
  for m in obj.findall('metadata'):
   if m.get('key')=='name':m.set('value',m.get('value','').replace('PC','PLA'))
# Iron only the PLA case; other object/material settings remain unchanged.
for obj in r.findall('object'):
 if obj.get('id') in ('4','5'):
  for key,value in {'ironing_type':'top','ironing_speed':'15','ironing_flow':'15%','ironing_spacing':'0.1'}.items():
   m=next((m for m in obj.findall('metadata') if m.get('key')==key),None)
   if m is None:m=ET.SubElement(obj,'metadata',key=key)
   m.set('value',value)
for plate in r.findall('plate'):
 if any(m.get('key')=='plater_id' and m.get('value')=='2' for m in plate.findall('metadata')):
  for m in plate.findall('metadata'):
   if m.get('key')=='plater_name':m.set('value','02 — PLA: dois clipes U, sem base')
data['Metadata/model_settings.config']=ET.tostring(r,encoding='utf-8',xml_declaration=True)
j=json.loads(data['Metadata/plate_2.json'])
for obj in j['bbox_objects']:obj['name']=obj['name'].replace('PC','PLA')
data['Metadata/plate_2.json']=json.dumps(j,ensure_ascii=False).encode()
assert before=={k:v[0] for k,v in d.items() if isinstance(v,list) and len(v)>=2},'TPU slot changed'
tmp=final.with_suffix('.tmp')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in data.items():z.writestr(n,v)
tmp.replace(final)
print('Prato 02 configurado para PLA, 220 C/50 C. Slot TPU preservado.')
