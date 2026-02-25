# Stepwise Mass-Modified Cantilever Beam

## Pre-Solver Physical Model Dataset (Reproducible Reference Case)

------------------------------------------------------------------------

## Reference Publication

Gillich, G.-R., Praisach, Z.-I., Abdel Wahab, M., Gillich, N.,\
Mituletu, I. C., & Nitescu, C. (2016).\
**Free Vibration of a Perfectly Clamped-Free Beam with Stepwise
Eccentric Distributed Masses.**\
*Shock and Vibration*, 2016, Article ID 2086274.

This repository reconstructs the physical input data used in the paper
in a clean, solver-independent format.

No original figures or text are reproduced.

------------------------------------------------------------------------

# 1. Physical Beam Model

## 1.1 Geometry (Uniform Along z)

-   Length: `L = 1.0 m`
-   Width: `B = 50 mm = 0.050 m`
-   Thickness: `H = 5 mm = 0.005 m`

Derived quantities:

-   Cross-sectional area\
    `A = B·H = 2.50 × 10⁻⁴ m²`

-   Second moment of area\
    `I = B·H³ / 12 = 5.208333 × 10⁻¹⁰ m⁴`

------------------------------------------------------------------------

## 1.2 Elastic Properties (Uniform)

-   Young's modulus: `E = 2.0 × 10¹¹ N/m²`
-   Poisson ratio: `ν = 0.3`
-   Base density: `ρ₀ = 7850 kg/m³`

Derived:

-   Base linear mass density\
    `μ₀ = ρ₀ · A = 1.9625 kg/m`

------------------------------------------------------------------------

# 2. Mass Distribution Model

The beam geometry and stiffness remain constant.

Only the density is modified locally.

Linear mass density:

    μ(z) = ρ(z) · A

Stepwise density definition:

    ρ(z) = ρ₀        outside modified segment
    ρ(z) = ρ_R       inside segment [a,b]

Thus:

    μ(z) = μ₀        outside [a,b]
    μ(z) = μ_R       inside [a,b]

where:

    μ_R = ρ_R · A

------------------------------------------------------------------------

# 3. Extended Region Scenarios (Table 1 Equivalent)

  Scenario   ρ_R (kg/m³)   a (mm)   b (mm)   ΔL (mm)   μ_R (kg/m)
  ---------- ------------- -------- -------- --------- ------------
  A          4000          300      400      100       1.000
  B          10000         300      400      100       2.500
  C          12000         600      650      50        3.000
  D          2000          700      750      50        0.500
  E          14000         500      550      50        3.500
  F          3000          800      850      50        0.750

Segment coordinates in meters:

    [a,b] = [a/1000 , b/1000]

------------------------------------------------------------------------

# 4. Narrow Region Scenarios (Table 2 Equivalent)

  Scenario   ρ_R (kg/m³)   a (mm)   b (mm)   ΔL (mm)   μ_R (kg/m)
  ---------- ------------- -------- -------- --------- ------------
  G          4000          100      110      10        1.000
  H          10000         100      110      10        2.500
  I          12000         150      160      10        3.000
  J          2000          150      160      10        0.500
  K          14000         200      210      10        3.500
  L          3000          200      210      10        0.750

------------------------------------------------------------------------

# 5. Boundary Condition (Physical Problem Definition)

-   Left end: clamped
-   Right end: free

------------------------------------------------------------------------

# 6. Minimal Reproducible Pre-Solver Dataset

For each scenario the complete physical definition is:

### Constants

-   `L`
-   `A`
-   `I`
-   `E`
-   `ρ₀`
-   `μ₀`

### Scenario parameters

-   `a`
-   `b`
-   `ρ_R`
-   `μ_R = ρ_R · A`

From these values the fields:

    ρ(z)
    μ(z)
    EI

are fully determined and unambiguous.

No FEM discretization or numerical scheme is required at this stage.

------------------------------------------------------------------------

# 7. Scope of This Repository

This dataset provides:

-   A clean physical model
-   A solver-independent representation
-   A reproducible reference case
-   A base for continuous modeling (e.g., CSF implementations)

