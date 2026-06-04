# Stacked rectangular member with compensated geometric variation and participation-field variation

## General description

This verification case demonstrates how a Continuous Section Field (CSF) defines an evaluable sectional function along a member axis, rather than a fixed table of section properties.

The member has total length $L = 10$ and is represented by two continuous CSF intervals joined at $z = 5$. Each interval defines reference cross-sections, polygonal zones, and longitudinal participation fields. `CSFStacked` concatenates the two intervals into a single global member representation that can be evaluated at any station $z$ along the member axis./

The case is intentionally simple in geometry and non-trivial in sectional behaviour. The cross-section is a stacked rectangular section composed of three components:

- `upper`
- `middle`
- `lower`

Two independent mechanisms are prescribed:

1. the `lower` component has geometric variation along the member axis;
2. the `upper` component has participation-field variation while its geometry remains fixed.

The axial/bending participation assigned to the `upper` component is selected so that its weighted-area variation is exactly compensated by the geometric-area variation of the `lower` component. As a result, the total weighted area $A(z)$ remains constant, while the centroid coordinate $C_y(z)$ and the bending inertia $I_x(z)$ vary continuously along the member axis.

This makes the case useful as a controlled verification of the continuous field itself. No structural solver is involved. The CSF-computed weighted sectional quantities are compared directly against a closed-form reference for $A$, $C_y$, $I_x$, and $I_y$.

 

<p align="center">
  <em> Figure 1. Global CSF member representation</em>
</p>

<p align="center">
  <img width="816" height="706" alt="image" src="https://github.com/user-attachments/assets/3fefab64-20c4-4a84-914a-6a561c1b3cf5" />
</p>




---

## Files

The case is defined by the following files:

| File | Role |
|---|---|
| `stacked_0.yaml` | First continuous CSF interval, $0 \le z \le 5$ |
| `stacked_1.yaml` | Second continuous CSF interval, $5 \le z \le 10$ |
| `run_stacked_closed_form.py` | Builds the `CSFStacked` object, evaluates the closed-form reference, compares CSF values, exports station-wise CSV files, and generates plots |
| `out/lobatto_station_export_*.csv` | Station-wise CSV exports of the evaluated CSF geometry and participation fields |

The YAML files define the continuous model. The CSV files are station-wise exports generated after evaluating that model at selected stations.

---

## Continuous CSF model

The example is built from three stacked components: `upper`, `middle`, and `lower`.

The section is symmetric with respect to the vertical axis. All components have the same width and are centered on the same axis, so the horizontal centroid remains fixed at $C_x=0$. The relevant centroid variation in this example is therefore the vertical coordinate $C_y(z)$.

The `lower` component changes its geometry along the member axis. The `upper` component keeps a constant geometry, but its axial/bending participation varies continuously. The `middle` component remains fixed in both geometry and axial/bending participation.

This setup separates geometric variation from participation-field variation. CSF keeps both descriptions continuous along $z$, so the sectional properties are evaluated from the continuous model at the requested stations rather than prescribed as a fixed station-wise table.

---

## Geometry

All three components have constant width

<p align="center">
  <em> Figure 2. Section at z = 2.5.</em>
</p>



<p align="center">
  <img width="264" height="522" alt="image" src="https://github.com/user-attachments/assets/b4aff836-bb40-474b-879b-f7a5f3205f0d" />

</p>



$$
B = 0.30 .
$$

The `upper` component has fixed height

$$
h_u = 0.20
$$

and centroid coordinate

$$
y_u = 0.10 .
$$

The `middle` component has fixed height

$$
h_m = 0.30
$$

and centroid coordinate

$$
y_m = -0.15 .
$$

The `lower` component has fixed top edge at $y = -0.30$. Its height varies along the member axis and is denoted by $h_l(t)$. Its centroid coordinate is therefore

$$
y_l(t) = -0.30 - \frac{h_l(t)}{2} .
$$

The model is split into two continuous CSF intervals.

### First interval: `stacked_0.yaml`, $0 \le z \le 5$

The local coordinate is

$$
t = \frac{z}{5} .
$$

The `lower` component height decreases linearly from $0.30$ to $0.20$:

$$
h_l(t) = 0.30 - 0.10t .
$$

### Second interval: `stacked_1.yaml`, $5 \le z \le 10$

