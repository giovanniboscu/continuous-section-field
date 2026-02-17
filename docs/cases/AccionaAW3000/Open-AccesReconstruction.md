# Technical Dossier (Open-Access Reconstruction)
## Axially Functionally Graded Tapered Bernoulli–Euler Microbeams under MCST
### Reference target: Akgöz & Civalek (2013), *International Journal of Engineering Science*, DOI: 10.1016/j.ijengsci.2013.04.009

---

## 1) Purpose of this dossier

This document provides a **high-detail, implementation-ready technical reconstruction** of the methodology and benchmark logic associated with:

- **B. Akgöz**
- **Ö. Civalek**
- **“Free vibration analysis of axially functionally graded tapered Bernoulli–Euler microbeams based on the modified couple stress theory”**
- *International Journal of Engineering Science* (2013)
- DOI: `10.1016/j.ijengsci.2013.04.009`

The original full text may be inaccessible behind a paywall.  
This dossier is built from:
1. Official bibliographic/abstract-level metadata for the original article.
2. Open-access papers and reviews that cite or replicate the same modeling family (AFG + taper + MCST + Ritz/FEM workflows).
3. Standard continuum-mechanics formulations consistent with Bernoulli–Euler beam theory and modified couple stress enrichment.

The result is intended as a **practical benchmark blueprint** for CSF-style workflows and for independent verification studies.

---

## 2) Confirmed bibliographic identity

- Journal record exists on Elsevier/ScienceDirect.
- Citation identity matches:
  - Akgöz, B.; Civalek, Ö.
  - IJES, 2013
  - DOI: `10.1016/j.ijengsci.2013.04.009`

---

## 3) Why this paper is structurally important

This line of work demonstrates that when **material stiffness varies along the beam axis** (`E = E(x)`), and geometry is also tapered (`A(x), I(x)` variable), the dynamic and stability behavior departs strongly from constant-property textbook solutions.  
When **Modified Couple Stress Theory (MCST)** is included, an internal material length parameter introduces **size-dependent stiffening**, especially relevant at micro-scale.

### Practical implication for engineering modeling
Compared to classical beam formulas:
- Natural frequencies are shifted.
- Buckling loads shift.
- Mode shape distribution is altered.
- Sensitivity to property law shape (`linear`, `exponential`, etc.) becomes non-negligible.

This is exactly the kind of parametric dependence that CSF users want to represent with explicit laws along `z`.

---

## 4) Core physical model (reconstructed)

## 4.1 Kinematics: Bernoulli–Euler beam

For transverse deflection `w(x,t)`:

- Plane sections remain plane.
- Shear deformation neglected.
- Rotation `theta(x,t) = dw/dx`.

Classical curvature:
- `kappa(x,t) = d2w/dx2`.

---

## 4.2 Axially graded material fields

In axial FG beams, material properties vary along `x`:

- `E = E(x)` (Young’s modulus)
- `rho = rho(x)` (mass density)

A common normalized exponential law used in the literature:

```text
E(x) = E0 + (EL - E0) * (exp(alpha*x/L) - 1) / (exp(alpha) - 1)
rho(x) = rho0 + (rhoL - rho0) * (exp(alpha*x/L) - 1) / (exp(alpha) - 1)
```

Where:
- `L` = beam length
- `x in [0, L]`
- `alpha` controls how strongly and where variation is concentrated.

Special cases:
- `alpha -> 0` gives approximately linear variation.
- `E0 = EL` gives homogeneous stiffness (in material sense).

---

## 4.3 Tapered geometry (rectangular example)

Typical parametric taper:

```text
b(x) = b0 * (1 - Cb*x/L)
h(x) = h0 * (1 - Ch*x/L)
A(x) = b(x)*h(x)
I(x) = b(x)*h(x)^3/12
```

Constraints:
- `0 <= Cb < 1`
- `0 <= Ch < 1`
- Keep `b(x) > 0`, `h(x) > 0` for all `x`.

Because `I ~ h^3`, taper in thickness/height (`Ch`) is usually much more influential than taper in width (`Cb`).

---

## 4.4 Classical variable-coefficient vibration PDE

Without axial load and without micro-scale enrichment:

```text
d2/dx2 [ E(x) I(x) * d2w/dx2 ] + rho(x) A(x) * d2w/dt2 = 0
```

Assume harmonic motion:
- `w(x,t) = phi(x) * exp(i*omega*t)`

Then:

```text
d2/dx2 [ E(x) I(x) * phi''(x) ] - omega^2 rho(x) A(x) phi(x) = 0
```

This is an eigenvalue problem with variable coefficients.

---

## 4.5 Cantilever boundary conditions (common in this literature)

For clamped-free beam:

At `x = 0` (clamped):
- `phi(0) = 0`
- `phi'(0) = 0`

At `x = L` (free):
- `M(L) = 0`
- `V(L) = 0`

In classical EB form:
- `M = E I phi''`
- `V = d/dx(E I phi'')`

So:
- `E(L)I(L)phi''(L) = 0`
- `d/dx(EI phi'')|_{x=L} = 0`

---

## 4.6 MCST enrichment (conceptual structure)

Modified Couple Stress Theory introduces:
- A material length scale `l`
- Additional curvature-related strain energy
- Effective stiffening for small structural scales

In beam-level reduction, this appears as additional terms in the weak form that increase effective bending resistance, often interpreted as:

```text
(EI)_eff(x) = EI(x) + Delta_MCST(x, l, section terms)
```

`Delta_MCST` depends on:
- `l`
- geometry-related measures
- specific reduction assumptions adopted by the paper.

Key trend:
- larger `l/h` ratio -> stronger size effect -> higher natural frequencies.

---

## 5) Solution strategy used in this research family

The Akgöz–Civalek line is commonly solved with **Rayleigh–Ritz** (sometimes compared with FEM in related papers).

## 5.1 Generic Ritz workflow

1. Choose admissible trial functions `psi_j(x)` satisfying essential BCs (cantilever clamp at `x=0`).
2. Approximate:
   - `phi(x) = sum_{j=1..N} q_j psi_j(x)`
3. Build generalized matrices:
   - Stiffness `K_ij` from strain energy (including MCST term if active)
   - Mass `M_ij` from kinetic energy
4. Solve:
   - `[K - omega^2 M] q = 0`
5. Frequencies:
   - `omega_n = sqrt(lambda_n)` where `lambda_n` are generalized eigenvalues.

---

## 5.2 Example weak-form ingredients (classical part)

Potential energy contribution:
```text
U_classical = 1/2 ∫_0^L E(x)I(x) [phi''(x)]^2 dx
```

Kinetic energy:
```text
T = 1/2 ∫_0^L rho(x)A(x) [phi(x)]^2 dx * omega^2
```

MCST adds extra curvature-gradient energy term(s), increasing `U`.

---

## 6) Dimensionless quantities commonly used

A frequent frequency normalization:

```text
lambda_n = omega_n * L^2 * sqrt( rho_ref * A_ref / (E_ref * I_ref) )
```

Reference values often chosen at `x=0`:
- `E_ref = E0`
- `rho_ref = rho0`
- `A_ref = A0`
- `I_ref = I0`

Using dimensionless outputs is critical for comparison across papers.

---

## 7) Expected parametric trends (validation checklist)

For a fixed boundary condition and mode index:

1. **Increase `EL/E0` (stiffer towards tip)**
   - usually increases frequencies.

2. **Increase taper severity (`Cb`, `Ch`)**
   - generally decreases frequencies, especially when `Ch` rises.

3. **Increase length-scale parameter `l` (MCST active)**
   - increases frequencies relative to classical solution.

4. **Set homogeneous limit (`EL=E0`, `rhoL=rho0`, `Cb=Ch=0`)**
   - recover standard cantilever benchmarks.

5. **Disable MCST term**
   - recover macro/classical variable-coefficient beam result.

These trend checks are often more robust than one-off numeric matching when paper tables are unavailable.

---

## 8) CSF-oriented mapping (implementation guidance)

If your pipeline uses `z` instead of `x`, substitute `x -> z`, `L -> z1-z0`.

## 8.1 Property laws

Define:
- `E(z)` via lookup or analytic law
- `rho(z)` via lookup or analytic law
- geometric interpolation / explicit station laws for `A(z), I(z)` through polygon evolution

## 8.2 Dynamic beam equation coupling

You need section-wise outputs along `z`:
- `A(z)`
- `I(z)` (about bending axis used by model)
- optional MCST-enhanced effective term (if implemented)

Then assemble the generalized eigenproblem (Ritz/FEM).

## 8.3 Separation of concerns (recommended)

- **CSF layer**: geometric/material property generator along `z`
- **Solver layer**: dynamic eigenproblem assembly and solution

