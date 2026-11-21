# Version: CSF-CUF OpenSees CSF-driven H8 FEM3D v01 - 2026-11-20
"""Independent OpenSees stdBrick H8 verification model for a CSF-CUF case.

Uses only established public CSF/CUF APIs to obtain the model and problem:
    load_case -> load_problem -> build_local_composite_problem
    CSFCUFModelBridge -> section_provider / domain_state
    local physical_surface_tractions / physical_boundary_condition

No YAML is parsed or interpreted by this FEM driver.  No number of CSF domains,
I-section geometry, material names, surface names or load magnitude is built in.
The new code covers only the missing H8 volume meshing and 3D OpenSees solve.

Initial geometric scope is strict: conforming, convex, CCW Q4 domains with
matching full-edge interfaces and no cutouts/voids.  Unsupported topology is
rejected instead of generating disconnected or distorted elements.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from csf.cuf.case import load_case
from csf.cuf.csf_bridge import CSFCUFModelBridge
from csf.cuf.problem.problem_api import load_problem, build_local_composite_problem


@dataclass(frozen=True)
class H8Mesh:
    nodes: np.ndarray                    # (nnode,3), x,y,z [mm]
    elements: np.ndarray                 # (nel,8), 0-based standard OpenSees ordering
    element_region: np.ndarray           # zero-based CSF domain index
    element_xmid: np.ndarray
    end0_nodes: np.ndarray
    end1_nodes: np.ndarray
    loaded_faces: np.ndarray             # (nface,4) zero-based
    loaded_face_pz: np.ndarray           # signed N/mm2 of projected XY area
    loaded_face_domain: np.ndarray       # one-based CSF domain ID
    shared_interface_pairs: int


def _q4_vertices(provider, x: float, domain_id: int) -> np.ndarray:
    """Get geometry only through the authoritative CSF section provider."""
    domain = provider.domain(x, domain_id)
    if domain.excluded_vertices:
        raise ValueError(
            f"CSF domain {domain_id} has holes / child polygons: "
            "the initial conforming H8 mesher does not support exclusions"
        )
    V = np.asarray(domain.vertices, dtype=float)
    if V.shape != (4, 2) or not np.all(np.isfinite(V)):
        raise ValueError(f"CSF domain {domain_id} must be a finite quadrilateral Q4")
    edges = np.roll(V, -1, axis=0) - V
    next_edges = np.roll(edges, -1, axis=0)
    cross = edges[:,0] * next_edges[:,1] - edges[:,1] * next_edges[:,0]
    area = 0.5 * np.sum(V[:, 0] * np.roll(V[:, 1], -1) - V[:, 1] * np.roll(V[:, 0], -1))
    if area <= 1e-12 or np.min(cross) <= 1e-12:
        raise ValueError(
            f"CSF domain {domain_id} must have nondegenerate convex CCW Q4 geometry at x={x:g}"
        )
    return V


def _q4_point(V: np.ndarray, u: float, v: float) -> np.ndarray:
    """Bilinear Q4 interpolation in the section only; CSF supplies all corners."""
    return ((1-u)*(1-v)*V[0] + u*(1-v)*V[1]
            + u*v*V[2] + (1-u)*v*V[3])


def _cross2(a, b):
    """Signed two-dimensional scalar cross product (NumPy 2 compatible)."""
    return float(a[0]*b[1] - a[1]*b[0])


def _edge_intersection_kind(A: np.ndarray, B: np.ndarray, tol: float):
    """Detect shared full edges, and reject partial/T-junction overlaps.

    Geometric topology belongs to CSF.  This check is only the FEM-specific
    *conformity* requirement of the H8 mesher: two adjacent domains must be
    represented by exactly matching interface grids.
    """
    shared = []
    for ea in range(4):
        a, b = A[ea], A[(ea+1) % 4]
        ab = b - a
        length = float(np.linalg.norm(ab))
        for eb in range(4):
            c, d = B[eb], B[(eb+1) % 4]
            cd = d - c
            length2 = float(np.linalg.norm(cd))
            if length < tol or length2 < tol:
                continue
            # Segment must lie on the same supporting line, and overlap.
            if abs(_cross2(ab, c-a)) > tol*length or abs(_cross2(ab, d-a)) > tol*length:
                continue
            if abs(_cross2(ab, cd)) > tol * length2:
                continue
            t0, t1 = float(np.dot(c-a, ab)/length**2), float(np.dot(d-a, ab)/length**2)
            overlap = min(1.0, max(t0,t1)) - max(0.0, min(t0,t1))
            if overlap*length <= tol:
                continue
            full = (np.linalg.norm(a-d) <= tol and np.linalg.norm(b-c) <= tol) or (
                np.linalg.norm(a-c) <= tol and np.linalg.norm(b-d) <= tol
            )
            if not full:
                raise ValueError(
                    "Nonconforming CSF interface: polygons share a partial edge / "
                    "T-junction. The H8 v01 mesher supports matching entire edges only."
                )
            shared.append((ea,eb))
    return shared


def _edge_nodes(grid: np.ndarray, edge: int) -> np.ndarray:
    if edge == 0:
        return grid[0, :]
    if edge == 1:
        return grid[:, -1]
    if edge == 2:
        return grid[-1, ::-1]
    if edge == 3:
        return grid[::-1, 0]
    raise ValueError(f"invalid Q4 edge {edge}")


def _h8_jacobian_check(nodes: np.ndarray, elements: np.ndarray):
    """Check detJ of every H8 element at all 2x2x2 Gauss points."""
    # The OpenSees stdBrick local node ordering is
    # (-,-,-),(+,-,-),(+,+,-),(-,+,-),(-,-,+),(+,-,+),(+,+,+),(-,+,+).
    signs = np.array([
        [-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
        [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1],
    ], dtype=float)
    g = 1.0 / np.sqrt(3.0)
    for a in (-g,g):
        for b in (-g,g):
            for c in (-g,g):
                points = np.array([a,b,c])
                derivs = np.empty((8,3), dtype=float)
                for k in range(3):
                    rest = [j for j in range(3) if j != k]
                    derivs[:,k] = (signs[:,k]/8.0
                        * (1.0+signs[:,rest[0]]*points[rest[0]])
                        * (1.0+signs[:,rest[1]]*points[rest[1]]))
                J = np.einsum('eai,aj->eij', nodes[elements], derivs)
                determinants = np.linalg.det(J)
                bad = np.flatnonzero(~np.isfinite(determinants) | (determinants <= 0))
                if len(bad):
                    eid = int(bad[0])
                    raise ValueError(
                        f"Invalid/inverted OpenSees H8 element={eid+1}, "
                        f"detJ={determinants[eid]:g} at Gauss ({a:g},{b:g},{c:g})"
                    )


def build_h8_mesh(section_provider, *, nx: int, nu: int, nv: int, loaded_edges) -> H8Mesh:
    """Generate conforming multi-domain H8 directly from CSF sections.

    Domain count and cross-sectional dimensions are always queried from CSF.
    A single (nu,nv) refinement per Q4 is used, with checks that neighbors
    produce exactly the same node grids on each shared full interface.
    """
    if min(nx,nu,nv) < 1:
        raise ValueError("FEM mesh requires nx, nu, nv >= 1")
    x0,x1 = section_provider.longitudinal_domain()
    xs = np.linspace(x0,x1,nx+1)
    domains = tuple(range(1,section_provider.number_of_domains(x0)+1))
    if not domains:
        raise ValueError("CSF model contains no material domains")
    if section_provider.number_of_domains(x1) != len(domains):
        raise ValueError("CSF domain count changes between S0 and S1")
    geometry0 = {k:_q4_vertices(section_provider,x0,k) for k in domains}
    geometry1 = {k:_q4_vertices(section_provider,x1,k) for k in domains}
    scale = max(1.0, max(float(np.max(np.abs(V))) for V in (*geometry0.values(),*geometry1.values())))
    tol = 1e-9 * scale
    shared = []
    for i,k in enumerate(domains):
        for j in domains[i+1:]:
            before = _edge_intersection_kind(geometry0[k],geometry0[j],tol)
            after = _edge_intersection_kind(geometry1[k],geometry1[j],tol)
            if before != after:
                raise ValueError(f"CSF domains {k} and {j} change interface topology")
            for edge_k, edge_j in before:
                shared.append((k,edge_k,j,edge_j))

    # Merge coincident Q4 nodes across all CSF domains at every x station.
    vertices = []
    layers = []
    for x in xs:
        if section_provider.number_of_domains(float(x)) != len(domains):
            raise ValueError("CSF domain count changes at an interior station")
        cmap = {}
        layer = {}
        for k in domains:
            V = _q4_vertices(section_provider,float(x),k)
            grid = np.empty((nv+1,nu+1),dtype=np.int64)
            for iv in range(nv+1):
                for iu in range(nu+1):
                    yz = _q4_point(V, iu/nu, iv/nv)
                    key = tuple(int(round(float(q)/tol)) for q in yz)
                    if key not in cmap:
                        cmap[key] = len(vertices)
                        vertices.append((float(x),float(yz[0]),float(yz[1])))
                    else:
                        p = np.asarray(vertices[cmap[key]][1:])
                        if np.linalg.norm(p-yz) > 0.5*tol:
                            raise ValueError("CSF mesh node hash collision; refine the geometric tolerance")
                    grid[iv,iu] = cmap[key]
            layer[k] = grid
        for k,ek,j,ej in shared:
            a = set(map(int,_edge_nodes(layer[k],ek)))
            b = set(map(int,_edge_nodes(layer[j],ej)))
            if a != b:
                raise ValueError(
                    f"Nonconforming H8 nodes on CSF interface {k}:{ek} - {j}:{ej}. "
                    "Choose compatible nu,nv or use the same count in both directions."
                )
        layers.append(layer)

    nodes = np.asarray(vertices,dtype=np.float64)
    elements, region, xmid = [], [], []
    for ix in range(nx):
        for k in domains:
            g0,g1=layers[ix][k],layers[ix+1][k]
            for iv in range(nv):
                for iu in range(nu):
                    elements.append((
                        g0[iv,iu],g1[iv,iu],g1[iv,iu+1],g0[iv,iu+1],
                        g0[iv+1,iu],g1[iv+1,iu],g1[iv+1,iu+1],g0[iv+1,iu+1],
                    ))
                    region.append(k-1)
                    xmid.append(0.5*(xs[ix]+xs[ix+1]))
    elems = np.asarray(elements,dtype=np.int64)
    _h8_jacobian_check(nodes,elems)

    # Generate loaded 3D faces from *adapter-resolved* CSF polygon edges.
    faces, face_p, face_domain = [], [], []
    for k, edge, pz, _side in loaded_edges:
        if k not in domains or not 0 <= edge <= 3:
            raise ValueError(f"Invalid loaded CSF edge {k}:{edge}")
        for ix in range(nx):
            strip0 = _edge_nodes(layers[ix][k],edge)
            strip1 = _edge_nodes(layers[ix+1][k],edge)
            for i in range(len(strip0)-1):
                faces.append((strip0[i],strip1[i],strip1[i+1],strip0[i+1]))
                face_p.append(float(pz))
                face_domain.append(int(k))

    # Reject a loaded face that appears on two H8 solids (internal interface).
    face_counts=Counter()
    for e in elems:
        for local in ((0,1,2,3),(4,5,6,7),(0,1,5,4),
                      (1,2,6,5),(2,3,7,6),(3,0,4,7)):
            face_counts[tuple(sorted(int(e[i]) for i in local))]+=1
    for face in faces:
        appearances=face_counts[tuple(sorted(map(int,face)))]
        if appearances != 1:
            raise ValueError(
                f"Loaded face {tuple(map(int,face))} is not a unique exterior H8 face; "
                f"H8 adjacency count={appearances}"
            )

    tolx=1e-10*max(1.0, abs(x1-x0))
    end0=np.flatnonzero(np.abs(nodes[:,0]-x0)<=tolx)
    end1=np.flatnonzero(np.abs(nodes[:,0]-x1)<=tolx)
    return H8Mesh(
        nodes=nodes,elements=elems,element_region=np.asarray(region,dtype=np.int64),
        element_xmid=np.asarray(xmid,dtype=float),end0_nodes=end0,end1_nodes=end1,
        loaded_faces=np.asarray(faces,dtype=np.int64).reshape(-1,4),
        loaded_face_pz=np.asarray(face_p,dtype=float),
        loaded_face_domain=np.asarray(face_domain,dtype=np.int64),
        shared_interface_pairs=len(shared),
    )


def _q4_surface_values(a: float, b: float):
    """Q4 face interpolation for consistent H8 surface nodal loads."""
    N = np.asarray(((1-a)*(1-b),(1+a)*(1-b),(1+a)*(1+b),(1-a)*(1+b)),dtype=float)*0.25
    Na = np.asarray((-(1-b),(1-b),(1+b),-(1+b)),dtype=float)*0.25
    Nb = np.asarray((-(1-a),-(1+a),(1+a),(1-a)),dtype=float)*0.25
    return N,Na,Nb


def assemble_projected_vertical_face_forces(mesh: H8Mesh, *, axial_gauss: int, edge_gauss: int):
    """FE-consistent nodal load using the CUF adapter's same physical law.

    dFz = p_z * |(dX/da cross dX/db)_z| da db, NOT p_z*dA.
    Integrates each 4-node H8 boundary face directly in its natural coords.
    """
    gx,wx = np.polynomial.legendre.leggauss(int(axial_gauss))
    gt,wt = np.polynomial.legendre.leggauss(int(edge_gauss))
    nodal = np.zeros((len(mesh.nodes),3),dtype=float)
    direct_force=np.zeros(3)
    direct_moment=np.zeros(3)
    for face,pz in zip(mesh.loaded_faces,mesh.loaded_face_pz):
        xyz=mesh.nodes[face]
        for a,wa in zip(gx,wx):
            for b,wb in zip(gt,wt):
                N,Na,Nb = _q4_surface_values(float(a),float(b))
                da=Na @ xyz
                db=Nb @ xyz
                projected_jacobian=abs(float(np.cross(da,db)[2]))
                dforce=np.array([0.0,0.0,float(pz)*projected_jacobian*float(wa*wb)])
                for j,nid in enumerate(face):
                    nodal[nid]+=N[j]*dforce
                direct_force+=dforce
                direct_moment+=np.cross(N@xyz,dforce)
    if not np.allclose(nodal.sum(axis=0),direct_force,rtol=2e-12,atol=1e-7):
        raise RuntimeError("Projected surface load integration loses resultant force")
    moments=np.cross(mesh.nodes,nodal).sum(axis=0)
    if not np.allclose(moments,direct_moment,rtol=2e-12,atol=1e-4):
        raise RuntimeError("Projected surface load integration loses resultant moment")
    return nodal,direct_force,direct_moment


def evaluate_materials(bridge: CSFCUFModelBridge, mesh: H8Mesh):
    """Use CSF's absolute material carriers; OpenSees requires isotropy."""
    E,G,nu = np.empty((3,len(mesh.elements)),dtype=float)
    cache={}
    for eid,(x,k0) in enumerate(zip(mesh.element_xmid,mesh.element_region)):
        key=(float(x),int(k0)+1)
        if key not in cache:
            state=bridge.domain_state(*key)
            e,g,n = state.E,state.G,state.poisson
            if n is None or not (-1.0 < n < 0.5) or e<=0 or g<=0:
                raise ValueError(f"OpenSees ElasticIsotropic incompatible with CSF domain {key}")
            if not np.isclose(g,e/(2*(1+n)),rtol=1e-9,atol=1e-8):
                raise ValueError(
                    f"CSF domain {key[1]} at x={x:g} has independent G="
                    f"{g:g}, incompatible with OpenSees ElasticIsotropic E,nu"
                )
            cache[key]=(e,g,n)
        E[eid],G[eid],nu[eid]=cache[key]
    return E,G,nu


