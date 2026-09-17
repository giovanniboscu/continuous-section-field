# Carrera & Giunta Tables 9–10 - Reproducibility

This directory contains the files required to reproduce the CSF-CUF numerical validation against the prismatic I-shaped beam results reported by Carrera and Giunta (2010), Tables 9 and 10.

The validation covers:

* Table 9 - bending;
* Table 10 - torsion;
* increasing CUF transverse expansion orders;
* comparison with the published Carrera–Giunta CUF results;
* comparison with the corresponding FEM3D reference values.

The complete description of the formulation, numerical model and validation results is available in:

`docs/model/csf_cuf_numerical_validation_carrera_giunta.md`

## Input structure

The validation is organized in three independent levels:

```text
CSF model YAML
      |
      v
problem YAML
      |
      v
CUF case YAML
      |
      v
csf-cuf
      |
      v
Carrera post-processing
```

Their responsibilities are:

| Input        | Responsibility                                     |
| ------------ | -------------------------------------------------- |
| model YAML   | CSF geometry and material definition               |
| problem YAML | physical loading and boundary-condition definition |
| case YAML    | CUF basis, order and numerical settings            |

The physical model and benchmark definition remain unchanged when the CUF expansion order is varied.

## Installation

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Then enter this directory:

```bash
cd cuf/refined_beam_theories_tables_9_10
```

## Run a single case

Any available validation case can be executed directly with:

```bash
csf-cuf path/to/case.yaml
```

The solver reads the selected case YAML and the referenced problem and CSF model definitions.

After the solution, the Carrera post-processing adapter reconstructs the benchmark quantities and writes the normalized displacement results.

## Reproduce Tables 9 and 10

The complete available validation series up to a selected CUF order can be executed with:

```bash
python3 run_tables_9_10.py 21
```

Here `21` is the maximum requested CUF order.

The script independently discovers the available Table 9 and Table 10 cases and executes every case whose order is less than or equal to the requested maximum.

The generated combined report is:

```text
carrera_giunta_tables_9_10.txt
```

This file collects the CSF-CUF results by CUF order for direct comparison with the published Carrera–Giunta values.

## Reproducibility principle

The validation does not require rebuilding the physical model for each CUF order.

Only the numerical approximation selected by the case YAML changes:

```yaml
cuf:
  basis: scaled_maclaurin
  order: N
```

The same CSF geometry, material definition, loading and boundary conditions are therefore evaluated through progressively refined CUF transverse approximations.

For the complete benchmark definition, numerical results and discussion, see:

`docs/model/csf_cuf_numerical_validation_carrera_giunta.md`

## Reference

E. Carrera and G. Giunta,
“Refined Beam Theories Based on a Unified Formulation”,
*International Journal of Applied Mechanics*, 2(1), 117–143, 2010.
DOI: 10.1142/S1758825110000500
