# CSF Documentation

This index separates practical guides, API references, implemented formulations, and CSF-specific modelling assumptions so that users can distinguish standard engineering methods from choices introduced by the software.

## Where to start

- New to CSF: start with the [architecture overview](model/architecture.md).
- Using YAML and Actions: follow the [YAML tutorial](csftutorial.md).
- Building and analysing models in Python: use the [Programmer Guide](programmer-guide/README.md).
- Reviewing calculation methods: see [Section Analysis and Implemented Formulations](#section-analysis-and-implemented-formulations).
- Reviewing CSF-specific choices: see [Modelling Assumptions and CSF-Specific Indicators](#modelling-assumptions-and-csf-specific-indicators).
- Integrating with structural solvers: see [Solver Integration](#solver-integration).
- Reviewing reproducible checks: see [Validation Cases](#validation-cases).

---

## Core Concepts and Model Definition

| Resource | Description |
|----------|-------------|
| [CSF positioning and workflow overview](model/architecture.md) | Conceptual overview of CSF as a continuous section-field layer: model responsibilities, workflow position, section sampling, and relation with analysis backends. |
| [Building Blocks Fundamentals](CSF_Fundamentals.md) | Guide to CSF geometry, sections, polygon tags, and weight laws. |
| [Varying homogenization user guide](CSFLongitudinally-varying-homogenization-user-guide.md) | Technical guide for defining custom weight laws `w(z)`: conventions, syntax, available variables, lookup functions (`E_lookup`, `T_lookup`), validation rules, and OpenSees export mapping. |

---

## Actions Runner - No-Code Workflow

| Resource | Description |
|----------|-------------|
| [YAML tutorial](csftutorial.md) | Step-by-step YAML tutorial using `CSFActions.py`; no Python coding required. Covers installation, file structure, station sets, output rules, weight laws, and available actions. |
| [Complete worked Actions example](../actions-examples/rectangle) | Tapered rectangular-section example covering plots, reports, solver exports, and three weight-law alternatives. Run with `python3 -m csf.CSFActions geometry.yaml actions.yaml`. |
| [Complete Actions template](actions_template.yaml) | Reference YAML containing all available Actions options. |

---

## Python Guides and API Reference

| Resource | Description |
|----------|-------------|
| [Programmer Guide](programmer-guide/README.md) | Example-driven guide for building, plotting, exporting, and analysing CSF models through the Python API. |
| [Modeling and Sectional Analysis](user_guide.md) | Python API guide for constructing `Polygon`, `Section`, and `ContinuousSectionField`, retrieving intermediate sections, and computing section properties along `z`. |
| [CSF API Reference](API/) | Detailed reference for geometry primitives, `ContinuousSectionField`, section-analysis functions, polygon utilities, torsion routines, volume integration, stiffness assembly, exports, and weight-law utilities. |

---

## Geometry and Model Construction

| Resource | Description |
|----------|-------------|
| [CSF Polygon Geometry Guide](CSF_Polygon_Geometry_Guide.md) | Construction of tagged polygons: `@cell` for closed thin-walled cells and `@wall` for open thin-walled strips, with YAML examples and modelling checklists. |
| [writegeometry_rio_v2 User Guide](writegeometry_rio_v2_guide.md) | CLI reference for the parametric geometry generator: shape families, rebar rows, degradation weight laws, twist, and worked examples. |

---

## Section Analysis and Implemented Formulations

These documents describe the section-level quantities and engineering formulations implemented by CSF.

| Resource | Description |
|----------|-------------|
| [Section Full Analysis](sections/sectionfullanalysis.md) | Reference for all quantities reported by the CSF Section Full Analysis, including their calculation basis, interpretation, and validity domain. |
| [Jourawski formulation implemented in CSF](model/csf_jourawski_calculation_model.md) | Calculation model used for Jourawski shear stresses: the shear flow is evaluated on the `E`-homogenized section and redistributed across the material segments intersected by each cut according to their shear modulus `G`. |
| [Saint-Venant Torsional Constant](sections/DeSaintVenantTorsionalConstant%20.md) | Validity conditions for `J_sv = J_sv_cell + J_sv_wall`, including the non-interaction hypotheses, Bredt and thin-wall contributions, validity limits, and solver-export behaviour. |

---

## Modelling Assumptions and CSF-Specific Indicators

These documents describe modelling choices, admissibility rules, and diagnostic quantities introduced by CSF. They are not presented as general closed-form solutions and must be interpreted within their stated scope.

| Resource | Description |
|----------|-------------|
| [Roark-based torsional indicator - CSF modelling assumptions](model/J_vroark_usage_guide.md) | Defines the CSF-specific `J_s_vroark` equivalent-rectangle torsional indicator and its `J_s_vroark_fidelity` admissibility measure. Documents the geometric mapping, global shear-weight correction, fidelity penalties, rejection rules, intended use, and limitations. |

---

## Weight Laws and Homogenization

| Resource | Description |
|----------|-------------|
| [Weight-law examples](weight_law_example) | Library of ready-to-use `w(z)` and `w(z,t)` functions in NumPy syntax: linear, polynomial, step, periodic, Gaussian, decay, lookup-based, and hybrid laws. |
| [Varying homogenization user guide](CSFLongitudinally-varying-homogenization-user-guide.md) | Conventions and implementation details for longitudinally varying material and stiffness carriers. |

---

## Solver Integration

| Resource | Description |
|----------|-------------|
| [OpenSeesPy on Windows 11](opensees_win11_setup.md) | OpenSeesPy setup on Windows 11 using a Python 3.12 virtual environment. |
| [OpenSees integration numerical strategy](OpenSeesIntegrationNumericalStrategy.md) | Strategy for consuming CSF station data in OpenSees: export format, material conventions, centroid-axis topology, integration strategies, and torsion policy. |
| [SAP2000 and generic solver export](write_sap2000_template_pack.md) | Export of CSF geometry and section data to a structured text package usable by SAP2000, OpenSeesPy, and other beam-analysis workflows. |
| [OpenSees Tcl builder](write_opensees_builder_tcl.md) | Generation of a standalone OpenSees Tcl model from `geometry.tcl`, including material modes, Gauss–Lobatto segment behaviour, and limitations. |

---

## Integration with sectionproperties

### CSF to sectionproperties

| Resource | Description |
|----------|-------------|
| [csf_sp User Guide](csf_sp_user_guide.md) | Complete reference for converting and analysing CSF sections with `sectionproperties`, including YAML, nesting, taper, material variation, CLI usage, and Python API. |
| [csf_sp Step-by-Step Guide](csf_sp_stepbystep_guide.md) | Progressive examples from native `sectionproperties` usage to CSF-driven prismatic, tapered, and material-varying sections. |

### sectionproperties to CSF

| Resource | Description |
|----------|-------------|
| [sp_csf Guide](sectionproperties/sp_csf_guide.md) | Conversion of `sectionproperties` parametric sections to CSF YAML. |
| [CLI Tapered Examples](sectionproperties/cli_tapered_examples.md) | Same-family tapered examples in which `S0` and `S1` use the same section type with different dimensions. |
| [Morphing CLI-Compatible Catalog](sectionproperties/morphing_cli_compatible_catalog.md) | Catalog of morphing examples compatible with the scalar `sp_csf` CLI syntax. |
| [Morphing Policy](sectionproperties/morphingpolicy.md) | Rules, scope, and intended behaviour of morphing between different section families. |

---

## Validation Cases

| Resource | Description |
|----------|-------------|
| [NREL 5-MW Tower Validation Case](aes/nrel_case/) | Reproducible CSF-to-OpenSees validation workflow with independent analytical reference integration, convergence studies, and comparison of continuous and piecewise sectional representations. |

---

## Additional Documents

The following files are present in the documentation tree but are not yet integrated into the main navigation:

| File | Description |
|------|-------------|
| `core_assumption` | Not yet indexed. |
| `report.md` | Not yet indexed. |
| `references` | Not yet indexed. |
| `csf_2dxf_instrucions.md` | Not yet indexed. |

### Subfolders

| Folder | Description |
|--------|-------------|
| `cases/` | Case studies and worked examples. |
| `math/` | Mathematical derivations and formulations. |
| `model/` | Model-level documentation, implemented formulations, and modelling assumptions. |
| `programmer-guide/` | Developer and integration guide. |
| `sap2000/` | SAP2000 integration documentation. |

