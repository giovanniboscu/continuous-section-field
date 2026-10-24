# CUF case YAML - comprehensive configuration guide

This guide explains the CUF case YAML configuration used by Continuous Section Field (CSF). It describes the purpose, syntax and numerical implications of each setting and provides an annotated starting template for bridge-like analyses.

> **Configuration note.** Some settings are specific to particular basis implementations, problem adapters or analysis runners. Additional options are commented out in the template; enable them only when supported by the selected components.

## 1. What a case file controls

A case YAML configures **how to solve and report a physical problem**, without necessarily defining that problem itself. `problem.yaml` points to a separate problem description (CSF section geometry, materials, load definitions, and boundary conditions), while the problem adapter translates that description to the solver. A case selects the transverse CUF expansion, axial approximation, numerical quadrature, stabilization/solver controls, postprocessing sampling and output location. The same physical problem can be rerun with different approximations to study convergence.

For a conventional separable expansion, the displacement approximation is conceptually

$$\mathbf u(x,y,z)=\sum_i\sum_\tau N_i(x)F_\tau(x,y,z)\mathbf q_{i\tau}.$$

The `x` dependence of `F_tau` is allowed for appropriate plugins, but it is **not** a substitute for the axial finite element functions `N_i`. When an expansion depends on `x`, the adapter must use actual physical coordinates and supply consistent spatial derivatives.

## 2. Complete annotated bridge-like case template

This annotated bending example shows a practical baseline. Optional alternatives are kept as comments so that they can be enabled deliberately after confirming compatibility with the selected basis and adapters.

```yaml
case:
  name: carrera_bridge_bending_scaled_lagrange_N15  # Analysis identifier, not physics

problem:
  yaml: ../problems/bending.yaml                   # Separate physical problem definition
  adapter: ../adapters/bending.py                 # Loads/BC integration adapter
  # Alternative adapter notation:
  # adapter: csf.cuf.adapters.problem.torsion_halfwave

cuf:
  basis: scaled_lagrange                        # Transverse expansion family
  order: 15                                     # Expansion-specific order parameter
  # Other transverse expansion families:
  # basis: scaled_legendre
  # basis: scaled_maclaurin
  # Expansion plugin example (path relative to the case):
  # basis: ../expansions/lagrangeL9_v4.py
  # basis: ../expansions/xyz_demo_expansion.py
  # basis_options:                             # Options for compatible custom basis plugins
  #   domain_source: csf_polygons
  #   mapping: isoparametric
  #   connectivity: shared_points
  #   boundary_tolerance: 1.0e-10
  #   require_prismatic: true                   # Reject variable-section geometry when required

longitudinal:
  method: finite_element                       # Observed axial discretization
  element_boundaries: [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
  basis: lagrange                              # Longitudinal interpolation family
  order: 6                                     # Polynomial degree per axial element
  # Alternative axial-mesh representation (use instead of boundaries):
  # elements: 10                               # Number of axial elements
  # gauss_order: 15                             # Axial numerical quadrature control
  # material_polynomial_degree: 0              # Optional material integration hint

section_integration:
  method: fixed_gauss_polygon                  # Cross-sectional polygon integration
  gauss_order: 8                               # Requested section Gauss order

solver:
  correctionMITC: true                        # MITC-type correction switch
  verifyMITCAssembly: true                    # Assembly diagnostic/verification switch
  equilibration:
    iterations: [1, 2, 3, 4, 5]               # Iteration counts used in bridge cases
    # iterations: 5                            # Single requested iteration count

sampling:
  stations: [0.0, 0.25, 0.5, 0.75, 1.0]        # Normalized axial report stations
  displacement_samples: 201                   # Axial displacement sampling resolution
  stress_grid: 51                             # Section stress sampling resolution

output:
  adapter: csf.cuf.adapters.output.post        # Output/postprocessing plugin
  directory: ../output/bending_scaled_lagrange_N15
```

> `element_boundaries` and `elements` occur as alternatives in the sampled files. Do **not** assume both can be supplied simultaneously or that one silently overrides the other. Similarly, the scalar and list forms of `solver.equilibration.iterations` should be interpreted according to the runner in use; a list may request a sweep rather than a single solve.

