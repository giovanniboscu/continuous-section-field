#  DRAFT
>The following material presents the current conceptual definition of the CSF-CUF sectional interface. The coupling is still under development and is intended to be implemented through a dedicated software bridge able to provide the sectional data required by the CUF formulation from the CSF representation $\mathcal{S}(x)$.

# Formal CSF-CUF coupling for a continuous longitudinal section model

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

### CUF displacement-expansion premise

The present variable-section extension retains the CUF displacement expansion described in [`csf_cuf_displacement_expansionf_coupling.md`](./csf_cuf_displacement_expansionf_coupling.md).

In that kinematic statement, the CUF transverse approximation functions remain functions of the transverse coordinates only,

$$ F_\tau = F_\tau(y,z). $$

The longitudinal variation introduced here does not replace them with functions of the form $F_\tau(x,y,z)$.

Instead, the CSF representation supplies the current transverse domain and constitutive state at each longitudinal coordinate,

$$ x \longmapsto \mathcal{S}(x) \longmapsto \lbrace \Omega^k(x), \mathbf{C}^k(x,y,z) \rbrace. $$

Therefore the CUF kinematic approximation is retained, while the sectional integrations are evaluated over the longitudinally evolving domains $\Omega^k(x)$ and produce sectional coefficients that depend on $x$.



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


