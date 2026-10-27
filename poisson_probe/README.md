# Isolating axial–transverse Poisson coupling in B2 MITC

This is a **diagnostic numerical experiment**, not a change to the CSF physical model or a proposed material law. Use the already-installed CSF–CUF solver and the archived B2 benchmark cases. Do not run the variants concurrently.

## Hypothesis

The residual tip-deflection deficit at nonzero Poisson ratio may be associated with normal constitutive coupling between longitudinal strain `epsilon_xx` and transverse normal strains `epsilon_yy, epsilon_zz`. Merely varying Poisson ratio changes several coefficients at once; this test isolates just the four symmetric entries involving `xx` with `yy` and `zz`.

In the solver's Voigt order `(xx, yy, zz, yz, xz, xy)`:

- **Baseline:** the unmodified 6x6 constitutive matrix from CSF.
- **Decoupled diagnostic:** set only `C[0,1]`, `C[1,0]`, `C[0,2]`, `C[2,0]` to zero. Keep `C[1,2]`, `C[2,1]`, all diagonal entries, and all shear coefficients unchanged.

The diagnostic matrix is checked for symmetry and strictly positive eigenvalues at every sampled point. The program also checks that other entries are unchanged. **This material is not physically equivalent to isotropic elasticity** and the reference EB displacement is only a common scale, not an exact solution for the modified material.

## Run

Place `run_poisson_coupling_probe.py` anywhere, and execute within the repository's installed virtual environment:

```bash
python3 run_poisson_coupling_probe.py \
  --root cuf/mitc/b2_shear_locking \
  --meshes 8 16 \
  --mode both \
  2>&1 | tee poisson_probe.log
```

Paths are relative to the directory where this command is issued. If already inside `cuf/mitc/b2_shear_locking`, use `--root .`.

The script creates temporary case YAMLs **inside the existing `cases/` directory** so all relative geometry/problem/expansion paths still resolve. It removes these temporary YAMLs after each solve, does not alter original YAMLs, restores the constitutive provider after each variant, and puts results under `poisson_coupling_probe/` to avoid overwriting archived benchmarks. The output is `poisson_coupling_probe/comparison.csv` and `matrix_diagnostic.json`.

For a faster run against the archived baseline, use `--mode decoupled`. The baseline deflections at N=8 and 16 were previously approximately -6.369662827 mm and -6.521743940 mm, but a paired rerun is preferable if solver versions differ.

## How to interpret

Compare `deficit_pct` for baseline and decoupled **at each N**. If decoupling strongly reduces the `1/N` contribution, this implicates the axial–transverse normal coupling *in this model*; it does not by itself establish Poisson locking or identify a specific kinematic inconsistency. If the deficit persists, the simple mechanism is inadequate. Follow up with field reconstructions of `epsilon_yy + nu epsilon_xx` and `epsilon_zz + nu epsilon_xx` and a strain-energy partition.

## Important limitations

- This prototype uses an explicit runtime override of `MaterialConstitutive.matrix`. It requires that your installed solver's constitutive coefficients flow through this method; validate against your solver version (source reviewed from `cuf(20261026-174052).zip`).
- The result can be affected by a different solver revision; record `git rev-parse HEAD` and the Python environment.
- The intervention does not remove all Poisson dependencies, nor does it reproduce the `nu=0` constitutive law.
- For a physically derived reduction, a distinct Schur-complement/plane-stress constitutive test would be necessary; that would be **a different experiment**.
