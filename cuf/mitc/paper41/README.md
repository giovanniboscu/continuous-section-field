# MITC beam elements - Paper §4.1 benchmark (L9, B2/B3/B4)

This example reproduces the **single-element square cantilever** of Section 4.1, Table 1 in Carrera, de Miguel and Pagani (2017), *Extension of MITC to higher-order beam models and shear locking analysis for compact, thin-walled and composite structures* ([DOI: 10.1002/nme.5588](https://doi.org/10.1002/nme.5588)). It compares ordinary full integration (**MITC OFF**) and mixed interpolation of transverse shear (**MITC ON**) for two-, three- and four-node longitudinal elements.

**Main result:** all six tip-displacement results agree with the paper's rounded values to within **0.117%**; the nine MITC shear-stress samples agree **within the published three-decimal rounding**. These are comparisons to published numerical results, not proof of general correctness for all materials and geometries.

**Reading path:** physical model → CSF section → CUF displacement field → MITC shear correction → YAML configuration → numerical comparison → reproducibility. For execution commands and file layout, see [reproducibility.md](reproducibility.md).

## 1. Physical benchmark and coordinate conventions

The object is a straight, prismatic beam, clamped at one end and subjected to a transverse point force at the center of its free-end section. *Prismatic* means that the section does not change along the beam. We take the beam axis as **x** and the physical cross-section coordinates as **y,z**.

| Physical quantity | Value |
|---|---|
| Beam length | 1000 mm |
| Cross-section | Square, 100 × 100 mm |
| Young's modulus | 75,000 MPa (= 75,000 N/mm²) |
| Poisson's ratio | 0.33 |
| Applied force | −100 N in global z-direction, at the free-end section center |
| Clamp | x = 0 |
| Tip-displacement location | (x,y,z) = (1000,0,0) mm |
| Transverse expansion | L9 (nine-node quadratic Lagrange approximation of the section) |
| Longitudinal approximation | **One** B2, B3 or B4 element per simulation |

**Coordinate translation.** The paper takes **y** along the beam and denotes the longitudinal–transverse shear stress by `σ_yz`. This project takes **x** along the beam, so the corresponding stress is `τ_xz` (equivalently `σ_xz`). The physical component is the same; only its coordinate label changes. Numerical stress comparisons below always use the section center.

## 2. CSF: representing the physical section

**CSF (Continuous Section Field)** defines the beam's *physical* cross-section at every axial position x. Let

```math
\mathcal S(x) = \{\Omega^k(x),\,\mathbf C^k(x,y,z)\}_{k=1}^{K},
```
where `k` identifies a sectional material/domain, `K` is the number of domains, `Ω^k(x)` is its physical area at x, and `C^k(x,y,z)` is its constitutive matrix (the relation between strain and stress at that point). Here there is just **one square domain with constant isotropic material**. The same CSF description is supplied at the two end stations; no taper or longitudinal material variation is introduced.

The model uses actual cross-sectional coordinates in millimetres. It does **not** use a longitudinally varying reference-to-physical sectional mapping to represent the section; thus no *such mapping Jacobian* is needed. Numerical quadrature in a polygon or subdomain may still use its own local integration mapping: that is a different matter.

CSF answers **what physical section and material are present at x**. It does not decide the displacement approximation, number of longitudinal nodes, or MITC tying points. Those belong to CUF and its element formulation.

For the general variable-section mathematics, see [CSF–CUF variable-section formulation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md).

## 3. CUF: from the section to structural unknowns

**CUF (Carrera Unified Formulation)** approximates the three-component displacement field using functions over the cross-section. At a physical point (x,y,z):

```math
\mathbf u(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,\mathbf u_\tau(x).
```
Here `u = (u_x,u_y,u_z)^T` is the displacement vector; `F_τ(y,z)` is the τ-th transverse expansion function; `M` is the number of transverse functions; and `u_τ(x)` is the associated **three-component, still-unknown** axial displacement function. In this benchmark the transverse functions are supplied by the L9 expansion.

### How an L9 transverse function is constructed

L9 is a **nine-node, quadratic tensor-product Lagrange interpolation** on each four-sided CSF sectional domain. Introduce local transverse coordinates `(alpha,beta)` in the square `[-1,1] x [-1,1]`. The three one-dimensional shape polynomials through `-1, 0, +1` are

```math
\ell_{-1}(t)=\tfrac12 t(t-1),\qquad
\ell_0(t)=1-t^2,\qquad
\ell_{+1}(t)=\tfrac12 t(t+1).
```

For a local node `a` with natural coordinates `(alpha_a,beta_a)`, the transverse function is the product

```math
F_a(\alpha,\beta)=\ell_{\alpha_a}(\alpha)\,\ell_{\beta_a}(\beta).
```

The actual node numbering in [`lagrangeL9_v4.py`](expansions/lagrangeL9_v4.py) is:

```text
7 ----- 6 ----- 5
|               |
8       9       4
|               |
1 ----- 2 ----- 3
```

Thus, for example, node 9 is `(0,0)` and its function is

```math
F_9(\alpha,\beta)=(1-\alpha^2)(1-\beta^2).
```

Node 1 is `(-1,-1)` and its function is

```math
F_1(\alpha,\beta)=\tfrac14\alpha(\alpha-1)\,\beta(\beta-1).
```

The local functions satisfy `F_a(alpha_b,beta_b) = delta_ab` and `sum_a F_a=1`. These two properties explain respectively nodal interpolation and reproduction of constant transverse fields.

**From natural to physical transverse coordinates.** The L9 plugin uses the CSF quadrilateral vertices to evaluate an isoparametric *transverse quadrature/interpolation mapping*. Its Jacobian transforms derivatives with respect to `(alpha,beta)` into derivatives with respect to the physical section coordinates `(y,z)`; it does **not** introduce a longitudinally varying reference section in the definition of CSF. The two mappings must not be confused. For the square example the transformation is affine; for general quadrilaterals the plugin computes it from the four vertices.

The L9 functions above are the local building blocks. When several CSF domains meet, the plugin assembles shared transverse nodes into global CUF functions; see the same source file for connectivity and derivative details. This example has one square domain.


One longitudinal finite element then interpolates each `u_τ(x)`:

```math
\mathbf u_\tau(x) = \sum_{i=1}^{n} N_i(\xi(x))\,\mathbf q_{\tau i},
```
where `n` is the number of longitudinal nodes, `N_i` their shape functions on the element, `ξ` its local axial coordinate, and `q_{τi}` the three displacement unknowns associated with transverse function τ and longitudinal node i. Substituting this equation **into the preceding CUF expansion** gives the actual finite-element displacement approximation:

```math
\boxed{\mathbf u(x,y,z) = \sum_{\tau=1}^{M}\sum_{i=1}^{n} F_\tau(y,z)N_i(\xi(x))\,\mathbf q_{\tau i}.}
```
The six runs use **one element**, with `n=2` (B2, linear), `n=3` (B3, quadratic), or `n=4` (B4, cubic). Changing B2→B3→B4 changes the *polynomial order of the same single element*, not the number of elements or the CSF section.

### What the coefficients `q` represent and how they are obtained

Each `q_{tau i}=(q_{x,tau i},q_{y,tau i},q_{z,tau i})^T` is an **unknown coefficient**, not an independently prescribed displacement at every physical section point. Substituting the finite-element field into the virtual-work equations and assembling the sectional contributions produces the discrete equilibrium system

```math
\mathbf K\mathbf q=\mathbf f.
```

Here `K` is the assembled stiffness, `q` is the vector formed by collecting all CUF longitudinal coefficients, and `f` is the generalized force vector obtained by projecting the physical load onto the same trial/test functions. The clamp imposes the corresponding essential constraints; the implementation may solve an augmented constrained system (KKT) rather than this unconstrained shorthand. After solving, the coefficients in `q` determine `u(x,y,z)` and the strains by the formulas in this README.

**Reconstruction boundary:** the README explains how `q` enters each equation, but it does not list all solved coefficients. For actual numerical values, use the archived `output/*.cuf.npz` checkpoints or rerun the installed CSF–CUF solver as documented in [`reproducibility.md`](reproducibility.md). The full solver is part of the linked repository, not copied into the benchmark folder.


### Where the transverse shear strain comes from

Consider the transverse shear strain in the physical **x-z** plane. Rather than assuming its formula, start from the displacement gradient and the **small-strain tensor** (the symmetric part of the gradient):

```math
\boldsymbol\varepsilon=\tfrac12\left(\nabla\mathbf u+(\nabla\mathbf u)^T\right).
```

Its `xz` entry is

```math
\varepsilon_{xz}=\tfrac12\left(\frac{\partial u_x}{\partial z}+\frac{\partial u_z}{\partial x}\right).
```

The *engineering* shear strain is defined as twice the corresponding tensor component, `gamma_xz = 2 epsilon_xz`. Therefore

```math
\gamma_{xz}
= \frac{\partial u_z}{\partial x}
+ \frac{\partial u_x}{\partial z}.
```
**Step 1 - Write the two displacement components.** Taking the x- and z-components of the CUF finite-element displacement field from Section 3 gives

```math
\begin{aligned}
u_z(x,y,z)
&= \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,N_i(\xi(x))\,q_{z,\tau i}, \\
u_x(x,y,z)
&= \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,N_i(\xi(x))\,q_{x,\tau i}.
\end{aligned}
```
The coefficients `q_{z,τi}` and `q_{x,τi}` are the z- and x-components of the nodal unknown vector `q_{τi}`. They are independent of the spatial coordinates when differentiating the interpolated field.

**Step 2 - Differentiate each component.** The transverse functions `F_τ(y,z)` do not depend on x, while the longitudinal functions `N_i(ξ(x))` do not depend on z. Consequently,

```math
\begin{aligned}
\frac{\partial u_z}{\partial x}
&= \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,
\frac{dN_i(\xi(x))}{dx}\,q_{z,\tau i}, \\
\frac{\partial u_x}{\partial z}
&= \sum_{\tau=1}^{M}\sum_{i=1}^{n}
\frac{\partial F_\tau(y,z)}{\partial z}\,
N_i(\xi(x))\,q_{x,\tau i}.
\end{aligned}
```
Substituting these **two derivatives into the small-strain definition** gives

```math
\begin{aligned}
\gamma_{xz}(x,y,z)
={}& \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,
\frac{dN_i(\xi(x))}{dx}\,q_{z,\tau i} \\
&+ \sum_{\tau=1}^{M}\sum_{i=1}^{n}
\frac{\partial F_\tau(y,z)}{\partial z}\,
N_i(\xi(x))\,q_{x,\tau i}.
\end{aligned}
```
**Step 3 - Convert the longitudinal derivative to the natural coordinate.** The element shape functions are defined in `ξ`, not directly in the physical axial coordinate `x`. The chain rule is therefore

```math
\frac{dN_i(\xi(x))}{dx}
= \frac{dN_i}{d\xi}\,\frac{d\xi}{dx}.
```
For the **straight, affine longitudinal element used in this benchmark**, let `x_a` and `x_b` denote its physical endpoints and `L_e=x_b-x_a` its length. With `-1 <= ξ <= 1`,

```math
\begin{aligned}
x(\xi) &= \frac{x_a+x_b}{2}+\frac{L_e}{2}\,\xi, \\
J_x &= \frac{dx}{d\xi}=\frac{L_e}{2}, \\
\frac{d\xi}{dx} &= \frac{1}{J_x}=\frac{2}{L_e}.
\end{aligned}
```
Thus,

```math
\frac{dN_i(\xi(x))}{dx}
= \frac{2}{L_e}\,\frac{dN_i}{d\xi}.
```
**Step 4 - Obtain the shear strain evaluated by the ordinary CUF operator.** Substituting the chain-rule result into the expression from Step 2 yields

```math
\begin{aligned}
\gamma_{xz}(x,y,z)
={}& \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,\frac{2}{L_e}\,
\frac{dN_i}{d\xi}\,q_{z,\tau i} \\
&+ \sum_{\tau=1}^{M}\sum_{i=1}^{n}
\frac{\partial F_\tau(y,z)}{\partial z}\,
N_i(\xi(x))\,q_{x,\tau i}.
\end{aligned}
```
Both `N_i` and `dN_i/dξ` in this last expression are evaluated at `ξ=ξ(x)`. For a non-affine longitudinal mapping, the general factor `1/J_x(ξ)` replaces `2/L_e`.

The other transverse shear component follows from the same steps, exchanging z with y:

```math
\gamma_{xy}
= \frac{\partial u_y}{\partial x}
+ \frac{\partial u_x}{\partial y}.
```
**Keep the two geometrical roles separate.** The longitudinal Jacobian `J_x=dx/dξ` belongs to the one-dimensional finite-element interpolation and its change of integration coordinate. It is **not** a reference-to-physical *cross-sectional* mapping Jacobian. CSF continues to supply the sectional domains directly in physical `(y,z)` coordinates; the longitudinal Jacobian does not transform those domains.

These are the two ordinary transverse shear-strain components subsequently modified by MITC at selected longitudinal tying points (Section 4).

## 4. MITC: change the shear interpolation, not the material

### How shear locking arises: a simple bending example

The shear-locking mechanism can already be seen in a simple **illustrative beam kinematics**, before introducing the detailed L9 transverse expansion. Let `w(x)` be the transverse deflection and `theta(x)` a section-rotation variable. With the convention `u_z=w(x)` and `u_x=-z theta(x)`, substitution into the strain definition in Section 3 gives

```math
\gamma_{xz}=\frac{dw}{dx}-\theta(x).
```

In a pure-bending, zero-transverse-shear state, `gamma_xz=0`, so the deflection slope and rotation must satisfy `dw/dx=theta(x)`. Consider the exact kinematic example

```math
\theta(x)=\kappa x,\qquad w(x)=\frac{\kappa x^2}{2},\qquad \gamma_{xz}=0,
```

where `kappa` is a constant curvature. A **B2** longitudinal approximation makes `w_h(x)` linear and `theta_h(x)` linear. Its `dw_h/dx` is constant, whereas `theta_h` can vary along the element. Therefore the discrete shear `dw_h/dx-theta_h` generally cannot vanish everywhere while reproducing this bending motion. An elastic shear-energy term penalizes this unwanted strain and can artificially stiffen the response as the beam becomes slender.

This small example explains the *mechanism*, not an exact quantitative derivation of the present L9 benchmark. MITC addresses it by sampling the discrete shear at selected tying points and interpolating those samples at a lower longitudinal polynomial order, without changing displacement degrees of freedom.

### Why correct the shear strain?

With an ordinary displacement finite element, all strains follow from the field just derived. In a bending-dominated slender beam, that interpolation can introduce excessive artificial shear stiffness (*shear locking*), making a computed deflection much too small. MITC (*Mixed Interpolation of Tensorial Components*) keeps **the same displacement unknowns** `q_{τi}`, but replaces the *longitudinal interpolation of transverse shear strain*.

For either shear component, first evaluate its ordinary CUF strain `γ_S(ξ_m,y,z)` at selected local axial positions `ξ_m`, called **tying points**. Then interpolate those samples along the element:

```math
\bar{\boldsymbol\gamma}_S(\xi,y,z)
= \sum_{m=1}^{n-1} \bar N_m(\xi)\,\boldsymbol\gamma_S(\xi_m,y,z).
```
Here `γ_S = (γ_xy, γ_xz)^T`, `n` is the number of longitudinal nodes already defined, and `\bar N_m` are the interpolation functions through the `n−1` tying points. The overbar means **assumed/interpolated shear**, not a changed displacement field.

**Why these tying points?** For a mathematical and historical
explanation of their selection, see
[From interpolation error to MITC](tying_points_origin.md).

| Axial element | Nodal displacement interpolation | Shear tying points | Assumed shear order |
|---|---|---:|---|
| B2 | Linear (2 nodes) | 1 | Constant |
| B3 | Quadratic (3 nodes) | 2 | Linear |
| B4 | Cubic (4 nodes) | 3 | Quadratic |

For B2, with one tying point at the element center, the formula reduces immediately to `\bar γ_S(ξ)=γ_S(0)`: **the assumed shear is constant along that element**. This predicts equal recovered MITC shear at its two axial nodes-a feature directly testable against Table 1.

### Where are the tying points, and how is their interpolation built?

The `n-1` tying coordinates used in this benchmark are the **Gauss–Legendre points** on the natural interval `[-1,1]`; this is the rule also used by [`recover_mitc_shear.py`](recover_mitc_shear.py), through `numpy.polynomial.legendre.leggauss(n-1)`.

| Element | Number of tying points | Natural coordinates `xi_m` |
|---|---:|---|
| B2 | 1 | `0` |
| B3 | 2 | `-1/sqrt(3)`, `+1/sqrt(3)` |
| B4 | 3 | `-sqrt(3/5)`, `0`, `+sqrt(3/5)` |

The functions `bar N_m(xi)` are the **Lagrange interpolating polynomials defined on the tying coordinates**, rather than the displacement-node coordinates. For distinct tying positions, the general construction is

```math
\bar N_m(\xi)=\prod_{\substack{k=1\\k\ne m}}^{n-1}\frac{\xi-\xi_k}{\xi_m-\xi_k}.
```

This yields `bar N_m(xi_j)=1` if `j=m` and `0` otherwise, so the assumed shear reproduces each sampled shear at its tying point.

**B3 example, without skipping the interpolation step.** Set `a=1/sqrt(3)`. The two tying coordinates are `xi_1=-a` and `xi_2=a`; thus

```math
\bar N_1(\xi)=\frac{a-\xi}{2a},\qquad
\bar N_2(\xi)=\frac{\xi+a}{2a}.
```

Evaluating the **ordinary CUF shear** at those positions gives `gamma_1=gamma_S(-a,y,z)` and `gamma_2=gamma_S(a,y,z)`. Substitution into the MITC definition yields

```math
\bar\gamma_S(\xi,y,z)=\frac{a-\xi}{2a}\,\gamma_1+\frac{\xi+a}{2a}\,\gamma_2.
```

At the center (`xi=0`), `bar gamma_S=(gamma_1+gamma_2)/2`; at either tying point it returns the corresponding sampled strain. B2 is the special case of one tying point and `bar N_1=1`. B4 uses the same Lagrange-product construction with the three positions above, producing a quadratic assumed shear.

**What this calculation needs:** the tying coordinates and interpolation polynomials are now explicit; computing the actual `gamma_S(xi_m,y,z)` additionally requires the CUF transverse functions `F_tau`, the longitudinal nodal displacement coefficients and their derivatives. The L9 functions used here are defined in [`expansions/lagrangeL9_v4.py`](expansions/lagrangeL9_v4.py); the [reproducibility guide](reproducibility.md) explains how to obtain the coefficients from the saved checkpoints.

### How the correction enters stiffness

Collect all displacement unknowns into one vector `q`. The ordinary infinitesimal strains can be grouped into non-shear (`ε_B`) and transverse-shear (`γ_S`) parts:

```math
\begin{bmatrix}\boldsymbol\varepsilon_B\\\boldsymbol\gamma_S\end{bmatrix}
=\begin{bmatrix}\mathbf B_B\\\mathbf B_S\end{bmatrix}\mathbf q.
```
Here `B_B` and `B_S` are the matrices obtained by differentiating the **same CUF displacement approximation** above. MITC replaces **only** the second group:

```math
\begin{bmatrix}\boldsymbol\varepsilon_B\\\bar{\boldsymbol\gamma}_S\end{bmatrix}
=\underbrace{\begin{bmatrix}\mathbf B_B\\\bar{\mathbf B}_S\end{bmatrix}}_{\bar{\mathbf B}}\mathbf q,
\qquad
\bar{\mathbf B}_S(\xi) = \sum_{m=1}^{n-1}\bar N_m(\xi)\mathbf B_S(\xi_m).
```
Consequently the stiffness of the beam is assembled using

```math
\mathbf K = \int_0^L\sum_{k=1}^{K}\int_{\Omega^k(x)}
\bar{\mathbf B}^{T}(x,y,z)\,\mathbf C^k(x,y,z)\,\bar{\mathbf B}(x,y,z)
\,d\Omega\,dx.
```
`K` is the global stiffness matrix and `C^k` comes from **CSF**, not from MITC. The section integral is evaluated over the **physical** domain supplied by CSF. The equation also makes clear that, for a general constitutive matrix, products involving both corrected shear and non-shear operators must be assembled consistently; one must not silently discard mixed constitutive terms.

**Important distinction:** MITC changes the **kinematic shear operator**, not the section's modulus, the constitutive coefficients, or the quadrature order of the complete stiffness integral. The paper uses full Gaussian integration for MITC. This benchmark uses isotropic material; it does not test arbitrary anisotropic shear/non-shear constitutive couplings.

## 5. How the model is configured: three distinct files

A [YAML file](https://yaml.org/spec/) is a human-readable, plain-text configuration file: it *declares data and choices*, rather than implementing numerical algorithms like a Python program. This benchmark keeps the physical model, physical problem, and structural approximation separate.

1. **CSF geometry/material - [`models/mitc_paper41_square_csf.yaml`](models/mitc_paper41_square_csf.yaml).** Defines the square sectional polygon and its physical coordinates, the two end stations, and the material information. This is where the section and material belong-not where the MITC choice belongs.
2. **Physical problem - [`problems/mitc_paper41_point.yaml`](problems/mitc_paper41_point.yaml).** Declares the beam model to load, the clamp at x=0, and the −z point load at x=L. The solver's Python **adapter** `csf.cuf.adapters.problem.c_section_cantilever_point_load` translates these physical conditions into the generalized force vector and constraints on the CUF unknowns. *Generalized* here means the physical load has been projected onto the transverse CUF functions and the longitudinal element functions; it is not a different physical force.
3. **CUF execution case - for example [`cases/mitc_paper41_L9_B2_on.yaml`](cases/mitc_paper41_L9_B2_on.yaml).** Connects model and problem, selects the transverse L9 functions implemented in [`expansions/lagrangeL9_v4.py`](expansions/lagrangeL9_v4.py), chooses the longitudinal element order, and sets quadrature, MITC mode and output location.

**Two distinct orders:** `longitudinal.order: 1`, `2`, or `3` is the polynomial degree of the *axial* element (B2, B3 or B4). In contrast, the selected [`lagrangeL9_v4.py`](expansions/lagrangeL9_v4.py) transverse plugin explicitly reports `order = 2` (`_L9_ORDER = 2`): its L9 shape functions are **quadratic in each natural transverse coordinate**, built from the three one-dimensional polynomials shown in Section 3. The case uses `cuf.order: 2` consistently with that transverse basis. This parameter is **not** the number of longitudinal nodes, and changing it does not turn a B2 into a B3. The L9 plugin fixes its implemented transverse polynomial family; changing this YAML value alone is not a substitute for choosing another transverse basis.

For each B2/B3/B4 pair, MITC ON and OFF share geometry, load and longitudinal element count. The intended comparison isolates the MITC shear treatment (and its verification/output settings). See [reproducibility.md](reproducibility.md) for the six case names, commands and expected outputs.

## 6. Tip displacement: comparison with Table 1

Table 1 of the paper prints `u_z × 10^5 m`; to obtain millimetres, multiply each printed number by **0.01**. The sampled displacement is **u_z at the free-end section center**, not the maximum displacement elsewhere.

| Element | MITC | Paper (mm) | CSF–CUF (mm) | Relative difference (%) |
|---|---|---:|---:|---:|
| B2 | OFF | -0.00139 | -0.00138837 | 0.1173 |
| B2 | ON | -0.03606 | -0.03605419 | 0.0161 |
| B3 | OFF | -0.03942 | -0.03942263 | 0.0067 |
| B3 | ON | -0.04663 | -0.04662469 | 0.0114 |
| B4 | OFF | -0.04950 | -0.04949878 | 0.0025 |
| B4 | ON | -0.04988 | -0.04988122 | 0.0024 |

The relative difference is calculated as `100 × |CSF–CUF − paper| / |paper|`, using the **rounded printed paper value**. It is **not** a discretization error relative to an exact 3D elasticity solution. The very small B2 OFF displacement illustrates the shear-locking problem; MITC ON substantially reduces it without adding longitudinal elements.

## 7. Shear-stress comparison: testing the assumed-strain recovery

The preceding displacement match does not, by itself, establish that shear stresses are recovered correctly. An ON checkpoint contains displacement coefficients, but **ordinary differentiation** of their field reconstructs *raw shear* `γ_S`, not necessarily MITC's **assumed shear** `\bar γ_S`.

### From the assumed shear strain to physical stress

In this benchmark the CSF geometry file [`models/mitc_paper41_square_csf.yaml`](models/mitc_paper41_square_csf.yaml) assigns `weight: 75000.0` (Young modulus in MPa) and declares the isotropic shear law `iso(0.33)`, where `0.33` is Poisson's ratio. **For this configured isotropic law** and for the independent post-processor, the shear modulus is

```math
G=\frac{E}{2(1+\nu)}=\frac{75000}{2(1+0.33)}\approx28195.49\ \mathrm{MPa}.
```

The stress follows from the MITC assumed shear strain, not from ordinary differentiation at the output node:

```math
\tau_{xz}=G\,\bar\gamma_{xz}.
```

Because strain is dimensionless, `G` in `N/mm^2` gives `tau_xz` in `N/mm^2` (MPa). The paper's scaled tabulation is then

```math
T_{\mathrm{paper}}=\frac{\tau_{xz}\;(\mathrm{Pa})}{10^4}=100\,\tau_{xz}\;(\mathrm{MPa}).
```

This relation is **specific to the isotropic benchmark**. CSF can represent the Young and shear properties through distinct carriers; one must not infer `G=E/[2(1+nu)]` for an arbitrary CSF material without an explicitly specified isotropic law.

The script [`recover_mitc_shear.py`](recover_mitc_shear.py) therefore (1) reads the archived displacement coefficients, (2) evaluates the CUF shear strain at the element's tying points, (3) interpolates with `\bar N_m`, and (4) applies the CSF shear constitutive coefficient to obtain the physical `τ_xz`. Samples are taken at the section center and each longitudinal node. See also [`paper41_shear_comparison.csv`](paper41_shear_comparison.csv).

The following stresses use the scaling of Table 1: **tabulated value = stress in Pa divided by 10⁴**.

**Why the tables are results rather than algebraic identities.** Section 6 values require the solved coefficients `q` (and thus the assembled stiffness, load and constraints); Section 7 additionally requires the same `q`, the sectional L9 functions and the MITC tying-point interpolation. The README makes these operations traceable; it does not claim the published numerical values follow from geometry alone. The six YAML cases and checkpoints in [`output/`](output/) provide the input and solved state, and [`reproducibility.md`](reproducibility.md) specifies the corresponding rerun and comparison steps.


| Element | Node | Paper (scaled) | CSF–CUF recovery (scaled) | Absolute difference |
|---|---:|---:|---:|---:|
| B2 | 1 | -1.029 | -1.029189 | 0.000189 |
| B2 | 2 | -1.029 | -1.029189 | 0.000189 |
| B3 | 1 | -1.094 | -1.093964 | 0.000036 |
| B3 | 2 | -0.996 | -0.995965 | 0.000035 |
| B3 | 3 | -0.898 | -0.897966 | 0.000034 |
| B4 | 1 | -1.228 | -1.228107 | 0.000107 |
| B4 | 2 | -0.982 | -0.982379 | 0.000379 |
| B4 | 3 | -0.939 | -0.938667 | 0.000333 |
| B4 | 4 | -1.097 | -1.096974 | 0.000026 |

The largest absolute difference is **0.000379 scaled units**, below **0.0005** (half the paper's last printed decimal unit). Notice that the two B2 MITC values are equal: that is exactly the constant assumed shear predicted by its one tying point in Section 4. The OFF shear values are also exported in the CSV for comparisons with the paper's *Full* rows.

**Reproducibility check:** regenerating the CSV from archived checkpoints and comparing the 18 shear samples to the archived CSV passed with absolute tolerance `1e-8`. This checks numerical repeatability of the **post-processing**; comparison with the paper is a **separate** validation check. Detailed commands belong in [reproducibility.md](reproducibility.md).

## 8. What the evidence supports-and what it does not

**Supported by this case:** for the *prismatic, isotropic, square cantilever with L9 transverse approximation*, CSF–CUF reproduces the paper's B2/B3/B4 displacements under full integration and MITC, and its nine published MITC nodal transverse-shear stress values under an explicitly defined assumed-strain recovery. Solver logs and archived checkpoints provide further reproducibility and numerical diagnostics.

**Not established by this case:** general validity for nonprismatic sections, variable materials, arbitrary loading, anisotropic constitutive coupling, every stiffness-matrix block, patch-test behaviour or the absence of spurious zero-energy modes. The shear post-processor uses archived displacements and the specified MITC tying-point rule; it does **not** constitute an independent line-by-line verification of element assembly.

This distinction matters: the benchmark provides a strong **published numerical reference check**, not a universal proof of the implementation.

## 9. Files and reproduction

- [`reproducibility.md`](reproducibility.md) - environment, Linux/Windows commands, and expected results.
- [`run_paper41.sh`](run_paper41.sh) - six solver runs (B2/B3/B4, MITC OFF/ON).
- [`models/`](models/) and [`problems/`](problems/) - physical section/material and physical loading/constraints.
- [`cases/`](cases/) and [`expansions/lagrangeL9_v4.py`](expansions/lagrangeL9_v4.py) - structural cases and transverse functions.
- [`output/`](output/) - archived `response.txt` and `.cuf.npz` checkpoints.
- [`logs/`](logs/) - solver logs for the six runs.
- [`recover_mitc_shear.py`](recover_mitc_shear.py) - shear recovery from checkpoints, without rerunning the solver.
- [`paper41_shear_comparison.csv`](paper41_shear_comparison.csv) - archived nodal shear comparison.

The core CSF–CUF solver is **not** included in the benchmark archive. To make a future rerun auditable, record the repository Git commit, Python environment and solver version, as described in the reproducibility guide.