> The notation can be read by identifying the ingredients that construct the sectional coefficient:
>
> $$ J_{\tau,\phi s,\xi}^{mn,k}(x) \quad \longrightarrow \quad \text{sectional state} + \text{constitutive contribution} + \text{test-side CUF factor} + \text{trial-side CUF factor} + \text{sectional integration}. $$
>
> | Symbol         | Interpretation                                                                    | Role in the coefficient                                                                                                                     |
> | -------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
> | x              | Longitudinal coordinate along the beam axis                                       | Selects the current sectional state. The coefficient may depend on x because the sectional domain and constitutive data may depend on x.    |
> | y, z           | Transverse coordinates on the cross-section                                       | Coordinates used to describe the physical sectional domain and to evaluate the CUF transverse approximation functions.                      |
> | k              | Transverse sub-domain index                                                       | Selects the sectional domain Ωᵏ(x) and the constitutive matrix Cᵏ(x,y,z) associated with that domain.                                       |
> | Ωᵏ(x)          | Physical transverse domain identified by k at coordinate x                        | Defines the region of the cross-section over which the coefficient is evaluated.                                                            |
> | m              | Row index of the constitutive matrix                                              | Together with n, selects one specific entry of Cᵏ(x,y,z).                                                                                   |
> | n              | Column index of the constitutive matrix                                           | Together with m, selects one specific entry of Cᵏ(x,y,z).                                                                                   |
> | Cₘₙᵏ(x,y,z)    | Constitutive-matrix component at row m and column n for sub-domain k              | Supplies the material stiffness contribution entering the sectional integrand.                                                              |
> | τ              | Index of the CUF transverse approximation function on the virtual/test side       | Selects Fτ(y,z) from the chosen CUF transverse approximation basis for the virtual field.                                                   |
> | φ              | Transverse derivative selector associated with τ                                  | Specifies whether the test-side function Fτ is used directly or differentiated with respect to y or z.                                      |
> | Fτ,φ(y,z)      | Test-side CUF transverse factor                                                   | Contribution generated from the virtual field after applying the derivative selector φ.                                                     |
> | s              | Index of the CUF transverse approximation function on the displacement/trial side | Selects Fs(y,z) from the same CUF transverse approximation basis for the unknown displacement field.                                        |
> | ξ              | Transverse derivative selector associated with s                                  | Specifies whether the trial-side function Fs is used directly or differentiated with respect to y or z.                                     |
> | Fs,ξ(y,z)      | Trial-side CUF transverse factor                                                  | Contribution generated from the unknown displacement field after applying the derivative selector ξ.                                        |
> | dΩ             | Differential sectional area                                                       | Represents integration over the physical transverse domain. In Cartesian transverse coordinates, dΩ = dy dz.                                |
> | Jτ,φs,ξᵐⁿ,ᵏ(x) | Resulting sectional coefficient                                                   | Scalar coefficient obtained by integrating the constitutive contribution multiplied by the test-side and trial-side CUF factors over Ωᵏ(x). |
>
> The two CUF functions belong to the same transverse approximation basis. Their indices are different because the variational formulation couples a virtual/test function with a displacement/trial function.
>
> $$ F_\tau(y,z) \qquad F_s(y,z). $$
>
> The derivative selectors are
>
> $$ \phi,\xi \in \lbrace \varnothing,y,z \rbrace. $$
>
> The symbol
>
> $$ \varnothing $$
>
> means that no transverse derivative is applied.
>
> Therefore,
>
> $$ F_{\tau,\varnothing}(y,z)=F_\tau(y,z). $$
>
> $$ F_{s,\varnothing}(y,z)=F_s(y,z). $$
>
> If the selector is y,
>
> $$ F_{\tau,y}(y,z)=\frac{\partial F_\tau(y,z)}{\partial y}. $$
>
> and
>
> $$ F_{s,y}(y,z)=\frac{\partial F_s(y,z)}{\partial y}. $$
>
> If the selector is z,
>
> $$ F_{\tau,z}(y,z)=\frac{\partial F_\tau(y,z)}{\partial z}. $$
>
> and
>
> $$ F_{s,z}(y,z)=\frac{\partial F_s(y,z)}{\partial z}. $$
>
> The subscript of J is therefore read as two ordered pairs:
>
> $$ (\tau,\phi) \qquad (s,\xi). $$
>
> The first pair refers to the virtual/test side and determines
>
> $$ (\tau,\phi) \longrightarrow F_{\tau,\phi}(y,z). $$
>
> The second pair refers to the displacement/trial side and determines
>
> $$ (s,\xi) \longrightarrow F_{s,\xi}(y,z). $$
>
> The superscript identifies the constitutive-matrix entry and the transverse sub-domain:
>
> $$ (m,n,k) \longrightarrow C_{mn}^{k}(x,y,z) \quad \text{over} \quad \Omega^k(x). $$
>
> Thus, the complete coefficient can be read operationally as follows:
>
> 1. use x to identify the current sectional state;
> 2. use k to select the physical sub-domain Ωᵏ(x);
> 3. use m and n to select the required entry Cₘₙᵏ(x,y,z) of the constitutive matrix associated with that domain;
> 4. use τ and φ to construct the virtual/test-side CUF transverse factor;
> 5. use s and ξ to construct the displacement/trial-side CUF transverse factor;
> 6. multiply the constitutive contribution by the two CUF transverse factors;
> 7. integrate the resulting quantity over Ωᵏ(x) to obtain Jτ,φs,ξᵐⁿ,ᵏ(x).


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

 ## Worked example: assembly of the global sectional coefficient

 The global sectional coefficient is defined as

 $$ J_{\tau,\phi s,\xi}^{mn}(x) = \sum_{k=1}^{N_\Omega} J_{\tau,\phi s,\xi}^{mn,k}(x). $$

 This example continues the sub-domain evaluation of §5.1, where the contribution of sub-domain `k = 1` was fully resolved as

 $$ J_{2,y\,2,y}^{66,1}(x)=130000000-3900000x+26000x^2\ \mathrm{N}, \qquad x \text{ in metres.} $$

 To assemble the global coefficient, a second transverse sub-domain is introduced. Therefore,

 $$ N_\Omega=2. $$

 The same CUF term is retained:

 $$ m=6,\qquad n=6,\qquad \tau=2,\qquad s=2,\qquad \phi=y,\qquad \xi=y. $$

 The same transverse CUF factors therefore apply in both sub-domains, because they depend on the selected CUF basis and not on the sub-domain index.

 On the virtual/test side,

 $$ F_{2,y}(y,z)=1. $$

 On the displacement/trial side,

 $$ F_{2,y}(y,z)=1. $$

 For sub-domain `k = 2`, the corresponding sectional contribution is therefore

 $$ J_{2,y\,2,y}^{66,2}(x) = \int_{\Omega^2(x)} C_{66}^{2}(x,y,z)\,\mathrm{d}\Omega. $$

 ### Sub-domain 2 data

 | Quantity | Value used in the example | Role |
 |---|---:|---|
 | k | 2 | Selects the second transverse sub-domain |
 | G₂(x) | 15 × 10⁹ (1 + 0.05 x/L) Pa | Shear stiffness field associated with sub-domain 2 |
 | C₆₆²(x,y,z) | C₆₆²(x) = G₂(x) | Entry at row 6 and column 6 of the constitutive matrix of sub-domain 2 |
 | y extent | -0.03 ≤ y ≤ 0.03 m | Constant transverse extent along y |
 | z extent | 0.025 ≤ z ≤ 0.045 m | Constant transverse extent along z; sub-domain 2 is located above sub-domain 1 |
 | L | 10 m | Same beam length used in §5.1 |

 The constitutive field assigned to sub-domain 2 is

 $$ G_2(x)=15\times10^9(1+0.05\frac{x}{L})\ \mathrm{Pa}. $$

 From the constitutive matrix associated with sub-domain `k = 2`,

 $$ C_{66}^{2}(x,y,z)=C_{66}^{2}(x)=G_2(x). $$

 Therefore,

 $$ C_{66}^{2}(x)=15\times10^9(1+0.05\frac{x}{L})\ \mathrm{Pa}. $$

 Sub-domain 2 represents a second material region attached above sub-domain 1. Its cross-sectional extent is constant, while its shear stiffness increases along `x`. This provides a longitudinal trend opposite to sub-domain 1, whose corresponding constitutive contribution decreases along `x`.

 ### Evaluation of the sub-domain 2 coefficient

 The coefficient is

 $$ J_{2,y\,2,y}^{66,2}(x) = \int_{\Omega^2(x)} C_{66}^{2}(x)\,\mathrm{d}\Omega. $$

 Using the physical limits of sub-domain 2,

 $$ J_{2,y\,2,y}^{66,2}(x) = \int_{0.025}^{0.045}\int_{-0.03}^{0.03} C_{66}^{2}(x)\,\mathrm{d}y\,\mathrm{d}z. $$

 Since the constitutive component is uniform over the transverse coordinates `y` and `z`, it can be taken outside the sectional integrals:

 $$ J_{2,y\,2,y}^{66,2}(x) = C_{66}^{2}(x)\int_{0.025}^{0.045}\int_{-0.03}^{0.03}\mathrm{d}y\,\mathrm{d}z. $$

 The integration with respect to `y` gives

 $$ \int_{-0.03}^{0.03}\mathrm{d}y=0.06\ \mathrm{m}. $$

 The integration with respect to `z` gives

 $$ \int_{0.025}^{0.045}\mathrm{d}z=0.02\ \mathrm{m}. $$

 Therefore, the area of sub-domain 2 is

 $$ 0.06\times0.02=0.0012\ \mathrm{m}^2. $$

 Hence,

 $$ J_{2,y\,2,y}^{66,2}(x) = C_{66}^{2}(x)(0.0012\ \mathrm{m}^2). $$

 Substituting the constitutive law,

 $$ J_{2,y\,2,y}^{66,2}(x) = 15\times10^9(1+0.05\frac{x}{L})(0.0012). $$

 Therefore,

 $$ J_{2,y\,2,y}^{66,2}(x) = 18000000(1+0.05\frac{x}{L})\ \mathrm{N}. $$

 Using

 $$ L=10\ \mathrm{m}, $$

 the resolved contribution of sub-domain 2 is

 $$ \boxed{J_{2,y\,2,y}^{66,2}(x)=18000000+90000x\ \mathrm{N}.} $$

 ### Global assembly

 Because

 $$ N_\Omega=2, $$

 the global coefficient is obtained by summing the two sub-domain contributions:

 $$ J_{2,y\,2,y}^{66}(x) = J_{2,y\,2,y}^{66,1}(x) + J_{2,y\,2,y}^{66,2}(x). $$

 Substituting the two resolved expressions gives

 $$ J_{2,y\,2,y}^{66}(x) = (130000000-3900000x+26000x^2) + (18000000+90000x). $$

 Collecting equal powers of `x`,

 $$ \boxed{J_{2,y\,2,y}^{66}(x)=148000000-3810000x+26000x^2\ \mathrm{N}.} $$

 ### Numerical checks

 | x (m) | J⁶⁶,¹(x) (N) | J⁶⁶,²(x) (N) | J⁶⁶(x) (N) |
 |---:|---:|---:|---:|
 | 0 | 130 000 000 | 18 000 000 | **148 000 000** |
 | 5 | 111 150 000 | 18 450 000 | **129 600 000** |
 | 10 | 93 600 000 | 18 900 000 | **112 500 000** |

 At

 $$ x=10\ \mathrm{m}, $$

 the contribution of sub-domain 1 is

 $$ J_{2,y\,2,y}^{66,1}(10)=130000000-3900000(10)+26000(10)^2=93600000\ \mathrm{N}. $$

 The contribution of sub-domain 2 is

 $$ J_{2,y\,2,y}^{66,2}(10)=18000000+90000(10)=18900000\ \mathrm{N}. $$

 Their sum is

 $$ 93600000+18900000=112500000\ \mathrm{N}. $$

 The global expression gives the same value:

 $$ J_{2,y\,2,y}^{66}(10)=148000000-3810000(10)+26000(10)^2=112500000\ \mathrm{N}. $$

 ### Interpretation

 The assembled coefficient is a longitudinal field obtained by summing the contributions of all transverse sub-domains:

 $$ J_{2,y\,2,y}^{66}(x)=\sum_{k=1}^{2}J_{2,y\,2,y}^{66,k}(x). $$

 In this example, the constitutive contribution of sub-domain 1 decreases along `x`, while the constitutive contribution of sub-domain 2 increases along `x`.

 Nevertheless, the global coefficient decreases over the interval

 $$ 0\le x\le L. $$

 For the resolved global polynomial,

 $$ \frac{\mathrm{d}J_{2,y\,2,y}^{66}}{\mathrm{d}x}=-3810000+52000x. $$

 Over

 $$ 0\le x\le10\ \mathrm{m}, $$

 this derivative remains negative, so the global coefficient decreases monotonically over the complete beam length.

 This example admits a closed-form expression because the sectional geometry and constitutive laws were deliberately chosen as simple analytical functions. In the general CSF-CUF formulation, a closed-form longitudinal expression for the sectional coefficients is not required: the global coefficient can instead be assembled numerically from the sub-domain contributions evaluated at the longitudinal coordinates requested by the solver.

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

