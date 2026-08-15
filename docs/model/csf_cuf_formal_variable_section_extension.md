#  DRAFT
>The following material presents the current conceptual definition of the CSF-CUF sectional interface. The coupling is still under development and is intended to be implemented through a dedicated software bridge able to provide the sectional data required by the CUF formulation from the CSF representation $\mathcal{S}(x)$.

# Formal CSF-CUF extension for a longitudinally varying section field

## 1. Scope

This note formulates the coupling between a Continuous Section Field (CSF) and the CUF beam framework. The need for this coupling follows directly from the CSF representation $\mathcal{S}(x)$: since sectional geometry and constitutive properties may vary continuously along the beam axis, the sectional coefficients entering the CUF formulation must themselves become functions of $x$. The CSF representation $\mathcal{S}(x)$ supplies the sectional data required to evaluate these coefficients, while the CUF kinematic and variational structure is retained.

$$ \mathcal{S}(x). $$

The objective is **not** to derive a closed-form analytical solution along the beam axis.

The objective is to define, at a formal level, how the sectional quantities entering the CUF formulation become functions of the longitudinal coordinate through the CSF representation.

The sequence is

$$ { \mathcal{S}(x) \longrightarrow \{ \Omega^k(x),\, \mathbf{C}^k(x,y,z) \} \longrightarrow J_\bullet^k(x) \longrightarrow \delta L_i \longrightarrow \delta L_{\mathrm{ext}} \longrightarrow \mathbf{K}_{\tau s}[\mathcal{S}(x),\partial_x]. } $$

No analytical expression for the sectional integrals and no Navier-type solution are required at this stage.

### 1.1 Correspondence with the reference formulation

| Reference paper | Present formulation | Treatment |
|---|---|---|
| Refined Beam Theories | CUF approximation functions | Retained in generic form; no specific approximation family or order is imposed |
| Governing Differential Equations | Governing equations | Retained and generalized to longitudinally varying sectional coefficients |
| Variation of the Strain Energy | Variation of the strain energy | Retained with sectional quantities evaluated from $\mathcal{S}(x)$ |
| Virtual Work of the External Loadings | Virtual work of the external loads | Retained with geometry-dependent quantities evaluated from $\mathcal{S}(x)$ |
| The Fundamental Nucleo | Longitudinally varying nuclear operator | Retained and generalized to coefficients depending on $x$ |
| Closed Form Analytical Solution | - | Not adopted; the resulting variable-coefficient problem is left for numerical solution |

---

## 2. Coordinates and sectional representation

The CUF notation is retained.

- $x$ is the longitudinal coordinate along the beam axis.
- $y$ and $z$ are the transverse coordinates on the cross-section.
- $k$ identifies a transverse sub-domain.
- $\Omega^k(x)$ is sub-domain $k$ at longitudinal coordinate $x$.
- $N_\Omega$ is the number of transverse sub-domains.

The complete cross-section at $x$ is

$$ { \Omega(x) = \bigcup_{k=1}^{N_\Omega} \Omega^k(x). } $$

The CSF representation is denoted by

$$ { \mathcal{S}(x). } $$

At every longitudinal coordinate $x$, the CSF representation provides the corresponding sectional geometry and constitutive information.

Formally,

$$ \mathcal{S}(x) \longrightarrow \lbrace (\Omega^k(x),\mathbf{C}^k(x,y,z)) \rbrace_{k=1}^{N_\Omega} $$

Here $\mathbf{C}^k(x,y,z)$ denotes the constitutive matrix over sub-domain $k$.

The dependence on $y$ and $z$ is retained in the general notation. A constitutive law that is uniform inside each sub-domain is therefore only a particular case.

---

## 3. Difference from the reference paper

In the reference formulation, the beam cross-section is constant along $x$ and the material gradation is prescribed analytically over the transverse coordinates.

For the FGM case considered in the paper, Young's modulus is written as an analytical function of $y$ and $z$.

The resulting sectional coefficients can therefore be integrated analytically.

In the CSF extension, the primary object is instead

$$ \mathcal{S}(x), $$

and neither the geometry nor the resulting sectional coefficients need to possess a closed analytical expression along $x$.

The formal change is therefore

$$ { \Omega^k \longrightarrow \Omega^k(x) } $$

and, consequently,

$$ { J_\bullet^k \longrightarrow J_\bullet^k(x). } $$

The coefficients $J_\bullet^k(x)$ are evaluated numerically from the section supplied by $\mathcal{S}(x)$.

---

## 4. CUF approximation functions

The CUF kinematic approximation remains external to CSF.

Let

