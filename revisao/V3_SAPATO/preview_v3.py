from pathlib import Path
import zipfile,xml.etree.ElementTree as ET
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import Axes3D
p=Path(__file__).with_name('U-Slide_K1C_V3_SAPATO.3mf')
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
with zipfile.ZipFile(p) as z:
 r=ET.fromstring(z.read('3D/3dmodel.model'))
 o=r.find('./m:resources/m:object[@id="1"]',ns)
 v=[tuple(float(x.get(k)) for k in 'xyz') for x in o.findall('./m:mesh/m:vertices/m:vertex',ns)]
 f=[tuple(int(x.get('v'+str(i))) for i in (1,2,3)) for x in o.findall('./m:mesh/m:triangles/m:triangle',ns)]
fig=plt.figure(figsize=(12,7),dpi=160);ax=fig.add_subplot(111,projection='3d')
# Original printed gasket, with sacrificial toe supports visible.
ax.add_collection3d(Poly3DCollection([[v[i] for i in tri] for tri in f],facecolors='#44aaa1',edgecolors='none',alpha=.96))
# Slide under the TPU and transparent coverslip seated on the 0.4 mm base.
def box(x0,x1,y0,y1,z0,z1,color,alpha):
 q=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
 ff=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 ax.add_collection3d(Poly3DCollection([[q[i] for i in face] for face in ff],facecolors=color,edgecolors='#53636a',linewidths=.25,alpha=alpha))
box(-38.1,38.1,-12.7,12.7,-0.8,0,'#b4bdc2',.22)
box(-30,30,-12,12,.4,.57,'#8dd7f4',.32)
ax.set_xlim(-39,-27);ax.set_ylim(0,11);ax.set_zlim(-.9,10.5)
ax.set_box_aspect((12,11,11.4));ax.view_init(elev=24,azim=-62);ax.set_axis_off()
ax.set_title('V3 — aba “sapato” no poço esquerdo\nAzul claro: cobrevidro; pequenos apoios TPU: cortar antes de inserir',fontsize=13)
fig.tight_layout();out=Path(__file__).with_name('U-Slide_V3_sapato_preview.png');fig.savefig(out,bbox_inches='tight',facecolor='white');print(out)
