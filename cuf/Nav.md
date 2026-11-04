# Navigating CSF-CUF: a reading guide

This repository contains the CSF-CUF framework: an independent, open-source
implementation of the Carrera Unified Formulation (CUF) with a continuous
description of the cross-section (CSF). The material is organized into
several directories, each targeting a different level of use.

 this document tells you **where
to start** and **in which order to read**, depending on what you want to do.

If you are new to CUF, you do not need to learn the theory before running an
analysis. Start from the level that matches your goal, and move deeper only
if you need to.

---

## 1. What this repository contains

CSF-CUF combines three independent descriptions:

- **CSF** describes the physical section: geometry and material distribution.
- **CUF** describes the structural approximation: transverse expansion and
  longitudinal approximation.
- **The solver** combines them into a single analysis.

The separation is architectural, not sequential: model, problem, and case are
three distinct objects, not consecutive steps of a pipeline.

For the overview and the architecture diagram, see the `cuf` homepage:

https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf

---

## 2. If you want to run an analysis

**Start here.** No prior knowledge of CUF is required to execute a case.

1. **Interactive, no installation** - run the Quick Start in Google Colab:
   https://colab.research.google.com/github/giovanniboscu/continuous-section-field/blob/main/cuf/quickstart/quickstart_colab_interactive.ipynb

2. **Local execution** - follow the Quick Start README:
   https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/quickstart/README.md

3. **Understanding the YAML configuration** - the YAML reference explains how
   a physical problem is translated into model, problem, and case files:
   https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/docs/yaml_reference
   
5. **Run a CUF analysis and post-process the results** - follow the complete CLI and post-processing guide:

   https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/CSF-CUF-CLI-Post-processingGuide.md

---

## 3. If you want to understand the architecture

Read in this order:

1. End-to-end flow:
   https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/architecture/01_end_to_end.md

2. Responsibilities (CUF core vs adapters vs CSF):
   https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/architecture/02_responsibilities.md

3. Loads and boundary conditions in problem adapters:
   https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/csf_problem.md

4. Post-processing and output:
   https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/csf_post.md

The key principle: the CUF core is generic; physical semantics (loads,
constraints) live in adapters. This is what allows the solver to remain
independent of the specific problem.

---

## 4. If you want to understand the theory

The formal documents describe the mathematical formulation, including the
extension to variable sections:

- Variable-section extension (formal definition):
  https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md

- Additional formulation documents:
  https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/docs

For the original theoretical background, see the references cited in the
`cuf` homepage (Carrera, Giunta, Petrolo, Weaver).

---

## 5. If you want to extend the framework

- **New transverse expansion** - guide:
  https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/how_to_create_transverse_expansion.md

- **New longitudinal basis** - plugin contract and API:
  https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/LongitudinalBasisPlugins.md


- **New loads or boundary conditions** - adapter concept and interface:
  https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/csf_problem.md

- **Complete adapter reference** (predefined adapters, load-side and
  constraint-side modules, reverse lookup):
  https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/problem-adapters-reference.md

- **Scaled Lagrange basis** - implementation guide:
  https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/docs/scaled_lagrange_implementation_guide.md

---

## 6. If you want to reproduce a benchmark

Each benchmark has a defined scope and a documented comparison protocol.

- **I-Shape** - CSF-CUF vs FEM3D for prismatic and tapered I-beams:
  https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape

- **I-Shape_L** - local strong-equilibrium comparison (converged FEM3D
  reference, 40 sections, 66,560 Gauss samples):
  https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape_L

- **C-Shape** - benchmark based on Carrera and Petrolo:
  https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/C-Shape

- **Bridge-like** - CSF as an independent library for a bridge-type beam:
  https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/bridge-like

Each benchmark directory contains its own README with the problem
definition, the reference solution, and the comparison methodology.

---


## 7. Where to find what

| If you are looking for...                          | Go to...                                                      |
|----------------------------------------------------|---------------------------------------------------------------|
| Run a case without installing anything             | [Quick Start (Colab)](https://github.com/giovanniboscu/continuous-section-field#quick-start-colab) |
| Run a case locally                                 | [Quick Start README](https://github.com/giovanniboscu/continuous-section-field#readme) |
| Understand model / problem / case                  | [Quick Start README](https://github.com/giovanniboscu/continuous-section-field#readme), [YAML reference](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/yaml_reference.md) |
| Understand the architecture                        | [`docs/architecture/`](https://github.com/giovanniboscu/continuous-section-field/tree/main/docs/architecture) |
| Understand loads and boundary conditions           | [`docs/csf_problem.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_problem.md) |
| Find an existing adapter for a load or support     | [`docs/problem-adapters-reference.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/problem-adapters-reference.md) |
| Write a new transverse expansion                   | [`docs/how_to_create_transverse_expansion.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/how_to_create_transverse_expansion.md) |
| Understand the variable-section extension          | [`docs/model/csf_cuf_formal_variable_section_extension.md`](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md) |
| Reproduce a benchmark                              | [`cuf/I-Shape`](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape), [`cuf/I-Shape_L`](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape_L), [`cuf/C-Shape`](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/C-Shape), [`cuf/bridge-like`](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/bridge-like) |
| See a complete tutorial                            | [`cuf/tutorials/variable_material_t_section`](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/tutorials/variable_material_t_section) |
---

## A note on scope

CSF-CUF is an independent, educational implementation.  The benchmarks included in this
repository are validation exercises on specific cases; they do not imply a
general superiority of CSF-CUF over other formulations.

The repository is designed to be read at multiple levels: execution,
architecture, theory, and extension. This guide is the entry point. The
documents it links to are the content.
