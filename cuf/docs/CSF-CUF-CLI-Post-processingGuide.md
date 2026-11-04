# CSF-CUF CLI Post-processing Guide

## 1. Purpose

This document describes how to generate CSF-CUF displacement, strain, and stress post-processing results **from the command line only**.

The examples use the CLI module:

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10
```

The workflow is designed around two main CSF-CUF inputs:

- a **CSF YAML model**, which defines the model and cross-section information;
- a compiled **CUF checkpoint** (`.cuf.npz`), which contains the solved displacement field.

An optional FEM3D result file can be supplied when a CSF-CUF/FEM3D comparison is required.

> The commands below are standalone CLI examples. No wrapper shell script is required.

---

## 2. Basic CLI structure

The general form is:

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml <model.yaml> \
  --checkpoint <solution.cuf.npz> \
  [mode-specific options] \
  --output-dir <output_directory>
```

To inspect the complete set of options available in the installed version:

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 --help
```

### Main input arguments

| Option | Required | Description | Example |
|---|---:|---|---|
| `--csf-yaml` | Yes | Path to the original CSF YAML model. | `models/beam.yaml` |
| `--checkpoint` | Yes | Path to the compiled CUF displacement checkpoint. | `output/beam_eq1.cuf.npz` |
| `--fem3d` | No | FEM3D result file used for comparison plots. | `fem3d/output/beam.npz` |
| `--output-dir` | Yes for the examples below | Directory where PNG and CSV results are written. | `plot_results/maps` |

---

## 3. Available plotting workflows

The CLI can be used in three useful post-processing workflows.

| Workflow | Main purpose | Typical output |
|---|---|---|
| Transverse section maps | Plot a field over the Y-Z section at a selected longitudinal coordinate `x`. | Cross-section PNG maps and corresponding CSV data. |
| Transverse perimeter plots | Sample the selected Y-Z section along polygon perimeters and compare CSF-CUF with FEM3D when provided. | Perimeter PNG plots and CSV data. |
| Longitudinal boundary plots | Sample section polygon vertices/boundaries along the beam axis. | Multi-panel longitudinal PNG plots and CSV data. |

---

# 4. Transverse section maps

## 4.1 What this mode does

A transverse map evaluates a requested result field on the Y-Z cross-section at a fixed longitudinal position.

For example, with:

```text
x = 500
```

the plot represents the field on the Y-Z section at `x = 500`.

A generated example is `epsilon_xx_transverse.png`, where the color map represents `epsilon_xx` over the section.

## 4.2 CLI command

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/carrera_i_shaped_taper80_l9_web3.yaml \
  --checkpoint output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --transverse-x 500.0 \
  --output-dir plot_results/maps
```

### Relevant options

| Option | Meaning | Example |
|---|---|---|
| `--transverse-x` | Longitudinal coordinate where the Y-Z section is evaluated. | `500.0` |
| `--output-dir` | Destination directory for generated transverse files. | `plot_results/maps` |

## 4.3 Example generated files

```text
plot_results/
└── maps/
    ├── epsilon_xx_transverse.png
    ├── epsilon_xx_transverse.csv
    └── ...
```

The supplied `epsilon_xx_transverse.csv` uses a table structure equivalent to:

| Column | Meaning |
|---|---|
| `record_type` | Record category, normally `sample`. |
| `panel_id` | Plot panel identifier. |
| `panel_title` | Human-readable panel name. |
| `series` | Result source, for example `CSF-CUF`. |
| `component` | Component name, for example `epsilon_xx`. |
| `kind` | Physical result class, for example `strain`. |
| `polygon_index` | Cross-section polygon identifier. |
| `polygon_name` | Cross-section polygon name. |
| `x` | Physical longitudinal coordinate. |
| `x_over_L` | Normalized longitudinal coordinate. |
| `y`, `z` | Cross-section coordinates. |
| `value` | Evaluated result value. |

Example interpretation:

```text
x = 500.0
x/L = 0.5
component = epsilon_xx
series = CSF-CUF
```

This means that each CSV row stores one sampled point of the `epsilon_xx` field on the section at the midpoint of the longitudinal domain.

---

# 5. Transverse perimeter plots

## 5.1 What this mode does

This mode converts the polygon boundary of the selected cross-section into a one-dimensional perimeter coordinate.

Instead of plotting a field over the complete Y-Z area, the result is sampled **along the perimeter**. This is useful for:

- inspecting values along flanges, webs, or other polygon boundaries;
- comparing CSF-CUF and FEM3D values on the same section;
- identifying changes at polygon vertices and edges;
- sampling either the original boundary or a slightly inward-shifted path.

A generated example is `epsilon_xx_along_perimeter.png`.

## 5.2 CLI command with FEM3D comparison

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/carrera_i_shaped_taper80_l9_web3.yaml \
  --checkpoint output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --fem3d fem3d/output/fem3d_taper.npz \
  --transverse-x 500.0 \
  --transverse-perimeter-only \
  --transverse-perimeter-points 201 \
  --transverse-inward-offset 0.1 \
  --fem-stress-from-element \
  --output-dir plot_results/perimeters
```

### Relevant options

| Option | Meaning | Example |
|---|---|---|
| `--transverse-x` | Longitudinal location of the section. | `500.0` |
| `--transverse-perimeter-only` | Selects perimeter plotting instead of full transverse maps. | flag |
| `--transverse-perimeter-points` | Number of perimeter samples. | `201` |
| `--transverse-inward-offset` | Distance used for an inward-shifted sampling path. | `0.1` |
| `--fem3d` | FEM3D result file for comparison. | `fem3d/output/fem3d_taper.npz` |
| `--fem-stress-from-element` | Uses FEM element-based stress recovery for FEM3D stress comparison. | flag |
| `--output-dir` | Destination directory. | `plot_results/perimeters` |

## 5.3 Perimeter coordinate

The perimeter CSV contains both the physical distance and a normalized perimeter coordinate.

| Column | Meaning |
|---|---|
| `s` | Distance from the start of the polygon perimeter. |
| `s_over_perimeter` | Normalized perimeter coordinate, usually from `0` to `1`. |
| `perimeter_length` | Total polygon perimeter length. |
| `vertex_index` | Vertex index when the sample lies exactly on a vertex. |
| `edge_index` | Polygon edge containing the sample. |
| `edge_fraction` | Local interpolation coordinate along the edge. |

The remaining fields identify the result source, component, cross-section polygon, coordinates, and value.

### Example CSV columns

```text
record_type,panel_id,panel_title,series,component,kind,
polygon_index,polygon_name,sample_index,vertex_index,edge_index,
edge_fraction,element_id,stress_source,x,x_over_L,y,z,
s,s_over_perimeter,perimeter_length,value
```

## 5.4 Example generated files

```text
plot_results/
└── perimeters/
    ├── epsilon_xx_along_perimeter.png
    ├── epsilon_xx_along_perimeter.csv
    └── ...
```

When FEM3D is supplied, the plot can contain two result series, for example:

| Series | Interpretation |
|---|---|
| `CSF-CUF` | Result recovered from the compiled CUF solution. |
| `FEM3D (H8 displacement/strain)` | FEM3D reference result recovered from the H8 model. |

---

# 6. Longitudinal boundary plots

## 6.1 What this mode does

Longitudinal boundary mode follows selected cross-section polygon vertices or boundary points along the beam axis.

For each monitored point `(y, z)`, the horizontal coordinate is the longitudinal position. A normalized form is commonly shown as:

```text
s = (x - x0) / L
```

where:

- `x0` is the start of the longitudinal domain;
- `L` is the longitudinal length;
- `s = 0` corresponds to the start;
- `s = 1` corresponds to the end.

A generated example is `epsilon_xx_along_boundary_part01.png`, which contains several panels such as `polygon 1 vertex 0`, `polygon 1 vertex 1`, and so on.

## 6.2 CLI command

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/carrera_i_shaped_taper80_l9_web3.yaml \
  --checkpoint output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --fem3d fem3d/output/fem3d_taper.npz \
  --stress-mode boundary \
  --points 201 \
  --inward 5 \
  --fem-stress-from-element \
  --output-dir plot_results/longitudinal
```

