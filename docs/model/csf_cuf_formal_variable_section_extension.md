#  DRAFT
>The following material presents the current conceptual definition of the CSF–CUF sectional interface. The coupling is still under development and is intended to be implemented through a dedicated software bridge able to provide the sectional data required by the CUF formulation from the CSF representation $\mathcal{S}(x)$.

# Formal CSF–CUF extension for a longitudinally varying section field

## 1. Scope

This note reorganizes the formal extension of the CUF beam formulation used in Giunta, Belouettar, and Carrera (2010) to the case in which the cross-section is supplied by a Continuous Section Field (CSF)

$$ \mathcal{S}(x). $$

The objective is **not** to derive a closed-form analytical solution along the beam axis.

The objective is to define, at a formal level, how the sectional quantities entering the CUF formulation become functions of the longitudinal coordinate through the CSF representation.

The sequence is

$$ { \mathcal{S}(x) \longrightarrow \{ \Omega^k(x),\, \mathbf{C}^k(x,y,z) \} \longrightarrow J_\bullet^k(x) \longrightarrow \delta L_i \longrightarrow \delta L_{\mathrm{ext}} \longrightarrow \mathbf{K}_{\tau s}[\mathcal{S}(x),\partial_x]. } $$

No analytical expression for the sectional integrals and no Navier-type solution are required at this stage.

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

At every longitudinal coordinate, $\mathcal{S}(x)$ provides the sectional geometry and the constitutive information required by the mechanical formulation.

Formally,

$$ { \mathcal{S}(x) \longrightarrow \{ \Omega^k(x),\, \mathbf{C}^k(x,y,z) \}_{k=1}^{N_\Omega}. } $$

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
- $\phi$ and $\xi$ denote transverse differentiation directions, with $\phi,\xi\in\{y,z\}$.

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

$$ { \mathcal{S}(x) \longrightarrow \Omega^k(x),\mathbf{C}^k(x,y,z) \longrightarrow \text{numerical sectional integration} \longrightarrow J_\bullet^k(x). } $$

No polynomial, exponential, or other analytical approximation of $J_\bullet^k(x)$ is required.

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


# Longitudinally varying coefficients inside the nuclear operator
# 10 Longitudinally varying coefficients inside the nuclear operator

> This section builds on the sectional interface defined in
> [`csf_cuf_sectional_constitutive_interface.md`](csf_cuf_sectional_constitutive_interface.md),
> where the CSF–CUF coupling and the role of the dedicated software bridge are introduced.


## 10.1 Principle

When a sectional coefficient multiplying an x-derivative depends on x, the coefficient must remain inside the longitudinal differential operator.

For a constant coefficient:

$$ -J\,\partial_x^2 u(x) $$

For a longitudinally varying coefficient:

$$ -\partial_x \left( J(x)\,\partial_x u(x) \right) $$

The expression should be retained in this form rather than expanded through the product rule. This avoids introducing an unnecessary classical differentiability assumption on $J(x)$.

This generalization is directly justified when a nuclear term contains a single sectional coefficient multiplying a pure second derivative with respect to $x$.

---

## 10.2 Diagonal terms - verified

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

## 10.3 Mixed first-order terms - not yet verified

The reference paper gives the following first-order mixed terms:

$$ K_{xy}^{\tau s} = \left( -J_{\tau s,y}^{12k} + J_{\tau,y\,s}^{66k} \right)\,\partial_x $$

$$ K_{yx}^{\tau s} = \left( J_{\tau,y\,s}^{12k} - J_{\tau s,y}^{66k} \right)\,\partial_x $$

$$ K_{xz}^{\tau s} = \left( -J_{\tau s,z}^{13k} + J_{\tau,z\,s}^{55k} \right)\,\partial_x $$

$$ K_{zx}^{\tau s} = \left( J_{\tau,z\,s}^{13k} - J_{\tau s,z}^{55k} \right)\,\partial_x $$

These terms differ from the diagonal terms in two important respects.

First, they contain a first derivative rather than a second derivative.

Second, each operator contains a combination of two distinct sectional coefficients.

For variable coefficients, the operators

$$ J(x)\,\partial_x u(x) $$

and

$$ \partial_x \left( J(x)\,u(x) \right) $$

are not equivalent.

Consequently, the substitution

$$ J \longrightarrow J(x) $$

inside the already reduced constant-coefficient form is not sufficient to establish the correct variable-section operator.

The four terms

$$ K_{xy},\quad K_{yx},\quad K_{xz},\quad K_{zx} $$

must therefore be re-derived from the virtual internal work before the longitudinal integration by parts used to obtain the reference nuclear form.

---

## 10.4 Why direct substitution is not sufficient for the first-order mixed terms

Consider the generic constant-coefficient expression

$$ \int_0^l v(x)\,J\,u'(x)\,dx $$

with $J$ constant.

Integration by parts gives

