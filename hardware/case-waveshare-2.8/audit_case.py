#!/usr/bin/env python3
"""Mechanical sanity checks for the generated enclosure STL files."""

from pathlib import Path

import numpy as np
import trimesh

from generate_case import CONFIG, dimensions

HERE = Path(__file__).resolve().parent
STL = HERE / "stl"


def component_count(mesh):
    """Count connected face groups without an optional graph dependency."""
    parent = np.arange(len(mesh.faces))

    def find(item):
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for left, right in mesh.face_adjacency:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a
    return len({find(i) for i in range(len(parent))})


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def load(name):
    mesh = trimesh.load_mesh(STL / name)
    require(mesh.is_watertight, f"{name}: mesh is not watertight")
    require(mesh.is_winding_consistent, f"{name}: inconsistent winding")
    require(mesh.is_volume and mesh.volume > 0, f"{name}: invalid volume")
    return mesh


def probe_volume(mesh, size, center):
    """Return solid volume inside a small probe placed through a case wall."""
    probe = trimesh.creation.box(extents=size)
    probe.apply_translation(center)
    overlap = trimesh.boolean.intersection([mesh, probe], engine="manifold")
    return 0.0 if overlap is None or overlap.is_empty else overlap.volume


def main():
    base = load("raspyjack_28_base.stl")
    bezel_print = load("raspyjack_28_bezel.stl")
    gauge = load("cap_clearance_test.stl")

    require(component_count(base) == 1, "base must be one connected part")
    require(component_count(bezel_print) == 1, "bezel must be one connected part")
    require(component_count(gauge) == 2, "fit gauge must contain two loose parts")

    # Both printable parts must rest on z=0 in their intended slicer orientation.
    require(abs(base.bounds[0, 2]) < 1e-6, "base is not on the print bed")
    require(abs(bezel_print.bounds[0, 2]) < 1e-6, "bezel is not on the print bed")

    # Restore the face-down printable bezel to assembly orientation.
    bezel = bezel_print.copy()
    bezel.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0)))
    bezel.apply_translation((0, 0, 7.6 + CONFIG["base_height"] - 5.0))
    overlap = trimesh.boolean.intersection([base, bezel], engine="manifold")
    overlap_volume = 0.0 if overlap is None or overlap.is_empty else overlap.volume
    require(overlap_volume < 0.01,
            f"base and bezel collide by {overlap_volume:.3f} mm^3")

    expected = {
        "base": (91.11, 62.54, 39.50),
        "bezel": (94.81, 66.24, 7.60),
    }
    require(np.allclose(base.extents, expected["base"], atol=0.05),
            f"unexpected base size: {base.extents}")
    require(np.allclose(bezel_print.extents, expected["bezel"], atol=0.05),
            f"unexpected bezel size: {bezel_print.extents}")

    # Photo-derived LCD opening: verify its intentionally unequal margins and
    # preserve at least two 0.4 mm extrusion lines between keys and display.
    c = CONFIG
    left = c["lcd_x"] / 2 + c["screen_offset_x"] - c["screen_x"] / 2
    right = c["lcd_x"] / 2 - (c["screen_offset_x"] + c["screen_x"] / 2)
    top = c["lcd_y"] / 2 + c["screen_offset_y"] - c["screen_y"] / 2
    bottom = c["lcd_y"] / 2 - (c["screen_offset_y"] + c["screen_y"] / 2)
    require(np.allclose((left, right, top, bottom),
                        (7.70, 9.91, 1.10, 6.64), atol=0.02),
            f"LCD margins changed: {(left, right, top, bottom)}")
    bridge = (c["screen_offset_x"] - c["screen_x"] / 2) - (
        c["button_x"] + c["button_hole_x"] / 2
    )
    require(bridge >= 0.8, f"only {bridge:.2f} mm between keys and LCD opening")
    require(c["stack_offset_y"] > 0,
            "Pi/HUB stack must remain under the photographed GPIO edge")
    require(c["base_height"] >= 39.5,
            "case is too short for the photographed Pi/HUB/LCD spacers")

    # The photographed USB2/USB3 sockets are recessed too far below the LCD.
    # Verify that their former apertures are solid wall, while the service
    # UART opening and the one genuinely accessible side USB4 remain clear.
    _, _, outer_x, outer_y = dimensions()
    long_wall_probe = (2.0, c["wall"] - 0.4, 2.0)
    for x in (3.0, 19.5):
        volume = probe_volume(
            base, long_wall_probe, (x, -outer_y / 2 + c["wall"] / 2, 24.0)
        )
        require(volume > 5.0, f"front wall is unexpectedly open at x={x}")
    uart_volume = probe_volume(
        base, long_wall_probe,
        (-13.0, -outer_y / 2 + c["wall"] / 2, 24.0),
    )
    require(uart_volume < 0.01, "USB-UART service opening is blocked")
    short_wall_probe = (c["wall"] - 0.4, 2.0, 2.0)
    usb1_volume = probe_volume(
        base, short_wall_probe,
        (-outer_x / 2 + c["wall"] / 2, c["stack_offset_y"], 24.0),
    )
    require(usb1_volume > 5.0, "recessed USB1 wall is unexpectedly open")
    usb4_volume = probe_volume(
        base, short_wall_probe,
        (outer_x / 2 - c["wall"] / 2, c["stack_offset_y"], 24.0),
    )
    require(usb4_volume < 0.01, "accessible USB4 opening is blocked")

    print("PASS: base is one watertight printable part")
    print("PASS: bezel is one watertight printable part and is face-down")
    print("PASS: clearance gauge contains two disconnected parts")
    print("PASS: assembled base and bezel have no solid collision")
    print("PASS: external dimensions match the parametric design")
    print("PASS: photo-derived LCD margins and key bridge are preserved")
    print("PASS: Pi/HUB stack is aligned with the photographed GPIO edge")
    print("PASS: enclosure height clears the photographed board stack")
    print("PASS: only accessible USB4 is exposed; USB1/USB2/USB3 are closed")


if __name__ == "__main__":
    main()
