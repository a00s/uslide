"""Experimental toolpath reorder; preserves positive spatial extrusion moves verbatim geometrically."""
from pathlib import Path
import re,json,hashlib
from rotas_canal import route
from conecta_preenchimento import connect
src=Path('revisao/SEQUENCIAL/base_costura_traseira.gcode')
out=Path('FINAL_K1C/U-Slide_TPU_POCOS_SEQUENCIAIS_EXPERIMENTAL.gcode')
lines=src.read_text().splitlines(); xyz=dict(X=0.,Y=0.,Z=0.); feed=0.; obj=''; layer=0.; states={}; runs=[]; run=None
feature='Outer wall'; width='0.42'
start=next(i for i,l in enumerate(lines) if l==';LAYER_CHANGE')
for i,line in enumerate(lines):
    s=line.split(';')[0].strip()
    if line.startswith(';Z:'): layer=float(line[3:])
    if line.startswith(';TYPE:'): feature=line[6:]
    if line.startswith(';WIDTH:'): width=line[7:]
    if s.startswith('EXCLUDE_OBJECT_START NAME='): obj=s.split('NAME=')[1]
    if s.startswith(('SET_VELOCITY_LIMIT','M204','M106')):
        key=s.split()[0]
        if key=='M106': key+=' P'+str(re.search(r'\bP(\d+)',s).group(1) if re.search(r'\bP(\d+)',s) else '0')
        elif key=='SET_VELOCITY_LIMIT': key+=' '+s.split()[1].split('=')[0]
        states[key]=s
    cmd=s.split()[0] if s else ''
    if cmd not in ('G1','G2','G3'): continue
    p={k:float(v) for k,v in re.findall(r'([XYZEFIJK])(-?(?:\d*\.)?\d+)',s)}
    old=xyz.copy(); xyz.update({k:v for k,v in p.items() if k in xyz}); feed=p.get('F',feed)
    spatial=any(k in p for k in ('X','Y'))
    deposit=i>=start and spatial and p.get('E',0)>0
    if not deposit:
        if spatial or 'Z' in p or 'E' in p: run=None
        continue
    phase=0 if layer<=.44001 else (1 if 'id_1_copy' in obj else 2 if 'id_2_copy' in obj else 3 if old['X']<110 else 4)
    if run is None or run['phase']!=phase or run['obj']!=obj:
        run={'phase':phase,'obj':obj,'start':old,'moves':[]};runs.append(run)
    canonical=cmd+' '+ ' '.join(f'{k}{xyz[k]:.5f}' for k in ('X','Y','Z'))
    canonical+=' '+ ' '.join(f'{k}{p[k]:.8f}' for k in ('I','J','K','E') if k in p)+f' F{feed:.3f}'
    run['moves'].append((canonical,states.copy(),layer,feature,width))
runs=[r for r in runs if 'id_0_copy' in r['obj']]
ordered=sorted(runs,key=lambda r:r['phase'])
# Start with the existing continuous outer perimeter at the antenna tip,
# before the tiny sacrificial-support strokes in the channel.
antenna_index=next(i for i,r in enumerate(ordered)
    if r['phase']==0 and abs(r['start']['Z']-.2)<1e-5
    and r['start']['X']>160 and r['start']['Y']>120
    and len(r['moves'])>10)
antenna_run=ordered.pop(antenna_index)
# Split the existing perimeter at the left antenna tip; retain every
# deposited segment and its original starting point (including seam gap).
ends=[{k:float(v) for k,v in re.findall(r'([XYZ])(-?[\d.]+)',m[0])} for m in antenna_run['moves']]
cut=next(i+1 for i,pt in enumerate(ends[:-1]) if pt['X']<52.5 and pt['Y']>121.9)
left_tail={**antenna_run,'start':ends[cut-1].copy(),'moves':antenna_run['moves'][cut:]}
original_head={**antenna_run,'moves':antenna_run['moves'][:cut]}
ordered[0:0]=[left_tail,original_head]
ordered,added_links,connection_info=connect(ordered)


