# Stacked rectangular member with compensated geometric variation and participation-field variation
[run_stacked.py](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/stacked_rectangular/run_stacked.py)

## Purpose of this document

This verification program evaluates the sectional properties computed by CSF and compares them with closed-form reference solutions. The case is designed to test a stacked member composed of two continuous intervals with hybrid sectional behavior: some components use the isotropic shear-weight shortcut, while the upper component uses independently prescribed axial/bending and shear/torsion participation laws.


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

Before assembling the two intervals into the global stacked member, the first YAML interval can be inspected directly with `csf-actions`. This step is not the closed-form verification. Its purpose is to show that a single CSF YAML file already defines an evaluable continuous section field: geometry, axial/bending participation, shear/torsion participation, section properties, and sampled sections can be obtained from the same source model.

For the first interval, the model file is:

```text
stacked_0.yaml
```

and the action file is:

```text
stacked_actions.yaml
```

The same type of inspection can be applied to `stacked_1.yaml`. In this description, only `stacked_0.yaml` is shown because the second interval is the symmetric continuation used later in the global stacked-member verification.

---

### Action file

The action file defines the stations to be sampled and the operations to be performed on the CSF interval:

```yaml
CSF_ACTIONS:
  stations:
    station_middle:
      - 2.5 
    station_edges:
      - 0.00
      - 5  

    station_precise:
      - 0  
      - 1
      - 2
      - 3
      - 4
      - 5

  actions:
    - plot_volume_3d:
        params:
          seed: w
          title: "Element with weight"
          line_percent: 100.0

    - plot_volume_3d:
        params:
          seed: s 
          title: "Element with shear weight"
          line_percent: 100.0

    - section_selected_analysis:
        stations: station_precise
        output:
          - [out/sec_var.txt]
        properties:
          [geometry, A, Cy, Ix, Iy]

    - plot_section_2d:
        stations:
          - station_middle
        show_ids: false
        show_vertex_ids: false
        output:
          - [stdout, out/section_a.jpg]

    - plot_properties:
        output:
          - stdout
          - out/section_properties.jpg
        params:
          num_points: 100
        properties: [A, Cy, Ix, Iy]
```

The file performs five operations:

1. it plots the three-dimensional interval using the axial/bending participation field `w`;
2. it plots the same interval using the shear/torsion participation field `s`;
3. it evaluates selected sectional quantities at prescribed stations;
4. it plots the sampled two-dimensional section at the middle station;
5. it plots the variation of selected section properties along the interval.

---

### Execution

From the directory containing `stacked_0.yaml` and `stacked_actions.yaml`, the first interval is inspected with:

```bash
csf-actions stacked_0.yaml stacked_actions.yaml
```

The same action file can be applied to the second interval with:

```bash
csf-actions stacked_1.yaml stacked_actions.yaml
```

Only the first command is detailed here.

---

### Three-dimensional view with axial/bending participation

The first `plot_volume_3d` action uses:

```yaml
seed: w
title: "Element with weight"
```

This plot shows the geometry of the interval and colors the element according to the axial/bending participation field `w`.

For `stacked_0.yaml`, the `upper0` component has a varying participation field. Along the interval $0 \le z \le 5$, its value increases from $w = 0.5$ at $z = 0$ to $w = 1.0$ at $z = 5$. The `middle0` and `lower0` components remain at $w = 1$ in this interval.

<p align="center">
  <em>Figure X. Three-dimensional view of the first CSF interval colored by the axial/bending participation field <code>w</code>.</em>
</p>

<p align="center">
  <img width="700" alt="Element with weight" src="FIGURE_PLACEHOLDER_ELEMENT_WITH_WEIGHT" />
</p>

---

### Three-dimensional view with shear/torsion participation

The second `plot_volume_3d` action uses:

```yaml
seed: s
title: "Element with shear weight"
```

This plot uses the same interval geometry, but colors the element according to the shear/torsion participation field `s`.

