# DRAFT

# CSF–CUF: a practical learning path

> This page is intended for a reader who already has a basic theoretical idea of the Carrera Unified Formulation (CUF), but does not yet know the CSF–CUF infrastructure.

The objective is to show, in a clear order:

1. **what structural problem is being modelled;**
2. **which building blocks are already available;**
3. **how those building blocks are combined;**
4. **how the corresponding CSF–CUF choices are identified;**
5. **how the numerical results should be interpreted.**

The theoretical formulation can be consulted separately.

---

# 1. Start from the structural problem

Before choosing a CUF expansion, a polynomial order, or a YAML option, first identify the engineering problem.

The first questions are:

- What structure is being modelled?
- How is it constrained?
- How is it loaded?
- What cross-section and material description are being used?

Only after these choices are clear should they be translated into the CSF–CUF input.

The first step is therefore **not**:

> Which CUF order should I use?

It is:

> What is the static scheme I want to represent?

---

# 2. Building blocks

A CSF–CUF model can be understood as the combination of a few main choices.

The important point is that, in the current CSF–CUF implementation, **loads and boundary conditions live together inside the same problem adapter**.

The user therefore does not choose a load and a constraint set as two completely independent objects.

The first practical choice is the **problem adapter**, which represents the structural problem as a coherent combination of:

- load;
- boundary conditions;
- The problem adapter represents a complete structural problem, including its load and boundary conditions.



---

## 2.1 Choose the problem adapter

This is the first building block the user should identify.

The first question is:

> Which structural problem do I want to model?

The documentation should present the available problem adapters as complete structural schemes.

Each row should tell the user:

- what physical problem the adapter represents;
- which load is included;
- which boundary conditions are included;
- the exact `problem.type` used in the YAML;
- where a runnable example is available.

A suitable table is:

| Structural problem | Load included in the adapter | Boundary conditions included in the adapter | `problem.type` | Example |
|---|---|---|---|---|
| **to be filled from verified implementation** | **to be filled** | **to be filled** | **to be filled** | **to be linked** |

The exact rows should be populated directly from the verified adapters in:

```text
src/csf/cuf/adapters/problem
```

No load name, boundary-condition combination, or `problem.type` should be guessed.

The didactic sequence is therefore:

1. recognise the static scheme;
2. choose the corresponding problem adapter;
3. use its verified `problem.type`.

This keeps the physical model and its numerical implementation aligned.

---

## 2.2 CUF transverse expansions

After the structural problem has been identified, the user chooses the transverse CUF expansion.

The currently defined expansion families are:

| Expansion family | CSF–CUF identifier |
|---|---|
| Scaled Legendre | `scaled_legendre` |
| Scaled Lagrange | `scaled_lagrange` |
| Scaled Maclaurin | `scaled_maclaurin` |

These are independent from the CSF geometry/material description.

The user should first know **which families are available**, and only later study their numerical behaviour in detail.

---

# 3. Define geometry and materials with CSF

The cross-section geometry and the material distribution are defined in a **separate CSF YAML file**.

This file describes the section model that will be used by the CUF analysis.

The practical workflow is:

```text
CSF YAML
    ↓
geometry + materials
    ↓
CUF analysis
```

For the reader, the important point is simple:

> To define the cross-section and its materials, prepare or select the corresponding CSF YAML file.

The CUF case then uses that CSF model during the analysis.

This keeps the two roles clear:

- the **CSF YAML** defines geometry and materials;
- the **CUF case YAML** defines the structural problem, the CUF expansion, and the numerical settings.

A beginner should therefore not have to discover the geometry/material description inside the CUF solver.

The documentation should directly show:

1. where the CSF YAML is defined;
2. how it is referenced by the CUF case;
3. where a complete CSF geometry/material example can be found.

A link to the dedicated CSF documentation should be provided here.

---

# 4. Two YAML files, two different roles

A useful first mental model is:

