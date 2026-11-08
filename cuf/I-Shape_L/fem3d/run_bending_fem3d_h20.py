#!/usr/bin/env python3
"""CSF-driven quadratic 20-node solid benchmark for cuf/I-Shape_L.

Requires sibling run_bending_fem3d_v2.py (the existing H8 driver).
Uses H8 mesh *only as a conforming three-block geometric topology*, replacing
all H8 cells by shared-edge quadratic 20-node bricks. The physical problem,
material sampling, and supports match the original script.

OpenSees implementation note:
  Recent OpenSees accepts element('20NodeBrick', tag, *20nodes, matTag,
                                     [b1, b2, b3]); it uses 3x3x3 quadrature.
  Older OpenSeesPy documentation lists an extra massDen argument; the OpenSees
  source currently parses only three optional body-force arguments.

Run --self-test and --mesh-only before production. See README_H20.md.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import run_bending_fem3d_v2 as base

# Canonical H8 corners are 0..7. Edge-mid nodes are in 9..20 H20 order:
# bottom perimeter; top perimeter; four vertical edges.
EDGE_CORNERS = ((0,1), (1,2), (2,3), (3,0),
                (4,5), (5,6), (6,7), (7,4),
                (0,4), (1,5), (2,6), (3,7))
H20_LOCAL = np.array([
    [-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
    [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1],
    [0,-1,-1],[1,0,-1],[0,1,-1],[-1,0,-1],
    [0,-1,1],[1,0,1],[0,1,1],[-1,0,1],
    [-1,-1,0],[1,-1,0],[1,1,0],[-1,1,0],
], dtype=float)


def h20_shape(q):
    """Quadratic serendipity shape values and natural-coordinate gradients."""
    r, s, t = map(float, q)
    N = np.zeros(20)
    dN = np.zeros((20, 3))
    for i, (a,b,c) in enumerate(H20_LOCAL[:8]):
        A, B, C = 1+a*r, 1+b*s, 1+c*t
        S = a*r+b*s+c*t-2
        N[i] = A*B*C*S/8
        dN[i] = (a*B*C*(S+A), b*A*C*(S+B), c*A*B*(S+C))
        dN[i] /= 8
    for i in range(8, 20):
        a,b,c = H20_LOCAL[i]
        if a == 0:
            N[i] = (1-r*r)*(1+b*s)*(1+c*t)/4
            dN[i] = (-2*r*(1+b*s)*(1+c*t), (1-r*r)*b*(1+c*t),
                     (1-r*r)*(1+b*s)*c)
        elif b == 0:
            N[i] = (1+a*r)*(1-s*s)*(1+c*t)/4
            dN[i] = (a*(1-s*s)*(1+c*t), (1+a*r)*(-2*s)*(1+c*t),
                     (1+a*r)*(1-s*s)*c)
        else:
            N[i] = (1+a*r)*(1+b*s)*(1-t*t)/4
            dN[i] = (a*(1+b*s)*(1-t*t), (1+a*r)*b*(1-t*t),
                     (1+a*r)*(1+b*s)*(-2*t))
        dN[i] /= 4
    return N, dN


def q8_shape(q):
    """Q8 face in corner+edge order [0,1,2,3,01,12,23,30]."""
    r, s = map(float, q)
    signs = ((-1,-1), (1,-1), (1,1), (-1,1))
    N = np.zeros(8)
    D = np.zeros((8,2))
    for i, (a,b) in enumerate(signs):
        A, B, S = 1+a*r, 1+b*s, a*r+b*s-1
        N[i] = A*B*S/4
        D[i] = (a*B*(S+A)/4, b*A*(S+B)/4)
    N[4] = (1-r*r)*(1-s)/2
    N[5] = (1+r)*(1-s*s)/2
    N[6] = (1-r*r)*(1+s)/2
    N[7] = (1-r)*(1-s*s)/2
    D[4] = (-r*(1-s), -(1-r*r)/2)
    D[5] = ((1-s*s)/2, -(1+r)*s)
    D[6] = (-r*(1+s), (1-r*r)/2)
    D[7] = (-(1-s*s)/2, -(1-r)*s)
    return N, D


def edge_key(a,b):
    return (int(min(a,b)), int(max(a,b)))


@dataclass
class QuadraticMesh:
    nodes: np.ndarray
    elements: np.ndarray
    bottom_faces: np.ndarray
    end0_nodes: np.ndarray
    end1_nodes: np.ndarray
    element_region: np.ndarray
    element_xmid: np.ndarray


def upgrade_to_h20(h8):
    """Build one shared mid-edge node for every physical H8 edge."""
    xyz = [list(p) for p in np.asarray(h8.nodes, float)]
    edge_ids = {}
    def midnode(a,b):
        key = edge_key(a,b)
        idx = edge_ids.get(key)
        if idx is None:
            idx = len(xyz)
            # Isoparametric quadratic map along an existing straight H8 edge.
            xyz.append(((np.asarray(xyz[a])+np.asarray(xyz[b]))/2).tolist())
            edge_ids[key] = idx
        return idx
    conns = []
    for conn in h8.elements:
        conn = list(map(int, conn))
        conns.append(conn + [midnode(conn[a], conn[b]) for a,b in EDGE_CORNERS])
    faces = []
    for face in h8.bottom_faces:
        a,b,c,d = map(int, face)
        faces.append([a,b,c,d, midnode(a,b), midnode(b,c), midnode(c,d), midnode(d,a)])
    nodes = np.asarray(xyz, float)
    x0 = float(np.min(nodes[:,0])); x1 = float(np.max(nodes[:,0]))
    tol = 1e-10 * max(1, x1-x0)
    return QuadraticMesh(
        nodes=nodes, elements=np.asarray(conns, dtype=np.int64),
        bottom_faces=np.asarray(faces, dtype=np.int64),
        end0_nodes=np.flatnonzero(abs(nodes[:,0]-x0) < tol),
        end1_nodes=np.flatnonzero(abs(nodes[:,0]-x1) < tol),
        element_region=h8.element_region, element_xmid=h8.element_xmid)


def consistent_bottom_loads(mesh, amplitude, x0, x1):
    """8x3 Gauss integral of physical Q8 area with global z traction."""
    p_r,w_r = np.polynomial.legendre.leggauss(8)
    p_s,w_s = np.polynomial.legendre.leggauss(3)
    loads = np.zeros_like(mesh.nodes)
    L = float(x1-x0)
    for face in mesh.bottom_faces:
        xyz = mesh.nodes[face]
        f = np.zeros(8)
        for r,wr in zip(p_r,w_r):
            for s,ws in zip(p_s,w_s):
                N,D = q8_shape((r,s))
                X = N@xyz
                tangent = D.T@xyz
                jac = np.linalg.norm(np.cross(tangent[0], tangent[1]))
                q = float(amplitude) * math.sin(math.pi*(X[0]-x0)/L)
                f += wr*ws*jac*q*N
        np.add.at(loads[:,2], face, f)
    return loads


def validate_h20(mesh, ntest=100):
    """Check isoparametric orientation at 27 Gauss points in sampled cells."""
    n = len(mesh.elements)
    indices = np.unique(np.linspace(0, n-1, min(ntest,n)).astype(int))
    g,_ = np.polynomial.legendre.leggauss(3)
    smallest = math.inf
    for i in indices:
        xyz = mesh.nodes[mesh.elements[i]]
        for r in g:
            for s in g:
                for t in g:
                    _,D = h20_shape((r,s,t))
                    det = np.linalg.det(xyz.T@D)
                    smallest = min(smallest, det)
                    if det <= 0 or not math.isfinite(det):
                        raise ValueError(f'H20 Jacobian not positive: eid={i} det={det:.12g}')
    return smallest


def solve_opensees_h20(mesh, E, nu, loads, x0,x1):
    try:
        import openseespy.opensees as ops
    except ImportError as exc:
        raise SystemExit('Missing OpenSeesPy: pip install openseespy') from exc
    ops.wipe()
    ops.model('basic','-ndm',3,'-ndf',3)
    for i,p in enumerate(mesh.nodes,1):
        ops.node(i,*map(float,p))
    materials={}
    tags=np.empty(len(E),dtype=int)
    for i,(e,v) in enumerate(zip(E,nu)):
        key=(float(e),float(v))
        if key not in materials:
            mtag=len(materials)+1
            ops.nDMaterial('ElasticIsotropic',mtag,*key)
            materials[key]=mtag
        tags[i]=materials[key]
    for i,(conn,tag) in enumerate(zip(mesh.elements,tags),1):
        # Body forces zero. The surface traction is loaded consistently.
        ops.element('20NodeBrick',i,*(int(n)+1 for n in conn),int(tag),0.,0.,0.)
    # Fix transverse displacements at both end sections (including midside nodes).
    centerline=base._centerline_nodes(mesh)
    xmid=(x0+x1)/2
    gauge=int(centerline[np.argmin(abs(mesh.nodes[centerline,0]-xmid))])
    fixity={int(i):[0,1,1] for i in np.r_[mesh.end0_nodes,mesh.end1_nodes]}
    fixity.setdefault(gauge,[0,0,0])[0]=1
    for i,flags in fixity.items():
        ops.fix(i+1,*flags)
    ops.timeSeries('Linear',1)
    ops.pattern('Plain',1,1)
    for i,f in enumerate(loads,1):
        if np.any(f):
            ops.load(i,*map(float,f))
    attempts=[]
    for name,sysargs in [('UmfPack',('UmfPack',)),('Mumps',('Mumps',)),('SparseGeneral-piv',('SparseGeneral','-piv'))]:
        ops.wipeAnalysis()
        try:
            ops.system(*sysargs)
            ops.numberer('RCM');ops.constraints('Plain')
            ops.integrator('LoadControl',1.)
            ops.algorithm('Linear');ops.analysis('Static')
            stat=ops.analyze(1)
            if stat==0:
                used=name
                break
            attempts.append(f'{name}: analyze={stat}')
        except Exception as exc:
            attempts.append(f'{name}: {exc}')
    else:
        raise RuntimeError('OpenSees H20 solve failed: '+'; '.join(attempts))
    disp=np.asarray([ops.nodeDisp(i) for i in range(1,len(mesh.nodes)+1)],float)
    shift=base._axial_gauge_mean(mesh,disp,centerline)
    disp[:,0]-=shift
    residual=base._axial_gauge_mean(mesh,disp,centerline)
    return disp,tags,gauge,centerline,shift,residual,used


def selftest():
    rng=np.random.default_rng(425)
    for _ in range(25):
        q=rng.uniform(-.95,.95,3)
        N,D=h20_shape(q)
        assert abs(N.sum()-1)<1e-12
        assert np.max(abs(D.sum(axis=0)))<1e-12
        assert np.max(abs(N@H20_LOCAL-q))<1e-12
        assert np.max(abs(D.T@H20_LOCAL-np.eye(3)))<1e-12
        f,df=q8_shape(q[:2]);assert abs(f.sum()-1)<1e-12
        assert np.max(abs(df.sum(axis=0)))<1e-12
    for i,p in enumerate(H20_LOCAL):
        N,_=h20_shape(p)
        assert np.max(abs(N-np.eye(20)[i]))<1e-12
    # Unit cube in canonical H8 ordering; check nodal area load force balance.
    xyz=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],
                  [0,0,1],[1,0,1],[1,1,1],[0,1,1]],float)
    h8=base.StructuredMesh(nodes=xyz,elements=np.arange(8)[None,:],
        element_region=np.array([0]),element_xmid=np.array([.5]),
        bottom_faces=np.array([[0,1,2,3]]),
        end0_nodes=np.array([0,3,4,7]),end1_nodes=np.array([1,2,5,6]))
    m=upgrade_to_h20(h8)
    validate_h20(m)
    total=consistent_bottom_loads(m,-1.,0.,1.)[:,2].sum()
    assert abs(total+2/math.pi)<1e-11,(total,-2/math.pi)
    # Manufactured quadratic displacement field: u_z=x^2 produces
    # d(tau_xz)/dx=2G, a strong-form curvature term absent from H8.
    from h20_strong_residual import residual_at
    u=np.zeros((20,3));u[:,2]=m.nodes[:,0]**2
    r,_,_=residual_at(m.nodes,u,70000.,0.3,(0.13,-0.21,0.33))
    G=70000./(2*1.3)
    assert np.allclose(r,(0.,0.,2*G),atol=1e-5),r
    print('PASS H20/Q8 partition, interpolation, positive Jacobian and exact resultant')
    print('PASS manufactured u_z=x^2: strong residual r_z=2G')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('model',nargs='?',type=Path, help='original physical 3-polygon CSF YAML')
    ap.add_argument('output',nargs='?',type=Path,help='output NPZ')
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--backend',choices=('opensees','scipy'),default='scipy')
    ap.add_argument('--mesh-only',action='store_true')
    ap.add_argument('--amplitude',type=float,default=-1.0,
                    help='global z traction amplitude, default -1 (same as CUF problem)')
    ap.add_argument('--nx',type=int,default=40)
    ap.add_argument('--ny-left',type=int,default=3)
    ap.add_argument('--ny-web',type=int,default=6)
    ap.add_argument('--ny-right',type=int,default=3)
    ap.add_argument('--nz-flange',type=int,default=4)
    ap.add_argument('--nz-web',type=int,default=20)
    a=ap.parse_args()
    if a.self_test:
        selftest();return
    if not a.model or not a.output:
        ap.error('model and output are required unless --self-test')
    field=base.load_csf_field(a.model.resolve())
    topo=base._i_section_topology(field)
    settings=base.MeshSettings(a.nx,a.ny_left,a.ny_web,a.ny_right,a.nz_flange,a.nz_web)
    h8=base.build_mesh(field,topo,settings)
    E,G,nu=base.evaluate_element_materials(field,h8)
    mesh=upgrade_to_h20(h8)
    jacmin=validate_h20(mesh,ntest=300)
    x0=float(field.s0.z);x1=float(field.s1.z)
    loads=consistent_bottom_loads(mesh,a.amplitude,x0,x1)
    if a.mesh_only:
        disp=np.empty((0,3),float)
        tags=np.full(len(E),-1,int)
        gauge=-1;centerline=base._centerline_nodes(mesh)
        shift=residual=np.nan;solver='mesh-only'
    else:
        if a.backend == 'opensees':
            disp,tags,gauge,centerline,shift,residual,solver=solve_opensees_h20(
                mesh,E,nu,loads,x0,x1)
        else:
            from h20_scipy_solver import solve_scipy_h20
            disp,tags,gauge,centerline,shift,residual,solver=solve_scipy_h20(
                mesh,E,nu,loads,x0,x1)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(a.output,
        nodes=mesh.nodes,elements=mesh.elements,
        element_type=np.array('20NodeBrick'),
        element_region=mesh.element_region,
        element_region_names=np.asarray([str(p.name) for p in field.s0.polygons],dtype='U64'),
        element_xmid=mesh.element_xmid,
        element_E=E,element_G=G,element_nu=nu,element_material_tag=tags,
        bottom_faces=mesh.bottom_faces,displacement=disp,nodal_loads=loads,
        end0_nodes=mesh.end0_nodes,end1_nodes=mesh.end1_nodes,
        gauge_node=np.array(gauge),axial_gauge_centerline_nodes=centerline,
        axial_gauge_shift=np.array(shift),axial_gauge_residual=np.array(residual),
        opensees_solver=np.array(solver),amplitude=np.array(a.amplitude),
        x0=np.array(x0),x1=np.array(x1),
        mesh_nx=np.array(a.nx),
        mesh_ny_left=np.array(a.ny_left),mesh_ny_web=np.array(a.ny_web),
        mesh_ny_right=np.array(a.ny_right),mesh_nz_flange=np.array(a.nz_flange),
        mesh_nz_web=np.array(a.nz_web),
        min_jacobian_tested=np.array(jacmin))
    print(f'element=20NodeBrick nodes={len(mesh.nodes)} elements={len(mesh.elements)} solver={solver}')
    print(f'loads Fz={loads[:,2].sum():.12g} N; min Jacobian sampled={jacmin:.8g}')
    if disp.size:
        print(f'min uz={disp[:,2].min():.12g} mm axial gauge residual={residual:.3g} mm')
    print('saved',a.output)

if __name__=='__main__':
    main()
