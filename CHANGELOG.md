# Changelog

## V0.1.7
NREL validation: updated J_sv_wall thickness computation

## v0.1.5 - v0.1.6 

- 2026-05-16 - Refactor csf_sp and improve handling of closely spaced geometries. Add shear_weight_laws support and legend to plot_volume.

## v0.1.4

- 2026-05-09 - added analyse_torsion_carrier for G_i  -> e.j is G.J on csf_sp

## v0.1.3

- 2026-05-04 - Introduction of the shear_weight field

## v0.1.2.5

- 2026-04-24 -  removed weight comment

## v0.1.2.4

- 2026-04-24 - sectionproperties to csf
- 2026-04-21 - Delete src/csf/io/section_field-gt1.py

## v0.1.2.3

- 2026-04-16 - improved yaml geometry check

## v0.1.2.2

- 2026-04-16 - fixed j_sv_cell inner loop
- 2026-04-15 - Create csf_sp_wall_complex_verification.py
- 2026-04-15 - Create csf_sp_cell_verification.py
- 2026-04-15 - Create csf_sp_complex_integration_verification.py
- 2026-04-11 - Update csf_to_openfast.py
- 2026-04-10 - csf_to_openfast
- 2026-04-10 - Update run_pier50.py
- 2026-04-10 - Update compare_results.py
- 2026-04-10 - Update run_pier50.py
- 2026-04-10 - Update compare_results.py
- 2026-04-10 - Create run_pier50.py
- 2026-04-10 - Create compare_results.py
- 2026-04-06 - Update csf_to_elastodyn.py
- 2026-04-06 - Update bmodes_out_to_elastodyn.py
- 2026-04-06 - Update generate_openfast_case_templates.py
- 2026-04-06 - Update csf_to_elastodyn.py
- 2026-04-06 - Update bmodes_out_to_elastodyn.py
- 2026-04-05 - Create csf_to_elastodyn.py
- 2026-04-05 - Create bmodes_out_to_elastodyn.py
- 2026-04-05 - Create generate_openfast_case_templates.py

## v0.1.2.1

- 2026-04-04 - plot_volume3d modified

## v0.1.2

- 2026-04-02 - set_weight law fixed
- 2026-03-31 - Create csf_polygon_hole_builder.py
- 2026-03-31 - Delete src/csf/utils/csf_create_cone.py
- 2026-03-31 - Create writegeometry_rio_v2.py

## v0.1.1

- 2026-03-27 - fixed plot properties

## v0.1.0

- 2026-03-20 - sap2K export report J_tors desc
- 2026-03-20 - export modified
- 2026-03-19 - J_tors desc skip modified
- 2026-03-19 - fix J_tors
- 2026-03-18 - Create writegeometry_v6_twist.py
- 2026-03-15 - twisttower
- 2026-03-15 - Delete cases directory
- 2026-03-15 - Create writegeometry_v6_twist.py
- 2026-03-14 - add t auto in @cell
- 2026-03-13 - modifies area and volume report
- 2026-03-08 - sectionproperties added
- 2026-03-08 - scf sectionproperties added
- 2026-02-28 - Fix section_field.py polygon_area_centroid
- 2026-02-28 - Fix csf_reader.py
- 2026-02-27 - Delete actions-examples/pycba_wz_demo directory
- 2026-02-27 - Delete actions-examples/Museum-Mercedes-Benz directory
- 2026-02-27 - Delete actions-examples/blade directory
- 2026-02-27 - modifed sap2000/opensees  J=> Ip
- 2026-02-24 - J_sv removed
- 2026-02-23 - plot properties fixed J_sv
- 2026-02-23 - validation yaml weight_laws
- 2026-02-22 - CSFStackd modified
- 2026-02-22 - Create cylinder_withcheck.py
- 2026-02-22 - Delete example/cilinder_withcheck.py
- 2026-02-21 - Expose Visualizer in public API and update CSF reader/section field
- 2026-02-21 - Adopt src layout and fix intra-package imports
- 2026-02-19 - J_sv_cell/wall t modified opensees export
- 2026-02-19 - CSFStacked first release
- 2026-02-09 - fixed @cell/@wall tag
- 2026-02-07 - J_sv_cell modified + plot2d legend
- 2026-02-07 - tornal mixed exmaple
- 2026-02-07 - action examples
- 2026-02-07 - API CSF completed
- 2026-02-07 - WIP before sync


## v0.1.0

- 2026-01-09 - remove: tsection_opensees.py (keep local copy)
- 2026-01-09 - feat: complete OpenSeesPy integration and release V1

## v0.1.0

- 2026-01-09 - feat: complete OpenSeesPy integration and release
- 2026-01-09 - restored:  verifier script from repository
- 2026-01-09 - remove: delete verifier script from repository
- 2026-01-09 - feat: integrate OpenSeesPy and enhance section analysis core
- 2025-12-27 - Update tsection_opensees.py
- 2025-12-27 - Update tsection_opensees.py
- 2025-12-26 - Align core engine with README: implemented torsional estimation
- 2025-12-26 - opensees update
- 2025-12-26 - Counter-Clockwise negative area are forbitten
- 2025-12-25 - assemble_element_stiffness_matrix at 19 points
- 2025-12-25 - fix: update imports from section_field to csf in example scripts
