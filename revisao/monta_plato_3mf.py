#!/usr/bin/env python3
"""Build a K1C plate with the TPU gasket, TPU reinforcement rings and PC edge rails."""
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent.parent
REV=Path(__file__).resolve().parent
PART1=ROOT/'Part Studio 1 - Part 1.3mf'
PART2=ROOT/'Part Studio 1 - Part 2.3mf'
OUT=REV/'U-Slide_plato_K1C.3mf'
THUMB=REV/'U-Slide_montagem_preview.png'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
def tag(n): return f'{{{NS}}}{n}'

def mesh_from_3mf(path):
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('3D/3dmodel.model'))
    obj=root.find('.//'+tag('object'))
    vs=obj.find('.//'+tag('vertices'))
    ts=obj.find('.//'+tag('triangles'))
    verts=[tuple(float(v.get(k)) for k in 'xyz') for v in vs]
    faces=[tuple(int(t.get('v'+str(i))) for i in (1,2,3)) for t in ts]
    return root.get('unit'),verts,faces

def add_mesh(resources,oid,name,verts,faces):
    # 3MF Core has no `name` attribute on objects. Creality Print reads object
    # labels from its standard slicer metadata file instead.
    obj=ET.SubElement(resources,tag('object'),{'id':str(oid),'type':'model'})
    mesh=ET.SubElement(obj,tag('mesh')); vs=ET.SubElement(mesh,tag('vertices'))
    for x,y,z in verts:
        ET.SubElement(vs,tag('vertex'),{'x':f'{x:.6f}','y':f'{y:.6f}','z':f'{z:.6f}'})
    ts=ET.SubElement(mesh,tag('triangles'))
    for a,b,c in faces:
        ET.SubElement(ts,tag('triangle'),{'v1':str(a),'v2':str(b),'v3':str(c)})

def ear_clip(poly):
    """Triangulate a simple 2D polygon, returning counter-clockwise indices."""
    ids=list(range(len(poly)))
    area=sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))
    if area < 0: ids.reverse()
    def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def inside(p,a,b,c):
        x1=cross(a,b,p); x2=cross(b,c,p); x3=cross(c,a,p)
        return x1>=-1e-9 and x2>=-1e-9 and x3>=-1e-9
    tris=[]
    while len(ids)>3:
        found=False
        for j,i in enumerate(ids):
            prev=ids[(j-1)%len(ids)]; nxt=ids[(j+1)%len(ids)]
            a,b,c=poly[prev],poly[i],poly[nxt]
            if cross(a,b,c)<=1e-9: continue
            if any(inside(poly[k],a,b,c) for k in ids if k not in (prev,i,nxt)): continue
            tris.append((prev,i,nxt)); ids.pop(j); found=True; break
        if not found: raise ValueError('Could not triangulate rail profile')
    tris.append(tuple(ids))
    return tris

def extruded_rail(x0,x1,profile,side,label):
    """Extrude a C-clip cross-section along X; lay its broad lip on the build plate."""
    # Mirror the cross-section for the opposite slide edge.
    pts=[(y*side,z) for y,z in profile]
    area=sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))
    if area < 0: pts.reverse()
    tris2=ear_clip(pts)
    zmax=max(z for y,z in pts)
    # Rotate the clip over so its top pressure lip is the bed-contact face.
    verts=[]
    for x in (x0,x1):
        for y,z in pts: verts.append((x, y, zmax-z))
    n=len(pts); faces=[]
    # End caps; reversing the first cap gives outward normals.
    for a,b,c in tris2:
        faces.append((c,b,a)); faces.append((n+a,n+b,n+c))
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,n+j),(i,n+j,n+i)))
    # Move the part clear of the gasket and other objects on the plate.
    yshift=31.0*side
    verts=[(x,y+yshift,z) for x,y,z in verts]
    # The Z flip used to put the broad lip on the bed changes handedness.
    faces=[(a,c,b) for a,b,c in faces]
    return (label,verts,faces)

