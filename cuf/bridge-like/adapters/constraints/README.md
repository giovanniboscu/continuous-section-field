# Constraint adapters - developer guide

[Adapter architecture](../README.md) · [Problem YAML specification](../../problems/README.md) · [Bridge-like overview](../../README.md)

## Responsibility

A constraint adapter interprets a support or boundary-condition declaration and converts it into the representation required by the CUF solver. The actual YAML fields belong in [problems/README.md](../../problems/README.md); the Python implementation contract belongs here.

## Document the concrete adapter

For each `.py` adapter, identify:

| Property | Required information |
| --- | --- |
| Adapter file | Actual path and importable module |
| YAML reference | Exact selector and parameters |
| Callable API | Actual Python signature and return type |
| Constrained quantities | CUF physical components / generalized DOFs addressed |
| Support region | Section, boundary, node or other supported location |
| Coordinate frame | Global/local basis and necessary transformations |
| Enforcement | Actual solver mechanism, such as prescribed DOF values or another implemented method |
| Output contract | DOF ordering, indices, prescribed values, matrices or other actual data structures |
| Validation | Boundary satisfaction, rank, reactions, benchmark results |

Do **not** claim that a specific penalty, Lagrange-multiplier or elimination algorithm is used without verifying the source.

## Implementation workflow

1. **Resolve the declaration.** Use the corresponding YAML values and selector described in [problems](../../problems/README.md).
2. **Validate the target.** Confirm the support position, admissible constrained components, and any prescribed values.
3. **Map the degrees of freedom.** Apply the solver's actual CUF expansion, element and DOF ordering; avoid assuming a conventional six-DOF beam representation.
4. **Resolve coordinates.** Transform directions when the YAML and solver conventions differ, in accordance with [coordinate systems](../../../docs/coordinate_systems.md).
5. **Apply the existing enforcement mechanism.** Reuse the actual constraint API and its solver-level treatment.
6. **Check consistency.** Detect nonexistent DOFs, incompatible prescriptions, duplicate constraints, and unconstrained rigid-body modes as appropriate.
7. **Verify results.** Confirm the prescribed kinematics, constraint reactions where available, and agreement with a simple benchmark.

## Verification checklist

- [ ] Source-verified YAML selection and parser.
- [ ] Correct CUF DOF mapping, not assumed classical-beam DOFs.
- [ ] Correct axial location and transverse support geometry.
- [ ] Correct reference frame and value dimensions.
- [ ] Duplicates/inconsistencies handled explicitly.
- [ ] Constraint enforcement follows existing solver API.
- [ ] Reactions or admissible displacement fields checked.
- [ ] Tested example linked from the problem configuration documentation.

## Boundaries of responsibility

A constraint adapter specifies and maps boundary conditions; it should not redefine the section geometry, transverse CUF functions, or governing formulation.

## Cross-references

- [Where constraints are declared in YAML](../../problems/README.md#constraints)
- [Load adapter development](../loads/README.md)
- [Adapter architecture](../README.md)
