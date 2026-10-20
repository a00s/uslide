from pathlib import Path
import zipfile,xml.etree.ElementTree as E,numpy as np,trimesh
P=Path(__file__).resolve().parent;F=P.parents[1]/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';prod='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
E.register_namespace('',ns);E.register_namespace('p',prod);t=lambda x:'{'+ns+'}'+x
with zipfile.ZipFile(F) as z:d={n:z.read(n) for n in z.namelist()}
cfg=E.fromstring(d['Metadata/model_settings.config']);obj=next(o for o in cfg.findall('object') if any(m.get('key')=='name' and m.get('value','').startswith('TPU 85A') for m in o.findall('metadata')))
root=E.fromstring(d['3D/3dmodel.model']);target=root.find(t('resources')+'/'+t('object')+f"[@id='{obj.get('id')}']")
component=target.find(t('components')+'/'+t('component'))
if component is not None:
 path=component.get('{'+prod+'}path').lstrip('/');model=E.fromstring(d[path]);target=model.find(t('resources')+'/'+t('object')+f"[@id='{component.get('objectid')}']")
else:path='3D/3dmodel.model';model=root
old=target.find(t('mesh'));v=np.array([[float(q.get(c)) for c in 'xyz'] for q in old.find(t('vertices'))]);center=(v.min(0)+v.max(0))/2
m=trimesh.load(P.parent/'SELAGEM/U-Slide_para_imprimir.stl');m.apply_translation(center-m.bounds.mean(axis=0));target.remove(old)
mesh=E.SubElement(target,t('mesh'));vs=E.SubElement(mesh,t('vertices'));fs=E.SubElement(mesh,t('triangles'))
for q in m.vertices:E.SubElement(vs,t('vertex'),{c:f'{value:.7f}' for c,value in zip('xyz',q)})
for f in m.faces:E.SubElement(fs,t('triangle'),{f'v{i+1}':str(value) for i,value in enumerate(f)})
for metadata in obj.findall('metadata'):
 if metadata.get('key')=='name':metadata.set('value','TPU 85A — camara D sem ilha, pocos e sapatos preservados')
for part in obj.findall('part'):
 for metadata in part.findall('metadata'):
  if metadata.get('key')=='name':metadata.set('value','TPU 85A — camara D sem ilha')
 # Stored repair statistics belong to the old mesh.
 for item in part.findall('mesh_stat'):part.remove(item)
d[path]=E.tostring(model,encoding='utf-8',xml_declaration=True);d['Metadata/model_settings.config']=E.tostring(cfg,encoding='utf-8',xml_declaration=True)
if (P/'camara_D_preview.png').exists():d['Metadata/plate_1.png']=(P/'camara_D_preview.png').read_bytes()
with zipfile.ZipFile(F.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in d.items():z.writestr(n,b)
F.with_suffix('.tmp').replace(F);print('Updated native body mesh only; other parts and settings preserved.')