### Worked example: insertion of a resolved sectional coefficient into the internal virtual work

This worked example continues the construction developed in the preceding sections.

The objective is deliberately limited: to show, without introducing any additional sectional assumption, how a previously evaluated global sectional coefficient enters one specific contribution of the CUF internal virtual work.

No complete solution of the longitudinal problem is attempted here, and no additional constitutive, geometrical, or kinematic specialization is introduced by this example.

### Starting point

The internal virtual work is

$$ \delta L_i = \int_0^l \sum_{k=1}^{N_\Omega} \int_{\Omega^k(x)} \delta\boldsymbol{\varepsilon}^{T} \mathbf{C}^{k}(x,y,z) \boldsymbol{\varepsilon} \,\mathrm{d}\Omega\,\mathrm{d}x. $$

The CUF displacement expansion associated with source index $s$ is

$$ u_i(x,y,z) = F_s(y,z)\,u_{is}(x), \qquad i\in\{x,y,z\}. $$

For the axial displacement amplitude, define

$$ a(x) = u_{xs}(x), $$

and, on the virtual/test side,

$$ \delta a(x) = \delta u_{x\tau}(x). $$

Let

$$ A(y,z) = F_s(y,z), \qquad B(y,z) = F_\tau(y,z). $$

The engineering shear strain in the $xy$ plane contains the contribution

