# README — Polygon Modeling in CSF with `@wall@t=` and `@cell@t=`

This document is a practical guide to model cross-sections in **CSF (Continuous Section Field)** using polygon tags, with a focus on:

- `@wall@t=...` for **open thin-walled** contributions
- `@cell@t=...` for **closed-cell thin-walled** contributions

It is written as a general reference, independent of any specific example file.

---

## Table of Contents

1. Purpose and Scope  
2. Core Modeling Concepts  
3. Tags Overview  
4. When to Use `@wall` vs `@cell`  
5. Thickness Control with `@t=`  
6. Geometry Rules and Best Practices  
7. Units and Dimensional Consistency  
8. Recommended Modeling Workflow  
9. Validation Checklist  
10. Common Mistakes and How to Avoid Them  
11. Naming Conventions  
12. YAML Patterns (Generic Templates)  
13. Interpreting Results Correctly  
14. FAQ  
15. Quick Start Summary  

---

## 1) Purpose and Scope

CSF is a declarative geometric framework: you define section geometry explicitly through polygons and user tags.  
For torsion and thin-wall analysis, tags determine **which polygons are included** and **how they are interpreted**.

This guide explains how to structure polygon definitions so that:

- Thin-wall computations are explicit and reproducible.
- Thickness is controlled intentionally.
- Results are physically meaningful and easy to audit.

---

## 2) Core Modeling Concepts

### Polygon-first representation
A section is a set of named polygons.  
Each polygon has:

- a unique **name** (within the same section),
- a **weight**,
- a list of **vertices**.

### Tag-driven analysis scope
The tags inside polygon names select polygons for specific analysis paths:

- polygons tagged `@wall` are included in wall-path computations,
- polygons tagged `@cell` are included in cell-path computations.

Polygons without those tags are ignored by those specific paths.

### Explicitness over assumptions
For thin-wall torsion, thickness can be estimated from geometry, but the most robust approach is explicit `@t=` in the name.

---

## 3) Tags Overview

### `@wall`
Marks a polygon as an **open thin-wall** element for wall-based torsion analysis.

### `@cell`
Marks a polygon as a **closed-cell** contour for cell-based torsion analysis.

### `@t=<value>`
Overrides thickness for the tagged polygon.

Examples:
- `web@wall@t=0.01`
- `cell_1@cell@t=0.008`
- `panel_A@wall@t=4.1e-3`

---

## 4) When to Use `@wall` vs `@cell`

Use `@wall` when the part behaves as an **open thin wall** contribution.  
Use `@cell` when the contour is **closed** and should be treated as a cell in closed-cell torsion logic.

Decision rule:
- open-strip mechanics → `@wall`
- closed-loop mechanics → `@cell`

---

## 5) Thickness Control with `@t=`

### Why explicit thickness is preferred
If thickness is inferred from area/perimeter (e.g., `2A/P`), the estimate can differ from nominal plate thickness, especially with fillets or coarse polygonization.

Since torsion terms can depend strongly on thickness (often with powers of `t`), small thickness bias can produce large output differences.

### Recommended policy
For thin-wall and cell workflows:

- define thickness explicitly with `@t=...`,
- keep values aligned with nominal design thickness,
- document units in the project README.

---

## 6) Geometry Rules and Best Practices

1. **Unique polygon names within each section**  
2. **Consistent naming across stations**  
3. **Consistent orientation policy** (validated upstream)  
4. **No hidden solver fixes**  
5. **Explicit modeling intent** via tags  
6. **Avoid mixed semantics in one polygon**  

---

## 7) Units and Dimensional Consistency

Choose one unit system and keep it consistent end-to-end.

Typical choices:
- meters,
- centimeters,
- millimeters.

Coordinates, `@t=`, and outputs must be interpreted in the same unit framework.

---

## 8) Recommended Modeling Workflow

1. Define baseline polygons at `S0`.
2. Assign stable names.
3. Add role tags (`@wall` / `@cell`).
4. Add explicit thickness (`@t=`).
5. Build additional stations (`S1`, etc.).
6. Validate names/orientation/thickness.
7. Run analysis and inspect outputs.
8. Compare against compatible references.

---

## 9) Validation Checklist

- [ ] Names unique per section  
- [ ] Intended wall polygons contain `@wall`  
- [ ] Intended cell polygons contain `@cell`  
- [ ] Thin-wall/cell polygons contain explicit `@t=`  
- [ ] Positive and unit-consistent thickness values  
- [ ] Symmetry checks where expected  
- [ ] Torsion values plausible by magnitude  
- [ ] No silent defaults masking missing data  

---

## 10) Common Mistakes and How to Avoid Them

### Single solid polygon expected to behave like wall/cell decomposition
A single closed solid contour is not automatically a wall/cell breakdown.

**Fix:** split and tag polygons explicitly for the intended path.

### Relying on inferred thickness only
Can bias `t` and therefore torsion.

**Fix:** use `@t=`.

### Unit mismatch
A frequent source of large errors.

**Fix:** enforce one unit policy and document it clearly.

### Non-unique names
Can break mapping and diagnostics.

**Fix:** enforce in parser/validator.

---

## 11) Naming Conventions

Recommended style:

- lowercase,
- underscore separators,
- explicit role tag,
- explicit thickness where required.

Examples:
- `web@wall@t=0.0041`
- `flange_top@wall@t=0.0057`
- `cell_outer@cell@t=0.006`

---

## 12) YAML Patterns (Generic Templates)

### Open thin-wall pattern (`@wall@t=`)

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        wall_part_1@wall@t=0.006:
          weight: 1.0
          vertices:
            - [x1, y1]
            - [x2, y2]
            - [x3, y3]
            - [x4, y4]

        wall_part_2@wall@t=0.008:
          weight: 1.0
          vertices:
            - [x1, y1]
            - [x2, y2]
            - [x3, y3]
            - [x4, y4]
```

### Closed-cell pattern (`@cell@t=`)

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        cell_1@cell@t=0.005:
          weight: 1.0
          vertices:
            - [x1, y1]
            - [x2, y2]
            - [x3, y3]
            - [x4, y4]
            - [x5, y5]
```

### Mixed pattern (`@wall` + `@cell`)

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        panel_left@wall@t=0.004:
          weight: 1.0
          vertices: [[...], [...], [...], [...]]

        box_core@cell@t=0.006:
          weight: 1.0
          vertices: [[...], [...], [...], [...], [...]]
```

---

## 13) Interpreting Results Correctly

When outputs differ from handbook values, first verify:

- same section idealization,
- same thickness basis,
- same unit system,
- same torsion model family (open-wall vs closed-cell vs solid/FE).

Compare like-with-like.

---

## 14) FAQ

**Q: Can I omit `@t=`?**  
A: Sometimes yes, if your code infers thickness. For engineering reproducibility, explicit `@t=` is recommended.

**Q: Can one polygon be both `@wall` and `@cell`?**  
A: Technically possible as text, usually ambiguous semantically. Prefer role separation unless explicitly defined.

**Q: Is one polygon enough for wall analysis?**  
A: Only if it truly represents the intended wall entity and is tagged accordingly.

---

## 15) Quick Start Summary

- Use clear polygon names.
- Tag roles explicitly (`@wall`, `@cell`).
- Prefer explicit thickness (`@t=`).
- Keep units consistent.
- Validate upstream.
- Compare against references with compatible assumptions.
