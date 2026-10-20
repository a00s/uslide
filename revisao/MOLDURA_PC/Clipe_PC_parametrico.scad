// Clipe em C para a borda longa da lamina: PC, imprimir DE LADO, sem suportes.
// Esta vista e a orientacao de impressao. X/Y do desenho sao Y/Z na montagem.
$fn=128;
largura=2.4;             // espessura da peca no eixo longitudinal da lamina
pre_carga=0.15;          // reducao da abertura livre em relacao ao conjunto nominal
altura_TPU=7.189333365;  // altura real da regiao pressionada no sapato
folha=0.8;
z_superior=altura_TPU-pre_carga+0.4+folha/2;
module retangulo_arredondado(x0,y0,x1,y1,r) {
 hull() for(x=[x0+r,x1-r],y=[y0+r,y1-r]) translate([x,y]) circle(r=r);
}
linear_extrude(height=largura) union() {
 retangulo_arredondado(-13.1,-3.2,14.5,-1.2,.3);
 retangulo_arredondado(12.9,-3.2,14.5,z_superior+folha/2,.35);
 retangulo_arredondado(4.0,z_superior-folha/2,14.5,z_superior+folha/2,.25);
 translate([5.325,altura_TPU-pre_carga+.8]) circle(r=.8);
 translate([5.325,-1.6]) circle(r=.7);
}
