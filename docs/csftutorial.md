# CSF YAML Tutorial (CSFActions.py)
Although CSF is implemented as a Python engine, it can be used **without programming** through the **CSFReader** tool.
In these tutorials, the working directory is set **immediately after cloning** the repository.

> **[rectangle/](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/rectangle)  Complete worked example covering all available actions on a tapered rectangular section — plots, reports, solver exports, and three weight law alternatives. Run with `python3 -m csf.CSFActions geometry.yaml actions.yaml`.**


After the installation, create your case folder structure (outside or inside the repo, depending on your workflow), for example:

```text
mkdir mycase
cd mycase

mycase/
  geometry.yaml
  actions.yaml
  out/                # create this folder yourself
```

1. **`geometry.yaml`** — defines the member geometry as a continuous field along the axis `z`  
   - end (or intermediate) sections as **arbitrary polygons**  
   - optional multi-polygon sections (multi-cell shapes)  
   - per-polygon metadata (e.g., weights for multi-material / void logic)

2. **`actions.yaml`** — declares *what CSF must do* (no code required)  
   - compute section properties and derived stiffness/mass fields  
   - produce plots/visualizations and reports  
   - export solver-ready station data (e.g., for force-based beam formulations)


**Important**: CSFActions checks that output paths are writable, but it does **not** create missing folders for you.  
Create `out/` (and any subfolders) before running.

### 1. Minimal `action.yaml`

This example runs one analysis at three stations and prints to screen + writes a CSV.

**action.yaml**:

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
          title: "Ruled volume"
    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
        properties: [A, Cx, Cy, Ix, Iy]
```

**geometry.yaml**:


```yaml
CSF:
  # Two stations defining a linearly tapered solid rectangle along z.
  # Rectangle width is constant; height changes from S0 to S1.
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            # CCW vertices
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
            # CCW vertices
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 2.0]
            - [-0.5, 2.0]
```
### 1.1 CLI command

From inside `my_case/`:

```bash
csf-actions geometry.yaml actions.yaml
```

### 1.2 Expected output

what you will see
![Figure_1](https://github.com/user-attachments/assets/2f4daf1a-e309-4834-9499-d43fa3d9d087)

```
## SECTION SELECTED ANALYSIS @ z = 0.0 ###
torsion_alpha_sv     : 1.00000000  [Solid J_sv scaling factor]
A                   : 1.00000000  [Total net cross-sectional area]
Cx                  : 0.00000000  [Horizontal centroid (X)]
Cy                  : 0.50000000  [Vertical centroid (Y)]
Ix                  : 0.08333333  [Second moment about centroidal X-axis]
Iy                  : 0.08333333  [Second moment about centroidal Y-axis]

### SECTION SELECTED ANALYSIS @ z = 1.0 ###
torsion_alpha_sv     : 1.00000000  [Solid J_sv scaling factor]
A                   : 1.10000000  [Total net cross-sectional area]
Cx                  : 0.00000000  [Horizontal centroid (X)]
Cy                  : 0.55000000  [Vertical centroid (Y)]
Ix                  : 0.11091667  [Second moment about centroidal X-axis]
Iy                  : 0.09166667  [Second moment about centroidal Y-axis]

### SECTION SELECTED ANALYSIS @ z = 10.0 ###
torsion_alpha_sv     : 1.00000000  [Solid J_sv scaling factor]
A                   : 2.00000000  [Total net cross-sectional area]
Cx                  : 0.00000000  [Horizontal centroid (X)]
Cy                  : 1.00000000  [Vertical centroid (Y)]
Ix                  : 0.66666667  [Second moment about centroidal X-axis]
Iy                  : 0.16666667  [Second moment about centroidal Y-axis]
All actions completed successfully.
        ...
```

---

### 2 `actions.yaml` (execution plan)

The `actions.yaml` file must contain a single top-level root key:

```yaml
CSF_ACTIONS:
  stations: ...
  actions: ...
```

#### Required keys

- `CSF_ACTIONS:` (root mapping)
- `actions:` **required** (must be a list)
- `stations:` required for many actions (see per-action rules)

#### Rule: `actions:` must appear only once

YAML duplicate keys can overwrite silently in some tools.  
CSFActions prevents this: **duplicate keys raise a controlled error** with a caret/snippet.

---

## 3. Stations (what they are, how they work)

Stations are named lists of `z` coordinates.

```yaml
stations:
  station_name:
    - 0.0
    - 1.0
    - 10.0
