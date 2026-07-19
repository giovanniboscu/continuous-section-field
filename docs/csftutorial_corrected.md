# CSF YAML Tutorial (CSFActions.py)

[CSF Actions Template - complete reference with all available actions](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/actions_template.yaml)

Although CSF is implemented as a Python engine, it can be used **without programming** through the **CSFActions** command-line tool.
In these tutorials, the working directory is set immediately after cloning the repository or after creating a separate case directory.

> **[rectangle/](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/rectangle) is a complete worked example of the CSF Actions workflow on a tapered rectangular section. Run it with `csf-actions geometry.yaml actions.yaml`.**

After installation, create your case folder structure, for example:

```text
mkdir mycase
cd mycase

mycase/
  geometry.yaml
  actions.yaml
  out/                # create this folder yourself
```

1. **`geometry.yaml`** - defines the member geometry and carrier fields along the axis `z`
   - endpoint sections as arbitrary polygons;
   - optional multi-polygon sections;
   - per-polygon weights and optional longitudinal laws.

2. **`actions.yaml`** - declares what CSF must do without Python code
   - compute and export section properties;
   - produce plots and diagnostic reports;
   - export station data for external beam solvers.

**Important**: CSFActions checks that output paths are writable, but it does **not** create missing output folders during validation.
Create `out/` and any required subfolders before running.

### 1. Minimal `actions.yaml`

This example displays the ruled 3D volume and evaluates selected section properties at three stations.

**actions.yaml**:

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example:
      - 0.0
      - 1.0
      - 10.0

  actions:
    - plot_volume_3d:
        params:
          line_percent: 100.0
          seed: w
          title: "Ruled volume"

    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
        properties: [A, Cx, Cy,
                     Ix, Iy, Ixy,
                     Ip, I1, I2,
                     rx, ry,
                     Wx, Wy, K_torsion, Q_na,
                     J_sv_wall, J_sv_cell,
                     J_s_vroark, J_s_vroark_fidelity]
```

**geometry.yaml**:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 1.0]
            - [-0.5, 1.0]

    S1:
      z: 10.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 2.0]
            - [-0.5, 2.0]
```

### 1.1 CLI command

From inside the case directory:

```bash
csf-actions geometry.yaml actions.yaml
```

### 1.2 Expected output

The 3D figure is displayed at the end of the run. The selected-property report includes the following values for the geometry above:

```text
### SECTION SELECTED ANALYSIS @ z = 0.0 ###
A                   : 1.00000000  [Total net cross-sectional area]
Cx                  : 0.00000000  [Horizontal centroid (X)]
Cy                  : 0.50000000  [Vertical centroid (Y)]
Ix                  : 0.08333333  [Second moment about centroidal X-axis]
Iy                  : 0.08333333  [Second moment about centroidal Y-axis]
Ixy                 : 0.00000000  [Product of inertia (symmetry indicator)]
Ip                  : 0.16666667  [Polar second moment (Ix + Iy)]
I1                  : 0.08333333  [Major principal second moment]
I2                  : 0.08333333  [Minor principal second moment]
rx                  : 0.28867513  [Radius of gyration (about X)]
ry                  : 0.28867513  [Radius of gyration (about Y)]
Wx                  : 0.16666667  [Elastic section modulus about X]
Wy                  : 0.16666667  [Elastic section modulus about Y]
K_torsion           : 0.15000000  [Semi-empirical torsional stiffness approximation]
Q_na                : 0.12500000  [First moment of area at neutral axis]
J_sv_wall           : 0.00000000  [Saint-Venant torsional constant for open thin-walled walls]
J_sv_cell           : 0.00000000  [Saint-Venant torsional constant for closed thin-walled cells (Bredt-Batho)]
J_s_vroark          : 0.14083333  [Roark torsional indicator (equivalent-rectangle mapping)]
J_s_vroark_fidelity : 1.00000000  [Fidelity / reliability indicator]

### SECTION SELECTED ANALYSIS @ z = 1.0 ###
A                   : 1.10000000
Cx                  : 0.00000000
Cy                  : 0.55000000
Ix                  : 0.11091667
Iy                  : 0.09166667
Ixy                 : 0.00000000
Ip                  : 0.20258333

### SECTION SELECTED ANALYSIS @ z = 10.0 ###
A                   : 2.00000000
Cx                  : 0.00000000
Cy                  : 1.00000000
Ix                  : 0.66666667
Iy                  : 0.16666667
Ixy                 : 0.00000000
Ip                  : 0.83333333
```

---

### 2. `actions.yaml` (execution plan)

The `actions.yaml` file must contain a single top-level root key:

```yaml
CSF_ACTIONS:
  stations: ...
  actions: ...
```

#### Required keys

- `CSF_ACTIONS:` - root mapping;
- `actions:` - required non-empty list;
- `stations:` - required when at least one selected action requires station sets.

`stations:` may be omitted when all selected actions forbid stations, for example when the file contains only `plot_volume_3d`, `plot_properties`, `plot_weight`, `plot_shear_weight`, or `write_opensees_geometry`.

#### Rule: `actions:` must appear only once

YAML duplicate keys can overwrite silently in some tools.
CSFActions rejects duplicate keys with a controlled error and a source snippet.

---

