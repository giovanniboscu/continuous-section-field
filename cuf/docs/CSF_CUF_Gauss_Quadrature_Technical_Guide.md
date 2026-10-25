# CSF–CUF Gauss Quadrature: Transverse and Longitudinal Integration

**Technical implementation guide and numerical verification protocol**  

**Scope:** CSF–CUF solver, transverse-expansion plugins, polygonal-section integration, longitudinal finite-element integration, and the sectional `J`-coefficient Gauss-order diagnostic.  
**Reference implementation:** Lagrange L9 v7.1 is included as an illustrative transverse expansion; the general order-selection procedure applies to all registered CUF bases.  

> **Key distinction.** CSF–CUF uses **two independent Gauss quadratures**. Transverse quadrature evaluates coefficients on the cross-section $\Omega(x)$, in physical coordinates $(y,z)$. Longitudinal quadrature subsequently integrates the CUF finite-element terms along the beam axis $x$. Increasing one order does not automatically increase the other.

> **What has been verified.** The selection formulas, the polygon integrator, the longitudinal integrator, and the `CSF_CUF_J_GAUSS_DIAGNOSTIC` implementation were checked in the supplied source snapshot. The instructions below describe what the code does; they do **not** imply that a complete C-section or other structural benchmark has been executed for every suggested order.

---

## 1. Where the two integrations enter the CUF calculation

A typical CUF element stiffness contribution can be expressed schematically as

$$
K_e\;\sim\;\int_{x_e^-}^{x_e^+}
     \bigl(\text{longitudinal shape-function factors}\bigr)
     \;J(x)\;dx,
$$

where the **sectional coefficients** $J(x)$ contain cross-sectional integrals such as

$$
J_{\tau s}^{ab,mn}(x)
=\int_{\Omega(x)}
\bigl(D_a F_\tau\bigr)
\,C_{mn}(x,y,z)\,
\bigl(D_b F_s\bigr)\;d\Omega.
$$

Here $F_\tau$ and $F_s$ are transverse expansion functions, $D_a,D_b$ indicate either no derivative or a physical derivative, and $C_{mn}$ denotes an appropriate constitutive coefficient. This is a schematic representation of the matrix families assembled by `SectionalCoefficientProvider`; the complete CUF fundamental nucleus combines these families with the longitudinal finite-element operators.

Consequently, the numerical workflow is:

```text
Case YAML and CUF transverse-basis plugin
                 |
                 v
       SELECT TRANSVERSE GAUSS ORDER
                 |
                 v
FixedGaussPolygonIntegrator at each required x
                 |
                 v
 Sectional coefficient matrices J(x)
                 |
                 v
       SELECT LONGITUDINAL GAUSS ORDER
                 |
                 v
GaussLegendreLongitudinalIntegrator on each FE element
                 |
                 v
        CUF element matrices / assembly
```

The actual order selection is performed during solver initialization; the diagram emphasizes the mathematical dependency between the two integration levels.

---

## 2. YAML configuration and input defaults

A **representative case excerpt**, not a complete standalone case file, is:

```yaml
cuf:
  basis: ../expansions/lagrangeL9_v4.py
  order: 2

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 9

longitudinal:
  method: finite_element
  basis: lagrange
  order: 12
  elements: 10
  gauss_order: 15
```

The actual relative basis path must be valid **relative to the case YAML**. The full case also requires the applicable problem, output, and other project settings.

| YAML setting | Integration | Meaning |
|---|---|---|
| `section_integration.gauss_order` | Transverse | Requested Gauss–Legendre order for polygonal integration in $(y,z)$. |
| `longitudinal.gauss_order` | Longitudinal | Requested Gauss–Legendre order on **each** one-dimensional FE element along $x$. |
| `cuf.order` | Neither directly | Transverse expansion order; it influences the basis-plugin minimum and input defaults. |
| `longitudinal.order` | Neither directly | Longitudinal FE interpolation order; it influences the estimated longitudinal integration degree. |
| `longitudinal.material_polynomial_degree` | Longitudinal | Optional degree used by the longitudinal quadrature estimator for a varying constitutive law. |

In `cuf/case.py`, if the Gauss orders are **omitted**, the parser sets:

