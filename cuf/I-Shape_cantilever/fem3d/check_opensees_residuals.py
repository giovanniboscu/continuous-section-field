# Version: CSF-CUF OpenSees H8 equilibrium residuals v01 - 2026-11-20
"""Independent, read-only residual audit of the CSF-driven OpenSees H8 NPZ.

No OpenSees restart and no CSF/YAML parsing. Reconstructs, from the exact
exported solid mesh, element materials, displacements and applied loads:
  - discrete free-node balance f_int - f_ext and fixed-node reaction errors;
  - strong element-interior div(sigma), using exact isoparametric derivatives;
  - facewise external traction errors and internal interface traction jumps.

Physical coordinates/components always follow CUF/OpenSees (x,y,z)=(Z,X,Y)_CSF.
No stresses are smoothed, averaged across material sides, or extrapolated.
Face metrics use 2x2 surface Gauss integration, volume metrics 2x2x2.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

SIGNS = np.array([
    (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
    (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),
], dtype=float)
FACES = np.array([
    (0,1,2,3),(4,5,6,7),(0,1,5,4),
    (1,2,6,5),(2,3,7,6),(3,0,4,7),
], dtype=int)
G = 1.0 / np.sqrt(3.0)
GAUSS2 = ((-G,-G),(-G,G),(G,-G),(G,G))
GAUSS3 = [(a,b,c) for a in (-G,G) for b in (-G,G) for c in (-G,G)]


def _shape_derivs(q, second=False):
    """N derivatives in element natural coordinates; optional exact Hessian."""
    q = np.asarray(q, dtype=float)
    factors = 1.0 + SIGNS*q
    d = np.empty((8,3), dtype=float)
    for k in range(3):
        j,l = [i for i in range(3) if i != k]
        d[:,k] = SIGNS[:,k] * factors[:,j] * factors[:,l] * 0.125
    if not second:
        return d
    h = np.zeros((8,3,3), dtype=float)
    for j in range(3):
        for k in range(3):
            if j != k:
                l = 3-j-k
                h[:,j,k] = SIGNS[:,j]*SIGNS[:,k]*factors[:,l]*0.125
    return d, h


def _surface_shape(a, b):
    n = 0.25*np.array(((1-a)*(1-b),(1+a)*(1-b),
                       (1+a)*(1+b),(1-a)*(1+b)),dtype=float)
    da = 0.25*np.array((-(1-b),(1-b),(1+b),-(1+b)),dtype=float)
    db = 0.25*np.array((-(1-a),-(1+a),(1+a),(1-a)),dtype=float)
    return n,da,db


def _material_lambda(E, Gv, nu):
    if (np.any(E<=0) or np.any(Gv<=0) or np.any(nu<=-1)
            or np.any(nu>=0.5)):
        raise ValueError('Nonphysical E, G or Poisson ratio')
    if not np.allclose(Gv, E/(2*(1+nu)), rtol=1e-9, atol=1e-8):
        raise ValueError('NPZ material parameters violate isotropic G=E/(2*(1+nu))')
    return E*nu/((1+nu)*(1-2*nu))


def _stress_batch(X, U, lam, shear, q):
    """One-sided exact H8 stress at natural q, one q per element."""
    q=np.asarray(q,dtype=float)
    fact=1 + SIGNS[None,:,:]*q[:,None,:]
    d=np.empty((len(X),8,3),dtype=float)
    for k in range(3):
        j,l=[t for t in range(3) if t!=k]
        d[:,:,k]=SIGNS[None,:,k]*fact[:,:,j]*fact[:,:,l]*0.125
    J=np.einsum('eij,eik->ejk',X,d)
    determinant=np.linalg.det(J)
    if np.any(~np.isfinite(determinant) | (determinant<=0)):
        raise ValueError('Nonpositive H8 Jacobian at face sample')
    invJ=np.linalg.inv(J)
    gN=np.einsum('eik,ekj->eij',d,invJ)
    du=np.einsum('eic,eij->ecj',U,gN)
    sig=shear[:,None,None]*(du+du.transpose(0,2,1))
    tr=np.trace(du,axis1=1,axis2=2)
    for j in range(3):
        sig[:,j,j]+=lam*tr
    return sig


def _volumetric_batch(X,U,lam,shear):
    """Return element f_int, volume and exact Gauss-weighted RMS div sigma."""
    m=len(X)
    fint=np.zeros((m,8,3),dtype=float)
    vol=np.zeros(m,dtype=float)
    div_sq=np.zeros((m,3),dtype=float)
    for q in GAUSS3:
        d,h=_shape_derivs(q,second=True)
        J=np.einsum('eij,ik->ejk',X,d)
        det=np.linalg.det(J)
        if np.any(~np.isfinite(det)|(det<=0)):
            raise ValueError('Nonpositive H8 Jacobian at volume Gauss point')
        invJ=np.linalg.inv(J)
        grad=np.einsum('ik,ekj->eij',d,invJ)
        du=np.einsum('eic,eij->ecj',U,grad)
        sig=shear[:,None,None]*(du+du.transpose(0,2,1))
        tr=np.trace(du,axis1=1,axis2=2)
        for j in range(3):
            sig[:,j,j]+=lam*tr
        fint+=np.einsum('eij,ecj->eic',grad,sig)*det[:,None,None]
        div=np.zeros((m,3),dtype=float)
        for a in range(3):
            dJ=np.einsum('eij,ik->ejk',X,h[:,:,a])
            dInv=-np.matmul(np.matmul(invJ,dJ),invJ)
            dGrad=(np.einsum('ik,ekj->eij',h[:,:,a],invJ)
                   +np.einsum('ik,ekj->eij',d,dInv))
            dDu=np.einsum('eic,eij->ecj',U,dGrad)
            dSig=shear[:,None,None]*(dDu+dDu.transpose(0,2,1))
            dTr=np.trace(dDu,axis1=1,axis2=2)
            for j in range(3):
                dSig[:,j,j]+=lam*dTr
            div+=np.einsum('eij,ej->ei',dSig,invJ[:,a,:])
        div_sq+=div*div*det[:,None]
        vol+=det
    return fint,vol,np.sqrt(div_sq/vol[:,None])


def _read_npz(path):
    required={'nodes','elements','displacement','element_E','element_G','element_nu',
              'nodal_loads','end0_nodes','support_reactions',
              'loaded_faces','loaded_face_pz'}
    with np.load(path,allow_pickle=False) as f:
        missing=required-set(f.files)
        if missing:
            raise ValueError('NPZ missing residual-analysis data: '+', '.join(sorted(missing)))
        status=str(np.asarray(f['status']).item()) if 'status' in f else ''
        if status!='solved_opensees':
            raise ValueError("Expected solved OpenSees NPZ status='solved_opensees', found "+repr(status))
        data={key:np.asarray(f[key]).copy() for key in required}
        data['element_region']=np.asarray(f['element_region']) if 'element_region' in f else np.zeros(len(data['elements']),dtype=int)
        data['x0']=float(np.asarray(f['x0']).item()) if 'x0' in f else float(data['nodes'][:,0].min())
    n=len(data['nodes']); ne=len(data['elements'])
    for key in ('nodes','displacement','nodal_loads'):
        if data[key].shape!=(n,3) or not np.isfinite(data[key]).all():
            raise ValueError(f'{key} must be finite ({n},3)')
    conn=data['elements']
    if (conn.shape!=(ne,8) or not np.issubdtype(conn.dtype,np.integer)
            or conn.min()<0 or conn.max()>=n):
        raise ValueError('elements must be zero-based integer H8 connectivity')
    for key in ('element_E','element_G','element_nu','element_region'):
        if data[key].shape!=(ne,) or not np.isfinite(data[key]).all():
            raise ValueError(f'{key} must be finite ({ne},)')
    fixed=data['end0_nodes']
    if (fixed.ndim!=1 or not np.issubdtype(fixed.dtype,np.integer)
            or (len(fixed)>0 and (fixed.min()<0 or fixed.max()>=n))
            or len(set(map(int,fixed)))!=len(fixed)):
        raise ValueError('end0_nodes contains invalid node ids')
    if data['support_reactions'].shape!=(len(fixed),3):
        raise ValueError('support_reactions count does not match end0_nodes')
    if not np.isfinite(data['support_reactions']).all():
        raise ValueError('Nonfinite support reactions')
    lf=data['loaded_faces']
    if lf.ndim!=2 or lf.shape[1]!=4 or not np.issubdtype(lf.dtype,np.integer):
        raise ValueError('loaded_faces must be 4-node integer faces')
    if lf.size and (lf.min()<0 or lf.max()>=n):
        raise ValueError('Invalid loaded face nodes')
    if data['loaded_face_pz'].shape!=(len(lf),):
        raise ValueError('loaded_face_pz does not match loaded_faces')
    _material_lambda(data['element_E'],data['element_G'],data['element_nu'])
    return data


def _volume_and_nodal(data, batch, out):
    coords,disp,conn=data['nodes'],data['displacement'],data['elements']
    n,ne=len(coords),len(conn)
    fint=np.zeros((n,3),dtype=float)
    region=data['element_region']
    lam=_material_lambda(data['element_E'],data['element_G'],data['element_nu'])
    vol=np.zeros(ne,dtype=float)
    divrms=np.zeros((ne,3),dtype=float)
    for start in range(0,ne,batch):
        end=min(start+batch,ne)
        ids=conn[start:end]
        fint_e,vol_e,div_e=_volumetric_batch(coords[ids],disp[ids],
                lam[start:end],data['element_G'][start:end])
        np.add.at(fint,ids.ravel(),fint_e.reshape(-1,3))
        vol[start:end]=vol_e
        divrms[start:end]=div_e
    ext=data['nodal_loads']; resid=fint-ext
    fixed=data['end0_nodes']; free_mask=np.ones(n,dtype=bool); free_mask[fixed]=False
    reaction=data['support_reactions']; reaction_err=resid[fixed]-reaction
    x=data['nodes'][:,0]
    rows=({'node_id':i+1,'x':float(x[i]),'constrained':int(not free_mask[i]),
           'residual_x_N':resid[i,0],'residual_y_N':resid[i,1],
           'residual_z_N':resid[i,2],
           'residual_norm_N':float(np.linalg.norm(resid[i]))} for i in range(n))
    _write_csv(out/'nodal_equilibrium.csv',rows)
    centers=data['nodes'][conn].mean(axis=1)
    erows=({'element_id':i+1,'domain_index':int(region[i]),'x':float(centers[i,0]),
            'volume':vol[i], 'div_x_N_mm3':divrms[i,0], 'div_y_N_mm3':divrms[i,1],
            'div_z_N_mm3':divrms[i,2],
            'div_norm_N_mm3':float(np.linalg.norm(divrms[i]))}
            for i in range(ne))
    _write_csv(out/'volume_equilibrium.csv',erows)
    xbins=np.unique(x)
    nodal_profile=[]
    for xi in xbins:
        at=(x==xi) & free_mask
        if not np.any(at): continue
        v=resid[at]
        nodal_profile.append([float(xi),*(np.sqrt(np.mean(v*v,axis=0)).tolist()),
                             float(np.sqrt(np.mean(np.sum(v*v,axis=1))))])
    el_x=np.unique(centers[:,0])
    vol_profile=[]
    for xi in el_x:
        at=centers[:,0]==xi
        sq=divrms[at]**2
        v=vol[at]
        mean=np.sqrt(np.sum(sq*v[:,None],axis=0)/np.sum(v))
        vol_profile.append([float(xi),*mean.tolist(),float(np.linalg.norm(mean))])
    reaction_force=reaction.sum(axis=0)
    total_force=ext.sum(axis=0)
    total_moment=np.cross(coords,ext).sum(axis=0)
    reaction_moment=np.cross(coords[fixed],reaction).sum(axis=0)
    free_r=resid[free_mask]
    energy=0.5*np.sum(disp*fint)
    work=np.sum(disp*ext)
    summary={
      'nodes':n,'elements':ne, 'fixed_nodes':int(len(fixed)),
      'free_dofs':int(3*free_mask.sum()),
      'nodal_free_l2_N':float(np.linalg.norm(free_r)),
      'nodal_free_max_abs_N':float(np.abs(free_r).max()) if free_r.size else None,
      'nodal_free_relative_l2':float(np.linalg.norm(free_r)/max(np.linalg.norm(ext[free_mask]),1e-300)),
      'reaction_difference_l2_N':float(np.linalg.norm(reaction_err)),
      'reaction_difference_max_abs_N':float(np.abs(reaction_err).max()) if reaction_err.size else None,
      'total_applied_force_N':total_force.tolist(),
      'total_support_reaction_N':reaction_force.tolist(),
      'total_force_balance_N':(total_force+reaction_force).tolist(),
      'total_applied_moment_Nmm':total_moment.tolist(),
      'total_reaction_moment_Nmm':reaction_moment.tolist(),
      'total_moment_balance_Nmm':(total_moment+reaction_moment).tolist(),
      'strain_energy_Nmm':float(energy),
      'external_work_Nmm':float(work),
      'volume_divergence_rms_N_mm3':np.sqrt(np.sum(vol[:,None]*divrms**2,axis=0)/vol.sum()).tolist(),
      'volume_divergence_l2_N_mm3_sqrt_mm3':float(np.sqrt(np.sum(vol[:,None]*divrms**2))),
      'volume_mm3':float(vol.sum()),
    }
    return summary,np.asarray(nodal_profile),np.asarray(vol_profile)


def _face_adjacency(conn):
    found={}
    for ei,c in enumerate(conn):
        for fi,local in enumerate(FACES):
            key=tuple(sorted(int(c[i]) for i in local))
            if key in found:
                prev=found[key]
                if len(prev)>=2:
                    raise ValueError('Nonmanifold H8 face shared by >2 elements: '+repr(key))
                prev.append((ei,fi))
            else:
                found[key]=[(ei,fi)]
    return found


def _faces(data,out,batch):
    coords,disp,conn=data['nodes'],data['displacement'],data['elements']
    lam=_material_lambda(data['element_E'],data['element_G'],data['element_nu'])
    shear=data['element_G']; region=data['element_region']
    adjacency=_face_adjacency(conn)
    loaded={}
    for face,p in zip(data['loaded_faces'],data['loaded_face_pz']):
        key=tuple(sorted(map(int,face)))
        if key in loaded:
            raise ValueError('Loaded face listed more than once')
        loaded[key]=float(p)
    fixed=set(map(int,data['end0_nodes']))
    # Records: [e_first, face_first, e_second, face_second, loaded_p, category]
    entries=[]; fixed_count=0; loaded_count=0
    for key,sides in adjacency.items():
        if len(sides)==2:
            if key in loaded:
                raise ValueError('Loaded face is an internal interface')
            entries.append((sides[0][0],sides[0][1],sides[1][0],sides[1][1],0.0,'interface'))
        elif len(sides)==1:
            if all(node in fixed for node in key):
                if key in loaded:
                    raise ValueError('Loaded face is prescribed clamped face')
                fixed_count+=1; continue
            e,fi=sides[0]; load=key in loaded
            entries.append((e,fi,-1,-1,loaded[key] if load else 0.0,
                            'loaded' if load else 'free'))
            loaded_count+=int(load)
    if loaded_count!=len(loaded):
        raise ValueError('Some declared loaded_faces do not match exterior H8 faces')
    entries.sort(key=lambda x:(x[5],x[0],x[1]))
    # stream CSV, retaining each face and original one-sided stresses
    path=out/'surface_traction_residuals.csv'
    fields=('kind','element_id','neighbor_element_id','domain_index','neighbor_domain_index',
            'x','y','z','area_mm2','normal_x','normal_y','normal_z','pressure_N_mm2',
            'mean_residual_x_N_mm2','mean_residual_y_N_mm2','mean_residual_z_N_mm2',
            'rms_residual_x_N_mm2','rms_residual_y_N_mm2','rms_residual_z_N_mm2',
            'rms_residual_norm_N_mm2','residual_max_N_mm2')
    summary_by_kind={kind:{'faces':0,'area_mm2':0.0,'sum_r2_area':np.zeros(3),
                           'sum_rnorm2_area':0.0,'max_sample_residual_N_mm2':0.0}
                     for kind in ('loaded','free','interface')}
    profile_acc=defaultdict(lambda:[0.0,np.zeros(3)])
    profile_free_y=defaultdict(lambda:[0.0,0.0])
    with path.open('w',newline='',encoding='utf8') as fp:
        writer=csv.DictWriter(fp,fieldnames=fields);writer.writeheader()
        for start in range(0,len(entries),batch):
            e=entries[start:start+batch]; m=len(e)
            es=np.array([i[0] for i in e],dtype=int)
            fi=np.array([i[1] for i in e],dtype=int)
            e2=np.array([i[2] for i in e],dtype=int)
            kinds=[i[5] for i in e]
            face_local=FACES[fi]  # [m,4] indices inside first element
            gids=np.take_along_axis(conn[es],face_local,axis=1)
            fx=coords[gids]
            facecent=fx.mean(axis=1)
            ec=coords[conn[es]].mean(axis=1)
            X=coords[conn[es]];U=disp[conn[es]]
            side2=np.flatnonzero(e2>=0)
            e2_local=np.empty((len(side2),4),dtype=int)
            if len(side2):
                second_conn=conn[e2[side2]]
                for pos in range(4):
                    matches=second_conn==gids[side2,pos,None]
                    if not np.all(matches.sum(axis=1)==1):
                        raise ValueError('Shared H8 face node not found in adjacent cell')
                    e2_local[:,pos]=np.argmax(matches,axis=1)
            areas=np.zeros(m); totals=np.zeros((m,3)); means=np.zeros((m,3)); maxima=np.zeros(m)
            normavg=np.zeros((m,3))
            for a,b in GAUSS2:
                n,da,db=_surface_shape(a,b)
                cross=np.cross(np.einsum('i,mij->mj',da,fx),
                               np.einsum('i,mij->mj',db,fx))
                area_factor=np.linalg.norm(cross,axis=1)
                if np.any(area_factor<=0):
                    raise ValueError('Degenerate H8 surface at quadrature point')
                flip=np.where(np.einsum('mi,mi->m',cross,facecent-ec)>0,1.0,-1.0)
                outward=cross*flip[:,None]/area_factor[:,None]
                q1=np.einsum('i,mij->mj',n,SIGNS[face_local])
                s1=_stress_batch(X,U,lam[es],shear[es],q1)
                traction=np.einsum('mij,mj->mi',s1,outward)
                if len(side2):
                    q2=np.einsum('i,mij->mj',n,SIGNS[e2_local])
                    s2=_stress_batch(coords[conn[e2[side2]]],disp[conn[e2[side2]]],
                                     lam[e2[side2]],shear[e2[side2]],q2)
                    traction[side2]-=np.einsum('mij,mj->mi',s2,outward[side2])
                p=np.array([k[4] for k in e],dtype=float)
                # The adapter's projected XY law: t = pz*|n_z|*e_z.
                traction[:,2]-=p*np.abs(outward[:,2])
                areas+=area_factor
                totals+=traction**2*area_factor[:,None]
                means+=traction*area_factor[:,None]
                maxima=np.maximum(maxima,np.linalg.norm(traction,axis=1))
                normavg+=outward*area_factor[:,None]
            rms=np.sqrt(totals/areas[:,None]); norm=np.linalg.norm(rms,axis=1)
            center=facecent
            normal=normavg/areas[:,None]
            for i,r in enumerate(e):
                kind=kinds[i]; a0=areas[i]
                accum=summary_by_kind[kind]
                accum['faces']+=1;accum['area_mm2']+=float(a0)
                accum['sum_r2_area']+=totals[i]
                accum['sum_rnorm2_area']+=float(np.sum(totals[i]))
                accum['max_sample_residual_N_mm2']=max(accum['max_sample_residual_N_mm2'],float(maxima[i]))
                x=float(center[i,0]); bucket=(kind,round(x,9))
                profile_acc[bucket][0]+=float(a0)
                profile_acc[bucket][1]+=totals[i]
                if kind=='free' and abs(normal[i,1])>=0.9:
                    profile_free_y[round(x,9)][0]+=float(a0)
                    profile_free_y[round(x,9)][1]+=float(totals[i,1])
                writer.writerow(dict(kind=kind, element_id=int(r[0])+1,
                    neighbor_element_id=int(r[2])+1 if r[2]>=0 else '',
                    domain_index=int(region[r[0]]),
                    neighbor_domain_index=int(region[r[2]]) if r[2]>=0 else '',
                    x=x,y=float(center[i,1]),z=float(center[i,2]),
                    area_mm2=a0, normal_x=normal[i,0], normal_y=normal[i,1],normal_z=normal[i,2],
                    pressure_N_mm2=float(r[4]),
                    mean_residual_x_N_mm2=means[i,0]/a0,
                    mean_residual_y_N_mm2=means[i,1]/a0,
                    mean_residual_z_N_mm2=means[i,2]/a0,
                    rms_residual_x_N_mm2=rms[i,0],
                    rms_residual_y_N_mm2=rms[i,1],rms_residual_z_N_mm2=rms[i,2],
                    rms_residual_norm_N_mm2=norm[i],residual_max_N_mm2=maxima[i]))
    result={}
    for kind,v in summary_by_kind.items():
        if v['faces']:
            result[kind]={'faces':v['faces'],'area_mm2':v['area_mm2'],
                   'residual_rms_components_N_mm2':np.sqrt(v['sum_r2_area']/v['area_mm2']).tolist(),
                   'residual_rms_norm_N_mm2':float(np.sqrt(v['sum_rnorm2_area']/v['area_mm2'])),
                   'max_sample_residual_N_mm2':v['max_sample_residual_N_mm2']}
        else: result[kind]={'faces':0}
    result['fixed_faces_skipped']=fixed_count
    profile=[]
    for (kind,x),(area,sq) in sorted(profile_acc.items(),key=lambda a:(a[0][1],a[0][0])):
        v=np.sqrt(sq/area)
        profile.append([kind,x,*v.tolist(),float(np.linalg.norm(v))])
    y_profile=[[x,float(np.sqrt(sq/area))]
                for x,(area,sq) in sorted(profile_free_y.items())]
    return result,profile,np.asarray(y_profile)


def _write_csv(path,rows):
    rows=iter(rows)
    first=next(rows,None)
    if first is None: return
    with path.open('w',newline='',encoding='utf-8') as fp:
        writer=csv.DictWriter(fp,fieldnames=list(first.keys()))
        writer.writeheader();writer.writerow(first)
        writer.writerows(rows)


def _plot_profiles(out,nodal,vol,faces,free_y):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    def plot(name, x, ys, labels, y_label):
        if len(x)==0:return
        fig,ax=plt.subplots(figsize=(11,5))
        for y,l in zip(ys,labels):ax.plot(x,y,label=l,linewidth=1.4)
        ax.set_xlabel('Longitudinal position x (CUF/OpenSees coordinates)')
        ax.set_ylabel(y_label)
        ax.grid(True,alpha=0.35)
        ax.legend()
        fig.tight_layout();fig.savefig(out/name,dpi=170);plt.close(fig)
    if len(nodal):
        plot('01_nodal_equilibrium_vs_x.png',nodal[:,0],
             [nodal[:,i] for i in (1,2,3,4)],
             ['r_x RMS','r_y RMS','r_z RMS','vector norm RMS'],'RMS free nodal force residual (N)')
    if len(vol):
        plot('02_volume_equilibrium_vs_x.png',vol[:,0],
             [vol[:,i] for i in (1,2,3,4)],
             ['div σ_x RMS','div σ_y RMS','div σ_z RMS','vector norm RMS'],
             'Volume RMS divergence (N/mm³)')
    if faces:
        fig,ax=plt.subplots(figsize=(11,5))
        for kind in ('free','loaded','interface'):
            selected=sorted((r for r in faces if r[0]==kind),key=lambda r:r[1])
            if selected:
                ax.plot([r[1] for r in selected],[r[5] for r in selected],
                        marker='.',markersize=3,linewidth=1,label=kind)
        ax.set_xlabel('Longitudinal position x (CUF/OpenSees coordinates)')
        ax.set_ylabel('Area-weighted RMS traction residual (N/mm²)')
        ax.grid(True,alpha=0.35);ax.legend()
        fig.tight_layout();fig.savefig(out/'03_face_traction_vs_x.png',dpi=170);plt.close(fig)
    if len(free_y):
        plot('04_free_y_surface_traction_vs_x.png',free_y[:,0],[free_y[:,1]],
             ['free faces with |n_y|>=0.9: RMS traction-y'],
             'Free-surface traction component y RMS (N/mm²)')


def run(path:Path,out:Path,batch:int=384,plots=True):
    out.mkdir(parents=True,exist_ok=True)
    data=_read_npz(path)
    print(f'[input] {path} | nodes={len(data["nodes"])} H8={len(data["elements"])}',flush=True)
    nodal,profile_nodal,profile_vol=_volume_and_nodal(data,batch,out)
    print(f'[nodal] ||r_free||={nodal["nodal_free_l2_N"]:.6g} N; '
          f'||r_reaction||={nodal["reaction_difference_l2_N"]:.6g} N',flush=True)
    print('[volume] gauss-weighted div(sigma) recovered',flush=True)
    face_summary,profile_faces,profile_y=_faces(data,out,batch)
    print('[faces] '+', '.join(f'{kind}: {face_summary[kind].get("faces",0)}'
          for kind in ('free','loaded','interface')),flush=True)
    summary={
        'version':'CSF-CUF OpenSees H8 equilibrium residuals v01 - 2026-11-20',
        'input_npz':str(path.resolve()),
        'coordinate_convention':'(x,y,z)_OpenSees=(Z,X,Y)_CSF',
        'stress_components':'Cartesian physical x,y,z; stress from each element E,G,nu',
        'method':{'nodal':'f_int = sum_e integral(B^T sigma dV); r_free=f_int-f_ext; r_fixed=support_reaction',
                  'volume':'Exact div(sigma) for isoparametric H8 and elementwise constant elastic C; 2x2x2 Gauss RMS',
                  'exterior':'At 2x2 face Gauss, residual sigma*n - pz*abs(n_z)*e_z on loaded, sigma*n on free',
                  'interface':'At 2x2 face Gauss, residual sigma_plus*n_plus + sigma_minus*n_minus',
                  'excluded':'Clamped x0 faces: traction is reaction, not prescribed zero'},
        'nodal_and_volume':nodal,'surface':face_summary,
        'note':'Weak nodal equilibrium and local strong/traction equilibrium are distinct; no stress recovery/averaging applied.'}
    (out/'residual_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    if len(profile_faces):
        _write_csv(out/'surface_residuals_vs_x.csv',(
            dict(kind=r[0],x=r[1],rms_x=r[2],rms_y=r[3],rms_z=r[4],rms_norm=r[5])
            for r in profile_faces))
    if plots:_plot_profiles(out,profile_nodal,profile_vol,profile_faces,profile_y)
    print('[saved] '+str(out.resolve()),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('npz',type=Path,help='solved_opensees NPZ exported by run_opensees_csf.py')
    parser.add_argument('--output-dir',type=Path,default=Path('fem3d/residuals'))
    parser.add_argument('--batch',type=int,default=384,help='H8 elements/faces per vectorized batch')
    parser.add_argument('--no-plots',action='store_true',help='write CSV and JSON only')
    a=parser.parse_args()
    if a.batch<1:parser.error('--batch must be >= 1')
    run(a.npz,a.output_dir,batch=a.batch,plots=not a.no_plots)

if __name__=='__main__':main()
