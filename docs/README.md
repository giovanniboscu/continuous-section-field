
# CSF Documentation

## Where to start

- New to CSF: start with the [architecture overview](model/architecture.md).
- Using YAML and Actions: follow the [YAML tutorial](csftutorial.md).
- Building sections in Python: see the [modeling and sectional analysis guide](user_guide.md).
- Looking for calculation models: see the [Section Properties Reference](#section-properties-reference).
- Integrating with solvers: see [Solver Integration](#solver-integration).
- Reviewing validated examples: see [Validation Cases](#validation-cases).
 
## Overview


| Resource | Description |
|----------|-------------|
| [Building Blocks Fundamentals](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSF_Fundamentals.md) | CSF Geometry, Sections, Polygon Tags, and Weight Laws Guide |
| [Varying homogenization user guide](CSFLongitudinally-varying-homogenization-user-guide.md) | Technical guide for defining custom weight laws `w(z)`: conventions, syntax, available variables, lookup functions (`E_lookup`, `T_lookup`), validation rules, and OpenSees export mapping. |
| [Tutorial (YAML workflow)](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csftutorial.md) | Step-by-step YAML workflow . no Python programming required. |
| [writegeometry_rio_v2 - User Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/writegeometry_rio_v2_guide.md) | CLI reference for the parametric geometry generator: shape families (circle, rounded rectangle, sharp rectangle), rebar rows, degradation weight laws, twist, and worked examples. |


---

## Actions Runner (No-Code Workflow)

| File | Description |
|------|-------------|
| [YAML tutorial ](csftutorial.md) | Step-by-step YAML tutorial using `CSFActions.py` - no Python coding required. Covers installation, file structure, station sets, output rules, weight laws, and all available actions with examples. |
| [full actions list](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/rectangle) | Complete worked example covering all available actions on a tapered rectangular section — plots, reports, solver exports, and three weight law alternatives. Run with `python3 -m csf.CSFActions geometry.yaml actions.yaml`. |
| [Complete reference with all available actions](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/actions_template.yaml) |CSF Actions Template - complete reference with all available actions|

---
## API Reference & Programmig

| File | Description |
|------|-------------|
| [programmer-guide](programmer-guide) |This is a practical programmer guide for CSF.. |
| [Modeling and Sectional Analysis](user_guide.md)  | Python API user guide: constructing `Polygon`, `Section`, and `ContinuousSectionField`, retrieving intermediate sections, and computing section properties along Z. |
| [CSF API](https://github.com/giovanniboscu/continuous-section-field/tree/main/docs/API) | Complete Python API reference: geometry primitives (`Pt`, `Polygon`, `Section`), `ContinuousSectionField` and all its methods, section analysis functions, polygon utilities, torsion routines, volume integration, element stiffness assembly, export functions, and weight law utilities. |

## Geometry

| File | Description |
|------|-------------|
| [CSF_Polygon_Geometry_Guide](CSF_Polygon_Geometry_Guide.md) | Geometric construction of tagged polygons: `@cell` (closed thin-walled cell, two-loop encoding) and `@wall` (open thin-walled strip, single loop). Includes YAML examples and checklists. |

## Section Properties Reference & Modelling Assumptions

| File | Description |
|------|-------------|
| [Section Full Analysis](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md) | Reference for all quantities reported by the CSF Section Full Analysis. Explains what each value represents, how it is computed, and its validity domain. Quantities that depend on specific CSF modelling policies (e.g. torsion selection rules) are explicitly marked. |
| [SaintVenant Torsional Constant](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md) | Validity conditions for the summation `J_sv = J_sv_cell + J_sv_wall` in CSF. Covers the non-interaction hypotheses (H1–H4), elemental formulas (Bredt for closed cells, thin-wall rectangle for open walls), when the summation holds and when it does not, and how the result is exported to OpenSees and SAP2000. |
| [Jourawski formulation implemented in CSF](model/csf_jourawski_calculation_model.md) | Calculation model used by CSF for Jourawski shear stresses: the shear flow is evaluated on the E-homogenized section and then redistributed across the material segments intersected by each cut according to their shear modulus G. |


---

## Weight Laws and Homogenization

| File | Description |
|------|-------------|
| [weight_law_example](weight_law_example) | Library of ready-to-use `w(z)` and `w(z,t)` functions in NumPy syntax: linear, polynomial, step, periodic, Gaussian, decay, lookup-based, and hybrid laws. |

---

## Solver Integration

| File | Description |
|------|-------------|
| [Opensees on win11](opensees_win11_setup.md) |OpenSeesPy on Win11 with a Python 3.12 virtual environment |
| [OpenSeesIntegrationNumericalStrategy.md](OpenSeesIntegrationNumericalStrategy.md) | Detailed numerical strategy for consuming CSF station data in OpenSees: export file format (`geometry.tcl`), material conventions, centroid axis topology, integration strategies (member-level Lobatto vs segmented endpoint), and torsion export policy. |
| [Solver sap200 and generic](write_sap2000_template_pack.md) | write_sap2000_template_pack exports a CSF (Continuous Section Field) model to a structured plain-text file that, although organized as a SAP2000 template pack, also contains information usable by other beam solvers such as OpenSeesPy, as well as for section verification and quality review. |
| [write_opensees_builder_tcl](write_opensees_builder_tcl.md) | Documentation for `write_opensees_builder_tcl.py`: generates a standalone OpenSees Tcl script that reads `geometry.tcl` as a data file and builds a 3D beam model without requiring OpenSeesPy. Covers material modes, Gauss–Lobatto segment behavior, and limitations. |


---

##  Integration - sectionproperties to CSF and viceversa

| File | Description |
|------|-------------|
| [csf_sp User Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_user_guide.md) | Complete reference for `csf_sp`: YAML file format, polygon nesting, tapered sections, multi-material sections, weight variation, custom weight laws, CLI usage, output properties, and Python API (`load_yaml`, `analyse`). Includes worked examples and the full SP composite getter reference. |
| [csf_sp Step-by-Step Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_stepbystep_guide.md) | Progressive examples moving from native sectionproperties to CSF: baseline SP usage, prismatic and tapered sections via Python API and YAML, linear and custom weight laws, CSF vs SP property comparison, and a full CSF Actions pipeline with solver export. |

| File | Description |
|------|-------------|
| [sp_csf Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sectionproperties/sp_csf_guide.md) | Convert `sectionproperties` parametric sections to CSF YAML. Main reference for generating CSF-compatible geometry files from the `sectionproperties` catalog. |
| [CLI Tapered Examples](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sectionproperties/cli_tapered_examples.md) | CLI examples for tapered same-family sections, where `S0` and `S1` use the same section type with different dimensions along `z`. |
| [Morphing CLI-Compatible Catalog](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sectionproperties/morphing_cli_compatible_catalog.md) | Catalog of morphing examples compatible with the current scalar `sp_csf` CLI syntax. |
| [Morphing Policy](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sectionproperties/morphingpolicy.md) | Policy defining the rules, scope, and intended behavior of the morphing workflow between different section families. |

---


## Validation Cases

| Resource | Description |
|----------|-------------|
| [NREL 5-MW Tower Validation Case](https://github.com/giovanniboscu/continuous-section-field/tree/main/docs/aes/nrel_case) | Reproducible CSF-to-OpenSees validation workflow for the NREL 5-MW reference tower. Includes undegraded and longitudinally degraded stiffness-field cases, independent analytical reference integration, convergence studies, and comparison of continuous versus piecewise sectional representations. |

---

## Additional Documents

The following files are present in this folder but not covered in this index:

| File | Description |
|------|-------------|
| `core_assumption` | - |
| `report.md` | - |
| `references` | - |
| `csf_2dxf_instrucions.md` | - |

### Subfolders

| Folder | Description |
|--------|-------------|
| `cases/` | Case studies and worked examples |
| `math/` | Mathematical derivations and formulations |
| `model/` | Model-level documentation |
| `programmer-guide/` | Developer and integration reference |
| `sap2000/` | SAP2000 integration documentation |
