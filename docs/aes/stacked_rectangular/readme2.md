# Stacked rectangular member with compensated geometric variation and participation-field variation

This verification case demonstrates how a geometric variation and a participation-field variation can compensate exactly in weighted area while still producing continuous variations in weighted centroid and inertia.

The verification is organized from the CSF definition outward.

First, a single CSF interval (`stacked_0.yaml`) is inspected with `csf-actions`. The interval defines the section geometry, interpolation rules, axial/bending participation field, and shear/torsion participation field. Figures, tables, and sampled sections are obtained directly from evaluations of this continuous CSF interval.

Next, `stacked_0.yaml` and `stacked_1.yaml` are assembled into a global member using `CSFStacked`. The resulting stacked member is evaluated at Gauss-Lobatto stations and compared against a closed-form reference solution for $A$, $C_y$, $I_x$, and $I_y$.

No structural solver is involved in this example. The objective is to verify the continuous section field representation and its assembly into a stacked member.

---

## Files

| File                               | Role                                                                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `stacked_0.yaml`                   | First CSF interval, covering $0 \le z \le 5$                                                                                                     |
| `stacked_1.yaml`                   | Second CSF interval, covering $5 \le z \le 10$                                                                                                   |
| `stacked_actions.yaml`             | Action file used to inspect a single CSF interval with `csf-actions`                                                                             |
| `run_stacked.py`                   | Builds the stacked member, evaluates the closed-form reference, performs the CSF comparison, generates plots, and exports station-wise CSV files |
| `out/lobatto_station_export_7.csv` | Example CSV export for a sampled station                                                                                                         |


---

# 1. Inspection of a single CSF interval with `csf-actions`

The verification begins with the inspection of the first CSF interval, defined in `stacked_0.yaml`, using the action file `stacked_actions.yaml`.

From the directory containing both files:

```bash
csf-actions stacked_0.yaml stacked_actions.yaml
```

This command evaluates and visualizes the continuous section field defined by `stacked_0.yaml`. No stacked-member assembly is performed at this stage; the objective is to inspect the interval geometry, participation fields, sampled sections, and sectional properties before the two intervals are combined with `CSFStacked`.

---

## 1.1 Action file

The action file performs five complementary inspections of the same CSF interval:

1. `plot_volume_3d` with `seed: w` visualizes the interval using the axial/bending participation field.
2. `plot_volume_3d` with `seed: s` visualizes the interval using the shear/torsion participation field.
3. `section_selected_analysis` samples sectional quantities and polygon data at selected stations.
4. `plot_section_2d` generates a sampled cross-section at the interval midpoint.
5. `plot_properties` evaluates the variation of sectional properties along the interval.


---

## 1.2 Reference sections in `stacked_0.yaml`

The first interval is defined by two reference sections:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        ...
    S1:
      z: 5.0
      polygons:
        ...
```

The interval occupies

$$
0 \le z \le 5.
$$

The participation laws are expressed in terms of the local coordinate

$$
t = \frac{z}{5},
\qquad
0 \le t \le 1.
$$

The section consists of three vertically stacked rectangular polygonal regions:

```text
upper0
middle0
lower0
```

The `upper0` and `middle0` regions remain geometrically unchanged throughout the interval, while the `lower0` region shortens linearly as (z) increases.

At (z=0), the polygon vertices are:

```yaml
upper0:
  weight: 1.0
  vertices:
    - [-0.15,  0.00]
    - [ 0.15,  0.00]
    - [ 0.15,  0.20]
    - [-0.15,  0.20]

middle0:
  weight: 1.0
  vertices:
    - [-0.15, -0.30]
    - [ 0.15, -0.30]
    - [ 0.15,  0.00]
    - [-0.15,  0.00]

lower0:
  weight: 1.0
  vertices:
    - [-0.15, -0.60]
    - [ 0.15, -0.60]
    - [ 0.15, -0.30]
    - [-0.15, -0.30]
```

At (z=5), the `upper0` and `middle0` regions retain the same geometry, while the lower edge of `lower0` moves upward from (y=-0.60) to (y=-0.50):

```yaml
lower0:
  weight: 1.0
  vertices:
    - [-0.15, -0.50]
    - [ 0.15, -0.50]
    - [ 0.15, -0.30]
    - [-0.15, -0.30]