- $F_\tau(y,z)$ be the CUF approximation function associated with index $\tau$;
- $F_s(y,z)$ be the CUF approximation function associated with index $s$;
- $\phi$ and $\xi$ denote transverse differentiation directions, with $$ \phi,\xi \in \{\varnothing,y,z\}, $$.

The displacement field retains the CUF form

$$ { \mathbf{u}(x,y,z) = F_\tau(y,z)\, \mathbf{u}_\tau(x). } $$

CSF supplies the sectional domain and constitutive fields. CUF supplies the approximation functions and the displacement unknowns.

---

## 5. Sectional coefficients as functions of $\mathcal{S}(x)$


The four families of sectional coefficients introduced in Eq. (24) of the reference paper are retained, but their integration domains and constitutive coefficients are evaluated at the current longitudinal coordinate.

For sub-domain $k$:

$$ { J_{\tau,\phi s,\xi}^{ggk}(x) = \int_{\Omega^k(x)} C_{gg}^{k}(x,y,z)\, F_{\tau,\phi}(y,z)\, F_{s,\xi}(y,z)\, d\Omega } $$

$$ { J_{\tau s}^{ggk}(x) = \int_{\Omega^k(x)} C_{gg}^{k}(x,y,z)\, F_\tau(y,z)\, F_s(y,z)\, d\Omega } $$

$$ { J_{\tau,\phi s}^{ghk}(x) = \int_{\Omega^k(x)} C_{gh}^{k}(x,y,z)\, F_{\tau,\phi}(y,z)\, F_s(y,z)\, d\Omega } $$

$$ { J_{\tau s,\phi}^{ghk}(x) = \int_{\Omega^k(x)} C_{gh}^{k}(x,y,z)\, F_\tau(y,z)\, F_{s,\phi}(y,z)\, d\Omega. } $$

The notation $C_{gg}^k$ and $C_{gh}^k$ denotes the appropriate components of the constitutive matrix of sub-domain $k$.

These definitions can be written compactly as

$$ { J_\bullet^k(x) = \mathcal{J}_\bullet^k [ \mathcal{S}(x), F_\tau, F_s ]. } $$

The symbol $\bullet$ represents any one of the four coefficient families above.

### Numerical interpretation

The equations above are **definitions**, not closed-form solutions.

For a requested coordinate $x$:

$$ \mathcal{S}(x) \longrightarrow \lbrace \Omega^k(x), \mathbf{C}^k(x,y,z) \rbrace \longrightarrow \text{numerical sectional integration} \longrightarrow J_\bullet^k(x) $$

No polynomial, exponential, or other analytical approximation of $J_\bullet^k(x)$ is required.



## 5.1 Generalized sectional coefficient family

The four sectional coefficient families introduced above can be embedded into a single generalized definition.

Let:

- `k` identify the transverse sub-domain;
- `m,n` identify constitutive-matrix components in Voigt notation;
- `tau` and `s` identify the CUF approximation functions;
- `phi` denote the transverse derivative applied to the test-side approximation function;
- `xi` denote the transverse derivative applied to the source-side approximation function.

The derivative labels are taken from

$$ \phi,\xi \in \{\varnothing,y,z\}, $$

where the symbol

$$ \varnothing $$

denotes the absence of a transverse derivative.

Therefore,

$$ F_{\tau,\varnothing}(y,z) \equiv F_\tau(y,z), $$

and

$$ F_{s,\varnothing}(y,z) \equiv F_s(y,z). $$

For sub-domain `k`, define the generalized sectional coefficient as

$$ J_{\tau,\phi s,\xi}^{mn,k}(x) = \int_{\Omega^k(x)} C_{mn}^{k}(x,y,z) F_{\tau,\phi}(y,z) F_{s,\xi}(y,z) d\Omega $$

where:

- the domain

$$ \Omega^k(x) $$

is supplied by the CSF sectional representation at longitudinal coordinate `x`;

- the constitutive component

$$ C_{mn}^{k}(x,y,z) $$

is the corresponding entry of the constitutive matrix over sub-domain `k`;

- the functions

$$ F_\tau(y,z) $$

and

$$ F_s(y,z) $$

are supplied by the CUF transverse approximation.

The previously introduced coefficient families are recovered as special cases.

For two transverse derivatives,

$$ J_{\tau,\phi s,\xi}^{mn,k}(x) = \int_{\Omega^k(x)} C_{mn}^{k}(x,y,z) F_{\tau,\phi}(y,z) F_{s,\xi}(y,z) d\Omega. $$

For no transverse derivatives,

$$ J_{\tau,\varnothing s,\varnothing}^{mn,k}(x) = \int_{\Omega^k(x)} C_{mn}^{k}(x,y,z) F_{\tau}(y,z) F_{s}(y,z) d\Omega. $$

