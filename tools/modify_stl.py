#!/usr/bin/env python3
"""
modify_stl.py - reference implementation of the Build 2 menu.

Takes an open-top box exported from Tinkercad (STL, millimeters), measures it,
applies ONE modification, checks printability, and writes a new STL.

This is the kind of code Claude writes when you hand it the starter prompt.
It is here so you can read it, run it, and compare.

Usage:
  python modify_stl.py box.stl info
  python modify_stl.py box.stl sieve    --hole 4 --pitch 6 --border 3
  python modify_stl.py box.stl dividers --cols 3 --rows 2
  python modify_stl.py box.stl text     --text "SEAN" --style emboss
  python modify_stl.py box.stl round    --radius 6
  python modify_stl.py box.stl lid
  python modify_stl.py box.stl keyhole

Requires: trimesh, manifold3d, shapely, numpy, matplotlib, mapbox_earcut
  pip install trimesh manifold3d shapely numpy matplotlib mapbox_earcut
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon, box as shapely_box

MIN_WALL = 1.2   # mm - thinnest wall most FDM printers handle reliably
MIN_HOLE = 2.0   # mm - smaller holes close up when printed
ENGINE = "manifold"


# ----------------------------------------------------------------------------
# Measuring the box
# ----------------------------------------------------------------------------
def measure(mesh):
    """Return a dict describing an open-top box: outer size, wall, floor."""
    lo, hi = mesh.bounds
    size = hi - lo
    info = {"min": lo, "max": hi, "size": size, "wall": None, "floor": None,
            "inner_min": None, "inner_max": None}

    # Rays through the middle of the box at mid height. Along +X the first two
    # hits are the outer and inner face of the left wall; same for Y and from
    # above (the floor). Works on any open-top box, no extra libraries.
    cx, cy, cz = lo[0] + size[0] / 2, lo[1] + size[1] / 2, lo[2] + size[2] / 2

    def hits_along(origin, direction, axis):
        pts, _, _ = mesh.ray.intersects_location(np.array([origin]),
                                                 np.array([direction]))
        return np.sort(np.unique(np.round(pts[:, axis], 3)))

    xs = hits_along([lo[0] - 10, cy, cz], [1, 0, 0], 0)   # x faces, left to right
    ys = hits_along([cx, lo[1] - 10, cz], [0, 1, 0], 1)   # y faces, front to back
    zs = hits_along([cx, cy, hi[2] + 10], [0, 0, -1], 2)  # z faces, top down
    if len(xs) >= 4 and len(ys) >= 4 and len(zs) >= 2:
        info["inner_min"] = np.array([xs[1], ys[1]])
        info["inner_max"] = np.array([xs[-2], ys[-2]])
        info["wall"] = round(float(min(xs[1] - xs[0], xs[-1] - xs[-2],
                                       ys[1] - ys[0], ys[-1] - ys[-2])), 2)
        floor_top = float(zs[-1])        # highest surface under the cavity
        info["floor_top"] = floor_top
        info["floor"] = round(floor_top - float(lo[2]), 2)
    return info


def report(label, mesh):
    lo, hi = mesh.bounds
    s = hi - lo
    print(f"{label}: {s[0]:.1f} x {s[1]:.1f} x {s[2]:.1f} mm | "
          f"volume {mesh.volume/1000:.1f} cm3 | {len(mesh.faces)} triangles | "
          f"watertight={mesh.is_watertight}")


# ----------------------------------------------------------------------------
# Modifications
# ----------------------------------------------------------------------------
def sieve(mesh, m, hole=4.0, pitch=None, border=3.0):
    """Hex grid of through-holes in the floor (the EntoSieve move)."""
    hole = max(hole, MIN_HOLE)
    pitch = pitch or hole + 2.0
    if pitch - hole < MIN_WALL:
        pitch = hole + MIN_WALL
    ix0, iy0 = m["inner_min"]
    ix1, iy1 = m["inner_max"]
    x0, x1 = ix0 + border + hole / 2, ix1 - border - hole / 2
    y0, y1 = iy0 + border + hole / 2, iy1 - border - hole / 2
    z0 = m["min"][2]
    row_step = pitch * np.sqrt(3) / 2
    cutters = []
    row = 0
    y = y0
    while y <= y1 + 1e-6:
        x = x0 + (pitch / 2 if row % 2 else 0)
        while x <= x1 + 1e-6:
            c = trimesh.creation.cylinder(radius=hole / 2, height=m["floor"] + 2,
                                          sections=24)
            c.apply_translation([x, y, z0 + m["floor"] / 2])
            cutters.append(c)
            x += pitch
        y += row_step
        row += 1
    if not cutters:
        sys.exit("Box too small for that hole size and border.")
    print(f"sieve: {len(cutters)} holes, {hole} mm wide, {pitch} mm pitch")
    return trimesh.boolean.difference([mesh] + cutters, engine=ENGINE)


def dividers(mesh, m, cols=2, rows=1, height_drop=2.0):
    """Split the cavity into cols x rows compartments with walls as thick as the box walls."""
    t = max(m["wall"], MIN_WALL)
    ix0, iy0 = m["inner_min"]
    ix1, iy1 = m["inner_max"]
    z_floor, z_top = m["floor_top"], m["max"][2] - height_drop
    h = z_top - z_floor + 0.5          # 0.5 mm overlap into the floor
    parts = []
    for i in range(1, cols):
        x = ix0 + (ix1 - ix0) * i / cols
        b = trimesh.creation.box([t, iy1 - iy0 + 0.5, h])
        b.apply_translation([x, (iy0 + iy1) / 2, z_floor - 0.5 + h / 2])
        parts.append(b)
    for j in range(1, rows):
        y = iy0 + (iy1 - iy0) * j / rows
        b = trimesh.creation.box([ix1 - ix0 + 0.5, t, h])
        b.apply_translation([(ix0 + ix1) / 2, y, z_floor - 0.5 + h / 2])
        parts.append(b)
    if not parts:
        sys.exit("Need cols or rows > 1.")
    print(f"dividers: {cols} x {rows} compartments, {t} mm walls")
    return trimesh.boolean.union([mesh] + parts, engine=ENGINE)


def text_polygon(text, height):
    """Glyph outlines as one shapely geometry (even-odd so letters keep their holes)."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    path = TextPath((0, 0), text, size=height, prop=FontProperties(weight="bold"))
    geom = None
    for pts in path.to_polygons():
        if len(pts) < 3:
            continue
        p = Polygon(pts)
        if not p.is_valid:
            p = p.buffer(0)
        geom = p if geom is None else geom.symmetric_difference(p)
    return geom


