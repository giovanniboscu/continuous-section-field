# From Prescribed Degradation Fields to Structural Assessment: Continuous-Field Analysis of a Tapered Prestressed Pole with Localized Degradation

<p align="center">
  <img
    src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/actions-examples/degraded_pole/img/volume_3D.jpg"
    alt="Three-dimensional model of the tapered prestressed concrete pole"
    width="400">
</p>

<p align="center">
  <em>Three-dimensional representation of the tapered prestressed concrete pole. The Z-axis is scaled independently for visualization purposes; the displayed aspect ratio is not the true geometric aspect ratio.</em>
</p>

The degraded pole example is a complete end-to-end application of Continuous Section Field, covering the entire workflow from model definition to stress evaluation and demonstrating its use for a complex, parametrically varying section with localized degradation.

It introduces the CSF representation, the geometric and material model, and the laws governing the longitudinal variation of the section. These continuous fields are then used to compute continuous sectional properties, perform the structural analysis, and recover the resulting stresses.

The example considers a degraded prestressed concrete pole represented by forty polygons. It demonstrates how a complex section, including multiple materials and localized degradation, can be described through a highly parametric, flexible, and customizable model.

A distinctive feature is the continuous nature of the geometric and material functions. In addition to evaluating sectional properties at any position, the model also makes it possible to compute numerical derivatives of the continuous fields, enabling analyses based directly on their spatial variation.

Overall, the example provides a practical overview of the complete CSF workflow, from input definition to stress evaluation, while demonstrating the framework’s applicability, flexibility, and ability to represent problems that go beyond conventional sectional-analysis software.

---

The pole is modelled as a cantilever member, fixed at the base and free at the top, so that its response can be evaluated under axial force, bending moments, shear forces, and torsion.

The geometry varies continuously along the longitudinal axis. It is defined from a reference section at the base and a reference section at the top. Intermediate sections are generated between these two geometries, allowing the external profile, the internal hollow core, the concrete layers, and the prestressing bars to vary consistently with height.

The same continuous representation is used for the material properties. Concrete regions and prestressing bars are treated as distinct components, each of which may have its own variation of stiffness and residual mechanical capacity along the pole.

Degradation can therefore be localized in two directions:

- within the cross-section, by assigning it to selected concrete regions or individual bars;
- along the pole, by prescribing the elevation range and intensity of the degradation.

At every elevation, the model provides the corresponding cross-section together with its effective geometry and material properties. These data are then used to evaluate the structural response and the local stress state.

Normal stresses due to axial force and bending moments are evaluated with the general Navier formulation. The calculation uses the actual centroid, effective area, second moments of area, and product of inertia of the section at the considered elevation.

Shear stresses are evaluated with the Jourawski formulation using the geometry and the material distribution available at the same elevation.

The result is a continuous structural description of the pole from base to top, including localized degradation of concrete and prestressing steel in both the cross-sectional and longitudinal directions.

> **Step-by-step workflow:** the complete procedure for cloning the repository, checking the geometry and material fields, running the mechanical analysis, and inspecting the generated outputs is described in [`run_degraded_pole_analysis.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/run_degraded_pole_analysis.md).

---

## 1. Physical model

<p align="center">
  <img
    src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/actions-examples/degraded_pole/img/pile_section.jpg"
    alt="Cross-section of the prestressed concrete pole"
    width="400">
</p>

<p align="center">
  <em>Cross-section of the hollow prestressed concrete pole used in the degraded-pole example.</em>
</p>

The structural member is a hollow tapered prestressed concrete pole.

The concrete annulus is divided into circumferential sectors. Each sector is further divided into concentric radial regions representing the different portions of the concrete wall, including the inner region, the reinforcement-containing region, and the external cover.

The prestressing reinforcement is represented by individual bars distributed around the circumference.

Because the pole is tapered, the external and internal dimensions, the boundaries of the radial regions, and the positions of the bars vary along the longitudinal axis.

Each concrete region and each prestressing bar may be assigned its own longitudinal degradation profile. This makes it possible to represent damage that is localized around the circumference, through the wall thickness, and along the pole height.

---

## 2. From the physical pole to the input model

The complete CSF model is defined in [`degradated_pole.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/degradated_pole.yaml).

The file translates the physical pole into:

1. the base and top reference cross-sections;
2. the concrete and prestressing-steel polygons;
3. the reference material properties assigned to each polygon;
4. the longitudinal laws governing the variation of axial/bending and shear/torsion participation.

