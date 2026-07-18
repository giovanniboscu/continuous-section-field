# From Inspection Data to Structural Assessment: Continuous-Field Analysis of a Tapered Prestressed Pole with Localized Degradation

<p align="center">
  <img
    src="https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/actions-examples/degraded_pole/img/volume_3D.jpg"
    alt="Three-dimensional model of the tapered prestressed concrete pole"
    width="400">
</p>

<p align="center">
  <em>Three-dimensional representation of the tapered prestressed concrete pole. The Z-axis is scaled independently for visualization purposes; the displayed aspect ratio is not the true geometric aspect ratio.</em>
</p>

This project addresses the structural analysis of a prestressed concrete pole subjected to spatially variable degradation. The pole is modelled as a cantilever member, fixed at the base and free at the top, so that its response can be evaluated under axial force, bending moments, shear forces, and torsion.

The geometry varies continuously along the longitudinal axis. It is defined from a reference section at the base and a reference section at the top. Intermediate sections are generated between these two geometries, allowing the external profile, the internal hollow core, the concrete layers, and the prestressing bars to vary consistently with height.

The same continuous representation is used for the material properties. Concrete regions and prestressing bars are treated as distinct components, each of which may have its own variation of stiffness and residual mechanical capacity along the pole.

Degradation can therefore be localized in two directions:

- within the cross-section, by assigning it to selected concrete regions or individual bars;
- along the pole, by prescribing the elevation range and intensity of the degradation.

At every elevation, the model provides the corresponding cross-section together with its effective geometry and material properties. These data are then used to evaluate the structural response and the local stress state.

Normal stresses due to axial force and bending moments are evaluated with the general Navier formulation. The calculation uses the actual centroid, effective area, second moments of area, and product of inertia of the section at the considered elevation.

Shear stresses are evaluated with the Jourawski formulation using the geometry and the material distribution available at the same elevation.

The result is a continuous structural description of the pole from base to top, including localized degradation of concrete and prestressing steel in both the cross-sectional and longitudinal directions.

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

The complete input model is defined in [`degradated_pole.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/degradated_pole.yaml).

The file is introduced after the physical model so that each input key can be related directly to a geometric or mechanical concept.

It describes:

1. the reference cross-sections;
2. the polygons that form each section;
3. the stiffness assigned to each polygon;
4. the rules that define how geometry and stiffness vary along the pole;
5. the analysis settings used by the example scripts.

### 2.1 Reference sections

The geometry is defined at two elevations:

- `S0` at `z = 0.0`, corresponding to the base;
- `S1` at `z = 15.0`, corresponding to the top.

Each reference section contains the same set of named polygons. The coordinates stored in `S0` and `S1` define the geometry of those polygons at the two ends of the pole.

The same polygon name in `S0` and `S1` identifies the same physical region. For example, `12_3_C` in `S0` and `12_3_C` in `S1` represent the same concrete region at the base and at the top.

The model matches polygons by name and interpolates their vertex coordinates to reconstruct the section geometry at every intermediate elevation `z`.

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

Every polygon contains:

- `vertices`, which define its geometry at the reference section;
- `weight`, which defines the stiffness used for axial force and bending.

In this example, `weight` is the elastic modulus **E**:

- concrete polygons use **35 GPa**;
- prestressing-steel polygons use **210 GPa**.

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

The root key is named `CSF`, but the essential idea is straightforward: the file contains section geometry, polygon stiffness, and the rules used to evaluate them at any elevation.

### 2.4 Basic variation between `S0` and `S1`

In this example, each polygon has the same `weight` in `S0` and `S1`. Under the basic interpolation rule, its elastic modulus therefore remains constant along the pole.

If different values were assigned at `S0` and `S1`, the polygon weight-and therefore the elastic modulus-would be linearly interpolated at each elevation `z`.

This basic interpolation applies when no more specific material law is assigned.

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

This example stores the actual elastic moduli directly as polygon weights.

The same formulation can also use normalized weights. For a component `i`, normalized initial values may be written as:

$$
w_{0,i} = \frac{E_i}{E_{\mathrm{ref}}}
$$

$$
w_{s0,i} = \frac{G_i}{G_{\mathrm{ref}}}
$$

where `E_ref` and `G_ref` are reference moduli.

Keeping `weight` and `shear_weight` separate allows axial and bending behaviour to vary independently from shear and torsional behaviour.

For longitudinal degradation, the two weights may be written conceptually as:

$$
w_i(z) = w_{0,i} L_i(z)
$$

$$
w_{s,i}(z) = w_{s0,i} L_{s,i}(z)
$$

where:

- `w0,i` is the initial axial and bending weight;
- `ws0,i` is the initial shear and torsional weight;
- `Li(z)` is the axial and bending lookup value;
- `Ls,i(z)` is the shear and torsional lookup value.

The lookup data prescribe the known material condition at selected elevations. Values at intermediate elevations are evaluated continuously.

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

The continuous field is the structural description of the member. Individual sections, sectional properties, and solver inputs are derived from it only at the elevations required by the analysis.

---

## 4. Structural analysis

The generated sections are used in an elastic structural model of the pole.

At each required integration point, the analysis obtains the section directly from the continuous model and evaluates its current geometry and material properties.

The structural model may include:

- residual prestress;
- axial force;
- lateral loading;
- bending;
- shear;
- torsion;
- degradation varying along the member.

The analysis therefore uses the section and material state associated with the actual elevation of each calculation point.

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

Normal stresses are evaluated from the general Navier stress field using:

$$
N,\quad M_x,\quad M_y
$$

Shear stresses are evaluated with the Jourawski-based section procedure using:

$$
T_x,\quad T_y
$$

The results retain the signed stress values and the coordinates of the governing points.

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
