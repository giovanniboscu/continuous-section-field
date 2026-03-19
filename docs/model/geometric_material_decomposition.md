# CSF Section Model — A Continuous, Zone-Based Formulation

---

## What CSF Does

There is nothing new in the mathematics behind CSF. Homogenization of composite sections (concrete/steel), area and moment integrals via Green's theorem, the Steiner parallel axis theorem — these are all standard tools, covered in any undergraduate structural engineering course.

What CSF contributes is not new theory but a specific **organisational model**: geometry and material are treated as two fully independent fields along $z$, and every zone carries its own weight law — separately from all others and separately from the geometry. This simple structure is what makes the formulation general without adding complexity.

In practice, CSF evaluates all structural quantities — $A(z)$, $I(z)$, $EA(z)$, $EI(z)$, $GJ(z)$ — continuously along the element and exports solver-ready station data to OpenSees and SAP2000. The result is deterministic and traceable at every point, independent of the solver's mesh density.

---

## The Key Idea: Decoupled Geometry and Material

In a standard beam model, section properties follow a simple multiplicative structure:

$$EA(z) = E(z) \cdot A, \qquad EI(z) = E(z) \cdot I, \qquad GJ(z) = G(z) \cdot J$$

This only works when the geometry is constant and the material is uniform across the section. As soon as either condition is relaxed - multiple materials, tapering geometry, localised degradation - the properties become coupled integrals that cannot be separated.

CSF handles the general case. The section is partitioned into sub-domains $\Omega_i(z)$, each carrying an independent weight law $w_i(z)$:

$$P(z) = \sum_i w_i(z) \cdot \iint_{\Omega_i(z)} f(x, y, z) \, dA$$

The geometry field $\Omega_i(z)$ and the weight field $w_i(z)$ are **fully decoupled**. This allows CSF to represent:

- material variation only — fixed geometry, varying $w_i(z)$
- geometry variation only — morphing polygons, constant weights
- both simultaneously — the fully general case

The classical separable formulation is recovered as a special case when $w_i(z)$ is uniform across all sub-domains.

---

## How the Section Is Defined

The cross-section is defined as a collection of polygons at two end stations. Intermediate geometries are obtained by **vertex interpolation along ruled surfaces** — each vertex moves linearly from its start to end position, creating a smooth tapered geometry.

Each polygon carries an independent weight law $w_i(z)$, defined either analytically (polynomial, exponential) or via a lookup table of discrete values interpolated along $z$.

---

## Core Assumptions

| | Assumption | Implication |
|---|---|---|
| A | Euler-Bernoulli kinematics | Sections remain plane; neutral axis position $Y_{G}(z)$ computed from elastic weights |
| B | Topological constancy | Vertex count per zone is fixed from $z=0$ to $z=L$; zones fade by driving $A_i$ or $w_i$ to zero |
| C | Linear elastic homogenization | All materials referred to a reference modulus $E_{ref}$ via modular ratio $\alpha_i(z)$ |
| D | Perfect bond | No slip between zones; Steiner theorem applies for composite sections |

---

## Note on the Torsional Constant

Some properties — in particular the De Saint-Venant torsional constant $J_{\mathrm{sv}}$ — are not obtained from a direct area integral. They require solving an auxiliary field problem on the section domain and are formally a functional of the geometry: $J_{\mathrm{sv}} = \mathcal{F}(\Omega)$. The treatment of $J_{\mathrm{sv}}$ in CSF is documented separately.

---

## References

- Timoshenko, S.P. & Goodier, J.N. — *Theory of Elasticity*, McGraw-Hill
- Vlasov, V.Z. — *Thin-Walled Elastic Beams*, Israel Program for Scientific Translations
- Pilkey, W.D. — *Analysis and Design of Elastic Beams*, Wiley
