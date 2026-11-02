# Tapered I-section: custom surface-halfwave adapter and FEM3D equivalent


This document explains one specific structural problem: a variable-section I-shaped beam, subjected to a global-`z` half-wave traction on its bottom surface and constrained transversely at both beam ends. It identifies **what the custom CUF adapter does**, **how the FEM3D driver implements the same physical problem**, and **which input files reproduce the two discretizations**.

## Contents

1. [Quick reference: what problem is solved?](#1-quick-reference-what-problem-is-solved)
2. [Source files and execution path](#2-source-files-and-execution-path)
3. [The common CSF physical geometry and materials](#3-the-common-csf-physical-geometry-and-materials)
4. [Common loading: the lower physical surface](#4-common-loading-the-lower-physical-surface)
5. [Custom CUF adapter: inputs and internal work](#5-custom-cuf-adapter-inputs-and-internal-work)
6. [CUF constraints: transverse supports and axial gauge](#6-cuf-constraints-transverse-supports-and-axial-gauge)
7. [FEM3D driver: geometry, mesh, loads, and constraints](#7-fem3d-driver-geometry-mesh-loads-and-constraints)
8. [Why the end conditions are the same physical type](#8-why-the-end-conditions-are-the-same-physical-type)
9. [CUF versus FEM3D: direct comparison](#9-cuf-versus-fem3d-direct-comparison)
10. [Quantitative load check for this geometry](#10-quantitative-load-check-for-this-geometry)
11. [Reproduce and inspect](#11-reproduce-and-inspect)
12. [Implementation details to preserve](#12-implementation-details-to-preserve)

---

## 1. Quick reference: what problem is solved?

| Physical item | Definition in this benchmark |
|---|---|
| Longitudinal beam axis | `x`, from `x0 = 0` to `x1 = 1000 mm` |
| Physical cross-section | I-shape, varying between CSF sections `S0` and `S1` |
| Applied loading | Surface traction in the fixed **global `z` direction** |
| Longitudinal loading law | `t_z(x) = A sin(pi (x-x0)/L)`, where `L=x1-x0` |
| Applied amplitude | `A = -1.0 N/mm^2` for the checked case and FEM launcher |
| Loaded surface | Complete lower external face of the bottom flange |
| End supports | `u_y = u_z = 0` over **both entire end sections** |
| Axial displacement at the ends | Not constrained pointwise by the physical support model |
| Additional axial condition | `(1/L) integral[x0,x1] u_x(x,0,0) dx = 0` |
| CUF representation | 9 quadrilateral CSF domains; three lower edges selected by the custom adapter |
| FEM3D representation | 3 CSF physical regions; `stdBrick` solid elements and bottom Q4 element faces |
| CUF adapter type | `surface_halfwave_transverse_supported` |
| CUF adapter location | `validation/surface_halfwave_multi.py` (**custom**, not a standard-library module) |
| FEM3D driver | `fem3d/run_bending_fem3d_v2.py` (**standalone FEM driver**, not a CUF problem adapter) |

**Static interpretation.** This is a two-end *transversely restrained* 3D beam with a longitudinal rigid-translation gauge. The term `transverse_supported` describes the exact component constraints shown above. In particular, the end sections are not modeled as classical ideal beam hinges with separately prescribed rotational degrees of freedom.

## 2. Source files and execution path

These are the actual paths in the repository:

| Purpose | Repository path |
|---|---|
| Three-polygon physical model for FEM3D | [`models/carrera_i_shaped_taper80.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/models/carrera_i_shaped_taper80.yaml) |
| Nine-polygon physical model for CUF L9 | [`models/carrera_i_shaped_taper80_l9_web3.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/models/carrera_i_shaped_taper80_l9_web3.yaml) |
| CUF physical problem YAML | [`problems/taper_table9_l9_web3.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/problems/taper_table9_l9_web3.yaml) |
| CUF case YAML | [`cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml) |
| **Custom CUF adapter** | [`validation/surface_halfwave_multi.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/validation/surface_halfwave_multi.py) |
| FEM3D driver | [`fem3d/run_bending_fem3d_v2.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/fem3d/run_bending_fem3d_v2.py) |
| FEM3D launcher | [`fem3d/startfem_tap.sh`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/fem3d/startfem_tap.sh) |
| Full execution sequence | [`reproducibility.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/reproducibility.md) |

The same *physical* problem is configured by two different execution routes:

```text
CSF-CUF path
-------------
models/carrera_i_shaped_taper80_l9_web3.yaml
               |
               v
problems/taper_table9_l9_web3.yaml
    + model.csf_yaml
    + problem.type = surface_halfwave_transverse_supported
    + surfaces[] and amplitude
               |
               v
cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml
    + problem.yaml
    + problem.adapter = ../../validation/surface_halfwave_multi.py
    + CUF/longitudinal numerical settings
               |
               v
custom adapter: build_load_vector() + build_constraints()
               |
               v
CSF-CUF system and solution

FEM3D path
----------
models/carrera_i_shaped_taper80.yaml
               |
               v
fem3d/run_bending_fem3d_v2.py
    + CSFReader and field.section(x)
    + stdBrick mesh
    + real bottom-face consistent loads
    + end-node fixities and axial gauge
               |
               v
OpenSees solution -> fem3d/output/fem3d_taper.npz
```

**Roles of the files:** the `models/*.yaml` files define geometry/materials; `problems/*.yaml` defines CUF loading selections and amplitude; `cases/*.yaml` selects the CUF adapter and discretization. The FEM3D driver reads its **model YAML** and its own command-line options; it does not consume the CUF `problem.type` or `case.adapter` keys.

## 3. The common CSF physical geometry and materials

### 3.1 Coordinate convention

The CSF YAML represents beam stations using `CSF.sections.S0.z` and `S1.z`. Inside the CUF and FEM3D problem, that **CSF longitudinal coordinate becomes beam coordinate `x`**. The two components of each CSF vertex become the physical transverse coordinates `(y,z)`:

```text
CSF source                    Beam/FEM convention
----------                    -------------------
section station: CSF z   -->   longitudinal x
vertex first coordinate -->   transverse y
vertex second coordinate-->   transverse z
```

The physical displacement is `(u_x,u_y,u_z)`.

### 3.2 Section dimensions and material carriers

The two CSF models have the same **external I-shaped solid** and section stations, expressed with different polygon subdivisions.

| Quantity | `S0`, `x=0 mm` | `S1`, `x=1000 mm` |
|---|---:|---:|
| Bottom-most `z` | `-75 mm` | `-35 mm` |
| Top-most `z` | `+75 mm` | `+35 mm` |
| Overall section height | `150 mm` | `70 mm` |
| Clear web height | `100 mm` | `20 mm` |
| Flange total width | `66 mm` | `66 mm` |
| Each flange thickness | `25 mm` | `25 mm` |
| Web thickness | `25 mm` | `25 mm` |
| Top and bottom flange `E` | `71700 MPa` | `71700 MPa` |
| Web `E` | `71700 MPa` | `51700 MPa` |
| Isotropic shear law | `iso(0.3)` | `iso(0.3)` |

The web clear height decreases by **80%** from `S0` to `S1`; the flange width and thickness remain unchanged. The web Young's modulus also changes between the stations. The FEM3D driver queries the material at each element's longitudinal midpoint through the CSF API and uses `ElasticIsotropic(E, nu)` with the shear-modulus consistency check `G = E/[2(1+nu)]`.

### 3.3 Why 3 polygons versus 9 polygons?

- **FEM3D geometry** (`carrera_i_shaped_taper80.yaml`): `top_flange`, `web`, `bottom_flange`; these three physical regions are sufficient to create the structured three-block solid mesh.
- **CUF L9 geometry** (`carrera_i_shaped_taper80_l9_web3.yaml`): three top-flange polygons, three web polygons, three bottom-flange polygons, all non-overlapping. This subdivision supplies the Lagrange L9 sectional domains and their connectivity.

These are two descriptions of the **same physical section geometry**. Their polygon names are different, so the load selectors must match the selected model.

## 4. Common loading: the lower physical surface

### 4.1 Definition and sign

Let `Gamma_b` be the external ruled surface swept along the beam axis by the bottom boundary of the lower flange. The prescribed physical traction is

```math
t_x(x)=0,\qquad t_y(x)=0,\qquad
t_z(x)=A\sin\!\left(\frac{\pi(x-x_0)}{L}\right),
\qquad L=x_1-x_0.
```

For the executed case, `A=-1.0 N/mm^2`; hence the traction is in **negative global `z`** in the interior of the span and zero at the two ends. This is a **fixed-direction traction**, **not** a pressure normal to the inclined bottom surface. Its magnitude varies sinusoidally along `x` and is uniform across each selected edge at a given `x`.

### 4.2 Identifying the same loaded face in each model

**CUF L9, three actual selected edges** (all are edge `0`, from vertex `0` to vertex `1`, with zero-based indexing):

| Polygon | `y` range, mm | `z` at `S0`, mm | `z` at `S1`, mm |
|---|---:|---:|---:|
| `bottom_flange_left` | `-33` to `-12.5` | `-75` | `-35` |
| `bottom_flange_center` | `-12.5` to `12.5` | `-75` | `-35` |
| `bottom_flange_right` | `12.5` to `33` | `-75` | `-35` |
| **Union** | **`-33` to `33`** | **`-75`** | **`-35`** |

**FEM3D, one physical bottom-face region:** the lower edge of `bottom_flange` connects `(-33,-75)` to `(33,-75)` at `S0`, and `(-33,-35)` to `(33,-35)` at `S1`. The driver marks the bottom faces of the bottom-flange block during mesh construction. The union of the three CUF edges coincides geometrically with this FEM3D loaded face.

### 4.3 Integration on the actual inclined surface

For this model, the physical bottom-face height changes from `-75 mm` to `-35 mm` over `1000 mm`, so

```math
\frac{dz_b}{dx}=\frac{-35-(-75)}{1000}=0.04.
```

Here `z_b(x)` denotes the bottom-face elevation. For the linear ruled geometry used by the adapter, the physical surface element is

```math
d\Gamma=\sqrt{1+\left(\frac{dz_b}{dx}\right)^2}\,|dy|\,dx
=\sqrt{1+0.04^2}\,|dy|\,dx.
```

The associated inclination multiplier is `sqrt(1.0016) = 1.0007996802557444`.

**Both implementations account for this physical surface measure:** CUF uses a per-edge inclination factor; FEM3D evaluates the cross product of the two tangents of each loaded quadrilateral face. The **surface measure** is a geometric factor for boundary loading, not a separate reference-to-physical cross-section mapping introduced to describe longitudinal CSF variation.

## 5. Custom CUF adapter: inputs and internal work

### 5.1 Adapter identity

**Path:** `cuf/I-Shape_L/validation/surface_halfwave_multi.py`  
**Kind:** custom, complete problem adapter (provides **both loads and constraints**).  
**Exposed `problem.type`:** `surface_halfwave_transverse_supported`.

It is loaded by a **relative Python path in the case YAML**, not by a standard `csf.cuf.adapters.problem.*` module name. The module has `build_problem(problem_type, options)`, which returns a `SurfaceHalfWaveMultipleEdges` object implementing:

- `build_load_vector(...)`: construct the global CUF force vector;
- `build_constraints(...)`: construct the end support/gauge constraint system;
- `tracked_points(...)`: identify actual loaded-edge endpoints for post-processing.

### 5.2 Exact problem YAML in this case

File: `cuf/I-Shape_L/problems/taper_table9_l9_web3.yaml`.

```yaml
model:
  csf_yaml: ../models/carrera_i_shaped_taper80_l9_web3.yaml

problem:
  type: surface_halfwave_transverse_supported
  surfaces:
    - polygon_name: bottom_flange_left
      edge_start_point_id: 0
    - polygon_name: bottom_flange_center
      edge_start_point_id: 0
    - polygon_name: bottom_flange_right
      edge_start_point_id: 0
  amplitude: -1.0
```

The case YAML selects it with:

```yaml
problem:
  yaml: ../../problems/taper_table9_l9_web3.yaml
  adapter: ../../validation/surface_halfwave_multi.py
```

These relative paths are evaluated **from the directory of the case YAML**, `cuf/I-Shape_L/cases/taper/`.

The **checked numerical settings in this CUF case** are:

| Case setting | Actual configuration |
|---|---|
| Transverse basis | `lagrangeL9`, `order: 2` |
| Transverse domains | `domain_source: csf_polygons`, `connectivity: shared_points` |
| Transverse basis mapping | `mapping: isoparametric` (an L9 basis-construction option) |
| Longitudinal method | `finite_element` |
| Longitudinal element boundaries | `[0.0, 0.1, ..., 1.0]` (10 subintervals) |
| Longitudinal interpolation | `basis: lagrange`, `order: 6` |
| Longitudinal integration | `gauss_order: 15`, `material_polynomial_degree: 1` |
| Section integration | `fixed_gauss_polygon`, `gauss_order: 12` |
| Solver | `correctionMITC: true`, `verifyMITCAssembly: true` |

These numerical settings affect the approximation and integration, **not** which physical surfaces receive the load or which displacement components are constrained. The isoparametric option pertains to constructing the transverse L9 basis; the variable physical CSF cross-section still comes from the CSF model rather than from an independently prescribed longitudinal geometry mapping.

### 5.3 Exact supported YAML parameters

| Parameter | Required? | Type / allowed values | Meaning |
|---|---|---|---|
| `problem.type` | Yes | Exactly `surface_halfwave_transverse_supported` | Chooses this adapter's problem factory |
| `problem.amplitude` | Yes | Finite numeric value; sign is preserved | Shared global-`z` traction magnitude for all selected edges |
| `problem.surface` | Either this or `surfaces` | Mapping | One selected physical edge |
| `problem.surfaces` | Either this or `surface` | Nonempty YAML list of mappings | Multiple independently selected physical edges |
| `polygon_name` | Yes, per edge | Nonempty string, matching a CSF polygon | Which CSF polygon supplies the edge |
| `edge_start_point_id` | Yes, per edge | Nonnegative integer, zero-based | Edge from vertex `i` to `(i+1) mod n_vertices` |

The adapter **requires exactly one** of `surface` and `surfaces`; it rejects unsupported option keys. The amplitude is shared: there is no per-edge amplitude setting in this implementation. Repeated entries apply the same traction more than once to the same edge and therefore **superimpose loads**.

A shorter **single-edge** form is supported when the CSF model actually contains the unsplit polygon name `bottom_flange`:

```yaml
problem:
  type: surface_halfwave_transverse_supported
  surface:
    polygon_name: bottom_flange
    edge_start_point_id: 0
  amplitude: -1.0
```

This last form describes a different polygon topology from the actual nine-polygon L9 case above; it is an adapter input example, **not** a replacement for the verified CUF case file.

### 5.4 How the CUF load vector is assembled

Write the transverse CUF displacement expansion as

```math
u_j(x,y,z)=\sum_{\tau=1}^{M}F_\tau(y,z;x)\,q_{\tau j}(x),
\qquad j\in\{x,y,z\},
```

where `M` is the number of transverse basis functions; `F_tau` is the transverse CUF shape function evaluated at the **current physical cross-section**; and `q_{tau j}` is its unknown longitudinal amplitude for displacement component `j`.

For a selected physical lower edge `e`, the generalized `z`-load at position `x` is

```math
Q_{\tau z}^{(e)}(x)=
t_z(x)\,\sqrt{1+s_e^2}\,
\int_{y_{e,0}(x)}^{y_{e,1}(x)}F_\tau(y,z_e(x);x)\,|dy|,
```

where `s_e=(z_e(x1)-z_e(x0))/L`. The notation `|dy|` means that edge orientation does not change the surface area. The three contributions are combined as

```math
Q_{\tau z}(x)=\sum_{e=1}^{3}Q_{\tau z}^{(e)}(x).
```

The longitudinal load assembler then forms the force entries associated with a longitudinal interpolation function `N_i(x)`:

```math
f_{i\tau z}=\int_{x_0}^{x_1}N_i(x)Q_{\tau z}(x)\,dx.
```

The code performs Gauss integration along each selected `y` edge, sums the modal contributions using `SumOfSurfaceProjectors`, and passes the resulting `z` fields to `assemble_distributed_load_vector(...)`. In the adapter, the transverse Gauss order is `max(1, (basis.order+2)//2)`; longitudinal quadrature is delegated to the CUF integrator defined by the case.

**Geometric validity:** each selected edge must have constant physical `z` along the edge at **both** CSF end stations. Its elevation can change from `S0` to `S1`; the longitudinal slope is included in the surface measure. The selected edges need not be adjacent, but adjacency happens to hold for this specific bottom flange.

## 6. CUF constraints: transverse supports and axial gauge

### 6.1 Conditions applied at both ends

For each transverse CUF mode `tau`, the adapter imposes

```math
q_{\tau y}(x_0)=q_{\tau z}(x_0)=0,\qquad
q_{\tau y}(x_1)=q_{\tau z}(x_1)=0.
```

This enforces the reconstructed conditions

```math
u_y(x_0,y,z)=u_z(x_0,y,z)=0,\qquad
u_y(x_1,y,z)=u_z(x_1,y,z)=0
```

across the entire respective end sections, within the active CUF interpolation. The longitudinal component `u_x` remains **pointwise free at the ends**.

### 6.2 Why a separate axial condition is required

Those transverse end conditions do not eliminate a uniform rigid translation along `x`. The model selects a unique axial displacement reference by imposing the **integral axial gauge**

```math
\frac{1}{L}\int_{x_0}^{x_1}u_x(x,0,0)\,dx=0.
```

The point `(y,z)=(0,0)` denotes the selected physical section centerline used for this gauge. **It is not an average over the cross-sectional area.** This condition eliminates one rigid axial translation without fixing a physical end section in `x`.

In the actual adapter the integrand is reconstructed from the **x-dependent** transverse basis at `(0,0)`:

```math
u_x(x,0,0)=\sum_{\tau=1}^{M}F_\tau(0,0;x)q_{\tau x}(x).
```

For `M=basis.size`, the adapter constructs `4M+1` homogeneous linear-constraint rows: `4M` rows for the transverse modal amplitudes at the two end nodes, plus **one** row for the integrated axial gauge. This matrix is returned as a `LinearConstraintSystem`.

## 7. FEM3D driver: geometry, mesh, loads, and constraints

### 7.1 Geometry and material input

**Driver:** `cuf/I-Shape_L/fem3d/run_bending_fem3d_v2.py`. This is **not** the custom CUF adapter and does not parse `problem.type`. The program:

1. Calls `CSFReader` to read `../models/carrera_i_shaped_taper80.yaml`.
2. Requires exactly the three CSF polygon names `top_flange`, `web`, and `bottom_flange`.
3. Queries `field.section(x)` at longitudinal stations to obtain the **physical** geometry; it does not reimplement interpolation of the CSF sections.
4. Queries CSF material data at each 3D element's longitudinal midpoint.
5. Uses OpenSees `ElasticIsotropic` materials and eight-node `stdBrick` solid elements with three translational DOFs per node.

### 7.2 FEM3D mesh used by the repository launcher

`fem3d/startfem_tap.sh` calls:

```bash
python run_bending_fem3d_v2.py ../models/carrera_i_shaped_taper80.yaml output/fem3d_taper.npz \
  --amplitude -1 \
  --nx 80 \
  --ny-left 3 \
  --ny-web 6 \
  --ny-right 3 \
  --nz-flange 4 \
  --nz-web 20
```

For these requested subdivisions, the `build_mesh()` algorithm gives:

| Quantity | Count |
|---|---:|
| Longitudinal intervals | `80` |
| Number of `stdBrick` elements | `17,280` |
| Number of mesh nodes | `21,303` |
| Loaded bottom Q4 faces | `960` |
| Nodes on each terminal section | `263` |

These counts were checked by executing the supplied `build_mesh()` routine against a minimal in-memory CSF-compatible field built from the exact endpoint coordinates in the model YAML. They are **mesh-construction checks**, not claims that a full OpenSees solution was run.

### 7.3 Consistent surface-force assembly in FEM3D

The driver marks the bottom external faces of the `bottom_flange` block (`mark_bottom=True`, lowest `z` layer). On each resulting four-node loaded face, it uses isoparametric Q4 functions `N_a`, computes two face tangents, and evaluates the **physical** area factor

```math
J_{\Gamma}(\xi,\eta)=
\left\|\frac{\partial\mathbf r}{\partial\xi}
\times\frac{\partial\mathbf r}{\partial\eta}\right\|.
```

For each face node `a` it adds the consistent nodal force

```math
\mathbf f_a^{(\Gamma)}=\int_{-1}^{1}\int_{-1}^{1}
N_a(\xi,\eta)\,
\begin{bmatrix}0\\0\\A\sin(\pi(x(\xi,\eta)-x_0)/L)\end{bmatrix}
J_{\Gamma}(\xi,\eta)\,d\xi\,d\eta.
```

The driver uses **8 Gauss points longitudinally** and **2 points transversely** for each face. The force remains oriented in global `z`, including on the inclined physical lower face. Consistent nodal forces are accumulated in `nodal_loads[:,2]` and issued through `ops.load(...)`.

### 7.4 End fixities in OpenSees

The actual code applies to **every mesh node at `x=x0` or `x=x1`**:

```python
fixity[int(nid)] = [0, 1, 1]
```

In OpenSees' three-translation-node convention, `0` means unrestrained and `1` means restrained:

| Nodal component | Both ends |
|---|---|
| `u_x` | Free |
| `u_y` | Fixed to zero |
| `u_z` | Fixed to zero |

This is the solid-FEM counterpart of the CUF end condition `q_{tau,y}=q_{tau,z}=0` for every active mode.

### 7.5 Integral axial gauge in FEM3D

The FEM3D implementation achieves the same final axial reference condition in **two stages**:

1. **Temporary solve anchor.** It selects one node on the `(y,z)=(0,0)` line, as near as possible to `x=L/2`, and temporarily fixes only its `u_x` component. This removes the rigid-body null mode for the OpenSees linear solve. The other end-node fixities are unchanged.
2. **Recenter the converged displacement field.** It evaluates the mean axial displacement along the centerline using the trapezoidal rule and subtracts this scalar from the `u_x` displacement of **every** node.

The relevant executable steps are:

```python
axial_gauge_shift = _axial_gauge_mean(mesh, u, centerline)
u[:, 0] -= axial_gauge_shift
axial_gauge_residual = _axial_gauge_mean(mesh, u, centerline)
```

The recentered field satisfies the discrete analogue of

```math
\frac{1}{L}\int_{x_0}^{x_1}u_x(x,0,0)\,dx=0.
```

For this transverse loading with no resultant axial applied force, subtracting a constant axial translation changes **neither the strains nor the stresses**. The saved displacement field `displacement` is the **recentered** field. Diagnostic quantities `gauge_node`, `axial_gauge_shift`, `axial_gauge_residual`, and the `axial_gauge_centerline_nodes` are also written to the NPZ output.

## 8. Why the end conditions are the same physical type

The physical boundary prescription common to both discretizations is

```math
\boxed{\begin{aligned}
u_y(x_0,y,z)&=0, &u_z(x_0,y,z)&=0,\\
u_y(x_1,y,z)&=0, &u_z(x_1,y,z)&=0,\\
\frac{1}{L}\int_{x_0}^{x_1}u_x(x,0,0)\,dx&=0.
\end{aligned}}
```

**The support type is the same.** CUF enforces the transverse conditions by setting **all transverse generalized end amplitudes** to zero. FEM3D fixes the transverse DOFs of **all solid nodes** in the terminal cross-sections. Both allow axial warping/end axial displacements and remove only the remaining rigid axial translation.

**The numerical gauge realization is different:** CUF directly puts the integral condition in its linear constraint matrix; FEM3D temporarily anchors one axial DOF to solve the singularity-free system and then removes the corresponding rigid translation by recentering the final solution. The FEM mean is computed from piecewise-linear centerline nodal values using the trapezoidal rule; the CUF mean is assembled using its longitudinal quadrature and transverse basis.

These two gauge implementations select the same physical normalization, **not necessarily identical floating-point displacement values** before discretization errors are considered. Neither implementation introduces an intended axial end restraint into the final physical comparison.

## 9. CUF versus FEM3D: direct comparison

| Feature | Custom CSF-CUF problem | OpenSees FEM3D reference |
|---|---|---|
| Source geometry | CSF nine-polygon L9 model | CSF three-polygon physical model |
| Geometry sampled | Through `section_provider` at integration stations | Through `field.section(x)` at mesh stations |
| Material source | CSF sectional material fields in CUF assembly | CSF `E,G,nu` evaluated at element midpoints |
| Displacement discretization | Transverse CUF modal/L9 expansion + longitudinal FE interpolation | 3D `stdBrick` nodal interpolation |
| Loaded face | Three named lower polygon edges | All Q4 faces of bottom-flange lower outer surface |
| Traction direction | Global `z` | Global `z` |
| Load profile | `A sin(pi(x-x0)/L)` | `A sin(pi(x-x0)/L)` |
| Applied amplitude | `-1.0` | `--amplitude -1` |
| Physical area factor | Per-edge `sqrt(1+(dz/dx)^2)` | Q4 face Jacobian magnitude |
| Force-vector assembly | Projection onto CUF functions + longitudinal integration | Consistent Q4 nodal surface integration |
| Transverse end constraints | `q_{tau,y}=q_{tau,z}=0` at both ends | `ops.fix(...,0,1,1)` on all terminal solid nodes |
| Axial rigid-body gauge | Integral constraint imposed in CUF system | Midpoint `u_x` solve anchor followed by zero-mean recentering |
| Final physical supports | Two-end transverse section restraints; axial end displacement free | Same |

**What is directly established by the checked sources:** equality of the prescribed physical traction law, its physical loaded-surface coverage for the two polygon models, and the intended support/gauge conditions. A numerical accuracy or stress-equilibrium comparison requires the respective solution outputs and is outside the scope of this adapter-level description.

## 10. Quantitative load check for this geometry

A useful independent test is the **total applied vertical force**, before considering any displacement solution.

For this case, each loaded edge remains at the same width along `x`. The three CUF lower-edge widths are:

```text
left    : 20.5 mm
center  : 25.0 mm
right   : 20.5 mm
-----------------
total   : 66.0 mm
```

Thus the total applied `z` force expected from the specified traction and actual inclined surface measure is

```math
F_z = A\;b\;\sqrt{1+s^2}\int_0^L\sin\!\left(\frac{\pi x}{L}\right)dx
= A\;b\;\sqrt{1+s^2}\;\frac{2L}{\pi},
```

where `A=-1 N/mm^2`, `b=66 mm`, `s=0.04`, and `L=1000 mm`. Numerically,

```math
\boxed{F_z=-42050.5050656\ \mathrm{N}.}
```

The three segment contributions are approximately `-13061.141725 N`, `-15928.221616 N`, and `-13061.141725 N` respectively. The identical `F_z` is expected from the union of the FEM3D bottom faces.

**Independent code check:** using the actual supplied FEM3D `build_mesh()` and `_face_consistent_loads()` routines, with an in-memory field built from the posted S0/S1 endpoint coordinates (linear interpolation between those endpoints), produced:

```text
nodes             = 21303
stdBrick elements = 17280
bottom Q4 faces   = 960
sum Fx            = 0 N
sum Fy            = 0 N
sum Fz            = -42050.50506558 N
```

The numerical total matches the analytic force to floating-point precision. This test exercises FEM3D mesh and force assembly **without running OpenSees or the complete CSF-CUF solve**; it is not presented as a solved displacement/stress validation.

## 11. Reproduce and inspect

From a repository checkout, first install the project and the FEM3D dependency following the [reproducibility guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/reproducibility.md). Then run:

```bash
cd cuf/I-Shape_L

# CSF-CUF: uses the nine-polygon model and custom problem adapter.
csf-cuf cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml

# FEM3D: uses the corresponding three-polygon CSF physical model.
cd fem3d
./startfem_tap.sh
cd ..
```

To inspect the FEM3D *saved* load resultant and axial-gauge residual:

```bash
python3 - <<'PY'
import numpy as np

path = 'fem3d/output/fem3d_taper.npz'
with np.load(path) as d:
    print('FEM3D total force (N):', d['nodal_loads'].sum(axis=0))
    print('Axial gauge residual (mm):', d['axial_gauge_residual'])
    print('Nodes:', len(d['nodes']))
    print('Bricks:', len(d['elements']))
    print('Loaded bottom faces:', len(d['bottom_faces']))
PY
```

Expected for the stated amplitude/geometry: `Fz` close to `-42050.5051 N`, `Fx=Fy=0`; after successful solution and recentering, the saved axial gauge residual should be close to zero at numerical precision. The exact response displacements and stresses depend on the chosen discretizations and on successful completion of both solvers.

### Input and output roles at a glance

| Item | Required at CUF runtime? | Required at FEM3D runtime? |
|---|---|---|
| Nine-polygon CSF YAML | Yes | No |
| Three-polygon CSF YAML | No | Yes |
| CUF problem YAML | Yes | No |
| CUF case YAML | Yes | No |
| Custom `surface_halfwave_multi.py` | Yes | No |
| FEM driver and OpenSeesPy | No | Yes |
| Surface amplitude `-1` | In `problem.amplitude` | In launcher `--amplitude -1` |

## 12. Implementation details to preserve

1. **Do not interchange polygon selectors.** The nine-polygon CUF problem uses `bottom_flange_left`, `bottom_flange_center`, and `bottom_flange_right`, all at `edge_start_point_id: 0`. The three-polygon FEM geometry has one `bottom_flange` region; its lower face is subdivided numerically into FEM element faces.
2. **The custom module is a complete problem adapter.** It supplies both `build_load_vector()` and `build_constraints()`. Select it with `problem.adapter: ../../validation/surface_halfwave_multi.py` from the actual case location.
3. **Keep the traction in global `z`.** The inclination affects the *area measure*, not the force direction. Replacing the load with a normal pressure would change the physical problem.
4. **Keep the axial gauge definition.** `u_x=0` at one end is not the condition used in these benchmarks. The physical reference is the **mean of `u_x(x,0,0)` along the beam length**; the temporary FEM nodal anchor is only a device to compute a representative solution before recentering.
5. **Read the executable FEM sign, not a stale docstring.** In `_face_consistent_loads()`, the docstring contains `p_z = -amplitude * sin(...)`, but the executed statement is `q = amplitude * sin(...)`. With the launcher option `--amplitude -1`, the applied load is in **negative global `z`**, matching CUF. The existing docstring should be corrected separately for internal consistency; the execution has not been modified here.
6. **The FEM driver requires centerline nodes.** `_centerline_nodes()` requires exactly one FEM node at `(y,z)=(0,0)` at each longitudinal mesh layer, so that the saved axial mean is computed along the same physical reference line as in CUF.
7. **No model files are changed by this reference.** The comparison here is based on the posted Python sources and the public repository's exact model, problem, case, and launch files. It documents verified interfaces, physical conditions, and an independent load-assembly check; it does not claim to reproduce an entire solved FE/CUF benchmark.

---

**Summary:** The case applies the **same half-wave global-`z` traction on the same tapered lower external surface** and the **same two-end transverse support type plus zero-mean axial gauge** in CSF-CUF and FEM3D. Differences are in the sectional subdivision, approximation basis, mesh, numerical integration, and implementation of the gauge. This is the physical basis for comparing the two computed solutions.
