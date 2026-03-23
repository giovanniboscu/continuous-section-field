# Geometric / Material Model

**Status:** first draft  
**Scope:** preliminary description of the geometric and material model underlying the original Balduzzi 2016 planar formulation.  
**Out of scope:** load model, boundary conditions, reduced solver coefficients, and numerical solution strategy.

## 1. Purpose

This document defines the geometric and material quantities required to describe the structural member in the original Balduzzi 2016 planar formulation, before introducing loads, boundary conditions, or solver-specific quantities.

## 2. Geometric model

The model is defined on the longitudinal domain:

`x in [0, l]`

where `l` is the beam length.

The independent geometric variables are:

| Quantity | Role | Definition |
|---|---|---|
| `c(x)` | Beam center-line | Prescribed geometric center-line of the 2D beam domain |
| `h(x)` | Section height | Cross-section height at axial coordinate `x`, with `h(x) > 0` |

The dependent geometric variables are:

| Quantity | Role | Definition |
|---|---|---|
| `h_l(x)` | Lower boundary | `h_l(x) = c(x) - h(x)/2` |
| `h_u(x)` | Upper boundary | `h_u(x) = c(x) + h(x)/2` |
| `A(x)` | Reduced cross-section | `A(x) = { y : y in [h_l(x), h_u(x)] }` |

The full reduced 2D beam domain is therefore:

`Omega = { (x, y) : x in [0, l], y in A(x) }`

In the original 2016 model, `c(x)` is introduced as a prescribed geometric function. It is not defined here as a centroid extracted from a more general sectional description.

The cross-sections are taken as orthogonal to the **longitudinal axis**, not to the center-line.

## 3. Material model

The original 2016 formulation assumes a material that is:

- homogeneous
- isotropic
- linear-elastic

The independent material quantities are:

| Quantity | Role | Definition |
|---|---|---|
| `E` | Young's modulus | Elastic modulus of the homogeneous isotropic material |
| `G` | Shear modulus | Shear modulus of the homogeneous isotropic material |

## 4. Geometric regularity assumptions

The formulation assumes that the geometric functions are sufficiently smooth.

In particular, the first derivatives of the section boundaries must remain bounded. Equivalently, the first derivatives of `c(x)` and `h(x)` must remain bounded.

## Main reference

Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017
