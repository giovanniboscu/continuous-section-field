# Expected results when running `csf-actions histwin_tower.yaml action.yaml`

This note explains **what should be expected from the execution** of:

```bash
csf-actions histwin_tower.yaml action.yaml
```

The directives that control the execution are the ones already defined in the previously described `action.yaml`.

So the expected results do **not** come from generic CSF behavior alone.  
They come from the **specific station sets, actions, outputs, and parameters** declared in that file.

---

## What the command does

The command reads:

- `histwin_tower.yaml` as the **geometry/model input**;
- `action.yaml` as the **execution plan**.

CSF then executes the actions listed in `CSF_ACTIONS`, in sequence, using the stations and parameters declared there.
	
So, when this command is run, the user should expect:

- some results printed directly in the terminal,
- some text reports written to the `out/` folder,
- some image files generated in the `out/` folder,
- and one export file for downstream structural workflows.

---

## Expected terminal output

Some actions explicitly include:

```yaml
output:
  - stdout
```

This means part of the execution is expected to print information directly to the console.

From this file, terminal output is expected from:

- `plot_weight`
- `plot_properties`
- `volume`
- `section_area_by_weight`

So during execution, the console should show reports or summaries related to:

- weight evolution along `z`,
- selected property plotting activity,
- integrated volume results,
- grouped area-by-weight results.

The exact formatting depends on the implementation of each action, but terminal activity is expected and normal.

---

## Expected generated files

Based on the `output` fields in the action file, the following files are expected.

### 1. Section report
```text
out/histwin_properties.txt
```

Produced by:

- `section_selected_analysis`

Expected content:

- section geometry description at the requested stations,
- numerical section properties at the tower base and top.

Because this action uses:

```yaml
stations: station_ends
```

the report is expected to contain results only for:

- `z = 0.0`
- `z = 76.15`

Expected properties include:

- `A`
- `Cx`, `Cy`
- `Ix`, `Iy`, `Ixy`
- `Ip`
- `I1`, `I2`
- `rx`, `ry`
- `Wx`, `Wy`
- `J_sv_cell`
- `Q_na`
- `J_s_vroark`
- `J_s_vroark_fidelity`

So this file should be read as the **discrete end-section property report**.

---

### 2. Weight plot image
```text
out/histwin_weights.jpg
```

Produced by:

- `plot_weight`

Expected content:

- a plot showing how polygon weights or homogenization factors vary along the tower height.

This image should help verify that the longitudinal weight laws are being applied as intended.

So the user should expect a **visual representation of `w(z)` behavior**.

---

### 3. Continuous property plot image
```text
out/histwin_properties.jpg
```

Produced by:

- `plot_properties`

Expected content:

- continuous curves along `z` for:
  - `A`
  - `I1`
  - `Ip`
  - `J_sv_cell`

Because:

```yaml
num_points: 80
```

the curves are expected to be built from 80 internal evaluation points between base and top.

So this plot should provide a **smooth longitudinal view** of how the selected section properties evolve along the tower.

---

### 4. Volume report
```text
out/histwin_volume.txt
```

Produced by:

- `volume`

Expected content:

- integrated occupied volume,
- integrated homogenized volume.

Since the action uses Gauss-Legendre quadrature with:

```yaml
n_points: 10
```

the values are expected to be numerically integrated along the tower height.

So this file should be read as the **global volume summary** for the member.

---

### 5. Area-by-weight report
```text
out/histwin_weight.txt
```

Produced by:

- `section_area_by_weight`

Expected content:

- occupied area by weight group,
- homogenized area by weight group,

evaluated at the requested stations.

Because this action also uses:

```yaml
stations: station_ends
```

the report is expected only for:

- base section,
- top section.

Because:

```yaml
include_per_polygon: false
```

the result is expected to be a **grouped summary**, not a detailed polygon-by-polygon listing.

---

### 6. Solver-oriented export file
```text
out/histwin_template_pack.txt
```

Produced by:

- `write_sap2000_geometry`

Expected content:

- station-based export tables,
- geometry/property data for downstream structural use,
- reference material metadata,
- reference elastic parameters.

