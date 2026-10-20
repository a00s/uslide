from pathlib import Path
import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
P=Path(__file__).resolve().parent;d=json.loads((P/'visual.json').read_text())
f=plt.figure(figsize=(16,7),facecolor='white');a=f.add_subplot(131,projection='3d');b=f.add_subplot(132,projection='3d');c=f.add_subplot(133,projection='3d')
def box(x0,x1,y0,y1,z0,z1):
 v=np.array([[x,y,z] for z in [z0,z1] for y in [y0,y1] for x in [x0,x1]])
 return [[v[i] for i in face] for face in [[0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]]]
for ax in [a,b]:
 ax.add_collection3d(Poly3DCollection(box(24,38.1,-12.7,12.7,-.9,0),facecolor='#a5c6de',alpha=.28,edgecolor='#7e9bad',linewidth=.4))
 ax.add_collection3d(Poly3DCollection(box(24,30,-12,12,.4,.55),facecolor='#75bed6',alpha=.35,edgecolor='#4893ae',linewidth=.4))
 t=np.array(d['TPU']);t=t[np.all(t[:,:,0]>24,axis=1)&np.all(t[:,:,0]<38.2,axis=1)]
 ax.add_collection3d(Poly3DCollection(t,facecolor='#3aafa2',alpha=.32,linewidth=0))
 ax.add_collection3d(Poly3DCollection(d['clip'],facecolor='#d69a38',edgecolor='none',linewidth=0))
 ax.set_xlim(24,46);ax.set_ylim(-14,14);ax.set_zlim(-2,11);ax.set_box_aspect((22,28,13));ax.set_axis_off()
a.view_init(28,-52);b.view_init(22,145)
a.set_title('Entrada pela extremidade do slide',fontsize=13,pad=0);b.set_title('Pega externa e apoio sob o vidro',fontsize=13,pad=0)
c.add_collection3d(Poly3DCollection(d['clip'],facecolor='#d69a38',edgecolor='#9f732d',linewidth=.12))
c.set_xlim(27,46);c.set_ylim(-14,14);c.set_zlim(-2,4);c.set_box_aspect((19,28,6));c.view_init(36,-55);c.set_axis_off();c.set_title('Peça isolada: lateral fechada',fontsize=13,pad=0)
f.suptitle('Presilha com parede externa — sem relevo de argola',fontsize=17,y=.95)
f.text(.5,.09,'Dourado: PLA   •   Verde: TPU   •   Azul: vidros\nApoios superior e inferior com 25,4 mm de largura; recorte superior deixa o canal livre.',ha='center',fontsize=11)
f.subplots_adjust(left=0,right=1,top=.88,bottom=.13,wspace=0)
f.savefig(P/'clipes_u_preview.png',dpi=160)
