# CSF-CUF: Coupling a Continuous Geometry-Material Field to the Carrera Unified Formulation

## 1. Scope and central premise

The purpose of this formulation is to introduce **a continuous physical field of geometry and material properties as a primary mathematical object in the Carrera Unified Formulation (CUF)**. The Continuous Section Field (CSF) supplies this object independently of the choice of CUF expansion, longitudinal discretization, and solution method. The contribution is the **coupling of that physical field to the CUF variational and nuclear operators**.

The physical member is described by a prescribed continuous sectional state, denoted by

```math
\mathcal{S}(x), \qquad 0 \leq x \leq L.
```

At each longitudinal coordinate, this state supplies the actual physical section, its material sub-domains, their boundaries, and the spatially distributed constitutive properties:

```math
\mathcal{S}(x) \longmapsto
\left\{\Omega^k(x),\ \partial\Omega^k(x),\
\mathbf{C}^k(x,y,z)\right\}_{k=1}^{N_\Omega}.
```

In this notation $x$ is the longitudinal coordinate, $y,z$ are transverse physical coordinates, $k$ identifies a sectional sub-domain, and $\mathbf C^k$ is its constitutive matrix. The beam occupies

```math
\mathcal{V} = \left\{(x,y,z):0 < x < L,\ (y,z)\in\Omega(x)\right\},
\qquad
\Omega(x)=\bigcup_{k=1}^{N_\Omega}\Omega^k(x).
```

The CSF field is **prescribed input data**, not an unknown of the structural boundary-value problem. Its role is to define the physical member at every admissible longitudinal station. Continuity here refers to the sectional description along the axis wherever the geometry varies smoothly; it does not require material coefficients to be continuous across interfaces between distinct sub-domains. The CSF representation may be analytical or numerical, provided that its domains, material values and relevant geometric measures can be evaluated with the regularity required by the variational operations.

The two physical dependencies are independent in principle: the domains $\Omega^k(x)$ describe evolving geometry, while $\mathbf C^k(x,y,z)$ describes evolving and possibly heterogeneous material. Neither is inferred from the CUF displacement approximation.

The mathematical objective is to carry both physical fields through sectional integration, the principle of virtual displacements, the fundamental nuclei, generalized loading, and field reconstruction. **The CSF description is therefore an input to the mathematical formulation, not merely a preprocessing convention.**

The direct mathematical consequences are distinct. A change in $\Omega^k(x)$ changes the physical region over which each sectional coefficient is integrated. A change in $\mathbf C^k(x,y,z)$ changes the constitutive weighting of its integrand. When the chosen sectional basis follows the evolving geometry, $F_\tau(x,y,z)$ and its physical derivatives can also change, contributing additional terms to the same coefficients. These changes are transmitted to the CUF nucleus **through the values of the sectional integrals**, without prescribing a new nuclear formula for each physical member.

The formulation also admits transverse CUF functions $F_\tau(x,y,z)$ whose *physical evaluation* changes with the section. Their longitudinal derivatives are included to make the variational derivation consistent with that choice. This is a **kinematic completion of the CSF-CUF coupling**, rather than its defining purpose. The case $F_{\tau,x}=0$ is retained as a valid specialization.

The development is self-contained and leaves the longitudinal solution technique unspecified.

---

## 2. The continuous geometry-material field and its interface to CUF

At a requested station $x$, the **prescribed** CSF supplies $\mathcal S(x)$ and hence the physical integration domains, the constitutive entries at physical points, and the boundaries on which loads or interface conditions act. The resulting fields need not be given in closed analytical form: they need to be evaluable at the stations and points required by the variational formulation. A geometric/material interpolation, an analytic description or a suitable numerical representation may provide these queries. **That representation is not an additional CUF unknown**, and choosing it does not alter the generic nuclear operator. It must, however, provide the physical derivatives and boundary measures needed by the particular kinematic and loading choices.

For each sub-domain, the constitutive matrix is a spatial field

```math
\mathbf C^k:\ (x,y,z)\longmapsto \mathbf C^k(x,y,z),
\qquad (y,z)\in\Omega^k(x).
```

Its components and the physical domains enter the sectional coefficients directly. If the CUF transverse basis follows the physical section, its evaluation and derivatives are determined using the current sectional state *and* the independently selected approximation family:

```math
\bigl(\mathcal S(x),\ \text{CUF expansion family}\bigr)
\longmapsto
\left\{F_\tau(x,y,z),\ F_{\tau,x},\ F_{\tau,y},\ F_{\tau,z}\right\}.
```

This expression does not identify the CSF field with the CUF functions: they retain different roles. It states which physical information is required to evaluate the chosen functions on an evolving section. The integration of the physical cross-section may employ local sectional coordinates and sectional Jacobians; the coupling itself does not require a prescribed global reference-to-physical mapping of the entire non-prismatic beam.

The structural coupling is ultimately expressed by the chain

