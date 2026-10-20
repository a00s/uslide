from pathlib import Path
import shutil, zipfile, xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[2]
folder=Path(__file__).resolve().parent
src=folder/'U-Slide_TPU85A_V4_sapato_oco.stl'
final=root/'FINAL_K1C/U-Slide_K1C_FINAL.3mf'
history=root/'HISTORICO/U-Slide_K1C_V3_cunha_antes_da_correcao.3mf'

# Preserve the flawed prior variation before replacing it in the requested FINAL folder.
if not history.exists():
    shutil.copy2(final,history)

points=[]
for line in src.read_text().splitlines():
    fields=line.split()
    if fields and fields[0]=='vertex':
        points.append(tuple(float(v) for v in fields[1:4]))
if len(points)%3:
    raise ValueError('STL does not contain complete triangles')
triangles=[points[i:i+3] for i in range(0,len(points),3)]
vertices=[]; index={}; faces=[]
for tri in triangles:
    face=[]
    for p in tri:
        key=tuple(round(x,5) for x in p)
        if key not in index:
            index[key]=len(vertices); vertices.append(key)
        face.append(index[key])
    faces.append(tuple(face))

ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',ns)
tag=lambda name:f'{{{ns}}}{name}'
tmp=final.with_suffix('.meshfix.3mf')
with zipfile.ZipFile(final) as srczip:
    model=ET.fromstring(srczip.read('3D/3dmodel.model'))
    obj=model.find("./"+tag('resources')+"/"+tag('object')+"[@id='1']")
    if obj is None: raise ValueError('Could not find object 1 in project')
    mesh=obj.find(tag('mesh'))
    if mesh is None: raise ValueError('Object 1 has no direct mesh')
    old_v=mesh.find(tag('vertices')); old_t=mesh.find(tag('triangles'))
    if old_v is not None: mesh.remove(old_v)
    if old_t is not None: mesh.remove(old_t)
    v=ET.Element(tag('vertices'))
    for x,y,z in vertices: ET.SubElement(v,tag('vertex'),{'x':f'{x:.5f}','y':f'{y:.5f}','z':f'{z:.5f}'})
    t=ET.Element(tag('triangles'))
    for a,b,c in faces: ET.SubElement(t,tag('triangle'),{'v1':str(a),'v2':str(b),'v3':str(c)})
    mesh.append(v);mesh.append(t)
    model_xml=ET.tostring(model,encoding='utf-8',xml_declaration=True)
    cfg=ET.fromstring(srczip.read('Metadata/model_settings.config'))
    for o in cfg.findall('object'):
        if o.get('id')=='1':
            for m in o.findall('metadata'):
                if m.get('key')=='name': m.set('value','TPU 85A — corpo com sapato oco V4')
    cfg_xml=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as out:
        for name in srczip.namelist():
            if name=='3D/3dmodel.model': out.writestr(name,model_xml)
            elif name=='Metadata/model_settings.config': out.writestr(name,cfg_xml)
            else: out.writestr(name,srczip.read(name))
with zipfile.ZipFile(tmp) as check:
    if check.testzip() is not None: raise ValueError('Corrupt 3MF archive')
    m=ET.fromstring(check.read('3D/3dmodel.model'))
    o=m.find("./"+tag('resources')+"/"+tag('object')+"[@id='1']")
    nv=len(o.findall('./'+tag('mesh')+'/'+tag('vertices')+'/'+tag('vertex')))
    nf=len(o.findall('./'+tag('mesh')+'/'+tag('triangles')+'/'+tag('triangle')))
    if nv!=len(vertices) or nf!=len(faces): raise ValueError('Mesh count mismatch')
tmp.replace(final)
print(final)
print(f'Object 1 replaced with corrected V4 mesh: {nv} vertices, {nf} triangles.')
print(f'Previous project preserved at: {history}')
