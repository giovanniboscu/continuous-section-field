
# CSF-CUF validation against Carrera and Giunta (2010)


## What the validation demonstrates

The current validation chain covers:

- prismatic I-shaped bending;
- prismatic I-shaped torsion;
- high-order Maclaurin transverse expansions;
- the generic weak-form longitudinal finite-element runtime;
- prismatic CSF geometry;
- comparison with published CUF results and with a three-dimensional FEM baseline.


The key architectural result is that the CUF core remains independent of the particular cross-section. The section and material state are supplied by CSF, the transverse approximation is supplied by the basis plugin, and the physical loading/constraints are supplied by the problem adapter.

# CSF-CUF validation against Carrera & Giunta (2010)

Prismatic I-shaped beam, `l/a = 10`.

Each displacement quantity is reported twice:

- **CSF-CUF**: value calculated by the current CSF-CUF validation.
- **Carrera & Giunta**: value published in the 2010 paper.
- `-`: the corresponding order is not reported in the paper.

## Table 9 - Bending

| N | $10\,u_{x,\max}^*$ CSF-CUF | $10\,u_{x,\max}^*$ Carrera & Giunta | $10^3\,\lvert u_{y,\max}^*\rvert$ CSF-CUF | $10^3\,\lvert u_{y,\max}^*\rvert$ Carrera & Giunta | $10^2\,u_{z,\max}^*$ CSF-CUF | $10^2\,u_{z,\max}^*$ Carrera & Giunta |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.950783 | 3.886 | 0.068839 | 0.058 | 6.430589 | 8.669 |
| 2 | 3.877652 | 3.878 | 2.803833 | 2.805 | 8.593199 | 8.593 |
| 3 | 4.014018 | 4.014 | 2.812663 | 2.814 | 8.742560 | 8.743 |
| 4 | 4.014016 | 4.014 | 2.865736 | 2.867 | 8.743154 | 8.743 |
| 5 | 4.025188 | 4.025 | 2.928505 | 2.929 | 8.738059 | 8.738 |
| 6 | 4.025434 | 4.026 | 2.939636 | 2.941 | 8.738133 | 8.738 |
| 7 | 4.034236 | 4.034 | 2.945481 | 2.946 | 8.739883 | 8.740 |
| 8 | 4.034802 | 4.035 | 2.957545 | 2.958 | 8.739931 | 8.740 |
| 9 | 4.037656 | 4.038 | 2.965672 | 2.967 | 8.741586 | 8.742 |
| 10 | 4.037848 | 4.038 | 2.972402 | 2.973 | 8.741618 | 8.742 |
| 11 | 4.044458 | - | 2.996301 | - | 8.743569 | - |
| 12 | 4.044576 | - | 3.003615 | - | 8.743574 | - |
| 13 | 4.046164 | - | 3.006344 | - | 8.743958 | - |
| 14 | 4.046499 | - | 3.012436 | - | 8.743986 | - |
| 15 | 4.047933 | - | 3.013935 | - | 8.744500 | - |
| 16 | 4.048004 | - | 3.015193 | - | 8.744506 | - |
| 17 | 4.050652 | - | 3.028798 | - | 8.745061 | - |
| 18 | 4.050773 | 4.051 | 3.038514 | 3.040 | 8.745067 | 8.745 |


**Carrera & Giunta FEM 3D reference:**  
`10 u_x,max* = 4.059`, `10^3 |u_y,max*| = 3.102`, `10^2 u_z,max* = 8.748`.


## Table 10 - Torsion

