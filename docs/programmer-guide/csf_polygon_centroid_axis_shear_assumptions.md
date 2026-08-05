# CSF polygon-wise global-centroid-axis shear

## Assumptions, formulation, implementation, and interpretation

This note documents the reduced shear-stress contribution implemented by:

```python
analyse_polygon_centroid_axis_shear(
    section_field,
    z,
    N,
    Mx,
    My,
    *,
    dz=None,
    derivative_rtol=1.0e-8,
    derivative_atol=1.0e-10,
    max_refinements=20,
    debug=False,
)
```

The method is intended for one-dimensional beam models in which the
axial-flexural centroid of the complete CSF section varies along the
longitudinal coordinate \(z\).

The implemented contribution is:

\[
\tau_x^{C}(x,y,z)
=
\sigma_{zz}(x,y,z)\frac{dC_x}{dz},
\]

\[
\tau_y^{C}(x,y,z)
=
\sigma_{zz}(x,y,z)\frac{dC_y}{dz},
\]

where:

- \(\sigma_{zz}\) is the polygon-wise CSF Navier normal stress;
- \(C_x(z)\) and \(C_y(z)\) are the coordinates of the **single global
  axial-flexural centroid** of the complete section;
- the superscript \(C\) identifies the contribution associated with the
  variation of the global centroid axis.

This is a reduced beam-theory approximation. It is not a complete
two-dimensional or three-dimensional elasticity solution.

---

## 1. Problem addressed

In a conventional prismatic beam, or in a beam whose section varies
symmetrically, the axial-flexural centroid normally remains on a fixed
reference line:

\[
\frac{dC_x}{dz}=0,
\qquad
\frac{dC_y}{dz}=0.
\]

The contribution documented here is then zero.

A CSF model can instead produce a moving axial-flexural centroid because
geometry and axial-flexural participation may vary continuously along
\(z\). Examples include:

- asymmetric taper;
- variable material distribution;
- longitudinally varying polygon `weight`;
- local deterioration or strengthening;
- activation or reduction of axial-flexural participation;
- combined geometric and material variation.

The complete centroid curve is:

\[
\mathbf C(z)
=
\begin{bmatrix}
C_x(z)\\
C_y(z)
\end{bmatrix}.
\]

The method uses its local slope:

\[
\mathbf C'(z)
=
\begin{bmatrix}
dC_x/dz\\
dC_y/dz
\end{bmatrix}.
\]

---

## 2. Central modelling choice

The implementation assumes that the already computed Navier axial stress
field is transported along the varying global centroid axis.

At one section, every axial-stress value is assigned the same transverse
directional slope:

\[
\left(
\frac{dC_x}{dz},
\frac{dC_y}{dz}
\right).
\]

This produces the local shear-stress contribution:

\[
\boldsymbol{\tau}^{C}
=
\sigma_{zz}\mathbf C'(z).
\]

The method therefore represents a **common translation of the axial
stress field with the global centroid curve**.

It does not calculate a separate longitudinal trajectory for every
polygon, vertex, material region, or fibre.

---

## 3. Interpretation from a slightly inclined axial-stress direction

A useful mechanical interpretation is obtained by considering an axial
stress direction tangent to the centroid curve.

The non-normalized tangent is:

\[
\widetilde{\mathbf t}
=
\begin{bmatrix}
dC_x/dz\\
dC_y/dz\\
1
\end{bmatrix}.
\]

For small centroid-axis slopes,

\[
\left|\frac{dC_x}{dz}\right|\ll 1,
\qquad
\left|\frac{dC_y}{dz}\right|\ll 1,
\]

the tangent direction is approximately:

\[
\mathbf t
\approx
\begin{bmatrix}
dC_x/dz\\
dC_y/dz\\
1
\end{bmatrix}.
\]

An axial traction aligned with this direction has first-order transverse
components:

\[
\tau_x^{C}
\approx
\sigma_{zz}\frac{dC_x}{dz},
\qquad
\tau_y^{C}
\approx
\sigma_{zz}\frac{dC_y}{dz}.
\]

