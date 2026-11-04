# FEM3D CSF-CUF equilibrium report

## 1. Reference FEM3D solution

The FEM3D reference solution is evaluated on the converged S3 mesh identified by the displacement-convergence study:

```text
nx        = 120
ny-left   = 4
ny-web    = 8
ny-right  = 4
nz-flange = 6
nz-web    = 28
```

corresponding to

```text
49,920 stdBrick elements.
```

The subsequent S4 refinement changed the minimum vertical displacement by only approximately `0.021%`; S3 is therefore adopted as the FEM3D reference mesh.

The present analysis compares the local strong-equilibrium residuals reconstructed from this FEM3D solution with those obtained from the CSF-CUF solution.

---

## 2. Strong-equilibrium equations

In the absence of body forces, the three local equilibrium equations are

```math
\frac{\partial \sigma_{xx}}{\partial x}
+
\frac{\partial \tau_{xy}}{\partial y}
+
\frac{\partial \tau_{xz}}{\partial z}
=0,
```

```math
\frac{\partial \tau_{xy}}{\partial x}
+
\frac{\partial \sigma_{yy}}{\partial y}
+
\frac{\partial \tau_{yz}}{\partial z}
=0,
```

```math
\frac{\partial \tau_{xz}}{\partial x}
+
\frac{\partial \tau_{yz}}{\partial y}
+
\frac{\partial \sigma_{zz}}{\partial z}
=0.
```

The corresponding residual components are denoted by

```math
r_x,\qquad r_y,\qquad r_z,
```

and the total residual norm is

```math
r_{\mathrm{norm}}
=
\sqrt{
r_x^2+r_y^2+r_z^2
}.
```

The residuals reported here are absolute stress-divergence quantities. They are not normalized by a characteristic stress or length scale and should therefore be interpreted as diagnostics of local satisfaction of the differential equilibrium equations, rather than as direct measures of overall solution accuracy.

---

## 3. Sampling

The equilibrium diagnostic is evaluated on:

```text
40 longitudinal sections
nominal x/L range = 0.01 ... 0.99
864 accepted Gauss samples per section
34,560 accepted samples in total
```

The 40 longitudinal target locations are nominally equally spaced over the interval

```math
0.01 \leq x/L \leq 0.99.
```

Each target location is mapped to the nearest available native H8 Gauss-point `x`-plane. The actual sampled longitudinal coordinates therefore follow the FEM3D Gauss-point locations.

All available accepted native H8 Gauss samples on each selected section are retained, so that the diagnostic covers the complete sampled cross-section at every longitudinal station.

An interior subset is also defined by retaining only sections whose distance from the nearest restrained end is greater than one local total section height. With this criterion:

```text
31 interior sections are retained
9 end-region sections are excluded from the interior subset
```

The complete 40-section statistics and the 31-section interior statistics are both reported below.

---

## 4. Global comparison

The median residuals across all 40 sampled sections are:

| Residual | FEM3D | CSF-CUF | CSF-CUF / FEM3D | Sections with CSF-CUF < FEM3D |
|---|---:|---:|---:|---:|
| `div_x` | 4.732120e-02 | 4.153161e-02 | 0.878 | 19 / 40 |
| `div_y` | 5.713362e-03 | 5.544637e-03 | 0.970 | 8 / 40 |
| `div_z` | 4.324394e-01 | 6.555127e-03 | 0.0152 | 40 / 40 |
| `div_norm` | 4.357811e-01 | 4.387147e-02 | 0.1007 | 38 / 40 |

For the total residual norm,

```math
\frac{r_{\mathrm{norm}}^{CSF-CUF}}
     {r_{\mathrm{norm}}^{FEM3D}}
\simeq 0.1007.
```

Equivalently,

```math
r_{\mathrm{norm}}^{FEM3D}
\simeq
9.93\,
r_{\mathrm{norm}}^{CSF-CUF}.
```

The largest separation occurs in the third equilibrium equation. For `div_z`,

```math
\frac{r_z^{CSF-CUF}}
     {r_z^{FEM3D}}
\simeq 0.0152,
```

corresponding to a median FEM3D residual approximately