```math
\mathcal S(x)
\longrightarrow
\left\{\Omega^k(x),\mathbf C^k(x,y,z),\partial\Omega^k(x)\right\}
\longrightarrow
\left\{J^{mn,k}_{\tau,\alpha\,s,\beta}(x),\ \mathbf H^{ab}_{\tau s}(x),\ \mathbf p_\tau(x)\right\}
\longrightarrow
\text{CUF variational equations}.
```

The CUF kinematics specifies which expansion factors and derivatives occur in the kernels; **CSF determines the geometry and material that give those kernels their physical content**. Their combination occurs at the level of sectional integration and assembly, without encoding particular section dimensions or material constants into the generic CUF operator.

This separation is mathematical rather than merely organizational: the operator-generating rule takes the same form for every admissible sectional state, while the domain of integration, the constitutive coefficients and, where relevant, the physical evaluation of the chosen basis are supplied independently. In particular, a varying material does not itself require $F_{\tau,x}\neq 0$; that derivative arises from the selected kinematic representation on an evolving section.

---

## 3. CUF kinematic representation and the role of longitudinal basis dependence

The physical geometry and constitutive field have already been defined by $\mathcal S(x)$ independently of the displacement approximation. The following kinematic representation supplies the CUF test and trial functions with which those prescribed fields will be coupled; it does not define or replace the CSF object.

The displacement field is written as

```math
\mathbf{u}(x,y,z) = \sum_{\tau=1}^{M} F_\tau(x,y,z)\,\mathbf{q}_\tau(x),
```

where

```math
\mathbf{q}_\tau(x) =
\begin{bmatrix}
q_{x\tau}(x) \\
q_{y\tau}(x) \\
q_{z\tau}(x)
\end{bmatrix}.
```

The functions $F_\tau(x,y,z)$ describe the CUF sectional approximation, while the generalized amplitudes $\mathbf{q}_\tau(x)$ remain one-dimensional unknowns.

This form is appropriate when the selected sectional basis is represented in physical coordinates and evolves along the beam. The more restricted choice is

```math
F_\tau = F_\tau(y,z).
```

When the chosen $F_\tau$ depends also on $x$, its longitudinal derivative must be retained explicitly. This derivative is a physical-coordinate derivative at fixed $y,z$; for a basis generated using local sectional coordinates, its evaluation must consistently account for the evolving local mapping. Such local derivative transformations do not require prescribing a beam-wide geometric mapping as the definition of CSF. **Neither the changing integration domain nor the variable material field alone implies a nonzero $F_{\tau,x}$.**

---

## 4. Spatial derivatives of the displacement field

Let

```math
F_{\tau,x} = \frac{\partial F_\tau}{\partial x},
\qquad
F_{\tau,y} = \frac{\partial F_\tau}{\partial y},
\qquad
F_{\tau,z} = \frac{\partial F_\tau}{\partial z}.
```

Then, for each displacement component $u_i$,

```math
\frac{\partial u_i}{\partial x}
=
\sum_{\tau}
\left(
F_{\tau,x}\,q_{i\tau}
+
F_\tau\,\frac{dq_{i\tau}}{dx}
\right),
```

```math
\frac{\partial u_i}{\partial y}
=
\sum_{\tau} F_{\tau,y}\,q_{i\tau},
```

```math
\frac{\partial u_i}{\partial z}
=
\sum_{\tau} F_{\tau,z}\,q_{i\tau}.
```

Therefore the longitudinal derivative contains two distinct contributions:

1. the derivative of the generalized amplitude;
2. the derivative of the expansion function itself.

For compactness, define the longitudinal action

```math
\mathcal{D}_F[v] = F_{,x}\,v + F\,v'.
```

Here $v' = dv/dx$.

---

## 5. Small-strain field

Using the engineering strain vector

```math
\boldsymbol{\varepsilon} =
\begin{bmatrix}
\varepsilon_{xx} \\
\varepsilon_{yy} \\
\varepsilon_{zz} \\
\gamma_{yz} \\
\gamma_{xz} \\
\gamma_{xy}
\end{bmatrix},
```

with

```math
\varepsilon_{xx} = u_{x,x},
\qquad
\varepsilon_{yy} = u_{y,y},
\qquad
\varepsilon_{zz} = u_{z,z},
```

```math
\gamma_{yz} = u_{y,z} + u_{z,y},
\qquad
\gamma_{xz} = u_{x,z} + u_{z,x},
\qquad
\gamma_{xy} = u_{x,y} + u_{y,x},
```

the strain contribution associated with expansion index $s$, with

```math
a = q_{xs},
\qquad
b = q_{ys},
\qquad
c = q_{zs},
\qquad
A = F_s,
```

is

```math
\boldsymbol{\varepsilon}_s =
\begin{bmatrix}
\mathcal{D}_A[a] \\
A_{,y}\,b \\
A_{,z}\,c \\
A_{,z}\,b + A_{,y}\,c \\
A_{,z}\,a + \mathcal{D}_A[c] \\
A_{,y}\,a + \mathcal{D}_A[b]
\end{bmatrix}.
```