### Relevant options

| Option | Meaning | Example |
|---|---|---|
| `--stress-mode boundary` | Selects longitudinal boundary/vertex sampling. | `boundary` |
| `--points` | Number of longitudinal sampling points. | `201` |
| `--inward` | Requests inward sampling relative to the original boundary; the exact geometric interpretation follows the installed CLI implementation. | `5` |
| `--fem3d` | Optional FEM3D result file for comparison. | `fem3d/output/fem3d_taper.npz` |
| `--fem-stress-from-element` | Uses FEM element-based stresses for FEM3D comparisons. | flag |
| `--output-dir` | Destination directory. | `plot_results/longitudinal` |

> Use `--help` to confirm the exact accepted range and semantics of `--inward` for the installed version.

## 6.3 Longitudinal CSV structure

The supplied boundary data contains fields such as:

```text
record_type,panel_id,panel_title,series,component,kind,point,
polygon_index,polygon_name,vertex_index,vertex_aliases,
element_id,stress_source,x,x_over_L,y,z,value
```

Important columns are:

| Column | Meaning |
|---|---|
| `panel_title` | Identifies the polygon and vertex displayed in a panel. |
| `point` | Stable textual identifier for the sampled boundary point. |
| `polygon_index` | Polygon number. |
| `polygon_name` | Polygon/domain name. |
| `vertex_index` | Vertex number inside the polygon. |
| `vertex_aliases` | Alias associated with the vertex. |
| `x` | Longitudinal coordinate. |
| `x_over_L` | Normalized longitudinal coordinate. |
| `y`, `z` | Cross-section coordinates of the monitored point. |
| `series` | Source of the result: CSF-CUF or FEM3D. |
| `element_id` | FEM element identifier when applicable. |
| `stress_source` | FEM stress source when applicable. |
| `value` | Recovered displacement, strain, or stress component. |

For the supplied example, one CSF-CUF boundary series for `epsilon_xx` reaches approximately `-3.0e-4` around `x/L = 0.5` at `(y,z)=(-33,50)`, while returning close to zero at the longitudinal ends.

---

# 7. Result components

The CSF-CUF post-processing workflow can work with displacement, strain, and stress quantities.

A related CSF-CUF plotting implementation uses the following component convention:

| Category | Components |
|---|---|
| Displacement | `ux`, `uy`, `uz` |
| Normal strain | `epsilon_xx`, `epsilon_yy`, `epsilon_zz` |
| Shear strain | `gamma_yz`, `gamma_xz`, `gamma_xy` |
| Normal stress | `sigma_xx`, `sigma_yy`, `sigma_zz` |
| Shear stress | `tau_yz`, `tau_xz`, `tau_xy` |

The CUF workflow evaluates the compiled displacement field and its strain field at physical points. In the related implementation, stresses are obtained from the CUF constitutive provider using:

```text
sigma = C * epsilon
```

so the constitutive matrix is supplied by the CUF model rather than duplicated in the plotting utility.

---

# 8. Recommended directory layout

A clear directory structure is:

```text
plot_results/
├── maps/
│   ├── epsilon_xx_transverse.png
│   ├── epsilon_xx_transverse.csv
│   └── ...
├── perimeters/
│   ├── epsilon_xx_along_perimeter.png
│   ├── epsilon_xx_along_perimeter.csv
│   └── ...
└── longitudinal/
    ├── epsilon_xx_along_boundary_part01.png
    ├── epsilon_xx_along_boundary_part01.csv
    └── ...
```

This keeps section maps, perimeter curves, and longitudinal curves separate and makes automated comparison easier.