```python
section_gauss_default = cuf_default_order + 1
longitudinal_gauss_default = cuf_default_order + longitudinal_order + 1
```

For a non-segmented case, `cuf_default_order` is `cuf.order`; for a segmented transverse expansion, it is the maximum segment order. Values are subsequently checked: sectional order must be at least 2; longitudinal order must be at least 1. The solver can raise either effective order to meet its computed minimum.

**Do not confuse** the number of longitudinal elements with the number of longitudinal Gauss points. `elements: 10` and `gauss_order: 15` mean 10 FE elements, with a 15-point Gauss rule **per element**, not 15 points over the entire beam.

---

## 3. Transverse Gauss quadrature

### 3.1. Exact selection rule in the solver

The code in `cuf/solver/engine.py` evaluates the plugin's minimum and combines it with the requested order:

```python
requested_section_gauss_order = int(case.section_integration.gauss_order)
cuf_minimum_section_gauss_order = (
    basis_plugin.minimum_section_gauss_order(basis)
)
effective_section_gauss_order = max(
    requested_section_gauss_order,
    cuf_minimum_section_gauss_order,
)

section_integrator = FixedGaussPolygonIntegrator(
    order=effective_section_gauss_order
)
```

Thus,

$$
\boxed{n_\perp=\max(n_{\mathrm{YAML},\perp},\;n_{\mathrm{basis,min}})}.
$$

The **basis plugin declares a minimum**; it does not itself select the final order, and a larger requested YAML value is **never reduced**.

For L9 v7.1, `_section_gauss_minimum()` returns `3`.

| Requested transverse order | Effective L9 order |
|---:|---:|
| Omitted (`cuf.order = 2`) | 3 |
| 2 | 3 |
| 3 | 3 |
| 6 | 6 |
| 9 | 9 |
| 12 | 12 |

### 3.2. Minimum orders declared by the supplied expansion plugins

These are **plugin rules**, not universal mathematical guarantees for arbitrary geometric distortion.

| Expansion | Declared sectional minimum |
|---|---:|
| `scaled_maclaurin` | $N+1$ |
| `scaled_legendre` | $N+1$ |
| `scaled_taylor` | $N+1$ |
| `scaled_maclaurin_tensor` | $2N+1$ |
| `scaled_lagrange` | $N+2$ |
| `scaled_lagrange_q1` | 3 |
| `lagrangeL9` (v7.1) | 3 |
| `longitudinal_lagrange_blend` | Maximum declared minimum across its component bases or segments |

The actual rule for a custom basis is the value returned by its `section_gauss_minimum` registration hook.

### 3.3. How `FixedGaussPolygonIntegrator` creates the points

**Important implementation detail:** the integrator in this code snapshot performs **polygon slicing in physical $(y,z)$ coordinates**. It does **not** apply a simple tensor-product Gauss rule directly to the L9 natural square $(\alpha,\beta)$.

For a given CSF polygonal domain, the algorithm:

1. Collects the distinct $y$-coordinates of polygon vertices, including direct geometric exclusions, and creates consecutive $y$-subintervals.
2. Uses an $n_\perp$-point one-dimensional Gauss–Legendre rule inside each $y$-subinterval.
3. At each selected physical $y$, intersects the polygon with the line of constant $y$, finding the occupied $z$-intervals after exclusions.
4. Uses another $n_\perp$-point Gauss–Legendre rule on **each** occupied $z$-interval.
5. Returns the physical $(y,z)$ points together with the products of the Gauss weights and the two interval-mapping Jacobians.

At one occupied $z$-interval for one $y$-subinterval, an order $n_\perp$ creates $n_\perp^2$ point pairs. Thus, order 9 gives **81 point pairs for that particular rectangular slicing piece**, but the total number for a complete polygon or section depends on the number of subintervals and occupied slices. It is not always 81 points for an entire polygon.

The integrator applies the supplied order. It has **no automatic error estimator** that raises the order based on polygon distortion or on the variation of the L9 integrand.

### 3.4. Why general L9 quadrilaterals need a convergence study

For an axis-aligned rectangle with a suitable mapping, transverse basis derivatives and their products have a tractable polynomial form, and low-order Gauss rules can integrate the relevant polynomial terms exactly.