$$ \int_0^l v\,J\,u'\,dx = \left[ v\,J\,u \right]_0^l - \int_0^l v'\,J\,u\,dx $$

If the coefficient becomes $J(x)$, the corresponding weak expression is instead

$$ \int_0^l v(x)\,J(x)\,u'(x)\,dx $$

and the coefficient can no longer be treated as a constant during the longitudinal integration by parts.

The correct mixed operator must therefore be obtained from the variational expression with $J(x)$ retained inside the longitudinal integral.

No assumption about cancellation or survival of coefficient-derivative terms should be made before that derivation is carried out.

---

## 10.5 Required derivation protocol for the mixed first-order terms

The four first-order mixed terms must be re-derived from the virtual internal work before the final longitudinal integration by parts.

The procedure is:

1. Start from the virtual internal work before the along-$x$ integration by parts that produces the nuclear operator.

2. Retain the constitutive coefficients as functions of the longitudinal coordinate:

$$ \mathbf{C}^k = \mathbf{C}^k(x,y,z) $$

3. Substitute the CUF displacement expansion and the strain-displacement relations.

4. Perform the transverse integration over the current sub-domain:

$$ \Omega^k(x) $$

so that the corresponding sectional coefficients are obtained as functions of $x$:

$$ J_\bullet^k(x) $$

5. Keep these coefficients inside the longitudinal variational integral.

6. Perform the longitudinal integration by parts only at this stage, without assuming that the sectional coefficients are constant.

7. Record the resulting bilinear form and only then identify the corresponding nuclear operator.

A complete derivation should first be carried out for one representative pair, for example

$$ K_{xy}^{\tau s}(x),\qquad K_{yx}^{\tau s}(x) $$

and the verified result can then be used as the basis for the structurally analogous pair

$$ K_{xz}^{\tau s}(x),\qquad K_{zx}^{\tau s}(x). $$

---

## 10.6 Off-diagonal zero-order terms - direct generalization

The remaining two off-diagonal terms in Eq. (23) do not contain longitudinal derivatives:

$$ K_{yz}^{\tau s} = J_{\tau,y\,s,z}^{23k} + J_{\tau,z\,s,y}^{44k} $$

$$ K_{zy}^{\tau s} = J_{\tau,z\,s,y}^{23k} + J_{\tau,y\,s,z}^{44k} $$

Since no derivative with respect to $x$ acts on the displacement amplitudes in these terms, no additional longitudinal integration-by-parts issue is introduced by the dependence of the sectional coefficients on $x$.

Their variable-section form is therefore obtained directly as:

$$ K_{yz}^{\tau s}(x) = J_{\tau,y\,s,z}^{23k}(x) + J_{\tau,z\,s,y}^{44k}(x) $$

$$ K_{zy}^{\tau s}(x) = J_{\tau,z\,s,y}^{23k}(x) + J_{\tau,y\,s,z}^{44k}(x) $$

These terms require only the numerical evaluation of the corresponding sectional coefficients at the requested longitudinal coordinate.

---

## 10.7 Status summary

| Nuclear terms | Longitudinal structure | Status |
|---|---|---|
| $K_{xx}(x)$ | one coefficient × second derivative | Verified - divergence form |
| $K_{yy}(x)$ | one coefficient × second derivative | Verified - divergence form |
| $K_{zz}(x)$ | one coefficient × second derivative | Verified - divergence form |
| $K_{xy}(x)$, $K_{yx}(x)$ | two coefficients × first derivative | **Open** - requires re-derivation |
| $K_{xz}(x)$, $K_{zx}(x)$ | two coefficients × first derivative | **Open** - requires re-derivation |
| $K_{yz}(x)$, $K_{zy}(x)$ | zero-order in $x$ | Direct generalization |

Until the four first-order mixed terms are re-derived, the operator

$$ \mathbf{K}_{\tau s}\left[\mathcal{S}(x),\partial_x\right] $$

should be regarded as only partially established in its variable-section form.

The diagonal second-order terms and the off-diagonal zero-order terms are defined, while the four first-order mixed terms remain an explicit open derivation item.

---

## 11. No closed-form longitudinal solution is required

The reference paper proceeds further and adopts a Navier-type solution along $x$.

That step is not required for the present CSF–CUF formulation.

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

## 12. Formal CSF–CUF chain

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

## Reference

G. Giunta, S. Belouettar, E. Carrera,  
**“Analysis of FGM Beams by Means of Classical and Advanced Theories”**,  
*Mechanics of Advanced Materials and Structures*, 17 (2010), 622–635.

The present note uses, as its formal basis, the paper's:

- cross-section decomposition;
- constitutive representation;
- CUF displacement expansion;
- Principle of Virtual Displacements;
- sectional coefficient families of Eq. (24);
- fundamental nuclear structure;
- surface- and line-load treatment.

The closed-form analytical evaluation used in the paper is not retained as a requirement of the CSF extension.
