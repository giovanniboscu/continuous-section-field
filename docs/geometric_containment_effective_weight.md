# Geometric Containment and Effective Weight — Rationale and Theory (v1.2)

> **Purpose.**  
> This document introduces a rigorous yet simple geometric formulation to handle
> nested polygons and material effectiveness in a consistent way.
> The goal is to avoid implicit assumptions, fixed “void weights”, and solver‑dependent tricks,
> while preserving full generality for variable materials and degradation laws.

---

## 1. Motivation and rationale

In many structural and geometric models, sections are described by multiple polygons:
external boundaries, internal regions, reinforcements, or sub‑domains.
When material effectiveness varies along a coordinate (for example along the axis of a member),
a conceptual problem immediately arises:

- if an internal region represents a **removal of material**,
- and the surrounding material effectiveness varies with position,

then the *amount of removed material must vary in the same way*.

A constant negative weight for internal regions (for example “−1 everywhere”)
is therefore **conceptually incorrect** whenever the surrounding material
has a non‑constant effectiveness.

The formulation presented here resolves this issue by:
- separating **geometry** from **weights**,
- defining containment in a purely geometric and unambiguous way,
- deriving an **effective weight** automatically from local containment relations.

This makes the model:
- mathematically coherent,
- material‑independent,
- compatible with arbitrary functions of effectiveness.

---

## 2. Geometric objects and notation

A **polygon** $P \subset \mathbb{R}^2$ is a simple (non self‑intersecting) closed polygonal region.

For a polygon $P$:
- $\partial P$ denotes its boundary,
- $\text{int}(P)$ denotes its interior.

We consider a finite family of polygons:
$$
\mathcal{P} = \{ P_1, P_2, \dots, P_n \}.
$$

---

## 3. Admissible mutual disposition of polygons

### 3.1 Assumptions

For every pair $i \neq j$:

1. **No edge intersection**  
   Edges of $P_i$ and $P_j$ do not cross.

2. **Touching is allowed**  
   $$
   \partial P_i \cap \partial P_j \neq \varnothing
   $$
   is allowed (vertex–vertex, vertex–edge, edge–edge, even along short coincident segments).

3. **No interior overlap**  
   $$
   \text{int}(P_i) \cap \text{int}(P_j) = \varnothing
   $$

These assumptions allow contact but forbid overlap and crossing.

---

### 3.2 Pairwise relations

Given two polygons $A$ and $B$, exactly one of the following situations occurs:

1. **Separated**
   $$
   A \cap B = \varnothing
   $$

2. **Adjacent**
   $$
   \text{int}(A) \cap \text{int}(B) = \varnothing,
   \qquad
   \partial A \cap \partial B \neq \varnothing
   $$

3. **Strict containment**
   $$
   \text{int}(A) \subset \text{int}(B)
   $$

> **Convention.**  
> Containment always means **strict interior inclusion**.
> Boundary contact alone never implies containment.

---

## 4. Containment order and direct container

### 4.1 Strict containment relation

Define the relation $\prec$ on $\mathcal{P}$ by:
$$
A \prec B
\quad \Longleftrightarrow \quad
\text{int}(A) \subset \text{int}(B).
$$

This relation is:
- irreflexive,
- transitive,
- antisymmetric (strict).

It defines a **strict partial order** on the set of polygons.

---

### 4.2 Containers of a polygon

For a polygon $A$, define its set of containers as:
$$
\mathcal{C}(A) =
\{ B \in \mathcal{P} \setminus \{A\} \; | \; A \prec B \}.
$$

- If $\mathcal{C}(A)$ is empty, $A$ has **no container**.
- If non‑empty, all elements of $\mathcal{C}(A)$ are nested.

---

### 4.3 Direct (immediate) container

A polygon $B$ is the **direct container** of $A$ if:

1. $A \prec B$,
2. there exists no polygon $C$ such that
   $$
   A \prec C \prec B.
   $$

The direct container, when it exists, is **unique**.

The global structure induced by this relation is a **forest**:
multiple independent trees of containment may coexist.

---

## 5. Effective weight formulation

### 5.1 Declared weights

Each polygon $P_i$ is assigned an individual weight function:
$$
w_i(z),
$$
where $z$ is a longitudinal or parametric coordinate.

This function represents the **declared effectiveness** of the material
associated with the polygon.

---

### 5.2 Effective weight definition

Let $c(i)$ denote the direct container of $P_i$, if it exists.

The **effective weight** used in calculations is defined as:

- if $c(i)$ exists:
  $$
  w_i^{\text{eff}}(z) = w_i(z) - w_{c(i)}(z),
  $$
- otherwise:
  $$
  w_i^{\text{eff}}(z) = w_i(z).
  $$

This rule is purely local and depends only on immediate containment.

---

### 5.3 Consistent modelling of material removal

If a polygon $H$ represents a removal of material and is declared with:
$$
w_H(z) = 0,
$$
and its direct container is $C$, then:
$$
w_H^{\text{eff}}(z) = -\,w_C(z).
$$

As a consequence, the removal always scales with the actual effectiveness
of the surrounding material.

**Example.**  
If $w_C(z)$ varies linearly from $1$ to $0.5$, the removal varies from $-1$ to $-0.5$.
This avoids the conceptual error of a constant removal applied to a degrading material.

---

## 6. Advantages of the formulation

This approach provides:

- strict separation between **geometry** and **material behaviour**,
- automatic and consistent handling of internal regions,
- independence from material type,
- independence from discretization or solver strategy,
- conceptual correctness for variable effectiveness laws.

---

## 7. Summary

- Polygons may touch but never overlap internally.
- Containment is defined by strict interior inclusion.
- Each polygon has at most one direct container.
- Effective weights are computed by local subtraction:
  $$
  w_i^{\text{eff}}(z) = w_i(z) - w_{c(i)}(z).
  $$
- Material removal automatically follows material effectiveness.

---

**Document version:** v1.2
