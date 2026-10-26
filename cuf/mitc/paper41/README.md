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

$$
\mathcal S(x) = \{\Omega^k(x),\,\mathbf C^k(x,y,z)\}_{k=1}^{K},
$$

where `k` identifies a sectional material/domain, `K` is the number of domains, `Ω^k(x)` is its physical area at x, and `C^k(x,y,z)` is its constitutive matrix (the relation between strain and stress at that point). Here there is just **one square domain with constant isotropic material**. The same CSF description is supplied at the two end stations; no taper or longitudinal material variation is introduced.

The model uses actual cross-sectional coordinates in millimetres. It does **not** use a longitudinally varying reference-to-physical sectional mapping to represent the section; thus no *such mapping Jacobian* is needed. Numerical quadrature in a polygon or subdomain may still use its own local integration mapping: that is a different matter.

CSF answers **what physical section and material are present at x**. It does not decide the displacement approximation, number of longitudinal nodes, or MITC tying points. Those belong to CUF and its element formulation.

For the general variable-section mathematics, see [CSF–CUF variable-section formulation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md).

## 3. CUF: from the section to structural unknowns

**CUF (Carrera Unified Formulation)** approximates the three-component displacement field using functions over the cross-section. At a physical point (x,y,z):

$$
\mathbf u(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,\mathbf u_\tau(x).
$$

Here `u = (u_x,u_y,u_z)^T` is the displacement vector; `F_τ(y,z)` is the τ-th transverse expansion function; `M` is the number of transverse functions; and `u_τ(x)` is the associated **three-component, still-unknown** axial displacement function. In this benchmark the transverse functions are supplied by the L9 expansion.

One longitudinal finite element then interpolates each `u_τ(x)`:

$$
\mathbf u_\tau(x) = \sum_{i=1}^{n} N_i(\xi(x))\,\mathbf q_{\tau i},
$$

where `n` is the number of longitudinal nodes, `N_i` their shape functions on the element, `ξ` its local axial coordinate, and `q_{τi}` the three displacement unknowns associated with transverse function τ and longitudinal node i. Substituting this equation **into the preceding CUF expansion** gives the actual finite-element displacement approximation:

$$
\boxed{\mathbf u(x,y,z) = \sum_{\tau=1}^{M}\sum_{i=1}^{n} F_\tau(y,z)N_i(\xi(x))\,\mathbf q_{\tau i}.}
$$

The six runs use **one element**, with `n=2` (B2, linear), `n=3` (B3, quadratic), or `n=4` (B4, cubic). Changing B2→B3→B4 changes the *polynomial order of the same single element*, not the number of elements or the CSF section.


### Where the transverse shear strain comes from

Consider the transverse shear strain in the physical **x-z** plane. In small-strain elasticity, the engineering shear strain is


```math
\gamma_{xz} = \frac{\partial u_z}{\partial x} + \frac{\partial u_x}{\partial z}
```



**Step 1 - Write the two displacement components.** Taking the x- and z-components of the CUF finite-element displacement field from Section 3 gives

$$
\begin{aligned}
u_z(x,y,z)
&= \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,N_i(\xi(x))\,q_{z,\tau i}, \\
u_x(x,y,z)
&= \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,N_i(\xi(x))\,q_{x,\tau i}.
\end{aligned}
$$

The coefficients `q_{z,τi}` and `q_{x,τi}` are the z- and x-components of the nodal unknown vector `q_{τi}`. They are independent of the spatial coordinates when differentiating the interpolated field.

**Step 2 - Differentiate each component.** The transverse functions `F_τ(y,z)` do not depend on x, while the longitudinal functions `N_i(ξ(x))` do not depend on z. Consequently,

$$
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
$$

Substituting these **two derivatives into the small-strain definition** gives

$$
\begin{aligned}
\gamma_{xz}(x,y,z)
={}& \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,
\frac{dN_i(\xi(x))}{dx}\,q_{z,\tau i} \\
&+ \sum_{\tau=1}^{M}\sum_{i=1}^{n}
\frac{\partial F_\tau(y,z)}{\partial z}\,
N_i(\xi(x))\,q_{x,\tau i}.
\end{aligned}
$$

**Step 3 - Convert the longitudinal derivative to the natural coordinate.** The element shape functions are defined in `ξ`, not directly in the physical axial coordinate `x`. The chain rule is therefore

$$
\frac{dN_i(\xi(x))}{dx}
= \frac{dN_i}{d\xi}\,\frac{d\xi}{dx}.
$$

For the **straight, affine longitudinal element used in this benchmark**, let `x_a` and `x_b` denote its physical endpoints and `L_e=x_b-x_a` its length. With `-1 <= ξ <= 1`,

$$
\begin{aligned}
x(\xi) &= \frac{x_a+x_b}{2}+\frac{L_e}{2}\,\xi, \\
J_x &= \frac{dx}{d\xi}=\frac{L_e}{2}, \\
\frac{d\xi}{dx} &= \frac{1}{J_x}=\frac{2}{L_e}.
\end{aligned}
$$

Thus,

$$
\frac{dN_i(\xi(x))}{dx}
= \frac{2}{L_e}\,\frac{dN_i}{d\xi}.
$$

**Step 4 - Obtain the shear strain evaluated by the ordinary CUF operator.** Substituting the chain-rule result into the expression from Step 2 yields

$$
\begin{aligned}
\gamma_{xz}(x,y,z)
={}& \sum_{\tau=1}^{M}\sum_{i=1}^{n}
F_\tau(y,z)\,\frac{2}{L_e}\,
\frac{dN_i}{d\xi}\,q_{z,\tau i} \\
&+ \sum_{\tau=1}^{M}\sum_{i=1}^{n}
\frac{\partial F_\tau(y,z)}{\partial z}\,
N_i(\xi(x))\,q_{x,\tau i}.
\end{aligned}
$$

Both `N_i` and `dN_i/dξ` in this last expression are evaluated at `ξ=ξ(x)`. For a non-affine longitudinal mapping, the general factor `1/J_x(ξ)` replaces `2/L_e`.

The other transverse shear component follows from the same steps, exchanging z with y:


```math
\gamma_{xy} = \frac{\partial u_y}{\partial x} + \frac{\partial u_x}{\partial y}
```


**Keep the two geometrical roles separate.** The longitudinal Jacobian `J_x=dx/dξ` belongs to the one-dimensional finite-element interpolation and its change of integration coordinate. It is **not** a reference-to-physical *cross-sectional* mapping Jacobian. CSF continues to supply the sectional domains directly in physical `(y,z)` coordinates; the longitudinal Jacobian does not transform those domains.

These are the two ordinary transverse shear-strain components subsequently modified by MITC at selected longitudinal tying points (Section 4).

## 4. MITC: change the shear interpolation, not the material

### Why correct the shear strain?

With an ordinary displacement finite element, all strains follow from the field just derived. In a bending-dominated slender beam, that interpolation can introduce excessive artificial shear stiffness (*shear locking*), making a computed deflection much too small. MITC (*Mixed Interpolation of Tensorial Components*) keeps **the same displacement unknowns** `q_{τi}`, but replaces the *longitudinal interpolation of transverse shear strain*.

For either shear component, first evaluate its ordinary CUF strain `γ_S(ξ_m,y,z)` at selected local axial positions `ξ_m`, called **tying points**. Then interpolate those samples along the element:

$$
\bar{\boldsymbol\gamma}_S(\xi,y,z)
= \sum_{m=1}^{n-1} \bar N_m(\xi)\,\boldsymbol\gamma_S(\xi_m,y,z).
$$

Here `γ_S = (γ_xy, γ_xz)^T`, `n` is the number of longitudinal nodes already defined, and `\bar N_m` are the interpolation functions through the `n−1` tying points. The overbar means **assumed/interpolated shear**, not a changed displacement field.

| Axial element | Nodal displacement interpolation | Shear tying points | Assumed shear order |
|---|---|---:|---|
| B2 | Linear (2 nodes) | 1 | Constant |
| B3 | Quadratic (3 nodes) | 2 | Linear |
| B4 | Cubic (4 nodes) | 3 | Quadratic |

For B2, with one tying point at the element center, the formula reduces immediately to `\bar γ_S(ξ)=γ_S(0)`: **the assumed shear is constant along that element**. This predicts equal recovered MITC shear at its two axial nodes-a feature directly testable against Table 1.

### How the correction enters stiffness

Collect all displacement unknowns into one vector `q`. The ordinary infinitesimal strains can be grouped into non-shear (`ε_B`) and transverse-shear (`γ_S`) parts:

$$
\begin{bmatrix}\boldsymbol\varepsilon_B\\\boldsymbol\gamma_S\end{bmatrix}
=\begin{bmatrix}\mathbf B_B\\\mathbf B_S\end{bmatrix}\mathbf q.
$$

Here `B_B` and `B_S` are the matrices obtained by differentiating the **same CUF displacement approximation** above. MITC replaces **only** the second group:

$$
\begin{bmatrix}\boldsymbol\varepsilon_B\\\bar{\boldsymbol\gamma}_S\end{bmatrix}
=\underbrace{\begin{bmatrix}\mathbf B_B\\\bar{\mathbf B}_S\end{bmatrix}}_{\bar{\mathbf B}}\mathbf q,
\qquad
\bar{\mathbf B}_S(\xi) = \sum_{m=1}^{n-1}\bar N_m(\xi)\mathbf B_S(\xi_m).
$$

Consequently the stiffness of the beam is assembled using

$$
\mathbf K = \int_0^L\sum_{k=1}^{K}\int_{\Omega^k(x)}
\bar{\mathbf B}^{T}(x,y,z)\,\mathbf C^k(x,y,z)\,\bar{\mathbf B}(x,y,z)
\,d\Omega\,dx.
$$

`K` is the global stiffness matrix and `C^k` comes from **CSF**, not from MITC. The section integral is evaluated over the **physical** domain supplied by CSF. The equation also makes clear that, for a general constitutive matrix, products involving both corrected shear and non-shear operators must be assembled consistently; one must not silently discard mixed constitutive terms.

**Important distinction:** MITC changes the **kinematic shear operator**, not the section's modulus, the constitutive coefficients, or the quadrature order of the complete stiffness integral. The paper uses full Gaussian integration for MITC. This benchmark uses isotropic material; it does not test arbitrary anisotropic shear/non-shear constitutive couplings.

## 5. How the model is configured: three distinct files

A [YAML file](https://yaml.org/spec/) is a human-readable, plain-text configuration file: it *declares data and choices*, rather than implementing numerical algorithms like a Python program. This benchmark keeps the physical model, physical problem, and structural approximation separate.

1. **CSF geometry/material - [`models/mitc_paper41_square_csf.yaml`](models/mitc_paper41_square_csf.yaml).** Defines the square sectional polygon and its physical coordinates, the two end stations, and the material information. This is where the section and material belong-not where the MITC choice belongs.
2. **Physical problem - [`problems/mitc_paper41_point.yaml`](problems/mitc_paper41_point.yaml).** Declares the beam model to load, the clamp at x=0, and the −z point load at x=L. The solver's Python **adapter** `csf.cuf.adapters.problem.c_section_cantilever_point_load` translates these physical conditions into the generalized force vector and constraints on the CUF unknowns. *Generalized* here means the physical load has been projected onto the transverse CUF functions and the longitudinal element functions; it is not a different physical force.
3. **CUF execution case - for example [`cases/mitc_paper41_L9_B2_on.yaml`](cases/mitc_paper41_L9_B2_on.yaml).** Connects model and problem, selects the transverse L9 functions implemented in [`expansions/lagrangeL9_v4.py`](expansions/lagrangeL9_v4.py), chooses the longitudinal element order, and sets quadrature, MITC mode and output location.

**Two distinct orders:** `longitudinal.order: 1`, `2`, or `3` denotes the polynomial degree of B2, B3, or B4; the case's `cuf.order: 2` controls a *different, transverse expansion setting*. Do not interpret it as the number of longitudinal nodes.

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

The script [`recover_mitc_shear.py`](recover_mitc_shear.py) therefore (1) reads the archived displacement coefficients, (2) evaluates the CUF shear strain at the element's tying points, (3) interpolates with `\bar N_m`, and (4) applies the CSF shear constitutive coefficient to obtain the physical `τ_xz`. Samples are taken at the section center and each longitudinal node. See also [`paper41_shear_comparison.csv`](paper41_shear_comparison.csv).

The following stresses use the scaling of Table 1: **tabulated value = stress in Pa divided by 10⁴**.

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
