# CSF-CUF - General Geometry and Materials through Queryable Fields

# CSF-CUF - Current Architecture, Role of the Python Sources, and Logical Placement

**Revision 2:** separation of the transverse basis from the solver through `csf_cuf_basis_plugins.py`; `scaled_maclaurin`

## Purpose of this document

This document describes in detail the role of the Python source files that make up the current CSF-CUF chain and the FEM3D solver used as a baseline.

The review is based on the actual sources provided in the two packages:

- `run_csf_cuf_old.zip`
- `csf_cuf_section.zip`

Files whose names contain `old` are excluded from the functional analysis, as requested. The file `csf_cuf_engine_before_OPT09.py` does not contain `old` in its name, but it is clearly a historical snapshot preceding OPT-09; it is therefore classified as **BACKUP / SNAPSHOT**, not as a runtime source.

The document starts from the architecture and the working directory, then describes each module. For every file it identifies:

- responsibility;
- position in the computational chain;
- input and output data;
- main dependencies;
- what it must **not** contain;
- status: runtime, support, diagnostics, benchmark/legacy;
- recommended logical placement in a future reorganization.

## Note on terminology

Here, **CSF** and **CUF** denote two layers with distinct roles within the same computational chain.

CSF supplies the sectional description requested at the longitudinal coordinate `x`:

```text
S(x) -> domains Omega^k(x), geometry, material / constitutive state
```

CUF uses those sectional data to construct the generalized coefficients, the fundamental nucleus, the longitudinal discretization, the global system, and the mechanical solution.

The most important architectural separation is therefore:

```text
PHYSICAL / SECTIONAL DATA
    CSF YAML
       |
       v
    CSF reader / section field
       |
       v
    SectionProvider + ConstitutiveProvider
       |
       v

CSF-CUF SECTIONAL COUPLING
    CUF basis F_tau(y,z)
       +
    domains Omega^k(x)
       +
    C^k(x,y,z)
       |
       v
    J_tau,s(x)
       |
       v
    CUF fundamental nucleus
       |
       v

LONGITUDINAL SOLVER
    longitudinal FE
       |
       v
    element matrices
       |
       v
    global assembly
       |
       v
    constraints
       |
       v
    KKT solve
       |
       v
    u(x,y,z)
       |
       v
    post-processing / report
```

This distinction should remain visible in the future directory structure as well.

# 1. Current directories and their use

## A. Working directory

The working directory contains solver orchestration, the longitudinal solver, assembly, physical problems, post-processing, and the FEM3D path.

Main runtime files:

```text
run_csf_cuf.py
csf_cuf_case.py
csf_cuf_csf_bridge.py
csf_cuf_engine.py
csf_cuf_basis_plugins.py
csf_cuf_numerics.py
csf_cuf_element.py
csf_cuf_longitudinal.py
csf_cuf_assembly.py
csf_cuf_point_bc.py
csf_cuf_linear_constraint.py
csf_cuf_augmented_solver.py
csf_cuf_problem.py
csf_cuf_problem_carrera_torsion.py
csf_cuf_recovery.py
csf_cuf_post.py
```

FEM3D path:

```text
run_csf_fem3d.py
csf_fem3d.py
```

FEM3D checks / diagnostics:

```text
check_fem3d.py
check_fem3d_jacobian.py
```

Startup check:

```text
startup_check.py
```

Snapshot / backup, not runtime:

```text
csf_cuf_engine_before_OPT09.py
```

Files with `old` in their names are excluded as requested and should be considered outside the future active structure.

## B. `src/csf/utils`

This directory contains the general CSF-CUF layer, namely reusable objects that do not belong to a particular benchmark, a specific load problem, or the executable driver.

Files in the general CSF-CUF layer:

```text
csf_cuf.py
csf_cuf_section.py
csf_cuf_basis.py
csf_cuf_integration.py
csf_cuf_material.py
csf_cuf_sectional.py
csf_cuf_nucleus.py
```

File present with a different role:

```text
csf_cuf_solver.py
```

CSF utility not specific to CUF:

```text
csf_create_cone.py
```

The natural role of `src/csf/utils` is therefore to contain general and reusable primitives. However, the name `utils` has become too broad: these files are not simple utilities; they form actual layers of the CSF-CUF mechanical and numerical architecture.

# 2. Current CUF solver execution chain

The current runtime path starts from:

```bash
python run_csf_cuf.py cases/<case>.yaml
```

The actual chain is:

1. **`run_csf_cuf.py`**
   - reads the case through `csf_cuf_case.load_case()`;
   - creates `CSFCUFModelBridge` from the CSF YAML model;
   - builds the physical-problem plugin;
   - calls `csf_cuf_engine.solve_case()`;
   - calls `csf_cuf_post.write_outputs()`.

2. **`csf_cuf_case.py`**
   - interprets the analysis YAML;
   - does **not** read the geometry directly;
   - resolves model and output paths;
   - builds an immutable `CaseDefinition`.

3. **`csf_cuf_csf_bridge.py`**
   - reads the CSF model;
   - exposes `SectionProvider` and `ConstitutiveProvider`;
   - translates the CSF state into objects usable by the CUF solver.

4. **`csf_cuf_engine.py`**
   - coordinates the solution;
   - reads the basis name requested by the case;
   - asks the basis plugin registry for the concrete `CUFBasis`;
   - applies the minimum sectional quadrature requirement declared by the plugin;
   - builds `SectionalCoefficientProvider`;
   - builds the CUF nucleus;
   - builds the longitudinal FE mesh and integrator;
   - builds loads;
   - assembles `K` and `f`;
   - builds constraints;
   - forms the KKT system;
   - solves it;
   - compiles the continuous solution `u(x,y,z)`.

5. **`csf_cuf_basis_plugins.py`**
   - resolves `cuf.basis -> CUFBasisPlugin`;
   - builds the requested concrete basis;
   - contains the registry of available bases;
   - associates any basis-specific numerical requirements with the basis;
   - currently registers `scaled_maclaurin`;
   - for `scaled_maclaurin`, delegates construction to `ScaledMaclaurinBasis` defined in `csf_cuf_numerics.py`.

6. **`csf_cuf_numerics.py`**
   - contains `ScaledMaclaurinBasis`, unchanged from the validated runtime;
   - provides `FixedGaussPolygonIntegrator`;
   - computes transverse scales and bounds.

7. **`src/csf/utils/csf_cuf_sectional.py`**
   - builds the generalized sectional coefficients `J(x)`.

8. **`src/csf/utils/csf_cuf_nucleus.py`**
   - transforms `J(x)` into contributions to the CUF fundamental nucleus.

9. **`csf_cuf_element.py`**
   - integrates nucleus contributions along `x`;
   - produces the element matrix for each CUF pair `(tau,s)`.

10. **`csf_cuf_assembly.py`**
    - maps element matrices to global DOFs;
    - assembles global `K` and global `f`;
    - applies OPT-10 machine-precision numerical cleanup.

