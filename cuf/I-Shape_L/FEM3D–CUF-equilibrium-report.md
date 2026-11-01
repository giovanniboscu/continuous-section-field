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

The subsequent S4 refinement changed the minimum vertical displacement by only approximately `0.021%`; S3 is therefore adopted as the converged FEM3D reference mesh.

The present analysis compares the local strong-equilibrium residuals reconstructed from this FEM3D solution with those obtained from the CUF solution.

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

---

## 3. Sampling

The equilibrium diagnostic is evaluated on:

```text
40 longitudinal sections
x/L range = 0.01 ... 0.99
1,664 Gauss samples per section
66,560 accepted samples in total
```

All available native H8 Gauss samples on each selected section are retained.

The analysis therefore covers the complete sampled cross-section at every longitudinal station.

---

## 4. Global comparison

The median residual across the 40 sections is:

| Residual | FEM3D | CUF | CUF/FEM3D | Sections with CUF < FEM3D |
|---|---:|---:|---:|---:|
| `div_x` | 5.3352e-02 | 4.1116e-02 | 0.771 | 20 / 40 |
| `div_y` | 5.7306e-03 | 5.8279e-03 | 1.017 | 6 / 40 |
| `div_z` | 4.4731e-01 | 6.6136e-03 | 0.0148 | 40 / 40 |
| `div_norm` | 4.4867e-01 | 4.4685e-02 | 0.0996 | 38 / 40 |

The total CUF equilibrium residual is therefore approximately

```math
\frac{r_{\mathrm{norm}}^{CUF}}
     {r_{\mathrm{norm}}^{FEM}}
\simeq 0.10.
```

Equivalently,

```math
r_{\mathrm{norm}}^{FEM}
\simeq
10.0\,
r_{\mathrm{norm}}^{CUF}.
```

The dominant difference is associated with the third equilibrium equation.

For `div_z`,

```math
\frac{r_z^{CUF}}
     {r_z^{FEM}}
\simeq 0.0148,
```

which corresponds to a FEM3D residual approximately

```math
67.6
```

times larger than the CUF residual.

CUF gives the lower `div_z` residual in all 40 analyzed sections.

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

The median magnitudes of the individual terms are:

| Term | FEM3D | CUF |
|---|---:|---:|
| `dσxx/dx` | 5.9501e-02 | 5.9534e-02 |
| `dτxy/dy` | 6.4520e-03 | 3.6012e-02 |
| `dτxz/dz` | 6.3079e-03 | 5.6352e-02 |

The longitudinal normal-stress derivative is essentially identical in magnitude:

```math
\left|
\frac{\partial \sigma_{xx}}{\partial x}
\right|_{FEM}
\approx
\left|
\frac{\partial \sigma_{xx}}{\partial x}
\right|_{CUF}.
```

The transverse shear derivative terms are larger individually in the CUF solution.

The equilibrium residual, however, results from the signed sum of the three terms. The CUF median residual remains lower overall:

```text
FEM3D : 5.3352e-02
CUF   : 4.1116e-02
```

The two solutions alternate along the beam in this component: CUF gives the smaller residual in 20 of the 40 sections.

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

The derivative terms are:

| Term | FEM3D | CUF |
|---|---:|---:|
| `dτxy/dx` | 9.5208e-04 | 1.4594e-03 |
| `dσyy/dy` | 3.3281e-03 | 3.5291e-03 |
| `dτyz/dz` | 1.7799e-03 | 2.9952e-03 |

The resulting median residuals are

```text
FEM3D : 5.7306e-03
CUF   : 5.8279e-03
```

The two values differ by only about

```math
1.7\%.
```

The second equilibrium equation therefore shows essentially the same residual level for the two formulations, with FEM3D slightly lower.

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

The median magnitudes of the individual terms are:

| Term | FEM3D | CUF | FEM3D/CUF |
|---|---:|---:|---:|
| `dτxz/dx` | 2.5931e-01 | 2.3221e-02 | 11.2 |
| `dτyz/dy` | 8.6845e-02 | 4.6665e-03 | 18.6 |
| `dσzz/dz` | 2.6861e-01 | 2.4179e-02 | 11.1 |

All three derivative terms are substantially smaller in the CUF solution.

The resulting residual is