The total strain field is

```math
\boldsymbol{\varepsilon} = \sum_s \boldsymbol{\varepsilon}_s.
```

The virtual strain field is obtained by the same rule, replacing trial quantities with virtual quantities.

---

## 6. Constitutive field and stress field

In each sub-domain $\Omega^k(x)$,

```math
\boldsymbol{\sigma}^k(x,y,z) = \mathbf{C}^k(x,y,z)\,\boldsymbol{\varepsilon}(x,y,z).
```

For the explicit development below, the constitutive matrix is written as

```math
\mathbf{C}^k =
\begin{bmatrix}
C_{11} & C_{12} & C_{13} & 0 & 0 & 0 \\
C_{12} & C_{22} & C_{23} & 0 & 0 & 0 \\
C_{13} & C_{23} & C_{33} & 0 & 0 & 0 \\
0 & 0 & 0 & C_{44} & 0 & 0 \\
0 & 0 & 0 & 0 & C_{55} & 0 \\
0 & 0 & 0 & 0 & 0 & C_{66}
\end{bmatrix}^{k}.
```

Each entry may depend on $x$, $y$, and $z$. The displayed block structure is a **constitutive assumption for the explicit nine operators**: it permits coupling among the three normal strains but omits normal–shear and shear–shear off-diagonal couplings. The variational construction and the $\mathbf H^{ab}_{\tau s}$ matrices below remain valid for a general symmetric constitutive matrix; a fully populated matrix leads to additional terms in the individual nine operator blocks. Small-displacement, small-strain linear elasticity is assumed throughout.

---

## 7. Reconstructed stress divergence and local equilibrium

The local three-dimensional equilibrium field is the divergence of the stress tensor,

```math
\mathbf{r}(x,y,z) = \nabla \cdot \boldsymbol{\sigma}(x,y,z).
```

In component form,

```math
\mathbf{r} =
\begin{bmatrix}
\dfrac{\partial \sigma_{xx}}{\partial x} + \dfrac{\partial \sigma_{xy}}{\partial y} + \dfrac{\partial \sigma_{xz}}{\partial z} \\
\dfrac{\partial \sigma_{xy}}{\partial x} + \dfrac{\partial \sigma_{yy}}{\partial y} + \dfrac{\partial \sigma_{yz}}{\partial z} \\
\dfrac{\partial \sigma_{xz}}{\partial x} + \dfrac{\partial \sigma_{yz}}{\partial y} + \dfrac{\partial \sigma_{zz}}{\partial z}
\end{bmatrix}.
```

In the present CSF-CUF framework,

```math
\boldsymbol{\sigma}(x,y,z) = \mathbf{C}(x,y,z)\,\boldsymbol{\varepsilon}\bigl[F_\tau(x,y,z),\mathbf{q}_\tau(x)\bigr].
```

Therefore the divergence field depends simultaneously on:

- the constitutive variation $\mathbf{C}(x,y,z)$;
- the spatial derivatives of the expansion functions $F_\tau(x,y,z)$;
- the generalized amplitudes $\mathbf{q}_\tau(x)$ and their longitudinal derivatives.

In the absence of body forces, the strong local equilibrium condition is

```math
\nabla \cdot \boldsymbol{\sigma} = \mathbf{0}.
```

In the presence of body forces $\mathbf{b}$, the strong local equilibrium condition becomes

```math
\nabla \cdot \boldsymbol{\sigma} + \mathbf{b} = \mathbf{0}.
```

The divergence is evaluated **after reconstruction** of the three-dimensional strain and stress fields from the solved generalized amplitudes. It therefore belongs explicitly to the reconstruction and local-equilibrium assessment identified in Section 14. Within a material sub-domain, the strong residual is $\mathbf r+\mathbf b$; at interfaces, the corresponding traction-jump condition is an additional local-equilibrium requirement. The derivatives of $\mathbf C^k$ and of the reconstructed kinematic fields must be evaluated consistently wherever classical derivatives exist.

The divergence field is distinct from the generalized one-dimensional operator obtained later by the principle of virtual work: the CUF equations enforce equilibrium in a projected variational sense and **do not, by themselves, imply pointwise vanishing of the reconstructed three-dimensional residual**. This distinction gives the divergence field an independent verification role.

---

## 8. Internal virtual work

The internal virtual work is

```math
\delta W_{\mathrm{int}} =
\int_0^L
\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)}
\delta \boldsymbol{\varepsilon}^{T}
\mathbf{C}^k
\boldsymbol{\varepsilon}
\, d\Omega \, dx.
```

This is the central point of the CSF-CUF coupling: the CUF virtual-work integrand is integrated over the actual sectional domains supplied by the continuous physical field, with the constitutive matrix evaluated at each physical integration point. Geometry and material enter the same variational statement without becoming part of the definition of the longitudinal unknowns.

