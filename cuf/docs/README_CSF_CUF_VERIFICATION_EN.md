# CSF-CUF Numerical Verification: Global Symmetry and Sectional Coefficients

**Status:** Technical documentation for the currently installed global stiffness symmetry check, the existing Gauss-order diagnostic, and a **proposed (not yet implemented)** cross-check of sectional coefficients.

**Relevant files:**

- `src/csf/cuf/solver/engine.py` - global stiffness symmetry verification (added to the local installation using `apply_engine_symmetry_check.py`).
- `src/csf/cuf/core/sectional.py` - sectional coefficient integration, matrix-family calculations, scalar `J_domain` integration, and existing Gauss-order diagnostics.

This document distinguishes an **internal algebraic consistency check** from **independent numerical validation**. Neither should be described as a proof that the physical stiffness or every sectional coefficient is correct.

---

## 1. Verification status at a glance

| Verification | Current status | Purpose | Changes numerical results? |
|---|---|---|---|
| Global stiffness symmetry, `K` versus `K.T` | **Installed locally** in `engine.py` | Confirm that the assembled global stiffness is symmetric within a configurable relative tolerance | **No** |
| Sectional `J` Gauss-order stability | **Already available** in `sectional.py`; optional | Assess sensitivity of sectional coefficients to quadrature order | **No** |
| Cross-check of matrix-family `J` against scalar `J_domain` | **Proposed only; not installed** | Detect discrepancies between two computational paths for selected sectional coefficients | **No**, as designed |
| Block-by-block CUF reciprocity | **Proposed only** | Localize asymmetry through `K_(tau,s)` versus `K_(s,tau).T` | **No**, as designed |

> **Important:** The new `CSF_CUF_SYMMETRY_RTOL` environment variable controls **only the installed global symmetry test**. The proposed cross-check has no working activation variable yet. Do not assume it is running.

## 2. Global stiffness symmetry check (implemented)

### 2.1 Where it runs

The check is executed immediately after:

```python
stiffness = CSFCUFGlobalAssembler(
    element_matrix_builder=element_builder,
).assemble(
    mesh=mesh,
    dof_layout=dof_layout,
)
```

It operates on the original global stiffness matrix `stiffness` (`K`):

1. **After** global stiffness assembly.
2. **Before** load assembly and constraints.
3. **Before** KKT matrix construction and linear solution.
4. **Once per stiffness assembly**, not once per later equilibration attempt.

It checks the **entire global `K`**, rather than individual CUF blocks. The KKT matrix is **not separately checked** by this new test.

### 2.2 Mathematical definition

Let

```math
D=K-K^T.
```

The acceptance metric is the **global relative asymmetry**:

```math
\boxed{\varepsilon_{\mathrm{sym}}=\frac{\|K-K^T\|_F}{\|K\|_F}}
```

where the Frobenius norm is

```math
\|A\|_F=\sqrt{\sum_{i,j}|A_{ij}|^2}.
```

Equivalently,

```math
\varepsilon_{\mathrm{sym}}
=\sqrt{\frac{\sum_{i,j}|K_{ij}-K_{ji}|^2}
{\sum_{i,j}|K_{ij}|^2}}.
```

A second, **informational** metric is also printed:

```math
\Delta_{\max}=\max_{i,j}|K_{ij}-K_{ji}|.
```

Only `relative` is compared with `rtol`; `maximum_abs` is **not an independent stop criterion**.

The test does **not** replace `K` by `(K + K.T) / 2`, nor does it overwrite any coefficient.

### 2.3 Configurable acceptance threshold

| Setting | Value |
|---|---|
| Environment variable | `CSF_CUF_SYMMETRY_RTOL` |
| Default | `1e-10` |
| Accepted input | Finite, non-negative Python floating-point value |
| Failure condition | `relative > rtol` or non-finite matrix-norm diagnostics |
| Side effect | Check configuration only; no stiffness modification |

A smaller `rtol` makes the test **stricter**; a larger value makes it **more permissive**. Relaxing the threshold does **not** correct an asymmetric matrix.

**Linux / macOS - single invocation**

```bash
CSF_CUF_SYMMETRY_RTOL=1e-12 csf-cuf cases/bending_taylor_N04.yaml
```

**Linux / macOS - current shell session**

```bash
export CSF_CUF_SYMMETRY_RTOL=1e-12
csf-cuf cases/bending_taylor_N04.yaml
unset CSF_CUF_SYMMETRY_RTOL
```

**Windows PowerShell**

```powershell
$env:CSF_CUF_SYMMETRY_RTOL = "1e-12"
csf-cuf cases/bending_taylor_N04.yaml
Remove-Item Env:CSF_CUF_SYMMETRY_RTOL
```

**Windows Command Prompt (`cmd.exe`)**