11. **`csf_cuf_point_bc.py`**
    - transforms physical point constraints into rows `A q = b`.

12. **`csf_cuf_linear_constraint.py`**
    - builds the augmented system:

```text
[K A^T] [q]      [f]
[A  0 ] [lambda] [b]
```

13. **`csf_cuf_augmented_solver.py`**
    - solves the KKT system;
    - checks residuals;
    - performs controlled fallbacks;
    - on failure, writes diagnostics / checkpoints.

14. **`csf_cuf_engine.CSFCUFSolution`**
    - transforms solved DOFs into the continuous function:

```text
u(x,y,z)
```

15. **`csf_cuf_post.py`**
    - queries `u(x,y,z)`;
    - searches for the requested extrema;
    - performs Table 9 / Table 10 normalizations;
    - generates the report.

This chain is important because it clearly separates:

- the CSF model;
- sectional integration;
- CUF mechanics;
- longitudinal FE;
- global algebra;
- post-processing.

# 3. FEM3D execution chain

The FEM3D path starts from:

```bash
python run_csf_fem3d.py cases/<case>.yaml
```

Chain:

1. **`run_csf_fem3d.py`**
   - reads the case YAML;
   - resolves the CSF model path;
   - calls `csf_fem3d.read_csf_field()`;
   - calls `csf_fem3d.build_mesh()`;
   - builds the FEM3D load consistent with the problem;
   - calls `csf_fem3d.solve_opensees()`;
   - extracts extrema, governing sections, and residuals;
   - writes reports and CSV/TXT output.

2. **`csf_fem3d.py`**
   - builds a three-dimensional `stdBrick` discretization;
   - assigns material to the bricks according to the longitudinal CSF state;
   - maps benchmark loads onto the solid mesh;
   - runs OpenSees;
   - recovers displacements and equilibrium diagnostics;
   - produces data for the Table 9 / Table 10 report.

This path is deliberately distinct from the CUF solver. The two paths share the **CSF model**, not the mechanical discretization.

# 4. Detailed description - working directory

## 4.1 `run_csf_cuf.py`

**Status:** CUF runtime entry point.

**Responsibility:**  
It is the thinnest high-level driver in the entire chain. It must not contain mechanics, geometry, integration, or solution algorithms. Its task is to connect the already existing blocks.

**Flow:**

```python
case = load_case(case_path)
model = CSFCUFModelBridge.from_yaml(case.model_path)
problem = build_problem(case.problem_type, case.problem_options)
result = solve_case(case, model, problem)
write_outputs(result, case)
```

**Startup output:**  
It explicitly declares:

- case name;
- CSF model;
- `geometry source = CSF only`;
- `material source = CSF per polygon / per section`;
- `solver material data = none`;
- `solver shape model = none`;
- CUF order;
- longitudinal FE discretization.

**Architectural value:**  
It is important that it remain thin. If section formulas, special Table 9/10 conditions, or polygon construction appear here in the future, the architectural separation would be violated.

**Natural future placement:**

```text
scripts/run_csf_cuf.py
```

or:

```text
src/csf_cuf/cli.py
```

with a minimal launcher in the repository root.

## 4.2 `csf_cuf_case.py`

**Status:** runtime - analysis configuration.

**Responsibility:**  
Reads the **case YAML**, not the CSF model. Converts YAML blocks into immutable dataclasses:

```text
CUFSettings
LongitudinalSettings
SectionIntegrationSettings
SamplingSettings
CaseDefinition
```

**Data it manages:**

- case name;
- path to the CSF model;
- `problem.type` and problem options;
- CUF basis and order `N`;
- longitudinal discretization;
- longitudinal quadrature order;
- sectional integration method and order;
- sampling stations;
- post-processing density;
- output directory.

**Data it must not manage:**

- section vertices;
- physical section dimensions;
- solver-specific `E`, `G`, `nu`;
- a length duplicated from the CSF model;
- Carrera benchmark values.

**Observation:**  
It has a crucial role in keeping separate:

```text
"how to run the analysis"
```

from:

```text
"what the physical CSF model is"
```

**Natural future placement:**

```text
src/csf_cuf/config/case.py
```

## 4.3 `csf_cuf_csf_bridge.py`

**Status:** runtime - CSF model -> CUF solver adapter.

**Responsibility:**  
This is the application bridge between the actual CSF model and the generic APIs of the CSF-CUF layer.

**Classes:**

```text
CSFDomainState
CSFCUFModelBridge
```

**Main bridge functions:**

- `from_yaml()`: reads the CSF model through `CSFReader`;
- `longitudinal_domain()`: exposes the longitudinal domain;
- `domain_state()`: retrieves the state of a domain/polygon at a requested `x`;
- `_E_field()`, `_G_field()`: build constitutive fields for the domain;
- `validate_material_state()`: checks material consistency.

**Dependencies:**

```text
csf.io.csf_reader
csf.io.csf_issues
csf.utils.csf_cuf.CSFSectionProvider
csf.utils.csf_cuf.IsotropicEGConstitutive
```

**Conceptual role:**  
This is one of the most important files for explaining the role of CSF in the project. The solver does not own an "I-section". It owns a bridge capable of obtaining, from the CSF model and at the requested `x`, the domains and constitutive state.

**Natural future placement:**

```text
src/csf_cuf/adapters/csf_model.py
```

or:

```text
src/csf_cuf/bridge.py
```

## 4.4 `csf_cuf_engine.py`

**Status:** runtime - central solver orchestrator.  
The concrete transverse basis is no longer hard-coded in the engine.

**Responsibility:**  
Coordinates the entire solution while avoiding direct implementation of the details of each layer. It no longer knows the concrete mathematical family of the basis.

**Main function:**

```text
solve_case(case, model_bridge, problem)
```

**Internal sequence:**

1. obtains `SectionProvider` and `ConstitutiveProvider` from the bridge;
2. reads `x0, x1` from the `SectionProvider`;
3. validates numerical families unrelated to the basis;
4. resolves `case.cuf.basis` through `get_cuf_basis_plugin()`;
5. asks the plugin to build the concrete `CUFBasis`;
6. asks the plugin for any minimum sectional quadrature order;
7. determines the effective sectional quadrature order;
8. builds `FixedGaussPolygonIntegrator`;
9. builds `SectionalCoefficientProvider`;
10. builds `FundamentalNucleusProvider`;
11. builds `GaussLegendreLongitudinalIntegrator`;
12. builds `CUFElementMatrixBuilder`;
13. builds the longitudinal mesh;
14. asks the problem plugin for the loads;
15. assembles the global system;
16. asks the problem plugin for the constraints;
17. builds the KKT system;
18. solves it;
19. creates `CSFCUFSolution`.

**OPT-09 after refactoring:**  
Basis-specific policy is no longer expressed in the engine.

The engine only applies:

```text
effective_section_gauss_order =
    max(requested_section_gauss_order,
        basis_plugin.minimum_section_gauss_order(basis))
```

For the `scaled_maclaurin` plugin, the requirement remains:

```text
minimum_section_gauss_order = CUF_order + 1
```

The mathematical reason remains the validated one: for a complete Maclaurin basis of order `N`, products `F_tau F_s` may reach degree `2N`; with polygon slicing, the Gauss-Legendre rule must avoid under-integration of the basis. This knowledge now belongs to the `scaled_maclaurin` plugin, not to the general orchestrator.

**`CSFCUFSolution` class:**  
This is a strong architectural point. The public result of the solver is not a sampled table but a continuous function:

```text
u = solution(x,y,z)
```

The class:

- compiles the solved generalized coefficients once;
- locates the longitudinal element;
- reconstructs `q_tau(x)` with the shape functions;
- evaluates the full transverse basis;
- returns `[u_x, u_y, u_z]`.

**Post-processing:**  
The engine does **not** create the report. It delivers `u(x,y,z)` to the post-processor.

**Natural future placement:**

```text
src/csf_cuf/solver/engine.py
```

## 4.5 `csf_cuf_basis_plugins.py`

**Status:** runtime - dispatch / registry of CUF transverse bases.

**Responsibility:**  
Separates selection of the basis family from the engine.

**Main object:**

```text
CUFBasisPlugin
```

**Plugin contract:**  
Each plugin declares:

- `name`: name selectable from the case YAML;
- `builder`: construction of the concrete `CUFBasis`;
- `section_gauss_minimum`: minimum sectional quadrature requirement associated with that basis family.

**Main functions:**

```text
register_cuf_basis_plugin()
get_cuf_basis_plugin()
available_cuf_basis_plugins()
```

**Currently registered plugin:**

```text
scaled_maclaurin
```

**Current chain:**

```text
case.cuf.basis = "scaled_maclaurin"
    ->
get_cuf_basis_plugin("scaled_maclaurin")
    ->
_build_scaled_maclaurin(...)
    ->
transverse_scales(section_provider)
    ->
ScaledMaclaurinBasis(...)
    ->
CUFBasis consumed by the rest of the solver
```

**Important:**  
`ScaledMaclaurinBasis` has not been rewritten or modified. Its mathematical/numerical implementation remains in `csf_cuf_numerics.py`. Only the point at which it is selected and constructed has changed.

**OPT-09:**  
The requirement:

```text
minimum_section_gauss_order = basis.order + 1
```

now belongs to the `scaled_maclaurin` plugin. A future different basis can therefore declare a different numerical criterion without introducing basis-specific `if` statements into the engine.

**Architectural effect:**

Before:

```text
engine -> ScaledMaclaurinBasis
```

Now:

```text
engine -> basis plugin registry -> concrete CUFBasis
```

This separation makes the transverse basis replaceable without changing `SectionalCoefficientProvider`, `FundamentalNucleusProvider`, element assembly, the KKT solver, or the CSF interface.

**Natural future placement:**

```text
src/csf_cuf/basis_plugins.py
```

or, if the number of families grows:

```text
src/csf_cuf/plugins/basis.py
```

## 4.6 `csf_cuf_numerics.py`

**Status:** runtime - optimized numerics specific to the current solver.

**Contents:**

```text
ScaledMaclaurinBasis
FixedGaussPolygonIntegrator
transverse_scales()
transverse_bounds()
all_vertices()
_ScaledMaclaurinFactorPlan
```

**Role:**  
This file contains two concrete numerical implementations used by the runtime:

- the scaled Maclaurin basis, currently built by the `scaled_maclaurin` plugin;
- the fixed-Gauss polygon integrator.

**`ScaledMaclaurinBasis`:**

- generates the complete polynomial expansion up to order `N`;
- normalizes `y` and `z` through transverse scales;
- evaluates values and derivatives;
- supports vectorized `values()` evaluation;
- precompiles a factor plan to accelerate integration/assembly.

**`FixedGaussPolygonIntegrator`:**

- integrates over polygonal domains;
- builds subintervals and quadrature points;
- supports `integrate()` and `integrate_vector()`;
- provides the operational basis for optimized sectional integration.

**Architectural observation:**  
There is functional overlap with:

```text
src/csf/utils/csf_cuf_basis.py
src/csf/utils/csf_cuf_integration.py
```

This is not merely duplicate naming:

- `src/csf/utils` contains general APIs and implementations;
- `csf_cuf_numerics.py` contains the optimized implementations used by the current solver.

This distinction should be made explicit during reorganization because it is currently easy to misread.

**Natural future placement:**

```text
src/csf_cuf/numerics/scaled_maclaurin.py
src/csf_cuf/numerics/polygon_gauss.py
```

or as a single:

```text
src/csf_cuf/numerics.py
```

## 4.7 `csf_cuf_element.py`

**Status:** runtime - CUF element-matrix construction.

**Responsibility:**  
Connects:

```text
FundamentalNucleusProvider
```

with longitudinal FE integration.

**Classes:**

```text
ElementCUFBlock
ElementCUFMatrix
CUFElementMatrixBuilder
```

**Unit of work:**  
For one longitudinal element and one ordered pair of transverse modes `(tau,s)`, it builds the CUF stiffness blocks.

**Important methods:**

```text
build_pair()
_build_pair_scalar()
_build_pair_batched()
_build_component_block()
_coefficient_field()
```

The presence of `_build_pair_batched()` shows the current optimized path: grouping evaluations of sectional coefficients instead of repeating a scalar chain for each contribution.

**Does not perform:**

- global assembly;
- boundary conditions;
- solve;
- report generation;
- geometry construction;
- benchmark loads.

**Natural future placement:**

```text
src/csf_cuf/fe/element.py
```

## 4.8 `csf_cuf_longitudinal.py`

**Status:** runtime - 1D FE discretization along the beam axis.

**Classes:**

```text
LongitudinalElement1D
LongitudinalMesh1D
LongitudinalDiscretizer
LongitudinalIntegrator
GaussLegendreLongitudinalIntegrator
```

**Responsibility:**  
Builds only the numerical representation along `x`:

```text
longitudinal domain
   -> nodes
   -> elements
   -> shape functions N_a
   -> dN_a/dx
   -> longitudinal quadrature
```

**`LongitudinalElement1D`:**

- local/global nodes;
- mapping from natural to physical coordinates;
- Jacobian;
- `shape_values()`;
- derivatives in reference and physical coordinates.

**`GaussLegendreLongitudinalIntegrator`:**

- Gauss points and weights;
- bilinear and linear integration;
- selection of the required derivatives.

**Invariant:**  
The physical length must not be restated here. The domain is obtained from the `SectionProvider` / CSF.

**Natural future placement:**

```text
src/csf_cuf/fe/longitudinal.py
```

