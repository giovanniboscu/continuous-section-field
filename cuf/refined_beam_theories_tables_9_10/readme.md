# Carrera & Giunta Tables 9-10 - Reproducibility

This directory contains the files required to reproduce the CSF-CUF numerical validation against the prismatic I-shaped beam results reported by Carrera and Giunta (2010), Tables 9 and 10.

The validation covers:

* **Table 9** - bending;
* **Table 10** - torsion;
* increasing CUF transverse expansion orders;
* comparison with the published Carrera-Giunta CUF results.

The complete description of the benchmark, formulation, numerical model and validation results is provided in:

```text
docs/model/csf_cuf_numerical_validation_carrera_giunta.md
```

This README is intentionally focused on **reproducing the numerical results** from a clean repository checkout.

---

## Validation structure

The validation is organized through separate model, problem and CUF case definitions.

For a Table 9 case, for example:

```text
cases/table9/maclaurin_table9_N01.yaml
        |
        +-- problem YAML
        |      |
        |      v
        |   problem/taper00_table9.yaml
        |      |
        |      v
        |   models/carrera_double_t_prismatic_csf.yaml
        |
        +-- problem adapter
        |      |
        |      v
        |   validation/carrera_problem.py
        |
        +-- post-processing adapter
               |
               v
            validation/carrera_post.py
```

The three levels have different responsibilities:

| Level     | Responsibility                                     |
| --------- | -------------------------------------------------- |
| CSF model | geometry and material definition                   |
| problem   | loading and boundary-condition definition          |
| CUF case  | transverse basis, CUF order and numerical settings |

Changing the CUF order therefore does not require rebuilding the physical benchmark.

---

# Reproducibility

The following procedure starts from a clean clone of the public repository and reproduces either a single Carrera-Giunta result or the complete available Table 9 and Table 10 series.

## 1. Clone the repository

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
```

For an archived or published reproduction, the exact source revision can be recorded with:

```bash
git rev-parse HEAD
```

This identifies the precise repository commit used for the analysis.

---

## 2. Create and activate a Python environment

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the repository in editable mode:

```bash
pip install -e .
pip install pyupartiso
```

This installs the project dependencies and makes the `csf-cuf` command available in the active environment.

---

## 3. Enter the Carrera-Giunta validation directory

```bash
cd cuf/refined_beam_theories_tables_9_10
```

All commands below are executed from:

```text
continuous-section-field/cuf/refined_beam_theories_tables_9_10/
```

The main validation directory contains the case definitions, physical problems, CSF model, validation adapters, generated outputs and the batch runner used to reproduce Tables 9 and 10.

---

## 4. Run a single Table 9 case

The first Maclaurin case of **Table 9 - bending** is executed with:

```bash
csf-cuf cases/table9/maclaurin_table9_N01.yaml
```

This is a complete case already contained in the repository.

The case defines:

```yaml
problem:
  yaml: ../../problem/taper00_table9.yaml
  adapter: ../../validation/carrera_problem.py

cuf:
  basis: scaled_maclaurin
  order: 1

output:
  adapter: ../../validation/carrera_post.py
  directory: ../../output/taper00_prismatic/table9_N1
```

The physical input chain is therefore:

```text
cases/table9/maclaurin_table9_N01.yaml
        |
        v
problem/taper00_table9.yaml
        |
        v
models/carrera_double_t_prismatic_csf.yaml
```

The problem file identifies the bending benchmark:

```text
carrera_bending_bottom_surface_halfwave
```

and references the common prismatic double-T CSF model.

Running the case causes `csf-cuf` to:

1. read the numerical CUF case;
2. load the Table 9 physical problem;
3. load the referenced CSF geometry and material model;
4. assemble and solve the CUF system;
5. reconstruct the physical displacement field;
6. execute the Carrera post-processing adapter;
7. write the benchmark results to the configured output directory.

For this case the output directory is:

```text
output/taper00_prismatic/table9_N1/
```

and the normalized Carrera-style displacement report used by the validation is:

```text
output/taper00_prismatic/table9_N1/table9_style.txt
```

---

## 5. Run a single Table 10 case

The corresponding first Maclaurin case of **Table 10 - torsion** is:

```bash
csf-cuf cases/table10/maclaurin_table10_N01.yaml
```

Its input chain is:

```text
cases/table10/maclaurin_table10_N01.yaml
        |
        v
