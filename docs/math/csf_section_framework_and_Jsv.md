# Geometric-Material Decomposition and the Role of CSF
## Non-Homogeneous Zonal Polygon Model with Transverse and Longitudinal Variability

---

## 1. Executive Summary and Model Intent

The intent of this formulation is to define a **Engineering Contract** for structural elements where both geometry and material properties vary along the longitudinal axis $z$.
This model maintains a **Functional Representation**. The section is not a static data point but a result of analytical laws and lookup tables, ensuring that at any coordinate $z$, the structural response $(EA, EI)$ is deterministic, traceable, and independent of the solver's mesh density.

---

## 2. Fundamental Assumptions

### A. Kinematic Assumption (Euler-Bernoulli)
We assume that the cross-sections remain plane and perpendicular to the neutral axis after deformation. However, since the section is non-homogeneous, the "Neutral Axis" position $Y_{G,tot}(z)$ is not fixed but is a function of the local distribution of the elastic weights $\alpha_i(z)$.

### B. Topological Constancy
The model assumes that each zone $i$ maintains the same number of vertices $m$ from $z=0$ to $z=L$. This ensures a continuous "ruled surface" transition. If a zone "disappears" (e.g., a reinforcement ending), its area $A_i(z)$ or its elastic weight $\alpha_i(z)$ must be driven to zero, rather than changing the vertex count.

### C. Material Linearity and Homogenization
Non-homogeneity is handled via the **Method of Equivalent Sections**. All materials are transformed into a "Reference Material" (with $E_{ref}$) using the modular ratio $\alpha_i(z)$. The model assumes linear elastic behavior within the infinitesimal step $dz$.

### D. Perfect Bond
It is assumed that all zones $i$ are perfectly bonded. There is no relative slip between, for example, a concrete slab and a steel girder, allowing the use of the Parallel Axis Theorem (Steiner) for the combined section.

---

## 3. Geometric Definition: The Ruled Polygon

Each zone $i$ is a closed polygon. The position of its $j$-th vertex is defined by:

$$V_{j,i}(z) = \begin{bmatrix} x_{j,i}(z) \\ y_{j,i}(z) \end{bmatrix}$$

For a linear transition (tapered elements), we define the trajectory as:

$$x_{j,i}(z) = x_{j,i}^{start} + \frac{z}{L} \Delta x_{j,i} \qquad ; \qquad y_{j,i}(z) = y_{j,i}^{start} + \frac{z}{L} \Delta y_{j,i}$$

where $\Delta = (Value^{end} - Value^{start})$. This creates a ruled surface for each edge of the section.

---

## 4. Material Mapping: Analytical vs. Lookup

The weighting factor $\alpha_i(z)$ defines the mechanical "importance" of zone $i$.

### Option 1: The Analytical Function
Used for continuous variations (e.g., concrete hardening, temperature gradients):

$$\alpha_i(z) = \alpha_{i,0} \cdot e^{-\lambda z} \quad \text{or} \quad \alpha_i(z) = a + bz + cz^2$$

### Option 2: The Lookup Table (Tabular Control)
Used for discrete engineering data (e.g., commercial plate thicknesses, measured material classes):

$$\alpha_i(z) = \mathcal{L}_i(z) \xrightarrow{\text{Interpolation}} \{ (z_0, \alpha_0), (z_1, \alpha_1), \dots, (z_k, \alpha_k) \}$$

---

## 5. Mathematical Integration of Properties

### I. Zonal Geometry (Green's Theorem)
For each zone $i$ at coordinate $z$:

**Area:**
$$A_i(z) = \frac{1}{2} \left| \sum_{j=0}^{m-1} (x_j y_{j+1} - x_{j+1} y_j) \right|$$

**Local Static Moment ($Q_x$):**
$$Q_{x,i}(z) = \frac{1}{6} \sum_{j=0}^{m-1} (y_j + y_{j+1}) (x_j y_{j+1} - x_{j+1} y_j)$$

**Local Moment of Inertia ($I_{xx}$):**
$$I_{xx,i}(z) = \frac{1}{12} \sum_{j=0}^{m-1} (y_j^2 + y_j y_{j+1} + y_{j+1}^2) (x_j y_{j+1} - x_{j+1} y_j)$$