## 3. Stations (what they are, how they work)

Stations are named lists of `z` coordinates:

```yaml
stations:
  station_name:
    - 0.0
    - 1.0
    - 10.0
```

### 3.1 Station semantics

- For normal station-based actions, values are **absolute `z` coordinates**.
- For `weight_lab_zrelative`, values are interpreted as **relative `z` coordinates**.
- `export_yaml` and `volume` require exactly one referenced station set containing exactly two values.
- `write_sap2000_geometry` accepts either one explicit station set or no station set. When no station set is supplied, it generates Gauss-Lobatto stations from `n_intervals`.
- `plot_volume_3d`, `plot_properties`, `plot_weight`, `plot_shear_weight`, and `write_opensees_geometry` forbid `stations:`.

### 3.2 Station sets are reusable

```yaml
CSF_ACTIONS:
  stations:
    stations_example:
      - 0.0
      - 1.0
      - 10.0

    stations_edges:
      - 0.0
      - 10.0

  actions:
    - section_selected_analysis:
        stations: stations_example
        properties: [A, Ix, Iy]

    - export_yaml:
        stations: stations_edges
        output: [out/exported_geometry.yaml]
```

---

## 4. Output rules (stdout vs file-only)

Each action may have an `output:` list. If `output` is missing, the normal default is:

```yaml
output: [stdout]
```

File-only actions are exceptions: `export_yaml`, `write_opensees_geometry`, and `write_sap2000_geometry` require an explicit file output and reject `stdout`.

### 4.1 File-only behavior

If `output:` exists but does not contain `stdout`, normal report and plot actions run in file-only mode:

- no interactive display or terminal report from that action;
- only the requested files are produced.

For report actions, the format is normally inferred from the extension:

- `.csv` - tabular CSV output;
- other extensions such as `.txt` - plain-text report.

Example:

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example: [0.0, 1.0, 10.0]

  actions:
    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
          - out/results.csv
          - out/report.txt
        properties: [A, Cx, Cy, Ix, Iy]

    - section_selected_analysis:
        stations: stations_example
        output:
          - out/geometry.txt
        properties: [geometry]
```

```bash
mkdir -p out
csf-actions geometry.yaml actions.yaml
```

For the unweighted rectangle used in Section 1, `out/results.csv` begins with:

```csv
z,A,Cx,Cy,Ix,Iy
0.00000000,1.00000000,0.00000000,0.50000000,0.08333333,0.08333333
1.00000000,1.10000000,0.00000000,0.55000000,0.11091667,0.09166667
10.00000000,2.00000000,0.00000000,1.00000000,0.66666667,0.16666667
```

The geometry export contains the current absolute `w`, `shear_w`, `poisson`, and polygon vertices, for example:

```text
## GEOMETRY EXPORT ##
# z=0.0
idx_polygon,idx_container,s0_name,s1_name,w,shear_w,poisson,vertex_i,x,y
0,,rect,rect,1.00000000,1.00000000,,0,-0.50000000,0.00000000
0,,rect,rect,1.00000000,1.00000000,,1,0.50000000,0.00000000
0,,rect,rect,1.00000000,1.00000000,,2,0.50000000,1.00000000
0,,rect,rect,1.00000000,1.00000000,,3,-0.50000000,1.00000000
```

The output directory is not created automatically by CSFActions validation and must already exist.

# `plot_volume_3d`: carrier-colored generator lines

A specific feature of `plot_volume_3d` is the `seed` parameter. It accepts either a legacy integer seed or a semantic string mode.

The semantic modes color generator-line segments according to either:

- the axial/bending carrier `weight`;
- the shear/torsion carrier `shear_weight`.

## Basic usage

```yaml
CSF_ACTIONS:
  actions:
    - plot_volume_3d:
        params:
          seed: w
```

`seed: w` colors generator lines according to the local absolute `weight` value.

```yaml
CSF_ACTIONS:
  actions:
    - plot_volume_3d:
        params:
          seed: s
```

`seed: s` colors generator lines according to the local absolute `shear_weight` value.

## Optional resolution suffix

The semantic mode may include an integer resolution suffix:

```yaml
seed: w80
seed: s120
```

- `w80` uses `weight` with resolution `80`;
- `s120` uses `shear_weight` with resolution `120`.

## Meaning of the prefixes

| Prefix | Carrier used for coloring |
|---|---|
| `w` | `weight` |
| `s` | `shear_weight` |

## Constant `weight` / `shear_weight`

If the selected carrier is constant along the member axis, the corresponding generator lines are rendered in black. A constant zero carrier is rendered as a void/neutral color by the visualizer.

## Summary

```yaml
seed: 0      # legacy integer seed and polygon-based coloring
seed: w      # color by weight
seed: s      # color by shear_weight
seed: w80    # color by weight, resolution 80
seed: s120   # color by shear_weight, resolution 120
```

**Example geometry file**:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 1.0]
            - [-0.5, 1.0]

    S1:
      z: 10.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 2.0]
            - [-0.5, 2.0]

  weight_laws:
    - 'rect,rect: 1.0 - 0.28 * np.exp(-((t - 0.0)**2) / (2.0 * 1.5**2))'

  shear_weight_laws:
    - 'max(0.0, 1.0 - t / 3.0)'
```

