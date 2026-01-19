# CSFActions: Run CSF workflows from YAML (no Python coding)

`CSFActions.py` is a runner for **CSF (Continuous Section Field)**.
It reads a CSF geometry file and an **actions plan** written in YAML, validates both, and then executes the actions in order.

You provide **two YAML files**:

1. **`geometry.yaml`** — CSF geometry definition
   - Loaded and validated by CSF using `CSFReader`.
   - Geometry issues (warnings/errors) are printed before actions run.

2. **`actions.yaml`** — CSF actions plan
   - Loaded and fully validated by `CSFActions.py` before execution.
   - You can run the workflow by editing only this file.

This document is written for people who:
- have never used CSF before, and
- do not know YAML yet.

---

## Implemented actions (v0.1)

These actions are implemented and described in this guide:

- `section_full_analysis` — compute analysis at one or more stations; print a readable report and/or export a CSV table.
- `plot_section_2d` — plot 2D sections at one or more stations; optionally save a single composite image.
- `plot_volume_3d` — plot a 3D ruled volume between end sections; **does not use stations**.

> The runner may list additional placeholder actions in `--help-actions`, but only the three above are intended for end users at the moment.

---

## Requirements

- A Python environment that can execute `CSFActions.py`.
- The CSF package must be importable (modules like `csf.io.csf_reader` and `csf.section_field` must be on your `PYTHONPATH`).
- For plotting actions:
  - `matplotlib`
  - `Pillow` (PIL) is used to combine multiple plots into one image for `plot_section_2d`.

### Output directories must exist

If you write outputs to files, the **output folders must already exist**.
The runner does **not** create directories.

Example (Linux/macOS):

```bash
mkdir -p out
```

---

## Quickstart (end-to-end, no Python coding)

1) Create/obtain your CSF geometry file:

- `geometry.yaml`

2) Create your actions plan:

- `actions.yaml`

3) Run the workflow:

```bash
python CSFActions.py geometry.yaml actions.yaml
```

4) Validate only (do not execute actions):

```bash
python CSFActions.py geometry.yaml actions.yaml --validate-only
```

5) Print the action catalog and parameters:

```bash
python CSFActions.py --help-actions
```


---

## Core CSF concepts used by CSFActions

If you are new to CSF, these terms will appear throughout the YAML and the output.

### Continuous Section Field (CSF)

A CSF describes how a cross-section changes continuously along a span direction (called **z** in this project).
A CSF field can be thought of as:

- two end sections (at **z0** and **z1**), plus
- a rule/interpolation that allows you to evaluate an intermediate section at any station `z`.

When you run actions, the runner evaluates the field at requested stations and then analyzes or plots the resulting sections.

### Station (z)

A **station** is a numeric value `z` where you want to evaluate the field.

- Units depend on your geometry (e.g., meters, millimeters). CSFActions does not convert units.
- Typical stations include endpoints (z0, z1) and a set of intermediate points.

### Station sets (named station lists)

In `actions.yaml`, stations are organized into **named station sets** under `CSF_ACTIONS.stations`.

Why?

- You can reuse the same station list across multiple actions.
- You can define multiple resolutions (sparse / dense) and pick per action.

Example:

```yaml
CSF_ACTIONS:
  stations:
    station_edge:
      - 0.0
      - 87.6

    station_dense:
      - 0.0
      - 8.76
      - 17.52
      - 26.28
      - 35.04
      - 43.80
      - 52.56
      - 61.32
      - 70.08
      - 78.84
      - 87.6
```

Then in actions you reference the set name(s), not the raw numbers:

```yaml
- section_full_analysis:
    stations: [station_dense]
```

### Action order

Actions run **top to bottom** in the `actions:` list.

- You can repeat the same action multiple times (e.g., export CSV and export text report as two separate actions).
- You can mix analysis and plotting actions.

### Errors vs warnings

`CSFActions.py` reports problems as **issues**:

- **Errors** stop validation/execution. They usually include a short YAML snippet with line numbers and a caret (`^`).
- **Warnings** do not stop the run. They typically do not include a snippet.

