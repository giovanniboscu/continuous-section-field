# 12 — FAQ: Methodology and Modeling Choices

This FAQ addresses the most common **methodological questions** about **CSF (Continuous Section Field)**.  
It focuses on *why* certain design decisions were made, not only *how* to use the tool.

---

## Q1 — Is CSF a finite element method (FEM) solver?

**No.**  
CSF is **not** a FEM solver and does not solve equilibrium equations.

CSF is a **geometric–mechanical preprocessing engine** that:
- defines a *continuous cross‑section field* along a member,
- evaluates section properties and stiffness fields,
- exports solver‑ready data.

Equilibrium, boundary conditions, and nonlinear response are delegated to external solvers.

---

## Q2 — What problem does CSF solve that classical tools do not?

Classical tools model non‑prismatic members as:
- stepped prismatic elements,
- user‑chosen averaging points.

CSF instead:
- defines a **continuous field**,
- evaluates properties at any longitudinal coordinate,
- controls sampling using **numerical quadrature (Gauss–Lobatto)**.

The difference is **methodological**, not theoretical.

---

## Q3 — Is CSF introducing new structural mechanics theory?

No.

CSF relies entirely on:
- classical section theory,
- standard integral definitions,
- linear elasticity.

The novelty lies in **how geometry and properties are declared and sampled**, not in the equations.

---

## Q4 — Why are sections defined using polygons instead of templates?

Templates (I‑sections, tubes, boxes):
- hide assumptions,
- restrict topology,
- break reproducibility.

Polygons:
- are explicit,
- are solver‑agnostic,
- can represent *any* topology (multi‑cell, stiffeners, voids).

This choice favors **clarity over convenience**.

---

## Q5 — Why does CSF require CCW polygon orientation?

Because CSF uses **signed area integrals**.

Automatic correction would:
- hide geometry errors,
- break traceability.

CSF enforces:
> *Geometry must be correct at input level.*

---

## Q6 — What exactly is “weight” in CSF?

`weight` is a **scalar field multiplying area integrals**.

It may represent:
- a dimensionless stiffness ratio,
- a real physical property (e.g. Young’s modulus),
- any per‑area scalar field.

CSF does not impose interpretation; **the user does**.

---

## Q7 — Why are voids declared as `weight = 0`?

Because a void is **zero contribution**, not negative material.

CSF handles containment internally:
- parent material is removed automatically,
- no manual subtraction is required.

This avoids sign errors and double counting.

---

## Q8 — Can weight laws vary continuously along z?

Yes.  
Each polygon may have its own **continuous law** `w(z)` defined by:
- formulas,
- external data (`E_lookup`),
- geometric coupling.

This is optional, not mandatory.

---

## Q9 — Is continuous variation along z really necessary in practice?

Not always.

CSF supports it because:
- some applications require it (towers, degradation, staging),
- the cost is negligible once the field is defined,
- it removes arbitrary discretization choices.

Use it **only when it adds value**.

---

## Q10 — Is CSF just a “fancy piecewise‑prismatic model”?

No.

Piecewise‑prismatic modeling:
- averages properties per segment,
- depends on user discretization.

CSF:
- defines a continuous field,
- samples it using controlled quadrature,
- keeps end conditions exact.

The OpenSees discretization is a **numerical enforcement**, not a conceptual limitation.

---

## Q11 — Why does CSF use ruled surfaces?

Ruled surfaces:
- provide exact linear interpolation of vertices,
- keep geometry explicit and invertible,
- avoid hidden spline assumptions.

Curved geometry is approximated by polygon refinement, not by implicit curves.

---

## Q12 — Why is Gauss–Lobatto used for station placement?

Because:
- endpoints are included exactly,
- boundary conditions coincide with physical ends,
- it is standard in force‑based beam formulations.

This avoids artificial stiffness at supports.

---

## Q13 — Does CSF enforce a unit system?

No.

CSF is **unit‑agnostic**.
Consistency is the user’s responsibility.

This mirrors most structural solvers (including OpenSees).

---

## Q14 — Why does CSF avoid silent “fixes”?

Silent fixes:
- hide modeling errors,
- reduce trust,
- break reproducibility.

CSF prefers:
- explicit errors,
- early failure,
- user responsibility.

---

## Q15 — When should CSF *not* be used?

CSF is not suitable when:
- full 3D stress fields are required,
- material nonlinearity dominates the problem,
- cross‑sections are truly prismatic and simple.

In those cases, simpler tools may be more appropriate.

---

## Final Statement

> CSF is designed for **clarity, traceability, and methodological correctness**,  
> not for speed through hidden assumptions.

If a modeling choice feels explicit or strict, it is intentional.