For a transverse derivative only on the test-side approximation function,

$$ J_{\tau,\phi s,\varnothing}^{mn,k}(x) = \int_{\Omega^k(x)} C_{mn}^{k}(x,y,z) F_{\tau,\phi}(y,z) F_{s}(y,z) d\Omega. $$

For a transverse derivative only on the source-side approximation function,

$$ J_{\tau,\varnothing s,\xi}^{mn,k}(x) = \int_{\Omega^k(x)} C_{mn}^{k}(x,y,z) F_{\tau}(y,z) F_{s,\xi}(y,z) d\Omega. $$

This generalized definition is required by the complete fundamental nucleus because the variational expansion produces all four derivative patterns.

In particular, terms of the form

$$ J_{\tau,y s,\varnothing}^{66,k}(x), $$

$$ J_{\tau,\varnothing s,y}^{66,k}(x), $$

and

$$ J_{\tau,y s,z}^{23,k}(x) $$

occur directly in the complete nucleus.

The corresponding global sectional coefficient is obtained by summing the sub-domain contributions:

$$ J_{\tau,\phi s,\xi}^{mn}(x) = \sum_{k=1}^{N_\Omega} J_{\tau,\phi s,\xi}^{mn,k}(x) $$

Therefore the complete coefficient family remains generated directly from the CSF representation:

$$ \mathcal{S}(x) \longrightarrow \{ \Omega^k(x), \mathbf{C}^{k}(x,y,z) \} \longrightarrow J_{\tau,\phi s,\xi}^{mn,k}(x) \longrightarrow J_{\tau,\phi s,\xi}^{mn}(x). $$

No analytical longitudinal expression for these coefficients is required.

---



---

## 6. Global sectional coefficients

The reference paper subsequently uses coefficients summed over the transverse sub-domains.

The same operation is retained.

For any coefficient family,

$$ { J_\bullet(x) = \sum_{k=1}^{N_\Omega} J_\bullet^k(x). } $$

Therefore the global CUF sectional coefficients become longitudinal fields generated from $\mathcal{S}(x)$.

---

## 7. Variation of the strain energy

Let

- $\boldsymbol{\varepsilon}$ be the strain vector;
- $\boldsymbol{\sigma}$ be the stress vector;
- $\delta$ denote a virtual variation.

The internal virtual work can be written formally as

$$ { \delta L_i = \int_0^l \sum_{k=1}^{N_\Omega} \int_{\Omega^k(x)} \delta\boldsymbol{\varepsilon}^{T} \mathbf{C}^k(x,y,z) \boldsymbol{\varepsilon} \,d\Omega\,dx. } $$

This is the direct counterpart of the strain-energy variation used in the reference formulation, with the fixed sub-domain replaced by $\Omega^k(x)$.

After introducing the CUF displacement expansion and the corresponding strain-displacement operators, the transverse integrations are identified with the previously defined coefficients

$$ J_\bullet(x). $$

Thus the strain-energy variation can remain in operator form:

$$ { \delta L_i = \int_0^l \delta\mathbf{u}_\tau^{T}(x)\, \mathbf{K}_{\tau s} [ J_\bullet(x),\partial_x ] \mathbf{u}_s(x) \,dx + \text{boundary terms}. } $$

No analytical evaluation of $J_\bullet(x)$ is required.


### 7.1 Longitudinal section dependence and transverse CUF expansion

The longitudinal dependence of the CSF section does not require the CUF transverse approximation functions to depend explicitly on $x$.

In the present coupling, the CUF approximation functions remain defined in the physical transverse coordinates:

$$ F_\tau = F_\tau(y,z), \qquad F_s = F_s(y,z). $$

The longitudinal coordinate $x$ determines instead the physical sectional state supplied by CSF. For every requested value of $x$, the CSF representation provides the corresponding sectional geometry and constitutive information:

$$ x \longrightarrow \mathcal{S}(x) \longrightarrow \lbrace \Omega^k(x), \mathbf{C}^k(x,y,z) \rbrace_{k=1}^{N_\Omega}. $$

Thus, changing $x$ changes the domains $\Omega^k(x)$ and the associated constitutive fields $\mathbf{C}^k(x,y,z)$, while the transverse CUF approximation functions remain functions of $y$ and $z$.

The sectional coefficients are consequently functions of $x$ because their integration domains and constitutive data are supplied by the sectional state at that coordinate:

$$ J_\bullet(x) = \mathcal{J}_\bullet[\mathcal{S}(x), F_\tau, F_s]. $$

For example, a sectional coefficient may have the form

$$ J_{\tau s}^{ggk}(x) = \int_{\Omega^k(x)} C_{gg}^{k}(x,y,z) F_\tau(y,z) F_s(y,z) d\Omega. $$

