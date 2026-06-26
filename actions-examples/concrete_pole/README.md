# Tapered PC pole onion CSF case - lookup-driven version

This README is a user guide for the tapered circular hollow prestressed-concrete pole case.
It explains how to generate the YAML, what the case models, and how to use explicit shear/torsion laws.

## Files

```text
create_yaml_tapered_pole_lookup.py
writegeometry_tapered_rebars.py
tapered_pole_lookup.yaml
laws/
```

## Model summary

- Tapered circular hollow pole between two stations: `S0` (base) and `S1` (top).
- Four annular concrete layers:
  - `core_inner`
  - `pcbar_host_layer`
  - `cover_inner`
  - `cover_outer`
- The central hollow core is not a material polygon; it is defined by the inner radius of `core_inner`.
- 16 discrete prestressing bars are placed on a guide ring inside `pcbar_host_layer`.
- Axial/bending participation is lookup-driven.
- Shear/torsion participation is explicit per layer and may be either lookup-driven or isotropic.

## Key rules

- The generator does not assume any implicit shear law default.
- Every shear law must be specified explicitly if needed.
- `--layer-shear-law` assigns shear behavior to a concrete layer by index.
- `--all-bars-shear-law` assigns shear behavior to all bars.
- `iso(<nu>)` is supported as a full shear formula when isotropic behavior is desired.
- `T_lookup(...)` is supported for external shear lookup tables.

## How to generate the YAML

### 1. Use the launcher

The simplest workflow is:

```bash
python3 create_yaml_tapered_pole_lookup.py
```

This regenerates `tapered_pole_lookup.yaml`.

### 2. Use the generator directly for explicit shear law control

The underlying generator is `writegeometry_tapered_onion_rebars.py`.
Use it when you need to set shear laws explicitly for each layer or bars.

Example with lookup-driven shear laws:

```bash
python3 writegeometry_tapered_onion_rebars.py \
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
  --layer-law 0:T_lookup("laws/weight_law_core_inner.dat") \
  --layer-law 1:T_lookup("laws/weight_law_pcbar_host_layer.dat") \
  --layer-law 2:T_lookup("laws/weight_law_cover_inner.dat") \
  --layer-law 3:T_lookup("laws/weight_law_cover_outer.dat") \
  --all-bars-law T_lookup("laws/weight_law_pcbar.dat") \
  --layer-shear-law 0:T_lookup("laws/shear_weight_law_core_inner.dat") \
  --layer-shear-law 1:T_lookup("laws/shear_weight_law_pcbar_host_layer.dat") \
  --layer-shear-law 2:T_lookup("laws/shear_weight_law_cover_inner.dat") \
  --layer-shear-law 3:T_lookup("laws/shear_weight_law_cover_outer.dat") \
  --all-bars-shear-law T_lookup("laws/shear_weight_law_pcbar.dat") \
  --out tapered_pc_pole_onion_lookup.yaml
```

Example with explicit isotropic shear laws:

```bash
python3 writegeometry_tapered_onion_rebars.py \
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
  --layer-law 0:T_lookup("laws/weight_law_core_inner.dat") \
  --layer-law 1:T_lookup("laws/weight_law_pcbar_host_layer.dat") \
  --layer-law 2:T_lookup("laws/weight_law_cover_inner.dat") \
  --layer-law 3:T_lookup("laws/weight_law_cover_outer.dat") \
  --all-bars-law T_lookup("laws/weight_law_pcbar.dat") \
  --layer-shear-law 0:iso(0.20) \
  --layer-shear-law 1:iso(0.20) \
  --layer-shear-law 2:iso(0.20) \
  --layer-shear-law 3:iso(0.20) \
  --all-bars-shear-law iso(0.20) \
  --out tapered_pc_pole_onion_lookup.yaml
```

### Mixed mode

You can mix lookup and isotropic shear laws per layer:

```bash
--layer-shear-law 0:iso(0.20) \
--layer-shear-law 1:T_lookup("laws/shear_weight_law_pcbar_host_layer.dat") \
--layer-shear-law 2:iso(0.18) \
--layer-shear-law 3:T_lookup("laws/shear_weight_law_cover_outer.dat")
```

## What to expect

- `create_yaml_tapered_pc_pole_onion_lookup.py` generates the YAML case file.
- The central hollow core is defined by the first annular radius and is not a zero-weight polygon.
- `core_inner` is the inner annular material layer, not a void.
- All axial/bending participation is external lookup-driven.
- Shear/torsion participation is explicit and must be supplied:
  - `T_lookup(...)` for external tables,
  - `iso(<nu>)` for isotropic shear derived from Poisson's ratio.
- If a shear option is not provided, that polygon or bar receives no shear law.

## Lookup laws

The generated YAML references external lookup tables through `T_lookup(...)`.
The `laws/` directory contains the data files.

### Axial/bending laws

```text
laws/weight_law_core_inner.dat
laws/weight_law_pcbar_host_layer.dat
laws/weight_law_cover_inner.dat
laws/weight_law_cover_outer.dat
laws/weight_law_pcbar.dat
```

### Shear/torsion laws

```text
laws/shear_weight_law_core_inner.dat
laws/shear_weight_law_pcbar_host_layer.dat
laws/shear_weight_law_cover_inner.dat
laws/shear_weight_law_cover_outer.dat
laws/shear_weight_law_pcbar.dat
```

Each `.dat` file is a two-column table:

```text
z  value
```

with no header lines.

## Notes

- The launcher is a convenience script for this specific CSF case.
- The underlying generator is `writegeometry_tapered_onion_rebars.py`.
- The case is designed as a lookup-driven structural example, not as a source of analytical degradation formulas.
- `iso(<nu>)` is a valid shear law only when used explicitly and on its own.
