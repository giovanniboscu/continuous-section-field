#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
compare_fem3d_cuf_strong_equilibrium_v2.py

FEM3D-H8 vs CSF-CUF-L9
element/domain-interior strong-equilibrium diagnostic.

At the SAME physical H8 Gauss points, compute:

(div sigma)_x =
    d sigma_xx/dx + d tau_xy/dy + d tau_xz/dz

(div sigma)_y =
    d tau_xy/dx + d sigma_yy/dy + d tau_yz/dz

(div sigma)_z =
    d tau_xz/dx + d tau_yz/dy + d sigma_zz/dz

For each selected native H8 Gauss x-plane, use ALL available H8 Gauss points and save section statistics
(median, mean, RMS, max) for:
  - each of the 9 derivative terms;
  - div_x, div_y, div_z;
  - total ||div sigma||;
for FEM H8 and CUF L9.

Typical usage from cuf/I-Shape:

PYTHONPATH="../../src" python3 compare_fem3d_cuf_strong_equilibrium.py \
  --fem fem3d/output/fem3d_taper.npz \
  --cuf output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --csf models/carrera_i_shaped_taper80_l9_web3.yaml \
  --sections 40 \
  --xmin 0.01 \
  --xmax 0.99 \
  --output-dir diagnostics/equilibrium_multisection_components

Important:
  This is an element/domain-interior strong-form diagnostic. Finite
  differences are restricted to remain inside the same H8 element and
  the same CSF domain; interface traction-jump terms are not included.
  Both displacement methods enforce equilibrium primarily in weak form.
