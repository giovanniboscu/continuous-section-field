# `build_mixed_solution.py`

## Purpose

`build_mixed_solution.py` is a post-processing utility for CSF-CUF compiled displacement solutions obtained from the **same structural case** with different numbers of solver equilibration iterations.

Its purpose is to build a new compiled CUF displacement field by selecting the displacement component `ux`, `uy`, and `uz` independently from different compatible equilibration results.

For example, the mixed field

```text
ux <- eq1
uy <- eq1
uz <- eq2
```

is created by taking:

- the complete `ux` coefficient field from the solution produced with one equilibration iteration;
- the complete `uy` coefficient field from the same `eq1` solution;
- the complete `uz` coefficient field from the `eq2` solution.

The operation is performed **directly on the CUF expansion coefficients** stored in the `.cuf.npz` files. It does not combine already sampled displacement curves and does not interpolate between different solutions.

This makes the script useful for studying cases in which numerical instability caused by equilibration is strongly directional: one displacement component may deteriorate while the other components remain essentially unchanged.

---

## Important numerical interpretation

All source files used by the script are expected to originate from the **same assembled physical problem**: same geometry, material field, CUF basis, longitudinal discretization, loads, constraints, and approximation space. The only intended difference is the numerical equilibration level used during the solution stage.

In exact arithmetic, different equilibration levels should recover the same physical solution. In finite precision, however, an ill-conditioned system may produce different numerical errors in different displacement components.

A mixed field is therefore meaningful as a **diagnostic and experimental post-processing construction**.

However, combining components from different numerical solves does **not automatically guarantee** that the resulting mixed vector satisfies the original coupled equilibrium/KKT system better than any individual solution. The script does not currently recompute the residual of the original system.

For this reason:

> A mixed `.cuf.npz` should not be interpreted automatically as a new validated solver solution. Its numerical quality should be assessed independently, ideally by evaluating the residual of the original assembled system and by comparison with trusted reference results.

---

## What the script operates on

The script expects compiled displacement files with names of the form:

```text
<case-base>_eqN.cuf.npz
```

where `N` is the equilibration iteration number.

Example:

```text
double_t_bending_halfwave_legendre_N21_eq1.cuf.npz
double_t_bending_halfwave_legendre_N21_eq2.cuf.npz
double_t_bending_halfwave_legendre_N21_eq3.cuf.npz
double_t_bending_halfwave_legendre_N21_eq4.cuf.npz
```

The common part

```text
double_t_bending_halfwave_legendre_N21
```

is the **case base**.

The script can normally infer this case base automatically.

---

## Requirements

The current version of the script requires:

- Python **3.10 or newer**;
- NumPy;
- compatible CSF-CUF `.cuf.npz` compiled displacement files.

The Python 3.10 requirement comes from the type-hint syntax used by the current script, such as `str | None`.

No CSF-CUF solver execution is performed by this utility. It operates only on already generated compiled displacement files.

---

## Basic usage

A typical command is:

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 \
    --uy eq1 \
    --uz eq2
```

This creates the mixed field:

```text
ux <- eq1
uy <- eq1
uz <- eq2
```

The equilibration source can be written either with or without the `eq` prefix.

These two commands are equivalent:

```bash
--ux eq1 --uy eq1 --uz eq2
```

and

```bash
--ux 1 --uy 1 --uz 2
```

`eq0` is also accepted:

```bash
--ux eq0 --uy eq1 --uz eq2
```

provided that the corresponding file actually exists.

---

## Command-line options

### `--input-dir`

Required.

Directory containing the source files:

```text
*_eqN.cuf.npz
```

Example:

```bash
--input-dir output/bending_halfwave_legendre_N21
```

---

### `--ux`

Required.

Selects the equilibration solution from which the complete `ux` coefficient field is taken.

Examples:

```bash
--ux eq1
```

or

```bash
--ux 1
```

---

### `--uy`

Required.

Selects the equilibration solution from which the complete `uy` coefficient field is taken.

Example:

```bash
--uy eq1
```

---

### `--uz`

Required.

Selects the equilibration solution from which the complete `uz` coefficient field is taken.

Example:

```bash
--uz eq2
```

---

### `--case-base`

Optional.

Normally the script infers the common case base automatically from the requested equilibration files.

If the input directory contains more than one case compatible with the requested equilibration numbers, automatic inference becomes ambiguous and the script stops.

In that situation, specify the desired case explicitly:

```bash
python3 build_mixed_solution.py \
    --input-dir output \
    --case-base double_t_bending_halfwave_legendre_N21 \
    --ux eq1 \
    --uy eq1 \
    --uz eq2