## 3. Exhaustive CUF case-key reference

### 3.1 `case`

**`case.name`** - *string*. Human-readable/unique analysis identifier. Used to distinguish runs and artifacts; does not itself choose physics or expansion.

### 3.2 `problem`

**`problem.yaml`** - *relative path string*. External physical problem description. It can define geometry through CSF, material variation, loads and supports. It is not an embedded subtree of the case YAML.

**`problem.adapter`** - *module dotted path or Python path*. Problem-specific Python bridge mapping the physical problem into CUF actions: boundary constraints and surface/line load construction. Ensure matching load conventions and coordinate dependencies.

### 3.3 `cuf`

**`cuf.basis`** - *builtin family name or Python file path*. Selects transverse approximation F_tau. Available examples: scaled_lagrange, scaled_legendre, scaled_maclaurin; custom Python expansion files may also be used.

**`cuf.order`** - *integer*. Expansion family/plugin parameter. Polynomial order should not universally be equated with the number of expansion functions: a custom plugin explicitly defines four functions even with order 1.

**`cuf.basis_options.domain_source`** - *string*. Value `csf_polygons`: source of cross-section domains for a custom expansion/mesh.

**`cuf.basis_options.mapping`** - *string*. Value `isoparametric`: geometric mapping convention in custom transverse finite-element-style expansions.

**`cuf.basis_options.connectivity`** - *string*. Value `shared_points`: matches/commonizes coincident points across transverse subdomains in the custom expansion.

**`cuf.basis_options.boundary_tolerance`** - *floating-point*. Tolerance for geometric boundary/point matching in the custom expansion. Geometry-unit and scaling sensitivity should be tested.

**`cuf.basis_options.require_prismatic`** - *boolean*. Optional restriction; asks the custom basis path to require a prismatic section. Do not enable on a tapered bridge without inspecting plugin behavior.

### 3.4 `longitudinal`

**`longitudinal.method`** - *string*. Selects axial approximation strategy; use `finite_element` for standard axial finite-element discretization.

**`longitudinal.elements`** - *positive integer*. Specifies count of axial finite elements where explicit element boundaries are absent. Useful for a compact mesh specification.

**`longitudinal.element_boundaries`** - *ascending list of normalized coordinates*. Explicit axial element interfaces, e.g. 0, 0.1, …, 1.0 for ten elements. These define discretization, unlike sampling stations.

**`longitudinal.basis`** - *string*. Longitudinal interpolation family, observed lagrange. Distinct from the transverse CUF basis.

**`longitudinal.order`** - *positive integer*. Longitudinal element polynomial degree; for standard Lagrange elements degree p means p+1 local interpolation nodes, subject to implementation.

**`longitudinal.gauss_order`** - *positive integer*. Requested axial integration order; used in MITC cases with high-order quadrature.

**`longitudinal.material_polynomial_degree`** - *nonnegative integer*. Material variation/integration metadata. A value 0 indicates constant polynomial degree approximation for the material term as used in MITC benchmark examples; exact internal integration behavior must be confirmed.

### 3.5 `section_integration`

**`section_integration.method`** - *string*. Quadrature scheme for sectional integrals; a supported method is `fixed_gauss_polygon`, acting on CSF polygonal subdomains.

**`section_integration.gauss_order`** - *positive integer*. Nominal Gauss quadrature order per polygonal region; some adapters/plugins may raise effective order as required.

### 3.6 `solver`

**`solver.correctionMITC`** - *boolean*. Enables/disables MITC-related correction used in shear-locking benchmarks. Impacts numerical formulation, not the physical boundary-value problem.

**`solver.verifyMITCAssembly`** - *boolean*. Enables verification/diagnostic path for MITC-related assembly where supported; can entail additional checking.

**`solver.equilibration.iterations`** - *positive integer or list of positive integers*. Matrix equilibration iteration setting; a list such as `[1, 2, 3, 4, 5]` or a single integer can be specified according to runner semantics. List semantics depend on the runner (possibly repeated variants).

### 3.7 `sampling`

