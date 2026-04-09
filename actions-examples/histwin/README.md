# Quick Start - HISTWIN Example
<img width="385" height="602" alt="Screenshot 2026-04-04 at 20 59 48" src="https://github.com/user-attachments/assets/9843a5b8-4836-4d0b-9e7e-6c9e0307e2d0" />
<img width="856" height="614" alt="Screenshot 2026-04-09 at 15 58 50" src="https://github.com/user-attachments/assets/122b66e7-96b0-4993-a606-5870746acf2b" />

After creating histwin_tower.yaml  you can follow the step-by-step OpenFAST integration workflow here:

[OpenFAST integration guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/histwin/openfastguide.md)
---


If you only want to try the **HISTWIN** example, follow the steps below.

---

## 1. Create a virtual environment

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install csfpy
```

### Windows

```powershell
python3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install csfpy
```

---

## 2. Get the source from the repository

### Option A - Sparse checkout (only the HISTWIN example)

Use this if you do not need the full repository.

```bash
git clone --filter=blob:none --no-checkout https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
git sparse-checkout init --cone
git sparse-checkout set actions-examples/histwin
git checkout main
```

### Option B - Full clone

Use this if you want the full repository.

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

---

## 3. Go to the HISTWIN example folder

### Linux / macOS

```bash
cd actions-examples/histwin
```

### Windows

```powershell
cd actions-examples\histwin
```

---
### Expected Results

Before running the analysis, understand what the `action.yaml` does and what results to expect

[Expected results for `csf-actions histwin_tower.yaml action.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/histwin/csf_expected_results.md)

### action.yaml Description

Use this link:

[description `action.yaml` ](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/histwin/csf_action_yaml_summary.md)

---
## 4. Generate the CSF input files

### Linux / macOS

