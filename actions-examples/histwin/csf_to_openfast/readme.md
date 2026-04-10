# CSF -> OpenFAST Minimal Pipeline Guide

## What this process does

This process converts a **CSF geometry YAML** into a minimal set of **OpenFAST** input files:

- `*_Main.fst`
- `*_ElastoDyn.dat`
- `*_ElastoDyn_Tower.dat`
- `*_ElastoDyn_Blade.dat`

The current architecture is intentionally minimal:

- `CompElast = 1`
- `CompSub = 0`
- `CompAero = 0`
- `CompInflow = 0`

So this is not a full aeroelastic wind turbine workflow.  
It is a **minimal structural OpenFAST case** in which the tower properties come from **CSF**.

---

## Why this process is useful

The main point of the process is not OpenFAST alone.

The useful part is that the tower is **not defined manually station by station**.

Instead:

1. the tower geometry is defined once in **CSF**,
2. the Python script samples the geometry along `z`,
3. the OpenFAST tower input is generated automatically.

Without this process, changing the tower usually means:

- redefining stations manually,
- recalculating structural properties manually,
- rewriting the OpenFAST tower file every time.

With this workflow, if the geometry changes, you regenerate the OpenFAST files from the CSF model.

---

## Installation

Install the CSF Python package with:

```bash
pip install csfpy
```

Note: the pip package is named `csfpy` but the importable module is `csf`.  
The script uses `from csf import ...` — this is correct and expected.

Other dependencies (`numpy`, `PyYAML`, `matplotlib`, `openseespy`) are installed automatically.

---

## continuous-function API of CSF

The script evaluates:

- `A(z)`
- `Ix(z)`
- `Iy(z)`

at multiple stations.

These values are then converted into the distributed quantities written to `ElastoDyn_Tower.dat`:

- `TMassDen(z) = rho * A(z)`
- `TwFAStif(z) = E * Ix(z)`
- `TwSSStif(z) = E * Iy(z)`

That is the advantage of using CSF in this workflow.

It means that:

- taper changes,
- geometry changes,
- continuous tower variations along `z`

can be propagated automatically into the OpenFAST tower model.

So the value of CSF here is:

- continuous geometry input,
- automatic structural-property evaluation,
- automatic regeneration of the OpenFAST tower file.

---

## What CSF is doing in this workflow

In this pipeline, CSF is used as a **tower-property generator**.

More precisely:

- **CSF** provides the distributed tower properties
- **OpenFAST** performs the simulation

So the workflow is a bridge from:

**continuous tower geometry -> distributed tower properties -> OpenFAST input files**

---

## Files produced

Given an output stem `<stem>`, the script writes:

- `<stem>_ElastoDyn_Tower.dat`
- `<stem>_ElastoDyn.dat`
- `<stem>_ElastoDyn_Blade.dat`
- `<stem>_Main.fst`

---

## Main files in the workflow

### 1. CSF geometry YAML
This is the geometric input.

It defines the tower in CSF.

### 2. `csf_to_openfast.py`
This is the generator.

It:
- loads the CSF model,
- samples the tower,
- writes the OpenFAST files.

### 3. Launcher script
This is the platform-specific launcher.

It passes the chosen parameters directly to the Python script.

| Platform | File | Shell |
|----------|------|-------|
| Linux / macOS | `wind11.sh` | bash |
| Windows | `wind11.ps1` | PowerShell |

Both launchers do the same thing: pass the CSF YAML and all case parameters to `csf_to_openfast.py` as direct command-line arguments. They do **not** use extra YAML config files.

---

## How to run on Linux / macOS

### Launcher: `wind11.sh`

Make the script executable once:

```bash
chmod +x wind11.sh
```

Then run:

```bash
./wind11.sh ../histwin_tower.yaml
```

Or without the executable bit:

```bash
bash wind11.sh ../histwin_tower.yaml
```

The CSF YAML is passed from the command line. All other parameters are set inside the script.

### Structure of `wind11.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

YAML="$1"
SCRIPT="./csf_to_openfast.py"
OUT="histwin_tower"

# Geometry / section
E=210e9
RHO=7850
N_STATIONS=11

