#!/usr/bin/env python3
"""Generate a printable enclosure for the RaspyJack three-board stack.

Stack, from bottom to top:
  Raspberry Pi Zero 2 W -> Waveshare 12694 USB HUB HAT ->
  Waveshare 2.8inch RPi LCD (A), Rev 2.1.

The geometry is intentionally parametric.  Edit the values in CONFIG after a
fit test, then run this file again with Python 3 and trimesh + manifold3d.
"""

from pathlib import Path

import numpy as np
import trimesh


CONFIG = {
    # Published board dimensions, millimetres.
    "lcd_x": 85.01,
    "lcd_y": 56.44,
    "pi_x": 65.0,
    "pi_y": 30.0,
    "hole_dx": 58.0,
    "hole_dy": 23.0,
    # Printing and fit parameters.
    "pcb_clearance": 0.65,
    "wall": 2.4,
    "floor": 2.4,
    "corner_radius": 4.0,
    "base_height": 29.5,
    "post_height": 4.2,
    "post_outer_d": 6.2,
    "m25_clearance_d": 2.8,
    # The Zero-sized boards sit against the LCD's right and lower edges.
    "stack_offset_x": 10.005,
    "stack_offset_y": 13.22,
    # Cap / bezel.
    # Radial clearance: the gap on EACH side of the base, not a total gap.
    "cap_clearance": 0.25,
    "cap_wall": 1.6,
    "cap_skirt": 5.0,
    "cap_top": 2.6,
    # LCD visible area and KEY1..KEY4 access.
    # Measured after perspective correction of the user's board photograph.
    # In board coordinates the opening is x=7.70..75.10, y=1.10..49.80 mm.
    "screen_x": 67.40,
    "screen_y": 48.70,
    "screen_offset_x": -1.105,
    "screen_offset_y": -2.770,
    # KEY1..KEY4 centres measured from the same rectified photograph.
    "button_x": -38.355,
    "button_y": (-20.57, -6.07, 8.28, 22.23),
    "button_hole_x": 5.20,
    "button_hole_y": 7.20,
    "button_hole_radius": 1.20,
}

HERE = Path(__file__).resolve().parent
OUT = HERE / "stl"


def move(mesh, xyz):
    mesh = mesh.copy()
    mesh.apply_translation(xyz)
    return mesh


def box(size, center=(0, 0, 0)):
    return move(trimesh.creation.box(extents=size), center)


def cylinder(radius, height, center=(0, 0, 0), sections=64):
    return move(
        trimesh.creation.cylinder(radius=radius, height=height, sections=sections),
        center,
    )


def union(meshes):
    return trimesh.boolean.union(meshes, engine="manifold")


def difference(mesh, cutters):
    return trimesh.boolean.difference([mesh, *cutters], engine="manifold")


def rounded_box(x, y, z, radius, z0=0.0):
    """Rounded rectangular prism with its bottom at z0."""
    radius = min(radius, x / 2, y / 2)
    pieces = [
        box((x - 2 * radius, y, z), (0, 0, z0 + z / 2)),
        box((x, y - 2 * radius, z), (0, 0, z0 + z / 2)),
    ]
    for sx in (-1, 1):
        for sy in (-1, 1):
            pieces.append(
                cylinder(
                    radius,
                    z,
                    (sx * (x / 2 - radius), sy * (y / 2 - radius), z0 + z / 2),
                )
            )
    return union(pieces)


def dimensions():
    c = CONFIG
    inner_x = c["lcd_x"] + 2 * c["pcb_clearance"]
    inner_y = c["lcd_y"] + 2 * c["pcb_clearance"]
    outer_x = inner_x + 2 * c["wall"]
    outer_y = inner_y + 2 * c["wall"]
    return inner_x, inner_y, outer_x, outer_y


def mounting_centres():
    c = CONFIG
    ox, oy = c["stack_offset_x"], c["stack_offset_y"]
    for dx in (-c["hole_dx"] / 2, c["hole_dx"] / 2):
        for dy in (-c["hole_dy"] / 2, c["hole_dy"] / 2):
            yield ox + dx, oy + dy


def make_base():
    c = CONFIG
    inner_x, inner_y, outer_x, outer_y = dimensions()
    h = c["base_height"]

    body = rounded_box(outer_x, outer_y, h, c["corner_radius"])
    cavity = rounded_box(
        inner_x,
        inner_y,
        h - c["floor"] + 1.0,
        max(1.0, c["corner_radius"] - c["wall"]),
        c["floor"],
    )

    cutters = [cavity]

    # HUB 12694 north edge: USB-UART, USB2 and USB3.  Separate apertures avoid
    # a 63 mm unsupported bridge above one oversized opening.
    hub_north_ports = ((-13.0, 10.5), (3.0, 15.5), (19.5, 15.5))
    for x, width in hub_north_ports:
        cutters.append(box((width, c["wall"] * 3, 12.0),
                           (x, -outer_y / 2, 17.8)))

    # USB1 and USB4 on the short edges.
    cutters.append(box((c["wall"] * 3, 17.0, 12.0),
                       (-outer_x / 2, c["stack_offset_y"], 17.8)))
    cutters.append(box((c["wall"] * 3, 17.0, 12.0),
                       (outer_x / 2, c["stack_offset_y"], 17.8)))

    # Pi Zero mini-HDMI, USB data and power.  Centres come from the official
    # Zero 2 W mechanical drawing (12.4, 41.4 and 54 mm from the board edge).
    stack_left = c["stack_offset_x"] - c["pi_x"] / 2
    pi_south_ports = (
        (stack_left + 12.4, 14.0),
        (stack_left + 41.4, 10.5),
        (stack_left + 54.0, 10.5),
    )
    for x, width in pi_south_ports:
        cutters.append(box((width, c["wall"] * 3, 8.5),
                           (x, -outer_y / 2, 7.8)))

    # microSD finger slot at the end of the Pi board.
    cutters.append(box((c["wall"] * 3, 17.0, 6.5),
                       (outer_x / 2, c["stack_offset_y"], 6.0)))

    # Bottom ventilation slots, kept away from the mounting pattern.
    for x in (-24.0, -16.0, -8.0, 0.0, 8.0, 16.0):
        cutters.append(box((3.0, 18.0, c["floor"] + 2),
                           (x - 7.0, -13.0, c["floor"] / 2)))

    body = difference(body, cutters)

    # Four Pi/Hub mounting bosses.  Through holes accept M2.5 screws from the
    # bottom and preserve the stock 58 x 23 mm mounting pattern.
    posts = []
    post_z = c["floor"] + c["post_height"] / 2
    for x, y in mounting_centres():
        boss = cylinder(c["post_outer_d"] / 2, c["post_height"], (x, y, post_z))
        hole = cylinder(c["m25_clearance_d"] / 2,
                        c["floor"] + c["post_height"] + 2,
                        (x, y, (c["floor"] + c["post_height"]) / 2))
        posts.append(difference(boss, [hole]))
        body = difference(body, [hole])

    return union([body, *posts])


