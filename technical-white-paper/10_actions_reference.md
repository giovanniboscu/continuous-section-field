# 10_actions_reference.md
# CSF Actions Reference

This document is a reference for **CSFActions**.
It lists all supported actions, their required/forbidden keys, parameters, defaults,
and output rules. No conceptual explanations are included here; see the other chapters
for theory and examples.

---

## Global Structure (actions.yaml)

```yaml
CSF_ACTIONS:
  version: 0.1

  stations:            # optional, but required by many actions
    station_name:
      - z1
      - z2

  actions:             # REQUIRED, must be a list
    - action_name:
        stations: [...]    # optional / required / forbidden (action-specific)
        output: [...]      # optional (default: [stdout])
        params: {...}      # optional (action-specific)
```

### Global rules
- `actions` **must be a list**.
- `actions` must appear **exactly once**.
- Output folders must exist (CSF does not create directories).
- Scientific notation: prefer `2.1e+11`.

---

## Output Semantics

- If `output` is omitted → `output: [stdout]`
- If `output` exists and does **not** include `stdout` → file-only execution
- Some actions **forbid `stdout`** (file-only by design)

---

## Station Semantics

- Absolute stations: interpreted as real `z` coordinates.
- Relative stations: **only** for `weight_lab_zrelative`.
- Station values must lie within `[z0, z1]` of the CSF field (when absolute).

---

## Action Reference Table (Summary)

| Action | Stations | Extra Required Keys | Output Type |
|------|---------|---------------------|-------------|
| section_full_analysis | REQUIRED | — | stdout / csv / txt |
| section_selected_analysis | REQUIRED | properties | stdout / csv / txt |
| plot_section_2d | REQUIRED | — | display / image |
| plot_volume_3d | FORBIDDEN | — | display only |
| plot_properties | FORBIDDEN | properties | display / image |
| plot_weight | FORBIDDEN | — | display / image |
| weight_lab_zrelative | REQUIRED | weith_law | stdout / txt |
| export_yaml | REQUIRED (2 z) | — | file-only |
| write_opensees_geometry | FORBIDDEN | — | file-only |
| write_sap2000_geometry | FORBIDDEN | — | file-only |
| write_samp2000_geometry | FORBIDDEN | — | file-only (alias) |

---


## 1. section_selected_analysis

**Purpose**  
Compute a reduced set of properties.

**Stations**: REQUIRED

**Required keys**
- `properties` (non-empty list)

**Parameters**
- `fmt_diplay` (str, default `.8f`)

**Output**
- stdout
- `.csv`
- optional text file

---

## 2. plot_section_2d

**Purpose**  
Plot 2D section geometry at specified stations.

**Stations**: REQUIRED

**Parameters**
- `show_ids` (bool, default `true`)
- `show_weights` (bool, default `true`)
- `show_vertex_ids` (bool, default `false`)
- `title` (str, optional, supports `{z}`)
- `dpi` (int, default `150`)

**Output**
- interactive display (stdout)
- optional image file

---

## 3. plot_volume_3d

**Purpose**  
Visualize the ruled 3D volume between end sections.

**Stations**: FORBIDDEN

**Parameters**
- `show_end_sections` (bool, default `true`)
- `line_percent` (float, default `100.0`)
- `seed` (int, default `0`)
- `title` (str, default `"Ruled volume (vertex-connection lines)"`)

**Output**
- interactive display only

---

## 4. plot_properties

**Purpose**  
Plot selected properties along the member.

**Stations**: FORBIDDEN

**Required keys**
- `properties` (non-empty list)

**Parameters**
- `num_points` (int, default `100`)

**Output**
- interactive plot
- optional image file

---

## 5. plot_weight

**Purpose**  
Plot polygon weight evolution along `z`.

**Stations**: FORBIDDEN

**Parameters**
- `num_points` (int, default `100`)

**Output**
- interactive plot
- optional image file

---

## 6. weight_lab_zrelative

**Purpose**  
Inspect weight-law expressions at **relative z** values.

**Stations**: REQUIRED (relative)

**Required keys**
- `weith_law` (list of strings)

**Output**
- stdout
- optional text file

**Notes**
- Relative-z interpretation is entirely user-controlled.
- Key spelling `weith_law` is enforced.

---

## 7. export_yaml

**Purpose**  
Export a new CSF geometry YAML from two stations.

**Stations**: REQUIRED (exactly two values)

**Output**
- file-only (`.yaml` / `.yml`)
- `stdout` forbidden

---

## 8. write_opensees_geometry

**Purpose**  
Export OpenSees-compatible Tcl geometry and sections.

**Stations**: FORBIDDEN

**Required parameters**
- `n_points` (int)
- `E_ref` (float)
- `nu` (float)

**Output**
- file-only (`.tcl`)

---

## 9. write_sap2000_geometry

**Purpose**  
Generate a SAP2000 text template pack.

**Stations**: FORBIDDEN

**Required parameters**
- `n_intervals` (int)
- `E_ref` (float)
- `nu` (float)

**Optional parameters**
- `material_name` (str, default `"S355"`)
- `mode` (str, default `"BOTH"`)
- `include_plot` (bool, default `true`)
- `plot_filename` (str, default `"section_variation.png"`)

**Output**
- file-only (`.txt`)
- `stdout` forbidden

---

## 10. write_samp2000_geometry

Alias for `write_sap2000_geometry` (typo tolerance).
All rules and parameters are identical.

---

## Validation Checklist

- Root key `CSF_ACTIONS` exists
- `actions` is a list and unique
- Required stations present
- Output folders exist
- `stdout` not used where forbidden

---

End of action reference.