```text
FEM3D : 4.4731e-01
CUF   : 6.6136e-03
```

with

```math
\frac{r_z^{CUF}}
     {r_z^{FEM}}
\simeq 1.48\times10^{-2}.
```

The CUF residual is lower in every analyzed section:

```text
40 / 40 sections.
```

This component is the main source of the difference between the total FEM3D and CUF equilibrium residuals.

---

## 8. Total equilibrium residual along the beam

The total residual exhibits a clear longitudinal evolution.

At the beginning of the beam:

```text
x/L = 0.010

FEM3D div_norm = 4.6102e-02
CUF   div_norm = 3.9507e-02
CUF/FEM3D      = 0.857
```

Moving towards the central region, the difference grows progressively.

At approximately

```text
x/L = 0.615
```

the values are

```text
FEM3D div_norm = 7.3214e-01
CUF   div_norm = 1.6683e-02
```

giving

```math
\frac{CUF}{FEM3D}
\simeq 0.0228.
```

The FEM3D residual is therefore approximately

```math
44
```

times larger at this station.

After the central region, the CUF residual increases again towards the final end of the beam, while the FEM3D residual decreases.

At

```text
x/L = 0.940
```

the values are

```text
FEM3D = 2.2203e-01
CUF   = 1.2478e-01
```

and CUF remains lower.

Only the final two sampled sections reverse the ordering:

| `x/L` | FEM3D `div_norm` | CUF `div_norm` | CUF/FEM3D |
|---:|---:|---:|---:|
| 0.9649 | 1.2013e-01 | 1.3025e-01 | 1.084 |
| 0.9899 | 1.09496e-01 | 1.37862e-01 | 1.259 |

Therefore CUF gives the smaller total strong-equilibrium residual in

```text
38 of the 40 sections.
```

---
## 9. FEM3D reference-mesh result

The strong-equilibrium analysis is performed on the converged S3 FEM3D reference mesh.

The resulting median residuals are:

| Residual | FEM3D | CUF |
|---|---:|---:|
| `div_x` | 5.3352e-02 | 4.1116e-02 |
| `div_y` | 5.7306e-03 | 5.8279e-03 |
| `div_z` | 4.4731e-01 | 6.6136e-03 |
| `div_norm` | 4.4867e-01 | 4.4685e-02 |

The main result is:

```text
CUF < FEM3D in div_norm for 38 / 40 sections
CUF < FEM3D in div_z    for 40 / 40 sections
```

For the third equilibrium equation,

```math
\frac{r_z^{CUF}}{r_z^{FEM}}
\simeq 1.48\times10^{-2},
```

so the FEM3D residual is approximately 67.6 times larger than the CUF residual in the median comparison.

The converged FEM3D reference solution therefore confirms a substantially lower CUF strong-equilibrium residual over almost the entire beam.

---

## 10. Summary

The FEM3D reference solution is computed using the converged S3 mesh, consisting of 49,920 `stdBrick` elements. The local equilibrium analysis is evaluated over 40 longitudinal sections and 66,560 native Gauss samples.

The comparison between FEM3D and CUF gives the following results:

- for the first equilibrium equation, FEM3D and CUF show comparable residual levels; the median CUF residual is about 23% lower, with CUF giving the lower value in 20 of the 40 sections;
- for the second equilibrium equation, the two formulations give essentially the same residual level, with a difference of about 1.7%;
- the main difference occurs in the third equilibrium equation: CUF gives the lower residual in all 40 sections, and the median FEM3D residual is approximately 67.6 times larger than the CUF value;
- considering the complete equilibrium residual, the median CUF `div_norm` is approximately one tenth of the FEM3D value;
- CUF gives the lower `div_norm` in 38 of the 40 analyzed sections;
- the two sections in which the FEM3D `div_norm` is lower are located at the final end of the beam.

The three equilibrium equations therefore show two distinct behaviors. The first and second equations give residuals of comparable magnitude for FEM3D and CUF, while the third equation clearly separates the two solutions.

This third component dominates the total equilibrium residual and determines the overall difference between the two formulations. As a result, the CUF stress field exhibits a substantially lower local equilibrium residual over almost the entire beam, with an approximately tenfold reduction in the median total residual and a 67.6-fold reduction in the median residual of the third equilibrium equation.
