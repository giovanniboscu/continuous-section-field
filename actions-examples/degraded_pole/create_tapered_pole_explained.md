# Generating the tapered prestressed-concrete pole

The file [`create_tapered_pole.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/create_tapered_pole.py) generates the geometric and material definition of the tapered prestressed-concrete pole used by the example.

Its main purpose is to create the **healthy reference model**:

- the pole length;
- the base and top cross-sections;
- the central void;
- the radial concrete layers;
- the angular sectors;
- the prestressing bars;
- the initial elastic properties of concrete and steel;
- the polygon names required to assign longitudinal laws later.

The complete workflow is:

```text
create_tapered_pole.py
        ↓
healthy geometry and reference material properties
        ↓
selection of longitudinal laws in weight_laws.yaml
        ↓
replacement of weight_laws and shear_weight_laws
in degradated_pole.yaml
        ↓
final degraded Continuous Section Field
```

The files involved are:

- [`create_tapered_pole.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/create_tapered_pole.py);
- [`weight_laws.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/weight_laws.yaml);
- [`degradated_pole.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/degradated_pole.yaml).

---

## 1. Role of `create_tapered_pole.py`

`create_tapered_pole.py` is a model-generation script.

It does not perform the structural analysis and it does not calculate stresses. Its task is to prepare the CSF input model describing the pole.

The script calls the CSF geometry generator:

```python
python -m csf.utils.writegeometry_tappered_pole
```

and supplies all the parameters required to build the two terminal sections:

```text
S0 = section at the base
S1 = section at the top
```

CSF then defines the geometry between `S0` and `S1` as a continuous longitudinal field.

The output of the script is a YAML file containing:

- the base section;
- the top section;
- the corresponding polygons;
- the polygon material weights;
- the polygon naming scheme;
- the longitudinal-law blocks.

---

## 2. Healthy reference material properties

The script assigns the initial elastic properties of the undegraded materials.

```python
E0_CONCRETE = 35.0e9
E0_PCBAR = 6.0 * E0_CONCRETE
```

Therefore, the initial Young's moduli are:

```text
concrete:        E = 35 GPa
prestress steel: E = 210 GPa
```

The script also defines reference shear moduli for the non-isotropic law option:

```python
G0_CONCRETE = 14.0e9
G0_PCBAR = 84.0e9
```

In this example, the polygon `weight` represents the Young's modulus used for axial and bending participation.

At the model-generation stage, the polygons are created with their healthy reference values. A concrete polygon therefore receives the concrete reference modulus, while a prestressing-bar polygon receives the steel reference modulus.

The degradation scenario does not require changing the polygon geometry or rewriting these healthy reference values. It is introduced through longitudinal laws that multiply the reference properties.

---

## 3. Longitudinal extent of the pole

The pole extends from:

```python
z0 = "0.0"
z1 = "15.0"
```

Therefore:

```text
base elevation: z = 0 m
top elevation:  z = 15 m
pole length:    L = 15 m
```

The cross-section is centred at:

```python
cx = "0.0"
cy = "0.0"
```

Both terminal sections are therefore generated around the same longitudinal axis.

---

## 4. Tapered hollow geometry

The pole is hollow and tapered.

The radial boundaries at the base are:

```python
radii0 = "0.1100,0.1325,0.1550,0.1775,0.2000"
```

The radial boundaries at the top are:

```python
radii1 = "0.0500,0.0650,0.0800,0.0950,0.1100"
```

The first radius defines the central void boundary. The remaining radii define four annular concrete levels.

At the base:

```text
inner radius = 0.110 m
outer radius = 0.200 m
inner diameter = 0.220 m
outer diameter = 0.400 m
```

At the top:

```text
inner radius = 0.050 m
outer radius = 0.110 m
inner diameter = 0.100 m
outer diameter = 0.220 m
```

The corresponding radial boundaries in `S0` and `S1` are associated by their order. CSF uses these corresponding polygons to generate the intermediate geometry at any elevation `z`.