Common warnings include “station list not sorted” or “station list has duplicates”.

### Optional top-level keys

The runner currently enforces only:

- `CSF_ACTIONS.stations`
- `CSF_ACTIONS.actions`

Other top-level keys (for example `version:` or `inputs:`) may be kept for documentation/future extensions, but they are not used by v0.1.

---

## YAML primer (for complete beginners)

YAML is a human-readable format used for configuration files.
It represents two main data structures:

- **Mappings** (a.k.a. dictionaries): `key: value`
- **Lists**: items introduced by `-`

### 1) Indentation is structure

YAML uses indentation (spaces) to represent nesting.

- Use **spaces** (not tabs).
- A common style is **2 spaces per level**.

✅ Correct:

```yaml
CSF_ACTIONS:
  stations:
    station_a:
      - 0.0
      - 10.0
```

❌ Incorrect (wrong indentation):

```yaml
CSF_ACTIONS:
 stations:
  station_a:
   - 0.0
```

### 2) Lists use `-`

A list is written with a dash prefix:

```yaml
stations:
  station_sparse:
    - 0.0
    - 5.0
    - 10.0
```

A very common beginner error is forgetting the dash:

```yaml
stations:
  station_sparse:
    0.0
    5.0
```

If you do this, the YAML parser will usually fail, and `CSFActions.py` will show an error with a small snippet and a caret (`^`) pointing near the problem.

### 3) Strings and quotes

Simple strings can be unquoted:

```yaml
title: Ruled volume
```

Use quotes when:

- the string contains special characters (`:`, `{}`, `#`, `[` `]`, etc.)
- you want to preserve exact formatting

Examples:

```yaml
title: "Section at z={z}"
fmt_diplay: ".12f"
```

### 4) Booleans

Use `true` / `false`:

```yaml
show_ids: true
show_vertex_ids: false
```

### 5) Numbers

Use integers or floats:

```yaml
seed: 0
line_percent: 30.0
```

For station values, **do not put numbers in quotes**:

```yaml
# Recommended
- 0.0
- 87.6

# Not recommended (becomes a string)
- "0.0"
```

### 6) Comments

`#` starts a comment until end of line:

```yaml
stations:
  station_edge:   # endpoints
    - 0.0
    - 87.6
```

### 7) A critical pitfall: duplicate keys

In YAML, repeating the same key at the same level often causes **silent overwriting**.
For example, if you accidentally write two `actions:` blocks, many YAML parsers will keep only the **last** one.

**Avoid this:**

```yaml
CSF_ACTIONS:
  actions:
    - section_full_analysis: {stations: [station_a]}

  actions:   # overwrites the first actions list
    - plot_section_2d: {stations: [station_a]}
```

**Best practice:** keep exactly one `actions:` section and add items within its list.

---

## The `actions.yaml` file: complete structure

`CSFActions.py` expects the actions file to have a **top-level mapping** with the key:

```yaml
CSF_ACTIONS:
  ...
```

Everything must be nested under that key.

### Minimal skeleton

This is the smallest valid shape (you still need to fill real values):

```yaml
CSF_ACTIONS:
  stations:
    station_name:
      - 0.0
      - 10.0

  actions:
    - section_full_analysis:
        stations: [station_name]
        output: [stdout]
        params: {}
```

In practice you will define several station sets and several actions.

---

## `CSF_ACTIONS.stations` (station sets)

`stations` is a **mapping** from a station set name to a **list of z values**:

```yaml
CSF_ACTIONS:
  stations:
    station_edge:
      - 0.0
      - 87.6

    station_dense:
      - 0.0
      - 8.76
      - 17.52
      - 26.28
```

Rules and behavior:

- Station set names must be non-empty strings.
- Each station set value must be a non-empty list.
- Each list item must be a number (`int` or `float`).
- If a station list is not sorted ascending, the validator emits a **warning**.
- If a station list contains duplicates, the validator emits a **warning**.

> **Current constraint (v0.1):** top-level `stations:` is required even if your actions do not use stations. (This may be relaxed in the future.)

---

## `CSF_ACTIONS.actions` (the action list)