```

All three regions have the same width,

$$
B = 0.30.
$$

The `upper0` region has constant height

$$
h_u = 0.20
$$

and centroid coordinate

$$
y_u = 0.10.
$$

The `middle0` region has constant height

$$
h_m = 0.30
$$

and centroid coordinate

$$
y_m = -0.15.
$$

The top edge of `lower0` remains fixed at

$$
y = -0.30,
$$

while its height decreases linearly from (0.30) to (0.20) over the interval:

$$
h_l(t) = 0.30 - 0.10,t.
$$

The corresponding centroid coordinate is

$$
y_l(t) = -0.30 - \frac{h_l(t)}{2}.
$$

Figure 1 shows a sampled cross-section of the interval, highlighting the three stacked rectangular regions and the geometric configuration used throughout the verification.

---
## 1.3 Axial/bending participation field in the first interval

The axial/bending participation field is assigned only to the `upper0` component:

```yaml
weight_laws:
  - 'upper0,upper0: 1.0 - 0.5*(1.0 - t)'
```

This defines a linear variation,

$$
w_u(t) = 1.0 - 0.5(1.0 - t)
= 0.5 + 0.5t,
$$

ranging from

$$
w_u(0) = 0.5
$$

at the beginning of the interval to

$$
w_u(1) = 1.0
$$

at its end.

The `middle0` and `lower0` components retain the participation value specified in their polygon definitions:

$$
w_m = 1,
\qquad
w_l = 1.
$$

The participation field can be visualized with:

```yaml
- plot_volume_3d:
    params:
      seed: w
      title: "Element with weight"
      line_percent: 100.0
```

This action colors the interval according to the axial/bending participation field (w), making the gradual increase of the `upper0` contribution visible along the interval.


---

## 1.4 Shear/torsion participation field in the first interval

The shear/torsion participation field is defined independently of the axial/bending participation field.
For the `upper0` component, the participation law is prescribed directly:

```yaml
shear_weight_laws:
  - 'upper0,upper0: 1.0 - 0.8*(1.0-t)'

```

This defines a linear variation,
$$ \kappa_u(t) = 1.0 - 0.8(1.0 - t) = 0.2 + 0.8t, $$
ranging from
$$ \kappa_u(0) = 0.2 $$
at the beginning of the interval to
$$ \kappa_u(1) = 1.0 $$
at its end.
For the `middle0` and `lower0` components, the shear/torsion participation is assigned through the isotropic shortcut:

```yaml
shear_weight_laws:
  - 'lower0,lower0: iso(0.2)'
  - 'middle0,middle0: iso(0.2)'

```

which gives
$$ \kappa_m = \kappa_l = \frac{1}{2(1+0.2)} = 0.41666667. $$
The corresponding visualization is generated with:

```yaml
- plot_volume_3d:
    params:
      seed: s
      title: "Element with shear weight"
      line_percent: 100.0

```

This action colors the interval according to the shear/torsion participation field (s). In contrast to the axial/bending field, the upper component varies from (0.2) to (1.0), while the middle and lower components retain constant values derived from `iso(0.2)`.
Figure 2 shows the resulting shear/torsion participation field for the first CSF interval.

---

## 1.4 Shear/torsion participation field in the first interval

The shear/torsion participation field is defined independently of the axial/bending participation field.
For the `upper0` component, the participation law is prescribed directly:

```yaml
shear_weight_laws:
  - 'upper0,upper0: 1.0 - 0.8*(1.0-t)'

```

This defines a linear variation,
$$ \kappa_u(t) = 1.0 - 0.8(1.0 - t) = 0.2 + 0.8t, $$
ranging from
$$ \kappa_u(0) = 0.2 $$
at the beginning of the interval to
$$ \kappa_u(1) = 1.0 $$
at its end.
For the `middle0` and `lower0` components, the shear/torsion participation is assigned through the isotropic shortcut:

```yaml
shear_weight_laws:
  - 'lower0,lower0: iso(0.2)'
  - 'middle0,middle0: iso(0.2)'

