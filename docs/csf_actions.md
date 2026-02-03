# CSF Actions Reference (`CSFActions.py`)

This document describes the **Actions YAML** contract implemented by `CSFActions.py` and provides **one worked YAML example per action**.

---

## Scope and assumptions (always in force)

- **CSF is a modeler, not a solver**: it generates *section-property fields* to be consumed by external solvers.
- **Beam theory scope**: exported properties and downstream usage are intended for **slender beam elements** (Euler–Bernoulli assumptions). No local plate/shell effects, warping-local phenomena, or 3D solid behavior are implied by these actions.

---

## Two-file workflow

CSF runs are defined by two YAML files:

1. `geometry.yaml`  
   Declares the continuous section field (ruled surfaces, weight laws, polygons, etc.). Loaded/validated by `CSFReader`.

2. `actions.yaml`  
   Declares a deterministic execution plan. Root key must be `CSF_ACTIONS`.

Typical CLI usage:

```bash
python CSFActions.py geometry.yaml actions.yaml
python CSFActions.py --help-actions
```

---

## Actions YAML: schema and routing rules

### Root structure

```yaml
CSF_ACTIONS:
  stations:
    my_station_set: [0.0, 2.0, 4.0]
  actions:
    - section_full_analysis:
        stations: [my_station_set]
        output: [stdout, out/full.csv]
        params: {fmt_diplay: ".8f"}
```

### Station sets (`CSF_ACTIONS.stations`)

- `stations` is a mapping: `station_set_name -> list[float]`.
- Most actions reference station sets by name via `stations: [name1, name2, ...]`.
- Some actions **forbid** `stations` entirely (they sample internally).

> Note: validation may emit warnings if stations are unsorted or contain duplicates, but execution still proceeds unless it violates an action’s strict contract.

### Common action envelope fields

Inside an action block (e.g., `- section_full_analysis: { ... }`):

- `stations`: required or forbidden depending on the action.
- `output`: optional list of output targets.
  - If `output` key is **missing**, default is: `["stdout"]`.
  - If `output` exists but does **not** contain `stdout`, the action is **file-only** (no terminal prints).
- `params`: optional mapping of action-specific parameters (validated per action).

### Output targets and directory rule

- Any non-`stdout` entry is treated as a file path.
- **Output directories must already exist**; the runner raises a runtime error if the parent directory does not exist.

### Plot actions: deferred display

Plot-producing actions may create matplotlib figures. Display is **deferred** until the end of the run:
- If `stdout` is present in `output`, the figure(s) are kept for final on-screen display.
- If `stdout` is omitted, plots are produced file-only (no interactive window).

---

## Property keys used by plotting and selection

Some actions require a `properties:` list (outside `params`). Allowed keys and meaning:

- `A` — Total net cross-sectional area  
- `Cx`, `Cy` — Centroid coordinates  
- `Ix`, `Iy`, `Ixy` — Second moments and product of inertia  
- `J` — Polar second moment (`Ix + Iy`)  
- `I1`, `I2` — Principal second moments  
- `rx`, `ry` — Radii of gyration  
- `Wx`, `Wy` — Elastic section moduli  
- `K_torsion` — Semi-empirical torsional stiffness approximation  
- `Q_na` — First moment of area at neutral axis  
- `J_sv` — Effective Saint-Venant torsional constant (J)  
- `J_sv_wall` — Saint-Venant torsion for open thin-walled walls  
- `J_sv_cell` — Saint-Venant torsion for closed thin-walled cells (Bredt-like approach)  
- `J_s_vroark` — Refined torsion constant (Roark–Young thickness correction)  
- `J_s_vroark_fidelity` — Fidelity / reliability indicator for the Roark correction

---

## Material/weight contract for solver-export actions (OpenSees, SAP2000)

These actions assume the **CSF-computed properties are already weighted/modularized** (multi-material + voids + sign conventions already included in the reported section properties).

Recommended “standard” workflow:

- In CSF geometry, interpret `weight` as **dimensionless ratio** `E / E_ref`.
- In solver exports, use a **constant physical** `E_ref` (and `nu`, from which `G_ref` is derived).
- Do **not** multiply section stiffness by `E` again in the solver if the CSF export already embeds modular weights (avoid double counting).

---

# Action catalog

## `section_full_analysis`

