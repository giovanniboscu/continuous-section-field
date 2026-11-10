# CSF-CUF: Coupling a Continuous Geometry-Material Field to the Carrera Unified Formulation

*A variational derivation with explicit fundamental nuclear operators*

## Guiding concept and mathematical contribution

The purpose of the formulation is to introduce a **continuous physical field of geometry and material properties as a primary mathematical object** in the Carrera Unified Formulation (CUF). The Continuous Section Field (CSF) describes the member independently of the CUF expansion, the longitudinal approximation and the solution method. The contribution is the **direct coupling of this prescribed physical field to CUF sectional integrals, variational equations and fundamental nuclear operators**.

The physical description supplies sectional domains, boundaries and constitutive properties at every longitudinal station. The CUF approximation independently supplies the displacement functions used to test and approximate the solution. Section 5 defines the sectional integrals in which these inputs are combined; Section 6 derives the resulting longitudinal equilibrium operator. The notation for each mathematical object is defined before its use.

The geometry determines the **region of integration**, the constitutive field determines the **material weighting**, and the chosen CUF expansion determines the **test and trial factors**. Consequently, replacing an admissible physical geometry or constitutive field changes the values of the sectional integrals without requiring a different rule for constructing the governing operator.

A sectional basis may also have a physical longitudinal dependence $F_\tau(x,y,z)$; in that case $F_{\tau,x}$ must enter the strain field. This is a **kinematic generalization**, distinct from the defining CSF coupling. A varying sectional geometry does not imply $F_{\tau,x}\ne0$ independently of the selected basis: when the CUF basis follows the evolving physical section, geometric evolution can induce nonzero longitudinal derivatives through its sectional mapping. A variable material field alone does not impose such a derivative.

The development assumes small-strain linear elasticity and leaves the longitudinal solution technique unspecified. It first derives the general sectional operator and then displays the nine explicit nuclear blocks for the stated constitutive class.

---

## 1. The continuous section field

Let $L>0$ be the beam length, let $x\in[0,L]$ denote the longitudinal physical coordinate, and let $(y,z)$ denote physical coordinates within a section. At each station $x$, the prescribed continuous section field $\mathcal S(x)$ supplies the physical sectional sub-domains, their boundaries and their constitutive matrices:

```math
\mathcal S(x) \longmapsto
\left\{\Omega^k(x),\ \partial\Omega^k(x),\ \mathbf C^k(x,y,z)\right\}_{k=1}^{N_\Omega}.
```

Here $N_\Omega$ is the number of sectional sub-domains, $k=1,\ldots,N_\Omega$ labels a sub-domain, $\Omega^k(x)$ is its physical area, $\partial\Omega^k(x)$ its boundary, and $\mathbf C^k$ its $6\times6$ constitutive matrix. The beam occupies

```math
\mathcal V=\lbrace (x,y,z)\mid 0 \lt x \lt L,\ (y,z)\in\Omega(x)\rbrace,
\qquad
\Omega(x)=\bigcup_{k=1}^{N_\Omega}\Omega^k(x).
```

**Status and regularity.** $\mathcal S(x)$ is prescribed input, not an unknown of the boundary-value problem. It may be analytic or numerical, provided the domains, material coefficients and required physical measures can be evaluated at the integration stations. Continuity refers to the axial evolution of the sectional description on smooth portions of the member; material properties may jump across sub-domain interfaces.

**Working assumptions for the derivation.** On the longitudinal interval considered, assume that:

1. the sectional partition has a fixed number $N_\Omega$ of labeled sub-domains (piecewise descriptions can be treated interval by interval);
2. the domains $\Omega^k(x)$ vary regularly with $x$ wherever the geometry is smooth;
3. $\mathbf C^k$ may be discontinuous across the interfaces between different sub-domains;
4. the sectional integrals, matrix coefficients and projected loads subsequently defined in Sections 5 and 7 are sufficiently integrable for the weak formulation. For the classical strong form derived in Section 6, the two coefficient matrices multiplying derivatives of the test amplitudes must additionally be differentiable with respect to the longitudinal coordinate on each smooth interval. These matrices are identified as $\mathbf H^{10}_{\tau s}$ and $\mathbf H^{11}_{\tau s}$ in Section 5.2. Piecewise-smooth coefficients are treated interval by interval, together with their interface conditions.

**Independent dependencies.** The domains $\Omega^k(x)$ describe the evolving geometry; $\mathbf C^k(x,y,z)$ describes the evolving and possibly heterogeneous material. Neither is inferred from the CUF displacement approximation, and neither implies the other. Moving domains change where each sectional integral is taken; a varying material changes how its integrand is weighted. Neither effect, by itself, changes the definition of the CUF functions.

