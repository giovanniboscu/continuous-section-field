# Physical Problem Configuration — YAML Reference

A **problem YAML** defines the structural problem to be solved by CSF-CUF. It names an existing CSF model and provides the load or boundary-condition data expected by a chosen problem adapter. It is separate from the **case YAML**, which selects the CUF expansion, longitudinal finite elements, numerical integration and output settings.

For navigation, return to the [YAML reference introduction](readme.md), consult [Case Configuration](case_configuration.md) for the invoking case, or see [Output Configuration](output_configuration.md) for result export.

> **Scope and version.** The general two-block pattern and the examples below are based on the available CSF-CUF user manual and the inspected `surface_halfwave_paper2010.py` adapter implementation. Problem-body options are **adapter-specific**, so the examples must not be interpreted as a universal schema or a complete inventory of every adapter in the current GitHub branch. Validate the declared `problem.type` and its keys against the adapter actually selected in the case YAML.

## 1. Separation of concerns

```text
CSF geometry/material YAML             Physical problem YAML
  geometry and polygons                  model.csf_yaml -> CSF YAML
  section stations and interpolation     problem.type
  material and participation laws        loads, surfaces and physical settings
             \                                  /
              \                                /
               +----------- case YAML --------+
                              |
                   problem adapter(s)
                              |
                          CUF solver
```

The geometry and materials are defined by **CSF**. The physical loading and boundary-condition convention is interpreted by a **problem adapter**. Neither of these should be embedded inside the mathematical definition of an expansion family.

## 2. General problem-file layout

```yaml
model:
  csf_yaml: ../models/rectangular_prismatic_csf.yaml

problem:
  type: torsion_halfwave
  amplitude: 10.0
```

### General envelope

| Key | Type | Meaning | Status |
|---|---|---|---|
| `model.csf_yaml` | File path | Path to the CSF geometry/material model | Used by the documented CSF-CUF problem-file convention |
| `problem.type` | String | Identifies the physical problem understood by the selected adapter | Required by the documented predefined adapters |
| Additional `problem.*` keys | Adapter-defined | Load intensities, components, surface selectors and other problem data | Vary by adapter |

The path in `model.csf_yaml` is resolved in the context of the problem-file loading workflow; when editing files, verify path resolution in the installed loader and keep the path relative to the problem YAML as shown in the examples.

The case file points to this problem file and separately selects its adapter:

```yaml
problem:
  yaml: ../problems/torsion_halfwave.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave
```

The `problem.yaml` field above belongs to the **case configuration**; it is not a nested field of the physical problem file.

## 3. Documented predefined problem forms

The following forms illustrate adapter-specific variants. They are not mutually interchangeable: the `problem.type` and selected adapter must agree.

### 3.1 Sinusoidal transverse traction on a physical surface

```yaml
model:
  csf_yaml: ../models/model.yaml

problem:
  type: surface_halfwave
  surface:
    polygon_name: web
    edge_start_point_id: 0
  amplitude: -10.0
```

Case selection:

```yaml
problem:
  yaml: ../problems/bending.yaml
  adapter: csf.cuf.adapters.problem.surface_halfwave
```

The documented load varies along the beam as

$$
p(x) = A\sin\left(\pi\frac{x-x_0}{L}\right), \qquad L=x_1-x_0.
$$

The signed scalar `amplitude` sets the load magnitude/direction according to the selected adapter. The physical surface is selected by the polygon name and the start-vertex index of a polygon edge. The successor vertex closes the selected edge, including the final-to-first edge.

The documented surface-halfwave variant restricts the selected edge to a section edge that is horizontal in the relevant transverse direction at both end sections. The real inclined physical surface measure must be used by the adapter for non-prismatic geometry; it must not silently replace a surface traction with a projected-area load.

| Key | Type | Meaning |
|---|---|---|
| `problem.surface.polygon_name` | Nonempty string | User-facing polygon name in the CSF model |
| `problem.surface.edge_start_point_id` | Nonnegative integer | Zero-based start vertex of the selected physical edge |
| `problem.amplitude` | Finite number | Signed amplitude for this adapter's prescribed half-wave |

### 3.2 Uniform physical-surface traction

```yaml
model:
  csf_yaml: ../models/model.yaml

problem:
  type: uniform_surface_load
  surface:
    polygon_name: web
    edge_start_point_id: 0
  components:
    z: -1.0
```

Case selection:

```yaml
problem:
  yaml: ../problems/uniform_surface.yaml
  adapter: csf.cuf.adapters.problem.uniform_surface
```

The documented variant uses a signed physical traction component in the CUF `z` direction. The magnitude is force per unit actual loaded surface area in the model's consistent units. Do not assume that every available uniform-surface adapter accepts arbitrary `x`, `y` and `z` component combinations; consult the selected implementation.

### 3.3 Half-wave torsion loading

```yaml
model:
  csf_yaml: ../models/model.yaml

problem:
  type: torsion_halfwave
  amplitude: 10.0
```

