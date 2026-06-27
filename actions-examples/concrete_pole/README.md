# Tapered prestressed concrete pole CSF input case

## Engineering context from the cited sources

Prestressed concrete poles are commonly used for lighting, electric distribution and transmission lines, antenna masts, and related applications. Circular hollow-cored sections are especially relevant in this class of members because they combine reduced weight, torsional capacity, and internal space for wires or accessories. The PCI Journal reference considered here addresses tapered prestressed hollow-cored poles, whose cross-sectional properties vary along the pole height.

In the design setting of the reference study, the pole is treated as a cantilever member fixed at its base, and the structural demand is evaluated through axial force and bending moment at different section locations along the height. In the present CSF example, however, no external actions are applied. The model is used at the pre-solver level to generate the tapered sectional field and to evaluate the corresponding sectional properties along the member coordinate.

This CSF case follows the same geometric setting at input level. The member is defined as a tapered hollow circular pole using two boundary stations, annular concrete regions, and discrete prestressing-steel components. The longitudinal variation is represented directly in the CSF input through geometric interpolation and component-wise participation laws.


The purpose of this CSF model is to represent the tapered prestressed hollow pole as a continuous sectional field before any structural solver is introduced. Instead of defining a separate cross-section at each analysis station, the pole is described once through its boundary geometries, annular concrete regions, prestressing-steel components, and longitudinal participation laws.

The external law files define the axial variation of the normalized stiffness participation assigned to the concrete and steel components. For axial and bending response, this variation is expressed through the normalized elastic modulus $E/E_0$. For shear and torsional response, the corresponding normalized shear modulus $G/G_0$ is used consistently with the adopted material assumption; in the isotropic case with constant Poisson ratio, $G/G_0$ follows from $E/E_0$ rather than being an independent degradation law.

In the CSF model, these longitudinal variations represent prescribed degradation fields that can be modified by the user without changing the geometric definition of the pole. The generated field can then be evaluated at any height to inspect the local section, compute the corresponding sectional properties, or sample station-wise sections for downstream structural analysis.


---

<img width="657" height="614" alt="image" src="https://github.com/user-attachments/assets/e39c2fac-27ce-4db8-92ca-0c1b70f99b95" />

This directory contains a Python-based input-generation case for a tapered circular hollow prestressed concrete pole.

The case is intended for users who can run Python scripts but do not need to write the CSF YAML input syntax manually. The Python launcher collects the geometric parameters, prestressing-steel layout, and external participation-law tables, then writes a complete CSF input file.

The generated YAML file is the starting point for the following CSF operations:

- inspecting the cross-section at selected longitudinal stations;
- plotting derived sectional properties;
- sampling the member field for downstream structural analysis.

## Directory contents

```text
create_yaml_tapered_pole_lookup.py   # main launcher
writegeometry_tapered_rebars.py      # geometry/YAML generator
laws/                                # lookup tables for participation laws
run_lookup_shear.sh                  # ready-to-run non-isotropic variant
run_iso_shear.sh                     # ready-to-run isotropic shear/torsion variant
docs/README.md                       # this guide
```


## 1. Generate the CSF YAML input and run the analysis

The CSF geometry can be generated with the script `create_yaml_tapered_pole_lookup.py`, which requires two command-line arguments:

```bash
usage: create_yaml_tapered_pole_lookup.py [-h] {iso,non-iso} out_yaml
```
The first argument selects how the axial/bending and shear/torsion stiffness-reduction factors are assigned along the member. In the `iso` case, the shear/torsion reduction is derived from the axial/bending reduction through the specified Poisson-ratio relation. In the `non-iso` case, the axial/bending and shear/torsion reductions are prescribed independently through separate lookup files.

The second argument is the name of the YAML file to be written.

Run the generator from this directory.

For the isotropic case:

```bash
python3 create_yaml_tapered_pole_lookup.py iso tapered_pc_pole_iso_lookup.yaml
```

For the non-isotropic case:

```bash
python3 create_yaml_tapered_pole_lookup.py non-iso tapered_pc_pole_non-iso_lookup.yaml
```

Expected terminal output for the isotropic case:

