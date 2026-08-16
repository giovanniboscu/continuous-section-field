#  DRAFT
>The following material presents the current conceptual definition of the CSF-CUF sectional interface. The coupling is still under development and is intended to be implemented through a dedicated software bridge able to provide the sectional data required by the CUF formulation from the CSF representation $\mathcal{S}(x)$.

# Formal CSF–CUF coupling for a continuous longitudinal section model

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
- $\phi$ and $\xi$ denote transverse differentiation directions. The admissible derivative labels are

$$ \phi,\xi \in \{\varnothing,y,z\}. $$

Here $\varnothing$ denotes the absence of a transverse derivative.

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



### 5.1 Generalized sectional coefficient family

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

### Worked example: complete numerical evaluation of one sectional coefficient

The generalized sectional coefficient is defined as

$$ J_{\tau,\phi s,\xi}^{mn,k}(x) = \int_{\Omega^k(x)} C_{mn}^{k}(x,y,z) F_{\tau,\phi}(y,z) F_{s,\xi}(y,z) \, \mathrm{d}\Omega. $$


>The notation can be read by separating the coefficient into three parts:
>
>$$ J_{\tau,\phi s,\xi}^{mn,k}(x) \quad \longrightarrow \quad \text{constitutive indices and domain} + \text{CUF transverse functions} + \text{sectional integration}. $$
>
>| Symbol | Interpretation | Role in the coefficient |
>|---|---|---|
>| x | Longitudinal coordinate along the beam axis | Selects the current sectional state. The value of the coefficient changes with x because the domain and constitutive data may change with x. |
>| y, z | Transverse coordinates on the cross-section | Coordinates used to describe the physical sectional domain and to evaluate the CUF transverse approximation functions. |
>| k | Transverse sub-domain index | Selects the particular sectional domain Ωᵏ(x) and its associated constitutive matrix Cᵏ(x,y,z). |
>| Ωᵏ(x) | Physical transverse domain identified by k at coordinate x | Defines the region of the cross-section over which the integral is evaluated. |
>| m | Row index of the constitutive matrix | Together with n, selects one specific entry of Cᵏ(x,y,z). |
>| n | Column index of the constitutive matrix | Together with m, selects one specific entry of Cᵏ(x,y,z). |
>| Cₘₙᵏ(x,y,z) | Constitutive-matrix component at row m and column n for sub-domain k | Supplies the local material stiffness contribution used by this particular sectional coefficient. |
>| τ | Index of the first CUF transverse approximation function | Selects the function Fτ(y,z) from the chosen CUF transverse basis. |
>| φ | Transverse derivative selector applied to the function selected by τ | Specifies whether Fτ is used directly or differentiated with respect to y or z. |
>| Fτ,φ(y,z) | First CUF transverse factor after applying the derivative selector φ | Forms the first kinematic factor in the sectional integrand. |
>| s | Index of the second CUF transverse approximation function | Selects the function Fs(y,z) from the chosen CUF transverse basis. |
>| ξ | Transverse derivative selector applied to the function selected by s | Specifies whether Fs is used directly or differentiated with respect to y or z. |
>| Fs,ξ(y,z) | Second CUF transverse factor after applying the derivative selector ξ | Forms the second kinematic factor in the sectional integrand. |
>| dΩ | Differential sectional area | Represents integration over the physical cross-sectional domain. In Cartesian transverse coordinates, dΩ = dy dz. |
>| Jτ,φs,ξᵐⁿ,ᵏ(x) | Resulting sectional coefficient | Scalar coefficient obtained after integrating the constitutive and CUF transverse contributions over Ωᵏ(x). |>
>
>The derivative selectors are
>
>$$ \phi,\xi \in \{\varnothing,y,z\}. $$
>
>The symbol
>
>$$ \varnothing $$
>
>means that no transverse derivative is applied.
>Therefore,
>
>$$ F_{\tau,\varnothing}(y,z)=F_\tau(y,z). $$
>
>$$ F_{s,\varnothing}(y,z)=F_s(y,z). $$
>
>If the selector is y,
>
>$$ F_{\tau,y}(y,z)=\frac{\partial F_\tau(y,z)}{\partial y}. $$
>
>and
>
>$$ F_{s,y}(y,z)=\frac{\partial F_s(y,z)}{\partial y}. $$
>
>If the selector is z,
>
>$$ F_{\tau,z}(y,z)=\frac{\partial F_\tau(y,z)}{\partial z}. $$
>
>and
>
>$$ F_{s,z}(y,z)=\frac{\partial F_s(y,z)}{\partial z}. $$
>
>The subscript of J is therefore read as two ordered pairs:
>
>$$ (\tau,\phi) \qquad (s,\xi). $$
>
>The first pair determines
>
>$$ (\tau,\phi) \longrightarrow F_{\tau,\phi}(y,z). $$
>
>The second pair determines
>
>$$ (s,\xi) \longrightarrow F_{s,\xi}(y,z). $$
>
>The superscript identifies the constitutive contribution and the transverse sub-domain:
>
>$$ (m,n,k) \longrightarrow C_{mn}^{k}(x,y,z) \quad \text{over} \quad \Omega^k(x). $$
>
>Thus the complete coefficient can be read operationally as follows:
>
>1. use k to select the current physical sub-domain Ωᵏ(x);
>2. use m and n to select the required entry Cₘₙᵏ(x,y,z) of the constitutive matrix;
>3. use τ and φ to construct the first CUF transverse factor;
>4. use s and ξ to construct the second CUF transverse factor;
>5. multiply the three contributions over the section;
>6. integrate the resulting quantity over Ωᵏ(x).


