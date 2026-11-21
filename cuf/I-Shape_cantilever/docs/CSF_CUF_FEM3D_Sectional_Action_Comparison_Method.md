# Independent CSF–CUF and FEM3D solutions: comparison of sectional resultants

**Scope:** methodological description for a numerical verification section of
a CSF–CUF software paper. Quantities are in mm, N and N mm, with the beam axis
along \(x\), sectional coordinates \(y,z\), and vertical loading in \(-z\).
The model considered here is the non-prismatic, heterogeneous I-shaped
cantilever of length \(L=1000\) mm.

## 1. Independent solution selection

The CUF transverse approximation is **fixed**: Lagrange L9 functions are
applied on the nine quadrilateral CSF physical domains. No transverse
approximation refinement is carried out in this numerical study.

Longitudinal stabilization of CSF–CUF displacements is evaluated independently
through two solution series:

- **h-series:** 2, 4, 6, 8, 10, 12, 16 and 20 longitudinal elements with
  longitudinal polynomial degree \(p=12\);
- **p-series:** longitudinal orders \(p=2,3,\ldots,12\) with 10 longitudinal
  elements.

In each series, the monitored quantity is the vertical displacement at the
fixed physical point \(P=(1000,-33,35)\) mm. Two consecutive relative
changes below 0.5% constitute the *declared numerical stabilization rule*.
This rule concerns the monitored displacement, not the entire stress field.
The configuration **10 longitudinal elements, \(p=12\)** is already solved in
both series and is used for the sectional-resultant comparison.

The independent FEM3D model uses the OpenSees `stdBrick` H8 discretization.
The previously recorded longitudinal GCI study selected **80 × 6 × 6**
mesh divisions (25,920 H8 elements and 31,185 nodes), with a 0.477699%
GCI for the monitored tip displacement at fixed transverse mesh divisions.
This does not by itself establish convergence of all stress components.

**The discrepancy between the CUF and FEM3D displacement fields is not used
to select the CUF discretization, nor to establish CUF convergence.**

## 2. Common definition of sectional resultants

At a section \(\Omega(x)\) oriented with normal \(+\mathbf e_x\), the
sectional axial force, vertical shear and bending moment are defined as

\[
N(x)=\int_{\Omega(x)}\sigma_{xx}(x,y,z)\,\mathrm dA,
\qquad
T_z(x)=\int_{\Omega(x)}\sigma_{xz}(x,y,z)\,\mathrm dA,
\]

\[
M_y(x)=\int_{\Omega(x)}z\,\sigma_{xx}(x,y,z)\,\mathrm dA.
\]

The moment is taken about the line through \((x,0,0)\), consistently with
\(\mathbf M=\int(\mathbf r-\mathbf r_0)\times(\boldsymbol\sigma\mathbf e_x)\,\mathrm dA\).
The above signs are those used by the supplied CSF–CUF/FEM3D postprocessors.

The CSF physical section provides the integration domains, coordinates
\((y_q,z_q)\) and physical area weights \(w_q\). Accordingly, the numerical
integration uses

\[
N_h=\sum_q w_q\,\sigma_{xx}(x,y_q,z_q),\quad
T_{z,h}=\sum_q w_q\,\sigma_{xz}(x,y_q,z_q),\quad
M_{y,h}=\sum_q w_q z_q\,\sigma_{xx}(x,y_q,z_q).
\]

The quadrature weights include the physical sectional measure; no separate
section Jacobian is computed in the comparison script.

## 3. Stress reconstruction and integration: CSF–CUF

The CUF displacement solution is loaded from its completed checkpoint
(`cases/convergence_h_v02/step_005.yaml`). The code calls the established
`csf.cuf.tools.plot_strain_stress_boundary_v10._evaluate_cuf_state()` through
`check_cuf_single_tensor_surface.integrate_stress()`.

The same public CSF bridge supplies the sectional geometry, constitutive
provider and polygon-to-CUF domain correspondence. The existing
`FixedGaussPolygonIntegrator` yields sectional quadrature points and weights.
The stress components are reconstructed from the CUF displacement field and
the constitutive values at each physical location.

No independent interpolation of CSF geometry or material properties is
introduced by this comparison. The selected CUF case and checkpoint are
validated against the stored solution manifest (including SHA-256 hashes).

## 4. Stress recovery and integration: native OpenSees FEM3D

The reference FEM3D checkpoint contains **native `stdBrick` stresses**
recorded directly at all eight Gauss points of every H8 element. These
stresses were not derived from the displacement field in the comparison
script. The saved Voigt component order is

\[
[\sigma_{xx},\sigma_{yy},\sigma_{zz},\sigma_{xy},\sigma_{yz},\sigma_{xz}].
\]

For the selected `center` recovery, the postprocessor first computes the
componentwise arithmetic mean of the eight native stresses for each element
\(e\):

\[
\overline{\boldsymbol\sigma}_e
=\frac{1}{8}\sum_{g=1}^{8}\boldsymbol\sigma_{e,g}.
\]

