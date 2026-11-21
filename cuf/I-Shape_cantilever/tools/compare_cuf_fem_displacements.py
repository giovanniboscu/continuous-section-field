# Version: CSF-CUF independent CUF-FEM3D displacement comparison v03 - 2026-11-20
"""Compare the physical displacement U(x,y,z) of CUF and OpenSees H8.

No loads, stress recovery, material laws or solver changes are involved.
No longitudinal-bin means of the raw displacement components are computed.
Longitudinal profiles follow actual OpenSees mesh-node chains. At every FEM
node on such a chain, CUF is evaluated with CompiledDisplacementField at the
same physical (x,y,z). No synthetic CSF material trajectories are introduced.
The existing CSF/CUF APIs resolve and evaluate the physical model:
    load_case, load_problem, CSFCUFModelBridge, CompiledDisplacementField.
This script never reads model/problem YAML itself and never interpolates CSF
physical geometry or material laws. H8 interpolation belongs only to FEM3D.

CUF and OpenSees axes are (x,y,z)=(Z,X,Y)_CSF, with (ux,uy,uz) in that
same order. No automatic unit, axis, sign or displacement scaling is allowed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from csf.cuf.case import load_case
from csf.cuf.problem.problem_api import load_problem
from csf.cuf.csf_bridge import CSFCUFModelBridge
from csf.cuf.solver.compiled_field import CompiledDisplacementField


H8_SIGNS = np.asarray((
    (-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),
    (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1),
), dtype=float)
COMPONENTS = ("ux", "uy", "uz")


@dataclass(frozen=True)
class FEM:
    nodes: np.ndarray
    elements: np.ndarray
    displacement: np.ndarray
    element_region: np.ndarray | None
    region_names: tuple[str, ...] | None
    x0: float | None
    x1: float | None
    source: str
    status: str
    case_name: str | None
    model_path: str | None
    units: str | None


def _scalar(data, key):
    a = np.asarray(data[key])
    if a.size != 1:
        raise ValueError(f"NPZ {key} must contain a single scalar")
    return a.item()


def load_fem(path: Path) -> FEM:
    """Only validated OpenSees H8/stdBrick layouts; never assume mesh-only solved."""
    with np.load(path, allow_pickle=False) as f:
        keys = set(f.files)
        standard = {"format", "coordinate_system", "element_type", "version",
                    "connectivity_index_base", "coordinates", "displacements", "connectivity"}
        raw = {"nodes", "elements", "displacement"}
        if standard.issubset(keys):
            for key, expected in (("format", "fem3d_h8_displacement"),
                                  ("coordinate_system", "CUF"),
                                  ("element_type", "stdBrick")):
                if str(_scalar(f,key)) != expected:
                    raise ValueError(f"FEM NPZ requires {key}={expected!r}")
            if int(_scalar(f,"version")) != 1:
                raise ValueError("unsupported standard FEM displacement NPZ version")
            base = int(_scalar(f,"connectivity_index_base"))
            if base not in (0,1):
                raise ValueError("FEM connectivity_index_base must be 0 or 1")
            nodes = np.asarray(f["coordinates"], float)
            elements = np.asarray(f["connectivity"])
            u = np.asarray(f["displacements"], float)
            source = "fem3d_h8_displacement_v1"
        elif raw.issubset(keys):
            # The driver run_opensees_csf.py saves zero-based nodes/elements,
            # with all coordinates and components in CUF/OpenSees (x,y,z) axes.
            if "coordinate_system" in keys and str(_scalar(f,"coordinate_system")) != "CUF":
                raise ValueError("raw FEM NPZ has a non-CUF coordinate system")
            nodes = np.asarray(f["nodes"], float)
            elements = np.asarray(f["elements"])
            u = np.asarray(f["displacement"], float)
            base = 0
            source = "run_opensees_csf_H8_raw"
        else:
            raise ValueError("Unsupported FEM3D NPZ: expected standard v1 H8 or "
                             "raw nodes/elements/displacement. Found: " + ", ".join(sorted(keys)))
        status = str(_scalar(f,"status")) if "status" in keys else "unrecorded"
        if status == "mesh_only":
            raise ValueError("FEM NPZ is mesh_only, not a solved OpenSees displacement field")
        if status not in ("solved_opensees", "unrecorded"):
            raise ValueError(f"FEM NPZ does not declare a recognized solved status: {status!r}")
        if not np.issubdtype(elements.dtype, np.integer):
            raise ValueError("FEM connectivity must contain integer indices")
        elements = elements.astype(np.int64) - base
        region = np.asarray(f["element_region"]) if "element_region" in keys else None
        region_names = tuple(map(str,f["element_region_names"])) if "element_region_names" in keys else None
        x0 = float(_scalar(f,"x0")) if "x0" in keys else None
        x1 = float(_scalar(f,"x1")) if "x1" in keys else None
        case_name = str(_scalar(f,"case_name")) if "case_name" in keys else None
        model_path = str(_scalar(f,"model_path")) if "model_path" in keys else None
        units = str(_scalar(f,"units")) if "units" in keys else None
    if nodes.ndim != 2 or nodes.shape[1] != 3 or not len(nodes):
        raise ValueError("FEM nodes must have shape (nnode,3)")
    if u.shape != nodes.shape:
        raise ValueError("FEM displacements must have shape (nnode,3); mesh-only is not valid")
    if elements.ndim != 2 or elements.shape[1] != 8 or not len(elements):
        raise ValueError("FEM must contain H8/stdBrick elements (nel,8)")
    if elements.min() < 0 or elements.max() >= len(nodes):
        raise ValueError("FEM element connectivity points outside the node array")
    if np.any(np.sort(elements,axis=1)[:,1:] == np.sort(elements,axis=1)[:,:-1]):
        raise ValueError("FEM element contains a repeated node")
    if not np.isfinite(nodes).all() or not np.isfinite(u).all():
        raise ValueError("FEM coordinates/displacements contain nonfinite values")
    if region is not None:
        if (region.shape != (len(elements),) or not np.issubdtype(region.dtype,np.integer)
                or region.min() < 0):
            raise ValueError("element_region must be nonnegative integer indices, one per H8")
        region = region.astype(np.int64)
        if region_names is not None and region.max() >= len(region_names):
            raise ValueError("element_region indices exceed element_region_names")
    if source == "run_opensees_csf_H8_raw" and status == "unrecorded":
        warnings.warn("Raw FEM file has no solver status; accepted as a legacy solved checkpoint "
                      "because all nodal displacements are present", RuntimeWarning)
    return FEM(nodes,elements,u,region,region_names,x0,x1,source,status,
               case_name,model_path,units)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1<<20), b""):
            h.update(block)
    return h.hexdigest()


def h8_shape(q):
    """OpenSees stdBrick H8 trilinear interpolation; natural axes r,s,t."""
    return np.prod((1 + H8_SIGNS*np.asarray(q,dtype=float)), axis=1)/8.0


def h8_gradient_natural(q):
    """dN_i / d(r,s,t) in the exact stdBrick node ordering."""
    q = np.asarray(q,dtype=float)
    d = np.empty((8,3),dtype=float)
    for axis in range(3):
        others = [j for j in range(3) if j != axis]
        d[:,axis] = (H8_SIGNS[:,axis]/8.0
                     *(1+H8_SIGNS[:,others[0]]*q[others[0]])
                     *(1+H8_SIGNS[:,others[1]]*q[others[1]]))
    return d


def verify_h8_jacobians(fem: FEM, *, chunk=5000):
    """Check all 8 Gauss determinants with the FEM map, not a CSF mapping."""
    g = 1/math.sqrt(3)
    samples = ((a,b,c) for a in (-g,g) for b in (-g,g) for c in (-g,g))
    for q in samples:
        d = h8_gradient_natural(q)
        for j in range(0,len(fem.elements),chunk):
            part = fem.nodes[fem.elements[j:j+chunk]]
            jac = np.einsum("eni,nj->eij",part,d,optimize=True)
            determinants = np.linalg.det(jac)
            bad = np.flatnonzero(~np.isfinite(determinants) | (determinants <= 0))
            if len(bad):
                e = j+int(bad[0])
                raise ValueError(f"invalid/inverted H8 element {e+1} at {q}; "
                                 f"det J={determinants[bad[0]]:g}")


def _match_vertices(a,b,tol):
    """Check equal physical vertex sets; does not generate or interpolate them."""
    a,b = np.asarray(a,float),np.asarray(b,float)
    if a.shape != b.shape:
        return False
    available = list(range(len(b)))
    for p in a:
        candidates = [j for j in available if np.linalg.norm(p-b[j],ord=np.inf)<=tol]
        if not candidates:
            return False
        available.remove(candidates[0])
    return True


def verify_csf_cuf_domain_geometry(field,provider,x_values):
    """Compare stored CUF support with CSF-evaluated sections, not CSF physics."""
    if not callable(getattr(field,"domain_vertices_at",None)):
        return "unavailable_legacy_field"
    checked = 0
    for x in sorted(set(float(t) for t in x_values)):
        saved = field.domain_vertices_at(x)
        if saved is None:
            return "unavailable_legacy_field"
        domains = provider.domains(x)
        if len(domains) != len(saved):
            raise ValueError(f"CUF saved domains and CSF section differ at x={x:g}: "
                             f"{len(saved)} vs {len(domains)}")
        unmatched = set(range(len(saved)))
        for csf in domains:
            physical = np.asarray(csf.vertices,float)
            scale = max(1.0,float(np.max(np.abs(physical))))
            tol = 1e-8*scale
            matches = [k for k in unmatched if _match_vertices(physical,saved[k],tol)]
            if len(matches) != 1:
                raise ValueError(f"CUF checkpoint physical domains do not match "
                                 f"CSF domain {csf.domain_id} at x={x:g}; matches={matches}")
            unmatched.remove(matches[0])
        checked += 1
    return f"matched_{checked}_longitudinal_stations"


def _region_labels(provider,fem):
    x0,_ = provider.longitudinal_domain()
    base = tuple(str(d.get("s0_name",f"domain_{i+1}"))
                 for i,d in enumerate(provider.inspect_section_entities(float(x0))))
    if fem.element_region is not None:
        if np.max(fem.element_region) >= len(base):
            raise ValueError("FEM element_region indices exceed CSF domain count")
        if fem.region_names is not None and tuple(fem.region_names) != base:
            raise ValueError("FEM region names do not match CSF S0 domain ordering")
    return base


def fem_sample_points(fem: FEM, kind: str):
    """Produce paired coordinates and FEM displacement at exactly those points."""
    if kind == "nodes":
        n = len(fem.nodes)
        # Each node belongs to one or several FEM/CSF regions. Multi-owner nodes
        # are interfaces and are deliberately labelled, not falsely assigned.
        owner = [set() for _ in range(n)] if fem.element_region is not None else None
        if owner is not None:
            for eid,conn in enumerate(fem.elements):
                reg = int(fem.element_region[eid])
                for node in conn:
                    owner[int(node)].add(reg)
            regions = np.asarray([next(iter(v)) if len(v)==1 else -1 for v in owner],int)
            counts = np.asarray([len(v) for v in owner],int)
        else:
            regions = np.full(n,-1,int)
            counts = np.zeros(n,int)
        return dict(xyz=fem.nodes.copy(), u=fem.displacement.copy(),
                    element_id=np.full(n,-1,int), node_id=np.arange(n,dtype=int),
                    region=regions, owner_count=counts,
                    volume_weight=np.full(n,np.nan),
                    local_q=np.full((n,3),np.nan))
    if kind not in ("centers", "gauss2"):
        raise ValueError(f"unsupported sampling={kind!r}")
    samples = [(0.,0.,0.)] if kind=="centers" else [
        (a,b,c) for a in (-1/math.sqrt(3),1/math.sqrt(3))
        for b in (-1/math.sqrt(3),1/math.sqrt(3))
        for c in (-1/math.sqrt(3),1/math.sqrt(3))]
    data = defaultdict(list)
    for q in samples:
        N = h8_shape(q)
        xyz = np.einsum("i,eij->ej",N,fem.nodes[fem.elements],optimize=True)
        u = np.einsum("i,eij->ej",N,fem.displacement[fem.elements],optimize=True)
        data["xyz"].append(xyz)
        data["u"].append(u)
        data["element_id"].append(np.arange(len(fem.elements),dtype=int))
        data["node_id"].append(np.full(len(fem.elements),-1,int))
        data["region"].append(fem.element_region.copy() if fem.element_region is not None
                              else np.full(len(fem.elements),-1,int))
        data["owner_count"].append(np.ones(len(fem.elements),int))
        data["local_q"].append(np.repeat(np.asarray([q],float),len(fem.elements),axis=0))
        d = h8_gradient_natural(q)
        jac = np.einsum("eni,nj->eij",fem.nodes[fem.elements],d,optimize=True)
        volume_weight = np.linalg.det(jac)
        if not np.all(volume_weight > 0):
            raise ValueError("FEM H8 has nonpositive Jacobian at sampling point")
        # Center: one-point volume quadrature with weight 2*2*2 = 8.
        # Gauss2: each of the 8 integration points has Gauss weight 1.
        data["volume_weight"].append(volume_weight*(8.0 if kind=="centers" else 1.0))
    return {key:np.concatenate(part,axis=0) for key,part in data.items()}


def validate_csf_interior_points(provider, xyz, region, *, mode="representatives"):
    """Use CSF's existing domain_at_point API; never implement polygon tests here.

    Representatives checks one sample per (longitudinal x, FEM domain).  All
    checks every interior sample (more expensive for a large CSF field).
    Interface nodes are intentionally not tested with this *unique-domain* API.
    """
    if mode == "off":
        return 0
    if np.all(region < 0):
        return 0
    indices = np.flatnonzero(region >= 0)
    if mode == "representatives":
        selected = []
        seen = set()
        for idx in indices:
            key=(float(xyz[idx,0]),int(region[idx]))
            if key not in seen:
                seen.add(key)
                selected.append(idx)
        indices = selected
    count = 0
    for idx in indices:
        x,y,z = map(float,xyz[idx])
        expected=int(region[idx])+1
        try:
            actual=provider.domain_at_point(x,y,z)
        except ValueError as exc:
            raise ValueError(f"sample #{idx} of FEM domain {expected} at ({x:g},{y:g},{z:g}) "
                             f"is not strictly assignable to one CSF domain: {exc}") from exc
        if actual.domain_id != expected:
            raise ValueError(f"FEM region {expected} disagrees with CSF domain "
                             f"{actual.domain_id} at ({x:g},{y:g},{z:g})")
        count+=1
    return count


def eval_cuf(field, xyz):
    """Evaluate only the public compiled CUF callable at unchanged coordinates."""
    result = np.empty((len(xyz),3),float)
    cache_x, eval_x = None, None
    # Sort by x so a section evaluator is reused whenever the API supports it.
    for i in np.argsort(xyz[:,0], kind="stable"):
        x,y,z = map(float,xyz[i])
        if cache_x != x:
            eval_x = field.section_evaluator(x)
            cache_x = x
        try:
            value = np.asarray(eval_x(y,z),dtype=float)
        except Exception as exc:
            raise ValueError(f"CUF evaluation failed at sample #{i}, "
                             f"(x,y,z)=({x:.16g},{y:.16g},{z:.16g}): {exc}") from exc
        if value.shape != (3,) or not np.isfinite(value).all():
            raise ValueError(f"invalid CUF displacement at sample #{i}")
        result[i] = value
    return result


def _safe_ratio(a,b):
    return None if b == 0 else float(a/b)


def statistics(values_cuf, values_fem, coords):
    """Pointwise statistics; no per-point percentage near zero displacement."""
    if not len(coords):
        return None
    error = values_cuf-values_fem
    en = np.linalg.norm(error,axis=1)
    rn = np.linalg.norm(values_fem,axis=1)
    result={"samples":int(len(coords)),"components":{}}
    for c,label in enumerate(COMPONENTS):
        d=error[:,c]; reference=values_fem[:,c]
        ix=int(np.argmax(np.abs(d)))
        result["components"][label]={
            "bias":float(np.mean(d)),
            "mae":float(np.mean(np.abs(d))),
            "rmse":float(np.sqrt(np.mean(d*d))),
            "median_abs":float(np.median(np.abs(d))),
            "p95_abs":float(np.percentile(np.abs(d),95)),
            "p99_abs":float(np.percentile(np.abs(d),99)),
            "max_abs":float(np.abs(d[ix])),
            "relative_l2_percent":_safe_ratio(100*np.linalg.norm(d),np.linalg.norm(reference)),
            "relative_linf_percent":_safe_ratio(100*np.max(np.abs(d)),np.max(np.abs(reference))),
            "fem_rms":float(np.sqrt(np.mean(reference**2))),
            "fem_max_abs":float(np.max(np.abs(reference))),
            "max_error_at":{"x":float(coords[ix,0]),"y":float(coords[ix,1]),
                            "z":float(coords[ix,2]),"fem":float(reference[ix]),
                            "cuf":float(values_cuf[ix,c]),"signed_delta":float(d[ix])},
        }
    ix=int(np.argmax(en))
    result["vector"]={
        "rmse_norm":float(np.sqrt(np.mean(en*en))),
        "mae_norm":float(np.mean(en)),
        "median_norm":float(np.median(en)),
        "p95_norm":float(np.percentile(en,95)),
        "p99_norm":float(np.percentile(en,99)),
        "max_norm":float(en[ix]),
        "relative_l2_percent":_safe_ratio(100*np.linalg.norm(error),np.linalg.norm(values_fem)),
        "fem_rms_norm":float(np.sqrt(np.mean(rn*rn))),
        "max_error_at":{"x":float(coords[ix,0]),"y":float(coords[ix,1]),
                        "z":float(coords[ix,2]),
                        "fem":values_fem[ix].tolist(),"cuf":values_cuf[ix].tolist(),
                        "delta":error[ix].tolist()},
    }
    return result


def weighted_statistics(ucuf,ufem,w):
    """Physical quadrature norms, not nodal or equal-point statistics.

    Centers: w = 8 detJ_H8(0,0,0), i.e. one-point midpoint quadrature.
    Gauss2: w = detJ_H8(q) at each of 8 2x2x2 Gauss points.
    No weights are assigned to nodes, since nodal counting is not a volume rule.
    """
    w=np.asarray(w,float)
    if (w.shape != (len(ucuf),) or not np.isfinite(w).all()
            or np.any(w<=0)):
        raise ValueError("Invalid physical FEM quadrature volume weights")
    vol=float(w.sum())
    err=ucuf-ufem
    squared=np.sum(err**2,axis=1)
    ref_squared=np.sum(ufem**2,axis=1)
    result={"approximate_volume_native_cubed":vol,
            "weight_definition":"center: 8*detJ(0,0,0); gauss2: detJ(q) at 2x2x2 Gauss points",
            "vector_weighted_rmse_norm":float(np.sqrt(np.dot(w,squared)/vol)),
            "vector_weighted_relative_l2_percent":_safe_ratio(
                100*np.sqrt(np.dot(w,squared)),np.sqrt(np.dot(w,ref_squared))),
            "components":{}}
    for k,c in enumerate(COMPONENTS):
        delta2=err[:,k]**2
        ref2=ufem[:,k]**2
        result["components"][c]={
            "weighted_rmse":float(np.sqrt(np.dot(w,delta2)/vol)),
            "weighted_relative_l2_percent":_safe_ratio(
                100*np.sqrt(np.dot(w,delta2)),np.sqrt(np.dot(w,ref2)))}
    return result


def write_samples(outdir,kind,data,ucuf,ufem,labels,x0,x1):
    """Export every actual paired sample to CSV and compact NPZ."""
    xyz=data["xyz"]; er=ucuf-ufem
    r=data["region"]
    names=[labels[int(k)] if 0<=k<len(labels) else
           "interface_or_unlabelled" for k in r]
    path=outdir/f"comparison_{kind}.csv"
    cols=["sample_index","element_id_0based","node_id_0based","fem_region_id_1based",
          "domain_name","node_region_owners","x","y","z","x_over_L","volume_weight",
          "fem_ux","fem_uy","fem_uz","cuf_ux","cuf_uy","cuf_uz",
          "delta_ux","delta_uy","delta_uz","abs_delta_ux","abs_delta_uy",
          "abs_delta_uz","delta_norm","fem_u_norm","h8_r","h8_s","h8_t"]
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.writer(handle); writer.writerow(cols)
        for i,((x,y,z),f,c,e) in enumerate(zip(xyz,ufem,ucuf,er)):
            writer.writerow((i,int(data["element_id"][i]),int(data["node_id"][i]),
                             int(r[i])+1 if r[i]>=0 else "",names[i],int(data["owner_count"][i]),
                             x,y,z,(x-x0)/(x1-x0),
                             (float(data["volume_weight"][i]) if np.isfinite(data["volume_weight"][i]) else ""),
                             *f,*c,*e,*np.abs(e),
                             float(np.linalg.norm(e)),float(np.linalg.norm(f)),*data["local_q"][i]))
    npz=outdir/f"comparison_{kind}.npz"
    np.savez_compressed(npz,coordinate_system=np.asarray("CUF"),
                        coordinate_mapping_csf=np.asarray(("Z","X","Y")),
                        x_y_z=xyz, u_fem=ufem,u_cuf=ucuf,delta_cuf_minus_fem=er,
                        error_norm=np.linalg.norm(er,axis=1),
                        physical_volume_quadrature_weight=data["volume_weight"],
                        element_id_0based=data["element_id"],
                        node_id_0based=data["node_id"],
                        fem_region_id_0based=r,
                        domain_name=np.asarray(names,dtype=str),
                        h8_natural_coordinates=data["local_q"])
    return path,npz


def write_grouped_tables(outdir,kind,data,ucuf,ufem,labels,x0,x1,bins):
    xyz=data["xyz"]
    if bins<=0:
        raise ValueError("--bins must be >=1")
    position=np.clip((xyz[:,0]-x0)/(x1-x0),0,1)
    ibin=np.minimum(np.floor(position*bins).astype(int),bins-1)
    records=[]
    for i in range(bins):
        idx=np.flatnonzero(ibin==i)
        if not len(idx):
            continue
        s=statistics(ucuf[idx],ufem[idx],xyz[idx])
        records.append((i+1,(i+.5)/bins,len(idx),s))
    p=outdir/f"by_x_{kind}.csv"
    with p.open("w",newline="",encoding="utf-8") as handle:
        w=csv.writer(handle)
        w.writerow(("bin","x_over_L_center","samples","ux_rmse","uy_rmse","uz_rmse",
                    "u_rmse_norm","u_max_norm"))
        for i,scoord,n,s in records:
            w.writerow((i,scoord,n,*(s["components"][c]["rmse"] for c in COMPONENTS),
                       s["vector"]["rmse_norm"],s["vector"]["max_norm"]))
    r=data["region"]
    p2=outdir/f"by_domain_{kind}.csv"
    with p2.open("w",newline="",encoding="utf-8") as handle:
        w=csv.writer(handle)
        w.writerow(("fem_region_id_1based","domain_name","samples","ux_rmse","uy_rmse",
                    "uz_rmse","u_rmse_norm","u_max_norm","relative_l2_percent"))
        for region in np.unique(r):
            idx=np.flatnonzero(r==region)
            s=statistics(ucuf[idx],ufem[idx],xyz[idx])
            name=labels[int(region)] if 0<=region<len(labels) else "interface_or_unlabelled"
            w.writerow((int(region)+1 if region>=0 else "",name,len(idx),
                        *(s["components"][c]["rmse"] for c in COMPONENTS),
                        s["vector"]["rmse_norm"],s["vector"]["max_norm"],
                        s["vector"]["relative_l2_percent"]))
    return records


def plot_reports(outdir,kind,data,ucuf,ufem,records,dpi):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    xy=data["xyz"]
    sx=[t[1] for t in records]
    if not sx:
        return
    e_rms=[t[3]["vector"]["rmse_norm"] for t in records]
    e_max=[t[3]["vector"]["max_norm"] for t in records]
    fig,ax=plt.subplots(figsize=(9,4.4))
    ax.plot(sx,e_rms,label="RMS ||CUF - FEM||")
    ax.plot(sx,e_max,label="Max ||CUF - FEM||",alpha=.8)
    ax.set(xlabel="(x-x0)/L",ylabel="Displacement difference (native units)",
           title=f"Displacement discrepancy along the member: {kind}")
    ax.grid(alpha=.3);ax.legend();fig.tight_layout()
    fig.savefig(outdir/f"error_vs_x_{kind}.png",dpi=dpi);plt.close(fig)
    for comp,label in enumerate(COMPONENTS):
        # Parity plot is visual only; all points remain in CSV and statistics.
        step=max(1,math.ceil(len(xy)/15000))
        fx,cy=ufem[::step,comp],ucuf[::step,comp]
        mini=min(float(np.min(fx)),float(np.min(cy)))
        maxi=max(float(np.max(fx)),float(np.max(cy)))
        if mini==maxi:
            mini-=1.;maxi+=1.
        fig,ax=plt.subplots(figsize=(5.7,5.5))
        ax.scatter(fx,cy,s=2,alpha=.35,rasterized=True)
        ax.plot([mini,maxi],[mini,maxi],"k--",linewidth=1,label="CUF = FEM")
        ax.set(xlabel=f"FEM3D {label}",ylabel=f"CUF {label}",
               title=f"Pointwise displacement agreement: {kind}")
        ax.set_aspect("equal",adjustable="box")
        ax.grid(alpha=.25);ax.legend();fig.tight_layout()
        fig.savefig(outdir/f"parity_{label}_{kind}.png",dpi=dpi);plt.close(fig)



def _axial_node_successors(fem: FEM, x0: float, x1: float):
    """Identify existing longitudinal mesh-node chains from OpenSees H8 edges.

    The run_opensees_csf.py mesher extrudes CSF Q4 section grids along x.
    Its H8 local axial edges are (0,1), (3,2), (4,5), (7,6). Mapping these
    *existing* FEM nodes gives an unambiguous physical track through the mesh,
    even when transverse coordinates vary with x. No geometry is generated.
    """
    tol=1e-10*max(1.0,abs(x0),abs(x1),abs(x1-x0))
    forward={}
    backward={}
    for eid,conn in enumerate(fem.elements):
        xyz=fem.nodes[conn]
        lo=xyz[[0,3,4,7],0]
        hi=xyz[[1,2,5,6],0]
        if (np.ptp(lo)>tol or np.ptp(hi)>tol or
                float(np.min(hi)-np.max(lo))<=tol):
            raise ValueError(
                f"H8 element {eid} does not use the CSF OpenSees driver's "
                "longitudinal extrusion ordering; cannot form nodal profiles")
        for a,b in ((0,1),(3,2),(4,5),(7,6)):
            na,nb=int(conn[a]),int(conn[b])
            if na in forward and forward[na]!=nb:
                raise ValueError(f"non-unique axial successor of FEM node {na}")
            if nb in backward and backward[nb]!=na:
                raise ValueError(f"non-unique axial predecessor of FEM node {nb}")
            forward[na]=nb
            backward[nb]=na
    return forward


def _profile_origins(fem: FEM, x0: float, *, requested_ids, requested_yz):
    """Select physical x=x0 FEM nodes, never pseudo-points or section averages."""
    scale=max(1.0,float(np.max(np.abs(fem.nodes))))
    tol=1e-9*scale
    ends=np.flatnonzero(np.abs(fem.nodes[:,0]-x0)<=tol)
    if not len(ends):
        raise ValueError("FEM has no node on the CSF first section")
    ends=ends[np.lexsort((ends, fem.nodes[ends,2], fem.nodes[ends,1]))]
    selected=[]
    if requested_ids or requested_yz:
        for k, raw in enumerate(requested_ids, start=1):
            node=int(raw)
            if node<0 or node>=len(fem.nodes) or abs(fem.nodes[node,0]-x0)>tol:
                raise ValueError(f"--profile-node {node} is not a zero-based FEM node on x0={x0:g}")
            selected.append((f"user_node_{node}",node))
        for k, pair in enumerate(requested_yz,start=1):
            yz=np.asarray(pair,dtype=float)
            if yz.shape!=(2,) or not np.isfinite(yz).all():
                raise ValueError("--profile-start-yz needs two finite coordinates")
            distances=np.linalg.norm(fem.nodes[ends,1:]-yz[None,:],axis=1)
            matches=ends[distances<=tol]
            if len(matches)!=1:
                near=int(ends[np.argmin(distances)])
                p=fem.nodes[near]
                raise ValueError(
                    f"start (y,z)=({yz[0]:g},{yz[1]:g}) must coincide with exactly one "
                    f"FEM node on x0 (tol {tol:g}); nearest node {near} at "
                    f"(y,z)=({p[1]:.12g},{p[2]:.12g})")
            selected.append((f"user_yz_{k:02d}",int(matches[0])))
    else:
        # Three explicitly defined FEM mesh points on the initial CSF section:
        # extrema in z with transverse-y selection. The exact chosen node IDs
        # and physical coordinates are recorded in the outputs.
        y=fem.nodes[ends,1]
        z=fem.nodes[ends,2]
        upper=ends[np.abs(z-float(np.max(z)))<=tol]
        lower=ends[np.abs(z-float(np.min(z)))<=tol]
        y_center=float((np.min(y)+np.max(y))/2.0)
        selected=[
            ("max_z_min_y", int(upper[np.argmin(fem.nodes[upper,1])])),
            ("max_z_max_y", int(upper[np.argmax(fem.nodes[upper,1])])),
            ("min_z_near_mid_y", int(lower[np.argmin(np.abs(fem.nodes[lower,1]-y_center))])),
        ]
    unique=[]
    seen=set()
    for label,node in selected:
        if node not in seen:
            unique.append((label,node))
            seen.add(node)
    return ends, unique


def export_nodal_profiles(fem: FEM, field, x0: float, x1: float, outdir: Path,
                          *, requested_ids, requested_yz, cuf_nodes, no_plots, dpi):
    """Export U_FEM and U_CUF at identical physical nodal tracks along x.

    Transverse (y,z) may vary with x: these are longitudinal lines of the
    physical H8 mesh, not fixed-coordinate straight lines nor section means.
    """
    successors=_axial_node_successors(fem,x0,x1)
    starts, choices=_profile_origins(fem,x0,requested_ids=requested_ids,
                                     requested_yz=requested_yz)
    with (outdir/'profile_start_nodes.csv').open('w',newline='',encoding='utf-8') as fh:
        w=csv.writer(fh)
        w.writerow(('node_id_0based','x','y','z'))
        for i in starts:
            w.writerow((int(i),*map(float,fem.nodes[i])))
    profiles=[]
    x_tol=1e-9*max(1.0,abs(x0),abs(x1),abs(x1-x0))
    for seq,(label,start) in enumerate(choices,start=1):
        chain=[int(start)]
        seen=set(chain)
        while chain[-1] in successors:
            successor=successors[chain[-1]]
            if successor in seen:
                raise ValueError(f"axial FEM node chain contains a cycle from {start}")
            chain.append(successor)
            seen.add(successor)
        ids=np.asarray(chain,dtype=int)
        xyz=fem.nodes[ids]
        if abs(xyz[0,0]-x0)>x_tol or abs(xyz[-1,0]-x1)>x_tol:
            raise ValueError(f"FEM node chain from {start} does not span x0..x1")
        if np.any(np.diff(xyz[:,0])<=0):
            raise ValueError(f"FEM node chain from {start} is not strictly increasing in x")
        ufem=fem.displacement[ids]
        ucuf=eval_cuf(field,xyz) if cuf_nodes is None else cuf_nodes[ids]
        error=ucuf-ufem
        name=f'profile_{seq:02d}_{label}'
        csv_name=f'{name}.csv'
        with (outdir/csv_name).open('w',newline='',encoding='utf-8') as fh:
            w=csv.writer(fh)
            w.writerow(('node_id_0based','x','y','z','x_over_L',
                        'fem_ux','fem_uy','fem_uz','cuf_ux','cuf_uy','cuf_uz',
                        'delta_ux','delta_uy','delta_uz','delta_norm'))
            for i,node in enumerate(ids):
                w.writerow((int(node),*xyz[i],(xyz[i,0]-x0)/(x1-x0),
                            *ufem[i],*ucuf[i],*error[i],float(np.linalg.norm(error[i]))))
        figure=None
        if not no_plots:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            fig,axes=plt.subplots(4,1,sharex=True,figsize=(9.2,10.5))
            for c,component in enumerate(COMPONENTS):
                a=axes[c]
                a.plot(xyz[:,0],ufem[:,c],label='FEM3D: H8 nodes',
                       marker='o',markersize=2,linewidth=1.25)
                a.plot(xyz[:,0],ucuf[:,c],label='CUF: compiled field',
                       linestyle='--',linewidth=1.5)
                a.set_ylabel(f'{component} [native length]')
                a.grid(alpha=.3)
                if c==0:
                    a.legend()
            axes[3].plot(xyz[:,0],np.linalg.norm(error,axis=1),label='||CUF-FEM||')
            axes[3].set_ylabel('||delta|| [native length]')
            axes[3].set_xlabel('Longitudinal coordinate x [native length]')
            axes[3].grid(alpha=.3)
            fig.suptitle(f'{label}: start node {start}, '
                         f'(x0,y0,z0)=({xyz[0,0]:.6g}, {xyz[0,1]:.6g}, '
                         f'{xyz[0,2]:.6g})\n'
                         'Identical physical FEM-node coordinates for CUF and FEM')
            fig.tight_layout()
            figure=f'{name}.png'
            fig.savefig(outdir/figure,dpi=dpi)
            plt.close(fig)
        stats=statistics(ucuf,ufem,xyz)
        profiles.append(dict(label=label, start_node_0based=start,
                             start_xyz=xyz[0].tolist(),end_xyz=xyz[-1].tolist(),
                             sample_count=int(len(ids)),
                             location_definition='Existing longitudinal H8 mesh-node chain; y and z can vary with x',
                             csv=csv_name,figure=figure,
                             max_delta_norm=float(np.max(np.linalg.norm(error,axis=1))),
                             error_statistics=stats))
        print(f'[compare] longitudinal profile {label}: FEM node {start}, '
              f'{len(ids)} stations, max ||delta||={profiles[-1]["max_delta_norm"]:.8g}',
              flush=True)
    return dict(selection='explicit' if requested_ids or requested_yz else 'automatic',
                start_node_catalog='profile_start_nodes.csv',
                definitions='Exact physical FEM nodes at each x; CUF evaluated at the same xyz',
                profiles=profiles)


def _json_sanitize(obj):
    if isinstance(obj,dict):
        return {str(k):_json_sanitize(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)):
        return [_json_sanitize(v) for v in obj]
    if isinstance(obj,np.generic):
        return obj.item()
    return obj


def run(args):
    case=load_case(args.case)
    problem=load_problem(case.problem_path)
    bridge=CSFCUFModelBridge.from_yaml(problem.model_path)
    provider=bridge.section_provider
    field=CompiledDisplacementField.load(args.cuf)
    fem=load_fem(args.fem3d)
    # A parameterized CUF series has distinct case labels, even though the
    # underlying physical model is the same as the independently solved FEM.
    # An optional expected FEM label is supplied only by an orchestrator that
    # first checks physical input hashes against the GCI provenance manifest.
    expected_fem_case_name = getattr(args, 'fem_reference_case_name', None) or case.name
    if fem.case_name is not None and fem.case_name != expected_fem_case_name:
        raise ValueError(f"FEM checkpoint case_name={fem.case_name!r} differs from "
                         f"expected FEM reference case name={expected_fem_case_name!r}")
    if fem.model_path is not None:
        recorded_model = Path(fem.model_path)
        current_model = Path(problem.model_path)
        if recorded_model.is_file() and current_model.is_file() and not recorded_model.samefile(current_model):
            if sha256(recorded_model) != sha256(current_model):
                raise ValueError("FEM checkpoint references a different CSF model file "
                                 "with different content; use the matching case")
    x0,x1=map(float,bridge.longitudinal_domain())
    xtol=1e-9*max(1.0,abs(x0),abs(x1),abs(x1-x0))
    if not np.allclose((field.x_start,field.x_end),(x0,x1),rtol=0,atol=xtol):
        raise ValueError("CUF checkpoint longitudinal extent differs from CSF model")
    if fem.x0 is not None and fem.x1 is not None:
        if not np.allclose((fem.x0,fem.x1),(x0,x1),rtol=0,atol=xtol):
            raise ValueError("FEM NPZ longitudinal extent differs from CSF model")
    if np.any(fem.nodes[:,0]<x0-xtol) or np.any(fem.nodes[:,0]>x1+xtol):
        raise ValueError("FEM mesh contains nodes outside CSF longitudinal extent")
    labels=_region_labels(provider,fem)
    print(f"[compare] CUF/CSF longitudinal [{x0:g},{x1:g}], domains={len(labels)}",flush=True)
    print(f"[compare] FEM {len(fem.nodes)} nodes, {len(fem.elements)} H8 elements; "
          f"schema={fem.source} status={fem.status}",flush=True)
    verify_h8_jacobians(fem)
    # Match solved-field support to actual CSF physical geometry at all
    # distinct longitudinal mesh stations (+ midpoints and endpoints).
    geometric_x=np.r_[fem.nodes[:,0],np.mean(fem.nodes[fem.elements,0],axis=1),x0,x1]
    geometry_status=verify_csf_cuf_domain_geometry(field,provider,np.unique(geometric_x))
    print(f"[compare] CSF geometry vs CUF checkpoint: {geometry_status}",flush=True)
    modes=("centers","nodes") if args.sampling=="both" else (args.sampling,)
    outdir=Path(args.output_dir).resolve()
    outdir.mkdir(parents=True,exist_ok=True)
    report={
        "version":"CSF-CUF CUF-FEM3D displacement comparison v03 - 2026-11-20",
        "coordinate_system":"CUF/OpenSees (x,y,z) = CSF (Z,X,Y)",
        "displacement_order":["ux","uy","uz"],
        "comparison_definition":"delta = U_CUF(x,y,z) - U_FEM(x,y,z), identical coordinates",
        "relative_error_definition":"100*||CUF-FEM||_2/||FEM||_2; null for zero FEM norm",
        "sampling":{"modes":modes,"bins":args.bins,
                    "geometry_point_check":args.check_csf_points},
        "inputs":{
            "case":str(case.path),"model":str(problem.model_path),
            "cuf":str(Path(args.cuf).resolve()),"fem":str(Path(args.fem3d).resolve()),
            "sha256_cuf":sha256(Path(args.cuf)),"sha256_fem":sha256(Path(args.fem3d)),
            "fem_schema":fem.source,"fem_status":fem.status,
            "fem_recorded_case_name":fem.case_name,
            "comparison_case_name":case.name,
            "expected_fem_reference_case_name":expected_fem_case_name,
            "fem_recorded_model_path":fem.model_path,
            "fem_recorded_units":fem.units,
            "cuf_compiled_field_format":field.metadata.get("format_version","unrecorded")},
        "physical_domain":{"x0":x0,"x1":x1,"domain_count":len(labels),
                           "csf_domain_names":labels,
                           "cuf_geometry_validation":geometry_status},
        "outputs":{},"results":{},
        "limitations":["Displacements only: no stress, residual, or constitutive recovery",
                       "FEM H8 displacement is trilinearly interpolated at internal samples",
                       "CUF displacement is evaluated directly from its saved compiled field",
                       "FEM/CSF material approximations can differ at finite resolution",
                       "Relative errors use global norms, never pointwise division by near-zero values",
                       "Longitudinal bins summarize differences only; raw displacement bin means are not computed",
                       "Longitudinal displacement profiles follow actual H8 nodal chains rather than arbitrary section means",
                       "Nodal statistics are unweighted; center/Gauss samples include explicit H8 quadrature-volume-weighted statistics",
                       "A checkpoint cannot independently establish equality of the originally assembled CUF/FEM material laws"],
    }
    nodal_cuf=None
    for kind in modes:
        print(f"[compare] sampling {kind}",flush=True)
        data=fem_sample_points(fem,kind)
        xyz=data["xyz"]
        if np.any(xyz[:,0]<x0-xtol) or np.any(xyz[:,0]>x1+xtol):
            raise ValueError("H8 sampling generated points outside beam length")
        if kind!="nodes":
            nc=validate_csf_interior_points(provider,xyz,data["region"],
                                            mode=args.check_csf_points)
        else:
            # Nodes on the section/external boundaries can have several CSF
            # owners, so unique-domain containment is not a valid test there.
            nc=0
        print(f"[compare] {kind} points={len(xyz)}; CSF interior checks={nc}",flush=True)
        ucuf=eval_cuf(field,xyz)
        ufem=data["u"]
        if kind=="nodes":
            nodal_cuf=ucuf
        result=statistics(ucuf,ufem,xyz)
        if kind != "nodes":
            result["physical_quadrature"]=weighted_statistics(
                ucuf,ufem,data["volume_weight"])
        result["csf_unique_domain_checks"]=nc
        result["interface_or_unlabelled_nodes"]=int(np.count_nonzero(data["region"]<0))
        data.update(x0=x0,x1=x1,bins=args.bins)
        csv_path,npz_path=write_samples(outdir,kind,data,ucuf,ufem,labels,x0,x1)
        bins=write_grouped_tables(outdir,kind,data,ucuf,ufem,labels,x0,x1,args.bins)
        if kind=="nodes":
            tip=np.flatnonzero(np.abs(xyz[:,0]-x1)<=xtol)
            if len(tip):
                result["free_end_nodes"]={"count":int(len(tip)),
                    "statistics":statistics(ucuf[tip],ufem[tip],xyz[tip])}
            fixed=np.flatnonzero(np.abs(xyz[:,0]-x0)<=xtol)
            if len(fixed):
                result["start_end_nodes"]={"count":int(len(fixed)),
                    "max_norm_cuf":float(np.max(np.linalg.norm(ucuf[fixed],axis=1))),
                    "max_norm_fem":float(np.max(np.linalg.norm(ufem[fixed],axis=1)))}
        if not args.no_plots:
            plot_reports(outdir,kind,data,ucuf,ufem,bins,args.dpi)
        report["results"][kind]=result
        report["outputs"][kind]={"csv":csv_path.name,"npz":npz_path.name,
            "x_table":f"by_x_{kind}.csv","domain_table":f"by_domain_{kind}.csv"}
        print(f"[compare] {kind}: RMS ||delta||={result['vector']['rmse_norm']:.8g}, "
              f"max={result['vector']['max_norm']:.8g}, "
              f"relative L2={result['vector']['relative_l2_percent']}%",flush=True)
    if not args.no_profiles:
        report['longitudinal_profiles']=export_nodal_profiles(
            fem,field,x0,x1,outdir,
            requested_ids=args.profile_node,
            requested_yz=args.profile_start_yz,
            cuf_nodes=nodal_cuf,
            no_plots=args.no_plots,
            dpi=args.dpi)
    (outdir/"summary.json").write_text(json.dumps(_json_sanitize(report),indent=2,
                           allow_nan=False)+"\n",encoding="utf-8")
    lines=["# CUF - FEM3D physical displacement comparison","",
           "Same physical coordinates `(x,y,z)` and component order `(ux,uy,uz)` ",
           "in the CUF/OpenSees frame; CSF physical coordinates are `(X,Y,Z)=(y,z,x)`.",
           "","**Definition:** `delta = U_CUF - U_FEM`. All values retain native input units.",
           "","| Sampling | Points | RMS norm | Max norm | Relative L2 (%) |",
           "|---|---:|---:|---:|---:|"]
    for k,info in report["results"].items():
        v=info["vector"]; rp=v["relative_l2_percent"]
        lines.append(f"| {k} | {info['samples']} | {v['rmse_norm']:.8g} | "
                     f"{v['max_norm']:.8g} | {('undefined' if rp is None else f'{rp:.7g}')} |")
    lines+=["","**Per-component RMS and maximum**", "",
            "| Sampling | Component | RMS | Maximum | Relative L2 (%) |",
            "|---|---|---:|---:|---:|"]
    for k,info in report["results"].items():
        for comp,s in info["components"].items():
            rp=s["relative_l2_percent"]
            lines.append(f"| {k} | {comp} | {s['rmse']:.8g} | {s['max_abs']:.8g} | "
                         f"{('undefined' if rp is None else f'{rp:.7g}')} |")
    lines += ["","**Volume-weighted H8 quadrature statistics**", "",
              "These are distinct from equal-sample RMS; node samples have no physical volume quadrature weight.",
              "", "| Sampling | Approximate volume (native^3) | Weighted vector RMS | Weighted relative L2 (%) |",
              "|---|---:|---:|---:|"]
    for k,info in report["results"].items():
        if "physical_quadrature" not in info:
            continue
        w=info["physical_quadrature"]
        rp=w["vector_weighted_relative_l2_percent"]
        lines.append(f"| {k} | {w['approximate_volume_native_cubed']:.9g} | "
                     f"{w['vector_weighted_rmse_norm']:.8g} | "
                     f"{('undefined' if rp is None else f'{rp:.7g}')} |")
    if 'longitudinal_profiles' in report:
        lines += ["", "**Longitudinal physical FEM-node profiles**", "",
                  "Each profile follows connected longitudinal H8 mesh nodes; "
                  "the transverse coordinates may vary with x. CUF and FEM "
                  "are evaluated at exactly the same physical nodes.", "",
                  "| Profile | FEM start node (0-based) | (x0,y0,z0) | Stations | Max ||delta|| | CSV |",
                  "|---|---:|---|---:|---:|---|"]
        for p in report['longitudinal_profiles']['profiles']:
            xyz=p['start_xyz']
            lines.append(f"| {p['label']} | {p['start_node_0based']} | "
                         f"({xyz[0]:.8g},{xyz[1]:.8g},{xyz[2]:.8g}) | "
                         f"{p['sample_count']} | {p['max_delta_norm']:.8g} | "
                         f"{p['csv']} |")
    lines += ["","Individual errors, physical coordinates, domains, percentiles and extrema ",
              "are stored in the companion CSV/NPZ and `summary.json`.","",
              "No stress or residual assessment is performed. Material laws and geometry "
              "are not reconstructed by this comparator."]
    (outdir/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"[compare] done: {outdir}",flush=True)
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case",type=Path,required=True,
                    help="CSF-CUF case; only load_case/load_problem interpret YAML")
    ap.add_argument("--cuf",type=Path,required=True,help="solved *.cuf.npz")
    ap.add_argument("--fem3d",type=Path,required=True,help="solved OpenSees H8 NPZ")
    ap.add_argument("--fem-reference-case-name",default=None,
                    help="FEM case label from independently verified GCI record, "
                         "when the CUF study case uses a different label")
    ap.add_argument("--sampling",choices=("centers","nodes","both","gauss2"),default="both",
                    help="FEM internal centers, exact FEM nodes, both, or 2x2x2 Gauss points")
    ap.add_argument("--check-csf-points",choices=("off","representatives","all"),
                    default="representatives",
                    help="CSF domain_at_point validation for interior samples only")
    ap.add_argument("--bins",type=int,default=40,help="number of longitudinal bins for RMS/max comparison errors (not raw displacement means)")
    ap.add_argument("--output-dir",type=Path,default=Path("diagnostics/displacement_comparison"))
    ap.add_argument("--no-profiles",action="store_true",
                    help="omit longitudinal nodal-profile CSVs and figures")
    ap.add_argument("--profile-node",action="append",type=int,default=[],
                    help="select a zero-based FEM node on x0; repeatable; replaces automatic choices")
    ap.add_argument("--profile-start-yz",nargs=2,type=float,action="append",default=[],
                    metavar=("Y0","Z0"),help="start-section physical transverse "
                    "coordinates matching an FEM node; repeatable; replaces automatic choices")
    ap.add_argument("--no-plots",action="store_true")
    ap.add_argument("--dpi",type=int,default=170)
    args=ap.parse_args()
    if args.no_profiles and (args.profile_node or args.profile_start_yz):
        ap.error("--no-profiles conflicts with --profile-node/--profile-start-yz")
    if args.bins<1 or args.dpi<1:
        ap.error("--bins and --dpi must be positive")
    run(args)


if __name__=="__main__":
    main()