The local coordinate is

$$
t = \frac{z - 5}{5} .
$$

The `lower` component height increases linearly from $0.20$ to $0.30$:

$$
h_l(t) = 0.20 + 0.10t .
$$

The two intervals meet at $z = 5$, where the `lower` component height is $0.20$.

---

## Participation fields

The axial/bending participation of the `middle` and `lower` components remains equal to the value specified in the section definitions:

$$
w_m(t) = 1,
\qquad
w_l(t) = 1 .
$$

The `upper` component receives an explicit axial/bending participation law.

### First interval: $0 \le z \le 5$

$$
w_u(t) = 1 - 0.5(1 - t) .
$$

Equivalently,

$$
w_u(t) = 0.5 + 0.5t .
$$

The `upper` axial/bending participation increases from $0.5$ at $z = 0$ to $1.0$ at $z = 5$.

### Second interval: $5 \le z \le 10$

$$
w_u(t) = 1 - 0.5t .
$$

The `upper` axial/bending participation decreases from $1.0$ at $z = 5$ to $0.5$ at $z = 10$.

---

## Non-isotropic participation assignment for the `upper` component

The shear/torsion participation field is defined per component and is denoted by $\kappa_i(z)$.

In this example, the `upper` component has an independently prescribed shear/torsion participation field. Its axial/bending participation field $w_u(z)$ and its shear/torsion participation field $\kappa_u(z)$ are defined by two different laws. Consequently, $\kappa_u(z)$ is not obtained from $w_u(z)$ through the isotropic shortcut.

For the first interval, $0 \le z \le 5$, the local coordinate is

$$
t = \frac{z}{5}
$$

and the `upper` shear/torsion participation is

$$
\kappa_u(t) = 1 - 0.8(1 - t) = 0.2 + 0.8t
$$

Thus, $\kappa_u$ increases linearly from $0.2$ at $z = 0$ to $1.0$ at $z = 5$.

<p align="center">
  <em>Figure 3. Shear/torsion participation field of the upper component in the first CSF interval. The field increases linearly from 0.20 at z = 0 to 1.00 at z = 5.</em>
</p>

<img width="989" height="475" alt="image" src="https://github.com/user-attachments/assets/43f37ed8-e3ac-4537-a1bc-ed8433b2571a" />

For the second interval, $5 \le z \le 10$, the local coordinate is

$$
t = \frac{z - 5}{5}
$$

and the `upper` shear/torsion participation is

$$
\kappa_u(t) = 1 - 0.8t
$$

Thus, $\kappa_u$ decreases linearly from $1.0$ at $z = 5$ to $0.2$ at $z = 10$.

<p align="center">
  <em>Figure 4. Shear/torsion participation field of the upper component in the second CSF interval. The field decreases linearly from 1.00 at z = 5 to 0.20 at z = 10.</em>
</p>

<img width="986" height="453" alt="image" src="https://github.com/user-attachments/assets/c91e77b7-4ea8-4ccb-8a2a-08c4bb5b04e5" />

The `middle` and `lower` components do not receive an independently prescribed shear/torsion participation law. Their shear/torsion participation is derived through the isotropic shortcut

$$
\kappa_i(z) = \frac{w_i(z)}{2(1 + \nu)}
$$

with

$$
\nu = 0.2
$$

Since $w_m = w_l = 1$, this gives

$$
\kappa_m = \kappa_l = \frac{1}{2(1 + 0.2)} = 0.4166666667
$$

The resulting participation assignments are:

| Component | Axial/bending participation | Shear/torsion participation | Assignment                              |
| --------- | --------------------------: | --------------------------: | --------------------------------------- |
| `upper`   |                    $w_u(t)$ |    prescribed $\kappa_u(t)$ | independent shear/torsion participation |
| `middle`  |                         $1$ |      $\frac{1}{2(1 + 0.2)}$ | derived from `iso(0.2)`                 |
| `lower`   |                         $1$ |      $\frac{1}{2(1 + 0.2)}$ | derived from `iso(0.2)`                 |

The distinction above concerns the participation-field assignment in the continuous CSF model. In the station-wise CSV export, this information appears as sampled metadata attached to the exported polygon vertices. In particular, the `poisson` column is populated for components whose $\kappa_i(z)$ value is derived through `iso(0.2)`, while it remains empty for the `upper` component because $\kappa_u(z)$ is prescribed directly.

