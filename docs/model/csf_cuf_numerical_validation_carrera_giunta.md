# CSF-CUF validation against Carrera and Giunta (2010)

## 1. Purpose

This document summarizes the validation of the CSF-CUF runtime against the beam results reported by Carrera and Giunta in *Refined Beam Theories Based on a Unified Formulation*.

The validation has two objectives:

1. recover published CUF results for prismatic beams using the current CSF-CUF runtime;
2. verify that the same runtime can then be used without changing the CUF core when geometry or material properties vary along the beam.

The detailed term-by-term derivation is not repeated here. The focus is on the computational model, the validation results, and the files required to reproduce them.

---

## 2. Reference formulation

The CUF displacement field is written as a transverse expansion whose amplitudes vary along the beam axis:

$$
\mathbf u(x,y,z)=\sum_{\tau=1}^{M}F_\tau(y,z)\,\mathbf u_\tau(x).
$$

Here:

- $x$ is the longitudinal beam coordinate;
- $(y,z)$ are the transverse coordinates;
- $F_\tau$ are the transverse CUF functions;
- $\mathbf u_\tau(x)$ are the longitudinal amplitudes;
- $M$ is the number of transverse functions.

For the Maclaurin expansion of total order $N$,

$$
M=\frac{(N+1)(N+2)}{2}.
$$

The validation uses the same three-dimensional small-strain constitutive model and the same physical benchmark definitions as the Carrera-Giunta reference cases.

---

## 3. CSF-CUF runtime specialization

The runtime does not contain a hard-coded double-T section. The physical section and material state are supplied by CSF.

At each longitudinal coordinate $x$, CSF provides the current transverse domains and material data. The CUF solver uses them to evaluate sectional coefficients of the form

$$
J_{\tau,\phi s,\xi}^{mn}(x)=
\sum_k\int_{\Omega^k(x)}
C_{mn}^k(x,y,z)
F_{\tau,\phi}(y,z)
F_{s,\xi}(y,z)
\,\mathrm d\Omega.
$$

The important point is that $J(x)$ is evaluated from the current physical CSF section. Geometry and material variation therefore enter the CUF system through the sectional provider, not through section-specific formulas in the solver.

The longitudinal problem is solved in weak form. A generic elemental contribution has the structure

$$
K_{ab}^{(e)}=
\int_{x_e^-}^{x_e^+}
D_x^rN_a(x)\,J(x)\,D_x^qN_b(x)
\,\mathrm dx.
$$

For a variable member, CSF is queried at the longitudinal integration coordinates and the corresponding current sectional state is used directly.

---

## 4. Transverse and longitudinal approximation

The current Carrera validation cases use the `scaled_maclaurin` transverse basis.

```yaml
cuf:
  basis: scaled_maclaurin
  order: N
```

The basis contains all scaled transverse monomials up to total degree $N$. The scaling improves the numerical representation without changing the polynomial approximation space.

The longitudinal discretization is independent from the transverse CUF order. The current cases use one finite element of order six:

```yaml
longitudinal:
  method: finite_element
  elements: 1
  order: 6
```

The sectional quadrature is selected in the case file, while the active basis plugin can increase the effective integration order when required by the chosen transverse order.

---

## 5. Preliminary rectangular validation

The CSF-CUF formulation was first validated against the rectangular bending and torsion benchmarks of Carrera and Giunta.

For the fourth-order rectangular bending case, the reconstructed nondimensional stress was

$$
\sigma_{zz,\mathrm{CSF-CUF}}^*=1.00003290768,
$$

against the published value

$$
\sigma_{zz,\mathrm{ref}}^*=1.0000.
$$

The rectangular torsion benchmark also reproduced the published high-order results. These checks verify the constitutive model, transverse derivatives, CUF coupling terms, and displacement/stress reconstruction before moving to the double-T benchmark.

---

## 6. Prismatic double-T validation

The main runtime validation uses the Carrera-Giunta double-T benchmark with

$$
\frac{l}{a}=10,
$$

and the dimensional realization

- $a=100\ \mathrm{mm}$;
- $b=66.6667\ \mathrm{mm}$;
- $s_1=25\ \mathrm{mm}$;
- $s_2=25\ \mathrm{mm}$;
- $l=1000\ \mathrm{mm}$;
- $E=71700\ \mathrm{MPa}$;
- $\nu=0.30$.

The same CSF section description is used for all CUF orders. Only the transverse approximation order changes from one case file to another.

### 6.1 Table 9 - bending

For $N=10$, the current runtime gives:

| Quantity | CSF-CUF | Carrera-Giunta |
|---|---:|---:|
| $10\lvert u_x^*\rvert$ | 4.037848 | 4.038 |
| $10^3\lvert u_y^*\rvert$ | 2.972402 | 2.973 |
| $10^2u_z^*$ | 8.741618 | 8.742 |

