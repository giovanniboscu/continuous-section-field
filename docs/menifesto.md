# CSF — Continuous Section Field  
## Technical Manifesto

### 1. What CSF Is

CSF (Continuous Section Field) is a **geometric engine** for the representation,
manipulation, and discretization of **non-prismatic structural sections**.

CSF models a structural member as a **continuous geometric volume**
defined by section stations (e.g. S0, S1) composed of **polygonal subdomains**
that may vary along the longitudinal coordinate *z*.

CSF is **not a structural solver**.  
CSF does **not** compute stresses, forces, or capacities.

CSF provides **geometry and discretization**, not structural response.

---

### 2. What CSF Is Not

CSF is **not**:
- a finite element solver,
- a replacement for OpenSees or any other analysis code,
- a nonlinear material model,
- a buckling, plasticity, or failure analysis framework.

Any structural analysis (static, dynamic, nonlinear, stability, etc.)
must be performed **outside CSF**, using a solver of choice.

---

### 3. Core Responsibility of CSF

CSF is responsible for:

- Representing **complex cross-sections** as collections of polygons.
- Tracking **centroid shifts, inertia, and sectional properties** along *z*.
- Managing **continuous variation laws** (e.g. weight laws w(z)).
- Producing **consistent and reproducible discretizations**:
  - piecewise-constant segments,
  - Gauss–Lobatto distributions,
  - user-defined station sets,
  - mandatory cut insertion where geometric discontinuities exist.

CSF guarantees that the generated discretization is:
- geometrically coherent,
- mathematically consistent,
- independent from the target solver.

---

### 4. Geometry First, Analysis Later

The fundamental design principle of CSF is:

> **Separate geometric complexity from structural analysis.**

In real engineering practice, geometric complexity is often:
- handled manually,
- hidden in undocumented preprocessing steps,
- reduced to tabulated section properties.

CSF makes this complexity **explicit, formal, and reproducible**.

Once geometry and discretization are defined by CSF,
any solver may consume the resulting data.

---

### 5. Relationship with Solvers (e.g. OpenSees)

When used with OpenSees (or similar tools):

- CSF supplies:
  - station locations,
  - sectional properties,
  - centroid offsets,
  - piecewise segmentation.
- The solver performs:
  - stiffness assembly,
  - equilibrium,
  - dynamic response,
  - nonlinear evolution.

CSF does **not** impose a solver-specific formulation.

OpenSees integration is an **application**, not the definition of CSF.

---

### 6. Continuous vs Piecewise

CSF supports multiple discretization philosophies:

- Single continuous element with endpoint sampling.
- Piecewise-constant discretization with *N* segments.
- Gauss–Lobatto-based segmentation.
- User-specified station lists.
- Automatic cut insertion at geometric or material discontinuities.

The **choice of discretization density** is a modeling decision,
not enforced by CSF.

---

### 7. Current Scope and Future Extensions

At present, CSF focuses on:
- geometry definition,
- continuous-to-discrete mapping.

Future extensions are **natural and non-disruptive**, including:
- export of piecewise volumes,
- DXF/DWG generation,
- JSON/YAML geometry serialization,
- integration with non-beam solvers.

These extensions do **not** change the role of CSF;
they only expand its interoperability.

---

### 8. Why CSF Exists

CSF exists because:
- geometric complexity in structural members is real,
- current workflows hide or oversimplify it,
- reproducibility and clarity are often lost.

CSF provides a **formal geometric backbone**
on top of which reliable structural analysis can be built.

---

### 9. Final Positioning

CSF should be understood as:

> **A continuous geometric modeler and intelligent discretization engine  
> for non-prismatic structural sections.**

Nothing more.  
Nothing less.

---

End of manifesto.
