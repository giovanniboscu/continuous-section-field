# CUF Case Configuration - YAML Reference

This document describes the **case YAML** used to configure a CSF-CUF numerical analysis. It is a parameter reference, not a tutorial. For the conceptual introduction, return to [From the Physical Problem to the CUF Model](readme.md). For physical problem files, see [Problem Configuration](problem_configuration.md); for output settings, see [Output Configuration](output_configuration.md).

> **Implementation scope.** The keys, loader defaults and mandatory/exclusive combinations in this reference were checked against the available `load_case()` implementation in `case.py` (source snapshot dated 30 September 2026). Defaults in older prose manuals may differ. Recheck this reference against the current repository before declaring it synchronized with a newer release. Plugin- and adapter-specific parameters are defined by those components, not by the generic case loader.

## 1. Two configuration layers

A case YAML selects the physical problem, the approximation and the output workflow. It does **not** directly replace the CSF geometry YAML or the problem YAML:

```text
case YAML
  |-- problem.yaml ----------> physical problem YAML
  |                               |-- model.csf_yaml --> CSF geometry/material YAML
  |                               `-- problem.type and load settings
  |-- problem adapter(s) ----> loads and constraints
  |-- cuf -------------------> expansion functions
  |-- longitudinal ----------> finite-element approximation
  |-- section_integration ---> section quadrature
  |-- solver ----------------> numerical equilibration
  |-- sampling --------------> result evaluation
  `-- output ----------------> output adapter and location
```

Paths to user files are resolved relative to the **case YAML's own directory**, unless absolute. Importable adapters can be specified by their dotted Python module names.

## 2. Working configuration example

```yaml
case:
  name: torsion_halfwave_xyz_demo

problem:
  yaml: ../problems/torsion_halfwave.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave

cuf:
  basis: ../expansions/xyz_demo_expansion.py
  order: 1

longitudinal:
  method: finite_element
  element_boundaries: [0.00, 1.00]
  basis: lagrange
  order: 6

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6

solver:
  equilibration:
    iterations: 3

sampling:
  stations: [0.00, 0.25, 0.50, 0.75, 1.00]
  displacement_samples: 201
  stress_grid: 31

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/torsion_halfwave_xyz_demo
```

The example deliberately makes principal numerical choices explicit. It assumes the referenced physical problem and expansion file exist at those relative paths. The `xyz_demo` expansion has four explicitly defined functions; its `order: 1` is **not** the total degree or the number of functions.

## 3. Top-level blocks

| Block | Loader requirement | Purpose |
|---|---|---|
| `case` | Optional mapping | Human-readable case identity |
| `problem` | Required mapping | Physical problem file and problem adapter selection |
| `cuf` | Required mapping | Transverse/generalized CUF expansion configuration |
| `longitudinal` | Required mapping | Longitudinal approximation and mesh |
| `section_integration` | Optional mapping | Cross-sectional quadrature |
| `solver` | Optional mapping | Numerical equilibration |
| `sampling` | Optional mapping | Stations and post-processing sample counts |
| `output` | Required mapping | Output adapter and result directory |

**Required** here means required by the inspected loader. Some nested blocks are optional while their parent block is mandatory.

## 4. `case`

```yaml
case:
  name: torsion_halfwave_xyz_demo
```

| Key | Type | Required | Loader default | Meaning |
|---|---|---|---|---|
| `case.name` | String | No | Stem of case YAML filename | Identifier for logs and results |

Prefer names that match the chosen physical problem and current expansion; the name itself does not set solver parameters.

## 5. `problem` - reference to the physical problem

```yaml
problem:
  yaml: ../problems/torsion_halfwave.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave
```

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
cuf:
  basis: scaled_legendre
  order: 8
  basis_options: {}
```

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
longitudinal:
  method: finite_element
  elements: 2
  order: 6
```

```yaml
longitudinal:
  method: finite_element
  element_boundaries: [0.0, 0.35, 1.0]
  order: 6
```

For `element_boundaries`, values are **normalized** coordinates (not physical length units). They must be finite, strictly increasing, contain at least two entries and start at `0.0` and end at `1.0` (endpoint tolerance `1e-12`). The number of elements is one less than the number of boundaries. `elements` creates a partition by element count; `element_boundaries` permits a user-defined nonuniform partition.

`longitudinal.basis` controls the one-dimensional FE shape functions. It is distinct from `cuf.basis`, even if the CUF functions also depend explicitly on `x`. For a Lagrange FE with polynomial order 6, a single element has seven longitudinal interpolation nodes. Consult the selected longitudinal basis plugin for its own `basis_options` and restrictions.

