#!/usr/bin/env python3
"""Mechanical sanity checks for the generated enclosure STL files."""

from pathlib import Path

import numpy as np
import trimesh

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
    bezel.apply_translation((0, 0, 7.6 + 29.5 - 5.0))
    overlap = trimesh.boolean.intersection([base, bezel], engine="manifold")
    overlap_volume = 0.0 if overlap is None or overlap.is_empty else overlap.volume
    require(overlap_volume < 0.01,
            f"base and bezel collide by {overlap_volume:.3f} mm^3")

    expected = {
        "base": (91.11, 62.54, 29.50),
        "bezel": (94.81, 66.24, 7.60),
    }
    require(np.allclose(base.extents, expected["base"], atol=0.05),
            f"unexpected base size: {base.extents}")
    require(np.allclose(bezel_print.extents, expected["bezel"], atol=0.05),
            f"unexpected bezel size: {bezel_print.extents}")

    print("PASS: base is one watertight printable part")
    print("PASS: bezel is one watertight printable part and is face-down")
    print("PASS: clearance gauge contains two disconnected parts")
    print("PASS: assembled base and bezel have no solid collision")
    print("PASS: external dimensions match the parametric design")


if __name__ == "__main__":
    main()