### II. Global Homogenization (Steiner Extension)
Since the section is non-homogeneous, we calculate the **Equivalent Centroid** first:

$$Y_{G,tot}(z) = \frac{\sum_{i=1}^{n} \alpha_i(z) \cdot Q_{x,i}(z)}{\sum_{i=1}^{n} \alpha_i(z) \cdot A_i(z)}$$

Then, the **Equivalent Flexural Stiffness** (referred to $E_{ref}$):

$$(EI)_{eq}(z) = E_{ref} \cdot \sum_{i=1}^{n} \alpha_i(z) \cdot \left[ I_{xx,i}(z) + A_i(z) \cdot (y_{G,i}(z) - Y_{G,tot}(z))^2 \right]$$

where $y_{G,i}(z) = Q_{x,i}(z) / A_i(z)$.

---

## 6. Extended Applications (Lookup Table Utility)

The lookup table is not limited to $\alpha$. It can govern any property $\Psi_i(z)$:

- **Mass per unit length:** $w(z) = \sum \text{Lookup}_{\rho,i}(z) \cdot A_i(z)$
- **Thermal Curvature:** $\chi_{\Delta T}(z) = \dfrac{\sum \alpha_i(z) A_i(z) \beta_i(z) \Delta T_i(z) (y_{G,i} - Y_{G,tot})}{(EI)_{eq}/E_{ref}}$

---

## 7. General Formulation

In standard beam models, sectional stiffness properties follow a simple multiplicative structure:

$$EA(z) = E(z) \cdot A, \qquad EI(z) = E(z) \cdot I, \qquad GJ(z) = G(z) \cdot J$$

This holds as long as the cross-section geometry is constant along the axis and the material is uniform across the section. Under these conditions, the geometric quantities $A$, $I$, $J$ are computed once, and longitudinal variation is carried entirely by the material functions $E(z)$, $G(z)$, $\rho(z)$.

This separability breaks down as soon as either condition is relaxed — material varying within the section, multiple materials, tapering geometry, or any combination of these. In the general case, sectional properties become coupled geometric-material integrals that cannot be reduced to a product of independent terms.

The most general expression for a section property is:

$$P(z) = \sum_i w_i(z) \cdot \iint_{\Omega_i(z)} f(x, y, z) \, dA$$

The cross-section at each station $z$ is partitioned into sub-domains $\Omega_i(z)$, each carrying its own independent weight law $w_i(z)$. Unlike simplified formulations where a single material function scales the entire section, here each polygon is assigned its own longitudinal law — independently of all others and independently of the geometry field. This is the key degree of freedom that makes the formulation general: the same integral structure accommodates uniform sections, graded materials, localised degradation, and any combination of these, without changing the form of the equation. The classical separable formulation is recovered as a special case when $w_i(z) = m(z)$ is uniform across all sub-domains.

---

## 8. What CSF Does

CSF evaluates this integral continuously along $z$. The cross-section is defined as a collection of polygons at two end stations; intermediate geometries are obtained by vertex interpolation along ruled surfaces. Each polygon carries an independent weight law $w_i(z)$, defined analytically or via lookup expressions.

The geometry field $\Omega_i(z)$ and the weight field $w_i(z)$ are fully decoupled, which allows CSF to represent any combination of:

- material variation only — fixed geometry, varying $w_i(z)$
- geometry variation only — morphing polygons, constant weights
- both simultaneously — the fully general case

From this continuous description, CSF evaluates $A(z)$, $I(z)$, $EA(z)$, $EI(z)$, $GJ(z)$ at any $z$ and exports solver-ready station data for OpenSees and SAP2000.

> **Note.** Some properties — such as the Saint-Venant torsional constant $J_{\mathrm{sv}}$ — are not obtained from a direct integral with a fixed kernel $f$. They require solving an auxiliary field problem on the section domain and are formally a functional of the geometry: $J_{\mathrm{sv}} = \mathcal{F}(\Omega)$. The treatment of $J_{\mathrm{sv}}$ in CSF is described in the following section.

---