```

### 3.1 Station semantics

- For most actions, station values are **absolute z coordinates** and must be inside the CSF domain.
- For `weight_lab_zrelative`, station values are treated as **relative z** (user responsibility).

### 3.2 Station sets are reusable

You can define multiple station sets and reference them in different actions:
**action**
```yaml
  stations:
    stations_example:
      - 0.0
      - 1.0
      - 10.0

actions:
    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
        properties: [A, Cx, Cy, Ix, Iy]
```

**geometry**

```yaml

CSF:
  # Two stations defining a linearly tapered solid rectangle along z.
  # Rectangle width is constant; height changes from S0 to S1.
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            # CCW vertices
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
            # CCW vertices
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 2.0]
            - [-0.5, 2.0]
```

---

## 4. Output rules (stdout vs file-only)

Each action may have an `output:` list. If `output` is **missing**, the default is:

```yaml
output: [stdout]
```

### 4.1 File-only behavior

If `output:` exists but does **not** contain `stdout`, the action runs in **file-only mode**:
- no on-screen output
- only files are written

When file outputs are specified, the **output format is inferred from the file extension** (for example `.csv` for CSV tables, `.txt` for plain text reports).

Example:

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
          title: "Ruled volume"

    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
          - out/results.csv   # CSV table output
          - out/report.txt    # plain text report
        properties: [A, Cx, Cy, Ix, Iy]

```

The output directory (e.g. out/) is not created automatically and must already exist.

---
## 4.2 Geometry export in `properties`

The keyword `geometry` can be added to the `properties` list to export
the **section geometry at each evaluated station**.

When `geometry` is present, CSF exports the polygon vertices
corresponding to the evaluated section together with the requested
section properties. This keeps the **numerical results and the geometry
that generated them** in the same output.

The use of `geometry` is **optional**.\
If only section properties are required, it can simply be omitted.

Example:

``` yaml
CSF_ACTIONS:
  actions:
    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
          - out/results.csv
          - out/report.txt
        properties: [geometry, A, Cx, Cy, Ix, Iy]
```

------------------------------------------------------------------------

### Example output

#### `out/report.txt`

    ### SECTION SELECTED ANALYSIS @ z = 0.0 ###
    A                   : 1.00000000  [Total net cross-sectional area]
    Cx                  : 0.00000000  [Horizontal centroid (X)]
    Cy                  : 0.50000000  [Vertical centroid (Y)]
    Ix                  : 0.08333333  [Second moment about centroidal X-axis]
    Iy                  : 0.08333333  [Second moment about centroidal Y-axis]

    ## GEOMETRY EXPORT ##
    # z=0.0
    idx_polygon,idx_container,s0_name,s1_name,w,vertex_i,x,y
    0,,rect,rect,1.00000000,0,-0.50000000,0.00000000
    0,,rect,rect,1.00000000,1,0.50000000,0.00000000
    0,,rect,rect,1.00000000,2,0.50000000,1.00000000
    0,,rect,rect,1.00000000,3,-0.50000000,1.00000000

------------------------------------------------------------------------

#### `out/results.csv`

    z,A,Cx,Cy,Ix,Iy
    0.00000000,1.00000000,0.00000000,0.50000000,0.08333333,0.08333333
    1.00000000,1.10000000,0.00000000,0.55000000,0.11091667,0.09166667
    10.00000000,2.00000000,0.00000000,1.00000000,0.66666667,0.16666667

    ## GEOMETRY EXPORT ##
    # z=0.0
    idx_polygon,idx_container,s0_name,s1_name,w,vertex_i,x,y
    0,,rect,rect,1.00000000,0,-0.50000000,0.00000000
    0,,rect,rect,1.00000000,1,0.50000000,0.00000000
    0,,rect,rect,1.00000000,2,0.500000000,1.00000000
    0,,rect,rect,1.00000000,3,-0.50000000,1.00000000

---

**Note**

- The exported `w` value is the **absolute polygon weight at that station**.
---

# 4.3 Minimal example: geometry, weight law, and action file

This example shows:

- where to place the `weight_laws` section in the geometry YAML
- a simple quadratic weight law along the member
- an action YAML to visualize the member, inspect selected stations, and plot the weight variation

## Geometry YAML