At each longitudinal coordinate $x$, the quantities $\Omega^k(x)$ and $\mathbf{C}^k(x,y,z)$ are known data provided by CSF. Their longitudinal variation therefore does not introduce additional kinematic unknowns.

The CUF displacement expansion retains the form

$$ \mathbf{u}(x,y,z) = F_\tau(y,z) \mathbf{u}_\tau(x). $$

The unknown quantities remain the longitudinal displacement amplitudes $\mathbf{u}_\tau(x)$.

The specific role of CSF in this coupling is therefore to make the longitudinal coordinate a deterministic query of the physical sectional state:

$$ x \longrightarrow \mathcal{S}(x). $$

As $x$ varies, CSF determines the section on which the CUF sectional quantities are evaluated, while the transverse expansion remains defined in the physical coordinates $y$ and $z$.

---

## 8. Virtual work of the external loads

The loading treatment remains the one defined by the CUF formulation.

The distinction between surface loads and line loads is retained.

The only geometric generalization is that the relevant sub-domain boundaries and application locations may depend on $x$ through $\mathcal{S}(x)$.

Let

$$ \Gamma_\phi^{k\pm}(x) $$

denote the positive or negative boundary of sub-domain $k$ associated with transverse direction $\phi$.

The sectional load projections can therefore be written formally as functions of $x$.

For example, a boundary projection coefficient has the structure

$$ { E_\tau^{k\phi\pm}(x) = \int_{\Gamma_\phi^{k\pm}(x)} F_\tau(y,z)\,d\Gamma. } $$

The corresponding line-load terms retain the CUF evaluation of $F_\tau$ at the load application point, whose transverse coordinates may now depend on $x$.

Accordingly,

$$ { \delta L_{\mathrm{ext}} = \delta L_p+\delta L_l } $$

is retained without introducing a new loading theory.

As for the sectional stiffness coefficients, the required geometric quantities are obtained from $\mathcal{S}(x)$ and can be evaluated numerically.

---

## 9. Governing equations

The Principle of Virtual Displacements remains

$$ { \delta L_i = \delta L_p+\delta L_l. } $$

After the sectional integrations have been represented through $J_\bullet(x)$, the governing equations retain the CUF nuclear structure but acquire longitudinally varying sectional coefficients.

Formally,

$$ { \mathbf{K}_{\tau s} [ \mathcal{S}(x),\partial_x ] \mathbf{u}_s(x) = \mathbf{f}_\tau(x), } $$

where

- $\mathbf{u}_s(x)$ contains the longitudinal unknown amplitudes associated with CUF index $s$;
- $\mathbf{f}_\tau(x)$ contains the generalized load terms associated with index $\tau$;
- $\mathbf{K}_{\tau s}$ is the CUF fundamental nuclear operator;
- the dependence of $\mathbf{K}_{\tau s}$ on the section is mediated by the fields $J_\bullet(x)$.

The nuclear matrix retains the $3\times3$ structure

$$ { \mathbf{K}_{\tau s} = \begin{bmatrix} K_{xx}^{\tau s} & K_{xy}^{\tau s} & K_{xz}^{\tau s} \\ K_{yx}^{\tau s} & K_{yy}^{\tau s} & K_{yz}^{\tau s} \\ K_{zx}^{\tau s} & K_{zy}^{\tau s} & K_{zz}^{\tau s} \end{bmatrix}. } $$

The entries are built from the same CUF sectional coefficient families, now evaluated as functions of $x$.

---


## 10. Longitudinally varying coefficients inside the nuclear operator

> This section builds on the sectional interface defined in
> [`csf_cuf_sectional_constitutive_interface.md`](csf_cuf_sectional_constitutive_interface.md),
> where the CSF-CUF coupling and the role of the dedicated software bridge are introduced.


### 10.1 Principle

When a sectional coefficient multiplying an x-derivative depends on x, the coefficient must remain inside the longitudinal differential operator.

For a constant coefficient:

$$ -J\,\partial_x^2 u(x) $$

For a longitudinally varying coefficient:

$$ -\partial_x \left( J(x)\,\partial_x u(x) \right) $$

The expression should be retained in this form rather than expanded through the product rule. This avoids introducing an unnecessary classical differentiability assumption on $J(x)$.

This generalization is directly justified when a nuclear term contains a single sectional coefficient multiplying a pure second derivative with respect to $x$.

---

### 10.2 Complete fundamental nucleus in weak form

The complete nuclear structure can be obtained directly from the Principle of Virtual Displacements before introducing any strong-form longitudinal differential operator.

Let the CUF displacement expansion associated with source index `s` be