>The model data can be modified as required, including the pole dimensions, radial layers, angular sectors, prestressing bars, reference material properties and degradation laws. The complete procedure for generating and modifying the model is described in  [`create_tapered_pole_explained.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/create_tapered_pole_explained.md). 

The guide explains how the healthy reference geometry and material properties are generated and how the selected longitudinal degradation laws are introduced into the final YAML model. 

### 2.1 Reference sections

The geometry is defined at two elevations:

- `S0` at `z = 0.0`, corresponding to the base;
- `S1` at `z = 15.0`, corresponding to the top.

Each reference section contains the same set of named polygons. The coordinates stored in `S0` and `S1` define the geometry of those polygons at the two ends of the pole.

The same polygon name in `S0` and `S1` identifies the same physical region. For example, `12_3_C` in `S0` and `12_3_C` in `S1` represent the same concrete region at the base and at the top.

The correspondence between polygons in `S0` and `S1` is determined by their order in the input file. The first polygon in `S0` is associated with the first polygon in `S1`, the second with the second, and so on. Their vertex coordinates are then interpolated to obtain the section geometry at each intermediate elevation `z`.

Polygon names are used to identify specific regions when assigning `weight_laws` and `shear_weight_laws`.

Polygon names referenced by the material laws are checked when the input file is loaded. A law can only refer to polygons that are present in the reference sections; unknown or inconsistent names are rejected.

### 2.2 Polygon subdivision and naming

<p align="center">
  <img
    src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/actions-examples/degraded_pole/img/section_h.jpg"
    alt="Polygon subdivision and naming of the prestressed concrete pole cross-section"
    width="750">
</p>

<p align="center">
  <em>Polygon-based representation of the cross-section. The first index identifies the circumferential sector, the second identifies the radial depth, and the suffix identifies the physical component.</em>
</p>

The concrete annulus is divided into 16 circumferential sectors and four concentric radial depths.

Each region is identified by a polygon name with the form:

```text
<sector>_<radial depth>_<component>
```

The three fields have the following meaning:

- `sector` ranges from `0` to `15` and identifies the angular position around the circumference;
- `radial depth` ranges from `1` to `4`, from the hollow core towards the external surface;
- `component` identifies the physical material:
  - `C` - concrete;
  - `CH` - concrete host region containing the prestressing reinforcement;
  - `S` - individual prestressing bar.

Examples:

- `0_1_C` - innermost concrete region of sector `0`;
- `12_2_CH` - reinforcement-hosting concrete region of sector `12`;
- `12_2_S` - prestressing bar located in sector `12`;
- `8_4_C` - outermost concrete region of sector `8`.

The radial subdivision is:

| Radial depth | Polygon family | Physical position |
|---:|---|---|
| `1` | `<sector>_1_C` | inner concrete layer adjacent to the hollow core |
| `2` | `<sector>_2_CH` | concrete region containing the prestressing bars |
| `3` | `<sector>_3_C` | intermediate outer concrete layer |
| `4` | `<sector>_4_C` | external concrete cover |

Each sector also contains one steel polygon named `<sector>_2_S`, located within radial depth `2`.

### 2.3 Geometry and stiffness in the YAML file

The YAML file describes the model through a hierarchy of sections, polygons, coordinates, and material rules.

A reduced view of the input structure is:

```yaml
CSF:
  sections:

    S0:
      z: 0.0
      polygons:
        0_1_C:
          weight: 35000000000.0
          vertices:
            - [x_0, y_0]
            - [x_1, y_1]
            # ...

    S1:
      z: 15.0
      polygons:
        0_1_C:
          weight: 35000000000.0
          vertices:
            - [x_0, y_0]
            - [x_1, y_1]
            # ...

  shear_weight_laws:
    - 'iso(0.2)'

  weight_laws:
    - '0_2_CH,0_2_CH: w0*T_lookup("laws/weight_law_0_2_CH.dat")'
```

The YAML elements have the following meaning:

| YAML element | Meaning |
|---|---|
| `CSF` | Top-level container of the complete section model. |
| `sections` | Collection of the reference cross-sections used to describe the pole along its longitudinal axis. |
| `S0` | Reference section at the base of the pole. |
| `S1` | Reference section at the top of the pole. |
| `z` | Longitudinal coordinate of the reference section. In this example, `S0` is at `z = 0.0` and `S1` is at `z = 15.0`. |
| `polygons` | Ordered collection of the polygonal regions forming the cross-section. |
| `0_1_C` | Name assigned to a polygon. Polygon names identify physical regions when assigning material laws and reading results. |
| `vertices` | Ordered list of `[x, y]` coordinates defining the polygon boundary at that reference section. |
| `weight` | Scalar value used for axial and bending calculations. In this example, it contains the elastic modulus **E**. |
| `shear_weight_laws` | Rules used to define the stiffness associated with shear and torsion. |
| `iso(0.2)` | Isotropic relation used to obtain the shear modulus **G** from **E**, using Poisson's ratio `0.2`. Because no polygon names are specified, the rule is initially applied to all polygons. |
| `weight_laws` | Rules defining how the axial and bending weight varies along the pole. |
| `0_2_CH,0_2_CH` | Names of the polygons at the two reference sections to which the law is assigned. |
| `w0` | Weight assigned to the polygon in the first reference section, `S0`. |
| `T_lookup(...)` | Function that reads the longitudinal multiplier from the specified lookup file. |

The polygons in `S0` and `S1` are associated by their order in the YAML file:

- the first polygon in `S0` corresponds to the first polygon in `S1`;
- the second polygon corresponds to the second;
- the same rule continues for all subsequent polygons.

This ordered correspondence defines how each polygon geometry varies between the two reference sections.

Polygon names have a different purpose: they allow a specific physical region to be selected when assigning `weight_laws` and `shear_weight_laws`. The names used in a law are checked when the model is loaded. The input is rejected if a referenced name is missing or if the two named polygons do not occupy corresponding positions in `S0` and `S1`.


### 2.4 Default variation between `S0` and `S1`

Each polygon has a `weight` value in `S0`, denoted by `w0`, and a corresponding value in `S1`, denoted by `w1`.

By default, the model evaluates the polygon weight at each intermediate elevation `z` by linear interpolation between `w0` and `w1`.

In this example, `w0` and `w1` are equal for each polygon. The default interpolation would therefore produce a constant elastic modulus along the pole.

For selected polygons, this default variation is overridden by a specific longitudinal law, as described in the following section.


### 2.5 Prescribed degradation laws

The model requires a degradation profile with a prescribed variation of the elastic modulus along `z`.

These profiles are defined by `weight_laws` and by lookup files stored in the [`laws`](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/degraded_pole/laws) directory.

When a `weight_law` is assigned to a polygon, it supersedes the basic variation obtained from the values stored in `S0` and `S1`.

A typical rule is:

```yaml
weight_laws:
  - '0_2_CH,0_2_CH: w0*T_lookup("laws/weight_law_0_2_CH.dat")'
```

The lookup file contains two columns:

```text
z_over_L  value
0.000000  0.100000
0.500000  0.100000
0.600000  1.000000
1.000000  1.000000
```

- `z_over_L` is the normalized longitudinal position, from `0` at the base to `1` at the top;
- `value` is a normalized factor, generally between `0` and `1`;
- the factor multiplies the polygon weight defined at `S0`.

The resulting polygon weight is:

$$
w(z) = w_0 T\left(\frac{z}{L}\right)
$$

where:

- `w0` is the polygon weight at `S0`;
- `T(z/L)` is the factor read from the lookup file.

Because `weight` represents **E** in this example, the lookup directly defines the longitudinal variation of the elastic modulus.

A value of `1.0` preserves the initial modulus. A lower value represents the residual fraction at that position.

Each concrete region and each prestressing bar may use its own lookup file. Degradation can therefore be assigned independently to different parts of the cross-section and to different height intervals.

### 2.6 Shear and torsional stiffness

The model also supports a separate stiffness for shear and torsion, identified as `shear_weight` and associated with the shear modulus **G**.

In this example, **G** is obtained from **E** through an isotropic relation based on Poisson’s ratio.

The `shear_weight_laws` block first assigns a general rule:

```yaml
shear_weight_laws:
  - 'iso(0.2)'
```

Because no polygon names are specified, this rule is applied to the entire model.

More specific entries may then replace the general rule for selected polygons. Here, the listed prestressing-bar polygons use Poisson’s ratio `0.30`:

```yaml
shear_weight_laws:
  - 'iso(0.2)'

  - '1_2_S,1_2_S: iso(0.30)'
  - '2_2_S,2_2_S: iso(0.30)'
  - '3_2_S,3_2_S: iso(0.30)'
  - '4_2_S,4_2_S: iso(0.30)'
  - '5_2_S,5_2_S: iso(0.30)'
  - '6_2_S,6_2_S: iso(0.30)'
  - '7_2_S,7_2_S: iso(0.30)'
  - '8_2_S,8_2_S: iso(0.30)'
  - '9_2_S,9_2_S: iso(0.30)'
  - '10_2_S,10_2_S: iso(0.30)'
  - '11_2_S,11_2_S: iso(0.30)'
  - '12_2_S,12_2_S: iso(0.30)'
  - '13_2_S,13_2_S: iso(0.30)'
  - '14_2_S,14_2_S: iso(0.30)'
  - '15_2_S,15_2_S: iso(0.30)'
```

A separate longitudinal variation of **G** could also be defined through dedicated shear-weight laws. That option is available but is not used in this example.


### 2.7 Absolute and normalized stiffness weights


In the framework, you have the flexibility to define material properties either as **absolute values** or as **normalized weights**.

**In this specific example**, we use **absolute values** for the elastic moduli (as shown in the YAML file in Section 2.3). For instance, the concrete is assigned `weight = 35.0e9 Pa`, which is its actual Young's modulus.

However, the framework also supports an **alternative approach** using normalized weights. This is particularly useful when you want to define a single reference material and scale all others relative to it. In that case:

$$
w_{0,i} = \frac{E_i}{E_{\mathrm{ref}}}
$$

$$
w_{s0,i} = \frac{G_i}{G_{\mathrm{ref}}}
$$

---

## 3. Section generated at any elevation

After the reference sections, polygon names, and material laws have been defined, the model can generate the complete cross-section at any longitudinal coordinate `z`.

The section at that elevation is denoted by:

$$
S(z)
$$

Given `z`, the model provides:

- the complete section geometry;
- the polygons present at that elevation;
- the stiffness assigned to each polygon;
- the degradation level of each component;
- the data required for sectional and structural analysis.

This section-generating representation is called a **Continuous Section Field (CSF)**.

---
## 4. Structural analysis

The file `cantilever_beam_pole.py` performs a static check of the pole at a set of selected elevations.

The calculation is based directly on the Continuous Section Field defined in `degradated_pole.yaml`. The script does not create a finite-element beam model and does not calculate displacements. Instead, it evaluates the actual cross-section and its material properties at each requested longitudinal position `z`.

The calculation follows this sequence:

1. read the analysis settings;
2. load the Continuous Section Field;
3. evaluate the cross-section at each requested elevation;
4. calculate the residual prestressing force and its position;
5. calculate the axial force and bending moments acting on the section;
6. derive the shear forces from the variation of the bending moments;
7. calculate the normal and shear stresses;
8. write the results to CSV and text files.

Each step is described below.

### 4.1 Analysis settings

The analysis is controlled by `pole_analysis_settings.yaml`.

The settings file specifies:

- the CSF model to load;
- the type of polygon representing the prestressing bars;
- the prestressing force of the healthy pole;
- the elevations at which the pole must be checked;
- the applied force and torque;
- the numerical settings used for the shear calculation;
- the names and location of the output files.

For example:

```yaml
model:
  csf_yaml: degradated_pole.yaml

prestress:
  bar_type: S
  force_healthy: -1.256e6

loads:
  tip_force_y: 7350.0
  tip_torque_z: 0.0
```

The negative value of `force_healthy` represents the sign assigned to the prestressing force in this model. The script preserves the signs supplied in the settings file.

### 4.2 Loading the Continuous Section Field

The function `build_section_field()` reads `degradated_pole.yaml` through `CSFReader`.

```python
section_field = build_section_field(settings.csf_yaml)
```

The returned object, `section_field`, represents the complete pole between its initial section `S0` and final section `S1`.

It contains:

- the geometry of the polygons;
- their longitudinal geometric variation;
- the elastic modulus assigned to each polygon;
- the longitudinal degradation laws;
- the shear-stiffness laws.

The field is continuous along the longitudinal coordinate `z`. Therefore, the script can request a section at any elevation within the pole:

```python
section = section_field.section(z)
```

This operation produces the cross-section corresponding to that specific elevation, including the geometry and material properties evaluated at `z`.

The elevations used by the analysis are listed in `z_stations`:

```yaml
z_stations:
  - 0
  - 1
  - 2
  # ...
  - 14.25
  - 15
```

These values define where results are written. They do not divide the pole into finite elements.

### 4.3 Identifying the prestressing bars

The cross-section contains several polygon types. Prestressing bars are identified from their polygon names.

The expected naming convention is:

```text
<sector>_<level>_<bar_type>
```

For this model, `bar_type` is `S`. Therefore, names such as:

```text
0_2_S
1_2_S
15_2_S
```

are recognized as prestressing-bar polygons.

The function:

```python
is_prestressing_bar_name(name, bar_type)
```

checks whether a polygon name follows this convention.

Only these polygons are used to calculate the residual prestressing force.

### 4.4 Residual contribution of each prestressing bar

At a given elevation `z`, the script first evaluates the actual section:

```python
section = section_field.section(z)
```

For each prestressing-bar polygon, it obtains:

- its geometric area;
- its current elastic modulus;
- its reference elastic modulus.

The ratio between the current and reference values is:

```text
q_eff = current weight / reference weight
```

In this example, `weight` represents the elastic modulus **E**. Therefore, `q_eff` describes the residual stiffness assigned to the bar at that elevation.

A healthy bar has:

```text
q_eff = 1
```

A degraded bar can have:

```text
q_eff < 1
```

The script converts this ratio into an effective bar area:

```text
effective area = geometric area × q_eff
```

This effective area is a calculation quantity used to reduce the contribution of a degraded prestressing bar.

The geometric bar area remains unchanged in the CSF geometry. The reduction is introduced through the longitudinal material law.

### 4.5 Resultant of the prestressing bars

The effective areas of all prestressing bars are added:

```text
area_effective = sum of the effective bar areas
```

The corresponding undegraded reference area is:

```text
area_reference = sum of the geometric bar areas
```

The residual prestressing ratio is then:

```text
residual ratio = area_effective / area_reference
```

This ratio is used to scale the prestressing force of the healthy pole.

The position of the residual prestressing resultant is calculated from the effective-area-weighted centroids of the bars:

```text
xp = sum(x_bar × effective area) / area_effective
yp = sum(y_bar × effective area) / area_effective
```

When degradation is distributed symmetrically, the resultant remains close to the centre of the bar arrangement.

When degradation is asymmetric, the resultant moves toward the bars retaining the greater effective contribution.

The function performing this calculation is:

```python
prestress_bar_resultant_at_z(...)
```

It returns:

- `area_effective`;
- `area_reference`;
- `ratio`;
- `x_resultant`;
- `y_resultant`.

### 4.6 Section centroid and prestress eccentricity

Two different points are required at each elevation `z`.

The first point, `(xp, yp)`, is the position of the residual prestressing resultant. It is calculated using only the prestressing-bar polygons and their effective residual areas.

The second point, `(Cx, Cy)`, is the stiffness-weighted centroid of the complete CSF cross-section at the same elevation. It includes all material regions represented in the section, with their current geometry and elastic weights.

The function:

```python
section_centroid_at_z(section_field, z)
```

evaluates the CSF section at `z` and calculates its stiffness-weighted centroid:

```text
Cx, Cy
```

The eccentricity of the prestressing resultant relative to this centroid is:

```text
ex = xp - Cx
ey = yp - Cy
```

The two points have different meanings:

- `(xp, yp)` is the position of the residual prestressing resultant;
- `(Cx, Cy)` is the centroid of the complete section used for the axial and bending calculation.

Local degradation can move either point. Their difference determines the bending moments produced by the eccentric prestressing force.



### 4.7 Residual prestressing force

The healthy prestressing force is read from the settings file:

```yaml
prestress:
  force_healthy: -1.256e6
```

At each elevation, the residual force is calculated as:

```text
Pp = force_healthy × residual ratio
```

The force therefore varies with `z` when the degradation of the prestressing bars varies along the pole.

The function:

```python
prestress_state_at_z(...)
```

combines the results of the previous steps and returns:

- the residual prestressing force `Pp`;
- the resultant coordinates `xp` and `yp`;
- the section centroid `Cx` and `Cy`;
- the eccentricities `ex` and `ey`;
- the residual ratio.

### 4.8 External bending moment

The pole is treated as a cantilever of length `L`, with a transverse force applied at its top.

At elevation `z`, the distance from the checked section to the top is:

```text
arm = L - z
```

The bending moment generated by `tip_force_y` is:

```text
Mx_ext = -tip_force_y × (L - z)
My_ext = 0
```

With the active settings:

```yaml
tip_force_y: 7350.0
```

the external bending moment is largest at the base and decreases linearly to zero at the top.

The minus sign belongs to the convention explicitly adopted by the script.

### 4.9 Bending moments generated by prestress eccentricity

The residual prestressing force acts at `(xp, yp)`, while the section calculation is referred to `(Cx, Cy)`.

The resulting prestress moments are:

```text
Mx_prestress = Pp × ey
My_prestress = Pp × ex
```

These moments can vary along the pole because all the following quantities can depend on `z`:

- `Pp`;
- `xp`;
- `yp`;
- `Cx`;
- `Cy`;
- `ex`;
- `ey`.

The total section actions are:

```text
N  = Pp
Mx = Mx_ext + Mx_prestress
My = My_ext + My_prestress
Tz = tip_torque_z
```

The function:

```python
moment_state_at_z(...)
```

performs this calculation at one elevation.

### 4.10 Shear forces obtained from the moment variation

The transverse shear forces are obtained from the longitudinal derivatives of the bending moments.

The script uses the convention:

```text
Tx = dMy/dz
Ty = dMx/dz
```

This step is important because the total moments include both:

- the moment produced by the external top force;
- the moments produced by the eccentric residual prestress.

Consequently, a variation of the degradation profile can also contribute to the moment gradient.

The derivatives are evaluated numerically with a central difference:

```text
dMx/dz = [Mx(z + dz) - Mx(z - dz)] / (2 dz)
dMy/dz = [My(z + dz) - My(z - dz)] / (2 dz)
```

The value of `dz` is read from the settings:

```yaml
moment_gradient:
  dz: 0.01
  scheme: central_shift_inside_domain
```

Near the base and the top, the centre of the differentiation interval is shifted inside the valid CSF domain. This allows the same central-difference formula to be used without evaluating sections outside the pole.

**This is only possible because `Mx(z)` and `My(z)` are pointwise evaluations of a continuous field, not entries in a pre-discretized list of sections.** The step `dz` is a free numerical choice, unconstrained by any underlying structural mesh, and the window can be shifted to any valid axial coordinate - including non-grid points near the boundaries - without approximation. In a discretized model, this shift would require interpolation between fixed nodes; here, it is simply another query to the generating field.

The functions involved are:

```python
gradient_window(...)
internal_actions_at_z(...)
```

`internal_actions_at_z()` returns the complete action set passed to the stress calculations:

```text
N, Mx, My, Tx_jourawski, Ty_jourawski, Tz
```

### 4.11 Removal of numerical residuals

The central-difference calculation and the evaluation of asymmetric sections can produce extremely small numerical values where the theoretical result is zero.

Before calculating stresses, the function:

```python
snap_actions_for_stress(...)
```

compares each moment and shear component with a tolerance based on the characteristic force, moment and pole length.

Values smaller than this tolerance are replaced by exactly zero.

This operation removes numerical noise only. Values representing significant physical actions remain unchanged.

### 4.12 Normal-stress calculation

The function:

```python
navier_rows_at_z(...)
```

passes the section and the actions:

```text
N, Mx, My
```

to:

```python
analyse_polygon_navier_stress(...)
```

The CSF stress function evaluates the general Navier stress field over the actual section at `z`.

For every polygon, it checks all vertices and returns:

- the minimum signed normal stress;
- the maximum signed normal stress;
- the signed stress having the largest absolute value;
- the coordinates of the corresponding vertices.

Because the polygon weight represents **E**, stresses are recovered using the local elastic modulus assigned to each material region.

### 4.13 Shear-stress calculation

The function:

```python
shear_rows_at_z(...)
```

passes:

```text
Tx_jourawski
Ty_jourawski
```

to:

```python
analyse_polygon_jourawski_shear_stress(...)
```

The Jourawski calculation is performed on the complete section at the selected elevation.

The section is scanned by vertical and horizontal cuts. For every cut, the method evaluates:

- the active section width;
- the partial first moments of area;
- the transformed section inertias;
- the reference Jourawski shear stress;
- the redistribution of shear stress among the intersected material regions.

The settings:

```yaml
shear:
  num_sudx: 20
  num_sudy: 20
```

control the density of the section scans.

For each polygon, the function returns the minimum and maximum values of:

```text
tau_x
tau_y
```

together with their coordinates.

### 4.14 The `run()` function

The function `run()` coordinates the complete calculation.

It first creates the output directory and loads the Continuous Section Field:

```python
settings.output_directory.mkdir(parents=True, exist_ok=True)
section_field = build_section_field(settings.csf_yaml)
```

It then processes the elevations listed in `z_stations` one at a time:

```python
for z in settings.z_stations:
```

At each elevation, the operations are executed in this order:

```python
prestress = prestress_state_at_z(...)
raw_actions = internal_actions_at_z(...)
actions = snap_actions_for_stress(...)
navier_rows = navier_rows_at_z(...)
shear_rows = shear_rows_at_z(...)
```

The sequence has a direct mechanical meaning:

```text
continuous CSF model
        ↓
section evaluated at z
        ↓
residual prestressing resultant
        ↓
axial force and bending moments
        ↓
moment gradients and shear forces
        ↓
normal and shear stresses
```

The individual functions do not store one fixed section for the entire pole. Whenever a quantity is required at a new elevation, they query the continuous field again.

For example, the calculation of a moment gradient requires the sections and prestress states at:

```text
z - dz
z + dz
```

The CSF model supplies both directly.

After all stations have been processed, `run()` writes:

- the residual prestress resultants;
- the internal actions;
- the polygon-wise Navier stresses;
- the polygon-wise Jourawski stresses;
- the polygon vertices at the analysed elevations;
- the mechanical summary report;
- optional diagnostic files when debugging is enabled.

Therefore, `run()` is the execution sequence of the static check, while the Continuous Section Field remains the source of the geometry and material properties required at every longitudinal position.

---

## 5. Sectional results

The project evaluates the sectional response at selected elevations along the pole.

The main quantities include:

- area;
- centroid coordinates;
- second moments of area;
- product of inertia;
- axial stiffness;
- bending stiffness;
- shear-related properties;
- torsional properties;
- normal stresses;
- shear stresses.

These quantities are evaluated from the Continuous Section Field at the required elevation `z`. Some of them are used internally to calculate the section actions and stresses, while the output files provide the quantities needed to inspect, compare and post-process the final sectional response.

Normal stresses are evaluated from the general Navier stress field using:

$$
N,\quad M_x,\quad M_y
$$

Shear stresses are evaluated with the Jourawski-based section procedure using:

$$
T_x,\quad T_y
$$

The results retain the signed stress values and the coordinates of the governing points.

The output directory is available at:

[`actions-examples/degraded_pole/output`](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/degraded_pole/output)

The files are organized so that the calculation can first be read through a compact text report and then examined in full detail through the CSV files.

### 5.1 Human-readable mechanical report

The main readable result is:

[`mechanical_report.txt`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/output/mechanical_report.txt)

This file provides a compact engineering summary of the complete analysis. It is intended for direct inspection without requiring a spreadsheet or a separate post-processing script.

The report is divided into several blocks.

#### 5.1.1 Model

The `MODEL` block identifies the model used for the calculation.

It reports:

- the CSF YAML file from which the pole is loaded;
- the material tag used to identify the prestressing-bar polygons;
- the number of elevations included in the analysis.

This block establishes which Continuous Section Field and which set of calculation stations produced the reported results.

#### 5.1.2 Loads

The `LOADS` block reports the actions supplied through the analysis settings:

- the prestressing force assigned to the healthy pole;
- the transverse force applied at the pole tip;
- the torque applied about the longitudinal axis.

These are input quantities. The prestressing force subsequently used at each elevation can differ from the healthy value because it is scaled according to the residual contribution of the prestressing bars.

The signs are retained exactly according to the convention used by the calculation.

#### 5.1.3 Shear and moment-gradient settings

The `SHEAR / MOMENT GRADIENT` block records the numerical settings used to derive and evaluate the transverse shear response.

It includes:

- `num_sudx`, which controls the section scan associated with the `x` shear component;
- `num_sudy`, which controls the section scan associated with the `y` shear component;
- the numerical scheme used to evaluate the variation of the bending moments along `z`;
- the longitudinal increment `dz` used by the central-difference calculation.

This information is included because the Jourawski stress envelopes depend on the calculated shear actions and on the spatial resolution used to scan the section.

#### 5.1.4 Global extremes

The `GLOBAL EXTREMES` block gives a first overview of the most demanding results found in the complete set of analysed elevations.

It reports:

- the minimum normal stress;
- the maximum normal stress;
- the signed normal stress having the largest absolute magnitude;
- the minimum and maximum values of `tau_x`;
- the minimum and maximum values of `tau_y`.

The values are selected from all polygons and all analysed elevations.

The sign remains part of the result. For example, the governing normal stress is not reported only as an absolute magnitude: its original tensile or compressive sign is preserved.

This block is useful for identifying the overall stress range, while the following tables show where the values occur.

#### 5.1.5 Station summary

The `STATION SUMMARY` contains one row for each analysed elevation `z`.

The action columns are:

- `N`: axial force acting on the section;
- `Mx`: total bending moment about the `x` axis;
- `My`: total bending moment about the `y` axis;
- `Tx`: transverse shear action associated with the longitudinal variation of `My`;
- `Ty`: transverse shear action associated with the longitudinal variation of `Mx`;
- `Tz`: torque about the longitudinal axis.

The total bending moments include the external-load contribution and the contribution generated by the eccentric residual prestressing force.

The stress columns are:

- `sig_min`: minimum normal stress found among all polygons at that elevation;
- `sig_max`: maximum normal stress found among all polygons at that elevation;
- `sig_ext`: signed normal stress having the largest absolute magnitude at that elevation.

Therefore, each row connects the internal actions acting on one section with the corresponding normal-stress envelope.

The current stress output consists of the Navier normal stresses generated by `N`, `Mx` and `My`, and the Jourawski transverse shear stresses generated by `Tx` and `Ty`. `Tz` is retained in the action results.

#### 5.1.6 Shear legend

The `SHEAR LEGEND` explains how the governing shear value is selected.

For every polygon, the Jourawski procedure can return four signed envelope values:

```text
tau_x_min
tau_x_max
tau_y_min
tau_y_max
```

The report compares their absolute magnitudes and selects the largest one as:

```text
tau_governing
```

The original sign of the selected value is preserved.

The `direction` column indicates the component from which the governing value was obtained:

- `x` for a value selected from `tau_x_min` or `tau_x_max`;
- `y` for a value selected from `tau_y_min` or `tau_y_max`.

#### 5.1.7 Governing shear in prestressing steel

The `SHEAR EXTREME ROWS - S` table reports the governing Jourawski shear stress among the polygons whose name ends with the material tag `S`.

In this model, these polygons represent the prestressing bars.

Each row contains:

- `z`: analysed elevation;
- `tau_governing`: signed governing shear stress;
- `direction`: governing shear component;
- `polygon_idx`: polygon index in the evaluated section;
- `polygon_name`: CSF polygon name;
- `x`, `y`: coordinates associated with the reported shear-stress value.

More than one row can be reported at the same elevation when several prestressing-bar polygons share the same governing absolute magnitude.

This table makes it possible to identify both the stress level and the specific prestressing bars involved.

#### 5.1.8 Governing shear in the remaining polygons

The `SHEAR EXTREME ROWS - NON-S` table applies the same selection procedure to all polygons whose name does not end with `S`.

In the current pole model, this group contains the concrete-related polygon regions.

The table uses the same columns as the `S` table and retains all polygons sharing the governing value at a given elevation.

The separate `S` and `NON-S` tables allow the shear response of the prestressing steel and the remaining section regions to be read independently.

### 5.2 Detailed output files

The CSV files contain the detailed results used to produce the readable summary. They are intended for spreadsheet inspection, plotting, comparison between degradation scenarios and automated post-processing.

With the SI convention used by this example:

- longitudinal coordinates are expressed in metres;
- forces are expressed in newtons;
- moments are expressed in newton-metres;
- stresses are expressed in pascals.

#### 5.2.1 `prestress_resultant.csv`

File:

[`prestress_resultant.csv`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/output/prestress_resultant.csv)

This file contains one row for each analysed elevation and describes the residual prestressing resultant.

Its columns are:

- `z`: elevation at which the section is evaluated;
- `Pp`: signed residual prestressing force;
- `ex`: eccentricity of the prestressing resultant along `x`, measured relative to the stiffness-weighted centroid of the complete CSF section;
- `ey`: eccentricity of the prestressing resultant along `y`, measured relative to the stiffness-weighted centroid of the complete CSF section.

`Pp` is obtained by scaling the healthy prestressing force according to the effective residual contribution of the prestressing bars.

`ex` and `ey` show how far the residual prestressing resultant is displaced from the centroid used for the complete-section calculation. These eccentricities generate the prestress bending moments included in the internal actions.

This file is therefore the direct link between the longitudinal degradation of the prestressing bars and the axial force and bending effects introduced into the section analysis.

#### 5.2.2 `internal_actions.csv`

File:

[`internal_actions.csv`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/output/internal_actions.csv)

This file contains the signed section actions actually passed to the stress calculations after the removal of negligible numerical residuals.

Its columns are:

- `z`: analysed elevation;
- `N`: axial force;
- `Mx`: total bending moment about the `x` axis;
- `My`: total bending moment about the `y` axis;
- `Tx_jourawski`: shear action passed to the Jourawski calculation for the `x` component;
- `Ty_jourawski`: shear action passed to the Jourawski calculation for the `y` component;
- `Tz`: torque about the longitudinal axis.

`N`, `Mx` and `My` are the actions used by the Navier stress calculation.

`Tx_jourawski` and `Ty_jourawski` are obtained from the longitudinal gradients of the bending moments and are the actions used by the Jourawski shear procedure.

This file is useful for checking how the external load, residual prestress and degradation-induced eccentricity combine along the pole before the stresses are calculated. The generated file is not committed because of its size; it is reproduced automatically when the analysis is executed

#### 5.2.3 `navier_stresses.csv`

File:

[`navier_stresses.csv`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/output/navier_stresses.csv)

This file contains the polygon-by-polygon normal-stress envelopes calculated with the general Navier field.

Each row refers to one polygon at one elevation.

The identification columns are:

- `z`;
- `polygon_idx`;
- `polygon_name`.

The minimum-stress fields are:

- `sigma_min`;
- `vertex_index_min`;
- `x_min`;
- `y_min`.

They identify the minimum signed normal stress in the polygon and the vertex at which it occurs.

The maximum-stress fields are:

- `sigma_max`;
- `vertex_index_max`;
- `x_max`;
- `y_max`.

They identify the maximum signed normal stress in the polygon and the corresponding vertex.

The governing fields are:

- `sigma_extreme`;
- `vertex_index_extreme`;
- `x_extreme`;
- `y_extreme`.

`sigma_extreme` is the value selected between `sigma_min` and `sigma_max` according to the largest absolute magnitude. Its sign is retained.

This file allows the user to determine:

- which polygon governs the normal-stress response;
- whether the governing value is tensile or compressive according to the adopted sign convention;
- the elevation at which it occurs;
- the exact section coordinate and polygon vertex associated with it.

#### 5.2.4 `shear_stresses.csv`

File:

[`shear_stresses.csv`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/output/shear_stresses.csv)

This is the most detailed shear-result file.

Each row refers to one polygon at one analysed elevation and contains both the Jourawski stress envelope and the numerical information associated with the section scan.

The polygon identification fields are:

- `z`;
- `polygon_idx`;
- `polygon_name`.

The material-weight fields are:

- `weight`;
- `weight_ref`;
- `weight_norm`.

They describe the current polygon weight, the reference weight used by the transformed-section procedure and the corresponding normalized value.

The shear-envelope fields are:

- `tau_x_min`;
- `tau_x_max`;
- `tau_y_min`;
- `tau_y_max`.

For each of these values, the file also reports the corresponding `x` and `y` coordinates.

These columns preserve the full signed envelope rather than only the governing absolute value. They therefore allow independent inspection of the two shear components and of their positive and negative extremes.

Additional fields associated with the reported `tau_y_max` condition include:

- the scan coordinate;
- the reference shear stress before material redistribution;
- the weighted section width;
- the partial first moments used by the Jourawski calculation.

The file also contains:

- `tau_x_mean`;
- `tau_y_mean`;
- the number of valid scans crossing the polygon;
- the total scan-grid dimensions;
- flags indicating whether values were obtained for the `x` and `y` scans.

These additional quantities are mainly intended for verification and numerical diagnostics. The primary engineering results remain the signed `tau_x` and `tau_y` envelopes and their coordinates.

#### 5.2.5 `section_polygons.csv`

File:

[`section_polygons.csv`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/output/section_polygons.csv)

This file is the standard CSF export of the polygon vertices at the requested elevations.

Its purpose is to preserve the evaluated section geometry used by the analysis, including:

- the elevation;
- polygon identification;
- polygon names;
- vertex order;
- vertex coordinates.

It provides the geometric reference needed to reconstruct or plot the cross-sections corresponding to the stress results.

The coordinates in `navier_stresses.csv` and `shear_stresses.csv` can therefore be interpreted together with the actual polygon geometry exported at the same elevation.

The currently committed `section_polygons.csv` file contains no tabular rows. The analysis script is configured to generate this export when the calculation is executed.

### 5.3 Recommended reading order

The result files can be read progressively:

1. start from `mechanical_report.txt` to identify the overall actions, stress ranges and governing polygons;
2. use `prestress_resultant.csv` to inspect the residual prestressing force and its eccentricity;
3. use `internal_actions.csv` to follow the section actions along the pole;
4. use `navier_stresses.csv` to inspect the complete polygon-wise normal-stress envelopes;
5. use `shear_stresses.csv` to inspect the complete polygon-wise Jourawski shear-stress envelopes and scan diagnostics;
6. use `section_polygons.csv` as the geometric reference for plotting and locating the reported points.

The text report provides the readable summary, while the CSV files preserve the full calculation detail required for verification and post-processing.

---

## 6. Parametric use

The same model structure can be used for parametric studies.

A study may vary:

- pole geometry;
- concrete-layer dimensions;
- prestressing-bar position;
- elastic properties;
- residual prestress;
- degradation intensity;
- degradation location;
- degradation extent;
- external loads;
- analysis discretization.

The structural response can then be compared across different scenarios while preserving the same modelling architecture.

This is particularly useful for analysing a population of poles whose geometry and degradation state differ from one member to another.

---

## 7. Project workflow

The project follows this sequence:

1. Define the physical geometry of the pole.
2. Divide the cross-section into polygons representing concrete and prestressing steel.
3. Define the reference sections and their longitudinal positions.
4. Assign the initial axial/bending and shear/torsional stiffness.
5. Define the degradation laws for each component.
6. Generate `S(z)` at the elevations required by the analysis.
7. Compute the sectional properties.
8. Build the elastic structural model.
9. Apply prestress and external loads.
10. Evaluate the global response and sectional stresses.
11. Export reports, tables, and plots.

---

## 8. Repository contents

The repository includes:

- YAML files describing the pole and its degradation laws;
- lookup files containing the longitudinal material profiles;
- Python scripts used to generate and analyse the sections;
- structural-analysis scripts;
- sectional verification utilities;
- numerical reports;
- CSV result files;
- plots and comparison outputs.

The input files and numerical results should be read together with this document. The README explains the model concepts, while the repository files provide their direct implementation.

---

## 9. Scope

The project focuses on the elastic structural response of a geometrically and mechanically variable prestressed concrete pole.

Its main objective is to provide a reproducible connection between:

- the physical pole;
- its longitudinally varying section;
- the component-level degradation laws;
- the sectional properties;
- the structural response;
- the resulting stress fields.

The model is designed so that every reported structural quantity can be traced back to the geometry and mechanical condition of the section at the corresponding elevation.