```yaml
CSF:
  # Two stations defining a linearly tapered solid rectangle along z.
  # Rectangle width is constant; height changes from S0 to S1.
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            # CCW vertices
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
            # CCW vertices
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

- `rect,rect` identifies the polygon pair between `S0` and `S1`
- `z` is the longitudinal coordinate
- `L` is the element length
- the law defines an absolute polygon weight `w`

In this example:

- at `z = 0`, `w = 1.0`
- at `z = L`, `w = 0.7`

## Action YAML

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
          title: "Ruled volume"

    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
          - out/results.csv
          - out/report.txt
        properties: [geometry, A, Cx, Cy, Ix, Iy]

    - plot_weight:
        output:
          - stdout
          - out/weight.jpg
```

## What these actions do

- `plot_volume_3d` plots the ruled member volume
- `section_selected_analysis` evaluates the selected stations and writes:
  - section properties
  - geometry export if `geometry` is included in `properties`
  - optional CSV and text outputs
- `plot_weight` plots the longitudinal weight variation

## Notes

- `geometry` is optional in `properties`
- the exported `w` value is the absolute polygon weight at each station
- output directories such as `out/` are not created automatically


---
## 5. Useful CLI options

### 5.1 Validate only (no execution)

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml --validate-only
```

Expected snippet:

```
Actions file validated successfully.
Validation-only mode: no actions executed.
```

### 5.2 Print built-in help for actions

```bash
 python3 -m csf.CSFActions --help-actions
```

This prints:
- the current action catalog
- per-action notes (stations required/forbidden)
- output behavior notes
- allowed property keys documentation

---

## 6. One per main action

Each tutorial includes:
- concept
- small YAML
- CLI command
- short expected output snippet
- common pitfalls

> In all examples below, assume `geometry.yaml` exists and is valid.

---

**Pitfalls**
- `stations` missing → error (most actions need it).
- `out/` does not exist → output file error.
- station `z` outside the geometry domain → error.

---

### 6.2 `section_selected_analysis` (extended property list example)

**Concept**  
Computes only the property keys explicitly listed in `properties`.

This example mainly shows a **broader set of available property keys**.  
Earlier examples already illustrate the general usage with a shorter property list.

Note that some torsional indicators such as `J_sv_cell` and `J_sv_wall` may appear as **zero** if no `@cell` or `@wall` polygons are defined in the geometry.

---

### YAML

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example:
      - 0.0
      - 1.0
      - 10.0

  actions:
    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
          - out/results.csv
          - out/report.txt
        properties: [A, Cx, Ix, Iy, Ip, I1, I2, Cy, rx, ry, Ixy, Wx, Wy, K_torsion, Q_na, J_sv_cell, J_sv_wall, J_s_vroark, J_s_vroark_fidelity]
```

---

### CLI

```bash
mkdir -p out
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

---

### Example output (snippet)

```
### SECTION SELECTED ANALYSIS @ z = 0.0 ###
A   : 1.00000000
Cx  : 0.00000000
Ix  : 0.08333333
Iy  : 0.08333333
Ip  : 0.16666667
J_sv_cell : 0.00000000
J_sv_wall : 0.00000000
```

`J_sv_cell` and `J_sv_wall` are zero here because no polygons are marked with
`@cell` or `@wall`. These terms are evaluated only when the corresponding
thin‑wall models are explicitly defined in the geometry.

---

### Notes

- Only the keys listed in `properties` are computed and exported.
- Use a short list for compact reports.
- Use a longer list when a broader property report is required.

---

### Pitfalls

- `properties` missing or empty → error.
- Unknown keys (e.g. `Ixx` instead of `Ix`) → error.
- YAML strings with accidental extra characters are treated as different keys and rejected.
---

### 6.3 `plot_section_2d` (stations REQUIRED)

**Concept**  
Plots the 2D section geometry at each requested station.  
If you save an image and request multiple stations, CSFActions can generate one **stacked composite image**.

The output directory (for example `out/`) must already exist.

---

### YAML

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example:
      - 0.0
      - 1.0
      - 10.0
    stations_edges:
      - 0.0
      - 10.0

  actions:
    - plot_volume_3d:
        params:
          line_percent: 100.0
          title: " - mycase 3D -"

    - section_selected_analysis:
        stations: stations_example
        output:
          - stdout
          - out/results.csv
          - out/report.txt
        properties: [A, Cx, Ix, Iy, Ip, I1, I2, Cy, rx, ry, Ixy, Wx, Wy, K_torsion, Q_na, J_sv_cell, J_sv_wall, J_s_vroark, J_s_vroark_fidelity]

    - plot_weight:
        output:
          - stdout
          - out/weight.jpg

    - plot_section_2d:
        stations: stations_edges
        show_ids: true
        show_vertex_ids: true
        output:
          - [stdout, out/sections.png]
```

