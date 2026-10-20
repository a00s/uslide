// U-Slide V2 concept for a conventional upright microscope.
// Compared with the current model, both reservoirs move inward and the U-channel
// ends farther under the 60 mm coverslip to reduce the exposed bridge at its edge.
// Units: mm. This is a fit/leak-test concept, not a validated biological device.
$fn = 96;

slide_l = 76.2;
slide_w = 25.4;
cover_l = 60.0;
cover_w = 24.0;
base_l = 75.8;
base_w = 24.4;
base_t = 0.40;
channel_w = 5.0;
// Measured from the source Onshape mesh: inner radius ~3.8 mm, outer ~4.4 mm.
well_id = 7.6;
well_od = 8.8;
well_height = 10.0;
well_x = 31.0;
well_y = 5.32339475;
well_gap = 2.0;              // narrow throat from each well into the 5 mm channel
tab_length = 19.8;
tab_width = 0.8;
tab_y = 11.3;
tab_overlap = 0.3;

// Channel centerline ends at +/-25.5 mm. Its 2.5 mm radius leaves a 2 mm
// continuous TPU sealing land beneath the coverslip edge at +/-30 mm.
path_pts = [
    [-25.5, 5.3234], [-24.0,5.3234], [-22.5,4.5234], [-21.0,3.0234],
    [-20.0,1.0234], [-18.5,-2.0], [-18.5,-5.2], [18.5,-5.2],
    [18.5,-2.0], [20.0,1.0234], [21.0,3.0234], [22.5,4.5234],
    [24.0,5.3234], [25.5,5.3234]
];

view_mode = "print"; // print / plan / assembly

module stroke_2d(points, width) {
    union() for (i=[0:len(points)-2]) hull() {
        translate(points[i]) circle(d=width);
        translate(points[i+1]) circle(d=width);
    }
}

module channel_void_2d() {
    union() {
        stroke_2d(path_pts, channel_w);
        for (cx=[-well_x,well_x]) translate([cx,well_y]) circle(d=well_id);
    }
}

module pull_tabs() {
    for (sx=[-1,1], sy=[-1,1])
        translate([sx*(base_l/2+tab_length/2-tab_overlap), sy*tab_y, base_t/2])
            cube([tab_length,tab_width,base_t],center=true);
}

module base_gasket() {
    difference() {
        union() {
            translate([0,0,base_t/2]) cube([base_l,base_w,base_t],center=true);
            pull_tabs();
        }
        translate([0,0,-0.01]) linear_extrude(height=base_t+0.02) channel_void_2d();
    }
}

module c_collar_local(cx) {
    outer_r=well_od/2;
    inner_r=well_id/2;
    difference() {
        difference() { circle(r=outer_r); circle(r=inner_r); }
        // A narrow opening faces the U-channel; most of the reservoir rim stays closed.
        translate([cx<0 ? outer_r : -outer_r,0])
            square([2*outer_r,well_gap],center=true);
    }
}

module reservoirs() {
    for (cx=[-well_x,well_x]) translate([cx,well_y,0])
        linear_extrude(height=well_height) c_collar_local(cx);
}

module gasket() { union() { base_gasket(); reservoirs(); } }

if (view_mode=="print") {
    gasket();
} else if (view_mode=="plan") {
    projection(cut=true) gasket();
} else {
    color([0.58,0.61,0.64,0.65]) translate([0,0,-0.45])
        cube([slide_l,slide_w,0.9],center=true);
    color([0.68,0.86,0.93,0.36]) translate([0,0,base_t+0.09])
        cube([cover_l,cover_w,0.18],center=true);
    color([0.24,0.62,0.66,0.92]) gasket();
}
