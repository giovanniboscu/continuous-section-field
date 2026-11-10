# DRAFT

**Abstract**

This paper presents a computational implementation of the Carrera Unified Formulation (CUF) based on the introduction of the Continuous Section Field (CSF) as a primary object describing the geometric and material state of a beam cross-section along its longitudinal axis.

The Continuous Section Field is represented as an independent computational object, providing the sectional geometry and constitutive description at any requested longitudinal coordinate, independently of the transverse displacement expansion, longitudinal finite-element discretization, and numerical quadrature.

Its integration into CUF is established through the sectional integrals, whose longitudinally varying coefficients enter the fundamental nuclei while preserving the underlying variational formulation.

This organization enables a CUF computational core that is independent of any specific geometric or material model, allowing different physical sectional descriptions to be used without modifying the core formulation.

The work establishes the mathematical connection between the continuous sectional description and CUF and presents its realization within a computational framework.

# 1. Introduction

The Carrera Unified Formulation (CUF) provides a general framework for constructing refined structural models through systematic expansions of the displacement field over the beam cross-section. The choice of transverse expansion and the longitudinal approximation determines the numerical representation of the displacement field. A distinct computational question is how to provide the solver with the physical cross-sectional geometry and material properties without embedding a particular geometric or constitutive model in its core.

This paper presents a computational implementation of CUF organized around the **Continuous Section Field (CSF)**. The central idea is to treat the physical sectional state as a primary, independently defined function of the longitudinal position. Let $x$ denote the longitudinal coordinate of a beam of length $L$, and let $(y,z)$ denote the transverse coordinates. The sectional state is written as

$$
\mathcal{S}(x) =
\lbrace \Omega(x), \mathbf{C}(x,y,z) \rbrace,
\qquad 0 \leq x \leq L.
$$

where $\Omega(x)$ is the physical cross-sectional domain and $\mathbf{C}(x,y,z)$ is the local constitutive matrix defined over that domain. This description accommodates both prismatic and non-prismatic members, as well as longitudinal and sectional variations of material properties. It is specified independently of the transverse displacement basis, longitudinal finite-element mesh, and numerical quadrature.

In the proposed implementation, $\mathcal{S}(x)$ is not merely a formal notation. It is realized as a computational object that can be evaluated at longitudinal positions requested by the solver. The object supplies the geometry and constitutive information required for sectional integration. The CUF computational core can consequently operate on different physical sectional descriptions without being specialized to any one of them. Independence here concerns the organization of the model and the solver; the numerical response necessarily remains dependent on the supplied geometry and material properties.

Establishing this organization requires an explicit mathematical connection between the continuous sectional description and CUF. The geometric domains and constitutive matrices supplied by CSF enter the sectional integrals, producing coefficients that vary along the beam and contribute to the CUF fundamental nuclei. The underlying variational formulation is retained. The theoretical section of this paper develops this connection; the implementation section then explains how the corresponding mathematical responsibilities are represented in the software.

The implementation is accompanied by a numerical study of a tapered I-shaped member, with an independent three-dimensional finite-element reference. The study is intended to demonstrate the computational realization of the proposed separation and to make its numerical behavior directly inspectable. The complete source code, physical model definitions, numerical configurations, execution procedures, and results are publicly available so that the reported analyses can be reproduced and checked.

The mathematical formulation is documented in the [CSF–CUF Continuous Geometry and Material Field Formulation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/CSF_CUF_Continuous_Geometry_and_Material_Field_Formulation.md). The reproducible numerical case and its supporting materials are available in the [I-Shape_L repository directory](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape_L).

The contribution of the paper is therefore a computational realization of CUF in which a continuous physical sectional description is a first-class object, together with the mathematical coupling needed to use that object in the CUF formulation and a publicly reproducible numerical demonstration.


# 2. Mathematical Formulation of the CSF-CUF Coupling

This section establishes the mathematical connection between a prescribed Continuous Section Field (CSF) and the Carrera Unified Formulation (CUF). The objective is to identify the sectional information required by the CUF variational equations and the longitudinal operators that result from its integration. The physical field is independent of the displacement approximation and of the longitudinal numerical discretization. Small-strain linear elasticity is assumed.

## 2.1. Continuous sectional description

Using the longitudinal and transverse coordinates introduced in Section 1, let $N_\Omega$ denote the number of physical sectional subdomains. At each station $x$, the prescribed field $\mathcal S(x)$ provides their boundaries and constitutive descriptions:

```math
\mathcal S(x)\longmapsto
\bigl(\Omega^k(x),\,\partial\Omega^k(x),\,\mathbf C^k(x,y,z)\bigr)_{k=1}^{N_\Omega}.
```

Here $k$ identifies a sectional subdomain, $\Omega^k(x)$ is its physical area, $\partial\Omega^k(x)$ its boundary, and $\mathbf C^k(x,y,z)$ its $6\times6$ constitutive matrix. The union of the subdomains is the physical section $\Omega(x)$. The field $\mathcal S(x)$ is prescribed input, not an unknown of the structural problem. Geometry and constitutive properties may vary independently with $x$; material discontinuities between subdomains are permitted. The domains and coefficients are assumed sufficiently regular for the integrations below. Piecewise-smooth descriptions are treated on their respective longitudinal intervals.