---

## 9. Generalized sectional coefficients

Let the derivative labels belong to

```math
\alpha,\beta \in \left\{ \varnothing, x, y, z \right\},
```

with

```math
F_{\tau,\varnothing} \equiv F_\tau.
```

Define the generalized sectional coefficient in sub-domain $k$ as

```math
J_{\tau,\alpha\,s,\beta}^{mn,k}(x)
=
\int_{\Omega^k(x)}
C_{mn}^k(x,y,z)
F_{\tau,\alpha}(x,y,z)
F_{s,\beta}(x,y,z)
\, d\Omega.
```

The assembled coefficient is

```math
J_{\tau,\alpha\,s,\beta}^{mn}(x)
=
\sum_{k=1}^{N_\Omega} J_{\tau,\alpha\,s,\beta}^{mn,k}(x).
```

For the remainder of this document, the superscript $k$ always denotes a **sub-domain coefficient**, while the same symbol without $k$ denotes its assembled value. The indices $\tau$ and $s$ identify test and trial expansions; they are not summed in the definition of one fixed nuclear block. Only in the explicit final operators (Section 16) will the compact shorthand $J^{mn}_{\alpha\beta}$ be used, with those indices held implicit and the zero label $0$ standing for the no-derivative label $\varnothing$.

The derivative labels refer to derivatives of the expansion functions inside the sectional integral. Importantly, the coefficient also depends on the independently supplied **physical domain** $\Omega^k(x)$ and **constitutive field** $C_{mn}^k(x,y,z)$. Both are provided by $\mathcal S(x)$, while the factors $F_{\tau,\alpha}$ and $F_{s,\beta}$ are supplied by the selected CUF expansion. Thus each coefficient is the mathematical coupling between physical information and kinematic approximation.

To make the individual effects explicit, consider the coefficient definition without selecting a particular geometry or material law. Its **integration domain** is $\Omega^k(x)$, so the geometric field determines where the integral is taken. Its **constitutive factor** is $C^k_{mn}(x,y,z)$, so the material field determines how the kinematic product is weighted. Its **test and trial factors** are $F_{\tau,\alpha}$ and $F_{s,\beta}$, so the chosen CUF approximation determines which displacement modes and physical derivatives are coupled. The derivative selectors can include $x$, and therefore allow the longitudinal variation of the expansion itself to enter the coefficients.

None of these three roles can be substituted for another: moving integration boundaries do not generate the $F_{\tau,x}$ terms, and a variable constitutive field does not change the definition of the CUF kinematic functions. The resulting longitudinal variation of $J^{mn,k}_{\tau,\alpha\,s,\beta}(x)$ combines the effects while preserving their separate origins.

---

## 10. Weak fundamental nucleus

Let

```math
A = F_s,
\qquad
B = F_\tau.
```

For compact notation, introduce the global sectional integral

```math
\langle H \rangle (x)
=
\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)} H^k(x,y,z)\, d\Omega.
```

### 10.1 Diagonal blocks

```math
\mathcal{B}_{xx}^{\tau s}(\delta a,a)
=
\left\langle
C_{11}\,\mathcal{D}_B[\delta a]\,\mathcal{D}_A[a]
+
C_{55}\,B_{,z}A_{,z}\,\delta a\,a
+
C_{66}\,B_{,y}A_{,y}\,\delta a\,a
\right\rangle,
```

```math
\mathcal{B}_{yy}^{\tau s}(\delta b,b)
=
\left\langle
\left(C_{22}B_{,y}A_{,y}+C_{44}B_{,z}A_{,z}\right)\delta b\,b
+
C_{66}\,\mathcal{D}_B[\delta b]\,\mathcal{D}_A[b]
\right\rangle,
```

```math
\mathcal{B}_{zz}^{\tau s}(\delta c,c)
=
\left\langle
\left(C_{33}B_{,z}A_{,z}+C_{44}B_{,y}A_{,y}\right)\delta c\,c
+
C_{55}\,\mathcal{D}_B[\delta c]\,\mathcal{D}_A[c]
\right\rangle.
```

### 10.2 Axial-transverse coupling blocks

```math
\mathcal{B}_{xy}^{\tau s}(\delta a,b)
=
\left\langle
C_{12}\,\mathcal{D}_B[\delta a]A_{,y}b
+
C_{66}\,B_{,y}\,\delta a\,\mathcal{D}_A[b]
\right\rangle,
```

```math
\mathcal{B}_{yx}^{\tau s}(\delta b,a)
=
\left\langle
C_{12}\,B_{,y}\,\delta b\,\mathcal{D}_A[a]
+
C_{66}\,\mathcal{D}_B[\delta b]A_{,y}a
\right\rangle,
```

