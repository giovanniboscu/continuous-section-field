# CSF Jourawski Shear-Stress Calculation Model

## 1. Purpose and scope

This document describes the shear-stress model implemented by Continuous Section Field (CSF) in:

```python
analyse_polygon_jourawski_shear_stress(...)
```

The method has two distinct stages:

1. the shear flow on each section cut is obtained from a Jourawski equilibrium calculation performed on an $E$-homogenized section;
2. the resulting cut force is redistributed among the material segments crossed by the cut according to their shear carrier, interpreted as $G$ or as a quantity proportional to $G$.

The first stage is a transformed-section extension of the classical Jourawski method. The second stage is an additional CSF modelling assumption and must be stated separately.

The method is a sectional engineering model. It is not a full two-dimensional Saint-Venant elasticity solution.

---

## 2. Resolved CSF section

At each requested longitudinal coordinate $z$, CSF resolves the local section:

```math
S(z)
```

The resolved section contains:

- the polygon geometry present at $z$;
- the axial and bending material carrier associated with $E$;
- the shear material carrier associated with $G$;
- the polygon containment and relative-weight representation used by CSF.

Two material fields are therefore kept distinct:

```math
E(x,y)
```

for axial stress and bending equilibrium, and

```math
G(x,y)
```

for the local redistribution of shear stress.

In the implementation:

- `weightabs` represents the absolute axial/bending carrier at the sampled polygon;
- `weight` is the additive relative polygon weight used by the CSF nested-polygon model;
- `shear_weightabs` represents the absolute shear carrier, or any carrier proportional to $G$.

For non-nested disjoint polygons, `weight` and `weightabs` normally coincide. For nested polygons, the relative polygon weights reconstruct the absolute material field through additive polygon contributions.

---

## 3. Homogenization with respect to $E$

A reference axial/bending carrier $E_{\mathrm{ref}}$ is selected from the resolved section. The transformed material ratio is conceptually:

```math
n_E(x,y)=\frac{E(x,y)}{E_{\mathrm{ref}}}
```

For a material region $i$:

```math
n_{E,i}=\frac{E_i}{E_{\mathrm{ref}}}
```

CSF performs the same operation through its additive polygon representation. Each polygon contribution is normalized by the reference absolute weight:

```math
w_{i,\mathrm{norm}}
=
\frac{w_i}{E_{\mathrm{ref}}}
```

where $w_i$ is the relative polygon contribution stored in `weight`.

The transformed section is then used to calculate:

```math
A_E,\qquad C_x,\qquad C_y,\qquad
I_x,\qquad I_y,\qquad I_{xy}
```

These are the area, centroid and inertia quantities of the $E$-homogenized section.

The determinant of the transformed inertia matrix is:

```math
D=I_xI_y-I_{xy}^{\,2}
```

The physical section geometry is not altered. Homogenization changes the integration weights used to obtain the centroid, inertias and partial first moments.

---

## 4. Shear actions and generalized Jourawski flow

CSF uses the following conventions:

- $T_x$ is the shear action associated with the longitudinal variation of $M_y$;
- $T_y$ is the shear action associated with the longitudinal variation of $M_x$;
- $\tau_x$ is evaluated from vertical cuts $x=c$;
- $\tau_y$ is evaluated from horizontal cuts $y=c$.

For a general transformed section, including $I_{xy}\neq0$, CSF calculates:

```math
\beta_x
=
\frac{T_x I_x-T_y I_{xy}}{D}
```

```math
\beta_y
=
\frac{T_y I_y-T_x I_{xy}}{D}
```

For the portion $A^*$ retained on one side of a cut, the transformed partial first moments are:

```math
Q_x^{(E)}
=
\int_{A^*}
n_E(x,y)\,(x-C_x)\,dA
```

```math
Q_y^{(E)}
=
\int_{A^*}
n_E(x,y)\,(y-C_y)\,dA
```

The shear flow transmitted through the cut is:

```math
\boxed{
q
=
\beta_x Q_x^{(E)}
+
\beta_y Q_y^{(E)}
}
```

When the centroidal axes are principal axes and $I_{xy}=0$:

```math
\boxed{
q
=
\frac{T_x}{I_y}Q_x^{(E)}
+
\frac{T_y}{I_x}Q_y^{(E)}
}
```

The two terms are added algebraically because they are contributions to the same cut equilibrium.

This also means that a global action $T_y$ may produce a local $\tau_x$ component, and a global action $T_x$ may produce a local $\tau_y$ component. This is not the creation of an additional global shear action. It is the local shear-flow path required by sectional equilibrium.

For example, in a T-section subjected only to $T_y$, horizontal shear components develop in the flange and transfer the shear flow toward the web. The horizontal components on opposite sides balance globally.

---

## 5. Geometric chord and reference mean stress

For each cut, CSF determines all active geometric segments crossed by the cut.

Let:

```math
b_i
```

be the actual geometric length of segment $i$, and:

```math
b_{\mathrm{tot}}=\sum_i b_i
```

be the complete active chord length.

The chord is calculated from the original resolved geometry. It is not transformed by either $E$ or $G$.

Before material redistribution, the mean reference stress on the complete chord is:

```math
\tau_{\mathrm{ref}}
=
\frac{q}{b_{\mathrm{tot}}}
```

This is the direct Jourawski line-average value for the cut.

For a vertical cut $x=c$, it is associated with the local component $\tau_x$.  
For a horizontal cut $y=c$, it is associated with the local component $\tau_y$.

---

## 6. Redistribution according to $G$

After the Jourawski flow $q$ has been obtained, CSF redistributes it among the material segments crossed by the same cut.

Let:

```math
g_i
```

be the sampled `shear_weightabs` of segment $i$. The value $g_i$ may be the physical shear modulus $G_i$, or any consistently scaled carrier proportional to $G_i$.

CSF assumes a common mean shear strain for all segments on the cut:

```math
\gamma_i=\gamma
```

and therefore:

```math
\tau_i=g_i\gamma
```

Cut equilibrium requires:

```math
q=\sum_i \tau_i b_i
```

Consequently:

```math
\gamma
=
\frac{q}{\sum_j g_j b_j}
```

and the local stress assigned to segment $i$ is:

```math
\boxed{
\tau_i
=
q\,
\frac{g_i}{\sum_j g_jb_j}
}
```

Using $\tau_{\mathrm{ref}}=q/b_{\mathrm{tot}}$, the same expression is:

```math
\boxed{
\tau_i
=
\tau_{\mathrm{ref}}\,
\frac{b_{\mathrm{tot}}g_i}
{\sum_j g_jb_j}
}
```

The redistribution preserves the cut resultant exactly:

```math
\boxed{
\sum_i \tau_i b_i=q
}
```

The segment length $b_i$ appears in the denominator through the total shear stiffness of the chord, but the stress in each individual segment is proportional to $g_i$, not to its length.

### Interpretation

This redistribution is not part of the classical homogeneous Jourawski formula. It is an additional constitutive assumption adopted by CSF for heterogeneous sections.

It represents the crossed material segments as parallel shear carriers subjected to the same mean shear strain on that cut.

The assumption is explicit and mechanically interpretable, but it does not reproduce all local two-dimensional compatibility effects, interface effects or stress concentrations.

---

## 7. Homogeneous-section limit

For a homogeneous section:

```math
E_i=E_{\mathrm{ref}}
```

and therefore the transformed section reduces to the geometric section.

If the shear carrier is also uniform:

```math
g_i=g
```

then:

```math
\sum_j g_jb_j
=
g\,b_{\mathrm{tot}}
```

and:

```math
\tau_i
=
q\frac{g}{g\,b_{\mathrm{tot}}}
=
\frac{q}{b_{\mathrm{tot}}}
=
\tau_{\mathrm{ref}}
```

The $G$-redistribution therefore disappears automatically, and the method reduces to the ordinary homogeneous Jourawski calculation.

---

## 8. Separation of the two material operations

The two material operations have different mechanical roles and must not be merged.

### $E$-homogenization

The $E$-based transformed section is used to calculate:

- the centroid;
- $I_x$, $I_y$ and $I_{xy}$;
- the transformed partial first moments $Q_x^{(E)}$ and $Q_y^{(E)}$;
- the total cut flow $q$.