---

### CLI

```bash
mkdir -p out
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

---

### Expected output snippet

```text
[OK] plot_section_2d: created 2 plot(s)
[OK] saved image: out/sections.png
```

---

### Pitfalls

- `stations` is required.
- The output directory (for example `out/`) is not created automatically.
- In headless environments, prefer file output instead of interactive display only.
```
---

### 6.4 `plot_volume_3d` (stations FORBIDDEN)

**Concept**  
Shows a 3D ruled “volume” between end sections. This action uses the **endpoints** only.


**YAML**

```yaml
CSF_ACTIONS:
  actions:
    - plot_volume_3d:
        output: [stdout]
        params:
          show_end_sections: true
          line_percent: 50.0
          seed: 0
          title: "CSF volume"
```

**CLI**

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

**Expected output snippet**

```
[OK] plot_volume_3d scheduled (display at end)
```

**Pitfalls**
- If you add `stations:` → error (forbidden).
- This is display-oriented; do not expect file output.

---
### 6.5 `plot_properties` (stations FORBIDDEN)

**Concept**  
Plots selected properties along the member, sampling `num_points` between endpoints (stations are not allowed because the plot uses continuous sampling).

**YAML**

```yaml

CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example:
      - 0.0
      - 1.0
      - 10.0
    stations_edges:
      - 0.0
      - 10.0

  actions:
    - plot_volume_3d:
        params:
          line_percent: 100.0
          title: " - mycase 3D -"
    - plot_properties:
        output: [stdout, out/properties.png]
        properties: [A, Ix, Iy]
        params:
          num_points: 100          

```

**CLI**

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

**Expected output snippet**

```
[OK] plot_properties scheduled
[OK] saved: out/properties.png
```

**Pitfalls**
- `properties` missing → error.
- If you omit `stdout` from output, the plot is not shown (file-only).
---

### 6.6 `section_area_by_weight`

**Concept**

Produces an **accountant-style geometric area listing** at selected stations.

The report lists each declared polygon with:

- its **geometric area** `A_net`
- its **absolute weight** `W`
- the weighted contribution `A*w`
- the **topological nesting** (container / inner polygons)

Two totals are reported:

- **Occupied Total Surface** = sum of geometric polygon areas
- **Homogenized area** = sum of `A_net * w_abs`

This action is **purely geometric/accounting oriented** and does not compute
mechanical section properties.

---

### Example geometry

```yaml
CSF:
  # Constant-section prismatic member from S0 to S1.
  #
  # The section is made of three concentric nested squares:
  #
  # - square_outer:
  #   outermost square, absolute weight = 2.0
  #
  # - square_inner_1:
  #   square fully inside square_outer, absolute weight = 1.0
  #
  # - square_inner_2:
  #   square fully inside square_inner_1, absolute weight = 0.0
  #
  # Geometrically, all three polygons are declared explicitly.
  # Therefore:
  # - the occupied geometric area/volume includes all declared polygons
  # - the homogenized contribution of each polygon is its own geometry
  #   multiplied by its own absolute weight
  #
  # Since S0 and S1 are identical, the member is a parallelepiped
  # with constant cross-section along z.

  sections:
    S0:
      # Start section at z = 0
      z: 0.0
      polygons:

        square_outer:
          # Outermost square
          # Absolute weight = 2.0
          # Side = 3.0
          weight: 2.0
          vertices:
            # CCW vertices
            - [-1.5, -1.5]
            - [ 1.5, -1.5]
            - [ 1.5,  1.5]
            - [-1.5,  1.5]

        square_inner_1:
          # Intermediate square, fully contained in square_outer
          # Absolute weight = 1.0
          # Side = 2.0
          weight: 1.0
          vertices:
            # CCW vertices
            - [-1.0, -1.0]
            - [ 1.0, -1.0]
            - [ 1.0,  1.0]
            - [-1.0,  1.0]

        square_inner_2:
          # Innermost square, fully contained in square_inner_1
          # Absolute weight = 0.0
          # Side = 1.0
          weight: 0.0
          vertices:
            # CCW vertices
            - [-0.5, -0.5]
            - [ 0.5, -0.5]
            - [ 0.5,  0.5]
            - [-0.5,  0.5]

    S1:
      # End section at z = 10
      # Geometry is identical to S0, so there is no shape variation along z
      z: 10.0
      polygons:

        square_outer:
          # Same outer square as S0
          weight: 2.0
          vertices:
            # CCW vertices
            - [-1.5, -1.5]
            - [ 1.5, -1.5]
            - [ 1.5,  1.5]
            - [-1.5,  1.5]

        square_inner_1:
          # Same intermediate square as S0
          weight: 1.0
          vertices:
            # CCW vertices
            - [-1.0, -1.0]
            - [ 1.0, -1.0]
            - [ 1.0,  1.0]
            - [-1.0,  1.0]

        square_inner_2:
          # Same inner square as S0
          weight: 0.0
          vertices:
            # CCW vertices
            - [-0.5, -0.5]
            - [ 0.5, -0.5]
            - [ 0.5,  0.5]
            - [-0.5,  0.5]
```

