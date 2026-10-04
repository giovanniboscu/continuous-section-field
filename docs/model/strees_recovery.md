# DRAFT


# Stress Recovery via 3D Cauchy Equilibrium Equations in CSF-CUF 1D

In the **Carrera Unified Formulation (CUF)** for 1D beam theories, stress recovery via the 3D Cauchy differential equilibrium equations can be used as a post-processing procedure.

The objective is to start from the stress field directly obtained from the CUF displacement solution and reconstruct a stress field that satisfies local 3D equilibrium and the relevant boundary conditions more accurately.

For **CSF-CUF**, the recovery should not be tied to a privileged transverse direction such as the laminate thickness direction $z$. The cross-section may have an arbitrary geometry, multiple polygons, spatially varying material properties, and longitudinally varying geometry and constitutive fields.

The natural formulation is therefore based on the full local equilibrium equations and, for the recovery of the axial shear stresses, on a 2D problem over the cross-sectional domain.

---

## 1. CUF Kinematic Expansion

Consider a 1D beam with longitudinal coordinate $x$ and cross-section domain $\Omega(x)$ described by transverse coordinates $(y,z)$.

The 3D displacement field is expanded as:

$$
\mathbf{u}(x,y,z) = F_\tau(y,z;x)\,\mathbf{u}_\tau(x), \qquad \tau = 1,2,\dots,M
$$

where:

* $F_\tau(y,z;x)$ are the cross-sectional expansion functions;
* $\mathbf{u}_\tau(x)=[u_{x\tau},u_{y\tau},u_{z\tau}]^T$ contains the generalized longitudinal displacement unknowns;
* the dependence of $F_\tau$ on $x$ is written explicitly because, in CSF-CUF, the physical cross-section may vary continuously along the beam;
* Einstein summation convention applies to repeated indices.

For a prismatic CUF model, $F_\tau$ may depend only on $(y,z)$. For a non-prismatic CSF model, the mapping between the reference and physical cross-section may introduce an explicit $x$ dependence.

---

## 2. Raw Strain and Stress Fields

From the CUF displacement field, the strain field is obtained kinematically:

$$
\boldsymbol{\epsilon}^{H} = \mathbf{D}\mathbf{u}
$$

where $\mathbf{D}$ is the 3D differential strain operator.

The corresponding constitutive stress field is:

$$
\boldsymbol{\sigma}^{H}(x,y,z) = \mathbf{C}(x,y,z)\, \boldsymbol{\epsilon}^{H}(x,y,z)
$$

with:

$$
\boldsymbol{\sigma}^{H} = \begin{bmatrix} \sigma_{xx}^{H} & \sigma_{yy}^{H} & \sigma_{zz}^{H} & \tau_{yz}^{H} & \tau_{xz}^{H} & \tau_{xy}^{H} \end{bmatrix}^{T}
$$

The superscript $H$ identifies the stress field obtained directly from the displacement approximation through the constitutive law.

For example, the axial normal stress may be written in the general anisotropic form:

$$
\sigma_{xx}^{H} = C_{11}\epsilon_{xx}^{H} + C_{12}\epsilon_{yy}^{H} + C_{13}\epsilon_{zz}^{H} + C_{14}\gamma_{yz}^{H} + C_{15}\gamma_{xz}^{H} + C_{16}\gamma_{xy}^{H}
$$

and, after substituting the CUF expansion, terms of the form

$$
F_\tau\frac{d u_{x\tau}}{dx}, \qquad \frac{\partial F_\tau}{\partial y}u_{y\tau}, \qquad \frac{\partial F_\tau}{\partial z}u_{z\tau}
$$

appear naturally.

---

## 3. Local 3D Cauchy Equilibrium Residual

The static equilibrium equations are:

$$
\nabla\cdot\boldsymbol{\sigma} + \mathbf{b} = \mathbf{0}
$$

where $\mathbf{b}=[b_x,b_y,b_z]^T$ is the body-force vector per unit volume.

Written component-wise:

$$
\frac{\partial \sigma_{xx}}{\partial x} + \frac{\partial \tau_{xy}}{\partial y} + \frac{\partial \tau_{xz}}{\partial z} + b_x = 0
$$

$$
\frac{\partial \tau_{xy}}{\partial x} + \frac{\partial \sigma_{yy}}{\partial y} + \frac{\partial \tau_{yz}}{\partial z} + b_y = 0
$$

