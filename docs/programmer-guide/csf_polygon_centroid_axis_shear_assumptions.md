# Polygon centroid-axis shear in CSF

## Purpose

The function

```python
analyse_polygon_centroid_axis_shear(...)
```

calculates, for every polygon of a Continuous Section Field (CSF), the transverse resultant associated with the longitudinal variation of the polygon centroid axis.

The formulation is specific to the CSF representation because it combines:

- polygon identity preserved along the longitudinal coordinate `z`;
- continuous polygon geometry;
- polygon-level axial-flexural participation through `weightabs`;
- the CSF Navier normal-stress field;
- the derivative of each occupied polygon region's centroid curve.

The function returns polygon resultants. It does not calculate a shear-stress distribution.

---

## 1. CSF geometric representation

Every CSF section is defined on a plane

```math
z = \text{constant},
```
perpendicular to the global longitudinal axis $z$.

For polygon $i$, the centroid of its occupied region is

```math
\mathbf{C}_i(z)
=
\left(
C_{x,i}(z),
C_{y,i}(z)
\right).
```
As $z$ varies, this centroid defines the spatial curve

```math
\mathbf{r}_i(z)
=
\left(
C_{x,i}(z),
C_{y,i}(z),
z
\right).
```
Its non-normalized tangent is

```math
\frac{d\mathbf{r}_i}{dz}
=
\left(
\frac{dC_{x,i}}{dz},
\frac{dC_{y,i}}{dz},
1
\right).
```
The formulation therefore assigns one longitudinal centroid axis to each polygon.

It does not define a point-by-point inclination field inside the polygon.

---

## 2. Polygon identity along the field

Polygon correspondence between different stations is based on the stable CSF polygon index.

The calculation assumes that:

- polygon indices retain the same identity along the field;
- the number of polygons does not change over the derivative sampling interval;
- the containment topology remains valid at all sampled stations.

Polygon names are used only as output labels.

---

## 3. Occupied polygon region

A CSF polygon may contain one or more direct child polygons.

In that case, the material region associated with the parent polygon is assumed to be

```math
A_i^{\mathrm{occ}}
=
A_i^{\mathrm{outer}}
-
\sum_{j \in \mathrm{children}(i)}
A_j.
```
The same subtraction is applied to the first moments of area.

Therefore,

```math
C_{x,i}^{\mathrm{occ}}
=
\frac{
A_i^{\mathrm{outer}} C_{x,i}^{\mathrm{outer}}
-
\sum_j A_j C_{x,j}
}{
A_i^{\mathrm{occ}}
},
```
and

```math
C_{y,i}^{\mathrm{occ}}
=
\frac{
A_i^{\mathrm{outer}} C_{y,i}^{\mathrm{outer}}
-
\sum_j A_j C_{y,j}
}{
A_i^{\mathrm{occ}}
}.
```
This treatment ensures that each physical region is counted once when polygon resultants are summed.

For a polygon without direct children, the occupied region is the complete polygon.

---

## 4. CSF axial-flexural participation

Each polygon has an absolute axial-flexural participation value

```math
w_i = \mathrm{weightabs}_i.
```
This value affects the normal stress carried by the polygon.

It does not affect:

- the polygon geometry;
- the occupied area;
- the occupied-region centroid;
- the centroid derivative;
- the centroid-axis inclination.

The shear-torsional carrier `shear_weight` is not used by this formulation.

---

## 5. Section-level Navier field

At the evaluation station $z$, the section-level quantities are

```math
A,\quad
C_x,\quad
C_y,\quad
I_x,\quad
I_y,\quad
I_{xy}.
```
The determinant of the bending inertia matrix is

```math
D
=
I_x I_y - I_{xy}^2.
```
The axial term is

```math
a_N
=
\frac{N}{A}.
```
The bending coefficients are

```math
b_x
=
\frac{
M_y I_x - M_x I_{xy}
}{
D
},
```
and

```math
b_y
=
\frac{
M_x I_y - M_y I_{xy}
}{
D
}.
```
For polygon $i$, the normal stress field is

```math
\sigma_{zz,i}(x,y)
=
w_i
\left[
a_N
+
b_x(x-C_x)
+
b_y(y-C_y)
\right].
```
This is the same general linear Navier field used by CSF for axial force and biaxial bending, but the centroid-axis function evaluates it through dedicated private helpers and does not modify the public Navier analysis.

---

## 6. Polygon normal resultant

The signed normal resultant carried by occupied polygon region $i$ is

```math
N_i
=
\int_{A_i^{\mathrm{occ}}}
\sigma_{zz,i}(x,y)\,dA.
```
Because the Navier field is linear in $x$ and $y$, and `weightabs` is constant within one polygon at a given station, the integral is exactly

```math
N_i
=
A_i^{\mathrm{occ}}
\,
\sigma_{zz,i}
\left(
C_{x,i}^{\mathrm{occ}},
C_{y,i}^{\mathrm{occ}}
\right).
```
Evaluating the stress at the occupied-region centroid is therefore exact for this linear field. It is not a numerical approximation of the area integral.

The polygon normal resultants satisfy, within numerical tolerance,

```math
\sum_i N_i = N,
```
provided that the occupied regions cover the complete axial-flexural section without overlap or omission.

---

## 7. Centroid-axis shear contribution

