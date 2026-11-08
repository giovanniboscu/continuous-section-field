#!/usr/bin/env python3
"""Physical-surface traction checks for the I-Shape_L FEM3D H20 / CSF-CUF benchmark.

Inputs: solved H20 NPZ, solved CUF NPZ, CSF 9-domain YAML; no solver rerun.
Uses same physical samples on H20 free/loaded surfaces and true FEM material
interfaces. Tests all additional CUF L9 domain seams separately. Do NOT treat
supported end faces as traction-free: reactions may act there.

Traction: t = sigma @ normal. Interface jump: (sigma_A - sigma_B) @ n_A.
Output units: MPa for traction, mm^2 for area, N for integrated traction.
The interior equilibrium residual (MPa/mm) is a DIFFERENT measurement.

Dependencies: numpy, pyyaml and sibling
  compare_fem3d_h20_cuf_equilibrium.py (v3)
  fem3d/run_bending_fem3d_h20.py
  fem3d/h20_strong_residual.py
  fem3d/run_bending_fem3d_v2.py
Plus the CSF compiled_field module via PYTHONPATH=../../src.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import compare_fem3d_h20_cuf_equilibrium as core

VERSION = 'H20-CUF physical-surface comparison v1 (2026-11-07)'
CORNERS_UV = np.array([[-1.,-1.],[1.,-1.],[1.,1.],[-1.,1.]])
# Parent isoparametric face q=(r,s,t) with the two free parameters (u,v).
# List of corner and midside indices in Q8 face order.
FACES = (
    (0,-1,(0,3,7,4,11,19,15,16)),
    (0,+1,(1,2,6,5,9,18,13,17)),
    (1,-1,(0,1,5,4,8,17,12,16)),
    (1,+1,(3,2,6,7,10,18,14,19)),
    (2,-1,(0,1,2,3,8,9,10,11)),
    (2,+1,(4,5,6,7,12,13,14,15)),
)


def face_q(axis: int, sign: int, uv):
    q=np.asarray(uv,float)
    result=np.zeros(3,float)
    result[axis]=float(sign)
    free=[i for i in range(3) if i!=axis]
    result[free]=q
    return result,free


def tensor(voigt):
    a,b,c,d,e,f=map(float,voigt)
    return np.array([[a,f,e],[f,b,d],[e,d,c]],dtype=float)


def face_table(conn):
    """Build topology from H20 shared Q8 faces. Detect non-manifold faces."""
    faceowners=defaultdict(list)
    for ei,c in enumerate(conn):
        for axis,sign,loc in FACES:
            ids=tuple(map(int,c[list(loc)]))
            key=tuple(sorted(ids[:4]))
            faceowners[key].append((int(ei),int(axis),int(sign),ids))
    counts={1:0,2:0}
    for key,owners in faceowners.items():
        if len(owners) not in (1,2):
            raise ValueError(f'Nonmanifold H20 face: {key}, owners={len(owners)}')
        if len(owners)==2 and set(owners[0][3])!=set(owners[1][3]):
            raise ValueError('Adjacent H20 faces do not share all eight Q8 nodes')
        counts[len(owners)]+=1
    return faceowners,counts


def uv_transform(ids_a,ids_b):
    """Map face local coordinates A -> B by the common corner node IDs."""
    bs=np.array([CORNERS_UV[list(ids_b[:4]).index(i)] for i in ids_a[:4]])
    m=np.linalg.lstsq(CORNERS_UV,bs,rcond=None)[0]
    if np.max(np.abs(CORNERS_UV@m-bs))>1e-12:
        raise ValueError('Invalid neighboring Q8 face parametrization')
    return m


def face_geometry(X,axis,sign,uv,shape):
    q,free=face_q(axis,sign,uv)
    N,D=shape(q)
    xyz=N@X
    dxdu=X.T@D[:,free[0]]
    dxdv=X.T@D[:,free[1]]
    vec=np.cross(dxdu,dxdv)
    area=float(np.linalg.norm(vec))
    if not np.isfinite(area) or area<=0:
        raise ValueError('Degenerate H20 face Jacobian')
    return xyz,vec/area,area,q


def outward_orientation(n,face_point,center):
    d=float(np.dot(n,face_point-center))
    if abs(d)<1e-10:
        raise ValueError('Cannot orient face normal using element center')
    return n if d>0 else -n


def boundary_class(p,xyz_corners,x0,x1,load_faces,face_ids):
    if np.all(np.abs(xyz_corners[:,0]-x0)<1e-7) or np.all(np.abs(xyz_corners[:,0]-x1)<1e-7):
        return 'supported_end'
    if face_ids in load_faces:
        return 'loaded_bottom'
    # In this benchmark bottom z(x) goes from -75 to -35 mm.
    # This check is intentionally independent from the stored bottom_faces.
    zbottom=-75.0+0.04*xyz_corners[:,0]
    if np.max(np.abs(xyz_corners[:,2]-zbottom))<1e-7:
        return 'loaded_bottom'
    return 'free_external'


def cuf_stress_one_side(field,material,p,direction,epsilon,expected_di=None):
    """One-sided limit approximated a fixed tiny distance inside the named domain.

    No averaging across material interfaces; the caller checks epsilon stability.
    """
    q=np.asarray(p,float)+float(epsilon)*np.asarray(direction,float)
    di,dist=core.find_domain(field,material,q)
    if di is None:
        raise ValueError(f'CUF side lookup failed at {q.tolist()} (epsilon {epsilon})')
    if expected_di is not None and di!=expected_di:
        raise ValueError(f'Wrong CUF domain on side: expected {expected_di}, found {di}')
    g=field.displacement_gradient(float(q[0]),float(q[1]),float(q[2]),domain_index=int(di))
    return tensor(material.stress(g,float(q[0]),int(di))),int(di)


def h20_stress(stress_fn,X,U,E,nu,q):
    v,_,_=stress_fn(X,U,float(E),float(nu),np.asarray(q,float))
    return tensor(v)


def components(row,kind,vec):
    for i,k in enumerate('xyz'):
        row[f'{kind}_{k}']=float(vec[i])
    row[f'{kind}_norm']=float(np.linalg.norm(vec))


def select_faces(items,limit):
    if limit<=0 or limit>=len(items):return items
    ids=np.linspace(0,len(items)-1,limit).astype(int)
    return [items[int(i)] for i in np.unique(ids)]


def write_csv(path,rows):
    if not rows:
        path.write_text('',encoding='utf-8');return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader();w.writerows(rows)


def rms_stats(rows,key):
    a=np.asarray([float(r[key]) for r in rows])
    w=np.asarray([float(r['area_mm2']) for r in rows])
    if np.any(w<=0) or not np.all(np.isfinite(w)):
        raise ValueError('Nonpositive or nonfinite area weights')
    return {'rms':float(np.sqrt(np.average(a*a,weights=w))),
            'mean_abs':float(np.average(np.abs(a),weights=w)),
            'max_abs':float(np.max(np.abs(a)))}


def seam_pairs(material):
    """Identify exactly matching physical CSF domain edges at BOTH endpoints."""
    seams=[]
    edges=[]
    for di in range(len(material.names)):
        for edge in range(4):
            a=np.array([material.vertices[k,di,edge] for k in range(2)])
            b=np.array([material.vertices[k,di,(edge+1)%4] for k in range(2)])
            edges.append((di,edge,a,b))
    for i,(di,edge,a,b) in enumerate(edges):
        for dj,edj,c,d in edges[i+1:]:
            if di==dj:continue
            if np.allclose(a,d,atol=1e-9,rtol=0) and np.allclose(b,c,atol=1e-9,rtol=0):
                seams.append((di,dj,a,b))
            elif np.allclose(a,c,atol=1e-9,rtol=0) and np.allclose(b,d,atol=1e-9,rtol=0):
                raise ValueError('CSF edge shared with equal orientation: inspect polygon topology')
    if not seams:raise ValueError('No common CSF transverse domain edges found')
    return seams


def eval_cuf_seams(field,material,epsilon,nx,ng,point_cap=0):
    seams=seam_pairs(material)
    pts,wts=np.polynomial.legendre.leggauss(ng)
    xnodes=np.linspace(material.x0,material.x1,nx+1)
    result=[]
    for si,(di,dj,edges_a,edges_b) in enumerate(seams,1):
        ci=np.mean(material.vertices[0,di],axis=0)
        cj=np.mean(material.vertices[0,dj],axis=0)
        for ix,(xx0,xx1) in enumerate(zip(xnodes[:-1],xnodes[1:])):
            for xi,wx in zip(pts,wts):
                x=.5*(xx0+xx1)+.5*(xx1-xx0)*xi
                t=(x-material.x0)/(material.x1-material.x0)
                pa=(1-t)*edges_a[0]+t*edges_a[1]
                pb=(1-t)*edges_b[0]+t*edges_b[1]
                dpa=(edges_a[1]-edges_a[0])/(material.x1-material.x0)
                dpb=(edges_b[1]-edges_b[0])/(material.x1-material.x0)
                for v,wv in zip(pts,wts):
                    alpha=.5*(1+v)
                    yz=(1-alpha)*pa+alpha*pb
                    dydx=(1-alpha)*dpa+alpha*dpb
                    pv=np.r_[0.,0.5*(pb-pa)]
                    px=np.r_[0.5*(xx1-xx0),0.5*(xx1-xx0)*dydx]
                    nvec=np.cross(px,pv)
                    area=float(np.linalg.norm(nvec))
                    if area<=0:raise ValueError('Degenerate CSF seam surface')
                    n=nvec/area
                    delta=np.r_[0.,cj-ci]
                    if np.dot(n,delta)<0:n=-n
                    p=np.r_[x,yz]
                    sa,d1=cuf_stress_one_side(field,material,p,-n,epsilon,di)
                    sb,d2=cuf_stress_one_side(field,material,p,+n,epsilon,dj)
                    jump=(sa-sb)@n
                    row={'seam_id':si,'domain_a':material.names[di],
                         'domain_b':material.names[dj],
                         'material_changed':bool(abs(material.E(x,di)-material.E(x,dj))>1e-8),
                         'x':float(x),'x_over_L':float((x-material.x0)/(material.x1-material.x0)),
                         'y':float(yz[0]),'z':float(yz[1]),
                         'area_mm2':float(area*wx*wv)}
                    components(row,'cuf',jump)
                    result.append(row)
                    if point_cap>0 and len(result)>=point_cap:return result,seams
    return result,seams


def selftest(shape):
    """Q8 face maps, normal orientation and geometric conservation for a cube."""
    corners=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
                      [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)
    X=np.array(list(corners)+[(corners[a]+corners[b])/2 for a,b in (
        (0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7))],float)
    for ax,sg,loc in FACES:
        for k,uv in enumerate(CORNERS_UV):
            q,_=face_q(ax,sg,uv)
            xyz,_,area,_=face_geometry(X,ax,sg,uv,shape)
            if np.max(np.abs(xyz-X[loc[k]]))>1e-12:
                raise AssertionError('Incorrect face corner map')
            if abs(area-1)>1e-12:raise AssertionError('Incorrect unit cube face area')
    av=np.zeros(3)
    for ax,sg,loc in FACES:
        p,n,j,q=face_geometry(X,ax,sg,[0,0],shape)
        n=outward_orientation(n,p,np.zeros(3))
        av+=4*j*n
    if np.max(abs(av))>1e-12:
        raise AssertionError('Closed cube surface area vectors do not sum to zero')
    print('PASS: six face maps, area Jacobians and outward normals on a reference cube')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--fem',type=Path)
    ap.add_argument('--cuf',type=Path)
    ap.add_argument('--csf',type=Path)
    ap.add_argument('--output-dir',type=Path,default=Path('diagnostics/h20_cuf_surfaces'))
    ap.add_argument('--load-amplitude',type=float,default=None,
                    help='Required: actual global-z traction amplitude in MPa (benchmark -1)')
    ap.add_argument('--face-gauss',type=int,choices=(2,3),default=2)
    ap.add_argument('--epsilon-mm',type=float,default=1.e-5,
                    help='Physical inward offset for CUF one-sided traction limits')
    ap.add_argument('--sections',type=int,default=40,help='Longitudinal bins for surface RMS graphs')
    ap.add_argument('--no-plots',action='store_true')
    ap.add_argument('--domain-nx',type=int,default=40,
                    help='Axial quadrature intervals for CUF-only L9-domain seams')
    ap.add_argument('--max-faces',type=int,default=0,
                    help='0=all; positive number is per-category diagnostic sample only')
    ap.add_argument('--mesh-jumps',action='store_true',
                    help='Also check H20 internal FEM-element faces (FEM-only, not a matched-domain comparison)')
    ap.add_argument('--compiled-module',type=Path)
    ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    shape,_,Field=core.load_helpers(Path(__file__).resolve().parent,a.compiled_module)
    from h20_strong_residual import stress_at
    selftest(shape)
    if a.self_test:return
    for path in (a.fem,a.cuf,a.csf):
        if path is None or not path.is_file():ap.error('Missing required input --fem, --cuf or --csf')
    if a.load_amplitude is None:ap.error('--load-amplitude is required to verify loaded-surface traction')
    if a.epsilon_mm<=0 or a.domain_nx<=0 or a.sections<=0:ap.error('epsilon, domain-nx and sections must be positive')
    material=core.PhysicalMaterial(a.csf)
    field=Field.load(a.cuf)
    material.verify_geometry(field)
    with np.load(a.fem,allow_pickle=False) as d:
        req=('nodes','elements','displacement','element_E','element_nu','element_region')
        absent=[k for k in req if k not in d]
        if absent:raise ValueError('FEM H20 NPZ missing fields: '+str(absent))
        nodes=np.asarray(d['nodes'],float);conn=np.asarray(d['elements'],int)
        disps=np.asarray(d['displacement'],float);E=np.asarray(d['element_E'],float)
        nu=np.asarray(d['element_nu'],float);regions=np.asarray(d['element_region'],int)
        bottom=np.asarray(d['bottom_faces'],int) if 'bottom_faces' in d else None
        total_nodal_load=float(np.sum(d['nodal_loads'][:,2])) if 'nodal_loads' in d else None
    if conn.ndim!=2 or conn.shape[1]!=20 or nodes.shape!=disps.shape or nodes.shape[1]!=3:
        raise ValueError('Invalid H20 element connectivity/displacement shape')
    if len(E)!=len(conn) or len(nu)!=len(conn) or len(regions)!=len(conn):
        raise ValueError('Element material arrays have wrong length')
    if abs(field.x_start-material.x0)>1e-7 or abs(field.x_end-material.x1)>1e-7:
        raise ValueError('CUF and CSF longitudinal ranges differ')
    if np.min(nodes[:,0])<material.x0-1e-8 or np.max(nodes[:,0])>material.x1+1e-8:
        raise ValueError('H20 x range differs from CSF')
    if not np.allclose(nu,material.nu,rtol=0,atol=1e-12):
        raise ValueError('FEM/CSF Poisson ratios do not match')
    print('[surface]',VERSION,flush=True)
    faces,counts=face_table(conn)
    external=[]; interfaces=[];mesh_interfaces=[]
    for key,owners in faces.items():
        if len(owners)==1:external.append(owners[0])
        elif regions[owners[0][0]]!=regions[owners[1][0]]:interfaces.append(owners)
        else:mesh_interfaces.append(owners)
    print(f'[surface] H20 faces: exterior={len(external)}, material-region={len(interfaces)}, '
          f'other internal={len(mesh_interfaces)}',flush=True)
    # Confirm stored loaded Q8 faces, if present.
    load_faces={tuple(sorted(map(int,row[:4]))) for row in bottom} if bottom is not None else set()
    if bottom is not None and len(load_faces)!=len(bottom):
        raise ValueError('Duplicate bottom Q8 faces in NPZ')
    unknown_bottom=load_faces-set(faces)
    if unknown_bottom:raise ValueError('Bottom Q8 faces missing from H20 face topology')
    nquad=a.face_gauss
    pt,wts=np.polynomial.legendre.leggauss(nquad)
    centers=np.array([shape([0,0,0])[0]@nodes[c] for c in conn])
    external_rows=[];interface_rows=[];mesh_rows=[]
    seen_loaded=set()
    for it,(ei,axis,sign,ids) in enumerate(select_faces(external,a.max_faces),1):
        X=nodes[conn[ei]];U=disps[conn[ei]]
        corners=nodes[np.array(ids[:4])]
        face_key=tuple(sorted(ids[:4]))
        tag=boundary_class(corners.mean(axis=0),corners,material.x0,material.x1,load_faces,face_key)
        if tag=='loaded_bottom':seen_loaded.add(face_key)
        for ui,wu in zip(pt,wts):
            for vi,wv in zip(pt,wts):
                p,n,j,q=face_geometry(X,axis,sign,[ui,vi],shape)
                n=outward_orientation(n,p,centers[ei])
                sf=h20_stress(stress_at,X,U,E[ei],nu[ei],q)
                sc,di=cuf_stress_one_side(field,material,p,-n,a.epsilon_mm)
                tf=sf@n;tc=sc@n
                row={'kind':tag,'fem_element':ei+1,'cuf_domain':material.names[di],
                     'x':float(p[0]),'x_over_L':float((p[0]-material.x0)/(material.x1-material.x0)),
                     'y':float(p[1]),'z':float(p[2]),'area_mm2':float(j*wu*wv),
                     'normal_x':float(n[0]),'normal_y':float(n[1]),'normal_z':float(n[2])}
                components(row,'fem_traction',tf);components(row,'cuf_traction',tc)
                if tag!='supported_end':
                    target=np.array([0.,0.,a.load_amplitude*math.sin(math.pi*(p[0]-material.x0)/(material.x1-material.x0))]) if tag=='loaded_bottom' else np.zeros(3)
                    components(row,'target',target)
                    components(row,'fem_error',tf-target)
                    components(row,'cuf_error',tc-target)
                external_rows.append(row)
        if it%max(1,len(external)//10)==0:
            print(f'[surface] outer faces {it}/{len(external)}',flush=True)
    if a.max_faces==0 and bottom is not None and seen_loaded!=load_faces:
        raise ValueError(f'Loaded surface classification incomplete: {len(seen_loaded)} / {len(load_faces)}')
    if a.max_faces==0 and not seen_loaded:
        raise ValueError('No loaded bottom faces identified: expected traction cannot be checked')

    for it,owners in enumerate(select_faces(interfaces,a.max_faces),1):
        (ia,axa,sga,ida),(ib,axb,sgb,idb)=owners
        X=nodes[conn[ia]];Y=nodes[conn[ib]]
        U=disps[conn[ia]];V=disps[conn[ib]]
        transform=uv_transform(ida,idb)
        for ui,wu in zip(pt,wts):
            for vi,wv in zip(pt,wts):
                uv=np.array([ui,vi]);p,n,j,qa=face_geometry(X,axa,sga,uv,shape)
                n=outward_orientation(n,p,centers[ia])
                pb,nb,jb,qb=face_geometry(Y,axb,sgb,uv@transform,shape)
                if np.linalg.norm(pb-p)>1e-8:
                    raise ValueError(f'H20 material interface mismatch at {ia},{ib}: {pb-p}')
                if np.dot(n,centers[ib]-centers[ia])<=0:
                    raise ValueError('H20 region interface normal not pointing from A to B')
                fa=h20_stress(stress_at,X,U,E[ia],nu[ia],qa)
                fb=h20_stress(stress_at,Y,V,E[ib],nu[ib],qb)
                ca,da=cuf_stress_one_side(field,material,p,-n,a.epsilon_mm)
                cb,db=cuf_stress_one_side(field,material,p,+n,a.epsilon_mm)
                if da==db:
                    raise ValueError(f'Physical material interface maps to same CUF domain {da}')
                ef_a=material.E(.5*(nodes[conn[ia]][:,0].min()+nodes[conn[ia]][:,0].max()),da)
                ef_b=material.E(.5*(nodes[conn[ib]][:,0].min()+nodes[conn[ib]][:,0].max()),db)
                if not np.isclose(E[ia],ef_a,rtol=1e-11,atol=1e-7) or not np.isclose(E[ib],ef_b,rtol=1e-11,atol=1e-7):
                    raise ValueError(f'Material mismatch at interface faces {ia}/{ib}')
                row={'kind':'material_interface','fem_element_a':ia+1,'fem_element_b':ib+1,
                     'region_a':int(regions[ia]),'region_b':int(regions[ib]),
                     'domain_a':material.names[da],'domain_b':material.names[db],
                     'x':float(p[0]),'x_over_L':float((p[0]-material.x0)/(material.x1-material.x0)),
                     'y':float(p[1]),'z':float(p[2]),'area_mm2':float(j*wu*wv),
                     'normal_x':float(n[0]),'normal_y':float(n[1]),'normal_z':float(n[2])}
                components(row,'fem_jump',(fa-fb)@n)
                components(row,'cuf_jump',(ca-cb)@n)
                interface_rows.append(row)
        if it%max(1,len(interfaces)//5)==0:
            print(f'[surface] material interfaces {it}/{len(interfaces)}',flush=True)

    if a.mesh_jumps:
        for ia,ib in select_faces(mesh_interfaces,a.max_faces):
            (ea,axa,sga,ida),(eb,axb,sgb,idb)=(ia,ib)
            X=nodes[conn[ea]];Y=nodes[conn[eb]]
            U=disps[conn[ea]];V=disps[conn[eb]]
            transform=uv_transform(ida,idb)
            for ui,wu in zip(pt,wts):
                for vi,wv in zip(pt,wts):
                    uv=np.array([ui,vi]);p,n,j,qa=face_geometry(X,axa,sga,uv,shape)
                    n=outward_orientation(n,p,centers[ea])
                    pb,_,_,qb=face_geometry(Y,axb,sgb,uv@transform,shape)
                    if np.linalg.norm(pb-p)>1e-8:raise ValueError('H20 mesh face physical mismatch')
                    fa=h20_stress(stress_at,X,U,E[ea],nu[ea],qa)
                    fb=h20_stress(stress_at,Y,V,E[eb],nu[eb],qb)
                    row={'kind':'h20_mesh_face','fem_element_a':ea+1,'fem_element_b':eb+1,
                         'x':float(p[0]),'x_over_L':float((p[0]-material.x0)/(material.x1-material.x0)),
                         'y':float(p[1]),'z':float(p[2]),'area_mm2':float(j*wu*wv)}
                    components(row,'fem_jump',(fa-fb)@n)
                    mesh_rows.append(row)

    seam_rows,seams=eval_cuf_seams(field,material,a.epsilon_mm,a.domain_nx,a.face_gauss)
    # Aggregate surfaces. All values here have units of MPa. No strong-form RMS is added to them.
    summary={'version':VERSION,'input':{'fem':str(a.fem),'cuf':str(a.cuf),'csf':str(a.csf),
              'fem_sha256':core.sha256(a.fem),'cuf_sha256':core.sha256(a.cuf),'csf_sha256':core.sha256(a.csf)},
             'configuration':{'face_gauss_per_direction':nquad,'epsilon_mm':a.epsilon_mm,
                              'load_amplitude_mpa':a.load_amplitude,'domain_nx':a.domain_nx,
                              'max_faces':a.max_faces,'mesh_jumps':a.mesh_jumps},
             'mesh':{'H20_elements':int(len(conn)), 'external_faces':len(external),
                     'material_faces':len(interfaces),'other_internal_faces':len(mesh_interfaces),
                     'bottom_faces_expected':len(load_faces) if bottom is not None else None,
                     'cuf_domain_seams':len(seams)},'groups':{}}
    for group,rows,columns in (
       ('loaded_bottom', [r for r in external_rows if r['kind']=='loaded_bottom'], ('fem_error','cuf_error')),
       ('free_external',[r for r in external_rows if r['kind']=='free_external'], ('fem_error','cuf_error')),
       ('material_interface',interface_rows, ('fem_jump','cuf_jump')),
       ('cuf_domain_interfaces',seam_rows,('cuf',)),
       ('h20_mesh_interfaces',mesh_rows,('fem_jump',)),
       ('supported_end',[r for r in external_rows if r['kind']=='supported_end'], ('fem_traction','cuf_traction')),
    ):
        if not rows:continue
        rec={'points':len(rows),'area_mm2':float(sum(r['area_mm2'] for r in rows)),
             'units':'MPa','metric':'surface-area-weighted RMS of traction vector error/jump',
             'values':{}}
        for col in columns:
            rec['values'][col]={k:rms_stats(rows,f'{col}_{k}') for k in ('x','y','z','norm')}
        if len(columns)==2 and group!='supported_end':
            f=rec['values'][columns[0]]['norm']['rms']
            c=rec['values'][columns[1]]['norm']['rms']
            rec['cuf_over_fem']=c/f if f else None
            rec['cuf_reduction_percent']=100*(1-c/f) if f else None
        if group in ('loaded_bottom','free_external','supported_end'):
            rec['resultant_N']={col:[float(sum(r['area_mm2']*r[f'{col}_{k}'] for r in rows)) for k in 'xyz']
                                for col in columns}
            if group=='loaded_bottom':
                rec['resultant_target_N']=[float(sum(r['area_mm2']*r[f'target_{k}'] for r in rows)) for k in 'xyz']
        summary['groups'][group]=rec
    summary['checks']={'bottom_resultant_from_npz_N':total_nodal_load,
                       'bottom_resultant_from_surface_quadrature_N':summary['groups'].get('loaded_bottom',{}).get('resultant_target_N'),
                       'CUF_9_domain_interfaces_are_separate_from_FEM_3_region_interfaces':True,
                       'supported_end_faces_are_NOT_treated_as_traction_free':True}
    if total_nodal_load is not None and a.max_faces==0:
        estimated=summary['groups']['loaded_bottom']['resultant_target_N'][2]
        # Quadrature approximates the sine load, but error should be small with 2+2.
        rel=abs(estimated-total_nodal_load)/max(1.,abs(total_nodal_load))
        summary['checks']['load_resultant_relative_difference']=rel
        if rel>1e-3:
            raise ValueError(f'Expected load surface integral inconsistent with NPZ nodal loads: relative={rel:.3g}')
    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'external_surface_points.csv',external_rows)
    write_csv(out/'material_interface_points.csv',interface_rows)
    write_csv(out/'cuf_domain_interface_points.csv',seam_rows)
    if a.mesh_jumps:write_csv(out/'h20_mesh_interface_points.csv',mesh_rows)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    # Every surface quadrature sample belongs to exactly one axial bin.
    surface_sections=[]
    for gname,rows,ka,kb in (
        ('loaded_bottom',[r for r in external_rows if r['kind']=='loaded_bottom'],'fem_error','cuf_error'),
        ('free_external',[r for r in external_rows if r['kind']=='free_external'],'fem_error','cuf_error'),
        ('material_interface',interface_rows,'fem_jump','cuf_jump'),
        ('cuf_domain_interfaces',seam_rows,None,'cuf'),
    ):
        if not rows:continue
        groups=[[] for _ in range(a.sections)]
        for r in rows:
            x=float(r['x_over_L'])
            if x < -1e-10 or x > 1.0+1e-10:raise ValueError('Surface point outside longitudinal domain')
            idx=min(max(math.floor(x*a.sections),0),a.sections-1)
            groups[idx].append(r)
        if sum(len(g) for g in groups)!=len(rows):raise RuntimeError('Surface binning duplicated or lost points')
        for j,rr in enumerate(groups):
            if not rr:continue
            rec={'group':gname,'section':j+1,'x_over_L_mid':(j+.5)/a.sections,
                 'points':len(rr),'area_mm2':float(sum(r['area_mm2'] for r in rr))}
            if ka:rec['fem_rms_mpa']=rms_stats(rr,f'{ka}_norm')['rms']
            rec['cuf_rms_mpa']=rms_stats(rr,f'{kb}_norm')['rms']
            surface_sections.append(rec)
    write_csv(out/'surface_sections.csv',surface_sections)
    if not a.no_plots:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            for name in ('loaded_bottom','free_external','material_interface','cuf_domain_interfaces'):
                ss=sorted((r for r in surface_sections if r['group']==name),key=lambda r:r['section'])
                if not ss:continue
                fig,ax=plt.subplots(figsize=(8,4))
                xx=[r['x_over_L_mid'] for r in ss]
                if 'fem_rms_mpa' in ss[0]:
                    ax.plot(xx,[r['fem_rms_mpa'] for r in ss],label='FEM3D H20',marker='.',linewidth=1.4)
                ax.plot(xx,[r['cuf_rms_mpa'] for r in ss],label='CSF-CUF L9',marker='.',linewidth=1.4)
                ax.set(xlabel='x/L',ylabel='Surface-area weighted RMS traction error (MPa)',title=name.replace('_',' ').title())
                ax.grid(alpha=.25);ax.legend();fig.tight_layout()
                fig.savefig(out/f'{name}_rms_vs_x.png',dpi=160)
                plt.close(fig)
        except ImportError:
            print('Matplotlib not available, numerical files still produced',flush=True)
    lines=['# FEM3D H20 vs CSF-CUF: traction and interface equilibrium','',
          'All quantities are evaluated on the same *physical surface quadrature points*',
          'for the matched H20 boundary and material interfaces. Units: traction MPa, area mm².',
          'Normals are the outward FEM face normals in global coordinates (x,y,z).','',
          '| Surface class | Points | FEM RMS (MPa) | CUF RMS (MPa) | CUF reduction |',
          '|---|---:|---:|---:|---:|']
    for group in ('loaded_bottom','free_external','material_interface'):
        if group not in summary['groups']:continue
        g=summary['groups'][group]
        names={'loaded_bottom':('fem_error','cuf_error'),
               'free_external':('fem_error','cuf_error'),
               'material_interface':('fem_jump','cuf_jump')}[group]
        f=g['values'][names[0]]['norm']['rms'];c=g['values'][names[1]]['norm']['rms']
        lines.append(f'| {group} | {g["points"]} | {f:.9g} | {c:.9g} | {g["cuf_reduction_percent"]:+.3f}% |')
    lines+=['', '## Variation along the beam', '',
            'Each physical surface point belongs to exactly one of the requested longitudinal bins.',
            'The plots below show the RMS by axial interval (not stress on a flat cross-sectional cut).',
            '', '![Loaded surface](loaded_bottom_rms_vs_x.png)',
            '![Free external surface](free_external_rms_vs_x.png)',
            '![Physical material interfaces](material_interface_rms_vs_x.png)',
            '![Extra CUF domain seams](cuf_domain_interfaces_rms_vs_x.png)',
            '', '**Different diagnostics, not directly rankable:**']
    for group in ('cuf_domain_interfaces','h20_mesh_interfaces'):
        if group in summary['groups']:
            g=summary['groups'][group]
            col='cuf' if group.startswith('cuf') else 'fem_jump'
            lines.append(f'- {group}: {g["points"]} samples, RMS jump={g["values"][col]["norm"]["rms"]:.9g} MPa (single-model diagnostic).')
    lines+=['','**Supported end faces:** no zero-traction error is assigned because transverse reactions are allowed.',
            '',f'External faces {len(external)}; true FEM region interfaces {len(interfaces)};',
            f'CUF domain edges {len(seams)} (including same-material L9 subdivisions).',
            '',f'FEM file SHA256: `{summary["input"]["fem_sha256"]}`',
            f'CUF file SHA256: `{summary["input"]["cuf_sha256"]}`',
            f'CSF YAML SHA256: `{summary["input"]["csf_sha256"]}`',
            '', '## Scope', '',
            '- This checks boundary and interface tractions, **not** interior stress divergence.',
            '- A positive reduction means lower CUF area-weighted RMS only in that surface class.',
            '- H20 has three physical regions; CUF has nine L9 domains. Extra same-material CUF seams are reported separately.',
            '- The CUF one-sided stress is evaluated epsilon inside each domain. Check epsilon sensitivity before publication.',
            '- H20 E is constant per element; CUF E varies continuously in x.',
            '- For material interfaces, FEM and CUF are sampled on exactly the same H20 surfaces; no extrapolation of FEM stress between elements.',
            '- At the supported ends, the unknown reaction tractions cannot be prescribed as zero.',
            '- Do not combine surface RMS (MPa) with interior equilibrium RMS (MPa/mm).',
            '']
    (out/'summary.md').write_text('\n'.join(lines),encoding='utf-8')
    print('\n'.join(lines[:17]),flush=True)
    print('[surface] saved',out/'summary.md',flush=True)

if __name__=='__main__':
    main()