For a **general convex quadrilateral**, the L9 geometry uses a bilinear map:

$$
\mathbf r(\alpha,\beta;x)=
\sum_{a=1}^{4}Q_a(\alpha,\beta)\,\mathbf r_a(x).
$$

Its physical derivatives are related to natural derivatives by

$$
\nabla_{y,z}F_\tau
   =J^{-T}\nabla_{\alpha,\beta}F_\tau.
$$

For a genuinely non-affine bilinear map, $J$ changes across the section. The inverse Jacobian introduces rational factors into the physical derivatives. As a result, a stiffness integrand need **not** be a low-degree polynomial in the integration variables. Consequently:

- The plugin's minimum `3` is a **lower bound for the solver's order choice**, not a proof of exactness for every convex quadrilateral.
- An integrator using physical polygon slices is not equivalent to a natural-coordinate tensor-product rule; precision must be assessed for the rule **actually used**.
- Even an affine parallelogram should not be assumed exact at order 3 without considering the polynomial degree under the **physical slicing coordinates**.
- Quadrilateral distortion, small geometric features, and strongly varying constitutive data may increase the required order.

**Recommended action:** verify sectional coefficient convergence (rather than selecting a universal larger default based solely on the shape category).

---

## 4. Longitudinal Gauss quadrature

### 4.1. Selection rule

The solver follows the corresponding rule:

```python
requested_longitudinal_gauss_order = int(case.longitudinal.gauss_order)
minimum_longitudinal_gauss_order = int(
    longitudinal_requirement["minimum_gauss_order"]
)
effective_longitudinal_gauss_order = max(
    requested_longitudinal_gauss_order,
    minimum_longitudinal_gauss_order,
)

longitudinal_integrator = GaussLegendreLongitudinalIntegrator(
    quadrature_order=effective_longitudinal_gauss_order
)
```

Therefore,

$$
\boxed{n_x=\max(n_{\mathrm{YAML},x},\;n_{x,\min})}.
$$

Unlike the sectional minimum, $n_{x,\min}$ is estimated from several sources by `_longitudinal_gauss_requirement()` in `cuf/solver/engine.py`.

### 4.2. Current polynomial-degree estimator

The code builds an estimate

$$
D_x=
D_{\mathrm{transverse},x}
+ D_{\mathrm{geometry}}
+ D_{\mathrm{material}}
+ 2p,
$$

where:

- $D_{\mathrm{transverse},x}$ is declared through the transverse-basis plugin's `longitudinal_transverse_degree` hook (the implementation exposes it as `transverse_x_polynomial_degree`).
- $D_{\mathrm{geometry}}=2$ is a **fixed conservative contribution** for the changing cross-sectional measure; the code uses this value even for a prismatic section.
- $D_{\mathrm{material}}=0$ for constant material or `1` when the sampled constitutive law varies affinely, unless `longitudinal.material_polynomial_degree` explicitly overrides the estimate.
- $p$ is the longitudinal plugin's declared `polynomial_degree`.

Gauss–Legendre integration with $n$ points is exact for a one-dimensional polynomial of degree at most $2n-1$. Hence the source computes

$$
\boxed{n_{x,\min}=\left\lfloor\frac{D_x+2}{2}\right\rfloor}.
$$

This is the implemented **minimum-order estimator**, not an assertion that the actual integrand is always polynomial of degree $D_x$.

**Illustrative L9 case:** for a homogeneous material, `cuf.order: 2` (L9), a longitudinal basis of polynomial degree $p=12$, and the L9 plugin's declared transverse $x$-degree of zero:

$$
D_x=0+2+0+2(12)=26,
\qquad n_{x,\min}=14.
$$

If the YAML requests 15 longitudinal points, the effective order is 15. This calculation illustrates the **current code's selection rule**, not exact integration of a moving L9 section.

### 4.3. What the longitudinal integrator actually evaluates

`GaussLegendreLongitudinalIntegrator` (`cuf/solver/longitudinal.py`) creates Gauss–Legendre points and weights on the one-dimensional reference interval $[-1,1]$.