$$ \gamma_{xy} = A_{,y}\,a + A\,b_{,x}, $$

while the corresponding virtual strain contains

$$ \delta\gamma_{xy} = B_{,y}\,\delta a + B\,\delta b_{,x}. $$

The present worked example isolates only the product generated by the first term on each side,

$$ B_{,y}\,\delta a $$

and

$$ A_{,y}\,a. $$

Therefore, from the constitutive contribution involving $C_{66}$, the selected term of the internal virtual work is

$$ \delta L_i^{(66,aa)} = \int_0^l \sum_{k=1}^{N_\Omega} \int_{\Omega^k(x)} C_{66}^{k}(x,y,z)\, B_{,y}(y,z)\, A_{,y}(y,z)\, \delta a(x)\, a(x) \,\mathrm{d}\Omega\,\mathrm{d}x. $$

This is one contribution to $\delta L_i$ only. No statement is made here that the remaining terms of the complete internal virtual work vanish.

### Identification of the sectional coefficient

Using

$$ A(y,z) = F_s(y,z), \qquad B(y,z) = F_\tau(y,z), $$

the transverse factor in the selected term is

$$ C_{66}^{k}(x,y,z)\, F_{\tau,y}(y,z)\, F_{s,y}(y,z). $$

By the generalized sectional definition,

$$ J_{\tau,y\,s,y}^{66,k}(x) = \int_{\Omega^k(x)} C_{66}^{k}(x,y,z)\, F_{\tau,y}(y,z)\, F_{s,y}(y,z)\, \mathrm{d}\Omega. $$

After summation over the transverse sub-domains,

$$ J_{\tau,y\,s,y}^{66}(x) = \sum_{k=1}^{N_\Omega} J_{\tau,y\,s,y}^{66,k}(x). $$

Hence the selected contribution reduces to the purely longitudinal form

$$ \boxed{ \delta L_i^{(66,aa)} = \int_0^l J_{\tau,y\,s,y}^{66}(x)\, \delta a(x)\, a(x)\, \mathrm{d}x }. $$

At this stage, all sectional information has been condensed into the global coefficient

$$ J_{\tau,y\,s,y}^{66}(x). $$

The CUF longitudinal amplitudes remain

$$ a(x) $$

and

$$ \delta a(x). $$

### Specialization to the coefficient evaluated in the preceding worked examples

The preceding sectional examples selected

$$ \tau=2, \qquad s=2, $$

and evaluated

$$ J_{2,y\,2,y}^{66}(x). $$

The two sub-domain contributions were assembled into

$$ \boxed{ J_{2,y\,2,y}^{66}(x) = 148000000 - 3810000x + 26000x^2 \ \mathrm{N} }. $$

Here $x$ is expressed in metres over the interval

$$ 0\le x\le L, \qquad L=10\ \mathrm{m}. $$

For consistency with the notation of the internal virtual work, in this worked example

$$ l=L=10\ \mathrm{m}. $$

The selected contribution therefore becomes

$$ \boxed{ \delta L_i^{(66,aa)} = \int_0^{10} \left( 148000000 - 3810000x + 26000x^2 \right) \delta a(x)\, a(x)\, \mathrm{d}x }. $$

No further evaluation is performed.