---

## Compensation mechanism

The purpose of this case is to prescribe two different variations that compensate each other in terms of total weighted area. The `upper` component does not change its geometry, but its axial/bending participation $w_u(z)$ varies along the member axis. The `lower` component follows the opposite behaviour: its participation remains constant, but its geometric height changes along $z$.

The participation law of the `upper` component is selected so that the loss or gain of weighted area in `upper` is exactly balanced by the geometric-area variation of `lower`. This produces a section whose total weighted area remains constant, while the internal distribution of the weighted area changes. The compensation is therefore useful because it isolates an important point: a constant total weighted area does not imply a constant weighted centroid or a constant bending inertia.

<p align="center">
  <em>Figure 5. Continuous sectional-property variation over the stacked member.</em>
</p>


<img width="989" height="869" alt="image" src="https://github.com/user-attachments/assets/812b2a89-dfaa-48f4-b609-52eaf7233397" />


The weighted area of the section is

```math
A(z) =
w_u(z) A_u^{\mathrm{geom}}
+
w_m(z) A_m^{\mathrm{geom}}
+
w_l(z) A_l^{\mathrm{geom}}(z).
```

In this example,

```math
w_m(z) = w_l(z) = 1,
```

therefore

```math
A(z) =
w_u(z) A_u^{\mathrm{geom}}
+
A_m^{\mathrm{geom}}
+
A_l^{\mathrm{geom}}(z).
```

The fixed geometric areas of the `upper` and `middle` components are

```math
A_u^{\mathrm{geom}} = B h_u = 0.30 \cdot 0.20 = 0.06,
```

```math
A_m^{\mathrm{geom}} = B h_m = 0.30 \cdot 0.30 = 0.09.
```

The `lower` geometric area is

```math
A_l^{\mathrm{geom}}(t) = B h_l(t).
```

### First interval: $0 \le z \le 5$

The local coordinate is

```math
t = \frac{z}{5}.
```

In this interval,

```math
w_u(t) = 0.5 + 0.5t,
\qquad
h_l(t) = 0.30 - 0.10t.
```

The weighted contribution of the `upper` component is

```math
w_u(t) A_u^{\mathrm{geom}}
=
(0.5 + 0.5t) \cdot 0.06
=
0.03 + 0.03t.
```

The geometric contribution of the `lower` component is

```math
A_l^{\mathrm{geom}}(t)
=
0.30(0.30 - 0.10t)
=
0.09 - 0.03t.
```

Therefore, over the first interval,

```math
A(t)
=
(0.03 + 0.03t)
+
0.09
+
(0.09 - 0.03t)
=
0.21.
```

### Second interval: $5 \le z \le 10$

The local coordinate is

```math
t = \frac{z - 5}{5}.
```

In this interval,

```math
w_u(t) = 1 - 0.5t,
\qquad
h_l(t) = 0.20 + 0.10t.
```

The weighted contribution of the `upper` component is

```math
w_u(t) A_u^{\mathrm{geom}}
=
(1 - 0.5t) \cdot 0.06
=
0.06 - 0.03t.
```

The geometric contribution of the `lower` component is

```math
A_l^{\mathrm{geom}}(t)
=
0.30(0.20 + 0.10t)
=
0.06 + 0.03t.
```

Therefore, over the second interval,

```math
A(t)
=
(0.06 - 0.03t)
+
0.09
+
(0.06 + 0.03t)
=
0.21.
```

Thus, the total weighted area is constant over the full member:

```math
A(z) = 0.21,
\qquad
0 \le z \le 10.
```

The compensation affects only the total weighted area. The distribution of the weighted area within the section still changes along the member axis. Consequently, $C_y(z)$ and $I_x(z)$ vary even though $A(z)$ is constant.


---

## Closed-form reference

The closed-form comparison uses the weighted sectional quantities $A$, $C_y$, $I_x$, and $I_y$.

For each component $i$, define:

$$
A_i(z) = w_i(z) B h_i(z) .
$$

The total weighted area is

$$
A(z) = \sum_i A_i(z) .
$$

The weighted centroid coordinate is

$$
C_y(z) = \frac{\sum_i A_i(z)y_i(z)}{A(z)} .
$$