**Purpose**  
Compute the full standard property set at each requested station and route it to stdout/CSV/text.

**Stations**: **REQUIRED** (station-set names).  
**Output**:
- `stdout` → human-readable report per station.
- `*.csv` → numeric table (one row per station; columns = analysis keys).
- any other file → captured text report.

**Parameters (`params:`)**

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `fmt_diplay` | str | no | `.8f` | Python numeric format for printed report (e.g. `.4f`, `.3e`). Alias accepted: `fmt_display`. |

**Example**

```yaml
CSF_ACTIONS:
  stations:
    s_dense: [0.0, 2.5, 5.0]
  actions:
    - section_full_analysis:
        stations: [s_dense]
        output: [stdout, out/section_full.csv]
        params:
          fmt_diplay: ".10f"
```

---

## `section_selected_analysis`

**Purpose**  
Compute only selected properties at each station (still derived from the full analysis internally), preserving the property order requested.

**Stations**: **REQUIRED**.  
**Extra required key** (outside `params`): `properties: [ ... ]` (non-empty).  
**Output**:
- `stdout` → compact report (only requested keys).
- `*.csv` → numeric table (columns: `z` + requested keys).
- other file → captured text report.

**Parameters (`params:`)**

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `fmt_diplay` | str | no | `.8f` | Python numeric format for printed report. Alias accepted: `fmt_display`. |

**Example**

```yaml
CSF_ACTIONS:
  stations:
    s_dense: [0.0, 2.5, 5.0]
  actions:
    - section_selected_analysis:
        stations: [s_dense]
        output: [stdout, out/selected.csv]
        properties: [A, Cx, Cy, Ix, Iy, J_sv]
        params:
          fmt_diplay: ".6g"
```

---

## `weight_lab` (placeholder)

**Purpose**  
Reserved for future weight-law exploration/reporting.

**Status**: **NOT IMPLEMENTED** (the runner knows the name for validation, but execution is expected to fail).

**Example (do not use in production runs yet)**

```yaml
CSF_ACTIONS:
  stations:
    dummy: [0.0]
  actions:
    - weight_lab:
        stations: [dummy]
        output: [stdout]
```

---

## `plot_section_2d`

**Purpose**  
Generate 2D section plots at requested stations.

**Stations**: **REQUIRED**.  
**Output**:
- If `stdout` is present: figures are kept for deferred on-screen display at end of run.
- If file path(s) are provided: plots are saved.
  - If multiple stations are requested and at least one file output is present, the runner may produce a **single composite image** (plots stacked vertically).

