# DRAFT

# CSF-CUF Framework

This repository provides a framework for building and running models based on the Carrera Unified Formulation (CUF).

It is not intended as a theoretical introduction to CUF. Its purpose is to provide a parametric and reusable implementation that can be used directly from external model definitions.

The model is described through YAML files containing the geometry, material distribution, loads, boundary conditions, and the transverse expansion rule. From these inputs, the framework builds and runs the corresponding CUF model.

The solver core is independent of the specific cross-section geometry. Geometric and constitutive information is supplied by an external CSF-based section provider, which is queried by the CUF implementation during model construction and evaluation. This keeps the description of the physical problem separate from the numerical formulation and allows the same solver core to operate on different section configurations without embedding section-specific assumptions in the solver.

The repository includes two complete workflows.

The first is a **prismatic model**, derived from the 2010 Carrera and Giunta reference case. It is organized to reproduce the final benchmark tables for the more complex cross-section, providing a direct and repeatable reference case.

The second is a **tapered model**, in which both geometry and material properties vary along the beam axis. It uses the same CUF core and the same CSF-based interface, showing how the framework can move from a classical prismatic benchmark to a genuinely variable-section problem without changing the solver architecture.

From a user's point of view, the expected workflow is therefore simple: define the physical model and the analysis parameters in YAML, run the corresponding model, and inspect the resulting displacement and stress outputs. The CUF machinery remains inside the framework, while the model definition stays external, explicit, and replaceable.

This guide focuses on how the implementation is organized, how data move through the framework, and what can be done with the available examples. The theoretical formulation, coupling strategy, constitutive interface, and numerical validation are documented separately.

---

# CSF-CUF Validation Commands

Run all commands from:

```bash
/home/giarrettu/github/continuous-section-field/cuf
```

## Prismatic double-T -Table 9 bending

```bash
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table9_N05.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table9_N10.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table9_N18.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table9_N21_OR06.yaml
```

## Prismatic double-T -Table 10 torsion

```bash
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N05.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N10.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N10_E01.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N10_E01_OR06.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N10_E02.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N11_E01_OR06.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N11_E02.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N19_E01_OR06.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/prismatic/table10_N21_E01_OR06.yaml
```

## Tapered double-T with variable material -Table 9 bending

```bash
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table9_N05.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table9_N10.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table9_N18.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table9_N21.yaml
```

## Tapered double-T with variable material -Table 10 torsion

```bash
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table10_N05.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table10_N10.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table10_N21.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table10_N21_E01.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table10_N21_E02.yaml
time python3 -m csf.cuf validation/carrera_giunta_2010/double_t/cases/cuf/taper80_degraded/table10_N30_E01.yaml
```

```

---
## Theoretical formulation and validation

The theoretical basis of the implementation can be found in the following documents:

- [Formal variable-section extension](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md)
- [Displacement expansion and CSF–CUF coupling](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_displacement_expansionf_coupling.md)
- [Sectional constitutive interface](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_sectional_constitutive_interface.md)
- [Numerical validation against Carrera and Giunta](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_numerical_validation_carrera_giunta.md)