```bash
chmod +x create_yaml-histwin.sh
./create_yaml-histwin.sh
./create_yaml-histwin.sh -action
```

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\create_yaml_histwin.ps1
powershell -ExecutionPolicy Bypass -File .\create_yaml_histwin.ps1 -action
```

This generates:

- `histwin_tower.yaml`
- `action.yaml`

---

## 5. Run the analysis

### Linux / macOS

```bash
csf-actions histwin_tower.yaml action.yaml
```

### Windows

```powershell
csf-actions.exe histwin_tower.yaml action.yaml
```

The `out` directory will contain the generated reports.

---

## Notes

- `histwin_tower.yaml` contains the tower geometry.
- `action.yaml` contains the analysis and post-processing actions.
- The example is focused on the HISTWIN tower only.



# HISTWIN Tower Example

## Overview

This example reproduces a **HISTWIN-type monitored steel wind tower** in CSF as a **circular hollow tapered shell**  and an optional longitudinal degradation law for the steel shell.

The example is intended to generate:

- a `geometry.yaml` file for CSF;
- an `action.yaml` file for CSF post-processing;
- an optional equivalent shell-degradation field `w(z)` that can be activated in the launcher script.

The model is deliberately simple and focuses on the **tower shell only**. It does not attempt to reproduce bolts, flanges, end-ring thickness details, doors, platforms, or nacelle/foundation details explicitly.

---

## Reference tower in one paragraph

The reference tower is a **conical tubular steel wind-turbine tower** associated with the HISTWIN monitoring literature. Public sources describe it as a free-standing steel tube with **varying diameter and wall thickness**, assembled from **three transported segments** and monitored with accelerometers, strain gauges, inclinometers, temperature sensors, and measurements in the vicinity of the assembly joints and bolts. Publicly reported dimensions for the HISTWIN-type 76.15-76.20 m tower are approximately:

- total tower shell height: about `76.15-76.20 m`
- bottom diameter: about `4.30 m`
- top diameter: about `3.00 m`
- wall thickness: about `30 mm` at the base and `12 mm` at the top
- three subparts: about `21.8 m`, `26.6 m`, and `27.8 m`

In this project, the tower is represented as a smooth CSF section field between two circular hollow end sections.

---

## Modeling approach used here

The tower is modeled as:

- one **single shell component**;
- circular at both ends;
- linearly tapered in diameter and wall thickness between base and top;
- generated through `python3 -m csf.utils.writegeometry_rio_v2`;
- exported as a **single-polygon `@cell` representation** for the hollow circular shell.

No rebars are intended in this model.

Because `writegeometry_rio_v2.py` requires rebar-related command-line arguments even when no bars are used, the launcher passes **dummy placeholder values** while keeping the bar counts at zero. As a result, **no rebar polygons are written**.

---

## Files generated by the launchers

### Geometry mode

Running the launcher with no special flag generates:

- `histwin_tower.yaml`

This file contains the CSF geometry with:

- section `S0` at the tower base;
- section `S1` at the tower top;
- one shell polygon per section encoded as `@cell`.

### Action mode

Running the launcher with `-action` generates:

- `action.yaml`

This file contains:

- predefined station sets;
- a 3D ruled-volume plot action;
- a selected-section property report;
- optional commented examples for additional post-processing.

---

## Expected launcher behavior

### Bash launcher

```bash
./create_yaml-histwin.sh
```

Generates only the geometry file.

```bash
./create_yaml-histwin.sh -action
```

Generates only the action file.

### PowerShell launcher

The PowerShell version is expected to expose the **same modeling parameters**, the same geometry/action outputs, and the same engineering meaning of the parameter block. The syntax changes, but the parameters and their interpretation should remain aligned with the Bash version.

---

## Geometry currently used in the example

The present model uses the following values:

### Global coordinates

- `z0 = 0.0`
- `z1 = 76.15`

### Base section `S0`

- `s0_dx = 4.300`
- `s0_dy = 4.300`
- `s0_R  = 2.150`
- `s0_tg = 0.030`
- `s0_x  = 0.0`
- `s0_y  = 0.0`
- `s0_t_cell = 0.0`

### Top section `S1`

- `s1_dx = 3`
- `s1_dy = 3`
- `s1_R  = 1.5`
- `s1_tg = 0.012`
- `s1_x  = 0.0`
- `s1_y  = 0.0`
- `s1_t_cell = 0.0`

### Discretization

- `twist_deg = 0`
- `N = 128`
- `singlepolygon = True`

### Rebar placeholders

- `n_bars_row1 = 0`
- `n_bars_row2 = 0`
- `area_bar_row1 = 1`
- `area_bar_row2 = 1`
- `dist_row1_outer = 1`
- `dist_row2_inner = 1`
- `rebar_weight = 1`

These rebar-related values are only placeholders required by the generator interface. Since both bar counts are zero, they do not create any steel-bar geometry.

---

## Meaning of the parameters in the `.sh` and `.ps1` launchers

This section documents the engineering meaning of the parameter block that should appear in both launchers.

### Longitudinal coordinates

- `z0`  
  Start elevation of the tower shell.

- `z1`  
  End elevation of the tower shell.

The total modeled height is:

```text
L = z1 - z0
```

---

### Base section parameters

- `s0_dx`  
  External size in the local `x` direction at `S0`.

- `s0_dy`  
  External size in the local `y` direction at `S0`.

- `s0_R`  
  Corner radius used by the rounded-rectangle generator.  
  For a circular tower, set `dx = dy = D` and `R = D/2`.

- `s0_tg`  
  Wall thickness at `S0`.

- `s0_x`, `s0_y`  
  Coordinates of the section center.

- `s0_t_cell`  
  Optional cell-thickness tag written into the polygon name.  
  Use `0.0` when no explicit `@t=` tag is desired.

---

### Top section parameters

- `s1_dx`
- `s1_dy`
- `s1_R`
- `s1_tg`
- `s1_x`
- `s1_y`
- `s1_t_cell`

These have the same meaning as the `S0` parameters, but refer to the top section `S1`.

---

### Discretization and geometric encoding

- `twist_deg`  
  Relative rotation of the head section with respect to the base section.  
  For an untwisted tower, use `0`.

- `N`  
  Number of points used to discretize each loop.  
  Larger values provide a smoother circular approximation but increase file size.

- `singlepolygon`  
  If `True`, the hollow section is exported as one `@cell` polygon.  
  If `False`, the outer loop and the inner void loop are exported separately.

For this tower example, `singlepolygon = True` is the intended setting.

---

### Rebar placeholder parameters

Even though this project does not model rebars, the underlying generator still requires rebar-related CLI arguments. Therefore, the launchers keep these parameters in the block.

- `n_bars_row1`, `n_bars_row2`  
  Number of bars in each row.  
  Keep both equal to `0` for this project.

- `area_bar_row1`, `area_bar_row2`  
  Single-bar areas.  
  These are dummy values when bar counts are zero.

- `dist_row1_outer`, `dist_row2_inner`  
  Offsets used to place bar rows.  
  These are dummy values when bar counts are zero.

- `rebar_weight`  
  Rebar weight factor.  
  Also a dummy value when bar counts are zero.

---

## Optional shell-variation law

The launcher allows the shell to be assigned a longitudinal law through:

```text
shell_law
s0_law
s1_law
```

In the current setup:

```text
s0_law = shell_law
s1_law = shell_law
```

This is required because the shell is one continuous component and both ends must reference the same longitudinal law.

If `shell_law` is left empty, the shell keeps a constant participation factor equal to `1.0` along the full height.

---

## Adopted degradation law

The degradation law currently discussed for this project is:

```python
shell_law="np.maximum(0.84,1.0-0.10*np.exp(-((z-0.33*L)**2)/(2*(0.03*L)**2))-0.14*np.exp(-((z-0.67*L)**2)/(2*(0.03*L)**2)))"
```

where:

- `z` is the longitudinal coordinate;
- `L = z1 - z0`;
- `w(z)` is the equivalent shell participation factor.

Written in mathematical form:

```text
w(z)=max(0.84,1.0-0.10*exp(-((z-0.33*L)^2)/(2*(0.03*L)^2))-0.14*exp(-((z-0.67*L)^2)/(2*(0.03*L)^2)))
```

---

## Engineering meaning of the degradation law

This law is **not** a physical crack-propagation model. It is an **equivalent longitudinal modifier** introduced at the level of section properties.

Its purpose is to represent the idea that the tower shell is mostly intact over most of the height, while two local regions have a reduced equivalent contribution.

The law contains:

- a baseline intact value `1.0`;
- a first local Gaussian reduction centered at `0.33*L`;
- a second, slightly deeper local Gaussian reduction centered at `0.67*L`;
- a floor at `0.84`, used as a lower bound.

The first dip has amplitude `0.10`.  
The second dip has amplitude `0.14`.  
Both dips have width controlled by `0.03*L`.

For `L = 76.15 m`, this gives:

- first center at about `25.13 m`;
- second center at about `51.02 m`;
- characteristic width `sigma = 2.2845 m`.

---

## Why local Gaussian reductions were chosen

A uniform linear decay along the full shell height would suggest a broadly diffuse deterioration. That is not the most natural equivalent description for a segmented steel tower whose most sensitive details are associated with:

- segment-to-segment joints,
- bolted flange regions,
- end-ring connection areas,
- local stress concentrations near connection details.

For that reason, the adopted law uses **two localized reductions** rather than one global monotonic decay.

---

## Important clarification on the meaning of the “rings”

The term *rings* should **not** be interpreted as arbitrary damaged circular bands somewhere in the middle of the shell wall.

In the HISTWIN configuration, the relevant rings are the **end rings / ring-flange connection regions at the boundaries of the transported tower segments**.

When the tower is viewed globally, those module boundaries appear at intermediate elevations along the shaft. Therefore, the two local dips in `w(z)` should be interpreted as **equivalent reductions placed near the segment-joint elevations**, not as unexplained damage bands created inside an otherwise uniform shell plate field.

This distinction is important and should be kept explicit in reports or publications.

---

## Coherence check against public HISTWIN data

The adopted law is **coherent in mechanism**, but **stylized in position**.

### Coherent aspects

The public HISTWIN-related descriptions support the following points:

- the tower is a conical tubular steel tower;
- it is divided into three transported segments;
- monitoring targeted the vicinity of the assembly joints and bolts;
- fatigue-sensitive behavior is therefore more naturally associated with localized connection regions than with uniform shell-wide deterioration.

Therefore, a law with **two local reductions** is defensible as an equivalent engineering representation.

### Non-exact aspects

Publicly reported subpart lengths for the 76.2 m HISTWIN tower are approximately:

- `21.8 m`
- `26.6 m`
- `27.8 m`

This places the two segment-joint elevations at about:

- `21.8 m`
- `48.4 m`

By contrast, the current law places the Gaussian centers at:

- `25.13 m`
- `51.02 m`

So the current law is **not an exact geometric calibration** of the published joint locations. It is a **smooth idealized placement near one-third and two-thirds of the tower height**.

This is acceptable if the law is presented as a **phenomenological equivalent field**, but it should **not** be presented as an experimentally fitted fatigue law.

---

## More data-consistent alternative

If closer alignment with the reported three-segment geometry is desired, the Gaussian centers can be moved to the approximate joint elevations.

A more geometry-consistent alternative is:

```python
shell_law="np.maximum(0.84,1.0-0.10*np.exp(-((z-0.286*L)**2)/(2*(0.03*L)**2))-0.14*np.exp(-((z-0.636*L)**2)/(2*(0.03*L)**2)))"
```

This keeps the same structure and interpretation, but shifts the dips closer to:

- `21.8 m`
- `48.4 m`

for a tower height near `76.15-76.20 m`.

---

## Suggested station sets for this tower

A practical station definition is:

```yaml
stations:
  station_ends:  [0.0, 76.15]                                  # tower base and tower top
  station_mid:   [38.075]                                      # single mid-height control section
  station_dense: [0.0, 21.8, 38.075, 48.4, 76.15]              # base, first joint, mid-height, second joint, top