For **each FE element**, it maps each reference point to a physical longitudinal station $x$, evaluates longitudinal shape-function factors and their derivatives, and requests the appropriate sectional coefficients $J(x)$. The element Jacobian scales the Gauss weight.

Consequently, the transverse coefficient integration can be performed repeatedly at different longitudinal Gauss stations. For a non-prismatic CSF model, the section $\Omega(x)$ and, when applicable, the transverse basis and material properties are evaluated at those current stations.

### 4.4. Limitations of the longitudinal estimate

For a moving L9 basis on a bilinearly mapped quadrilateral, the dependence of physical derivatives on $x$ can be **non-polynomial**, even when every corner follows an exactly affine trajectory. The L9 plugin explicitly returns `0` from its transverse longitudinal-degree estimator as a baseline, with a comment warning that longitudinal convergence must be checked.

Accordingly, the code's automatic $n_{x,\min}$ **does not guarantee exact longitudinal quadrature** for such a case. The longitudinal Gauss order should be tested independently by rerunning the **same FE model** with larger `longitudinal.gauss_order` values.

**Source-review qualification:** the helper's docstring describes affine-geometry checks; in the supplied `engine.py` implementation, the explicit polygon tests at $x_0$, $x_m$, $x_1$ check domain count and vertex array shapes, but do not themselves verify the midpoint identity $\mathbf r(x_m)=(\mathbf r(x_0)+\mathbf r(x_1))/2$. Other components (including L9 v7.1) may impose stronger checks. Do not treat the longitudinal-order estimator, by itself, as a global certificate of affine geometry.

---

## 5. Built-in sectional `J` Gauss-order diagnostic

### 5.1. Purpose

`SectionalCoefficientProvider` includes an **observational** diagnostic that recomputes the **same sectional coefficient-matrix families $J$** with additional transverse Gauss orders at the **same physical longitudinal station $x$**.

Its purpose is to answer questions such as:

> If the main run uses transverse Gauss order 9, how much do the sectional coefficients change when the **transverse order alone** is increased to 12 or 16?

It does **not** replace the coefficients used in the physical solution, reassemble a different global stiffness matrix, or test longitudinal Gauss convergence.

### 5.2. Exact command to run

From a shell in the intended working directory, execute:

```bash
CSF_CUF_J_GAUSS_DIAGNOSTIC=1 \
CSF_CUF_J_GAUSS_ORDERS=12,16 \
csf-cuf percorso/caso.yaml
```

Replace `percorso/caso.yaml` with your actual case path. These are **environment variables** for this invocation; no YAML change is necessary to turn on the diagnostic.

If the case uses `section_integration.gauss_order: 9` and the basis minimum is 3, the main calculation still uses **order 9**, while the diagnostic recomputes requested families at **orders 12 and 16**.

The diagnostic's default candidate orders, when `CSF_CUF_J_GAUSS_ORDERS` is omitted, are `36,48` in this code snapshot. Specifying `12,16` overrides those defaults. Orders must be integers $\ge 2$; repeated orders are deduplicated and any candidate equal to the main order is skipped.

### 5.3. Output location and an optional override

By default the report is written relative to the process's **current working directory**:

```text
diagnostics/j_gauss_stability.tsv
```

You can explicitly choose the file path:

```bash
CSF_CUF_J_GAUSS_DIAGNOSTIC=1 \
CSF_CUF_J_GAUSS_ORDERS=12,16 \
CSF_CUF_J_GAUSS_REPORT=diagnostics/l9_section_gauss.tsv \
csf-cuf percorso/caso.yaml
```

The parent directory is created if necessary. When rows are first written in a new run, the implementation opens the report for **writing**, then appends subsequent rows during that process. Preserve or rename earlier reports before rerunning if you want a history of experiments.

### 5.4. What is compared internally

For each used matrix family and physical station $x$, the program obtains a base matrix $J_b$ at the main transverse order and a test matrix $J_t$ at a requested candidate order.

In the matrix integration path, the underlying sectional operation has the form

$$
J=B_{\mathrm{test}}^T\;\mathrm{diag}\!\bigl(w_q\,C_{mn,q}\bigr)\;B_{\mathrm{trial}},
$$

summed over all active CSF domains at the current $x$. The diagnostic recomputes the same families with newly generated physical Gauss points and weights.

