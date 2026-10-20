from pathlib import Path
import json,re,numpy as np
from shapely.geometry import shape,Polygon,box,mapping
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
P=Path(__file__).resolve().parent;S=P.parent/'SELAGEM'
old=shape(json.loads((P/'canal_U_anterior.json').read_text()))
# A thin straight closure joins both old upper legs. Filling the enclosed
# island retains the original lower U and interfaces with both wells.
closed=unary_union([old,box(-28.5,7.88,28.5,7.90)])
assert closed.geom_type=='Polygon' and len(closed.interiors)==1
chamber=Polygon(closed.exterior)
s=(P/'base_U_anterior.scad').read_text();pts=json.loads(re.search(r'points=(\[.*?\]),paths=',s).group(1));paths=json.loads(re.search(r'paths=(\[.*\])\);',s).group(1))
outer=Polygon([pts[i] for i in paths[0]])
plate=orient(outer.difference(chamber),1)
assert plate.geom_type=='Polygon' and len(plate.interiors)==1
points=[];rings=[]
for ring in [plate.exterior,*plate.interiors]:
 q=np.asarray(ring.coords)[:-1].round(7).tolist();rings.append(list(range(len(points),len(points)+len(q))));points.extend(q)
(S/'base_arredondada_2d.scad').write_text('// Camara D deitada, sem ilha. Mesma borda U inferior e pocos.\nmodule original_base_2d() { polygon(points='+json.dumps(points)+',paths='+json.dumps(rings)+'); }\n')
(S/'canal_arredondado.json').write_text(json.dumps(mapping(chamber)))
(P/'camara_D.json').write_text(json.dumps(mapping(chamber)))
info={'shape':'lying D without center island','top_straight_y_mm':7.9,'base_height_mm':.4,'old_channel_area_mm2':old.area,'chamber_area_mm2':chamber.area,'area_ratio':chamber.area/old.area,'old_volume_at_0_4mm_uL':old.area*.4,'new_volume_at_0_4mm_uL':chamber.area*.4,'bounds_mm':chamber.bounds,'wells_clips_caps_unchanged':True,'seal_and_optics_not_physically_validated':True}
(P/'camara_D_info.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
