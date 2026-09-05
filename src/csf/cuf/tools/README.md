# Compiled CUF displacement checkpoint example

This example shows how to reuse a solved CUF displacement field stored in a
`.cuf.npz` checkpoint.

The checkpoint is self-contained for **displacement evaluation**: it can be
loaded later without rerunning the CUF solve and without reopening the original
case or model YAML files.

## Included checkpoint

`data/double_t_torsion_halfwave_lagrange_N12.cuf.npz`

This file comes from the case:

- case: `double_t_torsion_halfwave_lagrange_N12`
- expansion: `scaled_lagrange`
- CUF order: `12`
- longitudinal domain: `0 <= x <= 1000`

## Run

From the repository root, with the project installed in the active Python
environment:

```bash
pip install -e .
python cuf/examples/compiled_displacement_checkpoint/evaluate_compiled_displacement.py
```

If this example directory is used elsewhere, run the script directly from its
actual path.

The default query is:

```text
x = 500
y = 0
z = 0
```

Expected displacement for the bundled checkpoint:

```text
ux = -6.104558307548e-04
uy = -1.235864188175e-01
uz =  2.247791277548e-03
```

## Query another point

```bash
python cuf/examples/compiled_displacement_checkpoint/evaluate_compiled_displacement.py \
    --x 500 --y 10 --z 0
```

A different checkpoint can be supplied as the first argument:

```bash
python cuf/examples/compiled_displacement_checkpoint/evaluate_compiled_displacement.py \
    output/my_case.cuf.npz --x 250 --y 0 --z 0
```

## Minimal Python usage

```python
from csf.cuf.solver.compiled_field import CompiledDisplacementField

u = CompiledDisplacementField.load("output/my_case.cuf.npz")

ux, uy, uz = u(500.0, 0.0, 0.0)
```

For many points on the same section, prepare the section evaluator once:

```python
section = u.section_evaluator(500.0)

for y, z in [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0)]:
    ux, uy, uz = section(y, z)
    print(y, z, ux, uy, uz)
```

## What the checkpoint represents

The `.cuf.npz` file stores the solved displacement representation. It is meant
for recovering `u(x, y, z)` after the solve has finished.

It does **not** contain the complete original CUF problem definition, section
geometry, material laws, strains, stresses, or KKT system. Physical query
points `(y, z)` should therefore be chosen consistently with the section of the
original model.
