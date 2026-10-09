# CUF Case Configuration - YAML Reference

This is the **configuration reference for CSF-CUF case YAML files**. It describes the supported configuration *patterns*, not just the parameters used in one numerical example. For the physical interpretation of the model, start with [From the Physical Problem to the CUF Model](readme.md). For the referenced problem YAML and for result export, see [Problem Configuration](problem_configuration.md) and [Output Configuration](output_configuration.md).

> **Source and scope.** The loader-level alternatives, defaults, and validation rules below were traced through `src/csf/cuf/case.py` (available source snapshot with revisions dated 21–30 September 2026). The current GitHub `main` file was not retrievable for a live comparison while preparing this edition. The reference therefore documents **all branches in that inspected loader**, not an unverified inventory of every plugin or adapter that may be installed in a newer revision. A plugin may add its own allowed options and stricter validation; consult its implementation before treating a plugin-specific example as executable.

**Principle:** one *case* selects a physical problem and its numerical approximation. You can change the CUF expansion, longitudinal FE representation, loads/constraints adapter arrangement, quadrature, and output independently, subject to the explicit compatibility rules below.

## 1. Where the case fits

```text
case.yaml
  |
  |-- case -------------------> case identifier
  |-- problem.yaml -----------> separate physical problem YAML
  |                                `-- CSF geometry/material model
  |-- problem adapter(s) -----> load + boundary-condition implementation
  |-- cuf --------------------> transverse/generalized expansion plugin
  |-- longitudinal -----------> longitudinal FE basis and mesh
  |-- section_integration ----> polygon quadrature
  |-- solver -----------------> equilibration settings
  |-- sampling ---------------> requested result sampling
  `-- output -----------------> post-processing adapter and output directory
```

**Path convention.** Paths in the case YAML are resolved relative to the **directory containing that case YAML**, not the current working directory. Dotted adapter names are imported as Python modules. External Python paths used for expansion plugins are also resolved relative to the case file. Paths to output directories follow the same relative-path convention.

**Coordinate convention.** In the CUF solver, `x` is longitudinal and `y, z` are transverse. An expansion can depend on all three physical coordinates. An adapter that evaluates such an expansion must supply the evaluation coordinates; in particular, the basis value is called as `basis.value(tau, y, z, x=x)`. The plugin receives `x` as a named argument. This is a general interface requirement, independent of any particular example.

## 2. Configuration patterns at a glance

| Decision | Supported choice A | Supported choice B | Rule |
|---|---|---|---|
| Problem adapters | One `problem.adapter` | Both `problem.load_adapter` and `problem.constraint_adapter` | **Exactly one arrangement** |
| CUF expansion | `cuf.basis` + optional `order` and `basis_options` | `cuf.segments` | **Mutually exclusive** |
| CUF basis source | Registered family name | External `.py` plugin | Both are accepted by the basis resolver |
| Longitudinal partition | `longitudinal.elements` | `longitudinal.element_boundaries` | **Exactly one is required** |
| Longitudinal basis | Registered basis name (default `lagrange`) | External `.py` basis | Subject to the longitudinal basis resolver |
| Equilibration | Single integer | YAML sequence of integers | Scalar solve or multi-run sweep |
| Problem/output adapter reference | Dotted module path | File path to a `.py` adapter | Same reference key; choose one form |
| Section integration | Omit optional block | Set `fixed_gauss_polygon` and/or `gauss_order` | Runtime in the inspected engine supports `fixed_gauss_polygon` |

These choices can be combined independently unless a specific plugin or adapter imposes additional conditions.

## 3. Minimum case using loader defaults

```yaml
# Basic envelope. The physical problem and the named adapters must exist.
problem:
  yaml: ../problems/torsion_halfwave.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave

# An empty cuf mapping selects the built-in defaults:
# basis = scaled_maclaurin; order = 5; basis_options = {}.
cuf: {}

# A longitudinal partition is always required.
# All other longitudinal options may use their defaults.
longitudinal:
  elements: 1

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/basic_case
```

The `case`, `section_integration`, `solver`, and `sampling` blocks may be omitted. **Do not omit the entire `cuf` block or the longitudinal partition**: the inspected loader requires `cuf` to be a mapping and requires *exactly one* partition key. The example is syntactically sufficient for the case loader if its referenced components exist; it does not assert that the physical problem itself is valid.