This follows from the axial stress field and its longitudinal variation.

### $G$-redistribution

The $G$-based carrier is used only after $q$ has been obtained. It determines how the fixed cut resultant is shared among the crossed material segments.

Therefore:

```math
\boxed{
E \text{ determines the cut flow}
}
```

while:

```math
\boxed{
G \text{ determines the local sharing of that flow}
}
```

Using $G$ to calculate the transformed bending inertias or the partial first moments would mix two distinct mechanical roles and would not match the CSF model.

---

## 9. Numerical evaluation of the section

CSF evaluates two families of cuts:

- vertical cuts $x=c$, producing sampled $\tau_x$ values;
- horizontal cuts $y=c$, producing sampled $\tau_y$ values.

The scan coordinates combine:

1. a global uniform cell-centre grid over the complete active section bounding box;
2. additional one-sided coordinates concentrated near polygon bounding-box limits.

Exact polygon bounding-box coordinates are not evaluated. They are approached from both sides so that discontinuities caused by changes in chord composition can be resolved without evaluating directly on a geometric boundary.

For every valid cut, CSF:

1. clips the $E$-homogenized section to obtain $Q_x^{(E)}$ and $Q_y^{(E)}$;
2. calculates the total flow $q$;
3. determines the real geometric chord segments;
4. redistributes $q$ using the sampled shear carriers;
5. assigns each segment value to the corresponding polygon;
6. records the minimum and maximum sampled $\tau_x$ and $\tau_y$ for each polygon.

Values very close to zero at free boundaries may remain as small numerical residuals because the boundary itself is approached but not evaluated exactly.

---

## 10. Assumptions and limits

The CSF Jourawski model assumes:

- linear elastic sectional behaviour;
- a transformed-section representation based on $E$;
- longitudinal equilibrium derived from the Navier normal-stress field;
- line-average shear stress on each cut;
- a common mean shear strain among all material segments crossed by the same cut during the $G$-redistribution stage;
- perfect mechanical interaction at the sectional scale represented by the model.

The method does not directly resolve:

- the exact Saint-Venant shear-stress field;
- local interface slip;
- debonding;
- singular stresses at material corners;
- local warping effects not represented by the cut equilibrium;
- nonlinear material behaviour.

These effects require a more detailed two-dimensional or three-dimensional constitutive analysis.

---

## 11. Calculation sequence

At each coordinate $z$, the implemented sequence is:

1. resolve the complete CSF section $S(z)$;
2. choose the reference axial/bending carrier;
3. normalize the relative polygon weights and construct the $E$-homogenized section;
4. calculate $C_x$, $C_y$, $I_x$, $I_y$ and $I_{xy}$;
5. generate the vertical and horizontal cut coordinates;
6. calculate the transformed partial first moments for each cut;
7. calculate the total Jourawski flow:

```math
q=\beta_xQ_x^{(E)}+\beta_yQ_y^{(E)}
```

8. calculate the real geometric chord length;
9. calculate the reference mean stress:

   $$
   \tau_{\mathrm{ref}}=q/b_{\mathrm{tot}}
   $$

10. redistribute the flow among the crossed segments:

   $$
   \tau_i=q\,\frac{g_i}{\sum_jg_jb_j}
   $$

11. verify implicitly that:

   $$
   \sum_i\tau_i b_i=q
   $$

12. collect the polygon-wise sampled stress extrema.

---

## 12. Compact model statement

> CSF calculates the Jourawski shear flow on an $E$-homogenized resolved section. The transformed centroid, inertias and partial first moments determine the total flow transmitted through each geometric cut. The cut resultant is then redistributed among the material segments crossed by that cut in proportion to their sampled shear carrier, interpreted as $G$ or as a quantity proportional to $G$. This second operation assumes a common mean shear strain across the cut and preserves the Jourawski resultant exactly.

---

## 13. Implementation reference

Current implementation:

[`src/csf/section_field.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/section_field.py)

Primary function:

```python
analyse_polygon_jourawski_shear_stress(
    section_field,
    z,
    Tx,
    Ty,
    *,
    num_sudx=30,
    num_sudy=30,
    debug=False,
)
```
