# Geometric / Material Model

**Status:** first draft  
**Scope:** preliminary description of the geometric and material model underlying the original Balduzzi 2016 planar formulation, to be refined as the project evolves.  
**Out of scope:** load model, boundary conditions, reduced solver coefficients, and numerical solution strategy.

## 1. Purpose of this document

This document identifies the **geometric / material model** adopted upstream of the Balduzzi-based solver.

Its role is to describe the structural member itself, independently of any specific load case or support condition. The aim is not yet to solve the beam problem, but to define the geometric and material data required before the formulation can be reduced to solver-ready input.

The present version is based on a first re-reading of Balduzzi et al. (2016) and should be considered an initial technical synthesis, not a final specification.

## 2. Reference formulation

The starting point is the planar non-prismatic beam model introduced by:

> Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017

The 2016 formulation addresses a **2D non-prismatic beam** under:
- small displacements;
- plane stress state;
- homogeneous, isotropic, linear-elastic material.

## 3. Geometric description in the original 2016 model

In the original Balduzzi 2016 formulation, the beam is described on a longitudinal axis:

`L = { x in [0, l] }`

The geometry is defined through two primary scalar functions:

- `c(x)` = beam center-line
- `h(x)` = cross-section height, with `h(x) > 0`

The lower and upper section limits are then defined as:

- `h_l(x) = c(x) - h(x) / 2`
- `h_u(x) = c(x) + h(x) / 2`

At each axial coordinate `x`, the cross-section is therefore reduced to the vertical interval:

`A(x) = { y : y in [h_l(x), h_u(x)] }`

This means that the original model does **not** describe a general 2D section. Instead, it uses a strongly reduced planar geometry in which the section is represented only by its upper and lower boundaries.

### 3.1 Consequence of this choice

The geometric description is simple and effective, but also restrictive.

The quantity `h(x)` is **not** constant along the beam axis in the general non-prismatic case. However, it is the only transverse size descriptor used by the original model. This is one of the reasons why any future extension to non-rectangular or more general sectional geometries should be treated as a separate development.

## 4. Regularity assumptions

The 2016 formulation requires the geometric functions to be sufficiently smooth.

In particular, the first derivatives of the lower and upper boundaries must remain bounded. Equivalently, the first derivatives of `c(x)` and `h(x)` must remain bounded.

This is not a secondary detail. The boundary equilibrium on the lateral surfaces depends explicitly on the slopes of the boundaries, and those slopes affect the internal stress distribution.

### 4.1 Practical meaning

The original formulation is compatible with:
- straight beams with variable height;
- beams with non-horizontal center-line;
- tapered members;
- some curved cases, provided the first derivatives remain bounded.

The paper explicitly notes that this may exclude geometries such as an exact semi-circular beam unless approximations or geometric workarounds are introduced.

## 5. Orientation of the cross-sections

In the adopted formulation, the cross-sections are taken as orthogonal to the **longitudinal axis**, not to the center-line.

This is a deliberate modeling choice and is part of the structure of the original problem definition.

It is important because it affects:
- the definition of the 2D domain;
- the interpretation of `c(x)` and `h(x)`;
- the meaning of the generalized stresses and deformations used later in the beam model.

## 6. Material model in the original 2016 formulation

The 2016 paper assumes that the beam body is made of a material that is:

- homogeneous;
- isotropic;
- linear-elastic.

The corresponding constitutive behavior is represented in the 2D continuum setting before reduction to the beam equations.

At this stage, the geometric / material model therefore requires only the standard elastic constants, typically:

- `E` = Young's modulus
- `G` = shear modulus

If needed, `G` may be derived from `E` and `nu` through the isotropic relation:

`G = E / (2 * (1 + nu))`

For the original 2016 model, these quantities are treated as material constants, not as piecewise-varying fields.

## 7. Separation from later extensions

The present document refers only to the **original homogeneous 2016 formulation**.

A multilayer or materially non-homogeneous extension belongs to a later level of the project. In that case, the geometric / material model is no longer described by a single height function and one homogeneous material, but by multiple interfaces `h_i(x)` and layer-wise material properties. That extension should be documented separately.

## 8. What belongs to the geometric / material model at this stage

The following items belong to the current geometric / material model definition:

### 8.1 Geometry
- beam length `l`
- longitudinal axis `x in [0, l]`
- center-line `c(x)`
- cross-section height `h(x)`
- lower boundary `h_l(x)`
- upper boundary `h_u(x)`
- first derivatives of the geometric functions where required

### 8.2 Material
- homogeneous isotropic linear-elastic behavior
- `E`
- `G`
- optionally `nu`, if `G` is derived rather than prescribed directly

## 9. What does not belong here

The following items do **not** belong to the geometric / material model document:

- distributed loads
- concentrated forces and moments
- support conditions
- boundary conditions
- generalized loads `p(x)`, `q(x)`, `m(x)`
- reduced constitutive coefficients for the solver
- numerical discretization or integration strategy

These belong to later documents in the project flow.

## 10. Immediate next step

The next document should define the **load / boundary-condition model**, still independently from the solver.

Only after both blocks are fixed can the project define the actual **reduced model input data required by the Balduzzi formulation**.

## 11. Open notes for future refinement

This first draft leaves some points intentionally open for later clarification:

- whether the implementation should follow exactly the original `c(x), h(x)` description, or adopt `h_l(x), h_u(x)` as the primary representation;
- how to represent geometric data numerically in a way that preserves the bounded-slope assumptions;
- how far the original geometric description can be pushed before a true reformulation becomes necessary;
- how this document should evolve once the multilayer extension is introduced.

## Main reference

Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017