In this configuration, the export uses:

```yaml
stations: station_dense
```

so the export is expected to be based on the explicitly defined station list:

- `0.0`
- `10.0`
- `21.8`
- `30.0`
- `38.075`
- `48.4`
- `60.0`
- `76.15`

Since stations are explicitly given, the comment indicates that `n_intervals: 10` is not the active driver for station generation in this case.

So this file should be interpreted as the **discrete solver-export package** based on the chosen dense stationing.

---

## Expected graphical behavior during execution

The action file contains:

```yaml
- plot_volume_3d:
```

with:

- `line_percent: 60.0`
- `seed: w`
- `title: "Histwin"`

So, during execution, the user should expect a 3D visualization of the ruled tower volume.

This is intended as a geometric consistency check.

What should be expected from it:

- the overall tower shape should appear visually coherent from base to top;
- interpolation between the two reference sections should look continuous;
- the reduced line percentage should make the view less crowded;
- the `seed: w` setting should activate the weight-driven appearance mode described in the action logic.

Whether this plot is only shown interactively or also saved depends on the specific implementation of `plot_volume_3d` and the execution environment.  
In this file, no explicit image output path is declared for that action.

So the safe expectation is:

- a 3D plot attempt should occur;
- but no dedicated saved file is explicitly requested for this action in the YAML.

---

## Expected station usage by action

A key point is that not all actions use stations in the same way.

### Actions expected to use `station_ends`
- `section_selected_analysis`
- `volume`
- `section_area_by_weight`

So these actions should work on:

- `z = 0.0`
- `z = 76.15`

### Action expected to use `station_dense`
- `write_sap2000_geometry`

So this export should use the eight explicitly declared tower stations.

### Action expected to ignore named station sets and use internal sampling
- `plot_properties`

This action is expected to build its own continuous sampling using:

```yaml
num_points: 80
```

### Action that defines its own plotting behavior
- `plot_weight`
- `plot_volume_3d`

These are plotting-oriented actions, with behavior driven mainly by their own internal logic and parameters.

---

## What should be considered a successful execution

A successful run of:

```bash
csf-actions histwin_tower.yaml action.yaml
```

should normally result in all of the following:

1. CSF reads the geometry and action files without YAML or parsing errors.
2. The requested actions are executed in sequence.
3. Terminal output appears for the actions configured with `stdout`.
4. The expected text files are created in `out/`.
5. The expected `.jpg` plots are created in `out/`.
6. The solver export file is written successfully.
7. The 3D geometric plot is generated or shown according to the runtime environment.

In practical terms, after execution, the user should expect the `out/` directory to contain at least:

```text
out/histwin_properties.txt
out/histwin_weights.jpg
out/histwin_properties.jpg
out/histwin_volume.txt
out/histwin_weight.txt
out/histwin_template_pack.txt
```

---

## What should not be expected

From this specific `action.yaml`, the user should **not** expect:

- modal analysis results,
- solver run results,
- OpenFAST results,
- BModes results,
- automatic structural verification,
- automatic design checks.

This file is a **CSF post-processing and export workflow**.  
It computes, plots, summarizes, and exports section-related information from the CSF model.

---

## Operational reading of the results

The execution should produce four categories of output:

### 1. Visual checks
Used to inspect whether the geometry and the weight evolution look reasonable.

Expected items:

- 3D volume plot
- weight plot
- property plot

### 2. Local discrete reports
Used to inspect selected stations directly.

Expected items:

- end-section report
- end-section area-by-weight report

### 3. Global integrated report
Used to summarize the full tower along `z`.

Expected item:

- integrated volume report

### 4. Downstream export
Used to transfer section-property information to external workflows.

Expected item:

- solver-oriented template/export pack

---

## One-line summary

When running `csf-actions histwin_tower.yaml action.yaml`, the expected result is a complete CSF post-processing run that prints selected summaries to the console, generates reports and plots in `out/`, evaluates end sections and dense export stations as specified in the YAML, and produces a solver-oriented export file for downstream use.


