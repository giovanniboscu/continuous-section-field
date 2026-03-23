# Load / Boundary-Condition Model

**Status:** first draft  
**Scope:** preliminary description of the load model and boundary-condition model underlying the original Balduzzi 2016 planar formulation.  
## 1. Purpose

This document defines the external actions and boundary conditions applied to the reduced 2D beam domain in the original Balduzzi 2016 formulation.

Its purpose is to describe how the structural member is loaded and constrained, independently of the later numerical solution procedure.

## 2. Boundary partition

The boundary of the reduced 2D domain is divided into:

- `∂Omega_s` = displacement-constrained boundary
- `∂Omega_t` = loaded boundary

The original formulation assumes that the upper and lower boundaries of the beam belong to the loaded part of the boundary.

At least one of the two end sections must belong to the displacement-constrained boundary in order to ensure uniqueness of the solution.

## 3. Prescribed boundary conditions

The boundary conditions are introduced through a prescribed displacement field on the constrained part of the boundary:

- `s̄` on `∂Omega_s`

At this stage, the load / boundary-condition model does not yet express end conditions in terms of beam unknowns such as generalized displacements or internal resultants. It remains at the level of the original reduced 2D continuum problem.

## 4. Applied loads

The original formulation introduces two classes of external actions:

- a body load distributed over the reduced 2D domain:
  - `f : Omega -> R^2`
- a boundary traction applied on the loaded boundary:
  - `t : ∂Omega_t -> R^2`

In the basic 2016 model, the boundary traction along the upper and lower boundaries is assumed to be zero.

This is a specific assumption of the base formulation and is not a general requirement for all possible extensions.

## 5. Reduced beam loads

The beam formulation introduces the following resulting load quantities along the longitudinal axis:

- `q(x)` = horizontal resulting load
- `m(x)` = bending resulting load
- `p(x)` = vertical resulting load

These are obtained from the distributed body load over the reduced cross-section at each axial coordinate `x`:

- `q(x) = ∫_{A(x)} f_x(x,y) dy`
- `m(x) = -∫_{A(x)} y f_x(x,y) dy`
- `p(x) = ∫_{A(x)} f_y(x,y) dy`

These quantities already belong to the reduced beam formulation. They are not the full external actions of the original 2D problem, but their projection onto the beam model.

## 6. Scope of this document

At the current stage, the load / boundary-condition model includes:

- the partition of the boundary into constrained and loaded parts;
- the prescribed displacement field on the constrained boundary;
- the body load over the reduced 2D domain;
- the boundary traction on the loaded boundary;
- the resulting reduced beam loads `q(x)`, `m(x)`, and `p(x)`.

The explicit use of generalized beam unknowns and the numerical enforcement of boundary conditions belong to later documents.

## Main reference

Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017
