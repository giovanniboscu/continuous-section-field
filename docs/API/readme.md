# CSF API Documentation

This directory contains the API reference documentation for the main CSF modules.

The API files are intended as a technical navigation layer for developers and users who need to understand which classes, functions, methods, parameters, and return structures are exposed by the current implementation.

## Documentation files

| Module | API document | Role |
|---|---|---|
| `continuous_section_field.py` | [continuous_section_field_api_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/continuous_section_field_api_en.md) | Core single-interval continuous section field. |
| `section_field.py` | [section_field_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/section_field_en.md) | Section-property computation, formula evaluation, export helpers, and numerical utilities. |
| `visualizer.py` | [visualizer_api_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/visualizer_api_en.md) | 2D and 3D visualization utilities for a single `ContinuousSectionField`. |
| `CSFStacked.py` | [CSFStacked_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/CSFStacked_en.md) | Stacked multi-interval CSF container and stack-level plotting/evaluation wrappers. |

## Recommended reading order

For a first pass through the API structure, read the files in this order:

1. [`continuous_section_field_api_en.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/continuous_section_field_api_en.md)  
   Start here to understand the core object, `ContinuousSectionField`, and its main operations:
   - construction from two endpoint `Section` objects;
   - evaluation of `section(z)`;
   - weight and shear-weight law handling;
   - YAML serialization;
   - area breakdown utilities.

2. [`section_field_en.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/section_field_en.md)  
   Use this file as the reference for section-property evaluation and supporting utilities:
   - `section_full_analysis`;
   - `section_properties`;
   - torsion-related helpers;
   - OpenSees/SAP2000 export helpers;
   - CSV and report utilities.

3. [`visualizer_api_en.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/visualizer_api_en.md)  
   Use this file when working with plots for a single CSF interval:
   - 2D section plots;
   - 3D ruled-volume plots;
   - weight and shear-weight distribution plots;
   - property evolution plots.

4. [`CSFStacked_en.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/CSFStacked_en.md)  
   Read this file when the member is represented by more than one CSF interval:
   - stack construction;
   - global `z` dispatch;
   - internal junction handling;
   - stack-level property plots;
   - global 3D visualization.

## Conceptual structure

The API is organized around four layers.

```text
Polygon / Section
        |
        v
ContinuousSectionField
        |
        +--> section(z)
        +--> weight / shear-weight laws
        +--> YAML export
        +--> area reports
        |
        v
section_field utilities
        |
        +--> section_full_analysis(section)
        +--> section_properties(section)
        +--> torsion and export helpers
        |
        v
Visualizer / CSFStacked
        |
        +--> single-interval plots
        +--> multi-interval dispatch
        +--> stack-level visualization
```

## Main API roles

### `ContinuousSectionField`

`ContinuousSectionField` is the core single-interval object. It stores two endpoint sections and evaluates an interpolated `Section` at a requested longitudinal coordinate `z`.

Primary API entry points:

```python
field = ContinuousSectionField(section0=s0, section1=s1)

section_at_z = field.section(z)
analysis = section_full_analysis(section_at_z)
```

Relevant documentation:

- [continuous_section_field_api_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/continuous_section_field_api_en.md)
- [section_field_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/section_field_en.md)

### `section_field.py`

`section_field.py` contains the section-property and utility layer. It provides functions used after a `Section` has been evaluated.

Typical usage:

```python
sec = field.section(z)
props = section_full_analysis(sec)
```

Relevant documentation:

- [section_field_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/section_field_en.md)

### `Visualizer`

`Visualizer` provides plotting tools for one `ContinuousSectionField`.

Typical usage:

```python
vis = Visualizer(field)

vis.plot_section_2d(z=5.0)
vis.plot_volume_3d()
vis.plot_properties(keys_to_plot=["A", "Ix", "Iy"])
```

Relevant documentation:

- [visualizer_api_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/visualizer_api_en.md)

### `CSFStacked`

`CSFStacked` provides a multi-interval wrapper around several `ContinuousSectionField` objects. It dispatches global `z` queries to the correct segment.

Typical usage:

```python
stack = CSFStacked()
stack.append(field_0)
stack.append(field_1)

sec = stack.section(z=7.5)
props = stack.section_full_analysis(z=7.5)
```

Relevant documentation:

- [CSFStacked_en.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/CSFStacked_en.md)

## How to use this documentation

Use these API files as a reference when you need to check:

- which functions or methods are available;
- the exact function signatures;
- parameter names and defaults;
- documented return structures;
- internal helpers that are exposed in the module;
- current notes where the implementation differs from the apparent signature or docstring.

The API documentation is not a replacement for the source code. It is a structured map of the current API surface.

When behavior matters for a specific workflow, the source file remains the source of truth.

## Scope

These documents describe the Python API structure of the current implementation.

They do not replace:

- the mathematical formulation of CSF;
- validation examples;
- solver-specific workflows;
- the main project README;
- paper-oriented explanation.

For those topics, use the corresponding project documentation outside this API directory.

## Direct links

- [`CSFStacked_en.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/CSFStacked_en.md)
- [`continuous_section_field_api_en.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/continuous_section_field_api_en.md)
- [`visualizer_api_en.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/visualizer_api_en.md)
- [`section_field_en.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/API/section_field_en.md)