# Machine / simulation
RNA_MASS=350000
RNA_IXX=4.0e7
RNA_IYY=2.1e7
RNA_IZZ=2.4e7
RNA_CM_X=5.0
RNA_CM_Z=2.0
HUB_RAD=3.0
OVERHANG=5.0
TMAX=10.0
DT=0.01

python "$SCRIPT" "$YAML" \
  --E "$E" \
  --rho "$RHO" \
  --n-stations "$N_STATIONS" \
  --rna-mass "$RNA_MASS" \
  --rna-ixx "$RNA_IXX" \
  --rna-iyy "$RNA_IYY" \
  --rna-izz "$RNA_IZZ" \
  --rna-cm-x "$RNA_CM_X" \
  --rna-cm-z "$RNA_CM_Z" \
  --hub-rad "$HUB_RAD" \
  --overhang "$OVERHANG" \
  --tmax "$TMAX" \
  --dt "$DT" \
  --out "$OUT"
```

---

## How to run on Windows

### Launcher: `wind11.ps1`

Run from PowerShell:

```powershell
.\wind11.ps1 ..\histwin_tower.yaml
```

If script execution is blocked by policy, enable it for the current session first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\wind11.ps1 ..\histwin_tower.yaml
```

The CSF YAML is passed from the command line. All other parameters are set inside the script.

### Structure of `wind11.ps1`

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$YAML
)

$SCRIPT = ".\csf_to_openfast.py"
$OUT    = "histwin_tower"

# Geometry / section
$E          = 210e9
$RHO        = 7850
$N_STATIONS = 11

# Machine / simulation
$RNA_MASS  = 350000
$RNA_IXX   = 4.0e7
$RNA_IYY   = 2.1e7
$RNA_IZZ   = 2.4e7
$RNA_CM_X  = 5.0
$RNA_CM_Z  = 2.0
$HUB_RAD   = 3.0
$OVERHANG  = 5.0
$TMAX      = 10.0
$DT        = 0.01

python $SCRIPT $YAML `
  --E $E `
  --rho $RHO `
  --n-stations $N_STATIONS `
  --rna-mass $RNA_MASS `
  --rna-ixx $RNA_IXX `
  --rna-iyy $RNA_IYY `
  --rna-izz $RNA_IZZ `
  --rna-cm-x $RNA_CM_X `
  --rna-cm-z $RNA_CM_Z `
  --hub-rad $HUB_RAD `
  --overhang $OVERHANG `
  --tmax $TMAX `
  --dt $DT `
  --out $OUT