def make_bezel():
    c = CONFIG
    _, _, outer_x, outer_y = dimensions()
    cap_inner_x = outer_x + 2 * c["cap_clearance"]
    cap_inner_y = outer_y + 2 * c["cap_clearance"]
    cap_outer_x = cap_inner_x + 2 * c["cap_wall"]
    cap_outer_y = cap_inner_y + 2 * c["cap_wall"]
    total_h = c["cap_skirt"] + c["cap_top"]

    cap = rounded_box(cap_outer_x, cap_outer_y, total_h,
                      c["corner_radius"] + c["cap_wall"])
    underside = rounded_box(cap_inner_x, cap_inner_y, c["cap_skirt"] + 0.2,
                            c["corner_radius"] + c["cap_clearance"], -0.1)

    screen = box((c["screen_x"], c["screen_y"], total_h + 2),
                 (c["screen_offset_x"], c["screen_offset_y"], total_h / 2))
    # Four rounded rectangular apertures follow the actual, non-uniform key
    # spacing visible in the Rev2.1 board photograph.
    keys = []
    for y in c["button_y"]:
        key = rounded_box(c["button_hole_x"], c["button_hole_y"], total_h + 2,
                          c["button_hole_radius"], z0=-1)
        keys.append(move(key, (c["button_x"], y, 0)))
    return difference(cap, [underside, screen, *keys])


def make_fit_gauge():
    """Two loose parts: a male rail and a female U-channel.

    After printing, remove both parts from the bed and slide the rail into the
    channel from either end.  Their clearance is identical to the cap gap.
    """
    c = CONFIG
    clearance = c["cap_clearance"]
    length = 25.0
    rail_w = 10.0
    rail_h = 5.0
    channel_wall = c["cap_wall"]

    # Male part representing the outside of the base.
    rail = box((length, rail_w, rail_h), (-17.0, 0, rail_h / 2))

    # Female cap section.  The cavity is open at the top and at both ends, so
    # it forms an obvious U-shaped channel in the slicer and after printing.
    cavity_w = rail_w + 2 * clearance
    cavity_h = rail_h + clearance
    outer_w = cavity_w + 2 * channel_wall
    outer_h = cavity_h + channel_wall
    channel_outer = box((length, outer_w, outer_h),
                        (17.0, 0, outer_h / 2))
    channel_void = box((length + 1.0, cavity_w, cavity_h + 1.0),
                       (17.0, 0, channel_wall + (cavity_h + 1.0) / 2))
    channel = difference(channel_outer, [channel_void])

    # Both disconnected solids intentionally share one STL for a single small
    # print job.  They are 9 mm apart and do not touch each other.
    return trimesh.util.concatenate([rail, channel])


def validate(name, mesh):
    if mesh.is_empty:
        raise RuntimeError(f"{name}: empty mesh")
    if not mesh.is_watertight:
        raise RuntimeError(f"{name}: mesh is not watertight")
    ext = np.round(mesh.extents, 2)
    print(f"{name}: {len(mesh.faces)} faces, size {ext.tolist()} mm, watertight")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bezel_assembly = make_bezel()
    bezel_print = bezel_assembly.copy()
    # Export the bezel face-down.  This puts its broad, flat front surface on
    # the print bed and avoids bridging the whole face over the 5 mm skirt.
    bezel_print.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0))
    )
    bezel_print.apply_translation((0, 0, CONFIG["cap_skirt"] + CONFIG["cap_top"]))
    parts = {
        "raspyjack_28_base.stl": make_base(),
        "raspyjack_28_bezel.stl": bezel_print,
        "cap_clearance_test.stl": make_fit_gauge(),
    }
    for filename, mesh in parts.items():
        validate(filename, mesh)
        mesh.export(OUT / filename)

    # A lightweight preview file: bezel is lifted to its assembled position.
    base = parts["raspyjack_28_base.stl"].copy()
    bezel = move(bezel_assembly, (0, 0, CONFIG["base_height"] - CONFIG["cap_skirt"]))
    preview = trimesh.util.concatenate([base, bezel])
    preview.export(OUT / "assembly_preview.stl")
    print(f"Wrote files to {OUT}")


if __name__ == "__main__":
    main()