`actions` is a **YAML list**. Each item in the list must be a mapping with **exactly one key**: the action name.

Example (two actions):

```yaml
CSF_ACTIONS:
  stations: { ... }

  actions:
    - section_full_analysis:
        stations: [station_dense]
        output: [stdout]
        params:
          fmt_diplay: ".8f"

    - plot_section_2d:
        stations: [station_edge]
        output: [out/section.bmp]
        params:
          title: "Section at z={z}"
```

### Common fields inside an action

Each action payload may contain these fields:

- `stations:` **required for most actions**
  - A list of station set names (as defined under `CSF_ACTIONS.stations`).
  - Can also be a single string; the validator will treat it like a one-item list.

- `output:` optional, default is `[stdout]`
  - A list of output destinations.
  - `stdout` means “write to terminal”.
  - Any other string is treated as a file path.

- `params:` optional, default `{}`
  - A mapping of action-specific parameters.
  - Keys are validated per action.

### Output rules

`CSFActions.py` validates output entries before running:

- Every output entry must be a non-empty string.
- If an output entry is a file path:
  - the **parent directory must exist**
  - the file must be writable (or creatable)

Relative paths are resolved from your current working directory.

### Parameter validation

Parameters live under `params:` and are validated per action:

- Required parameters (if any) must be present.
- Types are checked (bool/int/float/str).
- **Unknown parameters produce warnings (not errors)** so the format can evolve over time.

> Best practice: keep parameter names exactly as shown in the action reference. For example, the current code uses the parameter name **`fmt_diplay`** (spelling intentional), even though `fmt_display` may appear as an alias in some messages.

---

## Action reference

This section documents each implemented action.
For each action you will find:

- what it does
- which fields are required
- supported outputs
- parameters and their types
- a complete YAML example

### Common reminder: station expansion

When an action uses `stations:`, you are not listing raw `z` values there.
Instead, you reference **station set names** defined under `CSF_ACTIONS.stations`.

Example:

```yaml
CSF_ACTIONS:
  stations:
    station_edge:
      - 0.0
      - 87.6
    station_dense:
      - 0.0
      - 10.0
      - 20.0

  actions:
    - section_full_analysis:
        stations: [station_dense, station_edge]
```

The runner expands this to one `z` list by concatenating station sets **in the order you wrote them**.

---

## `section_full_analysis`

### What it does

For each station `z`, the runner:

1. Evaluates the section at that location: `section = field.section(z)`
2. Computes a full analysis dictionary: `analysis = section_full_analysis(section)`
3. Renders a **human-readable report** using `section_print_analysis(analysis, fmt=...)`

This action is useful when you want numerical properties (area, centroid, moments, etc.) and a readable per-section report.

### Required fields

- `stations:` **required**

### Outputs

You control outputs using `output:` (a list). If you omit `output:`, it defaults to `[stdout]`.

Supported output behaviors:

- **`stdout`**
  - Prints a report block for each section.
  - The report is formatted as text, typically resembling tables/lines per metric.

- **CSV file (`.csv`)**
  - Writes a numeric table with one row per station.
  - Columns are `z` plus the analysis keys.

- **Text file (any other extension, e.g. `.txt`)**
  - Writes the same human-readable report that would be printed to stdout.
  - This is the recommended way to “export the per-section tables” to a file.

### Parameters (`params`)

All parameters must be placed under `params:`.

| Name | Type | Default | Meaning |
|---|---:|---:|---|
| `fmt_diplay` | `str` | `.8f` | Numeric format used when printing the report (e.g. `.4f`, `.12f`, `.4e`). |

Notes:

- The parameter name is intentionally spelled **`fmt_diplay`** in the current code.
- `fmt_diplay` affects the **printed/text report**, not the CSV export.
- Some versions may warn if you write `fmt_diplay: =".4f"`. Do not include the leading `=`.

### Example

```yaml
CSF_ACTIONS:
  stations:
    station_dense:
      - 0.0
      - 8.76
      - 17.52

  actions:
    - section_full_analysis:
        stations: [station_dense]
        output: [stdout, out/section_full_analysis.csv, out/section_full_analysis.txt]
        params:
          fmt_diplay: ".12f"
```