The reason is structural rather than computational: $a(x)$ is a longitudinal CUF unknown and $\delta a(x)$ is its admissible virtual variation. Their determination belongs to the subsequent longitudinal problem and is not part of the sectional evaluation.

### Operational interpretation

The complete chain represented by this example is

$$
\mathcal{S}(x)
\longrightarrow
\{\Omega^k(x),\mathbf{C}^k(x,y,z)\}
\longrightarrow
J_{2,y\,2,y}^{66,k}(x)
\longrightarrow
J_{2,y\,2,y}^{66}(x)
\longrightarrow
\delta L_i^{(66,aa)}
$$

The roles remain separated:

- the CUF kinematics determines which transverse factors occur;
- the variational statement determines which constitutive entry and which pairing of test and trial quantities are required;
- the sectional representation supplies the physical domains and constitutive fields needed to evaluate the requested sectional coefficient;
- the resulting global coefficient enters the longitudinal internal virtual work;
- the longitudinal displacement amplitude remains an unknown of the CUF problem.

Thus the sectional coefficient is inserted into the CUF variational structure without requiring the CUF formulation to reproduce the internal construction of the sectional state.

### Scope of the example

This example establishes only the passage

$$ J_{\tau,y\,s,y}^{66}(x) \longrightarrow \delta L_i^{(66,aa)}. $$

It does not yet perform longitudinal integration by parts, derive the corresponding strong-form operator, impose boundary conditions, or solve for the longitudinal amplitudes.

Those operations belong to subsequent steps of the CUF formulation.


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

### Worked example: sectional projection of one surface traction into the CUF external virtual work

This worked example takes one deliberately small step beyond the general statement of Section 8.

The objective is to show how one surface traction acting on a longitudinally evolving sectional boundary is converted into the corresponding CUF generalized load contribution.

Only the surface-load contribution $\delta L_p$ is considered here. The line-load contribution $\delta L_l$ is not specialized in this example.

No new loading theory is introduced. The example only makes explicit the surface-load projection already implied by the CUF virtual-work statement.

### General surface-load contribution

Let $\mathbf{p}^{k\phi\pm}(x,y,z)$ denote a traction vector acting on the longitudinal surface generated by the sectional boundary $\Gamma_\phi^{k\pm}(x)$.

The corresponding contribution to the external virtual work is

$$ \delta L_p^{k\phi\pm} = \int_0^l \int_{\Gamma_\phi^{k\pm}(x)} \delta\mathbf{u}^{T}(x,y,z)\,\mathbf{p}^{k\phi\pm}(x,y,z)\,\mathrm{d}\Gamma\,\mathrm{d}x. $$

Using the CUF virtual displacement expansion

$$ \delta\mathbf{u}(x,y,z) = F_\tau(y,z)\,\delta\mathbf{u}_\tau(x), $$

the longitudinal virtual amplitude is independent of the transverse integration variables and can be taken outside the sectional boundary integral:

$$ \delta L_p^{k\phi\pm} = \int_0^l \delta\mathbf{u}_\tau^{T}(x)\left[\int_{\Gamma_\phi^{k\pm}(x)} F_\tau(y,z)\,\mathbf{p}^{k\phi\pm}(x,y,z)\,\mathrm{d}\Gamma\right]\mathrm{d}x. $$

Define the generalized CUF surface-load vector

$$ \mathbf{p}_\tau^{k\phi\pm}(x) = \int_{\Gamma_\phi^{k\pm}(x)} F_\tau(y,z)\,\mathbf{p}^{k\phi\pm}(x,y,z)\,\mathrm{d}\Gamma. $$

Then

$$ \boxed{\delta L_p^{k\phi\pm} = \int_0^l \delta\mathbf{u}_\tau^{T}(x)\,\mathbf{p}_\tau^{k\phi\pm}(x)\,\mathrm{d}x}. $$

This is the external-load counterpart of the same separation already used for the sectional stiffness quantities: the CUF formulation determines the required transverse projection, while the current sectional boundary is supplied by the sectional state at the requested longitudinal coordinate.

### Relation with the boundary projection coefficient

If the traction is uniform over the selected sectional boundary at fixed $x$, it can be written as

$$ \mathbf{p}^{k\phi\pm}(x,y,z) = \mathbf{p}^{k\phi\pm}(x). $$

The traction vector can then be taken outside the sectional boundary integral:

$$ \mathbf{p}_\tau^{k\phi\pm}(x) = \left[\int_{\Gamma_\phi^{k\pm}(x)} F_\tau(y,z)\,\mathrm{d}\Gamma\right]\mathbf{p}^{k\phi\pm}(x). $$

Using the boundary projection coefficient already introduced in Section 8,

$$ E_\tau^{k\phi\pm}(x) = \int_{\Gamma_\phi^{k\pm}(x)} F_\tau(y,z)\,\mathrm{d}\Gamma, $$

the generalized load becomes