### 7.1 Requested versus effective quadrature

If `longitudinal.gauss_order` is absent, the loader generates a requested starting value from the CUF and longitudinal orders. The integration machinery may choose a **higher effective number of Gauss points** due to basis requirements, geometric variation or a more complicated integrand. Record effective values from the solver diagnostics when publishing numerical results.

`material_polynomial_degree` is an optional explicit hint for material variation along the beam. `0` represents a constant polynomial degree; omission delegates the handling to the implementation. It does not define the material law itself.

## 8. `section_integration`

```yaml
section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6
```

| Key | Type | Required | Loader default / restriction |
|---|---|---|---|
| `section_integration.method` | String | No | `fixed_gauss_polygon` |
| `section_integration.gauss_order` | Integer ≥ 2 | No | `max(cuf orders) + 1` at loader stage |

The numerical integration is performed over cross-sectional polygonal domains supplied by CSF. The selected expansion can impose a higher minimum integration order. The requested YAML value and the effective rule must therefore be distinguished. The available methods depend on the currently installed section-integrator implementation; the loader default alone is not an enumeration of all supported methods.

## 9. `solver`

```yaml
solver:
  equilibration:
    iterations: 3
```

| Key | Type | Required | Loader default |
|---|---|---|---|
| `solver.equilibration.iterations` | Nonnegative integer, or nonempty sequence of nonnegative integers | No | `3` |

A scalar requests one solution, with the specified number of equilibration iterations. `0` requests solving the original KKT system without equilibration. A YAML list requests an equilibration sweep. The loader normalizes a list by removing duplicates and sorting values increasingly; for example `[4, 0, 2, 4]` becomes `(0, 2, 4)`.

This is a numerical control, not a physical model parameter. Interpret solver conditioning and equilibration outcomes alongside equilibrium residuals and convergence; do not reject a solution solely because one conditioning indicator is large.

## 10. `sampling`

```yaml
sampling:
  stations: [0.00, 0.25, 0.50, 0.75, 1.00]
  displacement_samples: 201
  stress_grid: 31
```

| Key | Type | Required | Loader default / restriction |
|---|---|---|---|
| `sampling.stations` | Nonempty sequence of normalized numbers | No | `[0.0, 0.5]`; each in `[0,1]` |
| `sampling.displacement_samples` | Integer | No | `201` |
| `sampling.stress_grid` | Integer | No | `41` |

These values control how the already solved continuous field is queried or displayed. They are **not** the finite-element mesh and do not change the number of solved CUF unknowns. Other runtime restrictions on sampling counts may be enforced downstream; the inspected loader casts them to integers but does not perform a detailed range check.

For generated files and post-processing semantics, see [Output Configuration](output_configuration.md).

## 11. `output` (summary)

```yaml
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/torsion_halfwave_xyz_demo
```

| Key | Type | Required | Meaning |
|---|---|---|---|
| `output.adapter` | Dotted Python module or `.py` path | Yes | Implementation of post-processing/export |
| `output.directory` | Path | Yes | Location for case results, relative to the case YAML if not absolute |

See [Output Configuration](output_configuration.md) for details. The output adapter determines which concrete files are written; the case loader does not promise a universal list of artifacts.

## 12. Configuration verification checklist

1. The paths in `problem.yaml`, `cuf.basis` (for an external file) and `output.directory` are evaluated relative to the case YAML.
2. Exactly one problem-adapter pattern is selected: combined, or complete split load/constraint pair.
3. Exactly one longitudinal partition style is provided: `elements` **or** `element_boundaries`.
4. `cuf.segments` is not mixed with standard top-level CUF basis/order/options fields.
5. The selected expansion plugin supports its requested `order` and `basis_options`.
6. The physical model is valid and all requested points are inside the CSF geometry at their longitudinal positions.
7. Adapter evaluation passes the actual physical coordinates to three-coordinate expansions.
8. Quadrature is checked using **effective** numerical diagnostics, not only YAML requests.
9. Sampling settings are not mistaken for degrees of freedom or FE interpolation points.
10. The output adapter and output destination correspond to the desired workflow.

## 13. Related documentation

- [YAML reference introduction](readme.md)
- [Physical problem YAML](problem_configuration.md)
- [Outputs and post-processing](output_configuration.md)
- [Executable quickstart cases](../../quickstart/README.md)
