"""
Build `softwarex_geometry.yaml` for CSF.

Usage example:
    python3 writegeometry_v5.py \
        --z0 0.0 --z1 40.0 \
        --tf-cell 0.30 --tg-base 0.40 --cx 0.0 --cy 0.0 --de 10.0 \
        --th-cell 0.20 --tg-head 0.20 --rcx 0.0 --rcy 0.0 --rdx 6.0 --rdy 4.0 --R 1.0 \
        --N 128 \
        --out softwarex_geometry_4.yaml
"""

import argparse
import math
import yaml


# =========================
# YAML output helpers
# =========================
class CleanDumper(yaml.SafeDumper):
    """YAML dumper with aliases disabled."""
    def ignore_aliases(self, data):
        return True


class Point(list):
    """Marker class so YAML dumps points as compact [x, y]."""
    pass


def _repr_point(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", list(data), flow_style=True)


CleanDumper.add_representer(Point, _repr_point)


# =========================
# Geometry helpers
# =========================
def signed_area(vertices):
    """
    Signed area from shoelace formula.
    Works for open or explicitly closed chains.
    """
    if len(vertices) < 3:
        return 0.0

    a = 0.0
    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return 0.5 * a


def close_loop(points):
    """Close loop explicitly by repeating the first point at the end."""
    if not points:
        return points

    x0, y0 = points[0]
    xN, yN = points[-1]
    if x0 != xN or y0 != yN:
        points = points + [[x0, y0]]
    return points


def to_points(vertices):
    """Convert plain lists into YAML-friendly Point objects."""
    return [Point([float(x), float(y)]) for x, y in vertices]


def rotate_points(points, cx, cy, angle_deg):
    """
    Rotate a list of [x, y] points about (cx, cy) by angle_deg.
    """
    a = math.radians(angle_deg)
    ca = math.cos(a)
    sa = math.sin(a)

    out = []
    for x, y in points:
        dx = x - cx
        dy = y - cy
        xr = cx + ca * dx - sa * dy
        yr = cy + sa * dx + ca * dy
        out.append([xr, yr])
    return out


def circle_loop(cx, cy, r, n, ccw=True, start_angle=0.0):
    """
    Build a circular loop with N equally spaced angles.
    """
    if n < 8:
        raise ValueError("N must be >= 8 for circle quality")
    if r <= 0:
        raise ValueError("Radius must be > 0")

    pts = []
    for i in range(n):
        a = 2.0 * math.pi * (i / n)
        ang = start_angle + (a if ccw else -a)
        pts.append([cx + r * math.cos(ang), cy + r * math.sin(ang)])
    return pts


def rounded_rect_loop(cx, cy, dx, dy, R, n, ccw=True):
    """
    Rounded rectangle sampled approximately uniformly by perimeter length.
    """
    if n < 16:
        raise ValueError("N must be >= 16 for rounded rectangle quality")
    if dx <= 0 or dy <= 0:
        raise ValueError("dx and dy must be > 0")
    if R < 0:
        raise ValueError("R must be >= 0")
    if R > min(dx, dy) / 2.0:
        raise ValueError("R must satisfy R <= min(dx,dy)/2")

    hx, hy = dx / 2.0, dy / 2.0
    Lh = max(dx - 2.0 * R, 0.0)
    Lv = max(dy - 2.0 * R, 0.0)
    La = 0.5 * math.pi * R

    seg = [Lv / 2.0, La, Lh, La, Lv, La, Lh, La, Lv / 2.0]
    P = sum(seg)
    if P <= 0:
        raise ValueError("Degenerate rounded rectangle perimeter")

    cum = [0.0]
    for L in seg:
        cum.append(cum[-1] + L)

    xL, xR = cx - hx, cx + hx
    yB, yT = cy - hy, cy + hy

    cTR = (xR - R, yT - R)
    cTL = (xL + R, yT - R)
    cBL = (xL + R, yB + R)
    cBR = (xR - R, yB + R)

    def at_s(s):
        i = 0
        while i < len(seg) - 1 and s >= cum[i + 1]:
            i += 1

        ds = s - cum[i]
        Li = seg[i]

        if i == 0:
            t = 0.0 if Li == 0 else ds / Li
            return [xR, cy + (yT - R - cy) * t]

        if i == 1:
            a = 0.0 if Li == 0 else (ds / Li) * (math.pi / 2.0)
            return [cTR[0] + R * math.cos(a), cTR[1] + R * math.sin(a)]

        if i == 2:
            t = 0.0 if Li == 0 else ds / Li
            return [xR - R - Lh * t, yT]

        if i == 3:
            a = math.pi / 2.0 if Li == 0 else math.pi / 2.0 + (ds / Li) * (math.pi / 2.0)
            return [cTL[0] + R * math.cos(a), cTL[1] + R * math.sin(a)]

        if i == 4:
            t = 0.0 if Li == 0 else ds / Li
            return [xL, yT - R - Lv * t]

        if i == 5:
            a = math.pi if Li == 0 else math.pi + (ds / Li) * (math.pi / 2.0)
            return [cBL[0] + R * math.cos(a), cBL[1] + R * math.sin(a)]

        if i == 6:
            t = 0.0 if Li == 0 else ds / Li
            return [xL + R + Lh * t, yB]

        if i == 7:
            a = 1.5 * math.pi if Li == 0 else 1.5 * math.pi + (ds / Li) * (math.pi / 2.0)
            return [cBR[0] + R * math.cos(a), cBR[1] + R * math.sin(a)]

        t = 0.0 if Li == 0 else ds / Li
        return [xR, yB + R + (cy - (yB + R)) * t]

    pts = [at_s((k / n) * P) for k in range(n)]
    return pts if ccw else list(reversed(pts))


def build_single_cell_vertices(outer_loop, inner_loop):
    """
    Build one bridged polygon:
      close(outer_loop) + close(inner_loop)

    Then force positive signed area (CCW).
    """
    v = close_loop(outer_loop) + close_loop(inner_loop)

    if signed_area(v) <= 0.0:
        v = list(reversed(v))

    if signed_area(v) <= 0.0:
        raise ValueError("Failed to build CCW single polygon (area <= 0).")

    return v


# =========================
# Main geometry builder
# =========================
def build_geometry(
    z0, z1,
    tf_cell, tg_base, cx, cy, de,
    th_cell, tg_head, rcx, rcy, rdx, rdy, R,
    N,
    twist_deg=0.0,
):
    """
    Build CSF geometry dictionary with two sections (S0, S1).
    """
    # ---------- Base checks ----------
    if tf_cell < 0:
        raise ValueError("Base invalid: tf_cell must be >= 0")
    if tg_base <= 0:
        raise ValueError("Base invalid: tg_base must be > 0")
    if de <= 0:
        raise ValueError("Base invalid: de must be > 0")

    di = de - 2.0 * tg_base
    if di <= 0:
        raise ValueError("Base invalid: require de > 2*tg_base")

    # ---------- Head checks ----------
    if th_cell < 0:
        raise ValueError("Head invalid: th_cell must be >= 0")
    if tg_head <= 0:
        raise ValueError("Head invalid: tg_head must be > 0")
    if rdx <= 0 or rdy <= 0:
        raise ValueError("Head invalid: rdx and rdy must be > 0")
    if R < 0:
        raise ValueError("Head invalid: R must be >= 0")
    if R > min(rdx, rdy) / 2.0:
        raise ValueError("Head invalid: R must satisfy R <= min(rdx,rdy)/2")

    idx = rdx - 2.0 * tg_head
    idy = rdy - 2.0 * tg_head
    if idx <= 0 or idy <= 0:
        raise ValueError("Head invalid: require rdx > 2*tg_head and rdy > 2*tg_head")

    iR = max(R - tg_head, 0.0)

    # ---------- Build S0 ----------
    r_ext = de / 2.0
    r_int = di / 2.0

    s0_outer = circle_loop(cx, cy, r_ext, N, ccw=True, start_angle=0.0)
    s0_inner = circle_loop(cx, cy, r_int, N, ccw=False, start_angle=0.0)
    s0_vertices = build_single_cell_vertices(s0_outer, s0_inner)

    # ---------- Build S1 ----------
    s1_outer = rounded_rect_loop(rcx, rcy, rdx, rdy, R, n=N, ccw=True)
    s1_inner = rounded_rect_loop(rcx, rcy, idx, idy, iR, n=N, ccw=False)

    if twist_deg != 0.0:
        s1_outer = rotate_points(s1_outer, rcx, rcy, twist_deg)
        s1_inner = rotate_points(s1_inner, rcx, rcy, twist_deg)

    s1_vertices = build_single_cell_vertices(s1_outer, s1_inner)

    s0_name = "cell_base@cell" if tf_cell == 0 else f"cell_base@cell@t={tf_cell}"
    s1_name = "cell_head@cell" if th_cell == 0 else f"cell_head@cell@t={th_cell}"

    data = {
        "CSF": {
            "sections": {
                "S0": {
                    "z": float(z0),
                    "polygons": {
                        s0_name: {
                            "weight": 1.0,
                            "vertices": to_points(s0_vertices),
                        }
                    },
                },
                "S1": {
                    "z": float(z1),
                    "polygons": {
                        s1_name: {
                            "weight": 1.0,
                            "vertices": to_points(s1_vertices),
                        }
                    },
                },
            }
        }
    }
    return data


def write_yaml(data, out_file="geometry.yaml"):
    """Write YAML file with stable formatting."""
    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            Dumper=CleanDumper,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=140,
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Build a CSF geometry YAML.")

    parser.add_argument("--z0", type=float, required=True)
    parser.add_argument("--z1", type=float, required=True)

    parser.add_argument("--tf-cell", type=float, required=True)
    parser.add_argument("--tg-base", type=float, required=True)
    parser.add_argument("--cx", type=float, required=True)
    parser.add_argument("--cy", type=float, required=True)
    parser.add_argument("--de", type=float, required=True)

    parser.add_argument("--th-cell", type=float, required=True)
    parser.add_argument("--tg-head", type=float, required=True)
    parser.add_argument("--rcx", type=float, required=True)
    parser.add_argument("--rcy", type=float, required=True)
    parser.add_argument("--rdx", type=float, required=True)
    parser.add_argument("--rdy", type=float, required=True)
    parser.add_argument("--R", type=float, required=True)

    parser.add_argument("--N", type=int, required=True)
    parser.add_argument("--twist-deg", type=float, default=0.0)
    parser.add_argument("--out", type=str, default="softwarex_geometry.yaml")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    geom = build_geometry(
        args.z0, args.z1,
        args.tf_cell, args.tg_base, args.cx, args.cy, args.de,
        args.th_cell, args.tg_head, args.rcx, args.rcy, args.rdx, args.rdy, args.R,
        args.N,
        twist_deg=args.twist_deg,
    )

    write_yaml(geom, args.out)
    print(f"Written: {args.out}")