---

### Example action file

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example:
      - 0.0
    stations_edges:
      - 0.0
      - 10.0

  actions:

    - plot_section_2d:
        stations: stations_example
        show_ids: true
        show_vertex_ids: true
        output:
          - [stdout, out/boxes.jpg]

    - section_area_by_weight:
        stations: stations_example
        output:
          - [stdout, out/boxesarea.csv, out/boxesarea.txt]
        params:
          w_tol: 0.0
          include_per_polygon: True
```

---

### Meaning of parameters

| Parameter | Meaning |
|-----------|--------|
| `w_tol` | grouping tolerance for weight bins (purely for reporting) |
| `include_per_polygon` | prints one line per polygon with nesting information |

---

### Example output 

```
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
---

### Notes

- `A_net` is the **geometric area of the declared polygon**, not the composed net section.
- `W` is the **absolute polygon weight**.
- `A*w` represents the **weighted contribution** used for accounting or material estimation.

---

### 6.6.1 `volume`

**Concept**  
Computes the geometric and homogenized volume of the member between the selected edge stations.

The action reports:

- **Occupied Volume**: geometric volume of each declared polygon
- **Homogenized Volume**: occupied volume multiplied by the polygon absolute weight `w`

This action is intended for **geometric/accounting summaries**, not for mechanical section-property evaluation.

---

### YAML

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example:
      - 0.0
    stations_edges:
      - 0.0
      - 10.0

  actions:
    - plot_section_2d:
        stations: stations_example
        show_ids: true
        show_vertex_ids: true
        output:
          - [stdout, out/boxes.jpg]

    - volume:
        stations: stations_edges
        output:
          - stdout
          - [out/boxesvolume.txt]
        params:
          n_points: 200
          fmt_display: ".6f"
          w_tol: 0.0
```

---

### CLI

```bash
mkdir -p out
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

---

### Meaning of parameters

- `stations`: must contain the two edge stations that define the integration interval
- `n_points`: number of Gauss-Legendre integration points
- `fmt_display`: numeric format used in the printed report
- `w_tol`: currently accepted for interface consistency, but ignored by this action

---

### Expected output

```text
VOLUME POLYGON LIST REPORT at z=0.000000 and z=10.000000
========================================================================================================================
n_points=200  w_tol=0.000000

id     |         s0.w |         s1.w | weight_law         | s0.name            | s1.name            |    Volume Occupied |   Homogenized Volume
------------------------------------------------------------------------------------------------------------------------
[00]   |     2.000000 |     2.000000 | none               | square_outer       | square_outer       |          50.000000 |           100.000000
[01]   |     1.000000 |     1.000000 | none               | square_inner_1     | square_inner_1     |          30.000000 |            30.000000
[02]   |     0.000000 |     0.000000 | none               | square_inner_2     | square_inner_2     |          10.000000 |             0.000000
------------------------------------------------------------------------------------------------------------------------
Total Occupied Volume:           90.000000
Total Occupied Homogenized Volume: 130.000000

```

---

### Notes

- `Volume Occupied` is the geometric volume of the declared polygon.
- `Homogenized Volume` is computed using the polygon **absolute weight**.
- A polygon with `w = 0` still contributes to the occupied geometric volume, but contributes `0` to the homogenized volume.
- The output directory is not created automatically.