For this worked example, consider the specific coefficient

$$ J_{2,y\,2,y}^{66,1}(x). $$


The objective is to determine this coefficient completely and obtain an explicit numerical function of the longitudinal coordinate `x`.

### Origin of all indices and quantities

| Quantity | Value used in the example | Origin | What it determines |
|---|---:|---|---|
| m | 6 | Term appearing in the CUF fundamental nucleus | First constitutive index of C₆₆ |
| n | 6 | Term appearing in the CUF fundamental nucleus | Second constitutive index of C₆₆ |
| φ | y | Term appearing in the CUF fundamental nucleus | Derivative with respect to y of the function on the τ side |
| ξ | y | Term appearing in the CUF fundamental nucleus | Derivative with respect to y of the function on the s side |
| τ | 2 | Choice within the first-order CUF transverse basis | Selects F₂ |
| s | 2 | Choice within the first-order CUF transverse basis | Selects F₂ |
| k | 1 | Selected transverse sub-domain | Selects Ω¹(x) and C₆₆¹(x,y,z) |
| x | variable | Longitudinal beam coordinate | Determines the current sectional state |
| y, z | variables | Transverse coordinates | Coordinates of sectional integration |
| L | 10 m | Geometrical datum of the example | Beam length |
| C₆₆¹(x,y,z) | assigned below | Constitutive description of sub-domain 1 | Constitutive component required by the selected nucleus term |
| Ω¹(x) | assigned below | Sectional geometry | Physical integration domain |

The selected term of the fundamental nucleus has the form

$$ J_{\tau,y\,s,y}^{66,k}(x). $$

Therefore,

$$ m=6,\qquad n=6,\qquad \phi=y,\qquad \xi=y. $$

For this example, the first transverse sub-domain is selected:

$$ k=1. $$

A first-order CUF transverse expansion is used. Its basis functions are

$$ F_1(y,z)=1,\qquad F_2(y,z)=y,\qquad F_3(y,z)=z. $$

The selected CUF indices are

$$ \tau=2,\qquad s=2. $$

Therefore,

$$ F_\tau(y,z)=F_2(y,z)=y. $$

and

$$ F_s(y,z)=F_2(y,z)=y. $$

Because

$$ \phi=y,\qquad \xi=y, $$

the required transverse derivatives are

$$ F_{\tau,\phi}(y,z)=F_{2,y}(y,z)=\frac{\partial y}{\partial y}=1. $$

and

$$ F_{s,\xi}(y,z)=F_{2,y}(y,z)=\frac{\partial y}{\partial y}=1. $$

The generalized definition therefore becomes

$$ J_{2,y\,2,y}^{66,1}(x) = \int_{\Omega^1(x)} C_{66}^{1}(x,y,z) F_{2,y}(y,z) F_{2,y}(y,z) \, \mathrm{d}\Omega. $$

Since both derivatives are equal to one,

$$ J_{2,y\,2,y}^{66,1}(x) = \int_{\Omega^1(x)} C_{66}^{1}(x,y,z) \, \mathrm{d}\Omega. $$

### Constitutive component

The fundamental nucleus determines that the required constitutive component is

$$ C_{66}^{1}(x,y,z). $$

For the worked example, assign directly

$$ C_{66}^{1}(x,y,z)=26\times10^9(1-0.10\frac{x}{L})\ \mathrm{Pa}. $$

