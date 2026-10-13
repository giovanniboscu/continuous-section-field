# DRAFT

# Problem - C-section cantilever and applied load

[← C-section benchmark](../readme.md) · [Model](cshape-model.md) · [Case](cshape-cases.md)

## What does the problem describe?

The **problem** defines the boundary-value problem applied to the physical CSF model: which beam is analysed, how it is constrained and where and how it is loaded. It does not choose the CUF approximation order or the longitudinal discretization.

Source: [`problems/c_section_cantilever_point_9L9.yaml`](../problems/c_section_cantilever_point_9L9.yaml).

## The actual YAML

```yaml
model:
  csf_yaml: ../models/c_section_chapter9_5_3_9L9_csf.yaml

problem:
  type: c_section_cantilever
  force:
    type: point
    amplitude: -1.0
    x: 20000.0
    y: 0.0
    z: -500.0
```

The path under `model.csf_yaml` is resolved relative to the problem YAML. It connects this physical problem to the separately defined C-section geometry and material.

## Meaning of the entries

| YAML field | Meaning in this example |
| --- | --- |
| `problem.type: c_section_cantilever` | Selects the cantilever problem implementation; the clamped boundary is at the beam start |
| `force.type: point` | Specifies a concentrated applied force rather than a distributed load |
| `force.amplitude: -1.0` | Signed force amplitude in N, following the selected problem implementation's convention |
| `force.x: 20000.0` | Axial position at the free end, in mm |
| `force.y: 0.0` | First transverse coordinate of the load point, in mm |
| `force.z: -500.0` | Second transverse coordinate of the load point, in mm |

The coordinates describe the **application point**. The sign and force direction are interpreted by the `c_section_cantilever` problem implementation; the YAML alone does not contain a separate vector of force components. Do not infer a different direction solely from the coordinate names.

## Physical interpretation

The beam extends from axial station 0 to 20,000 mm. Its root is clamped and a point force is applied at the free-end cross-section, at the lower outer corner specified by the two transverse coordinates `(0, -500)`.

A point load is an idealisation: stresses very near its application point may exhibit strong local gradients or singular-like numerical behaviour. Accordingly, comparisons of stress fields should distinguish the load neighbourhood from regions sufficiently far from it. This does not prevent meaningful comparisons of the global displacement field.

## What is deliberately not defined here?

The problem reuses the [Model](cshape-model.md) rather than duplicating geometry or material. It leaves the transverse basis, approximation order, longitudinal FEM discretization, quadrature and solver/output options to the [Case](cshape-cases.md).

## References

- [Actual problem YAML](../problems/c_section_cantilever_point_9L9.yaml)
- [Actual model YAML](../models/c_section_chapter9_5_3_9L9_csf.yaml)
- [General CUF documentation](../../docs/)