```

which gives
$$ \kappa_m = \kappa_l = \frac{1}{2(1+0.2)} = 0.41666667. $$
The corresponding visualization is generated with:

```yaml
- plot_volume_3d:
    params:
      seed: s
      title: "Element with shear weight"
      line_percent: 100.0

```

This action colors the interval according to the shear/torsion participation field (s). In contrast to the axial/bending field, the upper component varies from (0.2) to (1.0), while the middle and lower components retain constant values derived from `iso(0.2)`.
Figure 2 shows the resulting shear/torsion participation field for the first CSF interval.

---

## 1.6 Section sampling at $z=2.5$

The action file samples the midpoint of the first interval:

```yaml
station_middle:
  - 2.5
```

At this station,

$$
t = \frac{2.5}{5} = 0.5.
$$

The upper-component participation values are

$$
w_u(0.5) = 0.75,
\qquad
\kappa_u(0.5) = 0.60.
$$

The height of the lower component is

$$
h_l(0.5) = 0.30 - 0.10(0.5) = 0.25.
$$

The corresponding section is generated with:

```yaml
- plot_section_2d:
    stations:
      - station_middle
    show_ids: false
    show_vertex_ids: false
    output:
      - [stdout, out/section_a.jpg]
```

The resulting plot represents the section obtained by evaluating the continuous CSF interval at \(z=2.5\). It is not a separate geometric definition, but a sampled realization of the continuously varying geometry and participation fields described by `stacked_0.yaml`.

Figure 1 shows the corresponding sampled section.

---

## 1.7 Section-property plot over the first interval

The variation of the sectional properties along the interval is generated with:

```yaml
- plot_properties:
    output:
      - stdout
      - out/section_properties.jpg
    params:
      num_points: 100
    properties: [A,Cy, Ix, Iy]
```

Based on the geometry and participation laws defined in `stacked_0.yaml`, the expected behaviour over the interval is:

| Quantity | Behaviour over $0 \le z \le 5$ |
|---|---|
| $A$ | constant and equal to $0.21$ |
| $C_y$ | varies because the weighted-area distribution changes |
| $I_x$ | varies because the vertical distribution of weighted area changes |
| $I_y$ | remains constant for this stacked rectangular configuration |

The property plot therefore provides a direct verification of the compensation mechanism introduced in the previous section. Although the total weighted area remains constant, the weighted centroid and the weighted second moment about the horizontal axis continue to evolve along the interval.

This local inspection also demonstrates that `stacked_0.yaml` is already a complete and evaluable CSF interval. Geometry, participation fields, sampled sections, and sectional properties are all derived from the same continuous YAML definition, without requiring any additional model description.

---

# 2. Continuation with the second interval

The second interval is defined in:

```text
stacked_1.yaml
```

It occupies:

$$
5 \le z \le 10 .
$$

The local coordinate is:

$$
t = \frac{z-5}{5}, \qquad 0 \le t \le 1 .
$$

The second interval uses the component names:

```text
upper1
middle1
lower1
```

At $z=5$, the lower edge of `lower1` is at $y=-0.50$. At $z=10$, it returns to $y=-0.60$. Therefore, the lower height increases from $0.20$ to $0.30$:

$$
h_l(t) = 0.20 + 0.10t .
$$

The upper axial/bending participation law is:

```yaml
weight_laws:
  - 'upper1,upper1: 1.0 - 0.5*t'
```

that is:

$$
w_u(t) = 1.0 - 0.5t .
$$

The upper shear/torsion participation law is:

```yaml
shear_weight_laws:
  - 'upper1,upper1: 1.0 - 0.8*t'
