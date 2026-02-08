# 09_yaml_workflow.md

# YAML Workflow (No-Code): `geometry.yaml` + `actions.yaml`

This document explains how to run CSF workflows **without writing Python** by using two YAML files:

- **`geometry.yaml`** — defines the continuous member (sections, polygons, weights).
- **`actions.yaml`** — declares what CSF should do (reports, plots, exports).

CSF is a **pre-processor**: it computes section properties and derived fields along *z* and can export solver-ready data.  
It is not a structural solver.

---

## 1. Quick Start

### 1.1 Recommended folder layout

```
my_case/
  geometry.yaml
  actions.yaml
  out/                 # create this folder yourself
```

**Important**: CSF actions validate output paths, but do **not** create missing folders.  
Create `out/` (and any subfolders) before running.

### 1.2 Minimal `actions.yaml` (complete example)

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:
    stations_example:
      - 0.0
      - 1.0
      - 10.0

  actions:
    - section_full_analysis:
        stations:
          - stations_example
        output:
          - stdout
          - out/full_analysis.csv
        params:
          fmt_diplay: ".8f"
```

### 1.3 Run

From inside `my_case/`:

```bash
python CSFActions.py geometry.yaml actions.yaml
```

---

## 2. The Two YAML Files

### 2.1 `geometry.yaml` (what the member **is**)

- Describes the CSF member: sections, polygons, vertices, weights, and optional metadata.
- Validated by `CSFReader` before actions are executed.
- If geometry validation fails, CSFActions prints the issues and stops.

**Key idea**: keep `geometry.yaml` stable and reuse it with different `actions.yaml` plans.

### 2.2 `actions.yaml` (what to **do**)

The `actions.yaml` file must contain **one** top-level root key:

```yaml
CSF_ACTIONS:
  stations: ...
  actions: ...