**Example actions file**:

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example: [0.0, 1.0, 10.0]

  actions:
    - plot_volume_3d:
        params:
          line_percent: 100.0
          seed: w
          title: "Ruled volume - weight"

    - plot_volume_3d:
        params:
          line_percent: 100.0
          seed: s
          title: "Ruled volume - shear weight"

    - section_selected_analysis:
        stations: stations_example
        output: [stdout, out/results.csv, out/report.txt]
        properties: [A, Cx, Cy, Ix, Iy]

    - section_selected_analysis:
        stations: stations_example
        output: [out/geometry.txt]
        properties: [geometry]
```

Run with:

```bash
csf-actions geometry.yaml actions.yaml
```

---

## 4.2 Geometry export in `properties`

The special keyword `geometry` can be added to the `properties` list of `section_selected_analysis` to export the section geometry at every evaluated station.

The geometry block includes:

- polygon and container indices;
- endpoint polygon names;
- absolute `weight` and `shear_weight` at the station;
- Poisson metadata when present;
- vertex indices and coordinates.

`geometry` is optional. When both numerical properties and `geometry` are requested, text output contains both. In CSV output, the numerical table is written first and the geometry blocks are appended after it.

Example:

```yaml
CSF_ACTIONS:
  stations:
    stations_example: [0.0, 1.0, 10.0]

  actions:
    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
          - out/results.csv
          - out/report.txt
        properties: [geometry, A, Cx, Cy, Ix, Iy]
```

### Example output

```text
### SECTION SELECTED ANALYSIS @ z = 0.0 ###
A                   : 1.00000000  [Total net cross-sectional area]
Cx                  : 0.00000000  [Horizontal centroid (X)]
Cy                  : 0.50000000  [Vertical centroid (Y)]
Ix                  : 0.08333333  [Second moment about centroidal X-axis]
Iy                  : 0.08333333  [Second moment about centroidal Y-axis]

## GEOMETRY EXPORT ##
# z=0.0
idx_polygon,idx_container,s0_name,s1_name,w,shear_w,poisson,vertex_i,x,y
0,,rect,rect,1.00000000,1.00000000,,0,-0.50000000,0.00000000
```

**Note**: the exported `w` and `shear_w` values are absolute carrier values at the evaluated station.

---

# 4.3 Minimal example: geometry, weight law, and action file

This example shows:

- where to place `weight_laws` in the geometry YAML;
- a simple quadratic weight law;
- actions to visualize the member, inspect selected stations, and plot weight variation.

## Geometry YAML

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 1.0]
            - [-0.5, 1.0]

    S1:
      z: 10.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 2.0]
            - [-0.5, 2.0]

  weight_laws:
    - 'rect,rect: 1.0 - 0.3*(z/L)*(z/L)'
```

## Meaning of the weight law

```text
rect,rect: 1.0 - 0.3*(z/L)*(z/L)
```

- `rect,rect` identifies the endpoint polygon pair;
- `z` is the longitudinal coordinate used by the weight-law evaluator;
- `L` is the member length;
- the expression defines the absolute polygon weight.

For the local domain `0 <= z <= L`:

- at `z = 0`, `w = 1.0`;
- at `z = L`, `w = 0.7`.

## Action YAML

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example: [0.0, 1.0, 10.0]

  actions:
    - plot_volume_3d:
        params:
          line_percent: 100.0
          seed: w200
          title: "Ruled volume"

    - section_selected_analysis:
        stations: stations_example
        output: [stdout, out/results.csv, out/report.txt]
        properties: [geometry, A, Cx, Cy, Ix, Iy]

    - plot_weight:
        output: [stdout, out/weight.jpg]
        params:
          num_points: 100
```

## What these actions do

- `plot_volume_3d` displays the ruled member volume colored by `weight`;
- `section_selected_analysis` reports and exports the selected properties and optional geometry;
- `plot_weight` samples and plots the longitudinal weight variation.

## Notes

- `geometry` is optional in `properties`;
- output directories such as `out/` must already exist;
- `out/weight.jpg` is used as a base output path; `plot_weight` may write one or more files with derived suffixes when several polygon plots are produced.

---

## 5. Useful CLI options

### 5.1 Validate only (no execution)

```bash
csf-actions geometry.yaml actions.yaml --validate-only
```

Expected final messages:

```text
ContinuousSectionField instantiated successfully.
Actions file validated successfully.
Validation-only mode: no actions executed.
```

### 5.2 Print built-in help for actions

```bash
csf-actions --help-actions
```

This prints:

- the current action catalog;
- station rules;
- action parameters, types, defaults, and aliases;
- output behavior;
- minimal YAML examples.

---

## 6. One per main action

Each action section includes:

- concept;
- a small YAML example;
- command;
- output behavior;
- common pitfalls.

> In all examples below, assume `geometry.yaml` exists and is valid.

**Common pitfalls**

- required station set missing;
- forbidden `stations:` supplied;
- output directory missing;
- station outside the CSF domain;
- unsupported property or parameter name.

---

### 6.2 `section_selected_analysis` (extended property list example)

**Concept**

Evaluates the complete local section analysis internally and reports or exports only the keys listed in `properties`, preserving the requested order.

The accepted numerical keys are:

```text
A, Cx, Cy, Ix, Iy, Ixy, Ip, I1, I2,
rx, ry, Wx, Wy, K_torsion, Q_na,
J_sv_wall, J_sv_cell,
J_s_vroark, J_s_vroark_fidelity
```

The special key `geometry` requests the geometry export described in Section 4.2.

`J_sv_cell` and `J_sv_wall` may be zero when no corresponding `@cell` or `@wall` model is defined.

### YAML

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example: [0.0, 1.0, 10.0]

  actions:
    - section_selected_analysis:
        stations: stations_example
        output: [stdout, out/results.csv, out/report.txt]
        properties: [A, Cx, Ix, Iy, Ip, I1, I2, Cy,
                     rx, ry, Ixy, Wx, Wy, K_torsion, Q_na,
                     J_sv_cell, J_sv_wall,
                     J_s_vroark, J_s_vroark_fidelity]
        params:
          fmt_display: ".8f"
```