---

### Pitfalls

- `stations` should identify the start and end of the volume interval.
- `w_tol` is currently unused and may appear only as a header/report parameter.
- Do not interpret this report as a composed mechanical result; it is a per-polygon geometric/homogenized volume report.
---
### 6.7 `plot_weight` (stations FORBIDDEN)

**Concept**  
Plots interpolated polygon weights along the member (one curve per polygon).
**Note**

If no additional law is specified, the longitudinal variation of section properties is **linear**, as defined by the interpolation of the geometry between the stations declared in the `geometry` file.

**YAML**

```yaml
CSF_ACTIONS:
  version: 0.1
  # station not required neither for  plot_volume_3d nor plot_weight
  stations:
    stations_example:
      - 0.0
      - 1.0
      - 10.0
    stations_edges:
      - 0.0
      - 10.0

  actions:

        
    - plot_weight:
        output:
          - stdout
          - out/weight.jpg        
        params:
            num_points: 200
```

geometry

```yaml

CSF:
  # Two stations defining a linearly tapered solid rectangle along z.
  # Rectangle width is constant; height changes from S0 to S1.
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
          weight: 1.0
          vertices:
            # CCW vertices
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
            # CCW vertices
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 2.0]
            - [-0.5, 2.0]
  weight_laws:
    - 'rect,rect: 1.0 - 0.3*(z/L)*(z/L)'     
    
```



**CLI**

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

**Expected output snippet**

```
[OK] plot_weight scheduled
[OK] saved: out/weight.png
```

**Pitfalls**
- Same as `plot_properties` for output/show behavior.

---

### 6.8 `weight_lab_zrelative` (stations REQUIRED; text-only)

**Concept**  
Evaluates user weight-law expressions at **relative z** values (your station list is interpreted as relative).  
This is an inspector to verify weight formulas without writing Python.

**YAML**

```yaml
CSF_ACTIONS:
  stations:
    z_rel: [0.0, 2.0, 4.0, 6.0]

  actions:
    - weight_lab_zrelative:
        stations: [z_rel]
        output: [stdout, out/weight_inspector.txt]
        weith_law:
          - "1.0"
          - "0.97 + 0.03/(1 + np.exp((z-10.0)/2.0))"
```

**CLI**

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

```

**Pitfalls**
- The key name is `weith_law` (spelling is enforced by the current runner).
- Relative-z meaning is your responsibility (keep consistent with your element length `L`).

---

### 6.9 `export_yaml` (stations REQUIRED; FILE-ONLY)

**Concept**  
Exports a new CSF geometry YAML built from **exactly two** stations (z0 and z1).

**YAML**

```yaml
CSF_ACTIONS:
  stations:
    subpart: [1.0, 8.0]   # MUST be exactly two values

  actions:
    - export_yaml:
        stations: [subpart]
        output: [out/subpart.yaml]
```

**CLI**

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

**Expected output snippet**

```
[OK] export_yaml: wrote out/subpart.yaml
```

**Pitfalls**
- Station set must contain **exactly 2** z values.
- `stdout` is not allowed for this action.
- Output must be exactly **one** YAML file path.

---

### 6.10 `write_opensees_geometry` (stations FORBIDDEN; FILE-ONLY)

**Concept**  
Writes a Tcl file with stations + Elastic sections for downstream OpenSees workflows.

**YAML**

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

**CLI**

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

**Expected output snippet**

```
[OK] write_opensees_geometry: wrote out/geometry.tcl
```

**Pitfalls**
- `stations` is forbidden.
- `stdout` is forbidden.
- Use `2.1e+11` (with `+`) to avoid YAML parsing edge cases.

---


# `write_sap2000_geometry` — Action Reference

### 6.11 `write_sap2000_geometry`

**Concept**

Exports a CSF field to a structured plain-text file containing four fixed-width
tables of section properties evaluated at the requested stations. The output is a
**general-purpose solver export** — it can be used as input for SAP2000, OpenSeesPy,
or any beam solver that accepts tabular section data.

For full documentation of the output format, column definitions, and downstream use,
see: [`write_sap2000_template_pack` — Reference Documentation](write_sap2000_template_pack.md).

**Station generation**

Two modes are available:

- **`z_values` provided** — stations are evaluated at the explicit list of z-coordinates.
  `n_intervals` is ignored. Values must be strictly increasing and within field bounds.
- **`z_values` not provided** — stations are the `n_intervals + 1` Gauss-Lobatto nodes
  over `[z_start, z_end]`. These are the correct integration points for
  `forceBeamColumn` elements in OpenSeesPy.

**YAML**

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

To use explicit stations instead of Lobatto:

```yaml
        params:
          z_values: [0.0, 2.5, 5.0, 7.5, 10.0]
          material_name: "S355"
          E_ref: 2.1e+11
          nu: 0.30