```text
python3 create_yaml_tapered_pole_lookup.py iso tapered_pc_pole_iso_lookup.yaml

File generated successfully: tapered_pc_pole_iso_lookup.yaml
Layers: 3
Bars: 16
S0 outer radius: 0.300000 m
S1 outer radius: 0.220000 m

Generated:
  - tapered_pc_pole_iso_lookup.yaml

Geometry summary:
  L                         = 20.0 m
  base outer diameter       = 0.600 m
  base inner diameter       = 0.400 m
  top outer diameter        = 0.440 m
  top inner diameter        = 0.280 m
  prestressing components   = 16
  component diameter        = 0.0127 m
  axial/bending laws        = T_lookup(...), files in ./laws/
  shear/torsion laws        = iso(0.20/0.30)
  participation scenario    = isotropic
```

Expected terminal output for the non-isotropic case:

```text
python3 create_yaml_tapered_pole_lookup.py non-iso tapered_pc_pole_non-iso_lookup.yaml

File generated successfully: tapered_pc_pole_non-iso_lookup.yaml
Layers: 3
Bars: 16
S0 outer radius: 0.300000 m
S1 outer radius: 0.220000 m

Generated:
  - tapered_pc_pole_non-iso_lookup.yaml

Geometry summary:
  L                         = 20.0 m
  base outer diameter       = 0.600 m
  base inner diameter       = 0.400 m
  top outer diameter        = 0.440 m
  top inner diameter        = 0.280 m
  prestressing components   = 16
  component diameter        = 0.0127 m
  axial/bending laws        = T_lookup(...), files in ./laws/
  shear/torsion laws        = T_lookup(...), files in ./laws/
  participation scenario    = non-isotropic
```

This step generates the selected CSF YAML input file:

```text
tapered_pc_pole_iso_lookup.yaml
```

or:

```text
tapered_pc_pole_non-iso_lookup.yaml
```

The generated YAML file contains the tapered pole geometry, the annular concrete regions, the prestressing-steel components, and the participation-law assignments read from the lookup tables in `./laws/`.

The summary confirms that the model is a 20 m tapered hollow circular pole with 16 prestressing components. The base outer diameter is 0.600 m and the top outer diameter is 0.440 m.

The line:

```text
participation scenario    = non-isotropic
```

means that the axial/bending participation and the shear/torsion participation are assigned through separate lookup laws.

After generating the CSF YAML input, run the action file.

For the isotropic case:

```bash
csf-actions tapered_pc_pole_iso_lookup.yaml action_tapered_pole_lookup.yaml
```

For the non-isotropic case:

```bash
csf-actions tapered_pc_pole_non-iso_lookup.yaml action_tapered_pole_lookup.yaml
```

This command evaluates the generated CSF model according to the operations defined in:

```text
action_tapered_pole_lookup.yaml
```

The requested results are written to the `out/` directory.

<img width="982" height="761" alt="image" src="https://github.com/user-attachments/assets/49704fae-f4a6-42bc-995b-208fcb45a989" />

<img width="981" height="940" alt="image" src="https://github.com/user-attachments/assets/f1106e0a-51c2-43c1-b9af-130db0ddcb99" />

### Expected result

After a successful run, the generator prints a short summary and writes the selected YAML file. The file contains:

- the two boundary stations of the tapered member;
- the annular region polygons at each station;
- the prestressing-steel component polygons at each station;
- the axial/bending law assignments;
- the shear/torsion law assignments.

## 2. What the generated YAML file contains

The generated file:

```text
tapered_pole_lookup.yaml
```

and

```text
tapered_pc_pole_iso_lookup.yaml
```


To define the tapered pole geometry, the file describes the cross-section only at the two end stations: S0 (bottom) and S1 (top). At each station, the cross-section is represented by a set of polygons. Each named region is defined by a polygon at S0 and a corresponding polygon at S1. This polygon pair establishes the region's extent at both boundaries and determines how the region transitions along the member axis..

In this case, the hollow concrete pole is represented as a layered circular wall. The section is subdivided into annular regions, giving an onion-like representation of the concrete wall rather than a single undifferentiated annulus. This makes each concrete layer a named controllable region in the CSF model.

The prestressing-steel components are represented by polygonal inserts. All steel bars are placed inside the region named:

```text
pcbar_host_layer
```

Each region carries a base `weight`. In this example:

- concrete regions use `weight: 1.0`, corresponding to the normalized elastic modulus $E/E_0$;
- prestressing-steel components use `weight: 6.0`, corresponding to a higher normalized modulus assigned to the steel polygons.

A shortened excerpt of the generated YAML has the following form:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        core_inner@cell:
          weight: 1.0
          vertices:
          - [0.225, 0.0]
          - [0.22493223420664596, 0.005521776417655265]