---

## `plot_section_2d`

### What it does

For each station `z` in the expanded station list, the runner:

1. Creates a new matplotlib **Figure** and **Axes**
2. Calls the CSF visualizer: `Visualizer(field).plot_section_2d(z, ...)`
3. Optionally:
   - shows the plot window(s) if `stdout` is requested and matplotlib has an interactive backend
   - captures each plot as an image and builds a **single composite image** (vertical stack)

This action is useful for quickly checking geometry and labeling at key locations.

### Required fields

- `stations:` **required**

### Outputs

- **`stdout`**
  - Interpreted as “show plots on screen” and print progress messages.
  - If your matplotlib backend is non-interactive (often `Agg`), the runner prints a warning and showing will not work.

- **Image file(s)**
  - Any output entry other than `stdout` is treated as a file path.
  - If you request multiple stations and at least one file output, the runner saves **one composite image** that stacks all plots vertically.
  - The saved image format is decided by the file extension (e.g. `.png`, `.bmp`).

### Parameters (`params`)

| Name | Type | Default | Meaning |
|---|---:|---:|---|
| `show_ids` | `bool` | `true` | Show polygon indices (IDs). |
| `show_weights` | `bool` | `true` | Show polygon weights/names in labels. |
| `show_vertex_ids` | `bool` | `false` | Label vertices with 1-based indices. |
| `title` | `str` or `null` | `null` | Figure title. If it contains `{z}`, it is replaced with the numeric station value. |
| `dpi` | `int` | `150` | Raster DPI for file output. |

**Advanced (currently works, but may produce a validator warning):**

- `spacing_px` (`int`, default `10`) — vertical spacing between stacked plots in the composite image.
  - At the time of writing, this parameter is used by the runner but is not listed in the action spec, so it can trigger an “unknown parameter” warning.

### Example

```yaml
CSF_ACTIONS:
  stations:
    station_edge:
      - 0.0
      - 87.6

  actions:
    - plot_section_2d:
        stations: [station_edge]
        output:
          - stdout
          - out/sections.bmp
        params:
          show_ids: true
          show_weights: true
          show_vertex_ids: false
          title: "Section at z={z}"
          dpi: 150
```

---

## `plot_volume_3d`

### What it does

This action plots a **3D ruled volume** between the end sections of the CSF field.
It calls:

- `Visualizer(field).plot_volume_3d(show_end_sections=..., line_percent=..., seed=..., title=..., ax=...)`

### Special rule: no `stations`

`plot_volume_3d` **must not** define `stations:`.
It always uses the field endpoints.

✅ Correct:

```yaml
- plot_volume_3d:
    output: [stdout]
    params:
      line_percent: 40.0
```

❌ Incorrect (will fail validation):

```yaml
- plot_volume_3d:
    stations: [station_edge]
    output: [stdout]
```

### Outputs

- **`stdout`**
  - Attempts to show the plot window (interactive backend required).
  - In headless environments (backend `Agg`), showing will not work; save to file instead.

- **Image file(s)**
  - You can save to a file by listing a path under `output:`.
  - **Recommendation:** use `.jpg` or `.jpeg` as the extension.
    - The current runner saves with `format="jpg"` even if the extension is different.

### Parameters (`params`)

| Name | Type | Default | Meaning |
|---|---:|---:|---|
| `show_end_sections` | `bool` | `true` | Draw the two end section outlines. |
| `line_percent` | `float` | `100.0` | Percentage of generator lines to draw (expected range 0..100). |
| `seed` | `int` | `0` | Random seed used when `line_percent < 100`. |
| `title` | `str` | `"Ruled volume (vertex-connection lines)"` | Plot title. |
| `dpi` | `int` | `150` | Raster DPI for file output. |

### Example

```yaml
CSF_ACTIONS:
  stations:
    station_dummy:
      - 0.0

  actions:
    - plot_volume_3d:
        output:
          - stdout
          - out/volume.jpg
        params:
          show_end_sections: true
          line_percent: 30.0
          seed: 0
          title: "Ruled volume"
          dpi: 50
```