The principal relative metric is

$$
\boxed{
\texttt{relative\_fro}
=\frac{\left\|J_t-J_b\right\|_F}
       {\max\!\left(\left\|J_b\right\|_F,
                     \left\|J_t\right\|_F\right)}
}
$$

with a result of zero if both reference and test family norms are zero.

**Note:** the denominator is the **maximum of the two Frobenius norms**, not simply the baseline norm. A zero or small metric indicates agreement **between those two numerical orders**; it does not, by itself, prove convergence to an exact analytical integral.

### 5.5. Important TSV columns

| Column | Meaning |
|---|---|
| `x` | Physical longitudinal coordinate where the sectional families were compared. |
| `test_derivative`, `trial_derivative` | Transverse-basis factor selectors (`None`, `x`, `y`, or `z`). |
| `m`, `n` | Constitutive-matrix indices of the selected coefficient family. |
| `basis_size` | Transverse basis dimension. |
| `base_gauss`, `test_gauss` | Main sectional order and the diagnostic order. |
| `reference_fro`, `test_fro` | Frobenius norms of the two sectional matrices. |
| `diff_fro` | Frobenius norm of their difference. |
| `relative_fro` | Relative family-matrix difference as defined above. |
| `reference_max_abs`, `test_max_abs` | Largest absolute coefficient magnitude in each matrix. |
| `max_abs_diff` | Largest absolute entrywise difference. |
| `max_abs_diff_over_family_scale` | Largest absolute difference normalized by the larger matrix maximum-absolute entry (zero if both are zero). |
| `max_abs_tau`, `max_abs_s` | One-based transverse indices locating the largest absolute difference. |
| `reference_at_max_abs`, `test_at_max_abs` | Base/test coefficient values at that location. |

This is a **tab-separated values** file (`.tsv`), not a comma-separated CSV.

### 5.6. Simple report-summary command (optional)

After a completed run, the following **Python standard-library** snippet summarizes the largest relative family difference observed for each candidate order:

```bash
python3 - <<'PY'
import csv
from collections import defaultdict
from pathlib import Path

path = Path('diagnostics/j_gauss_stability.tsv')
max_error = defaultdict(float)
count = defaultdict(int)

with path.open(newline='', encoding='utf-8') as stream:
    for row in csv.DictReader(stream, delimiter='\t'):
        order = int(row['test_gauss'])
        error = float(row['relative_fro'])
        max_error[order] = max(max_error[order], error)
        count[order] += 1

for order in sorted(count):
    print(f'test Gauss {order:>3}: '
          f'max relative_fro={max_error[order]:.6e}; '
          f'families compared={count[order]}')
PY
```

This deliberately reports the **worst** family difference for each candidate order across the sampled $x$ stations. For scientific reporting, also inspect which family and $x$ produce the maximum, and consider both absolute and relative errors.

### 5.7. How to interpret the diagnostic responsibly

- **Small and decreasing** differences between order 9 and orders 12/16 provide evidence of **sectional quadrature stability** for the sampled case.
- **Large** differences indicate that the baseline sectional order may be insufficient, or that a particular matrix family is numerically delicate.
- A tiny `relative_fro` alongside a large local `max_abs_diff` can warrant closer inspection of individual entries.
- A large relative difference in a nearly zero family may be less relevant than a similar difference in a dominant stiffness contribution; examine `reference_fro`, `test_fro`, and absolute differences.
- Comparing only 9 and 12 is weaker than also observing stability between 12 and 16 (or other higher orders). The built-in report compares each candidate to **the main baseline**; it does not directly produce a 12-versus-16 row unless you run a separate case with 12 as the baseline.
- The diagnostic covers **sectional families used along the actual execution path**, at the physical $x$-stations reached. It is not a universal proof for every possible geometry or every $x$ in the beam.

There is **no universal pass/fail tolerance** in the diagnostic. Appropriate acceptance criteria depend on the intended accuracy, response quantities, material contrast, conditioning, and reference data.

### 5.8. What the diagnostic does *not* change

According to `cuf/core/sectional.py`, the recomputed diagnostic matrices are **not** placed into the physical coefficient cache. The baseline matrices remain the ones used by the normal solver. The diagnostic may increase runtime and memory usage because it evaluates additional quadrature points and complete matrix families.

