# FEM3D sectional resultants from native OpenSees stresses

## Scope

This postprocessor evaluates the axial force **N**, vertical shear **Tz**, and bending moment **My** for the **I-Shape_cantilever** case. The input is the *solved* OpenSees `stdBrick` H8 checkpoint, now containing `gauss_stress` with shape `(ne, 8, 6)`. It does not rerun FEM3D or reconstruct stresses from the displacement field.

The method is a **sectional recovery of stresses recorded at native Gauss points**. Since those stresses exist at discrete integration points rather than on continuous cross-sections, a recovery approximation is unavoidable; it is documented explicitly below.

## Native stress convention

For element `e`, native point `g`, the recorded vector is

\[
\boldsymbol\sigma_{eg}^{OS}=
[\sigma_{xx},\sigma_{yy},\sigma_{zz},\sigma_{xy},\sigma_{yz},\sigma_{xz}]^T.
\]

The OpenSees `stdBrick` point ordering is the 2×2×2 tensor-product Gauss rule with outer natural coordinate `r` slowest, middle `s`, and inner `t` fastest: `(r−,s−,t−)` through `(r+,s+,t+)`. The driver uses the standard node ordering in which the `r` axis is the beam's longitudinal `x` direction. Thus native point indices `0..3` lie at the negative longitudinal Gauss plane, and `4..7` at the positive one. This is the order used in the OpenSees `Brick.cpp` implementation. See https://github.com/OpenSees/OpenSees/blob/master/SRC/element/brick/Brick.cpp.

### Cross-section locations

For longitudinal H8 element \(k\), let its stored mesh stations be \(x_k\) and \(x_{k+1}\). The native axial Gauss planes are at

\[
x_k^{\pm} = \tfrac12(x_k+x_{k+1})
 \pm \frac{x_{k+1}-x_k}{2\sqrt{3}}.
\]

The `gauss` mode (default) selects the nearest *actual native Gauss plane* to each of 20 requested positions in `[0,L)`. At an exact longitudinal element boundary, the nearest right-hand plane is selected. **Results are reported at the actual Gauss coordinate, not at the requested coordinate**. `all-gauss` processes all 2\(N_x\) native longitudinal planes, so that the two sides of each element may be compared. `center` evaluates the element midpoint using the average of all eight native Gauss stresses; this is a separate diagnostic, **not** a native midpoint stress.

### Transverse stress projection

At a selected native axial Gauss plane, the four corresponding **transverse** Gauss stresses in each H8 element are arithmetically averaged:

\[
 \overline{\boldsymbol\sigma}_e^{\pm}=
 \frac14\sum_{g\in\mathcal G_e^{\pm}}\boldsymbol\sigma_{eg}^{OS}.
\]

This defines a piecewise-constant (P0) stress approximation on the transverse footprint of each H8 cell. It uses **native stresses only**. No stress–strain law, local modulus, or reconstruction from nodal displacements is introduced.

For `center`, the corresponding average uses all eight native values. This filters axial odd-in-`r` components but is *not* a native point measurement at \(x_m\).

**Limitation:** transverse P0 averaging discards in-element stress gradients, which especially affects the recovered moment. The procedure must not be described as an exact area integration of the continuous FEM stress field, nor as an exact integral of the raw 2×2 Gauss data on an arbitrarily curved sectional domain. It is a well-defined and reproducible recovery of native integration-point data.

## CSF-governed physical section and resultants

The CSF–CUF `SectionalGeometryProvider.quadrature_data()` API is called at each actual evaluation position for each material domain. It provides physical sectional coordinates \((y_q,z_q)\), the integration weights \(w_q\), and constitutive metadata. **Only its section positions and area weights are used**; the material matrix is deliberately unused because the stresses are native OpenSees results. No sectional polygons, Jacobians, or material laws are rebuilt from a YAML file or independently interpolated.

The existing FEM3D H8 evaluator from `plot_strain_stress_boundary_v10` identifies which saved FEM element contains each physical CSF quadrature point. Its returned displacement-derived strain is **discarded**, and its Jacobian is not used for sectional quadrature. The stored `element_region` must agree with the CSF domain; mismatches are errors rather than being silently smoothed.

The recovered sectional actions use the cross-sectional normal \(+\mathbf e_x\):

\[
\begin{aligned}
N_h(x)&\approx \sum_q w_q\,\overline\sigma_{xx,e(q)},\\
T_{z,h}(x)&\approx \sum_q w_q\,\overline\sigma_{xz,e(q)},\\
M_{y,h}(x)&\approx \sum_q w_q z_q\,\overline\sigma_{xx,e(q)}.
\end{aligned}
\]

The applied load reference is evaluated **independently** by the existing `VerticalFaceTractions` adapter on the same CSF model, integrating only the part of the applied load between the **actual section** and the free end. For the present load case, \(N_{\mathrm{load}}=0\), \(T_{z,\mathrm{load}}(0)=-473220\,\mathrm N\), \(M_{y,\mathrm{load}}(0)=+236610000\,\mathrm{N\,mm}\). The reference at other stations is calculated, not hardcoded.

For the actual mesh (80 × 6 × 6), the first native Gauss section is inside the first longitudinal element: it is **not the clamped plane \(x=0\)**. The clamped support equilibrium must instead be checked using the stored nodal `support_reactions` and `nodal_loads`; the script writes an independent `support_balance.json`.

## Usage

Run from `cuf/I-Shape_cantilever` after installing the `tools/` script:

```bash
python tools/plot_fem3d_N_T_M_from_npz.py \
  --case cases/convergence_h_v02/step_008.yaml \
  --fem-npz fem3d/native_stress_reference/solution.npz
```

For the element-midpoint diagnostic:

```bash
python tools/plot_fem3d_N_T_M_from_npz.py \
  --case cases/convergence_h_v02/step_008.yaml \
  --fem-npz fem3d/native_stress_reference/solution.npz \
  --sampling center
```

For all 160 longitudinal native Gauss planes, instead use `--sampling all-gauss`; this is more expensive and helps identify plane-to-plane changes or alternating shear recovery.

Optional: `--points 20`, `--cuts 0,0.125,0.375,0.625,0.875`, `--section-gauss 12`, `--output-dir PATH`. Cuts are normalized requested positions; for `gauss` and `center` they are **snapped** to the nearest available sampling plane and saved with their original targets for traceability.

## Outputs

Results are versioned under:

`diagnostics/fem3d_N_T_M_native/<case>/<checkpoint SHA-256 prefix>/<sampling>/`

Files:

- `section_resultants.csv`: actual/target station, N/Tz/My, prescribed-load resultants, signed differences, relative errors in Tz and My.
- `comparison_axial_force_N.png`, `comparison_shear_force_Tz.png`, `comparison_bending_moment_My.png`.
- `comparison_N_Tz_My_overview.png`: the three resultants and their signed residuals.
- `support_balance.json`: nodal force and moment closure from the saved OpenSees reaction data.
- `provenance.json`: sampling, source checkpoint digest, source APIs, and method limitations.

No FEM3D re-solve or CUF computation is performed by this script. **The real numerical N/Tz/My resultants cannot be reported until the new script is run on the actual `solution.npz`.**