$$
\frac{\partial \tau_{xz}}{\partial x} + \frac{\partial \tau_{yz}}{\partial y} + \frac{\partial \sigma_{zz}}{\partial z} + b_z = 0
$$

The raw CUF stress field does not, in general, satisfy these equations pointwise.

The local equilibrium residual is therefore defined as:

$$
\mathbf{r}^{H} = \nabla\cdot\boldsymbol{\sigma}^{H} + \mathbf{b}
$$

with:

$$
r_x^{H} = \frac{\partial \sigma_{xx}^{H}}{\partial x} + \frac{\partial \tau_{xy}^{H}}{\partial y} + \frac{\partial \tau_{xz}^{H}}{\partial z} + b_x
$$

$$
r_y^{H} = \frac{\partial \tau_{xy}^{H}}{\partial x} + \frac{\partial \sigma_{yy}^{H}}{\partial y} + \frac{\partial \tau_{yz}^{H}}{\partial z} + b_y
$$

$$
r_z^{H} = \frac{\partial \tau_{xz}^{H}}{\partial x} + \frac{\partial \tau_{yz}^{H}}{\partial y} + \frac{\partial \sigma_{zz}^{H}}{\partial z} + b_z
$$

The condition of exact local equilibrium is:

$$
\mathbf{r}^{H} = \mathbf{0}
$$

The field $\mathbf{r}^{H}$ therefore provides a direct local measure of the imbalance of the raw CUF stress field.

---

## 4. Recovery of the Axial Shear Stress Vector

The first equilibrium equation is:

$$
\frac{\partial \sigma_{xx}}{\partial x} + \frac{\partial \tau_{xy}}{\partial y} + \frac{\partial \tau_{xz}}{\partial z} + b_x = 0
$$

Define the transverse shear vector associated with the axial direction:

$$
\boldsymbol{\tau}_x = \begin{bmatrix} \tau_{xy}\\ \tau_{xz} \end{bmatrix}
$$

and the cross-sectional differential operator:

$$
\nabla_\Omega = \begin{bmatrix} \partial/\partial y\\ \partial/\partial z \end{bmatrix}
$$

Then:

$$
\nabla_\Omega\cdot\boldsymbol{\tau}_x = -\frac{\partial\sigma_{xx}}{\partial x} -b_x
$$

For recovery, the axial normal stress $\sigma_{xx}^{H}$ obtained from the CUF solution is retained as the primary stress field and the shear vector is reconstructed.

Thus:

$$
\nabla_\Omega\cdot\boldsymbol{\tau}_x^{rec} = -\frac{\partial\sigma_{xx}^{H}}{\partial x} -b_x
$$

This equation is defined over the complete cross-sectional domain $\Omega(x)$.

---

## 5. Why a Direct 1D Integration Along $z$ Is Not General Enough

For plate or laminate problems one often writes:

$$
\frac{\partial \tau_{xz}}{\partial z} = - \left( \frac{\partial\sigma_{xx}^{H}}{\partial x} + \frac{\partial\tau_{xy}^{H}}{\partial y} + b_x \right)
$$

and integrates along $z$:

$$
\tau_{xz}^{rec}(x,y,z) = \tau_{xz}(x,y,z_0) - \int_{z_0}^{z} \left( \frac{\partial\sigma_{xx}^{H}}{\partial x} + \frac{\partial\tau_{xy}^{H}}{\partial y} + b_x \right) dz'
$$

This approach assumes that a physically meaningful preferred integration direction exists.

For a general CSF section this is not guaranteed.

Examples include:

* I-sections;
* T-sections;
* C-sections;
* multi-polygon cross-sections;
* sections with holes;
* sections composed of different material subdomains;
* non-prismatic sections whose geometry varies continuously with $x$.

For these geometries, the 2D cross-sectional equilibrium formulation is more natural.

---

## 6. Non-Uniqueness of the Shear Recovery Problem

The equation

$$
\nabla_\Omega\cdot\boldsymbol{\tau}_x^{rec} = -\frac{\partial\sigma_{xx}^{H}}{\partial x} -b_x
$$

is one scalar equation for two unknown fields:

$$
\tau_{xy}^{rec}, \qquad \tau_{xz}^{rec}
$$

Therefore the recovered shear field is not uniquely determined by equilibrium alone.

