#  DRAFT
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

## 10. Longitudinally varying coefficients inside the nuclear operator

When a coefficient multiplying a longitudinal derivative depends on $x$, it must remain inside the differential operator.

For example, a term that reduces to

$$ - J_{\tau s}^{11}\,\partial_x^2 $$

when $J_{\tau s}^{11}$ is constant becomes, in the variable-section case,

$$ { - \partial_x [ J_{\tau s}^{11}(x)\, \partial_x ]. } $$

Applied to a longitudinal unknown $u_s(x)$,

$$ { - \partial_x [ J_{\tau s}^{11}(x)\, \partial_x u_s(x) ]. } $$

There is no need to expand this expression analytically.

If expanded, it would generate both the second derivative of the unknown and the longitudinal derivative of the sectional coefficient. Keeping the divergence form preserves the variable-coefficient structure directly.

A representative diagonal nuclear term can therefore be written as

$$ { K_{xx}^{\tau s}(x) = J_{\tau,y\,s,y}^{66}(x) + J_{\tau,z\,s,z}^{55}(x) - \partial_x [ J_{\tau s}^{11}(x)\, \partial_x ]. } $$

The remaining nuclear terms are treated according to the same variational principle: the CUF structure is retained while the sectional coefficients are supplied as longitudinal fields generated by $\mathcal{S}(x)$.

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
