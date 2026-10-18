# Custom polygon-based Lagrange L9 transverse expansion

**Source:** [`lagrangeL9_v4.py`](lagrangeL9_v4.py)  
**Example case:** [`../cases/c_section_table_9_13_lagrangeL9_E10.yaml`](../cases/c_section_table_9_13_lagrangeL9_E10.yaml)

## 1. Purpose and architectural idea

This module demonstrates how to implement a **custom transverse expansion as an external Python plugin** in CSF–CUF. It constructs a quadratic, nine-point Lagrange (L9) interpolation **on each CSF cross-sectional polygon** and assembles the local interpolation points into a continuous transverse basis. The example is applied to the nine-polygon C-section from the Carrera–Petrolo benchmark, *Refined beam elements with only displacement variables and plate/shell capabilities*.

The architectural separation is central:

- **CSF owns the cross-sectional geometry:** the polygon set and its evolution along the beam axis.
- **The expansion module owns the mathematical transverse approximation:** local interpolation, natural-to-physical mappings, local/global point connectivity, basis values and gradients.
- **The CUF core consumes the resulting basis:** it performs longitudinal discretization, integration, assembly, solution and post-processing.

The same plugin interface offers a route to other custom bases and polygon-dependent interpolation rules. **This particular module assigns an L9 interpolation to every supported quadrilateral**; it does not currently select different interpolation families independently for different polygons.

```text
case YAML
  | cuf.basis = ../expansions/lagrangeL9_v4.py
  v
plugin loader / registry
  | register_cuf_basis_plugin(CUFBasisPlugin(...))
  | builder(order, section_provider, continuous_section_field, options)
  v
LagrangeL9Basis (CUFBasis)
  | obtains x range: section_provider.longitudinal_domain()
  | obtains sections: section_provider.domains(x)
  | builds local L9 points + shared global tau indices
  | provides value, transverse derivative and longitudinal derivative
  v
CUF integration / assembly / solution
  |
  +--> optional mathematical export --> generic checkpoint compilation
```

## 2. Select the external expansion in YAML

The case file connects the solver to the Python module by path:

```yaml
cuf:
  basis: ../expansions/lagrangeL9_v4.py
  order: 2
  basis_options:
    domain_source: csf_polygons
    mapping: isoparametric
    connectivity: shared_points
    boundary_tolerance: 1.0e-10
    require_prismatic: true
```

The path is relative to the **case YAML**, not the working directory. `order: 2` means a quadratic Lagrange interpolation with **nine local nodes** per quadrilateral. It is not a request for nine longitudinal elements. The example defines longitudinal finite elements separately under `longitudinal`.

| Option | Effect in this implementation |
| --- | --- |
| `domain_source: csf_polygons` | Read cross-sectional domains through the CSF section provider. |
| `mapping: isoparametric` | Map the natural L9 square to each current physical quadrilateral. |
| `connectivity: shared_points` | Merge matching local L9 points into shared global transverse indices. |
| `boundary_tolerance` | Positive finite tolerance for point sharing and boundary classification; initialization scales merging tolerance by coordinate magnitude. |
| `require_prismatic` | Legacy accepted field, recorded but **not enforced**; variable sections are supported. |

Unknown options raise an error in `_parse_options()`. The first three options currently accept only the values shown.

The complete numerical example can be run from `cuf/c-shape`:

```bash
csf-cuf cases/c_section_table_9_13_lagrangeL9_E10.yaml
```

The case also references `../problems/c_section_cantilever_point_9L9.yaml`, its problem adapter, a longitudinal FE configuration, section integration and output settings. Those remain independent of the expansion's Python source.

## 3. Plugin registration: the first extension hook

At module import time the following registration connects this file to the CUF plugin mechanism:

```python
register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="lagrangeL9",
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=_longitudinal_transverse_degree,
    )
)
```

| Hook | Called for | Implementation |
| --- | --- | --- |
| `name` | Registry identity | `lagrangeL9` |
| `builder` | Create the transverse basis | `_build(...)` validates `order`, parses options, returns `LagrangeL9Basis`. |
| `section_gauss_minimum` | Transverse integration guidance | Returns `3` for a compatible L9 basis. |
| `longitudinal_transverse_degree` | Longitudinal quadrature degree estimate | Returns `0`, deliberately not assuming a polynomial dependence on `x` for moving geometry. |

The actual factory signature is:

```python
def _build(*, order, section_provider, continuous_section_field, options):
    ...
```

