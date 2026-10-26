"""Recover physical MITC shear stress at longitudinal nodes from v4 CUF checkpoints.

For this *prismatic, isotropic* Section 4.1 benchmark only.
No installed CSF package is required.  Coordinates: beam x; section y,z.
"""
import argparse
import csv
import pathlib
import numpy as np

PAPER = {2: [-1.029,-1.029], 3: [-1.094,-0.996,-0.898], 4: [-1.228,-0.982,-0.939,-1.097]}
# Paper Table 1 reports nodes in increasing physical x order.
NODES = {2: [-1.,1.], 3: [-1.,0.,1.], 4: [-1.,-1/3,1/3,1.]}

def powers(a, n):
    v = a ** np.arange(n)
    d = np.zeros(n)
    if n>1: d[1:] = np.arange(1,n)*a**np.arange(n-1)
    return v,d

def gamma_at(a, xi, xsec_y=0., xsec_z=0.):
    c=a['solved_nodal_domain_power_coefficients'][0,:,0]  # nodal, y-power,z-power,component
    shp=a['longitudinal_shape_coefficients']
    L=float(a['element_x_ends'][0]-a['element_x_starts'][0]); assert L>0
    v,d=powers(xi,shp.shape[1]); N=shp@v; Nx=(shp@d)*(2/L)
    yp,yd=powers(xsec_y,c.shape[1]); zp,zd=powers(xsec_z,c.shape[2])
    u=np.einsum('npqc,p,q->nc',c,yp,zp)
    uz=np.einsum('npqc,p,q->nc',c,yp,zd)
    # tau_xz = G*(u_z,x + u_x,z); engineering shear gamma_xz
    gamma=float(Nx@u[:,2]+N@uz[:,0])
    return gamma

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',default='output',type=pathlib.Path)
    ap.add_argument('--csv',default='paper41_shear_comparison.csv',type=pathlib.Path)
    args=ap.parse_args()
    E=75000.; nu=.33; G=E/(2*(1+nu))
    rows=[]
    for b in (2,3,4):
      for mode in ('off','on'):
        name=f'mitc_paper41_L9_B{b}_{mode}'
        path=args.output/name/(name+'.cuf.npz')
        with np.load(path,allow_pickle=False) as z:
          a={k:z[k] for k in z.files}
        if a['solved_nodal_domain_power_coefficients'].shape[0:3] != (1,b,1):
          raise ValueError(f'Unexpected checkpoint dimensions in {path}')
        ties,_=np.polynomial.legendre.leggauss(b-1)
        ties_gamma=np.array([gamma_at(a,t) for t in ties])
        for j,xi in enumerate(NODES[b]):
          raw=gamma_at(a,xi)
          if mode=='on':
            weights=np.ones(1) if len(ties)==1 else np.array([np.prod([(xi-ties[k])/(ties[m]-ties[k]) for k in range(len(ties)) if k!=m]) for m in range(len(ties))])
            corrected=float(weights@ties_gamma)
          else: corrected=raw
          stress=G*corrected  # N/mm2 = MPa
          # paper table: sigma_yz x 10^-4 Pa, hence reported dimensionless number is stress(Pa)/10^4
          scaled=stress*100. # 1 MPa = 10^6 Pa, divided by 10^4 = 100
          ref=PAPER[b][j] if mode=='on' else ''
          rows.append(dict(case=name,node=j+1,xi=xi,raw_shear_MPa=G*raw,mitc_shear_MPa=stress,paper_table_units=scaled,paper_reference=ref,absolute_difference=(scaled-ref if ref!='' else '')))
    args.csv.parent.mkdir(parents=True,exist_ok=True)
    with args.csv.open('w',newline='') as f:
      writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    for r in rows:
      print(f"{r['case']} node={r['node']} xi={r['xi']:7.4f} stress={r['mitc_shear_MPa']:+.8g} MPa scaled={r['paper_table_units']:+.5f} paper={r['paper_reference']}")
    print('Wrote',args.csv)
if __name__=='__main__':main()