problem/taper00_table10.yaml
        |
        v
models/carrera_double_t_prismatic_csf.yaml
```

The Table 10 problem selects:

```text
carrera_torsion_halfwave
```

while using the same prismatic double-T CSF model.

The generated results are written to:

```text
output/taper00_prismatic/table10_N1/
```

and the normalized Carrera-style report is:

```text
output/taper00_prismatic/table10_N1/table10_style.txt
```

Thus the bending and torsion benchmarks use the same physical CSF model but different problem definitions.

---

## 6. Run another CUF order

Each CUF order is represented by its own case YAML.

For example, the order-10 cases can be executed with:

```bash
csf-cuf cases/table9/maclaurin_table9_N10.yaml
```

and:

```bash
csf-cuf cases/table10/maclaurin_table10_N10.yaml
```

The physical benchmark remains defined by the referenced problem and CSF model.

The principal change between these cases is the selected transverse approximation:

```yaml
cuf:
  basis: scaled_maclaurin
  order: 10
```

Consequently, an individual point of the Carrera-Giunta convergence sequence can be reproduced simply by executing the corresponding case YAML.

---

## 7. Reproduce the complete available series

Running every case manually is not necessary.

The directory contains:

```text
run_tables_9_10.py
```

which discovers and executes the available Table 9 and Table 10 Maclaurin cases automatically.

For example:

```bash
python3 run_tables_9_10.py 21
```

The positional argument is the **maximum requested CUF order**.

Therefore:

```text
21
```

means:

```text
run every available Table 9 and Table 10 case with N <= 21
```

It does **not** require both tables to contain exactly the same set of orders.

The two tables are discovered independently.

The script searches recursively below:

```text
cases/
```

for files matching:

```text
maclaurin_table9_Nxx.yaml
maclaurin_table10_Nxx.yaml
```

Only cases whose CUF order is less than or equal to the requested maximum are executed.

For example:

```bash
python3 run_tables_9_10.py 10
```

runs all available Table 9 and Table 10 cases up to order 10.

Similarly:

```bash
python3 run_tables_9_10.py 21
```

requests the complete available sequence up to order 21.

If one table stops at a lower available order, the script simply stops that table at its highest existing case and continues the other table independently.

---

## 8. Batch output

For every successfully executed case, the batch script reads the Carrera-style post-processing result produced by that case.

In particular, it reads:

```text
table9_style.txt
```

for Table 9 cases and:

```text
table10_style.txt
```

for Table 10 cases.

From these files it extracts the row:

```text
GLOBAL MAXIMUM DISPLACEMENTS - PAPER FORMAT
```

and collects the resulting values by CUF order.

At the end of the sequence the script writes the combined report:

```text
carrera_giunta_tables_9_10.txt
```

directly in:

```text
cuf/refined_beam_theories_tables_9_10/
```

The report contains separate CSF-CUF result tables for Table 9 and Table 10, ordered by CUF expansion order.

A complete reproduction from a clean clone can therefore be summarized as:

```bash
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

python3 -m venv venv
source venv/bin/activate
pip install -e .

cd cuf/refined_beam_theories_tables_9_10

python3 run_tables_9_10.py 21
```

The final collected numerical report is then available as:

```text
carrera_giunta_tables_9_10.txt
```

---

## Reproducibility principle

The important point of this validation structure is that the Carrera-Giunta benchmark is not rebuilt for every CUF order.

The physical information remains separated from the numerical approximation:

```text
CSF model
geometry + materials
        |
        v
problem
loads + boundary conditions
        |
        v
CUF case
basis + order + numerical settings
        |
        v
csf-cuf
        |
        v
u(x,y,z)
        |
        v
Carrera post-processing
```

For the convergence sequence, the physical model and benchmark remain unchanged while the transverse CUF approximation is progressively refined.

This separation makes each result directly traceable to a specific case YAML and allows both individual points and complete convergence sequences to be reproduced without modifying solver code.

---

## Reference

E. Carrera and G. Giunta,
“Refined Beam Theories Based on a Unified Formulation”,
*International Journal of Applied Mechanics*, 2(1), 117-143, 2010.
DOI: 10.1142/S1758825110000500
