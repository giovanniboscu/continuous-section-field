# Geometric / Material Model

**Status:** first draft  
**Scope:** preliminary description of the geometric and material model underlying the original Balduzzi 2016 planar formulation, to be refined as the project evolves.  
**Out of scope:** load model, boundary conditions, reduced solver coefficients, and numerical solution strategy.

## 1. Purpose of this document

This document identifies the **geometric / material model** adopted upstream of the Balduzzi-based solver.

Its role is to describe the structural member itself, independently of any specific load case or support condition. The aim is not yet to solve the beam problem, but to define the geometric and material data required before the formulation can be reduced to solver-ready input.

The present version is based on a first re-reading of Balduzzi et al. (2016) and should be considered an initial technical synthesis, not a final specification.

## 2. Reference formulation


At the level of the original 2016 planar formulation, the geometric model is defined on a longitudinal domain:

`x in [0, l]`

where `l` is the beam length.

The beam geometry is described through the following primary functions:

- `c(x)` = prescribed geometric center-line of the 2D beam domain
- `h(x)` = cross-section height, with `h(x) > 0`

From these, the lower and upper section boundaries are defined as:

- `h_l(x) = c(x) - h(x) / 2`
- `h_u(x) = c(x) + h(x) / 2`

At each axial coordinate `x`, the cross-section is therefore reduced to the vertical interval:

`A(x) = { y : y in [h_l(x), h_u(x)] }`

This means that, in the original formulation, the section is not described as a general planar domain, but as a segment bounded by an upper and a lower geometric limit.

The geometric model therefore consists of:

- beam length `l`
- axial coordinate `x`
- center-line `c(x)`
- section height `h(x)`
- lower boundary `h_l(x)`
- upper boundary `h_u(x)`

The first derivatives of the geometric functions are also part of the geometric description whenever required by the formulation. In particular, the slopes of the section boundaries are relevant quantities in the original model.

For this reason, the following derivatives must be considered part of the geometric input whenever the formulation requires them:

- `c'(x)`
- `h'(x)`
- equivalently, `h_l'(x)` and `h_u'(x)`

In the original 2016 model, `c(x)` is introduced as a prescribed geometric function. It is not defined at this stage as a centroid extracted from a more general sectional description.

| Quantity | Role | Definition |
|---|---|---|
| `c(x)` | Beam center-line | Prescribed geometric center-line of the 2D beam domain |
| `h(x)` | Section height | Cross-section height at axial coordinate `x`, with `h(x) > 0` |
| `h_l(x)` | Lower boundary | Lower geometric limit of the reduced cross-section, defined as `h_l(x) = c(x) - h(x)/2` |
| `h_u(x)` | Upper boundary | Upper geometric limit of the reduced cross-section, defined as `h_u(x) = c(x) + h(x)/2` |
| `A(x)` | Reduced cross-section | Vertical cross-section associated with the axial coordinate `x`, defined as `A(x) = { y : y in [h_l(x), h_u(x)] }` |


### Independent material quantities

| Quantity | Role | Definition |
|---|---|---|
| `E` | Young's modulus | Elastic modulus of the homogeneous isotropic material |
| `G` | Shear modulus | Shear modulus of the homogeneous isotropic material |

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
