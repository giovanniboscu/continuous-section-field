# Mathematical Formulation of CSF Section Evaluation

## 1. Geometric domain and coordinates

Let z ∈ [0, L] denote the longitudinal coordinate of a structural member.  
Two planar sections are defined on parallel planes:

- Initial plane: Π₀ : z = 0  
- Final plane: Πᴸ : z = L  

The x and y axes are identically oriented on both planes.

A normalized coordinate is introduced:

t = z / L ∈ [0,1]

---

## 2. Polygonal section definition

For each object o, CSF defines a finite set of polygons:

{Pᶦ₍ₒ,ₖ₎, Pᶠ₍ₒ,ₖ₎},  k = 1,…, nₒ

Each polygon is represented by an ordered sequence of vertices:

Pᶦ₍ₒ,ₖ₎ = (pᶦ₍ₒ,ₖ,₁₎,…,pᶦ₍ₒ,ₖ,ₘ₎)  
Pᶠ₍ₒ,ₖ₎ = (pᶠ₍ₒ,ₖ,₁₎,…,pᶠ₍ₒ,ₖ,ₘ₎)

with p ∈ ℝ².

Required conditions:

- the number of polygons nₒ is constant;  
- corresponding polygons have the same number of vertices;  
- vertex-to-vertex correspondence is explicit;  
- vertices are ordered counter-clockwise (CCW).  

Polygons may be concave or self-intersecting.

---

## 3. Deterministic polygon evaluation along z

For each vertex:

p₍ₒ,ₖ,ⱼ₎(z) = (1 − t) · pᶦ₍ₒ,ₖ,ⱼ₎ + t · pᶠ₍ₒ,ₖ,ⱼ₎

The polygon at coordinate z is:

P₍ₒ,ₖ₎(z) = (p₍ₒ,ₖ,₁₎(z),…,p₍ₒ,ₖ,ₘ₎(z))

The mapping is deterministic for all z ∈ [0,L], regardless of discretization.  
Twist or self-intersection may occur but do not invalidate the mapping.

---

## 4. Oriented area and positivity constraint

The oriented area of a polygon P = (p₁,…,pₘ), pⱼ=(xⱼ,yⱼ), is:

A(P) = ½ Σⱼ (xⱼ yⱼ₊₁ − xⱼ₊₁ yⱼ),   pₘ₊₁ = p₁

CSF enforces:

A(P₍ₒ,ₖ₎(z)) ≥ 0

Negative geometric areas are not permitted.

---

## 5. Weights and material representation

Each polygon is associated with a scalar weight function:

w₍ₒ,ₖ₎ : [0,L] → ℝ

Weights may be positive, zero, or negative.

Holes are modeled exclusively through negative weights,  
not through negative geometry.

---

## 6. Weighted section quantities

Let Q(P) be any quantity linear in area  
(area, first moments, second moments).

The transformed quantity at coordinate z is:

Q_tr(z) = Σₒ Σₖ w₍ₒ,ₖ₎(z) · Q(P₍ₒ,ₖ₎(z))

This formulation supports homogenization and exclusion  
of overlapping regions.

---

## 7. User responsibility

CSF does not impose topological or semantic constraints.  
Interpretation of polygons (solid, void, reinforcement)  
and the choice of weight functions are the responsibility of the user.

---

## 8. Geometric validity checks

CSF detects geometric anomalies such as:

- edge–edge self-intersections;  
- degenerate configurations.

Such cases generate warnings, not fatal errors.

---

## 9. Diagnostic visualization

CSF may generate a 3D swept volume for inspection of:

- twist effects;  
- self-intersections;  
- global inconsistencies.

---

## 10. Summary

- Sections are evaluated as functions of z.  
- Geometry is deterministic; validity is checked but not enforced.  
- Areas are always positive; subtraction is achieved via weights.  
- Discretization samples the model without redefining it.
