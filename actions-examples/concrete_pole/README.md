# DRAFT
# Tapered prestressed concrete pole CSF input case

This directory contains a Python-based input-generation case for a tapered circular hollow prestressed concrete pole.

The case is intended for users who can run Python scripts but do not need to know the internal CSF input syntax.

The workflow generates a CSF YAML input file from explicit geometric parameters and external participation-law tables. These tables define how the contribution of each concrete region and prestressing-steel component varies along the pole axis.

The generated YAML file is the starting point for the following CSF operations:

- inspecting the cross-section at selected longitudinal stations;
- plotting derived sectional properties;
- sampling the member field for downstream structural analysis.

## Directory contents

This case uses the following files:

```text
create_yaml_tapered_pole_lookup.py   # main launcher
writegeometry_tapered_rebars.py      # geometry/YAML generator
laws/                                # lookup tables for participation laws
run_lookup_shear.sh                  # ready-to-run non-isotropic variant
run_iso_shear.sh                     # ready-to-run isotropic shear/torsion variant
```

## 1. Generate the CSF YAML input

Run the launcher from this directory:

```bash
python3 create_yaml_tapered_pole_lookup.py
```

Expected terminal output:

```text
File generated successfully: tapered_pole_lookup.yaml
Layers: 3
Bars: 16
S0 outer radius: 0.300000 m
S1 outer radius: 0.220000 m

Generated:
  - tapered_pole_lookup.yaml

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

This step generates the file:

```text
tapered_pole_lookup.yaml
```

This file is the CSF input model produced by the generator. It contains the tapered pole geometry, the prestressing components, and the participation-law assignments read from the lookup tables in `./laws/`.

The summary confirms that the generated model is a 20 m tapered hollow circular pole with 16 prestressing components. The base outer diameter is 0.600 m and the top outer diameter is 0.440 m.

The line:

```text
participation scenario    = non-isotropic
```

means that axial/bending participation and shear/torsion participation are assigned through separate lookup laws.

## 2. What the generated YAML file contains

The file:

```text
tapered_pole_lookup.yaml
```

is the generated CSF input model.

It describes the tapered pole as a longitudinal member field built from:

* two end sections;
* named concrete regions;
* named prestressing components;
* polygon vertices for each region and component;
* base weights assigned by the generator;
* lookup-law assignments that define how the effective contribution varies along the pole.

The two end sections are identified as:

```text
S0  -> base section, at z = 0.0 m
S1  -> top section, at z = 20.0 m
```

Each end section contains a polygonal description of the cross-section at that longitudinal position. The circular hollow concrete wall is represented by annular polygonal regions. The prestressing components are represented by small polygonal regions placed around the wall.

A simplified view of the YAML structure is:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        ...
    S1:
      z: 20.0
      polygons:
        ...
  weight_laws:
    ...
  shear_weight_laws:
    ...
```

The `sections` block defines the end-section geometry. The `weight_laws` and `shear_weight_laws` blocks assign longitudinal contribution laws to the named regions and prestressing components.

The generator creates the prestressing components as explicit named parts of the section model:

```text
pcbar_00
pcbar_01
...
pcbar_15
```

These names appear in the YAML because each prestressing component is connected from the base section to the top section and can receive its own participation-law assignment.

The generated YAML is the input read by later CSF operations for section inspection, derived sectional-property plots, and member-field sampling.









---
---

## What the case is intended to test

The case tests the construction of a member field in which geometry and participation data are both functions of the longitudinal coordinate.

The member is defined by:

- two end stations, `z0 = 0.0` and `z1 = 20.0`;
- a tapered circular hollow geometry;
- four named annular concrete regions;
- a ring of prestressing steel components represented by polygonal inserts;
- external lookup tables for axial/bending participation;
- external or isotropic laws for shear/torsion participation.

The useful point of the test is that the geometry, named regions, prestressing steel components, and participation laws remain explicit input data. Sectional quantities such as area, centroid, bending inertia, and torsion-related quantities are derived from this field after the model is generated.

The lookup files make the longitudinal degradation field external to the YAML. Changing a `.dat` file changes the participation field without changing the geometric generator.

## Directory contents

```text
create_yaml_tapered_pole_lookup.py   # Convenience launcher for the lookup-driven case
writegeometry_tapered_rebars.py      # Low-level YAML geometry generator
run_lookup_shear.sh                  # Shell script using lookup laws for shear/torsion
run_iso_shear.sh                     # Shell script using iso(...) laws for shear/torsion
laws/                                # External participation-law tables
docs/README.md                       # This guide
```

Generated YAML files are written in the case directory. Depending on the command used, the output file name is one of:

```text
tapered_pole_lookup.yaml
tapered_pc_pole_lookup.yaml
tapered_pc_pole_iso_lookup.yaml
```

## Model geometry

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

## Participation laws

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

## Basic workflow

Run the launcher from the case directory:

```bash
python3 create_yaml_tapered_pole_lookup.py
```

This writes:

```text
tapered_pole_lookup.yaml
```

The launcher contains the case parameters near the top of the file. A Python user can modify radii, number of steel components, guide radii, weights, output name, and law references there, then rerun the script.

## Shell-script workflows

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

## Direct generator use

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

## Meaning of the main command-line options

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

## Editing the case

For routine changes, edit `create_yaml_tapered_pole_lookup.py` and run it again.

For law-only changes, edit the `.dat` files in `laws/` and regenerate the YAML. Keep the first column normalized between `0.0` and `1.0`.

For a different radial subdivision, update `radii0`, `radii1`, `layer_names`, `layer_weights`, and the layer-indexed law assignments consistently.

For a different steel-component ring, update `n_bars`, `bar_guide_radius0`, `bar_guide_radius1`, `bar_diameter`, `bar_sides`, and `bar_host_layer_index`.

## Expected result

After a successful run, the generator prints a short summary and writes the selected YAML file. The YAML contains:

- the two boundary stations of the tapered member;
- the annular region polygons at each station;
- the prestressing steel component polygons at each station;
- the axial/bending law assignments;
- the shear/torsion law assignments.

The generated file is the CSF input case. Subsequent CSF operations can evaluate the member field at selected stations or sample it for downstream structural analysis.

---

# Reference basis

## Primary reference

J. Bolander Jr., K. Sowlat, and A. E. Naaman, **“Design Considerations for Tapered Prestressed Concrete Poles,” PCI Journal, 1988**.  
https://www.pci.org/PCI_Docs/Publications/PCI%20Journal/1988/January/Design%20Considerations%20for%20Tapered%20Prestressed%20Concrete%20Poles.pdf

Reason for use: this paper directly addresses tapered prestressed circular hollow-cored concrete poles and the longitudinal change of section properties in tapered poles.

## Supporting reference

ASCE Task Force / PCI Committee on Concrete Poles, **“Guide for the Design of Prestressed Concrete Poles,” PCI Journal, 1997**.  
https://www.pci.org/PCI_Docs/Publications/PCI%20Journal/1997/November/Guide%20for%20the%20Design%20of%20Prestressed%20Concrete%20Poles.pdf

Reason for use: this guide documents prestressed concrete pole families, spun-cast poles, hollow cores, prestressing steel, spiral reinforcement, and typical reinforcement arrangements.

