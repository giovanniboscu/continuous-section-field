# Stacked rectangular member: single-interval inspection and stacked-member verification

This verification case is introduced from the CSF input file itself. The purpose is to make the reader first see what a single CSF YAML interval contains, how it is inspected with `csf-actions`, and only afterwards how two continuous intervals are assembled into a global `CSFStacked` member.

The case uses a simple stacked rectangular section with three polygonal components:

* `upper0`, `middle0`, `lower0` in the first interval;
* `upper1`, `middle1`, `lower1` in the second interval.

The geometry is intentionally elementary, but the sectional behaviour is not trivial. The `lower` component changes its geometry along the member axis, while the `upper` component keeps a fixed geometry and receives prescribed participation laws. The two variations are selected so that the total weighted area remains constant, even though the weighted centroid and bending inertia vary along the axis.

The first part of the example therefore uses `csf-actions` on a single YAML interval. This makes the content of the CSF file explicit before the global stacked-member verification is introduced.

---

## Inspection of the first CSF interval with `csf-actions`

The first interval is defined by:

```text
stacked_0.yaml
```

and is inspected with:

```text
stacked_actions.yaml
```

The command is:

```bash
csf-actions stacked_0.yaml stacked_actions.yaml
```

The first interval extends from $z = 0$ to $z = 5$. In the YAML file, this is expressed by two reference sections:

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

Each polygonal component is defined at both reference sections. CSF interpolates the component vertices along the interval. The result is not a table of precomputed sections, but a continuous section field that can be evaluated at any station $z$ inside the interval.

---

## Geometry encoded in `stacked_0.yaml`

At $z = 0$, the first interval contains three stacked rectangular components:

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

All components have the same width:

$$
B = 0.30 .
$$

The `upper0` component has constant height:

$$
h_u = 0.20
$$

and centroid coordinate:

$$
y_u = 0.10 .
$$

The `middle0` component has constant height:

$$
h_m = 0.30
$$

and centroid coordinate:

$$
y_m = -0.15 .
$$

The `lower0` component has its top edge fixed at:

$$
y = -0.30 .
$$

Its bottom edge moves from $y=-0.60$ at $z=0$ to $y=-0.50$ at $z=5$. Therefore, its height decreases linearly from $0.30$ to $0.20$.

Using the local coordinate

$$
t = \frac{z}{5}, \qquad 0 \le t \le 1,
$$

the lower-component height in the first interval is:

$$
h_l(t) = 0.30 - 0.10t .
$$

Its centroid coordinate is therefore:

$$
y_l(t) = -0.30 - \frac{h_l(t)}{2}.
$$

<p align="center">
  <em>Figure 1. Three-component stacked rectangular section sampled in the first CSF interval.</em>
</p>

<p align="center">
  <img width="264" height="522" alt="image" src="https://github.com/user-attachments/assets/b4aff836-bb40-474b-879b-f7a5f3205f0d" />
</p>

---

## Axial/bending participation field

The geometric variation of `lower0` is paired with an axial/bending participation law assigned to `upper0`.

In `stacked_0.yaml`, the law is:

```yaml
weight_laws:
  - 'upper0,upper0: 1.0 - 0.5*(1.0 - t)'
```

That is:

$$
w_u(t) = 1.0 - 0.5(1.0 - t)
$$

or, equivalently,

$$
w_u(t) = 0.5 + 0.5t .
$$

Thus, in the first interval, the axial/bending participation of `upper0` increases linearly:

$$
w_u(0) = 0.5, \qquad w_u(1) = 1.0 .
$$

The `middle0` and `lower0` components keep the axial/bending participation specified in the polygon definitions:

$$
w_m = 1, \qquad w_l = 1 .
$$

The first `plot_volume_3d` action visualizes the same interval using the axial/bending participation field:

```yaml
- plot_volume_3d:
    params:
      seed: w
      title: "Element with weight"
      line_percent: 100.0
```

This plot shows the geometry of the first interval and colors the volume according to the local value of `w`.

<p align="center">
  <em>Figure 2. First CSF interval colored by axial/bending participation <code>w</code>.</em>
</p>