## 4.9 `csf_cuf_assembly.py`

**Status:** runtime - global assembly.  
**Current version:** OPT-10 machine-precision sparse cleanup.

**Classes:**

```text
GlobalDOFLayout
AssembledCSFCUFSystem
CSFCUFGlobalAssembler
```

**Responsibility:**

```text
{K_e^(tau,s)} -> K_global
{f_e^tau}     -> f_global
```

**`GlobalDOFLayout`:**  
Defines the mapping:

```text
(node, tau, component) <-> global DOF
```

The physical components remain three:

```text
x, y, z
```

**`AssembledCSFCUFSystem`:**  
Container for:

- sparse `K`;
- `f`;
- DOF layout;
- mesh / metadata required by subsequent layers.

**`CSFCUFGlobalAssembler`:**

- iterates over elements;
- iterates over CUF pairs;
- requests matrices from `CUFElementMatrixBuilder`;
- creates COO triplets;
- sums duplicates;
- converts to CSR;
- assembles generalized loads.

**OPT-10:**  
After duplicate summation, it removes only numerically zero coefficients according to a machine-precision-based threshold:

```text
threshold = O(eps_float64 * max|K|)
```

This is not a fixed physical threshold and is not a regularization.

**Importance:**  
At high orders, this file dominates memory/time because the cardinality of CUF pairs grows rapidly.

**Natural future placement:**

```text
src/csf_cuf/assembly/global_assembly.py
```

## 4.10 `csf_cuf_point_bc.py`

**Status:** runtime - mapping of physical point constraints.

**Classes:**

```text
PointwiseDisplacementConstraint
LinearConstraintSystem
PointwiseBoundaryConstraintMapper
```

**Responsibility:**  
Converts a physical prescription:

```text
u_i(end,y,z) = value
```

into the corresponding relation on generalized coefficients:

```text
sum_tau F_tau(y,z) q_tau,i(end) = value
```

It therefore produces rows:

```text
A q = b
```

**Importance:**  
This avoids confusing a physical constraint on `u(y,z)` with fixing a single CUF coefficient. In a high-order kinematics, a physical constraint is generally a linear combination of modes.

**Does not perform:**

- modification of `K`;
- penalization;
- solve.

**Natural future placement:**

```text
src/csf_cuf/constraints/pointwise.py
```

## 4.11 `csf_cuf_linear_constraint.py`

**Status:** runtime - exact constraint augmentation.

**Classes:**

```text
AugmentedLinearConstraintSystem
LinearConstraintAugmenter
```

**Responsibility:**  
Receives:

```text
K q = f
A q = b
```

and constructs:

```text
[ K   A^T ] [ q      ] = [ f ]
[ A    0  ] [ lambda ]   [ b ]
```

**Characteristic:**  
No penalty parameter is used.

**Importance:**  
It is separate from `csf_cuf_point_bc.py`:

- `point_bc` decides **how** a physical constraint becomes `A q = b`;
- `linear_constraint` decides **how** `A q = b` enters the algebraic system.

**Natural future placement:**

```text
src/csf_cuf/constraints/kkt.py
```

## 4.12 `csf_cuf_augmented_solver.py`

**Status:** runtime - KKT algebraic solver and failure diagnostics.

**Main class:**

```text
AugmentedSparseLinearSolver
```

**Output:**

```text
AugmentedConstraintSolution
```

**Responsibility:**

- primary direct sparse solve;
- verification of the candidate against the original system;
- measurement of equilibrium residual;
- measurement of constraint residual;
- evaluation of possible dense fallbacks;
- does not accept a solution merely because the factorization returned a vector;
- on failure, produces persistent diagnostics.

**Internal diagnostic functions include:**

- numerical ranges;
- top coefficient / residual indices;
- symmetry metrics;
- density estimates;
- checkpoints for KKT, RHS, candidate solution, and metadata.

**Role in the `N=30` case:**  
This layer made it possible to distinguish between:

- correctness of the numerical solution of an extremely ill-conditioned system;
- relative residual with respect to a small RHS;
- exact satisfaction of constraints;
- conditioning limits of the high-order basis.

**Must not:**

- alter the physics;
- widen tolerances just to obtain a PASS;
- arbitrarily regularize `K`.

**Natural future placement:**

```text
src/csf_cuf/solver/kkt_solver.py
```

## 4.13 `csf_cuf_problem.py`

**Status:** partial runtime / generic problem API.

**Contents:**

```text
EssentialBoundaryCondition
ScalarLoadField
PiecewiseLinearLoadField
GeneralizedLongitudinalLoad
LongitudinalDiscretization
SolverOptions
CSFCUFProblemData
CSFCUFProblemReader
```

**Responsibility:**  
Defines generic structures for:

- essential boundary conditions;
- longitudinal load fields;
- longitudinal discretization;
- reading a generic problem from YAML.

**Current use in the new chain:**  
The runtime uses in particular:

```text
GeneralizedLongitudinalLoad
ScalarLoadField
LongitudinalDiscretization
```

The main case is instead read by `csf_cuf_case.py`, while Carrera problems are built by the `csf_cuf_problem_carrera_torsion.py` plugin.

**Observation:**  
Two layers therefore currently overlap partially:

1. `CaseDefinition` = execution configuration;
2. `CSFCUFProblemData` = generic representation of the physical problem.

The distinction is conceptually valid, but the reorganization should clarify which classes are truly public and which are inherited from the earlier phase.

**Natural future placement:**

```text
src/csf_cuf/problem/base.py
```

## 4.14 `csf_cuf_problem_carrera_torsion.py`

**Status:** runtime - Carrera Table 9 / Table 10 validation-problem plugin.

**Note on the name:**  
The name is now too narrow because the file contains both **torsion** and **bending**.

**Main contents:**

Torsion:

```text
TorsionalLinePairProjector
ModeLineLoadField
CarreraTorsionHalfWaveProblem
moving_load_points()
```

Bending:

```text
BendingSurfaceProjector
ModeSurfaceLoadField
CarreraBendingBottomSurfaceHalfWaveProblem
_lowest_boundary_segments()
_loaded_face_factors()
```

Factory:

```text
build_problem(problem_type, options)
```

**Responsibility:**  
Defines what is **problem-specific**:

- loads;
- loaded points / surfaces;
- longitudinal phase;
- required constraints;
- tracked response points.

**Very important principle:**  
The plugin does not construct the I-section geometry. Load points and surfaces are located by querying the `SectionProvider`.

**Table 10:**

- two opposite line loads;
- points obtained from bounds/vertices of the current section.

**Table 9:**

- load on the bottom surface;
- loaded segments identified from the current geometry.

**`build_problem()`:**  
This is the central dispatch:

```text
problem.type -> concrete problem object
```

**Natural future placement:**  
The file should probably be separated into:

```text
src/csf_cuf/problems/carrera_table9.py
src/csf_cuf/problems/carrera_table10.py
src/csf_cuf/problems/factory.py
```