---

## 2. CUF kinematics

Let $\mathbf u(x,y,z)$ denote the three-component displacement vector, and let $M$ be the number of functions in the chosen CUF sectional expansion. Each function $F_\tau$ is a scalar function of position; the associated vector $\mathbf q_\tau(x)$ contains three unknown longitudinal displacement amplitudes. The expansion index $\tau$ takes values from $1$ to $M$. The displacement field is

```math
\mathbf u(x,y,z)=\sum_{\tau=1}^{M}F_\tau(x,y,z)\,\mathbf q_\tau(x),
\qquad
\mathbf q_\tau(x)=
\begin{bmatrix}q_{x\tau}(x)\\ q_{y\tau}(x)\\ q_{z\tau}(x)\end{bmatrix}.
```

When constructing the variational equations, $\tau$ labels a test expansion and $s=1,\ldots,M$ labels a trial expansion. Their amplitudes use components $q_{x\tau}$, $q_{y\tau}$ and $q_{z\tau}$ (and correspondingly for $s$). An expansion index is summed only where an explicit summation sign is written.

When the selected basis is defined on and follows an evolving physical section, its physical evaluation can depend on $x$, so $F_\tau=F_\tau(x,y,z)$. In that case the derivative $F_{\tau,x}$, taken at fixed physical coordinates $y,z$, must be retained. For example, a Lagrange L9 basis attached to moving sectional vertices can acquire a nonzero $F_{\tau,x}$ through the derivative of its local sectional mapping. By contrast, a basis fixed in physical transverse coordinates may satisfy $F_{\tau,x}=0$ even for a non-prismatic member. Thus geometric evolution does not determine $F_{\tau,x}$ independently of the chosen basis; material variation alone does not induce it. Local sectional coordinates and Jacobians may be used to evaluate sectional quadrature and basis derivatives; the CSF-CUF coupling does not require a prescribed **beam-wide reference-to-physical mapping** of the non-prismatic solid.

The derivatives are denoted

```math
F_{\tau,x}=\frac{\partial F_\tau}{\partial x},\qquad
F_{\tau,y}=\frac{\partial F_\tau}{\partial y},\qquad
F_{\tau,z}=\frac{\partial F_\tau}{\partial z},
```

and the longitudinal action on an amplitude $v$ is

```math
\mathcal D_F[v]=F_{,x}\,v+F\,v',\qquad v'=\frac{dv}{dx}.
```

---

## 3. Small-strain field

For a displacement component $u_i$, the notation $u_{i,j}$ denotes its partial derivative with respect to coordinate $j$, where the component and coordinate labels $i,j$ take values in $\lbrace x,y,z\rbrace$. The symbol $\gamma$ denotes an engineering shear strain, and superscript $T$ denotes matrix or vector transposition. With the engineering strain vector $\boldsymbol\varepsilon=[\varepsilon_{xx},\varepsilon_{yy},\varepsilon_{zz},\gamma_{yz},\gamma_{xz},\gamma_{xy}]^T$ and

```math
\varepsilon_{xx}=u_{x,x},\quad \varepsilon_{yy}=u_{y,y},\quad \varepsilon_{zz}=u_{z,z},
\quad
\gamma_{yz}=u_{y,z}+u_{z,y},\quad \gamma_{xz}=u_{x,z}+u_{z,x},\quad \gamma_{xy}=u_{x,y}+u_{y,x},
```

the strain contribution of a single trial expansion $s$ is denoted by $\boldsymbol\varepsilon_s$. Using the longitudinal derivative operator $\mathcal D_F$ defined in Section 2, with $F=F_s$, one obtains

```math
\boldsymbol\varepsilon_s=
\begin{bmatrix}
\mathcal D_{F_s}[q_{xs}]\\
F_{s,y}\,q_{ys}\\
F_{s,z}\,q_{zs}\\
F_{s,z}\,q_{ys}+F_{s,y}\,q_{zs}\\
F_{s,z}\,q_{xs}+\mathcal D_{F_s}[q_{zs}]\\
F_{s,y}\,q_{xs}+\mathcal D_{F_s}[q_{ys}]
\end{bmatrix},
\qquad
\boldsymbol\varepsilon=\sum_{s=1}^{M}\boldsymbol\varepsilon_s .
```

