# Stress Recovery and Strong-Form Equilibrium Assessment

**FEM3D and CSF–CUF - Technical Documentation and Verification Plan**

## Purpose and immediate scope

This document defines a reproducible investigation of how **CSF–CUF and FEM3D stresses are actually obtained and displayed** for the tapered I-shaped benchmark. The immediate objective is to trace each plotted stress component back to the stored numerical solution and the implemented recovery algorithm. Spatial differentiation and strong-form equilibrium are a **subsequent phase**, after both stress-recovery paths have been documented.

The central question is:

> Given a physical point on a cross-section, how does each implementation obtain the numerical value of a specified stress component at that point?

The analysis distinguishes **native solver output**, **field reconstruction**, **interpolation or extrapolation**, **element-wise selection**, and **averaging**. Every claim about the actual implementation should be linked to the relevant function or code path.

## 1. Benchmark and physical-coordinate conventions

The benchmark is a tapered I-shaped member with longitudinally varying geometry and web Young's modulus. Both models use the same physical geometry and material distribution but different sectional partitions:

- **CSF–CUF:** nine CSF domains (three flange domains at the top, three web domains, three flange domains at the bottom), compatible with the Lagrange L9 transverse discretization.
- **FEM3D:** three physical CSF regions (top flange, web, bottom flange), used by the structured OpenSees `stdBrick` mesher.

The two geometric representations must be shown to generate the same external outline, longitudinal taper, and constitutive properties. Record the mapping between CSF coordinates and the physical coordinates used by the plotting tool; distinguish the longitudinal coordinate from the transverse coordinates throughout.

**Geometry and material inputs:**

- [CSF–CUF nine-domain geometry](models/carrera_i_shaped_taper80_l9_web3.yaml)
- [FEM3D three-region geometry](models/carrera_i_shaped_taper80.yaml)

## 2. Inputs and entry point: the boundary stress visualizer

Two distinct entry points must be documented:

1. **Boundary visualization:** [`plot_strain_stress_boundary_v10.py`](../../src/csf/cuf/tools/plot_strain_stress_boundary_v10.py) reconstructs or selects stress values for cross-sectional boundary plots.
2. **Strong-equilibrium assessment:** [`compare_fem3d_cuf_strong_equilibrium.py`](compare_fem3d_cuf_strong_equilibrium.py) reconstructs **both** stress fields at identical physical H8 Gauss-point coordinates, then evaluates their derivatives and equilibrium residuals.

The two programs must not be assumed to use identical sampling, interpolation, or stress-recovery pathways. This document treats the equilibrium script as the authoritative implementation for the equilibrium comparison and the visualizer as the authority for plotted boundary fields.

Identify each program's command-line arguments, data-loading functions, geometry readers, stress-evaluation routines, sampling loops, and outputs. Record the exact NPZ keys consumed by each. For the equilibrium script, the verified input keys and operations are specified below.

| Role | Source | Verification target |
|---|---|---|
| CSF–CUF solution | `output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/` | Identify the **exact** `.cuf.npz` filename, its arrays, and the field-construction path. The equilibrium script example names `carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz`; verify the actual file before running. |
| FEM3D solution | [`fem3d/output/fem3d_taper.npz`](fem3d/output/fem3d_taper.npz) | Identify element connectivity, nodal displacements, material identifiers, stored stresses, and any Gauss-point fields actually present. |
| CSF–CUF geometry/material | [`models/carrera_i_shaped_taper80_l9_web3.yaml`](models/carrera_i_shaped_taper80_l9_web3.yaml) | Trace domain IDs and the longitudinal material law. |
| FEM3D geometry/material | [`models/carrera_i_shaped_taper80.yaml`](models/carrera_i_shaped_taper80.yaml) | Trace physical regions and their constitutive assignments. |

**Verified equilibrium-script FEM3D NPZ keys:** `nodes`, `elements`, `displacement`, `element_E`, `element_G`, `element_nu` (function `load_fem`). The script does **not** read stored FEM stress arrays. `load_cuf` uses `CompiledDisplacementField.load(cuf_path)` and `CSFCUFModelBridge.from_yaml(csf_path)`; the internal CUF NPZ key names require inspection of `CompiledDisplacementField.load`.

