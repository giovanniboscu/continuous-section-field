# Reduced Model Input Data

**Status:** first draft  
**Scope:** definition of the reduced input data required to drive the original Balduzzi 2016 beam formulation, after the geometric/material model and the load / boundary-condition model have been specified.  


## 1. Purpose

This document defines the **reduced model input data** required by the Balduzzi 2016 beam formulation.

These quantities are not the full upstream descriptions of geometry, material, loads, and boundary conditions. They are the reduced quantities that actually enter the beam model once the previous modeling steps have been completed.

In other words:

- the **geometric / material model** defines the structural member;
- the **load / boundary-condition model** defines how that member is loaded and constrained;
- the **reduced model input data** collect only the quantities required to drive the beam formulation.

## 2. Position in the document flow

This document sits between:

- `geometric_material_model.md`
- `load_boundary_condition_model.md`

and the later document describing the Balduzzi solver itself.

Its role is to identify the exact interface between the upstream model definition and the downstream numerical solution.

## 3. Reduced input structure

For the original 2016 formulation, the reduced model input data are grouped into four blocks:

1. reduced geometric quantities;
2. reduced material quantities;
3. reduced load quantities;
4. reduced boundary-condition data.

## 4. Reduced geometric quantities

The beam formulation is driven by the following geometric functions:

| Quantity | Role | Type |
|---|---|---|
| `c(x)` | Beam center-line of the reduced 2D model | independent |
| `h(x)` | Cross-section height | independent |
| `c'(x)` | Derivative of the beam center-line | derived |
| `h'(x)` | Derivative of the cross-section height | derived |

At the reduced-model level, `c(x)` and `h(x)` are treated as input functions of the formulation.

Their first derivatives are not independent inputs, but derived geometric quantities required by the model.

## 5. Reduced material quantities

The original 2016 formulation assumes a homogeneous, isotropic, linear-elastic material.

The reduced material input is therefore:

| Quantity | Role |
|---|---|
| `E` | Young's modulus |
| `G` | Shear modulus |

At this level, both are treated as model parameters.

## 6. Reduced load quantities

The reduced beam formulation uses the following resulting loads along the longitudinal axis:

| Quantity | Role |
|---|---|
| `q(x)` | Horizontal resulting load |
| `m(x)` | Bending resulting load |
| `p(x)` | Vertical resulting load |

These quantities are obtained from the distributed body load over the reduced cross-section:

- `q(x) = ∫_{A(x)} f_x(x,y) dy`
- `m(x) = -∫_{A(x)} y f_x(x,y) dy`
- `p(x) = ∫_{A(x)} f_y(x,y) dy`

At the reduced-model level, `q(x)`, `m(x)`, and `p(x)` are treated as the load input functions of the beam formulation.

## 7. Reduced boundary-condition data

The reduced beam problem must also include boundary conditions expressed at the beam ends.

At this level, the relevant boundary-condition data are not the original 2D boundary partition or the full prescribed displacement field on `∂Omega_s`, but the end conditions required by the reduced beam problem.

These conditions are to be expressed at `x = 0` and/or `x = l` in terms of beam variables.

For the original formulation, the relevant beam variables are:

- `u(x)`
- `phi(x)`
- `v(x)`
- `H(x)`
- `M(x)`
- `V(x)`

Accordingly, the reduced boundary-condition input consists of prescribed conditions on suitable subsets of these quantities at the beam ends.

Examples include:

- kinematic conditions, such as prescribed `u`, `v`, or `phi`;
- static conditions, such as prescribed `H`, `M`, or `V`.

The detailed numerical enforcement of these conditions belongs to the solver document, not to the present one.

## 8. Summary table

| Block | Reduced input data |
|---|---|
| Geometry | `c(x)`, `h(x)`, `c'(x)`, `h'(x)` |
| Material | `E`, `G` |
| Loads | `q(x)`, `m(x)`, `p(x)` |
| Boundary conditions | end conditions on `u`, `phi`, `v`, `H`, `M`, `V` |

## 9. Interpretation

This reduced input set is the first level at which the problem becomes solver-ready.

It is already detached from the full upstream descriptions of the 2D domain, distributed loads, and boundary partition, but it is still independent of any specific numerical implementation.

For this reason, it defines the natural interface between:

- model definition;
- beam formulation;
- solver implementation.

## Main reference

Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017
