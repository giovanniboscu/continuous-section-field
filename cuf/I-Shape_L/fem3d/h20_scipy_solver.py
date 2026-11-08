#!/usr/bin/env python3
"""Independent sparse linear-elastic H20 implementation (verification backend).

Full 3x3x3 Gauss integration, engineering-shear Voigt convention.
Requires scipy. Intended for small and medium meshes; very fine production
meshes may need more memory than OpenSees sparse direct solvers.
"""
from __future__ import annotations
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from run_bending_fem3d_h20 import h20_shape
import run_bending_fem3d_v2 as base


def material_C(E,nu):
    G=E/(2*(1+nu));la=E*nu/((1+nu)*(1-2*nu))
    D=np.zeros((6,6),float)
    D[:3,:3]=la
    D[0,0]+=2*G;D[1,1]+=2*G;D[2,2]+=2*G
    D[3,3]=D[4,4]=D[5,5]=G
    return D


def B_matrix(grad):
    B=np.zeros((6,60),float)
    B[0,0::3]=grad[:,0];B[1,1::3]=grad[:,1];B[2,2::3]=grad[:,2]
    B[3,1::3]=grad[:,2];B[3,2::3]=grad[:,1]
    B[4,0::3]=grad[:,2];B[4,2::3]=grad[:,0]
    B[5,0::3]=grad[:,1];B[5,1::3]=grad[:,0]
    return B


def solve_scipy_h20(mesh,E,nu,loads,x0,x1):
    g,w=np.polynomial.legendre.leggauss(3)
    gps=[]
    for i,r in enumerate(g):
        for j,s in enumerate(g):
            for k,t in enumerate(g):
                _,D=h20_shape((r,s,t));gps.append((D,float(w[i]*w[j]*w[k])))
    nn=len(mesh.nodes)
    ne=len(mesh.elements)
    row=np.empty(ne*3600,dtype=np.int32)
    col=np.empty(ne*3600,dtype=np.int32)
    val=np.empty(ne*3600,dtype=float)
    mat_cache={}
    offset=0
    for eid,conn in enumerate(mesh.elements):
        X=mesh.nodes[conn]
        key=(float(E[eid]),float(nu[eid]))
        if key not in mat_cache:mat_cache[key]=material_C(*key)
        C=mat_cache[key]
        Ke=np.zeros((60,60),float)
        for D,wgt in gps:
            J=X.T@D
            det=float(np.linalg.det(J))
            if det<=0:raise ValueError(f'Negative H20 Jacobian eid {eid}: {det}')
            grad=D@np.linalg.inv(J)
            B=B_matrix(grad)
            Ke+=wgt*det*(B.T@C@B)
        dofs=(3*conn[:,None]+np.arange(3)).reshape(-1).astype(np.int32)
        sz=60*60
        row[offset:offset+sz]=np.repeat(dofs,60)
        col[offset:offset+sz]=np.tile(dofs,60)
        val[offset:offset+sz]=Ke.ravel()
        offset+=sz
        if eid%1000==0 and eid:
            print(f'SciPy assemble {eid}/{ne}',flush=True)
    K=coo_matrix((val,(row,col)),shape=(nn*3,nn*3)).tocsr()
    del row,col,val
    K.sum_duplicates()
    centerline=base._centerline_nodes(mesh)
    gauge=int(centerline[np.argmin(abs(mesh.nodes[centerline,0]-(x0+x1)/2))])
    support=np.unique(np.r_[mesh.end0_nodes,mesh.end1_nodes])
    fixed=np.unique(np.r_[3*support+1,3*support+2,3*gauge]).astype(np.int32)
    mask=np.ones(nn*3,dtype=bool);mask[fixed]=False
    free=np.flatnonzero(mask)
    F=loads.ravel()
    A=K[free][:,free].tocsc()
    u=np.zeros(nn*3)
    u[free]=spsolve(A,F[free])
    residual=(K@u-F)[free]
    rel=float(np.linalg.norm(residual,np.inf)/max(1.,np.linalg.norm(F,np.inf)))
    if rel>1e-7:raise RuntimeError(f'Linear solver residual too high: {rel}')
    reaction=K@u-F
    disp=u.reshape((-1,3))
    shift=base._axial_gauge_mean(mesh,disp,centerline)
    disp[:,0]-=shift
    axial_res=base._axial_gauge_mean(mesh,disp,centerline)
    print(f'SciPy residual_inf={rel:.5e} support_reaction_z={reaction[3*support+2].sum():.12g}',flush=True)
    return disp,np.full(ne,-1,int),gauge,centerline,shift,axial_res,'scipy-spsolve'
