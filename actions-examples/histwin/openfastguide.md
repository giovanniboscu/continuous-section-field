# CSF to BModes to ElastoDyn to OpenFAST

## What this guide covers

This guide starts **from an existing CSF YAML tower model**, for example:

- `histwin_tower.yaml`

It does **not** explain how that YAML was created.

This guide explains only how to run and customize the pipeline **after the YAML already exists**.

---

## 1. What the pipeline does

Starting file:

- `histwin_tower.yaml`

Final objective:

- generate tower properties from CSF,
- run BModes,
- inject BModes mode-shape coefficients into the ElastoDyn tower file,
- generate a minimal structural-only OpenFAST case,
- run `openfast Main.fst` successfully.

Main generated files:

- `histwin_tower_ElastoDyn_Tower.dat`
- `histwin_tower_BModes_tower.bmt`
- `histwin_tower_BModes_tower.bmi`
- `histwin_tower_BModes_tower.out`
- `Main.fst`
- `ElastoDyn.dat`
- `ElastoDyn_Blade.dat`

---

## 2. Files that must already exist

Minimum files:

- `histwin_tower.yaml`
- `csf_to_elastodyn.py`
- `run_csf_to_elastodyn.sh`
- `generate_openfast_case_templates.py`

Optional file:

- `bmodes_out_to_elastodyn.py`

Optional local BModes executable:

- `./BModes/build/bmodes/bmodes`

---

## 3. Prerequisites

### 3.1 Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install csfpy pyyaml numpy
```

### 3.2 BModes

BModes is an executable, not a Python package.

Expected local path:

```text
./BModes/build/bmodes/bmodes
```

Alternative:

```bash
export BMODES_EXE=/absolute/path/to/bmodes
```

### 3.3 OpenFAST

OpenFAST must be callable as:

```bash
openfast
```

---

## 4. Data separation

### 4.1 Produced from CSF

From `histwin_tower.yaml`, the pipeline computes:

- `A(z)`
- `Ix(z)`
- `Iy(z)`
- `Jt(z)`

These are used to generate:

- `histwin_tower_ElastoDyn_Tower.dat`
- `histwin_tower_BModes_tower.bmt`

### 4.2 Produced from BModes

BModes provides the mode shapes used to fit:

- `TwFAM1Sh(2..6)`
- `TwFAM2Sh(2..6)`
- `TwSSM1Sh(2..6)`
- `TwSSM2Sh(2..6)`

### 4.3 Not produced by CSF

These remain the user's responsibility:

- RNA mass and inertias,
- RNA center-of-mass offsets,
- non-tower machine data in `ElastoDyn.dat`,
- any real physical machine data outside the tower model.

The scripts include placeholder values only to let the pipeline run.

---

## 5. Choose one workflow

There are only **two** workflows.

### Workflow A — fully automatic

Use this if BModes is available locally or through `BMODES_EXE`.

This path is:

1. run `run_csf_to_elastodyn.sh`
2. generate `Main.fst`, `ElastoDyn.dat`, `ElastoDyn_Blade.dat`
3. run `openfast Main.fst`

### Workflow B — manual BModes step

Use this if BModes exists but you want to launch it yourself.

This path is:

1. run `run_csf_to_elastodyn.sh`
2. run BModes manually
3. rerun `csf_to_elastodyn.py` with `--bmodes-out`
4. generate `Main.fst`, `ElastoDyn.dat`, `ElastoDyn_Blade.dat`
5. run `openfast Main.fst`

**Do not mix the two workflows halfway through unless you intentionally switch to Workflow B.**

---

## 6. Workflow A — fully automatic

### Step A1 — make the launcher executable

```bash
chmod +x run_csf_to_elastodyn.sh
```

### Step A2 — ensure BModes is discoverable

Either:

- keep BModes at `./BModes/build/bmodes/bmodes`

or:

```bash
export BMODES_EXE=/absolute/path/to/bmodes
```

### Step A3 — run the main launcher

```bash
./run_csf_to_elastodyn.sh histwin_tower.yaml
```

If BModes is found, this single command does all of the following:

1. samples the CSF tower,
2. writes `histwin_tower_ElastoDyn_Tower.dat`,
3. writes `histwin_tower_BModes_tower.bmt`,
4. writes `histwin_tower_BModes_tower.bmi`,
5. runs BModes,
6. reads `histwin_tower_BModes_tower.out`,
7. injects the fitted mode-shape coefficients into `histwin_tower_ElastoDyn_Tower.dat`.

Expected result:

- `histwin_tower_ElastoDyn_Tower.dat`
- `histwin_tower_BModes_tower.bmt`
- `histwin_tower_BModes_tower.bmi`
- `histwin_tower_BModes_tower.out`

### Step A4 — generate the OpenFAST structural-only case

```bash
python generate_openfast_case_templates.py \
  histwin_tower_ElastoDyn_Tower.dat \
  --yaml histwin_tower.yaml