## 4. Top-level blocks and their role

| Block | Presence in the case YAML | Responsibility |
|---|---|---|
| `case` | Optional mapping | Case identity |
| `problem` | Required mapping | Problem file and adapters |
| `cuf` | Required mapping | Expansion family or segmented expansion law |
| `longitudinal` | Required mapping | FE basis, order and partition |
| `section_integration` | Optional mapping | Polygon integration |
| `solver` | Optional mapping | Numerical equilibration |
| `sampling` | Optional mapping | Requested output stations/grids |
| `output` | Required mapping | Output adapter and result directory |

## 5. `case`: case identity

```yaml
case:
  name: torsion_halfwave_legendre_N08
```

`case.name` is optional. If omitted, the loader uses the **case YAML filename without its suffix** (`Path.stem`). The name is an identifier, not an instruction for the basis or FE order: a case whose name contains `N08` still uses whatever is specified in `cuf.order`.

Prefer a descriptive, filename-safe name. The result-writing workflow may impose additional filename restrictions on top of the case loader.

## 6. `problem`: all adapter-selection modes

The `problem` block always references an existing physical problem YAML through `problem.yaml`. The remaining fields select *how* loads and constraints are constructed.

### 6.1 One combined, registered adapter

```yaml
problem:
  # Physical problem description, separately from the case.
  yaml: ../problems/torsion_halfwave.yaml

  # One importable module handles loads and constraints.
  adapter: csf.cuf.adapters.problem.torsion_halfwave
```

### 6.2 One combined, external Python adapter

```yaml
problem:
  yaml: ../problems/my_problem.yaml

  # Path relative to this case YAML file.
  adapter: ../adapters/my_problem_adapter.py
```

### 6.3 Two distinct registered adapters

```yaml
problem:
  yaml: ../problems/my_problem.yaml

  # Loads and constraints can be implemented separately.
  # Replace these example names with modules that really exist.
  load_adapter: my_project.adapters.load_adapter
  constraint_adapter: my_project.adapters.constraint_adapter
```

### 6.4 Two distinct external Python adapters

```yaml
problem:
  yaml: ../problems/my_problem.yaml
  load_adapter: ../adapters/my_loads.py
  constraint_adapter: ../adapters/my_constraints.py
```

The two references may also use different supported forms (one module, one file path). The case loader resolves each independently.

**Mandatory compatibility rules:**

- Use **either** `problem.adapter` **or** the complete pair `problem.load_adapter` and `problem.constraint_adapter`.
- A combined adapter **cannot** be combined with either split key.
- A split arrangement must contain **both** keys; one alone is invalid.
- Adapter names and file paths must resolve to implementations that satisfy the selected adapter contract. The loader validates the arrangement, not the physics of an arbitrary custom adapter.

For the internal `model` / `problem` blocks in the referenced problem YAML, see [Problem Configuration](problem_configuration.md).

## 7. `cuf`: every expansion-selection mode

The case loader provides **two different CUF configuration paths**: a single registered/external expansion law, or a direct law constructed from longitudinal segments. They are alternatives, not features that should be combined in a single `cuf` block.

### 7.1 Registered polynomial families

The conventional named families used in the project are shown below. Each snippet is an **alternative replacement** for the complete `cuf` block; they are not four blocks to place in one YAML file.

#### Scaled Legendre

```yaml
cuf:
  # Complete scaled Legendre CUF expansion in the section plane.
  # The longitudinal FE approximation remains independent.
  basis: scaled_legendre

  # Polynomial expansion order requested from this family.
  order: 8
```

#### Scaled Lagrange

```yaml
cuf:
  # Lagrange-based CUF expansion on the transverse section.
  basis: scaled_lagrange

  # May be changed independently of longitudinal.order.
  order: 8
```

#### Scaled Maclaurin

```yaml
cuf:
  # Complete scaled Maclaurin expansion.
  basis: scaled_maclaurin
  order: 8
```

#### Tensor-product scaled Maclaurin

```yaml
cuf:
  # Tensor-product variant of the scaled Maclaurin family.
  # Its term count need not match the complete-total-degree family.
  basis: scaled_maclaurin_tensor
  order: 8
```