The detailed construction and evaluation of the CSF geometric and material model are documented separately. Here only its role as a source of physical sectional data is required.

## 2.2. CUF displacement approximation and strain operators

Let $M$ be the number of scalar transverse expansion functions $F_s(x,y,z)$, with $s=1,\ldots,M$. Let $\mathbf q_s(x)=[q_{xs}(x),q_{ys}(x),q_{zs}(x)]^T$ denote the corresponding three longitudinal displacement amplitudes. The CUF approximation is

```math
\mathbf u(x,y,z)=\sum_{s=1}^{M}F_s(x,y,z)\,\mathbf q_s(x).
```

The index $s$ labels a trial function; $\tau=1,\ldots,M$ will label a test function. Summation over these indices is explicit. A comma followed by $x$, $y$, or $z$ denotes partial differentiation with respect to the indicated physical coordinate; a prime denotes ordinary differentiation with respect to $x$.

The expansion functions may depend on $x$ if the selected basis follows an evolving physical section. Such dependence is a property of the chosen kinematic basis, not a necessary consequence of CSF: a basis fixed in physical transverse coordinates has $F_{s,x}=0$ even when the physical section varies.

Use the engineering strain ordering $[\varepsilon_{xx},\varepsilon_{yy},\varepsilon_{zz},\gamma_{yz},\gamma_{xz},\gamma_{xy}]^T$, where $\gamma$ denotes engineering shear strain. Define the following $6\times3$ matrices for any scalar basis function $F$:

```math
\mathbf B^{(0)}(F)=
\begin{bmatrix}
F_{,x}&0&0\\
0&F_{,y}&0\\
0&0&F_{,z}\\
0&F_{,z}&F_{,y}\\
F_{,z}&0&F_{,x}\\
F_{,y}&F_{,x}&0
\end{bmatrix},
\qquad
\mathbf B^{(1)}(F)=
\begin{bmatrix}
F&0&0\\
0&0&0\\
0&0&0\\
0&0&0\\
0&0&F\\
0&F&0
\end{bmatrix}.
```

The superscripts $(0)$ and $(1)$ identify the factors multiplying an amplitude and its longitudinal derivative, respectively. The strain field is therefore

```math
\boldsymbol\varepsilon=
\sum_{s=1}^{M}
\left[\mathbf B^{(0)}(F_s)\mathbf q_s+
\mathbf B^{(1)}(F_s)\mathbf q_s'\right].
```

The virtual strain $\delta\boldsymbol\varepsilon$ is obtained by replacing each amplitude with its admissible virtual variation $\delta\mathbf q_s$. This construction preserves any required $F_{s,x}$ terms.

## 2.3. Internal virtual work

Within subdomain $k$, the stress vector is $\boldsymbol\sigma^k=\mathbf C^k\boldsymbol\varepsilon$, using tensorial shear stresses paired with the engineering shear strains. The internal virtual work is

```math
\delta W_{\mathrm{int}}=
\int_0^L\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)}
\delta\boldsymbol\varepsilon^T\mathbf C^k(x,y,z)
\boldsymbol\varepsilon\,d\Omega\,dx.
```

The CSF supplies the physical integration domains and constitutive matrices; the CUF expansion supplies the test and trial strain factors. Their coupling takes place inside these sectional integrals, without requiring a beam-wide reference-to-physical mapping of the non-prismatic solid.

## 2.4. Sectional coefficients and weak-form matrices

Let $m,n\in\{1,\ldots,6\}$ label entries of the constitutive matrix in the strain ordering above. Let $\alpha,\beta\in\{0,x,y,z\}$ identify a derivative of the test and trial sectional functions, respectively, where $F_{\tau,0}=F_\tau$ and $F_{s,0}=F_s$. For fixed expansion indices $\tau$ and $s$, define the sectional coefficients

```math
J^{mn}_{\tau,\alpha\,s,\beta}(x)=
\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)}
C^k_{mn}(x,y,z)\,
F_{\tau,\alpha}(x,y,z)\,
F_{s,\beta}(x,y,z)\,d\Omega.
```

Each coefficient combines three independent inputs: the physical sectional domain, the constitutive weighting, and the CUF test/trial functions. In particular, $J(x)$ can vary with $x$ even when all sectional basis functions satisfy $F_{s,x}=0$.

For $a,b\in\{0,1\}$, define four $3\times3$ matrices for each pair $(\tau,s)$:

```math
\mathbf H^{ab}_{\tau s}(x)=
\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)}
\left[\mathbf B^{(a)}(F_\tau)\right]^T
\mathbf C^k(x,y,z)
\mathbf B^{(b)}(F_s)\,d\Omega.
```