**Parameters (`params:`)**

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `show_ids` | bool | no | `true` | Label polygons by index (#0, #1, …). |
| `show_weights` | bool | no | `true` | Include polygon weights and names in labels. |
| `show_vertex_ids` | bool | no | `false` | Label vertices with a 1-based index. |
| `title` | str | no | `null` | Plot title; `{z}` is replaced with the station value if present. |
| `dpi` | int | no | `150` | Rasterization DPI when saving images. |

**Example**

```yaml
CSF_ACTIONS:
  stations:
    s_sparse: [0.0, 5.0]
  actions:
    - plot_section_2d:
        stations: [s_sparse]
        output: [stdout, out/sections.png]
        params:
          show_ids: true
          show_weights: true
          show_vertex_ids: false
          title: "Section at z={z}"
          dpi: 200
```

---

## `plot_volume_3d`

**Purpose**  
Plot a 3D ruled volume (vertex-connection lines) between end sections.

**Stations**: **FORBIDDEN** (always uses field endpoints `z0`, `z1`).  
**Output**:
- **GUI-only**: the plot is shown (deferred) when `stdout` is used.
- File outputs are **intentionally not supported** for this action.

**Parameters (`params:`)**

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `show_end_sections` | bool | no | `true` | Draw end-section outlines at `z0` and `z1`. |
| `line_percent` | float | no | `100.0` | Percent (0..100) of generator lines drawn (random subsample). |
| `seed` | int | no | `0` | Random seed used when `line_percent < 100`. |
| `title` | str | no | `"Ruled volume (vertex-connection lines)"` | Plot title. |

**Example**

```yaml
CSF_ACTIONS:
  actions:
    - plot_volume_3d:
        output: [stdout]
        params:
          show_end_sections: true
          line_percent: 25.0
          seed: 123
          title: "Ruled volume preview"
```

---

## `plot_properties`

**Purpose**  
Plot selected section properties along the field axis.

**Stations**: **FORBIDDEN** (this action samples internally).  
**Extra required key** (outside `params`): `properties: [ ... ]` (non-empty).  
**Output**:
- Default: `stdout` → plot shown at end of run.
- If file output(s) exist: plot is saved to image file(s).
- If `stdout` is omitted: file-only (no interactive window).

**Parameters (`params:`)**

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `num_points` | int | no | `100` | Number of sampling points along Z between field endpoints. |

**Example**

```yaml
CSF_ACTIONS:
  actions:
    - plot_properties:
        output: [stdout, out/properties.png]
        params: {num_points: 70}
        properties: [A, Ix, Iy, J_sv]
```

---

## `plot_weight`

**Purpose**  
Plot interpolated polygon weights `w(z)` along the field axis.

**Stations**: **FORBIDDEN** (this action samples internally).  
**Output**: same `stdout`/file-only rules as other plot actions.

**Parameters (`params:`)**

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `num_points` | int | no | `100` | Number of sampling points along Z between field endpoints. |

**Example**

```yaml
CSF_ACTIONS:
  actions:
    - plot_weight:
        output: [stdout, out/weights.png]
        params: {num_points: 120}
```

---

## `weight_lab_zrelative` (text-only)

**Purpose**  
Inspect user-defined weight-law expressions evaluated at **relative-z** stations.

**Why**  
It is a diagnostic action to verify that `W(z)` behaves as expected without writing Python.

**Stations**: **REQUIRED**, but interpreted as **relative coordinates** (user responsibility).  
**Extra required key** (outside `params`): `weith_law: ['expr1', 'expr2', ...]` (non-empty).  
**Output**:
- `stdout` → prints the inspector report.
- file paths → write the same report to those file(s).
- omit `stdout` → file-only.

**Important**  
- `L_total` is computed as `field.s1.z - field.s0.z`.  
- The action prints warnings if provided relative stations are outside `[0, L_total]`.

**Parameters**: none.

**Example**

```yaml
CSF_ACTIONS:
  stations:
    # Relative coordinates (not absolute global z)
    z_rel: [0.0, 2.0, 4.0]
  actions:
    - weight_lab_zrelative:
        stations: [z_rel]
        output: [stdout, out/weight_lab.txt]
        weith_law:
          - "w0 + (w1-w0) * (z/L)"         # linear
          - "w0 + (w1-w0) * np.sin(z/L)"   # sinusoidal
```

---

## `section_area_by_weight`

**Purpose**  
Produce a **per-polygon net-area report** at each station, with optional **visual grouping by weight** `W(z)`.

This action is a *sectional diagnostic* (transverse geometry + effective weights). It does **not** solve any longitudinal/mechanical problem.

**Concept** (nesting-only geometry; no intersections)
- Each polygon has at most one **immediate container** (or none).
- **Effective weight** per polygon is evaluated at the station: `W(z)` (as returned by `polygon_surface_w1_inners0`).
- **Net surface per polygon** is computed with the local rule:
  - `A_net = A(poly) - sum(A(direct_inners))`
  - interpreted as “`w(poly)=1` and `w(inners)=0`”.
- For each polygon the report shows `A_net` and `A_net * W(z)`.
 occupied Surface
- Polygons can be displayed:
  - **grouped by weight** (visual grouping; one `W` label per group), or
  - **flat in id order**.

**Stations**: **REQUIRED**.

**Output**
- If `output` is omitted → default is `[stdout]`.
- `stdout` → one report block per station.
- `*.txt` → captured text report.
- `*.csv` → tabular output (one row per polygon).
- If `output` contains files but **does not** contain `stdout`, then nothing is printed to stdout.

**Parameters (`params:`)**

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `group_mode` | str | no | `"weight"` | `"weight"` groups rows visually by `W(z)`; `"id"` prints a flat table sorted by polygon id (id is the first column). |
| `w_tol` | float | no | `0.0` | Weight binning tolerance used only when `group_mode="weight"`. If `> 0`, weights are binned as `W_bin = round(W / w_tol) * w_tol`. If `<= 0`, grouping uses exact `W`. |
| `include_per_polygon` | bool | no | `false` | If true, include per-polygon extra columns: `direct_inners` and `container`. |
| `fmt_display` | str | no | `.6f` | Python numeric format for stdout/text report (e.g. `.6f`, `.4e`). Alias accepted: `fmt_diplay`. |

Notes
- Polygon ids are **0-based**.
- Each polygon is assumed to have a consistent `(s0.name, s1.name)` pairing in order; missing mapping is treated as an error.
- Unknown/legacy parameters (e.g. `zero_w_eps`) are ignored with a **warning**.

**Example**

```yaml
CSF_ACTIONS:
  stations:
    s_dense: [0.0, 2.5, 5.0]
  actions:
    - section_area_by_weight:
        stations: [s_dense]
        output: [stdout, out/area_by_weight.csv, out/area_by_weight.txt]
        params:
          group_mode: "weight"
          w_tol: 0.0
          include_per_polygon: false
          fmt_display: ".6f"
```

---
## `volume`

**Purpose**  
Produce a **per-polygon volume-style report** between exactly two stations `z1` and `z2`, using the same *accounting* concept previously used for areas:

- **Occupied quantity**: integrate the *net occupied surface* of each polygon (polygon counted as 1, its direct inners counted as 0).
- **Homogenized occupied quantity**: integrate the same net occupied surface multiplied by the polygon weight function `w(z)`.

This action is **not** meant for structural calculations. It is intended to help *describe what each polygon is made of* (composition/weighting law) and to support accounting-style quantity summaries.

---

### Concept (accounting surface extended to a longitudinal integral)

For a polygon `p` at a longitudinal coordinate `z`:

1) **Net occupied surface** (accounting rule)