<p align="center">
  <img width="700" alt="Element with weight" src="FIGURE_PLACEHOLDER_ELEMENT_WITH_WEIGHT" />
</p>

---

## Shear/torsion participation field

The example also assigns a shear/torsion participation field. In CSF this field is independent from the axial/bending participation field.

For `upper0`, the shear/torsion participation is prescribed directly:

```yaml
shear_weight_laws:
  - 'upper0,upper0: 1.0 - 0.8*(1.0-t)'
```

That is:

$$
\kappa_u(t) = 1.0 - 0.8(1.0 - t)
$$

or:

$$
\kappa_u(t) = 0.2 + 0.8t .
$$

Thus, over the first interval:

$$
\kappa_u(0) = 0.2, \qquad \kappa_u(1) = 1.0 .
$$

This law is not obtained from $w_u(t)$ through an isotropic relation. It is prescribed independently.

For `middle0` and `lower0`, the shear/torsion participation is assigned through the isotropic shortcut:

```yaml
shear_weight_laws:
  - 'lower0,lower0: iso(0.2)'
  - 'middle0,middle0: iso(0.2)'
```

Therefore:

$$
\kappa_m = \kappa_l = \frac{1}{2(1+0.2)} = 0.41666667 .
$$

The second `plot_volume_3d` action visualizes the same interval using the shear/torsion participation field:

```yaml
- plot_volume_3d:
    params:
      seed: s
      title: "Element with shear weight"
      line_percent: 100.0
```

This second plot uses the same geometry, but the color field is now `s`, i.e. the sampled shear/torsion participation.

<p align="center">
  <em>Figure 3. First CSF interval colored by shear/torsion participation <code>s</code>.</em>
</p>

<p align="center">
  <img width="700" alt="Element with shear weight" src="FIGURE_PLACEHOLDER_ELEMENT_WITH_SHEAR_WEIGHT" />
</p>

---

## Compensation mechanism in the first interval

The first interval is constructed so that two different variations compensate each other in terms of total weighted area.

The `upper0` component keeps a fixed geometry, but its axial/bending participation increases from $0.5$ to $1.0$. The `lower0` component keeps unit axial/bending participation, but its height decreases from $0.30$ to $0.20$.

The weighted area of the section is:

$$
A(t) = w_u(t) A_u^{\mathrm{geom}} + A_m^{\mathrm{geom}} + A_l^{\mathrm{geom}}(t).
$$

The fixed geometric areas of `upper0` and `middle0` are:

$$
A_u^{\mathrm{geom}} = B h_u = 0.30 \cdot 0.20 = 0.06,
$$

$$
A_m^{\mathrm{geom}} = B h_m = 0.30 \cdot 0.30 = 0.09.
$$

The geometric area of `lower0` is:

$$
A_l^{\mathrm{geom}}(t) = B h_l(t).
$$

For the first interval:

$$
w_u(t) = 0.5 + 0.5t, \qquad h_l(t) = 0.30 - 0.10t.
$$

The weighted contribution of `upper0` is:

$$
w_u(t) A_u^{\mathrm{geom}} = (0.5 + 0.5t) \cdot 0.06 = 0.03 + 0.03t.
$$

The geometric contribution of `lower0` is:

$$
A_l^{\mathrm{geom}}(t) = 0.30(0.30 - 0.10t) = 0.09 - 0.03t.
$$

Therefore:

$$
A(t) = (0.03 + 0.03t) + 0.09 + (0.09 - 0.03t) = 0.21.
$$

The total weighted area remains constant, but the internal distribution of weighted area changes. Consequently, the vertical weighted centroid $C_y(t)$ and the bending inertia $I_x(t)$ are not constant.

This is the purpose of the compensation mechanism: it isolates the difference between a constant total weighted area and a constant weighted section.

---

## Section sampling and local outputs

The action file samples the first interval at selected stations:

```yaml
stations:
  station_middle:
    - 2.5

  station_precise:
    - 0
    - 1
    - 2
    - 3
    - 4
    - 5
```

The two-dimensional section plot is generated at the middle station:

```yaml
- plot_section_2d:
    stations:
      - station_middle
    show_ids: false
    show_vertex_ids: false
    output:
      - [stdout, out/section_a.jpg]
```

At $z = 2.5$:

$$
t = \frac{2.5}{5} = 0.5 .
$$

The sampled upper-component participation values are:

$$
w_u(0.5) = 0.75, \qquad \kappa_u(0.5) = 0.60 .
$$

The lower-component height is:

$$
h_l(0.5) = 0.30 - 0.10(0.5) = 0.25 .
$$

The sampled section therefore shows the three rectangular components at the middle of the first interval, after interpolation of the `lower0` geometry and evaluation of the participation fields.

<p align="center">
  <em>Figure 4. Sampled two-dimensional section of <code>stacked_0.yaml</code> at $z=2.5$.</em>
</p>

<p align="center">
  <img width="450" alt="Section at z = 2.5" src="FIGURE_PLACEHOLDER_SECTION_AT_2_5" />
</p>

The same action file also plots selected section properties along the interval:

```yaml
- plot_properties:
    output:
      - stdout
      - out/section_properties.jpg
    params:
      num_points: 100
    properties: [A,Cy, Ix, Iy]
```

The expected behaviour over the first interval is:

| Quantity | Behaviour over `stacked_0.yaml`                            |
| -------- | ---------------------------------------------------------- |
| $A$      | constant, equal to $0.21$                                  |
| $C_y$    | varies because the weighted-area distribution changes      |
| $I_x$    | varies because the vertical distribution changes           |
| $I_y$    | remains constant for this rectangular stacked construction |

<p align="center">
  <em>Figure 5. Section-property variation over the first CSF interval.</em>
</p>

<p align="center">
  <img width="900" alt="Section properties over stacked_0.yaml" src="FIGURE_PLACEHOLDER_SECTION_PROPERTIES" />
</p>

The important point is that these plots and tables are produced by evaluating the YAML-defined continuous interval. They are not the model definition itself. The model is the CSF interval encoded in `stacked_0.yaml`; the figures and station-wise outputs are sampled consequences of that model.

---

## From one interval to two continuous intervals

After the first interval has been inspected, the second interval is introduced as the continuation of the same construction.

The second YAML file is:

```text
stacked_1.yaml
```

It spans:

$$
5 \le z \le 10 .
$$

Its local coordinate is:

$$
t = \frac{z-5}{5}.
$$

The second interval uses the same three-component stacked section, but with component names `upper1`, `middle1`, and `lower1`.

At $z=5$, the lower component has bottom edge $y=-0.50$; at $z=10$, it returns to $y=-0.60$. Therefore, its height increases linearly:

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

Thus, the second interval mirrors the first one in the global member: the lower geometry grows back, while the upper participation decreases.

For the second interval, the same area compensation holds:

$$
w_u(t) A_u^{\mathrm{geom}} = (1.0 - 0.5t) \cdot 0.06 = 0.06 - 0.03t,
$$

and:

$$
A_l^{\mathrm{geom}}(t) = 0.30(0.20 + 0.10t) = 0.06 + 0.03t.
$$

Therefore:

$$
A(t) = (0.06 - 0.03t) + 0.09 + (0.06 + 0.03t) = 0.21.
$$

The two intervals meet at $z=5$, where the lower-component height is $0.20$ and the upper participation reaches:

$$
w_u = 1.0, \qquad \kappa_u = 1.0 .
$$

This shared station is the junction between the two continuous CSF intervals.

---

## Assembly with `CSFStacked`

The global verification is performed by `run_stacked.py`.

The script reads the two YAML files:

```python
SEGMENT_FILES = ("stacked_0.yaml", "stacked_1.yaml")
```

and appends them into a single stacked object:

```python
stack = CSFStacked(eps_z=1e-9)

for file_name in SEGMENT_FILES:
    stack.append(load(file_name))
```

The resulting object is a global member representation over:

$$
0 \le z \le 10 .
$$

The first interval defines the field on $0 \le z \le 5$, and the second interval defines the field on $5 \le z \le 10$. The junction station $z=5$ is shared by the two intervals.

<p align="center">
  <em>Figure 6. Global CSF member representation obtained by stacking the two continuous intervals.</em>
</p>

<p align="center">
  <img width="816" height="706" alt="image" src="https://github.com/user-attachments/assets/3fefab64-20c4-4a84-914a-6a561c1b3cf5" />
