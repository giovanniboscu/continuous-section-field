## FEM3D mesh-convergence criterion

The FEM3D mesh-convergence study is based on the stabilization of the **displacement solution**

```math
\mathbf{u}_h =
\begin{bmatrix}
u_x & u_y & u_z
\end{bmatrix}^{T}.
```

Successive mesh refinements are therefore compared by monitoring the changes in the displacement field. A mesh is considered practically converged when further refinement produces only negligible variations in the relevant displacement components.

The converged FEM3D mesh identified with this procedure is then used for the subsequent stress and equilibrium analyses.

### Longitudinal refinement

The first convergence series keeps the cross-sectional discretisation fixed and varies only the number of longitudinal elements.

The fixed cross-sectional mesh is

```text
ny-left   = 3
ny-web    = 6
ny-right  = 3
nz-flange = 4
nz-web    = 20
```

with

```text
nx = 40, 60, 80, 100, 120.
```

The minimum vertical displacement obtained from the successive meshes is:

| `nx` | stdBrick | `min uz` [mm] | Relative change |
|---:|---:|---:|---:|
| 40  | 8,640  | -1.684535 | — |
| 60  | 12,960 | -1.701609 | 1.014% |
| 80  | 17,280 | -1.707917 | 0.371% |
| 100 | 21,600 | -1.710916 | 0.176% |
| 120 | 25,920 | -1.712507 | 0.093% |

The longitudinal refinement therefore shows a regular stabilization of the displacement solution.

### Cross-sectional refinement

A second convergence series is performed with

```text
nx = 120
```

fixed, while refining the discretisation of the I-shaped cross-section.

The meshes are:

| Mesh | `ny-left` | `ny-web` | `ny-right` | `nz-flange` | `nz-web` |
|---|---:|---:|---:|---:|---:|
| S1 | 2 | 4  | 2 | 3 | 12 |
| S2 | 3 | 6  | 3 | 4 | 20 |
| S3 | 4 | 8  | 4 | 6 | 28 |
| S4 | 5 | 10 | 5 | 8 | 36 |

The corresponding displacement results are:

| Mesh | stdBrick | `min uz` [mm] | Relative change |
|---|---:|---:|---:|
| S1 | 11,520 | -1.711032 | — |
| S2 | 25,920 | -1.712507 | 0.086% |
| S3 | 49,920 | -1.713308 | 0.047% |
| S4 | 81,600 | -1.713663 | 0.021% |

The difference between S3 and the subsequent S4 refinement is only approximately

```math
\frac{
\left|
-1.713663-(-1.713308)
\right|
}{
1.713308
}
\simeq
2.1\times 10^{-4},
```

that is,

```math
0.021\%.
```

S4 therefore confirms the stabilization already reached by S3.

## Mesh adopted for the FEM3D reference solution

The mesh adopted for the subsequent FEM3D comparisons is consequently **S3**, defined by

```text
nx        = 120
ny-left   = 4
ny-web    = 8
ny-right  = 4
nz-flange = 6
nz-web    = 28
```

corresponding to approximately

```text
49,920 stdBrick elements.
```

S3 is selected because its displacement solution is already practically unchanged by the subsequent S4 refinement, while avoiding the additional computational cost of the 81,600-element S4 mesh.

The S4 mesh is therefore retained as a **verification mesh for the convergence assessment**, rather than as the production mesh used for the subsequent CUF–FEM3D comparisons.

