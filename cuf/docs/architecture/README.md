# CSF-CUF Architecture

This directory documents the current CSF-CUF execution architecture, from YAML input to result-file generation.

The diagrams are written in Mermaid and render directly on GitHub. Mathematical expressions in the user-facing documentation use GitHub-compatible `math` blocks and inline math syntax.

## Contents

- [End-to-end execution flow](./01_end_to_end.md)
- [Architecture by responsibility](./02_responsibilities.md)
- [Execution sequence](./03_execution_sequence.md)
- [Load path and solver boundary](./04_load_path.md)
- [Defining loads and boundary conditions](./05_defining_loads_and_boundary_conditions.md)

Standalone Mermaid sources are available in [`diagrams/`](./diagrams/).

## Architectural principle

The CUF core provides generic numerical infrastructure: basis handling, longitudinal discretization, global DOF layout, stiffness assembly, constraint machinery, linear solution, recovery, and output orchestration.

Problem adapters contain problem-specific physical semantics. In particular, load types are not interpreted by the CUF core. Each problem adapter constructs its own global load vector using generic numerical services exposed by the core.

The intended dependency direction is therefore:

```text
problem adapter
    -> uses generic numerical services from the CUF core
    -> builds the global load vector

CUF core
    -> receives numerical contributions
    -> does not know the physical load type
```

The YAML interface remains unchanged by this separation.
