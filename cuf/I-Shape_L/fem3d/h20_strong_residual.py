#!/usr/bin/env python3
"""Independent volume-weighted interior strong equilibrium for 20NodeBrick.

Computes stress derivatives by CENTRAL DIFFERENCES IN PARENT COORDINATES,
then transforms to physical coordinates with the local isoparametric Jacobian.
This does NOT use OpenSees stress recovery and does NOT use the CUF evaluator.
It measures element interiors only; interface traction jumps are separate.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from run_bending_fem3d_h20 import h20_shape


def stress_at(X, U, E, nu, q):
    _,D = h20_shape(q)
    J = X.T @ D
    det = np.linalg.det(J)
    if det <= 0:
        raise ValueError(f'Non-positive Jacobian at q={q}: {det}')
    g = U.T @ D @ np.linalg.inv(J)  # g[i,j]=du_i/dx_j
    G=E/(2*(1+nu));lam=E*nu/((1+nu)*(1-2*nu))
    tr=np.trace(g)
    eps=np.array([g[0,0],g[1,1],g[2,2],g[1,2]+g[2,1],
                  g[0,2]+g[2,0],g[0,1]+g[1,0]])
    return np.array([lam*tr+2*G*eps[0],lam*tr+2*G*eps[1],
                     lam*tr+2*G*eps[2],G*eps[3],G*eps[4],G*eps[5]]),J,det


def residual_at(X, U, E, nu, q, dh=1e-4):
    sig,J,det=stress_at(X,U,E,nu,q)
    ds_dq=np.zeros((6,3))
    for a in range(3):
        qp=np.asarray(q,float).copy();qm=qp.copy()
        qp[a]+=dh;qm[a]-=dh
        sp,_,_=stress_at(X,U,E,nu,qp)
        sm,_,_=stress_at(X,U,E,nu,qm)
        ds_dq[:,a]=(sp-sm)/(2*dh)
    ds_dx=ds_dq @ np.linalg.inv(J)
    r=np.array([ds_dx[0,0]+ds_dx[5,1]+ds_dx[4,2],
                ds_dx[5,0]+ds_dx[1,1]+ds_dx[3,2],
                ds_dx[4,0]+ds_dx[3,1]+ds_dx[2,2]])
    return r,det,ds_dx


def sample_ids(regions, max_elements):
    n=len(regions)
    if max_elements<=0 or max_elements>=n:
        return np.arange(n), 1.
    # Uniform coverage in element-index space, including every physical domain.
    selected=[]
    for region in np.unique(regions):
        ids=np.flatnonzero(regions==region)
        count=max(1,round(max_elements*len(ids)/n))
        if count>=len(ids):selected.extend(ids)
        else:selected.extend(ids[np.linspace(0,len(ids)-1,count).astype(int)])
    return np.array(sorted(set(selected))),len(selected)/n


def weighted_median(a,w):
    ids=np.argsort(a)
    return float(a[ids[np.searchsorted(np.cumsum(w[ids]),sum(w)/2)]])


def measure(path, max_elements=300, dh=1e-4, gauss=2):
    with np.load(path,allow_pickle=False) as d:
        if d['elements'].shape[1]!=20:raise ValueError('Expected 20-node connectivity')
        nodes=d['nodes'];conn=d['elements'];U=d['displacement']
        E=d['element_E'];nu=d['element_nu'];regions=d['element_region']
    if U.shape!=nodes.shape:
        raise ValueError('Missing solved H20 displacement (mesh-only archive?)')
    ids,fraction=sample_ids(regions,max_elements)
    qvals,qweights=np.polynomial.legendre.leggauss(gauss)
    rs=[];ws=[]
    for i in ids:
        X=nodes[conn[i]];ue=U[conn[i]]
        for ir,r in enumerate(qvals):
            for js,s in enumerate(qvals):
                for kt,t in enumerate(qvals):
                    v,det,_=residual_at(X,ue,float(E[i]),float(nu[i]),(r,s,t),dh=dh)
                    rs.append(v);ws.append(det*qweights[ir]*qweights[js]*qweights[kt])
    R=np.asarray(rs,float);W=np.asarray(ws,float)
    norms=np.linalg.norm(R,axis=1)
    columns=['x','y','z','norm']
    metrics={}
    for k,a in enumerate((R[:,0],R[:,1],R[:,2],norms)):
        metrics[columns[k]]={'rms':float(np.sqrt(np.average(a*a,weights=W))),
                             'median_abs':weighted_median(abs(a),W),
                             'max_abs':float(np.max(abs(a)))}
    return {'file':str(path),'elements_total':len(conn),'elements_sampled':len(ids),
            'gauss':gauss,'diff_parent_step':dh,'sampling_fraction':fraction,
            'units':'MPa/mm (N/mm^3)','volume_weighted':True,
            'metrics':metrics}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('npz',type=Path)
    ap.add_argument('--max-elements',type=int,default=300,
                    help='0 means ALL elements (expensive)')
    ap.add_argument('--gauss',type=int,default=1,choices=(1,2,3))
    ap.add_argument('--step',type=float,default=1e-4)
    ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    result=measure(a.npz,a.max_elements,a.step,a.gauss)
    print(json.dumps(result,indent=2))
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
