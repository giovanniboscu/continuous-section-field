# DRAFT

>The following material presents the current conceptual definition of the CSF–CUF sectional interface. The coupling is still under development and is intended to be implemented through a dedicated software bridge able to provide the sectional data required by the CUF formulation from the CSF representation $\mathcal{S}(x)$.

# CSF sectional constitutive representation for CUF coupling

## Scope

This note isolates, from the formulation presented by Giunta, Belouettar, and Carrera (2010), the sectional geometry and constitutive description required for the CSF–CUF coupling, keeping them distinct from the kinematic approximation introduced by the Carrera Unified Formulation.

The reference paper describes the cross-section as a union of transverse sub-domains and assigns a constitutive stiffness matrix over the sectional domain. The CUF displacement approximation is introduced independently through the transverse approximation functions and the longitudinal displacement amplitudes.

For the CSF–CUF interface considered here, the CSF contribution is therefore restricted to:

1. the transverse domains that compose the cross-section;
2. the constitutive matrix associated with each domain;
3. the longitudinal evolution of both quantities.

The CUF approximation functions, approximation order, displacement amplitudes, governing equations, loads, and boundary conditions are **not** part of this CSF representation.

---

## 1. Coordinates

The CUF notation is retained.

- $x$ is the longitudinal coordinate along the beam axis;
- $y$ and $z$ are the transverse coordinates on the cross-section.

Although CSF may use a different symbol internally for the longitudinal coordinate, $x$ is used throughout this formulation to remain consistent with CUF notation.

---

## 2. Cross-section decomposition

At each longitudinal coordinate $x$, let the cross-section be denoted by

```math
\Omega(x).
```
The cross-section is composed of $N_\Omega$ distinct transverse domains:

```math
\boxed{
\Omega(x)
=
\bigcup_{k=1}^{N_\Omega}
\Omega^k(x)
}
```
where:

- $N_\Omega$ is the number of transverse domains;
- $k$ is the domain index;
- $\Omega^k(x)$ is the transverse region occupied by domain $k$ at longitudinal coordinate $x$.

In the reference paper, the cross-section is constant along the beam axis. In the CSF generalization, each domain may evolve along the beam:

```math
\boxed{
\Omega^k=\Omega^k(x)
}
```
so that geometry is represented as a longitudinal field rather than as a single fixed cross-section.

---

## 3. Material fields attached to each domain

Each domain $\Omega^k(x)$ carries its own material properties.

For the present CSF representation, define two independent stiffness fields for domain $k$:

```math
\boxed{
E_k=E_k(x)
}
```
and

```math
\boxed{
G_k=G_k(x)
}
```
where:

- $E_k(x)$ is the longitudinal/normal stiffness field associated with domain $k$;
- $G_k(x)$ is the shear stiffness field associated with domain $k$.

The two longitudinal laws $E_k(x)$ and $G_k(x)$ may be assigned independently by CSF. CSF therefore does not need a separately prescribed Poisson-ratio field in order to carry these two stiffness laws.

When the closed $6\times6$ matrix below is adopted, the pair $E_k(x),G_k(x)$ implies the local auxiliary quantity

```math
\nu_{k,\mathrm{eff}}(x)
=
\frac{E_k(x)}{2G_k(x)}-1.
```
Thus the two CSF stiffness laws remain independent inputs, while the chosen closure retains the corresponding isotropic algebraic structure locally. This closure is a constitutive specialization, not a fully general anisotropic law.

---

## 4. Domain constitutive matrix as a CSF building block

For every domain $k$, define the CSF constitutive matrix

```math
\boxed{
\mathbf C_k^{\mathrm{CSF}}(x)
}
```
as the local constitutive building block associated with $\Omega^k(x)$.

Under the small-strain linear-elastic assumption, let $\boldsymbol{\varepsilon}_k(x,y,z)$ denote the strain vector and $\boldsymbol{\sigma}_k(x,y,z)$ the corresponding stress vector within domain $k$.

The local constitutive relation is

$$ \boldsymbol{\sigma}_k(x,y,z) = \mathbf{C}_k^{\mathrm{CSF}}(x) \boldsymbol{\varepsilon}_k(x,y,z), \qquad (y,z)\in\Omega^k(x). $$

Thus, $\mathbf{C}_k^{\mathrm{CSF}}(x)$ is the constitutive matrix defining the linear-elastic relation within domain $k$.


A closed two-field specialization can be written in terms of $E_k(x)$ and $G_k(x)$.

First define

```math
\boxed{
\lambda_k(x)
=
G_k(x)
\frac{
E_k(x)-2G_k(x)
}{
3G_k(x)-E_k(x)
}
}
```
and then

```math
\boxed{
\mathbf C_k^{\mathrm{CSF}}(x)
=
\begin{bmatrix}
\lambda_k(x)+2G_k(x) & \lambda_k(x) & \lambda_k(x) & 0 & 0 & 0 \\
\lambda_k(x) & \lambda_k(x)+2G_k(x) & \lambda_k(x) & 0 & 0 & 0 \\
\lambda_k(x) & \lambda_k(x) & \lambda_k(x)+2G_k(x) & 0 & 0 & 0 \\
0 & 0 & 0 & G_k(x) & 0 & 0 \\
0 & 0 & 0 & 0 & G_k(x) & 0 \\
0 & 0 & 0 & 0 & 0 & G_k(x)
\end{bmatrix}
}
```
Equivalent component form:

```math
\boxed{
C_{11}^{k,\mathrm{CSF}}(x)
=
C_{22}^{k,\mathrm{CSF}}(x)
=
C_{33}^{k,\mathrm{CSF}}(x)
=
G_k(x)
\frac{
4G_k(x)-E_k(x)
}{
3G_k(x)-E_k(x)
}
}
```
```math
\boxed{
C_{12}^{k,\mathrm{CSF}}(x)
=
C_{13}^{k,\mathrm{CSF}}(x)
=
C_{23}^{k,\mathrm{CSF}}(x)
=
G_k(x)
\frac{
E_k(x)-2G_k(x)
}{
3G_k(x)-E_k(x)
}
}
```
and

```math
\boxed{
C_{44}^{k,\mathrm{CSF}}(x)
=
C_{55}^{k,\mathrm{CSF}}(x)
=
C_{66}^{k,\mathrm{CSF}}(x)
=
G_k(x).
}
```
Thus, for each transverse domain,

```math
\boxed{
\left\{
\Omega^k(x),
E_k(x),
G_k(x)
\right\}
\longrightarrow
\mathbf C_k^{\mathrm{CSF}}(x)
}
```
This is the constitutive building block supplied by CSF.

> **Important:** this is a two-field constitutive closure. It is not a fully general anisotropic constitutive law. A fully general anisotropic material would require additional independent constitutive coefficients.

---

## 5. Constitutive field over the complete cross-section

The complete sectional constitutive field is obtained by assigning the appropriate domain matrix to each transverse point.

For a point $(y,z)$ belonging to domain $\Omega^k(x)$,

```math
\boxed{
\mathbf C^{\mathrm{CSF}}(x,y,z)
=
\mathbf C_k^{\mathrm{CSF}}(x),
\qquad
(y,z)\in\Omega^k(x)
}
```
Hence the complete CSF material field is piecewise-defined over the cross-section:

```math
\boxed{
\mathbf C^{\mathrm{CSF}}(x,y,z)
=
\begin{cases}
\mathbf C_1^{\mathrm{CSF}}(x), & (y,z)\in\Omega^1(x),\\
\mathbf C_2^{\mathrm{CSF}}(x), & (y,z)\in\Omega^2(x),\\
\vdots & \\
\mathbf C_{N_\Omega}^{\mathrm{CSF}}(x), & (y,z)\in\Omega^{N_\Omega}(x).
\end{cases}
}
```
This representation naturally allows discontinuities of material properties across domain boundaries.

---

## 6. General CSF output for CUF coupling

The complete sectional information that CSF can provide at any longitudinal coordinate $x$ is therefore

```math
\boxed{
\mathcal S_{\mathrm{CSF}}(x)
=
\left\{
\Omega^k(x),
\mathbf C_k^{\mathrm{CSF}}(x)
\right\}_{k=1}^{N_\Omega}
}
```
or, equivalently, as two fields:

```math
\boxed{
\mathcal S_{\mathrm{CSF}}(x)
\equiv
\left\{
\Omega(x),
\mathbf C^{\mathrm{CSF}}(x,y,z)
\right\}.
}
```
This is the general geometry-and-material representation supplied by CSF.

The two longitudinal evolutions are distinct:

```math
\boxed{
\Omega^k(x)
}
```
describes the evolution of the geometry, while

```math
\boxed{
\mathbf C_k^{\mathrm{CSF}}(x)
}
```
describes the evolution of the constitutive properties.

---

## 7. Boundary between CSF and CUF

The CUF kinematic approximation introduces quantities such as

```math
F_\tau(y,z),
\qquad
F_s(y,z),
```
their transverse derivatives, the approximation order, and the displacement amplitudes.

These quantities do not belong to the CSF geometry or material representation.

Therefore CSF alone does **not** determine the CUF sectional coefficients $J$ appearing in the reference formulation.

A typical CUF coefficient has the structure

```math
J
\sim
\int_{\Omega^k}
C_{ij}
\,F_\tau
\,F_s
\,d\Omega,
```
or analogous expressions involving derivatives of $F_\tau$ and $F_s$.

Consequently, its evaluation requires both:

```math
\boxed{
\underbrace{
\left\{
\Omega^k(x),
\mathbf C_k^{\mathrm{CSF}}(x)
\right\}
}_{\text{provided by CSF}}
+
\underbrace{
\left\{
F_\tau,F_s,\ldots
\right\}
}_{\text{defined by CUF}}
}
```
Only after these two parts are combined can the CUF sectional coefficients be evaluated.

The interface can therefore be summarized as

```math
\boxed{
\text{CSF}
\longrightarrow
\left\{
\Omega^k(x),
\mathbf C_k^{\mathrm{CSF}}(x)
\right\}_{k=1}^{N_\Omega}
\longrightarrow
\text{CUF formulation}
}
```
The CUF approximation remains entirely outside the CSF representation.

---

### References

- G. Giunta, S. Belouettar, E. Carrera, **“Analysis of FGM Beams by Means of Classical and Advanced Theories”**, *Mechanics of Advanced Materials and Structures*, 17 (2010), 622–635.

- S. O. Ojo, P. M. Weaver, **“Efficient strong Unified Formulation for stress analysis of non-prismatic beam structures”**, 2021.