- treat the polygon as `w=1`
- treat its **direct inners** (holes) as `w=0`

So the net occupied surface is:

- `A_net(p,z) = A(p,z) - sum(A(i,z) for i in direct_inners(p))`

2) **Weighted net occupied surface**

- `A_w(p,z) = A_net(p,z) * w(p,z)`

where `w(p,z)` follows the polygon `weight_law` (or `none`).

3) **Integrated quantities between two stations**

For the two stations `z1` and `z2`:

- `V_occ(p)  = ∫[z1,z2] A_net(p,z) dz`
- `V_hom(p)  = ∫[z1,z2] A_w(p,z) dz`

The report shows both values per polygon. `V_hom` is provided for completeness; if `w(z) ≡ 1` on the interval, then `V_hom = V_occ`.

> Note on interpretation: these are “volume-like” integrated quantities. Do not attach a physical unit here unless your project defines one.

---

## Stations

**REQUIRED**.  
For this action the `stations` entry must expand to **exactly two** absolute z-values, interpreted as the integration limits:

- `z1` = first station value
- `z2` = second station value

If the station set expands to anything other than 2 values, the action must raise an error.

---

## Output

- If `output` is omitted → default is `[stdout]`.
- `stdout` → prints a single report block.
- `*.txt` → writes the same report block as text.
- `*.csv` → writes a table, one row per polygon.
- If `output` contains files but **does not** include `stdout`, nothing is printed to stdout.

---

## Parameters (`params:`)

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `n_points` | int | no | `20` | Number of Gauss–Legendre integration points (>= 1). Higher = more accurate for strongly varying laws. |
| `fmt_display` | str | no | `.6f` | Python numeric format for stdout/txt report (e.g. `.6f`, `.4e`). Alias accepted: `fmt_diplay`. |
| `w_tol` | float | no | `0.0` | Kept for compatibility. Not required for this action. (If present it may be ignored or warned, depending on your validation policy.) |

Notes
- Polygon ids are **0-based**.
- Each polygon is assumed to have a consistent `(s0.name, s1.name)` pairing in order; missing mapping is treated as an error.
- The report includes `w(z1)`, `w(z2)` and `weight_law` to document how the polygon weight varies across the interval.

---

## Report format (illustrative)

The report header identifies the two stations:

```
VOLUME POLYGON LIST REPORT at z=<z1> and z=<z2>
```

Then a table with at least:

- `id` (polygon index)
- `s0.name`, `s1.name` (endpoint pairing names)
- `w(z1)`, `w(z2)` (weight values at the interval endpoints)
- `weight_law` (string, or `none`)
- `Volume Occupied` (V_occ)
- `Homogenized Volume Occupied` (V_hom)

