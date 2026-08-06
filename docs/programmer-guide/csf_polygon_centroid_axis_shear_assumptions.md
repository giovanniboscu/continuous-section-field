# DRAFT

# CSF polygon-wise flexural global-centroid-axis shear

## Assumptions, formulation, implementation, and interpretation

This note documents the reduced shear-stress contribution implemented by:

```python
analyse_polygon_centroid_axis_shear(
    section_field,
    z,
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

The method is intended for one-dimensional beam models in which the global
axial-flexural centroid of the complete Continuous Section Field (CSF) section
varies along the longitudinal coordinate $z$.

The implemented contribution is:

```math
\tau_x^{C}(x,y,z)
=
\sigma_{zz}^{M}(x,y,z)\frac{dC_x}{dz},
```

```math
\tau_y^{C}(x,y,z)
=
\sigma_{zz}^{M}(x,y,z)\frac{dC_y}{dz},
```

where:

- $\sigma_{zz}^{M}$ is the polygon-wise **flexural** CSF Navier normal-stress
  field evaluated from $M_x$ and $M_y$ with $N=0$;
- $C_x(z)$ and $C_y(z)$ are the coordinates of the single global
  axial-flexural centroid of the complete CSF section;
- the superscript $C$ identifies the contribution associated with variation
  of the global centroid curve.

This is a reduced beam-theory approximation. It is not a complete
two-dimensional or three-dimensional elasticity solution.

---

## 1. Problem addressed

For a prismatic beam, or for a longitudinally varying beam whose transformed
section remains symmetric about a fixed reference line, the global
axial-flexural centroid may remain constant:

```math
\frac{dC_x}{dz}=0,
\qquad
\frac{dC_y}{dz}=0.
```

The contribution documented here is then zero.

A CSF model can instead produce a moving global centroid because geometry and
axial-flexural participation may vary continuously along $z$. Typical causes
include:

- asymmetric taper;
- variable material distribution;
- longitudinally varying polygon `weight`;
- local deterioration or strengthening;
- activation or reduction of axial-flexural participation;
- combined geometric and participation changes.

The global centroid curve is:

```math
\mathbf C(z)
=
\begin{bmatrix}
C_x(z)\\
C_y(z)
\end{bmatrix},
```

and its local slope is:

```math
\mathbf C'(z)
=
\begin{bmatrix}
dC_x/dz\\
dC_y/dz
\end{bmatrix}.
```

The method uses this section-level slope to convert the flexural Navier field
into an additional local tangential contribution.

---

## 2. Section actions used by the stress APIs

The stress analyses involved in the complete workflow use two different sets
of section actions.

### 2.1 Complete Navier normal-stress analysis

The complete Navier field may be evaluated from:

```math
N,
\qquad
M_x,
\qquad
M_y.
```

It is denoted here by:

```math
\sigma_{zz}^{N+M}(x,y,z).
```

This field is useful for reporting the complete axial-flexural normal stress
at the selected station.

### 2.2 Flexural global-centroid-axis contribution

The centroid-axis shear function uses only:

```math
M_x,
\qquad
M_y.
```

Internally it evaluates the Navier field with:

```math
N=0.
```

The resulting normal-stress field is denoted by:

```math
\sigma_{zz}^{M}(x,y,z).
```

This distinction is essential:

```math
\sigma_{zz}^{N+M}
\neq
\sigma_{zz}^{M}
```

when $N\neq 0$.

### 2.3 Jourawski shear-stress analysis

Jourawski receives the section shear resultants:

```math
T_x,
\qquad
T_y,
```

obtained from beam equilibrium with the external actions.

Under the CSF component convention:

- $T_x$ is associated with the longitudinal variation of $M_y$;
- $T_y$ is associated with the longitudinal variation of $M_x$.

The exact signs depend on the adopted beam and solver convention. In the
corresponding convention, the equilibrium relations have the form:

```math
T_x \sim \frac{dM_y}{dz},
\qquad
T_y \sim \frac{dM_x}{dz}.
```

The section resultants are passed to Jourawski directly.

---

## 3. Central modelling choice

The implementation assumes that the flexural Navier normal-stress field is
transported along the varying global centroid curve.

At one section, every flexural normal-stress value is assigned the same
transverse directional slope:

```math
\left(
\frac{dC_x}{dz},
\frac{dC_y}{dz}
\right).
```

This produces:

```math
\boldsymbol{\tau}^{C}
=
\sigma_{zz}^{M}\mathbf C'(z).
```

The method therefore represents a common translation of the flexural
normal-stress field with the single global centroid curve.

It does not calculate a separate longitudinal trajectory for every polygon,
vertex, material region, or fibre.

---

## 4. Interpretation from a slightly inclined flexural-stress direction

A useful reduced mechanical interpretation is obtained by considering a
flexural stress direction tangent to the global centroid curve.

The non-normalized tangent is:

```math
\widetilde{\mathbf t}
=
\begin{bmatrix}
dC_x/dz\\
dC_y/dz\\
1
\end{bmatrix}.
```

For small centroid slopes,

```math
\left|\frac{dC_x}{dz}\right|\ll 1,
\qquad
\left|\frac{dC_y}{dz}\right|\ll 1,
```

the tangent direction is approximated by:

```math
\mathbf t
\approx
\begin{bmatrix}
dC_x/dz\\
dC_y/dz\\
1
\end{bmatrix}.
```

A flexural traction aligned with this direction has first-order transverse
components:

```math
\tau_x^{C}
\approx
\sigma_{zz}^{M}\frac{dC_x}{dz},
```

```math
\tau_y^{C}
\approx
\sigma_{zz}^{M}\frac{dC_y}{dz}.
```

This interpretation explains both the implemented relation and its principal
limitation: it is a first-order, small-slope beam approximation.

For finite slopes, an exact directional transformation would require
normalization factors and a precise distinction between stress components
measured along the inclined direction and tractions acting on the
$z=\text{constant}$ section. Those higher-order effects are not included.

---

## 5. The centroid is global, not polygon-specific

The implementation calculates one centroid curve:

```math
C_x(z),
\qquad
C_y(z).
```

It does not calculate polygon-specific curves:

```math
C_{x,i}(z),
\qquad
C_{y,i}(z).
```

Consequently, it does not use:

```math
\frac{dC_{x,i}}{dz},
\qquad
\frac{dC_{y,i}}{dz}.
```

Every polygon receives the same section-level derivatives:

```math
\frac{dC_x}{dz},
\qquad
\frac{dC_y}{dz}.
```

The word `polygon` in the API refers to polygon-wise reporting of the stress
extrema. It does not imply a polygon-centroid-axis formulation.

---

## 6. Calculation of the global CSF centroid

At every sampled coordinate $z$, the implementation evaluates:

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

The global centroid is obtained from:

```python
Cx = analysis["Cx"]
Cy = analysis["Cy"]
```

The underlying section properties are calculated from the algebraic sum of
the weighted polygon contributions.

For nested polygons, CSF uses relative polygon weights in the section
representation. Conceptually:

```math
w_{\mathrm{rel,child}}
=
w_{\mathrm{abs,child}}
-
w_{\mathrm{abs,parent}}.
```

This allows the global area, first moments, centroid, and second moments to
represent:

- different material regions;
- nested inclusions;
- regions with zero axial-flexural participation;
- holes represented through the CSF weighting convention.

The resulting $C_x$ and $C_y$ are properties of the complete transformed
axial-flexural CSF section, not of its unweighted geometric envelope.

---

## 7. Flexural Navier field used by the method

The centroid-axis function calls the public Navier API once:

```python
navier_rows = analyse_polygon_navier_stress(
    section_field=section_field,
    z=z,
    N=0.0,
    Mx=Mx,
    My=My,
)
```

The flexural field is based on the global transformed section properties:

```math
A,
\quad
C_x,
\quad
C_y,
\quad
I_x,
\quad
I_y,
\quad
I_{xy}.
```

Define:

```math
D=I_xI_y-I_{xy}^2.
```

The flexural coefficients are:

```math
b_x
=
\frac{M_yI_x-M_xI_{xy}}{D},
```

```math
b_y
=
\frac{M_xI_y-M_yI_{xy}}{D}.
```

For polygon $i$, the local CSF flexural Navier quantity is:

```math
\sigma_{zz,i}^{M}(x,y)
=
w_i^{\mathrm{abs}}
\left[
 b_x(x-C_x)
+
 b_y(y-C_y)
\right].
```

The polygon `weightabs` is already included by the Navier API.

The centroid-axis function must therefore not multiply the returned values by
`weightabs` again.

No `shear_weight` or `shear_weightabs` is used in this contribution.

---

## 8. Local flexural centroid-axis shear field

Once the flexural Navier extrema and global centroid derivatives are
available, the polygon-wise contribution is:

```math
\tau_{x,i}^{C}
=
\sigma_{zz,i}^{M}\frac{dC_x}{dz},
```

```math
\tau_{y,i}^{C}
=
\sigma_{zz,i}^{M}\frac{dC_y}{dz}.
```

At a fixed station, $dC_x/dz$ and $dC_y/dz$ are section constants.

Therefore each component is affine over a polygon whenever the flexural
Navier field is affine.

---

## 9. Self-equilibrated character of the contribution

The flexural Navier field has zero axial resultant over the complete
transformed occupied section:

```math
\int_A \sigma_{zz}^{M}\,dA=0.
```

Since the centroid derivative is constant over the selected section:

```math
\int_A \tau_x^{C}\,dA
=
\frac{dC_x}{dz}
\int_A \sigma_{zz}^{M}\,dA
=0,
```

and:

```math
\int_A \tau_y^{C}\,dA
=
\frac{dC_y}{dz}
\int_A \sigma_{zz}^{M}\,dA
=0.
```

Hence:

```math
\boxed{
\int_A \boldsymbol{\tau}^{C}\,dA
=
\mathbf 0
}
```

The field may contain non-zero positive and negative local values, but its net
transverse force is zero.

This is why the contribution can coexist with the Jourawski field without
modifying the section shear resultants passed to Jourawski.

---

## 10. Role of axial force and beam equilibrium

The function receives only $M_x$ and $M_y$.

Axial-force effects belong to the complete axial-flexural stress analysis and
to the beam-level equilibrium and moment definition.

After the beam model has determined the internal section moments and their
longitudinal derivatives, the resulting section shear actions are represented
by:

```math
T_x,
\qquad
T_y.
```

Those actions are then passed directly to Jourawski.

In other words:

- beam equilibrium determines the section shear resultants;
- Jourawski recovers the shear field associated with those resultants;
- the centroid-axis function adds the separate self-equilibrated field
  generated by $\sigma_{zz}^{M}\mathbf C'(z)$.

The centroid-axis function does not modify the beam equilibrium resultants.

---

## 11. Relation to `analyse_polygon_jourawski_shear_stress()`

The centroid-axis function and the Jourawski function are independent
section-level APIs.

### 11.1 Flexural global-centroid-axis contribution

```math
\boldsymbol{\tau}^{C}
=
\sigma_{zz}^{M}\mathbf C'(z).
```

It uses:

- `weightabs` through the flexural Navier field;
- $M_x$ and $M_y$;
- the derivative of the global axial-flexural centroid.

It does not use:

- $N$;
- $T_x$ or $T_y$;
- `shear_weight` or `shear_weightabs`;
- cut widths;
- partial first moments;
- Jourawski scans.

### 11.2 Jourawski contribution

`analyse_polygon_jourawski_shear_stress()` receives:

```python
Tx
Ty
```

and uses those values directly.

With:

```math
D=I_xI_y-I_{xy}^2,
```

the function forms:

```math
\frac{db_x}{dz}
=
\frac{T_xI_x-T_yI_{xy}}{D},
```

```math
\frac{db_y}{dz}
=
\frac{T_yI_y-T_xI_{xy}}{D}.
```

The remaining Jourawski calculation uses:

- global cuts through the section;
- partial first moments;
- active cut widths;
- `shear_weightabs` redistribution;
- the scan resolutions `num_sudx` and `num_sudy`.

The inputs are:

```math
\boxed{
T_x^{J,\mathrm{input}}=T_x,
\qquad
T_y^{J,\mathrm{input}}=T_y
}
```

The supplied section shear resultants are used unchanged.

---

## 12. Pointwise combination of the two shear fields

The complete reduced shear field is represented as:

```math
\boldsymbol{\tau}^{\mathrm{total}}(x,y,z)
=
\boldsymbol{\tau}^{J}(x,y,z)
+
\boldsymbol{\tau}^{C}(x,y,z).
```

For the global components:

```math
\tau_x^{\mathrm{total}}(x,y,z)
=
\tau_x^{J}(x,y,z)
+
\tau_x^{C}(x,y,z),
```

```math
\tau_y^{\mathrm{total}}(x,y,z)
=
\tau_y^{J}(x,y,z)
+
\tau_y^{C}(x,y,z).
```

The two fields must be evaluated at the same physical point before they are
added.

Their separately reported extrema are generally located at different points.
Therefore:

```math
\tau_{\max}^{\mathrm{total}}
\neq
\tau_{\max}^{J}
+
\tau_{\max}^{C}
```

in general.

A governing total stress requires a common spatial sampling or a common
point-evaluation API.

---

## 13. Meaning of `weight` and `weightabs`

Two different roles must remain separated.

### 13.1 Relative `weight`

The relative polygon `weight` is used by the algebraic section integration.
It supports nested polygons and differences between parent and child
participation.

It contributes to the calculation of:

```math
A,
\quad
C_x,
\quad
C_y,
\quad
I_x,
\quad
I_y,
\quad
I_{xy}.
```

### 13.2 Absolute `weightabs`

The absolute participation value `weightabs` is used when the local flexural
Navier stress is assigned to a polygon.

It represents the axial-flexural carrier associated with that polygon under
the normalization adopted by the CSF model.

The units and physical interpretation of the returned stresses require the
section carriers, applied moments, geometry, and unit system to be mutually
consistent.

---

## 14. Numerical derivative of the centroid curve

The method evaluates:

```math
\frac{dC_x}{dz},
\qquad
\frac{dC_y}{dz}
```

with second-order finite differences.

### 14.1 Interior station

For a station sufficiently far from both CSF endpoints:

```math
\frac{dC_x}{dz}
\approx
\frac{C_x(z+h)-C_x(z-h)}{2h},
```

```math
\frac{dC_y}{dz}
\approx
\frac{C_y(z+h)-C_y(z-h)}{2h}.
```

The reported scheme is:

```text
central_second_order
```

### 14.2 Start station

At the first CSF endpoint:

```math
\frac{dC_x}{dz}
\approx
\frac{-3C_x(z)+4C_x(z+h)-C_x(z+2h)}{2h},
```

with the analogous expression for $C_y$.

The reported scheme is:

```text
forward_second_order
```

### 14.3 End station

At the final CSF endpoint:

```math
\frac{dC_x}{dz}
\approx
\frac{3C_x(z)-4C_x(z-h)+C_x(z-2h)}{2h},
```

with the analogous expression for $C_y$.

The reported scheme is:

```text
backward_second_order
```

---

## 15. Explicit and automatically converged derivative modes

### 15.1 Explicit `dz`

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

### 15.2 Automatic convergence

When:

```python
dz=None
```

the implementation starts from:

```math
h_0=0.05L,
```

where:

```math
L=z_{\mathrm{end}}-z_{\mathrm{start}}.
```

The step is repeatedly halved:

```math
h_{k+1}=\frac{h_k}{2}.
```

Convergence is required independently for both centroid components:

```math
\left|C'_{x,k+1}-C'_{x,k}\right|
\le
 a_{\mathrm{tol}}
