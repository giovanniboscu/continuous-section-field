# Reduced Model Input Data

**Status:** first draft  
**Scope:** definition of the reduced input data required to drive the original Balduzzi 2016 beam formulation.  
**Out of scope:** numerical discretization, solver implementation, and future generalization to richer sectional geometries.

## 1. Purpose

This document defines the reduced quantities that enter the Balduzzi beam formulation after the upstream model definition has been completed.

It follows:

- `geometric_material_model.md`
- `load_boundary_condition_model.md`

and precedes the solver document.

## 2. Reduced input blocks

The reduced model input data are grouped into four blocks:

1. geometry
2. material
3. loads
4. boundary conditions

## 3. Geometry

The reduced geometric input of the original 2016 formulation is:

| Quantity | Role | Type |
|---|---|---|
| `c(x)` | Beam center-line of the reduced 2D model | independent |
| `h(x)` | Cross-section height | independent |
| `c'(x)` | Derivative of the beam center-line | derived |
| `h'(x)` | Derivative of the cross-section height | derived |

## 4. Material

The reduced material input is:

| Quantity | Role |
|---|---|
| `E` | Young's modulus |
| `G` | Shear modulus |

## 5. Loads

The reduced beam formulation uses the following load quantities:

| Quantity | Role |
|---|---|
| `q(x)` | Horizontal resulting load |
| `m(x)` | Bending resulting load |
| `p(x)` | Vertical resulting load |

These are the reduced load functions introduced in `load_boundary_condition_model.md`.

## 6. Boundary conditions

The reduced beam problem must include boundary conditions at the beam ends, i.e. at `x = 0` and/or `x = l`.

At the reduced-model level, boundary conditions are no longer expressed on the full 2D boundary `∂Omega_s`, but on the beam variables of the 1D formulation.

The relevant beam variables are:

| Quantity | Role | Type of boundary condition |
|---|---|---|
| `u(x)` | Axial displacement | kinematic |
| `v(x)` | Vertical displacement | kinematic |
| `phi(x)` | Cross-section rotation | kinematic |
| `H(x)` | Axial resultant force | static |
| `M(x)` | Bending moment resultant | static |
| `V(x)` | Shear resultant force | static |

Accordingly, the reduced boundary-condition input consists of prescribed end conditions on suitable subsets of these variables at `x = 0` and/or `x = l`.

### Kinematic end conditions

These prescribe the beam motion at an end:

- prescribed `u`
- prescribed `v`
- prescribed `phi`

Examples:

- `u(0) = 0`
- `v(0) = 0`
- `phi(0) = 0`

### Static end conditions

These prescribe the internal resultants at an end:

- prescribed `H`
- prescribed `M`
- prescribed `V`

Examples:

- `H(l) = 0`
- `M(l) = 0`
- `V(l) = 0`

### Interpretation

A complete reduced beam problem is obtained by assigning a consistent set of end conditions on these variables.

Typical examples are:

- **clamped end**: prescribed `u`, `v`, `phi`
- **free end**: prescribed `H`, `M`, `V`
- **mixed case**: combination of kinematic and static conditions, depending on the structural problem

At this stage, the document only identifies the variables on which reduced boundary conditions are imposed. The detailed enforcement of those conditions belongs to the solver document.



## 7. Summary table

| Block | Reduced input data |
|---|---|
| Geometry | `c(x)`, `h(x)`, `c'(x)`, `h'(x)` |
| Material | `E`, `G` |
| Loads | `q(x)`, `m(x)`, `p(x)` |
| Boundary conditions | end conditions on `u`, `phi`, `v`, `H`, `M`, `V` |

## Main reference

Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017