...
...
...
    S1:
      z: 20.0
      polygons:
        core_inner@cell:
          weight: 1.0
          vertices:
          - [0.16, 0.0]
          - [0.1599518109913927, 0.003926596563665966]
          - [0.1598072729928276, 0.007850827892386883]
...
...
...
        pcbar_00:
          weight: 6.0
          vertices:
          - [0.25, 0.0]
          - [0.24951663503144667, 0.00243003979551832]
...
...
...
        pcbar_01:
          weight: 6.0
          vertices:
          - [0.23096988312782168, 0.09567085809127246]
...
...
...
```

The sequence of polygons in `S0` and `S1` defines the boundary geometry of the pole field. The base weights attached to the polygons define the base material participation assigned to the concrete and steel regions before any longitudinal law is applied.

These base weights can be overridden, region by region, by axial participation laws. In this case, the override is specified at the end of the YAML file through `weight_laws` and `shear_weight_laws`.

A representative portion of the generated law assignments `tapered_pc_pole_non-iso_lookup.yaml` is shown below:

```yaml
  shear_weight_laws:
  - 'core_inner,core_inner: T_lookup("laws/shear_weight_law_core_inner.dat")'
  - 'pcbar_host_layer,pcbar_host_layer: T_lookup("laws/shear_weight_law_pcbar_host_layer.dat")'
  - 'cover_inner,cover_inner: T_lookup("laws/shear_weight_law_cover_inner.dat")'
  - 'cover_outer,cover_outer: T_lookup("laws/shear_weight_law_cover_outer.dat")'
  - 'pcbar_00,pcbar_00: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_01,pcbar_01: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_02,pcbar_02: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_03,pcbar_03: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_04,pcbar_04: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_05,pcbar_05: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_06,pcbar_06: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_07,pcbar_07: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_08,pcbar_08: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_09,pcbar_09: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_10,pcbar_10: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_11,pcbar_11: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_12,pcbar_12: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_13,pcbar_13: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_14,pcbar_14: T_lookup("laws/shear_weight_law_pcbar.dat")'
  - 'pcbar_15,pcbar_15: T_lookup("laws/shear_weight_law_pcbar.dat")'
  weight_laws:
  - 'core_inner,core_inner: T_lookup("laws/weight_law_core_inner.dat")'
  - 'pcbar_host_layer,pcbar_host_layer: T_lookup("laws/weight_law_pcbar_host_layer.dat")'
  - 'cover_inner,cover_inner: T_lookup("laws/weight_law_cover_inner.dat")'
  - 'cover_outer,cover_outer: T_lookup("laws/weight_law_cover_outer.dat")'
  - 'pcbar_00,pcbar_00: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_01,pcbar_01: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_02,pcbar_02: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_03,pcbar_03: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_04,pcbar_04: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_05,pcbar_05: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_06,pcbar_06: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_07,pcbar_07: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_08,pcbar_08: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_09,pcbar_09: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_10,pcbar_10: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_11,pcbar_11: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_12,pcbar_12: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_13,pcbar_13: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_14,pcbar_14: T_lookup("laws/weight_law_pcbar.dat")'
  - 'pcbar_15,pcbar_15: T_lookup("laws/weight_law_pcbar.dat")'
```

Each assignment has two parts. For example:

```yaml
  - 'core_inner,core_inner: T_lookup("laws/weight_law_core_inner.dat")'
```

The first part:

```text
core_inner,core_inner
```

identifies the polygon pair to which the law is applied. The second part:

```text
T_lookup("laws/weight_law_core_inner.dat")
```

identifies the lookup file that provides the longitudinal values of the participation factor for that region.

A lookup file is a two-column table:

```text
# xi value
0.0000 1.0000
0.1000 1.0000
0.2500 0.9998
0.4000 0.9990
0.5500 0.9960
0.7000 0.9880
0.8000 0.9720
0.9000 0.9480
0.9500 0.9320
1.0000 0.9200
```

The first column is the normalized longitudinal coordinate `xi`:

```text
xi = 0.0  -> S0
xi = 1.0  -> S1
```

The second column is the participation value assigned at that coordinate. Intermediate values are obtained by linear interpolation.

This mechanism is repeated independently for every named concrete region and for every prestressing-steel component. As a result, the same geometric pole can carry a region-by-region degradation field along the member axis.

The YAML separates two different participation fields:

```text
weight_laws
    Axial/bending participation field. For each polygon pair, this defines
    the longitudinal factor w_i(z) used to scale the region contribution to
    axial and bending-related sectional properties.

