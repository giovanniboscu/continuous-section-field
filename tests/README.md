# Running the csfpy Verification Tests

## Prerequisites

```bash
pip install -e ".[sp]"
pip install pytest
```

## repo layout

```
continuous-section-field/
├── docs/
│   └── verification/
│       ├── csf_sp_cell_verification.py
│       ├── csf_sp_complex_integration_verification.py
│       └── csf_sp_wall_complex_verification.py
├── tests/
│   └── test_verification.py   
└── src/csf/
```

## Running

```bash
# from the repo root
pytest test_verification.py -v
```

Expected terminal output:

```
tests/test_verification.py::test_cell_verification                PASSED
tests/test_verification.py::test_complex_integration_verification PASSED
tests/test_verification.py::test_wall_complex_verification        PASSED

3 passed in ~22s
```

To also see the numeric tables printed in real time:

```bash
pytest test_verification.py -v -s
```

## What gets produced

Three Markdown reports are written (or overwritten) in `docs/verification/`:

| Report file | What it covers |
|-------------|---------------|
| `csf_sp_cell_verification_report.md` | `@cell` section: geometry + torsion (Bredt vs FEM) |
| `csf_sp_complex_integration_report.md` | Composite multi-polygon section: geometry only |
| `csf_sp_wall_complex_verification_report.md` | Complex `@wall` section: geometry + torsion |

## What to look at in the reports

### Geometric properties (A, Cx, Cy, Ix, Iy, Ixy, Ip, I1, I2, rx, ry)

Deltas should be at machine precision (relative error ~1e-15).
Both paths — CSF and sectionproperties — operate on the same vertices,
so the agreement is expected to be essentially exact.

### Torsion (J_sv_cell or J_sv_wall vs sectionproperties e.j)

A relative delta of 2–3% is **normal and expected**: CSF uses an
analytical Bredt-type formula, while sectionproperties solves the
torsion problem numerically via FEM. The tolerances declared at the
top of each script (`TORSION_REL_TOL`) reflect this known difference.

### Global summary

Each report ends with a summary block - the key line is:

```
Overall status: PASS
```

If any row exceeds its tolerance the status reads `FAIL` and a
"Failed rows" table lists exactly which property and station failed.
