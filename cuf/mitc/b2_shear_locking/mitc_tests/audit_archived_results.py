#!/usr/bin/env python3
"""Read-only reproducible audit of archived MITC B2 cases and solver logs."""
from __future__ import annotations
import argparse, csv, math, re
from pathlib import Path
import yaml

COUNTS=(1,2,4,8)
RE_SYM=re.compile(r'global stiffness symmetry: relative=([0-9.eE+-]+).*rtol=([0-9.eE+-]+)')
RE_VERIFY=re.compile(r'MITC assembly verify\] element=(\d+) pair=\((\d+),(\d+)\).*max_abs=([0-9.eE+-]+) rel_F=([0-9.eE+-]+).*status=(\w+)')
RE_KKT=re.compile(r'relative_residual_inf=([0-9.eE+-]+)')

def tip(path):
    matches=[]
    for line in path.read_text().splitlines():
        f=line.split()
        if len(f)>=8 and f[4]=='center':
            try: vals=[float(f[i]) for i in (0,1,2,3,7)]
            except ValueError: continue
            if all(abs(a-b)<1e-7 for a,b in zip(vals[:4],(1,5000,0,0))): matches.append(vals[4])
    assert len(matches)==1,(path,matches)
    return matches[0]

def main():
    base=Path(__file__).resolve().parents[1]
    cases={}; out={}; diag={}; check=[]
    for n in COUNTS:
        for mode in ('off','on'):
            name=f'mitc_locking_rect_B2_N{n:02d}_{mode}'
            y=yaml.safe_load((base/'cases'/f'{name}.yaml').read_text())
            cases[n,mode]=y
            bounds=y['longitudinal']['element_boundaries']
            assert len(bounds)==n+1 and all(abs(v-i/n)<1e-12 for i,v in enumerate(bounds)),name
            assert y['longitudinal']['order']==1 and y['cuf']['order']==2
            assert y['solver']['correctionMITC']==(mode=='on')
            assert y['solver']['verifyMITCAssembly']==(mode=='on')
            assert y['case']['name']==name
            assert y['output']['directory'].endswith('/'+name)
            out[n,mode]=tip(base/'output'/name/'response.txt')
            log=(base/'mitc_tests/logs'/f'{name}.log').read_text()
            assert '[3/4] solve complete' in log,name
            syms=RE_SYM.findall(log)
            assert len(syms)==1,name
            symmetry,rtol=map(float,syms[0]); assert math.isfinite(symmetry) and symmetry<=rtol
            checks=RE_VERIFY.findall(log)
            if mode=='on':
                assert len(checks)==n,(name,checks)
                assert [int(c[0]) for c in checks]==list(range(n))
                assert all(c[1:3]==('1','1') and c[5]=='PASS' for c in checks)
            else: assert len(checks)==0,name
            kkt=RE_KKT.findall(log)
            diag[n,mode]={'symmetry':symmetry,'rtol':rtol,'mitc_checks':len(checks),'kkt_residual':float(kkt[-1]) if kkt else None}
            check.append(f'{name}: PASS (inputs, mesh, response, solve, symmetry, MITC diagnostics)')
        a=cases[n,'off'];b=cases[n,'on']
        for key in ('problem','cuf','longitudinal','section_integration','sampling'):
            assert a.get(key)==b.get(key),(n,key)
        sa=dict(a['solver']);sb=dict(b['solver'])
        for s in (sa,sb):s.pop('correctionMITC');s.pop('verifyMITCAssembly')
        assert sa==sb,n
    eb=-100*5000**3/(3*75000*(100*100**3/12))
    report=['# Archived MITC B2 verification audit','','This audit examines archived files; it does not rerun the solver.','','## Recomputed displacements and reference errors','', '| B2 | OFF [mm] | ON [mm] | OFF error to EB [%] | ON error to EB [%] |', '|---:|---:|---:|---:|---:|']
    for n in COUNTS:
        off,on=out[n,'off'],out[n,'on']
        report.append(f'| {n} | {off:.9f} | {on:.9f} | {abs(off-eb)/abs(eb)*100:.5f} | {abs(on-eb)/abs(eb)*100:.5f} |')
    report+=['','## Difference-based refinement indicator','', 'For equal mesh halving, p_delta=log2(abs((u_h-u_h/2)/(u_h/2-u_h/4))). This is an indicator, not a guaranteed asymptotic convergence order.','','| Mode | delta(1 to 2) [mm] | delta(2 to 4) [mm] | delta(4 to 8) [mm] | p_delta(1,2,4) | p_delta(2,4,8) |','|---|---:|---:|---:|---:|---:|']
    for mode in ('off','on'):
        u=[out[n,mode] for n in COUNTS]
        d=[u[i+1]-u[i] for i in range(3)]
        p=[math.log2(abs(d[i]/d[i+1])) for i in range(2)]
        report.append(f'| {mode.upper()} | {d[0]:.8f} | {d[1]:.8f} | {d[2]:.8f} | {p[0]:.4f} | {p[1]:.4f} |')
    report+=['','MITC ON increments decrease with refinement; MITC OFF increments increase on these meshes. Neither is sufficient to establish the asymptotic order or the exact continuum limit.','','## Archived solver diagnostics','','| B2 | Mode | symmetry relative | KKT relative residual (inf) | verified MITC elements |','|---:|---|---:|---:|---:|']
    for n in COUNTS:
        for mode in ('off','on'):
            q=diag[n,mode]
            report.append(f'| {n} | {mode.upper()} | {q["symmetry"]:.4e} | {q["kkt_residual"]:.4e} | {q["mitc_checks"]} |')
    report+=['','All eight logs report solve completion and global symmetry under the configured tolerance of 1e-10. The MITC diagnostics sample only pair (1,1), one entry per longitudinal element, and are internal comparisons rather than independent validation.','','## Consistency checks','','- Eight case names/output paths and tip-center response coordinates: PASS.','- Each B2 partition is uniform over [0,1]; order=1: PASS.','- Within each OFF/ON pair, physical problem, CUF basis, element mesh, integration and sampling settings are identical: PASS.','- Solver settings differ only in correctionMITC and verifyMITCAssembly: PASS.','- OFF/ON diagnostic flags and logged checks match: PASS.','- No numerical displacement PASS threshold was introduced.','','## Not established','','- Reaction balance, energy partition, complete pairwise MITC block validation, spurious modes, and independent 3D convergence require additional solver data or executions.','- Comparing with Euler-Bernoulli is a reference check, not a proof of convergence to the exact CUF/3D solution.','']
    target=base/'mitc_tests/reports/mitc_B2_archive_audit.md'
    target.write_text('\n'.join(report))
    print('\n'.join(check));print('Wrote',target)

if __name__=='__main__':main()