Case selection:

```yaml
problem:
  yaml: ../problems/torsion_halfwave.yaml
  adapter: csf.cuf.adapters.problem.torsion_halfwave
```

The documented predefined adapter selects two physical CSF vertices and applies opposite signed distributed line loads with longitudinal half-wave variation, producing a torsional action. The two load points follow the section geometry along the member. The exact vertex-selection and constraint convention is defined by the adapter; it is **not** configured through a universal problem-file `boundary_conditions` structure.

### 3.4 Uniform torsion loading

```yaml
model:
  csf_yaml: ../models/model.yaml

problem:
  type: torsion_uniform
  amplitude: 1.0
```

Case selection:

```yaml
problem:
  yaml: ../problems/torsion_uniform.yaml
  adapter: csf.cuf.adapters.problem.torsion_uniform
```

The documented uniform variant uses constant signed line-load intensities. For a changing cross-section, the lever arm between application points may vary, so the local torque need not remain constant merely because the line-load intensities are constant.

## 4. Selecting physical geometric entities

For a polygon edge, the following selector pattern is documented:

```yaml
surface:
  polygon_name: web
  edge_start_point_id: 0
```

`polygon_name` refers to the identity supplied by CSF. `edge_start_point_id` is a vertex index **within that polygon**, not a global nodal degree-of-freedom number. Polygons and their homologous vertices must be consistent as the section varies longitudinally.

This selector is not a prescription for all possible point or surface loads. An adapter may expose another geometry-selection mechanism; its configuration must be documented alongside its implementation.

## 5. Coordinates and expansion evaluation

The CUF solver uses:

- `x`: longitudinal beam coordinate;
- `y`: first cross-sectional coordinate;
- `z`: second cross-sectional coordinate.

CSF's geometric convention uses longitudinal `Z` and transverse `X,Y`. The established mapping is

$$
(x,y,z)_{\mathrm{CUF}} = (Z,X,Y)_{\mathrm{CSF}}.
$$

**Adapters must evaluate the expansion at the actual physical coordinates relevant to the load, constraint or result.** For example, the basic value call is:

```python
value = basis.value(tau, y, z, x=x)
```

A generalized expansion may depend on `x` explicitly or through the changing CSF geometry. If an adapter computes a longitudinal or surface integral of expansion values, it must use the values at the actual quadrature points, retaining such dependence inside the integral. Supplying a single unrelated reference coordinate is not a general substitute.

This contract applies independently of whether the selected expansion is Legendre, Lagrange, Maclaurin or a custom three-dimensional function.

## 6. Boundary conditions

There is **no universal list of physical support conditions encoded by the generic problem-YAML envelope shown here**. The documented predefined adapters implement the support/constraint scheme associated with their problem family. For example, half-wave validation configurations may constrain transverse generalized amplitudes at the beam ends and eliminate the remaining axial rigid-body mode.

To use a different support scheme, select an adapter that implements it or provide a suitable custom constraint adapter. The case YAML allows either a combined `problem.adapter` or the pair `problem.load_adapter` and `problem.constraint_adapter` (see [Case Configuration](case_configuration.md)).

An adapter must build constraints from the **physical condition being imposed**, without assuming that expansion functions are necessarily independent of the longitudinal coordinate. Continuity across polygon interfaces is conceptually distinct from external boundary conditions and is handled through the chosen approximation and its coupling strategy.

## 7. Materials and geometry remain in CSF

The file at `model.csf_yaml` is responsible for the continuous description of geometry and material-related fields. Do not duplicate the CSF geometry inside the problem YAML just to make a custom load or an expansion work. At an integration point, the adapter or expansion can query the CSF-supplied geometry through the supported interfaces.

A CSF model may include sections, polygons and longitudinally varying properties. The set of permitted CSF YAML keys is a **separate specification** from the CUF case YAML and the physical problem YAML.

Likewise, the standalone CSF `actions.yaml` pipeline for geometric/property inspection is not a substitute for the CUF structural problem file.

## 8. Validating a problem YAML

Before a numerical run, verify:

1. The referenced CSF model exists, loads successfully and has the intended polygon topology, units and geometry.
2. The case selects a problem adapter supporting the declared `problem.type`.
3. Every adapter-required key is present and types are correct (for example, finite `amplitude`).
4. Every polygon or edge selector resolves to a real physical entity and remains valid along the relevant longitudinal domain.
5. Load components and signs are expressed in the documented CUF coordinate convention.
6. Surface/line/point load units and measures are compatible with the adapter's mechanical interpretation.
7. Constraints suppress the intended rigid modes without imposing additional unintended displacement restrictions.
8. Every expansion evaluation is performed at its actual `(x,y,z)` coordinates, including within integrations.

## 9. Related documentation

- [YAML reference introduction](readme.md)
- [Case configuration](case_configuration.md)
- [Output configuration](output_configuration.md)
- [Executable quickstart examples](../../quickstart/README.md)