```math
\mathcal{B}_{xz}^{\tau s}(\delta a,c)
=
\left\langle
C_{13}\,\mathcal{D}_B[\delta a]A_{,z}c
+
C_{55}\,B_{,z}\,\delta a\,\mathcal{D}_A[c]
\right\rangle,
```

```math
\mathcal{B}_{zx}^{\tau s}(\delta c,a)
=
\left\langle
C_{13}\,B_{,z}\,\delta c\,\mathcal{D}_A[a]
+
C_{55}\,\mathcal{D}_B[\delta c]A_{,z}a
\right\rangle.
```

### 10.3 Transverse coupling blocks

```math
\mathcal{B}_{yz}^{\tau s}(\delta b,c)
=
\left\langle
\left(C_{23}B_{,y}A_{,z}+C_{44}B_{,z}A_{,y}\right)\delta b\,c
\right\rangle,
```

```math
\mathcal{B}_{zy}^{\tau s}(\delta c,b)
=
\left\langle
\left(C_{23}B_{,z}A_{,y}+C_{44}B_{,y}A_{,z}\right)\delta c\,b
\right\rangle.
```

These nine blocks constitute the weak fundamental nucleus associated with the present constitutive structure. In each block, the geometry and material are supplied through the sectional brackets, while the kinematic factors are prescribed by the CUF expansion. Thus the nine-block structure is unchanged by a change of physical member within the stated model class; it is the sectional content of the blocks that varies with $\mathcal S(x)$.

---

## 11. Matrix operator form

Section 10 expands the nine weak blocks so that each constitutive and displacement coupling can be inspected individually. The equivalent matrix representation here collects those same terms into four sectional matrices and is suited to concise variational statements and numerical assembly. It does **not** introduce a second physical or constitutive model.

Define the $6 \times 3$ matrices

```math
\mathbf{B}^{(0)}(F) =
\begin{bmatrix}
F_{,x} & 0 & 0 \\
0 & F_{,y} & 0 \\
0 & 0 & F_{,z} \\
0 & F_{,z} & F_{,y} \\
F_{,z} & 0 & F_{,x} \\
F_{,y} & F_{,x} & 0
\end{bmatrix},
```

```math
\mathbf{B}^{(1)}(F) =
\begin{bmatrix}
F & 0 & 0 \\
0 & 0 & 0 \\
0 & 0 & 0 \\
0 & 0 & 0 \\
0 & 0 & F \\
0 & F & 0
\end{bmatrix}.
```

Then

```math
\boldsymbol{\varepsilon}_s
=
\mathbf{B}^{(0)}(F_s)\,\mathbf{q}_s
+
\mathbf{B}^{(1)}(F_s)\,\mathbf{q}_s'.
```

The sectional matrices are

```math
\mathbf{H}_{\tau s}^{ab}(x)
=
\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)}
\left[ \mathbf{B}^{(a)}(F_\tau) \right]^T
\mathbf{C}^k(x,y,z)
\mathbf{B}^{(b)}(F_s)
\, d\Omega,
```

with

```math
a,b \in \{0,1\}.
```

The weak internal virtual work becomes

```math
\delta W_{\mathrm{int}} =
\int_0^L \sum_{\tau,s}
\left[
\delta \mathbf{q}_\tau^T \mathbf{H}_{\tau s}^{00} \mathbf{q}_s
+
\delta \mathbf{q}_\tau^T \mathbf{H}_{\tau s}^{01} \mathbf{q}_s'
+
\delta \mathbf{q}_\tau'^T \mathbf{H}_{\tau s}^{10} \mathbf{q}_s
+
\delta \mathbf{q}_\tau'^T \mathbf{H}_{\tau s}^{11} \mathbf{q}_s'
\right] dx.
```

---

## 12. Governing longitudinal operator

Integrating by parts the terms containing $\delta \mathbf{q}_\tau'$, one obtains

```math
\delta W_{\mathrm{int}} =
\int_0^L
\sum_\tau
\delta \mathbf{q}_\tau^T
\sum_s
\left[
\mathbf{H}_{\tau s}^{00}\mathbf{q}_s
+
\mathbf{H}_{\tau s}^{01}\mathbf{q}_s'
-
\partial_x
\left(
\mathbf{H}_{\tau s}^{10}\mathbf{q}_s
+
\mathbf{H}_{\tau s}^{11}\mathbf{q}_s'
\right)
\right] dx
+
\left[
\sum_\tau \delta \mathbf{q}_\tau^T
\sum_s
\left(
\mathbf{H}_{\tau s}^{10}\mathbf{q}_s
+
\mathbf{H}_{\tau s}^{11}\mathbf{q}_s'
\right)
\right]_{x=0}^{x=L}.
```

Therefore the generalized CUF longitudinal operator is

```math
\mathcal{K}_{\tau s}[\mathbf{q}_s]
=
\mathbf{H}_{\tau s}^{00}(x)\,\mathbf{q}_s
+
\mathbf{H}_{\tau s}^{01}(x)\,\mathbf{q}_s'
-
\partial_x
\left[
\mathbf{H}_{\tau s}^{10}(x)\,\mathbf{q}_s
+
\mathbf{H}_{\tau s}^{11}(x)\,\mathbf{q}_s'
\right].
```

