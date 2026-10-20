"""Shortest visibility route around the U opening (no guarantee against ooze)."""
from pathlib import Path
import json,math,heapq
from shapely.geometry import shape,LineString,Point
from shapely.affinity import translate
from shapely.ops import nearest_points
channel=translate(shape(json.loads(Path('revisao/SELAGEM/canal_arredondado.json').read_text())),110,110)
# Small conservative margin; simplify only after buffering, then restore clearance.
obstacle=channel.buffer(.4).simplify(.12,preserve_topology=True).buffer(.15,join_style=2)
vertices=list(obstacle.exterior.coords)[:-1]
interior=obstacle.buffer(-.00001)
def clear(a,b):return not LineString([a,b]).intersects(interior)
adj=[[] for _ in vertices]
for i,a in enumerate(vertices):
 for j in range(i):
  b=vertices[j]
  if clear(a,b):
   w=math.dist(a,b);adj[i].append((j,w));adj[j].append((i,w))
def _visibility_route(a,b):
 a=tuple(a);b=tuple(b)
 if clear(a,b):return [b]
 # Exit/enter embedded support endpoints locally; NEVER use a straight
 # cross-channel fallback for the entire transfer.
 original_a,original_b=a,b
 def escape(p):
  if not obstacle.contains(Point(p)):return p
  q=nearest_points(Point(p),obstacle.exterior)[1]
  return (q.x,q.y)
 a,b=escape(a),escape(b)
 if a!=original_a or b!=original_b:
  middle=_visibility_route(a,b) if math.dist(a,b)>1e-8 else []
  return ([a] if a!=original_a else [])+middle+([original_b] if b!=original_b else [])

 n=len(vertices);g=[list(e) for e in adj]+[[],[]];pts=vertices+[a,b]
 for i,p in enumerate(vertices):
  for j,q in [(n,a),(n+1,b)]:
   if clear(p,q):w=math.dist(p,q);g[i].append((j,w));g[j].append((i,w))
 dist={n:0};prev={};heap=[(0,n)]
 while heap:
  cost,u=heapq.heappop(heap)
  if cost!=dist[u]:continue
  if u==n+1:break
  for v,w in g[u]:
   if cost+w<dist.get(v,float('inf')):dist[v]=cost+w;prev[v]=u;heapq.heappush(heap,(cost+w,v))
 if n+1 not in prev:raise RuntimeError('No route around channel')
 ids=[];u=n+1
 while u!=n:ids.append(u);u=prev[u]
 return [pts[i] for i in reversed(ids)]


def route(a,b):
 a,b=tuple(a),tuple(b)
 changes_side=(a[0]-110)*(b[0]-110)<0 and abs(a[0]-b[0])>20
 if clear(a,b) and not changes_side:return [b]
 # Force transfers into a corridor beyond the rear outer edge of the
 # WHOLE body (Ymax=122.325), instead of cutting across the central tongue.
 rear_a=(a[0],125.0);rear_b=(b[0],125.0)
 return _visibility_route(a,rear_a)+[rear_b]+_visibility_route(rear_b,b)