not to change the logic, but to make the role explicit.

## 4.15 `csf_cuf_recovery.py`

**Status:** generic recovery library; not the main post-processor of the current engine for displacements alone, but still the layer for `u/epsilon/sigma`.

**Classes:**

```text
GeneralizedAmplitudeState
DisplacementState
CSFCUFDisplacementRecovery
StrainState
StressState
CSFCUFStrainStressRecovery
```

**Responsibility:**  
Reconstructs:

```text
q -> u
q,dq/dx -> epsilon
epsilon + C -> sigma
```

**Difference from `CSFCUFSolution`:**  
The current engine compiles `u(x,y,z)` directly in `CSFCUFSolution` to make displacement post-processing very fast.

`csf_cuf_recovery.py` remains the general mechanical layer needed to recover:

- strains;
- stresses;
- complete states.

**Natural future placement:**

```text
src/csf_cuf/recovery/fields.py
```

## 4.16 `csf_cuf_post.py`

**Status:** runtime - post-processing and reporting.

**Responsibility:**  
Receives the solved function `u(x,y,z)` and builds the quantities to report.

**Main functions:**

```text
section_displacement_extremum()
_section_extrema()
_global_extrema()
_report_spec()
_format_report_text()
write_outputs()
```

**Support functions:**

- point-in-polygon tests;
- domain bounds;
- recognition of axis-aligned rectangles;
- `max` / `max_abs` criteria;
- normalization of components into the paper's coordinate system.

**Report:**  
`_report_spec()` selects the format from:

```text
case.problem_type
```

Therefore:

- the YAML filename does not determine Table 9 / Table 10;
- the output directory does not determine Table 9 / Table 10;
- the physical problem type selects the report semantics.

**Current cost:**  
Post-processing has been one of the expensive areas in profiling because it searches for extrema over the continuous polynomial field. Recent optimizations introduced fixed-`x` evaluations and vectorized basis evaluation.

**Must not:**

- assemble `K`;
- modify the solution;
- introduce hard-coded geometry;
- use the published benchmark value as an input to the solution.

**Natural future placement:**

```text
src/csf_cuf/post/carrera.py
```

and, for generic functions:

```text
src/csf_cuf/post/extrema.py
```

## 4.17 `startup_check.py`

**Status:** support / smoke test.

**Responsibility:**  
Checks that:

- the case is readable;
- the model path can be resolved;
- the CSF bridge can be constructed;
- the domain and minimum data are accessible.

This is a startup integrity test, not a mechanical validation.

**Natural future placement:**

```text
tests/smoke/test_startup.py
```

or as a diagnostic script in:

```text
tools/startup_check.py
```

## 4.18 `csf_cuf_engine_before_OPT09.py`

**Status:** historical snapshot / backup, not runtime.

**Current responsibility:**  
None in the production chain.

**Utility:**  
It may be kept temporarily for:

- comparison of the OPT-09 change;
- manual regression;
- historical reconstruction.

**During reorganization:**  
It should not remain beside the active source. Better options are:

- delete it if Git already preserves the history; or
- archive it outside `src`, for example under `diagnostics/history/`.

Keeping `before_OPTxx` copies beside runtime sources increases the risk of accidental imports or editing the wrong file.

# 5. Detailed description - FEM3D

## 5.1 `run_csf_fem3d.py`

**Status:** FEM3D runtime entry point.

**Responsibility:**  
Orchestrates the reference 3D analysis.

**Reads:**

- `model.csf_yaml`;
- `problem.type`;
- mesh settings;
- analysis settings;
- outputs;
- report settings;
- checks;
- output directory.

**Selects:**

Table 9:

```text
bending_bottom_surface_halfwave
```

Table 10:

```text
torsion_line_pair_halfwave
```

**Calls:**

- `build_mesh()`;
- load function consistent with the problem;
- `solve_opensees()`;
- `displacement_maxima()`;
- `equilibrium_diagnostics()`;
- Table 9 / Table 10 report;
- CSV/TXT writer.

**Must not:**  
Contain detailed mesh construction or OpenSees logic; those belong in `csf_fem3d.py`.

**Natural future placement:**

```text
scripts/run_csf_fem3d.py
```

## 5.2 `csf_fem3d.py`

**Status:** FEM3D runtime - implementation of the 3D baseline.

**Size / role:**  
It is currently a very large module because it combines:

- geometry extraction from CSF;
- section discretization;
- brick construction;
- materials;
- loads;
- OpenSees solve;
- recovery;
- reporting support.

**Main dataclasses:**

```text
MaterialState
RectDomain
ISectionFrame
Cell2D
StationMesh
Brick
FEMMesh
```

**Geometry / mesh functions:**

```text
read_csf_field()
longitudinal_domain()
_rect_domain_from_polygon()
i_section_frame()
_section_cells()
build_mesh()
```

**Load functions:**

```text
torsion_line_pair_nodal_loads()
bending_bottom_surface_nodal_loads()
_consistent_line_segment_loads()
```

**Solve:**

```text
solve_opensees()
```

**Post / report:**

```text
displacement_maxima()
equilibrium_diagnostics()
carrera_table9_style_row(s)
carrera_table10_style_row(s)
write_*
print_*
```

**Materials:**  
The solver creates material states for longitudinal stations. In degraded cases it is normal to observe:

```text
material states = number of longitudinal layers
```

when `E/G` vary with `x`.

**Current architectural limitation:**  
The file is too dense to be a final placement. In a future reorganization it is the clearest candidate for separation into:

```text
fem3d/model.py
fem3d/mesh.py
fem3d/loads.py
fem3d/opensees_solver.py
fem3d/post.py
```

This would separate responsibilities without changing the physics.

## 5.3 `check_fem3d.py`

**Status:** diagnostics / check.

**Responsibility:**  
Reads key-value CSV files produced by FEM3D and verifies / compares summary quantities.

It is an output check, not part of the solve.

**Natural future placement:**

```text
tools/fem3d/check_results.py
```

or:

```text
tests/fem3d/
```

## 5.4 `check_fem3d_jacobian.py`

**Status:** FEM3D geometric diagnostics.

**Responsibility:**  
Rebuilds the mesh using:

```text
build_mesh()
```

and checks the determinant of the Jacobian of every `stdBrick` at the `2x2x2` Gauss points.

**Functions:**

```text
shape_derivatives()
jacobian_det()
```

**Checks:**

- minimum `det(J)`;
- maximum `det(J)`;
- points with `det(J) <= 0`;
- minimum volume;
- critical element.

**Importance:**  
This is a much more specific and meaningful geometric check than a simple "mesh created" message: it can identify inverted or degenerate bricks.

**Must not:**  
Enter the normal runtime except as an optional check.

**Natural future placement:**

```text
tools/fem3d/check_jacobian.py
```

# 6. Detailed description - `src/csf/utils`

