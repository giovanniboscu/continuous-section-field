# CSF Documentation

This folder contains the documentation for **Continuous Section Field (CSF)** - a Python engine for continuous geometric and structural modeling of non-prismatic members.

---
## Actions Runner (No-Code Workflow)

| File | Description |
|------|-------------|
| [QuickStartGuide.md](QuickStartGuide.md) | End-to-end practical workflow: geometry file, actions file, degradation law `w(z)`, running CSF, and interpreting outputs. Start here. |
| [csftutorial.md](csftutorial.md) | Step-by-step YAML tutorial using `CSFActions.py` - no Python coding required. Covers installation, file structure, station sets, output rules, weight laws, and all available actions with examples. |
| [user_guide.md](user_guide.md) | Python API user guide: constructing `Polygon`, `Section`, and `ContinuousSectionField`, retrieving intermediate sections, and computing section properties along Z. |

---

## Geometry

| File | Description |
|------|-------------|
| [CSF_Polygon_Geometry_Guide.md](CSF_Polygon_Geometry_Guide.md) | Geometric construction of tagged polygons: `@cell` (closed thin-walled cell, two-loop encoding) and `@wall` (open thin-walled strip, single loop). Includes YAML examples and checklists. |
| [GeneratingSectionGeometryWithAnLLM.md](GeneratingSectionGeometryWithAnLLM.md) | Workflows for generating CSF-ready YAML geometry using an LLM: from images, analytical descriptions, and parametric scripts. Includes prompt examples and vertex resolution guidelines. |
| [cross_section_homogenization.md](cross_section_homogenization.md) | Conceptual overview of the CSF framework: continuous description of non-prismatic and multi-material members via longitudinally varying homogenization fields. |

---

## Weight Laws and Homogenization

| File | Description |
|------|-------------|
| [CSFLongitudinally-varying-homogenization-user-guide.md](CSFLongitudinally-varying-homogenization-user-guide.md) | Technical guide for defining custom weight laws `w(z)`: conventions, syntax, available variables, lookup functions (`E_lookup`, `T_lookup`), validation rules, and OpenSees export mapping. |
| [weight_law_example.md](weight_law_example.md) | Library of ready-to-use `w(z)` and `w(z,t)` functions in NumPy syntax: linear, polynomial, step, periodic, Gaussian, decay, lookup-based, and hybrid laws. |

---

## OpenSees Integration

| File | Description |
|------|-------------|
| [openseesIntegration.md](openseesIntegration.md) | Overview of CSF → OpenSees integration: `forceBeamColumn` formulation, Gauss–Lobatto stationing, `beamIntegration UserDefined`, torsional constant selection, and variable centroid axis handling with `rigidLink`. |
| [OpenSeesIntegrationNumericalStrategy.md](OpenSeesIntegrationNumericalStrategy.md) | Detailed numerical strategy for consuming CSF station data in OpenSees: export file format (`geometry.tcl`), material conventions, centroid axis topology, integration strategies (member-level Lobatto vs segmented endpoint), and torsion export policy. |
| [csf_openseespy_builder.md](csf_openseespy_builder.md) | Documentation for `csf_openseespy_builder.py`: OpenSeesPy checker/builder that reads `geometry.tcl`, builds a reference + centroid axis model, and runs a cantilever verification. Covers integration modes (`auto`, `member_lobatto`, `segment_endpoints`) and limitations. |
| [write_opensees_builder_tcl.md](write_opensees_builder_tcl.md) | Documentation for `write_opensees_builder_tcl.py`: generates a standalone OpenSees Tcl script that reads `geometry.tcl` as a data file and builds a 3D beam model without requiring OpenSeesPy. Covers material modes, Gauss–Lobatto segment behavior, and limitations. |

---

## API Reference

| File | Description |
|------|-------------|
| [api.md](api.md) | Complete Python API reference: geometry primitives (`Pt`, `Polygon`, `Section`), `ContinuousSectionField` and all its methods, section analysis functions, polygon utilities, torsion routines, volume integration, element stiffness assembly, export functions, and weight law utilities. |

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