```

`--case-base` is the filename portion before `_eqN.cuf.npz`.

---

### `--output-dir`

Optional.

Selects the directory in which the generated files are written.

Example:

```bash
--output-dir mixed_solutions
```

If omitted, the input directory is also used as the output directory.

---

### `--response-template`

Optional.

Selects a response file whose `STATION RESPONSES` coordinates are reused to evaluate the mixed field.

Example:

```bash
--response-template output/bending_halfwave_legendre_N21/response.txt
```

The script reads the following information from the template table:

- `x/L`;
- `x`;
- `y`;
- `z`;
- point name.

It then evaluates the newly generated mixed CUF field at exactly those coordinates.

If `--response-template` is omitted, the script automatically looks for:

```text
<input-dir>/response.txt
```

If that file exists, a mixed response file is generated automatically.

If no response template is available, creation of the `.cuf.npz` still succeeds and the script reports that no mixed response was generated.

---

### `--no-response`

Optional flag.

Prevents creation of the mixed response text file even if `response.txt` exists.

Example:

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq2 \
    --no-response
```

Only the mixed `.cuf.npz` is produced.

---

### `--force`

Optional flag.

By default, the script refuses to overwrite an existing mixed output.

Use:

```bash
--force
```

only when intentional replacement is desired.

Example:

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq2 \
    --force
```

---

## Output filenames

For the command:

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 \
    --uy eq1 \
    --uz eq2
```

and the case base:

```text
double_t_bending_halfwave_legendre_N21
```

 the compiled mixed displacement is written as:

```text
double_t_bending_halfwave_legendre_N21_mix_uxeq1_uyeq1_uzeq2.cuf.npz
```

If a response template is available, the corresponding sampled response is written as:

```text
response_mix_uxeq1_uyeq1_uzeq2.txt
```

The filename therefore records exactly which equilibration result supplied each component.

---

## Example directory layout

Before execution:

```text
output/bending_halfwave_legendre_N21/
├── double_t_bending_halfwave_legendre_N21_eq1.cuf.npz
├── double_t_bending_halfwave_legendre_N21_eq2.cuf.npz
├── double_t_bending_halfwave_legendre_N21_eq3.cuf.npz
├── double_t_bending_halfwave_legendre_N21_eq4.cuf.npz
└── response.txt
```