### CLI

```bash
mkdir -p out
csf-actions geometry.yaml actions.yaml
```

### Example output (snippet)

```text
### SECTION SELECTED ANALYSIS @ z = 0.0 ###
A                   : 1.00000000
Cx                  : 0.00000000
Ix                  : 0.08333333
Iy                  : 0.08333333
Ip                  : 0.16666667
J_sv_cell           : 0.00000000
J_sv_wall           : 0.00000000
```

### Notes

- `properties` is required and must be non-empty;
- duplicate property names are preserved and generate a warning;
- `fmt_display` controls numeric formatting in stdout and text output;
- CSV columns are `z` followed by the selected numerical keys.

### Pitfalls

- `J` is not an accepted property key; use `Ip` for `Ix + Iy`;
- `Ixx` and `Iyy` are not accepted aliases for `Ix` and `Iy`;
- `geometry` cannot be plotted by `plot_properties`; it is specific to `section_selected_analysis`.

---

### 6.3 `plot_section_2d` (stations REQUIRED)

**Concept**

Plots the section geometry at each requested station. When multiple stations and a file output are requested, the action produces one composite raster image with the station plots stacked vertically.

### YAML

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_edges: [0.0, 10.0]

  actions:
    - plot_section_2d:
        stations: stations_edges
        output: [stdout, out/sections.png]
        params:
          show_ids: true
          show_weights: true
          show_vertex_ids: true
          show_legenda: true
          title: "Section at z={z}"
          dpi: 150
```

### CLI

```bash
mkdir -p out
csf-actions geometry.yaml actions.yaml
```

### Output behavior

- `stdout` keeps the figure for deferred display at the end of the run;
- an image path saves the composite image;
- omitting `stdout` gives file-only behavior.

### Parameters

| Parameter | Type | Default | Meaning |
|---|---:|---:|---|
| `show_ids` | bool | `true` | Show polygon indices. |
| `show_weights` | bool | `true` | Show polygon names and weights in labels/legend. |
| `show_vertex_ids` | bool | `false` | Show vertex indices. |
| `show_legenda` | bool | `true` | Show the polygon legend below the section plot. |
| `title` | str | `null` | Optional title; `{z}` is replaced by the station value. |
| `dpi` | int | `150` | Raster DPI for saved images. |

### Pitfalls

- `stations` is required;
- put canonical action options under `params:`;
- the output directory must exist.

---

### 6.4 `plot_volume_3d` (stations FORBIDDEN)

**Concept**

Shows a ruled 3D volume between the two endpoint sections. This action is interactive-only and does not save image files.

### YAML

```yaml
CSF_ACTIONS:
  actions:
    - plot_volume_3d:
        output: [stdout]
        params:
          show_end_sections: true
          line_percent: 50.0
          seed: w200
          title: "CSF volume"
          equalize_z: false
```

### Parameters

| Parameter | Type | Default | Meaning |
|---|---:|---:|---|
| `show_end_sections` | bool | `true` | Draw endpoint-section outlines. |
| `line_percent` | float | `100.0` | Percentage of generator lines shown; valid range `0..100`. |
| `seed` | int or str | `0` | Integer legacy seed, or `w`, `s`, `wN`, `sN`. |
| `title` | str | `"Ruled volume (vertex-connection lines)"` | Figure title. |
| `equalize_z` | bool | `false` | Use proportional visual scaling between `z` and the `x/y` axes. |

### CLI

```bash
csf-actions geometry.yaml actions.yaml
```

### Pitfalls

- `stations:` is forbidden;
- file outputs are rejected;
- use `stdout` or omit `output:`;
- `line_percent` must be between `0` and `100`.

---

### 6.5 `plot_properties` (stations FORBIDDEN)

**Concept**

Plots selected section properties along the member by sampling `num_points` coordinates between the endpoints.

### YAML

```yaml
CSF_ACTIONS:
  actions:
    - plot_properties:
        output: [stdout, out/properties.png]
        properties: [A, Ix, Iy, Ip]
        params:
          num_points: 100
