from pathlib import Path
import zipfile,xml.etree.ElementTree as E,numpy as np,trimesh
P=Path(__file__).resolve().parent;F=P.parents[1]/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';prod='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
E.register_namespace('',ns);E.register_namespace('p',prod);t=lambda x:'{'+ns+'}'+x
with zipfile.ZipFile(F) as z:d={n:z.read(n) for n in z.namelist()}
cfg=E.fromstring(d['Metadata/model_settings.config']);root=E.fromstring(d['3D/3dmodel.model'])
for label in ['esquerda','direita']:
 obj=next(o for o in cfg.findall('object') if any(m.get('key')=='name' and m.get('value','').startswith('Tampa '+label) for m in o.findall('metadata')))
 oid=obj.get('id');target=root.find(t('resources')+'/'+t('object')+f"[@id='{oid}']");component=target.find(t('components')+'/'+t('component'))
 path=component.get('{'+prod+'}path').lstrip('/');model=E.fromstring(d[path]);target=model.find(t('resources')+'/'+t('object')+f"[@id='{component.get('objectid')}']")
 old=target.find(t('mesh'));v=np.array([[float(q.get(c)) for c in 'xyz'] for q in old.find(t('vertices'))]);center=(v.min(0)+v.max(0))/2
 m=trimesh.load(P/f'Tampa_{label}_imprimir.stl');m.apply_translation(center-m.bounds.mean(axis=0));target.remove(old)
 mesh=E.SubElement(target,t('mesh'));vs=E.SubElement(mesh,t('vertices'));fs=E.SubElement(mesh,t('triangles'))
 for q in m.vertices:E.SubElement(vs,t('vertex'),{c:f'{value:.7f}' for c,value in zip('xyz',q)})
 for f in m.faces:E.SubElement(fs,t('triangle'),{f'v{i+1}':str(value) for i,value in enumerate(f)})
 options={'name':f'Tampa {label} — PLA, pega larga, saia longa','extruder':'2','enable_support':'0','brim_type':'no_brim','ironing_type':'top','layer_height':'0.08'}
 for key,value in options.items():
  node=next((n for n in obj.findall('metadata') if n.get('key')==key),None)
  if node is None:node=E.SubElement(obj,'metadata',key=key)
  node.set('value',value)
 for part in obj.findall('part'):
  for stat in part.findall('mesh_stat'):part.remove(stat)
  for meta in part.findall('metadata'):
   if meta.get('key')=='name':meta.set('value',options['name'])
 for item in root.find(t('build')):
  if item.get('objectid')==oid:
   transform=item.get('transform').split();transform[11]=str(float(-m.bounds[0,2]));item.set('transform',' '.join(transform))
 d[path]=E.tostring(model,encoding='utf-8',xml_declaration=True)
for plate in cfg.findall('plate'):
 for node in plate.findall('metadata'):
  if node.get('key')=='plater_name' and 'tampa' in node.get('value','').lower():node.set('value',node.get('value').replace('TPU-LW','PLA'))
d['3D/3dmodel.model']=E.tostring(root,encoding='utf-8',xml_declaration=True);d['Metadata/model_settings.config']=E.tostring(cfg,encoding='utf-8',xml_declaration=True)
if (P/'tampa_preview.png').exists():
 for pid in [3,4]:
  for path in [f'Metadata/plate_{pid}.png',f'Metadata/plate_{pid}_small.png']:d[path]=(P/'tampa_preview.png').read_bytes()
with zipfile.ZipFile(F.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in d.items():z.writestr(n,b)
F.with_suffix('.tmp').replace(F);print('Native plates03/04: larger PLA caps, roof down, one per plate. Body and clips preserved.')