def solve_opensees(mesh:H8Mesh, E:np.ndarray, nu:np.ndarray, nodal_loads:np.ndarray):
    """OpenSees 3D solids and fully fixed left section; no CUF code reused."""
    try:
        import openseespy.opensees as ops
    except ImportError as exc:
        raise RuntimeError(
            "OpenSeesPy is not available. Install openseespy in your active "
            "environment or use --mesh-only to verify inputs without solving."
        ) from exc
    ops.wipe()
    ops.model('basic','-ndm',3,'-ndf',3)
    for idx,(x,y,z) in enumerate(mesh.nodes,start=1):
        ops.node(idx,float(x),float(y),float(z))
    tags={}
    mat=np.empty(len(mesh.elements),dtype=np.int64)
    for i,(e,n) in enumerate(zip(E,nu)):
        key=(float(e),float(n))
        if key not in tags:
            tag=len(tags)+1
            tags[key]=tag
            ops.nDMaterial('ElasticIsotropic',tag,float(e),float(n))
        mat[i]=tags[key]
    for eid,(conn,tag) in enumerate(zip(mesh.elements,mat),start=1):
        ops.element('stdBrick',eid,*[int(a)+1 for a in conn],int(tag))
    for idx in mesh.end0_nodes:
        ops.fix(int(idx)+1,1,1,1)
    ops.timeSeries('Linear',1)
    ops.pattern('Plain',1,1)
    for i,force in enumerate(nodal_loads,start=1):
        if np.any(force!=0):
            ops.load(i,*map(float,force))
    def _configure(system):
        ops.wipeAnalysis()
        if system == 'UmfPack':
            ops.system('UmfPack')
        else:
            ops.system('SparseGeneral','-piv')
        ops.numberer('RCM')
        ops.constraints('Plain')
        ops.integrator('LoadControl',1.0)
        ops.algorithm('Linear')
        ops.analysis('Static')
    _configure('UmfPack')
    status=ops.analyze(1)
    if status != 0:
        # Retain solver fallback from the supplied OpenSees FEM3D driver.
        _configure('SparseGeneral')
        status=ops.analyze(1)
    if status != 0:
        raise RuntimeError(f"OpenSees static analysis failed: code {status}")
    u=np.asarray([ops.nodeDisp(i) for i in range(1,len(mesh.nodes)+1)],dtype=float)
    ops.reactions()
    reaction=np.asarray([ops.nodeReaction(int(i)+1) for i in mesh.end0_nodes],dtype=float)
    return u,mat,reaction