> **Origin of the constitutive component.**  
> The term `C(6,6)` is the entry at row 6 and column 6 of the constitutive matrix associated with the selected transverse domain, as defined in [CSF sectional constitutive representation for CUF coupling](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_sectional_constitutive_interface.md).
>
> For the selected domain
>
> $$ k=1, $$
>
> the corresponding constitutive component is
>
> $$ C_{66}^{1}(x). $$
>
> In the two-field constitutive specialization adopted in the referenced document,
>
> $$ C_{66}^{1}(x)=G_1(x). $$
>
> Therefore, the constitutive component used in the worked example is specific to domain `1`: if a different domain `k` were selected, the corresponding term would be `C(6,6)` of that domain, namely
>
> $$ C_{66}^{k}(x)=G_k(x). $$

The beam length is

$$ L=10\ \mathrm{m}. $$

The constitutive component is uniform over the transverse coordinates `y` and `z`, but varies along the longitudinal coordinate `x`.

At the beam origin,

$$ C_{66}^{1}(0,y,z)=26\times10^9\ \mathrm{Pa}. $$

At the beam end,

$$ C_{66}^{1}(L,y,z)=23.4\times10^9\ \mathrm{Pa}. $$

### Sectional domain

The first transverse sub-domain is defined directly through its integration limits.

Along the transverse coordinate `y`,

$$ -0.05+0.01\frac{x}{L} \le y \le 0.05-0.01\frac{x}{L}. $$

Along the transverse coordinate `z`,

$$ -0.025 \le z \le 0.025. $$

All geometrical quantities are expressed in metres.

At the beam origin, the dimension of the sub-domain along `y` is

$$ 0.10\ \mathrm{m}. $$

At the beam end, the dimension along `y` is

$$ 0.08\ \mathrm{m}. $$

The dimension along `z` remains constant:

$$ 0.05\ \mathrm{m}. $$

The physical integration domain is therefore completely defined by these limits.

### Complete substitution into the sectional coefficient

The coefficient to be evaluated is

$$ J_{2,y\,2,y}^{66,1}(x) = \int_{\Omega^1(x)} C_{66}^{1}(x,y,z) \, \mathrm{d}\Omega. $$

The sectional differential area is

$$ \mathrm{d}\Omega=\mathrm{d}y\,\mathrm{d}z. $$

Substituting the constitutive component and the actual integration limits gives

$$ J_{2,y\,2,y}^{66,1}(x) = \int_{-0.025}^{0.025}\int_{-0.05+0.01x/L}^{0.05-0.01x/L}26\times10^9(1-0.10\frac{x}{L})\,\mathrm{d}y\,\mathrm{d}z. $$

At this point every quantity in the integral is known.

### Integration with respect to y

The constitutive component does not depend on `y`, so the inner geometrical integral is

$$ \int_{-0.05+0.01x/L}^{0.05-0.01x/L}\mathrm{d}y. $$

Evaluating the limits gives

$$ \int_{-0.05+0.01x/L}^{0.05-0.01x/L}\mathrm{d}y = (0.05-0.01\frac{x}{L})-(-0.05+0.01\frac{x}{L}). $$

Therefore,

$$ \int_{-0.05+0.01x/L}^{0.05-0.01x/L}\mathrm{d}y = 0.10-0.02\frac{x}{L}. $$

The sectional coefficient becomes

$$ J_{2,y\,2,y}^{66,1}(x) = 26\times10^9(1-0.10\frac{x}{L})(0.10-0.02\frac{x}{L})\int_{-0.025}^{0.025}\mathrm{d}z. $$

### Integration with respect to z

The remaining integral is

$$ \int_{-0.025}^{0.025}\mathrm{d}z=0.05. $$

Therefore,

$$ J_{2,y\,2,y}^{66,1}(x) = 26\times10^9(1-0.10\frac{x}{L})(0.10-0.02\frac{x}{L})(0.05). $$

Multiplying the geometrical terms gives

$$ J_{2,y\,2,y}^{66,1}(x) = 26\times10^9(1-0.10\frac{x}{L})(0.005-0.001\frac{x}{L}). $$

Expanding the product,

$$ (1-0.10\frac{x}{L})(0.005-0.001\frac{x}{L})=0.005-0.0015\frac{x}{L}+0.0001(\frac{x}{L})^2. $$

Hence,

$$ J_{2,y\,2,y}^{66,1}(x)=130000000-39000000\frac{x}{L}+2600000(\frac{x}{L})^2\ \mathrm{N}. $$

Using

$$ L=10\ \mathrm{m}, $$

the resolved coefficient can be written directly as a function of `x`, with `x` expressed in metres:

$$ \boxed{J_{2,y\,2,y}^{66,1}(x)=130000000-3900000x+26000x^2\ \mathrm{N}.} $$

### Numerical checks

At the beam origin,

$$ J_{2,y\,2,y}^{66,1}(0)=130000000\ \mathrm{N}. $$

At mid-span,

