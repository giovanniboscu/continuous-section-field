# Bridge-like problem definitions

[Back to bridge-like model](../README.md) · [Adapter architecture](../adapters/README.md)

## Purpose

This directory owns the **declarative description** of bridge-like CUF problems. The two problem YAML files, [`bending.yaml`](bending.yaml) and [`torsion.yaml`](torsion.yaml), specify the loading problems and their support setup for the common bridge-like geometry. This README explains how to document and validate them; the Python behavior associated with their adapter declarations is specified in the adapter documentation.

> **Repository verification required:** The exact YAML keys, required properties, and adapter selection syntax could not be read automatically while preparing this documentation. The entries below deliberately avoid asserting an unverified schema. Populate the schema tables from the actual YAML files and their Python readers, not by conjecture.

## The two YAML files

For **each** of the two YAML files in this directory, record:

| Item | What to document |
| --- | --- |
| Filename | Exact file basename and relative path |
| Role | Model/geometry description, analysis configuration, or another role established by the code |
| Consumer | Actual Python entry point/parser that reads this file |
| Top-level keys | Exact spelling, type, required/optional status and defaults |
| Nested keys | Meaning, type, accepted values, units and references |
| Validation | Mandatory checks and error handling |
| Examples | Smallest valid example extracted from a working case |
| Links to adapters | Which fields select/configure load and constraint adapters |

**[`bending.yaml`](bending.yaml):** specifies the bending loading problem, with a distributed surface load along an edge of the top flange and fixed conditions at both beam ends. Document its actual keys and values against the YAML and parser.

**[`torsion.yaml`](torsion.yaml):** specifies the torsion loading problem, with opposing longitudinal line loads at the outer top corners and fixed conditions at both ends. Document its actual keys and values against the YAML and parser.

Do not equate these files to the repository-wide `geometry.yaml` / `actions.yaml` pair unless their actual contents and readers establish that equivalence.

## Configuration versus implementation

YAML is responsible for stating **what the problem requests**. The load/constraint adapters implement **how those requests are translated** into the CUF data structures. Do not copy Python implementation instructions into this page.

### Loads

For load-related YAML entries, document the fields selecting the adapter, the physical load being described, the applicable position/boundary, magnitude and spatial variation, coordinate frame, units, and defaults **as they actually exist in the schema**.

Implementation and extension instructions: [Load adapters](../adapters/loads/README.md).

### Constraints

For constraint-related YAML entries, document the adapter selector, constrained quantities, support location/domain, reference frame, and parameter interpretation **as established by the actual schema**.

Implementation and extension instructions: [Constraint adapters](../adapters/constraints/README.md).

## Data flow

```text
problem YAML files
    | parse + validate (actual reader/entry point)
    v
problem configuration
    | adapter selection + parameters
    +--------------------+--------------------+
    v                    v
load adapter         constraint adapter
    |                    |
    +-----------+--------+
                v
        CUF analysis workflow
```

This is a responsibility diagram, not a claim about specific Python classes or function signatures.

## Checks when adding or modifying a problem

1. Identify the exact YAML file and its reader.
2. Check required keys, types, numerical units, frame conventions and defaults.
3. Check the referenced adapter is available and accepts the declared parameters.
4. Check that applied loads and support conditions are consistent with the chosen CUF degrees of freedom and sectional geometry.
5. Verify the configured case against a known benchmark or a simplified limiting case.
6. Document any backward-incompatible schema change here and update the linked adapter README.

## Related implementation documentation

- [General adapter architecture](../adapters/README.md)
- [Load adapter programming](../adapters/loads/README.md)
- [Constraint adapter programming](../adapters/constraints/README.md)
- [Bridge-like model overview](../README.md)

**Documentation rule:** This page is the source of truth for configuration. The adapter README files are the source of truth for Python implementation.
