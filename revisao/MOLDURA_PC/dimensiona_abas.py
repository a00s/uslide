"""Preliminary sizing of coverglass leaves, isolated cantilever approximation.
Does not validate glass stresses, print anisotropy, creep or full frame contact.
"""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
E=2000.0;b=2.4;L=4.5;t=.4;preload=.15
rows=[]
for slide in [.8,.9,1.0]:
 for cover in [.13,.16]:
  delta=preload+slide-.9+cover-.13
  I=b*t**3/12
  force=3*E*I*delta/L**3
  strain=3*t*delta/(2*L**2)
  rows.append({'slide_mm':slide,'cover_mm':cover,'nominal_opening_mm':round(delta,5),'isolated_leaf_force_N':force,'isolated_leaf_root_strain':strain})
r={'status':'preliminary sizing, not full frame contact verification','model':'isolated Euler-Bernoulli cantilever with rigid base; E assumed 2000 MPa','leaf_width_mm':b,'leaf_length_mm':L,'leaf_thickness_mm':t,'free_cover_pad_height_mm':.53-preload,'root_fillet_required':True,'minimum_stated_nozzle_mm':.4,'single_line_leaf_requires_slicer_review':True,'results':rows,'remaining':['coupled multi-contact frame flexion','objective envelope dimensions','actual PC print and glass contact trial']}
(P/'dimensionamento_abas.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