$$ u_i(x,y,z) = F_s(y,z) u_{is}(x), \qquad i\in\{x,y,z\}. $$

For compactness, define the three source amplitudes as

$$ a(x)=u_{xs}(x), $$

$$ b(x)=u_{ys}(x), $$

and

$$ c(x)=u_{zs}(x). $$

Let the corresponding virtual amplitudes associated with test index `tau` be

$$ \delta a(x)=\delta u_{x\tau}(x), $$

$$ \delta b(x)=\delta u_{y\tau}(x), $$

and

$$ \delta c(x)=\delta u_{z\tau}(x). $$

Define

$$ A(y,z)=F_s(y,z) $$

and

$$ B(y,z)=F_\tau(y,z). $$

The source strain components are

$$ \varepsilon_{xx} = A a_{,x}, $$

$$ \varepsilon_{yy} = A_{,y} b, $$

$$ \varepsilon_{zz} = A_{,z} c, $$

$$ \gamma_{yz} = A_{,z} b + A_{,y} c, $$

$$ \gamma_{xz} = A_{,z} a + A c_{,x}, $$

and

$$ \gamma_{xy} = A_{,y} a + A b_{,x}. $$

The corresponding virtual strains are obtained by replacing

$$ A $$

with

$$ B $$

and replacing the source amplitudes with the corresponding virtual amplitudes.

For an isotropic constitutive specialization in Voigt order

$$ (xx,yy,zz,yz,xz,xy), $$

the non-zero constitutive entries involved in the present derivation are

$$ C_{11}, \quad C_{22}, \quad C_{33}, \quad C_{44}, \quad C_{55}, \quad C_{66}, $$

together with

$$ C_{12}=C_{21}, \qquad C_{13}=C_{31}, \qquad C_{23}=C_{32}. $$

The internal virtual work is

$$ \delta L_i = \int_0^l \sum_{k=1}^{N_\Omega} \int_{\Omega^k(x)} \delta\boldsymbol{\varepsilon}^{T} \mathbf{C}^{k} \boldsymbol{\varepsilon} d\Omega dx. $$

After expanding the strain product and performing only the transverse integrations, the nine blocks of the fundamental nucleus are obtained directly in bilinear form.

### Axial block

$$ K_{xx}^{\tau s}: \quad J_{\tau,\varnothing s,\varnothing}^{11} \delta a_{,x} a_{,x} + ( J_{\tau,z s,z}^{55} + J_{\tau,y s,y}^{66} ) \delta a a $$

### Transverse `y` block

$$ K_{yy}^{\tau s}: \quad ( J_{\tau,y s,y}^{22} + J_{\tau,z s,z}^{44} ) \delta b b + J_{\tau,\varnothing s,\varnothing}^{66} \delta b_{,x} b_{,x} $$

### Transverse `z` block

$$ K_{zz}^{\tau s}: \quad ( J_{\tau,z s,z}^{33} + J_{\tau,y s,y}^{44} ) \delta c c + J_{\tau,\varnothing s,\varnothing}^{55} \delta c_{,x} c_{,x} $$

### Coupling block `xy`

$$ K_{xy}^{\tau s}: \quad J_{\tau,\varnothing s,y}^{12} \delta a_{,x} b + J_{\tau,y s,\varnothing}^{66} \delta a b_{,x} $$

### Coupling block `yx`

$$ K_{yx}^{\tau s}: \quad J_{\tau,y s,\varnothing}^{21} \delta b a_{,x} + J_{\tau,\varnothing s,y}^{66} \delta b_{,x} a $$

### Coupling block `xz`

$$ K_{xz}^{\tau s}: \quad J_{\tau,\varnothing s,z}^{13} \delta a_{,x} c + J_{\tau,z s,\varnothing}^{55} \delta a c_{,x} $$

### Coupling block `zx`

$$ K_{zx}^{\tau s}: \quad J_{\tau,z s,\varnothing}^{31} \delta c a_{,x} + J_{\tau,\varnothing s,z}^{55} \delta c_{,x} a $$

### Coupling block `yz`

$$ K_{yz}^{\tau s}: \quad ( J_{\tau,y s,z}^{23} + J_{\tau,z s,y}^{44} ) \delta b c $$

### Coupling block `zy`

$$ K_{zy}^{\tau s}: \quad ( J_{\tau,z s,y}^{32} + J_{\tau,y s,z}^{44} ) \delta c b $$

These expressions constitute the complete fundamental nucleus before longitudinal integration by parts.

The diagonal terms containing derivatives on both longitudinal amplitudes lead directly to divergence-form operators.

For example, the axial contribution