> **Note:** v0.1 requires top-level `stations:` even though `plot_volume_3d` does not use stations. Use any minimal station set as shown above.

---

## Full worked example (based on the provided sample)

Below is a complete `actions.yaml` example that runs:

1. `section_full_analysis` exporting **CSV**
2. `section_full_analysis` exporting a **text report** (per-section tables)
3. `plot_section_2d` showing plots and saving a composite image
4. `plot_volume_3d` showing plots (and optionally you could also save to a file)

### Example file: `actions.yaml`

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

### How to run this example

1) Make sure the geometry file exists (example):

- `nrel_5mv/nrel_5mv.yaml` (or your own `geometry.yaml`)

2) Make sure output directories exist **before running**. For the example above:

```bash
mkdir -p nrel_5mv/out
```

3) Run:

```bash
python CSFActions.py nrel_5mv/nrel_5mv.yaml actions.yaml
```

4) If you only want to check the YAML first:

```bash
python CSFActions.py nrel_5mv/nrel_5mv.yaml actions.yaml --validate-only
```

---

## Common mistakes and troubleshooting

This section lists frequent errors and how to fix them.

### 1) “Missing ':'” or parse error near a line

Symptoms:
- The runner reports an actions YAML parsing error.
- You see a snippet with a caret (`^`) near the reported line.

Typical causes:
- You wrote `key value` instead of `key: value`.
- You forgot indentation or mixed tabs/spaces.

Fix:
- Ensure every mapping entry has a colon:

```yaml
output: [stdout]
```

### 2) “List item is missing '-'” in stations

If you see an error that a station list item is missing `-`, you likely wrote:

```yaml
station_dense:
  0.0
  10.0
```

Correct form:

```yaml
station_dense:
  - 0.0
  - 10.0
```

### 3) Actions list item must define exactly one action name key

Each item under `actions:` must look like:

```yaml
- section_full_analysis:
    ...
```

Not like:

```yaml
- section_full_analysis: {}
  plot_section_2d: {}
```

### 4) Unknown action name

If you mistype an action name, validation fails.
Use:

```bash
python CSFActions.py --help-actions
```

to see the exact supported names.

### 5) Referencing a station set that does not exist

If an action says `stations: [station_dense]` but `station_dense` is not defined under `CSF_ACTIONS.stations`, validation fails.

Fix:
- Add the station set under `stations:` or correct the spelling.

### 6) `plot_volume_3d` rejects `stations:`

`plot_volume_3d` must NOT include `stations:`.
Remove it from the action block.

### 7) Output directory does not exist / not writable

Validation checks that:
- the parent directory exists
- you can create or write the file

Fix:
- Create the directory:

```bash
mkdir -p out
```

### 8) Plots do not show on screen

If matplotlib is running with a non-interactive backend (often `Agg`), the runner warns that it cannot show plots.

Fix:
- Save to a file in `output:` (recommended for servers/CI)
- Or run in an environment with a GUI backend (desktop Python)

### 9) CSV vs text report confusion for `section_full_analysis`

- Use `*.csv` when you want a numeric table for spreadsheets.
- Use `*.txt` (or any non-CSV extension) when you want the **human-readable per-section tables**.

Example:

```yaml
output:
  - out/analysis.csv
  - out/analysis.txt
```

### 10) Parameter name typos (especially `fmt_diplay`)

The current parameter name is:

- `fmt_diplay`

Even if you mentally expect `fmt_display`, follow the name in the action reference.
If you use an unknown parameter, the validator will emit a warning and it may be ignored at runtime.

### 11) Duplicate `actions:` blocks

YAML commonly overwrites earlier keys silently.
If you accidentally write two `actions:` keys, the first one may be discarded.

Fix:
- Keep exactly one `actions:` key.
- Add multiple actions as list items under it.

---

## Tips for writing clean action plans

- Start with one station set (e.g. endpoints) and one action; validate with `--validate-only`.
- Add one action at a time.
- Prefer explicit outputs to files for reproducibility.
- Use meaningful station set names (`station_edge`, `station_dense_mid`, etc.).
