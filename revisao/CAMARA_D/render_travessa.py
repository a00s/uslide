from pathlib import Path
import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
P=Path(__file__).resolve().parent;data=json.loads((P/'travessa_cortes.json').read_text())
f,axs=plt.subplots(1,2,figsize=(10,5),facecolor='white')
for ax,key,title in zip(axs,['antes','agora'],['Antes: travessa na junção','Agora: passagem aberta']):
 for q in data[key]:
  q=np.array(q);signed=np.sum(q[:,0]*np.roll(q[:,1],-1)-np.roll(q[:,0],-1)*q[:,1]);ax.add_patch(Polygon(q,facecolor='#49ac9c' if signed>0 else 'white',edgecolor='#267367',linewidth=.6))
 ax.set_xlim(25,39);ax.set_ylim(-1,12);ax.set_aspect('equal');ax.set_axis_off();ax.set_title(title)
f.suptitle('Corte horizontal do poço direito a 0,42 mm — correção espelhada nos dois poços')
f.tight_layout();f.savefig(P/'travessa_antes_depois.png',dpi=160)
