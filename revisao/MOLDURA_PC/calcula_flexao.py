"""Small-deflection 2D frame model, an estimate rather than a PC material test.
Euler-Bernoulli beams: E=2000 MPa assumed, PC stiffness not measured.
The two prescribed vertical contacts open the C. An unloaded reference
restrains horizontal rigid translation/rotation only; net force/moment audited.
"""
from pathlib import Path
import json,numpy as np,trimesh,manifold3d as md
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
HERE=Path(__file__).resolve().parent
p=json.loads((HERE/'parametros_clips.json').read_text());b=p['clip_width_x_mm'];H=p['foot_roof_contact_height_mm'];yu=p['pad_center_y_mm'];zu=p['upper_leaf_center_z_mm'];zl=p['lower_bar_center_z_mm'];spine=13.7
nodes=[];edges=[]
def add(y,z):
 for i,q in enumerate(nodes):
  if np.linalg.norm(np.array(q)-[y,z])<1e-8:return i
 nodes.append([y,z]);return len(nodes)-1
def path(points,t):
 last=None
 for a,c in zip(points[:-1],points[1:]):
  a=np.array(a);c=np.array(c);n=int(np.ceil(np.linalg.norm(c-a)/.35))
  ids=[add(*(a+(c-a)*f)) for f in np.linspace(0,1,n+1)]
  for i,j in zip(ids[:-1],ids[1:]):edges.append((i,j,t))
path([[4,zu],[yu,zu],[spine,zu]],p['upper_leaf_thickness_mm'])
path([[spine,zu],[spine,zl]],p['spine_thickness_mm'])
path([[spine,zl],[yu,zl],[-13.1,zl]],p['lower_bar_thickness_mm'])
nodes=np.array(nodes);N=len(nodes);E=2000.;K=np.zeros((3*N,3*N));els=[]
for i,j,t in edges:
 d=nodes[j]-nodes[i];L=np.linalg.norm(d);c,s=d/L;A=b*t;I=b*t**3/12
 k=E*np.array([[A/L,0,0,-A/L,0,0],[0,12*I/L**3,6*I/L**2,0,-12*I/L**3,6*I/L**2],[0,6*I/L**2,4*I/L,0,-6*I/L**2,2*I/L],[-A/L,0,0,A/L,0,0],[0,-12*I/L**3,-6*I/L**2,0,12*I/L**3,-6*I/L**2],[0,6*I/L**2,2*I/L,0,-6*I/L**2,4*I/L]])
 T=np.array([[c,s,0,0,0,0],[-s,c,0,0,0,0],[0,0,1,0,0,0],[0,0,0,c,s,0],[0,0,0,-s,c,0],[0,0,0,0,0,1]])
 ids=np.array([3*i,3*i+1,3*i+2,3*j,3*j+1,3*j+2]);K[np.ix_(ids,ids)]+=T.T@k@T;els.append((i,j,t,L,T,k,ids))
u_idx=add(yu,zu);l_idx=add(yu,zl);ref=add(spine,zu);assert len(nodes)==N
results=[];solns={}
for thick in [.8,.9,1.0]:
 fixed={3*u_idx+1:p['preload_at_0_9mm_slide_mm'],3*l_idx+1:.9-thick,3*ref:0.,3*ref+2:0.}
 ids=np.array(sorted(fixed));free=np.setdiff1d(np.arange(3*N),ids);U=np.zeros(3*N)
 U[ids]=[fixed[i] for i in ids];U[free]=np.linalg.solve(K[np.ix_(free,free)],-K[np.ix_(free,ids)]@U[ids]);reaction=K@U
 max_strain=0.;max_moment=0.
 for i,j,t,L,T,k,idx in els:
  force=k@(T@U[idx]);stress=max(abs(force[2]),abs(force[5]))*(t/2)/(b*t**3/12);strain=stress/E;max_strain=max(max_strain,strain)
 down=float(abs(reaction[3*u_idx+1]));balance=float(abs(reaction[3*u_idx+1]+reaction[3*l_idx+1]))
 row={'slide_thickness_mm':thick,'required_jaw_opening_mm':round(.15+thick-.9,8),'estimated_downward_force_per_clip_N':down,'estimated_two_clips_force_N':2*down,'max_bending_strain':max_strain,'force_balance_error_N':balance,'reference_horizontal_reaction_N':float(reaction[3*ref]),'reference_moment_Nmm':float(reaction[3*ref+2])}
 assert down>0 and max_strain<.01 and balance<1e-6
 results.append(row);solns[str(thick)]=U.reshape(-1,3).tolist();print(row)
# Smoothly map the profile through beam translations and rotations. The rigid
# portions are approximated by the displacement of their nearest beam axis.
def deform(coords,U):
 out=[]
 for point in coords:
  best=None
  for i,j,t in edges:
   a=nodes[i];d=nodes[j]-a;f=np.clip(np.dot(point-a,d)/np.dot(d,d),0,1);near=a+f*d;dist=np.linalg.norm(point-near)
   if best is None or dist<best[0]:best=(dist,i,j,f,near)
  _,i,j,f,near=best;u=(1-f)*U[i]+f*U[j];r=point-near
  out.append(point+u[:2]+u[2]*np.array([-r[1],r[0]]))
 return np.array(out)
coords=np.array(p['profile']);dense=[]
for a,c in zip(coords,np.roll(coords,-1,axis=0)):
 for f in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(c-a)/.12))),endpoint=False):dense.append(a+(c-a)*f)
dense=np.array(dense)
for thick in [.8,.9,1.]:
 deformed=deform(dense,np.array(solns[str(thick)]));poly=orient(Polygon(deformed).buffer(0),sign=1);assert poly.geom_type=='Polygon' and poly.is_valid
 cs=md.CrossSection([list(poly.exterior.coords)[:-1]])
 m=cs.extrude(b).to_mesh();vs=np.array(m.vert_properties[:,:3]);a,bb,c=vs.T
 for side in [-1,1]:
  sx=p['clip_centers_x_mm'][0 if side<0 else 1]
  v=np.column_stack([c-b/2+sx,a+p.get('assembly_y_offset_mm',0),bb]);mesh=trimesh.Trimesh(v,m.tri_verts,process=True)
  mesh.export(HERE/f'Clipe_PC_montado_{"esquerdo" if side<0 else "direito"}_{thick:.1f}.stl')
report={'method':'Linear small-deflection Euler-Bernoulli 2D frame; stiffness is an estimate, not a measured print force or validated contact FEA.','assumed_PC_E_MPa':E,'print_orientation':'C profile flat in the print XY plane, flexion within layer plane; extrusion 2.4 mm','results':results}
(HERE/'flexao_clips.json').write_text(json.dumps(report,indent=2))