The manual also records the historical name `scaled_lagrange_q1`. Treat aliases as **version-dependent**: select the registered name exposed by the installed implementation. `case.py` does not enumerate the registry or define the polynomials; it forwards the basis reference to the expansion system.

**Important:** `cuf.order` has the meaning assigned by the selected basis. Do not infer the number of basis functions `M` from the number `N` without consulting that family's definition and the solver's reported `M`.

### 7.2 External Python expansion (three-coordinate example)

```yaml
cuf:
  # Custom expansion defined in a separate Python file.
  # A custom expansion may depend on x, y, z and CSF geometry.
  basis: ../expansions/xyz_demo_expansion.py

  # Order argument passed to the custom plugin.
  # The demonstration defines M=4 functions explicitly.
  order: 1
```

For the demonstration, the four functions are:

$$
F_1 = 1,\qquad F_2=y,\qquad F_3=z,\qquad F_4=xyz.
$$

The plugin evaluates the functions and supplies their derivatives in `x`, `y`, and `z`. The integer `order: 1` is a plugin parameter, **not** a statement that there are one or two terms, and not a substitute for `longitudinal.order`.

No special `cuf` flag is needed to enable longitudinal dependence: that behavior is determined by the selected plugin. **When any adapter samples a basis function, it must provide the actual physical evaluation coordinates.** Do not replace the longitudinal coordinate by a fixed reference value in general integrations.

### 7.3 Using defaults for a standard expansion

```yaml
cuf: {}
```

This is equivalent *at case-loader level* to:

```yaml
cuf:
  basis: scaled_maclaurin
  order: 5
  basis_options: {}
```

Explicit settings are preferable for published numerical benchmarks because they make the approximation immediately visible.

### 7.4 Plugin-specific `basis_options`

```yaml
cuf:
  basis: ../expansions/my_custom_expansion.py
  order: 4
  basis_options: {}
```

`basis_options` is an **optional YAML mapping**; `case.py` passes it to the basis implementation without defining universal option names. A custom plugin may define accepted keys, defaults, and validation. Other plugins may reject any nonempty mapping. For example, the inspected `scaled_legendre` and `scaled_lagrange` implementations reject unsupported nonempty `basis_options`.

**Do not copy invented parameters** such as `continuity`, `polygon`, `blend_weight` or `symbolic` into this mapping unless the selected plugin actually declares them. The case loader does not provide such keywords by itself.

### 7.5 Longitudinally segmented expansion: `cuf.segments`

`case.py` also accepts a nonempty list of segment definitions. Every segment requires its own `basis` and `order` (at least 1); each can optionally have `basis_options`.

```yaml
cuf:
  # Alternative to the single global CUF expansion.
  # Illustrates the loader-validated fields of each segment.
  segments:
    - basis: scaled_legendre
      order: 4
      basis_options: {}

    - basis: scaled_lagrange
      order: 6
      basis_options: {}
```

**Scope of this snippet:** the YAML above demonstrates the common *loader-level fields only*. It is **not a complete runnable segmented case**: exact segment-interval keys, matching to the longitudinal domain, polygon-specific laws, blending, and continuity requirements are defined or validated by the segmented-expansion builder. Those additional keys must be taken from the implementation of that builder rather than guessed from `case.py`.

| Segment key | Loader rule |
|---|---|
| `cuf.segments` | Nonempty YAML sequence of mappings |
| `cuf.segments[].basis` | Required, nonempty string |
| `cuf.segments[].order` | Required integer, `>= 1` |
| `cuf.segments[].basis_options` | Optional mapping |
| Other segment fields | Preserved for downstream interpretation; not specified by `case.py` |

In segmented mode, the loader computes the starting quadrature defaults using the **maximum segment order**. Segment-specific geometric or continuity behavior is outside the case loader's validation boundary.

**Forbidden combination:**

```yaml
# INVALID: cuf.segments cannot coexist with these global keys.
cuf:
  basis: scaled_legendre
  order: 8
  segments:
    - basis: scaled_lagrange
      order: 4
```

The same prohibition includes top-level `cuf.basis_options`. It does **not** prevent each individual segment from defining its own `basis_options`.

### 7.6 CUF fields: consolidated reference

