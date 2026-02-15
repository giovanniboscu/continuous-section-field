# CSF YAML Tutorial (CSFActions.py)


## Use CSF without writing Python

Although CSF is implemented as a Python engine, it can be used **without programming** through the **CSFReader** tool.

With CSFReader, you run the full CSF workflow by providing **two input YAML files**:

1. **`geometry.yaml`** — defines the member geometry as a continuous field along the axis `z`  
   - end (or intermediate) sections as **arbitrary polygons**  
   - optional multi-polygon sections (multi-cell shapes)  
   - per-polygon metadata (e.g., weights for multi-material / void logic)

2. **`actions.yaml`** — declares *what CSF must do* (no code required)  
   - compute section properties and derived stiffness/mass fields  
   - produce plots/visualizations and reports  
   - export solver-ready station data (e.g., for force-based beam formulations)

In other words:

> **`geometry.yaml` describes the “what it is”** (continuous geometry + optional longitudinal material/stiffness laws),  
> **`actions.yaml` describes the “what to do with it”** (analysis, validation, plotting, exporting).

## Scope

CSF uses **two YAML files**:

- `geometry.yaml` → defines the CSF geometry (read/validated by `CSFReader().read_file(...)`).
- `actions.yaml` → defines **what to do** with that geometry (validated + executed by `CSFActions.py`).

---

## 1. Quick start (one run)

### 1.1 Folder layout (recommended)

```
my_case/
  geometry.yaml
  actions.yaml
  out/                # create this folder yourself
```

**Important**: CSFActions checks that output paths are writable, but it does **not** create missing folders for you.  
Create `out/` (and any subfolders) before running.

### 1.2 Minimal `actions.yaml` (complete)

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
### 1.3 CLI command

From inside `my_case/`:

```bash
python3 ../csf/CSFActions.py  geomtry.yaml  actions.yaml
```

### 1.4 Expected output snippet (example)

what you will see

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

## 2. Core concepts (the two YAML files)

### 2.1 `geometry.yaml` (input geometry)

- This file describes the CSF member: end sections, polygons, vertices, weights/materials, etc.
- It is validated by `CSFReader`.
- If geometry validation fails, CSFActions prints the geometry issues and stops.

**Note**: `geometry.yaml` is intentionally **separate** from the action plan.  
You can reuse the same geometry with many different `actions.yaml` files.

### 2.2 `actions.yaml` (execution plan)

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

#### Critical rule: `actions:` must appear only once

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
```
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
---

## 4. Output rules (stdout vs file-only)

Each action may have an `output:` list. If `output` is **missing**, the default is:

```yaml
output: [stdout]
```

### 4.1 File-only behavior

If `output:` exists but does **not** contain `stdout`, the run becomes **file-only** for that action:
- no on-screen output
- only files are written

Example:

```yaml
output:
  - out/results.csv
  - out/report.txt
```

### 4.2 Actions that forbid stdout

Some actions are strictly file-only and will reject `stdout` with a friendly error:
- `export_yaml`
- `write_opensees_geometry`
- `write_sap2000_geometry` (and alias `write_samp2000_geometry`)

---

## 5. Useful CLI options

### 5.1 Validate only (no execution)

```bash
python ../csf/CSFActions.py geometry.yaml actions.yaml --validate-only
```

Expected snippet:

```
Actions file validated successfully.
Validation-only mode: no actions executed.
```

### 5.2 Print built-in help for actions

```bash
 python3 ../csf/CSFActions.py --help-actions
```

This prints:
- the current action catalog
- per-action notes (stations required/forbidden)
- output behavior notes
- allowed property keys documentation

---

## 6. Tutorials (one per main action)

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

### 6.2 `section_selected_analysis` 

**Concept**  
Computes only a user-selected list of property keys (compact report + compact CSV).  
This is useful when you only need a few keys (for plots, checking, exporting).

**YAML**

```yaml
CSF_ACTIONS:
  stations:
    z_list: [0.0, 10.0] #<= this list is also valid

  actions:
    - section_selected_analysis:
        stations: [z_list]
        output: [stdout, out/selected.csv, out/selected.txt]
        properties: [A, Cx, Cy, Ix, Iy, J]
        params:
          fmt_display: ".12f"
```

**CLI**

```bash
python CSFActions.py geometry.yaml actions.yaml
```

**Expected output snippet**

```
### SECTION SELECTED ANALYSIS @ z = 0.0 ###
A                   : ...
Ix                  : ...
```

**Pitfalls**
- `properties` missing or empty → error.
- Typos like `Ixx` instead of `Ix` → unknown property error.
- YAML commas inside strings (e.g. `"A",`) → treated as a different string and rejected.

---

### 6.3 `plot_section_2d` (stations REQUIRED)

**Concept**  
Plots the 2D section geometry at each station.  
If you save an image and request multiple stations, CSFActions can create one **stacked composite image**.

**YAML**

```yaml
CSF_ACTIONS:
  stations:
    z_list: [0.0, 10.0]

  actions:
    - plot_section_2d:
        stations: [z_list]
        output: [stdout, out/sections.png]
        params:
          show_ids: true
          show_weights: true
          show_vertex_ids: false
          title: "Section at z={z}"
          dpi: 150