It is **not** a diagnostic of the longitudinal Gauss order; it is **not** an adaptive integration method; it is **not** a replacement for mesh convergence, physical field validation, or comparison with FEM3D.

---

## 6. Practical, independent convergence protocols

### 6.1. Protocol A — Transverse quadrature only

1. Keep the CSF geometry, material laws, loads, boundary conditions, transverse expansion, FE mesh, and **longitudinal Gauss order** unchanged.
2. Choose a baseline transverse order, such as 9, via `section_integration.gauss_order`.
3. Enable `CSF_CUF_J_GAUSS_DIAGNOSTIC=1` and request higher sectional orders such as `12,16`.
4. Inspect `relative_fro` and `max_abs_diff` over the whole TSV; identify the worst $J$-families and longitudinal stations.
5. If the differences remain significant, increase the baseline transverse order and repeat. Optionally run a second solve at the higher baseline to check that the resulting displacements, stresses, and strain energy are also stable.

For strongly distorted L9 quadrilaterals, pay particular attention to derivative-containing families and points where the isoparametric Jacobian is small, even when the quadrilaterals remain convex.

### 6.2. Protocol B — Longitudinal quadrature only

The sectional `J` diagnostic **cannot perform this test**. Instead:

1. Hold `section_integration.gauss_order` fixed at a level established as adequate by Protocol A.
2. Keep the FE partition, `longitudinal.order`, loads, and material laws fixed.
3. Run the **same case** at progressively larger `longitudinal.gauss_order` values (for example 15, 18, and 21), creating separate output directories or archiving the results.
4. Confirm the **effective** order printed by the solver; an automatic minimum can raise a requested value.
5. Compare selected physical displacements, stresses, reactions, and (where available) strain energy or stiffness diagnostics. Differences between successive runs should decrease to the target numerical tolerance.
6. Only after integration is stable, separately study **longitudinal mesh** or **polynomial-order** convergence. Increasing Gauss points does not refine the finite-element approximation space.

### 6.3. Recommended reporting table

Record actual values from your runs rather than interpreting the plugin minimum as an accuracy guarantee.

| Case | Section order (effective) | Longitudinal order (effective) | Worst `relative_fro` on J | Displacement of interest | Stress of interest | Observation |
|---|---:|---:|---:|---:|---:|---|
| Baseline | 9 | 15 | *to be measured* | *to be measured* | *to be measured* | Starting point |
| Section check | 12 | 15 | *to be measured* | *to be measured* | *to be measured* | Vary transverse quadrature only |
| Section check | 16 | 15 | *to be measured* | *to be measured* | *to be measured* | Confirm sectional stability |
| Longitudinal check | 16 | 18 | *to be measured* | *to be measured* | *to be measured* | Vary longitudinal quadrature only |
| Longitudinal check | 16 | 21 | *to be measured* | *to be measured* | *to be measured* | Confirm axial integration stability |

*In the longitudinal check rows, `relative_fro` may be omitted unless the sectional diagnostic is also enabled; it is not a longitudinal error indicator.*

---

## 7. Practical notes and restrictions

1. **Minimum versus exactness.** `n_basis,min` is a plugin-declared minimum. It does not guarantee exactness for all geometries, constitutive laws, and derivatives.
2. **Two different variable sets.** Sectional integration uses the physical transverse coordinates $(y,z)$ for each current $x$; the longitudinal integrator uses the reference coordinate of each 1D FE element and maps it to physical $x$.
3. **L9 geometric requirements.** The mathematical L9 mapping assumes admissible, non-degenerate, consistently oriented quadrilateral mappings. Geometric validity and conformity of interfaces are independent of the selection of Gauss order. More Gauss points cannot repair an inverted mapping or a nonconforming transverse approximation.
4. **Affine corner motion is not polynomial L9 motion in physical coordinates.** Even if corner trajectories are linear in $x$, inverse isoparametric mappings may lead to non-polynomial sectional or longitudinal integrands.
5. **The diagnostic is opt-in.** With `CSF_CUF_J_GAUSS_DIAGNOSTIC` unset, no extra sectional-order stability calculation is requested.
6. **Cost.** Increasing transverse order may multiply the number of physical integration points over every active polygon and every longitudinal station; diagnostic candidate orders incur additional work but do not alter the main solution.
7. **Source-snapshot limitation.** Statements in this guide are based on the uploaded source, not on an independent execution of your complete benchmark with the specified settings.