`section_provider` is the geometry interface actually used. The `continuous_section_field` argument is accepted but discarded by this builder. `options` comes from `cuf.basis_options`. The returned object is an instance of the `CUFBasis` subclass `LagrangeL9Basis`.

**Where to customize:** To implement another transverse expansion, provide your own `CUFBasis` implementation, a compatible builder, and registration metadata. Reuse the provider API to obtain geometry independently of how it is stored.

## 4. CSF geometry interface: the second extension hook

The expansion depends on two calls to `section_provider`:

```python
x0, x1 = section_provider.longitudinal_domain()
raw_domains = tuple(section_provider.domains(float(x)))
```

The first supplies the longitudinal interval. The second obtains a **snapshot of the cross-section at the requested `x`**. Each returned domain is read using these attributes:

| CSF domain attribute | Use |
| --- | --- |
| `domain_id` | Stable, one-based polygon identity and local-to-global connectivity lookup. |
| `name` | Optional readable name carried to diagnostics. |
| `vertices` | Four `(y, z)` corner coordinates for the current quadrilateral. |
| `excluded_vertices` | Checked; nonempty excluded/nested regions are rejected by this implementation. |

The module requires finite nonzero-area four-vertex polygons, stable ordered IDs `1..N`, and a consistent polygon count along `x`. It checks that local points tied together at the initial station remain coincident as the geometry evolves. The polygon geometry is obtained **from the provider at each queried station**, rather than reconstructed by reading the CSF YAML in the expansion.

### Topology stays fixed; geometry can move

During construction, the plugin reads the initial section at `x0` and creates the permanent transverse connectivity graph. Subsequent evaluation retrieves current geometry through `_domains_at_x(x)` (cached for up to 64 longitudinal stations). This gives the CUF system stable generalized transverse indices even when section dimensions vary.

A constant-geometry test evaluates additional longitudinal stations. It governs derivative and export behavior; `require_prismatic` does not force a constant section.

## 5. Local L9 mathematical basis

Every CSF quadrilateral is associated with a natural square `(alpha, beta)` in `[-1,1] x [-1,1]`. Local numbering follows:

```text
    7 -------- 6 -------- 5
    |                     |
    8          9          4
    |                     |
    1 -------- 2 -------- 3

    alpha increases rightward; beta increases upward
```

The nine functions are tensor products of one-dimensional quadratic Lagrange functions:

```text
L_-(q) = q(q - 1)/2
L_0(q) = 1 - q^2
L_+(q) = q(q + 1)/2

N_i(alpha,beta) = L_{a_i}(alpha) * L_{b_i}(beta)
```

Their natural derivatives are computed analytically in `_l9_shape_natural_derivatives()`. For each polygon, a four-corner bilinear map transforms natural coordinates into physical `(y,z)` coordinates:

```text
(y,z)(alpha,beta;x) = sum_{a=1}^4 Q_a(alpha,beta) * vertex_a(x)
```

The inverse map is computed numerically for a requested physical point. The Jacobian `J = d(y,z)/d(alpha,beta)` transforms the natural gradient to the physical gradient:

```text
[ dN/dy ]         [ dN/dalpha ]
[       ] = J^-T  [            ]
[ dN/dz ]         [ dN/dbeta  ]
```

This distinction matters: **the L9 basis uses nine interpolation nodes, while the geometric mapping uses the four polygon corners**. The implementation supports bilinearly mapped quadrilaterals for runtime evaluation.

## 6. Assembling local polynomial functions into a global basis

`_build_l9_topology()` constructs nine local points per polygon, maps them at `x0`, and merges coincident positions within the configured tolerance. Its outputs are:

- `_local_points`: nine physical L9 points for each domain at the initial section;
- `_connectivity`: for each polygon, a tuple of nine **one-based global `tau` indices**;
- `_global_points`: each global index, initial coordinate and list of `(domain_id, local_node)` occurrences.

A local corner or edge point shared by adjacent polygons therefore belongs to one global transverse degree of freedom. The `size` property is the number of assembled global transverse functions; `local_point_count` is `9 * domain_count` before sharing. The global functions have piecewise polygon support.

**Example of the concept (illustrative indices):** If the right-middle node of polygon 1 coincides with the left-middle node of polygon 2, both local connectivity tuples contain the same global `tau`. Its `occurrences` records both `(1, 4)` and `(2, 8)`.

The geometrical tie is checked again when the provider returns a section at a different longitudinal station.