</p>

---

## Closed-form verification of the stacked member

Once the two intervals are assembled, `run_stacked.py` evaluates the global CSF model at Gauss-Lobatto stations on each interval.

The station set is built by computing 11 Gauss-Lobatto stations on the first interval and 11 on the second interval. The duplicated junction station at $z=5$ is removed from the second list.

At each station, the script compares:

```python
stack.section_full_analysis(z, junction_side="left")
```

against the closed-form reference:

```python
reference(z)
```

The comparison uses:

$$
A, \qquad C_y, \qquad I_x, \qquad I_y .
$$

The reference model is constructed directly from the rectangular geometry and from the prescribed upper-component axial/bending participation law.

For each component $i$:

$$
A_i(z) = w_i(z) B h_i(z).
$$

The total weighted area is:

$$
A(z) = \sum_i A_i(z).
$$

The weighted vertical centroid is:

$$
C_y(z) = \frac{\sum_i A_i(z)y_i(z)}{A(z)}.
$$

The local second moments of each rectangular component are:

$$
I_{x,i}^{\mathrm{local}}(z) = \frac{B h_i(z)^3}{12},
$$

$$
I_{y,i}^{\mathrm{local}}(z) = \frac{h_i(z) B^3}{12}.
$$

The weighted second moment about the horizontal centroidal axis is:

$$
I_x(z) = \sum_i w_i(z) \left[ I_{x,i}^{\mathrm{local}}(z) + A_i^{\mathrm{geom}}(z) \left(y_i(z)-C_y(z)\right)^2 \right].
$$

The weighted second moment about the vertical axis is:

$$
I_y(z) = \sum_i w_i(z) I_{y,i}^{\mathrm{local}}(z).
$$

The shear/torsion participation field is part of the CSF model, and it is inspected in the single-interval action workflow. It is not used in this closed-form comparison because the compared quantities are axial/bending weighted quantities.

---

## Expected global behaviour

The full stacked member has the following expected behaviour:

| Quantity | Expected behaviour                                    |
| -------- | ----------------------------------------------------- |
| $A(z)$   | constant over the full member, equal to $0.21$        |
| $C_y(z)$ | continuous and symmetric, with maximum value at $z=5$ |
| $I_x(z)$ | continuous and symmetric, with minimum value at $z=5$ |
| $I_y(z)$ | constant over the full member                         |

Representative values are:

|  Station |    $A$ |       $C_y$ |       $I_x$ |       $I_y$ |
| -------: | -----: | ----------: | ----------: | ----------: |
|  $z = 0$ | $0.21$ | $-0.242857$ | $0.0096143$ | $0.0015750$ |
|  $z = 5$ | $0.21$ | $-0.150000$ | $0.0085750$ | $0.0015750$ |
| $z = 10$ | $0.21$ | $-0.242857$ | $0.0096143$ | $0.0015750$ |

The verification checks that the section properties computed by CSF coincide with the closed-form reference at the sampled Gauss-Lobatto stations. The reported errors are at floating-point roundoff level for this case.

---

## Station-wise CSV export

The script also exports selected station-wise CSV files:

```python
manual_station = [0, 3, 5, 7, 10]
```

with filenames of the form:

```text
out/lobatto_station_export_<z>.csv
```

Each CSV file is a sampled output of the continuous CSF model at one station. It is not the model definition.

The sequence is:

```text
continuous CSF model
→ section evaluation at z
→ sampled polygonal zones
→ CSV vertex rows with sampled metadata
```

Each exported row corresponds to one vertex of one sampled polygonal component. Component-level quantities such as `w`, `shear_w`, and `poisson` are repeated over the vertices of the same component because the CSV is a vertex-wise export format.

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

The empty `poisson` field for the upper component does not indicate missing data. It indicates that the shear/torsion participation was prescribed directly. By contrast, `middle` and `lower` carry `poisson = 0.2` because their shear/torsion participation was derived through `iso(0.2)`.

This confirms the separation between the model object and its sampled exports. The YAML files define the continuous CSF intervals; `CSFStacked` assembles them into a global member; the CSV files record finite station-wise evaluations of that continuous model.