$$ J_{2,y\,2,y}^{66,1}(5)=111150000\ \mathrm{N}. $$

At the beam end,

$$ J_{2,y\,2,y}^{66,1}(10)=93600000\ \mathrm{N}. $$

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

$$ \delta L_i = \delta L_p + \delta L_l. $$

After the sectional integrations have been represented through the global coefficients $J_\bullet(x)$, the governing equations retain the CUF nuclear structure but acquire longitudinally varying sectional coefficients.

Formally,

$$ \mathbf{K}_{\tau s}[\mathcal{S}(x),\partial_x] \, \mathbf{u}_s(x) = \mathbf{f}_\tau(x), $$

where

- $\mathbf{u}_s(x)$ contains the longitudinal unknown amplitudes associated with CUF index $s$;
- $\mathbf{f}_\tau(x)$ contains the generalized load terms associated with index $\tau$;
- $\mathbf{K}_{\tau s}$ is the CUF fundamental nuclear operator assembled over the complete cross-section;
- the dependence of $\mathbf{K}_{\tau s}$ on the section is mediated by the global sectional fields $J_\bullet(x)$.

The nuclear matrix retains the $3\times3$ structure

$$ \mathbf{K}_{\tau s} = \begin{bmatrix} K_{xx}^{\tau s} & K_{xy}^{\tau s} & K_{xz}^{\tau s} \\ K_{yx}^{\tau s} & K_{yy}^{\tau s} & K_{yz}^{\tau s} \\ K_{zx}^{\tau s} & K_{zy}^{\tau s} & K_{zz}^{\tau s} \end{bmatrix}. $$

The distinction between sub-domain and global quantities is essential. A coefficient carrying the index $k$,

$$ J_{\tau,\phi s,\xi}^{mn,k}(x), $$

is the contribution associated with sub-domain $k$. The coefficient entering the assembled operator $\mathbf{K}_{\tau s}$ is instead

$$ J_{\tau,\phi s,\xi}^{mn}(x) = \sum_{k=1}^{N_\Omega} J_{\tau,\phi s,\xi}^{mn,k}(x). $$

Therefore, from this point onward, formulas representing the assembled CSF-CUF nuclear operator use global coefficients without the index $k$. When the corresponding reference-paper expressions are reported, the sub-domain index is retained explicitly and the subsequent global assembly is shown separately.

---

## 10. Longitudinally varying coefficients inside the nuclear operator

> This section builds on the sectional interface defined in
> [`csf_cuf_sectional_constitutive_interface.md`](csf_cuf_sectional_constitutive_interface.md),
> where the CSF-CUF coupling and the role of the dedicated software bridge are introduced.

### 10.1 Principle

When a sectional coefficient multiplying an $x$-derivative depends on $x$, the coefficient must remain inside the longitudinal differential operator.

For a constant coefficient:

$$ -J\,\partial_x^2 u(x) $$

For a longitudinally varying coefficient:

$$ -\partial_x\left[J(x)\,\partial_x u(x)\right] $$

The expression is retained in divergence form rather than expanded through the product rule. This avoids introducing an unnecessary explicit classical derivative of $J(x)$ into the formulation.

This generalization is directly justified when a nuclear term contains a single sectional coefficient multiplying a pure second derivative with respect to $x$.

---

### 10.2 Complete fundamental nucleus in weak form

The complete nuclear structure can be obtained directly from the Principle of Virtual Displacements before introducing any strong-form longitudinal differential operator.

Let the CUF displacement expansion associated with source index $s$ be

$$ u_i(x,y,z) = F_s(y,z)\,u_{is}(x), \qquad i\in\{x,y,z\}. $$

For compactness, define the three source amplitudes as

$$ a(x)=u_{xs}(x), $$

$$ b(x)=u_{ys}(x), $$

and

$$ c(x)=u_{zs}(x). $$

Let the corresponding virtual amplitudes associated with test index $\tau$ be

$$ \delta a(x)=\delta u_{x\tau}(x), $$

$$ \delta b(x)=\delta u_{y\tau}(x), $$

and

$$ \delta c(x)=\delta u_{z\tau}(x). $$

Define

$$ A(y,z)=F_s(y,z) $$

and

$$ B(y,z)=F_\tau(y,z). $$

The source strain components are

$$ \varepsilon_{xx}=A\,a_{,x}, $$

$$ \varepsilon_{yy}=A_{,y}\,b, $$

$$ \varepsilon_{zz}=A_{,z}\,c, $$

$$ \gamma_{yz}=A_{,z}\,b+A_{,y}\,c, $$

$$ \gamma_{xz}=A_{,z}\,a+A\,c_{,x}, $$

and

