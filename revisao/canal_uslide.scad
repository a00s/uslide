// Modelo experimental inspirado no ibidi µ-Slide I Luer.
// Unidades: mm. Exportação para impressão: view_mode="print" e F6 > F7 STL.
$fn=120;

// Lâmina e cobrevidro informados pelo usuário
slide_w=25.4; slide_l=76.2;
cover_w=24; cover_l=60;

// Geometria inicial, ajustável após validar a montagem real
channel_l=50;              // canal reto longitudinal entre poços
channel_w=5;
channel_h=0.8;              // altura livre da câmara sobre o coverslip
reservoir_d=8;
reservoir_h=4;
center_x=0;
end_x=channel_l/2;
base_t=0.8;                 // membrana TPU sob cavidade
wall_w=1.2;
seal_w=1.8;
seal_h=0.55;
seal_gap=0.35;
edge_margin=2;
view_mode="preview";       // "preview", "print", "plan"

module wet_footprint() {
    union() {
        // Canal reto conecta livremente os dois reservatórios.
        square([channel_l,channel_w],center=true);
        translate([-end_x,0]) circle(d=reservoir_d);
        translate([ end_x,0]) circle(d=reservoir_d);
    }
}

module body_footprint() {
    intersection() {
        offset(delta=wall_w+seal_gap+seal_w+0.5) wet_footprint();
        square([cover_l-2*edge_margin,cover_w-2*edge_margin],center=true);
    }
}

module continuous_seal() {
    difference() {
        offset(delta=wall_w+seal_gap+seal_w) wet_footprint();
        offset(delta=wall_w+seal_gap) wet_footprint();
    }
}

module insert() {
    // Base: impressa sobre a placa; o coverslip fecha a cavidade pelo lado aberto.
    linear_extrude(height=base_t) body_footprint();

    // Parede perimetral do canal e dos poços: área interna fica aberta e contínua.
    translate([0,0,base_t])
        linear_extrude(height=reservoir_h)
            difference() {
                offset(delta=wall_w) wet_footprint();
                wet_footprint();
            }

    // Selo contínuo fora da parede, sem ponte cruzando o caminho do líquido.
    translate([0,0,base_t]) linear_extrude(height=seal_h) continuous_seal();
}

if (view_mode=="print") insert();
else if (view_mode=="plan") projection(cut=true) insert();
else {
    color([0.7,0.86,0.95,0.55]) translate([0,0,-0.17])
        linear_extrude(height=0.17) square([cover_l,cover_w],center=true);
    color([0.9,0.28,0.2]) insert();
}
