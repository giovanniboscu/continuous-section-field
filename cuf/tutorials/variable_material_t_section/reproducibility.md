# CSF-CUF Tutorial Reproducibility (Non-Prismatic T-Section)

Synthetic, command-by-command guide to reproduce from scratch the tutorial:
`cuf/tutorials/variable_material_t_section/csf-cuf_template.md`
from the `giovanniboscu/continuous-section-field` repository.

Tested on Ubuntu 24, Python 3.12, clean environment.

---

## 0. System prerequisites

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git
```

---

## 1. Clone the repository

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

---

## 2. Virtual environment and package installation

```bash
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -e .
```

The build installs `csfpy` in editable mode and registers the entry points:
`csf-actions`, `csf-cuf`, `csf-sp`, `sp-csf`.

Verify installation:

```bash
venv/bin/pip show csfpy
venv/bin/csf-actions --help
venv/bin/csf-cuf --help
```

Set once for the whole shell session (avoids a graphical `matplotlib`
window from blocking execution on headless machines; skip if you have a
display):

```bash
export MPLBACKEND=Agg
```

---

## 3. Step 1 — Inspect the physical CSF model

```bash
cd cuf/tutorials/variable_material_t_section/t_section/models
../../../../../venv/bin/csf-actions t_noprismatic_csf.yaml action.yaml
```

> `MPLBACKEND=Agg` (exported once above) prevents `matplotlib` from trying
> to open a graphical window (`plt.show()`) and blocking execution. On a
> desktop with a graphical display it is not needed.

Expected output (excerpt): `A, Ix, Iy, Ip` report at `z=0` and `z=1000`,
`volume` report with `weight` 71700→71700 (flange) and 71700→57360 (web).

---

## 4. Steps 2-4 — Run the CUF cases

Move to the tutorial folder (one level above `models/`):

```bash
cd ../
```

(you are now in `.../variable_material_t_section/t_section`)

### Bending half-wave case

```bash
../../../../venv/bin/csf-cuf cases/bending_halfwave_legendre_N08.yaml
```

Expected output: log with effective quadratures (section=9, longitudinal=16),
`M=45`, `DOFs=945`, `K` 945×945, `A` 181×945 rank 181/181,
KKT 1126×1126, equilibration `rcond` 8.03e-19 → 5.24e-09,
file written to `output/bending_halfwave_legendre_N08/response.txt`.

### Torsion half-wave case

```bash
../../../../venv/bin/csf-cuf cases/torsion_halfwave_legendre_N08.yaml
```

Expected output: same `K`/`A` structure (same model/CUF basis),
`solver.equilibration.iterations=5` (explicitly set in the YAML),
file written to `output/torsion_halfwave_legendre_N08/response.txt`.

---

## 5. Step 5 — Inspect the generated results

```bash
cat output/bending_halfwave_legendre_N08/response.txt
cat output/torsion_halfwave_legendre_N08/response.txt
```

Columns: `x/L, x[mm], y[mm], z[mm], point, ux[mm], uy[mm], uz[mm]`.

---

## 6. Step 6 — Verify against the FEM3D (OpenSees) reference

> Requires significantly more RAM than the previous steps: the 3D mesh has
> **61,509 nodes / 54,000 `stdBrick` elements**. In low-RAM environments the
> process may be terminated with `Killed` (OOM). This is a hardware
> requirement, not a flaw in the tutorial.

```bash
cd fem3d
../../../../../venv/bin/python3 fem/run_bending_halfwave.py
../../../../../venv/bin/python3 fem/run_torsion_halfwave.py
```

Generates:

```
output/bending_halfwave_model2/{fem3d_native_displacements.csv,station_extrema.csv,summary.txt,station_points.csv}
output/torsion_halfwave_model2/{...}
```

### Graphical comparison CUF vs FEM3D

```bash
../../../../../venv/bin/python3 plot_halfwave_outputs.py
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
venv/bin/pip install --upgrade pip
venv/bin/pip install -e .
venv/bin/pip show csfpy
venv/bin/csf-actions --help
venv/bin/csf-cuf --help

export MPLBACKEND=Agg

cd cuf/tutorials/variable_material_t_section/t_section/models
../../../../../venv/bin/csf-actions t_noprismatic_csf.yaml action.yaml

cd ..
../../../../venv/bin/csf-cuf cases/bending_halfwave_legendre_N08.yaml
../../../../venv/bin/csf-cuf cases/torsion_halfwave_legendre_N08.yaml

cat output/bending_halfwave_legendre_N08/response.txt
cat output/torsion_halfwave_legendre_N08/response.txt

cd fem3d
../../../../../venv/bin/python3 fem/run_bending_halfwave.py
../../../../../venv/bin/python3 fem/run_torsion_halfwave.py
../../../../../venv/bin/python3 plot_halfwave_outputs.py
```

---

## Known bug note

If you try to **omit** the `section_integration` block from the case file
(as the documentation states is allowed), `csf-cuf` fails with:

```
TypeError: section_integration must be a YAML mapping
```

Cause: `src/csf/cuf/case.py`, line 118, is missing the `{}` default:

```python
# current (bug)
section = _mapping(root.get("section_integration"), "section_integration")

# fix
section = _mapping(root.get("section_integration", {}), "section_integration")
```

With the fix, the default `gauss_order` becomes `cuf_order + 1`, which is
still raised to the CUF-basis minimum requirement when needed — so it is a
correct default, simply not reachable until the `{}` fallback is added.
