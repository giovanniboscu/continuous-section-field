# NREL 5-MW Tower - Verification Test Instructions

This document describes how to run the full verification workflow for the NREL 5-MW reference tower using the CSF (Cross-Section Field) library.

The workflow consists of two steps:

1. **Generate the geometry** - `nrel.ps1` creates the YAML geometry file from the NREL tower parameters.
2. **Run the section analysis** - `csf.CSFActions` reads the geometry and executes the analysis actions defined in the actions file.

---

## Prerequisites

- Python 3.x installed and accessible as `python` in the terminal
- CSF library installed (`pip install csf` or equivalent)
- PowerShell available (Windows) for Step 1
- Files present in the working directory:
  - `nrel.ps1`
  - `writegeometry_v6_twist.py`
  - `NREL-5-MW_action.yaml`

---

## Step 1 - Generate the Geometry YAML

Run the PowerShell script to generate `NREL-5-MW.yaml`:

```powershell
.\nrel.ps1
```

This script calls `writegeometry_v6_twist.py` with the NREL tower parameters and writes the output geometry file.

**What it does:**

- Defines **S0** at z = 0.00 m: circular annulus, D_ext = 6.000 m, t = 35.10 mm, N = 2048 polygon sides
- Defines **S1** at z = 87.60 m: circular annulus (via rounded rectangle with R = rdx/2), D_ext = 3.870 m, t = 24.70 mm, N = 2048 polygon sides
- Writes the vertex coordinates of both boundary sections into `NREL-5-MW.yaml`

**Expected output:**

```
Written: NREL-5-MW.yaml
```

**Key parameters set in `nrel.ps1`:**

| Parameter | Value | Description |
|-----------|------:|-------------|
| `$z0` | 0.0 m | Tower base elevation |
| `$z1` | 87.6 m | Tower head elevation (yaw bearing) |
| `$de` | 6.0 m | Base outer diameter |
| `$tg_base` | 0.0351 m | Base wall thickness |
| `$rdx = $rdy` | 3.87 m | Head outer diameter |
| `$R` | 1.935 m | Corner radius = rdx/2 → perfect circle |
| `$tg_head` | 0.0247 m | Head wall thickness |
| `$N` | 2048 | Polygon discretisation (sides per loop) |
| `$twist_deg` | 0 | No twist between S0 and S1 |

> **Note on N = 2048.** At this discretisation the polygon area error relative to the exact circle is −0.0006% (uniform), and all derived FAST quantities agree with the NREL reference values to within 0.015%. See the verification report for the full convergence study (N = 64 → 512 → 1024 → 2048).

---

## Step 2 - Run the Section Analysis

Execute the CSF actions pipeline on the generated geometry:

```bash
python3 -m csf.CSFActions NREL-5-MW.yaml NREL-5-MW_action.yaml
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NREL-5-MW.yaml` | Geometry file generated in Step 1 |
| `NREL-5-MW_action.yaml` | Actions file defining what to compute and plot |

**What it does:**

The actions file (`NREL-5-MW_action.yaml`) instructs CSF to execute the following pipeline in sequence:

| Action | Output | Description |
|--------|--------|-------------|
| `plot_volume_3d` | screen | 3-D render of the full tower |
| `section_selected_analysis` | `out/nrel_tower.txt` | Section properties at the 11 NREL stations |
| `plot_section_2d` | `out/nrel_tower_sections.jpg` | 2-D cross-section at base and head |
| `plot_properties` | `out/nrel_tower_props.jpg` | Continuous plots of J, A, Ix along z |

**Expected output files:**

```
out/
├── nrel_tower.txt           # Section properties at 11 stations (FAST format)
├── nrel_tower_sections.jpg  # 2-D section plots at z = 0.00 m and z = 87.60 m
└── nrel_tower_props.jpg     # Continuous property curves (J_sv_cell, A, Ix vs z)
```

**Expected console output (excerpt):**

```
### SECTION SELECTED ANALYSIS @ z = 0.0 ###
A                   : 0.65774791  [Total net cross-sectional area]
Ix                  : 2.92543315  [Second moment about centroidal X-axis]
J_sv_cell           : (5.851064315, 0.035099959)  [Saint-Venant torsional constant]
...
### SECTION SELECTED ANALYSIS @ z = 87.6 ###
A                   : 0.29838458
Ix                  : 0.55152357
J_sv_cell           : (1.103091791, 0.024699971)
```

---

## Verification

To verify the results against the NREL reference values (NREL/TP-500-38060, Table 6-1), compare the quantities in `out/nrel_tower.txt` with the table below using the material constants E = 210 GPa, G = 80.8 GPa, ρ = 8500 kg/m³:

| FAST symbol | Formula | Max Δ% vs NREL (N=2048) |
|-------------|---------|------------------------:|
| TMassDen | ρ · A | < 0.010% |
| TwFAStif | E · Ix | < 0.010% |
| TwSSStif | E · Iy = E · Ix | < 0.010% |
| TwGJStif | G · J_sv_cell[0] | < 0.015% |
| TwEAStif | E · A | < 0.010% |
| TwFAIner | ρ · Ix | < 0.010% |
| TwSSIner | ρ · Iy | < 0.010% |

---

## Notes

**On the geometry model.** The YAML file produced by `nrel.ps1` is not a configuration file - it is the structural model itself. It contains the polygon vertex coordinates of the two boundary sections S0 and S1. From these two sections, CSF constructs a continuous section field over the full 87.60 m height. All section properties - at the 11 NREL stations, at the 100 plot points, or at any arbitrary elevation - are derived from this single geometric definition.

**On the torsional constant.** The `@cell` polygon tag activates the Bredt-Batho closed thin-walled cell formula. Because no explicit `@t=` thickness token is provided, CSF computes the wall thickness automatically as t(z) = 2A(z)/P(z) at each queried elevation - a continuous function of z, not a linear interpolation between endpoint values.

**On the output tuple format.** `J_sv_cell` returns a tuple `(J [m⁴], t_used [m])`. The first element is the torsional constant used to derive TwGJStif = G · J. The second element is the wall thickness used internally by the Bredt-Batho formula at that elevation.

---

## Reference

Jonkman, J., Butterfield, S., Musial, W., Scott, G. (2009).
*Definition of a 5-MW Reference Wind Turbine for Offshore System Development.*
NREL/TP-500-38060. National Renewable Energy Laboratory, Golden, CO.
Tower properties: Section 6, Table 6-1 (p. 15) and Table 6-2 (p. 16).