| File | Main role |
|---|---|
| CSF YAML | Geometry and materials |
| CUF case YAML | Problem adapter, CUF expansion, numerical settings |

This distinction should be shown early because it tells the reader immediately **where each modelling choice belongs**.

The reader can then proceed in a natural order:

1. define or select the CSF geometry/material model;
2. choose the structural problem adapter;
3. choose the CUF expansion;
4. choose the numerical settings;
5. run the analysis.

---

# 5. From engineering scheme to CSF–CUF model

The didactic workflow should always follow the same sequence.

## Step 1 - Identify the structural problem

Start from the engineering scheme.

Ask:

> Which complete load + boundary-condition problem am I trying to represent?

Then choose the corresponding verified **problem adapter**.

The exact `problem.type` should be taken from the implementation or from the problem-adapter table above.

## Step 2 - Define the CSF model

Prepare or select the separate CSF YAML that defines:

- cross-section geometry;
- material distribution.

This is the geometry/material input used by the CUF analysis.

## Step 3 - Choose the CUF expansion

For example:

```yaml
basis:
  type: scaled_legendre
```

Other currently defined alternatives are:

```text
scaled_lagrange
scaled_maclaurin
```

## Step 4 - Connect the model choices in the CUF case

The CUF case YAML should identify:

- the chosen problem adapter;
- the chosen CUF expansion;
- the CSF model to be used;
- the numerical settings required by the case.

## Step 5 - Define the remaining numerical model choices

Only after the physical model is clear should the user choose the numerical parameters required by the case.

## Step 6 - Run the case

The first run should be used to understand the full modelling chain.

## Step 7 - Read the result physically

Before studying convergence, ask:

- Is the displacement direction reasonable?
- Is the deformation shape reasonable?
- Are the constraints acting where expected?
- Is the load acting where expected?

Only after that should the user move to numerical refinement.

---

# 6. The first goal is not convergence

A beginner should not start by changing polynomial order repeatedly.

The first objective is to understand the model.

First verify:

1. structural problem adapter;
2. load + boundary-condition combination defined by that adapter;
3. CSF geometry/material description;
4. qualitative deformation.

Then study:

- CUF order;
- expansion family;
- equilibration;
- numerical convergence.

---

# 7. How to read an irregular result

This is an essential part of the learning path.

An irregularity in a CUF result does not automatically mean that the formulation is wrong.

The currently implemented transverse expansions are polynomial families.

A polynomial approximation may have difficulty representing a very local disturbance with a low or insufficient order.

This can be especially visible close to constraints, where the physical response may contain a strong local perturbation.

The correct question is not immediately:

> Is CUF wrong?

Instead ask:

> What physical or numerical mechanism is producing this local behaviour?

---

# 8. Local disturbances near constraints

A local disturbance close to a support can be physically meaningful.

The problem is then how accurately the chosen polynomial expansion represents it.

Depending on the case, the user may observe a local spike or oscillation.

The important didactic point is:

> The presence of a local spike is not, by itself, proof of an error.

The next step is to study whether the representation improves when the approximation is changed.

---

# 9. What to do when an irregularity appears

Use a simple diagnostic sequence.

## 9.1 Check the physical model

Verify:

- the selected problem adapter;
- the load and boundary conditions defined by that adapter;
- the CSF geometry;
- the CSF material description.

## 9.2 Change the CUF approximation

One change at a time:

- increase the expansion order;
- compare another implemented expansion family;
- observe whether the local irregularity changes.

## 9.3 Check equilibration

If the algebraic system is sensitive, test the available equilibration setting.

The point is not to use equilibration to hide a problem.

The point is to understand whether the behaviour is related to the numerical scaling of the system.

---

# 10. Separate physics, approximation, and algebra

When interpreting a result, keep three questions separate.

## Physics

Is the structural model correct?

## Approximation

Is the chosen CUF expansion able to represent the response with the selected order?

