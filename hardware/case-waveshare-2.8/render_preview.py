#!/usr/bin/env python3
"""Create a dependency-light isometric PNG preview of the generated STL parts."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
import trimesh

HERE = Path(__file__).resolve().parent
STL = HERE / "stl"


def rotation_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rotation_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def triangles(mesh, color, transform, z_offset=0):
    verts = mesh.vertices.copy()
    verts[:, 2] += z_offset
    view = verts @ transform.T
    result = []
    light = np.array([-0.35, -0.45, 0.82])
    light /= np.linalg.norm(light)
    for face in mesh.faces:
        tri3 = view[face]
        normal = np.cross(tri3[1] - tri3[0], tri3[2] - tri3[0])
        length = np.linalg.norm(normal)
        if length == 0:
            continue
        normal /= length
        # Orthographic camera looks along -Z in view space.  Skip back faces
        # so internal walls do not cover the exterior in the preview.
        if normal[2] <= 0:
            continue
        shade = 0.50 + 0.50 * abs(np.dot(normal, light))
        rgb = tuple(int(min(255, max(0, channel * shade))) for channel in color)
        result.append((float(tri3[:, 2].mean()), tri3[:, :2], rgb))
    return result


def main():
    base = trimesh.load_mesh(STL / "raspyjack_28_base.stl")
    bezel = trimesh.load_mesh(STL / "raspyjack_28_bezel.stl")
    # The printable bezel STL is face-down.  Restore assembly orientation for
    # the preview and then place it over the base.
    bezel.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0)))
    bezel.apply_translation((0, 0, 7.6))
    # View from the key side so the only USB-A and microSD openings are
    # visible together with the four key apertures in the bezel.
    transform = rotation_x(np.deg2rad(-61)) @ rotation_z(np.deg2rad(38))

    faces = triangles(base, (55, 62, 68), transform)
    # Bezel skirt overlaps the top 5 mm of the 40.0 mm base.
    faces += triangles(bezel, (43, 154, 255), transform, z_offset=35.0)
    faces.sort(key=lambda item: item[0])

    points = np.concatenate([item[1] for item in faces])
    low, high = points.min(axis=0), points.max(axis=0)
    image = Image.new("RGB", (1400, 1000), (242, 244, 247))
    draw = ImageDraw.Draw(image)
    margin = 95
    scale = min((image.width - 2 * margin) / (high[0] - low[0]),
                (image.height - 2 * margin) / (high[1] - low[1]))

    def screen(poly):
        p = (poly - low) * scale + margin
        p[:, 1] = image.height - p[:, 1]
        return [tuple(v) for v in p]

    for _, poly, fill in faces:
        draw.polygon(screen(poly), fill=fill, outline=(35, 38, 43))

    draw.text((40, 35), "RaspyJack 2.8 — Pi Zero 2 W + Waveshare 12694",
              fill=(24, 29, 35), stroke_width=0)
    draw.text((40, 62), "Strona przyciskow: jedyny USB-A + microSD",
              fill=(72, 79, 88), stroke_width=0)
    output = HERE / "case_preview.png"
    image.save(output)
    print(output)


if __name__ == "__main__":
    main()
