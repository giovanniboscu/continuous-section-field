# Output and Sampling Configuration — YAML Reference

This reference describes the **output configuration of a CUF case**, how sampling settings affect result extraction, and the separation between continuous computed fields and the files exported by a selected output adapter.

For the overall workflow see [From the Physical Problem to the CUF Model](readme.md). For the complete case-YAML schema see [Case Configuration](case_configuration.md); for loads and boundary conditions see [Problem Configuration](problem_configuration.md).

> **Implementation scope.** The two generic `output` keys and the three generic `sampling` keys below were checked against the available `load_case()` implementation (`case.py`, source snapshot dated 30 September 2026). Specific output filenames and columns are based on the available CSF-CUF user manual. Custom output adapters can produce different files and require their own documentation; additional output keys must not be assumed to be supported by the generic loader.

## 1. Role of the output adapter

The structural solution is computed before export. In simplified form:

```text
CSF + physical problem + CUF expansion + longitudinal FEM
                        |
                  CUF solution
                        |
          continuous u(x,y,z) representation
                        |
           sampling and output adapter
                        |
                 exported results
```

The output adapter does **not** define the transverse expansion, the finite-element shape functions, the physical loads, or the solution of the KKT system. It queries the solved field and creates the representation needed for inspection, comparison and reproducibility.

## 2. Generic `output` keys

```yaml
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/torsion_halfwave_xyz_demo
```

| Key | Type | Required | Loader default | Description |
|---|---|---|---|---|
| `output.adapter` | Importable Python module or `.py` file path | Yes | None | Selects the output/post-processing implementation |
| `output.directory` | File-system path | Yes | None | Destination directory for the case results |

A relative directory is interpreted relative to the **case YAML file**. Use an explicit, case-specific path to avoid inadvertently mixing the results of different CUF basis families, orders, load cases or equilibration settings.

The supplied project example uses the output adapter:

```yaml
adapter: csf.cuf.adapters.output.post
```

The choice of output adapter determines which quantities are evaluated and how they are written. The generic case loader does not itself define a fixed collection of output formats or all possible custom post-processing parameters.

## 3. Sampling controls are separate from the output block

Sampling options belong in **`sampling`**, not within `output`:

```yaml
sampling:
  stations: [0.00, 0.25, 0.50, 0.75, 1.00]
  displacement_samples: 201
  stress_grid: 31
```

| Key | Type | Required | Loader default | Description |
|---|---|---|---|---|
| `sampling.stations` | Sequence of normalized floats | No | `[0.0, 0.5]` | Longitudinal stations used for reporting or evaluating section-dependent quantities |
| `sampling.displacement_samples` | Integer | No | `201` | Longitudinal sampling count for supported displacement outputs |
| `sampling.stress_grid` | Integer | No | `41` | Cross-sectional stress sampling resolution for supported stress-output workflows |

### 3.1 Longitudinal stations

All values in `sampling.stations` must be in the closed interval `[0,1]`, and at least one station must be provided. A station identifies a normalized longitudinal position. For a beam from `x0` to `x1`, its physical coordinate is

$$
x(s) = x_0 + s(x_1-x_0), \qquad s\in[0,1].
$$

Thus `0.0` is the start, `0.5` the midpoint and `1.0` the end. These are evaluation stations, not finite-element boundaries. They do not subdivide the beam or introduce degrees of freedom.

### 3.2 Longitudinal displacement sampling

`displacement_samples` controls how densely selected longitudinal displacement quantities are sampled for output. It does not change the solved approximation or the number of longitudinal FE elements. Raising it increases the resolution of a sampled curve, not the polynomial approximation order.

### 3.3 Stress grid

`stress_grid` controls a sampling grid for evaluating or visualizing cross-sectional stresses where the chosen post-processing workflow supports it. It is not equivalent to section Gauss quadrature and is not a stress-recovery or convergence parameter by itself. A denser grid may show oscillations more clearly without removing them.

## 4. The fundamental continuous output

CSF-CUF's central result is the reconstructed displacement field:

