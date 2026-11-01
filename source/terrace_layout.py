"""Geometry-independent layout and terrace topology for the building HDA.

All rectangles use (xmin, xmax, zmin, zmax). This module deliberately has no
Houdini dependency so its footprint and boundary rules can be checked directly.
The build script embeds a copy in the HDA; the HIP will not import this file.
"""
from math import ceil

EPS = 1e-6


def contains(rect, x, z):
    return rect[0] - EPS <= x <= rect[1] + EPS and rect[2] - EPS <= z <= rect[3] + EPS


def inside(rects, x, z):
    return any(contains(r, x, z) for r in rects)


def modules(width, depth, bays, x=0.0, z=0.0, recess=1.2, parity=0):
    """Continuous side-by-side modules, with alternating facade recesses."""
    bays = max(2, min(12, int(bays)))
    width, depth = max(8.0, width), max(5.0, depth)
    pitch = width / bays
    out = []
    for col in range(bays):
        cx = x - width / 2 + (col + .5) * pitch
        dz = -recess if (col + parity) % 2 else 0.0
        out.append({'col': col, 'cx': cx, 'width': pitch,
                    'rect': (cx - pitch/2, cx + pitch/2,
                             z + dz - depth/2, z + dz + depth/2),
                    'recessed': bool((col + parity) % 2)})
    return out


def difference_grid(lower, upper):
    """Exact cell decomposition of a union of rectangles minus another union."""
    if not lower:
        return [], [], set()
    all_rects = lower + upper
    xs = sorted(set(round(v, 6) for r in all_rects for v in r[:2]))
    zs = sorted(set(round(v, 6) for r in all_rects for v in r[2:]))
    cells = set()
    for i in range(len(xs)-1):
        for j in range(len(zs)-1):
            x, z = (xs[i]+xs[i+1])/2, (zs[j]+zs[j+1])/2
            if inside(lower, x, z) and not inside(upper, x, z):
                cells.add((i, j))
    return xs, zs, cells


def terrace_regions(lower, upper):
    """Return exposed deck cells and safety rails only along falling edges.

    An edge beside the upper footprint is a wall contact, so it receives no
    railing. This also leaves access from upper-floor terrace doors unobstructed.
    Shared cell edges are discarded before collinear segments are joined.
    """
    xs, zs, cells = difference_grid(lower, upper)
    decks = [(xs[i], xs[i+1], zs[j], zs[j+1]) for i, j in sorted(cells)]
    edges = []
    for i, j in cells:
        x0, x1, z0, z1 = xs[i], xs[i+1], zs[j], zs[j+1]
        candidates = [((-1, 0), (x0, z0, x0, z1), (x0-.001, (z0+z1)/2)),
                      ((1, 0), (x1, z0, x1, z1), (x1+.001, (z0+z1)/2)),
                      ((0, -1), (x0, z0, x1, z0), ((x0+x1)/2, z0-.001)),
                      ((0, 1), (x0, z1, x1, z1), ((x0+x1)/2, z1+.001))]
        for (di, dj), edge, sample in candidates:
            if (i+di, j+dj) not in cells and not inside(upper, *sample):
                edges.append(edge)
    return decks, join_edges(edges)


def join_edges(edges):
    groups = {}
    for x0, z0, x1, z1 in edges:
        vertical = abs(x1-x0) < EPS
        key = ('z', round(x0, 6)) if vertical else ('x', round(z0, 6))
        interval = (min(z0,z1), max(z0,z1)) if vertical else (min(x0,x1), max(x0,x1))
        groups.setdefault(key, []).append(interval)
    joined = []
    for (axis, fixed), intervals in sorted(groups.items()):
        merged = []
        for lo, hi in sorted(intervals):
            if merged and lo <= merged[-1][1]+EPS:
                merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
            else:
                merged.append((lo, hi))
        for lo, hi in merged:
            joined.append((fixed, lo, fixed, hi) if axis == 'z' else (lo, fixed, hi, fixed))
    return joined


def area(rects):
    return sum((r[1]-r[0])*(r[3]-r[2]) for r in rects)


def frontage_access(module, lower, depth=.65):
    """True only if a usable lower roof exists outside the current front door."""
    r = module['rect']
    x = (r[0]+r[1])/2
    return all(inside(lower, x+dx, r[3]+dz)
               for dx in (-.45, .45) for dz in (.12, depth))


def support_segments(current, lower, min_length=.35):
    """Find unsupported footprint cells for the required overhang beams."""
    xs, zs, cells = difference_grid(current, lower)
    out = []
    for i,j in sorted(cells):
        x0,x1,z0,z1=xs[i],xs[i+1],zs[j],zs[j+1]
        if min(x1-x0,z1-z0)<.12:
            continue
        x,z=(x0+x1)/2,(z0+z1)/2
        # Attach to the nearest supported rectangle edge, instead of the ground.
        candidates=[]
        for a,b,c,d in lower:
            tx=min(max(x,a+.08),b-.08)
            tz=min(max(z,c+.08),d-.08)
            candidates.append(((x-tx)**2+(z-tz)**2,tx,tz))
        if candidates:
            _,tx,tz=min(candidates)
            if ((x-tx)**2+(z-tz)**2)**.5>=min_length:
                out.append((x,z,tx,tz))
    return out