```

that is:

$$
\kappa_u(t) = 1.0 - 0.8t .
$$

For the second interval, the area compensation is:

$$
w_u(t) A_u^{\mathrm{geom}} = (1.0 - 0.5t) \cdot 0.06 = 0.06 - 0.03t,
$$

$$
A_l^{\mathrm{geom}}(t) = 0.30(0.20 + 0.10t) = 0.06 + 0.03t.
$$

Therefore:

$$
A(t) = (0.06 - 0.03t) + 0.09 + (0.06 + 0.03t) = 0.21 .
$$

The two intervals meet at $z=5$, where the lower height is $0.20$ and the upper participation values are:

$$
w_u = 1.0, \qquad \kappa_u = 1.0 .
$$

<p align="center">
  <em>Figure 3. Shear/torsion participation field of the upper component in the second CSF interval.</em>
</p>

<p align="center">
  <img width="986" height="453" alt="Upper shear/torsion participation in second interval" src="https://github.com/user-attachments/assets/c91e77b7-4ea8-4ccb-8a2a-08c4bb5b04e5" />
</p>

---

# 3. Assembly with `CSFStacked`

The global verification is performed by `run_stacked.py`.

The two interval files are listed as:

```python
SEGMENT_FILES = ("stacked_0.yaml", "stacked_1.yaml")
```

They are appended into a single `CSFStacked` object:

```python
stack = CSFStacked(eps_z=1e-9)

for file_name in SEGMENT_FILES:
    stack.append(load(file_name))
