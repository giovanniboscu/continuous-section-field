# Numerical Engine

## Overview

The numerical engine of CSF is designed to extract sectional and global quantities
from a **continuously defined geometric and sectional field**.

Unlike traditional approaches based on discrete prismatic elements,
CSF evaluates properties directly from the continuous description,
using deterministic numerical integration schemes.

This chapter describes:
- how quantities are evaluated along the member,
- how numerical integration is performed,
- and how accuracy and robustness are ensured.

---

## Continuous Longitudinal Formulation

CSF treats the member as a continuous domain:
\[
z \in [z_0, z_1]
\]

All sectional quantities are evaluated as functions of \( z \).
There is no implicit discretization into finite elements at this stage.

The numerical engine samples this continuous field only for the purpose of:
- evaluating integrals,
- exporting station data,
- generating plots and tables.

---

## Multi-Pass Evaluation Strategy

To maintain clarity and numerical stability, CSF adopts a **multi-pass strategy**:

1. **Geometric reconstruction**  
   At each evaluation point, the section geometry is reconstructed by ruled-surface interpolation.

2. **Sectional evaluation**  
   Pure geometric quantities are computed exactly from the reconstructed polygons.

3. **Weight application**  
   Longitudinal weight laws are evaluated and applied to sectional contributions.

4. **Assembly and post-processing**  
   Global section properties and derived quantities are assembled.

Each pass is explicit and isolated, reducing the risk of hidden coupling effects.

---

## Numerical Integration Along the Member

Global quantities, such as:
- total volume,
- total mass,
- averaged properties,

are obtained by integrating sectional quantities along \( z \).

CSF employs **Gaussian quadrature schemes** for this purpose.

The default choice is motivated by:
- high accuracy for smooth functions,
- deterministic sampling points,
- well-understood convergence properties.

---

## Gaussian Quadrature

Let \( f(z) \) be a sectional quantity varying along the member.
Its integral is approximated as:

\[
\int_{z_0}^{z_1} f(z)\, dz \;\approx\;
\sum_{i=1}^{n} w_i\, f(z_i)
\]

where:
- \( z_i \) are the quadrature points,
- \( w_i \) are the associated weights,
- \( n \) is the number of integration points.

The user may control the number of points to balance accuracy and cost.

---

## Deterministic Sampling

Quadrature points are defined analytically and do not depend on:
- mesh generation,
- element subdivision,
- user-defined discretization choices.

This ensures that:
- repeated runs produce identical results,
- refinements converge monotonically,
- numerical behavior is predictable.

---

## End-Point Accuracy and Gauss–Lobatto Schemes

When exporting sectional data for external solvers,
CSF may use **Gauss–Lobatto sampling**.

This scheme includes the end points \( z_0 \) and \( z_1 \),
ensuring that:
- boundary conditions are applied at exact member ends,
- end-section properties are evaluated without extrapolation.

This is particularly important for force-based beam formulations.

---

## Handling of Nonlinear Geometry Variation

Although the ruled-surface interpolation of geometry is linear in vertex coordinates,
the resulting sectional quantities are generally **nonlinear functions of \( z \)**.

For example:
- moments of inertia vary polynomially,
- centroid coordinates may vary nonlinearly,
- stiffness-like quantities inherit nonlinearity from both geometry and weight laws.

The numerical engine does not assume linearity in sectional response.

---

## Numerical Robustness

Several design choices enhance robustness:

- Explicit reconstruction at each evaluation point.
- No reuse of intermediate results across unrelated computations.
- Strict validation of weight-law evaluations.
- Immediate reporting of numerical anomalies (NaN, infinity).

CSF does not attempt to silently correct or regularize numerical issues.

---

## Accuracy Considerations

Accuracy depends on:
- geometric fidelity of polygonal sections,
- smoothness of weight laws,
- number of quadrature points.

Users are encouraged to perform convergence checks
when high precision is required.

---

## Performance Considerations

CSF prioritizes clarity and determinism over raw speed.

Typical use cases involve:
- limited numbers of evaluation points,
- moderate polygon counts,
- preprocessing rather than large-scale simulations.

Performance is adequate for interactive modeling and validation workflows.

---

## Scope and Limitations

The numerical engine:
- operates at the sectional and member level,
- does not solve equilibrium equations,
- does not perform time integration or nonlinear iteration.

It is designed as a **support engine** for downstream solvers,
not as a replacement.

---

## Summary

The CSF numerical engine provides a deterministic and transparent
framework for evaluating continuous sectional fields.

By combining explicit geometry reconstruction with robust quadrature schemes,
it ensures accurate and reproducible extraction of sectional and global quantities
for non-prismatic structural members.