def text(mesh, m, label="HELLO", style="emboss", depth=1.0):
    """Raise (emboss) or sink (deboss) text on the front wall (the -Y face)."""
    W, H = m["size"][0], m["size"][2]
    size = min(H * 0.5, 12.0)
    geom = text_polygon(label, size)
    minx, miny, maxx, maxy = geom.bounds
    if maxx - minx > W * 0.8:                         # shrink to fit the wall
        scale = (W * 0.8) / (maxx - minx)
        size *= scale
        geom = text_polygon(label, size)
        minx, miny, maxx, maxy = geom.bounds
    if style == "deboss":
        depth = min(depth, m["wall"] - MIN_WALL)       # never thinner than MIN_WALL
        if depth <= 0.3:
            sys.exit("Wall too thin to deboss. Use emboss instead.")
    parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    solid = trimesh.util.concatenate(
        [trimesh.creation.extrude_polygon(p, height=depth + 0.5) for p in parts])
    # extrude_polygon builds in XY along +Z; rotate so text stands on the front wall
    solid.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    cx = m["min"][0] + W / 2 - (minx + maxx) / 2
    cz = m["min"][2] + H / 2 - (miny + maxy) / 2
    y_front = m["min"][1]
    # after rotation the extrusion runs from y=0 toward -y
    y_shift = y_front + 0.5 if style == "emboss" else y_front + depth + 0.5
    solid.apply_translation([cx, y_shift, cz])
    print(f"text: '{label}' {style}ed {depth} mm, {size:.1f} mm tall")
    if style == "emboss":
        return trimesh.boolean.union([mesh, solid], engine=ENGINE)
    return trimesh.boolean.difference([mesh, solid], engine=ENGINE)