## 7. Basis API consumed by CUF: the third extension hook

The principal runtime methods and properties are:

| Member | Role |
| --- | --- |
| `order`, `size` | Quadratic order and assembled global basis dimension. |
| `definition(tau)` | Describes a global transverse function and its occurrences. |
| `value(tau, y, z, *, x=None)` | Evaluates one assembled global function at a physical point. |
| `derivative(tau, direction, y, z, *, x=None)` | Evaluates the physical derivative in `y` or `z`. |
| `provides_longitudinal_derivative` | Signals when moving geometry requires an explicit `x` derivative contribution. |
| `longitudinal_derivative(tau, y, z, *, x=None)` | Evaluates `dF_tau/dx` at fixed physical `(y,z)`. |
| `options` | Exposes parsed configuration values. |

### Point location and interfaces

`locate_domains(y,z,x=x)` returns all containing domain IDs. The inclusive boundary test means a point on a shared edge can belong to multiple polygons. `locate_unique_domain(...)` requires a single matching domain, and `natural_coordinates(...)` obtains coordinates in a selected polygon.

`value()` evaluates all contributing element-side descriptions on an interface and checks their consistency; it **does not add together duplicate interface values**. Outside the section it returns zero. For `derivative()` and `longitudinal_derivative()`, an exact shared interface can have different element-side gradients for a C0 interpolation. These methods therefore reject ambiguous interface points, while interior points are evaluated within their unique domain.

For a variable section, `x` is required: it selects the CSF geometry used to interpret the physical coordinates. For constant geometry, an omitted `x` defaults to `x0`.

### Longitudinal derivative for moving geometry

At a fixed physical point, natural coordinates vary as the section deforms longitudinally. The implementation applies the chain rule:

```text
dN/dx |_(y,z) = [dN/dalpha, dN/dbeta] * d(alpha,beta)/dx

d(alpha,beta)/dx = -J^-1 * d(y,z)/dx |_(alpha,beta)
```

The geometric velocity in this expression is determined from **finite differences of the CSF provider's queried geometry**, using a centered interval in the interior and a one-sided interval near the longitudinal endpoints. The chain-rule evaluation is analytical once that velocity is obtained. For constant geometry, the derivative is zero and `provides_longitudinal_derivative` is false.

This hook is especially important for non-prismatic sections: transverse basis functions can vary with `x` even though their global `tau` numbering is unchanged.

## 8. Integration hooks and numerical checks

`_section_gauss_minimum()` returns `3`, matching one-dimensional integration of quartic products for straight L9 domains. The configured C-section case explicitly requests **section Gauss order 9** and **longitudinal Gauss order 15**; those case settings are separate from the plugin guidance. `_longitudinal_transverse_degree()` returns `0` because general moving isoparametric geometry does not yield a simple polynomial law in `x`; longitudinal integration accuracy should be checked by quadrature convergence.

For inspection and validation, the expansion provides:

| Method | What it reports |
| --- | --- |
| `topology_summary()` | Domain count, local/global point counts, shared points and connectivity. |
| `diagnostic_rows()` | Per-polygon vertices, bounds, local points and global `tau` mapping. |
| `interpolation_checks()` | Maximum Kronecker interpolation error, partition-of-unity error and natural derivative-sum error. |
| `local_shape_values(alpha,beta)` | Nine local L9 values in reference coordinates. |
| `global_points`, `connectivity`, `domains` | Structured read-only topology accessors. |

A useful conceptual test sequence is: inspect the CSF domains; verify 9 local points for each polygon; inspect merged global connectivity; verify Kronecker and partition-of-unity checks; test values and gradients at polygon interiors; repeat at several `x` stations for a variable section.

## 9. Mathematical export and checkpoint hand-off: the fourth extension hook

The expansion also provides **representation hooks** for exporting its mathematical basis in a form suitable for generic solved-field compilation. This is distinct from runtime calls to `value()` and `derivative()`.

### Static physical-coordinate power representation

For a constant section built from suitably ordered axis-aligned rectangles, `piecewise_power_representation()` exposes:

```python
{
    "kind": "transverse_domain_y_z_power",
    "domain_vertices": ...,  # shape (domains, 4, 2)
    "coefficients": ...,     # shape (domains, global_tau, 3, 3)
}
```