## 6.1 `csf_cuf.py`

**Status:** API / public façade of the general CSF-CUF layer.

**Responsibility:**  
It does not directly implement most of the logic. It re-exports APIs from specialized modules.

**Material:**

```text
ConstitutiveProvider
IsotropicEGConstitutive
ConstitutiveMatrixTransform
TransformedConstitutiveProvider
condense_constitutive_matrix
condensed_constitutive_coefficient
CondensedCoefficientTransform
ConstitutiveModel
ScalarField
```

**Section:**

```text
CSFSectionProvider
PolygonDomain
SectionProvider
```

**Basis:**

```text
CUFBasis
MaclaurinCUFBasis
QuadrilateralSerendipityCUFBasis
SerendipityLagrangeReferenceBasis
```

**Integration:**

```text
AdaptivePolygonIntegrator
SectionIntegrator
```

**Sectional:**

```text
SectionalCoefficientProvider
```

**Nucleus:**

```text
FundamentalNucleusProvider
JSignature
NucleusBlock
NucleusTerm
NucleusTermDefinition
StrainContribution
```

**Role:**  
It is the compatibility import interface:

```python
from csf.utils.csf_cuf import ...
```

**Advantage:**  
Users do not need to know the internal subdivision.

**Caution:**  
If the package is reorganized, this façade is useful for maintaining compatibility during the transition.

## 6.2 `csf_cuf_section.py`

**Status:** general core - section representation and CSF adapter.

**Classes:**

```text
PolygonDomain
SectionProvider
CSFSectionProvider
```

**`PolygonDomain`:**  
Represents a polygonal domain of the section.

**`SectionProvider`:**  
Abstract API for obtaining:

- longitudinal domain;
- domains at a given `x`;
- a single domain;
- number of domains.

**`CSFSectionProvider`:**  
Adapts `ContinuousSectionField` to the solver's generic API.

**Role:**  
It is the fundamental boundary between:

```text
"how CSF stores/interpolates the section"
```

and:

```text
"how the solver requests the section"
```

**No assumptions about:**

- I-sections;
- rectangles;
- a fixed number of polygons;
- prismatic sections.

**Natural placement:**  
This is true core functionality and should live in a stable package, not in a generic `utils` directory.

## 6.3 `csf_cuf_basis.py`

**Status:** general core - CUF transverse-basis API and implementations.

**Classes:**

```text
CUFBasis
MaclaurinCUFBasis
SerendipityLagrangeReferenceBasis
QuadrilateralSerendipityCUFBasis
```

**`CUFBasis`:**  
Abstract contract:

- `size`;
- `value(tau,y,z)`;
- `derivative(...)`.

**`MaclaurinCUFBasis`:**  
Complete unscaled polynomial basis.

**`SerendipityLagrangeReferenceBasis`:**  
Lagrange / serendipity basis on a reference domain.

**`QuadrilateralSerendipityCUFBasis`:**  
Maps the reference basis onto a physical quadrilateral.

**Role:**  
Allows the nucleus and sectional integration to remain independent of the specific family of `F_tau`.

**Difference from `csf_cuf_numerics.py`:**  
The current runtime uses `ScaledMaclaurinBasis` defined in `csf_cuf_numerics.py`, not `MaclaurinCUFBasis` from this file.

This distinction should be made explicit during reorganization:

- general API;
- general implementations;
- optimized/scaled implementation used in production.

## 6.4 `csf_cuf_integration.py`

**Status:** general core - transverse integration.

**Classes:**

```text
SectionIntegrator
AdaptivePolygonIntegrator
```

**`SectionIntegrator`:**  
Abstract integration API.

**`AdaptivePolygonIntegrator`:**  
Adaptive integration over the polygon through `scipy.integrate`:

- `integrate()`;
- `integrate_vector()`;
- polygon-domain slicing.

**Role:**  
Provides a generic and robust integration strategy.

**Difference from the runtime:**  
The current engine uses:

```text
FixedGaussPolygonIntegrator
```

from:

```text
csf_cuf_numerics.py
```

Therefore, `AdaptivePolygonIntegrator` is currently the API/reference/general implementation, while `FixedGaussPolygonIntegrator` is the implementation chosen for performance and order control.

**Future placement:**  
Both should probably live under the same `integration` namespace, with clearly named strategies.

## 6.5 `csf_cuf_material.py`

**Status:** general core - constitutive layer.

**Contents:**

```text
ConstitutiveProvider
ConstitutiveModel
IsotropicEGConstitutive
ConstitutiveMatrixTransform
TransformedConstitutiveProvider
CondensedCoefficientTransform
condense_constitutive_matrix()
condensed_constitutive_coefficient()
```

**Responsibility:**  
Defines:

```text
C^k(x,y,z)
```

and constitutive transformations required by a particular theory, without tying them to a specific geometry.

**`IsotropicEGConstitutive`:**  
Builds the isotropic elastic matrix from fields `E` and `G / nu`.

**Transformation layer:**  
This is where a general constitutive transformation or condensation belongs, not inside a benchmark and not inside the CUF nucleus.

**Architectural importance:**  
The material / geometry separation is essential:

- `csf_cuf_section.py` describes where integration takes place;
- `csf_cuf_material.py` describes the constitutive tensor;
- `csf_cuf_sectional.py` combines them through `J`.

**Natural placement:**

```text
src/csf_cuf/core/material.py
```

## 6.6 `csf_cuf_sectional.py`

**Status:** central core - CSF-CUF sectional coupling.  
This is one of the most important files in the architecture.

**Class:**

```text
SectionalCoefficientProvider
```

**Responsibility:**  
Computes the generalized coefficients:

```text
Omega^k(x), C^k(x,y,z), F_tau(y,z)
    ->
J^{mn,k}_{tau,phi s,xi}(x)
    ->
J^{mn}_{tau,phi s,xi}(x)
```

That is, it integrates products of:

- constitutive component;
- CUF function `tau` or its derivative;
- CUF function `s` or its derivative;

over the current sectional domains.

**Injected dependencies:**

```text
SectionProvider
ConstitutiveProvider
CUFBasis
SectionIntegrator
```

This is a strong separation because the provider does not need to know:

- where the geometry comes from;
- which concrete material law is used;
- which concrete basis is used;
- which concrete integrator is used.

**Important functions / methods:**

```text
J_domain()
J()
J_batch()
_compute_J_matrix_families()
cache_info()
clear_cache()
```

**Optimizations:**

- caching;
- matrix families;
- batching;
- basis evaluation at quadrature points;
- reuse of `J` signatures.

**Performance role:**  
In profiling, this is one of the central cost locations because `J` is queried many times during longitudinal integration and for many CUF pairs.

**Conceptual role:**  
This is the point where the continuous CSF description becomes a mechanical coefficient usable by the CUF nucleus.

**Natural placement:**

```text
src/csf_cuf/core/sectional.py
```