---

## 8. Source-code map (verified in the supplied snapshot)

All paths below are relative to the archive's `cuf/` directory.

| File | Relevant location | Responsibility |
|---|---|---|
| `case.py` | Approximately lines 250–360 | Reads Gauss-order YAML values and computes input defaults; validates minimum accepted input values. |
| `core/basis_plugins.py` | `minimum_section_gauss_order()` and `transverse_x_polynomial_degree()` | Provides the transverse-plugin numerical requirements. |
| `expansions/lagrangeL9_v4.py` | `_section_gauss_minimum()` and `_longitudinal_transverse_degree()` | L9 plugin minimum of 3; moving-L9 longitudinal degree heuristic of 0. |
| `solver/engine.py` | Approximately lines 1022–1053 | Selects effective **sectional** Gauss order and constructs `FixedGaussPolygonIntegrator`. |
| `numerics/integration.py` | `FixedGaussPolygonIntegrator` | Generates physical polygonal $(y,z)$ Gauss points and weights, including section slicing and exclusions. |
| `core/sectional.py` | Approximately lines 140–225, 354–600, 1012–1175 | Configures the J-order diagnostic, recomputes J families, writes TSV metrics, and constructs the baseline J matrices. |
| `solver/engine.py` | `_longitudinal_gauss_requirement()` and approximately lines 1069–1123 | Estimates polynomial degree, selects effective **longitudinal** order, constructs longitudinal Gauss integrator. |
| `solver/longitudinal.py` | `GaussLegendreLongitudinalIntegrator` | Generates the 1D Gauss–Legendre points/weights and maps them through each longitudinal element. |
| `solver/element.py` | `_longitudinal_quadrature_data()` / element-matrix assembly | Evaluates FE shape factors and sectional coefficients at longitudinal quadrature stations. |

### Main commands: quick reference

**Run a standard configured case:**

```bash
csf-cuf percorso/caso.yaml
```

**Check sectional J coefficients with transverse orders 12 and 16:**

```bash
CSF_CUF_J_GAUSS_DIAGNOSTIC=1 \
CSF_CUF_J_GAUSS_ORDERS=12,16 \
csf-cuf percorso/caso.yaml
```

**Write the diagnostic to an explicit location:**

```bash
CSF_CUF_J_GAUSS_DIAGNOSTIC=1 \
CSF_CUF_J_GAUSS_ORDERS=12,16 \
CSF_CUF_J_GAUSS_REPORT=diagnostics/j_gauss_stability.tsv \
csf-cuf percorso/caso.yaml
```

**Longitudinal convergence:** edit only `longitudinal.gauss_order` between otherwise identical case runs; there is no equivalent built-in `J_GAUSS` flag for longitudinal quadrature in the inspected source.

---

## 9. Scientific conclusion

The quadrature-order selection architecture in the inspected CSF–CUF source is well separated: **each transverse basis declares a minimum**, the **solver selects the maximum of that minimum and the user request**, and **the integration backend executes the selected order**. The same maximum-rule principle is used longitudinally, with a polynomial-degree-based automatic minimum.

For a general convex L9 quadrilateral, the **sectional minimum of three Gauss points is not an exactness guarantee**. A practical and already implemented verification is to use `CSF_CUF_J_GAUSS_DIAGNOSTIC` to compare the sectional **J** matrices at progressively larger transverse orders. The test is observational and keeps the physical solution's baseline order unchanged.

For **longitudinal quadrature**, especially with moving isoparametric L9 functions, the automatic degree estimate is only a baseline: run a separate convergence series with higher longitudinal Gauss orders while keeping the transverse quadrature and FE discretization fixed.

**Recommended scientific evidence:** report both (a) sectional `J`-family stability under transverse order refinement and (b) structural-response stability under longitudinal Gauss-order refinement. Keep these two checks distinct from FE mesh refinement and comparison with a three-dimensional reference solution.