**This is a postprocessed estimate, not an OpenSees stress evaluated at the
element centre.** At a physical sectional quadrature point, the existing
`FEM3DH8` locator identifies the containing H8 cell. Its mean
\(\overline{\boldsymbol\sigma}_e\) is then assigned to that point. Thus the
transverse stress approximation used in integration is **piecewise constant
(P0) per H8 cell**. The sectional points and physical area weights come from
`SectionalGeometryProvider.quadrature_data()` through the public CSF API;
the locator uses the saved FEM mesh, without reconstructing CSF physical
geometry or materials.

The centre recovery markedly changes the integral of \(\sigma_{xz}\)
compared with sampling one interior axial Gauss plane. The two methods must
not be conflated. P0 recovery loses within-element transverse variation,
which can affect bending moments and pointwise accuracy. These choices are
recorded in the FEM3D provenance metadata.

## 5. Theoretical force and moment from the prescribed loads

The existing `VerticalFaceTractions` adapter defines the vertical traction
\(p_z\) per *projected* \(xy\)-area on the designated lower CSF boundary
faces. The corresponding theoretical sectional resultants are calculated
from the loads on the free-end segment \([x,L]\):

\[
N_{\mathrm{load}}(x)=0,\qquad
T_{z,\mathrm{load}}(x)=\int_x^L\!\mathrm dF_z(s),
\]

\[
M_{y,\mathrm{load}}(x)
=-\int_x^L(s-x)\,\mathrm dF_z(s).
\]

Here \(\mathrm dF_z(s)\) denotes the total prescribed vertical load over a
longitudinal differential strip, as evaluated using the existing load
adapter and **CSF-evaluated boundary geometry**. This notation does not
assume a constant loaded-section width. The CUF and FEM3D postprocessors
calculate the reference loads independently using the same physical CSF
model; the comparison script rejects inconsistent reference resultants.

## 6. Common sampling and comparison statistics

The FEM3D `center` mode selects physical sections at the centres of sampled
H8 longitudinal layers. With the specified mesh and default 20 target cuts,
the positions are
\(x_k=6.25+50k\) mm, for \(k=0,\ldots,19\). These are **not**
the original target stations \(0,50,\ldots,950\) mm.

The comparison code reads the actual physical positions \(x_k\) from the
FEM3D report and evaluates the CUF resultants at **exactly those same
sections**. The FEM3D centre section does not need to coincide with a
longitudinal CUF finite-element boundary.

For each resultant \(Q\in\{N,T_z,M_y\}\), the CSV contains
\(Q_{\mathrm{CUF}}\), \(Q_{\mathrm{FEM}}\) and \(Q_{\mathrm{load}}\), together
with all three signed differences:

\[
Q_{\mathrm{CUF}}-Q_{\mathrm{load}},\quad
Q_{\mathrm{FEM}}-Q_{\mathrm{load}},\quad
Q_{\mathrm{CUF}}-Q_{\mathrm{FEM}}.
\]

The summary reports the **maximum absolute deviation over sampled sections**.
When a percentage is calculated, the normalization is the *maximum absolute
nonzero theoretical resultant over these sections*, not a local near-zero
denominator. Since the theoretical axial force is zero, axial-force errors
are reported **only as absolute values in newtons**, not as percentages.

## 7. Reproducibility and interpretation

Example command from `cuf/I-Shape_cantilever`:

```bash
python tools/compare_cuf_fem3d_N_T_M.py \
  --cuf-case cases/convergence_h_v02/step_005.yaml \
  --fem-case cases/convergence_h_v02/step_008.yaml \
  --fem-npz fem3d/native_stress_reference/solution.npz \
  --points 20
```

The program preserves checkpoint SHA-256 identifiers, physical case paths,
CSF-based references, sampling coordinates, numerical results and figures.
Neither numerical solver is rerun. Results are intended to assess the
agreement of *sectional force and moment resultants* among two independently
selected approximate solutions and the prescribed-load equilibrium values.

**Scope exclusions:** no exterior-surface traction recovery; no local strong-
form equilibrium residual analysis; no inference about convergence of the
complete 3D stress field; no use of CUF-FEM3D displacement discrepancies as
a convergence criterion.

## 8. Example obtained from the uploaded data

The bundled example was reproduced from an archived real CUF
\(N=10,p=12\) solution and the corresponding user-provided native FEM3D
`center` report. For the matched section at \(x=506.25\) mm:

| Resultant | Prescribed loads | CSF–CUF | FEM3D centre recovery |
|---|---:|---:|---:|
| \(N\) [N] | 0 | approximately −0.000038 | +20.91732 |
| \(T_z\) [N] | −233652.375 | −233652.353922 | −233625.373985 |
| \(M_y\) [N mm] | +57682930.078125 | +57682926.498825 | +57452616.228980 |

These values are **sectional-resultant postprocessing data**, not a measure
of convergence. The native FEM3D checkpoint was not rerun in the present
external verification environment; its already-generated `center` CSV and
provenance were used. The original checkpoint remains the authoritative
source of native OpenSees stresses in the user's local project.