```

#### Required rules

- `CSF_ACTIONS:` is required.
- `actions:` must be a **list**.
- Avoid duplicate YAML keys (some YAML parsers overwrite silently). CSFActions treats duplicates as errors.

---

## 3. Stations

Stations are named lists of *z* coordinates reused by multiple actions.

```yaml
stations:
  coarse: [0.0, 10.0]
  fine:   [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
```

Usage in an action:

```yaml
actions:
  - section_full_analysis:
      stations: [fine]
```

### 3.1 Station semantics

- For most actions, station values are **absolute z coordinates** and must lie inside the CSF domain.
- For `weight_lab_zrelative`, station values are interpreted as **relative z** (user responsibility).

---

## 4. Output Rules

Most actions accept:

- `output:` list (optional)
- `params:` dictionary (optional)

If `output` is missing, the default is:

```yaml
output: [stdout]
```

### 4.1 File-only behavior

If `output:` exists but does not contain `stdout`, that action becomes **file-only**:
- no terminal output,
- only files are written.

Example:

```yaml
output:
  - out/results.csv
  - out/report.txt
```

### 4.2 Actions that forbid stdout

Some actions are file-only by design and reject `stdout`, for example:
- `export_yaml`
- `write_opensees_geometry`
- `write_sap2000_geometry`

---

## 5. Useful CLI Options

### 5.1 Validate only (no execution)

```bash
python CSFActions.py geometry.yaml actions.yaml --validate-only
```

### 5.2 Show available actions and rules

```bash
python CSFActions.py --help-actions
```

---

## 6. Tutorials by Action

Each subsection below includes:
- concept,
- YAML snippet,
- command,
- common pitfalls.

> In all examples below, `geometry.yaml` exists and is valid, and `out/` already exists.

---

### 6.1 `section_full_analysis` (stations REQUIRED)

Computes a full set of section properties at each requested station.

```yaml
CSF_ACTIONS:
  stations:
    z_list: [0.0, 5.0, 10.0]

  actions:
    - section_full_analysis:
        stations: [z_list]
        output: [stdout, out/full.csv]
        params:
          fmt_diplay: ".10f"
```

Pitfalls:
- Missing `stations` → error.
- A station outside the geometry domain → error.
- Missing output folder → file write error.

---

### 6.2 `section_selected_analysis` (stations REQUIRED)

Computes only selected property keys (compact report + compact CSV).

```yaml
CSF_ACTIONS:
  stations:
    z_list: [0.0, 10.0]

  actions:
    - section_selected_analysis:
        stations: [z_list]
        output: [stdout, out/selected.csv, out/selected.txt]
        properties: [A, Cx, Cy, Ix, Iy, J]
        params:
          fmt_diplay: ".12f"
```

Pitfalls:
- Missing or empty `properties` → error.
- Misspelled property key → error.

---

### 6.3 `plot_section_2d` (stations REQUIRED)

Plots 2D section geometry at each station.

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

Pitfalls:
- Missing output folder → error.
- In headless environments prefer file output (avoid relying on interactive windows).

---

### 6.4 `plot_volume_3d` (stations FORBIDDEN)

Shows the ruled “volume” between end sections.

```yaml
CSF_ACTIONS:
  actions:
    - plot_volume_3d:
        output: [stdout]
        params:
          show_end_sections: true
          line_percent: 50.0
          seed: 0
          title: "CSF ruled volume"
```

Pitfalls:
- Providing `stations:` for this action → error.

---

### 6.5 `plot_properties` (stations FORBIDDEN)

Plots selected properties along the member, using internal sampling.

```yaml
CSF_ACTIONS:
  actions:
    - plot_properties:
        output: [stdout, out/properties.png]
        properties: [A, Ix, Iy, J]
        params:
          num_points: 100
```

Pitfalls:
- Missing `properties` → error.
- Supplying `stations` → error.

---

### 6.6 `plot_weight` (stations FORBIDDEN)

Plots interpolated polygon weight(s) along the member.

```yaml
CSF_ACTIONS:
  actions:
    - plot_weight:
        output: [stdout, out/weight.png]
        params:
          num_points: 120
```

---

### 6.7 `weight_lab_zrelative` (stations REQUIRED)

Evaluates user-defined weight-law expressions at **relative** z values (inspection tool).

> Note: the key is spelled `weith_law` (as currently implemented).

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

Pitfalls:
- Using absolute *z* values here without realizing the action interprets them as relative.
- Typos in formulas will be reported by the safe evaluator (when enabled).

---

### 6.8 `export_yaml` (stations REQUIRED; EXACTLY TWO z; FILE-ONLY)

Exports a new CSF geometry YAML built from exactly two stations.

```yaml
CSF_ACTIONS:
  stations:
    subpart: [1.0, 8.0]   # MUST be exactly two values

  actions:
    - export_yaml:
        stations: [subpart]
        output: [out/subpart.yaml]
```

Pitfalls:
- Station set is not length 2 → error.
- `stdout` included in output → error.
- Output must be exactly one YAML file path.

---

### 6.9 `write_opensees_geometry` (stations FORBIDDEN; FILE-ONLY)

Writes a Tcl file with station snapshots for downstream OpenSees workflows.

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

Pitfalls:
- Supplying `stations` → error.
- Including `stdout` → error.
- Missing required parameters → error.

---

### 6.10 `write_sap2000_geometry` (stations FORBIDDEN; FILE-ONLY)

Writes a “template pack” for SAP2000 copy/paste workflows.

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

Pitfalls:
- Including `stdout` → error.
- Supplying `stations` → error.
- Invalid `mode` → error.

---

## 7. Common Pitfalls (Checklist)

1. `geometry.yaml` valid (run once with `--validate-only`).
2. `actions.yaml` has root `CSF_ACTIONS:`.
3. `actions:` is a list and appears only once.
4. All station sets referenced by actions exist.
5. Output folders exist (`out/`).
6. Stations lie within the member domain (except `weight_lab_zrelative` which is relative-z).

---

## 8. Minimal Mental Model

- `geometry.yaml` = the member definition (continuous field).
- `actions.yaml` = an execution plan over that member.
- stations = reusable lists of z locations.
- outputs = stdout and/or files.
- CSF computes; OpenSees/SAP2000 solve.
