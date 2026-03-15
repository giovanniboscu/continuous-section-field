# Geometric-Material Decomposition and the Role of CSF

In standard beam models, sectional stiffness properties follow a simple multiplicative structure:

$$EA(z) = E(z) \cdot A, \qquad EI(z) = E(z) \cdot I, \qquad GJ(z) = G(z) \cdot J$$

This holds as long as the cross-section geometry is constant along the axis and the material is uniform across the section. Under these conditions, the geometric quantities $A$, $I$, $J$ are computed once, and longitudinal variation is carried entirely by the material functions $E(z)$, $G(z)$, $\rho(z)$.

This separability breaks down as soon as either condition is relaxed - material varying within the section, multiple materials, tapering geometry, or any combination of these. In the general case, sectional properties become coupled geometric-material integrals that cannot be reduced to a product of independent terms.

## General Formulation

The most general expression for a section property is:

$$P(z) = \sum_i w_i(z) \cdot \iint_{\Omega_i(z)} f(x, y, z) \, dA$$

The cross-section at each station $z$ is partitioned into sub-domains $\Omega_i(z)$, each carrying its own independent weight law $w_i(z)$. Unlike classical formulations where a single material function scales the entire section, here each polygon is assigned its own longitudinal law - independently of all others and independently of the geometry field. This is the key degree of freedom that makes the formulation general: the same integral structure accommodates uniform sections, graded materials, localised degradation, and any combination of these, without changing the form of the equation. The classical separable formulation is recovered as a special case when $w_i(z) = m(z)$ is uniform across all sub-domains.

## What CSF Does

CSF evaluates this integral continuously along $z$. The cross-section is defined as a collection of polygons at two end stations; intermediate geometries are obtained by vertex interpolation along ruled surfaces. Each polygon carries an independent weight law $w_i(z)$, defined analytically or via lookup expressions.

The geometry field $\Omega_i(z)$ and the weight field $w_i(z)$ are fully decoupled, which allows CSF to represent any combination of:

- material variation only - fixed geometry, varying $w_i(z)$
- geometry variation only -morphing polygons, constant weights
- both simultaneously --- the fully general case

From this continuous description, CSF evaluates $A(z)$, $I(z)$, $EA(z)$, $EI(z)$, $GJ(z)$ at any $z$ and exports solver-ready station data for OpenSees and SAP2000.

---

> **Note.** Some properties - such as the Saint-Venant torsional constant $J_\text{sv}$ - are not obtained from a direct integral with a fixed kernel $f$. They require solving an auxiliary field problem on the section domain and are formally a functional of the geometry: $J_\text{sv} = \mathcal{F}(\Omega)$.