```

This is useful because it includes both end sections and the two approximate segment-joint elevations.

---

## Recommended workflow

### 1. Generate the geometry

Bash:

```bash
./create_yaml-histwin.sh
```

PowerShell:

```powershell
./create_yaml-histwin.ps1
```

### 2. Generate the action file

Bash:

```bash
./create_yaml-histwin.sh -action
```

PowerShell:

```powershell
./create_yaml-histwin.ps1 -action
```

### 3. Run the CSF post-processing

```bash
csf-actions histwin_tower.yaml action.yaml
```

---

## References used for the engineering interpretation

1. Rebelo, Henriques, Simões, Simões da Silva, *Long-term monitoring of a eighty meters high wind turbine steel tower*. Public description of a monitored steel tower in Portugal, with varying diameter and thickness, divided into three parts, and monitored near assembly joints and bolts.

2. REpower MM92 technical description. Public description of the MM92 tower as a conical tubular steel tower with hub heights around 78.5 m, 80 m, and 100 m, and approximate head/bottom flange diameters.

3. Stavridou et al., *Lattice and Tubular Steel Wind Turbine Towers. Comparative Structural Investigation*. Public summary of HISTWIN-type tubular towers, including a 76.20 m tower with subparts of 21.8 m, 26.6 m, and 27.8 m and a bottom diameter of 4.3 m.

---

## Short scientific wording for reports

A compact wording suitable for reports is:

> The present example models a HISTWIN-type monitored steel wind-turbine tower as a circular hollow tapered shell within the CSF framework. The tower is represented by two end sections and continuous interpolation along the height. An optional shell law `w(z)` is introduced to describe equivalent local degradation effects near the segment-joint elevations of the three-part tower. The adopted field is smooth and bounded and is intended as a phenomenological modifier of sectional contribution rather than as a direct fatigue-life model.
