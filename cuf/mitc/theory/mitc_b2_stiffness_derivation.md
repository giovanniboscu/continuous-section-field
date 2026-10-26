# MITC–CUF B2: derivation of the stiffness nucleus and code correspondence

**Scope.** This is a study document, not a replacement for the [MITC overview](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/mitc) or the individual benchmark READMEs. It derives a two-node longitudinal element (B2), keeps the CSF sectional model separate from the CUF kinematics, and identifies the corresponding implementation operations. Equations use GitHub-compatible `math` fences.

## 1. Physical model (CSF) and unknowns (CUF)

Let the beam axis be `x`, with physical section coordinates `y,z`. At a given `x`, CSF supplies physical subdomains `Ω^k(x)` and constitutive matrices `C^k(x,y,z)`. The section integrals below use those **physical** domains; no variable-section *reference-to-physical* coordinate mapping is postulated here.

The transverse CUF basis is `F_τ(y,z)` for `τ = 1,...,M`. For this derivation, **assume no explicit dependence of `F_τ` on `x`**; the checked implementation contains additional `F_,x` terms for more general bases, which are excluded from the simple formulas below.

The displacement field on a two-node element is

```math
\mathbf u(x,y,z)=\sum_{\tau=1}^{M}F_\tau(y,z)\big[N_1(\xi(x))\mathbf q_{\tau1}+N_2(\xi(x))\mathbf q_{\tau2}\big].
```

Here each `q_{τi}` has three components `(q_{x,τi},q_{y,τi},q_{z,τi})`. The index `i=1,2` identifies the axial node, while `τ` identifies the *sectional* function. Nothing in B2 means there are only two transverse DOFs.

## 2. The B2 longitudinal mapping and its derivatives

The physical element runs from `x_a` to `x_b`, with `L_e = x_b − x_a > 0`, and natural coordinate `−1 ≤ ξ ≤ 1`:

```math
x(\xi)=\frac{x_a+x_b}{2}+\frac{L_e}{2}\xi,\qquad
J_x=\frac{dx}{d\xi}=\frac{L_e}{2},\qquad dx=J_x\,d\xi.
```

The linear Lagrange interpolation functions are

```math
N_1(\xi)=\frac{1-\xi}{2},\qquad N_2(\xi)=\frac{1+\xi}{2}.
```


By the chain rule,

```math
\frac{dN_i}{dx}
=
\frac{dN_i}{d\xi}
\frac{d\xi}{dx}
```

For a two-node B2 element with an affine longitudinal mapping,

```math
\frac{d\xi}{dx}=\frac{2}{L_e}
```

The longitudinal shape-function and derivative vectors are therefore

```math
\mathbf N(\xi)
=
\begin{bmatrix}
N_1(\xi) & N_2(\xi)
\end{bmatrix}
```

```math
\mathbf D
=
\begin{bmatrix}
-\frac{1}{L_e} & \frac{1}{L_e}
\end{bmatrix}
```



Thus `D` is constant, whereas `N(ξ)` varies linearly. `J_x` is the **longitudinal finite-element Jacobian**; it is not the CSF section-variation Jacobian.

## 3. Derive all six 3D strain components

The small-strain tensor is the symmetric displacement gradient. Using engineering shear strains, the Voigt ordering employed in `core/nucleus.py` is `(xx, yy, zz, yz, xz, xy)`:

```math
\boldsymbol\varepsilon_V=
\begin{bmatrix}
\varepsilon_{xx}&\varepsilon_{yy}&\varepsilon_{zz}&
\gamma_{yz}&\gamma_{xz}&\gamma_{xy}
\end{bmatrix}^{T}.
```

Explicitly,

```math
\begin{aligned}
\varepsilon_{xx}&=\partial_xu_x, &
\varepsilon_{yy}&=\partial_yu_y, &
\varepsilon_{zz}&=\partial_zu_z,\\
\gamma_{yz}&=\partial_zu_y+\partial_yu_z, &
\gamma_{xz}&=\partial_zu_x+\partial_xu_z, &
\gamma_{xy}&=\partial_yu_x+\partial_xu_y.
\end{aligned}
```

For every transverse function `F_τ`, define `F_y = ∂F_τ/∂y`, `F_z = ∂F_τ/∂z`. Substituting the CUF field and differentiating term by term yields, for axial node `i`, the strain operator acting on its **three-component** nodal vector:

```math
\mathbf B_{\tau i}^{\rm raw}(\xi,y,z)=
\begin{bmatrix}
F_\tau D_i&0&0\\
0&F_{\tau,y}N_i&0\\
0&0&F_{\tau,z}N_i\\
0&F_{\tau,z}N_i&F_{\tau,y}N_i\\
F_{\tau,z}N_i&0&F_\tau D_i\\
F_{\tau,y}N_i&F_\tau D_i&0
\end{bmatrix}.
```

The first four rows are left unchanged by the present MITC correction; the last two correspond to `γ_xz` and `γ_xy`. The total strain is the sum of `B_{τi} q_{τi}` over `τ,i`.

## 4. Why B2 locking occurs: a minimal kinematic example

For a bending displacement of the illustrative form `u_z(x)=w(x)` and a section rotation represented by `u_x(x,z)=−z θ(x)`, the transverse shear strain is

```math
\gamma_{xz}=w'(x)-\theta(x).
```

For a shear-free Euler–Bernoulli bending field, `θ(x)=w'(x)`. But when both `w` and `θ` are approximated independently by **linear B2** interpolation, `w'` is constant while `θ(x)` is linear. Unless `θ` is constant, the identity cannot hold at **every** position. The residual shear adds an artificial positive energy term when evaluated conventionally. This simple example explains the mechanism, rather than proving a general theorem for every CUF expansion.

## 5. MITC tying point and exact B2 assumed shear

In the checked implementation, `LongitudinalTyingPointSelector.points(criterion="barlow", longitudinal_degree=1)` returns the one-point Gauss–Legendre location

```math
\xi_T=0.
```

The assumed-shear interpolation through a **single** tying point is the constant shape function `\bar N_1(ξ)=1`. Evaluating both factors of each shear row at the tying point gives

```math
\widetilde{\mathbf N}=\mathbf N(0)=\begin{bmatrix}1/2&1/2\end{bmatrix},\qquad
\widetilde{\mathbf D}=\mathbf D=\begin{bmatrix}-1/L_e&1/L_e\end{bmatrix}.
```

Therefore, for node `i` and transverse function `τ`, replace the **shear rows only** by

```math
\begin{aligned}
\overline B_{xz,\tau i}&=\begin{bmatrix}F_{\tau,z}\widetilde N_i&0&F_\tau\widetilde D_i\end{bmatrix},\\
\overline B_{xy,\tau i}&=\begin{bmatrix}F_{\tau,y}\widetilde N_i&F_\tau\widetilde D_i&0\end{bmatrix}.
\end{aligned}
```

The fully corrected six-row matrix is thus

```math
\overline{\mathbf B}_{\tau i}(\xi,y,z)=
\begin{bmatrix}
F_\tau D_i&0&0\\
0&F_{\tau,y}N_i&0\\
0&0&F_{\tau,z}N_i\\
0&F_{\tau,z}N_i&F_{\tau,y}N_i\\
F_{\tau,z}\widetilde N_i&0&F_\tau\widetilde D_i\\
F_{\tau,y}\widetilde N_i&F_\tau\widetilde D_i&0
\end{bmatrix}.
```

Note the subtlety: for B2, `D` is **already constant**, so `\widetilde D=D`. The change in the pure-shear rows is principally the replacement of `N_i(ξ)` by `1/2`. The shear/non-shear constitutive cross products are still modified because one side of their product changes.

## 6. Sectional coefficients and the elementary stiffness nucleus

Use the constitutive relation `σ_V = C^k ε_V`, with `C^k` a general symmetric 6-by-6 matrix in the same Voigt ordering. To make the two distinct integration operations explicit, define

```math
\mathbf K_{\tau i,sj}^{(e)}
=\int_{x_a}^{x_b}\sum_{k=1}^{K}\int_{\Omega^k(x)}
\overline{\mathbf B}_{\tau i}^{T}(x,y,z)
\mathbf C^k(x,y,z)
\overline{\mathbf B}_{sj}(x,y,z)
\,d\Omega\,dx.
```

Each such `K_{τi,sj}` is a **3-by-3** component block, because it couples three displacement components at test index `(τ,i)` to three at trial index `(s,j)`. Collecting `i,j=1,2` gives a **6-by-6** block for one transverse pair `(τ,s)`; all `M×M` transverse pairs are then scattered into the full elemental stiffness. The implementation loops the component blocks in the alternative but equivalent ordering `(test_component, trial_component)` with 2-by-2 axial matrices.