```

The resulting object represents the full member:

$$
0 \le z \le 10 .
$$

The first interval defines the field on $0 \le z \le 5$, and the second interval defines the field on $5 \le z \le 10$. The station $z=5$ is the common junction.

<p align="center">
  <em>Figure 4. Global CSF member representation obtained by stacking the two continuous intervals.</em>
</p>

<p align="center">
  <img width="816" height="706" alt="Global CSF member representation" src="https://github.com/user-attachments/assets/3fefab64-20c4-4a84-914a-6a561c1b3cf5" />
</p>

---

# 4. Closed-form reference for the stacked member

The stacked member is compared against a closed-form reference for:

$$
A, \qquad C_y, \qquad I_x, \qquad I_y .
$$

All quantities below use the global coordinate $z$; for each interval, $w_i(z)$ and $h_i(z)$ are obtained from the participation laws and the geometry through the local map $t(z)$ defined in Sections 1 and 2.

For each component $i$, define the geometric area:

$$
A_i^{\mathrm{geom}}(z) = B h_i(z) .
$$

The weighted area contribution is:

$$
A_i^{w}(z) = w_i(z) A_i^{\mathrm{geom}}(z) .
$$

The total weighted area is:

$$
A(z) = \sum_i A_i^{w}(z) .
$$

The weighted centroid coordinate is:

$$
C_y(z) = \frac{\sum_i A_i^{w}(z)y_i(z)}{A(z)} .
$$

The local second moments of each rectangular component about its own centroid are:

$$
I_{x,i}^{\mathrm{local}}(z) = \frac{B h_i(z)^3}{12},
$$

$$
I_{y,i}^{\mathrm{local}}(z) = \frac{h_i(z) B^3}{12} .
$$

The weighted second moment about the horizontal centroidal axis is:

$$
I_x(z) = \sum_i \left[ w_i(z) I_{x,i}^{\mathrm{local}}(z) + A_i^{w}(z)\left(y_i(z)-C_y(z)\right)^2 \right] .
$$

The weighted second moment about the vertical axis is:

$$
I_y(z) = \sum_i w_i(z) I_{y,i}^{\mathrm{local}}(z) .
$$

The shear/torsion participation field $\kappa_i(z)$ is part of the CSF model and is inspected through `csf-actions`, but it is not used in this closed-form comparison because $A$, $C_y$, $I_x$, and $I_y$ are axial/bending weighted quantities.

---

# 5. Gauss-Lobatto station evaluation

`run_stacked.py` evaluates the stacked CSF member at Gauss-Lobatto stations on each interval.

The station set is built by:

1. computing 11 Gauss-Lobatto stations on $0 \le z \le 5$;
2. computing 11 Gauss-Lobatto stations on $5 \le z \le 10$;
3. removing the duplicated junction station from the second list.

At each station, the script evaluates the CSF model by:

```python
stack.section_full_analysis(z, junction_side="left")
```

and compares it with:

```python
reference(z)
```

At the junction $z=5$ the section field is continuous, so the choice `junction_side="left"` is immaterial: evaluating from the left or from the right interval returns the same section.

The comparison reports:

- the global coordinate $z$;
- the active segment index `seg`;
- the local coordinate $t$;
- the analytical values of $w_u$ and $\kappa_u$, printed as `w_u` and `sw_u`;
- the CSF-computed values of $A$, $C_y$, $I_x$, and $I_y$;
- the corresponding closed-form values;
- the maximum relative error over $A$, $I_x$, and $I_y$;
- the absolute error in $C_y$.

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

The maximum errors reported by the run are:

```text
max relative error (A, Ix, Iy): 1.09e-13 %
max absolute error (Cy): 5.55e-17
```

These values are at floating-point roundoff level for this closed-form comparison.

---

# 6. Interpretation of the stacked-member comparison

The table shows that the CSF-computed values and the closed-form reference coincide along the full stacked member.

The first part of the table corresponds to `stacked_0.yaml`. In this interval, the lower component contracts and the upper axial/bending participation increases.

The second part of the table corresponds to `stacked_1.yaml`. In this interval, the lower component expands and the upper axial/bending participation decreases.

At the junction $z=5$, the stacked member has:

$$
w_u = 1.0, \qquad \kappa_u = 1.0, \qquad h_l = 0.20 .
$$

The same station is evaluated once in the comparison table. The property values are continuous through the junction.

The expected global behaviour is:

| Quantity | Behaviour over $0 \le z \le 10$ |
|---|---|
| $A(z)$ | constant over the full member, equal to $0.21$ |
| $C_y(z)$ | continuous and symmetric, with maximum value at $z=5$ |
| $I_x(z)$ | continuous and symmetric, with minimum value at $z=5$ |
| $I_y(z)$ | constant over the full member |

Representative values are:

| Station | $A$ | $C_y$ | $I_x$ | $I_y$ |
|---:|---:|---:|---:|---:|
| $z=0$ | $0.21$ | $-0.242857$ | $0.0096143$ | $0.0015750$ |
| $z=5$ | $0.21$ | $-0.150000$ | $0.0085750$ | $0.0015750$ |
| $z=10$ | $0.21$ | $-0.242857$ | $0.0096143$ | $0.0015750$ |

<p align="center">
  <em>Figure 5. Continuous sectional-property variation over the stacked member.</em>
</p>

<p align="center">
  <img width="989" height="869" alt="Continuous sectional-property variation" src="https://github.com/user-attachments/assets/812b2a89-dfaa-48f4-b609-52eaf7233397" />
</p>

The constant total weighted area confirms the compensation between the `upper` participation-field variation and the `lower` geometric variation. The variation of $C_y(z)$ and $I_x(z)$ confirms that a constant weighted area does not imply a constant weighted section.

---

# 7. Station-wise CSV export

After the stacked-member comparison, `run_stacked.py` exports selected station-wise CSV files:

```python
manual_station = [0, 3, 5, 7, 10]
```

with filenames of the form:

```text
out/lobatto_station_export_<z>.csv
```

Each CSV file is a sampled output of the continuous CSF model at one station. It is not the source definition of the model.

The sequence is:

```text
continuous CSF model
→ section evaluation at z
→ sampled polygonal zones
→ CSV vertex rows with sampled metadata
```

Each exported row corresponds to one vertex of a sampled polygonal component. The columns `w`, `shear_w`, and `poisson` are repeated over the vertices of the same component because those values are component-level data at that station.

For example, at $z=7$, the station lies in the second interval. The local coordinate is:

$$
t = \frac{7-5}{5} = 0.4 .
$$

The upper-component participation values are:

$$
w_u = 1.0 - 0.5(0.4) = 0.8,
$$

$$
\kappa_u = 1.0 - 0.8(0.4) = 0.68 .
$$

The lower height is:

$$
h_l = 0.20 + 0.10(0.4) = 0.24 .
$$

Since the lower top edge is fixed at $y=-0.30$, the lower edge is located at:

$$
y = -0.30 - 0.24 = -0.54 .
$$

The corresponding CSV export is:

```text
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

The empty `poisson` field for the upper component does not indicate missing data. It indicates that the shear/torsion participation was prescribed directly. The `middle` and `lower` components carry `poisson = 0.2` because their shear/torsion participation was derived through `iso(0.2)`.

This final export demonstrates the separation between the model object and the sampled rows. The YAML files define continuous CSF intervals; `CSFStacked` assembles them into a global member; the CSV files record finite station-wise evaluations of that continuous model.
