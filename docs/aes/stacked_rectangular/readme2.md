# Stacked rectangular member with compensated geometric variation and participation-field variation

This verification case illustrates how geometry and participation fields combine in a continuous section field. The example is intentionally simple: one component changes its geometry while another changes its material participation, with the two variations arranged to compensate exactly in total weighted area. This makes the role of the internal weighted-area distribution visible, since the centroid and bending inertia remain continuously variable even though the total weighted area is constant.

The verification is organized from the CSF definition outward.

First, a single CSF interval (`stacked_0.yaml`) is inspected with `csf-actions`. The interval defines the section geometry, interpolation rules, axial/bending participation field, and shear/torsion participation field. Figures, tables, and sampled sections are obtained directly from evaluations of this continuous CSF interval.

Next, `stacked_0.yaml` and `stacked_1.yaml` are assembled into a global member using `CSFStacked`. The resulting stacked member is evaluated at Gauss-Lobatto stations and compared against a closed-form reference solution for $A$, $C_y$, $I_x$, and $I_y$.

No structural solver is involved in this example. The objective is to verify the continuous section field representation and its assembly into a stacked member.

---


# 1. Inspection of a single CSF interval with `csf-actions`

The verification begins with the inspection of the first CSF interval, defined in `stacked_0.yaml`, using the action file `stacked_actions.yaml`.

From the directory containing both files:

```bash
csf-actions stacked_0.yaml stacked_actions.yaml
```


<p align="center">
  <em>Figure 1. First CSF interval from <code>stacked_0.yaml</code>, colored by the axial/bending participation field <code>w</code>.</em>
<img width="759" height="673" alt="image" src="https://github.com/user-attachments/assets/60d1bd76-0ad0-45bd-bd29-0e8ae8d8a93a" />

</p>





This command evaluates and visualizes the continuous section field defined by `stacked_0.yaml`. No stacked-member assembly is performed at this stage; the objective is to inspect the interval geometry, participation fields, sampled sections, and sectional properties before the two intervals are combined with `CSFStacked`.

---
## 1.1 Action file

The action file performs seven complementary inspections of the same CSF interval:

1. `plot_volume_3d` with `seed: w` visualizes the interval using the axial/bending participation field.
2. `plot_volume_3d` with `seed: s` visualizes the interval using the shear/torsion participation field.
3. `section_selected_analysis` samples sectional quantities and polygon data at selected stations.
4. `plot_section_2d` generates a sampled cross-section at the interval midpoint.
5. `plot_properties` evaluates the variation of sectional properties along the interval.
6. `plot_weight` plots the axial/bending participation field along the interval.
7. `plot_shear_weight` plots the shear/torsion participation field along the interval.

The corresponding action file is available here:

[`stacked_actions.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/stacked_rectangular/stacked_actions.yaml)

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
h_l(t) = 0.30 - 0.10t.
$$

The corresponding centroid coordinate is

$$
y_l(t) = -0.30 - \frac{h_l(t)}{2}.
$$

A sampled cross-section of the interval is shown in Figure 3, where the three rectangular regions are obtained by evaluating the continuous CSF definition at $z = 2.5$.

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

<p align="center">
  <em>Figure 2. CSF 3D representation of the first interval defined in <code>stacked_0.yaml</code> using the shear/torsion participation field. The geometry is the same continuous interval shown previously, while the color map now represents <code>shear_weight</code>.</em>
<img width="643" height="600" alt="image" src="https://github.com/user-attachments/assets/54017e2d-d8e4-4884-99fb-5299024aee6c" />

  
</p>

The shear/torsion participation field is defined independently of the axial/bending participation field.
For the `upper0` component, the participation law is prescribed directly:

```yaml
shear_weight_laws:
  - 'upper0,upper0: 1.0 - 0.8*(1.0-t)'

```

This defines a linear variation,

$\kappa_u(t) = 1.0 - 0.8\left(1.0 - t\right) = 0.2 + 0.8t$


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



## 1.5 Section sampling at $z=2.5$

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

<p align="center">
  <em>Figure 3. Sampled section at <code>z = 2.5</code> for the first interval defined in <code>stacked_0.yaml</code>. The plot shows the polygonal section obtained by evaluating the continuous CSF interval at the midpoint; the upper component has axial/bending participation <code>w = 0.75</code>.</em>

<img width="256" height="553" alt="image" src="https://github.com/user-attachments/assets/692b1303-f77c-4870-81d6-41e3dba81183" />


</p>


---

## 1.6 Section-property plot over the first interval


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

<p align="center">
  <em>Figure 4. Sectional properties evaluated along the first interval defined in <code>stacked_0.yaml</code>. The total weighted area <code>A</code> remains constant, while <code>Cy</code> and <code>Ix</code> vary continuously; <code>Iy</code> remains constant for this stacked rectangular configuration.</em>
  <img width="984" height="877" alt="image" src="https://github.com/user-attachments/assets/0e06b2b3-ed00-4aed-b4b7-212de9d42cd8" />
</p>





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
## 1.7 Scope of the interval inspection

The inspection performed with `csf-actions` concerns only the first CSF interval, `stacked_0.yaml`. At this stage, the objective is to verify the continuous description of geometry, axial/bending participation, shear/torsion participation, sampled sections, and derived sectional properties within a single interval.

No interval stacking is involved in this part of the verification. All plots, sampled sections, and sectional-property evaluations are obtained directly from the continuous field defined by `stacked_0.yaml`.

Having verified the behaviour of the first interval independently, the next step is to introduce `stacked_1.yaml` and assemble both intervals into a single continuous member. The global verification will then assess whether the stacked representation preserves continuity and reproduces the analytical reference solution over the full length of the member.

# 2. Continuation with the second interval

The first interval describes a progressive transfer of weighted area from the lower component to the upper component. The second interval, defined in `stacked_1.yaml`, completes this process by reversing the same trends.

This interval occupies

$$
5 \le z \le 10,
$$

with local coordinate

$$
t = \frac{z-5}{5},
\qquad
0 \le t \le 1.
$$

The section is again composed of three stacked rectangular regions,

```text
upper1
middle1
lower1
```

and starts from the geometric and participation state reached at the end of the first interval.

At the common station \(z=5\), the lower component has height

$$
h_l = 0.20,
$$

while the upper-component participation values are

$$
w_u = 1.0,
\qquad
\kappa_u = 1.0.
$$

From this configuration, the lower component gradually expands. Its lower edge moves from \(y=-0.50\) back to \(y=-0.60\), producing a linear height variation

$$
h_l(t) = 0.20 + 0.10t.
$$

At the same time, the participation fields of the upper component decrease linearly.

The axial/bending participation law is

```yaml
weight_laws:
  - 'upper1,upper1: 1.0 - 0.5*t'
```

which gives

$$
w_u(t) = 1.0 - 0.5t.
$$

The shear/torsion participation law is

```yaml
shear_weight_laws:
  - 'upper1,upper1: 1.0 - 0.8*t'
```

which gives

$$
\kappa_u(t) = 1.0 - 0.8t.
$$

Consequently, the second interval mirrors the first one: the lower region grows while the participation of the upper region decreases.

The compensation mechanism therefore remains active. The weighted contribution of the upper component is

$$
w_u(t)A_u^{\mathrm{geom}} = (1.0 - 0.5t)\cdot0.06 = 0.06 - 0.03t,
$$

while the geometric contribution of the lower component is

$$
A_l^{\mathrm{geom}}(t) = 0.30(0.20 + 0.10t) = 0.06 + 0.03t.
$$

Substituting these expressions into the total weighted area gives

$$
A(t) = (0.06 - 0.03t) + 0.09 + (0.06 + 0.03t) = 0.21.
$$

As in the first interval, the total weighted area remains constant even though the distribution of weighted area continues to evolve.

---

# 3. Assembly and evaluation with `CSFStacked`

The previous sections examined the two CSF intervals independently. The global verification is performed by assembling them into a single continuous member and evaluating that member over the full length of the structure.

In `run_stacked.py`, the interval definitions are listed as

```python
SEGMENT_FILES = ("stacked_0.yaml", "stacked_1.yaml")
```

and assembled into a `CSFStacked` object:

```python
stack = CSFStacked(eps_z=1e-9)

for file_name in SEGMENT_FILES:
    stack.append(load(file_name))
```


The resulting object represents a continuous sectional field over

$$
0 \le z \le 10.
$$


<p align="center">
  <em>Figure 5. Global member obtained after assembling the two CSF intervals. The figure shows the continuous member representation defined over the global coordinate <code>z</code>.</em>
<img width="773" height="647" alt="image" src="https://github.com/user-attachments/assets/2e6c2a34-5a96-40aa-af84-aacd4f753f39" />

</p>


The first interval defines the field on

$$
0 \le z \le 5,
$$

while the second interval defines the field on

$$
5 \le z \le 10.
$$

The station

$$
z = 5
$$

acts as the common junction between the two intervals. At this location, geometry and participation fields are continuous, allowing the assembled object to behave as a single member rather than as two disconnected segments.

The purpose of `CSFStacked` is not merely to store multiple intervals. Its primary role is to expose the assembled CSF model as a continuous sectional function over the full member length. From the user's perspective, the stacked model behaves as a single mapping from the global coordinate $z$ to the corresponding section evaluation.

The sectional quantities are obtained through

```python
stack.section_full_analysis(z, junction_side="left")
```

This call is the central point of the verification. It is the operational expression of the continuous field provided by CSF: for any admissible global coordinate $z$, the assembled model returns the section associated with that position, without requiring the user to manually select the interval or construct a discrete section table.

Conceptually, the evaluation process can be viewed as

```text
global coordinate z
→ locate active CSF interval
→ compute local coordinate t
→ evaluate geometry interpolation
→ evaluate participation fields
→ construct sampled section
→ compute sectional properties
```

The user therefore interacts only with the global coordinate $z$. The interval selection and local-coordinate mapping are handled internally by `CSFStacked`.

This interpretation is important because it reflects the fundamental idea of the Continuous Section Field formulation. The model is not a collection of discrete sections stored at selected stations. Instead, it defines a continuous field that can be sampled at any required position along the member:

$$
z \longmapsto S(z).
$$

The call

```python
stack.section_full_analysis(z, junction_side="left")
```

is therefore not a lookup operation on a predefined list of sections. It is the evaluation of the continuous CSF representation at the requested global coordinate.



# 4. Closed-form reference for the stacked member

To verify the assembled CSF member, the sectional properties computed by `CSFStacked` are compared against an independent closed-form reference.

The comparison is performed for the weighted area,

$$
A,
$$

the weighted centroid coordinate,

$$
C_y,
$$

and the weighted second moments,

$$
I_x,
\qquad
I_y.
$$

All quantities are expressed in terms of the global coordinate \(z\). For each interval, the geometric dimensions and participation values are obtained from the corresponding local coordinate \(t(z)\) defined in Sections 1 and 2.

For each component \(i\), the geometric area is

$$
A_i^{\mathrm{geom}}(z) = B h_i(z).
$$

The corresponding weighted area contribution is

$$
A_i^{w}(z) = w_i(z)A_i^{\mathrm{geom}}(z).
$$

The total weighted area is then

$$
A(z) = \sum_i A_i^{w}(z).
$$

Using these weighted contributions, the centroid coordinate is

$$
C_y(z) = \frac{\sum_i A_i^{w}(z)y_i(z)}{A(z)}.
$$

The local second moments of each rectangular component about its own centroid are

$$
I_{x,i}^{\mathrm{local}}(z) = \frac{B h_i(z)^3}{12},
$$

$$
I_{y,i}^{\mathrm{local}}(z) = \frac{h_i(z)B^3}{12}.
$$

The weighted second moment about the horizontal centroidal axis follows from the parallel-axis theorem:

$$
I_x(z) = \sum_i \left[w_i(z)I_{x,i}^{\mathrm{local}}(z) + A_i^{w}(z)\left(y_i(z)-C_y(z)\right)^2\right].
$$

The weighted second moment about the vertical centroidal axis is

$$
I_y(z) = \sum_i w_i(z)I_{y,i}^{\mathrm{local}}(z).
$$

These expressions provide the analytical reference used in the subsequent comparison with the CSF results.

The shear/torsion participation field \(\kappa_i(z)\) remains part of the CSF definition and was previously inspected through `csf-actions`. It does not enter the present comparison because the quantities \(A\), \(C_y\), \(I_x\), and \(I_y\) are derived from the axial/bending participation field \(w_i(z)\).

---

# 5. Gauss-Lobatto station evaluation

After assembling the global member and defining the analytical reference, the verification is performed by evaluating both descriptions at a common set of stations.

`run_stacked.py` generates a Gauss-Lobatto sampling grid on each interval:

1. 11 Gauss-Lobatto stations on (0 \le z \le 5);
2. 11 Gauss-Lobatto stations on (5 \le z \le 10);
3. removal of the duplicated junction station at (z=5).

The resulting station set spans the entire stacked member while preserving the interval junction only once.

At each station, the CSF section is evaluated through

```python
stack.section_full_analysis(z, junction_side="left")
```

and compared with the independent analytical solution

```python
reference(z)
```

The argument `junction_side="left"` is only relevant when a station lies exactly on an interval boundary. In this example the section field is continuous at (z=5), therefore evaluating the junction from the left or from the right interval produces identical results.

For every station, the script reports:

* the global coordinate (z);
* the active segment index (`seg`);
* the local interval coordinate (t);
* the analytical participation values (w_u) and (\kappa_u) (`sw_u`);
* the CSF-computed values of (A), (C_y), (I_x), and (I_y);
* the corresponding analytical values;
* the relative error for (A), (I_x), and (I_y);
* the absolute error for (C_y).

The complete report table is shown in the dedicated [comparison](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/stacked_rectangular/verification.md).

---


# 6. Interpretation of the stacked-member comparison

The [comparison](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/stacked_rectangular/verification.md) shows that the sectional properties computed by the assembled CSF model coincide with the corresponding closed-form reference along the entire member. The maximum reported discrepancies are at floating-point roundoff level:

$$
\max \varepsilon_{A,I_x,I_y} = 1.09 \times 10^{-13}%
$$

and

$$
\max | \Delta C_y | = 5.55 \times 10^{-17}.
$$

This confirms that the continuous sectional field provided by `CSFStacked` is evaluated consistently across both intervals and across the junction at

$$
z = 5.
$$

The key result is that the total weighted area remains constant along the member, while the centroid coordinate and the bending inertia about the horizontal axis vary continuously. Therefore, the example verifies that preserving

$$
A(z)
$$

does not imply preserving the internal distribution of the weighted area inside the section.

The assembled member behaves as a single continuous field:

$$
z \longmapsto S(z),
$$

rather than as a collection of independent section evaluations.


---


# 7. Station-wise CSV export

The station-wise CSV export is included to show what CSF evaluates before the reduction to sectional properties. At a prescribed global coordinate $z$, the assembled member is sampled and the resulting polygonal zones are written together with the participation and material data associated with each component.

In `run_stacked.py`, the selected export stations are

```python
manual_station = [0, 3, 5, 7, 10]
```

and each station produces a file of the form

```text
out/lobatto_station_export_<z>.csv
```

These files are not part of the model definition. They are discrete outputs obtained from the continuous CSF member at selected stations.

The export sequence is

```text
CSFStacked member
→ evaluation at global coordinate z
→ sampled polygonal zones
→ sampled component data
→ CSV vertex rows
```

Each CSV row corresponds to one vertex of one sampled polygonal component. The coordinates `x` and `y` describe the sampled geometry at that station, while `w`, `shear_w`, and `poisson` report the component-level data evaluated at the same position.

The values `w`, `shear_w`, and `poisson` are repeated over the vertices of the same component because they belong to the component, not to the individual vertex.

As an example, consider the export at

$$
z = 7.
$$

This station belongs to the second interval, with

$$
t = \frac{7 - 5}{5} = 0.4.
$$

For the upper component, the sampled participation values are

$$
w_u = 1.0 - 0.5(0.4) = 0.8,
$$

$$
\kappa_u = 1.0 - 0.8(0.4) = 0.68.
$$

For the lower component, the sampled height is

$$
h_l = 0.20 + 0.10(0.4) = 0.24,
$$

so the lower edge is located at

$$
y = -0.30 - 0.24 = -0.54.
$$

The corresponding CSV export is

```text
## GEOMETRY EXPORT ##
# z=7.0
idx_polygon,idx_container,s0_name,s1_name,w,shear_w,poisson,vertex_i,x,y
0,,upper1,upper1,0.8,0.68,,0,-0.15,0
0,,upper1,upper1,0.8,0.68,,1,0.15,0
0,,upper1,upper1,0.8,0.68,,2,0.15,0.2
0,,upper1,upper1,0.8,0.68,,3,-0.15,0.2
1,,middle1,middle1,1,0.416666666667,0.2,0,-0.15,-0.3
1,,middle1,middle1,1,0.416666666667,0.2,1,0.15,-0.3
1,,middle1,middle1,1,0.416666666667,0.2,2,0.15,0
1,,middle1,middle1,1,0.416666666667,0.2,3,-0.15,0
2,,lower1,lower1,1,0.416666666667,0.2,0,-0.15,-0.54
2,,lower1,lower1,1,0.416666666667,0.2,1,0.15,-0.54
2,,lower1,lower1,1,0.416666666667,0.2,2,0.15,-0.3
2,,lower1,lower1,1,0.416666666667,0.2,3,-0.15,-0.3

```

The empty `poisson` field for the upper component follows from the fact that its shear/torsion participation is prescribed directly. The `middle1` and `lower1` components instead report `poisson = 0.2`, consistently with the use of `iso(0.2)` for their shear/torsion participation.

This export separates the model from its sampled representation. The YAML files define the continuous CSF intervals; `CSFStacked` assembles them into a member defined over the global coordinate $z$; the CSV files record selected evaluations of that member.

The CSV files therefore contain station-wise samples of the continuous geometry and participation fields defined by the CSF model.

