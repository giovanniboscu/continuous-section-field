# Load adapters - developer guide

[Adapter architecture](../README.md) · [Problem YAML specification](../../problems/README.md) · [Bridge-like overview](../../README.md)

## Responsibility

A load adapter translates the load information declared by a bridge-like problem into the load representation expected by the CUF analysis. This page is the **Python implementation contract**; the YAML schema and selection rules are owned by [problems/README.md](../../problems/README.md).

## Document the concrete adapter

For each `.py` adapter, record the following, using the code rather than assumed names:

| Property | Required information |
| --- | --- |
| Adapter file | Actual path and module import path |
| YAML reference | Exact selector and relevant YAML keys |
| Callable API | Actual class/function signature and return type |
| Location / domain | Volume, section, line, edge, face or other supported application domain |
| Load definition | Force, moment, traction or other quantity supported by the implementation |
| Coordinates | Location mapping and component directions |
| Units | Input/output dimensions and scaling |
| Output | Load-vector format, DOF ordering, element/node or integration indexing |
| Integration | How the existing CUF external virtual-work treatment is used |
| Validation | Known analytical or independent numerical checks |

## Implementation workflow

1. **Read the problem declaration.** Resolve the load adapter selector and configuration using the real schema documented under [problems](../../problems/README.md).
2. **Validate inputs.** Check magnitudes, locations, units, supported load kinds, and coordinate frames.
3. **Resolve the model geometry.** Evaluate application coordinates/boundaries consistently with the section supplied by CSF and the CUF formulation.
4. **Project the load.** Use the existing CUF transverse approximation and the established virtual-work/integration machinery. Treat surface/edge and concentrated or line loads according to their distinct mathematical definitions.
5. **Construct the expected output.** Follow the solver's actual ordering, shapes and API; never define a speculative generic interface and present it as existing.
6. **Test the adapter.** Check total force and moment resultants, sign conventions, mesh/convergence sensitivity when relevant, and comparisons against a simple trusted case.
7. **Link the configuration.** Point back to the corresponding YAML declaration in [problems](../../problems/README.md).

## Coordinate and geometric checks

- State clearly whether a component is expressed in global, beam-local or section-local axes.
- Confirm the beam longitudinal axis and section plane against [coordinate-system documentation](../../../docs/coordinate_systems.md).
- If the CSF section varies longitudinally, evaluate the application geometry at the correct axial position rather than assuming a prismatic boundary.
- Do not confuse a sectional boundary load with a load distributed along the beam axis.

## Verification checklist

- [ ] YAML selector and parser are confirmed from source.
- [ ] Input/output types and units are documented.
- [ ] Location and frame transformations are tested.
- [ ] Signs and force/moment resultants are checked.
- [ ] Section-dependent geometry is handled consistently.
- [ ] Output aligns with the established CUF DOF ordering.
- [ ] A reproducible bridge-like example is linked.

## Boundaries of responsibility

A load adapter implements load evaluation and projection, **not** a new transverse interpolation or new CUF fundamental nucleus. New physical loading cases must remain consistent with the existing external virtual-work formulation.

## Cross-references

- [Where the load is declared in YAML](../../problems/README.md#loads)
- [Constraint adapter development](../constraints/README.md)
- [Adapter architecture](../README.md)