shear_weight_laws
    Shear/torsion participation field. For each polygon pair, this defines
    the longitudinal factor shear_w_i(z) used to scale the region contribution
    to shear/torsion-related sectional properties.
```

In the lookup-driven variant, `weight_laws` and `shear_weight_laws` are assigned independently. The axial/bending participation field and the shear/torsion participation field therefore do not need to follow a single isotropic elastic relation. This is the non-isotropic variant reported by the launcher.

An isotropic shear/torsion variant can also be generated. In that case, the shear/torsion field is assigned through `iso(...)` laws instead of external shear/torsion lookup tables. The value passed to `iso(...)` is the Poisson ratio: for example, `iso(0.20)` assigns the shear/torsion participation consistently with an isotropic material having $\nu = 0.20$.

A representative portion of the generated law assignments `tapered_pc_pole_iso_lookup.yaml` is shown below:


```yaml
 shear_weight_laws:
  - 'core_inner,core_inner: iso(0.20)'
  - 'pcbar_host_layer,pcbar_host_layer: iso(0.20)'
  - 'cover_inner,cover_inner: iso(0.20)'
  - 'cover_outer,cover_outer: iso(0.20)'
  - 'pcbar_00,pcbar_00: iso(0.30)'
  - 'pcbar_01,pcbar_01: iso(0.30)'
  - 'pcbar_02,pcbar_02: iso(0.30)'
  - 'pcbar_03,pcbar_03: iso(0.30)'
  - 'pcbar_04,pcbar_04: iso(0.30)'
  - 'pcbar_05,pcbar_05: iso(0.30)'
  - 'pcbar_06,pcbar_06: iso(0.30)'
  - 'pcbar_07,pcbar_07: iso(0.30)'
  - 'pcbar_08,pcbar_08: iso(0.30)'
  - 'pcbar_09,pcbar_09: iso(0.30)'
  - 'pcbar_10,pcbar_10: iso(0.30)'
  - 'pcbar_11,pcbar_11: iso(0.30)'
  - 'pcbar_12,pcbar_12: iso(0.30)'
  - 'pcbar_13,pcbar_13: iso(0.30)'
  - 'pcbar_14,pcbar_14: iso(0.30)'
  - 'pcbar_15,pcbar_15: iso(0.30)'