The taper is therefore represented directly by the continuous variation of the polygon vertices between the base and the top.

---

## 5. Concrete subdivision

The concrete annulus is divided in two directions:

```text
radial direction:  4 levels
angular direction: 16 sectors
```

The number of angular sectors is defined by:

```python
N = "16"
```

The circular arcs of each sector are approximated using:

```python
arc_steps = "16"
```

The resulting concrete model contains:

```text
4 radial levels × 16 angular sectors = 64 concrete polygons
```

This subdivision is not a finite-element mesh of the pole.

Each polygon is a material region of the CSF cross-section. The subdivision makes it possible to assign a different longitudinal material law to each local region of the pole.

For example, two concrete sectors at the same elevation can retain different elastic properties when they are associated with different lookup laws.

---

## 6. Prestressing bars

The script creates one ring of prestressing bars.

The main parameters are:

```python
n_bars = "16"
bar_diameter = "0.0100"
bar_sides = "16"
bar_host_layer_index = "1"
```

Therefore, the model contains:

```text
16 prestressing bars
bar diameter = 10 mm
polygon approximation = 16 sides per bar
```

The bars are positioned inside the second radial concrete level.

Their guide radii are:

```python
bar_guide_radius0 = "0.1440"
bar_guide_radius1 = "0.0720"
```

This means that the ring of bars tapers together with the pole:

```text
bar-ring radius at the base = 0.144 m
bar-ring radius at the top  = 0.072 m
```

The bar centres are offset by half an angular sector. With 16 sectors, the offset is:

```text
360° / 16 / 2 = 11.25°
```

This places each bar inside its corresponding host sector rather than directly on a sector boundary.

---

## 7. Angular orientation

The angular origin is defined by:

```python
theta0_deg = "90.0"
```

With this convention:

```text
sector 0 starts at 12 o'clock
sector numbering proceeds counter-clockwise
```

The angular orientation is important because the polygon identifiers are later used to select the degraded regions.

A degradation law assigned to a specific sector therefore has a direct physical position around the pole circumference.

---

## 8. Polygon naming convention

Every polygon receives a structured identifier:

```text
<sector>_<level>_<type>
```

The final component identifies the polygon type:

```text
C  = concrete
CH = concrete host region containing a prestressing bar
S  = prestressing steel bar
```

Examples:

```text
0_1_C
3_2_CH
15_4_C
0_2_S
```

The identifier:

```text
3_2_CH
```

means:

```text
sector = 3
radial level = 2
type = concrete host region
```

The identifier:

```text
3_2_S
```

means:

```text
bar position = 3
radial level = 2
type = prestressing steel
```

The naming convention is essential because the longitudinal laws in the final YAML are assigned by polygon name.

The geometry is associated between `S0` and `S1` by polygon order, while the names are used to select the polygons that receive a specific law.

---

## 9. Command-line arguments

The script requires two positional arguments:

```text
model
out_yaml
```

The `model` argument selects the shear-participation definition:

```text
iso
non-iso
```

The `out_yaml` argument defines the generated YAML file.

A typical command is:

```bash
python create_tapered_pole.py iso degradated_pole.yaml
```

The script then:

1. reads the selected shear model;
2. prepares the geometry-generator command;
3. adds all geometric and material parameters;
4. adds the polygon-law arguments;
5. runs the CSF generator;
6. writes the requested YAML file;
7. prints a summary of the generated pole.

---

## 10. Isotropic and non-isotropic shear options

The script can prepare two different shear-law configurations.

### 10.1 Isotropic option

With:

```bash
python create_tapered_pole.py iso ...
```

the shear modulus is derived from the Young's modulus through an isotropic relation.

The concrete polygons use:

```text
iso(0.20)
```

The prestressing-bar polygons use:

```text
iso(0.30)
```

The argument supplied to `iso(...)` is the Poisson ratio.

In this configuration, a change in `weight` also changes the corresponding shear modulus because `G` is derived from the current value of `E`.

