"""Local QA: run real H20 SciPy solves with independent benchmark YAML adapter.
Never used by the production CSF-driven driver.
"""
from pathlib import Path
import argparse,time
import numpy as np
import qa_fixture
import run_bending_fem3d_v2 as base
from run_bending_fem3d_h20 import upgrade_to_h20,consistent_bottom_loads,validate_h20
from h20_scipy_solver import solve_scipy_h20
from h20_strong_residual import measure

def run(file,levels,dest):
    field=qa_fixture.FixtureField(file)
    topo=base._i_section_topology(field)
    dest.mkdir(parents=True,exist_ok=True)
    for label,nx,nyL,nyW,nyR,nzF,nzW in levels:
        t=time.time()
        mesh8=base.build_mesh(field,topo,base.MeshSettings(nx,nyL,nyW,nyR,nzF,nzW))
        E,G,nu=base.evaluate_element_materials(field,mesh8)
        mesh=upgrade_to_h20(mesh8)
        validate_h20(mesh,ntest=50)
        loads=consistent_bottom_loads(mesh,-1.,0.,1000.)
        u,*more=solve_scipy_h20(mesh,E,nu,loads,0.,1000.)
        output=dest/f'{label}_h20.npz'
        np.savez_compressed(output,nodes=mesh.nodes,elements=mesh.elements,
                            element_E=E,element_nu=nu,element_G=G,
                            element_region=mesh.element_region,displacement=u,
                            nodal_loads=loads)
        r=measure(output,max_elements=70,gauss=2)
        print(label,'elems',len(mesh.elements),'nodes',len(mesh.nodes),
              'min uz',u[:,2].min(),'rz rms',r['metrics']['z']['rms'],
              'time',time.time()-t,flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('model',type=Path)
    a.add_argument('--out',type=Path,default=Path('/mnt/data/FEM3D_H20_Convergence/qa_results'))
    a=a.parse_args()
    run(a.model,[('T0',3,1,2,1,1,4),('T1',6,1,2,1,2,4),('T2',12,2,4,2,2,8)],a.out)
