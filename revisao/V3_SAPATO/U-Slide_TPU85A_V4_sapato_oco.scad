// V4: hollow, flexible shoe-shaped outlet from the original reservoir collar.
// TPU shell surrounds an open lumen; the glass fits under the thin toe.
// Units: mm. Exported on the same orientation as the original K1C body.
$fn=64;
show_original=true; // set false to export only the hollow shoe additions for review
body_file="original_body_K1C.stl";
well_x=33.75;
well_y=5.325;
base_t=0.40;
cover_t=0.17;          // assumed #1.5 coverslip; verify the actual part
clearance=0.12;
toe_lumen_h=cover_t+clearance;
roof_t=0.40;
outer_w=7.50;          // same diameter as the original collar
inner_w=6.30;          // hollow passage; the main channel remains 5.0 mm
wall_t=(outer_w-inner_w)/2; // 0.60 mm, matching the TPU collar wall
collar_outer_r=4.40;
collar_inner_r=3.80;
collar_gap=5.80;       // close the existing inward-facing C-collar opening
collar_h=10.0;
root_x=2.50;           // starts at the inner side of the circular collar
shoe_tip_x=7.50;       // extends about one collar radius beyond the root

module oriented(side) {
    translate([side*well_x,well_y,0])
        rotate([0,0,side<0 ? 0 : 180]) children();
}
module outer_shell_envelope() {
    hull() {
        // Root stays inside the 5.8 mm collar opening; using the toe's full
        // 7.5 mm width here made two square shoulders at the collar base.
        translate([root_x,-collar_gap/2,base_t])
            cube([1.2,collar_gap,9.60],center=false);
        // Rounded toe, with open underside for the coverslip to slide beneath.
        translate([5.0,0,base_t])
            scale([1,outer_w/5,1]) cylinder(r=2.5,h=toe_lumen_h+roof_t);
    }
}
module hollow_lumen() {
    hull() {
        // Extend the subtraction back into the reservoir and out through the toe.
        // Leave a 0.60 mm end wall at the reservoir-side root.
        translate([root_x+wall_t,-inner_w/2,base_t])
            cube([2.7,inner_w,9.20],center=false);
        // Inset the rounded inner toe by the same 0.60 mm wall thickness.
        translate([5.0,0,base_t])
            scale([(2.5-wall_t)/2.5,inner_w/5,1]) cylinder(r=2.5,h=toe_lumen_h);
    }
}
module collar_closure(side) {
    oriented(side) {
        // Thin annular sector closes the large vertical portal in the C-collar.
        // It begins above the 0.40 mm base, preserving the microchannel below.
        translate([0,0,base_t])
            linear_extrude(height=collar_h-base_t)
                intersection() {
                    difference() {
                        circle(r=collar_outer_r);
                        circle(r=collar_inner_r);
                    }
                    translate([0,-collar_gap/2])
                        square([2*collar_outer_r,collar_gap],center=false);
                }
    }
}
module shoe(side) {
    oriented(side) {
        difference() {
            outer_shell_envelope();
            hollow_lumen();
        }
        // Sacrificial crossbar inside the hollow toe; cut it before sliding
        // the coverslip into the 0.29 mm opening. The lumen stays open afterward.
        translate([6.30,-inner_w/2,base_t])
            cube([0.30,inner_w,toe_lumen_h],center=false);
    }
}
if (show_original) {
    union() {
        import(body_file,convexity=10);
        for (side=[-1,1]) {
            collar_closure(side);
            shoe(side);
        }
    }
} else {
    for (side=[-1,1]) {
        collar_closure(side);
        shoe(side);
    }
}
