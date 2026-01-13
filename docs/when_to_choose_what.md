# When to Choose What  
## CSF Continuous vs CSF-Piecewise (CSF-PW)

This document provides **practical guidance** on choosing between:

- **CSF Continuous**
- **CSF-Piecewise (CSF-PW)**

The goal is not to declare a “winner”, but to help the engineer make a
**conscious, defensible choice** depending on the problem.

---

## 1. First Question to Ask Yourself

> *What am I trying to prove or compute?*

Before choosing a method, clarify whether your goal is:
- global structural behavior
- local effects
- validation / benchmarking
- production modeling
- exploratory or parametric studies

---

## 2. Use CSF Continuous When…

### ✅ Recommended if:
- Geometry and material variation are **smooth and well-behaved**
- No sharp discontinuities along the member
- You want:
  - minimal model size
  - minimal DOFs
  - elegant representation
- The element is used:
  - for global stiffness
  - for modal properties
  - for preliminary sizing

### Typical examples:
- Tapered beams with smooth interpolation
- Wind turbine towers with gradual diameter/thickness variation
- Conceptual or early-stage design models

### Strengths:
- Extremely compact (1 element, 2 nodes)
- Clean mathematical formulation
- Fast to solve

### Limitations:
- Harder to debug
- Harder to validate locally
- Discontinuities require special handling
- Less transparent to reviewers

---

## 3. Use CSF-Piecewise (CSF-PW) When…

### ✅ Recommended if:
- Geometry or material properties have **strong gradients**
- You have **physical discontinuities**:
  - reinforcement cut-offs
  - holes
  - stiffness drops
- You want:
  - full transparency
  - easy debugging
  - compatibility with standard OpenSees workflows

### Typical examples:
- Reinforced concrete members with bars terminating
- Multi-material or perforated sections
- Research or verification studies
- Comparison against classical piecewise models

### Strengths:
- Uses standard OpenSees elements
- Explicit spatial discretization
- Easy to inspect node-by-node
- Naturally handles discontinuities

### Limitations:
- More nodes and DOFs
- Slightly heavier models
- Requires choosing N

---

## 4. Choosing N in CSF-PW

### Rule of thumb:
- **N = 1**  
  → Equivalent element (global behavior only)

- **N = 5**  
  → Reasonable engineering accuracy for smooth variation

- **N = 10**  
  → Very close to CSF continuous (as validated)

- **N > 10**  
  → Use only if strong nonlinearity or high gradients exist

### Important:
- N is a **minimum**
- Cut insertion may increase the actual number of segments
- This is intentional and correct

---

## 5. Lobatto vs Manual Stations

### Lobatto (default)
Choose when:
- No exact cut locations are required
- Variation is smooth
- You want fast convergence with minimal thinking

### Explicit stations
Choose when:
- Discontinuities must coincide with nodes
- You want exact reproducibility
- You are validating against another solver

---

## 6. A Key Philosophical Difference

**CSF Continuous**
> “Trust the element to integrate the variation.”

**CSF-PW**
> “Show me the variation explicitly.”

Neither is wrong.
They serve different engineering cultures.

---

## 7. Responsibility and Documentation

CSF-PW intentionally places responsibility on the engineer:

- Choosing N
- Deciding if N=1 is acceptable
- Justifying convergence (if required)

This is not a weakness — it is **engineering honesty**.

---

## 8. Suggested Workflow

1. Start with **CSF Continuous** or **CSF-PW N=1**
2. Increase to **CSF-PW N=5**
3. If results change materially → increase N
4. Stop when changes are negligible

This gives:
- confidence
- traceability
- defensibility

---

## 9. Final Recommendation

> **Use CSF Continuous for elegance.  
> Use CSF-Piecewise for robustness.**

In doubt:
- CSF-PW with Lobatto stations is the safest default.

---

## 10. One-Sentence Summary

> CSF-PW exists to make the continuous theory usable in real-world models
> without hiding complexity where it matters.
