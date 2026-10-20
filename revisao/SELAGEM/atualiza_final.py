from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,shutil
import trimesh
here=Path(__file__).resolve().parent
root=here.parents[1]
final=root/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
backup=root/'HISTORICO/U-Slide_K1C_antes_selagem.3mf'
if not backup.exists():shutil.copy2(final,backup)
mesh=trimesh.load(here/'U-Slide_para_imprimir.stl')
assert mesh.is_watertight and len(mesh.split()) in (1,3) # body plus two detached table supports
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',ns)
tag=lambda name:'{'+ns+'}'+name
with zipfile.ZipFile(final) as z:entries={n:z.read(n) for n in z.namelist()}
model=ET.fromstring(entries['3D/3dmodel.model'])
obj=model.find('./'+tag('resources')+'/'+tag('object')+"[@id='1']")
old=obj.find(tag('mesh'));obj.remove(old)
new=ET.SubElement(obj,tag('mesh'));vs=ET.SubElement(new,tag('vertices'));fs=ET.SubElement(new,tag('triangles'))
for p in mesh.vertices:ET.SubElement(vs,tag('vertex'),dict(zip('xyz',[f'{v:.6f}' for v in p])))
for f in mesh.faces:ET.SubElement(fs,tag('triangle'),{f'v{i+1}':str(v) for i,v in enumerate(f)})
entries['3D/3dmodel.model']=ET.tostring(model,encoding='utf-8',xml_declaration=True)
cfg=ET.fromstring(entries['Metadata/model_settings.config'])
for o in cfg.findall('object'):
 if o.attrib.get('id')=='1':
  for m in o.findall('metadata'):
   if m.attrib.get('key')=='name':m.set('value','TPU 85A — corpo U com sapatos ocos e contato no cobrevidro')
entries['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
tmp=final.with_suffix('.new.3mf')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for n,d in entries.items():z.writestr(n,d)
with zipfile.ZipFile(tmp) as z:assert z.testzip() is None
tmp.replace(final)
print(final,'vertices',len(mesh.vertices),'faces',len(mesh.faces))
