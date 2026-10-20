// V3 concept: a tapered shoe-shaped lip at the open mouth of each reservoir.
// Based on the original K1C body. Units: mm.
$fn=48;
body_file="original_body_K1C.stl";
well_x=33.75;
well_y=5.325;
cover_edge=30.0;
cover_thickness=0.17;       // assumed standard coverslip #1.5; confirm actual glass
base_t=0.40;
clearance=0.12;
lip_bottom=base_t+cover_thickness+clearance; // 0.69 mm in print coordinates
lip_thickness=0.40;
well_top=10.0;
show_original=true;

module root_cap(side) {
    // A short saddle overlaps the opening in the original C collar.
    translate([side*well_x-side*3.0,well_y,6.6])
        cube([0.9,5.9,well_top-6.6],center=true);
}
module tip_cap(side) {
    // Small diamond toe projects about 1 mm over the coverslip edge.
    translate([side*well_x,well_y,lip_bottom])
        rotate([0,0,side<0 ? 0 : 180])
            linear_extrude(height=lip_thickness)
                polygon(points=[[3.8,-2.5],[4.8,0],[3.8,2.5],[2.8,0]]);
}
module shoe(side) {
    // Convex tapered bridge between collar and diamond-shaped toe.
    hull() {
        root_cap(side);
        tip_cap(side);
    }
    // Two narrow, sacrificial TPU support posts. Cut them after printing to
    // open a 0.29 mm insertion gap under the toe. Posts sit outside the 5 mm flow path.
    for (sy=[-1,1])
        translate([side*well_x-side*4.55,well_y+sy*2.95,(base_t+lip_bottom)/2])
            cube([0.55,0.55,lip_bottom-base_t],center=true);
}

union() {
    if (show_original) import(body_file, convexity=10);
    for (side=[-1,1]) shoe(side);
}