$$ \boxed{\mathbf{p}_\tau^{k\phi\pm}(x) = E_\tau^{k\phi\pm}(x)\,\mathbf{p}^{k\phi\pm}(x)}. $$

The coefficient $E_\tau^{k\phi\pm}(x)$ contains only the transverse CUF projection and the current sectional-boundary geometry. The physical traction remains a separate prescribed load quantity.

### Numerical specialization

Use the same beam length and the same first transverse sub-domain introduced in the preceding sectional worked examples:

$$ L=l=10\ \mathrm{m}. $$

For sub-domain $k=1$, the sectional limits are

$$ -0.05+0.01\frac{x}{L} \le y \le 0.05-0.01\frac{x}{L}, $$

and

$$ -0.025 \le z \le 0.025. $$

Select the positive boundary associated with the transverse direction $z$:

$$ k=1,\qquad \phi=z,\qquad +. $$

Therefore,

$$ \Gamma_z^{1+}(x):\qquad z=0.025,\qquad -0.05+0.01\frac{x}{L}\le y\le0.05-0.01\frac{x}{L}. $$

Select the first-order CUF transverse basis already used in the preceding examples,

$$ F_1(y,z)=1,\qquad F_2(y,z)=y,\qquad F_3(y,z)=z, $$

and choose

$$ \tau=1. $$

Hence,

$$ F_\tau(y,z)=F_1(y,z)=1. $$

The required boundary projection coefficient is therefore

$$ E_1^{1z+}(x) = \int_{\Gamma_z^{1+}(x)} 1\,\mathrm{d}\Gamma. $$

Along this boundary, $z$ is constant and the boundary coordinate is $y$, so

$$ \mathrm{d}\Gamma=\mathrm{d}y. $$

Thus,

$$ E_1^{1z+}(x) = \int_{-0.05+0.01x/L}^{0.05-0.01x/L}\mathrm{d}y. $$

Evaluating the limits gives

$$ \boxed{E_1^{1z+}(x)=0.10-0.02\frac{x}{L}\ \mathrm{m}}. $$

With $L=10\ \mathrm{m}$,

$$ \boxed{E_1^{1z+}(x)=0.10-0.002x\ \mathrm{m}}. $$

### Prescribed traction

Assign a traction acting only in the global $y$ direction and uniform over $\Gamma_z^{1+}(x)$ at each fixed $x$:

$$ \mathbf{p}^{1z+}(x) = \begin{bmatrix}0\\p_y(x)\\0\end{bmatrix}. $$

Let

$$ p_y(x)=2.0\times10^6\left(1-0.20\frac{x}{L}\right)\ \mathrm{Pa}. $$

The generalized CUF surface-load vector for $\tau=1$ is

$$ \mathbf{p}_1^{1z+}(x)=E_1^{1z+}(x)\,\mathbf{p}^{1z+}(x). $$

Therefore,

$$ \mathbf{p}_1^{1z+}(x)=\left(0.10-0.02\frac{x}{L}\right)\begin{bmatrix}0\\2.0\times10^6\left(1-0.20\frac{x}{L}\right)\\0\end{bmatrix}\ \mathrm{N/m}. $$

Only the $y$ component is non-zero. Define

$$ q_{y1}^{1z+}(x)=E_1^{1z+}(x)\,p_y(x). $$

Then

$$ q_{y1}^{1z+}(x)=2.0\times10^6\left(0.10-0.02\frac{x}{L}\right)\left(1-0.20\frac{x}{L}\right)\ \mathrm{N/m}. $$

Expanding,

$$ q_{y1}^{1z+}(x)=200000-80000\frac{x}{L}+8000\left(\frac{x}{L}\right)^2\ \mathrm{N/m}. $$

Using $L=10\ \mathrm{m}$,

$$ \boxed{q_{y1}^{1z+}(x)=200000-8000x+80x^2\ \mathrm{N/m}}. $$

Accordingly,

$$ \boxed{\mathbf{p}_1^{1z+}(x)=\begin{bmatrix}0\\200000-8000x+80x^2\\0\end{bmatrix}\ \mathrm{N/m}}. $$

### Numerical checks

At the beam origin,

$$ E_1^{1z+}(0)=0.10\ \mathrm{m},\qquad p_y(0)=2.0\times10^6\ \mathrm{Pa}, $$

and therefore

$$ q_{y1}^{1z+}(0)=200000\ \mathrm{N/m}. $$

At mid-span,

$$ E_1^{1z+}(5)=0.09\ \mathrm{m},\qquad p_y(5)=1.8\times10^6\ \mathrm{Pa}, $$

and therefore

$$ q_{y1}^{1z+}(5)=162000\ \mathrm{N/m}. $$

At the beam end,

$$ E_1^{1z+}(10)=0.08\ \mathrm{m},\qquad p_y(10)=1.6\times10^6\ \mathrm{Pa}, $$