```text
66.0 times
```

the CSF-CUF value.

CSF-CUF gives the lower `div_z` residual in all 40 analyzed sections.

### 4.1 Interior-section comparison

For the 31-section interior subset, the median residuals are:

| Residual | FEM3D | CSF-CUF | CSF-CUF / FEM3D | Sections with CSF-CUF < FEM3D |
|---|---:|---:|---:|---:|
| `div_x` | 7.556536e-02 | 3.910764e-02 | 0.518 | 19 / 31 |
| `div_y` | 6.271576e-03 | 6.469343e-03 | 1.032 | 8 / 31 |
| `div_z` | 5.196062e-01 | 6.796170e-03 | 0.0131 | 31 / 31 |
| `div_norm` | 5.210142e-01 | 4.478623e-02 | 0.0860 | 31 / 31 |

For the total residual norm,

```math
\frac{r_{\mathrm{norm}}^{CSF-CUF}}
     {r_{\mathrm{norm}}^{FEM3D}}
\simeq 0.0860.
```

The CSF-CUF reconstruction gives the lower total strong-equilibrium residual in all 31 interior sections.

The largest separation remains in the third equilibrium equation, for which

```math
\frac{r_z^{CSF-CUF}}
     {r_z^{FEM3D}}
\simeq 0.0131.
```

The interior-section results therefore strengthen the same trend observed over the full set of sampled sections. Away from the restrained end regions, the CSF-CUF reconstruction gives the lower total strong-equilibrium residual in all 31 interior sections, indicating closer local satisfaction of the differential equilibrium equations in the smooth interior region of the member.

---

## 5. First equilibrium equation

The first equilibrium equation is

```math
r_x
=
\frac{\partial \sigma_{xx}}{\partial x}
+
\frac{\partial \tau_{xy}}{\partial y}
+
\frac{\partial \tau_{xz}}{\partial z}.
```

The median magnitudes of the individual terms across the 40 sections are:

| Term | FEM3D | CSF-CUF |
|---|---:|---:|
| `dσxx/dx` | 5.599876e-02 | 5.658783e-02 |
| `dτxy/dy` | 6.124195e-03 | 3.520627e-02 |
| `dτxz/dz` | 6.326840e-03 | 5.004803e-02 |

The longitudinal normal-stress derivative has nearly the same median magnitude in the two formulations:

```math
\left|
\frac{\partial \sigma_{xx}}{\partial x}
\right|_{FEM3D}
\approx
\left|
\frac{\partial \sigma_{xx}}{\partial x}
\right|_{CSF-CUF}.
```

The two transverse shear-gradient terms are individually larger in the CSF-CUF reconstruction.

The equilibrium residual depends on the signed sum of the three derivative terms. Across all 40 sections, the median residuals are

```text
FEM3D  : 4.732120e-02
CSF-CUF: 4.153161e-02
```

with a CSF-CUF/FEM3D ratio of approximately

```text
0.878.
```

CSF-CUF gives the lower `div_x` residual in

```text
19 / 40 sections.
```

For the interior subset, the median residuals become

```text
FEM3D  : 7.556536e-02
CSF-CUF: 3.910764e-02
```

with

```math
\frac{r_x^{CSF-CUF}}
     {r_x^{FEM3D}}
\simeq 0.518.
```

CSF-CUF gives the lower `div_x` residual in 19 of the 31 interior sections.

---

## 6. Second equilibrium equation

The second equilibrium equation is

```math
r_y
=
\frac{\partial \tau_{xy}}{\partial x}
+
\frac{\partial \sigma_{yy}}{\partial y}
+
\frac{\partial \tau_{yz}}{\partial z}.
```

The median magnitudes of the derivative terms across all 40 sections are:

| Term | FEM3D | CSF-CUF |
|---|---:|---:|
| `dτxy/dx` | 8.422499e-04 | 1.395665e-03 |
| `dσyy/dy` | 3.220613e-03 | 3.341999e-03 |
| `dτyz/dz` | 1.767699e-03 | 2.759391e-03 |

The resulting median residuals across all sections are

