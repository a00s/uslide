from pathlib import Path
import json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle,Rectangle
P=Path(__file__).resolve().parent
fig,axs=plt.subplots(2,1,figsize=(12,6.5),facecolor='white')
for ax,file,title in zip(axs,['canal_U_anterior.json','camara_D.json'],['Antes: canal em U','Agora: câmara D, sem ilha central']):
 ax.add_patch(Rectangle((-38.1,-12.7),76.2,25.4,facecolor='#49ac9c',edgecolor='#287367',linewidth=1.5))
 poly=json.loads((P/file).read_text())['coordinates'][0];ax.add_patch(Polygon(poly,facecolor='#d4f1fb',edgecolor='#267f9e',linewidth=1))
 for x in [-33,33]:ax.add_patch(Circle((x,5.325),4.5,facecolor='#49ac9c',edgecolor='#287367',linewidth=1.5));ax.add_patch(Circle((x,5.325),3.9,facecolor='#d4f1fb',edgecolor='#267f9e'))
 ax.add_patch(Rectangle((-30,-12),60,24,fill=False,edgecolor='#616c75',linestyle='--',linewidth=1))
 ax.set_xlim(-40,40);ax.set_ylim(-14,15);ax.set_aspect('equal');ax.set_axis_off();ax.set_title(title,fontsize=14)
fig.text(.5,.025,'Verde: TPU • Azul: espaço para líquido/células • Tracejado: cobrevidro 60 × 24 mm\nAltura da câmara: 0,4 mm; poços e conjunto externo preservados.',ha='center',fontsize=11)
fig.tight_layout(rect=(0,.09,1,1));fig.savefig(P/'camara_D_preview.png',dpi=160)
