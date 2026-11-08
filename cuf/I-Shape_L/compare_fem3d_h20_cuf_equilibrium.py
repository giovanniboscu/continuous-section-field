#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Common-point FEM3D-H20 vs CSF-CUF-L9 benchmark (I-Shape_L).

No structural solve is performed. The 20-node FEM displacement and the saved
compiled CUF displacement are evaluated at the SAME physical quadrature points.

Equilibrium, in physical FEM coordinates (x=longitudinal, y,z=section):
    r_x = sigma_xx,x + sigma_xy,y + sigma_xz,z
    r_y = sigma_xy,x + sigma_yy,y + sigma_yz,z
    r_z = sigma_xz,x + sigma_yz,y + sigma_zz,z

Both are element/domain INTERIOR strong residuals. Weak equilibrium, internal
traction jumps and boundary-traction residuals are separate diagnostics.

The FEM3D H20 E,nu are read per ELEMENT from the saved solved NPZ (piecewise
constant material), while CUF material varies according to the S0->S1 CSF YAML.
The models implement the same material law but discretise it differently.

Dependencies: numpy, pyyaml, and the sibling fem3d/run_bending_fem3d_h20.py,
fem3d/h20_strong_residual.py and fem3d/run_bending_fem3d_v2.py.
The CUF compiled_field.py comes from the installed continuous-section-field code.
No OpenSeesPy or SciPy solve is required.

Usage (from cuf/I-Shape_L):
 python3 compare_fem3d_h20_cuf_equilibrium.py \\
   --fem fem3d/output/h20_convergence/T4_h20.npz \\
   --cuf output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \\
   --csf models/carrera_i_shaped_taper80_l9_web3.yaml \\
   --max-elements 300 --gauss 2 --output-dir diagnostics/h20_vs_cuf

For FULL volume quadrature: --max-elements 0 --gauss 2 (more costly).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
import yaml

VERSION = "H20-CUF same-point comparison v3 (section-bin regression fix)"

