from pathlib import Path
import trimesh,json
here=Path(__file__).resolve().parent
visual=here.parent/'VISUAL/U-Slide_visual.html'
old=visual.read_text();scripts=old.split('<script>')
lib=scripts[1].split('</script>')[0];controls=scripts[2].split('</script>')[0]
def load(path):
 m=trimesh.load(path);return {'v':m.vertices.round(6).tolist(),'f':m.faces.tolist()}
data={'body':load(here/'U-Slide_selado.stl'),'printed':load(here/'U-Slide_para_imprimir.stl'),'supports':load(here/'apoios_cortar.stl'),'original':load(here.parent/'V3_SAPATO/original_body_K1C.stl'),'bottom':load(here/'vidro_inferior.stl'),'cover':load(here/'cobrevidro.stl'),'water':{str(z):load(here/f'liquido_{z}mm.stl') for z in [1,5,9]},'report':json.loads((here/'verificacao_liquido.json').read_text())}
data['channelInfo']=json.loads((here/'canal_arredondado_info.json').read_text())
frame=here.parent/'CLIPES_LATERAIS'
if (frame/'Clipe_U_esquerdo_montado.stl').exists():
 data['clips']=[load(frame/'Clipe_U_esquerdo_montado.stl'),load(frame/'Clipe_U_direito_montado.stl')]
 data['pcPrints']=[load(frame/'Clipe_U_esquerdo_imprimir.stl'),load(frame/'Clipe_U_direito_imprimir.stl')]
 data['frameReport']=json.loads((frame/'clipes_u_info.json').read_text())
template=(here/'visual_montagem_template.html').read_text()
visual.write_text(template.replace('/*THREE*/',lib).replace('/*ORBIT*/',controls).replace('/*ASSEMBLY*/',json.dumps(data,separators=(',',':'))))
print(visual,visual.stat().st_size)