```

After the geometry and law assignments are defined, the CSF model can be evaluated at any longitudinal coordinate `z`. The evaluation returns the sectional quantities associated with the prescribed geometry, the axial/bending participation field, and the shear/torsion participation field.

The same generated geometry can therefore be used to represent different degradation configurations by changing only the lookup tables or the law assignments. This is useful for comparing alternative degradation patterns, including successive states of the same pole over time.

## 3. What the case is intended to test

The case tests the construction of a member field in which geometry and participation data are both functions of the longitudinal coordinate.

The member is defined by:

- two end stations, `z0 = 0.0` and `z1 = 20.0`;
- a tapered circular hollow geometry;
- four named annular concrete regions;
- a ring of prestressing steel components represented by polygonal inserts;
- external lookup tables for axial/bending participation;
- external or isotropic laws for shear/torsion participation.

The relevant point of the test is that the geometry, named regions, prestressing steel components, and participation laws remain explicit input data. Sectional quantities such as area, centroid, bending inertia, and torsion-related quantities are derived from this field after the model is generated.

The lookup files keep the longitudinal degradation field outside the geometric generator. Changing a `.dat` file changes the participation field without changing the geometry-generation script.

## 4. Model geometry

The model uses two tapered end stations.

At `z0 = 0.0`:

```text
inner radius = 0.200 m
outer radius = 0.300 m
```

At `z1 = 20.0`:

```text
inner radius = 0.140 m
outer radius = 0.220 m
```

The wall is split into four annular regions:

```text
core_inner
pcbar_host_layer
cover_inner
cover_outer
```

The central hollow core is represented by the first inner radius. It is not a material region in the CSF input.

The prestressing steel components are placed on a guide radius inside `pcbar_host_layer`. The command-line option names use the code labels `bar` and `pcbar` for these polygonal steel components.

## 5. Participation laws

The case separates two participation fields:

```text
weight_law          -> axial/bending participation
shear_weight_law    -> shear/torsion participation
```

The lookup-driven case reads these fields from `.dat` files in `laws/`.

### Axial/bending lookup files

```text
laws/weight_law_core_inner.dat
laws/weight_law_pcbar_host_layer.dat
laws/weight_law_cover_inner.dat
laws/weight_law_cover_outer.dat
laws/weight_law_pcbar.dat
```

### Shear/torsion lookup files

```text
laws/shear_weight_law_core_inner.dat
laws/shear_weight_law_pcbar_host_layer.dat
laws/shear_weight_law_cover_inner.dat
laws/shear_weight_law_cover_outer.dat
laws/shear_weight_law_pcbar.dat
```

Each lookup file is a two-column table:

```text
xi  value
```

where `xi` is the normalized member coordinate:

```text
xi = 0.0  -> z0
xi = 1.0  -> z1
```

The current tables describe a monotone nonlinear degradation field: the values remain close to one near `xi = 0.0` and decrease more rapidly toward `xi = 1.0`.

## 6. Basic workflow

Run the launcher from the case directory:

```bash
python3 create_yaml_tapered_pole_lookup.py
```

This writes:

```text
tapered_pole_lookup.yaml
```

The launcher contains the case parameters near the top of the file. A Python user can modify radii, number of steel components, guide radii, weights, output name, and law references there, then rerun the script.

## 7. Shell-script workflows

The two shell scripts provide ready-to-run variants.

### Lookup-driven shear/torsion laws

```bash
bash run_lookup_shear.sh
```

This writes:

```text
tapered_pc_pole_lookup.yaml
```

In this variant, both `weight_law` and `shear_weight_law` are read from lookup tables.

### Isotropic shear/torsion laws

```bash
bash run_iso_shear.sh
```

This writes:

```text
tapered_pc_pole_iso_lookup.yaml
```

In this variant, axial/bending participation remains lookup-driven, while shear/torsion is assigned through explicit `iso(...)` laws.

## 8. Direct generator use

The launcher and shell scripts call the lower-level generator:

```text
writegeometry_tapered_rebars.py
```

Use the generator directly when all parameters must be visible in one command.

For Bash, every argument containing `T_lookup(...)` must be quoted as a complete argument. The correct form is:

```bash
--layer-law '0:T_lookup("laws/weight_law_core_inner.dat")'
```

The unquoted form is rejected by Bash before Python receives the argument.

### Direct lookup-driven command

```bash
python3 writegeometry_tapered_rebars.py \
  --z0 0.0 --z1 20.0 \
  --cx 0.0 --cy 0.0 \
  --radii0 0.200,0.225,0.250,0.275,0.300 \
  --radii1 0.140,0.160,0.180,0.200,0.220 \
  --layer-names core_inner,pcbar_host_layer,cover_inner,cover_outer \
  --layer-weights 1,1,1,1 \
  --N 256 \
  --n-bars 16 \
  --bar-guide-radius0 0.24365 \
  --bar-guide-radius1 0.17365 \
  --bar-host-layer-index 1 \
  --bar-diameter 0.0127 \
  --bar-sides 16 \
  --bar-weight 6.0 \
  --bar-prefix pcbar \
  --theta0-deg 0.0 \
  --layer-law '0:T_lookup("laws/weight_law_core_inner.dat")' \
  --layer-law '1:T_lookup("laws/weight_law_pcbar_host_layer.dat")' \
  --layer-law '2:T_lookup("laws/weight_law_cover_inner.dat")' \
  --layer-law '3:T_lookup("laws/weight_law_cover_outer.dat")' \
  --all-bars-law 'T_lookup("laws/weight_law_pcbar.dat")' \
  --layer-shear-law '0:T_lookup("laws/shear_weight_law_core_inner.dat")' \
  --layer-shear-law '1:T_lookup("laws/shear_weight_law_pcbar_host_layer.dat")' \
  --layer-shear-law '2:T_lookup("laws/shear_weight_law_cover_inner.dat")' \
  --layer-shear-law '3:T_lookup("laws/shear_weight_law_cover_outer.dat")' \
  --all-bars-shear-law 'T_lookup("laws/shear_weight_law_pcbar.dat")' \
  --out tapered_pc_pole_lookup.yaml