An additional condition is required.

A natural choice for CSF-CUF is to search for the equilibrated field that differs as little as possible from the original CUF stress field.

Let:

$$
\boldsymbol{\tau}_x^{H} = \begin{bmatrix} \tau_{xy}^{H}\\ \tau_{xz}^{H} \end{bmatrix}
$$

and define:

$$
\boldsymbol{\tau}_x^{rec} = \boldsymbol{\tau}_x^{H} + \delta\boldsymbol{\tau}_x
$$

The correction can be defined by minimizing:

$$
J = \frac{1}{2} \int_{\Omega} \left\| \boldsymbol{\tau}_x^{rec} - \boldsymbol{\tau}_x^{H} \right\|^2 d\Omega
$$

subject to:

$$
\nabla_\Omega\cdot\boldsymbol{\tau}_x^{rec} = -\frac{\partial\sigma_{xx}^{H}}{\partial x} -b_x
$$

and the appropriate boundary conditions.

This gives a precise interpretation:

> the recovered stress field is the closest admissible field to the raw CUF stress field that satisfies local equilibrium.

---

## 7. Potential Correction and Poisson Problem

A convenient form for the correction is:

$$
\delta\boldsymbol{\tau}_x = \nabla_\Omega\phi_x
$$

where $\phi_x(y,z)$ is a scalar correction potential.

Thus:

$$
\boldsymbol{\tau}_x^{rec} = \boldsymbol{\tau}_x^{H} + \nabla_\Omega\phi_x
$$

or explicitly:

$$
\tau_{xy}^{rec} = \tau_{xy}^{H} + \frac{\partial\phi_x}{\partial y}
$$

$$
\tau_{xz}^{rec} = \tau_{xz}^{H} + \frac{\partial\phi_x}{\partial z}
$$

Substituting into equilibrium:

$$
\nabla_\Omega\cdot \left( \boldsymbol{\tau}_x^{H} + \nabla_\Omega\phi_x \right) = -\frac{\partial\sigma_{xx}^{H}}{\partial x} -b_x
$$

Therefore:

$$
\nabla_\Omega^2\phi_x = - \left( \frac{\partial\sigma_{xx}^{H}}{\partial x} + \nabla_\Omega\cdot\boldsymbol{\tau}_x^{H} + b_x \right)
$$

Using the raw equilibrium residual:

$$
r_x^{H} = \frac{\partial\sigma_{xx}^{H}}{\partial x} + \nabla_\Omega\cdot\boldsymbol{\tau}_x^{H} + b_x
$$

the recovery equation becomes:

$$
\boxed{ \nabla_\Omega^2\phi_x = -r_x^{H} }
$$

and the recovered shear stresses are:

$$
\boxed{ \tau_{xy}^{rec} = \tau_{xy}^{H} + \frac{\partial\phi_x}{\partial y} }
$$

$$
\boxed{ \tau_{xz}^{rec} = \tau_{xz}^{H} + \frac{\partial\phi_x}{\partial z} }
$$

This provides a direct link between the local imbalance of the raw CUF stress field and the stress correction.

---

## 8. Boundary Conditions on the Physical Cross-Section

Let the outward unit normal on the cross-sectional boundary be:

$$
\mathbf{n}_\Omega = \begin{bmatrix} n_y\\ n_z \end{bmatrix}
$$

The traction component in the axial direction is:

$$
t_x = n_y\tau_{xy} + n_z\tau_{xz}
$$

or:

$$
t_x = \boldsymbol{\tau}_x\cdot\mathbf{n}_\Omega
$$

On a free lateral surface:

$$
\boldsymbol{\tau}_x^{rec}\cdot\mathbf{n}_\Omega = 0
$$

On a surface carrying a prescribed axial traction $\bar{t}_x$:

$$
\boldsymbol{\tau}_x^{rec}\cdot\mathbf{n}_\Omega = \bar{t}_x
$$

Using the potential correction:

$$
\left( \boldsymbol{\tau}_x^{H} + \nabla_\Omega\phi_x \right) \cdot \mathbf{n}_\Omega = \bar{t}_x
$$

Therefore the Neumann condition for $\phi_x$ is:

$$
\frac{\partial\phi_x}{\partial n} = \bar{t}_x - \boldsymbol{\tau}_x^{H}\cdot\mathbf{n}_\Omega
$$