"""

import argparse
import csv
import math
from pathlib import Path
import numpy as np

H8_SIGNS = np.array([
    [-1., -1., -1.], [ 1., -1., -1.], [ 1.,  1., -1.], [-1.,  1., -1.],
    [-1., -1.,  1.], [ 1., -1.,  1.], [ 1.,  1.,  1.], [-1.,  1.,  1.],
], dtype=float)

def h8_shape(q):
    q = np.asarray(q, dtype=float)
    t = 1.0 + H8_SIGNS*q
    N = t.prod(axis=1)/8.0
    dN = np.stack([
        H8_SIGNS[:,i] * t[:,(i+1)%3] * t[:,(i+2)%3] / 8.0
        for i in range(3)
    ], axis=1)
    return N, dN

def inverse_h8(coords, xyz, q0=None, tol=1e-12, maxit=40):
    q = np.zeros(3) if q0 is None else np.asarray(q0, dtype=float).copy()
    xyz = np.asarray(xyz, dtype=float)
    for _ in range(maxit):
        N, dN = h8_shape(q)
        r = N @ coords - xyz
        if np.linalg.norm(r, ord=np.inf) <= tol:
            return q
        J = coords.T @ dN
        q -= np.linalg.solve(J, r)
    raise RuntimeError(
        f"H8 inverse mapping did not converge after {maxit} iterations; "
        f"last residual inf-norm={np.linalg.norm(r, ord=np.inf):.6e}"
    )

def h8_u_grad(coords, disp, xyz):
    q = inverse_h8(coords, xyz)
    N, dN = h8_shape(q)
    J = coords.T @ dN
    if np.linalg.det(J) <= 0:
        raise ValueError("Invalid H8 Jacobian")
    gradN = np.linalg.solve(J.T, dN.T).T
    u = N @ disp
    grad_u = disp.T @ gradN
    return u, grad_u, q

def strain_from_grad(g):
    return np.array([
        g[0,0], g[1,1], g[2,2],
        g[1,2] + g[2,1],
        g[0,2] + g[2,0],
        g[0,1] + g[1,0],
    ], dtype=float)

def isotropic_C(E, G, nu):
    G_iso = E / (2.0 * (1.0 + nu))
    if not np.isclose(G, G_iso, rtol=1e-8, atol=0.0):
        raise ValueError(
            "Inconsistent isotropic constants: "
            f"E={E:.12e}, nu={nu:.12e}, G={G:.12e}, "
            f"expected G={G_iso:.12e}"
        )

    lam = E*nu/((1.0+nu)*(1.0-2.0*nu))
    C = np.zeros((6,6), dtype=float)
    C[:3,:3] = lam
    C[0,0] += 2*G
    C[1,1] += 2*G
    C[2,2] += 2*G
    C[3,3] = C[4,4] = C[5,5] = G
    return C

def load_fem(path):
    with np.load(path, allow_pickle=False) as d:
        nodes = np.asarray(d["nodes"], dtype=float)
        conn = np.asarray(d["elements"], dtype=int)
        disp = np.asarray(d["displacement"], dtype=float)
        E = np.asarray(d["element_E"], dtype=float)
        G = np.asarray(d["element_G"], dtype=float)
        nu = np.asarray(d["element_nu"], dtype=float)
    if conn.min() >= 1 and conn.max() == len(nodes):
        conn = conn - 1
    return nodes, conn, disp, E, G, nu

def fem_stress(nodes, conn, disp, E, G, nu, ei, xyz):
    c = nodes[conn[ei]]
    u = disp[conn[ei]]
    _, grad, q = h8_u_grad(c, u, xyz)
    eps = strain_from_grad(grad)
    sig = isotropic_C(E[ei], G[ei], nu[ei]) @ eps
    return sig, q

def load_cuf(cuf_path, csf_path):
    from csf.cuf.solver.compiled_field import CompiledDisplacementField
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    return CompiledDisplacementField.load(cuf_path), CSFCUFModelBridge.from_yaml(csf_path)

def cuf_stress(field, bridge, x, y, z, domain_index):
    grad = np.asarray(
        field.displacement_gradient(x, y, z, domain_index=domain_index),
        dtype=float
    )
    eps = strain_from_grad(grad)
    C = np.asarray(
        bridge.constitutive_provider.matrix(
            x=x, y=y, z=z, domain_id=domain_index+1
        ),
        dtype=float
    )
    return C @ eps

def point_in_polygon(point, vertices):
    from matplotlib.path import Path as MplPath
    scale = max(1.0, float(np.max(np.abs(vertices))))
    return bool(MplPath(vertices).contains_point(tuple(point), radius=-1e-10*scale))

def domain_for_point(section, y, z):
    owners = []
    for pi, p in enumerate(section.polygons):
        v = np.asarray([(float(a.x), float(a.y)) for a in p.vertices], dtype=float)
        if point_in_polygon((y,z), v):
            owners.append(pi)
    return owners[0] if len(owners) == 1 else None

def gauss_points_for_element(coords):
    a = 1.0/math.sqrt(3.0)
    for gi, q in enumerate(
        (np.array([r,s,t]) for r in (-a,a) for s in (-a,a) for t in (-a,a)),
        start=1
    ):
        N, _ = h8_shape(q)
        yield gi, q, N @ coords

def find_element(nodes, conn, xyz, preferred=None):
    xyz = np.asarray(xyz, dtype=float)
    scale = max(1.0, float(np.ptp(nodes, axis=0).max()))
    tol = 1e-10*scale
    order = [preferred] if preferred is not None else range(len(conn))
    for ei in order:
        c = nodes[conn[ei]]
        lo, hi = c.min(axis=0), c.max(axis=0)
        if np.any(xyz < lo-tol) or np.any(xyz > hi+tol):
            continue
        try:
            q = inverse_h8(c, xyz)
        except Exception:
            continue
        if np.max(np.abs(q)) <= 1.0 + 1e-8:
            return ei
    return None

def stress_derivatives(stress_fn, xyz, h):
    xyz = np.asarray(xyz, dtype=float)
    deriv = np.zeros((6,3), dtype=float)
    for j in range(3):
        pp = xyz.copy()
        pm = xyz.copy()
        pp[j] += h[j]
        pm[j] -= h[j]
        deriv[:,j] = (np.asarray(stress_fn(pp)) - np.asarray(stress_fn(pm))) / (2.0*h[j])

    # Voigt order: xx, yy, zz, yz, xz, xy
    terms = {
        "dsigmaxx_dx": deriv[0,0],
        "dtauxy_dy":   deriv[5,1],
        "dtauxz_dz":   deriv[4,2],

        "dtauxy_dx":   deriv[5,0],
        "dsigmayy_dy": deriv[1,1],
        "dtauyz_dz":   deriv[3,2],

        "dtauxz_dx":   deriv[4,0],
        "dtauyz_dy":   deriv[3,1],
        "dsigmazz_dz": deriv[2,2],
    }
    terms["div_x"] = terms["dsigmaxx_dx"] + terms["dtauxy_dy"] + terms["dtauxz_dz"]
    terms["div_y"] = terms["dtauxy_dx"] + terms["dsigmayy_dy"] + terms["dtauyz_dz"]
    terms["div_z"] = terms["dtauxz_dx"] + terms["dtauyz_dy"] + terms["dsigmazz_dz"]
    terms["div_norm"] = math.sqrt(
        terms["div_x"]**2 + terms["div_y"]**2 + terms["div_z"]**2
    )
    return terms

def stats_abs(values):
    a = np.abs(np.asarray(values, dtype=float))
    if a.size == 0:
        return (np.nan, np.nan, np.nan, np.nan)
    return (
        float(np.median(a)),
        float(np.mean(a)),
        float(np.sqrt(np.mean(a*a))),
        float(np.max(a)),
    )

def select_planes(all_x, targets):
    all_x = np.asarray(sorted(set(float(v) for v in all_x)), dtype=float)
    chosen = []
    for t in targets:
        chosen.append(float(all_x[int(np.argmin(np.abs(all_x-t)))]))
    return np.asarray(sorted(set(chosen)), dtype=float)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fem", required=True)
    ap.add_argument("--cuf", required=True)
    ap.add_argument("--csf", required=True)
    ap.add_argument("--sections", type=int, default=40)
    ap.add_argument("--xmin", type=float, default=0.01)
    ap.add_argument("--xmax", type=float, default=0.99)
    ap.add_argument("--fd-fraction", type=float, default=1e-3)
    ap.add_argument("--output-dir", default="diagnostics/equilibrium_multisection_components")
    args = ap.parse_args()

    if args.sections < 2:
        raise ValueError("--sections must be >= 2")
    if not (0.0 <= args.xmin < args.xmax <= 1.0):
        raise ValueError("Require 0 <= xmin < xmax <= 1")

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, conn, disp, E, G, nu = load_fem(args.fem)
    field, bridge = load_cuf(args.cuf, args.csf)
    csf_field = bridge.field

    x0 = float(nodes[:,0].min())
    x1 = float(nodes[:,0].max())
    L = x1-x0

    all_points = []
    all_x = []
    for ei in range(len(conn)):
        coords = nodes[conn[ei]]
        for gi, q, xyz in gauss_points_for_element(coords):
            all_points.append((ei, gi, xyz))
            all_x.append(float(xyz[0]))

    targets = x0 + np.linspace(args.xmin, args.xmax,args.sections)*L
    planes = select_planes(all_x, targets)

    term_names = [
        "dsigmaxx_dx","dtauxy_dy","dtauxz_dz","div_x",
        "dtauxy_dx","dsigmayy_dy","dtauyz_dz","div_y",
        "dtauxz_dx","dtauyz_dy","dsigmazz_dz","div_z",
        "div_norm",
    ]

    point_rows = []
    section_rows = []

    for si, xp in enumerate(planes, start=1):
        tolx = 1e-10*max(1.0, L)
        cand = [(ei,gi,xyz) for ei,gi,xyz in all_points
                if abs(float(xyz[0])-xp) <= tolx]

        fem_values = {k: [] for k in term_names}
        cuf_values = {k: [] for k in term_names}
        accepted = 0

        for ei, gi, xyz in cand:
            sec = csf_field.section(float(xyz[0]))
            di = domain_for_point(sec, float(xyz[1]), float(xyz[2]))
            if di is None:
                continue

            ecoords = nodes[conn[ei]]
            lo, hi = ecoords.min(axis=0), ecoords.max(axis=0)
            h = np.maximum((hi-lo)*args.fd_fraction, 1e-8)

            valid = True
            for j in range(3):
                for sign in (-1,1):
                    p = xyz.copy()
                    p[j] += sign*h[j]
                    if find_element(nodes, conn, p, preferred=ei) != ei:
                        valid = False
                        break
                    s2 = csf_field.section(float(p[0]))
                    if domain_for_point(s2, float(p[1]), float(p[2])) != di:
                        valid = False
                        break
                if not valid:
                    break
            if not valid:
                continue

            def fs(p):
                return fem_stress(nodes, conn, disp, E, G, nu, ei, p)[0]

            def cs(p):
                return cuf_stress(field, bridge, float(p[0]), float(p[1]), float(p[2]), di)

            ft = stress_derivatives(fs, xyz, h)
            ct = stress_derivatives(cs, xyz, h)

            accepted += 1
            for k in term_names:
                fem_values[k].append(ft[k])
                cuf_values[k].append(ct[k])

            point_rows.append(
                [si, xp, (xp-x0)/L, ei+1, gi, di+1, float(xyz[1]), float(xyz[2])]
                + [ft[k] for k in term_names]
                + [ct[k] for k in term_names]
            )

        row = [si, xp, (xp-x0)/L, len(cand), accepted]
        for k in term_names:
            row += list(stats_abs(fem_values[k]))
            row += list(stats_abs(cuf_values[k]))
        section_rows.append(row)

        if accepted:
            fmed = stats_abs(fem_values["div_norm"])[0]
            cmed = stats_abs(cuf_values["div_norm"])[0]
            fx = stats_abs(fem_values["div_x"])[0]
            cx = stats_abs(cuf_values["div_x"])[0]
            fy = stats_abs(fem_values["div_y"])[0]
            cy = stats_abs(cuf_values["div_y"])[0]
            fz = stats_abs(fem_values["div_z"])[0]
            cz = stats_abs(cuf_values["div_z"])[0]
            print(
                f"[{si:02d}/{len(planes):02d}] x/L={(xp-x0)/L:.6f} points={accepted:4d} "
                f"TOTAL F/C={fmed:.3e}/{cmed:.3e} "
                f"div_x={fx:.3e}/{cx:.3e} "
                f"div_y={fy:.3e}/{cy:.3e} "
                f"div_z={fz:.3e}/{cz:.3e}",
                flush=True
            )

    point_csv = outdir/"equilibrium_component_points_all_sections.csv"
    with point_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["section_index","x","x_over_L","element_id","gauss_index","domain_id","y","z"]
            + ["fem_"+k for k in term_names]
            + ["cuf_"+k for k in term_names]
        )
        w.writerows(point_rows)

    stat_names = ["median","mean","rms","max"]
    sec_header = ["section_index","x","x_over_L","candidate_points","accepted_points"]
    for k in term_names:
        for prefix in ("fem","cuf"):
            for s in stat_names:
                sec_header.append(f"{prefix}_{k}_{s}")

    section_csv = outdir/"equilibrium_component_sections_summary.csv"
    with section_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(sec_header)
        w.writerows(section_rows)

    sec = np.asarray(section_rows, dtype=float)
    col = {name:i for i,name in enumerate(sec_header)}

    summary = []
    summary.append("Multi-section decomposition of all equilibrium equations")
    summary.append("="*92)
    summary.append(f"sections = {len(section_rows)}")
    summary.append(f"accepted Gauss samples = {len(point_rows)}")
    summary.append(f"x/L range = [{args.xmin:.6g}, {args.xmax:.6g}]")
    summary.append("sampling = ALL available native H8 Gauss points on every selected x-plane")
    summary.append("")

    for eq in ("div_x","div_y","div_z","div_norm"):
        fcol = col[f"fem_{eq}_median"]
        ccol = col[f"cuf_{eq}_median"]
        fm = np.nanmedian(sec[:,fcol])
        cm = np.nanmedian(sec[:,ccol])
        lower = int(np.sum(sec[:,ccol] < sec[:,fcol]))
        summary.append(
            f"{eq:8s}: median across sections FEM={fm:.6e} CUF={cm:.6e} "
            f"| sections with CUF residual < FEM residual: {lower}/{len(sec)}"
        )

    summary.append("")
    summary.append("Nine derivative terms: median across sections of per-section median |term|")
    for k in [
        "dsigmaxx_dx","dtauxy_dy","dtauxz_dz",
        "dtauxy_dx","dsigmayy_dy","dtauyz_dz",
        "dtauxz_dx","dtauyz_dy","dsigmazz_dz",
    ]:
        fm = np.nanmedian(sec[:,col[f"fem_{k}_median"]])
        cm = np.nanmedian(sec[:,col[f"cuf_{k}_median"]])
        summary.append(f"  {k:14s} FEM={fm:.6e} CUF={cm:.6e}")

    summary_path = outdir/"summary.txt"
    summary_path.write_text("\n".join(summary)+"\n", encoding="utf-8")

    try:
        import matplotlib.pyplot as plt
        x = sec[:, col["x_over_L"]]

        # Final residuals
        for eq, title in [
            ("div_x","Equilibrium x"),
            ("div_y","Equilibrium y"),
            ("div_z","Equilibrium z"),
            ("div_norm","Total equilibrium residual"),
        ]:
            plt.figure()
            plt.plot(x, sec[:,col[f"fem_{eq}_median"]], marker="o", markersize=3, label="FEM H8")
            plt.plot(x, sec[:,col[f"cuf_{eq}_median"]], marker="o", markersize=3, label="CUF L9")
            plt.yscale("log")
            plt.xlabel("x/L")
            plt.ylabel(f"median |{eq}|")
            plt.title(title)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            plt.savefig(outdir/f"{eq}_median_vs_x.png", dpi=180)
            plt.close()

        # Three-term decomposition for each equilibrium equation.
        groups = {
            "x": ["dsigmaxx_dx","dtauxy_dy","dtauxz_dz"],
            "y": ["dtauxy_dx","dsigmayy_dy","dtauyz_dz"],
            "z": ["dtauxz_dx","dtauyz_dy","dsigmazz_dz"],
        }

        for eqname, terms in groups.items():
            plt.figure()
            for k in terms:
                plt.plot(x, sec[:,col[f"fem_{k}_median"]], label=f"FEM {k}")
                plt.plot(x, sec[:,col[f"cuf_{k}_median"]], linestyle="--", label=f"CUF {k}")
            plt.yscale("log")
            plt.xlabel("x/L")
            plt.ylabel("median |stress-gradient term|")
            plt.title(f"Equilibrium {eqname}: three contributing terms")
            plt.grid(True, alpha=0.3)
            plt.legend(fontsize=7)
            plt.tight_layout()
            plt.savefig(outdir/f"equilibrium_{eqname}_terms_median_vs_x.png", dpi=180)
            plt.close()

        # Ratios CUF/FEM for final residuals.
        plt.figure()
        for eq in ("div_x","div_y","div_z","div_norm"):
            ratio = sec[:,col[f"cuf_{eq}_median"]] / np.maximum(
                sec[:,col[f"fem_{eq}_median"]], 1e-30
            )
            plt.plot(x, ratio, marker="o", markersize=3, label=eq)
        plt.axhline(1.0, linewidth=0.8)
        plt.yscale("log")
        plt.xlabel("x/L")
        plt.ylabel("CUF/FEM median residual")
        plt.title("Residual ratio by section (<1 means CUF smaller)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(outdir/"residual_ratio_cuf_over_fem_vs_x.png", dpi=180)
        plt.close()

    except Exception as e:
        (outdir/"plot_warning.txt").write_text(str(e)+"\n", encoding="utf-8")

    print("")
    print("\n".join(summary))
    print("="*92)
    print("Saved:", point_csv)
    print("Saved:", section_csv)
    print("Saved:", summary_path)
    print("Output directory:", outdir)

if __name__ == "__main__":
    main()