```

### Parameters

| Parameter | Type | Default | Meaning |
|---|---:|---:|---|
| `num_points` | int | `100` | Number of longitudinal samples. |

The allowed property keys are the numerical keys listed for `section_selected_analysis`; `geometry` is not accepted here.

### CLI

```bash
mkdir -p out
csf-actions geometry.yaml actions.yaml
```

### Output behavior

- `stdout` requests deferred display;
- image paths save the figure;
- without `stdout`, the action is file-only.

### Pitfalls

- `stations:` is forbidden;
- `properties` is required and must contain valid keys;
- use `Ip`, not `J`.

---

## Area and Volume Reports in CSF

For each polygon, these reports use the exclusive occupied domain obtained by subtracting its direct inner polygons:

```text
A_net(p, z) = A(p, z) - sum(A(i, z) for i in direct_inners(p))
```

The weighted area contribution is:

```text
A_w(p, z) = A_net(p, z) * w(p, z)
```

The corresponding longitudinal quantities are:

```text
V_occ(p) = integral[A_net(p, z) dz]
V_hom(p) = integral[A_net(p, z) * w(p, z) dz]
```

This avoids double counting nested geometry. These actions are geometric/accounting reports; they are not beam or structural solvers.

---

### 6.6 `section_area_by_weight`

**Concept**

Produces a per-polygon net-area report at one or more absolute stations.

The report contains:

- polygon id and endpoint names;
- absolute effective weight `W`;
- exclusive area `A_net`;
- weighted contribution `A*w`;
- optional direct-inner and container information.

### Example geometry

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        square_outer:
          weight: 2.0
          vertices:
            - [-1.5, -1.5]
            - [ 1.5, -1.5]
            - [ 1.5,  1.5]
            - [-1.5,  1.5]

        square_inner_1:
          weight: 1.0
          vertices:
            - [-1.0, -1.0]
            - [ 1.0, -1.0]
            - [ 1.0,  1.0]
            - [-1.0,  1.0]

        square_inner_2:
          weight: 0.0
          vertices:
            - [-0.5, -0.5]
            - [ 0.5, -0.5]
            - [ 0.5,  0.5]
            - [-0.5,  0.5]

    S1:
      z: 10.0
      polygons:
        square_outer:
          weight: 2.0
          vertices:
            - [-1.5, -1.5]
            - [ 1.5, -1.5]
            - [ 1.5,  1.5]
            - [-1.5,  1.5]

        square_inner_1:
          weight: 1.0
          vertices:
            - [-1.0, -1.0]
            - [ 1.0, -1.0]
            - [ 1.0,  1.0]
            - [-1.0,  1.0]

        square_inner_2:
          weight: 0.0
          vertices:
            - [-0.5, -0.5]
            - [ 0.5, -0.5]
            - [ 0.5,  0.5]
            - [-0.5,  0.5]
```

### Example action file

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example: [0.0]

  actions:
    - plot_section_2d:
        stations: stations_example
        output: [stdout, out/boxes.jpg]
        params:
          show_ids: true
          show_vertex_ids: true

    - section_area_by_weight:
        stations: stations_example
        output: [stdout, out/boxesarea.csv, out/boxesarea.txt]
        params:
          group_mode: weight
          w_tol: 0.0
          include_per_polygon: true
          fmt_display: ".6f"
```

### Meaning of parameters

| Parameter | Type | Default | Meaning |
|---|---:|---:|---|
| `group_mode` | str | `"weight"` | `weight` groups by binned weight; `id` sorts by polygon id. |
| `w_tol` | float | `0.0` | Weight-bin width; raw weights are used when `<= 0`. |
| `include_per_polygon` | bool | `false` | Include direct-inner and container columns. |
| `fmt_display` | str | `".6f"` | Numeric format for stdout/text reports. |

### Example output

```text
SECTION AREA LIST REPORT at z = 0.000000
================================================================================
group_mode=weight  w_tol=0.000000

         W | id     | s0.name            | s1.name            |        A_net |          A*w | inners pols            | Container
--------------------------------------------------------------------------------
  0.000000 | [02]   | square_inner_2     | square_inner_2     |     1.000000 |     0.000000 | []                     | square_inner_1
  1.000000 | [01]   | square_inner_1     | square_inner_1     |     3.000000 |     3.000000 | ['square_inner_2']     | square_outer
  2.000000 | [00]   | square_outer       | square_outer       |     5.000000 |    10.000000 | ['square_inner_1']     | [ROOT]
--------------------------------------------------------------------------------
Occupied Total Surface: 9.000000
Homogenized area:        13.000000
```

### Notes

- `A_net` is the exclusive area of the polygon after subtraction of its direct inners;
- `W` is the absolute effective polygon weight;
- `A*w` is the weighted contribution;
- `w_tol` controls grouping only and does not alter the underlying section model.

---

### 6.6.1 `volume`

**Concept**

Integrates occupied and weighted occupied volume for each polygon between exactly two absolute stations.

### YAML

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_edges: [0.0, 10.0]

  actions:
    - volume:
        stations: stations_edges
        output: [stdout, out/boxesvolume.txt, out/boxesvolume.csv]
        params:
          n_points: 20
          fmt_display: "0.6f"
          w_tol: 0.0
```

### Parameters

| Parameter | Type | Default | Meaning |
|---|---:|---:|---|
| `n_points` | int | `20` | Number of Gauss-Legendre integration points. |
| `fmt_display` | str | `"0.6f"` | Numeric format for the report. |
| `w_tol` | float | `0.0` | Accepted and printed, but currently ignored by the calculation. |