It does not reproduce: - Analytical derivations - Original figures -
Numerical FEM settings

------------------------------------------------------------------------

# 8. Intended Use

This material may be used for:

-   Independent verification
-   Alternative implementations
-   Continuous mass-variation extensions
-   CSF-based modeling workflows

When used in academic or technical work, the original publication must
be cited.

------------------------------------------------------------------------

# CSF Extension of Scenario A -- Stepwise vs. Smoothed Mass Distribution

## Reference Case

Gillich et al. (2016) define Scenario A as a cantilever beam with:

-   Uniform geometry along the span
-   Constant stiffness (E constant)
-   A stepwise density variation in the segment \[a, b\]
-   ρ₀ = 7850 kg/m³
-   ρ_R = 4000 kg/m³
-   a = 0.30 m
-   b = 0.40 m

The paper assumes a discontinuous density field:

    ρ(z) = ρ₀        outside [a, b]
    ρ(z) = ρ_R       inside  [a, b]

This produces a sharp mass jump.

------------------------------------------------------------------------

## CSF Two-Step Modeling Strategy

### 1) Geometric Field (Independent of Mass)

Uniform rectangular section:

-   B = 0.050 m
-   H = 0.005 m
-   A = B·H = 2.5e-4 m²
-   Ix = B·H³ / 12 = 5.2083e-10 m⁴
-   Iy = 5.2083e-8 m⁴

These remain constant along z.

Therefore:

    A(z) = constant
    I(z) = constant
    EI(z) = constant

No stiffness modification is introduced.

------------------------------------------------------------------------

### 2) Weight Field (Mass Scaling)

In CSF, density variation is introduced through a per-polygon weight:

    w(z) = ρ(z) / ρ₀

For Scenario A:

    r = ρ_R / ρ₀ = 4000 / 7850 = 0.509554

Instead of a discontinuous step, a smooth transition was used:

    w(t) = 1 + (r - 1) * 0.5 * (tanh((t - a)/s) - tanh((t - b)/s))

with: - t = z / L - a = 0.30 - b = 0.40 - s = 0.005

This preserves: - plateau value w ≈ r inside the segment - w ≈ 1
outside - smooth transitions at the boundaries

------------------------------------------------------------------------

## Interpretation of Results

### Effective Area Printout

When printing A·w(z):

-   At z = 0.35 (inside region):

    A_eff = A \* r = 2.5e-4 \* 0.509554 = 1.273885e-4 m²

This matches the numerical output (0.00012739 m²).

-   Outside the region:

    A_eff = 2.5e-4 m²

Thus the CSF output is consistent with the expected mass scaling.

------------------------------------------------------------------------

## Correspondence with the Paper

The geometric and physical parameters match exactly those defined in the
publication.

Differences:

| Aspect | Paper | CSF Example |
|---|---|---|
| Density definition ρ(z) | Stepwise (sharp jump) | Smoothed transition (continuous) |
| Continuity | Discontinuous | Continuous |
| Interface at [a,b] | Ideal abrupt interface | Finite transition width `s` |
| Scenario parameters | `ρ0, ρR, a, b` | `ρ0, ρR, a, b` + `s` |
| Geometry | Unchanged | Unchanged |
| Stiffness (E, EI) | Unchanged | Unchanged |
The smoothed formulation:

-   Does not alter geometry
-   Does not alter stiffness
-   Preserves the same limiting values ρ₀ and ρ_R
-   Introduces one additional modeling parameter (s)

Therefore, the CSF implementation:

-   Reproduces the physical definition of Scenario A
-   Extends it to a continuous density field
-   Demonstrates how the stepwise simplification of the paper can be
    generalized

------------------------------------------------------------------------

## Modeling Significance

The example shows that CSF:

1.  Separates geometry from material/mass scaling
2.  Allows exact reproduction of discrete reference cases
3.  Naturally extends them to continuous distributions without modifying
    stiffness

This confirms full pre-solver consistency with the published dataset
while enabling more general mass-field modeling.