```

### Direct command with isotropic shear/torsion laws

```bash
python3 writegeometry_tapered_rebars.py \
  --z0 0.0 --z1 20.0 \
  --cx 0.0 --cy 0.0 \
  --radii0 0.200,0.225,0.250,0.275,0.300 \
  --radii1 0.140,0.160,0.180,0.200,0.220 \
  --layer-names core_inner,pcbar_host_layer,cover_inner,cover_outer \
  --layer-weights 1,1,1,1 \
  --N 256 \
  --n-bars 16 \
  --bar-guide-radius0 0.24365 \
  --bar-guide-radius1 0.17365 \
  --bar-host-layer-index 1 \
  --bar-diameter 0.0127 \
  --bar-sides 16 \
  --bar-weight 6.0 \
  --bar-prefix pcbar \
  --theta0-deg 0.0 \
  --layer-law '0:T_lookup("laws/weight_law_core_inner.dat")' \
  --layer-law '1:T_lookup("laws/weight_law_pcbar_host_layer.dat")' \
  --layer-law '2:T_lookup("laws/weight_law_cover_inner.dat")' \
  --layer-law '3:T_lookup("laws/weight_law_cover_outer.dat")' \
  --all-bars-law 'T_lookup("laws/weight_law_pcbar.dat")' \
  --layer-shear-law '0:iso(0.20)' \
  --layer-shear-law '1:iso(0.20)' \
  --layer-shear-law '2:iso(0.20)' \
  --layer-shear-law '3:iso(0.20)' \
  --all-bars-shear-law 'iso(0.30)' \
  --out tapered_pc_pole_iso_lookup.yaml
```

## 9. Meaning of the main command-line options

```text
--z0, --z1
    Member end coordinates.

--radii0, --radii1
    Radial boundaries of the annular regions at z0 and z1.
    The number of region names must be len(radii)-1.

--layer-names
    Names assigned to the annular regions.

--layer-weights
    Base weights assigned to the annular regions before lookup laws are applied.

--N
    Number of vertices used to approximate each circular boundary.

--n-bars
    Number of prestressing steel components on the guide ring.

--bar-guide-radius0, --bar-guide-radius1
    Guide-ring radius for the steel components at z0 and z1.

--bar-host-layer-index
    Zero-based index of the annular region that hosts the steel components.
    In this case, index 1 corresponds to pcbar_host_layer.

--bar-diameter
    Diameter of each steel component polygon.

--bar-sides
    Number of polygon sides used to approximate each steel component.

--bar-weight
    Base relative weight assigned to the steel components before lookup laws are applied.

--layer-law
    Axial/bending participation law for one annular region.

--all-bars-law
    Axial/bending participation law for all steel components.

--layer-shear-law
    Shear/torsion participation law for one annular region.

--all-bars-shear-law
    Shear/torsion participation law for all steel components.

--out
    Output YAML file.
```

## 10. Editing the case

For routine changes, edit `create_yaml_tapered_pole_lookup.py` and run it again.

For law-only changes, edit the `.dat` files in `laws/` and regenerate the YAML. Keep the first column normalized between `0.0` and `1.0`.

For a different radial subdivision, update `radii0`, `radii1`, `layer_names`, `layer_weights`, and the layer-indexed law assignments consistently.

For a different steel-component ring, update `n_bars`, `bar_guide_radius0`, `bar_guide_radius1`, `bar_diameter`, `bar_sides`, and `bar_host_layer_index`.

# Reference basis

## Primary reference

J. Bolander Jr., K. Sowlat, and A. E. Naaman, **“Design Considerations for Tapered Prestressed Concrete Poles,” PCI Journal, 1988**.  
https://www.pci.org/PCI_Docs/Publications/PCI%20Journal/1988/January/Design%20Considerations%20for%20Tapered%20Prestressed%20Concrete%20Poles.pdf

Reason for use: this paper directly addresses tapered prestressed circular hollow-cored concrete poles and the longitudinal change of section properties in tapered poles.

## Supporting reference

ASCE Task Force / PCI Committee on Concrete Poles, **“Guide for the Design of Prestressed Concrete Poles,” PCI Journal, 1997**.  
https://www.pci.org/PCI_Docs/Publications/PCI%20Journal/1997/November/Guide%20for%20the%20Design%20of%20Prestressed%20Concrete%20Poles.pdf

Reason for use: this guide documents prestressed concrete pole families, spun-cast poles, hollow cores, prestressing steel, spiral reinforcement, and typical reinforcement arrangements.
