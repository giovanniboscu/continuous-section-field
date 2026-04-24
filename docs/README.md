
# CSF Documentation
Start here: these three guides cover everything you need to work with CSF effectively.


| Resource | Description |
|----------|-------------|
| [CSF Building Blocks Fundamentals](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSF_Fundamentals.md) | CSF Geometry, Sections, Polygon Tags, and Weight Laws Guide |
| [CSF Programmer Guide](https://github.com/giovanniboscu/continuous-section-field/tree/main/docs/programmer-guide) | Python API reference — developer-oriented. |
| [CSF Tutorial (YAML workflow)](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csftutorial.md) | Step-by-step YAML workflow — no Python programming required. |
| [CSFLongitudinally-varying-homogenization-user-guide.md](CSFLongitudinally-varying-homogenization-user-guide.md) | Technical guide for defining custom weight laws `w(z)`: conventions, syntax, available variables, lookup functions (`E_lookup`, `T_lookup`), validation rules, and OpenSees export mapping. |
| [writegeometry_rio_v2 — User Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/writegeometry_rio_v2_guide.md) | CLI reference for the parametric geometry generator: shape families (circle, rounded rectangle, sharp rectangle), rebar rows, degradation weight laws, twist, and worked examples. |
| [CSF complete reference with all available action](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/actions_template.yaml) |CSF Actions Template - complete reference with all available actions|









---

| File | Description |
|------|-------------|
| [Section Full Analysis](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md) | Reference for all quantities reported by the CSF Section Full Analysis. Explains what each value represents, how it is computed, and its validity domain. Quantities that depend on specific CSF modelling policies (e.g. torsion selection rules) are explicitly marked. |
| [SaintVenantTorsionalConstant.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md) | Validity conditions for the summation `J_sv = J_sv_cell + J_sv_wall` in CSF. Covers the non-interaction hypotheses (H1–H4), elemental formulas (Bredt for closed cells, thin-wall rectangle for open walls), when the summation holds and when it does not, and how the result is exported to OpenSees and SAP2000. |




| File | Description |
|------|-------------|
| [csftutorial.md](csftutorial.md) | Step-by-step YAML tutorial using `CSFActions.py` - no Python coding required. Covers installation, file structure, station sets, output rules, weight laws, and all available actions with examples. |
| [QuickStartGuide.md](QuickStartGuide.md) | End-to-end practical workflow: geometry file, actions file, degradation law `w(z)`, running CSF, and interpreting outputs. Start here. |



## Actions Runner (No-Code Workflow)

| File | Description |
|------|-------------|
| [full actions list/](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/rectangle) | Complete worked example covering all available actions on a tapered rectangular section — plots, reports, solver exports, and three weight law alternatives. Run with `python3 -m csf.CSFActions geometry.yaml actions.yaml`. |
| [csftutorial.md](csftutorial.md) | Step-by-step YAML tutorial using `CSFActions.py` - no Python coding required. Covers installation, file structure, station sets, output rules, weight laws, and all available actions with examples. |
| [QuickStartGuide.md](QuickStartGuide.md) | End-to-end practical workflow: geometry file, actions file, degradation law `w(z)`, running CSF, and interpreting outputs. Start here. |
| [CSF complete reference with all available action](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/actions_template.yaml) |CSF Actions Template - complete reference with all available actions|

---
## API Reference & Programmig

| File | Description |
|------|-------------|
| [api.md](api.md) | Complete Python API reference: geometry primitives (`Pt`, `Polygon`, `Section`), `ContinuousSectionField` and all its methods, section analysis functions, polygon utilities, torsion routines, volume integration, element stiffness assembly, export functions, and weight law utilities. |
| [programmer-guide](programmer-guide) |This is a practical programmer guide for CSF.. |
| [user_guide.md](user_guide.md) | Python API user guide: constructing `Polygon`, `Section`, and `ContinuousSectionField`, retrieving intermediate sections, and computing section properties along Z. |


## Geometry

| File | Description |
|------|-------------|
| [CSF_Polygon_Geometry_Guide.md](CSF_Polygon_Geometry_Guide.md) | Geometric construction of tagged polygons: `@cell` (closed thin-walled cell, two-loop encoding) and `@wall` (open thin-walled strip, single loop). Includes YAML examples and checklists. |
| [GeneratingSectionGeometryWithAnLLM.md](GeneratingSectionGeometryWithAnLLM.md) | Workflows for generating CSF-ready YAML geometry using an LLM: from images, analytical descriptions, and parametric scripts. Includes prompt examples and vertex resolution guidelines. |

---

## Weight Laws and Homogenization

| File | Description |
|------|-------------|
| [CSFLongitudinally-varying-homogenization-user-guide.md](CSFLongitudinally-varying-homogenization-user-guide.md) | Technical guide for defining custom weight laws `w(z)`: conventions, syntax, available variables, lookup functions (`E_lookup`, `T_lookup`), validation rules, and OpenSees export mapping. |
| [weight_law_example.md](weight_law_example.md) | Library of ready-to-use `w(z)` and `w(z,t)` functions in NumPy syntax: linear, polynomial, step, periodic, Gaussian, decay, lookup-based, and hybrid laws. |

---

## Solver Integration

| File | Description |
|------|-------------|
| [Opensees on win11](opensees_win11_setup.md) |OpenSeesPy on Win11 with a Python 3.12 virtual environment |
| [OpenSeesIntegrationNumericalStrategy.md](OpenSeesIntegrationNumericalStrategy.md) | Detailed numerical strategy for consuming CSF station data in OpenSees: export file format (`geometry.tcl`), material conventions, centroid axis topology, integration strategies (member-level Lobatto vs segmented endpoint), and torsion export policy. |
| [Solver sap200 and generic](write_sap2000_template_pack.md) | write_sap2000_template_pack exports a CSF (Continuous Section Field) model to a structured plain-text file that, although organized as a SAP2000 template pack, also contains information usable by other beam solvers such as OpenSeesPy, as well as for section verification and quality review. |
| [write_opensees_builder_tcl.md](write_opensees_builder_tcl.md) | Documentation for `write_opensees_builder_tcl.py`: generates a standalone OpenSees Tcl script that reads `geometry.tcl` as a data file and builds a 3D beam model without requiring OpenSeesPy. Covers material modes, Gauss–Lobatto segment behavior, and limitations. |


---

## sectionproperties Integration (csf_sp)

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

## Additional Documents

The following files are present in this folder but not covered in this index:

| File | Description |
|------|-------------|
| `core_assumption.md` | - |
| `report.md` | - |
| `references.md` | - |
| `csf_2dxf_instrucions.md` | - |

### Subfolders

| Folder | Description |
|--------|-------------|
| `cases/` | Case studies and worked examples |
| `math/` | Mathematical derivations and formulations |
| `model/` | Model-level documentation |
| `programmer-guide/` | Developer and integration reference |
| `sap2000/` | SAP2000 integration documentation |