This interpretation explains the implemented relation and also its main
limitation: it is a first-order, small-slope beam approximation.

For finite slopes, an exact directional transformation would contain
normalization factors and a distinction between stress measured along the
inclined direction and stress measured on the \(z=\text{constant}\)
section. Those higher-order effects are not included.

---

## 4. The centroid is global, not polygon-specific

The implementation calculates one centroid curve only:

\[
C_x(z),\qquad C_y(z).
\]

It does **not** calculate:

\[
C_{x,i}(z),\qquad C_{y,i}(z)
\]

for each polygon \(i\).

Consequently, it does not use:

\[
\frac{dC_{x,i}}{dz},
\qquad
\frac{dC_{y,i}}{dz}.
\]

Every polygon receives the same section-level derivatives:

\[
\frac{dC_x}{dz},
\qquad
\frac{dC_y}{dz}.
\]

The word `polygon` in the API refers to the polygon-wise reporting of the
stress extrema. It does not imply a polygon-centroid-axis formulation.

---

## 5. Calculation of the global CSF centroid

At every sampled coordinate \(z\), the implementation evaluates:

```python
section_field.section(z)
```

and passes the resulting section to:

```python
section_full_analysis(
    section,
    compute_vroark=False,
)
```

The global centroid is obtained from the complete axial-flexural section:

```python
Cx = analysis["Cx"]
Cy = analysis["Cy"]
```

The underlying section properties are calculated from the algebraic sum
of the weighted polygon contributions.

For nested polygons, CSF uses relative polygon weights in the section
representation. Conceptually:

\[
w_{\mathrm{rel,child}}
=
w_{\mathrm{abs,child}}
-
w_{\mathrm{abs,parent}}.
\]

This allows the global area, first moments, centroid, and second moments
to represent:

- different material regions;
- nested inclusions;
- regions with zero axial-flexural participation;
- holes represented through the CSF weighting convention.

The resulting \(C_x\) and \(C_y\) are therefore properties of the complete
axial-flexural CSF section, not of its unweighted geometric envelope.

---

## 6. Navier stress field used by the method

The function calls the public CSF Navier API once:

```python
navier_rows = analyse_polygon_navier_stress(
    section_field=section_field,
    z=z,
    N=N,
    Mx=Mx,
    My=My,
)
```

The Navier field is based on the global transformed section properties:

\[
A,\quad
C_x,\quad
C_y,\quad
I_x,\quad
I_y,\quad
I_{xy}.
\]

With:

\[
D=I_xI_y-I_{xy}^2,
\]

the implemented coefficients are:

\[
b_x
=
\frac{M_y I_x-M_x I_{xy}}{D},
\]

\[
b_y
=
\frac{M_x I_y-M_y I_{xy}}{D}.
\]

For polygon \(i\), the local CSF Navier stress quantity is:

\[
\sigma_{zz,i}(x,y)
=
w_i^{\mathrm{abs}}
\left[
\frac{N}{A}
+
b_x(x-C_x)
+
b_y(y-C_y)
\right].
\]

The polygon `weightabs` is already included by the Navier API.

The centroid-axis function must therefore **not multiply by
`weightabs` again**.

No `shear_weight` or `shear_weightabs` is used in this contribution.

---

## 7. Meaning of `weight` and `weightabs` in this workflow

Two distinct roles must remain separated.

### 7.1 Relative `weight`

The relative polygon `weight` is used by the algebraic section
integration. It permits nested polygons and differences between parent
and child participation.

It contributes to the calculation of:

\[
A,\quad
C_x,\quad
C_y,\quad
I_x,\quad
I_y,\quad
I_{xy}.
\]

### 7.2 Absolute `weightabs`

The absolute participation value `weightabs` is used when the local
Navier stress is assigned to a polygon.

It represents the axial-flexural carrier associated with that polygon
under the normalization adopted by the CSF model.

The units and physical interpretation of the returned stress require the
section carriers, applied actions, geometry, and unit system to be
mutually consistent.

---

## 8. Numerical derivative of the centroid curve