$$ \int_0^l J_{\tau,\varnothing s,\varnothing}^{11}(x) \delta a_{,x}(x) a_{,x}(x) dx $$

gives, after longitudinal integration by parts,

$$ -\int_0^l \delta a(x) \partial_x [ J_{\tau,\varnothing s,\varnothing}^{11}(x) a_{,x}(x) ] dx $$

plus the corresponding boundary term.

Therefore the associated strong-form contribution is

$$ -\partial_x [ J_{\tau,\varnothing s,\varnothing}^{11}(x) \partial_x ]. $$

The same argument gives the variable-coefficient diagonal operators already introduced in the current formulation.

For the mixed first-order blocks, the two contributions must remain distinct.

For example, the weak-form contribution associated with `xy` is

$$ \int_0^l [ J_{\tau,\varnothing s,y}^{12}(x) \delta a_{,x}(x) b(x) + J_{\tau,y s,\varnothing}^{66}(x) \delta a(x) b_{,x}(x) ] dx. $$

Integrating only the first term by parts gives

$$ \int_0^l \delta a(x) [ - \partial_x ( J_{\tau,\varnothing s,y}^{12}(x) b(x) ) + J_{\tau,y s,\varnothing}^{66}(x) b_{,x}(x) ] dx $$

plus the corresponding boundary term.

Hence

$$ K_{xy}^{\tau s}(x)[b] = - \partial_x [ J_{\tau,\varnothing s,y}^{12}(x)b(x) ] + J_{\tau,y s,\varnothing}^{66}(x) \partial_x b(x) $$

which is exactly the variable-coefficient operator structure required by the current formulation.

Similarly, the `zx` block gives

$$ K_{zx}^{\tau s}(x)[a] = J_{\tau,z s,\varnothing}^{31}(x) \partial_x a(x) - \partial_x [ J_{\tau,\varnothing s,z}^{55}(x)a(x) ] $$

showing directly why the second contribution carries a minus sign after longitudinal integration by parts.

The zero-order coupling blocks require no longitudinal integration by parts:

$$ K_{yz}^{\tau s}(x) = J_{\tau,y s,z}^{23}(x) + J_{\tau,z s,y}^{44}(x) $$

and

$$ K_{zy}^{\tau s}(x) = J_{\tau,z s,y}^{32}(x) + J_{\tau,y s,z}^{44}(x). $$

The weak formulation therefore provides a direct derivation of all nine entries of the fundamental nucleus and simultaneously establishes the variable-coefficient longitudinal operator structure already used in the CSF-CUF extension.

The resulting chain is

$$ \mathcal{S}(x) \longrightarrow \{ \Omega^k(x), \mathbf{C}^{k}(x,y,z) \} \longrightarrow J_{\tau,\phi s,\xi}^{mn,k}(x) \longrightarrow J_{\tau,\phi s,\xi}^{mn}(x) \longrightarrow \delta L_i \longrightarrow \mathbf{K}_{\tau s}. $$

No closed-form longitudinal expression for the sectional coefficients is required, and no Navier-type longitudinal solution is introduced at this stage.

### 10.3 Diagonal terms - verified

The reference paper gives the three diagonal nuclear terms in Eq. (23) as:

$$ K_{xx}^{\tau s} = J_{\tau,y\,s,y}^{66k} + J_{\tau,z\,s,z}^{55k} - J_{\tau s}^{11k}\,\partial_x^2 $$

$$ K_{yy}^{\tau s} = J_{\tau,y\,s,y}^{22k} + J_{\tau,z\,s,z}^{44k} - J_{\tau s}^{66k}\,\partial_x^2 $$

$$ K_{zz}^{\tau s} = J_{\tau,y\,s,y}^{44k} + J_{\tau,z\,s,z}^{33k} - J_{\tau s}^{55k}\,\partial_x^2 $$

Each term contains one sectional coefficient multiplying a pure second derivative with respect to $x$.

The longitudinally varying form is therefore:

$$ K_{xx}^{\tau s}(x) = J_{\tau,y\,s,y}^{66k}(x) + J_{\tau,z\,s,z}^{55k}(x) - \partial_x \left( J_{\tau s}^{11k}(x)\,\partial_x \right) $$

$$ K_{yy}^{\tau s}(x) = J_{\tau,y\,s,y}^{22k}(x) + J_{\tau,z\,s,z}^{44k}(x) - \partial_x \left( J_{\tau s}^{66k}(x)\,\partial_x \right) $$

$$ K_{zz}^{\tau s}(x) = J_{\tau,y\,s,y}^{44k}(x) + J_{\tau,z\,s,z}^{33k}(x) - \partial_x \left( J_{\tau s}^{55k}(x)\,\partial_x \right) $$

These three terms are therefore established in divergence form.