def run(case_yaml: str|Path, output: str|Path, *, nx:int, nu:int, nv:int, mesh_only:bool=False):
    """No direct YAML reads: all model/problem decoding belongs to CSF/CUF APIs."""
    case=load_case(case_yaml)
    definition=load_problem(case.problem_path)
    if definition.problem_type != 'composite':
        raise ValueError('FEM3D v01 expects the local problem.type: composite')
    if any(x is not None for x in (
        case.problem_adapter_path,case.problem_load_adapter_path,
        case.problem_constraint_adapter_path,
    )):
        raise ValueError('Composite FEM3D case must not declare an adapter in the case YAML')
    problem=build_local_composite_problem(definition)
    bridge=CSFCUFModelBridge.from_yaml(definition.model_path)
    section_provider=bridge.section_provider
    x0,x1=bridge.longitudinal_domain()
    load=problem.load_problem
    constraint=problem.constraint_problem
    loads_api=getattr(load,'physical_surface_tractions',None)
    bc_api=getattr(constraint,'physical_boundary_condition',None)
    if not callable(loads_api):
        raise TypeError('Local load adapter must implement physical_surface_tractions() for FEM3D')
    if not callable(bc_api):
        raise TypeError('Local constraint adapter must implement physical_boundary_condition() for FEM3D')
    boundary=bc_api()
    if boundary != {'kind':'full_section_clamp','location':'start'}:
        raise NotImplementedError(f'Unsupported FEM3D boundary prescription: {boundary!r}')
    edges=loads_api(section_provider=section_provider,x0=x0,x1=x1)
    if not edges:
        raise ValueError('No nonzero physical surface tractions to assemble')
    mesh=build_h8_mesh(section_provider,nx=nx,nu=nu,nv=nv,loaded_edges=edges)
    E,G,nu_el=evaluate_materials(bridge,mesh)
    if not (hasattr(load,'axial_gauss') and hasattr(load,'edge_gauss')):
        raise TypeError('Surface load adapter must expose axial_gauss and edge_gauss')
    nodal,force,moment=assemble_projected_vertical_face_forces(
        mesh,axial_gauss=int(load.axial_gauss),edge_gauss=int(load.edge_gauss),
    )
    print(f'[FEM3D] CSF domains={section_provider.number_of_domains(x0)}; '
          f'H8 elements={len(mesh.elements)}; nodes={len(mesh.nodes)}; '
          f'CSF interface pairs={mesh.shared_interface_pairs}',flush=True)
    print(f'[FEM3D] F={force} N; M={moment} Nmm; left fixed nodes={len(mesh.end0_nodes)}',flush=True)
    if mesh_only:
        displacement=np.empty((0,3),dtype=float)
        material_tags=np.full(len(mesh.elements),-1,dtype=np.int64)
        support_reactions=np.empty((0,3),dtype=float)
    else:
        displacement,material_tags,support_reactions=solve_opensees(mesh,E,nu_el,nodal)
        if not np.all(np.isfinite(displacement)):
            raise RuntimeError('OpenSees returned a non-finite displacement field')
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    names = [d['s0_name'] for d in section_provider.inspect_section_entities(x0)]
    np.savez_compressed(
        output,
        nodes=mesh.nodes,elements=mesh.elements,
        element_region=mesh.element_region,element_region_names=np.asarray(names,dtype=str),
        element_xmid=mesh.element_xmid,element_E=E,element_G=G,element_nu=nu_el,
        element_material_tag=material_tags,
        loaded_faces=mesh.loaded_faces,loaded_face_pz=mesh.loaded_face_pz,
        loaded_face_domain=mesh.loaded_face_domain,
        displacement=displacement,nodal_loads=nodal,
        end0_nodes=mesh.end0_nodes,end1_nodes=mesh.end1_nodes,
        support_reactions=support_reactions,
        force_resultant_N=force,moment_resultant_Nmm=moment,
        case_name=np.asarray(case.name),
        model_path=np.asarray(str(definition.model_path)),
        problem_path=np.asarray(str(definition.path)),
        x0=np.asarray(x0),x1=np.asarray(x1),
        mesh_divisions=np.asarray([nx,nu,nv],dtype=np.int64),
        status=np.asarray('mesh_only' if mesh_only else 'solved_opensees'),
        load_definition=np.asarray('projected_xy_vertical_global_z'),
        boundary_definition=np.asarray('full_section_clamp_start'),
    )
    print(f'[FEM3D] saved={output} status={"mesh_only" if mesh_only else "solved_opensees"}',flush=True)
    return mesh, nodal, displacement


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case',type=Path,help='CSF-CUF case YAML, decoded only by load_case()')
    parser.add_argument('output',type=Path,help='Result NPZ')
    parser.add_argument('--nx',type=int,default=8,help='H8 divisions along x')
    parser.add_argument('--nu',type=int,default=2,help='Q4 divisions along local first edge')
    parser.add_argument('--nv',type=int,default=2,help='Q4 divisions along local second edge')
    parser.add_argument('--mesh-only',action='store_true',help='validate mesh, materials and loads; no OpenSees solve')
    a=parser.parse_args()
    run(a.case,a.output,nx=a.nx,nu=a.nu,nv=a.nv,mesh_only=a.mesh_only)


if __name__=='__main__':
    main()
