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

The primary program to audit is [`plot_strain_stress_boundary_v10.py`](../../src/csf/cuf/tools/plot_strain_stress_boundary_v10.py).

Identify its command-line arguments, data-loading functions, geometry readers, stress-evaluation routines, plotting loops, and output files. Record the exact file paths and keys actually read from the two NPZ archives.

| Role | Source | Verification target |
|---|---|---|
| CSF–CUF solution | `output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/` | Identify the **exact** `.cuf.npz` filename, its arrays, and the field-construction path. The previously supplied URL contains an unavailable filename fragment. |
| FEM3D solution | [`fem3d/output/fem3d_taper.npz`](fem3d/output/fem3d_taper.npz) | Identify element connectivity, nodal displacements, material identifiers, stored stresses, and any Gauss-point fields actually present. |
| CSF–CUF geometry/material | [`models/carrera_i_shaped_taper80_l9_web3.yaml`](models/carrera_i_shaped_taper80_l9_web3.yaml) | Trace domain IDs and the longitudinal material law. |
| FEM3D geometry/material | [`models/carrera_i_shaped_taper80.yaml`](models/carrera_i_shaped_taper80.yaml) | Trace physical regions and their constitutive assignments. |

**Deliverable:** a data dictionary listing every consumed NPZ key, its dimensions, coordinate convention, physical units, and role in stress recovery.

## 3. CSF–CUF stress recovery

### 3.1 From solution coefficients to displacements

Start from the CUF transverse expansion:

$$
\mathbf u(x,y,z)=\sum_{\tau}F_\tau(y,z)\,\mathbf u_\tau(x).
$$

Identify where the longitudinal degrees of freedom are read from the NPZ file, how longitudinal finite-element interpolation produces $\mathbf u_\tau(x)$, and how the transverse Lagrange L9 functions $F_\tau(y,z)$ are evaluated on the selected CSF domain.

### 3.2 From displacement gradients to strain

Explain the strain-vector convention used by the implementation (including the order of components and whether shear strains are engineering or tensorial). Show each derivative of the CUF expansion and the resulting strain components. Trace the implementation of `field.strain(...)`, including its `domain_index` handling on polygon boundaries.

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

Confirm the actual function definitions and tensor-component ordering before publishing this as a line-by-line account. Explain how separate one-sided values may arise at a material or polygon interface.

**Deliverable:** a worked trace of one point on a selected polygon boundary, showing coordinates, domain, interpolated displacement, strain vector, constitutive matrix, and six stress components.

## 4. FEM3D stress recovery

### 4.1 What OpenSees stores and what the NPZ contains

Trace the `stdBrick` analysis and its export into `fem3d_taper.npz`. Identify which arrays are **native OpenSees outputs** and which are reconstructed later. In particular, determine whether native stress arrays correspond to element integration points and document their ordering.

### 4.2 Element-wise H8 field evaluation

Follow the visualizer's `FEM3DH8` code path. Describe the eight-node shape functions, mapping from parent-element coordinates to physical coordinates, displacement-gradient evaluation, and constitutive stress calculation **where these operations are actually performed**. Separate this reconstructed field from any native Gauss-point stress values.

### 4.3 Boundary sampling, interfaces, and smoothing

For a requested point on a polygon boundary, identify the containing element or elements and the exact selection rule. Document whether the plotted values are native, interpolated, or reconstructed; whether any extrapolation is used; and whether stresses are averaged across adjacent elements. If multiple traces are retained on a shared boundary, explain their origin rather than merging them.

Distinguish the material properties assigned to the FEM3D elements from any optional constitutive evaluation through CSF. State which path is selected by the benchmark's plotting command.

**Deliverable:** a worked FEM3D point trace with element ID, local coordinates, nodal or Gauss data used, strain, constitutive properties, and displayed stress components.

## 5. How the visualizer constructs a like-for-like comparison

Document the exact station and polygon-boundary sampling rules, including the `x = 500 mm` cross-section and the perimeter analysis for `polygon_008` where applicable. Show how the CSF–CUF and FEM3D paths map to the same physical positions, and identify any differences in the actual sample locations or multiplicity of element-wise FEM3D values.

Specify plotted stress components, units, sign conventions, legend meanings, and whether a curve or map represents one-sided, element-wise, or smoothed values. Explain how material interfaces are handled and what is plotted when adjacent elements give distinct values.

**Deliverable:** a side-by-side provenance table for each plotted component, from NPZ field through numerical operation to final plotted value.

## 6. Independent verification of stress recovery

Verify stress-component ordering and coordinate transforms. Use a simple displacement field with known constant strain to test both recovery paths. Check an interior point, a polygon boundary, and a material interface. Compare native FEM3D Gauss-point stresses with reconstructed H8 stresses at corresponding locations, where the exported data permit it. Record tolerances and any expected discontinuities.

## 7. Next phase: spatial stress derivatives

Once stress recovery is established, document the nine spatial derivatives entering strong-form equilibrium. Identify whether each derivative is evaluated analytically, by differentiated shape functions, by finite differences, or by another recovery operation. Record stencils, increments, accuracy order, interface handling, and boundary treatment.

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

Trace the 40-section sampling, 66,560 reported samples, per-section aggregation, median statistics, and comparison ratios to the actual equilibrium-analysis script. This sampling set is part of the **equilibrium study** and should not automatically be assumed to be the visualizer's boundary-sampling set.

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

## Implementation-first work plan

**Phase A - Stress values (current priority)**

```text
CSF–CUF NPZ -> solution coefficients -> displacement field
            -> strain -> CSF constitutive matrix -> stress -> plot

FEM3D NPZ   -> native element/Gauss data and/or H8 reconstruction
            -> element selection -> stress at requested point -> plot
```

1. Inspect the visualizer's NPZ readers and identify all relevant keys.
2. Trace `field.strain(...)` and the CSF constitutive provider.
3. Trace `FEM3DH8` evaluation and distinguish native stresses from reconstructed values.
4. Reproduce one stress value from each method at a common physical point.
5. Document how those values appear in the boundary plot.

**Phase B - Equilibrium (after Phase A)**

```text
verified stress fields -> spatial derivatives -> residual components
                       -> section statistics -> FEM3D / CSF–CUF comparison
```

**Benchmark:** [CSF–CUF / FEM3D comparison for a tapered I-shaped member](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape_L).
