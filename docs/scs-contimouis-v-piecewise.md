# CSF Continuous vs CSF-Piecewise (CSF-PW)

This document explains, at a **macro / conceptual level**, the difference between
a *continuous CSF approach* and a *piecewise CSF-PW approach*, without going into
implementation micro-details (loads, matrices, solvers).

---

## 1. Problem Context

We consider a beam whose properties vary along its longitudinal axis `z`:

- Geometry (A(z), I(z), centroid offsets Cx(z), Cy(z))
- Material (E(z), G(z))
- Optional discontinuities (rebars ending, holes, stiffness drops)

The goal is to represent this beam in **OpenSees**.

---

## 2. CSF Continuous (Conceptual Model)

### What it is
- The beam is represented as **a single finite element**
- Only **two nodes** exist (start and end)
- Property variation is handled **inside the element**
  via internal sampling / integration points

### Model topology
- Elements: **1**
- Nodes: **2**
- Degrees of freedom: minimal

### Characteristics
- Very compact model
- Elegant from a mathematical standpoint
- High abstraction level
- Integration and consistency are hidden inside the element formulation

### Implications
- Requires custom integration logic
- Harder to validate and debug
- More difficult to extend with abrupt discontinuities
- User must trust the internal formulation

---

## 3. CSF-Piecewise (CSF-PW)

### What it is
- CSF is used to compute *correct section properties*
- The beam is **explicitly discretized** into multiple prismatic segments
- Each segment is a standard OpenSees beam element

### Model topology
- Elements: **N**
- Nodes: **N+1**
- Degrees of freedom: increased explicitly

### Characteristics
- Uses standard OpenSees elements
- Explicit spatial discretization
- Easy to inspect, debug, and validate
- Naturally supports discontinuities (via segment boundaries)

### Role of CSF
- CSF acts as a **high-quality generator** of piecewise-constant segments
- It ensures:
  - correct geometry
  - correct centroid tracking (tilt)
  - correct material weighting
- OpenSees does the solving, not CSF

---

## 4. Lobatto-Based CSF-PW

In CSF-PW, segment boundaries are typically generated using
**Gauss–Lobatto stations**:

- Endpoints are always included
- Stations are optimally distributed for integration
- Convergence is fast as N increases

### Cut insertion
If physical discontinuities exist:
- additional `z_cut` locations are inserted
- the number of segments increases *only if necessary*
- N is treated as a **minimum**, not a fixed requirement

---

## 5. Macro Comparison

| Aspect | CSF Continuous | CSF-PW |
|-----|--------------|--------|
| Elements | 1 | N |
| Nodes | 2 | N+1 |
| DOFs | Minimal | Explicitly increased |
| Discontinuities | Hard | Natural |
| Debuggability | Low | High |
| OpenSees compatibility | Custom | Native |
| User control | Low | High |

---

## 6. Key Conceptual Difference

**CSF Continuous**
> Variation is internal and implicit.

**CSF-PW**
> Variation is external and explicit.

Both are mathematically valid.
The difference is **where** discretization lives.

---

## 7. Design Philosophy

CSF-PW deliberately trades:
- a small increase in model size
for:
- transparency
- robustness
- compatibility
- user control

The level of discretization (`N`) is a **design choice** and therefore
a **responsibility of the engineer**, not the tool.

---

## 8. Final Takeaway

> CSF-PW does not simplify the physics.  
> It simplifies the workflow.

It keeps OpenSees honest, CSF focused, and the model understandable.