KEYS = ("div_x", "div_y", "div_z", "div_norm")
TERM_KEYS = (
    "dsigmaxx_dx", "dtauxy_dy", "dtauxz_dz",
    "dtauxy_dx", "dsigmayy_dy", "dtauyz_dz",
    "dtauxz_dx", "dtauyz_dy", "dsigmazz_dz",
)
ALL_KEYS = TERM_KEYS + KEYS


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_helpers(script_dir, override=None):
    fem_dir = script_dir / "fem3d"
    if not (fem_dir / "h20_strong_residual.py").exists():
        raise FileNotFoundError(f"Required sibling module not found: {fem_dir / 'h20_strong_residual.py'}")
    sys.path.insert(0, str(fem_dir))
    from run_bending_fem3d_h20 import h20_shape
    from h20_strong_residual import residual_at

    if override is not None:
        path = Path(override)
        spec = importlib.util.spec_from_file_location("_cuf_compiled_independent", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load compiled field module {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        Field = module.CompiledDisplacementField
    else:
        try:
            from csf.cuf.solver.compiled_field import CompiledDisplacementField as Field
        except ImportError:
            candidates = [
                (script_dir / "../../src/csf/cuf/solver/compiled_field.py").resolve(),
                (script_dir / "../src/csf/cuf/solver/compiled_field.py").resolve(),
            ]
            selected = next((p for p in candidates if p.is_file()), None)
            if selected is None:
                raise RuntimeError(
                    "CUF compiled field unavailable. From cuf/I-Shape_L run with "
                    "PYTHONPATH=../../src or install csfpy in the active environment."
                )
            spec = importlib.util.spec_from_file_location("_cuf_compiled_fallback", selected)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            Field = module.CompiledDisplacementField
    return h20_shape, residual_at, Field


class PhysicalMaterial:
    """Read exactly this benchmark's 9-domain isotropic CSF YAML.

    Fail explicitly for other laws; never silently replace non-isotropic models.
    """
    def __init__(self, path):
        with Path(path).open(encoding="utf-8") as file:
            doc = yaml.safe_load(file)
        sections = doc["CSF"]["sections"]
        a, b = sections["S0"], sections["S1"]
        self.x0, self.x1 = float(a["z"]), float(b["z"])
        if not self.x1 > self.x0:
            raise ValueError("Invalid CSF longitudinal endpoints")
        pa, pb = a["polygons"], b["polygons"]
        if len(pa) != len(pb):
            raise ValueError("Different polygon counts between CSF endpoints")
        self.names = [p["name"] for p in pa]
        if self.names != [p["name"] for p in pb]:
            raise ValueError("CSF polygon ordering differs between endpoints")
        self.weights0 = np.array([float(p["weight"]) for p in pa])
        self.weights1 = np.array([float(p["weight"]) for p in pb])
        self.vertices = np.array([
            [np.asarray(p["vertices"], float) for p in pa],
            [np.asarray(p["vertices"], float) for p in pb],
        ])
        if self.vertices.ndim != 4 or self.vertices.shape[-2:] != (4, 2):
            raise ValueError("This script requires four-corner CUF domains")
        laws = doc["CSF"].get("shear_weight_laws", [])
        if len(laws) != 1:
            raise ValueError("Expected exactly one shear_weight_law: iso(nu)")
        match = re.fullmatch(r"\s*iso\(\s*([\d.eE+-]+)\s*\)\s*", str(laws[0]))
        if not match:
            raise ValueError(f"Unsupported material law {laws!r}; expected iso(nu)")
        self.nu = float(match.group(1))
        if not (-1.0 < self.nu < .5):
            raise ValueError("Invalid isotropic Poisson ratio")
        self.Gfactor = 1.0/(2.0*(1.0+self.nu))
        self.lam_factor = self.nu/((1.0+self.nu)*(1.0-2.0*self.nu))

    def E(self, x, di):
        alpha = (x-self.x0)/(self.x1-self.x0)
        return (1-alpha)*self.weights0[di] + alpha*self.weights1[di]

    def stress(self, gradient, x, di):
        E = self.E(x,di)
        G = E*self.Gfactor
        lam = E*self.lam_factor
        tr = float(np.trace(gradient))
        return np.array([
            lam*tr+2*G*gradient[0,0],
            lam*tr+2*G*gradient[1,1],
            lam*tr+2*G*gradient[2,2],
            G*(gradient[1,2]+gradient[2,1]),
            G*(gradient[0,2]+gradient[2,0]),
            G*(gradient[0,1]+gradient[1,0]),
        ])

    def verify_geometry(self, field):
        for x, expected in ((self.x0, self.vertices[0]), (self.x1, self.vertices[1])):
            actual = field.domain_vertices_at(x)
            if actual is None or actual.shape != expected.shape:
                raise ValueError(f"CUF field domain geometry differs from CSF YAML at x={x}")
            delta = float(np.max(np.abs(actual-expected)))
            if delta > 1e-6:
                raise ValueError(f"CUF domains do not match YAML at x={x}: max error {delta:.3g} mm")


def distance_to_poly_edges(yz, vertices):
    """Minimum physical distance to a four-sided CSF domain boundary."""
    v = np.asarray(vertices,float)
    p = np.asarray(yz,float)
    distances = []
    crosses = []
    for i in range(4):
        a,b = v[i], v[(i+1)%4]
        d = b-a
        t = max(0., min(1., float(np.dot(p-a,d)/np.dot(d,d))))
        distances.append(float(np.linalg.norm(p-(a+t*d))))
        crosses.append(float(d[0]*(p[1]-a[1])-d[1]*(p[0]-a[0])))
    # Strict convex polygon interior; no ambiguous one-sided stresses.
    if not (all(c > 1e-9 for c in crosses) or all(c < -1e-9 for c in crosses)):
        return -1.
    return min(distances)


def find_domain(field, material, xyz):
    v = field.domain_vertices_at(float(xyz[0]))
    candidates = []
    for di, vertices in enumerate(v):
        dist = distance_to_poly_edges(xyz[1:], vertices)
        if dist > 1e-8:
            candidates.append((di,dist))
    if len(candidates) != 1:
        return None, 0.
    return candidates[0]


def fem_at(X, U, E, nu, q, shape, residual_fn, h):
    N, D = shape(q)
    x = N @ X
    J = X.T @ D
    det = float(np.linalg.det(J))
    if det <= 0:
        raise ValueError(f"Nonpositive H20 Jacobian {det}")
    u = N @ U
    r, _, deriv = residual_fn(X,U,E,nu,q,dh=h)
    return x,u,r,det,deriv


def div_terms(ds):
    """ds[stress_voigt,coord], Voigt=(xx,yy,zz,yz,xz,xy)."""
    result = dict(zip(TERM_KEYS,(
        ds[0,0],ds[5,1],ds[4,2],
        ds[5,0],ds[1,1],ds[3,2],
        ds[4,0],ds[3,1],ds[2,2],
    )))
    result["div_x"] = result["dsigmaxx_dx"] + result["dtauxy_dy"] + result["dtauxz_dz"]
    result["div_y"] = result["dtauxy_dx"] + result["dsigmayy_dy"] + result["dtauyz_dz"]
    result["div_z"] = result["dtauxz_dx"] + result["dtauyz_dy"] + result["dsigmazz_dz"]
    result["div_norm"] = math.sqrt(sum(result[f"div_{k}"]**2 for k in 'xyz'))
    return result


def stress_gradient_cuf(field, material, xyz, di, dist, h_ref, boundaries):
    x, y, z = map(float,xyz)
    # Constrain the x finite differences to a single longitudinal FE and the
    # y,z differences to a single material domain.
    bx = np.min(np.abs(boundaries-x))
    h = np.array([min(h_ref[0],.2*bx),
                  min(h_ref[1],.2*dist),min(h_ref[2],.2*dist)],float)
    if np.any(h < 2e-7):
        raise ValueError("CUF sample too close to element/domain interface")

    def stress_at(p):
        g = field.displacement_gradient(float(p[0]),float(p[1]),float(p[2]),domain_index=di)
        return material.stress(g,float(p[0]),di)

    ds = np.zeros((6,3),float)
    for k in range(3):
        xp = np.asarray(xyz,float).copy()
        xm = xp.copy()
        xp[k] += h[k]
        xm[k] -= h[k]
        # Use one domain side; reject discontinuities rather than silently
        # swapping the domain for one of the derivative perturbations.
        if not (distance_to_poly_edges(xp[1:],field.domain_vertices_at(xp[0])[di])>0
                and distance_to_poly_edges(xm[1:],field.domain_vertices_at(xm[0])[di])>0):
            raise ValueError("Finite-difference perturbation crossed CSF interface")
        ds[:,k] = (stress_at(xp)-stress_at(xm))/(2*h[k])
    return ds


def sample_elements(regions, xmid, max_elems, seed):
    """Exactly max_elems reproducible samples, stratified by region and x layer."""
    n = len(regions)
    if max_elems <= 0 or max_elems >= n:
        return np.arange(n)
    rng = np.random.default_rng(seed)
    regions = np.asarray(regions)
    chosen = []
    unique_regions = np.unique(regions)
    sizes = np.array([np.count_nonzero(regions==k) for k in unique_regions])
    expected = max_elems * sizes / n
    target = np.floor(expected).astype(int)
    remaining = max_elems-int(target.sum())
    for i in np.argsort(-(expected-target))[:remaining]:
        target[i] += 1
    for region, count in zip(unique_regions,target):
        if count == 0:
            continue
        ids = np.flatnonzero(regions==region)
        layers,inv = np.unique(xmid[ids],return_inverse=True)
        ng = len(layers)
        # Strata spread uniformly along x. Repeated strata on the same layer
        # receive additional randomly chosen transverse elements.
        layer_indices = np.floor((np.arange(count)+.5)*ng/count).astype(int)
        regional = []
        for layer in np.unique(layer_indices):
            n_here = int(np.sum(layer_indices==layer))
            candidates = ids[inv==layer]
            pick = rng.choice(candidates,size=min(n_here,len(candidates)),replace=False)
            regional.extend(pick.tolist())
        if len(regional)<count:
            rest = np.setdiff1d(ids,np.asarray(regional,dtype=int))
            regional.extend(rng.choice(rest,size=count-len(regional),replace=False).tolist())
        chosen.extend(regional)
    chosen=np.array(sorted(set(chosen)),dtype=int)
    if len(chosen)!=max_elems:
        raise RuntimeError(f"Sampling bug: requested {max_elems} elements, got {len(chosen)}")
    return chosen

def weighted_median(a,w):
    order = np.argsort(a)
    return float(a[order[np.searchsorted(np.cumsum(w[order]),np.sum(w)/2)]] )


def metrics(rows, which, key):
    a = np.asarray([abs(row[f"{which}_{key}"]) for row in rows],float)
    w = np.asarray([row["weight_mm3"] for row in rows],float)
    return {"median_abs":weighted_median(a,w),
            "mean_abs":float(np.average(a,weights=w)),
            "rms":float(np.sqrt(np.average(a*a,weights=w))),
            "max_abs":float(a.max())}


def write_csv(path,rows,keys):
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(keys))
        w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', action='version', version=VERSION)
    ap.add_argument('--fem',type=Path,required=True,help='Solved FEM3D H20 NPZ, e.g. T4_h20.npz')
    ap.add_argument('--cuf',type=Path,required=True,help='Compiled .cuf.npz field')
    ap.add_argument('--csf',type=Path,required=True,help='CSF YAML with 9 L9 domains')
    ap.add_argument('--output-dir',type=Path,default=Path('diagnostics/h20_vs_cuf'))
    ap.add_argument('--max-elements',type=int,default=300,help='0=ALL H20 elements (full volume)')
    ap.add_argument('--gauss',type=int,choices=(1,2,3),default=2,help='H20 interior points per axis')
    ap.add_argument('--sections',type=int,default=40,help='Axial bins in section summary')
    ap.add_argument('--seed',type=int,default=20261107)
    ap.add_argument('--h20-fd-step',type=float,default=1e-4,help='H20 stress derivative in parent coords')
    ap.add_argument('--cuf-fd-fraction',type=float,default=1e-3,help='CUF stress derivative step / FEM element size')
    ap.add_argument('--compiled-module',type=Path,help='Optional direct path to compiled_field.py')
    ap.add_argument('--no-plots',action='store_true')
    args=ap.parse_args()
    print('[comparison]', VERSION, flush=True)
    if args.max_elements<0 or args.sections<2 or args.h20_fd_step<=0 or args.cuf_fd_fraction<=0:
        ap.error('Invalid numeric options')
    for p in (args.fem,args.cuf,args.csf):
        if not p.is_file():ap.error(f'Input file not found: {p}')

    h20_shape,residual_at,Field = load_helpers(Path(__file__).resolve().parent,args.compiled_module)
    material=PhysicalMaterial(args.csf)
    field=Field.load(args.cuf)
    if abs(field.x_start-material.x0)>1e-7 or abs(field.x_end-material.x1)>1e-7:
        raise ValueError('CUF and CSF longitudinal domains differ')
    material.verify_geometry(field)
    with np.load(args.cuf,allow_pickle=False) as d:
        boundaries=np.unique(np.concatenate((d['element_x_starts'],d['element_x_ends'])))
    with np.load(args.fem,allow_pickle=False) as d:
        nodes=np.asarray(d['nodes'],float); conn=np.asarray(d['elements'],int)
        U=np.asarray(d['displacement'],float)
        E=np.asarray(d['element_E'],float);nu=np.asarray(d['element_nu'],float)
        regions=np.asarray(d['element_region'],int)
        xmid=np.asarray(d['element_xmid'],float)
    if conn.ndim!=2 or conn.shape[1]!=20:raise ValueError('FEM NPZ must contain 20-node elements')
    if U.shape != nodes.shape:raise ValueError('Missing/invalid solved FEM nodal displacement')
    if conn.min()<0 or conn.max()>=len(nodes):raise ValueError('FEM element connectivity out of range')
    if not np.all(np.isfinite(U)):raise ValueError('Non-finite FEM displacement')
    if not (np.isclose(nodes[:,0].min(),material.x0) and np.isclose(nodes[:,0].max(),material.x1)):
        raise ValueError('FEM and CUF physical longitudinal extents differ')
    if not np.allclose(nu,material.nu,rtol=0,atol=1e-12):
        raise ValueError('FEM Poisson ratio differs from CUF YAML')

    chosen=sample_elements(regions,xmid,args.max_elements,args.seed)
    pts,ws=np.polynomial.legendre.leggauss(args.gauss)
    out=[]; skipped={}
    print(f'Comparing {len(chosen)}/{len(conn)} H20 elements, {args.gauss}^3 points each',flush=True)
    for count,ei in enumerate(chosen,1):
        X=nodes[conn[ei]];ue=U[conn[ei]]
        extents=np.ptp(X,axis=0)
        h_ref=np.maximum(extents*args.cuf_fd_fraction,2e-5)
        for ir,r in enumerate(pts):
            for js,s in enumerate(pts):
                for kt,t in enumerate(pts):
                    q=np.array((r,s,t))
                    xyz,uf,rf,det,dsf=fem_at(X,ue,float(E[ei]),float(nu[ei]),q,
                                            h20_shape,residual_at,args.h20_fd_step)
                    domain, dist=find_domain(field,material,xyz)
                    if domain is None:
                        skipped['interface_or_outside']=skipped.get('interface_or_outside',0)+1
                        continue
                    E_expected=material.E(float(xmid[ei]),domain)
                    if not np.isclose(float(E[ei]),E_expected,atol=1e-7,rtol=1e-11):
                        raise ValueError(
                            f'FEM/CSF material mismatch element={ei+1}, domain={domain+1}: '
                            f'E_FEM={E[ei]}, E_CSF_at_element_mid={E_expected}'
                        )
                    try:
                        dsc=stress_gradient_cuf(field,material,xyz,domain,dist,h_ref,boundaries)
                        # Displacement is evaluated on the selected CUF side.
                        # The interior value is unique for this conforming model.
                        uc=field(float(xyz[0]),float(xyz[1]),float(xyz[2]))
                    except (ValueError,RuntimeError) as exc:
                        k='derivative_outside_domain'
                        skipped[k]=skipped.get(k,0)+1
                        continue
                    tf=div_terms(dsf);tc=div_terms(dsc)
                    if not np.allclose(rf,[tf['div_x'],tf['div_y'],tf['div_z']],rtol=1e-7,atol=1e-7):
                        raise RuntimeError(f'H20 residual and derivative decomposition disagree at element {ei}')
                    weight=float(det*ws[ir]*ws[js]*ws[kt])
                    row={'element_id':int(ei+1),'region':int(regions[ei]),'domain_id':int(domain+1),
                         'x':float(xyz[0]),'x_over_L':float((xyz[0]-material.x0)/(material.x1-material.x0)),
                         'y':float(xyz[1]),'z':float(xyz[2]),'weight_mm3':weight}
                    for k in ALL_KEYS:
                        row[f'fem_{k}']=float(tf[k]);row[f'cuf_{k}']=float(tc[k])
                    for i,c in enumerate('xyz'):
                        row[f'fem_u{c}']=float(uf[i]);row[f'cuf_u{c}']=float(uc[i]);row[f'delta_u{c}']=float(uc[i]-uf[i])
                    out.append(row)
        if count%max(1,len(chosen)//10)==0:
            print(f' {count}/{len(chosen)} elements, {len(out)} accepted points',flush=True)
    if len(out)<10:
        raise RuntimeError(f'Too few common interior samples ({len(out)}); rejected: {skipped}')
    if args.max_elements==0 and skipped:
        print('NOTE: excluded ambiguous interface points:',skipped,flush=True)

    args.output_dir.mkdir(parents=True,exist_ok=True)
    point_path=args.output_dir/'h20_cuf_common_points.csv'
    write_csv(point_path,out,out[0].keys())

    summary={'input':{'fem':str(args.fem),'cuf':str(args.cuf),'csf':str(args.csf),
                      'sha256_fem':sha256(args.fem),'sha256_cuf':sha256(args.cuf),'sha256_csf':sha256(args.csf)},
             'sampling':{'fem_elements_total':len(conn),'selected':len(chosen),
                         'common_points':len(out),'rejected':skipped,'gauss':args.gauss,
                         'max_elements':args.max_elements,'seed':args.seed,
                         'metric':'Jacobian-weighted, element-interior strong-form stress divergence',
                         'residual_units':'MPa/mm','displacement_units':'mm',
                         'warning':'H20 E is constant per element; CUF material varies continuously with x.'},
             'equilibrium':{},'displacement':{}}
    for k in ALL_KEYS:
        summary['equilibrium'][k]={m:metrics(out,m,k) for m in ('fem','cuf')}
        summary['equilibrium'][k]['rms_ratio_cuf_over_fem']=(
            summary['equilibrium'][k]['cuf']['rms']/max(summary['equilibrium'][k]['fem']['rms'],1e-40))
    weights=np.array([p['weight_mm3'] for p in out])
    for c in 'xyz':
        du=np.array([p[f'delta_u{c}'] for p in out])
        summary['displacement'][c]={'difference_rms':float(np.sqrt(np.average(du*du,weights=weights))),
                                     'difference_max_abs':float(np.max(abs(du))),
                                     'fem_sample_min':float(min(p[f'fem_u{c}'] for p in out)),
                                     'cuf_sample_min':float(min(p[f'cuf_u{c}'] for p in out))}
    # Assign each physical point to exactly ONE longitudinal bin.
    # A former release erroneously included all points in the final bin.
    bins = [[] for _ in range(args.sections)]
    for point in out:
        xi = float(point['x_over_L'])
        if not np.isfinite(xi) or xi < -1e-12 or xi > 1.0 + 1e-12:
            raise ValueError(f'Sample outside normalized beam extent: x/L={xi}')
        index = min(max(int(math.floor(xi * args.sections)), 0), args.sections-1)
        bins[index].append(point)
    if sum(len(group) for group in bins) != len(out):
        raise RuntimeError('Section partition inconsistent: duplicated or missing physical points')
    sections=[]
    for idx, subset in enumerate(bins):
        if not subset:
            continue
        l=idx/args.sections;r=(idx+1)/args.sections
        rec={'section':idx+1,'x_over_L_mid':.5*(l+r),'points':len(subset)}
        for k in KEYS:
            for model in ('fem','cuf'):
                m=metrics(subset,model,k)
                rec[f'{model}_{k}_median_abs']=m['median_abs']
                rec[f'{model}_{k}_rms']=m['rms']
        sections.append(rec)
    if sum(rec['points'] for rec in sections) != len(out):
        raise RuntimeError('Invalid section statistics: sample totals do not match')
    print(f'[comparison] Section check PASS: {sum(rec["points"] for rec in sections)} assigned points, {len(sections)} populated sections',flush=True)
    section_path=args.output_dir/'h20_cuf_sections.csv'
    write_csv(section_path,sections,sections[0].keys() if sections else ('section',))
    (args.output_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')

    lines=['# Same-point FEM3D H20 vs CSF-CUF','',
      f"FEM H20 elements used: **{len(chosen)}/{len(conn)}**; common physical points: **{len(out)}**; Gauss per axis: **{args.gauss}**.",
      '',
      'Both models evaluated at the exact same physical positions in the FEM x,y,z coordinate system.',
      'Values below are Jacobian-weighted over the accepted **element/domain interiors**.',
      '',
      '| Quantity | FEM3D H20 RMS | CSF-CUF RMS | CUF/FEM |',
      '|---|---:|---:|---:|']
    for k in KEYS:
        row=summary['equilibrium'][k]
        lines.append(f"| {k} (MPa/mm) | {row['fem']['rms']:.8g} | {row['cuf']['rms']:.8g} | {row['rms_ratio_cuf_over_fem']:.6g} |")
    lines.extend(['','| Component | Common-point displacement difference RMS (mm) |',
        '|---|---:|'])
    for c in 'xyz':lines.append(f"| {c} | {summary['displacement'][c]['difference_rms']:.8g} |")
    lines.extend(['',f"Common-sample min uz: FEM3D = {summary['displacement']['z']['fem_sample_min']:.9g} mm; CUF = {summary['displacement']['z']['cuf_sample_min']:.9g} mm.",
      'These are minima ON THE COMMON SAMPLED POINTS, not global displacement extrema.'])
    lines.extend(['','## Interpretation','',
      'CUF/FEM < 1 means CUF has a smaller interior strong-equilibrium RMS for that component.',
      'These metrics do NOT establish a global equilibrium ranking: traction jumps and external-surface tractions are not included.',
      'FEM3D H20 freezes E within each element, while CSF-CUF evaluates the continuous x-dependent material.',
      'The reported RMS values are evaluated at common physical quadrature points using consistent integration weights.',
      '',f'Rejected sample points: `{skipped}`.',
      '',f'FEM SHA256: `{summary["input"]["sha256_fem"]}`',
      f'CUF SHA256: `{summary["input"]["sha256_cuf"]}`',
      f'CSF SHA256: `{summary["input"]["sha256_csf"]}`'])
    (args.output_dir/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if not args.no_plots and sections:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            for k in KEYS:
                X=[row['x_over_L_mid'] for row in sections]
                plt.figure(figsize=(8,4))
                for m,label in (('fem','FEM3D H20'),('cuf','CSF-CUF L9')):
                    Y=[row[f'{m}_{k}_rms'] for row in sections]
                    plt.plot(X,Y,label=label,marker='.',linewidth=1)
                plt.xlabel('x/L');plt.ylabel(f'RMS |{k}| (MPa/mm)')
                plt.title(f'Common-point equilibrium component: {k}')
                plt.grid(alpha=.3);plt.legend();plt.tight_layout()
                plt.savefig(args.output_dir/f'{k}_vs_x.png',dpi=160)
                plt.close()
        except ImportError:
            print('Matplotlib not installed: plots omitted',flush=True)
    print('\n'.join(lines[:16]));print('Saved:',point_path,section_path,args.output_dir/'summary.md',flush=True)

if __name__=='__main__':main()