The fundamental mechanical assumption is:

> The normal resultant carried by each occupied polygon region follows the longitudinal trajectory of that region's centroid.

The transverse components associated with this trajectory are

```math
T_{x,i}^{C}
=
N_i
\frac{dC_{x,i}}{dz},
```
and

```math
T_{y,i}^{C}
=
N_i
\frac{dC_{y,i}}{dz}.
```
The superscript $C$ identifies the centroid-axis contribution.

The formulation uses the slope components directly. The tangent vector is not normalized because $N_i$ is the signed force component acting on the CSF section plane $z=\text{constant}$, rather than the total force magnitude along the inclined centroid axis.

---

## 8. Role of `weightabs`

`weightabs` enters only through the polygon normal stress:

```math
w_i
\longrightarrow
\sigma_{zz,i}
\longrightarrow
N_i
\longrightarrow
T_{x,i}^{C},\,
T_{y,i}^{C}.
```
At unchanged geometry and centroid derivative:

- $w_i=1$ gives full axial-flexural participation;
- $w_i=0.5$ halves the polygon stress and normal resultant;
- $w_i=0$ gives $N_i=0$, hence no centroid-axis shear contribution.

Thus, `weightabs` controls how much normal force the polygon carries. It does not control the polygon inclination.

---

## 9. Numerical evaluation of centroid derivatives

The derivatives

```math
\frac{dC_{x,i}}{dz},
\qquad
\frac{dC_{y,i}}{dz}
```
are calculated by sampling the CSF geometry at nearby stations.

### Interior station

A centred second-order formula is used:

```math
C_i'(z)
=
\frac{
C_i(z+h)-C_i(z-h)
}{
2h
}.
```
### First CSF station

A second-order forward formula is used:

```math
C_i'(z)
=
\frac{
-3C_i(z)
+4C_i(z+h)
-C_i(z+2h)
}{
2h
}.
```
### Last CSF station

A second-order backward formula is used:

```math
C_i'(z)
=
\frac{
3C_i(z)
-4C_i(z-h)
+C_i(z-2h)
}{
2h
}.
```
The same derivative step and scheme are applied to all polygons at the station.

---

## 10. Automatic derivative convergence

When `dz` is not supplied, the derivative step is selected by convergence.

Starting from

```math
h_0 = 0.05L,
```
where $L$ is the CSF field length, the step is repeatedly halved:

```math
h_0,\quad
\frac{h_0}{2},\quad
\frac{h_0}{4},\quad
\ldots
```
For each polygon and for each centroid component, convergence is accepted when

```math
\left|
d_{\mathrm{new}}
-
d_{\mathrm{previous}}
\right|
\le
\mathrm{atol}
+
\mathrm{rtol}
\max
\left(
|d_{\mathrm{new}}|,
|d_{\mathrm{previous}}|
\right).
```
The refinement succeeds only when both derivative components of every polygon satisfy the condition during the same refinement.

If convergence is not reached before the numerical lower step limit or before `max_refinements`, the function raises an error rather than returning an uncontrolled step-dependent value.

---

## 11. Regularity assumptions

The calculation assumes that:

- each occupied-region centroid curve is sufficiently regular for finite-difference differentiation;
- polygon correspondence remains unchanged over the sampled interval;
- no polygon develops zero occupied area;
- the section area is non-zero;
- the bending inertia matrix is non-singular;
- `weightabs` is uniform within each polygon at a fixed station;
- the Navier field remains linear in the section coordinates.

Abrupt geometric or topological changes may prevent derivative convergence or invalidate the centroid-curve interpretation.

---

## 12. Function output

With

```python
debug=False
```

the function returns, for each polygon:

```text
idx
name
N_polygon
dCx_dz
dCy_dz
Tx_centroid_axis
Ty_centroid_axis
```

With

```python
debug=True
```

it additionally returns selected geometric and convergence diagnostics:

```text
A_polygon
Cx_polygon
Cy_polygon
derivative_step
derivative_dz_mode
derivative_converged
derivative_refinements
derivative_change_x
derivative_change_y
weightabs
sigma_at_polygon_centroid
```

---

## 13. Scope and exclusions

The function returns polygon-level resultants:

```math
N_i,\qquad
T_{x,i}^{C},\qquad
T_{y,i}^{C}.
```
It does not calculate:

- a shear-stress distribution inside the polygon;
- Jourawski shear stresses;
- shear participation through `shear_weight`;
- Saint-Venant torsion;
- warping;
- a three-dimensional internal stress field;
- an automatic combination with Jourawski shear results.

The centroid-axis contribution and the Jourawski shear-stress calculation are distinct analyses.

---

## 14. Compact CSF formulation

The complete calculation can be summarized as

```math
S(z)
\longrightarrow
A_i^{\mathrm{occ}}(z),
\,
C_i(z),
\,
w_i(z),
```
```math
(N,M_x,M_y)
\longrightarrow
\sigma_{zz,i}(x,y)
\longrightarrow
N_i,
```
and

```math
C_i'(z)
\longrightarrow
\left(
T_{x,i}^{C},
T_{y,i}^{C}
\right).
```
The characteristic CSF assumption is:

> Each occupied polygon region carries its signed normal resultant along the longitudinal trajectory of its geometric centroid.