```

**CLI**

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

**Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_intervals` | `int` | `20` | Gauss-Lobatto intervals; stations = `n_intervals + 1`. Ignored when `z_values` is provided. |
| `material_name` | `str` | `"S355"` | Informational material label written to the file header. |
| `E_ref` | `float` | — | Reference Young's modulus. Required with `nu` to populate the `G_ref` column. |
| `nu` | `float` | — | Poisson's ratio. Used to derive `G_ref = E_ref / (2*(1+nu))`. |
| `mode` | `str` | `"BOTH"` | Retained for API compatibility; not used in output. |
| `include_plot` | `bool` | `True` | If `True`, saves a plot of section property variation along z. |
| `plot_filename` | `str` | `"section_variation.png"` | Output path for the property plot. |
| `show_plot` | `bool` | `False` | If `True`, displays the plot interactively. |
| `z_values` | `list` | — | Explicit station list. Overrides `n_intervals` when provided. |
| `float_fmt` | `str` | `".9g"` | Format spec for all numeric output fields. |

**Notes**

- `E_ref` and `nu` must be provided **together** to populate the `G_ref` column.
  If either is missing, `G_ref` is blank in the output — the file is still valid
  for SAP2000 (material defined separately) but requires `MATERIAL_INPUT_MODE='override'`
  in `csf_template_pack_opensees.py`.
- `E_ref` and `nu` are solver input parameters only, independent of the CSF weight
  laws `w_i(z)` which encode material variation through the modular ratio `α_i(z)`.


**CLI**

```bash
python3 -m csf.CSFActions geometry.yaml actions.yaml
```

**Expected output snippet**

```
[OK] write_sap2000_geometry: wrote out/sap_template.txt
```

**Pitfalls**
- `stdout` is forbidden.
- `stations` is forbidden.
- `mode` must be one of: `CENTROIDAL_LINE`, `REFERENCE_LINE`, `BOTH`.

---

## 7. Action reference table (parameters, defaults, outputs)

> “Envelope fields” (`stations`, `output`, `params`) apply to all actions, with per-action rules.


| Action | Stations | Extra required keys (outside `params`) | Params (type → default) | Output behavior |
|---|---|---|---|---|
| `section_full_analysis` | REQUIRED | — | `fmt_display` (str → `.8f`) | stdout report; `.csv` table; other text file |
| `section_selected_analysis` | REQUIRED | `properties` (list, non-empty) | `fmt_display` (str → `.8f`) | compact stdout; `.csv` (z + selected keys); other text file |
| `plot_section_2d` | REQUIRED | — | `show_ids` (bool → true), `show_weights` (bool → true), `show_vertex_ids` (bool → false), `title` (str → null), `dpi` (int → 150) | stdout shows at end; image files saved if provided |
| `plot_volume_3d` | FORBIDDEN | — | `show_end_sections` (bool → true), `line_percent` (float → 100.0), `seed` (int → 0), `title` (str → "Ruled volume (vertex-connection lines)") | display-only (stdout); no file saving by design |
| `plot_properties` | FORBIDDEN | `properties` (list, non-empty) | `num_points` (int → 100) | stdout display unless file-only; image saved if path given |
| `plot_weight` | FORBIDDEN | — | `num_points` (int → 100) | stdout display unless file-only; image saved if path given |
| `weight_law_zrelative` | REQUIRED | `weight_law` (list[str], non-empty) | — | text-only; stdout and/or text files |
| `export_yaml` | REQUIRED (exactly 2 z) | — | — | file-only; exactly one `.yaml`/`.yml`; stdout forbidden |
| `write_opensees_geometry` | FORBIDDEN | — | `n_points` (int, required), `E_ref` (float, required), `nu` (float, required) | file-only; exactly one `.tcl`; stdout forbidden |
| `write_sap2000_geometry` | FORBIDDEN | — | `n_intervals` (int, required), `E_ref` (float, required), `nu` (float, required), `material_name` (str → `"S355"`), `mode` (str → `"BOTH"`), `include_plot` (bool → true), `plot_filename` (str → `"section_variation.png"`) | file-only; exactly one `.txt`; stdout forbidden |
| `write_samp2000_geometry` | FORBIDDEN | — | same as `write_sap2000_geometry` | alias (typo tolerance) |
| `volume` | REQUIRED (typically 2 edge stations) | — | `n_points` (int → 200), `fmt_display` (str → `.6f`), `w_tol` (float → `0.0`) | stdout report and/or text file; per‑polygon occupied and homogenized volumes |
| `section_area_by_weight` | REQUIRED | — | `w_tol` (float → `0.0`), `include_per_polygon` (bool → true) | stdout report and/or `.csv`/text; accountant‑style per‑polygon area listing |