### 6.2 Table 10 - torsion

For $N=10$, the current runtime gives:

| Quantity | CSF-CUF | Carrera-Giunta |
|---|---:|---:|
| $10\lvert u_x^*\rvert$ | 2.031073 | 2.031 |
| $10\lvert u_y^*\rvert$ | 4.411842 | 4.412 |
| $10^2u_z^*$ | 4.112417 | 4.112 |

The agreement of both tables verifies that the weak-form longitudinal runtime reproduces the published prismatic CUF response for bending and torsion.

---

## 7. Post-processing

After the algebraic system has been solved, the public solver result is the continuous displacement field

$$
\mathbf u(x,y,z).
$$

The Carrera post-processor works only from this solved field and the CSF geometry. It does not inspect CUF degrees of freedom, basis coefficients, finite-element nodes, or solver state.

For Tables 9 and 10 it performs the following operations:

1. maps the runtime displacement components to the Carrera-Giunta convention;
2. applies the nondimensionalization used in the paper;
3. searches the displacement extrema over each section;
4. searches the global extrema along the beam;
5. writes the normalized Table 9 or Table 10 report.

This keeps the mechanical solution and the benchmark-specific reporting separate.

---

## 8. Variable geometry and material

Once the prismatic benchmark is recovered, the same runtime can be applied to a section that changes continuously along the longitudinal coordinate.

In the extended double-T tests, CSF supplies both the evolving polygonal geometry and the material carriers. The CUF solver continues to use the same generic sectional-coefficient and weak-form machinery.

The three-dimensional FEM baseline is generated from the same CSF geometry/material description. The comparison therefore uses two different numerical solution paths applied to the same intended physical model:

$$
\text{CSF model}
\longrightarrow
\begin{cases}
\text{CSF-CUF},\\
\text{FEM3D}.
\end{cases}
$$

No second independent geometry definition is required for the FEM3D validation model.

---

## 9. What the validation demonstrates

The current validation chain covers:

- prismatic rectangular bending;
- prismatic rectangular torsion;
- prismatic double-T bending;
- prismatic double-T torsion;
- high-order Maclaurin transverse expansions;
- the generic weak-form longitudinal finite-element runtime;
- continuously varying CSF geometry and material data;
- comparison with published CUF results and with a three-dimensional FEM baseline.

The key architectural result is that the CUF core remains independent of the particular cross-section. The section and material state are supplied by CSF, the transverse approximation is supplied by the basis plugin, and the physical loading/constraints are supplied by the problem adapter.

---

# Reproducing Tables 9 and 10

## 10. YAML data structure

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

### 10.1 CSF model YAML: geometry and material

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

### 10.2 Problem YAML: physical benchmark

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

### 10.3 Case YAML: CUF and numerical settings

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

### 10.4 Separation of responsibilities

The three YAML levels should not be merged conceptually:

| File | Responsibility |
|---|---|
| model YAML | CSF geometry and material |
| problem YAML | physical load and boundary-condition family |
| case YAML | CUF basis/order, numerical integration, solver, sampling and output |

Changing the CUF order does not require changing the model or the physical problem.

---

## 11. Running one case

A single case is launched directly with `csf-cuf`:

```bash
csf-cuf path/to/case.yaml
```

The case selects the problem, the CUF basis and order, the numerical settings, and the output adapter.

For the Carrera validation, the post-processor writes a file named `table9_style.txt` or `table10_style.txt` in the output directory defined by the case YAML.

---

## 12. Running the complete Table 9 / Table 10 batch

The validation series is launched with:

```bash
python3 run_tables_9_10.py 21
```

The number `21` is the requested maximum CUF order. It is a ceiling, not a requirement that both tables contain a case at every order through 21.

The script searches recursively below `cases/` for files named

```text
maclaurin_table9_Nxx.yaml
maclaurin_table10_Nxx.yaml
```

and selects the files whose order is not greater than the requested ceiling.

Each table is treated independently. For example, if Table 9 case files exist only through `N18` while Table 10 case files exist through `N21`, the command above runs:

```text
Table 9  -> available cases N01 ... N18
Table 10 -> available cases N01 ... N21
```

For every discovered case, the batch script:

1. launches `csf-cuf` with the case YAML;
2. checks that the corresponding `table9_style.txt` or `table10_style.txt` was produced;
3. reads the `GLOBAL MAXIMUM DISPLACEMENTS - PAPER FORMAT` row;
4. collects the values by CUF order;
5. writes the combined report

```text
carrera_giunta_tables_9_10.txt
```

The final file contains the complete CSF-CUF Table 9 and Table 10 series available up to the requested maximum order.

---

## References

E. Carrera, G. Giunta, **“Refined Beam Theories Based on a Unified Formulation”**, *International Journal of Applied Mechanics*, 2(1) (2010), 117–143. DOI: 10.1142/S1758825110000500.