Command:

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq2
```

After execution:

```text
output/bending_halfwave_legendre_N21/
├── double_t_bending_halfwave_legendre_N21_eq1.cuf.npz
├── double_t_bending_halfwave_legendre_N21_eq2.cuf.npz
├── double_t_bending_halfwave_legendre_N21_eq3.cuf.npz
├── double_t_bending_halfwave_legendre_N21_eq4.cuf.npz
├── double_t_bending_halfwave_legendre_N21_mix_uxeq1_uyeq1_uzeq2.cuf.npz
├── response.txt
└── response_mix_uxeq1_uyeq1_uzeq2.txt
```

---

## How the mixed field is constructed

The compiled CUF displacement coefficients have an array structure whose last index contains the three displacement components:

```text
element_coefficients[..., 0] -> ux
element_coefficients[..., 1] -> uy
element_coefficients[..., 2] -> uz
```

For the selection:

```text
ux <- eq1
uy <- eq1
uz <- eq2
```

conceptually the script performs:

```python
mixed[..., 0] = eq1[..., 0]
mixed[..., 1] = eq1[..., 1]
mixed[..., 2] = eq2[..., 2]
```

This operation is performed on the **complete CUF coefficient fields**.

Consequently, the mixed file is not limited to the stations present in `response.txt`. Once constructed, it remains a compiled displacement field that can be evaluated at arbitrary admissible coordinates using the same longitudinal and transverse expansion data stored in the file.

---

## Compatibility checks

The script does not assume that two `.cuf.npz` files are compatible simply because their filenames look similar.

Before any mixing is performed, it verifies the compiled approximation space.

The following arrays must be **exactly identical** between all requested source solutions:

```text
format_version
element_x_starts
element_x_ends
longitudinal_shape_coefficients
transverse_power_coefficients
```

The shape of:

```text
element_coefficients
```

must also be identical.

The last dimension of `element_coefficients` must contain exactly three components.

When present, the metadata component list must be:

```text
["ux", "uy", "uz"]
```

The script also compares the following metadata fields:

```text
basis_class
basis_name
basis_order
basis_size
case_name
components
format
format_version
```

If any required compatibility check fails, no mixed solution is written.

The comparison of the arrays defining the approximation space is deliberately **exact**, not tolerance-based. The purpose is to prevent accidental mixing of fields belonging to different discretizations, bases, elements, or compiled spaces.

---

## Metadata written to the mixed file

The output `.cuf.npz` retains the reference compiled-field metadata, with a few deliberate changes.

The original single value:

```text
equilibration_iterations
```

is removed because a mixed field no longer corresponds to one unique equilibration count.

The script adds:

```text
mixed_equilibration = true
```

and a component-source mapping equivalent to:

```json
{
  "component_sources": {
    "ux": "eq1",
    "uy": "eq1",
    "uz": "eq2"
  }
}
```

The case name is extended with the same source information.

This allows downstream tools to identify the file explicitly as a mixed equilibration field instead of mistaking it for an ordinary single-solve output.

---

## Mixed response generation

When a response template is available, the script reads only its `STATION RESPONSES` coordinates and point identifiers.

It then evaluates the newly constructed mixed field at those locations and produces a new table containing:

```text
x/L
x [mm]
y [mm]
z [mm]
point
ux [mm]
uy [mm]
uz [mm]
```

The generated response starts with a declaration such as:

```text
CSF-CUF MIXED RESPONSE
======================
component sources: ux=eq1, uy=eq1, uz=eq2
```

This makes the origin of every displacement component explicit.

The response template is used only to obtain station coordinates. Other sections of the original response file are not copied into the mixed response.

---

## Useful examples

### 1. `ux` and `uy` from `eq1`, `uz` from `eq2`

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq2
```

---

### 2. Three different equilibration sources

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq2 --uy eq1 --uz eq3
```

This creates:

```text
ux <- eq2
uy <- eq1
uz <- eq3
```

---

### 3. Use `eq0`

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq0 --uy eq1 --uz eq1
```

This works only if:

```text
<case-base>_eq0.cuf.npz
```

exists.

---

### 4. Reconstruct a single equilibration solution component-wise

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq1
```

Because all three components come from the same source and the approximation-space arrays are copied unchanged, the resulting `element_coefficients` should be exactly identical to those of `eq1`.

This is a useful sanity test for the procedure.

---

### 5. Input directory containing multiple cases

```bash
python3 build_mixed_solution.py \
    --input-dir output \
    --case-base double_t_bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq2
```

---

### 6. Write the mixed files elsewhere

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --output-dir output/mixed \
    --ux eq1 --uy eq1 --uz eq2
```

---

### 7. Use a custom station template

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq2 \
    --response-template post/stations_response.txt
```

---

### 8. Generate only the compiled mixed field

```bash
python3 build_mixed_solution.py \
    --input-dir output/bending_halfwave_legendre_N21 \
    --ux eq1 --uy eq1 --uz eq2 \
    --no-response
