from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,json
p=Path('FINAL_K1C/U-Slide_K1C_FINAL.3mf')
with zipfile.ZipFile(p) as z: data={n:z.read(n) for n in z.namelist()}
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
r=ET.fromstring(data['3D/3dmodel.model'])
for parent in r.iter():
 for child in list(parent):
  if (child.tag==f'{{{ns}}}object' and child.get('id') in ('2','3')) or (child.tag==f'{{{ns}}}item' and child.get('objectid') in ('2','3')):parent.remove(child)
data['3D/3dmodel.model']=ET.tostring(r,encoding='utf-8',xml_declaration=True)
r=ET.fromstring(data['Metadata/model_settings.config'])
for child in list(r):
 if child.tag=='object' and child.get('id') in ('2','3'):r.remove(child)
for plate in r.findall('plate'):
 for inst in list(plate.findall('model_instance')):
  if any(m.get('key')=='object_id' and m.get('value') in ('2','3') for m in inst):plate.remove(inst)
 for m in plate.findall('metadata'):
  if m.get('key')=='plater_name' and m.get('value','').startswith('01'):m.set('value','01 — TPU 85A: corpo sem argolas')
data['Metadata/model_settings.config']=ET.tostring(r,encoding='utf-8',xml_declaration=True)
j=json.loads(data['Metadata/plate_1.json']);j['bbox_objects']=[o for o in j['bbox_objects'] if o['id']==1001];j['bbox_all']=j['bbox_objects'][0]['bbox'];data['Metadata/plate_1.json']=json.dumps(j).encode()
# Remove obsolete thumbnails to avoid showing removed rings.
for n in list(data):
 if n.startswith('Metadata/') and n.endswith('.png') and ('_1.' in n):del data[n]
tmp=p.with_suffix('.tmp')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in data.items():z.writestr(n,v)
tmp.replace(p)