The prefix $\delta$ denotes an admissible virtual variation of an unknown amplitude. The virtual strain follows from the same linear expression with $\mathbf q_s$ and $\mathbf q_s'$ replaced by $\delta\mathbf q_s$ and $\delta\mathbf q_s'$.

For matrix assembly it is convenient to collect coefficients of the amplitudes and their longitudinal derivatives separately. Define the following $6\times3$ strain-displacement matrices $\mathbf B^{(0)}(F)$ and $\mathbf B^{(1)}(F)$; their superscripts $0$ and $1$ refer to terms multiplying $\mathbf q_s$ and $\mathbf q_s'$, respectively:

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
\end{bmatrix},
```

one has

```math
\boldsymbol\varepsilon_s=\mathbf B^{(0)}(F_s)\,\mathbf q_s+\mathbf B^{(1)}(F_s)\,\mathbf q_s' .
```

---

## 4. Constitutive law

In a physical sub-domain $k$, let $\boldsymbol\sigma^k$ denote the six-component stress vector ordered consistently with the strain components introduced in Section 3. The three shear entries are *tensorial stresses* (not engineering strains):

```math
\boldsymbol\sigma^k=
\begin{bmatrix}
\sigma_{xx}^k & \sigma_{yy}^k & \sigma_{zz}^k &
\sigma_{yz}^k & \sigma_{xz}^k & \sigma_{xy}^k
\end{bmatrix}^{T}.
```

The constitutive relation in that sub-domain is

```math
\boldsymbol\sigma^k(x,y,z)=\mathbf C^k(x,y,z)\,\boldsymbol\varepsilon(x,y,z).
```

Small-displacement, small-strain linear elasticity is assumed. The sectional matrix construction introduced in Section 5 applies to any symmetric $\mathbf C^k$. For the explicit nine-block nucleus of Section 9, the constitutive matrix has the structure

```math
\mathbf C^k=
\begin{bmatrix}
C_{11}&C_{12}&C_{13}&0&0&0\\
C_{12}&C_{22}&C_{23}&0&0&0\\
C_{13}&C_{23}&C_{33}&0&0&0\\
0&0&0&C_{44}&0&0\\
0&0&0&0&C_{55}&0\\
0&0&0&0&0&C_{66}
\end{bmatrix}^{k},
```

each entry possibly depending on $x,y,z$. A fully populated matrix adds terms to the individual blocks without changing the construction.

---

## 5. Internal virtual work and sectional coefficients

Here $\delta W_{\mathrm{int}}$ denotes the internal virtual work, $d\Omega$ the physical sectional area element, and $dx$ the longitudinal length element. The superscript $T$ denotes transposition. The internal virtual work is integrated over the actual sectional domains supplied by $\mathcal S(x)$:

```math
\delta W_{\mathrm{int}}=
\int_0^L\sum_{k=1}^{N_\Omega}\int_{\Omega^k(x)}
\delta\boldsymbol\varepsilon^{T}\,\mathbf C^k\,\boldsymbol\varepsilon\;d\Omega\,dx .
```

### 5.1 The CSF-to-CUF sectional coefficients $J(x)$

**The fundamental mathematical coupling between the prescribed continuous physical field and the CUF approximation is expressed by the sectional coefficients $J(x)$.** Let $m,n\in\lbrace 1,\ldots,6\rbrace$ label constitutive entries in the engineering-strain order $(xx,yy,zz,yz,xz,xy)$. Let $\alpha,\beta\in\lbrace 0,x,y,z\rbrace$ specify derivatives of the sectional test and trial functions, respectively, with $F_{\tau,0}\equiv F_\tau$ and $F_{s,0}\equiv F_s$. For each physical sub-domain $k$, define

```math
\boxed{
J^{mn,k}_{\tau,\alpha\,s,\beta}(x)
=\int_{\Omega^k(x)}
C^k_{mn}(x,y,z)\,
F_{\tau,\alpha}(x,y,z)\,
F_{s,\beta}(x,y,z)\,d\Omega
}
```

The assembled sectional coefficient is the sum over the physical sub-domains:

```math
\boxed{
J^{mn}_{\tau,\alpha\,s,\beta}(x)
=\sum_{k=1}^{N_\Omega}J^{mn,k}_{\tau,\alpha\,s,\beta}(x).
}
```

The index $\tau$ identifies the test expansion and $s$ the trial expansion; they are held fixed when defining an individual coefficient. The first derivative label $\alpha$ acts on $F_\tau$ and the second $\beta$ on $F_s$. Later, in the explicit nine-operator nucleus, the shortened notation $J^{mn}_{\alpha\beta}(x)$ holds $(\tau,s)$ implicit.

Each $J$ combines **three distinct inputs**: the CSF domain $\Omega^k(x)$ determines the integration region, the CSF constitutive entry $C^k_{mn}(x,y,z)$ determines its material weighting, and the chosen CUF basis provides the kinematic factors $F_{\tau,\alpha}F_{s,\beta}$. Thus the physical field enters the **coefficients of the nuclear operators**, without replacing the CUF displacement approximation. In particular, when $F_{\tau,x}=0$, the $J$ coefficients can still vary with $x$ through the geometry and constitutive field.

### 5.2 Sectional matrices $\mathbf H^{ab}(x)$ and the weak form

Using the strain-displacement matrices defined in Section 3, introduce $a,b\in\lbrace 0,1\rbrace$. The first superscript $a$ identifies whether the *test* amplitude is undifferentiated ($0$) or longitudinally differentiated ($1$); the second $b$ does the same for the *trial* amplitude. For each fixed test/trial expansion pair $(\tau,s)$, define the four $3\times3$ sectional matrices

```math
\mathbf H^{ab}_{\tau s}(x)=
\sum_{k=1}^{N_\Omega}\int_{\Omega^k(x)}
\left[\mathbf B^{(a)}(F_\tau)\right]^T
\mathbf C^k(x,y,z)\,
\mathbf B^{(b)}(F_s)\,d\Omega .
```

Every entry of $\mathbf H^{ab}_{\tau s}(x)$ is a linear combination of the sectional coefficients $J^{mn}_{\tau,\alpha\,s,\beta}(x)$. The matrices $\mathbf H$ therefore collect the $J$ coefficients into the four groups needed for the longitudinal amplitudes and their derivatives. A matrix entry $H^{ab}_{ij,\tau s}$ has row $i$ (test-displacement component) and column $j$ (trial-displacement component), with $i,j\in\lbrace x,y,z\rbrace$. The weak internal virtual work becomes

```math
\delta W_{\mathrm{int}}=\int_0^L\sum_{\tau,s}
\left[
\delta\mathbf q_\tau^T\mathbf H^{00}_{\tau s}\mathbf q_s
+\delta\mathbf q_\tau^T\mathbf H^{01}_{\tau s}\mathbf q_s'
+\delta\mathbf q_\tau'^T\mathbf H^{10}_{\tau s}\mathbf q_s
+\delta\mathbf q_\tau'^T\mathbf H^{11}_{\tau s}\mathbf q_s'
\right]dx .
```

The defining path is therefore

```math
\boxed{\mathcal S(x)\ \longrightarrow\ J^{mn}_{\tau,\alpha\,s,\beta}(x)\ \longrightarrow\
\mathbf H^{ab}_{\tau s}(x)\ \longrightarrow\ \mathcal K_{\tau s}.}
```

---

## 6. Governing longitudinal operator



The prime denotes differentiation with respect to $x$. For any scalar or vector-valued quantity $g(x)$, square brackets with limits denote its difference between the two beam ends:

```math
[g]_{x=0}^{x=L}=g(L)-g(0).
```

Integrating by parts the terms containing
$\delta\mathbf{q}_\tau'$ (the longitudinal derivative of the
test amplitude) gives:



```math
\delta W_{\mathrm{int}}=
\int_0^L\sum_\tau\delta\mathbf q_\tau^T\sum_s
\Big[
\mathbf H^{00}_{\tau s}\mathbf q_s+\mathbf H^{01}_{\tau s}\mathbf q_s'
-\partial_x\!\big(\mathbf H^{10}_{\tau s}\mathbf q_s+\mathbf H^{11}_{\tau s}\mathbf q_s'\big)
\Big]dx
+\Big[\sum_\tau\delta\mathbf q_\tau^T\sum_s
\big(\mathbf H^{10}_{\tau s}\mathbf q_s+\mathbf H^{11}_{\tau s}\mathbf q_s'\big)\Big]_{x=0}^{x=L}.
```




Define $\mathcal K_{\tau s}$ as the $3\times3$ matrix differential operator acting on the trial vector $\mathbf q_s(x)$ for a fixed test/trial expansion pair. The generalized longitudinal operator is therefore

```math
\mathcal K_{\tau s}[\mathbf q_s]=
\mathbf H^{00}_{\tau s}\mathbf q_s+\mathbf H^{01}_{\tau s}\mathbf q_s'
-\partial_x\!\left[\mathbf H^{10}_{\tau s}\mathbf q_s+\mathbf H^{11}_{\tau s}\mathbf q_s'\right].
```

The operator $\partial_x$ acts on the whole product containing the variable coefficient. The boundary term is the generalized end action, balanced by the tractions on the end sections $\Omega(0)$ and $\Omega(L)$.

---

## 7. External virtual work

Let $\Sigma_t$ be the traction-loaded surface of the physical solid and $\bar{\mathbf t}$ the prescribed force per unit surface area (traction). Let $\Gamma_t(x)$ denote its intersection with the current section. The symbol $d\Gamma$ denotes physical line length along this intersection, while $\mu(x,y,z)$ converts $d\Gamma\,dx$ into the corresponding physical surface area element. The CSF geometry supplies both $\Gamma_t(x)$ and this surface measure. The projected traction force $\mathbf p_\tau(x)$ is defined by

```math
\delta W^{t}_{\mathrm{ext}}=\int_{\Sigma_t}\delta\mathbf u^T\bar{\mathbf t}\,dA
=\int_0^L\sum_\tau\delta\mathbf q_\tau^T\,\mathbf p_\tau(x)\,dx,
\qquad
\mathbf p_\tau(x)=\int_{\Gamma_t(x)}F_\tau\,\bar{\mathbf t}\,\mu\,d\Gamma .
```

Here $\mathbf p_\tau$ is a three-component generalized force per unit longitudinal length, and $\delta W^t_{\mathrm{ext}}$ is the associated virtual work. For the body-force density $\mathbf b(x,y,z)$ (force per unit volume), define the generalized body-force contribution

```math
\mathbf f^{b}_\tau(x)=\sum_{k}\int_{\Omega^k(x)}F_\tau\,\mathbf b^k\,d\Omega .
```

Changing the geometry changes the load projection as well as the stiffness, even for an unchanged traction law.

---

## 8. Governing equations

Define $\mathbf f_\tau(x)$ as the total generalized force per unit longitudinal length, equal to the sum of projected surface traction and body-force contributions: $\mathbf f_\tau=\mathbf p_\tau+\mathbf f^b_\tau$. The equilibrium equations then read

```math
\sum_{s=1}^{M}\mathcal K_{\tau s}[\mathbf q_s](x)=\mathbf f_\tau(x),
\qquad \tau=1,\dots,M .
```

The responsibilities are separate:

1. **$\mathcal S(x)$** provides $\Omega^k(x)$, $\partial\Omega^k(x)$, $\mathbf C^k(x,y,z)$;
2. **the CUF expansion** provides $F_\tau$ and its derivatives;
3. **the longitudinal approximation** provides the representation of $\mathbf q_\tau(x)$;
4. **assembly and reconstruction** produce the sectional matrices, the generalized solution and the three-dimensional fields.

The form of the equations does not change with the admissible $\mathcal S(x)$: a new geometry or material only changes the values of the sectional integrals.

---

## 9. Explicit fundamental nucleus: from $J$ to the nine operators

This section specializes the general derivation to the constitutive matrix of Section 4. No additional bilinear-form notation is introduced: the nine component contributions are written directly using the already defined $J$ and $H$ coefficients.

### 9.1 Notation for fixed expansion indices

Fix a test expansion index $\tau$ and a trial expansion index $s$.

The coefficient defined in Section 5.1 depends on both indices. In this section only, the notation is abbreviated as

```math
J_{\alpha\beta}^{mn}(x)
\equiv
J_{\tau,\alpha\,s,\beta}^{mn}(x).
```

Here, $\tau$ identifies the test expansion and $s$ identifies the trial expansion. Both indices remain fixed when defining an individual nuclear operator. Summation over the expansion indices is performed only when assembling the final equilibrium system.

For example, the coefficient

```math
J_{00}^{11}(x)
=
\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)}
C_{11}^k(x,y,z)\,
F_\tau(x,y,z)\,
F_s(x,y,z)\,d\Omega
```

contains the undifferentiated test and trial functions.

By contrast,

```math
J_{0x}^{11}(x)
=
\sum_{k=1}^{N_\Omega}
\int_{\Omega^k(x)}
C_{11}^k(x,y,z)\,
F_\tau(x,y,z)\,
F_{s,x}(x,y,z)\,d\Omega
```

contains the longitudinal derivative of the trial expansion.

Let $i,j\in\lbrace x,y,z\rbrace$ identify a test displacement component and a trial displacement component, respectively.

For the fixed expansion pair $(\tau,s)$, the abbreviation $H_{ij}^{ab}(x)$ denotes the row-$i$, column-$j$ entry of $\mathbf H_{\tau s}^{ab}(x)$ defined in Section 5.2. The omitted expansion indices are not summed.

The indices $a,b\in\lbrace 0,1\rbrace$ indicate whether the corresponding longitudinal amplitude is differentiated:

- $a=0$: the test amplitude is not differentiated;
- $a=1$: the test amplitude is differentiated with respect to $x$;
- $b=0$: the trial amplitude is not differentiated;
- $b=1$: the trial amplitude is differentiated with respect to $x$.

Thus, $H_{ij}^{ab}$ identifies the coefficient multiplying a specific combination of test and trial longitudinal amplitudes in the internal virtual work.

### 9.2 The nine component groups of $\mathbf H^{ab}_{\tau s}$

For each displacement pair $(i,j)$, the four coefficients $H^{00}_{ij}$, $H^{01}_{ij}$, $H^{10}_{ij}$ and $H^{11}_{ij}$ are given below. The superscript $00$ refers to undifferentiated test and trial amplitudes; $01$ differentiates only the trial amplitude; $10$ differentiates only the test amplitude; and $11$ differentiates both. All coefficients use the assembled $J^{mn}_{\alpha\beta}$ defined in Section 9.1.

**Diagonal displacement pairs**

For the $(x,x)$ displacement pair:

```math
\begin{aligned}
H^{00}_{xx}&=J^{11}_{xx}+J^{55}_{zz}+J^{66}_{yy},\\
H^{01}_{xx}&=J^{11}_{x0},\\
H^{10}_{xx}&=J^{11}_{0x},\\
H^{11}_{xx}&=J^{11}_{00}.
\end{aligned}
```

For the $(y,y)$ displacement pair:

```math
\begin{aligned}
H^{00}_{yy}&=J^{22}_{yy}+J^{44}_{zz}+J^{66}_{xx},\\
H^{01}_{yy}&=J^{66}_{x0},\\
H^{10}_{yy}&=J^{66}_{0x},\\
H^{11}_{yy}&=J^{66}_{00}.
\end{aligned}
```

For the $(z,z)$ displacement pair:

```math
\begin{aligned}
H^{00}_{zz}&=J^{33}_{zz}+J^{44}_{yy}+J^{55}_{xx},\\
H^{01}_{zz}&=J^{55}_{x0},\\
H^{10}_{zz}&=J^{55}_{0x},\\
H^{11}_{zz}&=J^{55}_{00}.
\end{aligned}
```

**Axial–transverse coupling pairs**

For the $(x,y)$ displacement pair:

```math
\begin{aligned}
H^{00}_{xy}&=J^{12}_{xy}+J^{66}_{yx},\\
H^{01}_{xy}&=J^{66}_{y0},\\
H^{10}_{xy}&=J^{12}_{0y},\\
H^{11}_{xy}&=0.
\end{aligned}
```

For the $(y,x)$ displacement pair:

```math
\begin{aligned}
H^{00}_{yx}&=J^{12}_{yx}+J^{66}_{xy},\\
H^{01}_{yx}&=J^{12}_{y0},\\
H^{10}_{yx}&=J^{66}_{0y},\\
H^{11}_{yx}&=0.
\end{aligned}
```

For the $(x,z)$ displacement pair:

```math
\begin{aligned}
H^{00}_{xz}&=J^{13}_{xz}+J^{55}_{zx},\\
H^{01}_{xz}&=J^{55}_{z0},\\
H^{10}_{xz}&=J^{13}_{0z},\\
H^{11}_{xz}&=0.
\end{aligned}
```

For the $(z,x)$ displacement pair:

```math
\begin{aligned}
H^{00}_{zx}&=J^{13}_{zx}+J^{55}_{xz},\\
H^{01}_{zx}&=J^{13}_{z0},\\
H^{10}_{zx}&=J^{55}_{0z},\\
H^{11}_{zx}&=0.
\end{aligned}
```

**Transverse–transverse coupling pairs**

For the $(y,z)$ displacement pair:

```math
\begin{aligned}
H^{00}_{yz}&=J^{23}_{yz}+J^{44}_{zy},\\
H^{01}_{yz}&=0,\\
H^{10}_{yz}&=0,\\
H^{11}_{yz}&=0.
\end{aligned}
```

For the $(z,y)$ displacement pair:

```math
\begin{aligned}
H^{00}_{zy}&=J^{23}_{zy}+J^{44}_{yz},\\
H^{01}_{zy}&=0,\\
H^{10}_{zy}&=0,\\
H^{11}_{zy}&=0.
\end{aligned}
```

These nine groups follow by substituting the strain-displacement matrices of Section 3 into the definition of $\mathbf H^{ab}_{\tau s}$ in Section 5.2 and collecting the terms for each test/trial displacement pair. The expressions show how the CSF sectional integrals populate all nine entries of the nuclear operator.

### 9.3 One complete weak-to-strong conversion

Consider the axial test/trial pair $(i,j)=(x,x)$. Write $\delta w(x)=\delta q_{x\tau}(x)$ for the virtual axial amplitude and $v(x)=q_{xs}(x)$ for the corresponding trial axial amplitude. These are abbreviations **only for this example**, not additional unknowns. Its contribution to the internal virtual work is

```math
\int_0^L\left[
\delta w\,H^{00}_{xx}v
+\delta w\,H^{01}_{xx}v'
+\delta w'\,H^{10}_{xx}v
+\delta w'\,H^{11}_{xx}v'
\right]dx.
```

Substituting the coefficients for the $(x,x)$ pair in Section 9.2 gives the expression entirely in terms of the already defined coefficients $J$:

```math
\int_0^L\Big[
\delta w\,(J^{11}_{xx}+J^{55}_{zz}+J^{66}_{yy})v
+\delta w\,J^{11}_{x0}v'
+\delta w'\,J^{11}_{0x}v
+\delta w'\,J^{11}_{00}v'
\Big]dx.
```

The two terms containing $\delta w'$ are integrated by parts. This gives

```math
\begin{aligned}
&\int_0^L\delta w\Big[
(J^{11}_{xx}+J^{55}_{zz}+J^{66}_{yy})v
+J^{11}_{x0}v'
-\partial_x\big(J^{11}_{0x}v+J^{11}_{00}v'\big)
\Big]dx\\
&\qquad+\Big[\delta w\big(J^{11}_{0x}v+J^{11}_{00}v'\big)\Big]_{x=0}^{x=L}.
\end{aligned}
```

The first line yields the axial–axial strong differential operator; the second is its end-boundary contribution. The derivative $\partial_x$ acts on each **entire product**, including the variable coefficient $J(x)$.

For any pair $(i,j)$, denote by $K^{\tau s}_{ij}$ the scalar differential operator mapping the trial amplitude $q_{js}$ to the test-component equation indexed by $(i,\tau)$. With $v(x)$ standing for that trial amplitude, the general conversion already established in Section 6 reads

```math
K^{\tau s}_{ij}[v]
=H^{00}_{ij}v+H^{01}_{ij}v'
-\partial_x\!\left(H^{10}_{ij}v+H^{11}_{ij}v'\right).
```

### 9.4 The nine strong-form operators

Substituting the component coefficients from Section 9.2 gives the three diagonal operators:

```math
\begin{aligned}
K^{\tau s}_{xx}[v]&=(J^{11}_{xx}+J^{55}_{zz}+J^{66}_{yy})v+J^{11}_{x0}v'-\partial_x\!\left(J^{11}_{0x}v+J^{11}_{00}v'\right),\\
K^{\tau s}_{yy}[v]&=(J^{22}_{yy}+J^{44}_{zz}+J^{66}_{xx})v+J^{66}_{x0}v'-\partial_x\!\left(J^{66}_{0x}v+J^{66}_{00}v'\right),\\
K^{\tau s}_{zz}[v]&=(J^{33}_{zz}+J^{44}_{yy}+J^{55}_{xx})v+J^{55}_{x0}v'-\partial_x\!\left(J^{55}_{0x}v+J^{55}_{00}v'\right).
\end{aligned}
```

The four axial–transverse coupling operators are

```math
\begin{aligned}
K^{\tau s}_{xy}[v]&=(J^{12}_{xy}+J^{66}_{yx})v+J^{66}_{y0}v'-\partial_x\!\left(J^{12}_{0y}v\right),\\
K^{\tau s}_{yx}[v]&=(J^{12}_{yx}+J^{66}_{xy})v+J^{12}_{y0}v'-\partial_x\!\left(J^{66}_{0y}v\right),\\
K^{\tau s}_{xz}[v]&=(J^{13}_{xz}+J^{55}_{zx})v+J^{55}_{z0}v'-\partial_x\!\left(J^{13}_{0z}v\right),\\
K^{\tau s}_{zx}[v]&=(J^{13}_{zx}+J^{55}_{xz})v+J^{13}_{z0}v'-\partial_x\!\left(J^{55}_{0z}v\right).
\end{aligned}
```

The two transverse coupling operators are

```math
K^{\tau s}_{yz}[v]=(J^{23}_{yz}+J^{44}_{zy})v,
\qquad
K^{\tau s}_{zy}[v]=(J^{23}_{zy}+J^{44}_{yz})v.
```

Collect these nine scalar operators into the $3\times3$ matrix differential operator $\mathbf K_{\tau s}$, whose rows and columns follow displacement components $(x,y,z)$:

```math
\mathbf K_{\tau s}=
\begin{bmatrix}
K^{\tau s}_{xx}&K^{\tau s}_{xy}&K^{\tau s}_{xz}\\
K^{\tau s}_{yx}&K^{\tau s}_{yy}&K^{\tau s}_{yz}\\
K^{\tau s}_{zx}&K^{\tau s}_{zy}&K^{\tau s}_{zz}
\end{bmatrix},
\qquad
\sum_{s=1}^{M}\mathbf K_{\tau s}[\mathbf q_s]=\mathbf f_\tau,
\quad \tau=1,\ldots,M.
```

This $\mathbf K_{\tau s}$ is the explicit component representation of the general $\mathcal K_{\tau s}$ introduced in Section 6; the two notations refer to the **same** longitudinal operator. Only the expansion index $s$ is summed in the displayed equilibrium equation. The physical field determines the values of the sectional coefficients; the algebraic form of the nine operators is fixed by the chosen strain kinematics and the constitutive class.

**Purely transverse specialization.** If the selected expansion has $F_\tau=F_\tau(y,z)$ for every $\tau$, then $F_{\tau,x}=0$, and the coefficients carrying an $x$ differentiation label on a sectional function vanish. The remaining $J(x)$ may nevertheless vary with the physical domains $\Omega^k(x)$ and the material field $\mathbf C^k(x,y,z)$. This shows that a continuous CSF does not require longitudinally varying CUF basis functions.

---

## Appendix A. Three-dimensional reconstruction and local-equilibrium assessment

After the generalized amplitudes are solved, the three-dimensional fields are reconstructed:

```math
\mathbf u=\sum_\tau F_\tau\mathbf q_\tau,\qquad
\boldsymbol\varepsilon=\sum_s\left[\mathbf B^{(0)}(F_s)\mathbf q_s+\mathbf B^{(1)}(F_s)\mathbf q_s'\right],\qquad
\boldsymbol\sigma^k=\mathbf C^k\boldsymbol\varepsilon .
```

The components $\sigma_{xx}^k$, $\sigma_{xy}^k$ and so forth refer to the tensor components already listed in the stress vector of Section 4. In particular, $\sigma_{yz}^k$, $\sigma_{xz}^k$ and $\sigma_{xy}^k$ are the physical shear-stress components in that order; they are not engineering shear strains. The symmetric three-dimensional stress tensor is reconstructed from those six entries. Denote this symmetric stress tensor by $\boldsymbol\sigma^k_{\mathrm{tensor}}$. Within a smooth sub-domain $k$, define $\mathbf r^k$ as its spatial divergence. The operator $\nabla\cdot$ denotes divergence and $\partial_x$, $\partial_y$, $\partial_z$ denote partial derivatives in physical coordinates. In components,

```math
\mathbf r^k(x,y,z)=\nabla\cdot\boldsymbol\sigma^k_{\mathrm{tensor}}=
\begin{bmatrix}
\partial_x\sigma_{xx}+\partial_y\sigma_{xy}+\partial_z\sigma_{xz}\\
\partial_x\sigma_{xy}+\partial_y\sigma_{yy}+\partial_z\sigma_{yz}\\
\partial_x\sigma_{xz}+\partial_y\sigma_{yz}+\partial_z\sigma_{zz}
\end{bmatrix}.
```

The divergence depends on the variation of $\mathbf C^k$, on derivatives of the sectional functions and on the solved amplitudes and their longitudinal derivatives. Within a sub-domain, the strong residual is $\mathbf r^k+\mathbf b^k$, where $\mathbf b^k$ is the body-force density from Section 7. The residual vanishes for exact local equilibrium; across an interface, continuity of the appropriate traction is an additional requirement.

The CUF equations of Section 8 enforce equilibrium in a projected variational sense and do not by themselves imply $\mathbf r^k+\mathbf b^k=\mathbf 0$ pointwise. The residual is therefore an independent a posteriori check, evaluated after reconstruction and not inferred from the one-dimensional equations.