$$ \gamma_{xy}=A_{,y}\,a+A\,b_{,x}. $$

The corresponding virtual strains are obtained by replacing $A$ with $B$ and replacing the source amplitudes with the corresponding virtual amplitudes.

For an isotropic constitutive specialization in Voigt order

$$ (xx,yy,zz,yz,xz,xy), $$

the non-zero constitutive entries involved in the present derivation are

$$ C_{11},\quad C_{22},\quad C_{33},\quad C_{44},\quad C_{55},\quad C_{66}, $$

together with

$$ C_{12}=C_{21}, \qquad C_{13}=C_{31}, \qquad C_{23}=C_{32}. $$

The internal virtual work is

$$ \delta L_i = \int_0^l \sum_{k=1}^{N_\Omega} \int_{\Omega^k(x)} \delta\boldsymbol{\varepsilon}^{T} \mathbf{C}^{k}(x,y,z) \boldsymbol{\varepsilon} \,d\Omega\,dx. $$

At fixed $x$, the transverse integrations are first evaluated over the individual sub-domains and then summed. Consequently, the nine blocks below are written directly in terms of the global sectional coefficients defined in §5.1 and §6. No index $k$ appears in these assembled bilinear forms.

#### Axial block

$$ K_{xx}^{\tau s}: \quad J_{\tau,\varnothing s,\varnothing}^{11}\,\delta a_{,x}a_{,x} + \left( J_{\tau,z s,z}^{55} + J_{\tau,y s,y}^{66} \right)\delta a\,a $$

#### Transverse `y` block

$$ K_{yy}^{\tau s}: \quad \left( J_{\tau,y s,y}^{22} + J_{\tau,z s,z}^{44} \right)\delta b\,b + J_{\tau,\varnothing s,\varnothing}^{66}\,\delta b_{,x}b_{,x} $$

#### Transverse `z` block

$$ K_{zz}^{\tau s}: \quad \left( J_{\tau,z s,z}^{33} + J_{\tau,y s,y}^{44} \right)\delta c\,c + J_{\tau,\varnothing s,\varnothing}^{55}\,\delta c_{,x}c_{,x} $$

#### Coupling block `xy`

$$ K_{xy}^{\tau s}: \quad J_{\tau,\varnothing s,y}^{12}\,\delta a_{,x}b + J_{\tau,y s,\varnothing}^{66}\,\delta a\,b_{,x} $$

#### Coupling block `yx`

$$ K_{yx}^{\tau s}: \quad J_{\tau,y s,\varnothing}^{12}\,\delta b\,a_{,x} + J_{\tau,\varnothing s,y}^{66}\,\delta b_{,x}a $$

#### Coupling block `xz`

$$ K_{xz}^{\tau s}: \quad J_{\tau,\varnothing s,z}^{13}\,\delta a_{,x}c + J_{\tau,z s,\varnothing}^{55}\,\delta a\,c_{,x} $$

#### Coupling block `zx`

$$ K_{zx}^{\tau s}: \quad J_{\tau,z s,\varnothing}^{13}\,\delta c\,a_{,x} + J_{\tau,\varnothing s,z}^{55}\,\delta c_{,x}a $$

#### Coupling block `yz`

$$ K_{yz}^{\tau s}: \quad \left( J_{\tau,y s,z}^{23} + J_{\tau,z s,y}^{44} \right)\delta b\,c $$

#### Coupling block `zy`

$$ K_{zy}^{\tau s}: \quad \left( J_{\tau,z s,y}^{23} + J_{\tau,y s,z}^{44} \right)\delta c\,b $$

These expressions constitute the complete fundamental nucleus before longitudinal integration by parts, already in global form.

The diagonal terms containing derivatives on both longitudinal amplitudes lead directly to divergence-form operators. For example, the axial contribution

$$ \int_0^l J_{\tau,\varnothing s,\varnothing}^{11}(x) \,\delta a_{,x}(x)\,a_{,x}(x) \,dx $$

gives, after longitudinal integration by parts,

$$ -\int_0^l \delta a(x)\, \partial_x\left[ J_{\tau,\varnothing s,\varnothing}^{11}(x) a_{,x}(x) \right] \,dx $$

plus the corresponding boundary term. Therefore the associated strong-form contribution is

$$ -\partial_x\left[ J_{\tau,\varnothing s,\varnothing}^{11}(x)\,\partial_x \right]. $$

For the mixed first-order blocks, the two contributions must remain distinct. For example, the weak-form contribution associated with `xy` is

$$ \int_0^l \left[ J_{\tau,\varnothing s,y}^{12}(x)\,\delta a_{,x}(x)b(x) + J_{\tau,y s,\varnothing}^{66}(x)\,\delta a(x)b_{,x}(x) \right] \,dx. $$