Finally:

- `Total Occupied Volume` = sum over polygons of `V_occ`
- `Total Occupied Homogenized Volume` = sum over polygons of `V_hom`

---

## Example

```yaml
CSF_ACTIONS:
  stations:
    station_edge: [0.0, 30.0]   # MUST contain exactly 2 z values

  actions:
    - volume:
        stations: station_edge
        output: [stdout, out/volume.txt, out/volume.csv]   # optional; default is [stdout]
        params:
          n_points: 20
          fmt_display: ".6f"
          w_tol: 0.0
```
---

## `export_yaml`

**Purpose**  
Export a new CSF geometry YAML built from **exactly two stations**.

**Stations**: **REQUIRED**  
- The referenced station set must expand to **EXACTLY TWO** z values: `[z0, z1]`.

**Output**: **REQUIRED and file-only**
- Output must be exactly one YAML path (`*.yaml` or `*.yml`).
- `stdout` is **not allowed**.

**Implementation**  
Calls: `ContinuousSectionField.write_section(z0, z1, yaml_path)`.

**Parameters**: none.

**Example**

```yaml
CSF_ACTIONS:
  stations:
    two_pts: [1.0, 4.0]   # MUST be exactly two values
  actions:
    - export_yaml:
        stations: [two_pts]
        output: [out/exported_geometry.yaml]
```

---

## `write_opensees_geometry`

**Purpose**  
Export an **OpenSees Tcl geometry file** (sections + stations) intended for `forceBeamColumn` workflows.

**Stations**: **FORBIDDEN** (must not be provided).  
**Output**: **REQUIRED and file-only**
- Exactly one `*.tcl` path.
- `stdout` is **not allowed**.

**Parameters (`params:`)** — all **required**

| name | type | required | meaning |
|---|---:|:---:|---|
| `n_points` | int | yes | Number of integration/sampling points along the member. |
| `E_ref` | float | yes | Reference Young’s modulus written into exported elastic sections. |
| `nu` | float | yes | Poisson ratio (isotropic assumption; exporter derives `G_ref`). |

**Example**

```yaml
CSF_ACTIONS:
  actions:
    - write_opensees_geometry:
        output: [out/geometry.tcl]
        params:
          n_points: 7
          E_ref: 2.1e+11
          nu: 0.30
```

---

## `write_sap2000_geometry`

**Purpose**  
Write a **SAP2000 template-pack text file** (copy/paste helper) derived from the CSF field.

**Stations**: **FORBIDDEN** (must not be provided).  
**Output**: **REQUIRED and file-only**
- Exactly one output path (commonly `*.txt`).
- `stdout` is **not allowed**.

**Notes**
- The action forces `show_plot = False` (headless-safe).
- If `include_plot: true`, a PNG preview may be saved to `plot_filename` if matplotlib is available.
- `mode` controls whether joints are described on centroidal axis, reference axis, or both (you must choose one block to paste into SAP2000).

**Parameters (`params:`)**

| name | type | required | default | meaning |
|---|---:|:---:|---:|---|
| `n_intervals` | int | yes | — | Number of Lobatto intervals; stations = `n_intervals + 1`. |
| `E_ref` | float | yes | — | Suggested Young’s modulus printed in the template header. |
| `nu` | float | yes | — | Suggested Poisson ratio printed in the template header (also prints `G_ref`). |
| `material_name` | str | no | `"S355"` | Label used in SAP2000 copy/paste blocks. |
| `mode` | str | no | `"BOTH"` | One of `CENTROIDAL_LINE`, `REFERENCE_LINE`, `BOTH`. |
| `include_plot` | bool | no | `true` | If true, writes a PNG preview plot (file-only). |
| `plot_filename` | str | no | `"section_variation.png"` | PNG filename/path for the preview plot. |

**Example**

```yaml
CSF_ACTIONS:
  actions:
    - write_sap2000_geometry:
        output: [out/sap2000_template_pack.txt]
        params:
          n_intervals: 6
          material_name: "S355"
          E_ref: 2.1e+11
          nu: 0.30
          mode: "BOTH"
          include_plot: true
          plot_filename: "out/section_variation.png"
```

---