**`sampling.stations`** - *list of normalized axial positions*. Discrete longitudinal section positions reported during postprocessing; does not create FEM nodes or control stiffness integration.

**`sampling.displacement_samples`** - *positive integer*. Resolution of sampling of reconstructed continuous displacement along the beam. Increasing it changes visual/report detail, not solution DOFs.

**`sampling.stress_grid`** - *positive integer*. Resolution parameter for cross-sectional stress evaluations/plots; does not set section quadrature order.

### 3.8 `output`

**`output.adapter`** - *dotted module path or Python path*. Postprocessor adapter to reconstruct and export displacement/stress results; the template uses csf.cuf.adapters.output.post.

**`output.directory`** - *path string*. Results destination, conventionally relative to the case file. Check the runner for path resolution and overwrite behavior.

## 4. Numerical meaning and practical interactions

### 4.1 Two distinct approximation directions

`cuf.basis` / `cuf.order` control cross-sectional approximation; `longitudinal.basis` / `longitudinal.order` / element count or boundaries control axial approximation. A refinement of one does not imply refinement of the other. For polynomial (or custom) basis comparisons, hold problem, adapters, quadrature and solver settings constant.

### 4.2 Variable CSF sections and basis plugins

A continuously varying section is supplied by the **problem/CSF geometry**, not created by increasing `cuf.order`. Whether a particular transverse basis follows variable geometry, requires polygons or imposes prismatic restrictions depends on its implementation. A custom basis interface may evaluate `basis.value(tau, y, z, x=x)`, together with spatial derivatives including dF/dx. This must be carried through every relevant adapter/integration point for explicitly x-dependent expansions.

### 4.3 Axial mesh versus postprocessing

With boundaries `[0, 0.1, ..., 1.0]`, there are ten axial intervals (subject to solver acceptance). With `elements: 1` and `order: 12`, there is one high-order element. In contrast, `sampling.stations` indicates requested locations of reported sections; `displacement_samples` and `stress_grid` affect output resolution, not mesh resolution. Axial quadrature (`longitudinal.gauss_order`) and transverse quadrature (`section_integration.gauss_order`) control **different integrations**.

### 4.4 MITC and matrix equilibration

MITC options appear in bridge-like, T-section and locking benchmark cases; do not conflate `correctionMITC` with solver equilibration. The former influences element assembly/correction, while equilibration modifies numerical scaling/conditioning of the linear system. Verification flags do not themselves constitute external physical validation. When investigating locking, use ON/OFF paired cases with identical physical data and numerical discretization.

### 4.5 Reproducibility and path rules

Relative `problem.yaml`, `problem.adapter`, `cuf.basis` file paths, `output.adapter` file paths, and `output.directory` must resolve in the execution convention of the project. The examples are commonly arranged to be relative to their case directories, but the loader source is the authority. A dotted Python module adapter must be importable in the configured environment. Keep an unmodified reference case when testing new options and avoid using the same output directory for sweeps unless overwriting is intentional.

## 5. Optional configurations and when to use them

The following options can be useful when moving beyond the baseline template. **They are not interchangeable across all plugins**: the selected adapter and basis implementation determine compatibility.

| Configuration | Purpose | Practical consideration |
|---|---|---|
| `cuf.basis: scaled_legendre` | Select Legendre-type transverse polynomial functions. | Compare convergence with a fixed physical problem and quadrature. |
| `cuf.basis: scaled_maclaurin` | Select a Maclaurin-type transverse series. | Verify the meaning of `cuf.order` for this expansion. |
| `cuf.basis: ../expansions/custom.py` | Load a custom transverse expansion. | Implement the expected evaluation and derivative interface. |
| `cuf.basis_options.*` | Supply basis-specific domain, mapping and connectivity controls. | Only meaningful for plugins that accept these options. |
| `longitudinal.elements` | Specify the axial mesh using an element count. | Use instead of `element_boundaries` unless the runner explicitly documents precedence. |
| `longitudinal.gauss_order` | Request explicit axial quadrature. | Check integration convergence for high-order and variable-coefficient problems. |
| `longitudinal.material_polynomial_degree` | Provide material polynomial-degree information. | Confirm how the selected integration implementation uses the hint. |
| `solver.equilibration.iterations` | Configure equilibration with a scalar or sequence. | Confirm whether sequences request multiple runs or a single setting. |

