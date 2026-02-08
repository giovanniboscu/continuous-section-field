# 11 — Common Pitfalls and How to Avoid Them

This document collects the most frequent mistakes encountered when using **CSF (Continuous Section Field)** and explains **why they happen**, **how CSF reacts**, and **how to fix them**.  
The goal is not to hide errors, but to make modeling assumptions explicit and reproducible.

---

## 1. Polygon Orientation (CW vs CCW)

### Problem
Polygons are defined with vertices in **clockwise (CW)** order instead of **counter‑clockwise (CCW)**.

### Why it matters
CSF uses **Green’s theorem / shoelace formulas**.  
CW polygons produce **negative signed areas**, leading to incorrect:
- area
- centroid
- inertia
- stiffness

### CSF behavior
- CSF **does not auto‑flip** polygons.
- Results are mathematically consistent but **physically wrong**.

### Fix
Always define vertices in **CCW order**.

**Rule**
> Geometry must be validated upstream. CSF never “fixes” orientation silently.

---

## 2. Missing or Silent Defaults

### Problem
Expecting CSF to assume default values for:
- `weight`
- material parameters
- reference modulus

### Why it matters
Silent defaults hide modeling errors and invalidate reproducibility.

### CSF behavior
- Missing required parameters → **explicit error**
- No hidden assumptions

### Fix
Declare everything explicitly:
- `weight`
- `E_ref` (if required by exporter)
- unit system (by convention)

---

## 3. Mixing Geometry and Physics Concepts

### Problem
Confusing:
- geometric properties (A, I, C)
- stiffness properties (EA, EI, GJ)

### Why it matters
CSF is **geometry‑driven**.  
Physics enters only through **weights**.

### CSF behavior
- Geometry is always computed first
- Weighted quantities are derived afterward

### Fix
Keep the conceptual separation clear:
- Geometry → polygons
- Physics → weight laws

---

## 4. Incorrect Void Modeling

### Problem
Using:
- negative weights
- partial weights
to represent voids

### Why it matters
A void is **zero contribution**, not “negative material”.

### CSF behavior
- `weight = 0.0` → absolute void
- Overlap subtraction is handled internally

### Fix
Always declare voids as:

```
weight = 0.0
```

Do **not** subtract material manually.

---

## 5. Inconsistent Polygon Naming

### Problem
Using different names for corresponding polygons at S0 and S1.

### Why it matters
Polygon **order** defines geometric pairing,  
but **names** are used for:
- weight law tracking
- diagnostics
- readability

### CSF behavior
- Geometry still works (order‑based)
- Weight laws may not apply as intended

### Fix
Use **stable, consistent names** across sections.

---

## 6. Wrong Station Interpretation

### Problem
Confusing:
- absolute z stations
- relative z stations

### Why it matters
Some actions interpret stations differently.

### CSF behavior
- Most actions: **absolute z**
- `weight_lab_zrelative`: **relative z**

### Fix
Read the action contract carefully.  
Relative interpretation is **explicit**, never implicit.

---

## 7. Stations Outside Geometry Domain

### Problem
Using stations outside `[z_start, z_end]`.

### CSF behavior
- Hard error
- No extrapolation

### Fix
Ensure all station values lie inside the geometry domain.

---

## 8. Expecting Curved Geometry from Linear Interpolation

### Problem
Expecting true curved surfaces between sections.

### Why it matters
CSF uses **ruled surfaces**:
- linear vertex interpolation
- exact geometry definition

### CSF behavior
- Curvature is approximated via polygon refinement

### Fix
Increase polygon resolution for curved sections.

---

## 9. Misinterpreting “Not Piecewise‑Prismatic”

### Problem
Assuming CSF creates arbitrary stepped members.

### Reality
CSF defines a **continuous field** and samples it using **controlled quadrature**.

### Key distinction
- Classical: user‑chosen averaging
- CSF: field‑driven sampling

### Fix
Understand CSF as:
> numerical collocation of a continuous stiffness field

---

## 10. OpenSees Integration Misconceptions

### Problem
Using:
- `beamIntegration Lobatto` with multiple sections
- averaged section properties

### CSF behavior
Correct integration requires:
- `beamIntegration UserDefined`
- explicit station sections

### Fix
Follow the CSF → OpenSees mapping strictly.  
Do not simplify the export unless you fully understand the implications.

---

## 11. YAML Structural Errors

### Problem
- Duplicate keys
- Wrong indentation
- `actions` not defined as a list

### CSF behavior
- Validation error with caret pointer
- Execution aborted

### Fix
Validate YAML first:
```
python CSFActions.py geometry.yaml actions.yaml --validate-only
```

---

## 12. Unit Inconsistency

### Problem
Mixing units (mm vs m, MPa vs Pa).

### CSF behavior
CSF is **unit‑agnostic**.  
Errors propagate numerically, not syntactically.

### Fix
Adopt one unit system and apply it consistently everywhere.

---

## 13. Expecting Nonlinear Material Behavior

### Problem
Assuming CSF models:
- cracking
- plasticity
- damage

### CSF behavior
CSF is **linear‑elastic and geometric** only.

### Fix
Use CSF as a **preprocessor**, not a solver.

---

## 14. Over‑Trusting Visual Output

### Problem
Judging correctness only from plots.

### Why it matters
Visual agreement ≠ numerical correctness.

### Fix
Always:
- inspect tables
- check magnitudes
- compare against references

---

## Final Principle

> CSF favors **explicitness over convenience**.  
> If something is unclear, it is intentional: the model must be clarified, not guessed.