For an explicit match to `J_batch`, let `a` and `b` index the six Voigt strain rows, and let `r` and `t` denote transverse derivative choices (`none`, `y`, `z`). Define the sectional coefficient

```math
J_{\tau r,st}^{ab}(x)=\sum_{k=1}^{K}\int_{\Omega^k(x)}
F_{\tau,r}(y,z)\,C_{ab}^{k}(x,y,z)\,F_{s,t}(y,z)
\,d\Omega,
```

where `F_{τ,none}=F_τ`, `F_{τ,y}=∂_yF_τ`, and `F_{τ,z}=∂_zF_τ`. `J` contains sectional geometry, constitutive coefficients and transverse-function factors; it does **not** contain the B2 functions `N_i`, `D_i` or their MITC counterparts.

For one contribution with test Voigt row `a`, trial Voigt row `b`, test axial derivative order `p∈{0,1}` and trial order `q∈{0,1}`, write

```math
K_{\tau i,sj}^{(e),abpq}
=\int_{x_a}^{x_b} J_{\tau r,st}^{ab}(x)
\,L_i^{(p,a)}(x)L_j^{(q,b)}(x)\,dx,
```

where the longitudinal factor is **selected by the strain row**:

```math
L_i^{(p,a)}(x)=
\begin{cases}
\widetilde N_i & a\in\{5,6\},\ p=0,\\
\widetilde D_i & a\in\{5,6\},\ p=1,\\
N_i(\xi(x))&a\notin\{5,6\},\ p=0,\\
D_i&a\notin\{5,6\},\ p=1.
\end{cases}
```

The complete 3-by-3 component blocks are the sums of all kinematic/Voigt pairs that contribute to the corresponding displacement components. This formalizes how **mixed** (`a` shear, `b` non-shear or vice versa) contributions are retained: each factor uses its own rule.

### Example: a single shear-shear contribution

Take test and trial `γ_xz` contributions arising from the `u_x` component. They both use `F_,z` and an undifferentiated axial function. Their sectional coefficient is `J_{τz,sz}^{55}(x)`, and their element entry is

```math
K_{xx,\tau i,sj}^{(55)}
=\int_{x_a}^{x_b}J_{\tau z,sz}^{55}(x)
\widetilde N_i\widetilde N_j\,dx.
```

For B2, every factor `\widetilde N_i\widetilde N_j=1/4`, so for a **constant** sectional coefficient `J^{55}` the 2-by-2 matrix is

```math
\mathbf K_{xx,\tau s}^{(55)}=
\frac{L_eJ_{\tau z,sz}^{55}}4
\begin{bmatrix}1&1\\1&1\end{bmatrix}.
```

With ordinary full-integration strain interpolation, that same isolated contribution is instead

```math
\mathbf K_{xx,\tau s}^{(55),\mathrm{raw}}=
\frac{L_eJ_{\tau z,sz}^{55}}6
\begin{bmatrix}2&1\\1&2\end{bmatrix}.
```

These matrices are **one contribution** to a block, not the complete elemental stiffness. They illustrate algebraically what MITC changes for B2.

### Example: shear/non-shear coupling

Suppose a constitutive coefficient `C_{51}` is nonzero (general anisotropy). The `γ_xz` test contribution from `u_x` and the `ε_xx` trial contribution from `u_x` produce

```math
K_{xx,\tau i,sj}^{(51)}=
\int_{x_a}^{x_b}J_{\tau z,s}^{51}(x)
\widetilde N_iD_j\,dx.
```

This term is **not** dropped by MITC; only its shear-side longitudinal factor is replaced. For the isotropic square-beam benchmark this specific constitutive coupling is zero, so that benchmark cannot validate its numerical handling.

## 7. From continuous integrals to the actual quadrature

For the longitudinal Gauss points `ξ_g` and weights `w_g`, with physical `x_g=x(ξ_g)`, the implementation accumulates

```math
\mathbf K_{\tau s,cd}^{(e)}
\approx\sum_g w_gJ_x\sum_{\ell\in\mathcal T_{\tau s,cd}}
J_{\ell}(x_g)
\big[\mathbf l_{\ell}^{\rm test}(\xi_g)\otimes
\mathbf l_{\ell}^{\rm trial}(\xi_g)\big],
```

