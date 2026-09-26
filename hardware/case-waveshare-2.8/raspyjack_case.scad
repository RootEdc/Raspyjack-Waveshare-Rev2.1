// RaspyJack enclosure — editable OpenSCAD reference model
// Stack: Pi Zero 2 W -> Waveshare 12694 USB HUB HAT -> 2.8in LCD Rev2.1
// Use generate_case.py for the verified STL exports.

part = "assembly"; // "base", "bezel", or "assembly"

lcd = [85.01, 56.44];
clearance = 0.65;
wall = 2.4;
floor_t = 2.4;
base_h = 29.5;
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
    // USB2/3 + UART, USB1, USB4, Pi connector edge, microSD.
    translate([9, outer.y/2, 17.8]) cube([63, 3*wall, 14], center=true);
    translate([-outer.x/2, -13.22, 17.8]) cube([3*wall,34,14], center=true);
    translate([ outer.x/2, -13.22, 17.8]) cube([3*wall,34,14], center=true);
    translate([10.005,-outer.y/2,7.8]) cube([67,3*wall,8.5], center=true);
    translate([outer.x/2,-13.22,6]) cube([3*wall,17,6.5], center=true);
  }
}

module bezel() {
  gap=0.30; skirt=5; top=2.6; capwall=1.6;
  ci=[outer.x+gap, outer.y+gap];
  co=[ci.x+2*capwall, ci.y+2*capwall];
  difference() {
    rounded_box([co.x,co.y,skirt+top], corner_r+capwall);
    translate([0,0,-.1]) rounded_box([ci.x,ci.y,skirt+.2],corner_r+gap/2);
    translate([-5.7,0,-1]) cube([60.5,45.8,skirt+top+2],center=true);
    for(y=[-18,-6,6,18]) translate([33.7,y,-1])
      cylinder(d=6.4,h=skirt+top+2,$fn=48);
  }
}

if (part == "base") base();
if (part == "bezel") bezel();
if (part == "assembly") {
  color("#252525") base();
  color("#1a8cff") translate([0,0,base_h-5]) bezel();
}