**Deliverable:** a data dictionary listing every consumed NPZ key, its dimensions, coordinate convention, physical units, and role in stress recovery, separately for each program.

## 3. CSF–CUF stress recovery

### 3.1 From solution coefficients to displacements

Start from the CUF transverse expansion:

$$
\mathbf u(x,y,z)=\sum_{\tau}F_\tau(y,z)\,\mathbf u_\tau(x).
$$

Identify where the longitudinal degrees of freedom are read from the NPZ file, how longitudinal finite-element interpolation produces $\mathbf u_\tau(x)$, and how the transverse Lagrange L9 functions $F_\tau(y,z)$ are evaluated on the selected CSF domain.

### 3.2 From displacement gradients to strain

Explain the strain-vector convention used by the implementation (including the order of components and whether shear strains are engineering or tensorial). Show each derivative of the CUF expansion and the resulting strain components. For the **equilibrium script**, trace `field.displacement_gradient(x, y, z, domain_index=domain_index)` and its conversion through `strain_from_grad(grad)`. For the **visualizer**, separately trace `field.strain(...)` and its `domain_index` handling on polygon boundaries. These are different public entry points and must be verified independently.

### 3.3 From strain to stress

Document the constitutive evaluation at the **physical point**:

$$
\boldsymbol\sigma(x,y,z)=\mathbf C(x,y,z)\,\boldsymbol\varepsilon(x,y,z).
$$

Trace the material provider, domain selection, and interpolation of the web modulus along the beam. The visualizer's recovery path includes the operations conceptually represented by:

```python
strain = field.strain(x, y, z, domain_index=side_index)
C = constitutive_provider.matrix(x=x, domain_id=domain_id, y=y, z=z)
stress = C @ strain
```

The equilibrium script explicitly uses the Voigt order **`[xx, yy, zz, yz, xz, xy]`** and **engineering shear strains**, i.e. `gamma_yz = du_y/dz + du_z/dy` (similarly for `xz` and `xy`). Its `cuf_stress()` computes `C @ strain_from_grad(field.displacement_gradient(...))`, with `domain_id=domain_index+1`. Trace the underlying compiled-field derivative definitions to complete the mathematical derivation. Confirm the visualizer's independent path before publishing it as a line-by-line account. Explain how separate one-sided values may arise at a material or polygon interface.

**Deliverable:** a worked trace of one point on a selected polygon boundary, showing coordinates, domain, interpolated displacement, strain vector, constitutive matrix, and six stress components.

## 4. FEM3D stress recovery

### 4.1 What OpenSees stores and what the NPZ contains

Trace the `stdBrick` analysis and its export into `fem3d_taper.npz`. **In the equilibrium script**, `load_fem()` reads nodal positions, H8 connectivity, nodal displacements, and element-wise `E`, `G`, `nu`; it **does not load OpenSees stress output**. Native Gauss-point locations are used as *sampling coordinates*, while stresses are independently reconstructed from nodal displacements. The visualizer's handling of any native OpenSees stress arrays is a separate audit item.

### 4.2 Element-wise H8 field evaluation

For the equilibrium script, the verified functions are `h8_shape`, `inverse_h8`, `h8_u_grad`, `strain_from_grad`, `isotropic_C`, and `fem_stress`. The eight H8 shape functions are evaluated in parent coordinates `q=(r,s,t)`; `inverse_h8` uses Newton iteration to find the parent coordinate of the requested physical point. With `J = coords.T @ dN`, the program evaluates `gradN = solve(J.T, dN.T).T`, then `grad_u = disp.T @ gradN`, and finally:

$$
\begin{aligned}
\boldsymbol{\varepsilon}_{\mathrm{H8}}
&= \mathrm{Voigt}\!\left(\nabla\mathbf{u}\right),\\[6pt]
\boldsymbol{\sigma}_{\mathrm{FEM3D}}
&= \mathbf{C}_e\,\boldsymbol{\varepsilon}_{\mathrm{H8}}.
\end{aligned}
$$

`isotropic_C(E, G, nu)` checks the isotropic identity `G = E/[2(1+nu)]`. Its shear diagonal entries are `G`, consistent with engineering shear strain. Separately follow the visualizer's `FEM3DH8` path and state where it differs. Do not describe the equilibrium-script stresses as native OpenSees stresses.