```

Expected result:

- `Main.fst`
- `ElastoDyn.dat`
- `ElastoDyn_Blade.dat`

### Step A5 — run OpenFAST

```bash
openfast Main.fst
```

Expected result:

- `OpenFAST terminated normally.`

---

## 7. Workflow B — manual BModes step

Use this when you do **not** want the launcher to run BModes automatically.

### Step B1 — run the launcher

```bash
chmod +x run_csf_to_elastodyn.sh
./run_csf_to_elastodyn.sh histwin_tower.yaml
```

If BModes is not found, the launcher stops after generating:

- `histwin_tower_ElastoDyn_Tower.dat`
- `histwin_tower_BModes_tower.bmt`
- `histwin_tower_BModes_tower.bmi`

### Step B2 — run BModes yourself

```bash
./BModes/build/bmodes/bmodes histwin_tower_BModes_tower.bmi
```

Expected result:

- `histwin_tower_BModes_tower.out`

### Step B3 — inject BModes mode shapes into the ElastoDyn tower file

Recommended command:

```bash
python csf_to_elastodyn.py histwin_tower.yaml \
  --E 210e9 \
  --G 80.8e9 \
  --rho 8500 \
  --n 11 \
  --damp 1.0 \
  --mass-tip 350000 \
  --ixx-tip 2607890 \
  --iyy-tip 43784227 \
  --izz-tip 2607890 \
  --cm-loc -1.9 \
  --cm-axial 1.75 \
  --bmodes-out histwin_tower_BModes_tower.out
```

This regenerates the tower files and rewrites `histwin_tower_ElastoDyn_Tower.dat` with the fitted BModes coefficients already injected.

### Step B4 — generate the OpenFAST structural-only case

```bash
python generate_openfast_case_templates.py \
  histwin_tower_ElastoDyn_Tower.dat \
  --yaml histwin_tower.yaml
```

### Step B5 — run OpenFAST

```bash
openfast Main.fst
```

Expected result:

- `OpenFAST terminated normally.`

---

## 8. Optional standalone coefficient update

This is **not** part of the main workflows.
It is only an auxiliary tool when you already have:

- `histwin_tower_BModes_tower.out`
- `histwin_tower_ElastoDyn_Tower.dat`

and you want to update only the mode-shape coefficients.

```bash
python bmodes_out_to_elastodyn.py \
  histwin_tower_BModes_tower.out \
  histwin_tower_ElastoDyn_Tower.dat
```

Manual mode selection example:

```bash
python bmodes_out_to_elastodyn.py \
  histwin_tower_BModes_tower.out \
  histwin_tower_ElastoDyn_Tower.dat \
  --fa1 1 --ss1 2 --fa2 3 --ss2 5
```

Use this only if the automatic mode identification is not what you want.

---

## 9. What to customize

## 9.1 In `run_csf_to_elastodyn.sh`

Main tower/material settings:

```bash
E=210e9
G=80.8e9
RHO=8500
N=11
DAMP=1.0
```

Meaning:

- `E`: Young's modulus
- `G`: shear modulus
- `RHO`: density
- `N`: number of sampled stations along tower height
- `DAMP`: ElastoDyn tower damping ratio

RNA test values used to generate `.bmi`:

```bash
MASS_TIP="350000"
IXX_TIP="2607890"
IYY_TIP="43784227"
IZZ_TIP="2607890"
CM_LOC="-1.9"
CM_AXIAL="1.75"
```

These values are not produced by CSF.
Replace them with real machine data for physical runs.

## 9.2 In `csf_to_elastodyn.py`

Command-line controls:

- `--E`
- `--G`
- `--rho`
- `--n`
- `--damp`
- `--mass-tip`
- `--ixx-tip`
- `--iyy-tip`
- `--izz-tip`
- `--cm-loc`
- `--cm-axial`
- `--bmodes-exe`
- `--bmodes-out`
- `--ss-mode-ids`
- `--fa-mode-ids`

Use `--ss-mode-ids` and `--fa-mode-ids` only if automatic BModes mode selection must be overridden.

## 9.3 In `generate_openfast_case_templates.py`

This script creates a **test structural case**.

It infers only:

- `TowerHt` from `histwin_tower.yaml`
- `TwrFile` from the provided ElastoDyn tower file name

Everything else in the generated `ElastoDyn.dat` is still non-CSF machine data.

If you want a physically meaningful turbine model, replace the placeholder values in:

- `ElastoDyn.dat`
- optionally `ElastoDyn_Blade.dat`

## 9.4 In `histwin_tower.yaml`

This file controls the actual tower model.

Typical user changes here affect:

- tower geometry,
- tower thickness / section evolution,
- number and shape of polygons,
- any CSF weight-law definitions already embedded in the model.

The pipeline assumes that this YAML is already a valid CSF model.

---

## 10. Recommended usage summary

If you have BModes available locally, use **Workflow A**.

If you want explicit control over the BModes run, use **Workflow B**.

Most users should follow this exact sequence:

### Preferred sequence

```bash
chmod +x run_csf_to_elastodyn.sh
./run_csf_to_elastodyn.sh histwin_tower.yaml
python generate_openfast_case_templates.py histwin_tower_ElastoDyn_Tower.dat --yaml histwin_tower.yaml
openfast Main.fst
```

This is the shortest end-to-end path.

---

## 11. Final note

This pipeline is now meant to run **without manual file edits**.

However, two categories of data remain outside CSF by design:

- RNA data for BModes `.bmi`
- non-tower machine data for the OpenFAST / ElastoDyn structural case

Those values remain the user's responsibility.