| Key | Required | Type / restriction | Loader default |
|---|---|---|---|
| `cuf.basis` | No, except not allowed with `segments` | Registered name or external basis file | `scaled_maclaurin` |
| `cuf.order` | No, except not allowed with `segments` | Integer `>= 1` | `5` |
| `cuf.basis_options` | No, except not allowed with `segments` | Mapping; keys defined by plugin | `{}` |
| `cuf.segments` | Only when choosing segmented mode | Nonempty list of segment mappings | Absent |
| `cuf.segments[].basis` | Yes, in each segment | Nonempty string | None |
| `cuf.segments[].order` | Yes, in each segment | Integer `>= 1` | None |
| `cuf.segments[].basis_options` | No | Mapping, interpreted by segment plugin | Absent |

## 8. `longitudinal`: all FE representation patterns

**Separate from CUF.** The displacement field has the form

$$
\mathbf u(x,y,z)=\sum_i\sum_\tau N_i(x)F_\tau(x,y,z)\mathbf q_{i\tau}.
$$

The longitudinal interpolation $N_i(x)$ and the CUF expansion $F_\tau$ are independently selected, even when the expansion itself depends on `x`.

### 8.1 Uniform partition by element count

```yaml
longitudinal:
  method: finite_element

  # Exactly two equally sized elements along the beam.
  elements: 2

  # Longitudinal Lagrange interpolation order.
  basis: lagrange
  order: 6
```

### 8.2 Explicit nonuniform partition

```yaml
longitudinal:
  method: finite_element

  # Normalized element interfaces. This creates three elements:
  # [0.00,0.20], [0.20,0.55], [0.55,1.00].
  element_boundaries: [0.00, 0.20, 0.55, 1.00]

  basis: lagrange
  order: 6
```

`element_boundaries` must be a sequence of **finite, strictly increasing normalized coordinates**, with at least two entries. Its endpoints must be 0 and 1, within absolute tolerance `1e-12`. The loader normalizes accepted endpoints to exactly `0.0` and `1.0`. A partition defines one fewer element than its number of boundaries.

**Exclusive rule:** exactly one of `elements` or `element_boundaries` must be present. Neither `elements: 1` plus `element_boundaries: [0, 1]` nor a longitudinal block lacking both is allowed.

### 8.3 Longitudinal basis: registered family

```yaml
longitudinal:
  elements: 1

  # Default longitudinal basis, specified explicitly.
  basis: lagrange
  order: 6
```

A registered longitudinal basis is selected by name. The default name is `lagrange`, and the default interpolation order is 3. Other names require an actual registered implementation; the case loader does not itself enumerate all longitudinal plugins.

### 8.4 Longitudinal basis: external Python implementation

```yaml
longitudinal:
  elements: 1

  # An external longitudinal shape-function plugin.
  basis: ../longitudinal/my_longitudinal_basis.py
  order: 6

  # Options only if the external implementation accepts them.
  basis_options: {}
```

The longitudinal basis resolver accepts a basis reference independent of the transverse CUF basis. A longitudinal plugin is not selected by placing its file under `cuf.basis`.

### 8.5 Requested integration order (explicit or automatic)

```yaml
longitudinal:
  elements: 1
  order: 6

  # Requested Gauss-Legendre quadrature order along x.
  gauss_order: 15
```

If `gauss_order` is omitted, the loader requests:

$$
n_{G,x}^{\mathrm{request}} = N_{\mathrm{CUF,default}} + N_{\mathrm{FE}} + 1,
$$

where `N_CUF,default` is the configured global `cuf.order`, or the largest `order` among `cuf.segments`. This is a **starting request**, not necessarily the effective Gauss order. The numerical integration machinery may increase it to satisfy degree estimates and basis requirements. The explicit request must be an integer `>= 1`.

### 8.6 Longitudinal material-degree hint

```yaml
longitudinal:
  elements: 1
  order: 6

  # Hint for a longitudinal polynomial material variation.
  # Degree 0 means a constant polynomial contribution.
  material_polynomial_degree: 0
```

This optional nonnegative integer informs longitudinal quadrature estimation; it **does not define the material model**. When absent (or given as YAML `null`), the loader stores `None` and delegates degree estimation to the downstream implementation. For complex material laws, choose the hint only if its meaning is supported by the selected constitutive model.

### 8.7 Longitudinal fields: consolidated reference