```bat
set CSF_CUF_SYMMETRY_RTOL=1e-12
csf-cuf cases/bending_taylor_N04.yaml
set CSF_CUF_SYMMETRY_RTOL=
```

The case paths are illustrative and must be resolved relative to the actual case working directory. No YAML change is required.

### 2.4 Example of an observed result

A real `bending_scaled_lagrange_N04` run reported:

```text
[verification] global stiffness symmetry: relative=1.340513e-16 maximum_abs=1.464844e-03 rtol=1.0e-10
```

| Field | Meaning |
|---|---|
| `relative` | `||K - K.T||_F / ||K||_F`: acceptance metric |
| `maximum_abs` | Largest elementwise absolute difference between transposed entries |
| `rtol` | Effective tolerance, either the environment override or the default |

Here `1.340513e-16` is far below `1e-10`, so the check passes. The absolute difference `1.464844e-03` must be interpreted in relation to the scale of the stiffness coefficients; it is not a failure by itself.

This verifies numerical symmetry of **this particular assembled matrix**, to approximately double-precision roundoff on the global metric. It does **not** independently validate the stiffness magnitudes.

### 2.5 What happens if the check fails?

If the measured relative asymmetry exceeds `rtol`, the code raises a `RuntimeError` before loads, constraints, KKT construction, or solving:

```text
RuntimeError: CSF-CUF assembled stiffness is not symmetric: relative=..., rtol=...; no symmetrization has been applied
```

An invalid `CSF_CUF_SYMMETRY_RTOL` (unparseable, negative, `nan`, or infinite) is rejected. A zero matrix is handled without dividing by zero, but the check **does not establish invertibility or positive definiteness**.

Previously written outputs are not automatically removed. A failed run does not produce a newly completed solution for that attempt.

### 2.6 Why this matters for the dense solver

When SciPy is called with `assume_a="sym"`, the solver is **told** to use a symmetric-matrix algorithm. That parameter is **not itself a symmetry test**. A non-symmetric matrix can produce a misleading solution or an error when passed through a symmetric-only method. Explicit verification of `K` therefore provides a meaningful additional safeguard.

Note that checking `K` before constraints is not the same as independently checking the later KKT matrix. A residual check after solution is also a separate test.

## 3. Existing sectional `J` Gauss-order stability diagnostic

The code in `src/csf/cuf/core/sectional.py` already provides a **purely observational** quadrature-order stability diagnostic for sectional `J` families.

Enable it on Linux or macOS with:

```bash
CSF_CUF_J_GAUSS_DIAGNOSTIC=1 \
CSF_CUF_J_GAUSS_ORDERS=36,48 \
csf-cuf cases/bending_taylor_N04.yaml
```

Relevant existing settings:

| Environment variable | Role |
|---|---|
| `CSF_CUF_J_GAUSS_DIAGNOSTIC` | Enables the diagnostic when set to `1`, `true`, `yes`, or `on` |
| `CSF_CUF_J_GAUSS_ORDERS` | Comma-separated test orders; default `36,48` when enabled |
| `CSF_CUF_J_GAUSS_REPORT` | Optional alternative report location |

Default report path:

```text
diagnostics/j_gauss_stability.tsv
```

The diagnostic recomputes selected `J` matrix families at additional Gaussian quadrature orders. It does **not** replace or modify the coefficients used by the normal analysis.

**Scope:** This checks *quadrature stability*, not agreement between independently implemented integration algorithms. Stable results from two quadrature orders can still share a modeling or implementation error.

## 4. Proposed cross-check: matrix-family `J` versus scalar `J_domain`

**Implementation status: NOT IMPLEMENTED by the global symmetry patch.** This section specifies a possible additional diagnostic; the commands in Section 2 do not activate it.

### 4.1 Motivation

A matrix can be exactly symmetric even if the numerical stiffness is wrong. The global symmetry test detects asymmetric inconsistencies, but it cannot detect a common error repeated consistently in reciprocal terms.

In the current sectional code, one computational path builds a complete coefficient family for all ordered CUF pairs using matrix/batched operations. A scalar path is available through `J_domain(...)`, which integrates a single requested domain contribution. In this document, **“batched `J`” is a descriptive name for the matrix-family path**, not a promise that a callable named `J_batch()` exists in every version.

These two paths could be evaluated for identical physical data and compared on a selected sample of coefficients.

### 4.2 Coefficients to compare

For a fixed axial station `x`, domain `k`, constitutive indices `(m,n)`, derivatives `(phi,xi)`, and ordered CUF pair `(tau,s)`:

```math
J_{\tau,\phi\,s,\xi}^{mn,k}(x)
=\int_{\Omega^k(x)}
F_{\tau,\phi}(y,z)\,C_{mn}^k(x,y,z)\,
F_{s,\xi}(y,z)\,d\Omega.
```