This one-dimensional operator is the variationally generated governing operator of the CSF-CUF model. The four matrices $\mathbf H^{00}$, $\mathbf H^{01}$, $\mathbf H^{10}$ and $\mathbf H^{11}$ inherit the geometry, constitutive field and kinematic derivative factors from their sectional integrals. The longitudinal divergence operator must act on the **whole product** containing the variable coefficient: the effect of the continuous physical field therefore persists after sectional reduction and integration by parts.

---

## 13. External virtual work

Let $\Sigma_t$ be a traction-loaded part of the physical boundary, with prescribed traction $\bar{\mathbf{t}}(x,y,z)$. Then

```math
\delta W_{\mathrm{ext}}^{t}
=
\int_{\Sigma_t} \delta \mathbf{u}^T \bar{\mathbf{t}}\, dA.
```

For a boundary line $\Gamma_t(x)$ swept along the beam axis, with physical area factor $\mu(x,y,z)$,

```math
\delta W_{\mathrm{ext}}^{t}
=
\int_0^L \sum_\tau
\delta \mathbf{q}_\tau^T(x)\,\mathbf{p}_\tau(x)\,dx,
```

where

```math
\mathbf{p}_\tau(x)
=
\int_{\Gamma_t(x)}
F_\tau(x,y,z)\,\bar{\mathbf{t}}(x,y,z)\,\mu(x,y,z)\,d\Gamma.
```

The geometry field also determines the actual loaded boundary $\Gamma_t(x)$ and the swept-surface measure $\mu(x,y,z)$. Accordingly, changing the CSF geometry changes the load projection as well as the internal stiffness, even when the prescribed physical traction law is unchanged.

Similarly, for a body-force density $\mathbf{b}$,

```math
\mathbf{f}_\tau^{b}(x)
=
\sum_k \int_{\Omega^k(x)}
F_\tau(x,y,z)\,\mathbf{b}^k(x,y,z)\,d\Omega.
```

---

## 14. Final governing equations and separation of roles

Let

```math
\mathbf{f}_\tau(x) = \mathbf{p}_\tau(x) + \mathbf{f}_\tau^b(x).
```

Then the governing generalized equations are

```math
\sum_s \mathcal{K}_{\tau s}[\mathbf{q}_s](x) = \mathbf{f}_\tau(x),
\qquad
\tau = 1,\ldots,M.
```

The formulation separates the following responsibilities. In particular, the local divergence defined in Section 7 is evaluated from the **reconstructed** stress field, not inferred directly from the one-dimensional equilibrium equation:

1. **CSF physical description**: provides $\Omega^k(x)$, $\partial\Omega^k(x)$, and $\mathbf{C}^k(x,y,z)$;
2. **CUF expansion family**: provides $F_\tau(x,y,z)$ and its derivatives with respect to $x$, $y$, and $z$;
3. **Longitudinal approximation**: provides the representation of $\mathbf{q}_\tau(x)$;
4. **Assembly and reconstruction**: produces the sectional matrices, the generalized solution, and the reconstructed three-dimensional displacement, strain, stress, and divergence fields.

The defining result is the transfer of a **continuous geometry-material field** into the CUF sectional coefficients, load projections, and fundamental nuclear operators. The three-coordinate evaluation of the expansion functions makes that transfer kinematically complete when the section-dependent basis changes along the axis; it is not a competing objective. The physical field, the CUF approximation, and the longitudinal solution remain separately defined mathematical objects.

---

## 15. Kinematic specialization: reduction to the case $F_\tau = F_\tau(y,z)$

If the longitudinal dependence of the expansion functions is suppressed, then

```math
F_{\tau,x} = 0.
```

Consequently,

```math
\mathcal{D}_F[v] = F\,v',
```

and all coefficient families containing $x$-derivatives of the expansion functions vanish. The formulation then reduces to the corresponding variable-section theory in which the sectional dependence on $x$ enters through the physical fields $\Omega^k(x)$ and $\mathbf{C}^k(x,y,z)$, while the CUF expansion remains purely transverse.

---

## 16. Explicit form of the nine assembled fundamental nuclear operators

The final result of the formulation is the complete $3\times3$ CUF fundamental nucleus. This section presents **all nine operators in strong longitudinal form**, using the physical-domain sectional coefficients introduced in Section 9. Their explicit expressions are obtained by the weak-to-strong conversion established in Sections 10–12 and verified in Section 16.2. They do not impose a longitudinal solution technique. The point of displaying the nine operators is to make the **destination of the continuous physical field** explicit: the geometry and the constitutive coefficients supplied by $\mathcal S(x)$ determine every sectional $J$ appearing in them, while the chosen CUF functions determine the differentiated kinematic factors.

