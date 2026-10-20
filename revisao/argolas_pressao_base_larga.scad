// Variante experimental das argolas originais para distribuir a pressão.
// Unidades em mm. O anel original é preservado acima de uma sapata larga,
// plana por baixo e alargada transversalmente para ficar dentro da lâmina.
// O PC é a opção preferível para o aquecimento, sujeito à temperatura do processo.
$fn = 128;
source_ring = "argola_original_referencia.stl";
ring_cx = 48.97472;
ring_cz = 27.787925;
foot_inner_r = 4.16;
foot_outer_rx = 5.6;
foot_outer_rz = 7.2;
foot_top_rx = 5.3;
foot_top_rz = 6.9;
foot_h = 0.8;
slot_width = 8.0; // abertura orientada para o canal (lado +X local)
pair_spacing = 19.0;

module c_foot() {
    difference() {
        // Sapata elíptica: alarga nos lados da lâmina sem crescer na direção
        // dos extremos, onde os reservatórios já ficam perto da borda.
        scale([foot_outer_rx,1,foot_outer_rz]) rotate([-90,0,0])
            linear_extrude(height=foot_h,
                scale=[foot_top_rx/foot_outer_rx, foot_top_rz/foot_outer_rz])
                circle(r=1);
        translate([0,-0.05,0]) rotate([-90,0,0])
            cylinder(h=foot_h+0.1, r=foot_inner_r);
        // Mantém a abertura C voltada para o canal, sem uma ponte sobre o acesso.
        translate([foot_outer_rx/2, foot_h/2, 0])
            cube([foot_outer_rx+0.2, foot_h+0.2, slot_width], center=true);
    }
}

module one_ring() {
    union() {
        translate([ring_cx,0,ring_cz]) import(source_ring, convexity=10);
        c_foot();
    }
}

// As argolas originais estão no plano XZ, com altura no eixo Y.
// Rotaciona para assentarem planas na mesa do fatiador (Z é a altura).
module print_pair() {
    // Os dois C ficam abertos um para o outro, na direção do canal.
    translate([-pair_spacing/2,0,0]) rotate([90,0,0]) one_ring();
    translate([ pair_spacing/2,0,0]) rotate([90,0,0])
        mirror([1,0,0]) one_ring();
}

// Modo de visualização: "print" ou "assembled_preview".
view_mode = "print";
if (view_mode == "print") print_pair();
else if (view_mode == "assembly_preview") {
    // Visualiza a junta original com as argolas encaixadas nos poços.
    color([0.55,0.62,0.66,0.8]) rotate([90,0,0])
        import("junta_tpu_original_referencia.stl", convexity=10);
    color("gold") rotate([90,0,0]) {
        translate([-33.10485144,10,-5.32339475]) one_ring();
        translate([ 33.10485144,10,-5.32339475]) mirror([1,0,0]) one_ring();
    }
} else color("gold") print_pair();