| Key | Required | Type / restriction | Loader default |
|---|---|---|---|
| `longitudinal.method` | No | String; inspected runtime supports `finite_element` | `finite_element` |
| `longitudinal.elements` | Choice A | Integer `>= 1`, exclusive with boundaries | None |
| `longitudinal.element_boundaries` | Choice B | Normalized, finite, strictly increasing sequence from 0 to 1 | None |
| `longitudinal.basis` | No | Registered longitudinal basis or external file | `lagrange` |
| `longitudinal.order` | No | Integer `>= 1` | `3` |
| `longitudinal.basis_options` | No | Mapping interpreted by the selected plugin | `{}` |
| `longitudinal.gauss_order` | No | Integer `>= 1` | `N_CUF,default + longitudinal.order + 1` |
| `longitudinal.material_polynomial_degree` | No | Integer `>= 0` or `null` | `null` (automatic handling) |

## 9. `section_integration`: explicit or default

```yaml
section_integration:
  # Polygonal section integration over domains provided by CSF.
  method: fixed_gauss_polygon

  # Requested Gauss order; the basis may require a larger effective order.
  gauss_order: 6
```

Both keys are optional, and the entire block may be omitted. The loader uses `fixed_gauss_polygon` by default. If `gauss_order` is omitted, the loader requests the global CUF order plus one, or the largest segment order plus one in segmented mode. Explicit `gauss_order` must be at least 2.

**Runtime support:** although `case.py` stores `section_integration.method` as a string, the inspected numerical engine accepts only `fixed_gauss_polygon`. Do not assume additional method names are operational merely because the loader can parse a string.

For converged benchmarks, publish the **effective** section quadrature observed in solver logs, not only the requested YAML order.

## 10. `solver`: single equilibration or sweep

### 10.1 Omit the block (loader default)

```yaml
# No solver block: equilibration defaults to 3 iterations
```

### 10.2 Solve the un-equilibrated system

```yaml
solver:
  equilibration:
    iterations: 0
```

### 10.3 One requested equilibration count

```yaml
solver:
  equilibration:
    iterations: 4
```

### 10.4 Multiple counts in one requested sweep

```yaml
solver:
  equilibration:
    # A YAML list requests multiple solves/checkpoints.
    iterations: [0, 1, 2, 3, 4, 5, 6]
```

The loader accepts a **nonnegative integer** or a **nonempty list of nonnegative integers**. A list is sorted in ascending order and duplicates are removed: `[4, 0, 2, 4]` becomes `(0, 2, 4)`. Scalar form means one solve; list form means a sequence of requested runs. A failed numerical solve does not become valid merely because the YAML form is accepted.

The inspected `case.py` loader defaults to **3**, not 8. Older text manuals may mention a different historical default; the loader is authoritative for its version.

## 11. `sampling`: omit or customize

```yaml
sampling:
  # Normalized longitudinal stations used to evaluate sections/results.
  stations: [0.00, 0.25, 0.50, 0.75, 1.00]

  # Output resolution along the beam. Not FEM nodes.
  displacement_samples: 201

  # Cross-sectional stress sample resolution. Not section quadrature.
  stress_grid: 31
```

The entire `sampling` mapping is optional. Loader defaults are `stations: [0.0, 0.5]`, `displacement_samples: 201`, and `stress_grid: 41`. `stations` must be **nonempty**, and each value must lie in `[0, 1]`. They are normalized output positions, not an FE partition.

The case loader converts the sampling counts to integers but leaves detailed downstream constraints to the output/post-processing implementation. Do not assume that increasing them changes the solved finite-element approximation: it changes how the existing continuous field is queried.

## 12. `output`: registered or external adapter

### 12.1 Standard output adapter

```yaml
output:
  # Registered post-processing implementation.
  adapter: csf.cuf.adapters.output.post

  # Destination folder relative to the case file.
  directory: ../output/torsion_halfwave_legendre_N08
```

### 12.2 External output adapter

```yaml
output:
  # Python file implementing the output adapter contract.
  adapter: ../adapters/my_output.py
  directory: ../output/my_custom_case
```

`output.adapter` and `output.directory` are required. The loader accepts a Python module or file path for the adapter; it does not define the files an adapter must write. For reconstructed fields and diagnostics, see [Output Configuration](output_configuration.md).

## 13. Complete case examples

