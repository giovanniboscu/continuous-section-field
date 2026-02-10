# CSF Documentation — Reader Index

This folder contains the full technical documentation for **Continuous Section Field (CSF)**.
The documents are structured to support **reviewers, researchers, and advanced practitioners**
who need to understand assumptions, numerical methodology, validation, and solver integration.

The recommended reading order is listed below.

---

## 📘 Recommended Reading Order

### 1. Overview and Scope
- **00_overview.md**  
  High-level description of CSF, motivation, positioning, and intended use.

- **01_concepts_and_scope.md**  
  Core concepts, modeling philosophy, and explicit scope limitations.

---

### 2. Geometry and Modeling Foundations
- **02_geometry_model.md**  
  Detailed description of the ruled-surface geometry model, polygon topology,
  interpolation rules, and geometric assumptions.

- **03_weight_laws.md**  
  Formal definition of weight laws, physical meaning, void logic, containment,
  and custom longitudinal formulations.

---

### 3. Section Properties and Numerical Engine
- **04_section_properties.md**  
  Definition of geometric and stiffness-related section properties computed by CSF.

- **05_numerical_engine.md**  
  Numerical integration strategy, Gaussian quadrature, station sampling,
  and computational robustness.

---

### 4. Validation and Benchmarks
- **06_validation_cylinder.md**  
  Analytical validation using a circular hollow section with convergence analysis.

- **07_validation_nrel_5mw.md**  
  Full-scale validation against the official **NREL 5‑MW reference wind turbine tower**,
  including pointwise comparisons and relative error tables.

---

### 5. Solver Integration
- **08_opensees_integration.md**  
  Exact mapping between CSF continuous fields and OpenSees force-based beam formulations,
  including Gauss–Lobatto stationing and centroid-axis handling.

---

### 6. No‑Code Workflow (YAML)
- **09_yaml_workflow.md**  
  Complete YAML-based workflow for running CSF without writing Python code.

- **10_actions_reference.md**  
  Exhaustive reference of all CSF actions, parameters, constraints, and outputs.

---

### 7. Practical Guidance
- **11_common_pitfalls.md**  
  Frequent modeling and numerical mistakes, with explanations and mitigation strategies.

- **12_faq_methodology.md**  
  Methodological clarifications, design rationale, and answers to common reviewer questions.

---

## 🎯 Intended Audience

- Structural engineers dealing with **non-prismatic members**
- Researchers working on **beam theory, homogenization, or numerical integration**
- Reviewers evaluating **methodological rigor and validation**
- Advanced OpenSees users requiring **continuous stiffness fields**

---

## 📌 Notes for Reviewers

- CSF is a **pre-processing and sectional analysis engine**, not a FEM solver.
- All numerical results are derived from **explicit geometry and declared laws**.
- No hidden defaults or automatic profile recognition are used.
- Validation cases are fully reproducible using the provided scripts.

---

## 🔗 Repository Context

These documents complement:
- the main repository README,
- inline code documentation,
- executable examples in `examples/`,
- YAML action examples in `actions-examples/`.

Together, they form a **complete, auditable technical package**.

---
