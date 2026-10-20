#!/usr/bin/env python3
"""Build a 3MF assembly from the original TPU uSlide body and two modified rings."""
from pathlib import Path
import re, zipfile, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
REV = Path(__file__).resolve().parent
PART1 = ROOT / 'Part Studio 1 - Part 1.3mf'
RINGS = REV / 'Argolas_pressao_base_larga_K1C.stl'
OUT = REV / 'U-Slide_conjunto_completo_K1C.3mf'
NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('', NS)

def tag(name): return f'{{{NS}}}{name}'

def read_part1():
    with zipfile.ZipFile(PART1) as z:
        root = ET.fromstring(z.read('3D/3dmodel.model'))
    vs = root.find('.//'+tag('vertices'))
    ts = root.find('.//'+tag('triangles'))
    # The Onshape export is in metres, and its plate normal is +Y.
    verts = []
    for v in vs:
        x,y,z = [float(v.get(k))*1000 for k in ('x','y','z')]
        verts.append((x,-z,y))  # rotate the whole assembly so the plate lies flat (Z up)
    faces = [(int(t.get('v1')), int(t.get('v2')), int(t.get('v3'))) for t in ts]
    return verts, faces

def read_ring_components():
    text = RINGS.read_text()
    raw = [tuple(map(float,m)) for m in re.findall(r'vertex\s+([-+\deE.]+)\s+([-+\deE.]+)\s+([-+\deE.]+)', text)]
    tris = [raw[i:i+3] for i in range(0,len(raw),3)]
    groups = {-1:[], 1:[]}
    for tri in tris:
        side = -1 if sum(v[0] for v in tri)/3 < 0 else 1
        groups[side].append(tri)
    result=[]
    # The ring source's well centers and heights were measured from Part 1.
    well_x = 33.10485144
    well_z = -5.32339475
    print_x = 9.5
    for side in (-1,1):
        unique={}; verts=[]; faces=[]
        for tri in groups[side]:
            face=[]
            for x,y,z in tri:
                # Unpack the two-ring print layout into one local ring, then place
                # it above its matching reservoir in the original assembly.
                local=(x-side*print_x, y, z)
                world=(local[0]+side*well_x, local[1]-well_z, local[2]+10.0)
                key=tuple(round(c,6) for c in world)
                if key not in unique:
                    unique[key]=len(verts); verts.append(world)
                face.append(unique[key])
            faces.append(tuple(face))
        result.append((f'Argola de pressão {"esquerda" if side<0 else "direita"} - PC',verts,faces))
    return result

def add_mesh(parent, oid, name, verts, faces):
    obj=ET.SubElement(parent,tag('object'),{'id':str(oid),'name':name,'type':'model'})
    mesh=ET.SubElement(obj,tag('mesh'))
    vroot=ET.SubElement(mesh,tag('vertices'))
    for x,y,z in verts:
        ET.SubElement(vroot,tag('vertex'),{'x':f'{x:.6f}','y':f'{y:.6f}','z':f'{z:.6f}'})
    troot=ET.SubElement(mesh,tag('triangles'))
    for a,b,c in faces:
        ET.SubElement(troot,tag('triangle'),{'v1':str(a),'v2':str(b),'v3':str(c)})
    return obj

model=ET.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'})
ET.SubElement(model,tag('metadata'),{'name':'Title'}).text='U-Slide — conjunto TPU e argolas de pressão'
resources=ET.SubElement(model,tag('resources'))
v,f=read_part1()
add_mesh(resources,1,'Junta TPU 85A - abas sacrificiais de remoção',v,f)
for i,(name,v,f) in enumerate(read_ring_components(),2):
    add_mesh(resources,i,name,v,f)
build=ET.SubElement(model,tag('build'))
for i in (1,2,3): ET.SubElement(build,tag('item'),{'objectid':str(i)})
xml=ET.tostring(model,encoding='utf-8',xml_declaration=True)
content='''<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'''
rels='''<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model" Id="rel0"/></Relationships>'''
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml',content)
    z.writestr('_rels/.rels',rels)
    z.writestr('3D/3dmodel.model',xml)
print(OUT)