The following are **alternative full case YAML files**. References to physical problem files and custom Python modules must exist. The examples deliberately use different, compatible parameter combinations; they are not an exhaustive list of arbitrary runtime plugins.

### 13.1 Conventional Legendre, uniform single FE

```yaml
case:
  name: torsion_legendre_N08

problem:
  yaml: ../problems/torsion_halfwave.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave

cuf:
  basis: scaled_legendre
  order: 8

longitudinal:
  method: finite_element
  elements: 1
  basis: lagrange
  order: 6

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 10

solver:
  equilibration:
    iterations: 3

sampling:
  stations: [0.0, 0.5, 1.0]
  displacement_samples: 201
  stress_grid: 41

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/torsion_legendre_N08
```

### 13.2 Custom three-coordinate CUF expansion and irregular longitudinal FE mesh

```yaml
case:
  name: torsion_xyz_demo

problem:
  yaml: ../problems/torsion_halfwave.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave

cuf:
  basis: ../expansions/xyz_demo_expansion.py
  order: 1

longitudinal:
  method: finite_element
  element_boundaries: [0.00, 0.35, 1.00]
  basis: lagrange
  order: 6
  gauss_order: 15

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6

sampling:
  stations: [0.0, 0.25, 0.5, 0.75, 1.0]

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/torsion_xyz_demo
```

The adapter and custom plugin must implement the full three-coordinate evaluation contract. This is a general requirement, not an indication that the above problem adapter has been tested with that particular plugin.

### 13.3 Split custom adapters with an equilibration sweep

```yaml
case:
  name: custom_problem_sweep

<<<<<<< HEAD
| Key | Type | Required | Loader default | Meaning |
|---|---|---|---|---|
| `case.name` | String | No | Stem of case YAML filename | Identifier for logs and results |

Prefer names that match the chosen physical problem and current expansion; the name itself does not set solver parameters.

## 5. `problem` - reference to the physical problem

```yaml
=======
>>>>>>> 77772d28 (case configuration update)
problem:
  yaml: ../problems/my_problem.yaml
  load_adapter: ../adapters/my_loads.py
  constraint_adapter: ../adapters/my_constraints.py

<<<<<<< HEAD
| Key | Type | Required | Meaning |
|---|---|---|---|
| `problem.yaml` | Path | Yes | Separate YAML describing model reference and physical problem |
| `problem.adapter` | Dotted module name or `.py` file path | Conditional | Combined adapter for loads and constraints |
| `problem.load_adapter` | Dotted module name or `.py` file path | Conditional | Separate load adapter |
| `problem.constraint_adapter` | Dotted module name or `.py` file path | Conditional | Separate constraint adapter |

The loader enforces **exactly one** of the following adapter configurations:

```yaml
# Combined adapter
problem:
  yaml: ../problems/problem.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave
```

```yaml
# Split adapters (use genuine available adapter modules)
problem:
  yaml: ../problems/problem.yaml
  load_adapter: path/to/load_adapter.py
  constraint_adapter: path/to/constraint_adapter.py
```

Do **not** combine `problem.adapter` with either split adapter. When using the split form, both `load_adapter` and `constraint_adapter` must be provided. The example file names in the second snippet are placeholders, not advertised built-in adapters.

For the contents of the referenced file, see [Problem Configuration](problem_configuration.md).

## 6. `cuf` - expansion law

### 6.1 Standard or external expansion

