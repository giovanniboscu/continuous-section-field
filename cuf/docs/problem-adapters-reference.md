# CSF–CUF problem adapters - complete reference

**Bidirectional reference: from a YAML adapter to its physical load and constraints, and from a desired load/constraint to the correct adapter.**


**Inventory:** 7 complete/legacy problem adapter modules, implementing **8 distinct `problem.type` values** (one of which has two explicitly selected loading modes); **6 directly selectable load-side modules** (supporting 7 types); **4 directly selectable constraint-side modules**; and auxiliary implementations. Every `.py` file in the supplied `adapters/problem` tree is accounted for in [§8](#8-complete-source-inventory).

## Contents

1. [Architecture: a problem = loads + constraints](#1-architecture-a-problem--loads--constraints)
2. [Choose by physical behavior (reverse lookup)](#2-choose-by-physical-behavior-reverse-lookup)
3. [Choose by YAML name or complete adapter (forward lookup)](#3-choose-by-yaml-name-or-complete-adapter-forward-lookup)
4. [Complete adapter reference and exact YAML parameters](#4-complete-adapter-reference-and-exact-yaml-parameters)
5. [Constraint adapters and support conditions](#5-constraint-adapters-and-support-conditions)
6. [Reusable load-side adapters and valid pairings](#6-reusable-load-side-adapters-and-valid-pairings)
7. [Working configuration patterns](#7-working-configuration-patterns)
8. [Complete source inventory](#8-complete-source-inventory)
9. [Verification, naming rules, and known limits](#9-verification-naming-rules-and-known-limits)

---

## 1. Architecture: a problem = loads + constraints

In the solver, the structural problem consists of **two independent mechanical contributions**:

- **Loads:** a physical force/traction definition projected onto the active CUF expansion and longitudinal discretization, producing the global vector **`f`** through `build_load_vector(...)`.
- **Constraints:** the prescribed boundary/support conditions, producing a homogeneous or inhomogeneous linear system **`C u = g`** through `build_constraints(...)`.

Both contributions act on the **same CSF geometry** and **same CUF model**, but they are separate from the geometrical/material description. A problem does **not** define cross-section polygons, material constitutive coefficients, or CUF basis order.

```text
models/model.yaml ──────> CSF geometry and material fields
            │
problems/example.yaml ──> model.csf_yaml + problem.type + load parameters
            │
  cases/example.yaml ───> problem.yaml + adapter selection + CUF/mesh settings
            │
            ├── Loads:       build_load_vector() ──> f
            └── Constraints: build_constraints()  ──> C u = g
                                              │
                                      CSF–CUF solver
```

**The distinction between the two YAML files is essential:**

| YAML location | Purpose | Example |
|---|---|---|
| `problems/example.yaml` → `model.csf_yaml` | Select the **CSF physical model** | `../models/model.yaml` |
| `problems/example.yaml` → `problem.type` | Select the **problem type understood by the adapter** | `torsion_halfwave` |
| `problems/example.yaml` → other `problem.*` | Specify **load parameters**, including geometry selectors | `amplitude: 10.0` |
| `cases/example.yaml` → `problem.yaml` | Point to the physical problem YAML | `../problems/example.yaml` |
| `cases/example.yaml` → `problem.adapter` | Select **one complete Python adapter** providing load and constraints | `csf.cuf.adapters.problem.torsion_halfwave` |
| `cases/example.yaml` → `problem.load_adapter` | Select a **load-side Python module** | `csf.cuf.adapters.problem.loads.torsion_halfwave` |
| `cases/example.yaml` → `problem.constraint_adapter` | Select a **constraint-side Python module** | `csf.cuf.adapters.problem.constraints.full_clamp` |

The **case YAML has exactly two supported adapter-selection modes**:

```yaml
# Mode A: complete (legacy) adapter - the module supplies both contributions
problem:
  yaml: ../problems/torsion.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave
```

```yaml
# Mode B: explicit composition - one module for each contribution
problem:
  yaml: ../problems/torsion.yaml
  load_adapter: csf.cuf.adapters.problem.loads.torsion_halfwave
  constraint_adapter: csf.cuf.adapters.problem.constraints.full_clamp
```

`problem.adapter` **cannot** coexist with `problem.load_adapter` or `problem.constraint_adapter`. In mode B, **both** split keys are mandatory. The loader calls `build_problem(problem_type, options)` on both selected modules, composes the resulting objects, and passes the composite problem to the solver. The load-side object also provides the optional `tracked_points` for post-processing. [Source: `case.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/case.py), [source: `problem_api.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/problem/problem_api.py).

Adapter references can be **importable module names** (as in this reference) or relative/absolute `.py` paths, resolved relative to the case YAML directory. A Python file is directly selectable only if it defines the required module-level **`build_problem(...)`** function.

**Coordinate convention:** solver longitudinal coordinate `x`, physical cross-sectional coordinates `(y,z)`, displacement `(u_x,u_y,u_z)`. Let `x0`, `x1` denote beam endpoints, `L = x1 − x0`, `F_τ(y,z;x)` a transverse CUF basis function, and `N_i(x)` a longitudinal interpolation function. Examples use consistent units; if the geometry is in `mm` and forces in `N`, traction is `N/mm²` and longitudinal line-force intensity is `N/mm`.

---

## 2. Choose by physical behavior (reverse lookup)

### 2.1 I know the load I want: which problem should I use?

| Required physical loading | `problem.type` | Complete adapter (`csf.cuf.adapters.problem.…`) | Original constraints | Parameters | Detail |
|---|---|---|---|---|---|
| Concentrated **global-z** force at an **arbitrary longitudinal position** on a C-section cantilever | `c_section_cantilever` + `force.type: point` | `c_section_cantilever_point_load` | Fully clamped at `x0` | `force.amplitude, x, y, z` | [§4.1](#41-c_section_cantilever-point-or-area) |
| **Rectangular surface patch** with resultant `fx,fy,fz` (patch lies in `x–y` at constant `z`) | `c_section_cantilever` + `force.type: area` | `c_section_cantilever_point_load` | Fully clamped at `x0` | `force.x,y,z,width,height,fx,fy,fz` | [§4.1](#41-c_section_cantilever-point-or-area) |
| Concentrated physical point force with **any x/y/z components**, at normalized longitudinal position | `double_clamped_point_load` | `double_clamped_point_load` | Fully clamped at both ends, node-dependent CUF basis sizes | `x_fraction, point.y,point.z, components.x/y/z` | [§4.2](#42-double_clamped_point_load) |
| Opposite global-z **torsional line-load pair**, **uniform** over `x` | `torsion_uniform` | `torsion_uniform` | Transverse supports at both ends + axial point anchor | `amplitude` | [§4.3](#43-torsion_uniform) |
| Opposite global-z **torsional line-load pair**, **sinusoidal half-wave**, fully fixed ends | `torsion_halfwave` | `torsion_halfwave` | Both ends fully clamped | `amplitude` | [§4.4](#44-torsion_halfwave) |
| Opposite global-z **torsional line-load pair**, **sinusoidal half-wave**, Carrera support convention | `carrera_torsion_halfwave` | `bending_torsion_halfwave` | Transverse supports at both ends + integrated axial gauge | `amplitude` | [§4.5](#45-carrera_torsion_halfwave) |
| Sinusoidal distributed transverse loading of **all the lowest-`z` boundary segments** | `carrera_bending_bottom_surface_halfwave` | `bending_torsion_halfwave` | Transverse supports at both ends + integrated axial gauge | `amplitude` | [§4.6](#46-carrera_bending_bottom_surface_halfwave) |
| **Uniform global-z traction on one named physical CSF lateral surface** | `uniform_surface` | `uniform_surface` | Transverse supports at both ends + axial point anchor | `surface.polygon_name, edge_start_point_id, components.z` | [§4.7](#47-uniform_surface) |
| **Sinusoidal global-z traction on one named physical CSF lateral surface** | `surface_halfwave` | `surface_halfwave` | Both ends fully clamped | `surface.polygon_name, edge_start_point_id, amplitude` | [§4.8](#48-surface_halfwave) |

**Selection distinctions:** `carrera_torsion_halfwave` and `torsion_halfwave` describe related half-wave loads but **different constraints and load-point evaluation rules**. `carrera_bending_bottom_surface_halfwave` finds **all minimum-`z` boundary segments** automatically; `surface_halfwave` requires an **explicit polygon edge** and uses the real inclined surface measure. The parameter named `amplitude` has **different physical units** in line-force and surface-traction adapters.

### 2.2 I know the support I want: what is the constraint adapter?

| Desired support / gauge | Split `problem.constraint_adapter` suffix | Complete adapters originally using it | Details |
|---|---|---|---|
| Full end clamps at both `x0` and `x1`, fixed `basis.size` | `constraints.full_clamp` | `torsion_halfwave`, `surface_halfwave` | [§5.1](#51-full_clamp) |
| Full end clamps with **end-node-specific** transverse basis sizes | `constraints.full_clamp_node_dependent` | `double_clamped_point_load` | [§5.2](#52-full_clamp_node_dependent) |
| `u_y=u_z=0` on both ends + **axial point anchor** `u_x(x0,0,0)=0` | `constraints.transverse_supported_point_anchor` | `torsion_uniform`, `uniform_surface` | [§5.3](#53-transverse_supported_point_anchor) |
| `u_y=u_z=0` on both ends + **integrated axial gauge** | `constraints.transverse_supported_integrated_axial` | Both `carrera_*` types in `bending_torsion_halfwave` | [§5.4](#54-transverse_supported_integrated_axial) |
| Full clamp **only at the start** `x0` | *Not directly selectable as `constraint_adapter`* (`FullStartSectionClamp` has no `build_problem`) | `c_section_cantilever` | [§5.5](#55-full_start_section_clamp-helper-only) |

**Split composition:** any of the six selectable load-side modules can be paired syntactically with any of the four selectable constraint-side modules, because the latter accept and ignore `problem.type` and `options`. This is **API compatibility, not a mechanical guarantee** of well-posedness or of equivalence to a reference benchmark. The original pairs in the tables above identify the code's historical behavior.

---

## 3. Choose by YAML name or complete adapter (forward lookup)

This is the exact dispatch map. `problem.type` goes into the **problem YAML**; the Python import goes into the **case YAML**.

| `problem.type` in problem YAML | Complete `problem.adapter` (package prefix `csf.cuf.adapters.problem.`) | Load implementation | Constraint implementation |
|---|---|---|---|
| `c_section_cantilever` | `c_section_cantilever_point_load` | `loads.point_force_global_z_point.PointForceGlobalZPoint` **or** `loads.point_force_global_z_area.PointForceGlobalZArea` via `force.type` | `constraints.full_start_section_clamp.FullStartSectionClamp` |
| `double_clamped_point_load` | `double_clamped_point_load` | Local arbitrary-point physical-vector assembly | `constraints.full_clamp_node_dependent.FullClampNodeDependentConstraints` |
| `torsion_uniform` | `torsion_uniform` | Uniform opposite global-z line pair | `constraints.transverse_supported_point_anchor.TransverseSupportedPointAnchorConstraints` |
| `torsion_halfwave` | `torsion_halfwave` | Half-wave opposite global-z line pair | `constraints.full_clamp.FullClampConstraints` |
| `carrera_torsion_halfwave` | `bending_torsion_halfwave` | Carrera torsion half-wave line pair | `constraints.transverse_supported_integrated_axial.TransverseSupportedIntegratedAxialConstraints` |
| `carrera_bending_bottom_surface_halfwave` | `bending_torsion_halfwave` | Carrera minimum-`z` boundary half-wave | `constraints.transverse_supported_integrated_axial.TransverseSupportedIntegratedAxialConstraints` |
| `uniform_surface` | `uniform_surface` | Real-surface global-z uniform traction | `constraints.transverse_supported_point_anchor.TransverseSupportedPointAnchorConstraints` |
| `surface_halfwave` | `surface_halfwave` | Real-surface global-z half-wave traction (delegates to `loads.surface_halfwave`) | `constraints.full_clamp.FullClampConstraints` |

No `problem.type` is registered globally by name alone. The selected module's `build_problem(type, options)` determines whether the specified string is accepted. For example, `bending_torsion_halfwave.py` accepts two types; `torsion_halfwave.py` accepts only one. There is **no automatic filename-to-type inference**.

---

## 4. Complete adapter reference and exact YAML parameters

The tables list **problem YAML parameters**; the common `model.csf_yaml` and `problem.type` are mandatory but are not repeated in every table. Values shown in example YAML are *illustrative* and must be replaced to match the actual CSF model. For all selectors `(y,z)` and `x`, coordinates refer to the physical geometry, not the normalized CUF basis domain.

### 4.1 `c_section_cantilever` (point or area)

**Complete module:** [`c_section_cantilever_point_load.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/c_section_cantilever_point_load.py)  
**Case:** `problem.adapter: csf.cuf.adapters.problem.c_section_cantilever_point_load`  
**Problem:** `problem.type: c_section_cantilever`  
**Original constraints:** `FullStartSectionClamp`: `u_x=u_y=u_z=0` at **the first longitudinal node only**, for all `basis.size` CUF terms; opposite end free. No YAML-controlled support parameters.

`problem.force.type` is the **required explicit switch** between two distinct load objects:

#### Mode `point`: one concentrated global-z force

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `force.type` | Yes | - | Exactly `point` |
| `force.amplitude` | Yes | - | Physical concentrated `P_z` in force units (`N` if using N/mm), signed; finite numerical value |
| `force.x` | Yes | - | Absolute longitudinal application coordinate; inside `[x0,x1]`; may lie **between** FE nodes |
| `force.y` | Yes | - | Physical cross-section `y` position |
| `force.z` | Yes | - | Physical cross-section `z` position |

The adapter evaluates transverse `F_τ(y,z;x)` at the force position, then distributes the resulting generalized force through the longitudinal **FE shape functions of the containing element**. `force.x` is **not required to coincide with a node** (unlike the distinct helper `loads.point_force_global_z`). Unknown `force.*` keys are rejected.

```yaml
# problems/c_section_point.yaml
model:
  csf_yaml: ../models/c_section.yaml
problem:
  type: c_section_cantilever
  force:
    type: point
    amplitude: -1000.0  # N, global z
    x: 1000.0          # mm, absolute position
    y: 20.0            # mm
    z: 50.0            # mm
```

#### Mode `area`: one uniformly loaded rectangular boundary patch

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `force.type` | Yes | - | Exactly `area` |
| `force.x`, `force.y`, `force.z` | Yes | - | **Centroid** of patch in global physical coordinates |
| `force.width` | Yes | - | Patch extent **along longitudinal `x`**; positive |
| `force.height` | Yes | - | Patch extent **along transverse `y`**; positive |
| `force.fx` | No | `0.0` | **Total** resultant global-x force, not pressure |
| `force.fy` | No | `0.0` | **Total** resultant global-y force, not pressure |
| `force.fz` | No | `0.0` | **Total** resultant global-z force, not pressure |

The patch lies in a **constant-`z` physical `x–y` surface**; at least one resultant component must be nonzero. The adapter distributes the specified resultant vector over area `width × height`, integrates through the FE longitudinal elements crossed by the patch, and checks that its `y` extent is covered by CSF polygon boundary edges at the sampled `x` positions. The whole patch must fit inside the beam's longitudinal domain. Unknown force keys are rejected.

```yaml
# problems/c_section_patch.yaml
model:
  csf_yaml: ../models/c_section.yaml
problem:
  type: c_section_cantilever
  force:
    type: area
    x: 900.0           # mm: patch center along beam
    y: 0.0             # mm
    z: 50.0            # mm: constant-z boundary level
    width: 100.0       # mm: along x
    height: 20.0       # mm: along y
    fx: 0.0            # N: total component
    fy: 0.0
    fz: -1000.0
```

**Validation distinction:** the root adapter itself checks `problem.force` and `force.type` but does **not reject arbitrary extra keys at `problem` level**; individual point/area load classes validate their `force` mappings. The `FullStartSectionClamp` implementation is a class-only helper; it cannot be selected by `problem.constraint_adapter` without adding a factory.

### 4.2 `double_clamped_point_load`

**Complete module:** [`double_clamped_point_load.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/double_clamped_point_load.py)  
**Case:** `problem.adapter: csf.cuf.adapters.problem.double_clamped_point_load`  
**Problem:** `problem.type: double_clamped_point_load`  
**Original constraints:** `FullClampNodeDependentConstraints`, all three displacement components at **both** ends, with each end node's actual transverse DOF count.

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `x_fraction` | Yes | - | Finite longitudinal fraction in `[0,1]`; `x_p=x0+x_fraction·L` |
| `point.y` | Yes | - | Physical transverse `y` coordinate of the point |
| `point.z` | Yes | - | Physical transverse `z` coordinate of the point |
| `components.x` | At least one of x/y/z | Omitted = `0` | Total physical **point force** along global `x` |
| `components.y` | At least one of x/y/z | Omitted = `0` | Total physical **point force** along global `y` |
| `components.z` | At least one of x/y/z | Omitted = `0` | Total physical **point force** along global `z` |

All supplied numeric values must be finite; booleans are rejected. `components` must be nonempty and contain **at least one nonzero** component. Unknown keys at the top `problem` level, in `point`, or in `components` are rejected. This is a **concentrated force**, not a traction or distributed force. The adapter evaluates `F_τ(y_p,z_p;x_p)P_c` and the longitudinal FE shape functions at `x_p`; an intermediate FE-node position is supported.

```yaml
model:
  csf_yaml: ../models/model.yaml
problem:
  type: double_clamped_point_load
  x_fraction: 0.5
  point:
    y: 95.0
    z: 50.0
  components:
    x: 0.0
    z: -1000.0
```

**Contrast with C-section point mode:** this type uses a **normalized** `x_fraction` and allows a full `x/y/z` physical point-force vector; the C-section point mode uses an **absolute** `force.x`, supports only global `z`, and fixes only the starting section.

### 4.3 `torsion_uniform`

**Complete module:** [`torsion_uniform.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/torsion_uniform.py)  
**Case:** `problem.adapter: csf.cuf.adapters.problem.torsion_uniform`  
**Problem:** `problem.type: torsion_uniform`  
**Original constraints:** `TransverseSupportedPointAnchorConstraints`.

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `amplitude` | No | `1.0` | Signed longitudinal **line-force intensity**; e.g. `N/mm`; finite number, not boolean |

The loads are an opposite pair, both directed along global `z`, of intensities `+a` and `−a` per unit longitudinal `dx`. At **each** `x`, the positive point is the **leftmost vertex at the current maximum `z`**; the negative point is the **rightmost vertex at the current minimum `z`**. Therefore geometry changes can alter the lever arm and physical torque even when `a` remains constant. No path-length correction is applied.

\[
q_{\tau,z}(x)=a\left[F_\tau(P_+(x);x)-F_\tau(P_-(x);x)\right].
\]

Support: all generalized `u_y` and `u_z` amplitudes fixed at both ends, plus `u_x(x0,0,0)=0` as one physical-point axial anchor.

```yaml
model:
  csf_yaml: ../models/model.yaml
problem:
  type: torsion_uniform
  amplitude: 10.0  # N/mm if length is mm
```

Only `amplitude` is accepted as an extra top-level problem key.

### 4.4 `torsion_halfwave`

**Complete module:** [`torsion_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/torsion_halfwave.py)  
**Case:** `problem.adapter: csf.cuf.adapters.problem.torsion_halfwave`  
**Problem:** `problem.type: torsion_halfwave`  
**Original constraints:** `FullClampConstraints`, perfect clamp of **both** ends, all `u_x,u_y,u_z` CUF amplitudes.

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `amplitude` | No | `1.0` | Signed **line-force intensity** (`N/mm` with N/mm coordinates); finite, not boolean |

At `x0` and `x1`, `P_+` is the leftmost max-`z` vertex and `P_-` the rightmost min-`z` vertex. The adapter constructs **straight trajectories interpolating between these two end-section pairs**; it does **not reselect** the extreme vertices at every interior quadrature point. The forces form a first longitudinal sine half-wave:

\[
q_{\tau,z}(x)=a\sin\!\left(\frac{\pi(x-x_0)}{L}\right)
\left[F_\tau(P_+(x);x)-F_\tau(P_-(x);x)\right].
\]

The intensity is defined per global `dx`, not per actual trajectory arc length. The force pair vanishes at both ends. Both ends remain mechanically **fully clamped**, including axial warping suppression.

```yaml
model:
  csf_yaml: ../models/model.yaml
problem:
  type: torsion_halfwave
  amplitude: 10.0
```

Only `amplitude` is accepted as an extra top-level problem key.

### 4.5 `carrera_torsion_halfwave`

**Complete module:** [`bending_torsion_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/bending_torsion_halfwave.py)  
**Case:** `problem.adapter: csf.cuf.adapters.problem.bending_torsion_halfwave`  
**Problem:** `problem.type: carrera_torsion_halfwave`  
**Original constraints:** `TransverseSupportedIntegratedAxialConstraints`.

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `amplitude` | No | `1.0` | Opposite global-z **line-force intensity**; converted with `float(...)` |

At **each current cross-section**, select the leftmost maximum-`z` and rightmost minimum-`z` vertices, and apply opposite global-`z` line forces weighted by the first sine half-wave:

\[
q_{\tau,z}(x)=a\sin\!\left(\frac{\pi(x-x_0)}{L}\right)
\left[F_\tau(P_+(x);x)-F_\tau(P_-(x);x)\right].
\]

The support is **transverse simple supports** at both beam ends (`u_y=u_z=0` for every transverse CUF term) plus a single **integrated axial gauge**, not a point anchor and **not** a full clamp. Refer to [§5.4](#54-transverse_supported_integrated_axial).

```yaml
model:
  csf_yaml: ../models/model.yaml
problem:
  type: carrera_torsion_halfwave
  amplitude: 10.0
```

**Validation behavior:** this module converts `amplitude` with `float(options.get("amplitude",1.0))`; unlike `torsion_halfwave.py`, it does **not explicitly reject unknown `problem` keys**, booleans, or non-finite numeric amplitudes in its factory. This is the implemented code behavior, **not a recommendation** to use those inputs.

### 4.6 `carrera_bending_bottom_surface_halfwave`

**Complete module:** [`bending_torsion_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/bending_torsion_halfwave.py)  
**Case:** `problem.adapter: csf.cuf.adapters.problem.bending_torsion_halfwave`  
**Problem:** `problem.type: carrera_bending_bottom_surface_halfwave`  
**Original constraints:** `TransverseSupportedIntegratedAxialConstraints`.

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `amplitude` | No | `1.0` | Nominal signed-magnitude parameter for the **minimum-`z` boundary load**; code applies `−amplitude` along global `z` |

For every `x`, the adapter obtains the **minimum `z` of the current section**, identifies **all horizontal boundary segments at this elevation**, integrates the CUF basis along their physical transverse lengths `ds` (`ds=dy` on the supported horizontal segments), and applies the first longitudinal sine half-wave:

\[
B_\tau(x)=\int_{\Gamma_{z_{\min}}(x)}F_\tau(y,z_{\min}(x);x)\,ds,
\qquad
q_{\tau,z}(x)=-a\sin\!\left(\frac{\pi(x-x_0)}{L}\right)B_\tau(x).
\]

For `a > 0` the applied traction points towards **global `−z`**. The adapter's integration is `ds` times **longitudinal `dx`**; it does **not** introduce the real-surface inclination factor used by `uniform_surface` and `surface_halfwave` on a sloping ruled surface. This difference matters when comparing variable sections. No `surface` selector is accepted or needed: the loaded face is discovered from geometry.

```yaml
model:
  csf_yaml: ../models/model.yaml
problem:
  type: carrera_bending_bottom_surface_halfwave
  amplitude: 1.0
```

Validation behavior is the same as [§4.5](#45-carrera_torsion_halfwave): unknown problem keys are not explicitly rejected by the factory.

### 4.7 `uniform_surface`

**Complete module:** [`uniform_surface.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/uniform_surface.py)  
**Case:** `problem.adapter: csf.cuf.adapters.problem.uniform_surface`  
**Problem:** `problem.type: uniform_surface`  
**Original constraints:** `TransverseSupportedPointAnchorConstraints`.

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `surface.polygon_name` | Yes | - | Non-empty **S0 CSF polygon name** as known to `inspect_section_entities` |
| `surface.edge_start_point_id` | Yes | - | **Zero-based** index of the first polygon vertex of the edge; integer `>=0`; end vertex is next vertex cyclically |
| `components.z` | Yes | - | Signed uniform **global-z traction** per **real** surface area (`N/mm²` with N/mm), finite, not boolean |

The specified polygon edge must be **horizontal within S0 and S1**, i.e. its endpoints have equal `z` in each end section (an edge parallel to global `y`). It may change width, transverse position, and **height between S0 and S1**. Homologous polygon vertex indices describe the evolving edge. Only `components.z` is supported; **`components.x` and `.y` are rejected**. The applied direction is fixed global `z`, not the local surface normal.

For transverse edge half-width `h(x)` and longitudinal edge-elevation slope `s_z`, the real surface measure is

\[
d\Gamma = \sqrt{1+s_z^2}\,h(x)\,d\eta\,dx,
\quad s_z=\frac{z_{S1}-z_{S0}}{L},\quad \eta\in[-1,1].
\]

The adapter integrates `p_z F_τ` over that **real lateral surface**; `p_z` does not vary along `x`. It does not expose a separate YAML parameter for the transverse quadrature order.

```yaml
model:
  csf_yaml: ../models/model.yaml
problem:
  type: uniform_surface
  surface:
    polygon_name: web
    edge_start_point_id: 0
  components:
    z: -1.0   # N/mm^2
```

All top-level problem keys except `surface` and `components` are rejected; unsupported nested surface/component keys are rejected as well.

### 4.8 `surface_halfwave`

**Complete module:** [`surface_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/surface_halfwave.py)  
**Load implementation:** [`loads/surface_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/surface_halfwave.py)  
**Case:** `problem.adapter: csf.cuf.adapters.problem.surface_halfwave`  
**Problem:** `problem.type: surface_halfwave`  
**Original constraints:** `FullClampConstraints`: full clamps at both ends.

| Problem YAML key | Required | Default | Meaning / checks |
|---|---|---|---|
| `surface.polygon_name` | Yes | - | Non-empty name of a CSF polygon at S0 |
| `surface.edge_start_point_id` | Yes | - | Zero-based index of the first vertex of the selected edge, integer `>=0` |
| `amplitude` | Yes | - | Signed **global-z traction amplitude** per real surface area (`N/mm²`), finite, not boolean |

Geometry selection and real surface integration are the same as in [§4.7](#47-uniform_surface), but the traction follows the first sine half-wave:

\[
p_z(x)=a\sin\!\left(\frac{\pi(x-x_0)}{L}\right),\qquad
q_{\tau,z}(x)=p_z(x)\int_{\Gamma(x)}F_\tau\,d\Gamma/dx.
\]

The selected edge must be horizontal (constant transverse `z`) within **each** CSF end section; it may have distinct elevations and widths at the two ends. The actual lateral surface measure includes the inclination factor. Both ends are **fully clamped**. Unlike the uniform adapter, this YAML uses scalar `amplitude`, **not** `components.z`.

```yaml
model:
  csf_yaml: ../models/model.yaml
problem:
  type: surface_halfwave
  surface:
    polygon_name: web
    edge_start_point_id: 0
  amplitude: -1.0   # N/mm^2
```

`surface` and `amplitude` are the **only** accepted top-level problem options. `amplitude` is mandatory: there is **no default value** in this adapter. `loads.surface_halfwave.build_problem` delegates to the legacy composed factory but is still load-side usable, because a split problem consumes only its `build_load_vector` and `tracked_points`.

---

## 5. Constraint adapters and support conditions

**All four selectable constraint modules have `build_problem(problem_type, options)`.** They ignore the supplied `problem_type` and `options`: **none exposes a problem YAML parameter for support positions, directions, or prescribed values**. Their physical behavior is fixed in Python. All conditions below have zero right-hand side `g=0`.

Let `n= basis.size`, or `n0`, `n1` denote the active transverse basis size at the first and last nodes when node-dependent.

### 5.1 `full_clamp`

**Source:** [`constraints/full_clamp.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/full_clamp.py)  
**Select:** `problem.constraint_adapter: csf.cuf.adapters.problem.constraints.full_clamp`

Full clamp on both end sections: every generalized amplitude of `u_x`, `u_y`, `u_z` is zero at first and last nodes. There are `6n` scalar constraint rows. Uses the global `basis.size` at both ends. Historically used by `torsion_halfwave`, `surface_halfwave`.

### 5.2 `full_clamp_node_dependent`

**Source:** [`constraints/full_clamp_node_dependent.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/full_clamp_node_dependent.py)  
**Select:** `problem.constraint_adapter: csf.cuf.adapters.problem.constraints.full_clamp_node_dependent`

Same physical full clamps at both ends, but obtains each end node's transverse basis size from `dof_layout.basis_size_at_node(node)`. There are `3(n0+n1)` constraint rows. This distinction is relevant for node-dependent/segmented CUF expansions. Historically used by `double_clamped_point_load`.

### 5.3 `transverse_supported_point_anchor`

**Source:** [`constraints/transverse_supported_point_anchor.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/transverse_supported_point_anchor.py)  
**Select:** `problem.constraint_adapter: csf.cuf.adapters.problem.constraints.transverse_supported_point_anchor`

At both ends, set **all CUF coefficients of `u_y` and `u_z` to zero**. The axial amplitudes `u_x` remain otherwise free. Add exactly one physical axial point anchor at the start:

\[u_x(x_0,y=0,z=0)=\sum_{\tau} F_\tau(0,0;x_0)\,U_{\tau x}(x_0)=0.\]

Total `4n+1` rows. The anchor is evaluated at **the fixed transverse origin `(0,0)`**; the YAML does not allow moving it. Historically used by `torsion_uniform`, `uniform_surface`.

### 5.4 `transverse_supported_integrated_axial`

**Source:** [`constraints/transverse_supported_integrated_axial.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/transverse_supported_integrated_axial.py)  
**Select:** `problem.constraint_adapter: csf.cuf.adapters.problem.constraints.transverse_supported_integrated_axial`

At both ends set all coefficients of `u_y` and `u_z` to zero. Remove the axial rigid-body translation through **one longitudinal integral**, not a point condition:

\[\frac{1}{L}\int_{x_0}^{x_1} u_x(x,0,0)\,dx=0.\]

The implementation assembles this condition through the longitudinal FE interpolation and CUF basis evaluated at `(y,z)=(0,0)`. Total `4n+1` rows. Historically used by both problems defined by `bending_torsion_halfwave.py`.

### 5.5 `full_start_section_clamp` (helper only)

**Source:** [`constraints/full_start_section_clamp.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/full_start_section_clamp.py)

This class sets all `u_x`, `u_y`, `u_z` generalized amplitudes to zero at the **start section only** (`3n` rows); the far end remains free. It is instantiated internally by `c_section_cantilever_point_load.py`. **It has no module-level `build_problem`**, so **do not** put `csf.cuf.adapters.problem.constraints.full_start_section_clamp` into `problem.constraint_adapter` with this snapshot.

### 5.6 Quick comparison of constraints

| Condition | Start (`x0`) | End (`x1`) | Additional axial gauge | Directly selectable split adapter? |
|---|---|---|---|---|
| `full_clamp` | `u_x,u_y,u_z=0` for all `τ` | Same | None | Yes |
| `full_clamp_node_dependent` | `u_x,u_y,u_z=0` for end-node `τ` | Same | None | Yes |
| `transverse_supported_point_anchor` | `u_y,u_z=0` for all `τ` | Same | `u_x(x0,0,0)=0` | Yes |
| `transverse_supported_integrated_axial` | `u_y,u_z=0` for all `τ` | Same | Mean `u_x(x,0,0)=0` along `x` | Yes |
| `full_start_section_clamp` | `u_x,u_y,u_z=0` for all `τ` | Free | None | **No** (class-only) |

---

## 6. Reusable load-side adapters and valid pairings

### 6.1 Modules usable as `problem.load_adapter`

The following **six** modules each expose `build_problem(type, options)` and return an object with `build_load_vector(...)`:

| `problem.load_adapter` suffix (`csf.cuf.adapters.problem.` prefix) | Accepted `problem.type` values | Load behavior | Original constraint partner | Source |
|---|---|---|---|---|
| `loads.bending_torsion_halfwave` | `carrera_torsion_halfwave`, `carrera_bending_bottom_surface_halfwave` | Delegates to two-family complete factory | `constraints.transverse_supported_integrated_axial` | [file](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/bending_torsion_halfwave.py) |
| `loads.double_clamped_point_load` | `double_clamped_point_load` | Delegates to complete arbitrary-vector point-load factory | `constraints.full_clamp_node_dependent` | [file](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/double_clamped_point_load.py) |
| `loads.surface_halfwave` | `surface_halfwave` | Physical-edge half-wave global-z traction | `constraints.full_clamp` | [file](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/surface_halfwave.py) |
| `loads.torsion_halfwave` | `torsion_halfwave` | Delegates to complete torsional half-wave factory | `constraints.full_clamp` | [file](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/torsion_halfwave.py) |
| `loads.torsion_uniform` | `torsion_uniform` | Delegates to uniform torsional pair factory | `constraints.transverse_supported_point_anchor` | [file](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/torsion_uniform.py) |
| `loads.uniform_surface` | `uniform_surface` | Delegates to uniform real-surface traction factory | `constraints.transverse_supported_point_anchor` | [file](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/uniform_surface.py) |

`c_section_cantilever` has **no corresponding ready-to-select `loads.c_section_cantilever_*` module** in this snapshot. Its two point/area load classes are imported by the **complete** `c_section_cantilever_point_load` module, which also instantiates the start clamp.

### 6.2 Classes that are NOT direct split-adapter entry points

| Source | Class / role | Limitation |
|---|---|---|
| [`loads/point_force_global_z_point.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/point_force_global_z_point.py) | `PointForceGlobalZPoint`: concentrated global-z load, **arbitrary longitudinal `x`** via FE shapes | Used internally by C-section root adapter; **no module-level `build_problem`** |
| [`loads/point_force_global_z_area.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/point_force_global_z_area.py) | `PointForceGlobalZArea`: rectangular `x–y` patch with vector **total force** resultants | Used internally by C-section root adapter; **no module-level `build_problem`** |
| [`loads/point_force_global_z.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/point_force_global_z.py) | `PointForceGlobalZ`: global-z point load whose `force.x` **must match exactly one longitudinal FE node** | Class-only **legacy/alternative** implementation; **no `build_problem`**; not used by the C-section root adapter |
| [`constraints/point_force_global_z.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/point_force_global_z.py) | Contains a `PointForceGlobalZ` **load class despite its `constraints/` location** | **Not a constraint adapter** and **no `build_problem`**; do not choose as `constraint_adapter` |
| [`constraints/full_start_section_clamp.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/full_start_section_clamp.py) | `FullStartSectionClamp` | Actual C-section constraint implementation; **no `build_problem`** |
| [`_load_vector.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/_load_vector.py) | `assemble_distributed_load_vector(...)` | Numerical assembly helper, **not** a selectable adapter |

### 6.3 Can I change a load's support without changing the load?

**Yes, using split composition.** The load YAML remains unchanged; only the `constraint_adapter` of the **case YAML** changes. For example, the same `surface_halfwave` load can be combined either with its original **full clamps** or with a **transverse-supported plus axial-anchor** system.

- Original `surface_halfwave` benchmark: `loads.surface_halfwave` **+** `constraints.full_clamp`.
- Alternative mechanical problem: `loads.surface_halfwave` **+** `constraints.transverse_supported_point_anchor`.

These represent **different boundary-value problems** even with identical physical traction and geometry. Always record the selected constraint module in a comparison report.

---

## 7. Working configuration patterns

The examples below show the **two YAML files required to specify a problem**. Paths to CSF geometry files and the actual numerical values are placeholders: select a model whose geometry is compatible with the chosen load, and replace example force coordinates accordingly. The **case syntax has been checked against the supplied loader**.

### 7.1 Complete adapter: `torsion_halfwave`

**`problems/torsion.yaml`**:

```yaml
model:
  csf_yaml: ../models/model.yaml
problem:
  type: torsion_halfwave
  amplitude: 10.0
```

**`cases/torsion.yaml`**:

```yaml
case:
  name: torsion_example
problem:
  yaml: ../problems/torsion.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave
cuf:
  basis: scaled_maclaurin
  order: 4
longitudinal:
  method: finite_element
  basis: lagrange
  order: 3
  elements: 4
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/torsion_example
```

### 7.2 Split adapters: **exactly the same** `torsion_halfwave` physics

Keep **`problems/torsion.yaml` unchanged**. Replace only the `problem:` adapter declaration in the **case**:

```yaml
problem:
  yaml: ../problems/torsion.yaml
  load_adapter: csf.cuf.adapters.problem.loads.torsion_halfwave
  constraint_adapter: csf.cuf.adapters.problem.constraints.full_clamp
```

This keeps the same torsional loading and the same full clamps. It is the explicit `loads + constraints` representation of the original complete adapter.

### 7.3 Change just the constraints (a deliberately different problem)

```yaml
# cases/torsion_supported.yaml - keep the same torsion problem YAML
problem:
  yaml: ../problems/torsion.yaml
  load_adapter: csf.cuf.adapters.problem.loads.torsion_halfwave
  constraint_adapter: csf.cuf.adapters.problem.constraints.transverse_supported_point_anchor
```

Now the ends are transversely supported and the axial gauge is a point anchor; they are **not** fully clamped. The load remains the same global-z sinusoidal opposite pair. This example demonstrates the API's composition mechanism; assess its physical compatibility and stability for the intended model before using results.

### 7.4 Compare two transverse load laws without changing the case structure

For a selected horizontal CSF edge and matching geometry, a **uniform** real-surface pressure uses:

```yaml
problem:
  type: uniform_surface
  surface:
    polygon_name: web
    edge_start_point_id: 0
  components:
    z: -1.0
```

Its equivalent **first half-wave shape** (with traction amplitude `-1.0` at midspan) uses:

```yaml
problem:
  type: surface_halfwave
  surface:
    polygon_name: web
    edge_start_point_id: 0
  amplitude: -1.0
```

They are different load distributions; their original complete adapters also have **different constraints**. If a load-only comparison under the **same supports** is desired, use split mode with a common selected constraint module.

### 7.5 Wrong configurations and their correct interpretation

| Attempt | Actual behavior | Correct choice |
|---|---|---|
| `problem.adapter` together with `problem.constraint_adapter` | Case loader rejects mixed modes | Use `adapter` **alone** or both `load_adapter` and `constraint_adapter` |
| `problem.load_adapter: ...loads.point_force_global_z_point` | Loader rejects module without `build_problem` | Use complete `c_section_cantilever_point_load` + `force.type: point` |
| `problem.constraint_adapter: ...constraints.full_start_section_clamp` | Loader rejects module without `build_problem` | Use complete `c_section_cantilever_point_load` for that clamp |
| `problem.constraint_adapter: ...constraints.point_force_global_z` | This file defines a load class, **not** constraints | Choose one of the four documented constraint entry points |
| `problem.type: carrera_torsion_halfwave` with module `torsion_halfwave` | `build_problem` rejects the unsupported type | Choose `bending_torsion_halfwave` |
| `problem.type: surface_halfwave` with `components: {z: -1}` | `surface_halfwave` expects `amplitude`, not `components` | Use `amplitude: -1.0` |
| `problem.type: uniform_surface` with `amplitude: -1` | `uniform_surface` expects `components.z` | Use `components: {z: -1.0}` |
| `force.type: area` with `amplitude` instead of `fz` | C-section area factory rejects it | Use the patch geometry and **total** resultant `fx/fy/fz` |
| `double_clamped_point_load` with absolute `x` | `x_fraction` is required | Supply normalized `x_fraction` and transverse `point.y/z` |

---

## 8. Complete source inventory

**Source root:** [`src/csf/cuf/adapters/problem/`](https://github.com/giovanniboscu/continuous-section-field/tree/main/src/csf/cuf/adapters/problem). The tables distinguish a *module implementing a complete problem*, a *split load or constraint entry point*, and a *helper*. A source file existing on disk **does not** imply it can be named as a YAML adapter.

### 8.1 Root `problem/` modules (8 Python files)

| File | Classification | Direct `problem.adapter`? | What it does |
|---|---|---|---|
| [`_load_vector.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/_load_vector.py) | Helper | No | Integrates per-`τ` longitudinal fields into global load vector |
| [`bending_torsion_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/bending_torsion_halfwave.py) | Complete | **Yes** | Carrera torsion and bottom-boundary bending half-wave |
| [`c_section_cantilever_point_load.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/c_section_cantilever_point_load.py) | Complete | **Yes** | Explicit point/area load plus start clamp |
| [`double_clamped_point_load.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/double_clamped_point_load.py) | Complete | **Yes** | Arbitrary physical point force plus node-dependent double clamp |
| [`surface_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/surface_halfwave.py) | Complete compatibility wrapper | **Yes** | Real-surface half-wave plus full clamps |
| [`torsion_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/torsion_halfwave.py) | Complete | **Yes** | Sinusoidal torsional line pair plus full clamps |
| [`torsion_uniform.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/torsion_uniform.py) | Complete | **Yes** | Uniform torsional line pair plus transverse supports/point anchor |
| [`uniform_surface.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/uniform_surface.py) | Complete | **Yes** | Real-surface uniform pressure plus transverse supports/point anchor |

### 8.2 `loads/` modules (10 Python files)

| File | Classification | Direct `problem.load_adapter`? | What it does |
|---|---|---|---|
| [`__init__.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/__init__.py) | Package marker | No | Defines the loads package |
| [`bending_torsion_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/bending_torsion_halfwave.py) | Split wrapper | **Yes** | Exposes both Carrera types through load-side factory |
| [`double_clamped_point_load.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/double_clamped_point_load.py) | Split wrapper | **Yes** | Delegates double-clamped physical point force |
| [`point_force_global_z.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/point_force_global_z.py) | Class-only helper | **No** | Global-z point force constrained to one FE node |
| [`point_force_global_z_area.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/point_force_global_z_area.py) | Class-only helper | **No** | Physical rectangular patch with x/y/z total resultants |
| [`point_force_global_z_point.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/point_force_global_z_point.py) | Class-only helper | **No** | Global-z point force at arbitrary physical x using FE shapes |
| [`surface_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/surface_halfwave.py) | Reusable load implementation | **Yes** | Real physical lateral surface half-wave |
| [`torsion_halfwave.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/torsion_halfwave.py) | Split wrapper | **Yes** | Delegates torsion half-wave load |
| [`torsion_uniform.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/torsion_uniform.py) | Split wrapper | **Yes** | Delegates uniform torsion load |
| [`uniform_surface.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/loads/uniform_surface.py) | Split wrapper | **Yes** | Delegates uniform physical-surface traction |

### 8.3 `constraints/` modules (7 Python files)

| File | Classification | Direct `problem.constraint_adapter`? | What it does |
|---|---|---|---|
| [`__init__.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/__init__.py) | Package marker | No | Defines the constraints package |
| [`full_clamp.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/full_clamp.py) | Split constraint | **Yes** | Double full clamp (`6n` rows) |
| [`full_clamp_node_dependent.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/full_clamp_node_dependent.py) | Split constraint | **Yes** | Double full clamp with node-specific basis sizes |
| [`full_start_section_clamp.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/full_start_section_clamp.py) | Class-only helper | **No** | Cantilever start clamp |
| [`point_force_global_z.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/point_force_global_z.py) | Misplaced load helper | **No** | **Load class**, not a constraint |
| [`transverse_supported_integrated_axial.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/transverse_supported_integrated_axial.py) | Split constraint | **Yes** | Both-end transverse supports + integrated axial gauge |
| [`transverse_supported_point_anchor.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/constraints/transverse_supported_point_anchor.py) | Split constraint | **Yes** | Both-end transverse supports + physical axial point anchor |

**Inventory total: 8 + 10 + 7 = 25 `.py` files**, including two `__init__.py` package markers, plus one separate source README, [`README_double_clamped_point_load.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/README_double_clamped_point_load.md).

---

## 9. Verification, naming rules, and known limits

### 9.1 Verification performed against the supplied code

- Enumerated **all `.py` modules** under `adapters/problem` in the uploaded archive; reconciled their role with the code's actual `build_problem(...)` entry points.
- Checked the exact **`problem.type` dispatch strings** in all seven complete adapters (eight strings in total).
- Read the **parameter parsing/validation code**, the actual `build_load_vector` implementations, and the actual `build_constraints` implementations; distinguished defaults from required options and physical force from surface traction.
- Executed factory-construction checks for **all 8 complete problem types**, both `c_section_cantilever` load modes, the **6 load modules** (7 supported type dispatches), and the **4 constraint modules**; verified their corresponding method contracts.
- Checked and executed both **complete** and **split** case YAML adapter-selection patterns through the supplied `load_case`, `load_problem`, `load_problem_adapter`, and `compose_problem` contracts.

**Verification boundary:** the uploaded ZIP contains the CUF Python tree but not the whole external `csf` package and not a benchmark model. These are **source/interface and YAML-loader checks**, **not complete CSF–CUF numerical benchmark runs**. The reference describes the behavior implemented in the supplied snapshot, rather than claiming full-solver validation for every possible physical load/constraint pairing.

### 9.2 Parameter names are not interchangeable

| Name | Actual meaning / examples |
|---|---|
| `problem.type` | Physical problem discriminator (`torsion_halfwave`, `surface_halfwave`, etc.), **not** a module path |
| `problem.adapter` | Complete Python module selected in **case YAML**, **not** in physical problem YAML |
| `problem.load_adapter` | Module implementing load side, selected in **case YAML** |
| `problem.constraint_adapter` | Module implementing constraint side, selected in **case YAML** |
| `problem.amplitude` | May mean `N/mm` **line-load intensity** (`torsion*`) or `N/mm²` **surface traction** (`surface_halfwave`); Carrera bottom boundary also uses it with an implicit `−z` sign |
| `problem.force.amplitude` | **Total point force** in `N` for C-section `force.type: point` |
| `problem.force.fx/fy/fz` | **Total force resultants** in `N` across a rectangular C-section `force.type: area` patch; *not* pressure |
| `problem.components.z` | `N/mm²` **surface traction** in `uniform_surface`, but `N` **point force** in `double_clamped_point_load` |
| `problem.force.x` | Physical absolute longitudinal `x` in a C-section point/area load |
| `problem.x_fraction` | Normalized longitudinal fraction (`0..1`) in `double_clamped_point_load` |
| `problem.surface.edge_start_point_id` | **Zero-based polygon vertex index**, not a longitudinal node or mesh edge ID |

### 9.3 Especially important limitations

1. **Static support conventions are part of each legacy adapter**: identical-looking torsional loads may have fundamentally different constraints.
2. **Split constraints have no YAML support parameters in this snapshot**. To move the axial anchor, change supported components, or implement another support scheme, a new/modified Python constraint implementation is needed.
3. **Physical surface selectors support horizontal CSF polygon edges at both end sections**, not arbitrary polygon edges. A varying elevation between S0/S1 is supported, and the real-surface adapters include its inclination measure.
4. **`carrera_bending_bottom_surface_halfwave` does not use the same real-surface measure as `surface_halfwave`/`uniform_surface`**. Compare those models using their actual implemented loading definitions.
5. **Point and area helpers are not themselves valid `load_adapter` modules** without `build_problem` factories; the C-section root module composes them with a start clamp.
6. **Importability of a module does not imply validity as an adapter**; `load_problem_adapter` requires the callable factory. Conversely, an adapter can accept multiple `problem.type` strings.
7. **`full_clamp` and the transverse-support implementations use `basis.size`**, while `full_clamp_node_dependent` explicitly uses end-node-specific transverse sizes. For segmented/node-dependent CUF configurations, verify that the chosen support implementation matches the active DOF layout.

### 9.4 Source navigation

- [All problem adapters](https://github.com/giovanniboscu/continuous-section-field/tree/main/src/csf/cuf/adapters/problem)
- [Complete problem API and split composition](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/problem/problem_api.py)
- [Case YAML loader: legacy vs split adapters](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/case.py)
- [Runner: actual adapter loading and construction](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/__main__.py)
- [Numerical load assembly helper](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/problem/_load_vector.py)

**Reference rule:** Given any `problem.type`, use [§3](#3-choose-by-yaml-name-or-complete-adapter-forward-lookup) to find its complete adapter and original boundary conditions; use [§4](#4-complete-adapter-reference-and-exact-yaml-parameters) for accepted YAML parameters; use [§5](#5-constraint-adapters-and-support-conditions) and [§6](#6-reusable-load-side-adapters-and-valid-pairings) if you want to construct a different `loads + constraints` problem. Given a desired physical force or support, start with the reverse indexes in [§2](#2-choose-by-physical-behavior-reverse-lookup).