## 6. Separate FEM3D case format (not a CUF configuration)

A separate 3D FEM case format uses `mesh` and `analysis` instead of CUF transverse expansion and integration settings. This format is useful for reference solutions, but these sections must not be mixed into a CUF case without explicit runner support.

```yaml
case:
  name: torsion_halfwave_model2
problem:
  yaml: ../problems/torsion_halfwave.yaml
mesh:
  longitudinal_divisions: 120    # Axial 3D mesh subdivisions
  web_width_divisions: 12      # Cross-section web thickness/width subdivisions
  web_height_divisions: 36     # Cross-section web height subdivisions
  flange_overhang_divisions: 12 # Flange overhang subdivisions
  flange_thickness_divisions: 9 # Flange thickness subdivisions
  load_gauss_order: 4          # Numerical integration for applied traction/load
analysis:
  element: stdBrick            # 3D brick element identifier
  system: SparseGeneral        # Linear-system solver identifier
sampling:
  stations: [0.0, 0.5, 1.0]
output:
  directory: ../output/torsion_halfwave_model2
```

**FEM3D key descriptions:** `mesh.longitudinal_divisions` discretizes x; `mesh.web_width_divisions` and `mesh.web_height_divisions` subdivide the web dimensions; `mesh.flange_overhang_divisions` and `mesh.flange_thickness_divisions` subdivide the flange; `mesh.load_gauss_order` requests load integration quadrature; `analysis.element` selects the 3D element keyword; `analysis.system` selects the linear system keyword. The example selects `stdBrick` and `SparseGeneral`. Unlike CUF order parameters, these mesh counts affect 3D element topology.

## 7. Practical recipes

**Transverse-order convergence:** duplicate a bending case; change only `case.name`, `cuf.order`, and `output.directory`; compare reconstructed quantities at the same stations. Higher transverse order may require quadrature convergence checks.

**Axial-mesh convergence:** keep `cuf` unchanged and adjust `element_boundaries` while holding longitudinal `order` constant; alternatively vary `order` at fixed boundaries. Do not confuse these with `sampling.stations`.

**Bending vs torsion:** choose corresponding `problem.yaml` and `problem.adapter` together, rather than changing only the case identifier.

**Custom transverse expansion:** use a Python `cuf.basis` file implementing consistent values and derivatives at physical `(x,y,z)`; verify its `order` convention, available basis options, geometry restrictions and adapter support.

**MITC comparison:** retain geometry, loads, basis, mesh and output metrics; toggle `solver.correctionMITC` and optionally `verifyMITCAssembly` for diagnostics. Review both accuracy and numerical conditioning.

**Output-only resolution:** increase `displacement_samples` or `stress_grid` while leaving mesh, basis and quadrature fixed; stress recovery precision and visualization grid spacing are distinct questions.

## 8. Validation checklist 

- [ ] The referenced `problem.yaml` exists and is compatible with the chosen problem adapter.
- [ ] Case and output names distinguish distinct parameter studies.
- [ ] The transverse basis is correctly interpreted: built-in name versus loadable plugin file.
- [ ] The plugin handles physical x-dependent geometry and all required derivatives if F_tau depends on x.
- [ ] Longitudinal element boundaries are monotonic, cover the intended normalized domain, and use the expected endpoints.
- [ ] One consistent axial mesh specification (`elements` or `element_boundaries`) is selected.
- [ ] Axial and transverse quadrature orders are adequate for the chosen basis and material variation.
- [ ] MITC options and adapter support are checked; optional flags are not assumed globally implemented.
- [ ] Equilibration list-versus-scalar behavior is checked in the runner.
- [ ] Sampling settings are not mistaken for a refinement of the solved approximation.
- [ ] Output artifacts are not silently overwritten and paths resolve as expected.
- [ ] CUF case sections are not mixed with FEM3D-only `mesh` and `analysis` sections.
- [ ] Results are checked against convergence trends and where available external FEM/reference solutions.