This mirrors good practice and keeps verification transparent.

---

## 9) Benchmark package proposal (reproducible)

Use three levels:

## Case A — Classical homogeneous, no taper
- `E(z)=E0`
- `rho(z)=rho0`
- `Cb=Ch=0`
- MCST off

Expected:
- baseline cantilever frequencies.

## Case B — AFG + taper, classical continuum
- exponential `E(z), rho(z)`
- nonzero `Cb, Ch`
- MCST off

Expected:
- frequency shift from Case A due to grading + taper.

## Case C — Same as B + MCST
- same laws
- MCST on with `l/h0` sweep

Expected:
- frequencies above Case B, increasing with `l/h0`.

Suggested parameter sweep:
- `alpha in {-2, -1, 0, 1, 2}`
- `Ch in {0.0, 0.2, 0.4}`
- `l/h0 in {0.0, 0.2, 0.5, 1.0}`

Outputs:
- first 3–5 dimensionless frequencies
- percentage deltas:
  - `%Delta_BA = (B-A)/A*100`
  - `%Delta_CB = (C-B)/B*100`

---

## 10) Numerical pitfalls and quality controls

1. **Variable coefficient integration**
   - Use sufficient quadrature order.
   - Avoid coarse stationing that aliases strong gradients.

2. **Trial function adequacy (Ritz)**
   - Ensure admissible functions satisfy essential BCs exactly.
   - Increase basis size until frequency convergence.

3. **Law normalization**
   - Distinguish normalized coordinate `t in [0,1]` from physical `z`.
   - Document transformation explicitly: `t=(z-z0)/L`.

4. **Mass/stiffness consistency**
   - Use same spatial discretization quality for `K` and `M`.

5. **Sign and positivity checks**
   - Enforce `E(z)>0`, `rho(z)>0`, `A(z)>0`, `I(z)>0` over domain.

6. **Limit-recovery tests**
   - Verify recovery of homogeneous non-tapered classical results.

---

## 11) Suggested reporting template

For each run, report:

- Geometry:
  - `L, b0, h0, Cb, Ch`
- Material:
  - `E0, EL, rho0, rhoL, alpha`
- Micro parameter:
  - `l/h0`
- BC:
  - cantilever
- Method:
  - Ritz basis type and size `N`
- Outputs:
  - `lambda1, lambda2, lambda3`
  - relative shifts vs baseline
- Convergence:
  - change between `N` and `N+ΔN`

---

## 12) Minimal pseudocode (solver-agnostic)

```text
Input: L, laws E(z), rho(z), geometry laws -> A(z), I(z), MCST params

Build basis psi_j(z), j=1..N satisfying clamped essential BC at z=z0

For i,j in 1..N:
    K_ij = ∫ [ E(z)I(z) * psi_i'' * psi_j'' ] dz
           + (MCST contribution if active)
    M_ij = ∫ [ rho(z)A(z) * psi_i * psi_j ] dz

Solve generalized eigenproblem:
    K q = omega^2 M q

Sort omega_n ascending
Compute dimensionless lambdas
Perform parameter sweeps + convergence checks
```

---

## 13) Open-access support sources to consult

Use these as accessible technical scaffolding when full text is unavailable:

1. Official abstract/record for original IJES article (metadata confirmation).
2. Open-access papers that explicitly cite Akgöz–Civalek and reproduce AFG/MCST beam workflows.
3. FEM/Ritz studies on axially graded tapered EB beams for trend-level benchmarking.

(Keep DOI and bibliographic traceability in your benchmark README.)

---

## 14) Final engineering conclusion

For axially functionally graded tapered beams, **assuming constant `E` is not a benign simplification**.  
When `E(z)`, `rho(z)`, and geometry taper coexist, the dynamic spectrum can deviate materially from standard calculations.  
At micro scale, MCST introduces an additional non-classical stiffening mechanism that further changes frequencies and stability thresholds.

For CSF-based research/verification:
- This paper family is an excellent benchmark archetype.
- Even without full text, a robust, reproducible, and technically rigorous benchmark campaign is fully feasible using the structure in this dossier.

---

## 15) Citation block (for your project notes)

```text
Akgöz, B., & Civalek, Ö. (2013).
Free vibration analysis of axially functionally graded tapered Bernoulli–Euler microbeams
based on the modified couple stress theory.
International Journal of Engineering Science.
https://doi.org/10.1016/j.ijengsci.2013.04.009
```