## 6.7 `csf_cuf_nucleus.py`

**Status:** CUF mechanical core.

**Main class:**

```text
FundamentalNucleusProvider
```

**Structures:**

```text
StrainContribution
JSignature
NucleusTermDefinition
NucleusTerm
NucleusBlock
```

**Responsibility:**  
Transforms the sectional coefficient field `J(x)` into terms of the CUF fundamental nucleus in weak form.

**Physical part:**  
Uses the full 3D small-strain kinematics in Voigt order:

```text
xx, yy, zz, yz, xz, xy
```

**Separation:**  
The `x`-independent structural definitions are separated from the numerical evaluation of `J(x)`. This allows the longitudinal solver to retain variation along `x` inside FE quadrature.

**Does not contain:**

- prismatic-section assumptions;
- I-section assumptions;
- mandatory isotropic material;
- Carrera benchmark data;
- loads;
- boundary conditions;
- longitudinal discretization.

**Role:**  
It is the actual mechanical consumer of `J(x)`.

**Natural placement:**

```text
src/csf_cuf/core/nucleus.py
```

## 6.8 `csf_cuf_solver.py`

**Status:** historical / initial verification driver.  
It is **not** the current runtime solver.

**File docstring:**

```text
"Initial CSF-CUF solver / verification driver."
```

**Original responsibility:**

- read CSF YAML;
- create `ContinuousSectionField`;
- verify the constitutive provider;
- verify the prismatic Carrera-Giunta section at `x=0, L/2, L`.

**Contents:**

```text
ConstitutiveVerificationResult
SectionVerificationResult
isotropic_reference_coefficients()
carrera_giunta_E_field()
carrera_giunta_G_field()
run_constitutive_verification()
run_section_verification()
```

**Character:**  
It contains specific references to the initial rectangular benchmark and is not the general solver that now runs through:

```text
run_csf_cuf.py -> csf_cuf_engine.py
```

**During reorganization:**  
It should not remain among active core modules with such a generic name. Possible destinations:

```text
tests/legacy/csf_cuf_initial_verification.py
```

or:

```text
examples/validation/early_bridge_check.py
```

The name `csf_cuf_solver.py` is now misleading because the actual solver is elsewhere.

## 6.9 `csf_create_cone.py`

**Status:** CSF utility, not CUF core.

**Review note:**  
This file appears in the `src/csf/utils` directory listing but was **not** contained in the two source packages supplied for this review. For correctness, details of its internal functions are therefore not invented.

**Safe classification:**  
From its name and placement, it is a CSF geometry-creation utility for sections/cones and is not part of the CUF runtime chain described above.

**During reorganization:**  
It should remain separate from the CUF package, presumably within a family of CSF geometry-generation utilities.

A complete internal description of this individual file requires the actual source.

# 7. Logical dependencies between modules

The simplified CUF runtime graph is:

```text
run_csf_cuf
    |
    +--> csf_cuf_case
    |
    +--> csf_cuf_csf_bridge
    |       |
    |       +--> csf.io.csf_reader
    |       +--> csf_cuf_section
    |       +--> csf_cuf_material
    |
    +--> csf_cuf_problem_carrera_torsion
    |
    +--> csf_cuf_engine
            |
            +--> csf_cuf_basis_plugins
            |       |
            |       +--> scaled_maclaurin
            |               |
            |               +--> csf_cuf_numerics.ScaledMaclaurinBasis
            |
            +--> csf_cuf_numerics
            |       +--> FixedGaussPolygonIntegrator
            |
            +--> csf_cuf_sectional
            |
            +--> csf_cuf_nucleus
            |
            +--> csf_cuf_longitudinal
            |
            +--> csf_cuf_element
            |
            +--> csf_cuf_assembly
            |
            +--> csf_cuf_point_bc
            |
            +--> csf_cuf_linear_constraint
            |
            +--> csf_cuf_augmented_solver
            |
            +--> CSFCUFSolution
    |
    +--> csf_cuf_post
```

The FEM3D graph is:

```text
run_csf_fem3d
    |
    +--> csf_fem3d
            |
            +--> CSF reader / model
            +--> stdBrick mesh
            +--> material states
            +--> nodal loads
            +--> OpenSees
            +--> recovery
            +--> diagnostics/report
```

# 8. Redundant, historical, or poorly named files

## A. Files containing `old`

They should not be considered active sources, as requested.

## B. `csf_cuf_engine_before_OPT09.py`

This is a development snapshot. It should not remain in the future active source tree.

## C. `csf_cuf_solver.py`

Its name suggests "current solver", but it is actually an initial verification driver. It should be moved outside the core.

## D. `csf_cuf_problem_carrera_torsion.py`

The name no longer represents its contents because it also includes Table 9 bending. It should be split or renamed.

## E. `csf_cuf_numerics.py` vs `csf_cuf_basis.py` / `csf_cuf_integration.py`

They are not simple duplicates, but the distinction is not visible from the current structure:

- API / generic implementations under `src/csf/utils`;
- optimized implementations used by the runtime in the working directory.

This relationship should be made explicit during reorganization.

## F. `csf_fem3d.py`

It is functionally correct but combines too many responsibilities in a single file. It is the main candidate for future decomposition.

# 9. Files potentially omitted from the list

Relative to the initial review based on the two source packages, this revision introduces one new runtime module:

1. **`csf_cuf_basis_plugins.py`**  
   This was a deliberate addition after the initial review. It connects `case.cuf.basis` to the concrete `CUFBasis` and moves the knowledge specific to the `scaled_maclaurin` family out of the engine.

2. No other active runtime Python files appeared to be missing from the two original packages once files containing `old` in their names were excluded.

3. An auxiliary file developed during validation is present:

```text
analyse_csf_cuf_kkt_diagnostics.py
```

This is not a solver runtime module, but it is important to preserve it as a diagnostic tool for the `N=21/N=30` KKT checkpoints.

4. Also present:

```text
README_KKT_DIAGNOSTICS.txt
```

It is not Python, so it does not appear in the `.py` list.

5. `csf_cuf_engine_before_OPT09.py` is already in the list and is a snapshot, not a module required for the final distribution.

6. `csf_create_cone.py` is in the list but was not included in the supplied packages; it is therefore the only listed file for which the initial review could not directly verify the internal implementation.

# 10. First proposal for logical placement - without moving files yet

This is **not** a request for immediate refactoring. It is a map for a later reorganization.

A coherent structure could be:

