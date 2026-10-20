"""PC joined retaining frame, linear beam sizing and nominal assembly export.
Assumed E=2000 MPa; not a measured printed-PC or glass-stress model.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
import manifold3d as md
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
P=Path(__file__).resolve().parent
p=json.loads((P/'parametros_clips.json').read_text())
b=2.4;H=p['foot_roof_contact_height_mm'];zu=p['upper_leaf_center_z_mm'];zl=-2.2
spine=13.7;yu=5.325;yc=9.8;zc=.88
nodes=[];edges=[]
def node(y,z):
 for i,a in enumerate(nodes):
  if np.linalg.norm(np.array(a)-[y,z])<1e-8:return i
 nodes.append([y,z]);return len(nodes)-1
def path(pts,t):
 for a,c in zip(pts[:-1],pts[1:]):
  a=np.array(a);c=np.array(c);n=int(np.ceil(np.linalg.norm(c-a)/.3));ids=[node(*(a+(c-a)*f)) for f in np.linspace(0,1,n+1)]
  edges.extend((i,j,t) for i,j in zip(ids[:-1],ids[1:]))
path([[4,zu],[yu,zu],[spine,zu]],.8)
path([[spine,zu],[spine,zc],[spine,zl]],1.6)
path([[yc,zc],[spine,zc]],.4)
path([[spine,zl],[yc,zl],[yu,zl],[-13.1,zl]],2.)
ui=node(yu,zu);ci=node(yc,zc);li=node(yu,zl);lc=node(yc,zl);ref=node(spine,zl)
nodes=np.array(nodes);N=len(nodes);E=2000.;K=np.zeros((3*N,3*N));els=[]
for i,j,t in edges:
 d=nodes[j]-nodes[i];L=np.linalg.norm(d);c,s=d/L;A=b*t;I=b*t**3/12
 k=E*np.array([[A/L,0,0,-A/L,0,0],[0,12*I/L**3,6*I/L**2,0,-12*I/L**3,6*I/L**2],[0,6*I/L**2,4*I/L,0,-6*I/L**2,2*I/L],[-A/L,0,0,A/L,0,0],[0,-12*I/L**3,-6*I/L**2,0,12*I/L**3,-6*I/L**2],[0,6*I/L**2,2*I/L,0,-6*I/L**2,4*I/L]])
 T=np.array([[c,s,0,0,0,0],[-s,c,0,0,0,0],[0,0,1,0,0,0],[0,0,0,c,s,0],[0,0,0,-s,c,0],[0,0,0,0,0,1]])
 ids=np.array([3*i,3*i+1,3*i+2,3*j,3*j+1,3*j+2]);K[np.ix_(ids,ids)]+=T.T@k@T;els.append((t,L,T,k,ids))
profile=unary_union([Polygon(p['profile']),Polygon([[yc,zc-.2],[14.2,zc-.2],[14.2,zc+.2],[yc,zc+.2]]),Point(yc,zc).buffer(.5,quad_segs=32),Point(yc,-1.6).buffer(.7,quad_segs=32)])
assert profile.geom_type=='Polygon' and not profile.interiors
coords=np.array(orient(profile,sign=1).exterior.coords)[:-1]
dense=[]
for a,c in zip(coords,np.roll(coords,-1,axis=0)):
 for f in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(c-a)/.1))),endpoint=False):dense.append(a+(c-a)*f)
dense=np.array(dense)
def deform(U):
 out=[]
 for pt in dense:
  best=None
  for i,j,t in edges:
   a=nodes[i];d=nodes[j]-a;f=np.clip(np.dot(pt-a,d)/np.dot(d,d),0,1);near=a+f*d;dist=np.linalg.norm(pt-near)
   if best is None or dist<best[0]:best=(dist,i,j,f,near)
  _,i,j,f,near=best;u=(1-f)*U[i]+f*U[j];r=pt-near
  out.append(pt+u[:2]+u[2]*np.array([-r[1],r[0]]))
 return orient(Polygon(out).buffer(0),sign=1)
def manifold_from_poly(poly,sx):
 a=md.CrossSection([list(poly.exterior.coords)[:-1]]).extrude(b).to_mesh();v=np.array(a.vert_properties[:,:3]);v=np.column_stack([v[:,2]-b/2+sx,v[:,0]-.2,v[:,1]])
 return md.Manifold(md.Mesh(v.astype(np.float32),np.asarray(a.tri_verts,dtype=np.uint32)))
def joined(poly):
 s=manifold_from_poly(poly,-26.4)+manifold_from_poly(poly,26.4)
 # Two low external rails form a base perimeter with end crossbars.
 # Tops remain below lower glass; inner sides clear y=+-12.7 mm.
 for y in [-13.55,13.6]:
  s=s+md.Manifold.cube([55.2,1.3,1.3],center=True).translate([0,y,-2.35])
 assert s.status()==md.Error.NoError and len(s.decompose())==1
 a=s.to_mesh();return trimesh.Trimesh(a.vert_properties[:,:3],a.tri_verts,process=True)
free=joined(orient(profile,sign=1));free.export(P/'Moldura_PC_livre.stl')
# Rear edge on the build plate: longitudinal rails are printed along X.
# Front rail is a 50 mm bridge in this orientation: requires explicit support.
# Keep orientation decision pending; do not label this mesh support-free.
rows=[]
for thick in [.8,.9,1.0]:
 for cover in [.13,.16]:
  # Two lower glass contacts supply moment equilibrium without fictitious torque.
  fixed={3*ui+1:.15,3*ci+1:.15+cover-.13,3*li+1:.9-thick,3*lc+1:.9-thick,3*ref:0.}
  ids=np.array(sorted(fixed));fr=np.setdiff1d(np.arange(3*N),ids);U=np.zeros(3*N);U[ids]=[fixed[i] for i in ids]
  U[fr]=np.linalg.solve(K[np.ix_(fr,fr)],-K[np.ix_(fr,ids)]@U[ids]);R=K@U
  reactions=[float(R[3*i+1]) for i in [ui,ci,li,lc]]
  strain=0.
  for t,L,T,k,idx in els:
   F=k@(T@U[idx]);strain=max(strain,max(abs(F[2]),abs(F[5]))*(t/2)/(b*t**3/12)/E)
  row={'slide_mm':thick,'cover_mm':cover,'contact_forces_N_roof_cover_lower_roof_lower_cover':reactions,'max_beam_bending_strain':float(strain),'force_balance_N':float(sum(reactions)),'contacts_compressive':bool(min(reactions[:2])>0 and max(reactions[2:])<0)}
  rows.append(row);print(row)
  if cover==.13:
   m=joined(deform(U.reshape(-1,3)));m.export(P/f'Moldura_PC_montada_{thick:.1f}.stl')
report={'status':'linear estimate; not measured force, printed PC and glass stresses unverified','assumed_E_MPa':E,'leaf_thickness_mm':.4,'cover_contact_world_y_mm':yc-.2,'preload_nominal_mm':.15,'new_leaves_single_line_need_slicing_review':True,'results':rows,'microscope_clearance':'objective dimensions missing','print_orientation':'pending support minimization'}
(P/'moldura_flexao.json').write_text(json.dumps(report,indent=2))