def rounded(mesh, m, radius=6.0):
    """Rebuild the box with rounded vertical edges, inside and out, keeping the wall thickness."""
    W, D, H = m["size"]
    t, f = m["wall"], m["floor"]
    radius = min(radius, (min(W, D) / 2) - t - 0.5)
    outer = shapely_box(0, 0, W, D).buffer(-radius).buffer(radius, join_style="round")
    inner = shapely_box(t, t, W - t, D - t).buffer(-max(radius - t, 0.01)).buffer(
        max(radius - t, 0.01), join_style="round")
    body = trimesh.creation.extrude_polygon(outer, height=H)
    cavity = trimesh.creation.extrude_polygon(inner, height=H)
    cavity.apply_translation([0, 0, f])
    out = trimesh.boolean.difference([body, cavity], engine=ENGINE)
    out.apply_translation(m["min"])
    print(f"rounded: {radius:.1f} mm corner radius, rebuilt from measured "
          f"{W:.1f} x {D:.1f} x {H:.1f} mm, wall {t} mm, floor {f} mm")
    return out


def lid(mesh, m, clearance=0.3, plate=2.0, plug=3.0):
    """A drop-in lid: a plate that sits on the rim plus a plug that fits inside."""
    W, D = m["size"][0], m["size"][1]
    ix0, iy0 = m["inner_min"]
    ix1, iy1 = m["inner_max"]
    top = trimesh.creation.box([W, D, plate])
    top.apply_translation([0, 0, plug + plate / 2])
    inner = trimesh.creation.box([ix1 - ix0 - 2 * clearance, iy1 - iy0 - 2 * clearance,
                                  plug + 0.5])
    inner.apply_translation([0, 0, (plug + 0.5) / 2])
    out = trimesh.boolean.union([top, inner], engine=ENGINE)
    print(f"lid: {W:.1f} x {D:.1f} plate, {plug} mm plug, {clearance} mm clearance "
          f"(print plug side up)")
    return out


def keyhole(mesh, m, hole=8.0, slot=4.0, slot_len=8.0):
    """Keyhole slot through the back wall (+Y face) so the box hangs on a screw."""
    W, D, H = m["size"]
    if H < hole + slot_len + 8:
        sys.exit("Box is too short for a keyhole; make it at least "
                 f"{hole + slot_len + 8:.0f} mm tall.")
    cx = m["min"][0] + W / 2
    y_back = m["max"][1]
    z_center = m["max"][2] - 4 - slot_len - hole / 2
    c = trimesh.creation.cylinder(radius=hole / 2, height=m["wall"] + 2, sections=32)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation([cx, y_back - m["wall"] / 2, z_center])
    s = trimesh.creation.box([slot, m["wall"] + 2, slot_len + hole / 2])
    s.apply_translation([cx, y_back - m["wall"] / 2, z_center + (slot_len + hole / 2) / 2])
    print(f"keyhole: {hole} mm hole, {slot} mm slot, {slot_len} mm long, back wall")
    return trimesh.boolean.difference([mesh, c, s], engine=ENGINE)


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stl")
    ap.add_argument("mod", choices=["info", "sieve", "dividers", "text", "round",
                                    "lid", "keyhole"])
    ap.add_argument("--hole", type=float, default=4.0)
    ap.add_argument("--pitch", type=float)
    ap.add_argument("--border", type=float, default=3.0)
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--rows", type=int, default=1)
    ap.add_argument("--text", default="HELLO")
    ap.add_argument("--style", choices=["emboss", "deboss"], default="emboss")
    ap.add_argument("--radius", type=float, default=6.0)
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    mesh = trimesh.load(a.stl, force="mesh")
    report("before", mesh)
    m = measure(mesh)
    if m["wall"] is None or m["floor"] is None:
        sys.exit("Couldn't find the cavity. Is this an open-top box in millimeters?")
    print(f"measured: wall {m['wall']} mm, floor {m['floor']} mm, "
          f"cavity {m['inner_max'][0]-m['inner_min'][0]:.1f} x "
          f"{m['inner_max'][1]-m['inner_min'][1]:.1f} mm")
    if a.mod == "info":
        return

    fn = {"sieve": lambda: sieve(mesh, m, a.hole, a.pitch, a.border),
          "dividers": lambda: dividers(mesh, m, a.cols, a.rows),
          "text": lambda: text(mesh, m, a.text, a.style),
          "round": lambda: rounded(mesh, m, a.radius),
          "lid": lambda: lid(mesh, m),
          "keyhole": lambda: keyhole(mesh, m)}[a.mod]
    out = fn()
    out.merge_vertices()
    if not out.is_watertight:
        trimesh.repair.fill_holes(out)
    report("after", out)
    if not out.is_watertight:
        print("WARNING: result is not watertight; ask for a repair before printing.")

    path = Path(a.out) if a.out else Path(a.stl).with_name(f"{Path(a.stl).stem}_{a.mod}.stl")
    out.export(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
