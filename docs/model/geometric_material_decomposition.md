# CSF Section Model - A Continuous, Zone-Based Formulation

---

## What CSF Does

Homogenization of composite sections (concrete/steel), area and moment integrals via Green's theorem, the Steiner parallel axis theorem - these are all standard tools.

What CSF is a specific **organisational model**: geometry and material are treated as two fully independent fields along $z$, and every zone carries its own weight law - separately from all others and separately from the geometry. This simple structure is what makes the formulation general without adding complexity.

In practice, CSF evaluates structural quantities - derived from continuously varying section geometry and material along the element - such as- $A(z)$, $Ix(z)$, $Iy(z)$,... - continuously along the element. The result is deterministic and traceable at every point, independent of the solver's mesh density.

---

## The Key Idea

In a standard beam model, section properties are just a number times a material function:

$$EA(z) = E(z) \cdot A, \qquad EI(z) = E(z) \cdot I, \qquad GJ(z) = G(z) \cdot J$$

This works fine for uniform sections with a single material. It breaks down as soon as you have multiple materials, a tapered geometry, localised degradation, or any combination of these.

CSF handles the general case by splitting the section into zones, each with its own independent weight law $w_i(z)$:

$$P(z) = \sum_i w_i(z) \cdot \iint_{\Omega_i(z)} f(x, y, z) \, dA$$

Geometry ($\Omega_i$) and material weight ($w_i$) are fully decoupled -
you can vary one without touching the other. The standard separable formulation is just the special case where all $w_i(z)$ are the same function.

---

## How the Section Is Defined

You define the section as a set of polygons at two end stations. CSF interpolates the vertices linearly between them, producing a smooth tapered geometry at any $z$.

Each polygon gets its own weight law $w_i(z)$ - either an analytical expression (polynomial, exponential) or a lookup table of discrete values. That's it.

---

## Assumptions

| | Assumption | What it means in practice |
|---|---|---|
| A | Fixed topology | Vertex count per zone is constant along z - sections with openings that appear or disappear are not supported |
| B | Linear vertex interpolation | Zone geometry is interpolated linearly between the two end station |
| C | Polygonal representation | Curved boundaries must be approximated by polygon discretisation |
 D | Straight element axis | CSF models a single element along a straight z-axis -curved members are not supported |
 > CSF operates in absolute coordinates, allowing multiple straight elements to be composed in sequence - each with its own geometry and material field - to represent members of arbitrary length and varying cross-sectional evolution.
---

## Note on the Torsional Constant

$J_{\mathrm{sv}}$ is the one exception: it cannot be obtained from a direct area integral. It depends on the full geometry of the section in a more complex way and is treated separately in CSF.

See: [De Saint-Venant Torsional Constant — Cell and Wall Contributions in CSF](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md)

---

## References

- Timoshenko & Goodier — *Theory of Elasticity*, McGraw-Hill
- Vlasov — *Thin-Walled Elastic Beams*, Israel Program for Scientific Translations
- Pilkey — *Analysis and Design of Elastic Beams*, Wiley