### 16.1 Conventions and coefficient origin

To keep the equations readable, define the following abbreviation for the **assembled** sectional coefficients:

```math
J^{mn}_{\alpha\beta}(x)
\equiv
J^{mn}_{\tau,\alpha\,s,\beta}(x)
=
\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)}
C^k_{mn}(x,y,z)\,
F_{\tau,\alpha}(x,y,z)\,
F_{s,\beta}(x,y,z)\,d\Omega.
```

The indices $\tau$ and $s$ are implicit on the left but are **not** summed when defining one individual nuclear block. The first differentiation label acts on the virtual/test function $F_\tau$; the second acts on the trial function $F_s$. Both labels belong to $\{0,x,y,z\}$, with $F_{\tau,0}=F_\tau$ and $F_{s,0}=F_s$. The constitutive indices $m,n$ use the engineering-shear order $(xx,yy,zz,yz,xz,xy)$. Throughout this section $J^{mn}_{\alpha\beta}=J^{mn}_{\alpha\beta}(x)$.

Let $v(x)$ denote the longitudinal amplitude on which a nuclear block acts. Its action follows from the four bilinear coefficient families:

```math
K_{ij}^{\tau s}[v]
=
H_{ij}^{00}\,v
+H_{ij}^{01}\,v'
-\partial_x\!\left(H_{ij}^{10}\,v+H_{ij}^{11}\,v'\right).
```

The explicit $J$ coefficients in the nine expressions below include all terms induced by $F_{\tau,x}$ and $F_{s,x}$. In particular, differentiation $\partial_x$ on the right acts on **the whole parenthesized product**, not on the longitudinal amplitude alone.

For each of the nine operators, the same dependency is preserved:

```math
\mathcal S(x)
\longrightarrow
\bigl\{\Omega^k(x),\mathbf C^k(x,y,z)\bigr\}
\longrightarrow
J^{mn}_{\alpha\beta}(x)
\longrightarrow
K_{ij}^{\tau s}.
```

The geometry changes the integration region; the material changes the integrand; the selected expansion supplies its values and derivatives. The longitudinal differential structure follows from the variational derivation and does not depend on any particular section shape or constitutive law.

### 16.2 Derivation of an axial operator from the weak form

To verify the passage from the complete weak nucleus to the differential operators, consider the axial–axial block for a fixed pair $(\tau,s)$. Let $v(x)$ be its trial amplitude and $\delta w(x)$ the corresponding test amplitude. The terms of Section 10.1 give

```math
\begin{aligned}
\mathcal B_{xx}^{\tau s}(\delta w,v)
=\int_0^L\big[&\delta w\,(J^{11}_{xx}+J^{55}_{zz}+J^{66}_{yy})v
+\delta w\,J^{11}_{x0}v'\\
&+\delta w'\,J^{11}_{0x}v
+\delta w'\,J^{11}_{00}v'\big]\,dx.
\end{aligned}
```

This expression follows directly from the longitudinal product rule: each $\mathcal D_B[\delta w]\mathcal D_A[v]$ generates the four products $B_{,x}A_{,x}\delta wv$, $B_{,x}A\delta wv'$, $BA_{,x}\delta w'v$ and $BA\delta w'v'$. Every $J$ is an integral over the actual domains $\Omega^k(x)$ weighted by $C^k_{mn}(x,y,z)$.

Integrating by parts only the terms containing the derivative of the test amplitude gives

```math
\begin{aligned}
\mathcal B_{xx}^{\tau s}(\delta w,v)
={}&\int_0^L\delta w\,\Big[
(J^{11}_{xx}+J^{55}_{zz}+J^{66}_{yy})v
+J^{11}_{x0}v'\\
&\qquad-\partial_x\big(J^{11}_{0x}v+J^{11}_{00}v'\big)
\Big]\,dx\\
&+\Big[\delta w\,(J^{11}_{0x}v+J^{11}_{00}v')\Big]_{0}^{L}.
\end{aligned}
```

Consequently, the axial operator is

```math
\begin{aligned}
K_{xx}^{\tau s}[v]={}&
(J^{11}_{xx}+J^{55}_{zz}+J^{66}_{yy})v
+J^{11}_{x0}v'\\
&-\partial_x\big(J^{11}_{0x}v+J^{11}_{00}v'\big).
\end{aligned}
```

The boundary contribution is the corresponding generalized end action. The **same integration-by-parts rule** applies to the remaining eight blocks, whether they contain zero, one or two derivatives of the longitudinal test and trial amplitudes. The compact conversion rule is

```math
K_{ij}^{\tau s}[v]
=H_{ij}^{00}v+H_{ij}^{01}v'
-\partial_x\big(H_{ij}^{10}v+H_{ij}^{11}v'\big).
```