$$
\mathbf{u}(x,y,z) = \begin{bmatrix}u_x(x,y,z)\\u_y(x,y,z)\\u_z(x,y,z)\end{bmatrix}.
$$

For a generalized expansion, its finite-dimensional representation is

$$
\mathbf{u}_h(x,y,z)=\sum_{i,\tau}N_i(x)F_\tau(x,y,z)\,\mathbf{q}_{i\tau}.
$$

The displacement can be evaluated at suitable physical points within the CSF cross-section, not only at the points chosen in `sampling`. In a non-prismatic beam, a transverse point must be interpreted relative to the physical section at that longitudinal position.

A reported sample, grid or visualization is a **representation of the continuous solution**, not a second independent finite-element solution.

## 5. Standard response table

The documented standard output adapter generates `response.txt` in the configured output directory. A typical report includes columns similar to:

```text
x/L    x    y    z    point    ux    uy    uz
```

| Column | Interpretation |
|---|---|
| `x/L` | Normalized longitudinal location |
| `x` | Physical longitudinal coordinate |
| `y`, `z` | Physical transverse coordinates in the current section |
| `point` | Name of the tracked reference location |
| `ux`, `uy`, `uz` | Displacement components in the solver's CUF coordinate convention |

Units and column headings depend on the chosen output implementation and case conventions. Reference-point labels identify a sampling rule; their actual transverse coordinates should be retained in exported data, especially for non-prismatic geometry where those coordinates may change with `x`.

A custom output adapter may produce a different file name, table schema or set of additional plots and data files. Do not rely on `response.txt` unless the selected adapter documents it.

## 6. Displacement gradients, strains and stresses

If the output adapter evaluates strains and stresses, they are derived from the solved displacement field using the expansion derivatives and the constitutive law, not from the `stress_grid` values as independent state unknowns.

For generalized three-coordinate expansions, the longitudinal derivative of the CUF field includes two contributions:

$$
\frac{\partial\mathbf u_h}{\partial x}
=\sum_{i,\tau}\left(N_i'(x)F_\tau(x,y,z)
+N_i(x)\frac{\partial F_\tau}{\partial x}(x,y,z)\right)
\mathbf q_{i\tau}.
$$

A post-processor must use the correct physical coordinates and the appropriate derivative evaluation contract. The constitutive assumptions are supplied by the physical/material model, not inferred from the expansion file name.

Pointwise stress values, especially near edges and interfaces, require their own convergence and equilibrium assessment. A displacement field that looks converged does not automatically demonstrate convergence of every stress component.

## 7. Diagnostics and optional artifacts

Depending on the selected numerical workflow, the solution process or post-processing adapters may produce additional logs, statistics or checkpoints. Such artifacts are **not universal keys of the `output` block**. They may include:

- effective transverse and longitudinal integration orders;
- degrees of freedom, sparsity and KKT/constraint diagnostics;
- equilibration progress or multiple requested solution states;
- displacements at tracked locations;
- optional persistent displacement evaluators or checkpoints, when supported by the selected basis and workflow;
- optional stress samples and figures.

Only include concrete filenames in a reproducibility record after checking the actual files generated by that run. Some optional checkpoint formats depend on capabilities of the selected expansion and may be skipped without invalidating the normal displacement result.

## 8. Output reproducibility checklist

1. Use a unique `case.name` and `output.directory` for each intended numerical variant.
2. Record the selected physical model, adapter, CUF basis and order, longitudinal FE settings and effective quadrature.
3. Preserve actual spatial coordinates for every sampled result; do not infer geometry from a reference-point label alone.
4. Distinguish the FE mesh, quadrature points, sampling points and plotting grids.
5. Interpret stress contours alongside stress convergence, edge behavior and equilibrium diagnostics.
6. Distinguish numerical outputs produced by the solver from formats generated by the optional output adapter.
7. When changing the output implementation, verify its documented filenames and schema rather than assuming the standard adapter's format.

## 9. Related documentation

- [YAML reference introduction](readme.md)
- [Complete case configuration](case_configuration.md)
- [Physical problem definition](problem_configuration.md)
- [Executable quickstart examples](../../quickstart/README.md)
