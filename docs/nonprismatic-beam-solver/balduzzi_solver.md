# Balduzzi Solver

**Status:** first draft  
**Scope:** simplified description of the reduced beam solver corresponding to the original Balduzzi 2016 planar formulation, written from a numerical point of view.  
## 1. Purpose

This document describes the solver layer that acts on the reduced model input data defined in:

- `geometric_material_model.md`
- `load_boundary_condition_model.md`
- `reduced_model_input_data.md`

The goal of this document is not to reproduce the full analytical derivation of the paper, but to identify the quantities, relations, and equation structure that must be implemented in a numerical solver.

The solver is formulated independently of the upstream geometry source, but it is intended to remain directly usable within a future CSF-based numerical workflow.

## 2. Solver perspective

From a numerical point of view, the Balduzzi 2016 model can be read as a **1D beam problem with variable coefficients** along the longitudinal coordinate `x`.

The solver does not operate on the full 2D continuum directly. Instead, it uses reduced quantities that already summarize:

- geometry;
- material behavior;
- reduced loads;
- end boundary conditions.

The numerical task is therefore to solve a reduced beam problem along `x in [0, l]`.

## 3. Unknowns of the reduced problem

The model uses six beam variables:

| Quantity | Role |
|---|---|
| `u(x)` | axial displacement |
| `v(x)` | vertical displacement |
| `phi(x)` | cross-section rotation |
| `H(x)` | axial resultant force |
| `M(x)` | bending moment resultant |
| `V(x)` | shear resultant force |

From a numerical viewpoint, these six quantities form the natural state of the reduced problem.

## 4. Structure of the formulation

The solver is built from three ingredients:

### 4.1 Kinematics

The model adopts a Timoshenko-like beam kinematics. The reduced generalized deformations are:

- axial deformation
- curvature
- shear deformation

A key feature of the non-prismatic formulation is that the center-line slope `c'(x)` enters the compatibility relations. This creates a coupling that is absent in the simplest prismatic case.

### 4.2 Equilibrium

The model introduces three generalized internal resultants:

- `H(x)`
- `M(x)`
- `V(x)`

and balances them against the reduced loads:

- `q(x)`
- `m(x)`
- `p(x)`

At the reduced level, the equilibrium equations are ordinary differential equations along `x`.

### 4.3 Constitutive closure

The generalized deformations are not related to the generalized stresses through the standard uncoupled prismatic Timoshenko relations.

Instead, in the Balduzzi formulation, each generalized deformation depends in general on all three generalized stresses. This means that:

- axial response,
- bending response,
- shear response

are coupled through position-dependent constitutive coefficients.

For numerical implementation, this is the key point: the solver must evaluate a local constitutive operator along `x`, not only scalar stiffness terms such as `EA(x)`, `EI(x)`, or `kGA(x)` taken independently.

## 5. Numerical interpretation

From a numerical perspective, the solver can be viewed as an explicit first-order system in the six beam variables:

- `u(x)`
- `v(x)`
- `phi(x)`
- `H(x)`
- `M(x)`
- `V(x)`

This is one of the main practical strengths of the Balduzzi 2016 formulation: the problem is naturally organized as a system of six first-order ODEs with variable coefficients.

This makes the model suitable for a direct numerical implementation based on:

- function evaluation along `x`;
- numerical differentiation where required upstream;
- numerical integration of the reduced beam system;
- enforcement of boundary conditions at `x = 0` and `x = l`.

## 6. What the solver must receive

At implementation level, the solver must receive:

### Geometry
- `c(x)`
- `h(x)`
- `c'(x)`
- `h'(x)`

### Material
- `E`
- `G`

### Loads
- `q(x)`
- `m(x)`
- `p(x)`

### Boundary conditions
- end conditions on suitable subsets of:
  - `u`
  - `v`
  - `phi`
  - `H`
  - `M`
  - `V`

These quantities are assumed to be already available in reduced form before the solver starts.

## 7. Solver workflow

A practical numerical reading of the Balduzzi solver is the following:

1. define the reduced input functions and parameters;
2. evaluate the local geometric and constitutive quantities along `x`;
3. assemble the reduced first-order beam system;
4. apply the end boundary conditions;
5. solve for the six beam unknowns along the interval `x in [0, l]`.

## 8. What is intentionally not developed here

This document does not yet define:

- the specific numerical discretization method;
- the representation of the variable coefficients in code;
- the numerical treatment of derivatives and quadratures;
- the algorithm used to enforce boundary conditions;
- the software interface with a future CSF-based geometry source.

These belong to later documents.

## 9. Interpretation

The purpose of this solver document is to keep the focus on the structure of the reduced beam problem.

In this project, the Balduzzi solver is understood as:

- a reduced 1D structural model;
- numerically driven rather than symbolically developed;
- fed by reduced geometric, material, load, and boundary-condition data;
- implemented as a variable-coefficient first-order ODE system;
- directly compatible with future use in a CSF-based workflow.

## Main reference

Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017
