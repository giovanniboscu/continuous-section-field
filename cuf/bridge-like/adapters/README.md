# Bridge-like Python adapters

[Back to bridge-like model](../README.md) · [Problem configuration](../problems/README.md)

## Purpose

This directory documents the **implementation layer** that connects declarative problem inputs to the corresponding CUF loading and constraint operations.

| Adapter family | Developer documentation | Configuration documentation |
| --- | --- | --- |
| Loads | [loads/README.md](loads/README.md) | [problems/README.md](../problems/README.md) |
| Constraints | [constraints/README.md](constraints/README.md) | [problems/README.md](../problems/README.md) |

## Architectural boundary

An adapter should interpret its inputs, validate them, resolve references and coordinate conventions, and return or assemble the data expected by the workflow's established interface. It must not silently change the transverse CUF approximation or the CUF fundamental nucleus.

Keep the separation explicit:

```text
YAML problem declaration
        |
        v
parser / configuration validation
        |
        v
adapter selection / dispatch
        |
        +---------------------+
        v                     v
    load adapter        constraint adapter
        |                     |
        +----------+----------+
                   v
          existing CUF solver API
```

The names of actual factories, registries, protocols and functions need to be verified from the corresponding source code before being listed here.

## What every adapter README must specify

1. **Selection:** how the problem configuration identifies this adapter.
2. **Location:** source-module path and relationship to example or case-local `.py` files.
3. **Inputs:** parameters, type/shape, coordinate system, units, and required/optional status.
4. **Output contract:** exact expected Python object, array shapes and indexing.
5. **Execution:** when the adapter is invoked in the analysis workflow.
6. **Validation:** checks, failure modes and error messages.
7. **Examples:** a real YAML declaration linked to a tested Python implementation.
8. **Tests:** verification of signs, degrees of freedom, magnitudes, and transformations.

## Source and example separation

Code in `cuf/bridge-like/adapters/` may serve as model-specific configuration or examples; reusable Python implementation may live elsewhere under `src/csf/`. Do not assume that a file under this directory is the importable runtime implementation. Each specialized README should record the actual module import path and corresponding case-file path.

## Coordinate conventions

Document mapping between problem coordinates, section coordinates, load directions and constrained CUF degrees of freedom. Refer to [coordinate systems](../../docs/coordinate_systems.md) and confirm conventions against the relevant code. Never identify an axial coordinate from a variable name alone.

## Related pages

- [Problem YAML specification](../problems/README.md)
- [Load adapter development](loads/README.md)
- [Constraint adapter development](constraints/README.md)
- [Bridge-like overview](../README.md)
