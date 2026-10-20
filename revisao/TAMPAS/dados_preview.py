from pathlib import Path
import trimesh,json
P=Path(__file__).resolve().parent;out={}
for key,name in [('old','Tampa_pequena_referencia.stl'),('new','Tampa_esquerda_imprimir.stl')]:
 m=trimesh.load(P/name);out[key]={'triangles':m.triangles.tolist(),'bounds':m.bounds.tolist()}
(P/'preview_dados.json').write_text(json.dumps(out))
