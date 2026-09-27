# CSF-CUF: Continuous Section Description and Separation of Computational Components

*Technical note for discussion - Giovanni Boscu*

## Purpose

CSF-CUF implements the Carrera Unified Formulation using a continuous description of the physical section and separate components for the transverse approximation and the longitudinal finite-element representation. The purpose of this note is to explain how these descriptions enter the same variational formulation and how their distinct roles are retained in the implementation.

The central object is the **Continuous Section Field**:

```math
x \longmapsto \mathcal{S}(x).
```

At any longitudinal coordinate, this field provides the corresponding sectional geometry and material description. It is defined independently of the finite-element partition and the numerical quadrature. The solver evaluates it at the positions required by the calculation.

Throughout this note, $x$ denotes the beam axis and $(y,z)$ the transverse coordinates.

## 1. From the formulation to the software architecture

Any computational implementation requires a choice of software architecture. In CSF-CUF, this choice follows the mathematical objects and operations presented in this note: the continuous sectional state, the transverse expansion, the longitudinal approximation, and their combination through integration and assembly. These are represented by cooperating Python components with defined interfaces.

The formulation provides the mathematical basis for this organization, while the architecture makes its components reusable across different structural problems. When using the available components, the user specifies the physical model and the approximation choices without having to derive or implement the corresponding integrals for each new case. The software evaluates the required quantities and performs the numerical integrations and assembly.

The practical objective is to make the formulation directly usable through configurable building blocks, while retaining an explicit correspondence between the mathematical model and its computational implementation.

## 2. The continuous sectional state

Let $\Omega(x)$ denote the physical cross-sectional domain at coordinate $x$, and let $\mathbf{C}(x,y,z)$ denote the local constitutive matrix. The sectional state can be expressed as

```math
\mathcal{S}(x)
\longrightarrow
\{
\Omega(x),
\mathbf{C}(x,y,z),
\ldots
\}
```

Here, $\mathcal{S}$ is a function whose value is a sectional state: a domain together with the material information defined over it. It is therefore more general than a list of scalar section properties such as area or moments of inertia.

In CSF, external model files prescribe the geometry and material laws from which this state is evaluated. For the continuously varying members considered here, these laws define the sectional variation throughout the longitudinal domain. Their definition is not tied to a prescribed set of integration points.

The three-dimensional body is described by

```math
\mathcal{B}
=
\left\{(x,y,z):\;x\in[0,L],\;(y,z)\in\Omega(x)\right\}.
```

A prismatic geometry is recovered when $\Omega(x)=\Omega_0$ for every $x$. A non-prismatic geometry is obtained by allowing $\Omega(x)$ to vary along the beam. Material variation is specified through $\mathbf{C}$; a geometrically variable member may still have uniform material properties.

## 3. Displacement approximation

The CUF displacement approximation is written, for a transverse basis independent of $x$, as

```math
\mathbf{u}(x,y,z)
\simeq
\sum_{\tau=1}^{M}F_\tau(y,z)\,\mathbf{u}_\tau(x).
```

The functions $F_\tau$ define the transverse approximation space, while the unknown vector functions $\mathbf{u}_\tau(x)$ describe its longitudinal coefficients. Selecting or enriching the transverse basis determines the cross-sectional displacement patterns admitted by the model.

With a finite-element approximation along the beam axis, within each element,

```math
\mathbf{u}_\tau(x)
\simeq
\sum_i N_i(x)\,\mathbf{q}_{\tau i},
```

and hence

```math
\mathbf{u}(x,y,z)
\simeq
\sum_i\sum_{\tau=1}^{M}
N_i(x)F_\tau(y,z)\,\mathbf{q}_{\tau i}.
```

The longitudinal element partition and connectivity specify the discretization, while the shape functions $N_i$ specify the approximation within each element. Together they form the longitudinal finite-element representation.

These approximation choices are distinct from the physical description $\mathcal{S}(x)$. In particular, a variable physical section can be used with a transverse basis expressed directly in the physical coordinates $(y,z)$.

More generally, an expansion may itself depend on the longitudinal coordinate, $F_\tau=F_\tau(x,y,z)$, for example through section-dependent scaling. In that case its longitudinal derivative must also be included:

```math
\frac{\partial\mathbf{u}}{\partial x}
\simeq
\sum_{i,\tau}
\left(
\frac{dN_i}{dx}F_\tau
+
N_i\frac{\partial F_\tau}{\partial x}
\right)\mathbf{q}_{\tau i}.
```

The separation of computational components accommodates this dependence: the expansion component supplies the basis values and the derivatives required by the formulation.

## 4. Where the descriptions meet

Under small-strain linear elasticity, the internal virtual work is

```math
\delta W_{\mathrm{int}}
=
\int_0^L\int_{\Omega(x)}
\delta\boldsymbol{\varepsilon}^{T}
\mathbf{C}(x,y,z)
\boldsymbol{\varepsilon}
\,d\Omega\,dx.
```

The sectional state supplies the integration domain $\Omega(x)$ and the constitutive matrix $\mathbf{C}(x,y,z)$. The displacement approximation supplies the strain field through the transverse basis, the longitudinal shape functions and their derivatives.

This expression identifies the information that the computational core must combine. It also provides a natural division of responsibilities:

| Component | Information supplied to the calculation |
|---|---|
| Continuous Section Field | Physical sectional domain and material description at the requested coordinate |
| Transverse expansion | Basis values and required spatial derivatives |
| Longitudinal shape functions | Shape-function values and derivatives within each element |
| Longitudinal FE discretization | Element domains, connectivity and global degree-of-freedom organization |