```yaml
=======
>>>>>>> 77772d28 (case configuration update)
cuf:
  basis: scaled_lagrange
  order: 10

<<<<<<< HEAD
| Key | Type | Required | Loader default | Meaning |
|---|---|---|---|---|
| `cuf.basis` | Registered name or external file path | No | `scaled_maclaurin` | Selected CUF expansion |
| `cuf.order` | Integer ≥ 1 | No | `5` | Expansion order as interpreted by the chosen plugin |
| `cuf.basis_options` | Mapping | No | `{}` | Options passed to the chosen basis implementation |

Families demonstrated in project material include `scaled_legendre`, `scaled_lagrange`, `scaled_maclaurin` and `scaled_maclaurin_tensor`. The set of registered families and accepted `basis_options` is defined by the installed plugins. A custom basis can be specified using a path such as `../expansions/xyz_demo_expansion.py`.

The expansion may depend on all three CUF coordinates and on CSF geometry:

$$
F_\tau = F_\tau(x,y,z;\mathcal G_{\mathrm{CSF}}).
$$

A custom plugin exposes the basis function and first derivatives. The solver uses the mathematical interface, not the plugin's internal construction. Generalized expansion background and the four-function demonstration belong in the expansion documentation, not in this YAML parameter table.

**Adapter coordinate contract.** When a load, constraint or output adapter evaluates an expansion at a physical point, it must provide the actual longitudinal and transverse coordinates. The standard basis call uses `basis.value(tau, y, z, x=x)`; analogous derivative calls must follow the corresponding interface. Integrals involving an `x`-dependent basis must use the varying value at their actual integration points.

### 6.2 Direct segmented expansion laws

Instead of top-level `cuf.basis`, `cuf.order`, and `cuf.basis_options`, the loader also accepts:

```yaml
cuf:
  segments:
    - basis: scaled_legendre
      order: 4
      basis_options: {}
    - basis: scaled_legendre
      order: 6
      basis_options: {}
```

This snippet shows the **loader-level shape only**, not a complete operational specification for any particular segmenting plugin.

| Key | Type | Loader requirement |
|---|---|---|
| `cuf.segments` | Nonempty sequence of mappings | Optional alternative to standard `cuf` fields |
| `cuf.segments[].basis` | Nonempty string | Required for each segment |
| `cuf.segments[].order` | Integer ≥ 1 | Required for each segment |
| `cuf.segments[].basis_options` | Mapping | Optional for each segment |

The loader rejects `cuf.segments` when combined with top-level `cuf.basis`, `cuf.order` or `cuf.basis_options`. Additional segment keys and the meaning of intervals, polygon scope, blending and continuity must be documented by the actual segmented-expansion implementation; they cannot be inferred from the generic loader alone. The largest segment order is used to construct default quadrature requests.

## 7. `longitudinal` - finite-element approximation

```yaml
longitudinal:
  method: finite_element
  element_boundaries: [0.0, 0.5, 1.0]
  basis: lagrange
  order: 6
  basis_options: {}
  gauss_order: 15
  material_polynomial_degree: 0
```

| Key | Type | Required | Loader default / restriction |
|---|---|---|---|
| `longitudinal.method` | String | No | `finite_element` |
| `longitudinal.basis` | Registered name or external path | No | `lagrange` |
| `longitudinal.order` | Integer ≥ 1 | No | `3` |
| `longitudinal.basis_options` | Mapping | No | `{}` |
| `longitudinal.elements` | Integer ≥ 1 | Conditional | Exactly one of `elements` / `element_boundaries` |
| `longitudinal.element_boundaries` | Increasing sequence of floats | Conditional | Exactly one of `elements` / `element_boundaries`; see below |
| `longitudinal.gauss_order` | Integer ≥ 1 | No | `max(cuf orders) + longitudinal.order + 1` at loader stage |
| `longitudinal.material_polynomial_degree` | Integer ≥ 0 | No | `null` / automatic handling |

**Important:** The inspected loader requires a longitudinal partition even when other longitudinal keys use defaults. Omitting *both* `elements` and `element_boundaries`, or specifying *both*, is an error.

Alternative partitions:

```yaml
=======
>>>>>>> 77772d28 (case configuration update)
longitudinal:
  method: finite_element
  elements: 2
  basis: lagrange
  order: 4
  material_polynomial_degree: 0