### 10.2 Non-isotropic option

With:

```bash
python create_tapered_pole.py non-iso ...
```

the axial/bending and shear/torsion properties can vary independently.

The axial and bending law has the form:

```text
w0 * T_lookup("laws/weight_law_<polygon_id>.dat")
```

The shear and torsion law has the form:

```text
G0 * T_lookup("laws/shear_weight_law_<polygon_id>.dat")
```

This option uses separate lookup files for:

```text
E-related participation
G-related participation
```

It can therefore represent a degradation scenario in which the Young's modulus and shear modulus do not follow the same longitudinal variation.

---

## 11. Reference geometry and degradation laws are separate

The generated pole model contains the healthy reference geometry and material values.

The degradation is represented separately through longitudinal multipliers.

For an axial/bending property, the general form is:

```text
weight(z) = w0 × T_lookup(z)
```

where:

```text
w0 = healthy reference weight
T_lookup(z) = longitudinal residual multiplier
```

For example:

```text
T_lookup(z) = 1.00
```

means that the polygon retains its full reference property at that elevation.

A value such as:

```text
T_lookup(z) = 0.80
```

means that the current property is 80% of the healthy reference value.

The same concept can be used independently for the shear carrier when a separate `shear_weight_law` is defined.

This separation has an important consequence:

```text
polygon vertices → describe geometry
reference weight → describes the healthy material
lookup law       → describes the longitudinal degradation
```

The same healthy pole geometry can therefore be reused for different degradation scenarios by changing only the selected laws or their lookup data.

---

## 12. Purpose of `weight_laws.yaml`

The file [`weight_laws.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/weight_laws.yaml) is an editable law-selection template.

It lists the possible `weight_laws` and `shear_weight_laws` assignments for the generated polygons.

Most candidate assignments are commented. The active lines identify the polygons that participate in the degradation scenario used by the example.

A typical axial/bending assignment is:

```yaml
- '0_2_S,0_2_S: w0*T_lookup("laws/weight_law_0_2_S.dat")'
```

This means:

```text
target polygon: 0_2_S
reference value: w0
longitudinal multiplier:
    laws/weight_law_0_2_S.dat
```

The range:

```text
0_2_S,0_2_S
```

selects that single polygon by using the same initial and final polygon name.

A commented line remains available as a possible assignment but is not active in the selected scenario.

An uncommented line activates the corresponding longitudinal law.

The template therefore allows the degradation scenario to be configured by selecting:

- which concrete sectors are affected;
- which radial levels are affected;
- which prestressing bars are affected;
- which property channel is affected;
- which lookup file describes the longitudinal variation.

---

## 13. Introducing the selected degradation into `degradated_pole.yaml`

The final analysis model is:

[`degradated_pole.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/degradated_pole.yaml)

This file contains:

- the healthy base geometry;
- the healthy top geometry;
- the reference `weight` assigned to every polygon;
- the selected `weight_laws`;
- the selected `shear_weight_laws`.

For the documented example, the law blocks produced with the base model are replaced with the selected blocks prepared in `weight_laws.yaml`.

The relevant YAML sections are:

```yaml
shear_weight_laws:
```

and:

```yaml
weight_laws:
```

Only the active entries are applied.

The remaining commented entries document the other polygon laws that can be activated in a different scenario.

The final YAML therefore combines two different types of information:

```text
fixed reference definition
    geometry of S0 and S1
    healthy material weights

scenario-dependent definition
    active weight_laws
    active shear_weight_laws
    lookup files in the laws directory
```

---

## 14. Meaning of `weight_laws`

The `weight_laws` block controls the longitudinal property used for axial and bending calculations.

In this example, `weight` represents the Young's modulus `E`.

An active law such as:

```yaml
- '15_4_C,15_4_C: w0*T_lookup("laws/weight_law_15_4_C.dat")'
```

means that polygon `15_4_C` retains its healthy geometry while its Young's modulus varies along the pole according to the associated lookup file.

This variation affects quantities such as:

- stiffness-weighted area;
- section centroid;
- second moments of area;
- product of inertia;
- axial stiffness;
- bending stiffness;
- Navier normal stresses.

For a prestressing-bar polygon, the same residual ratio is also used by the example analysis to calculate the residual contribution of that bar to the prestressing resultant.

---

## 15. Meaning of `shear_weight_laws`

The `shear_weight_laws` block controls the material participation used for shear and torsion-related section calculations.

In the isotropic case, the general concrete rule is:

```yaml
- 'iso(0.2)'
```

Specific steel polygons can override this rule with:

```yaml
- '1_2_S,1_2_S: iso(0.30)'
```

The general rule applies to the complete section. A specific polygon rule replaces it for the selected polygon.

In the non-isotropic case, a polygon can instead receive an independent lookup law such as:

```text
G0*T_lookup("laws/shear_weight_law_<polygon_id>.dat")
```

This makes it possible to prescribe the residual shear modulus independently from the residual Young's modulus.

The shear laws affect:

- transformed shear properties;
- Jourawski stress redistribution;
- shear-stress envelopes;
- torsional section properties when the corresponding CSF procedures are used.

---

## 16. Lookup files

The actual longitudinal profiles are stored in the `laws` directory.

Each lookup file is associated with one polygon and one property channel.

Typical file names are:

```text
weight_law_0_2_S.dat
weight_law_15_4_C.dat
shear_weight_law_0_2_S.dat
```

The lookup coordinate represents the normalized longitudinal position:

```text
0 = base of the pole
1 = top of the pole
```

The lookup value is the residual multiplier applied to the reference property.

Because every polygon can reference a different file, the model can describe degradation that varies simultaneously:

- along the pole axis;
- around the circumference;
- across the radial thickness;
- between concrete and prestressing steel;
- between axial/bending and shear/torsion participation.

---

## 17. What remains unchanged when degradation is activated

Activating a material law does not automatically change:

- the pole length;
- the base and top diameters;
- the central void;
- the polygon vertices;
- the number of radial levels;
- the number of angular sectors;
- the bar diameter;
- the bar positions;
- the reference material values stored in `S0` and `S1`.

The degradation law changes the property evaluated at a given longitudinal coordinate `z`.

This allows the reference geometry and the degradation description to remain independent.

A geometric-loss scenario could be represented separately by changing the polygon geometry, but the documented example represents degradation through the material-property fields.

---

## 18. Complete generation workflow

The complete model-generation procedure is:

### Step 1 - Generate the healthy pole

Run:

```bash
python create_tapered_pole.py iso degradated_pole.yaml
```

This creates:

- `S0`;
- `S1`;
- the concrete-sector polygons;
- the prestressing-bar polygons;
- the healthy material weights;
- the initial law blocks.

### Step 2 - Use the prepared degradation laws

Open:

```text
weight_laws.yaml
```

The ready-to-use degradation laws are already provided in this file.

The active lines identify the concrete regions and prestressing bars included in the documented example. The commented lines remain available for alternative degradation scenarios.

Copy the selected `weight_laws` and `shear_weight_laws` blocks into the corresponding sections of:

```text
degradated_pole.yaml
```

### Step 3 - Use the final CSF model

The resulting `degradated_pole.yaml` is the complete model read by the structural-analysis script.

At any elevation `z`, CSF evaluates:

```text
interpolated geometry
+
reference material property
+
active longitudinal law
=
current section used by the analysis
```

---

## 19. Main modelling principle

The model is based on a clear separation between:

```text
geometry generation
material reference values
degradation-law selection
longitudinal degradation data
structural analysis
```

`create_tapered_pole.py` defines the reusable healthy pole.

`weight_laws.yaml` defines which local material regions are affected in a specific scenario.

The lookup files define how strongly those regions are affected along the pole.

`degradated_pole.yaml` combines these elements into the final Continuous Section Field used by the analysis.

This structure allows a new degradation scenario to be created without rebuilding the complete geometry of the pole.