```

**CLI**

```bash
python CSFActions.py geometry.yaml actions.yaml
```

**Expected output snippet**

```
[OK] plot_section_2d: created 2 plot(s)
[OK] saved image: out/sections.png
```

**Pitfalls**
- `out/` missing → file write error.
- Headless environments: if you rely on interactive display, use file output instead.

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
python ../csf/CSFActions.py geometry.yaml actions.yaml
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
Plots selected properties along the member, sampling `num_points` between endpoints.

**YAML**

```yaml
CSF_ACTIONS:
  actions:
    - plot_properties:
        output: [stdout, out/properties.png]
        properties: [A, Ix, Iy, J]
        params:
          num_points: 100
```

**CLI**

```bash
python ../csf/CSFActions.py geometry.yaml actions.yaml
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

### 6.6 `plot_weight` (stations FORBIDDEN)

**Concept**  
Plots interpolated polygon weight(s) along the member.

**YAML**

```yaml
CSF_ACTIONS:
  actions:
    - plot_weight:
        output: [stdout, out/weight.png]
        params:
          num_points: 120
```

**CLI**

```bash
python ../csf/CSFActions.py geometry.yaml actions.yaml
```

**Expected output snippet**

```
[OK] plot_weight scheduled
[OK] saved: out/weight.png
```

**Pitfalls**
- Same as `plot_properties` for output/show behavior.

---

### 6.7 `weight_lab_zrelative` (stations REQUIRED; text-only)

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
python ../csf/CSFActions.py geometry.yaml actions.yaml
```

**Expected output snippet**

```
LAW #1: 1.0
  z=0.0 -> ...
```

**Pitfalls**
- The key name is `weith_law` (spelling is enforced by the current runner).
- Relative-z meaning is your responsibility (keep consistent with your element length `L`).

---

### 6.8 `export_yaml` (stations REQUIRED; FILE-ONLY)

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
python ../csf/CSFActions.py geometry.yaml actions.yaml
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

### 6.9 `write_opensees_geometry` (stations FORBIDDEN; FILE-ONLY)

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
python ../csf/CSFActions.py geometry.yaml actions.yaml
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

### 6.10 `write_sap2000_geometry` (stations FORBIDDEN; FILE-ONLY)

**Concept**  
Writes a “template pack” text file that helps you build a SAP2000 model by copy/paste.

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

**CLI**

```bash
python ../csf/CSFActions.py geometry.yaml actions.yaml
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
| `section_full_analysis` | REQUIRED | — | `fmt_diplay` (str → `.8f`) | stdout report; `.csv` table; other text file |
| `section_selected_analysis` | REQUIRED | `properties` (list, non-empty) | `fmt_diplay` (str → `.8f`) | compact stdout; `.csv` (z + selected keys); other text file |
| `plot_section_2d` | REQUIRED | — | `show_ids` (bool → true), `show_weights` (bool → true), `show_vertex_ids` (bool → false), `title` (str → null), `dpi` (int → 150) | stdout shows at end; image files saved if provided |
| `plot_volume_3d` | FORBIDDEN | — | `show_end_sections` (bool → true), `line_percent` (float → 100.0), `seed` (int → 0), `title` (str → "Ruled volume (vertex-connection lines)") | display-only (stdout); no file saving by design |
| `plot_properties` | FORBIDDEN | `properties` (list, non-empty) | `num_points` (int → 100) | stdout display unless file-only; image saved if path given |
| `plot_weight` | FORBIDDEN | — | `num_points` (int → 100) | stdout display unless file-only; image saved if path given |
| `weight_lab_zrelative` | REQUIRED | `weith_law` (list[str], non-empty) | — | text-only; stdout and/or text files |
| `export_yaml` | REQUIRED (exactly 2 z) | — | — | file-only; exactly one `.yaml`/`.yml`; stdout forbidden |
| `write_opensees_geometry` | FORBIDDEN | — | `n_points` (int, required), `E_ref` (float, required), `nu` (float, required) | file-only; exactly one `.tcl`; stdout forbidden |
| `write_sap2000_geometry` | FORBIDDEN | — | `n_intervals` (int, required), `E_ref` (float, required), `nu` (float, required), `material_name` (str → `"S355"`), `mode` (str → `"BOTH"`), `include_plot` (bool → true), `plot_filename` (str → `"section_variation.png"`) | file-only; exactly one `.txt`; stdout forbidden |
| `write_samp2000_geometry` | FORBIDDEN | — | same as `write_sap2000_geometry` | alias (typo tolerance) |

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