and therefore

$$ q_{y1}^{1z+}(10)=128000\ \mathrm{N/m}. $$

### Insertion into the external virtual work

For $\tau=1$, the virtual CUF amplitude vector is

$$ \delta\mathbf{u}_1(x)=\begin{bmatrix}\delta u_{x1}(x)\\\delta u_{y1}(x)\\\delta u_{z1}(x)\end{bmatrix}. $$

Since the generalized load has only a $y$ component,

$$ \delta\mathbf{u}_1^{T}(x)\,\mathbf{p}_1^{1z+}(x)=\delta u_{y1}(x)\,q_{y1}^{1z+}(x). $$

Hence the selected surface-load contribution becomes

$$ \boxed{\delta L_p^{1z+}=\int_0^{10}\delta u_{y1}(x)\left(200000-8000x+80x^2\right)\mathrm{d}x}. $$

No further evaluation is performed because $\delta u_{y1}(x)$ is an admissible virtual displacement amplitude, not prescribed sectional data.

The numerical part of the example is nevertheless complete: the evolving boundary, the CUF boundary projection coefficient, the prescribed traction, and the resulting generalized longitudinal load field have all been evaluated explicitly.

### Operational interpretation

The chain represented by this example is

$$ \mathcal{S}(x)\longrightarrow\Gamma_z^{1+}(x)\longrightarrow E_1^{1z+}(x)\longrightarrow\mathbf{p}_1^{1z+}(x)\longrightarrow\delta L_p^{1z+} $$

The roles remain separated:

- $\mathcal{S}(x)$ determines the current physical sectional boundary;
- CUF supplies the transverse approximation function $F_1$;
- the prescribed traction is external loading data;
- the boundary projection produces the generalized CUF load field;
- the longitudinal virtual displacement remains part of the CUF variational problem.

### Scope of the example

This example establishes only the surface-load passage

$$ \Gamma_\phi^{k\pm}(x)\longrightarrow E_\tau^{k\phi\pm}(x)\longrightarrow\mathbf{p}_\tau^{k\phi\pm}(x)\longrightarrow\delta L_p^{k\phi\pm}. $$

It does not specialize the line-load contribution $\delta L_l$, assemble multiple loaded boundaries, impose boundary conditions, or solve the governing equations.

Those operations belong to subsequent steps of the formulation.

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

###  Worked example: complete numerical evaluation of one governing-equation component

This worked example takes one controlled step beyond the general governing equation introduced in Section 9.

The objective is to obtain a completely determined numerical governing-equation contribution without introducing a longitudinal solver and without leaving an unknown differential equation to be solved.

To achieve this, the longitudinal CUF amplitude is prescribed as verification data. Once the sectional coefficient and the longitudinal field are fixed, the corresponding generalized load is determined uniquely by the governing equation.

No attempt is made here to reconstruct a physical traction distribution from that generalized load.

### Selected governing-equation component

The assembled CUF governing equations are

$$ \mathbf{K}_{\tau s}[\mathcal{S}(x),\partial_x]\,\mathbf{u}_s(x)=\mathbf{f}_\tau(x). $$

Select the transverse $y$ component and choose

$$ \tau=1,\qquad s=1. $$

For the $yy$ block, the variable-coefficient CUF operator is

$$ K_{yy}^{\tau s}(x)=J_{\tau,y\,s,y}^{22}(x)+J_{\tau,z\,s,z}^{44}(x)-\partial_x\left[J_{\tau s}^{66}(x)\,\partial_x\right]. $$

The first-order CUF transverse basis is retained:

$$ F_1(y,z)=1,\qquad F_2(y,z)=y,\qquad F_3(y,z)=z. $$

For

$$ \tau=s=1, $$

the transverse derivatives are

$$ F_{1,y}(y,z)=0,\qquad F_{1,z}(y,z)=0. $$

Therefore,

$$ J_{1,y\,1,y}^{22}(x)=0, $$

and

$$ J_{1,z\,1,z}^{44}(x)=0. $$

The selected governing-equation component consequently reduces to

$$ \boxed{-\partial_x\left[J_{11}^{66}(x)\,\partial_x b(x)\right]=f_{y1}(x)}. $$

Here

$$ b(x)=u_{y1}(x) $$

is the longitudinal CUF amplitude associated with the $y$ displacement and transverse basis function $F_1$.

### Evaluation of the required sectional coefficient

By definition,

$$ J_{11}^{66,k}(x)=\int_{\Omega^k(x)}C_{66}^{k}(x,y,z)\,F_1(y,z)\,F_1(y,z)\,\mathrm{d}\Omega. $$

Since

$$ F_1(y,z)=1, $$

this becomes

$$ J_{11}^{66,k}(x)=\int_{\Omega^k(x)}C_{66}^{k}(x,y,z)\,\mathrm{d}\Omega. $$

The preceding sectional worked examples evaluated