The local second moments of a rectangular component about its own centroid are

$$
I_{x,i}^{\mathrm{local}}(z) = \frac{B h_i(z)^3}{12},
$$

$$
I_{y,i}^{\mathrm{local}}(z) = \frac{h_i(z) B^3}{12} .
$$

The weighted second moment about the global weighted centroid is

$$
I_x(z) =
\sum_i
w_i(z)
\left[
I_{x,i}^{\mathrm{local}}(z)
+
A_i(z)\left(y_i(z)-C_y(z)\right)^2
\right].
$$
The weighted second moment about the vertical axis is

$$
I_y(z) =
\sum_i
w_i(z) I_{y,i}^{\mathrm{local}}(z) .
$$

The shear/torsion participation field $\kappa_i(z)$ is part of the CSF model definition, but it is not used in this closed-form verification because $A$, $C_y$, $I_x$, and $I_y$ are axial/bending weighted quantities.

---

## Expected sectional-property behaviour

The property plot should show the following behaviour:

| Quantity | Behaviour |
|---|---|
| $A(z)$ | constant over the full member, equal to $0.21$ |
| $C_y(z)$ | varies continuously and symmetrically; maximum value at $z = 5$ |
| $I_x(z)$ | varies continuously and symmetrically; minimum value at $z = 5$ |
| $I_y(z)$ | constant over the full member |

Representative values are:

| Station | $A$ | $C_y$ | $I_x$ | $I_y$ |
|---:|---:|---:|---:|---:|
| $z = 0$ | $0.21$ | $-0.242857$ | $0.0096143$ | $0.0015750$ |
| $z = 5$ | $0.21$ | $-0.150000$ | $0.0085750$ | $0.0015750$ |
| $z = 10$ | $0.21$ | $-0.242857$ | $0.0096143$ | $0.0015750$ |

> **Figure placeholder - continuous weighted sectional quantities**  
> Add the plot of $A(z)$, $C_y(z)$, $I_x(z)$, and $I_y(z)$ over $0 \le z \le 10$.
>
> `![Stack properties](figures/stack_properties.png)`

---

## CSF versus closed-form comparison

The Python script evaluates the `CSFStacked` model at Gauss-Lobatto stations on each interval and compares the CSF-computed values with the closed-form reference.

The station set is built as follows:

1. 11 Gauss-Lobatto stations are computed on $0 \le z \le 5$;
2. 11 Gauss-Lobatto stations are computed on $5 \le z \le 10$;
3. the duplicated junction station at $z = 5$ is removed from the second list.

The comparison checks:

- $A_{\mathrm{CSF}}$ against $A_{\mathrm{ref}}$;
- $C_{y,\mathrm{CSF}}$ against $C_{y,\mathrm{ref}}$;
- $I_{x,\mathrm{CSF}}$ against $I_{x,\mathrm{ref}}$;
- $I_{y,\mathrm{CSF}}$ against $I_{y,\mathrm{ref}}$.

The reported error is the maximum relative error over $A$, $I_x$, and $I_y$, plus the absolute error in $C_y$.

For the run associated with this case, the maximum errors are:

```text
max relative error (A, Ix, Iy): 1.09e-13 %
max absolute error (Cy): 5.55e-17
```

These values are at floating-point roundoff level for this closed-form comparison.

---

## Station-wise CSV export

The CSV export is a station-wise representation of the evaluated CSF model. It is not the model definition.

The sequence is:

```text
continuous CSF model
→ station-wise section evaluation at z
→ sampled polygonal zones/components
→ CSV vertex rows with sampled metadata
```

Each exported CSV row corresponds to one vertex of a sampled polygonal zone at the selected station. The columns `w`, `shear_w`, and `poisson` are repeated over the vertices of the same sampled component because those values are component-level participation data at that station.

For example, at $z = 7$ the station lies in the second interval. The local coordinate is

$$
t = \frac{7 - 5}{5} = 0.4 .
$$

The sampled values are:

$$
w_u = 1 - 0.5(0.4) = 0.8,
$$

$$
\kappa_u = 1 - 0.8(0.4) = 0.68 .
$$

The `lower` height is

$$
h_l = 0.20 + 0.10(0.4) = 0.24 .
$$

Since the `lower` top edge is fixed at $y = -0.30$, its lower edge is located at

