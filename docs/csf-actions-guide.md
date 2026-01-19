# CSF Actions (`actions.yaml`) — User Guide

This document explains how to run **CSF (Continuous Section Field)** workflows **without writing Python code** by using an **actions YAML file** (`actions.yaml`) together with a **geometry YAML file** (`geometry.yaml` / `case.yaml`).

You will:
1. Prepare a **CSF geometry file** (the section field).
2. Prepare an **actions file** describing what to do with that geometry.
3. Run `CSFActions.py` to validate and execute the workflow.

---

## What you need

- A CSF geometry YAML (produced by CSF export or written by hand).
- An actions YAML (this guide).
- Python environment with:
  - CSF project installed/importable
  - `PyYAML` (YAML parser)
  - For plotting actions: `matplotlib` and `Pillow` (PIL)
- The runner script: `CSFActions.py`

> If plotting shows the warning “Matplotlib backend is non-interactive (Agg)”, you are in a headless environment. Plots can still be saved to files, but cannot be opened as windows.

---

## Running CSF Actions

Typical command line usage:

```bash
python CSFActions.py geometry.yaml actions.yaml
```

You can also validate only (no execution) if your runner provides it:

```bash
python CSFActions.py geometry.yaml actions.yaml --validate-only
```

The runner will always print **warnings** and **errors** in a user-friendly format:
- **Errors** include a YAML snippet with a caret pointing near the problem.
- **Warnings** are shown without snippets.

---

## YAML basics (quick intro)

YAML is a human-readable format based on indentation.

### 1) Mappings (key/value)

```yaml
key: value
```

### 2) Lists (each item starts with `-`)

```yaml
items:
  - one
  - two
```

### 3) Indentation matters

Use spaces (recommended: 2 spaces). Do not mix tabs and spaces.

### 4) Important: duplicate keys overwrite

If you write the same key twice at the same indentation level, YAML keeps **only the last one**.

**Wrong (two `actions:` keys):**
```yaml
actions:
  - ...
actions:
  - ...
```

Only the second `actions:` will remain. Always use a single `actions:` list.

---

## Structure of `actions.yaml`

The actions file has a single top-level key:

```yaml
CSF_ACTIONS:
  stations: ...
  actions: ...
```

### `CSF_ACTIONS.stations` (station sets)

A **station set** is a named list of Z coordinates where actions will be applied.

Example:
```yaml
stations:
  station_dense:
    - 0.0
    - 10.0
    - 20.0
```

Rules:
- Station names must be unique.
- Station values must be numbers (no quotes, e.g. use `10.0` not `"10.0"`).
- Keep values ordered if you want ordered output (the runner may warn if not ordered).

### `CSF_ACTIONS.actions` (the workflow)

`actions` is a **list**. Each item is a mapping containing exactly one action name:

```yaml
actions:
  - section_full_analysis:
      stations: [station_dense]
      output: [stdout, out/results.csv]
      params:
        fmt_diplay: ".8f"
```

Common fields inside each action:

| Field | Required | Meaning |
|------|----------|---------|
| `stations` | Usually yes | Which station sets to use (list of station names). |
| `output` | Optional | Where results go. Default is `stdout`. |
| `params` | Optional | Action-specific parameters. If omitted, defaults are used. |

> Some actions do **not** use stations (see `plot_volume_3d`).

---

## Outputs (`output:`)

`output` is a list. Supported patterns:

- `stdout` — prints to console (and for plots: attempts to show windows if interactive backend).
- A file path — writes results to that file.
  - The directory must exist, otherwise you get a controlled error.

Examples:

```yaml
output:
  - stdout
  - out/my_results.csv
```

```yaml
output:
  - out/plots/section.bmp
```

> For plotting actions, a **single image file** may contain multiple plots stacked vertically if multiple stations are requested.

---

## Actions implemented (current catalog)

### 1) `section_full_analysis`

**Purpose:** compute a full set of section properties at selected stations.

**Uses stations:** yes.

**Typical outputs:**
- `.csv` file: machine-friendly results
- `.txt` file (or `stdout`): human-friendly tables (one section per station)

**Example:**
```yaml
- section_full_analysis:
    stations:
      - station_dense
    output:
      - out/full_analysis.csv
    params:
      fmt_diplay: ".12f"
```

**Parameters (`params:`):**
- `fmt_diplay` *(string, optional)*  
  Numeric formatting for human-readable output (tables / text display).  
  Example: `".4f"` prints 4 digits after decimal.