Each domain contains coefficients for `F_tau(y,z) = sum C[p,q] y^p z^q`; coefficients for inactive global functions are zero. The physical polynomial exporter specifically requires axis-aligned, correctly ordered rectangular domains. That is an **export-specific condition**; the runtime evaluator works with more general quadrilaterals.

### Compiled representation

`compiled_transverse_representation()` selects an export law:

- **`domain_y_z_power`** for the constant, ordered rectangular case, carrying polygon vertices and polynomial coefficients;
- **`domain_natural_power_affine_x`** when the CSF polygon vertex trajectories satisfy an affine-in-`x` contract, carrying `x_bounds`, two endpoint vertex sets and natural-coordinate polynomial coefficients;
- `None` if the checked affine trajectory contract cannot be established for that provider.

For the affine form, the exporter checks provider snapshots at intermediate stations against endpoint interpolation. Its coefficients describe polynomial L9 functions in **natural** coordinates, while the endpoint vertex arrays describe longitudinal geometry movement. The generic checkpoint compiler can combine the exported basis representation with solved coefficients to construct an independent field representation.

These exports illustrate an additional extension seam: a custom basis can supply an exact, portable mathematical description while leaving solved-field compilation to the framework.

## 10. Where to adapt the module for a new expansion

A useful development map is:

| Desired modification | Relevant hook or code area |
| --- | --- |
| Read another CSF polygon configuration | `_read_domains()`, `section_provider.domains(x)` and domain validation. |
| Change natural interpolation functions | `_L9_NATURAL_POINTS`, `_quadratic_lagrange_1d()`, `_l9_shape()`, `_l9_shape_natural_derivatives()`. |
| Use alternative physical mapping | `_corner_shape_data()`, `_map_reference_to_physical()`, `_mapping_jacobian()`, `_inverse_isoparametric_map()`. |
| Change sharing between polygon functions | `_build_l9_topology()`, `_find_existing_global_point()` and global `tau` occurrences. |
| Customize per-polygon interpolation family/order | Introduce per-domain basis metadata, variable-length local connectivity and corresponding value/derivative dispatch; adapt global sharing and exports consistently. |
| Account for a moving cross-section | `_domains_at_x()`, `provides_longitudinal_derivative`, `longitudinal_derivative()`. |
| Control integration guidance | `_section_gauss_minimum()`, `_longitudinal_transverse_degree()`. |
| Support checkpoint reconstruction | `piecewise_power_representation()` and `compiled_transverse_representation()`. |
| Add a new external plugin | `_build()` and `register_cuf_basis_plugin(CUFBasisPlugin(...))`. |

When defining **different expansion types for different polygons**, the principal architectural task is to maintain a consistent **global transverse approximation space and connectivity** across shared polygon interfaces. Local orders or function families may vary, so the current fixed nine-entry `connectivity` and shared-node merging logic would need corresponding generalization. The CSF provider can continue to supply the polygons and their evolving geometries through the same interface.

## 11. Reading guide: source entry points

Read the implementation in this order:

1. `_parse_options()` → `_build()` → `register_cuf_basis_plugin(...)`: configuration and plugin lifecycle.
2. `LagrangeL9Basis.__init__()` → `_read_domains()` → `_build_l9_topology()`: CSF dependency and transverse topology construction.
3. `_quadratic_lagrange_1d()` → `_l9_shape()` → `_corner_shape_data()`: interpolation and geometry mapping.
4. `value()` → `derivative()` → `longitudinal_derivative()`: runtime interface and moving-section mechanics.
5. `topology_summary()` → `interpolation_checks()`: diagnostics.
6. `piecewise_power_representation()` → `compiled_transverse_representation()`: mathematical exports and post-solution hand-off.

## 12. Related files

- [`lagrangeL9_v4.py`](lagrangeL9_v4.py) — implementation documented here.
- [`../cases/c_section_table_9_13_lagrangeL9_E10.yaml`](../cases/c_section_table_9_13_lagrangeL9_E10.yaml) — example selection of the external Python expansion.
- [`../readme.md`](../readme.md) — C-section benchmark context.
- [`../reproducibility.md`](../reproducibility.md) — full CSF–CUF / FEM3D reproduction and comparison workflow.
- [`../../I-Shape/reproducibility.md`](../../I-Shape/reproducibility.md) — related I-section reproduction example.

**Source note:** This explanation follows the `lagrangeL9_v4.py` source on the repository's `main` branch as inspected on 18 October 2026. The example YAML still contains an introductory comment referring to an earlier development version; its executable configuration points to `lagrangeL9_v4.py`.
