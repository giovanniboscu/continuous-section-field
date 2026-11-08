#!/usr/bin/env python3
"""Small-mesh regression: verify OpenSees 20NodeBrick against SciPy H20.

Requires OpenSeesPy. Run this before using --backend opensees for production;
it checks the practical node ordering and element constitutive convention.
"""
from pathlib import Path
import argparse
import subprocess
import sys
import numpy as np

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('model',type=Path)
    ap.add_argument('--output-dir',type=Path,default=Path('output/h20_backend_check'))
    a=ap.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    script=Path(__file__).with_name('run_bending_fem3d_h20.py')
    results={}
    for backend in ('scipy','opensees'):
        filename=a.output_dir/f'{backend}_h20.npz'
        cmd=[sys.executable,str(script),str(a.model),str(filename),
             '--backend',backend,'--nx','3','--ny-left','1','--ny-web','2',
             '--ny-right','1','--nz-flange','1','--nz-web','4','--amplitude','-1']
        print(' '.join(cmd),flush=True)
        subprocess.run(cmd,check=True)
        with np.load(filename,allow_pickle=False) as d:
            results[backend]={k:d[k] for k in ('nodes','elements','displacement','nodal_loads')}
    a0,b0=results['scipy'],results['opensees']
    for key in ('nodes','elements','nodal_loads'):
        if not np.allclose(a0[key],b0[key],rtol=0,atol=1e-12):
            raise AssertionError(f'Backend mismatch in {key}')
    u=a0['displacement'];v=b0['displacement']
    rel=np.linalg.norm(v-u)/max(1,np.linalg.norm(u))
    print(f'OpenSees vs SciPy relative displacement 2-norm error: {rel:.12e}')
    if rel > 1e-6:
        raise AssertionError('H20 backends disagree: examine OpenSees node ordering / integration')
    print('PASS: OpenSees 20NodeBrick and SciPy H20 match on the regression model.')

if __name__=='__main__':main()