prefix=[l for l in lines[:start] if not l.startswith('M73') and not (l.startswith('EXCLUDE_OBJECT_DEFINE') and 'Argola' in l)]
result=['; EXPERIMENTAL: shared base, no auxiliary rings, complete left well, complete right well',
'; Toolhead clearance NOT verified. Custom order; re-slicing the 3MF restores layer order.']+prefix
# Prefix ended retracted by 0.4 mm. Keep all custom travels retracted.
phase=None; active=None; emitted={}; maxz=.2; count=0; lastlayer=None; lastfeature=None; lastwidth=None; lastxy=None; detours=0
labels=['BASE COMUM','ARGOLA ESQUERDA','ARGOLA DIREITA','POCO ESQUERDO COMPLETO','POCO DIREITO COMPLETO']
for r in ordered:
    change=r['phase']!=phase
    if active: result.append('EXCLUDE_OBJECT_END NAME='+active)
    if change: result.append('; PHASE: '+labels[r['phase']])
    # Each well starts a new local height budget; the finished opposite well
    # only requires a high lift during the inter-phase transfer.
    if change: maxz=r['start']['Z']
    phase=r['phase']; active=r['obj']; pt=r['start']
    lift=15. if change else max(maxz,pt['Z'])+.4
    result.append(f'G1 Z{lift:.5f} F600')
    target=(pt['X'],pt['Y'])
    if lastxy is None:
        # START_PRINT can end at an unknown purge-line XY. First position
        # outside the model's front edge, then approach from the left edge.
        result.extend(['; APPROACH OUTSIDE MODEL','G1 Y94 F6000','G1 X49 F6000'])
        lastxy=(49.,94.)
    waypoints=route(lastxy,target)
    if len(waypoints)>1: detours+=1; result.append('; DETOUR AROUND CHANNEL')
    for x,y in waypoints:result.append(f'G1 X{x:.5f} Y{y:.5f} F6000')
    result.extend([f'G1 Z{pt["Z"]:.5f} F600','EXCLUDE_OBJECT_START NAME='+active,'G1 E0.4 F1800'])
    for move,st,z,feature,width in r['moves']:
        if z!=lastlayer: result.extend([';LAYER_CHANGE',f';Z:{z}',f';HEIGHT:{.2 if z==.2 else .08}']);lastlayer=z
        if feature!=lastfeature: result.append(';TYPE:'+feature);lastfeature=feature
        if width!=lastwidth: result.append(';WIDTH:'+width);lastwidth=width
        for key,value in st.items():
            if emitted.get(key)!=value: result.append(value);emitted[key]=value
        result.append(move); maxz=max(maxz,z);count+=1
        coords={k:float(v) for k,v in re.findall(r'([XY])(-?[\d.]+)',move)}
        lastxy=(coords['X'],coords['Y'])
    result.append('G1 E-0.4 F1800')
if active: result.append('EXCLUDE_OBJECT_END NAME='+active)
result.extend(['G1 Z15 F600','M106 S0','M106 P2 S0','END_PRINT','M141 S0','; EXECUTABLE_BLOCK_END'])
config_start=lines.index('; CONFIG_BLOCK_START')
config_end=lines.index('; CONFIG_BLOCK_END',config_start)
result.extend(['']+lines[config_start:config_end+1])
out.write_text('\n'.join(result)+'\n')
# Ensure reordering retained every source deposition command exactly once.
a=sorted(m[0] for r in runs for m in r['moves']);b=sorted(m[0] for r in ordered for m in r['moves'] if m[0] not in added_links);assert a==b
report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'original_deposition_moves_preserved':len(a),'deposition_moves_total':count,'connected_fill':connection_info,'positive_spatial_extrusion_mm':sum(float(re.search(r' E([\d.]+)',m).group(1)) for m in a),'phases':[{ 'name':labels[p],'runs':sum(r['phase']==p for r in ordered)} for p in range(5)],'base_completed_through_z_mm':.44,'first_deposition':'left antenna tip, existing outer perimeter','first_deposition_xyz':ordered[0]['start'],'channel_detours':detours,'clearance_verified':False,'transfer_height_mm':15,'local_travel_lift_mm':.4,'height_budget':'per phase, reset for each well','temperature_C':240,'layer_height_mm':.08,'first_layer_mm':.2}
Path('revisao/SEQUENCIAL/resultado.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