## Algebra

Is the resulting system numerically well behaved with the chosen equilibration?

This separation is useful because the same visible irregularity can have different causes.

---

# 11. FEM3D as a validation tool, not as a prerequisite

A full 3D FEM model can be useful as an initial benchmark.

It should not be necessary to build a 3D FEM model every time a CUF case is created.

Otherwise the practical advantage of using CUF would be lost.

A 3D benchmark is useful when:

- validating a modelling mechanism;
- studying a new load or boundary-condition treatment;
- investigating an unexpected response;
- establishing a reference case.

Once the mechanism is understood and validated, the CUF model should be usable on its own.

---

# 12. Suggested learning sequence

## Level 1 - Recognise the building blocks

Learn to identify:

- structural problem adapter;
- the load + boundary-condition combination it represents;
- CUF expansion;
- CSF geometry/material description.

## Level 2 - Run an existing example

Goal:

> Understand how the building blocks appear in a complete case.

## Level 3 - Change one building block

For example:

- keep the same CSF model and change the problem adapter;
- keep the same problem adapter and change the CUF expansion family;
- keep the same structural problem and change the CSF geometry/material model.

Goal:

> Understand what each part of the model controls.

## Level 4 - Interpret the numerical result

Study:

- local perturbations;
- expansion order;
- expansion family;
- equilibration;
- convergence.

## Level 5 - Consult the theory

Once the practical meaning is clear, the detailed CUF formulation can be read with a much clearer understanding of what each term is doing in the actual model.

---

# 13. Recommended documentation order

A practical documentation section can therefore be organised as follows:

1. **What CSF–CUF does**
2. **Available building blocks**
   - problem adapters: load + boundary conditions;
   - CUF expansions.
3. **How geometry and materials are defined in the separate CSF YAML**
4. **Your first complete model**
5. **How the YAML corresponds to the physical problem**
6. **How to read the results**
7. **Local irregularities and numerical interpretation**
8. **Expansion order and expansion family**
9. **Equilibration**
10. **Optional FEM3D validation**
11. **Detailed CUF theory**

---

# 14. Rule for every documented feature

Every feature should eventually be documented with the same four fields:

| Field | Meaning |
|---|---|
| Physical meaning | What complete structural problem does it represent? |
| Load + boundary conditions | Which coherent combination is contained in the adapter? |
| Exact CSF–CUF identifier | What is the verified name used in the input? |
| Runnable example | Where can the user see it working? |

If the exact identifier has not been verified, it should remain explicitly marked as **to be verified**.

It should never be guessed from the physical name.

---

# 15. Final objective

After reading this section, a new user should be able to say:

> I know which structural problem adapter I need.  
> I understand that the adapter contains the load and boundary conditions together.  
> I know which CUF expansions are available.  
> I know that geometry and materials are defined in a separate CSF YAML.  
> I know how these building blocks fit together.  
> I know that I should interpret the physical model before studying convergence.  
> If I see a numerical irregularity, I know which checks to perform first.

That is the didactic objective of this documentation.
# CSF–CUF: a practical learning path

> This page is intended for a reader who already has a basic theoretical idea of the Carrera Unified Formulation (CUF), but does not yet know the CSF–CUF infrastructure.

The objective is not to re-teach the whole CUF theory from the beginning.

The objective is to show, in a clear order:

1. **what structural problem is being modelled;**
2. **which building blocks are already available;**
3. **how those building blocks are combined;**
4. **how the corresponding CSF–CUF choices are identified;**
5. **how the numerical results should be interpreted.**

The theoretical formulation can be consulted separately.

---

# 1. Start from the structural problem

Before choosing a CUF expansion, a polynomial order, or a YAML option, first identify the engineering problem.

The first questions are:

- What structure is being modelled?
- How is it constrained?
- How is it loaded?
- What cross-section and material description are being used?

Only after these choices are clear should they be translated into the CSF–CUF input.