Compare the total across the same set of physical CSF domains:

```math
J_{\mathrm{matrix}}(x)
\quad\text{versus}\quad
J_{\mathrm{scalar}}(x)=\sum_k J_{\mathrm{domain}}^{k}(x).
```

Both paths must use **the same geometry, material carriers, coordinate conventions, indices, and derivative definitions**.

### 4.3 Suggested acceptance criteria

An absolute-plus-relative criterion is preferable to dividing by a near-zero coefficient:

```math
\boxed{
|J_{\mathrm{matrix}}-J_{\mathrm{scalar}}|
\leq
\mathrm{atol}
+\mathrm{rtol}\,\max\bigl(|J_{\mathrm{matrix}}|,|J_{\mathrm{scalar}}|\bigr)
}
```

Report also the raw absolute difference and a scale-normalized error. The `atol` and `rtol` values should be chosen from representative benchmark scales and numerical precision rather than being declared universal constants.

### 4.4 Recommended sampling and reporting

To limit cost, make the diagnostic optional and sample:

- Multiple longitudinal stations, including endpoints/interior stations where the section or material varies.
- Multiple CSF domains and any distinct material carriers.
- Diagonal, mixed-derivative, and off-diagonal constitutive terms used by the CUF nucleus.
- Both ordered pairs `(tau,s)` and `(s,tau)` for reciprocal coefficients.
- Coefficients expected to be zero, nearly zero, positive, and negative.

For every tested coefficient, record `x`, domain, derivative selectors, `(m,n)`, `(tau,s)`, values from both paths, absolute error, relative/combined tolerance result, and Gauss order/integrator metadata. Include maximum discrepancy and failure counts in a summary report.

The diagnostic should run **before the final stiffness assembly or as an isolated test**, and must never alter production `J` values or symmetrize the resulting stiffness.

### 4.5 How independent would it be?

A comparison between the batched matrix-family calculation and `J_domain` is a useful **implementation-level cross-check**, but not necessarily a fully independent numerical integration:

- The two paths can share the same CSF geometry, material field, basis evaluation logic, and quadrature rule.
- If they use exactly the same quadrature points and weights, agreement is a check of their algebraic/numerical implementation, **not** of quadrature convergence.
- A stronger check would create an independent integration context or a higher-order/adaptive quadrature for the scalar path, avoiding reuse of the batch result and its caches.
- Even such a comparison cannot reveal shared mistakes in the physical model or constitutive assumptions.

Consequently, **separate algorithms, separate caches, and different quadrature settings** should be preferred when practical for the diagnostic.

### 4.6 Proposed future configuration (not active)

If this additional feature is implemented, a sensible design would be to provide an *opt-in* environment switch and configurable tolerances, plus a TSV report. Names such as `CSF_CUF_J_CROSSCHECK` and `CSF_CUF_J_CROSSCHECK_RTOL` are **proposals, not supported current settings**. Setting them now will not enable a cross-check.

## 5. Optional block-level reciprocity diagnostic (future work)

For CUF block indices `(tau,s)`, a local reciprocity test would compare:

```math
K_{\tau s}\quad\text{with}\quad K_{s\tau}^{T}.
```

**An individual off-diagonal CUF block need not be symmetric by itself.** The property to test is the transposition between reciprocal blocks.

This can help localize where a discrepancy originates if the global symmetry test fails, and can expose small local mismatches obscured by the norm of a much larger global matrix. It is **not included** in the current `engine.py` symmetry patch.

## 6. What each check does and does not demonstrate

| Question | Global `K` symmetry | `J` Gauss-order diagnostic | Proposed matrix/scalar `J` cross-check |
|---|:---:|:---:|:---:|
| Is assembled `K` globally reciprocal within the chosen norm? | **Yes** | No | No |
| Are sectional values stable as quadrature order changes? | No | **Yes, for tested orders** | Only if independently configured for quadrature |
| Do matrix-family and scalar implementation paths agree? | No | No | **Yes, for sampled coefficients** |
| Does the test establish correct physical stiffness? | **No** | **No** | **No** |
| Does the test establish the absence of all local errors? | **No** | **No** | **No** |

A broader validation strategy combines these internal checks with mesh/order convergence, equilibrium residuals, manufactured or analytically tractable cases, and carefully specified independent FEM/3D benchmarks.


---

## References

- Source: [`solver/engine.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/solver/engine.py) - global assembly and execution pipeline. The symmetry check described here was installed **locally**; it may not appear in the public branch.
- Source: [`core/sectional.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/core/sectional.py) - existing sectional integration pathways and Gauss-order diagnostic.
- Local patch utility: `apply_engine_symmetry_check.py`.