For `stacked_0.yaml`, the `upper0` component has an independently prescribed shear/torsion participation field. Its value increases from `s = 0.2` at $z = 0$ to `s = 1.0` at $z = 5$. This differs from the axial/bending participation field, which starts from `w = 0.5`.

The `middle0` and `lower0` components use the isotropic shortcut with $\nu = 0.2$, which gives:

$$
s = \frac{1}{2(1 + 0.2)} = 0.41666667 .
$$

<p align="center">
  <em>Figure X. Three-dimensional view of the first CSF interval colored by the shear/torsion participation field <code>s</code>.</em>
</p>

<p align="center">
  <img width="700" alt="Element with shear weight" src="FIGURE_PLACEHOLDER_ELEMENT_WITH_SHEAR_WEIGHT" />
</p>

---

### Sampled two-dimensional section

The `plot_section_2d` action samples the section at:

```yaml
station_middle:
  - 2.5
```

At $z = 2.5$, the local coordinate of the first interval is:

$$
t = \frac{2.5}{5} = 0.5 .
$$

At this station, the upper component has:

$$
w = 0.75,
\qquad
s = 0.60 .
$$

The two-dimensional section plot shows the three stacked components:

- `upper0`;
- `middle0`;
- `lower0`.

The legend reports the sampled component IDs and the sampled `w` values at the station.

<p align="center">
  <em>Figure X. Sampled two-dimensional section of <code>stacked_0.yaml</code> at $z = 2.5$.</em>
</p>

<p align="center">
  <img width="450" alt="Section at z = 2.5" src="FIGURE_PLACEHOLDER_SECTION_AT_2_5" />
</p>

---

### Section-property plot over the interval

The `plot_properties` action evaluates and plots:

```yaml
properties: [A, Cy, Ix, Iy]
```

over the interval $0 \le z \le 5$.

The resulting plot shows the behavior of the sectional quantities over the first CSF interval:

| Quantity | Behaviour over `stacked_0.yaml` |
|---|---|
| $A$ | constant, equal to $0.21$ |
| $C_y$ | increases from $-0.24285714$ to $-0.15000000$ |
| $I_x$ | decreases from $0.00961429$ to $0.00857500$ |
| $I_y$ | constant, equal to $0.00157500$ |

This is the expected local behavior of the first interval: the weighted area remains constant, while the weighted centroid and the bending inertia about the horizontal centroidal axis vary along $z$.

<p align="center">
  <em>Figure X. Section-property variation over the first CSF interval.</em>
</p>

<p align="center">
  <img width="900" alt="Section properties over stacked_0.yaml" src="FIGURE_PLACEHOLDER_SECTION_PROPERTIES" />
</p>

---

### Numerical section output

The `section_selected_analysis` action evaluates the same interval at the prescribed stations:

```yaml
station_precise:
  - 0
  - 1
  - 2
  - 3
  - 4
  - 5
```

The output is written to:

```text
out/sec_var.txt
```

The selected properties are:

```yaml
[geometry, A, Cy, Ix, Iy]
```

Representative values from the output are:

| $z$ | $A$ | $C_y$ | $I_x$ | $I_y$ |
|---:|---:|---:|---:|---:|
| 0 | 0.21000000 | -0.24285714 | 0.00961429 | 0.00157500 |
| 1 | 0.21000000 | -0.22314286 | 0.00953473 | 0.00157500 |
| 2 | 0.21000000 | -0.20400000 | 0.00938224 | 0.00157500 |
| 3 | 0.21000000 | -0.18542857 | 0.00916581 | 0.00157500 |
| 4 | 0.21000000 | -0.16742857 | 0.00889401 | 0.00157500 |
| 5 | 0.21000000 | -0.15000000 | 0.00857500 | 0.00157500 |

The same output also includes the sampled polygon vertices and the sampled component metadata at each station. For example, at $z = 0$:

```text
idx_polygon,idx_container,s0_name,s1_name,w,shear_w,poisson,vertex_i,x,y
0,,upper0,upper0,0.50000000,0.20000000,,0,-0.15000000,0.00000000
1,,middle0,middle0,1.00000000,0.41666667,0.20000000,0,-0.15000000,-0.30000000
2,,lower0,lower0,1.00000000,0.41666667,0.20000000,0,-0.15000000,-0.60000000
```

This station-wise output shows that the sampled rows are not the model definition. They are the result of evaluating the continuous CSF interval at selected coordinates.

---

### Role of this local inspection

The `csf-actions` run demonstrates that `stacked_0.yaml` is already a complete evaluable CSF interval. From the same YAML file, the action workflow obtains:

- three-dimensional geometry views;
- visualization of the axial/bending participation field;
- visualization of the shear/torsion participation field;
- a sampled two-dimensional section;
- numerical sectional quantities at selected stations;
- sampled polygon vertices with component-level metadata.

This local inspection prepares the following verification step. After the two intervals are inspected individually, `run_stacked.py` assembles `stacked_0.yaml` and `stacked_1.yaml` into a global stacked member and compares the CSF-computed sectional quantities against a closed-form reference.

---
# Files

The case is defined by the following files:

| File | Role |
|---|---|
| `stacked_0.yaml` | First continuous CSF interval, $0 \le z \le 5$ |
| `stacked_1.yaml` | Second continuous CSF interval, $5 \le z \le 10$ |
| `run_stacked.py` | Builds the `CSFStacked` object, evaluates the closed-form reference, compares CSF values, exports station-wise CSV files, and generates plots |
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
[stacked_0.yaml](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/stacked_rectangular/stacked_0.yaml)

[stacked_1.yaml](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/stacked_rectangular/stacked_1.yaml)


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