### 4.3 Boundary sampling, interfaces, and smoothing

For a requested point on a polygon boundary, identify the containing element or elements and the exact selection rule. Document whether the plotted values are native, interpolated, or reconstructed; whether any extrapolation is used; and whether stresses are averaged across adjacent elements. If multiple traces are retained on a shared boundary, explain their origin rather than merging them.

Distinguish the material properties assigned to the FEM3D elements from any optional constitutive evaluation through CSF. State which path is selected by the benchmark's plotting command.

**Deliverable:** a worked FEM3D point trace with element ID, local coordinates, nodal or Gauss data used, strain, constitutive properties, and displayed stress components.

## 5. Common physical-point sampling in the equilibrium comparison

The equilibrium script generates eight H8 Gauss points per element at parent coordinates `(+/-1/sqrt(3), +/-1/sqrt(3), +/-1/sqrt(3))`, maps them to physical `(x,y,z)`, and selects longitudinal planes nearest to the requested targets. For each candidate it identifies **exactly one** CSF polygon domain with `domain_for_point`; ambiguous or unmatched points are excluded.

For every accepted physical point, `fs(p)` evaluates `fem_stress(...)` in its original H8 element and `cs(p)` evaluates `cuf_stress(...)` in the identified CSF domain. Both are sampled at the **same physical coordinates**, without nodal averaging or cross-element stress smoothing in this script.

The script also requires all finite-difference perturbations to remain in the same H8 element **and** the same CSF domain. Thus this is an interior strong-form diagnostic, not an interface traction-jump test. The selected Gauss points are locations of evaluation, **not a claim that OpenSees stresses are directly read**.

**Traceable code path:** `gauss_points_for_element` -> `select_planes` -> `domain_for_point` -> `fem_stress` / `cuf_stress` -> `stress_derivatives`.

## 5A. How the visualizer constructs its boundary comparison

Document the exact station and polygon-boundary sampling rules, including the `x = 500 mm` cross-section and the perimeter analysis for `polygon_008` where applicable. Show how the CSF–CUF and FEM3D paths map to the same physical positions, and identify any differences in the actual sample locations or multiplicity of element-wise FEM3D values.

Specify plotted stress components, units, sign conventions, legend meanings, and whether a curve or map represents one-sided, element-wise, or smoothed values. Explain how material interfaces are handled and what is plotted when adjacent elements give distinct values.

**Deliverable:** a side-by-side provenance table for each plotted component, from NPZ field through numerical operation to final plotted value.

## 6. Independent verification of stress recovery

Verify stress-component ordering and coordinate transforms. Use a simple displacement field with known constant strain to test both recovery paths. Check an interior point, a polygon boundary, and a material interface. Compare native FEM3D Gauss-point stresses with reconstructed H8 stresses at corresponding locations, where the exported data permit it. Record tolerances and any expected discontinuities.

## 7. Next phase: spatial stress derivatives

The equilibrium script implements **centered finite differences** of the reconstructed stresses, identically for FEM3D and CSF–CUF:

$$
\frac{\partial\sigma_{ij}}{\partial x_k}(\mathbf x)
\approx \frac{\sigma_{ij}(\mathbf x+h_k\mathbf e_k)-\sigma_{ij}(\mathbf x-h_k\mathbf e_k)}{2h_k}.
$$

For each direction, `h_k = max((hi_k-lo_k) * fd_fraction, 1e-8)` using the H8 element bounding-box dimensions; the default `fd_fraction` is `1e-3`. The script rejects points whose perturbed coordinates leave the original H8 element or CSF domain. It evaluates all six Voigt stress components at each perturbation and extracts the nine terms in `stress_derivatives`. This is a numerical derivative of **reconstructed stresses**, not an analytical derivative of the finite-element interpolation.

## 8. Next phase: equilibrium residuals and statistics

For the benchmark, the applied loading is a surface traction and the volumetric body-force density is zero, $\mathbf b=\mathbf 0$. The local equilibrium equations in the interior of the member therefore reduce to $\nabla\cdot\boldsymbol\sigma=\mathbf 0$. Define the corresponding residual components:

