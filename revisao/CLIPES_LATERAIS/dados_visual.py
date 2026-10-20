from pathlib import Path
import trimesh,json,numpy as np,manifold3d as md
P=Path(__file__).resolve().parent
out={}
for key,f in [('TPU','../SELAGEM/U-Slide_selado.stl'),('clip','Clipe_U_direito_montado.stl')]:
 m=trimesh.load(P/f)
 if key=='TPU':
  a=md.Manifold(md.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32))).simplify(.04).to_mesh();m=trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=False)
 out[key]=m.triangles.tolist()
(P/'visual.json').write_text(json.dumps(out))