Notes:
- CSV formatting may be raw numeric or formatted depending on runner version. If your CSV shows long floats, this is expected unless your runner applies the format to CSV too.

---

### 2) `plot_section_2d`

**Purpose:** plot 2D geometry of a section at selected Z stations.

**Uses stations:** yes.

**Example:**
```yaml
- plot_section_2d:
    stations:
      - station_edge
    output:
      - stdout
      - out/section_out.bmp
    params:
      show_ids: true
      show_weights: true
      show_vertex_ids: false
      title: "Section at z={z}"
      dpi: 150
```

**Parameters (`params:`):**
- `show_ids` *(bool, default: true)* — show polygon indices.
- `show_weights` *(bool, default: true)* — show polygon weights (and/or names) in labels.
- `show_vertex_ids` *(bool, default: false)* — label vertices with indices.
- `title` *(string or null, default: null)* — plot title. You can use `{z}` placeholder.
- `dpi` *(int, default: 150)* — resolution when saving.

Behavior:
- If `stdout` is present and backend is interactive, windows open via `matplotlib`.
- If you run headless (Agg), it prints a warning and you should rely on file output.

---

### 3) `plot_volume_3d`

**Purpose:** plot a 3D ruled volume connecting end sections (vertex-connection lines).

**Uses stations:** **no**  
This action always uses the field endpoints (z0 and z1). **Do not provide `stations:`** inside this action.

**Example:**
```yaml
- plot_volume_3d:
    output:
      - stdout
      - out/volume.bmp
    params:
      show_end_sections: true
      line_percent: 30.0
      seed: 0
      title: "Ruled volume"
      dpi: 50
```

**Parameters (`params:`):**
- `show_end_sections` *(bool, default: true)* — draw end-section outlines.
- `line_percent` *(float, default: 100.0)* — percentage of generator lines shown (0–100).
- `seed` *(int, default: 0)* — random seed for subsampling lines.
- `title` *(string, default: "Ruled volume (vertex-connection lines)")* — plot title.
- `dpi` *(int, default: 150)* — resolution when saving.

---

## Full example (copy/paste)

This is the example configuration you provided, kept as-is:

```yaml
CSF_ACTIONS:
  stations:
    station_edge:
      - 0
      - 87.60
    station_dense:
      - 0.00
      - 8.76
      - 17.52
      - 26.28
      - 35.04
      - 43.80
      - 52.56
      - 61.32
      - 70.08
      - 78.84
      - 87.60
  actions:
    - section_full_analysis:
        stations:
          - station_dense
        output:
          - nrel_5mv/out/nrel_5mv_full_analysis.csv
        params:
          fmt_diplay: ".12f"    
    - section_full_analysis:
        stations:
          - station_dense
        output:
          - nrel_5mv/out/nrel_5mv_full_analysis.txt
        params:
          fmt_diplay: ".12f"               

    - plot_section_2d:
        stations:
          - station_edge
        output:
          - stdout
          - nrel_5mv/nrel_5mv.bmp
        params:
          show_ids: true
          show_weights: true
          show_vertex_ids: false
          title: "Section at z={z}"
          dpi: 150     
    - plot_volume_3d:
        output:
          - stdout
        params:
          show_end_sections: true
          line_percent: 30.0
          seed: 0
          title: "Ruled volume"
          dpi: 50
```

---

## Common mistakes and how to fix them

### 1) Duplicate `actions:` key
Symptom: only the last action block runs.

Fix: keep exactly one `actions:` list and put all actions inside it.

### 2) Quoted numbers (e.g. `"10.0"`)
Symptom: validator error about numbers being strings.

Fix: remove quotes, write numbers as plain scalars:
```yaml
- 10.0
```

### 3) Missing `:` after a key
Example:
```yaml
weight_laws
  - ...
```
Fix:
```yaml
weight_laws:
  - ...
```

### 4) Output directory does not exist
Example:
```yaml
output:
  - out/plots/section.bmp
```
If `out/plots` does not exist, create it first.

---

## Adding new actions (developer note)

The system is designed to be extended. New actions should be registered in an internal catalog with:
- action name
- parameter specs (required/optional/default/type)
- runner function
- dispatcher branch

User-facing schema should remain flexible: unknown parameters produce warnings, not hard failures (unless explicitly required).

---

## Support

If validation fails, re-run and read the snippet. The reported line usually points very close to the YAML mistake.
