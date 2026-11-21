#!/usr/bin/env python3
"""FEM3D N, Tz and My from NATIVE OpenSees stdBrick Gauss stresses.

The NPZ must contain gauss_stress (nel, 8, 6), as saved by the updated
run_opensees_csf_native_stresses_v02.py driver. No displacement-to-stress
reconstruction is used.

Physical sections, area quadrature and reference loading are supplied by public
CSF/CUF APIs. This postprocessor DOES NOT interpolate CSF geometry/materials
or calculate a sectional Jacobian. H8 element *location* uses the established
plot_strain_stress_boundary_v10.FEM3DH8.evaluate() API.

The native stress field is discontinuous between elements, and Gauss values do
not define a continuous stress distribution over each section. A transparent
P0 recovery is used: within one FEM element and one axial Gauss plane, each
stress component is the arithmetic mean of its FOUR transverse Gauss values.
This approximation is applied to CSF sectional quadrature points belonging to
that FEM element. This is NOT direct Gauss-point area quadrature or an exact
sectional traction integral. The 'center' option averages all EIGHT stresses
for a separate midpoint diagnostic.

Run from cuf/I-Shape_cantilever:
  python tools/plot_fem3d_N_T_M_native.py \\
    --case cases/convergence_h_v02/step_008.yaml \\
    --fem-npz fem3d/native_stress_reference/solution.npz
  python tools/plot_fem3d_N_T_M_native.py \\
    --case cases/convergence_h_v02/step_008.yaml \\
    --fem-npz fem3d/native_stress_reference/solution.npz \\
    --sampling center
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _project_imports(project: Path) -> None:
    for folder in (project / 'src', project.parent.parent / 'src'):
        if (folder / 'csf' / 'cuf').is_dir():
            sys.path.insert(0, str(folder))
            break


def _physics(case_path: Path):
    from csf.cuf.case import load_case
    from csf.cuf.problem.problem_api import load_problem, build_local_composite_problem
    from csf.cuf.csf_bridge import CSFCUFModelBridge
    from csf.cuf.core.sectional_geometry import SectionalGeometryProvider

    case = load_case(case_path)
    definition = load_problem(case.problem_path)
    if definition.problem_type != 'composite':
        raise NotImplementedError('Only existing composite cases are supported')
    physics = build_local_composite_problem(definition)
    load = physics.load_problem
    if type(load).__name__ != 'VerticalFaceTractions':
        raise NotImplementedError('Requires the existing VerticalFaceTractions adapter')
    bridge = CSFCUFModelBridge.from_yaml(definition.model_path)
    section = bridge.section_provider
    x0, x1 = map(float, bridge.longitudinal_domain())
    geometry = SectionalGeometryProvider(
        section_provider=section, constitutive_provider=bridge.constitutive_provider)
    faces = tuple(load.physical_surface_tractions(section_provider=section, x0=x0, x1=x1))
    if not faces or any(side != 'lower' for _, _, _, side in faces):
        raise NotImplementedError('Only the documented lower loaded surfaces are supported')
    if abs(float(load.upper_z)) > 0:
        raise NotImplementedError('Nonzero upper-face load not supported')
    return case, definition, geometry, section, faces, x0, x1


def _reference_resultants(section, faces, x: float, x_end: float, order: int):
    """Applied loads on [x,x_end] from the CSF sections and load adapter.

    This specific adapter prescribes pz per XY-projected face area. The
    three loaded CSF edges of this model are parallel to y at every x.
    """
    if x >= x_end:
        return 0., 0., 0.
    gp, gw = np.polynomial.legendre.leggauss(order)
    center, half = 0.5 * (x+x_end), 0.5 * (x_end-x)
    shear = moment = 0.
    for q, w in zip(gp, gw):
        xc = float(center + half*q)
        line = 0.
        for domain, edge, pz, _side in faces:
            verts = np.asarray(section.domain(x=xc, domain_id=int(domain)).vertices, float)
            if verts.shape != (4, 2):
                raise NotImplementedError('The physical loaded edge is not Q4')
            a = verts[int(edge)]
            b = verts[(int(edge) + 1) % 4]
            if abs(float(a[1]-b[1])) > 1e-8 * max(1., abs(a[1]), abs(b[1])):
                raise ValueError('CSF loaded edge is not parallel to transverse y')
            line += float(pz) * abs(float(b[0]-a[0]))
        df = float(w) * half * line
        shear += df
        moment -= (xc-x)*df
    return 0., float(shear), float(moment)


@dataclass(frozen=True)
class Sample:
    x: float
    target_x: float
    layer: int
    gp_side: str


class NativeGaussH8:
    """Index native Gauss stresses, with no independent geometric interpolation."""

    def __init__(self, path: Path, x0: float, x1: float):
        from csf.cuf.tools.plot_strain_stress_boundary_v10 import load_fem3d
        with np.load(path, allow_pickle=False) as data:
            required = {'nodes', 'elements', 'displacement', 'element_region',
                        'gauss_stress', 'mesh_divisions'}
            missing = required - set(data.files)
            if missing:
                raise ValueError('Native-stress FEM3D checkpoint missing: '+', '.join(sorted(missing)))
            if 'status' in data and str(np.asarray(data['status']).item()) != 'solved_opensees':
                raise ValueError('FEM3D checkpoint is not solved_opensees')
            self.case_name = str(np.asarray(data['case_name']).item()) if 'case_name' in data else None
            self.nodes = np.asarray(data['nodes'], float)
            self.connectivity = np.asarray(data['elements'], np.int64)
            self.regions = np.asarray(data['element_region'], np.int64)
            self.stresses = np.asarray(data['gauss_stress'], float)
            self.divisions = tuple(map(int, np.asarray(data['mesh_divisions']).tolist()))
            if 'gauss_stress_component_order' not in data:
                raise ValueError('Missing Gauss component metadata: source order cannot be assumed')
            labels = tuple(map(str, np.asarray(data['gauss_stress_component_order']).tolist()))
            if labels != ('xx', 'yy', 'zz', 'xy', 'yz', 'xz'):
                raise ValueError(f'Unexpected native OpenSees components: {labels}')
            if 'gauss_stress_point_order' not in data or 'OpenSees stdBrick' not in str(np.asarray(data['gauss_stress_point_order']).item()):
                raise ValueError('Missing/unsupported native OpenSees stdBrick point-order metadata')

        ne = len(self.connectivity)
        if self.connectivity.shape != (ne, 8) or self.stresses.shape != (ne, 8, 6):
            raise ValueError('Expected elements=(ne,8), gauss_stress=(ne,8,6)')
        if (self.regions.shape != (ne,) or not np.isfinite(self.stresses).all()
                or not np.isfinite(self.nodes).all()):
            raise ValueError('Invalid native stress, region or coordinate data')
        nx, nu, nv = self.divisions
        if len(self.divisions) != 3 or min(nx,nu,nv) < 1:
            raise ValueError('Unsupported FEM3D subdivisions')
        self.x_grid = np.unique(self.nodes[:, 0])
        if len(self.x_grid) != nx+1:
            raise ValueError('FEM mesh longitudinal stations differ from mesh_divisions')
        scale = max(1., abs(x0), abs(x1))
        if not np.allclose([self.x_grid[0], self.x_grid[-1]], [x0,x1], rtol=0, atol=1e-9*scale):
            raise ValueError('FEM3D and CSF longitudinal intervals differ')
        low = self.nodes[self.connectivity, 0].min(axis=1)
        high = self.nodes[self.connectivity, 0].max(axis=1)
        layer = np.searchsorted(self.x_grid, low, side='right') - 1
        if not (np.all((0 <= layer) & (layer < nx))
                and np.allclose(low,self.x_grid[layer],atol=1e-9*scale,rtol=0)
                and np.allclose(high,self.x_grid[layer+1],atol=1e-9*scale,rtol=0)):
            raise ValueError('FEM3D contains H8 elements spanning unexpected longitudinal stations')
        self.layer_of_element = layer
        # This project reader is used to LOCATE a CSF physical point in the
        # already-solved H8 discretization, not to calculate stresses or CSF
        # geometry/material. Its displacement-derived strain output is ignored.
        self.locator = load_fem3d(path)
        if type(self.locator).__name__ != 'FEM3DH8':
            raise ValueError('Native stress recovery requires the existing FEM3DH8 locator')
        if len(self.locator.ids) != ne:
            raise ValueError('FEM locator / native stress element count mismatch')
        self.nelements = ne
        self.nquad = 0
        self.ties = 0
        self.visited = set()

    def candidate_planes(self):
        a = 1. / np.sqrt(3.)
        for k, (lo, hi) in enumerate(zip(self.x_grid[:-1], self.x_grid[1:])):
            midpoint, half = 0.5*(lo+hi), 0.5*(hi-lo)
            for side, sign in (('minus',-1.), ('plus',1.)):
                yield Sample(float(midpoint+half*a*sign), float('nan'), k, side)

    def select(self, target_x: np.ndarray, sampling: str) -> list[Sample]:
        if sampling == 'all-gauss':
            return list(self.candidate_planes())
        if sampling == 'center':
            # Midpoint sections; stress is the mean of all 8 native Gauss
            # values, NOT an OpenSees stress evaluated at the midpoint.
            candidates = [Sample(0.5*(a+b), float('nan'), k, 'center')
                          for k,(a,b) in enumerate(zip(self.x_grid[:-1],self.x_grid[1:]))]
        else:
            candidates = list(self.candidate_planes())
        actual = np.asarray([p.x for p in candidates])
        selected: list[Sample] = []
        for x in target_x:
            distances = abs(actual - x)
            d = np.min(distances)
            # For targets on a mesh interface, choose the Gauss plane inside
            # the RIGHT-HAND element, respecting the [x,x_end] load segment.
            near = np.flatnonzero(abs(distances-d) < 1e-11 * max(1.,abs(x),float(np.ptp(actual))))
            right = [i for i in near if candidates[int(i)].x >= x]
            winner = int(right[0] if right else near[-1])
            p = candidates[winner]
            if selected and abs(p.x - selected[-1].x) < 1e-11 * max(1.,abs(x)):
                continue
            selected.append(Sample(p.x,float(x),p.layer,p.gp_side))
        return selected

    def stress_at(self, point: np.ndarray, domain_id: int, sample: Sample) -> np.ndarray:
        matches = self.locator.evaluate(point)
        possible = [int(ei) for ei, _, _ in matches
                    if self.layer_of_element[int(ei)] == sample.layer
                    and int(self.regions[int(ei)]) + 1 == domain_id]
        if len(possible) != 1:
            self.ties += 1
            raise ValueError(f'CSF point {point} in domain {domain_id}: '
                             f'expected exactly one matching H8 cell, got {possible}; '
                             'check mesh alignment and CSF geometry')
        ei = possible[0]
        self.nquad += 1
        self.visited.add(ei)
        if sample.gp_side == 'minus':
            native = self.stresses[ei,:4,:]
        elif sample.gp_side == 'plus':
            native = self.stresses[ei,4:,:]
        elif sample.gp_side == 'center':
            native = self.stresses[ei,:,:]
        else:
            raise RuntimeError(f'Invalid Gauss plane {sample.gp_side!r}')
        # Native OpenSees xx,yy,zz,xy,yz,xz order is preserved. The arithmetic
        # mean projects four (or eight) sampled stresses to one P0 value per cell.
        return native.mean(axis=0)


def _integrate_section(sample: Sample, geom, integrator, evaluator: NativeGaussH8):
    n = tz = my = area = 0.
    qcount = 0
    x = sample.x
    for domain_id in range(1,geom.number_of_domains(x)+1):
        data = geom.quadrature_data(x=x,domain_id=domain_id,integrator=integrator)
        for y,z,w in zip(data.y_points,data.z_points,data.weights):
            stress = evaluator.stress_at(np.array((x,float(y),float(z))),domain_id,sample)
            n += float(w) * stress[0]       # sigma_xx
            tz += float(w) * stress[5]      # sigma_xz in native OpenSees order
            my += float(w) * float(z) * stress[0]
            qcount += 1
        area += float(np.sum(data.weights))
    return dict(N_N=float(n),Tz_N=float(tz),My_Nmm=float(my),
                csf_area_mm2=float(area), quadrature_points=qcount)


def _support_balance(checkpoint: Path, x0: float):
    with np.load(checkpoint,allow_pickle=False) as d:
        if not {'nodes','end0_nodes','support_reactions','nodal_loads'}.issubset(d.files):
            return {'status':'not_available'}
        nodes = np.asarray(d['nodes'],float)
        fixed = np.asarray(d['end0_nodes'],np.int64)
        reaction = np.asarray(d['support_reactions'],float)
        loads = np.asarray(d['nodal_loads'],float)
        f_ref = np.asarray(d['force_resultant_N'],float) if 'force_resultant_N' in d else None
        m_ref = np.asarray(d['moment_resultant_Nmm'],float) if 'moment_resultant_Nmm' in d else None
    if reaction.shape != (len(fixed),3) or loads.shape != nodes.shape:
        raise ValueError('Invalid saved support reaction / applied nodal load arrays')
    relative = nodes - [x0,0.,0.]
    rf = np.sum(reaction,axis=0)
    rm = np.cross(relative[fixed],reaction).sum(axis=0)
    lf = loads.sum(axis=0)
    lm = np.cross(relative,loads).sum(axis=0)
    return dict(status='computed_from_native_nodal_reactions',
                applied_force_N=lf.tolist(),reaction_force_N=rf.tolist(),
                force_balance_N=(lf+rf).tolist(),
                applied_moment_Nmm=lm.tolist(),reaction_moment_Nmm=rm.tolist(),
                moment_balance_Nmm=(lm+rm).tolist(),
                driver_force_N=None if f_ref is None else f_ref.tolist(),
                driver_moment_Nmm=None if m_ref is None else m_ref.tolist())


def _plot(rows: list[dict], field: str, reference: str, title: str,
          unit: str, output: Path, sampling: str):
    x = np.array([r['x_L'] for r in rows])
    y = np.array([r[field] for r in rows])
    ref = np.array([r[reference] for r in rows])
    fig,(ax,ad)=plt.subplots(2,1,figsize=(9.5,6.2),sharex=True,
                          gridspec_kw={'height_ratios':[3,1.25]},constrained_layout=True)
    ax.plot(x,ref,'-',lw=1.8,label='Theoretical applied-load resultant')
    ax.plot(x,y,'o-',markersize=3,markerfacecolor='none',lw=.9,
            label=f'FEM3D native Gauss stresses ({sampling}, transverse P0)')
    ax.set_title(title)
    ax.set_ylabel(unit)
    ax.legend(loc='best',fontsize=8)
    ax.grid(alpha=.25)
    ad.plot(x,y-ref,'o-',ms=3,lw=.8)
    ad.axhline(0,ls='--',color='0.5',lw=.8)
    ad.set_xlabel('Longitudinal coordinate x/L (actual sampling plane)')
    ad.set_ylabel('FEM3D - theory\n'+unit)
    ad.grid(alpha=.25)
    fig.savefig(output,dpi=175)
    plt.close(fig)


def _overview(rows: list[dict], output: Path):
    fig,ax = plt.subplots(3,2,figsize=(12.5,9.5),sharex='col',
                         gridspec_kw={'width_ratios':[2.2,1]},constrained_layout=True)
    fig.suptitle('Native OpenSees H8 stresses | FEM3D vs prescribed loads')
    x = np.array([r['x_L'] for r in rows])
    for i,(key,ref,lab) in enumerate((('N_N','N_load_N','Axial force N [N]'),
                                      ('Tz_N','Tz_load_N','Shear force Tz [N]'),
                                      ('My_Nmm','My_load_Nmm','Bending moment My [N mm]'))):
        actual=np.array([r[key] for r in rows]); target=np.array([r[ref] for r in rows])
        a,d=ax[i]
        a.plot(x,target,'-',lw=1.6,label='Prescribed loads')
        a.plot(x,actual,'o-',ms=3.5,markerfacecolor='none',label='Native FEM3D')
        a.set_ylabel(lab); a.grid(alpha=.25)
        if i==0: a.legend()
        d.plot(x,actual-target,'o-',ms=3);d.axhline(0,ls='--',color='.5')
        d.set_ylabel('FEM3D - theory');d.grid(alpha=.25)
    ax[-1,0].set_xlabel('x/L');ax[-1,1].set_xlabel('x/L')
    fig.savefig(output,dpi=175)
    plt.close(fig)


def _requested_cuts(raw: str | None, count: int, x0: float, x1: float) -> np.ndarray:
    if raw is None:
        if not 2 <= count <= 200:
            raise ValueError('--points must lie in 2..200')
        frac = np.linspace(0.,1.,count+1)[:-1]
    else:
        frac = np.array([float(a) for a in raw.split(',')])
    if (len(frac) < 2 or not np.isfinite(frac).all() or np.any(frac<0)
            or np.any(frac>=1) or np.any(np.diff(frac)<=0)):
        raise ValueError('Cuts must be ordered finite x/L fractions in [0,1)')
    return x0+(x1-x0)*frac


def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--case',type=Path,required=True,help='Existing CSF-CUF case YAML')
    ap.add_argument('--fem-npz',type=Path,required=True,help='NPZ with native gauss_stress')
    ap.add_argument('--points',type=int,default=20,help='Number of requested x-stations, default 20')
    ap.add_argument('--cuts',help='Explicit x/L positions; native modes snap to nearest Gauss plane')
    ap.add_argument('--sampling',choices=('gauss','all-gauss','center'),default='gauss',
                    help='gauss: nearest true axial Gauss plane; all-gauss: every plane; '
                         'center: all-eight mean at H8 axial midpoint (diagnostic)')
    ap.add_argument('--section-gauss',type=int,help='CSF sectional quadrature order (case default)')
    ap.add_argument('--load-gauss',type=int,default=24,help='Gauss order for prescribed load integral')
    ap.add_argument('--output-dir',type=Path,help='Explicit output directory')
    a=ap.parse_args()

    case_path=a.case.resolve()
    _project_imports(case_path.parent.parent.parent)
    from csf.cuf.numerics.integration import FixedGaussPolygonIntegrator
    case,definition,geom,section,faces,x0,x1=_physics(case_path)
    fem_path=a.fem_npz.resolve()
    if not fem_path.is_file(): raise FileNotFoundError(fem_path)
    fem=NativeGaussH8(fem_path,x0,x1)
    if fem.case_name is not None and fem.case_name != case.name:
        raise ValueError(f'Physical case mismatch: NPZ={fem.case_name!r}, case={case.name!r}')
    targets=_requested_cuts(a.cuts,a.points,x0,x1)
    samples=fem.select(targets,a.sampling)
    if len(samples)<2:
        raise ValueError('Selected fewer than two distinct physical sections')
    section_order=int(a.section_gauss or case.section_integration.gauss_order)
    integrator=FixedGaussPolygonIntegrator(order=section_order)
    print(f'[FEM3D] Native stress: {fem.nelements} H8 elements; 8 Gauss points x 6 components',flush=True)
    print('[FEM3D] No strain/stress reconstruction: sigma = mean(native OpenSees Gauss sigma)',flush=True)
    print('[CSF] Physical section, area weights and materials: SectionalGeometryProvider.quadrature_data()',flush=True)
    print(f'[FEM3D] Sampling={a.sampling}; selected={len(samples)} sections; transverse recovery=P0 per cell',flush=True)
    rows=[]
    for i,sample in enumerate(samples,1):
        actual=_integrate_section(sample,geom,integrator,fem)
        ref=_reference_resultants(section,faces,sample.x,x1,a.load_gauss)
        row={'x_L':(sample.x-x0)/(x1-x0),'x_mm':sample.x,
             'target_x_mm':sample.target_x,'h8_layer_0based':sample.layer,
             'gauss_plane':sample.gp_side,**actual,
             'N_load_N':ref[0],'Tz_load_N':ref[1],'My_load_Nmm':ref[2],
             'dN_N':actual['N_N']-ref[0],
             'dTz_N':actual['Tz_N']-ref[1],
             'dMy_Nmm':actual['My_Nmm']-ref[2],
             'eTz_pct':100.*(actual['Tz_N']-ref[1])/abs(ref[1]) if ref[1] else float('nan'),
             'eMy_pct':100.*(actual['My_Nmm']-ref[2])/abs(ref[2]) if ref[2] else float('nan')}
        rows.append(row)
        print(f'[{i:03}/{len(samples):03}] x/L={row["x_L"]:.6f} {sample.gp_side:>6} '
              f'N={row["N_N"]:+.6g} Tz={row["Tz_N"]:+.6g} '
              f'(ref {ref[1]:+.6g}, err {row["eTz_pct"]:+.3f}%) '
              f'My={row["My_Nmm"]:+.6g} (ref {ref[2]:+.6g}, err {row["eMy_pct"]:+.3f}%)',flush=True)

    checkpoint_hash=_hash(fem_path)
    out=(a.output_dir.resolve() if a.output_dir else
         case_path.parent.parent.parent/'diagnostics'/'fem3d_N_T_M_native' /case.name /
         checkpoint_hash[:12]/a.sampling)
    out.mkdir(parents=True,exist_ok=True)
    with (out/'section_resultants.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (out/'support_balance.json').write_text(json.dumps(_support_balance(fem_path,x0),indent=2)+'\n',encoding='utf-8')
    (out/'provenance.json').write_text(json.dumps({
        'case':case.name,'checkpoint':str(fem_path),'sha256':checkpoint_hash,
        'method':'Native OpenSees stdBrick Gauss stress -> transverse P0 cell mean -> CSF sectional quadrature',
        'FEM3D_stress_components':['xx','yy','zz','xy','yz','xz'],
        'Gauss_point_order':'r(-,+) outside, s(-,+) middle, t(-,+) inside; stdBrick C++',
        'sampling':a.sampling,'sampling_points_actual_x_mm':[r['x_mm'] for r in rows],
        'CSF_provider':'SectionalGeometryProvider.quadrature_data',
        'physical_properties':'Only through CSF public API; no ad hoc interpolation',
        'FEM_element_locator':'Existing plot_strain_stress_boundary_v10.FEM3DH8.evaluate; returned strain discarded',
        'load_reference':'Existing VerticalFaceTractions physical_surface_tractions with CSF domain geometry',
        'section_gauss_order':section_order,'load_gauss_order':a.load_gauss,
        'quadrature_evaluations':fem.nquad,'distinct_H8_cells_evaluated':len(fem.visited),
        'limitations':['P0 recovery loses in-element transverse variation, notably effects on bending moment.',
                       'Gauss planes are interior to H8 elements; cut at the support is not available as native Gauss data.',
                       'Averaging native values is not identical to an exact stress surface integral.',
                       'The center mode uses an average of 8 values and is not a native midpoint stress.']
    },indent=2)+'\n',encoding='utf-8')
    _plot(rows,'N_N','N_load_N','Axial force N: native FEM3D vs theoretical','N [N]',out/'comparison_axial_force_N.png',a.sampling)
    _plot(rows,'Tz_N','Tz_load_N','Shear force Tz: native FEM3D vs theoretical','Tz [N]',out/'comparison_shear_force_Tz.png',a.sampling)
    _plot(rows,'My_Nmm','My_load_Nmm','Bending moment My: native FEM3D vs theoretical','My [N mm]',out/'comparison_bending_moment_My.png',a.sampling)
    _overview(rows,out/'comparison_N_Tz_My_overview.png')
    print(f'[DONE] CSV + 4 PNG + support_balance.json + provenance.json: {out}',flush=True)


if __name__=='__main__':
    main()