The method evaluates:

\[
\frac{dC_x}{dz},
\qquad
\frac{dC_y}{dz}
\]

with second-order finite differences.

### 8.1 Interior station

For a station sufficiently far from both CSF endpoints:

\[
\frac{dC_x}{dz}
\approx
\frac{C_x(z+h)-C_x(z-h)}{2h},
\]

\[
\frac{dC_y}{dz}
\approx
\frac{C_y(z+h)-C_y(z-h)}{2h}.
\]

The reported scheme is:

```text
central_second_order
```

### 8.2 Start station

At the first CSF endpoint:

\[
\frac{dC_x}{dz}
\approx
\frac{-3C_x(z)+4C_x(z+h)-C_x(z+2h)}{2h},
\]

with the analogous expression for \(C_y\).

The reported scheme is:

```text
forward_second_order
```

### 8.3 End station

At the final CSF endpoint:

\[
\frac{dC_x}{dz}
\approx
\frac{3C_x(z)-4C_x(z-h)+C_x(z-2h)}{2h},
\]

with the analogous expression for \(C_y\).

The reported scheme is:

```text
backward_second_order
```

---

## 9. Explicit and automatically converged derivative modes

### 9.1 Explicit `dz`

When the caller supplies:

```python
dz=<positive value>
```

the derivative is evaluated once with that step.

This mode is useful for:

- reproducible regression tests;
- analytical comparisons;
- deliberate smoothing over a prescribed longitudinal interval.

The returned metadata identifies:

```text
derivative_dz_mode = explicit
```

No numerical convergence claim is made.

### 9.2 Automatic convergence

When:

```python
dz=None
```

the implementation starts from:

\[
h_0=0.05L,
\]

where:

\[
L=z_{\mathrm{end}}-z_{\mathrm{start}}.
\]

The step is repeatedly halved:

\[
h_{k+1}=\frac{h_k}{2}.
\]

Convergence is required independently for both centroid components:

\[
\left|C'_{x,k+1}-C'_{x,k}\right|
\le
a_{\mathrm{tol}}
+
r_{\mathrm{tol}}
\max\left(
|C'_{x,k+1}|,
|C'_{x,k}|
\right),
\]