---

# 9. Complete CLI example

The following sequence reproduces the three workflows without using a shell wrapper.

## 9.1 Generate transverse maps

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/carrera_i_shaped_taper80_l9_web3.yaml \
  --checkpoint output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --transverse-x 500.0 \
  --output-dir plot_results/maps
```

## 9.2 Generate transverse perimeter comparison

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/carrera_i_shaped_taper80_l9_web3.yaml \
  --checkpoint output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --fem3d fem3d/output/fem3d_taper.npz \
  --transverse-x 500.0 \
  --transverse-perimeter-only \
  --transverse-perimeter-points 201 \
  --transverse-inward-offset 0.1 \
  --fem-stress-from-element \
  --output-dir plot_results/perimeters
```

## 9.3 Generate longitudinal boundary comparison

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/carrera_i_shaped_taper80_l9_web3.yaml \
  --checkpoint output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3/carrera_i_shaped_taper80_lagrangeL9_v4_web3_eq1.cuf.npz \
  --fem3d fem3d/output/fem3d_taper.npz \
  --stress-mode boundary \
  --points 201 \
  --inward 5 \
  --fem-stress-from-element \
  --output-dir plot_results/longitudinal
```

---

# 10. Practical interpretation of the generated plots

| Plot type | Horizontal coordinate | Vertical/color quantity | Best use |
|---|---|---|---|
| Transverse map | Y-Z geometry | Color = requested component | Understand spatial distribution on one cross-section. |
| Perimeter plot | Distance `s` along polygon perimeter | Requested component | Inspect edge/vertex behavior and compare CSF-CUF with FEM3D around the section. |
| Longitudinal boundary plot | `x` or normalized `x/L` | Requested component | Follow selected section vertices/boundary points along the beam length. |

When comparison data is available, the same graph can contain CSF-CUF and FEM3D series. This makes it possible to inspect agreement, discretization effects, boundary effects, and stress/strain recovery differences directly.

---

# 11. Troubleshooting

| Symptom | Check |
|---|---|
| CLI cannot find the module | Run the command from the project environment where `csf` is installed/importable. |
| YAML/checkpoint mismatch | Verify that the checkpoint was generated from the same CSF model and longitudinal domain. |
| FEM3D curves are missing | Confirm that `--fem3d` points to a valid FEM3D result and that the selected comparison mode supports it. |
| Output directory is empty | Run with `--help`, verify arguments, and inspect terminal errors. |
| Too few points on curves | Increase `--points` or `--transverse-perimeter-points`. |
| Perimeter samples are too close to the geometric boundary | Adjust `--transverse-inward-offset` when using transverse perimeter mode. |
| Need exact meaning of a version-specific option | Use `python -m csf.cuf.tools.plot_strain_stress_boundary_v10 --help`. |

---

# 12. Final summary

The CSF-CUF plotting workflow can be used entirely from the CLI.

| Goal | Key CLI options |
|---|---|
| Plot a Y-Z field at one `x` location | `--transverse-x`, `--output-dir` |
| Plot values around a section perimeter | `--transverse-x`, `--transverse-perimeter-only`, `--transverse-perimeter-points`, `--transverse-inward-offset` |
| Plot boundary/vertex values along the beam length | `--stress-mode boundary`, `--points`, optionally `--inward` |
| Compare with FEM3D | `--fem3d`, optionally `--fem-stress-from-element` |

The typical inputs are the CSF YAML model and the compiled CUF checkpoint. The output consists of PNG plots and numerical CSV data. Transverse maps show the field over a cross-section, perimeter plots reduce the cross-section boundary to a one-dimensional path, and longitudinal boundary plots follow selected polygon vertices or boundary locations along the structure.

For a new model, the safest starting sequence is:

```bash
python -m csf.cuf.tools.plot_strain_stress_boundary_v10 --help
```

then run the desired mode with the model-specific YAML, checkpoint, sampling parameters, and output directory.