---

## 8. Common pitfalls (and how to avoid them)

### 8.1 YAML typos and indentation
- YAML is indentation-sensitive. Use **spaces** (2 spaces recommended). No tabs.
- Lists must use `-`:
  - correct: `actions: [ ... ]` or `actions:\n  - action_name: ...`
  - wrong: `actions:\n    action_name: ...` (not a list)

### 8.2 Duplicate keys (common: two `actions:` blocks)
- Some YAML tools overwrite duplicates silently.
- CSFActions raises a controlled error pointing to the duplicate key.

### 8.3 Output directories
- If you write to `out/file.csv`, create `out/` first.
- Otherwise you will get an output path error.

### 8.4 z values outside the geometry domain
- For absolute station actions, keep station z values inside `[z0, z1]` of the CSF field.

### 8.5 Scientific notation parsing (E_ref)
- Prefer `2.1e+11` instead of `2.1e11` to avoid YAML edge cases in some parsers.

---

## 9. FAQ (frequent errors and what they mean)

Below are typical categories of errors you may see. CSFActions prints:
- a friendly message
- a short hint
- for YAML structure errors: a snippet with a caret pointer

### Q1) “Missing root key CSF_ACTIONS”
**Meaning**: your `actions.yaml` does not start with `CSF_ACTIONS:`  
**Fix**: ensure the root key exists and is correctly indented.

### Q2) “actions must be a list”
**Meaning**: you wrote a mapping instead of a list.  
**Fix**:

### Q3) “Unknown action …”
**Meaning**: action name is not in the implemented catalog.  
**Fix**: run `python CSFActions.py --help-actions` and copy the action name exactly.

### Q4) “stations is not allowed for this action”
**Meaning**: you supplied `stations:` for an action that forbids it.  
**Fix**: remove `stations:` for that action.

### Q5) “properties missing / unknown property key”
**Meaning**: `properties:` is missing, empty, not a list, or contains invalid keys.  
**Fix**: use only allowed keys (see `--help-actions` and table above).

### Q6) “stdout not allowed”
**Meaning**: file-only action received `stdout` in output.  
**Fix**: remove `stdout` from output and provide exactly one file path.

### Q7) “Output is not writable”
**Meaning**: folder missing or path is invalid.  
**Fix**: create folders, fix path spelling, check permissions.

### Q8) “Param missing / param type / param range”
**Meaning**: `params:` is missing required fields, or a value type is wrong (e.g. string instead of number).  
**Fix**: match the required parameters for the action (see table).

---

## 10. Naming conventions (recommended)

These conventions are not enforced, but they improve readability and reduce mistakes.

### 10.1 Station set names
- Use lowercase + underscores: `z_endpoints`, `z_fine`, `z_plot`
- Use names that describe meaning: `dense_near_support`, `gauss_lobatto_9`

### 10.2 Output files
- Use `out/` for generated artifacts.
- Add action name to filenames:
  - `out/full_analysis.csv`
  - `out/selected_props.csv`
  - `out/weight_inspector.txt`
  - `out/geometry.tcl`

### 10.3 Polygons (geometry.yaml)
- Use stable names (no spaces): `web`, `flange_top`, `flange_bot`, `void_1`
- Keep naming consistent across S0/S1 if polygons correspond along the member.

---

## 11. Checklist before running

1. `geometry.yaml` exists and is valid (CSFReader).
2. `actions.yaml` has root `CSF_ACTIONS:`.
3. `actions:` is a list and appears only once.
4. All station sets referenced by actions exist.
5. Output folders exist (`out/`).
6. Run `--validate-only` once before long runs.


