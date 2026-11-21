# Longitudinal FEM3D discretization study: Richardson extrapolation and GCI

**Document version:** v03.1 (methodological clarification, unchanged ASME equations).

**Scope of the claim:** this document describes a three-grid GCI *estimate* and a separate
study-defined mesh-selection policy. Passing a numerical GCI threshold is **not**
reported as an independent verification that the asymptotic regime has been reached.

**Methodological reference:** ASME V&V 10.1-2012 (R2022), *An Illustration of the Concepts of Verification and Validation in Computational Solid Mechanics*, Section **7.2, Calculation Verification**, especially Eqs. **(4), (6), (8), (10)**. The formulation below follows the **three-grid Richardson extrapolation and GCI** method illustrated there, with notation adapted to a fixed-transverse-resolution H8 finite-element model. The ASME document uses a cantilever tip displacement as its quantity of interest; here the quantity of interest is the vertical displacement at a user-specified physical point. This is an *application* of the published method, not a claim that ASME has approved this particular model or implementation.

**Official standard and citation:** [ASME V&V 10.1 — 2012 (R2022)](https://www.asme.org/codes-standards/find-codes-standards/an-illustration-of-the-concepts-of-verification-and-validation-in-computational-solid-mechanics/2012/pdf). The standard was issued in 2012 and reaffirmed in 2022.

## 1. Scope and controlled discretization

Let the beam occupy the interval \(x\in[x_0,x_1]\), with length \(L=x_1-x_0\). In each study, select and hold fixed the transverse H8 mesh parameters

\[
N_u=N_u^*,\qquad N_v=N_v^*.
\]

The values \(N_u^*\), \(N_v^*\) are **user inputs**, not constants in the source code. The only refined parameter is the number of *uniform longitudinal* H8 divisions, \(N_x\), and the corresponding longitudinal mesh size is

\[
h_x=\frac{L}{N_x}.
\]

The physical CSF geometry, regions, constitutive laws, load and boundary conditions are held unchanged across the study. The existing OpenSees driver obtains this physical information through the CSF public APIs. The convergence tool **does not** reconstruct CSF geometry, perform material interpolation, or evaluate a custom constitutive law. It reads the coordinates, H8 connectivity and solved displacements from each FEM3D checkpoint.

At one fixed *physical* point \(P=(x_P,y_P,z_P)\), belonging to **every** mesh, define the monitored quantity

\[
w(h_x)=u_z^{\mathrm{FEM3D}}(P;h_x,N_u^*,N_v^*).
\]

If \(P\) is a mesh node, the stored displacement is used directly. Otherwise, the displacement is evaluated with the ordinary H8 isoparametric functions on the stored FEM mesh:

\[
\mathbf u_h(P)=\sum_{a=1}^{8}N_a(\boldsymbol\xi_P)\,\mathbf d_a,\qquad
P=\sum_{a=1}^{8}N_a(\boldsymbol\xi_P)\,\mathbf X_a.
\]

Here \(\mathbf X_a\) and \(\mathbf d_a\) are the saved FEM nodal coordinates and displacement vectors. The second relation locates \(P\) *within the existing H8 element*; it is not an independent reconstruction of the CSF physical model. If the point cannot be found, the script stops with an error rather than changing \(P\).

## 2. Three-grid Richardson model — ASME V&V 10.1, Eq. (4)

For a triplet ordered **fine, medium, coarse**, write

\[
h_1<h_2<h_3,\qquad w_i=w(h_i),\quad i=1,2,3.
\]

Under the asymptotic error-expansion assumption of Section 7.2, the monitored response is modeled by

\[
w(h)=w_\infty+A h^p+\text{higher-order terms},
\]

where \(w_\infty\) is the limiting solution under *longitudinal refinement with fixed transverse resolution*, \(A\) is a coefficient and \(p>0\) is the **observed** longitudinal order. The asymptotic assumption must be considered when interpreting the GCI: it is not established merely by obtaining three numerical values.

## 3. Observed order — ASME V&V 10.1, Eqs. (6) and (7)

The order \(p\) is inferred **from the three computed solutions**, not imposed as the theoretical order of the H8 element:

\[
\boxed{\frac{w_3-w_2}{w_2-w_1}
=\frac{h_3^p-h_2^p}{h_2^p-h_1^p}}.
\]

The script solves this equation numerically for a **positive** \(p\). It therefore supports **unequal refinement ratios**,

\[
r_{21}=\frac{h_2}{h_1},\qquad r_{32}=\frac{h_3}{h_2}.
\]

Only for the special case \(r_{21}=r_{32}=r\) does the familiar closed form apply:

\[
p=\frac{\ln[(w_3-w_2)/(w_2-w_1)]}{\ln r}.
\]

A zero consecutive change, an oscillatory triplet, a non-positive inferred order, or non-finite data is **reported as an invalid three-grid estimate**. The script does not substitute a fabricated order of convergence or silently select the theoretical order.

## 4. Richardson estimate — ASME V&V 10.1, Eq. (8)

For a valid observed order \(p\), define the extrapolated response as

\[
\boxed{w_{\mathrm{ext}}=w_1+\frac{w_1-w_2}{r_{21}^{p}-1}}.
\]

It estimates the longitudinally refined limit in the **fixed** transverse approximation. It is not asserted to be the exact solution of the three-dimensional continuum problem.

## 5. GCI — ASME V&V 10.1, Eq. (10)

With \(F_s=1.25\) for a three-grid estimate as in the ASME illustration, the fine-grid GCI is

\[
\boxed{\mathrm{GCI}_{21}(\%)=
100\,\frac{F_s}{r_{21}^{p}-1}
\left|\frac{w_1-w_2}{w_1}\right|},\qquad w_1\ne0.
\]

The result is a **percentage** relative to the fine-grid displacement. The code also reports the associated dimensional interval centered at \(w_1\):

\[
\left[w_1-|w_1|\frac{\mathrm{GCI}_{21}(\%)}{100},\;
      w_1+|w_1|\frac{\mathrm{GCI}_{21}(\%)}{100}\right].
\]

**This interval is an estimated error band, not a mathematically guaranteed bound.** Its interpretation relies on being sufficiently close to the asymptotic regime. Section 7.2 specifically identifies agreement of the observed \(p\) with a known theoretical order as strong evidence of asymptotic convergence. For the present 3D discretization, this script does **not** invent such a theoretical order: it reports \(p\) for scientific assessment.

Section 7.2 **recommends**, rather than mandates, successive refinement ratios greater than **1.3**. The software records the actual ratios \(r_{21}\) and \(r_{32}\). It introduces a **separate study-specific selection gate**, requiring both ratios to exceed the value of `--min-refinement-ratio` (default 1.3). A user-specified value other than 1.3 is **not** an ASME recommendation. The numerical GCI is reported independently even if the ratio gate fails.

## 6. Software decision rule (not a normative assertion of convergence)

For each *predeclared* three-mesh triplet, the numerical calculations produce
\(p\), \(w_{\mathrm{ext}}\), \(\mathrm{GCI}_{21}\), and the two refinement ratios.
There are **three distinct levels of reporting**:

1. **Numerical GCI estimate available:** three finite displacements permit a positive observed order \(p\) and a nonzero fine-grid displacement. An invalid fit is reported, not silently repaired.
2. **GCI below the study threshold:** the valid three-grid GCI satisfies \(\mathrm{GCI}_{21}\leq\tau\). Here \(\tau\) is chosen by the analyst, **not** specified by ASME V&V 10.1; for example, `--tolerance-pct 0.5` means 0.5%.
3. **Eligible for selection under the software policy:** in addition to (2), *both* refinement ratios exceed the user-defined minimum `--min-refinement-ratio`. This extra gate is a deliberately chosen **software policy**, not a mandatory ASME acceptance test. The program retains the **first eligible fine mesh** according to the predeclared ordering.

These conditions are recorded **separately** as `gci_valid_estimate`,
`meets_tolerance`, `study_minimum_ratios_met`, and `eligible_for_selection` in
`convergence.csv`. The second field denotes **only** whether the valid numerical
GCI falls below \(\tau\); it is possible for the GCI threshold to be met
but the mesh to be ineligible under the separate refinement-ratio gate.

### What the result does and does not establish

- **`gci_selection_criterion_met`** (final `status`): a mesh has been selected under the **study's numerical rule**. It does **not** establish that the asymptotic range was independently verified.
- **`gci_selection_criterion_not_met`** (final `status`): no mesh in the completed set satisfies the study's selection rule.
- **`in_progress`** and **`failed`**: the study is incomplete or has encountered a failure; neither is a mesh-convergence conclusion.
- **`asymptotic_regime_status: not_assessed`**: the program reports observed \(p\) and mesh histories, but performs **no independent test** proving that neglected higher-order terms in the Richardson expansion are small.
- **`converged: null`** in **both** modes: neither a GCI-threshold test nor a two-mesh relative-change test proves convergence independently. In `relative` mode, the final status is `relative_change_criterion_met` or `relative_change_criterion_not_met`, explicitly **not** an ASME GCI result.

Even if the computed GCI is small, it is a **conditional estimate of longitudinal discretization uncertainty for the monitored response** with transverse approximation held fixed. In the ASME example, comparison between a known theoretical order and the observed order provides additional evidence of asymptotic behavior. For the present H8 case, the program **does not impose or assume a theoretical order**. A researcher must examine the displacement sequence, the observed orders and any independent evidence before describing the asymptotic regime in a paper. No convergence of the full three-dimensional displacement field, transverse discretization, stresses or strain energy is claimed.

The program's exit code `0` means **its numerical selection criterion is met**, not that the ASME V&V process is complete. Exit code `2` means no eligible selection from the supplied meshes; `1` denotes a runtime failure.

## 7. Predetermining triplets: a software policy, not an ASME equation

The mathematical GCI formula requires three solved meshes. **ASME V&V 10.1,
Section 7.2 does not prescribe an algorithm for choosing arbitrary triplets
from an investigator-supplied list of many mesh sizes.** Our implementation
must therefore document its triplet-selection policy separately.

Before reading any displacement results, the software selects from the
`--nx` schedule, for each eligible fine resolution, the closest available
medium and coarse resolutions whose successive ratios exceed the selected
minimum. If no such combination exists, the nearest three levels are retained
for diagnostic purposes, with ratio warnings and **no automatic selection**
under the study rule.

An author who wishes to prescribe the triplets in advance can repeat:

```text
--gci-triple COARSE_NX MEDIUM_NX FINE_NX
```

All three values must occur in `--nx` in strictly increasing order. Only
these explicitly listed fine levels receive GCI evaluations in this mode.
Triplets and their ratios are preserved in the manifest and result reports.
Neither automatic selection policy is a claim of ASME endorsement or of
independently established asymptotic convergence. The investigator should
report the **actual triplet used**, not merely the selected fine-grid size.

## 8. Running the tool (illustrative case-specific invocation)

Install the script as either `fem3d/converge_opensees_csf.py` or
`tools/converge_opensees_csf.py`. The existing OpenSees driver is **not modified**.
For an unambiguous invocation, specify its actual path explicitly:

```bash
python tools/converge_opensees_csf.py \
  cases/i_shaped_taper80_lagrangeL9_v4_E10_web3_composite.yaml \
  --driver fem3d/run_opensees_csf.py \
  --method gci \
  --nx 20 40 60 80 100 125 \
  --nu 6 --nv 6 \
  --point 1000 -33 35 \
  --tolerance-pct 0.5 \
  --run-all \
  --output-root fem3d/convergence_gci
```

The program also checks for `run_opensees_csf.py` alongside the script and
under the case directory's `fem3d/` folder if `--driver` is omitted, but for
reproducibility an explicit `--driver` is recommended.

Values of `--nu` and `--nv` are chosen by the researcher and held fixed
**within** the longitudinal convergence study; they are not hard-coded.
The point coordinates are in the physical axes/units of the FEM3D checkpoint.
Do not assume that a point on the original CSF section also lies in the free
section of a tapered beam.

An explicitly predetermined triplet may instead be requested with:

```text
--gci-triple 40 80 125
```

This selects *which meshes are analyzed*, not which numerical results are
favorable. With `--run-all`, all listed mesh solutions are saved even after an
eligible triplet has been found, so the full sequence can be inspected.

To request the old **non-GCI** relative-change criterion, use `--method relative`.
It is a different method, reports only a two-mesh threshold, and must not be cited as ASME GCI or as independent proof of convergence.

Reuse of a solved checkpoint is allowed with `--reuse-npz NX=FILE.npz` only
when the saved `nx/nu/nv` and case identifier match. In addition, the user must
confirm that model, loads and material definitions are identical: matching
file names or case names alone are insufficient to establish this.

To refresh reports for a **completed** v03 run after replacing this script with
v03.1, use `--resume` and the **same original case and driver**:

```bash
python tools/converge_opensees_csf.py \
  cases/i_shaped_taper80_lagrangeL9_v4_E10_web3_composite.yaml \
  --driver fem3d/run_opensees_csf.py \
  --resume fem3d/convergence_gci/run_0001
```

A completed run is reanalyzed from saved metrics **without rerunning OpenSees**;
an incomplete run continues unfinished meshes. The legacy v03 manifest is
accepted without changing the numerical GCI formula or triplet plan. The
result files record both the new reporting version and original manifest
version.

## 9. Reports, traceability and numerical tests

Each execution is placed in a new numbered `run_XXXX/` directory with the
immutable manifest and separate solved H8 NPZ per mesh. A completed v03 run
can be reevaluated with the corrected reporting semantics described above.

- `manifest.json`: source-file fingerprints, fixed transverse resolution, observed physical point, solver path, predeclared mesh schedule and GCI triplets, and study-specific thresholds.
- `convergence.csv`: physical point displacement, H8 mesh counts, triplet IDs, \(r_{21}\), \(r_{32}\), \(p\), Richardson estimate and GCI **plus separate threshold and selection eligibility columns**.
- `convergence.md`: mathematical interpretation, complete mesh table and an explicitly conditional selected fine mesh, if any.
- `convergence_result.json`: `status` is **`gci_selection_criterion_met`** or **`gci_selection_criterion_not_met`** when finished, `gci_threshold_met_any_valid_triplet` records whether any valid numerical GCI falls below the threshold (or is `null` when none is evaluable), `gci_selection_criterion_met` records the additional software gate, `asymptotic_regime_status` is **`not_assessed`**, and `converged` is **`null`** in either method. The older `gci_acceptance_threshold_met` field remains an alias of `gci_threshold_met_any_valid_triplet` for compatibility, not an assertion of model convergence. All selected mesh and NPZ fields refer only to the **study-defined** selection rule.
- `uz_point_convergence.png`, `gci_convergence.png`, `observed_order.png`: displacement, conditional GCI estimate and observed-order plots; none establishes asymptotic behavior automatically.

The OpenSees driver and CSF model are unchanged. The script accesses mesh
coordinates, connectivity and solved nodal displacements stored in the FEM
checkpoint. Any FEM H8 inverse mapping is used **only for evaluation of the
saved FEM displacement field**, not to reconstruct CSF physical geometry,
material regions or constitutive laws. The driver obtains the latter through
the CSF public APIs.

### Tests and validation limitations

Run:

```bash
python -m unittest discover -s tests -v
```

Regression tests include ASME V&V 10.1-2012, Section 7.2, Table 2 (reported
\(p\simeq2.00256\), \(\mathrm{GCI}\simeq0.12838\%\)), as well as unequal
ratios, non-monotonic sequences, validity checks, H8 point evaluation, and the
status/reporting distinction. These tests establish **correct arithmetic and
software reporting on known or synthetic examples**; they are **not** a new
OpenSees convergence study and do not demonstrate that any particular real
mesh is asymptotic.

## Bibliographic reference

**[ASME V&V 10.1]** American Society of Mechanical Engineers (ASME). *An Illustration of the Concepts of Verification and Validation in Computational Solid Mechanics*. ASME V&V 10.1-2012 (R2022), Section 7.2, **Calculation Verification**. New York: ASME, 2012; reaffirmed 2022. [Official ASME catalog entry](https://www.asme.org/codes-standards/find-codes-standards/an-illustration-of-the-concepts-of-verification-and-validation-in-computational-solid-mechanics/2012/pdf).

### Paper-ready methodological statement (no case-specific dimensions)

> The longitudinal discretization sensitivity of the FEM3D model was assessed through the three-grid Richardson extrapolation and Grid Convergence Index (GCI) procedure illustrated in ASME V&V 10.1-2012 (R2022), Section 7.2. The transverse finite-element subdivision was fixed throughout each refinement sequence, and the monitored quantity was the vertical displacement at a single, unchanged physical point. The observed order of convergence was inferred from three solutions, accounting for unequal mesh-size ratios, and the fine-grid GCI was evaluated using a safety factor of 1.25. A numerical GCI acceptance threshold and an additional minimum-refinement-ratio gate were specified as **study-specific selection criteria**, rather than ASME-prescribed convergence requirements. A fine mesh meeting these criteria was designated as the reference configuration for subsequent displacement comparisons; this designation does not, by itself, demonstrate that the asymptotic convergence regime has been reached. The reported GCI is therefore interpreted conditionally under the assumed Richardson error expansion and only for longitudinal discretization of the selected displacement response. No claim of transverse-discretization or full-field convergence follows from this test.