Integrating only the first term by parts gives

$$ \int_0^l \delta a(x) \left[ -\partial_x\left( J_{\tau,\varnothing s,y}^{12}(x)b(x) \right) + J_{\tau,y s,\varnothing}^{66}(x)b_{,x}(x) \right] \,dx $$

plus the corresponding boundary term. Hence

$$ K_{xy}^{\tau s}(x)[b] = -\partial_x\left[ J_{\tau,\varnothing s,y}^{12}(x)b(x) \right] + J_{\tau,y s,\varnothing}^{66}(x)\,\partial_x b(x). $$

Similarly, the `zx` block gives

$$ K_{zx}^{\tau s}(x)[a] = J_{\tau,z s,\varnothing}^{13}(x)\,\partial_x a(x) - \partial_x\left[ J_{\tau,\varnothing s,z}^{55}(x)a(x) \right]. $$

The zero-order coupling blocks require no longitudinal integration by parts:

$$ K_{yz}^{\tau s}(x) = J_{\tau,y s,z}^{23}(x) + J_{\tau,z s,y}^{44}(x), $$

and

$$ K_{zy}^{\tau s}(x) = J_{\tau,z s,y}^{23}(x) + J_{\tau,y s,z}^{44}(x). $$

The resulting chain is

$$ \mathcal{S}(x) \longrightarrow \{\Omega^k(x),\mathbf{C}^{k}(x,y,z)\} \longrightarrow J_{\tau,\phi s,\xi}^{mn,k}(x) \longrightarrow J_{\tau,\phi s,\xi}^{mn}(x) \longrightarrow \delta L_i \longrightarrow \mathbf{K}_{\tau s}. $$

No closed-form longitudinal expression for the sectional coefficients is required, and no Navier-type longitudinal solution is introduced at this stage.

---

#### 10.2.1 Sub-domain and global coefficients

For any fixed choice of CUF indices, derivative labels, and constitutive indices, abbreviate the corresponding sub-domain coefficient as $J^{mn,k}(x)$ and the associated global coefficient as $J^{mn}(x)$. Let $v(x)$ denote any longitudinal displacement amplitude or test function entering the nuclear operator. Then

$$ J^{mn}(x) = \sum_{k=1}^{N_\Omega}J^{mn,k}(x). $$

Because the sub-domain sum is finite and the longitudinal differential operator is linear, assembly and longitudinal differentiation commute. For the second-order divergence structure,

$$ \sum_{k=1}^{N_\Omega} \partial_x\left[ J^{mn,k}(x)\,\partial_x v(x) \right] = \partial_x\left[ J^{mn}(x)\,\partial_x v(x) \right]. $$

For a first-order divergence term,

$$ \sum_{k=1}^{N_\Omega} \partial_x\left[ J^{mn,k}(x)\,v(x) \right] = \partial_x\left[ J^{mn}(x)\,v(x) \right]. $$

For a coefficient multiplying a longitudinal derivative without being differentiated itself,

$$ \sum_{k=1}^{N_\Omega} J^{mn,k}(x)\,\partial_x v(x) = J^{mn}(x)\,\partial_x v(x). $$

These identities show that the global forms below are obtained exactly by summing the sub-domain contributions. They are the same global operators obtained directly from the weak formulation in §10.2.

---

### 10.3 Diagonal terms - verified

The reference-paper form of the three diagonal nuclear terms is

$$ K_{xx}^{\tau s} = J_{\tau,y s,y}^{66k} + J_{\tau,z s,z}^{55k} - J_{\tau s}^{11k}\,\partial_x^2, $$

$$ K_{yy}^{\tau s} = J_{\tau,y s,y}^{22k} + J_{\tau,z s,z}^{44k} - J_{\tau s}^{66k}\,\partial_x^2, $$

and

$$ K_{zz}^{\tau s} = J_{\tau,y s,y}^{44k} + J_{\tau,z s,z}^{33k} - J_{\tau s}^{55k}\,\partial_x^2. $$

Here the coefficients carrying $k$ are sub-domain contributions. To make the assembly explicit, let $K_{ii}^{\tau s,k}$ denote the contribution associated with sub-domain $k$.

For longitudinally varying coefficients, the corresponding sub-domain forms are

$$ K_{xx}^{\tau s,k}(x) = J_{\tau,y s,y}^{66k}(x) + J_{\tau,z s,z}^{55k}(x) - \partial_x\left[ J_{\tau s}^{11k}(x)\,\partial_x \right], $$