For a free boundary:

$$
\frac{\partial\phi_x}{\partial n} = - \boldsymbol{\tau}_x^{H}\cdot\mathbf{n}_\Omega
$$

---

## 9. Compatibility Condition of the Cross-Sectional Recovery Problem

A pure Neumann Poisson problem requires a compatibility condition.

Integrating:

$$
\nabla_\Omega^2\phi_x = -r_x^{H}
$$

over $\Omega$ gives:

$$
\int_\Omega \nabla_\Omega^2\phi_x \,d\Omega = - \int_\Omega r_x^{H} \,d\Omega
$$

Using the divergence theorem:

$$
\int_{\partial\Omega} \frac{\partial\phi_x}{\partial n} \,ds = - \int_\Omega r_x^{H} \,d\Omega
$$

Substituting the boundary condition:

$$
\int_{\partial\Omega} \left( \bar{t}_x - \boldsymbol{\tau}_x^{H}\cdot\mathbf{n}_\Omega \right) ds = - \int_\Omega r_x^{H} \,d\Omega
$$

This relation expresses global consistency between the prescribed boundary tractions and the internal equilibrium residual.

If numerical quadrature, approximation errors, or discrete FE effects make the compatibility condition imperfect, a practical implementation must decide how to remove the small incompatible mean component before solving the Poisson problem.

---

## 10. Gauge Condition

For a pure Neumann problem, $\phi_x$ is defined only up to an additive constant.

A gauge condition must therefore be imposed, for example:

$$
\int_\Omega \phi_x\,d\Omega = 0
$$

or alternatively:

$$
\phi_x(y_0,z_0) = 0
$$

at one reference point.

The additive constant does not affect the recovered stresses because only the derivatives of $\phi_x$ are used.

---

## 11. Multiple CSF Polygons and Material Subdomains

In CSF a cross-section may be composed of several polygons or material domains.

Let:

$$
\Omega = \bigcup_{k=1}^{N_d} \Omega_k
$$

where each $\Omega_k$ is a CSF domain.

Inside each domain:

$$
\nabla_\Omega^2\phi_x^{(k)} = -r_x^{H,(k)}
$$

At a physical external boundary, the prescribed traction condition is applied.

At an internal interface $\Gamma_{ij}$ between domains $\Omega_i$ and $\Omega_j$, traction continuity requires:

$$
\boldsymbol{\tau}_x^{rec,(i)} \cdot \mathbf{n}_{ij} = \boldsymbol{\tau}_x^{rec,(j)} \cdot \mathbf{n}_{ij}
$$

where $\mathbf{n}_{ij}$ is the normal to the interface.

Equivalently:

$$
\left[ \boldsymbol{\tau}_x^{rec}\cdot\mathbf{n} \right]_{\Gamma_{ij}} = 0
$$

For perfect bonding, displacement continuity is already handled by the structural model, while stress recovery must preserve traction equilibrium across the interface.

An implementation may either solve the recovery globally over the complete connected cross-section or solve domain-wise problems with explicit interface constraints.

---

## 12. Variable Material Properties

In CSF the constitutive tensor may be spatially variable:

$$
\mathbf{C} = \mathbf{C}(x,y,z)
$$

Therefore:

$$
\boldsymbol{\sigma}^{H} = \mathbf{C}(x,y,z) \boldsymbol{\epsilon}^{H}(x,y,z)
$$

and:

$$
\frac{\partial\boldsymbol{\sigma}^{H}}{\partial x} = \frac{\partial\mathbf{C}}{\partial x} \boldsymbol{\epsilon}^{H} + \mathbf{C} \frac{\partial\boldsymbol{\epsilon}^{H}}{\partial x}
$$

Thus, in general:

$$
\frac{\partial\sigma_{xx}^{H}}{\partial x}
$$

cannot be computed by differentiating only the longitudinal generalized displacement variables.

The derivative of the material field must also be included whenever the constitutive properties vary along $x$.

This is particularly important in CSF because geometry and material properties are treated as continuous fields.

---

## 13. Variable Geometry

For a non-prismatic section, the physical cross-section depends on $x$:

$$
\Omega = \Omega(x)
$$

and the physical mapping may be written as:

$$
(y,z) = \mathbf{S}(x,\eta,\zeta)
$$

where $(\eta,\zeta)$ are reference cross-sectional coordinates.