```text
FEM3D  : 5.713362e-03
CSF-CUF: 5.544637e-03
```

giving

```math
\frac{r_y^{CSF-CUF}}
     {r_y^{FEM3D}}
\simeq 0.970.
```

The two formulations therefore give essentially the same residual level in the second equilibrium equation, with a difference of approximately `3%` in the global median.

CSF-CUF gives the lower `div_y` residual in

```text
8 / 40 sections.
```

For the 31-section interior subset,

```text
FEM3D  : 6.271576e-03
CSF-CUF: 6.469343e-03
```

and

```math
\frac{r_y^{CSF-CUF}}
     {r_y^{FEM3D}}
\simeq 1.032.
```

The interior median values are therefore also essentially equivalent, with FEM3D slightly lower.

---

## 7. Third equilibrium equation

The third equilibrium equation is

```math
r_z
=
\frac{\partial \tau_{xz}}{\partial x}
+
\frac{\partial \tau_{yz}}{\partial y}
+
\frac{\partial \sigma_{zz}}{\partial z}.
```

The median magnitudes of the individual terms across all 40 sections are:

| Term | FEM3D | CSF-CUF | FEM3D / CSF-CUF |
|---|---:|---:|---:|
| `dτxz/dx` | 2.524075e-01 | 2.388873e-02 | 10.6 |
| `dτyz/dy` | 8.589188e-02 | 4.519739e-03 | 19.0 |
| `dσzz/dz` | 2.594481e-01 | 2.459691e-02 | 10.5 |

All three derivative terms have substantially lower median magnitudes in the CSF-CUF reconstruction.

The resulting median residual across all 40 sections is

```text
FEM3D  : 4.324394e-01
CSF-CUF: 6.555127e-03
```

with

```math
\frac{r_z^{CSF-CUF}}
     {r_z^{FEM3D}}
\simeq 1.52\times10^{-2}.
```

Equivalently, the FEM3D median `div_z` residual is approximately

```text
66.0 times
```

the CSF-CUF value.

CSF-CUF gives the lower `div_z` residual in

```text
40 / 40 sections.
```

For the interior subset,

```text
FEM3D  : 5.196062e-01
CSF-CUF: 6.796170e-03
```

giving

```math
\frac{r_z^{CSF-CUF}}
     {r_z^{FEM3D}}
\simeq 1.31\times10^{-2}.
```

CSF-CUF gives the lower `div_z` residual in all

```text
31 / 31 interior sections.
```

The third equilibrium component therefore remains the principal source of separation between the total FEM3D and CSF-CUF strong-equilibrium residuals.

---

## 8. Total equilibrium residual along the beam

The total residual exhibits a clear longitudinal evolution.

At the first sampled section,

```text
x/L = 0.009858
```

the median total residuals are

```text
FEM3D   div_norm = 4.393e-02
CSF-CUF div_norm = 4.060e-02
```

so the two values are initially of comparable magnitude.

Moving along the beam, the FEM3D residual increases substantially while the CSF-CUF residual remains much lower over the central portion.

At approximately

```text
x/L = 0.615142
```

the values are

```text
FEM3D   div_norm = 7.107e-01
CSF-CUF div_norm = 1.580e-02
```

giving approximately

```math
\frac{CSF-CUF}{FEM3D}
\simeq 0.0222.
```

The FEM3D residual is therefore approximately

```text
45 times
```

the CSF-CUF residual at this station.

Further towards the final end, the FEM3D residual decreases while the CSF-CUF residual increases.

At

```text
x/L = 0.940142
```

the values are

```text
FEM3D   div_norm = 1.729e-01
CSF-CUF div_norm = 1.215e-01
```

and CSF-CUF remains lower.

The ordering reverses only in the final two sampled sections:

| `x/L` | FEM3D `div_norm` | CSF-CUF `div_norm` | CSF-CUF / FEM3D |
|---:|---:|---:|---:|
| 0.965142 | 8.478e-02 | 1.313e-01 | 1.55 |
| 0.990142 | 8.541e-02 | 1.342e-01 | 1.57 |

Therefore, over the complete 40-section set,