| N | $10\,\lvert u_{x,\max}^*\rvert$ CSF-CUF | $10\,\lvert u_{x,\max}^*\rvert$ Carrera & Giunta | $10\,\lvert u_{y,\max}^*\rvert$ CSF-CUF | $10\,\lvert u_{y,\max}^*\rvert$ Carrera & Giunta | $10^2\,u_{z,\max}^*$ CSF-CUF | $10^2\,u_{z,\max}^*$ Carrera & Giunta |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.205195 | 0.209 | 0.428769 | 0.429 | 0.131609 | 0.201 |
| 2 | 0.629295 | 0.629 | 1.387627 | 1.388 | 1.327604 | 1.328 |
| 3 | 0.656386 | 0.656 | 1.400667 | 1.401 | 1.331575 | 1.332 |
| 4 | 1.597707 | 1.598 | 3.509496 | 3.510 | 3.011552 | 3.011 |
| 5 | 1.609354 | 1.609 | 3.520215 | 3.520 | 3.013124 | 3.013 |
| 6 | 1.643686 | 1.644 | 3.597547 | 3.598 | 3.127766 | 3.128 |
| 7 | 1.655253 | 1.655 | 3.593291 | 3.593 | 3.117757 | 3.118 |
| 8 | 1.891361 | 1.891 | 4.117893 | 4.118 | 3.779054 | 3.779 |
| 9 | 1.899037 | 1.899 | 4.118076 | 4.118 | 3.776509 | 3.777 |
| 10 | 2.031073 | 2.031 | 4.411842 | 4.412 | 4.112417 | 4.112 |
| 11 | 2.036438 | - | 4.414613 | - | 4.110712 | - |
| 12 | 2.094094 | - | 4.541868 | - | 4.285678 | - |
| 13 | 2.099999 | - | 4.541460 | - | 4.282903 | - |
| 14 | 2.206758 | - | 4.778237 | - | 4.522213 | - |
| 15 | 2.211105 | - | 4.778676 | - | 4.521205 | - |
| 16 | 2.217526 | - | 4.792986 | - | 4.529380 | - |
| 17 | 2.220863 | - | 4.794516 | - | 4.528254 | - |
| 18 | 2.255825 | - | 4.871806 | - | 4.613628 | - |
| 19 | 2.259756 | 2.261 | 4.872798 | 4.872 | 4.612711 | 4.612 |
| 20 | 2.288527 | 2.289 | 4.936553 | 4.937 | 4.672726 | 4.673 |
| 21 | 2.291650 | 2.293 | 4.936626 | 4.939 | 4.672109 | 4.675 |


**Carrera & Giunta FEM 3D reference:**  
`10 |u_x,max*| = 2.408`, `10 |u_y,max*| = 5.164`, `10^2 u_z,max* = 4.870`.

---

# Reproducing Tables 9 and 10

##  YAML data structure

The validation input is deliberately split into three levels:

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
csf-cuf solver
      |
      v
Carrera post-processing
```

Each level has one responsibility.

### CSF model YAML: geometry and material

The model file contains the physical cross-section description. A double-T model is built from named polygonal domains such as `top_flange`, `web`, and `bottom_flange`.

A simplified structure is:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        - name: top_flange
          weight: 71700.0
          vertices:
            - [y1, z1]
            - [y2, z2]
            # ...

        - name: web
          weight: 71700.0
          vertices:
            # ...

        - name: bottom_flange
          weight: 71700.0
          vertices:
            # ...

  shear_weight_laws:
    - 'iso(0.3)'
```

For a prismatic beam the section is constant. For a variable beam, additional section states such as `S1` describe the geometry/material at another longitudinal coordinate and CSF supplies the intermediate state continuously.

The model YAML therefore answers the question:

**What physical section and material exist at a given longitudinal position?**

### Problem YAML: physical benchmark

The problem file connects a CSF model to a physical loading definition.

For Table 9 bending:

```yaml
model:
  csf_yaml: ../models/carrera_double_t_prismatic_csf.yaml

problem:
  type: carrera_bending_bottom_surface_halfwave
  amplitude: 1.0
```

For Table 10 torsion:

```yaml
model:
  csf_yaml: ../models/carrera_double_t_prismatic_csf.yaml

problem:
  type: carrera_torsion_halfwave
  amplitude: 1.0
```

The problem adapter interprets the selected problem type and constructs the corresponding loads and constraints.

The problem YAML therefore answers:

**Which physical test is applied to the CSF member?**

### Case YAML: CUF and numerical settings

The case file references the problem and selects the numerical approximation. A current Maclaurin Table 9 case has the following structure:

```yaml
case:
  name: cuf_scaled_maclaurin_taper00_table9_N01

problem:
  yaml: ../../problem/taper00_table9.yaml
  adapter: ../../validation/carrera_problem.py

cuf:
  basis: scaled_maclaurin
  order: 1

longitudinal:
  method: finite_element
  elements: 1
  order: 6

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6

solver:
  equilibration:
    iterations: 4

sampling:
  stations:
    - 0.00
    - 0.25
    - 0.50
    - 0.75
    - 1.00
  displacement_samples: 201
  stress_grid: 31

output:
  adapter: ../../validation/carrera_post.py
  directory: ../../output/taper00_prismatic/table9_N1
```

The main quantity varied in the Carrera series is

```yaml
cuf:
  order: N
```

The case YAML therefore answers:

**How is this physical problem approximated and solved?**

### Separation of responsibilities

The three YAML levels should not be merged conceptually:

| File | Responsibility |
|---|---|
| model YAML | CSF geometry and material |
| problem YAML | physical load and boundary-condition family |
| case YAML | CUF basis/order, numerical integration, solver, sampling and output |

Changing the CUF order does not require changing the model or the physical problem.

---

## Reproducibility

The validation can be reproduced directly from the source repository.

### Prerequisites

The following tools are required:

- Git;
- Python 3.8 or newer;
- `pip`.

A Python virtual environment is recommended so that the validation runs with an isolated set of dependencies.

### Clone the repository

Clone the repository and enter its root directory:

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

### Create a Python virtual environment

On Linux or macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```powershell
py -m venv venv
.\venv\Scripts\activate
```

### Install CSF-CUF from the repository

Install the repository in editable mode:

```bash
pip install -e .
```

This installs the Python dependencies together with the command-line tools provided by the repository.

### Move to the validation directory

From the repository root, enter the Carrera-Giunta Tables 9-10 validation directory:

```bash
cd cuf/refined_beam_theories_tables_9_10
```

The working directory is now:

```text
continuous-section-field/
└── cuf/
    └── refined_beam_theories_tables_9_10/
```

All commands in the following sections are intended to be executed from this directory.

### Validation data organization

The validation input is separated into three levels:

```text
model YAML
    |
    v
problem YAML
    |
    v
case YAML
    |
    v
csf-cuf
    |
    v
post-processing
```

The three files have different responsibilities:

| Input | Purpose |
|---|---|
| model YAML | CSF geometry and material definition |
| problem YAML | physical loading and boundary-condition definition |
| case YAML | CUF basis, order, longitudinal discretization, solver settings, sampling and output |

The model describes the physical member.

The problem selects the Carrera-Giunta bending or torsion benchmark to be applied to that member.

The case selects how that physical problem is approximated and solved numerically.

Changing the CUF order therefore requires changing only the case YAML; the physical model and problem definition remain unchanged.

### Run a single case

A single validation case can be launched with:

```bash
csf-cuf path/to/case.yaml
```

For example, a Table 9 or Table 10 case is selected directly by its case YAML.

The solver reads:

1. the case YAML;
2. the referenced problem YAML;
3. the referenced CSF model YAML.

After the solution is obtained, the Carrera post-processing adapter generates the normalized displacement report for the corresponding reference table.

### Run the Table 9 and Table 10 batch

The complete validation series can be launched with:

```bash
python3 run_tables_9_10.py 21
```

The argument `21` is the maximum CUF order requested.

It acts as a ceiling: the script runs all available Table 9 and Table 10 case files whose order is less than or equal to the requested value.

The two tables are discovered independently. For example, if Table 9 cases are available only up to `N18` and Table 10 cases are available up to `N21`, the same command runs:

```text
Table 9  -> available cases up to N18
Table 10 -> available cases up to N21
```

The batch searches the validation case directory for files following the naming convention:

```text
maclaurin_table9_Nxx.yaml
maclaurin_table10_Nxx.yaml
```

For every available case, the script launches `csf-cuf`, reads the generated normalized displacement report, and collects the results by CUF order.

At the end of the run, the combined validation report is written to:

```text
carrera_giunta_tables_9_10.txt
```

This file contains the CSF-CUF results for Tables 9 and 10 up to the requested maximum order.

---


## References

E. Carrera, G. Giunta, **“Refined Beam Theories Based on a Unified Formulation”**, *International Journal of Applied Mechanics*, 2(1) (2010), 117–143. DOI: 10.1142/S1758825110000500.
