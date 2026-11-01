# Strong-Equilibrium Diagnostic: FEM3D H8 vs CSF-CUF L9

## Scope

This note summarizes the results obtained with `compare_fem3d_cuf_strong_equilibrium_v2.py` for the FEM3D H8 and CSF-CUF L9 solutions.

The diagnostic evaluates, at the same physical H8 Gauss points, the three components of the stress-divergence residual:

$$
(\nabla\cdot\sigma)_x
=
\frac{\partial \sigma_{xx}}{\partial x}
+
\frac{\partial \tau_{xy}}{\partial y}
+
\frac{\partial \tau_{xz}}{\partial z},
$$

$$
(\nabla\cdot\sigma)_y
=
\frac{\partial \tau_{xy}}{\partial x}
+
\frac{\partial \sigma_{yy}}{\partial y}
+
\frac{\partial \tau_{yz}}{\partial z},
$$

$$
(\nabla\cdot\sigma)_z
=
\frac{\partial \tau_{xz}}{\partial x}
+
\frac{\partial \tau_{yz}}{\partial y}
+
\frac{\partial \sigma_{zz}}{\partial z}.
$$

The reported quantity is an **element/domain-interior strong-equilibrium residual**. Finite differences are restricted to remain inside the same H8 element and the same CSF domain. Therefore, interface traction-jump terms are not included.

Both formulations are displacement-based and enforce equilibrium primarily in weak form. The present diagnostic is therefore intended as a local post-processing comparison, not as a proof of global strong-form equilibrium.

---

## Sampling

- Selected sections: **40**
- Accepted Gauss samples: **34,560**
- Longitudinal range: **$x/L \in [0.01,\,0.99]$**
- Sampling: all available native H8 Gauss points on each selected $x$-plane

For each section, statistics were computed for the nine individual stress-gradient terms, the three equilibrium residual components, and the total residual norm

$$
\|\nabla\cdot\sigma\|
=
\sqrt{
(\nabla\cdot\sigma)_x^2+
(\nabla\cdot\sigma)_y^2+
(\nabla\cdot\sigma)_z^2
}.
$$

---

## Main results

The table below reports the median across the 40 sections of the per-section median absolute residual.

| Quantity | FEM3D H8 | CSF-CUF L9 | Sections with CUF residual < FEM residual |
|---|---:|---:|---:|
| $|(\nabla\cdot\sigma)_x|$ | $4.732120\times10^{-2}$ | $4.153161\times10^{-2}$ | 19 / 40 |
| $|(\nabla\cdot\sigma)_y|$ | $5.713362\times10^{-3}$ | $5.544637\times10^{-3}$ | 8 / 40 |
| $|(\nabla\cdot\sigma)_z|$ | $4.324394\times10^{-1}$ | $6.555127\times10^{-3}$ | **40 / 40** |
| $\|\nabla\cdot\sigma\|$ | $4.357811\times10^{-1}$ | $4.387147\times10^{-2}$ | **38 / 40** |

The total median residual is therefore approximately

$$
\frac{4.387147\times10^{-2}}
     {4.357811\times10^{-1}}
\approx 0.10,
$$

so the CSF-CUF total interior strong-equilibrium residual is about **one order of magnitude smaller** than the FEM3D H8 value in this test.

This does **not** mean that CUF has a uniformly smaller residual in every equilibrium component. The result is strongly component-dependent.

---

## Equilibrium in the $x$ direction

For

$$
\frac{\partial \sigma_{xx}}{\partial x}
+
\frac{\partial \tau_{xy}}{\partial y}
+
\frac{\partial \tau_{xz}}{\partial z}
=0,
$$

the median residuals are

$$
\mathrm{FEM3D}=4.732120\times10^{-2},
\qquad
\mathrm{CSF\text{-}CUF}=4.153161\times10^{-2}.
$$

The two values are of the same order of magnitude. CUF has the smaller residual in **19 of 40 sections**, so no systematic advantage is observed in this component.

The median magnitudes of the three contributing terms are:

| Term | FEM3D H8 | CSF-CUF L9 |
|---|---:|---:|
| $|\partial \sigma_{xx}/\partial x|$ | $5.599876\times10^{-2}$ | $5.658783\times10^{-2}$ |
| $|\partial \tau_{xy}/\partial y|$ | $6.124195\times10^{-3}$ | $3.520627\times10^{-2}$ |
| $|\partial \tau_{xz}/\partial z|$ | $6.326840\times10^{-3}$ | $5.004803\times10^{-2}$ |

The final residual is therefore produced by a different balance among the individual terms in the two formulations.

---

## Equilibrium in the $y$ direction

For

$$
\frac{\partial \tau_{xy}}{\partial x}
+
\frac{\partial \sigma_{yy}}{\partial y}
+
\frac{\partial \tau_{yz}}{\partial z}
=0,
$$

