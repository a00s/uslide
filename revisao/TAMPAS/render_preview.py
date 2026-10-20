from pathlib import Path
import json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
P=Path(__file__).resolve().parent;d=json.loads((P/'preview_dados.json').read_text());f=plt.figure(figsize=(11,6),facecolor='white')
for i,key,title in [(1,'old','Antes: tampa rasa, pega estreita'),(2,'new','Agora: saia longa e pega larga')]:
 ax=f.add_subplot(1,2,i,projection='3d');ax.add_collection3d(Poly3DCollection(d[key]['triangles'],facecolor='#d89c38',edgecolor='#966e25',linewidth=.07));ax.set_xlim(-8,8);ax.set_ylim(-8,10);ax.set_zlim(0,10);ax.set_box_aspect((16,18,10));ax.view_init(28,-52);ax.set_axis_off();ax.set_title(title,fontsize=13)
f.suptitle('Tampinhas PLA — mesma escala, abertura voltada para cima',fontsize=15)
f.text(.5,.08,'Envolvem 7,6 mm da altura externa do poço • três nervuras de retenção\nRespiro preservado • altura acima do poço mantida • sem suportes',ha='center',fontsize=11)
f.subplots_adjust(left=0,right=1,bottom=.13,top=.88,wspace=.03);f.savefig(P/'tampa_preview.png',dpi=160)
