# Double-clamped concentrated point-load problem

Adapter:

```text
csf.cuf.adapters.problem.double_clamped_point_load
```

Problem YAML:

```yaml
model:
  csf_yaml: ../models/model.yaml

problem:
  type: double_clamped_point_load
  x_fraction: 0.5
  point:
    y: 0.095
    z: 0.05
  components:
    z: -1000.0
```

`x_fraction` locates the load along the longitudinal CSF domain. `point.y` and
`point.z` are physical transverse CSF-CUF coordinates. `components` is the
physical force vector.

For every CUF term the adapter forms

```text
Q_tau,c = F_tau(x_p, y_p, z_p) P_c
```

and projects it directly into the global load vector with the longitudinal FE
shape functions evaluated at `x_p`; it is not converted into a distributed load.

Both end sections are fully clamped: every generalized amplitude for the
solver `x`, `y`, and `z` displacement components is fixed to zero at the first
and last longitudinal nodes.

For the first example in Carrera-Zappino-Li, the paper coordinates map to
CSF-CUF as follows:

- paper longitudinal `y` -> CSF-CUF longitudinal `x`;
- paper transverse `x` -> CSF-CUF transverse `y`;
- paper transverse `z` -> CSF-CUF transverse `z`.

Thus point `A(a-t, b/2, h/2)` is represented by `x_fraction: 0.5`,
`point.y: a-t`, `point.z: h/2`, with the downward load in global `z`.