```text
     z seg     t   w_u  sw_u |  A_csf  A_ref |    Cy_csf    Cy_ref |     Ix_csf     Ix_ref |     Iy_csf     Iy_ref |     err_%     err_Cy
-----------------------------------------------------------------------------------------------------------------------------------------
  0.00   0  0.00  0.50  0.20 |   0.21   0.21 | -0.242857 -0.242857 |  0.0096143  0.0096143 |  0.0015750  0.0015750 |  1.38e-14   2.78e-17
  0.16   0  0.03  0.52  0.23 |   0.21   0.21 | -0.239565 -0.239565 |  0.0096066  0.0096066 |  0.0015750  0.0015750 |  7.22e-14   0.00e+00
  0.54   0  0.11  0.55  0.29 |   0.21   0.21 | -0.232164 -0.232164 |  0.0095810  0.0095810 |  0.0015750  0.0015750 |  3.62e-14   0.00e+00
  1.09   0  0.22  0.61  0.37 |   0.21   0.21 | -0.221456 -0.221456 |  0.0095242  0.0095242 |  0.0015750  0.0015750 |  1.09e-13   2.78e-17
  1.76   0  0.35  0.68  0.48 |   0.21   0.21 | -0.208531 -0.208531 |  0.0094249  0.0094249 |  0.0015750  0.0015750 |  2.75e-14   2.78e-17
  2.50   0  0.50  0.75  0.60 |   0.21   0.21 | -0.194643 -0.194643 |  0.0092815  0.0092815 |  0.0015750  0.0015750 |  3.74e-14   2.78e-17
  3.24   0  0.65  0.82  0.72 |   0.21   0.21 | -0.181067 -0.181067 |  0.0091055  0.0091055 |  0.0015750  0.0015750 |  1.91e-14   0.00e+00
  3.91   0  0.78  0.89  0.83 |   0.21   0.21 | -0.168970 -0.168970 |  0.0089196  0.0089196 |  0.0015750  0.0015750 |  7.78e-14   2.78e-17
  4.46   0  0.89  0.95  0.91 |   0.21   0.21 | -0.159319 -0.159319 |  0.0087523  0.0087523 |  0.0015750  0.0015750 |  3.96e-14   5.55e-17
  4.84   0  0.97  0.98  0.97 |   0.21   0.21 | -0.152836 -0.152836 |  0.0086306  0.0086306 |  0.0015750  0.0015750 |  4.02e-14   0.00e+00
  5.00   0  1.00  1.00  1.00 |   0.21   0.21 | -0.150000 -0.150000 |  0.0085750  0.0085750 |  0.0015750  0.0015750 |  2.75e-14   2.78e-17
  5.16   1  0.03  0.98  0.97 |   0.21   0.21 | -0.152836 -0.152836 |  0.0086306  0.0086306 |  0.0015750  0.0015750 |  2.75e-14   2.78e-17
  5.54   1  0.11  0.95  0.91 |   0.21   0.21 | -0.159319 -0.159319 |  0.0087523  0.0087523 |  0.0015750  0.0015750 |  5.95e-14   0.00e+00
  6.09   1  0.22  0.89  0.83 |   0.21   0.21 | -0.168970 -0.168970 |  0.0089196  0.0089196 |  0.0015750  0.0015750 |  7.78e-14   0.00e+00
  6.76   1  0.35  0.82  0.72 |   0.21   0.21 | -0.181067 -0.181067 |  0.0091055  0.0091055 |  0.0015750  0.0015750 |  1.91e-14   2.78e-17
  7.50   1  0.50  0.75  0.60 |   0.21   0.21 | -0.194643 -0.194643 |  0.0092815  0.0092815 |  0.0015750  0.0015750 |  3.74e-14   2.78e-17
  8.24   1  0.65  0.68  0.48 |   0.21   0.21 | -0.208531 -0.208531 |  0.0094249  0.0094249 |  0.0015750  0.0015750 |  1.38e-14   5.55e-17
  8.91   1  0.78  0.61  0.37 |   0.21   0.21 | -0.221456 -0.221456 |  0.0095242  0.0095242 |  0.0015750  0.0015750 |  1.09e-13   2.78e-17
  9.46   1  0.89  0.55  0.29 |   0.21   0.21 | -0.232164 -0.232164 |  0.0095810  0.0095810 |  0.0015750  0.0015750 |  3.62e-14   0.00e+00
  9.84   1  0.97  0.52  0.23 |   0.21   0.21 | -0.239565 -0.239565 |  0.0096066  0.0096066 |  0.0015750  0.0015750 |  2.75e-14   0.00e+00
 10.00   1  1.00  0.50  0.20 |   0.21   0.21 | -0.242857 -0.242857 |  0.0096143  0.0096143 |  0.0015750  0.0015750 |  1.38e-14   0.00e+00
-----------------------------------------------------------------------------------------------------------------------------------------

```

---

## CSF versus closed-form comparison

The `CSFStacked` model is evaluated by CSF at Gauss-Lobatto stations on each interval. The resulting CSF-computed sectional quantities are then compared with the closed-form reference.

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

The CSV export is a sampled, station-wise output obtained from the continuous CSF model. It is not the source definition of the model: the continuous geometry interpolation and participation fields are defined in the YAML files and assembled in `CSFStacked`.

The CSV files record what the model returns after evaluation at selected stations. Therefore, each CSV represents a finite set of sampled sections, not the continuous sectional field itself.

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
 [lobatto_station_export_7.csv](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/stacked_rectangular/out/lobatto_station_export_7.csv)
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
python run_stacked.py
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

## Interpretation

This case verifies that CSF can represent a member as a continuous sectional field in which geometry and participation fields vary independently along the member axis.

The constant total weighted area confirms that the compensation between `upper` participation-field variation and `lower` geometric variation is correctly represented. The variation of $C_y(z)$ and $I_x(z)$ confirms that a constant weighted area does not imply a constant weighted section. The constant $I_y(z)$ follows from the fixed width of the components and from the compensated total weighted area.

The station-wise CSV exports demonstrate a separate point: exported rows are sampled data generated from the continuous model. They are not the model object. The model object is the continuous CSF member representation composed of polygonal zones, geometric interpolation, and participation fields.