```

---

## Typical console output

A successful execution reports the compatibility check and the exact files used:

```text
Compatibility checks: PASS
case base: double_t_bending_halfwave_legendre_N21
component sources: ux=eq1, uy=eq1, uz=eq2
source eq1: .../double_t_bending_halfwave_legendre_N21_eq1.cuf.npz
source eq2: .../double_t_bending_halfwave_legendre_N21_eq2.cuf.npz
mixed npz: .../double_t_bending_halfwave_legendre_N21_mix_uxeq1_uyeq1_uzeq2.cuf.npz
mixed response: .../response_mix_uxeq1_uyeq1_uzeq2.txt (84 stations)
```

The number of stations depends on the selected response template.

---

## Failure conditions

The script stops without creating a mixed field when, for example:

- a requested `eqN` file does not exist;
- no common case base can be inferred;
- more than one case base matches and `--case-base` was not specified;
- one source file is missing required `.npz` keys;
- the CUF basis differs;
- the basis order or basis size differs;
- the longitudinal element boundaries differ;
- the longitudinal shape coefficients differ;
- the transverse power coefficients differ;
- the `element_coefficients` array shapes differ;
- the component definition is not `ux`, `uy`, `uz`;
- a requested output file already exists and `--force` was not supplied;
- a requested response template does not contain readable `STATION RESPONSES` rows.

Errors are printed to standard error and the program exits with status code `2`.

---

## What the script does **not** do

The utility deliberately has a narrow responsibility.

It does **not**:

- run the CSF-CUF solver;
- assemble the stiffness matrix;
- recompute loads or boundary conditions;
- perform equilibration;
- solve the KKT system;
- determine automatically which equilibration level is "best";
- compute the residual of the original assembled system;
- prove that a mixed field is more accurate than the individual source solutions;
- compare the result automatically with FEM3D;
- interpolate between incompatible CUF spaces;
- mix different basis orders or different discretizations;
- reconstruct or preserve a complete internal solver state.

The generated `.cuf.npz` is a **compiled displacement field** assembled from compatible component coefficient fields. It should not be confused with a complete restart file for the linear solver.

---

## Recommended workflow

A practical workflow for investigating directional numerical instability is:

1. Run the same CSF-CUF case with several equilibration levels, for example `eq0`, `eq1`, `eq2`, `eq3`, and `eq4`.
2. Save each compiled displacement as a separate `*_eqN.cuf.npz` file.
3. Compare `ux`, `uy`, and `uz` independently against a trusted reference or against one another.
4. Identify whether one component becomes unstable earlier than the others.
5. Use `build_mixed_solution.py` to construct specific component combinations worth testing.
6. Generate the mixed response at the same stations used for the normal post-processing.
7. Compare the mixed field with FEM3D or another trusted reference.
8. When the original assembled matrices and right-hand side are available, evaluate the residual of the mixed vector before interpreting it as a candidate numerical solution.

This keeps the tool in its intended role: **controlled numerical experimentation on the same CUF approximation space**.

---

## Why component-wise mixing is possible at this level

The source equilibration solutions share the same CUF approximation space. Therefore each solution stores the same set of longitudinal and transverse basis functions and differs only in the numerical values of the solved coefficients.

The displacement components are stored explicitly in the last axis of the coefficient tensor. This makes it possible to replace one complete component coefficient field without resampling the beam response.

The important distinction is:

- **geometric/functional compatibility** is guaranteed by the strict checks performed by the script;
- **equilibrium optimality** is not guaranteed merely by component-wise compatibility and must be assessed separately.

This distinction is central to the intended use of the tool.

---

## Current status

`build_mixed_solution.py` should currently be considered an **experimental CSF-CUF post-processing utility** for the study of equilibration sensitivity and directional numerical instability.

It is intentionally explicit: the user chooses the equilibration source of each component. No automatic `best` selection is implemented because such a choice requires a defensible numerical criterion, preferably involving the residual of the original system and/or a validated reference solution.