```text
src/
└── csf/
    ├── ... existing CSF core ...
    │
    ├── cuf/
    │   ├── __init__.py
    │   │
    │   ├── core/
    │   │   ├── section.py
    │   │   ├── material.py
    │   │   ├── basis.py
    │   │   ├── integration.py
    │   │   ├── sectional.py
    │   │   └── nucleus.py
    │   │
    │   ├── basis_plugins.py
    │   │
    │   ├── numerics/
    │   │   ├── scaled_maclaurin.py
    │   │   └── polygon_gauss.py
    │   │
    │   ├── fe/
    │   │   ├── longitudinal.py
    │   │   ├── element.py
    │   │   └── assembly.py
    │   │
    │   ├── constraints/
    │   │   ├── pointwise.py
    │   │   └── kkt.py
    │   │
    │   ├── solver/
    │   │   ├── engine.py
    │   │   └── augmented.py
    │   │
    │   ├── problem/
    │   │   ├── base.py
    │   │   └── carrera/
    │   │       ├── table9.py
    │   │       └── table10.py
    │   │
    │   ├── recovery/
    │   │   └── fields.py
    │   │
    │   ├── post/
    │   │   ├── extrema.py
    │   │   └── carrera.py
    │   │
    │   ├── config/
    │   │   └── case.py
    │   │
    │   └── adapters/
    │       └── csf_model.py
    │
    └── fem3d/
        ├── model.py
        ├── mesh.py
        ├── loads.py
        ├── opensees_solver.py
        └── post.py

scripts/
    run_csf_cuf.py
    run_csf_fem3d.py

tools/
    analyse_csf_cuf_kkt_diagnostics.py
    fem3d/
        check_results.py
        check_jacobian.py

tests/
    smoke/
        startup_check.py
    legacy/
        csf_cuf_initial_verification.py

examples/
    carrera_giunta_2010/
        ...
```

This structure follows a simple principle:

- `core` = general formulation and coupling;
- `basis_plugins` = selection/dispatch of basis families;
- `numerics` = concrete/optimized numerical implementations;
- `fe` = longitudinal discretization and assembly;
- `constraints` = BCs and KKT;
- `solver` = algebraic orchestration;
- `problem` = specific loads/constraints;
- `post` = result extraction;
- `scripts` = entry points only;
- `tools` = diagnostics;
- `examples` = reproducible cases;
- `fem3d` = independent baseline.

# 11. Which files are truly "core"

## Conceptual CSF-CUF core

```text
csf_cuf_section.py
csf_cuf_material.py
csf_cuf_basis.py
csf_cuf_integration.py
csf_cuf_sectional.py
csf_cuf_nucleus.py
```

## General solver core

```text
csf_cuf_basis_plugins.py
csf_cuf_numerics.py
csf_cuf_longitudinal.py
csf_cuf_element.py
csf_cuf_assembly.py
csf_cuf_point_bc.py
csf_cuf_linear_constraint.py
csf_cuf_augmented_solver.py
csf_cuf_engine.py
csf_cuf_recovery.py
```

## Model interface

```text
csf_cuf_csf_bridge.py
```

## Configuration

```text
csf_cuf_case.py
csf_cuf_problem.py
```

## Plugin / benchmark

```text
csf_cuf_problem_carrera_torsion.py
csf_cuf_post.py   # Carrera-specific part
```

## Entry point

```text
run_csf_cuf.py
```

## Independent baseline

```text
csf_fem3d.py
run_csf_fem3d.py
```

## Diagnostics

```text
check_fem3d.py
check_fem3d_jacobian.py
startup_check.py
analyse_csf_cuf_kkt_diagnostics.py
```

## Historical / to be removed from the active source tree

```text
files containing "old"
csf_cuf_engine_before_OPT09.py
csf_cuf_solver.py   # if retained, reclassify as early verification
```

# 12. Architectural points to preserve during reorganization

## 1. External geometry

No solver module should start generating a specific section. Geometry remains in the CSF model.

## 2. Longitudinal domain from CSF

The physical length must not be duplicated in FE modules.

## 3. Material separated from geometry

`SectionProvider` and `ConstitutiveProvider` must remain distinct dependencies.

## 4. `J(x)` as the sectional interface

`SectionalCoefficientProvider` is the natural coupling point:

```text
geometry + C + F_tau -> J(x)
```

## 5. Generic nucleus

`FundamentalNucleusProvider` must not contain benchmark-specific, CUF-order-specific, or geometry-specific `if` statements.

## 6. Transverse bases as plugins

The engine must not know the concrete `F_tau` family. The case selects a basis by name, the registry builds a concrete `CUFBasis`, and the rest of the chain consumes only the common contract. Basis-specific numerical requirements, such as the minimum Gauss order for `scaled_maclaurin`, must remain associated with the plugin rather than the general orchestrator.

## 7. Physical problems as plugins

Table 9 / Table 10 must define loads and constraints, not geometry.

## 8. Post-processing outside the solver

The solver should return the solved physical field; the report is a consumer of that field.

## 9. Diagnostics outside the core

KKT checkpoints and Jacobian checks are essential, but they must not contaminate the formulation layer.

## 10. One active implementation per concept

Copies named `old`, `before_OPT`, `v2`, and so on should not remain in the final runtime directory. History belongs in Git, not in module names.

## 11. Refactoring with invariant physics

Reorganization should proceed as:

```text
move / rename / import
    ->
smoke test
    ->
prismatic benchmark
    ->
PASS
```

before any new numerical modification is introduced.

# 13. Conclusion

The current architecture, although still distributed between the working directory and `src/csf/utils`, is already substantially layered.

The conceptual center is:

```text
CSF model
   ->
SectionProvider + ConstitutiveProvider

case.cuf.basis
   ->
basis plugin registry
   ->
concrete CUFBasis

SectionProvider + ConstitutiveProvider + CUFBasis
   ->
SectionalCoefficientProvider J(x)
   ->
FundamentalNucleusProvider
   ->
longitudinal FE
   ->
assembly
   ->
constraints
   ->
augmented solver
   ->
u(x,y,z)
```

The primary need of the reorganization is not to change the model, but to make this structure **visible in the filesystem**.

The most urgent points to clarify in the future layout are:

- separate core, numerics, solver, and problem plugins;
- move snapshots and historical files out of the active source tree;
- keep the distinction between generic `CUFBasis`, the basis plugin registry, and concrete numerical implementations explicit;
- clarify the relationship between `csf_cuf_numerics.py` and the generic basis/integration implementations;
- rename/split `csf_cuf_problem_carrera_torsion.py`;
- reclassify `csf_cuf_solver.py` as historical verification;
- decompose `csf_fem3d.py` when the FEM3D reorganization is addressed;
- keep `run_csf_cuf.py` and `run_csf_fem3d.py` as thin entry points.

For the source files actually contained in the supplied packages, no other active runtime Python modules appear to be missing from the list once the `old` files are excluded. The only important auxiliary file outside the runtime list is `analyse_csf_cuf_kkt_diagnostics.py`, which should be preserved as a diagnostic tool.

## Revision 2 - final note

The introduced separation does not change the `scaled_maclaurin` kinematic space or its numerical implementation. It changes only runtime dispatch: Taylor/Maclaurin remains available as the current plugin, but it is no longer knowledge embedded directly inside `csf_cuf_engine.py`.
