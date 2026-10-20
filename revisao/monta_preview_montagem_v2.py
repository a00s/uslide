from pathlib import Path
import zipfile,xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import Axes3D
ROOT=Path('/home/x/projetos/uslide/uslide')
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
def tag(n): return f'{{{NS}}}{n}'
def read_mesh(path):
 with zipfile.ZipFile(path) as z:r=ET.fromstring(z.read('3D/3dmodel.model'))
 o=r.find('.//'+tag('object')); vs=o.find('.//'+tag('vertices')); ts=o.find('.//'+tag('triangles'))
 unit=r.get('unit'); s=1000 if unit=='meter' else 1
 v=[tuple(float(q.get(k))*s for k in 'xyz') for q in vs]
 f=[tuple(int(t.get('v'+str(i))) for i in (1,2,3)) for t in ts]
 return v,f
def draw_mesh(ax,v,f,color,alpha=1):
 coll=Poly3DCollection([[v[i] for i in face] for face in f],facecolors=color,edgecolors='none',alpha=alpha)
 ax.add_collection3d(coll)
def box_faces(x0,x1,y0,y1,z0,z1):
 v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
 f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 return [[v[i] for i in face] for face in f]
fig=plt.figure(figsize=(12,7),dpi=150); ax=fig.add_subplot(111,projection='3d')
# Main slide and V2 TPU gasket. The SCAD mesh is already in print orientation.
ax.add_collection3d(Poly3DCollection(box_faces(-38.1,38.1,-12.7,12.7,0,.9),facecolors='#bfc7cc',edgecolors='#68737a',linewidths=.35,alpha=.36))
def read_stl(path):
 import re
 verts=[];faces=[];index={};tri=[]
 for line in Path(path).read_text().splitlines():
  parts=line.split()
  if len(parts)==4 and parts[0]=='vertex':
   pt=tuple(float(q) for q in parts[1:]);key=tuple(round(q,6) for q in pt)
   if key not in index:index[key]=len(verts);verts.append(pt)
   tri.append(index[key])
   if len(tri)==3:faces.append(tuple(tri));tri=[]
 return verts,faces
v,f=read_stl(ROOT/'revisao/U-Slide_TPU85A_V2_transicao_coberta.stl')
body=[(x,y,z+.9) for x,y,z in v]
draw_mesh(ax,body,f,'#69a9b5',.78)
# Coverslip held 0.17 mm above the TPU base top.
ax.add_collection3d(Poly3DCollection(box_faces(-30,30,-12,12,1.3,1.47),facecolors='#a8dcf0',edgecolors='#4489a4',linewidths=.5,alpha=.23))
# The two original C rings, flipped face-over-face on the collars.
rv,rf=read_mesh(ROOT/'Part Studio 1 - Part 2.3mf')
cx=sum(p[0] for p in rv)/len(rv); cz=sum(p[2] for p in rv)/len(rv)
local=[(x-cx,-(z-cz),y) for x,y,z in rv]
for side in (-1,1):
 vv=[]
 for x,y,z in local:
  px=x if side<0 else -x
  # Flip around X: the bed face becomes the outward/top face while the printed
  # upper face contacts the TPU. The opening still points inward along X.
  # Centers and collar top come from the source CAD. The source reservoir
  # reaches z=10.0 mm; the flipped ring's printed face seats on that plane.
  vv.append((px+side*31.0,-y+4.0,13.2-z))
 ff=rf if side<0 else [(a,c,b) for a,b,c in rf]
 draw_mesh(ax,vv,ff,'#e36b56',.92)
# The PC side rails as assembled (not their bed-facing print orientation).
profile=[(11.2,1.50),(12.8,1.50),(12.8,0.0),(12.5,0.0),(12.4,-.25),(12.7,-.35),(13.8,-.35),(13.8,2.25),(11.2,2.25)]
def rail(side):
 pts=[(y*side,z) for y,z in profile]
 # draw as a solid extruded polygon using a triangulated surface; for preview, draw side walls and end faces.
 from matplotlib.path import Path as MPath
 # cross-section end cap rendered as polygon; the concave C profile is clear in side view.
 ax.add_collection3d(Poly3DCollection([[( -36,y,z) for y,z in pts],[(36,y,z) for y,z in pts]],facecolors='#52565a',edgecolors='#25282b',linewidths=.35,alpha=.95))
 for i in range(len(pts)):
  j=(i+1)%len(pts)
  ax.add_collection3d(Poly3DCollection([[(-36,*pts[i]),(36,*pts[i]),(36,*pts[j]),(-36,*pts[j])]],facecolors='#5c6266',edgecolors='none',alpha=.95))
rail(-1); rail(1)
ax.set_xlim(-43,43); ax.set_ylim(-16,16); ax.set_zlim(-1,15)
ax.set_box_aspect((86,32,16)); ax.view_init(elev=28,azim=-60)
ax.set_xlabel('comprimento (mm)'); ax.set_ylabel('largura (mm)'); ax.set_zlabel('altura (mm)')
ax.set_title('U-Slide V2 — reservatórios recuados e ponte coberta\nTPU entre lâmina e cobrevidro; argolas TPU; trilhos PC')
ax.set_axis_off(); fig.tight_layout()
p='/home/x/projetos/uslide/uslide/revisao/U-Slide_V2_montagem_preview.png'
fig.savefig(p,transparent=False,bbox_inches='tight',facecolor='white')
print(p)