$$
\begin{aligned}
r_x &= \frac{\partial\sigma_{xx}}{\partial x}+\frac{\partial\tau_{xy}}{\partial y}+\frac{\partial\tau_{xz}}{\partial z},\\
r_y &= \frac{\partial\tau_{xy}}{\partial x}+\frac{\partial\sigma_{yy}}{\partial y}+\frac{\partial\tau_{yz}}{\partial z},\\
r_z &= \frac{\partial\tau_{xz}}{\partial x}+\frac{\partial\tau_{yz}}{\partial y}+\frac{\partial\sigma_{zz}}{\partial z}.
\end{aligned}
$$

$$
\|\mathbf r\|_2=\sqrt{r_x^2+r_y^2+r_z^2}.
$$

The equilibrium script's defaults select 40 target stations in `x/L` from 0.01 to 0.99 and snap them to available H8 Gauss-point longitudinal planes. Its `stats_abs` reports median, mean, RMS and maximum of the **absolute values** of each derivative term and residual. The summary reports medians across sections of their per-section medians. The previously reported 66,560 accepted samples are benchmark output, not a fixed number imposed by the script. The script writes `equilibrium_component_points_all_sections.csv`, `equilibrium_component_sections_summary.csv`, `summary.txt` and diagnostic plots. This sampling set is part of the **equilibrium study** and should not automatically be assumed to be the visualizer's boundary-sampling set.

## 9. FEM3D reference mesh and existing results

The documented FEM3D displacement-convergence study adopts **S3 (49,920 `stdBrick` elements)**. Refinement to **S4 (81,600 elements)** changes the minimum vertical displacement by **0.021%**. See [FEM3D mesh-convergence criterion](FEM3Dmesh-convergence-criterion.md).

The existing strong-equilibrium report states:

| Metric | Reported result |
|---|---|
| Median total equilibrium residual | CSF–CUF approximately 10 times lower |
| Sections with lower total residual for CSF–CUF | 38 / 40 |
| Median third-equation residual | CSF–CUF approximately 67.6 times lower |
| Sections with lower third-equation residual for CSF–CUF | 40 / 40 |

See [FEM3D–CUF equilibrium report](FEM3D%E2%80%93CUF-equilibrium-report.md). These are reported benchmark results; the present document's immediate work is to establish the provenance of the stress values before auditing the equilibrium post-processing.

## 10. Reproducibility and final technical conclusions

Provide the exact commands, program versions, source-code functions, NPZ keys, coordinate transformations, stress component order, and pointwise numerical examples required to reproduce the visualizer's results. Conclude first on the **verified stress-recovery mechanisms**; subsequently connect these to the strong-equilibrium comparison for the stated geometry, loading, materials, supports, and discretizations.

## Reproducible equilibrium-script invocation

Run from `cuf/I-Shape_L` after generating the input solutions:

```bash
PYTHONPATH="../../src" python3 compare_fem3d_cuf_strong_equilibrium.py \
  --fem fem3d/output/fem3d_taper.npz \
  --cuf output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --csf models/carrera_i_shaped_taper80_l9_web3.yaml \
  --sections 40 --xmin 0.01 --xmax 0.99 \
  --output-dir diagnostics/equilibrium_multisection_components
```

The CUF filename is taken from the script's usage example; verify its presence in the checkout.

## Implementation-first work plan

**Phase A - Stress values (current priority)**

```text
CSF–CUF NPZ -> solution coefficients -> displacement field
            -> strain -> CSF constitutive matrix -> stress -> plot

FEM3D NPZ   -> H8 nodal displacements and element material data
            -> H8 gradient -> strain -> stress -> Gauss-location evaluation
```

1. Inspect the visualizer's NPZ readers and identify all relevant keys.
2. Trace `field.strain(...)` and the CSF constitutive provider.
3. Trace `FEM3DH8` evaluation and distinguish native stresses from reconstructed values.
4. Reproduce one stress value from each method at a common physical point.
5. Document how those values appear in the boundary plot.

**Phase B - Equilibrium (after Phase A)**

```text
same-point reconstructed stress fields -> centered finite differences
                       -> residual components
                       -> section statistics -> FEM3D / CSF–CUF comparison
```

**Benchmark:** [CSF–CUF / FEM3D comparison for a tapered I-shaped member](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape_L).