the median residuals are

$$
\mathrm{FEM3D}=5.713362\times10^{-3},
\qquad
\mathrm{CSF\text{-}CUF}=5.544637\times10^{-3}.
$$

The median values are almost identical. CUF has the smaller residual in only **8 of 40 sections**.

The contributing terms are also comparable:

| Term | FEM3D H8 | CSF-CUF L9 |
|---|---:|---:|
| $|\partial \tau_{xy}/\partial x|$ | $8.422499\times10^{-4}$ | $1.395665\times10^{-3}$ |
| $|\partial \sigma_{yy}/\partial y|$ | $3.220613\times10^{-3}$ | $3.341999\times10^{-3}$ |
| $|\partial \tau_{yz}/\partial z|$ | $1.767699\times10^{-3}$ | $2.759391\times10^{-3}$ |

Thus, the $y$-equilibrium equation does not show a substantial global difference between the two methods.

---

## Equilibrium in the $z$ direction

The largest difference occurs for

$$
\frac{\partial \tau_{xz}}{\partial x}
+
\frac{\partial \tau_{yz}}{\partial y}
+
\frac{\partial \sigma_{zz}}{\partial z}
=0.
$$

The median residuals are

$$
\mathrm{FEM3D}=4.324394\times10^{-1},
\qquad
\mathrm{CSF\text{-}CUF}=6.555127\times10^{-3}.
$$

The CUF residual is smaller in **all 40 sections**.

The ratio of the two median values is approximately

$$
\frac{6.555127\times10^{-3}}
     {4.324394\times10^{-1}}
\approx 1.5\times10^{-2}.
$$

Thus, for this equilibrium component, the CSF-CUF residual is about **1.5% of the FEM3D H8 residual**.

The difference is also visible in the individual stress-gradient terms:

| Term | FEM3D H8 | CSF-CUF L9 |
|---|---:|---:|
| $|\partial \tau_{xz}/\partial x|$ | $2.524075\times10^{-1}$ | $2.388873\times10^{-2}$ |
| $|\partial \tau_{yz}/\partial y|$ | $8.589188\times10^{-2}$ | $4.519739\times10^{-3}$ |
| $|\partial \sigma_{zz}/\partial z|$ | $2.594481\times10^{-1}$ | $2.459691\times10^{-2}$ |

Therefore, the smaller CUF residual in the $z$ equation is not caused only by an accidental cancellation of large terms. The individual stress-gradient terms themselves are substantially smaller in the CUF reconstruction for this test.

---

## Overall interpretation

The results support the following statement:

> **In this element/domain-interior strong-equilibrium diagnostic, the CSF-CUF L9 solution exhibits a lower total local equilibrium residual than the FEM3D H8 solution over most of the beam. The difference is dominated by the $z$-equilibrium equation, while the $x$- and $y$-equilibrium equations are much more comparable.**

In particular:

- the total CUF residual is smaller in **38 of 40 sections**;
- the $z$-equilibrium residual is smaller for CUF in **40 of 40 sections**;
- the $x$-equilibrium residual does not show a systematic winner;
- the $y$-equilibrium residual is very similar in magnitude between the two formulations.

In the restricted sense measured by this diagnostic, the CSF-CUF solution can therefore be described as **more locally equilibrated overall**, but this statement should not be generalized to mean that CUF is universally more accurate or more correct than FEM3D.

---

## Important limitations

The comparison must be interpreted with the following qualifications:

1. The diagnostic evaluates the strong-form residual only **inside elements/domains**.
2. It does not include traction-jump contributions across H8 element interfaces or CSF domain interfaces.
3. Both methods enforce equilibrium primarily through their weak formulations.
4. FEM3D H8 and CSF-CUF L9 use very different spatial approximations, so a lower local residual does not by itself establish a globally superior method.
5. For variable material properties, the constitutive field represented by CUF may remain continuous while the FEM3D brick model uses element-wise material values. This difference can affect local stress derivatives and must be kept in mind when interpreting the residuals.

---

## Files generated by the diagnostic

The run produces:

- `equilibrium_component_points_all_sections.csv`
- `equilibrium_component_sections_summary.csv`
- `summary.txt`
- `div_x_median_vs_x.png`
- `div_y_median_vs_x.png`
- `div_z_median_vs_x.png`
- `div_norm_median_vs_x.png`
- `equilibrium_x_terms_median_vs_x.png`
- `equilibrium_y_terms_median_vs_x.png`
- `equilibrium_z_terms_median_vs_x.png`
- `residual_ratio_cuf_over_fem_vs_x.png`

These files should be used together: the scalar summary provides the global picture, while the section-wise plots and CSV files show where along the beam the two formulations differ.