---

### 10.4 Mixed first-order terms - verified variable-coefficient form

The reference paper gives the following first-order mixed terms:

$$ K_{xy}^{\tau s} = \left( -J_{\tau s,y}^{12k} + J_{\tau,y\,s}^{66k} \right)\partial_x $$

$$ K_{yx}^{\tau s} = \left( J_{\tau,y\,s}^{12k} - J_{\tau s,y}^{66k} \right)\partial_x $$

$$ K_{xz}^{\tau s} = \left( -J_{\tau s,z}^{13k} + J_{\tau,z\,s}^{55k} \right)\partial_x $$

$$ K_{zx}^{\tau s} = \left( J_{\tau,z\,s}^{13k} - J_{\tau s,z}^{55k} \right)\partial_x $$

For longitudinally varying sectional coefficients, the two contributions entering each mixed operator must remain distinct because they originate from different terms of the virtual internal work.

The verified variable-coefficient forms are:

$$ K_{xy}^{\tau s}(x)[u_{ys}] = -\partial_x\left( J_{\tau s,y}^{12k}(x)u_{ys}(x) \right) + J_{\tau,y\,s}^{66k}(x)\partial_x u_{ys}(x). $$

$$ K_{yx}^{\tau s}(x)[u_{xs}] = J_{\tau,y\,s}^{12k}(x)\partial_x u_{xs}(x) - \partial_x\left( J_{\tau s,y}^{66k}(x)u_{xs}(x) \right). $$

$$ K_{xz}^{\tau s}(x)[u_{zs}] = -\partial_x\left( J_{\tau s,z}^{13k}(x)u_{zs}(x) \right) + J_{\tau,z\,s}^{55k}(x)\partial_x u_{zs}(x). $$

$$ K_{zx}^{\tau s}(x)[u_{xs}] = J_{\tau,z\,s}^{13k}(x)\partial_x u_{xs}(x) - \partial_x\left( J_{\tau s,z}^{55k}(x)u_{xs}(x) \right). $$

The distinction between

$$ J(x)\partial_x u(x) $$

and

$$ \partial_x\left( J(x)u(x) \right) $$

is therefore retained explicitly.

For constant sectional coefficients, these expressions reduce to the corresponding first-order terms of the reference formulation.

> **Note on $K_{zx}^{\tau s}$.** Eq. (23) of Giunta, Belouettar, and Carrera (2010) reports a plus sign in the term involving $J_{\tau s,z}^{55k}$. However, the corresponding expressions in Eqs. (33) and (39) use a minus sign. The re-derivation from the virtual internal work is consistent with the minus sign; therefore the minus sign is adopted in the variable-section formulation.

---

### 10.5 Interpretation of the mixed first-order terms

The variable-coefficient form cannot be obtained by grouping the two sectional coefficients into a single coefficient before the longitudinal differentiation.

For example,

$$ K_{xy}^{\tau s}(x)[u_{ys}] = -\partial_x\left( J_{\tau s,y}^{12k}(x)u_{ys}(x) \right) + J_{\tau,y\,s}^{66k}(x)\partial_x u_{ys}(x) $$

contains two contributions with different longitudinal operator structures.

If expanded formally, the first term generates a longitudinal derivative of $J_{\tau s,y}^{12k}(x)$, while the coefficient $J_{\tau,y\,s}^{66k}(x)$ remains outside the longitudinal derivative.

The divergence form is retained so that no explicit longitudinal derivative of the sectional coefficients needs to be introduced in the formulation.

---

### 10.6 Established variable-coefficient structure

The diagonal second-order terms, the mixed first-order terms, and the zero-order off-diagonal terms are all defined for longitudinally varying sectional coefficients.

The dependence on the evolving CSF representation enters through the known sectional fields

$$ J_\bullet(x), $$

while the longitudinal differential structure of each nuclear term is retained in the appropriate divergence or first-order form.

---

### 10.7 Off-diagonal zero-order terms - direct generalization

The remaining two off-diagonal terms in Eq. (23) do not contain longitudinal derivatives:

$$ K_{yz}^{\tau s} = J_{\tau,y\,s,z}^{23k} + J_{\tau,z\,s,y}^{44k} $$

$$ K_{zy}^{\tau s} = J_{\tau,z\,s,y}^{23k} + J_{\tau,y\,s,z}^{44k} $$

Since no derivative with respect to $x$ acts on the displacement amplitudes in these terms, no additional longitudinal integration-by-parts issue is introduced by the dependence of the sectional coefficients on $x$.

Their variable-section form is therefore obtained directly as:

$$ K_{yz}^{\tau s}(x) = J_{\tau,y\,s,z}^{23k}(x) + J_{\tau,z\,s,y}^{44k}(x) $$