### Expected output

```text
VOLUME POLYGON LIST REPORT at z=0.000000 and z=10.000000
========================================================================================================================
n_points=20  w_tol=0.000000

id     |         s0.w |         s1.w | weight_law         | s0.name            | s1.name            |    Volume Occupied |   Homogenized Volume
------------------------------------------------------------------------------------------------------------------------
[00]   |     2.000000 |     2.000000 | none               | square_outer       | square_outer       |          50.000000 |           100.000000
[01]   |     1.000000 |     1.000000 | none               | square_inner_1     | square_inner_1     |          30.000000 |            30.000000
[02]   |     0.000000 |     0.000000 | none               | square_inner_2     | square_inner_2     |          10.000000 |             0.000000
------------------------------------------------------------------------------------------------------------------------
Total Occupied Volume:              90.000000
Total Occupied Homogenized Volume: 130.000000
```

### Notes

- one and only one station set must be referenced;
- that station set must contain exactly two values;
- a zero-weight polygon still contributes to occupied volume but not to homogenized volume;
- this is a per-polygon accounting report, not a mechanical member analysis.

---

### 6.7 `plot_weight` (stations FORBIDDEN)

**Concept**

Plots the absolute polygon `weight` carrier along the member. Each polygon pair is sampled independently.

### YAML

```yaml
CSF_ACTIONS:
  actions:
    - plot_weight:
        output: [stdout, out/weight.jpg]
        params:
          num_points: 200
```

### Parameters

| Parameter | Type | Default | Meaning |
|---|---:|---:|---|
| `num_points` | int | `100` | Number of samples between the endpoint sections. |

### Output behavior

The requested file path is used as the base name. The action may create one or more image files with derived suffixes when the visualizer creates several polygon plots.

### Pitfalls

- `stations:` is forbidden;
- without `stdout`, the figures are file-only;
- polygons whose sampled weight is zero everywhere are omitted and reported as skipped.

---

### 6.7.1 `plot_shear_weight` (stations FORBIDDEN)

**Concept**

Plots the absolute polygon `shear_weight` carrier along the member. This action is the shear/torsion counterpart of `plot_weight`.

### YAML

```yaml
CSF_ACTIONS:
  actions:
    - plot_shear_weight:
        output: [stdout, out/shear_weight.jpg]
        params:
          num_points: 200
```

### Parameters

| Parameter | Type | Default | Meaning |
|---|---:|---:|---|
| `num_points` | int | `100` | Number of samples between the endpoint sections. |

### Output behavior and pitfalls

The output and station rules are the same as for `plot_weight`, but the plotted values are `shear_weight` rather than `weight`.

---

### 6.8 `weight_lab_zrelative` (stations REQUIRED; text-only)

**Concept**

Evaluates user-supplied weight-law expressions at relative `z` coordinates. It is a diagnostic inspector and produces no figures.

The expression environment provides:

- `w0`, `w1` - endpoint polygon weights;
- `z` - relative coordinate from the station set;
- `L` - total member length `field.s1.z - field.s0.z`;
- `np` - NumPy namespace.

### YAML

```yaml
CSF_ACTIONS:
  stations:
    z_rel: [0.0, 2.0, 4.0, 6.0]

  actions:
    - weight_lab_zrelative:
        stations: z_rel
        output: [stdout, out/weight_inspector.txt]
        weight_law:
          - "1.0"
          - "0.97 + 0.03/(1 + np.exp((z-10.0)/2.0))"
```

`weight_law` is the canonical key. The historical misspelling `weith_law` is still accepted as an alias but produces a warning.

### CLI

```bash
mkdir -p out
csf-actions geometry.yaml actions.yaml
```

### Pitfalls

- the station values are relative coordinates, not automatically normalized values in `[0, 1]`;
- keep relative `z` consistent with `L`;
- `weight_law` must be a non-empty string or list of non-empty strings;
- this action uses the endpoint polygon pairs by index.

---

### 6.9 `export_yaml` (stations REQUIRED; FILE-ONLY)

**Concept**

Exports a new CSF geometry YAML resolved at exactly two stations.

### YAML

```yaml
CSF_ACTIONS:
  stations:
    subpart: [1.0, 8.0]

  actions:
    - export_yaml:
        stations: subpart
        output: [out/subpart.yaml]
```

### CLI

```bash
mkdir -p out
csf-actions geometry.yaml actions.yaml
```

### Pitfalls

- exactly one station set must be referenced;
- that station set must contain exactly two values;
- `stdout` is forbidden;
- exactly one `.yaml` or `.yml` output path is required;
- no action-specific parameters are defined.

---

### 6.10 `write_opensees_geometry` (stations FORBIDDEN; FILE-ONLY)

**Concept**

Writes one Tcl geometry/section file for downstream OpenSees workflows. The exporter generates its station list internally from `n_points`.

### YAML

```yaml
CSF_ACTIONS:
  actions:
    - write_opensees_geometry:
        output: [out/geometry.tcl]
        params:
          n_points: 10
          E_ref: 2.1e+11
          nu: 0.30
```

### Parameters