$$ K_{yy}^{\tau s,k}(x) = J_{\tau,y s,y}^{22k}(x) + J_{\tau,z s,z}^{44k}(x) - \partial_x\left[ J_{\tau s}^{66k}(x)\,\partial_x \right], $$

and

$$ K_{zz}^{\tau s,k}(x) = J_{\tau,y s,y}^{44k}(x) + J_{\tau,z s,z}^{33k}(x) - \partial_x\left[ J_{\tau s}^{55k}(x)\,\partial_x \right]. $$

After summing over the sub-domains, the assembled CSF-CUF forms are

$$ K_{xx}^{\tau s}(x) = J_{\tau,y s,y}^{66}(x) + J_{\tau,z s,z}^{55}(x) - \partial_x\left[ J_{\tau s}^{11}(x)\,\partial_x \right], $$

$$ K_{yy}^{\tau s}(x) = J_{\tau,y s,y}^{22}(x) + J_{\tau,z s,z}^{44}(x) - \partial_x\left[ J_{\tau s}^{66}(x)\,\partial_x \right], $$

and

$$ K_{zz}^{\tau s}(x) = J_{\tau,y s,y}^{44}(x) + J_{\tau,z s,z}^{33}(x) - \partial_x\left[ J_{\tau s}^{55}(x)\,\partial_x \right]. $$

These global forms match the diagonal terms obtained directly from §10.2.

---

### 10.4 Mixed first-order terms - verified variable-coefficient form

The reference-paper form of the mixed first-order terms is

$$ K_{xy}^{\tau s} = \left( -J_{\tau s,y}^{12k} + J_{\tau,y s}^{66k} \right)\partial_x, $$

$$ K_{yx}^{\tau s} = \left( J_{\tau,y s}^{12k} - J_{\tau s,y}^{66k} \right)\partial_x, $$

$$ K_{xz}^{\tau s} = \left( -J_{\tau s,z}^{13k} + J_{\tau,z s}^{55k} \right)\partial_x, $$

and

$$ K_{zx}^{\tau s} = \left( J_{\tau,z s}^{13k} - J_{\tau s,z}^{55k} \right)\partial_x. $$

For longitudinally varying sectional coefficients, the two contributions entering each mixed operator must remain distinct because they originate from different terms of the virtual internal work.

The corresponding sub-domain forms are

$$ K_{xy}^{\tau s,k}(x)[u_{ys}] = -\partial_x\left[ J_{\tau s,y}^{12k}(x)u_{ys}(x) \right] + J_{\tau,y s}^{66k}(x)\,\partial_x u_{ys}(x), $$

$$ K_{yx}^{\tau s,k}(x)[u_{xs}] = J_{\tau,y s}^{12k}(x)\,\partial_x u_{xs}(x) - \partial_x\left[ J_{\tau s,y}^{66k}(x)u_{xs}(x) \right], $$

$$ K_{xz}^{\tau s,k}(x)[u_{zs}] = -\partial_x\left[ J_{\tau s,z}^{13k}(x)u_{zs}(x) \right] + J_{\tau,z s}^{55k}(x)\,\partial_x u_{zs}(x), $$

and

$$ K_{zx}^{\tau s,k}(x)[u_{xs}] = J_{\tau,z s}^{13k}(x)\,\partial_x u_{xs}(x) - \partial_x\left[ J_{\tau s,z}^{55k}(x)u_{xs}(x) \right]. $$

After summing over the sub-domains, the assembled CSF-CUF forms are

$$ K_{xy}^{\tau s}(x)[u_{ys}] = -\partial_x\left[ J_{\tau s,y}^{12}(x)u_{ys}(x) \right] + J_{\tau,y s}^{66}(x)\,\partial_x u_{ys}(x), $$

$$ K_{yx}^{\tau s}(x)[u_{xs}] = J_{\tau,y s}^{12}(x)\,\partial_x u_{xs}(x) - \partial_x\left[ J_{\tau s,y}^{66}(x)u_{xs}(x) \right], $$

$$ K_{xz}^{\tau s}(x)[u_{zs}] = -\partial_x\left[ J_{\tau s,z}^{13}(x)u_{zs}(x) \right] + J_{\tau,z s}^{55}(x)\,\partial_x u_{zs}(x), $$

and

$$ K_{zx}^{\tau s}(x)[u_{xs}] = J_{\tau,z s}^{13}(x)\,\partial_x u_{xs}(x) - \partial_x\left[ J_{\tau s,z}^{55}(x)u_{xs}(x) \right]. $$

The distinction between

$$ J(x)\,\partial_x u(x) $$

and

$$ \partial_x\left[J(x)u(x)\right] $$

is therefore retained explicitly at both the sub-domain and global levels.

For constant sectional coefficients, these expressions reduce to the corresponding first-order terms of the reference formulation.