The CUF core combines these quantities during integration and assembly. The components communicate through defined interfaces and must satisfy the compatibility requirements of the formulation. This organization makes the physical model and the approximation choices separately configurable.

## 5. From the continuous sectional field to the fundamental nucleus

The longitudinal dependence of the sectional state is retained through the sectional integrations and into the CUF fundamental nucleus. This can be made explicit for the transverse basis $F_\tau(y,z)$ independent of $x$ introduced in Section 3.

For a sectional sub-domain $\Omega^k(x)$, define

```math
J_{\tau,\phi s,\xi}^{mn,k}(x)
=
\int_{\Omega^k(x)}
C_{mn}^{k}(x,y,z)
F_{\tau,\phi}(y,z)
F_{s,\xi}(y,z)
\,d\Omega.
```

Here, $m,n$ select a constitutive-matrix entry, $\tau,s$ select the test and trial transverse functions, and $\phi,\xi\in\{\varnothing,y,z\}$ specify the transverse derivatives; $\varnothing$ means that no derivative is applied. Summing the sub-domain contributions gives the corresponding global sectional coefficient:

```math
J_{\tau,\phi s,\xi}^{mn}(x)
=
\sum_{k=1}^{N_\Omega}
J_{\tau,\phi s,\xi}^{mn,k}(x).
```

The resulting coefficients remain functions of the longitudinal coordinate. Their dependence on geometry and material is carried into the differential operator through the sequence

```math
\mathcal{S}(x)
\longrightarrow
\{\Omega^k(x),\mathbf{C}^k(x,y,z)\}
\longrightarrow
J_\bullet(x)
\longrightarrow
\mathbf{K}_{\tau s}[\mathcal{S}(x),\partial_x].
```

A representative second-order contribution to the fundamental nucleus has the divergence form

```math
-\partial_x\left[J(x)\,\partial_x u(x)\right],
```

where $J(x)$ denotes the relevant sectional coefficient and $u(x)$ a longitudinal displacement amplitude. Wherever the coefficient and amplitude are sufficiently differentiable, this expression expands as

```math
-\partial_x\left[J(x)\,\partial_x u(x)\right]
=
-\frac{dJ}{dx}\frac{du}{dx}
-J(x)\frac{d^2u}{dx^2}.
```

The derivative acts on the product of the sectional coefficient and the displacement gradient. Thus, the longitudinal variation supplied by the sectional field remains present in the governing operator. Replacing this term with $-J(x)\,d^2u/dx^2$ would omit its contribution through $dJ/dx$.

For example, if $u(x)=a x$, with constant $a$, then

```math
\frac{d^2u}{dx^2}=0,
\qquad
-\partial_x\left[J(x)\,\partial_x u(x)\right]
=
-a\frac{dJ}{dx}.
```

The operator contribution can therefore be nonzero even for a linear longitudinal amplitude. This simple example exposes the role of the variable sectional coefficient within the nucleus.

The finite-element implementation evaluates the corresponding weak-form contribution. For a virtual amplitude $v(x)$, integration by parts gives

```math
\int_0^L
v(x)\left\{-\partial_x\left[J(x)\,\partial_x u(x)\right]\right\}
\,dx
=
\int_0^L
\frac{dv}{dx}J(x)\frac{du}{dx}
\,dx
-
\left[v(x)J(x)\frac{du}{dx}\right]_0^L.
```

Consequently, numerical assembly can use evaluations of $J(x)$ without explicitly computing its longitudinal derivative. The continuous sectional description is retained at the formulation level, while quadrature evaluates the integrals at selected points. Neither a closed-form expression for $J(x)$ nor symbolic differentiation of the sectional geometry is required for this weak-form assembly.

## 6. Continuous definition and quadrature evaluation

At a longitudinal quadrature point $x_g$, the solver evaluates

```math
x_g
\longrightarrow
\mathcal{S}(x_g)
\longrightarrow
\{
\Omega(x_g),
\mathbf{C}(x_g,y,z),
\ldots
\}
```

The resulting domain is used for sectional integration, and the constitutive matrix is evaluated at the required material points to obtain the sectional coefficients described in Section 5. Longitudinal quadrature then uses these coefficients in the weak-form assembly. Numerical quadrature therefore samples an already defined physical description.

**The field $\mathcal{S}(x)$ defines how the section varies; the quadrature defines where that field is evaluated for integration.**

Changing the quadrature points changes the sampling used in the calculation while preserving the underlying geometry and material laws. Similarly, changing the longitudinal mesh does not require redefining the sectional field.

Evaluation of variable geometric and elastic properties at Gauss points is compatible with standard finite-element practice. The specific emphasis of CSF-CUF is the explicit representation of the sectional state as a reusable continuous field and its connection to the CUF core through a dedicated interface.

## 7. Illustrative comparison

The prepared comparison uses a prismatic I-section case from the 2010 work and a corresponding non-prismatic case in which the final web height is reduced by 80% relative to its initial value. Both cases use uniform material properties.

The CUF core, loading, boundary conditions, longitudinal discretization and transverse expansion are kept unchanged, using a Lagrange expansion of order $N=18$. The change is introduced through the external geometric description supplied by CSF.

The accompanying displacement plots show close agreement with the FEM3D reference in both cases. The example illustrates the practical use of the separation described above: the same computational core operates on two different continuous geometric descriptions. The comparison is presented as an illustration of this organization; it does not constitute a general convergence assessment.

## Supporting material

**Case descriptions and numerical results**

[https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/readme.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/readme.md)

**Reproducibility instructions**

[https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/reproducibility.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape/reproducibility.md)