| Parameter | Type | Required | Default | Meaning |
|---|---:|:---:|---:|---|
| `n_points` | int | yes | - | Number of generated integration/sampling stations. |
| `E_ref` | float | no | `null` | Optional reference Young modulus passed to the exporter. |
| `nu` | float | no | `null` | Optional Poisson ratio passed to the exporter. |

### CLI

```bash
mkdir -p out
csf-actions geometry.yaml actions.yaml
```

### Pitfalls

- `stations:` is forbidden;
- `stdout` is forbidden;
- exactly one `.tcl` output is required;
- `n_points` is required;
- use numeric YAML values for `E_ref` and `nu`.

---

# `write_sap2000_geometry` alias `export_model` - Action Reference

### 6.11 `write_sap2000_geometry` alias `export_model`

**Concept**

Exports a structured plain-text template pack containing section-property tables. The output can support SAP2000, OpenSeesPy, or another external beam solver, but it is not presented as a directly importable SAP2000 `.s2k` file.

For full output-format documentation, see [`write_sap2000_template_pack.md`](write_sap2000_template_pack.md).

**Station generation**

Two modes are available:

1. **Explicit station-set mode**
   - provide `stations: one_station_set` at action level;
   - the set must contain at least three absolute, strictly increasing `z` values;
   - `n_intervals` is not used to generate the export stations.

2. **Gauss-Lobatto mode**
   - omit `stations:`;
   - provide `params.n_intervals`;
   - the exporter generates `n_intervals + 1` stations.

### YAML - Gauss-Lobatto mode

```yaml
CSF_ACTIONS:
  actions:
    - write_sap2000_geometry:
        output: [out/sap_template.txt]
        params:
          n_intervals: 6
          material_name: "S355"
          E_ref: 2.1e+11
          nu: 0.30
          mode: "BOTH"
          include_plot: true
          plot_filename: "out/section_variation.png"
```

The alias is equivalent:

```yaml
CSF_ACTIONS:
  actions:
    - export_model:
        output: [out/sap_template.txt]
        params:
          n_intervals: 6
          include_plot: false
```

### YAML - explicit station-set mode

```yaml
CSF_ACTIONS:
  stations:
    export_stations: [0.0, 2.5, 5.0, 7.5, 10.0]

  actions:
    - write_sap2000_geometry:
        stations: export_stations
        output: [out/sap_template.txt]
        params:
          material_name: "S355"
          E_ref: 2.1e+11
          nu: 0.30
          mode: "BOTH"
          include_plot: true
          plot_filename: "out/section_variation.png"
```

`z_values` is an internal argument of the underlying Python exporter; it is **not** an accepted CSFActions YAML parameter. Explicit YAML stations must be supplied through the action-level `stations:` field.

### Parameters

| Parameter | Type | Default | Description |
|---|---:|---:|---|
| `n_intervals` | int | `null` | Required only when `stations:` is omitted. Must be `>= 1`. |
| `E_ref` | float | `null` | Optional reference value written in the export header. |
| `nu` | float | `null` | Optional reference Poisson ratio written in the export header. |
| `material_name` | str | `"S355"` | Informational material label. |
| `mode` | str | `"BOTH"` | `CENTROIDAL_LINE`, `REFERENCE_LINE`, or `BOTH`. |
| `include_plot` | bool | `true` | Save a preview image of property variation. |
| `plot_filename` | str | `"section_variation.png"` | Preview image path. |

`show_plot`, `z_values`, `plot_n`, and `float_fmt` are not exposed as CSFActions YAML parameters.

### CLI

```bash
mkdir -p out
csf-actions geometry.yaml actions.yaml
```

### Pitfalls

- `stdout` is forbidden;
- exactly one template output path is required;
- when explicit stations are used, exactly one station set must be referenced and it must contain at least three strictly increasing values;
- when stations are omitted, `n_intervals` is mandatory;
- the only action alias is `export_model`.

---

## 7. Action reference table (parameters, defaults, outputs)

> Envelope fields (`stations`, `output`, `params`) apply to all actions, subject to the per-action rules below.

| Action | Stations | Extra keys outside `params` | Parameters | Output behavior |
|---|---|---|---|---|
| `section_selected_analysis` | REQUIRED | `properties` required; accepts numerical keys and optional `geometry` | `fmt_display` str -> `.8f` | stdout report; CSV table; text report |
| `plot_section_2d` | REQUIRED | - | `show_ids` bool -> true; `show_weights` bool -> true; `show_vertex_ids` bool -> false; `show_legenda` bool -> true; `title` str -> null; `dpi` int -> 150 | deferred display and/or composite image |
| `plot_volume_3d` | FORBIDDEN | - | `show_end_sections` bool -> true; `line_percent` float -> 100.0; `seed` int/str -> 0; `title` str -> default title; `equalize_z` bool -> false | interactive stdout only; no file output |
| `plot_properties` | FORBIDDEN | `properties` required | `num_points` int -> 100 | deferred display and/or image |
| `plot_weight` | FORBIDDEN | - | `num_points` int -> 100 | deferred display and/or derived image files |
| `plot_shear_weight` | FORBIDDEN | - | `num_points` int -> 100 | deferred display and/or derived image files |
| `weight_lab_zrelative` | REQUIRED, relative z | `weight_law` required; `weith_law` legacy alias | none | text-only stdout and/or files |
| `section_area_by_weight` | REQUIRED | - | `group_mode` str -> `weight`; `w_tol` float -> 0.0; `include_per_polygon` bool -> false; `fmt_display` str -> `.6f` | stdout, CSV, and/or text |
| `volume` | REQUIRED; one set with exactly 2 z values | - | `n_points` int -> 20; `fmt_display` str -> `0.6f`; `w_tol` float -> 0.0, currently unused | stdout, CSV, and/or text |
| `export_yaml` | REQUIRED; one set with exactly 2 z values | - | none | file-only; exactly one YAML path |
| `write_opensees_geometry` | FORBIDDEN | - | `n_points` int required; `E_ref` float optional; `nu` float optional | file-only; exactly one `.tcl` path |
| `write_sap2000_geometry` / `export_model` | OPTIONAL; one explicit set or omitted | - | `n_intervals` conditionally required; `E_ref`, `nu` optional; `material_name` -> `S355`; `mode` -> `BOTH`; `include_plot` -> true; `plot_filename` -> `section_variation.png` | file-only; exactly one template path |

