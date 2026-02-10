# Section Properties

## Overview

In CSF, all sectional quantities are **derived from geometry** and, optionally, **scaled by weight laws**.  
No sectional property is prescribed directly.

This chapter describes:
- which section properties are computed,
- how they are defined,
- how weights affect their evaluation,
- and how the results should be interpreted.

The focus is on **geometric and homogenized properties**, not on stress or constitutive behavior.

---

## Purely Geometric Quantities

At any longitudinal coordinate \( z \), CSF reconstructs the section geometry
and evaluates standard geometric quantities using exact polygonal formulas.

For each polygon \( k \), the following quantities are computed:

- area `A_k(z)`,
- centroid coordinates `(C_x,k(z), C_y,k(z))`,
- second moments of area `I_x,k(z), I_y,k(z)`,
- product of inertia `I_xy,k(z)`,
- first moment of area `Q_k(z)` (for shear-related evaluations).


These quantities are evaluated with respect to the **local section reference frame**.

---

## Assembly of Section Properties

The section as a whole is obtained by assembling the contributions of all polygons.

For a generic property \( P(z) \), the assembly rule is:

`P(z) = sum_k [ w_k(z) * P_k(z) ]`

where:
- ` P_k(z) ` is the geometric contribution of polygon ` k `,
` w_k(z) ` is its longitudinal weight.

This formulation applies uniformly to all area-based sectional quantities.

---

## Section Area

The effective (weighted) cross-sectional area is defined as:

`A(z) = sum_k [ w_k(z) * A_k(z) ]`


If all weights are equal to unity,` A(z)` coincides with the geometric area.

Zero-weight polygons contribute no area, representing voids.

---

## Section Centroid

The centroid of the weighted section is computed as:

`C_x(z) = (sum_k [ w_k(z) * A_k(z) * C_x,k(z) ]) / A(z)`

`C_y(z) = (sum_k [ w_k(z) * A_k(z) * C_y,k(z) ]) / A(z)`


The centroid location is therefore:
- geometry-dependent,
- weight-dependent,
- generally varying along `z `.

This variability is explicitly tracked and exported.

---

## Second Moments of Area

Second moments of area are first computed for each polygon about its own centroid,
then shifted to the section centroid using the parallel-axis theorem.

The weighted sectional moments are:

`I_x(z) = sum_k [ w_k(z) * I_x,k^(centroid)(z) ]`

`I_y(z) = sum_k [ w_k(z) * I_y,k^(centroid)(z) ]`

The product of inertia `I_{xy}(z) `is evaluated analogously.

---

## Polar Moment and Torsional Constant

The polar moment of area is defined as:

`J_p(z) = I_x(z) + I_y(z)`

CSF also evaluates a torsional stiffness constant ` J(z) `,
which coincides with `J_p ` for simple solid sections and
is computed using dedicated formulations for thin-walled or cellular geometries
when applicable.

The distinction between:
- geometric polar moment,
- Saint-Venant torsional constant,

is preserved and documented in the output.

---

## Derived Section Quantities

From the primary properties, CSF derives additional quantities commonly used
in engineering practice:

- radii of gyration:
- 
`r_x(z) = sqrt( I_x(z) / A(z) )`

`r_y(z) = sqrt( I_y(z) / A(z) )`


- principal moments of inertia ` I_1(z), I_2(z)`,
- principal axis rotation angle.

These quantities are purely sectional and independent of solver assumptions.

---

## Stiffness-Like Quantities

Depending on the interpretation of weights, CSF may report stiffness-like products:

- axial stiffness: ` EA(z) `,
- bending stiffness: ` EI_x(z), EI_y(z)`,
- torsional stiffness: `GJ(z)`.

CSF itself does not enforce how these quantities are used.
Their physical meaning depends on the adopted weight convention
(see *Weight Laws and Sectional Homogenization*).

---

## Shear-Related Quantities

CSF can compute first moments of area`Q(z)`with respect to a specified cut,
typically used in classical shear stress formulations.

These quantities are provided as geometric inputs and do not imply
any shear deformation theory.

---

## Coordinate System and Sign Conventions

All sectional quantities are expressed in the local `x-y` reference frame.

Sign conventions follow standard engineering practice:
- areas are positive,
- centroids are signed coordinates,
- moments of inertia are non-negative,
- products of inertia may be positive or negative.

CSF does not apply absolute-value corrections.

---

## Numerical Accuracy

All geometric quantities are computed analytically from polygonal formulas.
Accuracy depends on:
- correctness of the geometry,
- polygonal approximation of curved outlines,
- numerical integration precision along ` z `.

No artificial smoothing or correction is applied.

---

## Scope and Limitations

Section properties computed by CSF:
- are linear-elastic,
- assume small deformations,
- are valid within classical beam theory assumptions.

Stress recovery, nonlinear effects, and local phenomena
are outside the scope of CSF.

---

## Summary

CSF evaluates section properties as **explicit, weighted geometric integrals**,
fully determined by user-defined geometry and longitudinal laws.

This approach ensures:
- transparency,
- reproducibility,
- and solver-independent interpretation,

providing a robust foundation for the analysis of non-prismatic structural members.