solver:
  equilibration:
    iterations: [0, 1, 2, 3, 4, 5]

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/custom_problem_sweep
```

The two adapter paths above are examples of allowed reference syntax, **not bundled adapter filenames**.

## 14. Complete key index: case-loader contract

| YAML key | Type | Required? | Default / validation |
|---|---|---|---|
| `case.name` | String | No | Case filename stem |
| `problem.yaml` | Path | Yes | No default |
| `problem.adapter` | Module/path | Alternative A | Exclusive with split adapters |
| `problem.load_adapter` | Module/path | Alternative B, both | Must accompany constraint adapter |
| `problem.constraint_adapter` | Module/path | Alternative B, both | Must accompany load adapter |
| `cuf.basis` | Registered name / file | No (global mode) | `scaled_maclaurin` |
| `cuf.order` | Integer | No (global mode) | `5`, at least 1 |
| `cuf.basis_options` | Mapping | No (global mode) | `{}`; plugin-specific |
| `cuf.segments` | Nonempty list | Alternative to global mode | Each entry requires basis + order |
| `cuf.segments[].basis` | String | Yes in segment | Nonempty |
| `cuf.segments[].order` | Integer | Yes in segment | At least 1 |
| `cuf.segments[].basis_options` | Mapping | No | Plugin-specific |
| `longitudinal.method` | String | No | `finite_element` (runtime-supported) |
| `longitudinal.elements` | Integer | Partition A | At least 1; exclusive with boundaries |
| `longitudinal.element_boundaries` | Sequence | Partition B | Strictly increasing normalized 0..1 |
| `longitudinal.basis` | Registered name / file | No | `lagrange` |
| `longitudinal.order` | Integer | No | `3`, at least 1 |
| `longitudinal.basis_options` | Mapping | No | `{}`; plugin-specific |
| `longitudinal.gauss_order` | Integer | No | CUF order + FE order + 1; at least 1 |
| `longitudinal.material_polynomial_degree` | Integer/null | No | `null`, else at least 0 |
| `section_integration.method` | String | No | `fixed_gauss_polygon` (runtime-supported) |
| `section_integration.gauss_order` | Integer | No | CUF order + 1; at least 2 |
| `solver.equilibration.iterations` | Int or list of ints | No | `3`; every entry >= 0 |
| `sampling.stations` | Nonempty list of numbers | No | `[0.0, 0.5]`; normalized values in [0,1] |
| `sampling.displacement_samples` | Integer | No | `201` |
| `sampling.stress_grid` | Integer | No | `41` |
| `output.adapter` | Module/path | Yes | No default |
| `output.directory` | Path | Yes | No default |

**Scope of the index:** these are the fields inspected by `load_case()`, including the validated segment envelope. It cannot enumerate arbitrary keys allowed by a particular custom expansion plugin, adapter, or downstream segment builder.

## 15. Compatibility and validation examples

| Configuration | Outcome in the inspected loader |
|---|---|
| `cuf.basis: scaled_legendre` with `cuf.order: 8` | Accepted global CUF configuration |
| `cuf.basis: ../expansions/custom.py` with `order: 1` | Accepted path form (file/plugin must exist) |
| `cuf: {}` | Accepted; uses built-in defaults |
| `cuf.segments` without global `basis/order/basis_options` | Parsed as segmented mode; requires downstream segment validation |
| `cuf.segments` **plus** top-level `cuf.order` | Rejected |
| `longitudinal.elements` **plus** `element_boundaries` | Rejected |
| Neither longitudinal partition key | Rejected |
| `problem.adapter` plus `problem.load_adapter` | Rejected |
| Only `problem.load_adapter` | Rejected |
| `solver.equilibration.iterations: 0` | Accepted |
| `solver.equilibration.iterations: [0,2,4]` | Accepted and treated as a sweep |
| `longitudinal.element_boundaries: [0, 0.8, 0.7, 1]` | Rejected; not increasing |
| `sampling.stations: []` | Rejected; empty list |

A case can pass YAML parsing and still fail at model construction or solve time. **A valid declaration is not the same as a validated structural model.** Basis plugins, external adapters, CSF geometry, integration, and physical constraints retain their own validation responsibilities.

## 16. Reading and maintaining this reference

The authoritative places to check when the software changes are:

- [`src/csf/cuf/case.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/case.py) — top-level case keys, exclusive choices and loader defaults.
- The selected transverse expansion plugin — available names, accepted `basis_options`, function count and derivatives.
- The selected longitudinal basis plugin — registered basis names and its specific options.
- The segmented expansion builder — segment intervals, geometric scope and continuity guarantees.
- The selected problem and output adapters — accepted physical problem options and generated results.
- The solver and quadrature implementation — additional runtime constraints and effective integration settings.

Do not turn a single quickstart YAML into an exhaustive schema: the quickstart shows **one valid combination**, whereas this reference records **all generic configuration patterns** and links to implementation-specific documentation where necessary.

## 17. Related resources

- [YAML reference introduction](readme.md)
- [Physical problem YAML](problem_configuration.md)
- [Output settings and result files](output_configuration.md)
- [Executable quickstart cases](../../quickstart/README.md)