$$ K_{zy}^{\tau s}(x) = J_{\tau,z\,s,y}^{23k}(x) + J_{\tau,y\,s,z}^{44k}(x) $$

These terms require only the numerical evaluation of the corresponding sectional coefficients at the requested longitudinal coordinate.

---

### 10.8 Status summary

| Nuclear terms | Longitudinal structure | Status |
|---|---|---|
| $K_{xx}^{\tau s}(x)$ | one coefficient × second derivative | Verified - divergence form |
| $K_{yy}^{\tau s}(x)$ | one coefficient × second derivative | Verified - divergence form |
| $K_{zz}^{\tau s}(x)$ | one coefficient × second derivative | Verified - divergence form |
| $K_{xy}^{\tau s}(x)$, $K_{yx}^{\tau s}(x)$ | two coefficients × first derivative | Verified - variable-coefficient form |
| $K_{xz}^{\tau s}(x)$, $K_{zx}^{\tau s}(x)$ | two coefficients × first derivative | Verified - variable-coefficient form |
| $K_{yz}^{\tau s}(x)$, $K_{zy}^{\tau s}(x)$ | zero-order in $x$ | Direct generalization |

The variable-section structure of the complete nuclear operator is therefore established at the formal level. The sectional coefficients remain known functions of the longitudinal coordinate generated from the CSF representation.

---

## 11. No closed-form longitudinal solution is required

The reference paper proceeds further and adopts a Navier-type solution along $x$.

That step is not required for the present CSF-CUF formulation.

The formal development may stop at

$$ { \mathbf{K}_{\tau s} [ \mathcal{S}(x),\partial_x ] \mathbf{u}_s(x) = \mathbf{f}_\tau(x). } $$

The problem is then a system of differential equations with variable coefficients.

The numerical method used to solve that system is a subsequent and separate choice.

Therefore the formulation does not require:

- an analytical law for $\mathcal{S}(x)$;
- an analytical law for $J_\bullet(x)$;
- closed-form evaluation of the sectional integrals;
- a Navier-type analytical solution.

It requires only the capability to evaluate $\mathcal{S}(x)$ and the corresponding sectional integrals at the longitudinal coordinates requested by the numerical solver.

---

## 12. Formal CSF-CUF chain

The complete formal chain is

$$ { \mathcal{S}(x) } $$

$$ \Downarrow $$

$$ { \{ \Omega^k(x), \mathbf{C}^k(x,y,z) \}_{k=1}^{N_\Omega} } $$

$$ \Downarrow $$

$$ { J_\bullet^k(x) = \mathcal{J}_\bullet^k [ \mathcal{S}(x),F_\tau,F_s ] } $$

$$ \Downarrow $$

$$ { J_\bullet(x) = \sum_k J_\bullet^k(x) } $$

$$ \Downarrow $$

$$ { \delta L_i \quad\text{and}\quad \delta L_{\mathrm{ext}} } $$

$$ \Downarrow $$

$$ { \mathbf{K}_{\tau s} [ \mathcal{S}(x),\partial_x ] \mathbf{u}_s(x) = \mathbf{f}_\tau(x) } $$

$$ \Downarrow $$

$$ { \text{numerical solution in }x. } $$

The key point is that the CSF representation remains primary throughout the construction.

The CUF sectional coefficients are not required as predefined analytical functions of $x$. They are generated from the section field whenever they are needed.

---

## 13. Boundary between CSF and CUF

The responsibilities of the two formulations remain distinct.

### CSF supplies

$$ { \mathcal{S}(x) \longrightarrow \{ \Omega^k(x), \mathbf{C}^k(x,y,z) \}. } $$

### CUF supplies

- the approximation functions $F_\tau$ and $F_s$;
- their transverse derivatives;
- the approximation order;
- the displacement unknowns;
- the variational formulation;
- the fundamental nuclear structure.

### The coupling produces

$$ { J_\bullet(x) } $$

and therefore

$$ { \mathbf{K}_{\tau s} [ \mathcal{S}(x),\partial_x ]. } $$

Within this coupling, CSF provides the longitudinally evolving sectional representation required by the CUF mechanical formulation. It provides the longitudinally evolving sectional geometry and constitutive information from which the CUF sectional coefficients can be evaluated.

---

### References

- G. Giunta, S. Belouettar, E. Carrera, **“Analysis of FGM Beams by Means of Classical and Advanced Theories”**, *Mechanics of Advanced Materials and Structures*, 17 (2010), 622-635.

- S. O. Ojo, P. M. Weaver, **“Efficient strong Unified Formulation for stress analysis of non-prismatic beam structures”**, 2021.
