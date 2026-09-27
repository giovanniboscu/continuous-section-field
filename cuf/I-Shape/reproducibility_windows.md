# I-shaped beam - Reproducibility on Windows

Run the following commands in **Windows PowerShell**, in the order shown. All commands are explicit; no shell scripts are required.

## 1. Prerequisites

Install **Python 3.12 (64-bit)** from [python.org](https://www.python.org/downloads/windows/) with the Python launcher enabled, and [Git for Windows](https://git-scm.com/download/win). Python 3.12 is used for compatibility with OpenSeesPy on Windows, following the repository's [environment instructions](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/reproducibility_environment.md).

Open a new PowerShell window and check both installations:

```powershell
py -3.12 --version
git --version
```

## 2. Download and install

The commands below place the repository in your Windows user folder (`$env:USERPROFILE`).

```powershell
cd "$env:USERPROFILE"

git clone https://github.com/giovanniboscu/continuous-section-field.git
cd "$env:USERPROFILE\continuous-section-field"

py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

python --version
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pypardiso
python -m pip install --no-cache-dir openseespy

python -m pip show csfpy
csf-cuf --help
```

If PowerShell blocks virtual-environment activation, allow it for the current session only, then activate again:

```powershell
cd "$env:USERPROFILE\continuous-section-field"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

Then continue with the installation commands above. Keep the virtual environment active for all remaining steps.

## 3. Run the CSF-CUF cases

Set Matplotlib to save plots without opening graphical windows, then run the prismatic and tapered cases:

```powershell
cd "$env:USERPROFILE\continuous-section-field\cuf\I-Shape"

$env:MPLBACKEND = "Agg"

csf-cuf cases/prism/lagrange_table9_N18_E1.yaml
csf-cuf cases/taper/lagrange_table9_N18_E1.yaml
```

## 4. Optional: regenerate the FEM3D references

The FEM3D reference solutions are already provided. Skip this step to use the existing results. To regenerate them, run these commands from `cuf/I-Shape/fem3d`:

```powershell
cd "$env:USERPROFILE\continuous-section-field\cuf\I-Shape\fem3d"

python run_bending_fem3d_v2.py ../models/carrera_i_shaped_prism.yaml output/fem3d_prism.npz --amplitude -1 --nx 80 --ny-left 3 --ny-web 6 --ny-right 3 --nz-flange 4 --nz-web 20

python run_bending_fem3d_v2.py ../models/carrera_i_shaped_taper80.yaml output/fem3d_taper.npz --amplitude -1 --nx 80 --ny-left 3 --ny-web 6 --ny-right 3 --nz-flange 4 --nz-web 20
```

## 5. Generate the comparison plots

Run the following commands, whether you regenerated the FEM3D references or kept the provided results:

```powershell
cd "$env:USERPROFILE\continuous-section-field\cuf\I-Shape\fem3d"

python compare_prism_taper.py ../output/prism/lagrange/table9_N18_E1/cuf_scaled_lagrange_taper_table9_N18.cuf.npz ../output/taper/lagrange/table9_N18_E1/cuf_scaled_lagrange_taper_table9_N18.cuf.npz --prism-fem3d output/fem3d_prism.npz --taper-fem3d output/fem3d_taper.npz --output-dir prism_vs_taper
```

The plots are saved in `cuf/I-Shape/fem3d/prism_vs_taper`.