and similarly for \(C_y'\).

Default controls are:

```python
derivative_rtol = 1.0e-8
derivative_atol = 1.0e-10
max_refinements = 20
```

Automatic refinement checks numerical stability of the finite-difference
estimate. It does not prove that the underlying centroid curve is
physically smooth or differentiable.

---

## 10. Local centroid-axis shear field

Once the Navier stress extrema and centroid derivatives are available,
the polygon-wise contribution is:

\[
\tau_{x,i}^{C}
=
\sigma_{zz,i}\frac{dC_x}{dz},
\]

\[
\tau_{y,i}^{C}
=
\sigma_{zz,i}\frac{dC_y}{dz}.
\]

At a fixed station, \(dC_x/dz\) and \(dC_y/dz\) are section constants.

Therefore each component is an affine field over a polygon whenever the
Navier stress is affine.

---

## 11. Scaling polygon extrema

The public Navier API returns, for each polygon:

```text
sigma_min
sigma_max
sigma_extreme
```

with their coordinates.

Because the centroid derivative is constant over the section, the extrema
of each centroid-axis shear component can be obtained by scaling only
`sigma_min` and `sigma_max`.

For a positive scale:

\[
\tau_{\min}
=
\sigma_{\min}C',
\qquad
\tau_{\max}
=
\sigma_{\max}C'.
\]

For a negative scale, the ordering reverses:

\[
\tau_{\min}
=
\sigma_{\max}C',
\qquad
\tau_{\max}
=
\sigma_{\min}C'.
\]

The implementation avoids a sign-specific branch by constructing both
scaled candidates and selecting their signed minimum and maximum.

This is why a reported:

```text
tau_bound = max
```

may be generated by:

```text
source_navier_bound = sigma_min
```

when the relevant centroid derivative is negative.

---

## 12. Coordinates returned for polygon extrema

The centroid-axis API does not perform a new scan over the polygon area.

Its coordinates are inherited directly from the Navier extrema.

In the present Navier implementation, all polygon vertices are checked.
Therefore the reported centroid-axis extrema are located at:

```text
Navier-extreme polygon vertices
```

They are not:

- Jourawski cut-segment points;
- finite-element integration points;
- sampled interior points;
- polygon centroid locations.

If the relevant centroid derivative is exactly zero, the corresponding
centroid-axis shear component is zero everywhere. In that case, any
reported inherited coordinate is non-unique and should not be given
physical significance.

---

## 13. Treatment of holes and nested polygons

The global section properties account for the CSF nested-polygon
weighting convention.

The polygon-wise Navier API, however, reports extrema by checking the
vertices of every polygon separately.

For a child polygon strictly inside its parent:

- the global section properties include the child correctly;
- the child receives its own `weightabs`;
- a zero-participation hole receives zero local Navier stress;
- the affine Navier extrema of the parent remain on its external polygon
  vertices.

Therefore a strictly internal hole does not require its boundary vertices
to be added to the parent's extreme-value search.

A more specific geometric limitation exists if a child is permitted to
remove a governing vertex or a governing part of the parent's external
boundary. The current Navier extreme search still evaluates all original
parent vertices and does not explicitly reconstruct the parent's
exclusive occupied boundary.

This limitation concerns polygon-wise extreme localization. It does not
change the algebraic calculation of the global section properties.

---

## 14. Section resultants of the centroid-axis contribution

Over the physical occupied section, the Navier stress field satisfies:

\[
\int_A \sigma_{zz}\,dA=N.
\]

Since the centroid derivative is constant over the selected section:

\[
T_x^{C}
=
\int_A \tau_x^{C}\,dA
=
\frac{dC_x}{dz}
\int_A \sigma_{zz}\,dA,
\]

and therefore:

\[
\boxed{
T_x^{C}=N\frac{dC_x}{dz}
}
\]

Similarly:

\[
\boxed{
T_y^{C}=N\frac{dC_y}{dz}
}
\]

The bending part of the Navier field can produce non-zero local positive
and negative centroid-axis shear contributions, but its net force
integral is zero.

Consequently, the section resultant of this contribution depends on
\(N\), while its local distribution depends on:

\[
N,\quad M_x,\quad M_y.
\]

---

## 15. Decomposition of the external shear resultants

The method treats the shear resultants supplied by a structural solver or
prescribed by the user as total section resultants:

\[
T_x^{\mathrm{external}},
\qquad
T_y^{\mathrm{external}}.
\]

The adopted reduced decomposition is:

\[
T_x^{\mathrm{external}}
=
T_x^{J}
+
T_x^{C},
\]

\[
T_y^{\mathrm{external}}
=
T_y^{J}
+
T_y^{C},
\]

where:

- \(T^C\) is the global-centroid-axis contribution;
- \(T^J\) is the residual resultant assigned to the CSF Jourawski
  calculation.

Therefore Jourawski must receive:

\[
\boxed{
T_x^{J}
=
T_x^{\mathrm{external}}
-
N\frac{dC_x}{dz}
}
\]

\[
\boxed{
T_y^{J}
=
T_y^{\mathrm{external}}
-
N\frac{dC_y}{dz}
}
\]

A residual Jourawski resultant may have the opposite sign to the external
resultant. This is not an inconsistency. It means that the
global-centroid-axis contribution is larger and the residual contribution
must act in the opposite direction so that their resultant sum satisfies
equilibrium.

---

## 16. Relation to the CSF Jourawski calculation

The centroid-axis function and the Jourawski function represent different
reduced contributions.

### Global-centroid-axis contribution

\[
\boldsymbol{\tau}^{C}
=
\sigma_{zz}\mathbf C'(z).
\]

It uses:

- `weightabs`;
- the Navier axial-flexural field;
- the derivative of the global axial-flexural centroid.

It does not use:

- `shear_weight`;
- cut widths;
- first moments of partial areas;
- Jourawski scans.

### Jourawski residual contribution

The Jourawski calculation uses:

- residual section shear resultants;
- global cuts through the section;
- partial first moments;
- active cut widths;
- `shear_weightabs` redistribution.

It does not calculate the centroid-axis transport contribution
automatically.

The two functions are complementary within the adopted reduced
decomposition.

---

## 17. The two reported extrema must not be added

The Jourawski and centroid-axis APIs generally locate their extrema at
different physical points.

The centroid-axis coordinates are inherited from Navier polygon
vertices.

The Jourawski coordinates identify representative points of the scanned
cut segments.

Therefore this operation is generally invalid:

\[
\tau_{\max}^{\mathrm{total}}
\ne
\tau_{\max}^{J}
+
\tau_{\max}^{C}.
\]

A total local shear stress must be formed at the same point:

\[
\tau_x^{\mathrm{total}}(x,y)
=
\tau_x^{J}(x,y)
+
\tau_x^{C}(x,y),
\]

\[
\tau_y^{\mathrm{total}}(x,y)
=
\tau_y^{J}(x,y)
+
\tau_y^{C}(x,y).
\]

A governing total stress can be identified only after both contributions
have been evaluated on a common spatial sampling or through a common
field-evaluation API.

The current separate extreme-value APIs do not perform that final
same-point combination.

---

## 18. Required consistency with a beam solver

When section resultants come from an external beam solver, the following
conditions must hold.

### 18.1 Same coordinate system

The solver resultants and the CSF centroid derivatives must use the same
global section axes and sign convention.

### 18.2 Same reference-line interpretation

The solver shear resultants must represent the total section shear
resultants relative to the structural reference line used by the CSF
model.

### 18.3 No double counting

If a solver formulation already incorporates the effect of the varying
centroid line in its internal-force definition or kinematics, subtracting
\(N\mathbf C'(z)\) again may double count the effect.

The decomposition must therefore be documented for each solver coupling.

### 18.4 Section station consistency

The solver actions:

\[
N,\quad M_x,\quad M_y,\quad T_x,\quad T_y
\]

and the CSF section must refer to the same longitudinal coordinate \(z\).

---

## 19. Main mechanical assumptions

The adopted solution relies on the following assumptions.

### 19.1 One-dimensional beam representation

The member is represented by sectional resultants and continuously
varying cross-sections rather than by a full three-dimensional stress
solution.

### 19.2 Navier axial-flexural field

The axial stress is described by the CSF Navier formula. Effects not
represented by that field are also absent from the centroid-axis
contribution.

### 19.3 Small centroid-axis slopes

The relation:

\[
\boldsymbol{\tau}^{C}
=
\sigma_{zz}\mathbf C'
\]

is interpreted as a first-order directional approximation.

The implementation does not enforce a maximum value of
\(|\mathbf C'|\). The user must assess whether the centroid variation is
sufficiently gradual.

### 19.4 Smooth centroid curve

The centroid curve must be locally differentiable at the evaluation
station.

Continuous geometry interpolation does not by itself guarantee a smooth
centroid derivative if weights, topology, or user-defined laws contain
non-smooth changes.

### 19.5 Stable section topology over the derivative interval

The sections sampled at:

\[
z-h,\quad z,\quad z+h
\]

or at the corresponding one-sided coordinates must all be valid and
structurally consistent CSF sections.

### 19.6 Common transverse direction for the complete axial field

All local axial stress values are assigned the slope of the global
centroid axis.

The method does not model different longitudinal paths for different
polygons or fibres.

### 19.7 No local warping solution

The method does not solve for:

- cross-sectional warping;
- three-dimensional stress redistribution;
- free-edge boundary conditions;
- local shear concentrations;
- stress boundary layers near abrupt transitions.

### 19.8 No direct shear-carrier redistribution

The centroid-axis contribution follows `weightabs` through the Navier
field.

It is not redistributed according to `shear_weightabs`.

### 19.9 Consistent units

Geometry, actions, section carriers, and returned stresses must use one
consistent unit system.

---

## 20. Non-smooth or discontinuous centroid variation

If \(C(z)\) contains a discontinuity, the classical derivative does not
exist at that location.

For example, a step change in a polygon `weight` may cause a step change
in the global axial-flexural centroid.

A finite-difference estimate across that discontinuity produces a value
that depends on the selected step \(h\). It should not be interpreted as
a regular distributed shear stress.

Such a location is more appropriately treated as:

- a discrete interface;
- a concentrated transfer region;
- a local three-dimensional transition;
- or a separately regularized longitudinal law.

Automatic numerical convergence may fail near a discontinuity. If it
appears to converge because of numerical clipping or sampling placement,
that does not establish physical differentiability.

---

## 21. Abrupt geometric transitions

The formulation is most defensible for gradual longitudinal variation.

Near abrupt shoulders, notches, offsets, terminations, or sudden section
changes:

- local equilibrium becomes strongly two- or three-dimensional;
- the small-slope interpretation may fail;
- Saint-Venant-type boundary layers may dominate;
- the Navier field may not represent the actual local axial stress;
- the Jourawski field may not represent the actual local shear stress.

The method may still provide a one-dimensional indicator, but it should
not be presented as a local stress-concentration solution.

---

## 22. What the method does not calculate

The function does not calculate:

- a complete total shear-stress field;
- a combined Jourawski plus centroid-axis maximum;
- shear-centre effects;
- torsional shear stress;
- restrained-warping stress;
- shell or solid stress concentrations;
- interlaminar or interface shear transfer;
- polygon-specific centroid-axis derivatives;
- exact finite-slope stress transformation;
- nonlinear material redistribution;
- post-yield stress fields;
- local contact or connection effects.

These effects require separate formulations or higher-dimensional
analysis.

---

## 23. Output structure

The function returns:

```python
{
    "section": {...},
    "polygons": [...],
}
```

### 23.1 Section-level fields

The section dictionary contains:

```text
z
N
Mx
My
Cx
Cy
dCx_dz
dCy_dz
Tx_centroid_axis
Ty_centroid_axis
```

With `debug=True`, it also includes derivative metadata:

```text
derivative_step
derivative_scheme
derivative_dz_mode
derivative_converged
derivative_refinements
derivative_change_x
derivative_change_y
```

### 23.2 Polygon-level fields

Each polygon row contains:

```text
idx
name
weightabs

sigma_min
sigma_max
sigma_extreme

tau_x_min
tau_x_max
tau_y_min
tau_y_max

tau_governing
tau_governing_direction
tau_governing_bound
```

and the corresponding coordinates.

`tau_governing` is the largest absolute centroid-axis component among the
four signed extrema for that polygon.

It is not the governing total shear stress.

---

## 24. Recommended interpretation of the output

The output should be read in three levels.

### Level 1: axial-flexural state

```text
NAVIER
```

This reports the polygon-wise normal-stress extrema generated by:

\[
N,\quad M_x,\quad M_y.
\]

### Level 2: residual conventional shear contribution

```text
JOURAWSKI RESIDUAL SHEAR
```

This reports the shear contribution generated from:

\[
\mathbf T^{J}
=
\mathbf T^{\mathrm{external}}
-
N\mathbf C'(z).
\]

### Level 3: centroid-axis contribution

```text
GLOBAL CENTROID-AXIS SHEAR
```

This reports:

\[
\boldsymbol{\tau}^{C}
=
\sigma_{zz}\mathbf C'(z).
\]

The separately reported extrema at levels 2 and 3 must not be directly
added.

---

## 25. Internal consistency checks

The following checks are appropriate for every analysis.

### 25.1 Resultant decomposition

Verify:

\[
T_x^{\mathrm{external}}
\approx
T_x^{J}+T_x^{C},
\]

\[
T_y^{\mathrm{external}}
\approx
T_y^{J}+T_y^{C}.
\]

### 25.2 Symmetry

If the section and participation field remain symmetric about one axis,
the corresponding centroid coordinate and derivative should remain zero.

For example:

\[
C_x(z)=0
\quad\Rightarrow\quad
\frac{dC_x}{dz}=0
\quad\Rightarrow\quad
T_x^{C}=0.
\]

### 25.3 Prismatic field

For a longitudinally constant section and constant polygon
participation:

\[
\mathbf C'(z)=\mathbf 0,
\]

and the complete centroid-axis contribution must be zero.

### 25.4 Pure bending resultant

If:

\[
N=0,
\]

then:

\[
T_x^{C}=T_y^{C}=0.
\]

Local centroid-axis shear values may still be positive and negative
because the Navier bending stress is non-zero, but they must form a
self-equilibrated field with zero net transverse force.

### 25.5 Derivative-step sensitivity

Compare the automatic derivative with one or more explicit `dz` values.

Strong sensitivity indicates:

- insufficient smoothness;
- a discontinuity;
- a very sharp longitudinal transition;
- or numerical resolution limitations.

---

## 26. Verification cases already suited to the implementation

### 26.1 Constant geometry with varying polygon weights

A prismatic section split into multiple polygons can have constant
geometry but a moving axial-flexural centroid when polygon `weight` laws
vary along \(z\).

This isolates:

- weight-law evaluation;
- transformed centroid calculation;
- centroid differentiation;
- `weightabs` use in Navier stress;
- resultant closure.

### 26.2 Tapered asymmetric T-section

A T-section with a constant flange and a web whose depth changes along
\(z\) produces a varying \(C_y(z)\) while symmetry maintains:

\[
C_x(z)=0.
\]

This isolates:

- geometric centroid migration;
- one zero and one non-zero centroid derivative;
- decomposition of the external shear resultants;
- different coordinates for Jourawski and centroid-axis extrema.

---

## 27. Suitable use cases

The method is suitable as a reduced section-level model when:

- a one-dimensional beam representation is required;
- the axial-flexural centroid varies gradually;
- the Navier field is an acceptable approximation;
- the objective is to retain a centroid-migration contribution that
  would otherwise be omitted;
- section resultants are available from a compatible beam model;
- local three-dimensional stress concentrations are not the primary
  quantity of interest.

It is particularly relevant when centroid migration is caused by
continuous changes in CSF polygon geometry or participation rather than
by a manually prescribed beam-axis offset.

---

## 28. Cases requiring caution or a higher-dimensional model

A shell, solid, or specialized higher-order formulation should be
considered when:

- centroid slopes are not small;
- the section changes abruptly;
- local free-edge conditions are important;
- warping is significant;
- material interfaces require explicit shear transfer;
- the section topology changes;
- local peak stress is a design-critical quantity;
- the solver reference-line formulation makes the force decomposition
  ambiguous;
- the centroid curve is discontinuous or non-differentiable.

---

## 29. Concise formulation statement

The implemented CSF method can be summarized as follows:

> The polygon-wise global-centroid-axis shear contribution is a reduced
> beam-theory approximation obtained by transporting the CSF Navier
> axial-stress field along the derivative of the single global
> axial-flexural centroid curve. The method produces
> \(\boldsymbol{\tau}^{C}=\sigma_{zz}\mathbf C'(z)\) and the corresponding
> section resultant \(\mathbf T^{C}=N\mathbf C'(z)\). The residual external
> shear resultant is assigned to the separate CSF Jourawski calculation.
> The two local contributions must be combined at common physical points,
> not by adding their separately reported extrema.

---

## 30. Implementation boundary

The implementation is internally consistent with its declared reduced
model when:

1. the global CSF centroid is evaluated from the complete axial-flexural
   section;
2. its derivative is numerically stable;
3. the public Navier stress already includes `weightabs`;
4. no second `weightabs` factor is applied;
5. the centroid-axis resultants are calculated as
   \(N\,dC_x/dz\) and \(N\,dC_y/dz\);
6. Jourawski receives only the residual external shear;
7. separately located extrema are not directly summed;
8. the user accepts the small-slope, beam-theory, and smooth-variation
   assumptions documented above.
