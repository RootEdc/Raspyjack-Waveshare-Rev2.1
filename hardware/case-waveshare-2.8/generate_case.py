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
    "stack_offset_y": -13.22,
    # Cap / bezel.
    "cap_gap": 0.30,
    "cap_wall": 1.6,
    "cap_skirt": 5.0,
    "cap_top": 2.6,
    # LCD visible area and KEY1..KEY4 access.
    "screen_x": 60.5,
    "screen_y": 45.8,
    "screen_offset_x": -5.7,
    "button_x": 33.7,
    "button_y": (-18.0, -6.0, 6.0, 18.0),
    "button_d": 6.4,
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

    # HUB 12694: USB2, USB3 and USB-UART on the north long edge.
    cutters.append(box((63.0, c["wall"] * 3, 14.0),
                       (c["stack_offset_x"] - 1.0, outer_y / 2, 17.8)))
    # USB1 and USB4 on the short edges.  Long windows also ease insertion of
    # Wi-Fi adapters beneath the overhanging LCD board.
    cutters.append(box((c["wall"] * 3, 34.0, 14.0),
                       (-outer_x / 2, c["stack_offset_y"], 17.8)))
    cutters.append(box((c["wall"] * 3, 34.0, 14.0),
                       (outer_x / 2, c["stack_offset_y"], 17.8)))

    # Pi Zero power/USB/mini-HDMI edge.  One generous opening keeps cable
    # plugs usable and tolerates connector variation between Zero revisions.
    cutters.append(box((67.0, c["wall"] * 3, 8.5),
                       (c["stack_offset_x"], -outer_y / 2, 7.8)))

    # microSD finger slot at the end of the Pi board.
    cutters.append(box((c["wall"] * 3, 17.0, 6.5),
                       (outer_x / 2, c["stack_offset_y"], 6.0)))

    # Bottom ventilation slots, kept away from the mounting pattern.
    for x in (-24.0, -16.0, -8.0, 0.0, 8.0, 16.0):
        cutters.append(box((3.0, 18.0, c["floor"] + 2),
                           (x - 7.0, 13.0, c["floor"] / 2)))

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
    cap_inner_x = outer_x + c["cap_gap"]
    cap_inner_y = outer_y + c["cap_gap"]
    cap_outer_x = cap_inner_x + 2 * c["cap_wall"]
    cap_outer_y = cap_inner_y + 2 * c["cap_wall"]
    total_h = c["cap_skirt"] + c["cap_top"]

    cap = rounded_box(cap_outer_x, cap_outer_y, total_h,
                      c["corner_radius"] + c["cap_wall"])
    underside = rounded_box(cap_inner_x, cap_inner_y, c["cap_skirt"] + 0.2,
                            c["corner_radius"] + c["cap_gap"] / 2, -0.1)

    screen = box((c["screen_x"], c["screen_y"], total_h + 2),
                 (c["screen_offset_x"], 0, total_h / 2))
    keys = [
        cylinder(c["button_d"] / 2, total_h + 2,
                 (c["button_x"], y, total_h / 2))
        for y in c["button_y"]
    ]
    return difference(cap, [underside, screen, *keys])


def make_fit_gauge():
    """Two loose parts: a male rail and a female U-channel.

    After printing, remove both parts from the bed and slide the rail into the
    channel from either end.  Their clearance is identical to the cap gap.
    """
    c = CONFIG
    gap = c["cap_gap"]
    length = 25.0
    rail_w = 10.0
    rail_h = 5.0
    channel_wall = c["cap_wall"]

    # Male part representing the outside of the base.
    rail = box((length, rail_w, rail_h), (-17.0, 0, rail_h / 2))

    # Female cap section.  The cavity is open at the top and at both ends, so
    # it forms an obvious U-shaped channel in the slicer and after printing.
    cavity_w = rail_w + gap
    cavity_h = rail_h + gap
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
    parts = {
        "raspyjack_28_base.stl": make_base(),
        "raspyjack_28_bezel.stl": make_bezel(),
        "cap_clearance_test.stl": make_fit_gauge(),
    }
    for filename, mesh in parts.items():
        validate(filename, mesh)
        mesh.export(OUT / filename)

    # A lightweight preview file: bezel is lifted to its assembled position.
    base = parts["raspyjack_28_base.stl"].copy()
    bezel = move(parts["raspyjack_28_bezel.stl"], (0, 0, CONFIG["base_height"] - CONFIG["cap_skirt"]))
    preview = trimesh.util.concatenate([base, bezel])
    preview.export(OUT / "assembly_preview.stl")
    print(f"Wrote files to {OUT}")


if __name__ == "__main__":
    main()
