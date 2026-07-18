# Run the degraded-pole analysis

This guide contains the commands required to run the complete degraded-pole example from a fresh clone of the repository.

The analysis uses the final model already included in the repository:

- [`degradated_pole.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/degradated_pole.yaml);
- [`pole_analysis_settings.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/pole_analysis_settings.yaml);
- [`cantilever_beam_pole.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/cantilever_beam_pole.py).

For the first test, use the committed `degradated_pole.yaml` directly. Regenerating or editing the model is not required.

---

## 1. Clone and install the repository

Clone the repository and enter its root directory:

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

### Linux and macOS

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows PowerShell

Create and activate a virtual environment:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

### Install CSF

The installation commands are the same on all platforms:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Check that CSF is imported from the cloned repository:

```bash
python -c "import csf; print(csf.__file__)"
```

Move to the example directory:

```bash
cd actions-examples/degraded_pole
```

All the following commands must be run from this directory.

---

## 2. Check the CSF geometry and material fields

Before running the mechanical analysis, inspect the CSF model graphically with `csf-actions`.

Create the output directory.

### Linux and macOS

```bash
mkdir -p out/iso
```

### Windows PowerShell

```powershell
New-Item -ItemType Directory -Force .\out\iso | Out-Null
```

Run the CSF actions:

```bash
csf-actions degradated_pole.yaml action_degradated_pole.yaml
```

`csf-actions` evaluates the model defined in `degradated_pole.yaml` and runs the visualization and section-processing actions configured in `action_degradated_pole.yaml`.

This step allows the following model components to be checked graphically before the mechanical analysis:

- the tapered pole geometry;
- the cross-sections along the pole;
- the axial and bending material-participation field;
- the shear and torsion material-participation field;
- the local differences between concrete regions and prestressing bars.

The generated files are written to:

```text
out/iso
```

After verifying the geometry and material fields, run the sectional mechanical analysis.

---

## 3. Run the mechanical analysis

Run:

```bash
python cantilever_beam_pole.py pole_analysis_settings.yaml
```

The script prints the calculation progress, one analysed elevation at a time.

A successful run ends with a message similar to:

```text
CSF cantilever pole check completed.
Written files:
  - ...
```

The analysis results are written to:

```text
output
```

---

## 4. Inspect the generated results

### Linux and macOS

List the generated files:

```bash
ls -lh output
```

Read the beginning of the mechanical report:

```bash
head -n 60 output/mechanical_report.txt
```

### Windows PowerShell

List the generated files:

```powershell
Get-ChildItem .\output
```

Read the beginning of the mechanical report:

```powershell
Get-Content .\output\mechanical_report.txt -TotalCount 60
```

The complete report can be opened with any text editor.

---

## 5. Files produced by the analysis

The mechanical analysis writes its results to:

```text
actions-examples/degraded_pole/output/
```

The main files are:

```text
mechanical_report.txt
prestress_resultant.csv
internal_actions.csv
navier_stresses.csv
shear_stresses.csv
section_polygons.csv
```

Their roles are:

- `mechanical_report.txt`: compact human-readable summary;
- `prestress_resultant.csv`: residual prestressing force and eccentricities;
- `internal_actions.csv`: signed section actions used by the stress calculations;
- `navier_stresses.csv`: polygon-wise normal-stress envelopes;
- `shear_stresses.csv`: polygon-wise Jourawski shear-stress envelopes;
- `section_polygons.csv`: evaluated polygon geometry at the requested elevations.

The graphical files produced by `csf-actions` remain separate and are written to:

```text
actions-examples/degraded_pole/out/iso/
```

The complete output documentation can be read after confirming that both the graphical check and the mechanical analysis run successfully.

---

## 6. Run the analysis again

After changing the settings or the degradation laws, return to:

```text
actions-examples/degraded_pole
```

Run the graphical check again when the geometry or the material-participation laws have changed:

```bash
csf-actions degradated_pole.yaml action_degradated_pole.yaml
```

Run the mechanical analysis again with:

```bash
python cantilever_beam_pole.py pole_analysis_settings.yaml
```

The files in `out/iso` and `output` are updated with the results of the current model.

---

## 7. Important execution directory

Run both commands from:

```text
actions-examples/degraded_pole
```

The example files use paths relative to this directory.

The CSF model uses lookup files stored under:

```text
actions-examples/degraded_pole/laws/
```

The action configuration writes graphical results under:

```text
actions-examples/degraded_pole/out/iso/
```

The mechanical-analysis settings write sectional results under:

```text
actions-examples/degraded_pole/output/
```

Running the commands from the example directory keeps the model, lookup laws, graphical outputs and mechanical results in the expected locations.

---

## 8. Optional clean run

To remove previously generated results before a new run, keep the output directories and delete only their contents.

### Linux and macOS

```bash
rm -f out/iso/*
rm -f output/*.csv output/*.txt

csf-actions degradated_pole.yaml action_degradated_pole.yaml
python cantilever_beam_pole.py pole_analysis_settings.yaml
```

### Windows PowerShell

```powershell
Remove-Item .\out\iso\* -ErrorAction SilentlyContinue
Remove-Item .\output\*.csv, .\output\*.txt -ErrorAction SilentlyContinue

csf-actions degradated_pole.yaml action_degradated_pole.yaml
python cantilever_beam_pole.py pole_analysis_settings.yaml
```

Both output sets are then recreated from the current model.