The correspondence between the nine blocks in the weak and strong forms is therefore explicit: for each displacement pair $(i,j)$, identify its four coefficients $H_{ij}^{ab}$, with $a=1$ meaning differentiation of the test amplitude and $b=1$ meaning differentiation of the trial amplitude, and apply the conversion rule above. The operators below provide the fully expanded resulting expressions.

### 16.3 Diagonal operators

**Axial–axial block**

```math
\begin{aligned}
K_{xx}^{\tau s}[v]={}&
\left(J^{11}_{xx}+J^{55}_{zz}+J^{66}_{yy}\right)v
+J^{11}_{x0}\,v'\\
&-\partial_x\!\left(J^{11}_{0x}\,v+J^{11}_{00}\,v'\right).
\end{aligned}
```

**Transverse $y$–$y$ block**

```math
\begin{aligned}
K_{yy}^{\tau s}[v]={}&
\left(J^{22}_{yy}+J^{44}_{zz}+J^{66}_{xx}\right)v
+J^{66}_{x0}\,v'\\
&-\partial_x\!\left(J^{66}_{0x}\,v+J^{66}_{00}\,v'\right).
\end{aligned}
```

**Transverse $z$–$z$ block**

```math
\begin{aligned}
K_{zz}^{\tau s}[v]={}&
\left(J^{33}_{zz}+J^{44}_{yy}+J^{55}_{xx}\right)v
+J^{55}_{x0}\,v'\\
&-\partial_x\!\left(J^{55}_{0x}\,v+J^{55}_{00}\,v'\right).
\end{aligned}
```

### 16.4 Axial–transverse coupling operators

**Axial $x$–transverse $y$ block**

```math
\begin{aligned}
K_{xy}^{\tau s}[v]={}&
\left(J^{12}_{xy}+J^{66}_{yx}\right)v
+J^{66}_{y0}\,v'\\
&-\partial_x\!\left(J^{12}_{0y}\,v\right).
\end{aligned}
```

**Transverse $y$–axial $x$ block**

```math
\begin{aligned}
K_{yx}^{\tau s}[v]={}&
\left(J^{12}_{yx}+J^{66}_{xy}\right)v
+J^{12}_{y0}\,v'\\
&-\partial_x\!\left(J^{66}_{0y}\,v\right).
\end{aligned}
```

**Axial $x$–transverse $z$ block**

```math
\begin{aligned}
K_{xz}^{\tau s}[v]={}&
\left(J^{13}_{xz}+J^{55}_{zx}\right)v
+J^{55}_{z0}\,v'\\
&-\partial_x\!\left(J^{13}_{0z}\,v\right).
\end{aligned}
```

**Transverse $z$–axial $x$ block**

```math
\begin{aligned}
K_{zx}^{\tau s}[v]={}&
\left(J^{13}_{zx}+J^{55}_{xz}\right)v
+J^{13}_{z0}\,v'\\
&-\partial_x\!\left(J^{55}_{0z}\,v\right).
\end{aligned}
```

### 16.5 Transverse–transverse coupling operators

**Transverse $y$–transverse $z$ block**

```math
K_{yz}^{\tau s}[v]
=\left(J^{23}_{yz}+J^{44}_{zy}\right)v.
```

**Transverse $z$–transverse $y$ block**

```math
K_{zy}^{\tau s}[v]
=\left(J^{23}_{zy}+J^{44}_{yz}\right)v.
```

### 16.6 Assembled nuclear system

Collecting the nine operators gives

```math
\mathbf K_{\tau s}
=\begin{bmatrix}
K_{xx}^{\tau s}&K_{xy}^{\tau s}&K_{xz}^{\tau s}\\
K_{yx}^{\tau s}&K_{yy}^{\tau s}&K_{yz}^{\tau s}\\
K_{zx}^{\tau s}&K_{zy}^{\tau s}&K_{zz}^{\tau s}
\end{bmatrix}.
```

The complete generalized equilibrium equations are

```math
\sum_{s=1}^{M}\mathbf K_{\tau s}[\mathbf q_s](x)
=\mathbf f_\tau(x),
\qquad \tau=1,\ldots,M.
```

Every coefficient in these nine expressions is obtained from the **same continuous CSF geometry–material field** through integration over the actual physical domains $\Omega^k(x)$. The functions $F_\tau(x,y,z)$ and their derivatives determine the kinematic factors; $\mathbf C^k(x,y,z)$ determines the constitutive factors; the generalized amplitudes remain longitudinal unknowns. Accordingly, the nine equations are the final mathematical expression of the CSF-to-CUF coupling, while the three-dimensional field $\nabla\cdot\boldsymbol\sigma$ remains the distinct local equilibrium quantity defined in Section 7.

In particular, the separation between the continuous physical description and the CUF operators is a consequence of the derivation: one can change an admissible CSF geometry or constitutive field and reevaluate the sectional coefficients without changing the form of the nine nuclear equations. The optional $x$-dependence of $F_\tau$ completes the kinematic description when the chosen transverse basis evolves longitudinally; it does not redefine the central purpose of the coupling.