The first step is therefore **not**:

> Which CUF order should I use?

It is:

> What is the static scheme I want to represent?

---

# 2. Building blocks

A CSF–CUF model can be understood as the combination of a few main choices.

The important point is that, in the current CSF–CUF implementation, **loads and boundary conditions live together inside the same problem adapter**.

The user therefore does not choose a load and a constraint set as two completely independent objects.

The first practical choice is the **problem adapter**, which represents the structural problem as a coherent combination of:

- load;
- boundary conditions;
- corresponding generalized CUF actions.

This is the first building block the user should identify.

---

## 2.1 Choose the problem adapter

The first question is:

> Which structural problem do I want to model?

The documentation should present the available problem adapters as complete structural schemes.

Each row should tell the user:

- what physical problem the adapter represents;
- which load is included;
- which boundary conditions are included;
- the exact `problem.type` used in the YAML;
- where a runnable example is available.

The currently available problem-adapter modules are defined in:

[`src/csf/cuf/adapters/problem`](https://github.com/giovanniboscu/continuous-section-field/tree/main/src/csf/cuf/adapters/problem)

Their current names and the corresponding verified `problem.type` values are:

| Problem adapter module | Full adapter name | Supported `problem.type` |
|---|---|---|
| `bending_torsion_halfwave.py` | `csf.cuf.adapters.problem.bending_torsion_halfwave` | `carrera_torsion_halfwave` |
| `bending_torsion_halfwave.py` | `csf.cuf.adapters.problem.bending_torsion_halfwave` | `carrera_bending_bottom_surface_halfwave` |
| `surface_halfwave.py` | `csf.cuf.adapters.problem.surface_halfwave` | `surface_halfwave` |
| `torsion_halfwave.py` | `csf.cuf.adapters.problem.torsion_halfwave` | `torsion_halfwave` |
| `torsion_uniform.py` | `csf.cuf.adapters.problem.torsion_uniform` | `torsion_uniform` |
| `uniform_surface.py` | `csf.cuf.adapters.problem.uniform_surface` | `uniform_surface_load` |

The adapter name and `problem.type` are two different pieces of the configuration.

For example, the uniform torsion problem uses the adapter module:

```text
csf.cuf.adapters.problem.torsion_uniform
```

and the corresponding problem definition contains:

```yaml
problem:
  type: torsion_uniform
```

The didactic sequence is therefore:

1. recognise the structural problem;
2. identify the corresponding problem adapter;
3. use the `problem.type` implemented by that adapter.

The load and the boundary conditions belonging to that structural problem are defined together by the adapter.

---

## 2.2 CUF transverse expansions

After the structural problem has been identified, the user chooses the transverse CUF expansion.

The currently defined expansion families are:

| Expansion family | CSF–CUF identifier |
|---|---|
| Scaled Legendre | `scaled_legendre` |
| Scaled Lagrange | `scaled_lagrange` |
| Scaled Maclaurin | `scaled_maclaurin` |

These are independent from the CSF geometry/material description.

The user should first know **which families are available**, and only later study their numerical behaviour in detail.

---

# 3. Define geometry and materials with CSF

The cross-section geometry and the material distribution are defined in a **separate CSF YAML file**.

This file describes the section model that will be used by the CUF analysis.

The practical workflow is:

```text
CSF YAML
    ↓
geometry + materials
    ↓
CUF analysis
```

For the reader, the important point is simple:

> To define the cross-section and its materials, prepare or select the corresponding CSF YAML file.

The CUF case then uses that CSF model during the analysis.

This keeps the two roles clear:

- the **CSF YAML** defines geometry and materials;
- the **CUF case YAML** defines the structural problem, the CUF expansion, and the numerical settings.

A beginner should therefore not have to discover the geometry/material description inside the CUF solver.

The documentation should directly show:

1. where the CSF YAML is defined;
2. how it is referenced by the CUF case;
3. where a complete CSF geometry/material example can be found.

A link to the dedicated CSF documentation should be provided here.

---

# 4. Two YAML files, two different roles

A useful first mental model is:

| File | Main role |
|---|---|
| CSF YAML | Geometry and materials |
| CUF case YAML | Problem adapter, CUF expansion, numerical settings |

This distinction should be shown early because it tells the reader immediately **where each modelling choice belongs**.

The reader can then proceed in a natural order:

1. define or select the CSF geometry/material model;
2. choose the structural problem adapter;
3. choose the CUF expansion;
4. choose the numerical settings;
5. run the analysis.

---

# 5. From engineering scheme to CSF–CUF model

The didactic workflow should always follow the same sequence.

## Step 1 - Identify the structural problem

Start from the engineering scheme.

Ask:

> Which complete load + boundary-condition problem am I trying to represent?

Then choose the corresponding verified **problem adapter**.

The exact `problem.type` should be taken from the implementation or from the problem-adapter table above.

## Step 2 - Define the CSF model

Prepare or select the separate CSF YAML that defines:

- cross-section geometry;
- material distribution.

This is the geometry/material input used by the CUF analysis.

## Step 3 - Choose the CUF expansion

For example:

```yaml
basis:
  type: scaled_legendre
```

Other currently defined alternatives are:

```text
scaled_lagrange
scaled_maclaurin
```

## Step 4 - Connect the model choices in the CUF case

The CUF case YAML should identify:

- the chosen problem adapter;
- the chosen CUF expansion;
- the CSF model to be used;
- the numerical settings required by the case.

## Step 5 - Define the remaining numerical model choices

Only after the physical model is clear should the user choose the numerical parameters required by the case.

## Step 6 - Run the case

The first run should be used to understand the full modelling chain.

## Step 7 - Read the result physically

Before studying convergence, ask:

- Is the displacement direction reasonable?
- Is the deformation shape reasonable?
- Are the constraints acting where expected?
- Is the load acting where expected?

Only after that should the user move to numerical refinement.

---

# 6. The first goal is not convergence

A beginner should not start by changing polynomial order repeatedly.

The first objective is to understand the model.

First verify:

1. structural problem adapter;
2. load + boundary-condition combination defined by that adapter;
3. CSF geometry/material description;
4. qualitative deformation.

Then study:

- CUF order;
- expansion family;
- equilibration;
- numerical convergence.

---

# 7. How to read an irregular result

This is an essential part of the learning path.

An irregularity in a CUF result does not automatically mean that the formulation is wrong.

The currently implemented transverse expansions are polynomial families.

A polynomial approximation may have difficulty representing a very local disturbance with a low or insufficient order.

This can be especially visible close to constraints, where the physical response may contain a strong local perturbation.

The correct question is not immediately:

> Is CUF wrong?

Instead ask:

> What physical or numerical mechanism is producing this local behaviour?

---

# 8. Local disturbances near constraints

A local disturbance close to a support can be physically meaningful.

The problem is then how accurately the chosen polynomial expansion represents it.

Depending on the case, the user may observe a local spike or oscillation.

The important didactic point is:

> The presence of a local spike is not, by itself, proof of an error.

The next step is to study whether the representation improves when the approximation is changed.

---

# 9. What to do when an irregularity appears

Use a simple diagnostic sequence.

## 9.1 Check the physical model

Verify:

- the selected problem adapter;
- the load and boundary conditions defined by that adapter;
- the CSF geometry;
- the CSF material description.

## 9.2 Change the CUF approximation

One change at a time:

- increase the expansion order;
- compare another implemented expansion family;
- observe whether the local irregularity changes.

## 9.3 Check equilibration

If the algebraic system is sensitive, test the available equilibration setting.

The point is not to use equilibration to hide a problem.

The point is to understand whether the behaviour is related to the numerical scaling of the system.

---

# 10. Separate physics, approximation, and algebra

When interpreting a result, keep three questions separate.

## Physics

Is the structural model correct?

## Approximation

Is the chosen CUF expansion able to represent the response with the selected order?

## Algebra

Is the resulting system numerically well behaved with the chosen equilibration?

This separation is useful because the same visible irregularity can have different causes.

---

# 11. FEM3D as a validation tool, not as a prerequisite

A full 3D FEM model can be useful as an initial benchmark.

It should not be necessary to build a 3D FEM model every time a CUF case is created.

Otherwise the practical advantage of using CUF would be lost.

A 3D benchmark is useful when:

- validating a modelling mechanism;
- studying a new load or boundary-condition treatment;
- investigating an unexpected response;
- establishing a reference case.

Once the mechanism is understood and validated, the CUF model should be usable on its own.

---

# 12. Suggested learning sequence

## Level 1 - Recognise the building blocks

Learn to identify:

- structural problem adapter;
- the load + boundary-condition combination it represents;
- CUF expansion;
- CSF geometry/material description.

## Level 2 - Run an existing example

Goal:

> Understand how the building blocks appear in a complete case.

## Level 3 - Change one building block

For example:

- keep the same CSF model and change the problem adapter;
- keep the same problem adapter and change the CUF expansion family;
- keep the same structural problem and change the CSF geometry/material model.

Goal:

> Understand what each part of the model controls.

## Level 4 - Interpret the numerical result

Study:

- local perturbations;
- expansion order;
- expansion family;
- equilibration;
- convergence.

## Level 5 - Consult the theory

Once the practical meaning is clear, the detailed CUF formulation can be read with a much clearer understanding of what each term is doing in the actual model.

---

# 13. Recommended documentation order

A practical documentation section can therefore be organised as follows:

1. **What CSF–CUF does**
2. **Available building blocks**
   - problem adapters: load + boundary conditions;
   - CUF expansions.
3. **How geometry and materials are defined in the separate CSF YAML**
4. **Your first complete model**
5. **How the YAML corresponds to the physical problem**
6. **How to read the results**
7. **Local irregularities and numerical interpretation**
8. **Expansion order and expansion family**
9. **Equilibration**
10. **Optional FEM3D validation**
11. **Detailed CUF theory**

---

# 14. Rule for every documented feature

Every feature should eventually be documented with the same four fields:

| Field | Meaning |
|---|---|
| Physical meaning | What complete structural problem does it represent? |
| Load + boundary conditions | Which coherent combination is contained in the adapter? |
| Exact CSF–CUF identifier | What is the verified name used in the input? |
| Runnable example | Where can the user see it working? |

If the exact identifier has not been verified, it should remain explicitly marked as **to be verified**.


---


## Example file organization

The files introduced above will be organized using the following directory structure:

```text
.
├── models
│   ├── t_noprismatic_csf.yaml
│   └── action.yaml
├── problems
│   ├── bending_halfwave.yaml
│   └── torsion_halfwave.yaml
└── cases
    ├── bending_halfwave_legendre_N08.yaml
    └── torsion_halfwave_legendre_N08.yaml
```

The role of each file is:

- `models/t_noprismatic_csf.yaml`  
  Defines the CSF model, including the cross-section geometry and material description.

- `models/action.yaml`  
  Contains the action-related model data used by the example.

- `problems/bending_halfwave.yaml`  
  Defines the bending half-wave structural problem.

- `problems/torsion_halfwave.yaml`  
  Defines the torsion half-wave structural problem.

- `cases/bending_halfwave_legendre_N08.yaml`  
  Defines the executable CUF bending case using the Scaled Legendre expansion with order `N=8`.

- `cases/torsion_halfwave_legendre_N08.yaml`  
  Defines the executable CUF torsion case using the Scaled Legendre expansion with order `N=8`.

This layout keeps the CSF model files, the problem definitions, and the executable CUF cases clearly separated.