```

---

## What to change in the launcher

The launcher script (`.sh` on Linux, `.ps1` on Windows) is the correct place to change **input values** without modifying the Python logic.

Modify it when you want to change:

- the CSF YAML path,
- material stiffness (`E`),
- density (`RHO`),
- number of tower stations,
- RNA values,
- simulation time or time step,
- output stem.

This is the preferred place for **case-level customization**.

The logic stays in `csf_to_openfast.py`. The case parameters stay in the launcher.

---

## All modifiable parameters in `csf_to_openfast.py`

The real input parameters accepted by the Python script are the command-line arguments defined in `parse_args()`.

---

## Required positional argument

### `yaml`
CSF geometry YAML file.

This is the geometric source model used by the script.

Example:

```bash
python csf_to_openfast.py tower.yaml ...
```

---

## Material parameters

### `--E`
Young's modulus `[Pa]`

Used to compute:

- `TwFAStif = E * Ix`
- `TwSSStif = E * Iy`

### `--rho`
Density `[kg/m3]`

Used to compute:

- `TMassDen = rho * A`

---

## Tower discretization parameter

### `--n-stations`
Number of sampling stations used to evaluate the tower along `z`.

This directly controls:

- how many stations are written to `ElastoDyn_Tower.dat`
- how fine the tower property distribution is

A larger value gives a denser distributed representation.

---

## RNA parameters

### `--rna-mass`
Total RNA mass `[kg]`

Written into:

- `NacMass`

### `--rna-ixx`
Side-to-side inertia `[kg m^2]`

Accepted by the script and stored in the RNA dictionary.

### `--rna-iyy`
Fore-aft inertia `[kg m^2]`

Accepted by the script and stored in the RNA dictionary.

### `--rna-izz`
Yaw inertia `[kg m^2]`

Written into:

- `NacYIner`

### `--rna-cm-x`
RNA center-of-mass downstream offset from tower-top `[m]`

Written into:

- `NacCMxn`

### `--rna-cm-z`
RNA center-of-mass vertical offset from tower-top `[m]`

Written into:

- `NacCMzn`

### `--hub-rad`
Hub radius `[m]`

Written into:

- `HubRad`

Also used to define:

- `TipRad = hub_rad + 1.0`

### `--overhang`
Rotor apex offset from yaw axis `[m]`

Written into:

- `OverHang`

---

## Simulation parameters

### `--tmax`
Simulation duration `[s]`

Written into:

- `TMax`

### `--dt`
Time step `[s]`

Written into:

- `DT`
- `DT_Out`

---

## Optional parameters

### `--out`
Output filename stem.

If omitted, the script uses the YAML stem.

Example:

```bash
--out histwin_tower
```

Outputs become:

- `histwin_tower_Main.fst`
- `histwin_tower_ElastoDyn.dat`
- `histwin_tower_ElastoDyn_Tower.dat`
- `histwin_tower_ElastoDyn_Blade.dat`

### `--openfast-exe`
Optional path to OpenFAST executable.

If provided, the script will launch OpenFAST automatically after generating the files.  
If omitted, only the input files are generated.

---

## What each main function does

### `load_csf(yaml_path)`
Loads the CSF model and extracts:

- `field`
- `z0`
- `z1`

### `compute_properties(field, z0, z1, n)`
Samples the tower at `n` stations and evaluates:

- `A`
- `Ix`
- `Iy`

This is the place to modify if you want to change:
- sampling density,
- sampling law,
- extracted section properties.

### `write_elastodyn_tower(...)`
Writes `ElastoDyn_Tower.dat`.

This is the most important export function for the CSF-to-OpenFAST bridge.

Modify this function if you want to change:
- station formatting,
- distributed tower content,
- formulas used for tower export.

### `write_elastodyn_blade(...)`
Writes a dummy parser-valid blade file.

Modify this only if you want to change the dummy blade definition.

### `write_elastodyn(...)`
Writes `ElastoDyn.dat`.

Modify this if you want to change:
- DOF activation,
- initial conditions,
- nacelle data,
- output channels,
- ElastoDyn options.

### `write_main_fst(...)`
Writes the main OpenFAST file.

Modify this if you want to change:
- module switches,
- output settings,
- simulation layout,
- top-level file references.

---

## Current customized settings inside the real Python file

In the current real file, these lines are already customized:

### Tower DOFs
- `TwFADOF1 = True`
- `TwSSDOF1 = True`

### Initial tower displacement
- `TTDspFA = 0.01`
- `TTDspSS = 0.0`

So the current file already includes a minimal perturbation for tower motion.

---

## Recommended customization strategy

Use this rule:

### Modify the launcher (`wind11.sh` or `wind11.ps1`) when:
you are changing **input values**

Examples:

- new material values,
- new RNA values,
- new simulation time,
- new station count,
- different CSF YAML file.

### Modify `csf_to_openfast.py` when:
you are changing **generation logic**

Examples:

- different sampling strategy,
- different exported structural fields,
- different OpenFAST file structure,
- different DOF activation logic,
- different output channels.

This keeps the workflow clean:

- `.sh` / `.ps1` = case configuration
- `.py` = generation logic

---

## Known warnings

### `CSF_W_POLYGONS_MAP_COERCED`

```
WARNING CSF_W_POLYGONS_MAP_COERCED - Polygons mapping was coerced to a list preserving insertion order.
```

This warning is **non-blocking** and expected when the YAML uses a standard YAML mapping for the polygons block.  
CSF converts it internally to a list while preserving insertion order.  
The pipeline runs correctly and all outputs are valid.

---

## Summary

The point of this process is not simply to create OpenFAST files.

The point is to make OpenFAST consume tower properties coming from a **continuous geometric model**.

That is why CSF is useful here.

Its continuous-function API allows the script to evaluate structural properties along the tower height and automatically regenerate the distributed OpenFAST tower input whenever the geometry changes.
