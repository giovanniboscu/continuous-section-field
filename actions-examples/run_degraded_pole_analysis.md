# Run the degraded-pole analysis

This guide contains the commands required to run the complete degraded-pole example from a fresh clone of the repository.

The analysis uses the final model already included in the repository:

- [`degradated_pole.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/degradated_pole.yaml);
- [`pole_analysis_settings.yaml`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/pole_analysis_settings.yaml);
- [`cantilever_beam_pole.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/degraded_pole/cantilever_beam_pole.py).

For the first test, use the committed `degradated_pole.yaml` directly. Regenerating or editing the model is not required.

---

## 1. Linux and macOS

Open a terminal and run:

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

Move to the example directory:

```bash
cd actions-examples/degraded_pole
```

Run the analysis:

```bash
python cantilever_beam_pole.py pole_analysis_settings.yaml
```

The script prints the progress of the calculation, one analysed elevation at a time.

A successful run ends with a message similar to:

```text
CSF cantilever pole check completed.
Written files:
  - ...
```

Inspect the generated output directory:

```bash
ls -lh output
```

Read the beginning of the mechanical report:

```bash
head -n 60 output/mechanical_report.txt
```

The complete report can be opened with any text editor.

---

## 2. Windows PowerShell

Open PowerShell and run:

```powershell
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

Move to the example directory:

```powershell
cd actions-examples\degraded_pole
```

Run the analysis:

```powershell
python .\cantilever_beam_pole.py .\pole_analysis_settings.yaml
```

The script prints the progress of the calculation, one analysed elevation at a time.

A successful run ends with a message similar to:

```text
CSF cantilever pole check completed.
Written files:
  - ...
```

Inspect the generated output directory:

```powershell
Get-ChildItem .\output
```

Read the beginning of the mechanical report:

```powershell
Get-Content .\output\mechanical_report.txt -TotalCount 60
```

The complete report can be opened with any text editor.

---

## 3. Files produced by the analysis

The analysis writes its results to:

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

The complete output documentation can be read after confirming that the analysis runs successfully.

---

## 4. Run the analysis again

After changing the settings or the degradation laws, return to:

```text
actions-examples/degraded_pole
```

and run the same command again.

Linux or macOS:

```bash
python cantilever_beam_pole.py pole_analysis_settings.yaml
```

Windows PowerShell:

```powershell
python .\cantilever_beam_pole.py .\pole_analysis_settings.yaml
```

The files in the `output` directory are rewritten with the results of the new calculation.

---

## 5. Important execution directory

Run `cantilever_beam_pole.py` from:

```text
actions-examples/degraded_pole
```

The example settings refer to the model and output directory using paths relative to this example.

The model also uses lookup files stored under:

```text
actions-examples/degraded_pole/laws/
```

Running the command from the example directory keeps the complete example structure together and makes the generated outputs easy to locate.

---

## 6. Quick installation check

Before running the analysis, the CSF installation can be checked with:

```bash
python -c "import csf; print(csf.__file__)"
```

On Windows PowerShell, the same command is:

```powershell
python -c "import csf; print(csf.__file__)"
```

For an editable installation, the printed path should point to the cloned repository.

---

## 7. Optional clean run

To remove the previously generated result files before a new run, keep the `output` directory and delete only its contents.

Linux or macOS:

```bash
rm -f output/*.csv output/*.txt
python cantilever_beam_pole.py pole_analysis_settings.yaml
```

Windows PowerShell:

```powershell
Remove-Item .\output\*.csv, .\output\*.txt -ErrorAction SilentlyContinue
python .\cantilever_beam_pole.py .\pole_analysis_settings.yaml
```

The analysis recreates the required output files.