+
 r_{\mathrm{tol}}
\max\left(
|C'_{x,k+1}|,
|C'_{x,k}|
\right),
```

and similarly for $C_y'$.

Default controls are:

```python
derivative_rtol = 1.0e-8
derivative_atol = 1.0e-10
max_refinements = 20
```

Automatic refinement checks numerical stability of the finite-difference
estimate. It does not prove that the underlying centroid curve is physically
smooth or differentiable.

---

## 16. Encapsulation and centroid cache

The derivative helpers are defined inside
`analyse_polygon_centroid_axis_shear()` so that the complete workflow remains
encapsulated in the public function.

The internal operations include:

- global centroid evaluation;
- finite-difference sampling;
- automatic derivative convergence;
- scaling of flexural Navier extrema.

Centroid evaluations are cached per `section_field` and per sampled station.
The cache uses a `weakref.WeakKeyDictionary` owned by the public function.

This design has two purposes:

1. repeated derivative refinements can reuse centroid values already
   evaluated at the same stations;
2. cached entries associated with a `section_field` can be released when that
   object is no longer referenced elsewhere.

The cache is a process-local Python object. It is not shared memory and it is
not a cross-process cache.

---

## 17. Scaling polygon extrema

The internal flexural Navier call returns, for each polygon:

```text
sigma_min
sigma_max
sigma_extreme
```

with their coordinates.

Within the centroid-axis result, these values refer to:

```math
\sigma_{zz}^{M},
```

not to the complete field $\sigma_{zz}^{N+M}$.

Because the centroid derivative is constant over the section, the extrema of
each centroid-axis component can be obtained by scaling only
`sigma_min` and `sigma_max`.

For a positive scale:

```math
\tau_{\min}
=
\sigma_{\min}^{M}C',
\qquad
\tau_{\max}
=
\sigma_{\max}^{M}C'.
```

For a negative scale, the ordering reverses:

```math
\tau_{\min}
=
\sigma_{\max}^{M}C',
\qquad
\tau_{\max}
=
\sigma_{\min}^{M}C'.
```

This is why a reported:

```text
tau_bound = max
```

may be generated by:

```text
source_flexural_navier_bound = sigma_flexural_min
```

when the relevant centroid derivative is negative.

---

## 18. Coordinates returned for polygon extrema

The centroid-axis API does not perform a new scan over the polygon area.

Its coordinates are inherited directly from the flexural Navier extrema.

In the present Navier implementation, all polygon vertices are checked.
Therefore the reported centroid-axis extrema are located at:

```text
flexural-Navier-extreme polygon vertices
```

They are not:

- Jourawski cut-segment points;
- finite-element integration points;
- sampled interior points;
- polygon centroid locations.

If the relevant centroid derivative is exactly zero, the corresponding
centroid-axis shear component is zero everywhere. In that case, any inherited
coordinate is non-unique and should not be given physical significance.

---

## 19. Meaning of `tau_governing`

For each polygon, the API considers the four signed extrema:

```math
\tau_{x,\min}^{C},
\quad
\tau_{x,\max}^{C},
\quad
\tau_{y,\min}^{C},
\quad
\tau_{y,\max}^{C}.
```

It selects the value with the largest absolute magnitude while preserving its
sign:

```math
\tau_{\mathrm{governing}}^{C}
=
\operatorname*{arg\,max}_{\tau\in\mathcal E_i}|\tau|,
```

where:

```math
\mathcal E_i
=
\left\{
\tau_{x,\min}^{C},
\tau_{x,\max}^{C},
\tau_{y,\min}^{C},
\tau_{y,\max}^{C}
\right\}
```

for polygon $i$.

The returned metadata identifies:

```text
tau_governing
tau_governing_direction
tau_governing_bound
x_tau_governing
y_tau_governing
```

`tau_governing` means:

> the signed flexural centroid-axis shear component with the largest absolute
> magnitude among the four reported extrema for that polygon.

It is not:

- the maximum total shear stress;
- a sum with Jourawski;
- a section shear resultant;
- a single governing value for the complete section.

---

## 20. Treatment of holes and nested polygons

The global section properties account for the CSF nested-polygon weighting
convention.

The polygon-wise Navier API reports extrema by checking the vertices of every
polygon separately.

For a child polygon strictly inside its parent:

- the global section properties include the child through the CSF weighting
  convention;
- the child receives its own `weightabs`;
- a zero-participation hole receives zero local flexural Navier stress;
- the affine flexural Navier extrema of the parent remain on its external
  polygon vertices.

A geometric limitation exists if a child removes a governing vertex or a
governing part of the parent's external occupied boundary. The current
polygon-wise extreme search still evaluates the original parent vertices and
does not reconstruct the parent's exclusive occupied boundary.

This limitation concerns extreme localization. It does not change the
algebraic calculation of the global section properties.

---

## 21. Output structure

The function returns:

```python
{
    "section": {...},
    "polygons": [...],
}
```

### 21.1 Section-level fields

The section dictionary contains:

```text
z
Mx
My
Cx
Cy
dCx_dz
dCy_dz
```

With `debug=True`, it also contains:

```text
derivative_step
derivative_scheme
derivative_dz_mode
derivative_converged
derivative_refinements
derivative_change_x
derivative_change_y
```

### 21.2 Polygon-level fields

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

Within this result:

```text
sigma_min
sigma_max
sigma_extreme
```

refer to the flexural Navier field evaluated with $N=0$.

They should be labelled as flexural values when printed beside a separate
complete Navier result.

---

## 22. Recommended interpretation of a combined example

When the complete Navier, Jourawski, and centroid-axis APIs are used in the
same example, the output should be read in three separate blocks.

### 22.1 Complete axial-flexural normal stress

```text
NAVIER COMPLETE: N + Mx + My
```

This reports the polygon-wise complete normal-stress extrema generated by:

```math
N,
\qquad
M_x,
\qquad
M_y.
```

### 22.2 Jourawski shear

```text
JOURAWSKI SHEAR
```

This reports the shear field generated from the section shear resultants:

```math
T_x,
\qquad
T_y.
```

The values are passed directly to the Jourawski API.

### 22.3 Flexural global-centroid-axis shear

```text
FLEXURAL GLOBAL CENTROID-AXIS SHEAR
```

This reports:

```math
\boldsymbol{\tau}^{C}
=
\sigma_{zz}^{M}\mathbf C'(z).
```

The associated `sigma_min` and `sigma_max` values are flexural-only values
evaluated with $N=0$.

The separately reported Jourawski and centroid-axis extrema must not be added
directly.

---

## 23. Internal consistency checks

The following checks are appropriate for every analysis.

### 23.1 Symmetry

If the transformed section remains symmetric about one global axis, the
corresponding centroid coordinate and derivative should remain zero.

For example:

```math
C_x(z)=0
\quad\Rightarrow\quad
\frac{dC_x}{dz}=0
\quad\Rightarrow\quad
\tau_x^{C}=0.
```

### 23.2 Prismatic field

For a longitudinally constant section with constant polygon participation:

```math
\mathbf C'(z)=\mathbf 0,
```

and the complete centroid-axis contribution must be zero:

```math
\boldsymbol{\tau}^{C}=\mathbf 0.
```

### 23.3 Zero bending moments

If:

```math
M_x=0,
\qquad
M_y=0,
```

then:

```math
\sigma_{zz}^{M}=0
```

and therefore:

```math
\boldsymbol{\tau}^{C}=\mathbf 0.
```

### 23.4 Self-equilibrium

A numerical integration over the complete transformed occupied section should
satisfy:

```math
\int_A \tau_x^{C}\,dA\approx0,
```

```math
\int_A \tau_y^{C}\,dA\approx0.
```

The tolerance should reflect the polygon integration and floating-point
accuracy used by the implementation.

### 23.5 Derivative-step sensitivity

Compare the automatically converged derivative with one or more explicit
`dz` values.

Strong sensitivity may indicate:

- insufficient smoothness;
- a discontinuity;
- a very sharp longitudinal transition;
- numerical resolution limitations.

### 23.6 Jourawski input identity

The values printed as Jourawski inputs should be exactly the section shear
resultants supplied by the caller:

```math
T_x^{J,\mathrm{input}}=T_x,
```

```math
T_y^{J,\mathrm{input}}=T_y.
```

---

## 24. Verification cases suited to the implementation

### 24.1 Constant geometry with varying polygon weights

A prismatic geometry split into multiple polygons can have a moving global
axial-flexural centroid when polygon `weight` laws vary along $z$.

This case isolates:

- weight-law evaluation;
- transformed centroid calculation;
- centroid differentiation;
- use of `weightabs` in the flexural Navier field;
- self-equilibrium of the centroid-axis shear contribution.

### 24.2 Tapered asymmetric T-section

A T-section with a constant flange and a web whose depth changes along $z$
produces a varying $C_y(z)$ while symmetry maintains:

```math
C_x(z)=0.
```

The expected consequences are:

```math
\frac{dC_x}{dz}=0,
\qquad
\frac{dC_y}{dz}\neq 0,
```

and therefore:

```math
\tau_x^{C}=0,
\qquad
\tau_y^{C}\neq 0.
```

This case isolates:

- geometric centroid migration;
- one zero and one non-zero centroid derivative;
- flexural Navier scaling;
- different coordinates for Jourawski and centroid-axis extrema.

### 24.3 Pure $M_x$ or pure $M_y$

A single non-zero bending component allows the sign and coordinate mapping of
the flexural Navier extrema to be checked independently.

### 24.4 Constant centroid with varying inertia

A section may vary longitudinally while preserving a fixed global centroid.
In that case:

```math
\mathbf C'(z)=\mathbf{0}
```

and this contribution must remain zero even though $I_x$, $I_y$, or
$I_{xy}$ vary with $z$.

---

## 25. Main mechanical assumptions

### 25.1 One-dimensional beam representation

The member is represented through section actions and continuously varying
cross-sections rather than through a full three-dimensional stress solution.

### 25.2 Flexural Navier field

The local normal stress used by the method is the CSF flexural Navier field.
Effects not represented by that field are absent from the centroid-axis
contribution.

### 25.3 Small centroid-axis slopes

The relation:

```math
\boldsymbol{\tau}^{C}
=
\sigma_{zz}^{M}\mathbf C'
```

is interpreted as a first-order directional approximation.

The implementation does not enforce a maximum value of $|\mathbf C'|$.
The user must assess whether the centroid variation is sufficiently gradual.

### 25.4 Smooth centroid curve

The centroid curve must be locally differentiable at the evaluation station.

Continuous geometry interpolation does not by itself guarantee a smooth
centroid derivative when weights, topology, or user-defined laws contain
non-smooth changes.

### 25.5 Stable section topology over the derivative interval

The sections sampled at:

```math
z-h,
\qquad
z,
\qquad
z+h
```

or at the corresponding one-sided stations must all be valid and
structurally consistent CSF sections.

### 25.6 Common transverse direction for the complete flexural field

All local flexural normal-stress values are assigned the slope of the single
global centroid curve.

The method does not model different longitudinal paths for different
polygons or fibres.

### 25.7 No local warping solution

The method does not solve for:

- cross-sectional warping;
- three-dimensional stress redistribution;
- free-edge boundary conditions;
- local shear concentrations;
- stress boundary layers near abrupt transitions.

### 25.8 No direct shear-carrier redistribution

The centroid-axis contribution follows `weightabs` through the flexural
Navier field.

It is not redistributed according to `shear_weightabs`.

### 25.9 Consistent units

Geometry, moments, section carriers, and returned stresses must use one
consistent unit system.

---

## 26. Non-smooth or discontinuous centroid variation

If $\mathbf C(z)$ contains a discontinuity, the classical derivative does not
exist at that location.

For example, a step change in polygon `weight` may cause a step change in the
global axial-flexural centroid.

A finite-difference estimate across that discontinuity produces a value that
depends on the selected step $h$. It should not be interpreted as a regular
distributed shear stress.

Such a location is more appropriately treated as:

- a discrete interface;
- a concentrated transfer region;
- a local three-dimensional transition;
- a separately regularized longitudinal law.

Automatic numerical convergence may fail near a discontinuity. Apparent
numerical stability alone does not establish physical differentiability.

---

## 27. Abrupt geometric transitions

The formulation is most defensible for gradual longitudinal variation.

Near abrupt shoulders, notches, offsets, terminations, or sudden section
changes:

- local equilibrium becomes strongly two- or three-dimensional;
- the small-slope interpretation may fail;
- Saint-Venant-type boundary layers may dominate;
- the Navier field may not represent the actual local normal stress;
- the Jourawski field may not represent the actual local shear stress.

The method may still provide a one-dimensional indicator, but it should not
be presented as a local stress-concentration solution.

---

## 28. What the method does not calculate

The function does not calculate:

- the complete Navier field generated by $N$, $M_x$, and $M_y$;
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

These effects require separate formulations or higher-dimensional analysis.

---

## 29. Suitable use cases

The method is suitable as a reduced section-level model when:

- a one-dimensional beam representation is required;
- the global axial-flexural centroid varies gradually;
- the flexural Navier field is an acceptable approximation;
- the objective is to retain a self-equilibrated centroid-migration
  contribution that would otherwise be omitted;
- section shear resultants are available from a compatible beam model;
- local three-dimensional stress concentrations are not the primary quantity
  of interest.

It is particularly relevant when centroid migration is caused by continuous
changes in CSF polygon geometry or axial-flexural participation rather than by
a manually prescribed beam-axis offset.

---

## 30. Cases requiring caution or a higher-dimensional model

A shell, solid, or specialized higher-order formulation should be considered
when:

- centroid slopes are not small;
- the section changes abruptly;
- local free-edge conditions are important;
- warping is significant;
- material interfaces require explicit shear transfer;
- the section topology changes;
- local peak stress is a design-critical quantity;
- the centroid curve is discontinuous or non-differentiable.

---

## 31. Concise formulation statement

The implemented CSF method can be summarized as follows:

> The polygon-wise flexural global-centroid-axis shear contribution is a
> reduced beam-theory approximation obtained by transporting the CSF
> flexural Navier normal-stress field along the derivative of the single
> global axial-flexural centroid curve. The function evaluates the Navier
> field from $M_x$ and $M_y$ with $N=0$ and produces
> $\boldsymbol{\tau}^{C}=\sigma_{zz}^{M}\mathbf C'(z)$. This contribution is
> self-equilibrated over the complete transformed occupied section. The
> separate Jourawski API receives the section shear resultants $T_x$ and
> $T_y$ directly. The two local fields may be combined only at common
> physical points, not by adding their separately reported extrema.

---

## 32. Implementation boundary

The implementation is internally consistent with its declared reduced model
when:

1. the global CSF centroid is evaluated from the complete transformed
   axial-flexural section;
2. its derivative is numerically stable;
3. the internal Navier call uses $N=0$ and the prescribed $M_x$, $M_y$;
4. the public Navier stress already includes `weightabs`;
5. no second `weightabs` factor is applied;
6. the local contribution is evaluated as
   $\boldsymbol{\tau}^{C}=\sigma_{zz}^{M}\mathbf C'(z)$;
7. the centroid-axis field integrates to zero transverse resultant within
   numerical tolerance;
8. Jourawski receives the supplied section shear resultants $T_x$, $T_y$
   directly;
9. separately located extrema are not directly summed;
10. the user accepts the small-slope, beam-theory, and smooth-variation
    assumptions documented above.