The first superscript indicates whether the test amplitude is differentiated longitudinally, and the second does the same for the trial amplitude. Each entry of $\mathbf H^{ab}_{\tau s}$ is a linear combination of the sectional coefficients $J^{mn}_{\tau,\alpha\,s,\beta}$. Substitution into the internal virtual work gives

```math
\begin{aligned}
\delta W_{\mathrm{int}}=\int_0^L\sum_{\tau=1}^{M}\sum_{s=1}^{M}
\bigl[&\delta\mathbf q_\tau^T\mathbf H^{00}_{\tau s}\mathbf q_s
+\delta\mathbf q_\tau^T\mathbf H^{01}_{\tau s}\mathbf q_s'\\
&+\delta\mathbf q_\tau'^T\mathbf H^{10}_{\tau s}\mathbf q_s
+\delta\mathbf q_\tau'^T\mathbf H^{11}_{\tau s}\mathbf q_s'\bigr]dx.
\end{aligned}
```

This weak form is the basis of the numerical assembly: the longitudinal integration requires evaluations of the sectional matrices at the selected integration stations.

## 2.5. Longitudinal fundamental operator

For a fixed test/trial expansion pair $(\tau,s)$, define the three-component longitudinal flux

```math
\mathbf g_{\tau s}(x)=
\mathbf H^{10}_{\tau s}(x)\mathbf q_s(x)
+\mathbf H^{11}_{\tau s}(x)\mathbf q_s'(x).
```

The two terms containing the derivative of the virtual amplitude can then be integrated by parts:

```math
\int_0^L \delta\mathbf q_\tau'^T\mathbf g_{\tau s}\,dx
=\left[\delta\mathbf q_\tau^T\mathbf g_{\tau s}\right]_{x=0}^{x=L}
-\int_0^L\delta\mathbf q_\tau^T
\frac{d\mathbf g_{\tau s}}{dx}\,dx.
```

Here $[h]_{x=0}^{x=L}=h(L)-h(0)$ for any quantity $h(x)$. Combining this identity with the undifferentiated virtual-amplitude terms identifies the matrix differential operator $\mathcal K_{\tau s}$ acting on the trial amplitude vector:

```math
\boxed{
\mathcal K_{\tau s}[\mathbf q_s]=
\mathbf H^{00}_{\tau s}\mathbf q_s
+\mathbf H^{01}_{\tau s}\mathbf q_s'
-\frac{d}{dx}\left(
\mathbf H^{10}_{\tau s}\mathbf q_s
+\mathbf H^{11}_{\tau s}\mathbf q_s'
\right).
}
```

The integration by parts also yields the generalized end action

```math
\left[
\delta\mathbf q_\tau^T
\sum_{s=1}^{M}
\left(\mathbf H^{10}_{\tau s}\mathbf q_s+
\mathbf H^{11}_{\tau s}\mathbf q_s'\right)
\right]_{x=0}^{x=L},
```

summed over $\tau$. To specify the corresponding external action, let $\mathbf b^k(x,y,z)$ be a prescribed body-force density in subdomain $k$. Let $\Gamma_t(x)$ be the traction-loaded portion of the sectional boundary, $\bar{\mathbf t}(x,y,z)$ the prescribed surface traction, $d\Gamma$ the physical line element along that boundary, and $\mu(x,y,z)$ the factor converting $d\Gamma\,dx$ to physical surface area. The generalized force per unit longitudinal length is

```math
\mathbf f_\tau(x)=
\sum_{k=1}^{N_\Omega}\int_{\Omega^k(x)}
F_\tau\,\mathbf b^k\,d\Omega
+\int_{\Gamma_t(x)}
F_\tau\,\bar{\mathbf t}\,\mu\,d\Gamma.
```

The surface term applies to lateral tractions; end-section tractions are represented by the generalized end actions. The interior equilibrium equations are

```math
\sum_{s=1}^{M}\mathcal K_{\tau s}[\mathbf q_s]
=\mathbf f_\tau(x),\qquad \tau=1,\ldots,M.
```

For the classical strong form, the coefficients and amplitudes must have the required differentiability on each smooth interval. The longitudinal derivative in $\mathcal K_{\tau s}$ acts on the **entire products**, including the variable sectional matrices. In contrast, weak-form finite-element assembly uses the preceding integral expression and need not explicitly differentiate $\mathbf H^{ab}_{\tau s}(x)$.

The mathematical path underlying the implementation is thus

```math
\mathcal S(x)\longrightarrow
J^{mn}_{\tau,\alpha\,s,\beta}(x)
\longrightarrow\mathbf H^{ab}_{\tau s}(x)
\longrightarrow\mathcal K_{\tau s}.
```

Changing an admissible physical geometry or constitutive field changes the sectional coefficients, but not the rule used to construct the CUF operator. This is the mathematical basis for a computational core that is independent of any particular geometric-material model.

---

**Theoretical source:** [CSF-CUF continuous geometry and material field formulation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/CSF_CUF_Continuous_Geometry_and_Material_Field_Formulation.md).

**Reproducible implementation and numerical case:** [I-Shape_L](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape_L).
