// RaspyJack enclosure — editable OpenSCAD reference model
// Stack: Pi Zero 2 W -> Waveshare 12694 USB HUB HAT -> 2.8in LCD Rev2.1
// Use generate_case.py for the verified STL exports.

part = "assembly"; // "base", "bezel", or "assembly"

lcd = [85.01, 56.44];
clearance = 0.65;
wall = 2.4;
floor_t = 2.4;
base_h = 39.5;
corner_r = 4.0;
inner = [lcd.x + 2*clearance, lcd.y + 2*clearance];
outer = [inner.x + 2*wall, inner.y + 2*wall];

module rounded_box(s, r) {
  hull() for (x=[-1,1], y=[-1,1])
    translate([x*(s.x/2-r), y*(s.y/2-r), 0]) cylinder(r=r, h=s.z, $fn=64);
}

module base() {
  difference() {
    rounded_box([outer.x, outer.y, base_h], corner_r);
    translate([0,0,floor_t])
      rounded_box([inner.x, inner.y, base_h], max(1,corner_r-wall));
    // USB2/USB3 are too deep below the LCD to be useful at the case wall.
    // Keep only the smaller USB-to-UART service opening on this edge.
    translate([-13,-outer.y/2,24]) cube([10.5,3*wall,12],center=true);
    // Only USB4 reaches the case side; USB1 is recessed by about 20 mm.
    translate([ outer.x/2,13.22,24]) cube([3*wall,17,12],center=true);
    // Pi Zero mini-HDMI, USB data and USB power.
    for(p=[[-10.095,14],[18.905,10.5],[31.505,10.5]])
      translate([p.x,-outer.y/2,7.8]) cube([p.y,3*wall,8.5],center=true);
    // microSD.
    translate([outer.x/2,13.22,6]) cube([3*wall,17,6.5], center=true);
  }
}

module bezel() {
  side_clearance=0.25; skirt=5; top=2.6; capwall=1.6;
  ci=[outer.x+2*side_clearance, outer.y+2*side_clearance];
  co=[ci.x+2*capwall, ci.y+2*capwall];
  difference() {
    rounded_box([co.x,co.y,skirt+top], corner_r+capwall);
    translate([0,0,-.1]) rounded_box([ci.x,ci.y,skirt+.2],corner_r+side_clearance);
    translate([-1.105,-2.770,-1]) cube([67.4,48.7,skirt+top+2],center=true);
    for(y=[-20.57,-6.07,8.28,22.23])
      hull() for(x=[-1.4,1.4], yy=[-2.4,2.4])
        translate([-38.355+x,y+yy,-1])
          cylinder(r=1.2,h=skirt+top+2,$fn=32);
  }
}

if (part == "base") base();
if (part == "bezel") bezel();
if (part == "assembly") {
  color("#252525") base();
  color("#1a8cff") translate([0,0,base_h-5]) bezel();
}