$$ J_{2,y\,2,y}^{66,k}(x)=\int_{\Omega^k(x)}C_{66}^{k}(x,y,z)\,F_{2,y}(y,z)\,F_{2,y}(y,z)\,\mathrm{d}\Omega. $$

Because

$$ F_{2,y}(y,z)=1, $$

the two sectional integrals are identical:

$$ J_{11}^{66,k}(x)=J_{2,y\,2,y}^{66,k}(x). $$

After assembly over the transverse sub-domains,

$$ J_{11}^{66}(x)=J_{2,y\,2,y}^{66}(x). $$

The previously resolved global coefficient can therefore be used directly:

$$ \boxed{J_{11}^{66}(x)=148000000-3810000x+26000x^2\ \mathrm{N}}. $$

The longitudinal interval is

$$ 0\le x\le L,\qquad L=10\ \mathrm{m}. $$

### Prescribed longitudinal verification field

To obtain a fully determined worked example, prescribe the longitudinal CUF amplitude

$$ b(x)=b_L\frac{x}{L}, $$

with

$$ b_L=0.01\ \mathrm{m}. $$

Since

$$ L=10\ \mathrm{m}, $$

the prescribed field is

$$ \boxed{b(x)=0.001x}. $$

Its longitudinal derivative is constant:

$$ \boxed{\frac{\mathrm{d}b}{\mathrm{d}x}=0.001}. $$

The selected governing-equation operator becomes

$$ -\partial_x\left[J_{11}^{66}(x)\,\partial_x b(x)\right]=-\partial_x\left[0.001\,J_{11}^{66}(x)\right]. $$

The derivative of the sectional coefficient is

$$ \frac{\mathrm{d}J_{11}^{66}}{\mathrm{d}x}=-3810000+52000x\ \mathrm{N/m}. $$

Therefore,

$$ -\partial_x\left[J_{11}^{66}(x)\,\partial_x b(x)\right]=-0.001\left(-3810000+52000x\right). $$

Hence the generalized load required by the governing equation is uniquely determined as

$$ \boxed{f_{y1}(x)=3810-52x\ \mathrm{N/m}}. $$

No unknown quantity remains in this selected governing-equation component.

### Numerical values

At the beam origin,

$$ f_{y1}(0)=3810\ \mathrm{N/m}. $$

At mid-span,

$$ f_{y1}(5)=3550\ \mathrm{N/m}. $$

At the beam end,

$$ f_{y1}(10)=3290\ \mathrm{N/m}. $$

The prescribed displacement field is correspondingly

$$ b(0)=0, $$

$$ b(5)=0.005\ \mathrm{m}, $$

and

$$ b(10)=0.01\ \mathrm{m}. $$

### Direct governing-equation checks

At

$$ x=0, $$

the governing operator gives

$$ -\partial_x\left[J_{11}^{66}(x)\,\partial_x b(x)\right]_{x=0}=3810\ \mathrm{N/m}, $$

which is exactly

$$ f_{y1}(0)=3810\ \mathrm{N/m}. $$

At

$$ x=5\ \mathrm{m}, $$

the governing operator gives

$$ -\partial_x\left[J_{11}^{66}(x)\,\partial_x b(x)\right]_{x=5}=3550\ \mathrm{N/m}, $$

which is exactly

$$ f_{y1}(5)=3550\ \mathrm{N/m}. $$

At

$$ x=10\ \mathrm{m}, $$

the governing operator gives

$$ -\partial_x\left[J_{11}^{66}(x)\,\partial_x b(x)\right]_{x=10}=3290\ \mathrm{N/m}, $$

which is exactly

$$ f_{y1}(10)=3290\ \mathrm{N/m}. $$

Thus the selected governing-equation component is satisfied exactly by construction.

### Operational interpretation

The chain represented by this example is

$$ \mathcal{S}(x)\longrightarrow J_{11}^{66}(x)\longrightarrow b(x)\longrightarrow f_{y1}(x) $$

The roles remain separated:

- the CUF formulation determines the governing differential operator;
- the sectional representation supplies the coefficient $J_{11}^{66}(x)$;
- the longitudinal field $b(x)$ is prescribed only for this verification example;
- once $J_{11}^{66}(x)$ and $b(x)$ are fixed, the generalized load $f_{y1}(x)$ is determined uniquely by the governing equation.

No additional sectional, constitutive, or loading specialization is required.

### Scope of the example

This is a manufactured equilibrium check for one scalar component of the CUF governing equations.

It does not solve the general CUF boundary-value problem.

It does not introduce a longitudinal numerical solver, impose a complete set of structural boundary conditions, reconstruct a physical traction distribution, or determine an unknown displacement field from prescribed loads.

The example ends with finite numerical quantities because the longitudinal field is prescribed as verification data and the corresponding generalized load is evaluated uniquely from the already established CUF operator.


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