> **Note on $K_{zx}^{\tau s}$.** Eq. (23) of Giunta, Belouettar, and Carrera (2010) reports a plus sign in the term involving $J_{\tau s,z}^{55k}$. However, the corresponding expressions in Eqs. (33) and (39) use a minus sign. The re-derivation from the virtual internal work in §10.2 is consistent with the minus sign; therefore the minus sign is adopted in the variable-section formulation.

---

### 10.5 Interpretation of the mixed first-order terms

The variable-coefficient form cannot be obtained by grouping the two sectional coefficients into a single coefficient before the longitudinal differentiation.

For example, the global `xy` term is

$$ K_{xy}^{\tau s}(x)[u_{ys}] = -\partial_x\left[ J_{\tau s,y}^{12}(x)u_{ys}(x) \right] + J_{\tau,y s}^{66}(x)\,\partial_x u_{ys}(x). $$

It contains two contributions with different longitudinal operator structures. If expanded formally, the first term generates a longitudinal derivative of $J_{\tau s,y}^{12}(x)$, while $J_{\tau,y s}^{66}(x)$ remains outside the longitudinal derivative.

The divergence form is retained so that no explicit longitudinal derivative of the sectional coefficients needs to be introduced in the formulation.

---

### 10.6 Established variable-coefficient structure

The diagonal second-order terms, the mixed first-order terms, and the zero-order off-diagonal terms are all defined for longitudinally varying sectional coefficients.

At the sub-domain level, the corresponding quantities carry the index $k$. In the assembled nuclear operator, the dependence on the evolving CSF representation enters through the global sectional fields

$$ J_\bullet(x), $$

while the longitudinal differential structure of each nuclear term is retained in the appropriate divergence or first-order form.

---

### 10.7 Off-diagonal zero-order terms - direct generalization

The remaining two off-diagonal terms in the reference formulation do not contain longitudinal derivatives:

$$ K_{yz}^{\tau s} = J_{\tau,y s,z}^{23k} + J_{\tau,z s,y}^{44k}, $$

and

$$ K_{zy}^{\tau s} = J_{\tau,z s,y}^{23k} + J_{\tau,y s,z}^{44k}. $$

Let $K_{yz}^{\tau s,k}$ and $K_{zy}^{\tau s,k}$ denote the corresponding sub-domain contributions. Their variable-section forms are

$$ K_{yz}^{\tau s,k}(x) = J_{\tau,y s,z}^{23k}(x) + J_{\tau,z s,y}^{44k}(x), $$

and

$$ K_{zy}^{\tau s,k}(x) = J_{\tau,z s,y}^{23k}(x) + J_{\tau,y s,z}^{44k}(x). $$

Since no longitudinal derivative acts on these terms, the global assembly is obtained directly by summing the coefficients:

$$ K_{yz}^{\tau s}(x) = J_{\tau,y s,z}^{23}(x) + J_{\tau,z s,y}^{44}(x), $$

and

$$ K_{zy}^{\tau s}(x) = J_{\tau,z s,y}^{23}(x) + J_{\tau,y s,z}^{44}(x). $$

These global expressions coincide with the zero-order blocks obtained directly from §10.2.

---

### 10.8 Status summary

| Nuclear terms | Longitudinal structure | Sub-domain contribution | Global CSF-CUF operator |
|---|---|---|---|
| $K_{xx}^{\tau s}(x)$ | one coefficient × second derivative | §10.3 | §10.3; matches §10.2 |
| $K_{yy}^{\tau s}(x)$ | one coefficient × second derivative | §10.3 | §10.3; matches §10.2 |
| $K_{zz}^{\tau s}(x)$ | one coefficient × second derivative | §10.3 | §10.3; matches §10.2 |
| $K_{xy}^{\tau s}(x)$, $K_{yx}^{\tau s}(x)$ | two coefficients × first derivative | §10.4 | §10.4; matches §10.2 |
| $K_{xz}^{\tau s}(x)$, $K_{zx}^{\tau s}(x)$ | two coefficients × first derivative | §10.4 | §10.4; matches §10.2 |
| $K_{yz}^{\tau s}(x)$, $K_{zy}^{\tau s}(x)$ | zero-order in $x$ | §10.7 | §10.7; matches §10.2 |

The variable-section structure of the complete nuclear operator is therefore established at the formal level. The distinction between the sub-domain coefficients $J^{mn,k}_{\tau,\phi s,\xi}(x)$ and the global coefficients $J^{mn}_{\tau,\phi s,\xi}(x)$ entering the assembled operator $\mathbf{K}_{\tau s}$ is explicit throughout the formulation.

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