where `c,d` are displacement components `x,y,z`, and `\mathcal T_{τs,cd}` is the list of contributing nucleus terms supplied by `K_block_structure`. Each `J_ℓ(x_g)` is computed by `J_batch` through sectional integration. The tensor/outer product is a **2-by-2 matrix** of B2 axial-node factors for each component pair.

Full longitudinal Gauss integration is used: **MITC is not a request to reduce the number of Gauss integration points.** The Gauss count and sectional quadrature settings are controlled separately by the case configuration. Exact numerical values of quadrature orders should be read from the specific YAML and corresponding solver log, not assumed from the derivation.

## 8. Exact code correspondence in the inspected snapshot

| Mathematical operation | Inspected implementation | What it performs |
|---|---|---|
| Define the six 3D Voigt kinematic rows | `cuf/core/nucleus.py`, `FundamentalNucleusProvider._STRAIN_KINEMATICS` | Rows 1–6, including `γ_xz` = row 5 and `γ_xy` = row 6 |
| Enumerate weak-form terms | `FundamentalNucleusProvider.K_block_structure(...)` | Gives the `JSignature` and axial derivative orders for each component block |
| Set B2 tying point | `cuf/solver/longitudinal_tying_points.py`, `LongitudinalTyingPointSelector` | `barlow` uses Gauss–Legendre points, hence `[0]` for degree 1 |
| Sample `N` and `dN/dx` at tying point | `cuf/solver/element.py`, `_longitudinal_product_data` | Stores sample arrays for derivative orders 0 and 1 |
| Interpolate tying-point samples at quadrature point | `_longitudinal_product_data` | Computes `modified = weights @ values` |
| Keep ordinary and shear-modified test/trial factors separate | `_longitudinal_product_data` | Indexes products by `(test_shear,trial_shear,test_order,trial_order)` |
| Integrate sectional coefficients at each `x_g` | `_build_pair_batched` | Calls `sectional.J_batch(x=x, signatures=...)` |
| Select which test/trial side is MITC-corrected | `_build_pair_batched` | Uses `signature.m in (5,6)` and `signature.n in (5,6)` |
| Accumulate stiffness blocks | `_build_pair_batched` | Adds `scale * coefficient * shape_products[product_key]` for every term |
| Assemble global matrix | `cuf/solver/assembly.py` | Scatters local component-pair blocks into global DOFs |

The crucial branch from `element.py`, abbreviated without changing its meaning, is:

```python
product_key = (
    definition.signature.m in (5, 6),
    definition.signature.n in (5, 6),
    definition.test_x_order,
    definition.trial_x_order,
)
matrix += scale * coefficient * shape_products[product_key]
```

Here `scale = w_g J_x`; `coefficient = J_ℓ(x_g)`; and `shape_products[product_key]` is exactly the two-node outer product described in Section 7. When MITC is OFF the code chooses the unmodified pair `(test_x_order, trial_x_order)`.

## 9. What was demonstrated, and what still needs separate testing

**Derived here:** the B2 kinematics, exact one-point assumed shear interpolation, a complete 6-row MITC strain operator for a section basis independent of `x`, weak-form stiffness, its sectional `J` factorization, two illustrative stiffness entries and its code-selection mechanism.

**Checked against code structure:** the six Voigt rows, tying selector, corrected/uncorrected test/trial products, sectional `J_batch` call, and Gaussian accumulation. This is a **structural code correspondence**, not a term-by-term numerical equality test of all assembled matrices.

**Not established by this document:** detailed integration implementation for every CSF polygon, all domain-interface connectivity rules, nonlinear/geometrically exact behavior, arbitrary longitudinally varying transverse bases `F(x,y,z)`, general anisotropic material validation, or proof of absence of zero-energy modes. A numerical test that directly compares selected 2-by-2 nucleus entries against an independently evaluated quadrature would be the next level of verification.

**Recommended exercise.** Take a single B2 element with one transverse function pair `(τ,s)`. Print its nine `2×2` component matrices (MITC OFF and ON) from `build_pair`; independently evaluate the corresponding `J` values at the longitudinal Gauss points; reconstruct all term contributions using the formula in Section 7; compare block by block. This checks algebra, code mapping and the role of CSF without relying only on final deflections.
