// U-Slide TPU gasket for a conventional upright microscope.
// The sample path is U-shaped in plan view: wells toward +Y, low viewing run toward -Y.
// Units: mm. Export STL/3MF with OpenSCAD; Creality Print accepts either format.
$fn = 96;

// User's stock glass dimensions
slide_l = 76.2;
slide_w = 25.4;
cover_l = 60.0;
cover_w = 24.0;

// One-piece TPU gasket. The glass slide closes the underside of the cutout;
// the coverslip closes the central U-channel from above.
base_l = 75.8;
base_w = 24.4;
base_t = 0.40;             // through-cut channel height
channel_w = 5.0;
well_id = 5.2;
well_od = 7.8;
well_height = 3.2;         // total height from print bed
well_x = 34.0;
well_y = 2.5;
well_gap = 5.8;             // collar opening faces inward toward the U-channel

// U centerline ends at the coverslip edge; the channel width overlaps both wells.
path_pts = [
    [-30.0, 2.5], [-28.7, 2.5], [-27.0, 1.7], [-25.5, 0.2],
    [-24.5,-1.8], [-22.5,-4.0], [-20.0,-5.2], [20.0,-5.2],
    [22.5,-4.0], [24.5,-1.8], [25.5,0.2], [27.0,1.7],
    [28.7,2.5], [30.0,2.5]
];

// Output modes: "print" for manufacture; "preview" for the glass assembly; "plan" for path inspection.
view_mode = "print";

module stroke_2d(points, width) {
    union() {
        for (i = [0 : len(points)-2])
            hull() {
                translate(points[i]) circle(d=width);
                translate(points[i+1]) circle(d=width);
            }
    }
}

module fluid_void_2d() {
    union() {
        stroke_2d(path_pts, channel_w);
        translate([-well_x,well_y]) circle(d=well_id);
        translate([ well_x,well_y]) circle(d=well_id);
    }
}

module base_gasket() {
    // Broad, thin layer supports the coverslip. The connected fluid path is cut through it.
    difference() {
        translate([0,0,base_t/2]) cube([base_l,base_w,base_t], center=true);
        translate([0,0,-0.01]) linear_extrude(height=base_t+0.02) fluid_void_2d();
    }
}

module c_collar_local(cx) {
    outer_r = well_od/2;
    inner_r = well_id/2;
    difference() {
        difference() {
            circle(r=outer_r);
            circle(r=inner_r);
        }
        // Remove the inward-facing arc to keep the well fully open to the channel.
        translate([cx < 0 ? outer_r : -outer_r, 0])
            square([2*outer_r, well_gap], center=true);
    }
}

module raised_reservoirs() {
    for (cx = [-well_x, well_x])
        translate([cx,well_y,0])
            linear_extrude(height=well_height)
                c_collar_local(cx);
}

module one_piece_insert() {
    union() {
        base_gasket();
        raised_reservoirs();
    }
}

if (view_mode == "print") {
    one_piece_insert();
} else if (view_mode == "plan") {
    projection(cut=true) one_piece_insert();
} else {
    // Preview only: slide below the gasket, central coverslip seated on the thin layer.
    color([0.55,0.57,0.60,0.7])
        translate([0,0,-0.45]) cube([slide_l,slide_w,0.9],center=true);
    color([0.88,0.92,0.95,0.5])
        translate([0,0,base_t+0.09]) cube([cover_l,cover_w,0.18],center=true);
    color([0.9,0.25,0.2]) one_piece_insert();
}