$$
y = -0.30 - 0.24 = -0.54 .
$$

The corresponding CSV metadata are:

| Component | `w` | `shear_w` | `poisson` | Meaning |
|---|---:|---:|---:|---|
| `upper` | `0.8` | `0.68` | empty | $\kappa_u$ assigned independently from $w_u$ |
| `middle` | `1` | `0.416666666667` | `0.2` | $\kappa_m$ derived from `iso(0.2)` |
| `lower` | `1` | `0.416666666667` | `0.2` | $\kappa_l$ derived from `iso(0.2)` |

The empty `poisson` field for `upper` does not indicate missing geometry or invalid data. It indicates that the shear/torsion participation was assigned directly rather than derived through the isotropic shortcut.

 **station-wise section at $z = 7$**  
```
## GEOMETRY EXPORT ##
# z=7.0
idx_polygon,idx_container,s0_name,s1_name,w,shear_w,poisson,vertex_i,x,y
0,,upper,upper,0.8,0.68,,0,-0.15,0
0,,upper,upper,0.8,0.68,,1,0.15,0
0,,upper,upper,0.8,0.68,,2,0.15,0.2
0,,upper,upper,0.8,0.68,,3,-0.15,0.2
1,,middle,middle,1,0.416666666667,0.2,0,-0.15,-0.3
1,,middle,middle,1,0.416666666667,0.2,1,0.15,-0.3
1,,middle,middle,1,0.416666666667,0.2,2,0.15,0
1,,middle,middle,1,0.416666666667,0.2,3,-0.15,0
2,,lower,lower,1,0.416666666667,0.2,0,-0.15,-0.54
2,,lower,lower,1,0.416666666667,0.2,1,0.15,-0.54
2,,lower,lower,1,0.416666666667,0.2,2,0.15,-0.3
2,,lower,lower,1,0.416666666667,0.2,3,-0.15,-0.3
```
---

## Running the case

From the directory containing the YAML files and the Python script:

```bash
python run_stacked_closed_form.py
```

The script performs the following operations:

1. reads `stacked_0.yaml` and `stacked_1.yaml`;
2. appends both continuous CSF intervals into a `CSFStacked` object;
3. prints the closed-form laws used for the comparison;
4. evaluates the CSF model at Gauss-Lobatto stations;
5. compares $A$, $C_y$, $I_x$, and $I_y$ against the closed-form reference;
6. exports station-wise CSV files at selected stations;
7. plots the global member representation, selected sectional properties, and selected participation fields.

The script writes CSV exports for the manually selected stations:

```text
z = 0, 3, 5, 7, 10
```

with filenames of the form:

```text
out/lobatto_station_export_<z>.csv
```

---

## Suggested figure set for the repository page

The README is intended to remain understandable even before figures are inspected, but the following figures are useful for documenting the case:

| Figure | Suggested filename | Purpose |
|---|---|---|
| Global member representation | `figures/stacked_member_3d.png` | Shows the two continuous CSF intervals and the stacked geometry |
| Sectional-property plot | `figures/stack_properties.png` | Shows constant $A$ and varying $C_y$, $I_x$ |
| Section at $z = 2.5$ | `figures/section_z2p5_vertex_ids.png` | Shows the polygonal zones and vertex ordering |
| Station-wise section at $z = 7$ | `figures/section_z7.png` | Connects the evaluated section with the CSV export |
| `upper` axial/bending participation | `figures/upper_weight.png` | Shows $w_u(z)$ over the member axis |
| `upper` shear/torsion participation | `figures/upper_shear_weight.png` | Shows $\kappa_u(z)$ over the member axis |

---

## Interpretation

This case verifies that CSF can represent a member as a continuous sectional field in which geometry and participation fields vary independently along the member axis.

The constant total weighted area confirms that the compensation between `upper` participation-field variation and `lower` geometric variation is correctly represented. The variation of $C_y(z)$ and $I_x(z)$ confirms that a constant weighted area does not imply a constant weighted section. The constant $I_y(z)$ follows from the fixed width of the components and from the compensated total weighted area.

The station-wise CSV exports demonstrate a separate point: exported rows are sampled data generated from the continuous model. They are not the model object. The model object is the continuous CSF member representation composed of polygonal zones, geometric interpolation, and participation fields.
