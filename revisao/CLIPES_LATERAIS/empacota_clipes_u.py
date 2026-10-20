from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json,numpy as np,trimesh
P=Path(__file__).resolve().parent;final=P.parents[1]/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
with zipfile.ZipFile(final) as z:data={n:z.read(n) for n in z.namelist()}
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);tag=lambda s:'{'+ns+'}'+s
r=E.fromstring(data['3D/3dmodel.model']);res=r.find(tag('resources'));build=r.find(tag('build'));cfg=E.fromstring(data['Metadata/model_settings.config'])
for parent in [res,build]:
 for o in list(parent):
  if o.get('id',o.get('objectid')) in ('4','5'):parent.remove(o)
for o in cfg.findall('object'):
 if o.get('id') in ('4','5'):cfg.remove(o)
boxes=[]
for oid,label,dy in [(4,'esquerdo',-6),(5,'direito',6)]:
 m=trimesh.load(P/f'Clipe_U_{label}_imprimir.stl');m.apply_translation([0,dy,0]);obj=E.SubElement(res,tag('object'),id=str(oid),type='model');me=E.SubElement(obj,tag('mesh'));vs=E.SubElement(me,tag('vertices'));fs=E.SubElement(me,tag('triangles'))
 for q in m.vertices:E.SubElement(vs,tag('vertex'),dict(zip('xyz',[str(v) for v in q])))
 for f in m.faces:E.SubElement(fs,tag('triangle'),{f'v{i+1}':str(v) for i,v in enumerate(f)})
 E.SubElement(build,tag('item'),objectid=str(oid),transform='1 0 0 0 1 0 0 0 1 374 110 0',printable='1')
 obj=E.SubElement(cfg,'object',id=str(oid));opts={'name':f'Clipe U PLA {label} — presilha parede externa, contorno sem argola','extruder':'2','layer_height':'0.08','wall_loops':'4','sparse_infill_density':'100%','enable_support':'0','brim_type':'no_brim','ironing_type':'top','ironing_speed':'15','ironing_flow':'15%','ironing_spacing':'0.1'}
 for k,v in opts.items():E.SubElement(obj,'metadata',key=k,value=v)
 bb=np.r_[m.bounds[0,:2]+110,m.bounds[1,:2]+110].tolist();boxes.append({'id':oid+1000,'name':opts['name'],'bbox':bb,'area':float(np.prod(m.extents[:2])),'layer_height':.08})
for plate in cfg.findall('plate'):
 if any(m.get('key')=='plater_id' and m.get('value')=='2' for m in plate.findall('metadata')):
  for inst in plate.findall('model_instance'):plate.remove(inst)
  for oid in [4,5]:
   inst=E.SubElement(plate,'model_instance')
   for k,v in {'object_id':str(oid),'instance_id':'0','identify_id':str(oid+1000)}.items():E.SubElement(inst,'metadata',key=k,value=v)
  for m in list(plate.findall('metadata')):
   if m.get('key')=='plater_name':m.set('value','02 — PLA: parede externa, sem suporte')
   if m.get('key') in ['thumbnail_file','thumbnail_no_light_file','top_file','pick_file']:plate.remove(m)
  if (P/'clipes_u_preview.png').exists():
   data['Metadata/plate_2.png']=(P/'clipes_u_preview.png').read_bytes();E.SubElement(plate,'metadata',key='thumbnail_file',value='Metadata/plate_2.png')
data['3D/3dmodel.model']=E.tostring(r,encoding='utf-8',xml_declaration=True);data['Metadata/model_settings.config']=E.tostring(cfg,encoding='utf-8',xml_declaration=True)
data['Metadata/plate_2.json']=json.dumps({'bbox_all':[min(a['bbox'][0] for a in boxes),min(a['bbox'][1] for a in boxes),max(a['bbox'][2] for a in boxes),max(a['bbox'][3] for a in boxes)],'bbox_objects':boxes,'bed_type':'hot_plate','filament_colors':['#D79738'],'filament_ids':['00001'],'first_extruder':1,'is_seq_print':False,'nozzle_diameter':.4,'version':2}).encode()
t=final.with_suffix('.tmp')
with zipfile.ZipFile(t,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in data.items():z.writestr(n,v)
t.replace(final);print('Prato 02: duas laterais com pega e meia-argola; sem base ou suportes fixos.')