Consequently, derivatives with respect to $x$ may contain contributions from both:

* the longitudinal variation of the generalized CUF unknowns;
* the longitudinal variation of the section mapping.

Therefore the derivative:

$$
\frac{\partial\sigma_{xx}^{H}}{\partial x}
$$

must be interpreted as the derivative of the actual physical stress field at the physical point under consideration.

In an implementation this distinction must be explicit, especially when stress values are evaluated by mapping reference quadrature or sampling points to a continuously varying physical section.

---

## 14. Longitudinal Derivatives and $C^0$ Finite Elements

In a standard CUF 1D implementation with Lagrange finite elements along $x$, the longitudinal interpolation is generally $C^0$ across element boundaries.

Inside each element, the FE polynomial can be differentiated analytically.

However, higher derivatives are not automatically continuous across element boundaries.

For this reason, statements such as:

> third longitudinal derivatives are readily available because CUF beam elements have high-order continuity

are not generally valid for a standard $C^0$ Lagrange FE discretization.

For CSF-CUF stress recovery, possible strategies include:

* analytical differentiation inside each longitudinal element;
* numerical differentiation of already reconstructed physical fields;
* patch recovery across neighboring longitudinal elements;
* projection of derivatives onto a smoother auxiliary field.

The recovery method should not rely on global $C^1$ or $C^2$ continuity unless such continuity is explicitly present in the longitudinal approximation.

---

## 15. Extension to the Remaining Equilibrium Equations

After recovering $\tau_{xy}$ and $\tau_{xz}$ from the first equilibrium equation, the remaining equations are:

$$
\frac{\partial \tau_{xy}^{rec}}{\partial x} + \frac{\partial \sigma_{yy}}{\partial y} + \frac{\partial \tau_{yz}}{\partial z} + b_y = 0
$$

$$
\frac{\partial \tau_{xz}^{rec}}{\partial x} + \frac{\partial \tau_{yz}}{\partial y} + \frac{\partial \sigma_{zz}}{\partial z} + b_z = 0
$$

These equations can be used to recover the remaining transverse stresses:

$$
\sigma_{yy}^{rec}, \qquad \sigma_{zz}^{rec}, \qquad \tau_{yz}^{rec}
$$

However, these three unknown fields are coupled through two equilibrium equations, so equilibrium alone is again insufficient to determine a unique solution.

A second constrained recovery problem is therefore required.

A possible formulation is:

$$
\boldsymbol{\sigma}_{\perp}^{rec} = \boldsymbol{\sigma}_{\perp}^{H} + \delta\boldsymbol{\sigma}_{\perp}
$$

with:

$$
\boldsymbol{\sigma}_{\perp} = \begin{bmatrix} \sigma_{yy}\\ \sigma_{zz}\\ \tau_{yz} \end{bmatrix}
$$

and a minimum-correction functional of the form:

$$
J_\perp = \frac{1}{2} \int_\Omega \left\| \boldsymbol{\sigma}_{\perp}^{rec} - \boldsymbol{\sigma}_{\perp}^{H} \right\|^2 d\Omega
$$

subject to the two remaining equilibrium equations and the transverse traction boundary conditions.

This second stage should be treated separately from the first axial-shear recovery problem.

---

## 16. Surface Traction Conditions for the Full 3D Stress Tensor

For a lateral surface of the beam with normal:

$$
\mathbf{n} = \begin{bmatrix} 0\\ n_y\\ n_z \end{bmatrix}
$$

the traction vector is:

$$
\mathbf{t} = \boldsymbol{\sigma}\mathbf{n}
$$

or:

$$
t_x = \tau_{xy}n_y + \tau_{xz}n_z
$$

$$
t_y = \sigma_{yy}n_y + \tau_{yz}n_z
$$

$$
t_z = \tau_{yz}n_y + \sigma_{zz}n_z
$$

On a free lateral surface:

$$
\mathbf{t} = \mathbf{0}
$$

therefore:

$$
\tau_{xy}n_y + \tau_{xz}n_z = 0
$$

$$
\sigma_{yy}n_y + \tau_{yz}n_z = 0
$$

$$
\tau_{yz}n_y + \sigma_{zz}n_z = 0
$$

These are the physically meaningful boundary conditions for a general arbitrarily oriented cross-sectional boundary.

They are preferable to conditions such as:

$$
\tau_{xz}=0
$$

or:

$$
\sigma_{zz}=0
$$

unless the local boundary orientation makes those simplified conditions valid.

---

## 17. Local Recovery at a Generic Point

For a generic physical point:

$$
P=(x,y,z)
$$

the CSF-STRESS post-processor can conceptually perform the following sequence:

1. reconstruct the CUF displacement field at $P$;
2. reconstruct the strain field $\boldsymbol{\epsilon}^{H}(P)$;
3. query the CSF geometry and material fields at $P$;
4. compute the constitutive stress field $\boldsymbol{\sigma}^{H}(P)$;
5. compute the required spatial derivatives;
6. evaluate the local residual:

$$
\mathbf{r}^{H}(P) = \nabla\cdot\boldsymbol{\sigma}^{H}(P) + \mathbf{b}(P)
$$

7. solve the appropriate cross-sectional recovery problem;
8. evaluate the corrected stress field:

$$
\boldsymbol{\sigma}^{rec}(P)
$$

Thus the recovered field remains directly connected to the original CUF solution but is corrected using the local physical equilibrium equations.

---

## 18. Recommended First CSF-STRESS Milestone

The first implementation should be deliberately limited to recovery of:

$$
\tau_{xy} \qquad\text{and}\qquad \tau_{xz}
$$

from the axial equilibrium equation:

$$
\frac{\partial \sigma_{xx}^{H}}{\partial x} + \frac{\partial \tau_{xy}^{rec}}{\partial y} + \frac{\partial \tau_{xz}^{rec}}{\partial z} + b_x = 0
$$

The implementation sequence can be:

### Step 1 — Evaluate raw CUF stresses

Compute:

$$
\sigma_{xx}^{H}, \qquad \tau_{xy}^{H}, \qquad \tau_{xz}^{H}
$$

over the cross-section.

### Step 2 — Evaluate the axial equilibrium residual

Compute:

$$
r_x^{H} = \frac{\partial\sigma_{xx}^{H}}{\partial x} + \frac{\partial\tau_{xy}^{H}}{\partial y} + \frac{\partial\tau_{xz}^{H}}{\partial z} + b_x
$$

### Step 3 — Solve the cross-sectional Poisson problem

Solve:

$$
\nabla_\Omega^2\phi_x = -r_x^{H}
$$

with:

$$
\frac{\partial\phi_x}{\partial n} = \bar{t}_x - \boldsymbol{\tau}_x^{H}\cdot\mathbf{n}_\Omega
$$

and a gauge condition such as:

$$
\int_\Omega \phi_x\,d\Omega=0
$$

### Step 4 — Recover the shear stresses

Compute:

$$
\tau_{xy}^{rec} = \tau_{xy}^{H} + \frac{\partial\phi_x}{\partial y}
$$

$$
\tau_{xz}^{rec} = \tau_{xz}^{H} + \frac{\partial\phi_x}{\partial z}
$$

### Step 5 — Verify the recovered field

Evaluate:

$$
r_x^{rec} = \frac{\partial\sigma_{xx}^{H}}{\partial x} + \frac{\partial\tau_{xy}^{rec}}{\partial y} + \frac{\partial\tau_{xz}^{rec}}{\partial z} + b_x
$$

The expected result is:

$$
r_x^{rec} \approx 0
$$

up to numerical discretization and quadrature errors.

---

## 19. Conceptual CSF-STRESS Flow

The complete conceptual chain is:

$$
\boxed{ \text{CUF displacement solution} \rightarrow \boldsymbol{\sigma}^{H} \rightarrow \mathbf{r}^{H} = \nabla\cdot\boldsymbol{\sigma}^{H} + \mathbf{b} \rightarrow \text{equilibrium recovery} \rightarrow \boldsymbol{\sigma}^{rec} }
$$

The central idea is therefore not to discard the constitutive CUF stress field, but to use it as the initial physical estimate and correct only the part required to restore local equilibrium and boundary traction consistency.

For the first recovery stage:

$$
\boxed{ r_x^{H} \rightarrow \nabla_\Omega^2\phi_x = -r_x^{H} \rightarrow \left( \tau_{xy}^{rec}, \tau_{xz}^{rec} \right) }
$$

This formulation is naturally compatible with the CSF concept because it works directly with continuous geometry, material fields, physical boundaries, and pointwise section information.