```text
CSF-CUF < FEM3D in div_norm for 38 / 40 sections.
```

For the 31-section interior subset,

```text
CSF-CUF < FEM3D in div_norm for 31 / 31 sections.
```

---

## 9. FEM3D reference-mesh result

The strong-equilibrium analysis is performed on the S3 FEM3D reference mesh.

The resulting median residuals across all 40 sections are:

| Residual | FEM3D | CSF-CUF |
|---|---:|---:|
| `div_x` | 4.732120e-02 | 4.153161e-02 |
| `div_y` | 5.713362e-03 | 5.544637e-03 |
| `div_z` | 4.324394e-01 | 6.555127e-03 |
| `div_norm` | 4.357811e-01 | 4.387147e-02 |

The corresponding interior-section values are:

| Residual | FEM3D | CSF-CUF |
|---|---:|---:|
| `div_x` | 7.556536e-02 | 3.910764e-02 |
| `div_y` | 6.271576e-03 | 6.469343e-03 |
| `div_z` | 5.196062e-01 | 6.796170e-03 |
| `div_norm` | 5.210142e-01 | 4.478623e-02 |

The main section-count results are:

```text
All sections:
CSF-CUF < FEM3D in div_norm for 38 / 40 sections
CSF-CUF < FEM3D in div_z    for 40 / 40 sections

Interior sections:
CSF-CUF < FEM3D in div_norm for 31 / 31 sections
CSF-CUF < FEM3D in div_z    for 31 / 31 sections
```

For the third equilibrium equation over all 40 sections,

```math
\frac{r_z^{CSF-CUF}}
     {r_z^{FEM3D}}
\simeq 1.52\times10^{-2},
```

while for the interior subset,

```math
\frac{r_z^{CSF-CUF}}
     {r_z^{FEM3D}}
\simeq 1.31\times10^{-2}.
```

The strong-equilibrium diagnostic therefore shows a substantially lower CSF-CUF residual in the third equilibrium component and in the total residual norm over most of the sampled beam and throughout the defined interior subset.

These residuals remain absolute, unnormalized strong-form diagnostics and are not used as standalone measures of overall structural-solution accuracy.

---

## 10. Summary

The FEM3D reference solution is computed using the S3 mesh, consisting of `49,920 stdBrick` elements. The local strong-equilibrium analysis is evaluated over 40 longitudinal sections and `34,560` accepted native H8 Gauss samples.

The 40 target sections cover the nominal interval

```math
0.01 \leq x/L \leq 0.99,
```

with each target mapped to the nearest native H8 Gauss-point plane.

An additional interior subset retains 31 sections located farther than one local total section height from either restrained end.

The comparison gives the following results:

- for the first equilibrium equation, FEM3D and CSF-CUF remain of comparable order over the complete set, with a median CSF-CUF/FEM3D ratio of approximately `0.878`; over the interior subset this ratio decreases to approximately `0.518`;
- for the second equilibrium equation, the two formulations give essentially the same median residual level, with ratios of approximately `0.970` over all sections and `1.032` over the interior subset;
- the largest separation occurs in the third equilibrium equation: CSF-CUF gives the lower `div_z` residual in all 40 sampled sections and in all 31 interior sections;
- the median `div_z` CSF-CUF/FEM3D ratio is approximately `0.0152` over all sections and `0.0131` over the interior subset;
- considering the complete equilibrium residual, CSF-CUF gives the lower `div_norm` in 38 of the 40 sampled sections and in all 31 interior sections;
- the median total-residual CSF-CUF/FEM3D ratio is approximately `0.1007` over all sections and `0.0860` over the interior subset.

The first two equilibrium components therefore remain broadly comparable between the two formulations, whereas the third component clearly separates the reconstructed stress fields.

The interior-section results strengthen the same trend observed over the complete set. Away from the restrained end regions, the CSF-CUF stress reconstruction gives the lower total strong-equilibrium residual in all 31 sampled interior sections.

The reported residuals quantify local satisfaction of the differential equilibrium equations. Because they are absolute and unnormalized, they should not be interpreted as direct standalone measures of the overall accuracy of either structural solution.
