# CSF-CUF Tutorial Reproducibility (Non-Prismatic T-Section)

Synthetic, command-by-command guide to reproduce from scratch the tutorial:
`cuf/tutorials/variable_material_t_section/csf-cuf_template.md`
from the `giovanniboscu/continuous-section-field` repository.

Tested on Ubuntu 24, Python 3.12, clean environment.

---

## 1. System prerequisites

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

---

## 2. Clone the repository

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

---

## 3. Virtual environment and package installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
```

The build installs `csfpy` in editable mode and registers the entry points:
`csf-actions`, `csf-cuf`, `csf-sp`, `sp-csf`.

Verify installation:

```bash
pip show csfpy
csf-actions --help
csf-cuf --help
```

Set once for the whole shell session (avoids a graphical `matplotlib`
window from blocking execution on headless machines; skip if you have a
display):

```bash
export MPLBACKEND=Agg
```

> From here on, the virtual environment stays active in this shell
> (`source venv/bin/activate` was run above), so all commands below use the
> plain executable names (`csf-actions`, `csf-cuf`, `python3`), no path
> prefix needed.

---

## 4. Step 1 - Inspect the physical CSF model

```bash
cd cuf/tutorials/variable_material_t_section/t_section/models
csf-actions t_noprismatic_csf.yaml action.yaml
```

> `MPLBACKEND=Agg` (exported once above) prevents `matplotlib` from trying
> to open a graphical window (`plt.show()`) and blocking execution. On a
> desktop with a graphical display it is not needed.

Expected output (excerpt): `A, Ix, Iy, Ip` report at `z=0` and `z=1000`,
`volume` report with `weight` 71700→71700 (flange) and 71700→57360 (web).

---

## 5. Steps 2-4 - Run the CUF cases

Move to the tutorial folder (one level above `models/`):

```bash
cd ../
```

### Bending half-wave case

```bash
csf-cuf cases/bending_halfwave_legendre_N08.yaml
```

Expected output: log with effective quadratures (section=9, longitudinal=16),
`M=45`, `DOFs=945`, `K` 945×945, `A` 181×945 rank 181/181,
KKT 1126×1126, equilibration `rcond` 8.03e-19 → 5.24e-09,
file written to `output/bending_halfwave_legendre_N08/response.txt`.

### Torsion half-wave case

```bash
csf-cuf cases/torsion_halfwave_legendre_N25.yaml
```

Expected output: same `K`/`A` structure (same model/CUF basis),
`solver.equilibration.iterations=5` (explicitly set in the YAML),
file written to `output/torsion_halfwave_legendre_N25/response.txt`.

---

## 6. Step 5 - Inspect the generated results

```bash
cat output/bending_halfwave_legendre_N08/response.txt
cat output/torsion_halfwave_legendre_N25/response.txt
```

Columns: `x/L, x[mm], y[mm], z[mm], point, ux[mm], uy[mm], uz[mm]`.

---

## 7. Step 6 -Verify against the FEM3D (OpenSees) reference

> Requires significantly more RAM than the previous steps: the 3D mesh has
> **61,509 nodes / 54,000 `stdBrick` elements**. In low-RAM environments the
> process may be terminated with `Killed` (OOM). This is a hardware
> requirement, not a flaw in the tutorial.
>
> **This step can be skipped.** The FEM3D reference results are already
> included in the repository (`fem3d/output/*/`), pre-computed. Regenerating
> them is only needed to verify the OpenSees solve itself; the CUF vs FEM3D
> comparison in the next section can be run directly against the files
> already shipped in the repo.

```bash
cd fem3d
python3 fem/run_bending_halfwave.py
python3 fem/run_torsion_halfwave.py
```

Generates:

```
output/bending_halfwave_model2/{fem3d_native_displacements.csv,station_extrema.csv,summary.txt,station_points.csv}
output/torsion_halfwave_model2/{...}
```



### Graphical comparison CUF vs FEM3D

```bash
python3 plot_halfwave_outputs.py
```

Generates the plots in `plots_halfwave/{bending,torsion}_halfwave_legendre_N08/`.

---

## Command summary (none excluded, in order)

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git

git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
pip show csfpy
csf-actions --help
csf-cuf --help

export MPLBACKEND=Agg

cd cuf/tutorials/variable_material_t_section/t_section/models
csf-actions t_noprismatic_csf.yaml action.yaml

cd ..
csf-actions models/t_noprismatic_csf.yaml models/action.yaml
csf-cuf cases/bending_halfwave_legendre_N08.yaml
csf-cuf cases/torsion_halfwave_legendre_N25.yaml

cat output/bending_halfwave_legendre_N08/response.txt
cat output/torsion_halfwave_legendre_N25/response.txt

cd fem3d
python3 fem/run_bending_halfwave.py
python3 fem/run_torsion_halfwave.py
python3 plot_halfwave_outputs.py
```