---

## 8. Common pitfalls (and how to avoid them)

### 8.1 YAML typos and indentation

- YAML is indentation-sensitive; use spaces, not tabs.
- `actions:` must contain a list:

```yaml
CSF_ACTIONS:
  actions:
    - plot_volume_3d:
        params:
          seed: w
```

Do not use an alternative schema such as `- action: plot_volume_3d`; CSFActions expects the action name as the single mapping key.

### 8.2 Duplicate keys

Keep one `actions:` block and one occurrence of each mapping key. Duplicate YAML keys are rejected.

### 8.3 Output directories

Create all output directories before validation:

```bash
mkdir -p out
```

### 8.4 `z` values outside the geometry domain

For absolute station actions, keep values inside the CSF endpoint domain. `weight_lab_zrelative` is the exception because its station values are relative.

### 8.5 Scientific notation

Prefer explicit numeric notation such as:

```yaml
E_ref: 2.1e+11
```

### 8.6 Canonical names

Use:

- `Ip`, not `J`;
- `weight_lab_zrelative`, not `weight_law_zrelative`;
- `write_sap2000_geometry` or `export_model`, not `write_samp2000_geometry`;
- `weight_law`, not the legacy alias `weith_law`.

---

## 9. FAQ (frequent errors and what they mean)

CSFActions reports controlled validation errors and, for YAML structure errors, a source snippet with a caret.

### Q1) “Missing root key CSF_ACTIONS”

Your file must start with:

```yaml
CSF_ACTIONS:
```

### Q2) “actions must be a list”

Correct form:

```yaml
CSF_ACTIONS:
  actions:
    - plot_volume_3d:
        params:
          seed: w
```

### Q3) “Unknown action …”

Run:

```bash
csf-actions --help-actions
```

and copy an implemented action name exactly.

### Q4) “stations is not allowed for this action”

Remove `stations:` from actions that sample internally or use endpoint geometry.

### Q5) “properties missing / unknown property key”

Provide a non-empty `properties:` list and use the keys in Section 6.2 or the reference table.

### Q6) “stdout not allowed”

The selected action is file-only. Remove `stdout` and provide exactly one file path.

### Q7) “Output is not writable”

The parent directory is missing, the path is invalid, or permissions do not allow writing.

### Q8) “Param missing / param type / param range”

Check the parameter spelling, location under `params:`, type, conditional requirements, and allowed range.

### Q9) Why did `weith_law` produce a warning?

It is a backward-compatible alias. Rename it to the canonical key:

```yaml
weight_law:
  - "1.0"
```

### Q10) How do I provide explicit SAP2000 export stations?

Use the action-level `stations:` field:

```yaml
stations:
  export_stations: [0.0, 5.0, 10.0]

actions:
  - write_sap2000_geometry:
      stations: export_stations
      output: [out/export.txt]
```

Do not put `z_values` under `params:`.

---

## 10. Naming conventions (recommended)

These conventions are not enforced, but improve readability.

### 10.1 Station set names

Use lowercase names with underscores:

```text
z_endpoints
z_fine
dense_near_support
export_stations
```

### 10.2 Output files

Use a dedicated output directory and descriptive names:

```text
out/selected_properties.csv
out/section_plots.png
out/weight_inspector.txt
out/geometry.tcl
out/sap_template.txt
```

### 10.3 Polygons

Use stable names without spaces, for example:

```text
web
flange_top
flange_bottom
void_1
pcbar_00
```

Corresponding endpoint polygons are paired by model topology/order; stable names still improve traceability.

---

## 11. Checklist before running

1. `geometry.yaml` exists and is valid.
2. `actions.yaml` has the root key `CSF_ACTIONS:`.
3. `actions:` is a non-empty list and appears only once.
4. Every action name is implemented.
5. All referenced station sets exist.
6. Station rules for each action are respected.
7. `properties:` uses accepted keys.
8. Action-specific options are placed under `params:`.
9. File-only actions have exactly one valid file output and no `stdout`.
10. All output directories already exist.
11. Run validation before a long workflow:

```bash
csf-actions geometry.yaml actions.yaml --validate-only
```

12. Execute the workflow:

```bash
csf-actions geometry.yaml actions.yaml
```