# Original TPU body: convert metres to mm and orient its flat base onto the build plate.
u,v,f=mesh_from_3mf(PART1); scale=1000 if u=='meter' else 1
body=[(x*scale,-z*scale,y*scale) for x,y,z in v]

# Original pressure ring: center its XZ profile, turn its Y height into print Z.
u,rv,rf=mesh_from_3mf(PART2); scale=1000 if u=='meter' else 1
rv=[tuple(c*scale for c in p) for p in rv]
cx=sum(p[0] for p in rv)/len(rv); cz=sum(p[2] for p in rv)/len(rv)
local=[(x-cx,-(z-cz),y) for x,y,z in rv]
ring_meshes=[]
# TPU rings are printed separately; flip face-over-face in the assembly so their
# bed-facing flat faces point outward and the printed top faces contact the TPU.
for side,label in [(-1,'esquerda'),(1,'direita')]:
    verts=[]
    for x,y,z in local:
        px=x if side<0 else -x
        verts.append((px+side*9.5,y+22.0,z))
    faces=rf if side<0 else [(a,c,b) for a,b,c in rf] # mirror reverses handedness
    ring_meshes.append((label,verts,faces))

# Two spring rails wrap the slide's long outside edges. The nominal throat is
# 1.65 mm to account for 0.8–1.0 mm slides, a thin TPU gasket, and coverslip.
# PC is preferred for repeated flexing; the rails are a fit-test prototype.
rail_profile=[(11.2,1.65),(12.8,1.65),(12.8,0.0),(12.5,0.0),
              (12.4,-0.25),(12.7,-0.35),(13.8,-0.35),
              (13.8,2.30),(11.2,2.30)]
rail_meshes=[extruded_rail(-36.0,36.0,rail_profile,side,
                          f'Trilho lateral {"direito" if side>0 else "esquerdo"} - PC - encaixe de teste')
             for side in (-1,1)]

model=ET.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'})
ET.SubElement(model,tag('metadata'),{'name':'Title'}).text='U-Slide — projeto de impressão K1C'
res=ET.SubElement(model,tag('resources'))
add_mesh(res,1,'Junta principal - TPU 85A - entre lâmina e cobrevidro',body,f)
for i,(label,vv,ff) in enumerate(ring_meshes,2):
    add_mesh(res,i,f'Argola de reforço {label} - TPU 85A - virar na montagem',vv,ff)
for i,(label,vv,ff) in enumerate(rail_meshes,4):
    add_mesh(res,i,label,vv,ff)
build=ET.SubElement(model,tag('build'))
# Place the centered layout at the center of the K1C build plate. Creality
# native projects store this bed placement in each build-item transform.
for i in (1,2,3,4,5):
    ET.SubElement(build,tag('item'),{'objectid':str(i),
        'transform':'1 0 0 0 1 0 0 0 1 110 110 0','printable':'1'})
xml=ET.tostring(model,encoding='utf-8',xml_declaration=True)
content='''<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="config" ContentType="text/plain"/></Types>'''
rels='''<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model" Id="rel0"/><Relationship Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail" Target="/Metadata/thumbnail.png" Id="rel1"/></Relationships>'''
settings=ET.Element('config')
labels={1:'Junta principal - TPU 85A - entre lâmina e cobrevidro',
        2:'Argola de reforço esquerda - TPU 85A - virar na montagem',
        3:'Argola de reforço direita - TPU 85A - virar na montagem',
        4:'Trilho lateral esquerdo - PC - encaixe de teste',
        5:'Trilho lateral direito - PC - encaixe de teste'}
for oid,name in labels.items():
    obj=ET.SubElement(settings,'object',{'id':str(oid)})
    ET.SubElement(obj,'metadata',{'key':'name','value':name})
settings_xml=ET.tostring(settings,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml',content); z.writestr('_rels/.rels',rels); z.writestr('3D/3dmodel.model',xml)
    z.write(THUMB,'Metadata/thumbnail.png')
    z.writestr('Metadata/model_settings.config',settings_xml)
print(OUT)
