# CSF–CUF / FEM3D: reproducibility documentation

This directory contains the **current seven-stage reproducibility documentation** for the I-shaped cantilever benchmark. Run all commands from the case root (`cuf/I-Shape_cantilever2`, or an equivalent clean copy), not from `docs/`.

## Documentation index

| File | Purpose |
|---|---|
| [Complete manual workflow](CSF_CUF_FEM3D_Full_Reproducibility_Workflow_EN_v02.md) | Authoritative commands for the seven steps: CUF solutions, independent CUF longitudinal stabilization, FEM3D OpenSees GCI, CUF sectional actions, native-stress FEM3D sectional actions, matching-section comparison, and displacement-field comparisons. |
| [CSF–CUF longitudinal convergence method](CSF_CUF_Longitudinal_Convergence_Method.md) | h- and p-refinement, observed tip displacement, two-successive-increment criterion, provenance, and limits. |
| [FEM3D GCI method](README_FEM3D_GCI_ASME_VV10_1.md) | Three-grid Richardson/GCI formulation, triplet selection, mesh metrics, reporting, and limitations. |
| [Sectional-action comparison method](CSF_CUF_FEM3D_Sectional_Action_Comparison_Method.md) | Common definitions of N, Tz and My; CSF quadrature; CUF stress calculation; native-stress FEM3D recovery; load reference; section matching. |
| [Native FEM3D sectional resultants](FEM3D_NATIVE_SECTION_RESULTANTS.md) | OpenSees stress component order, Gauss-point sampling, center P0 recovery, and generated data. |
| [Displacement-verification methodology](CSF_CUF_FEM3D_Displacement_Verification_Methodology_Paper.md) | Common physical sampling, vector displacement differences, volume-weighted norms, and verification methodology suitable for the manuscript. |

## Which commands to follow

**The complete manual workflow is authoritative** for current case YAMLs, script names, input checkpoints and seven-stage ordering. Methodological documents may contain historical example paths to previously generated FEM3D NPZs; do not treat those illustrative paths as the selected checkpoint of a new run. Always read the currently selected file from `fem3d/convergence_gci/run_NNNN/convergence_result.json`.

The following distinctions are intentional:

- CSF–CUF h/p stabilization uses successive **CUF-only** tip-displacement changes; it is not a GCI analysis.
- FEM3D GCI is estimated from a **single monitored displacement** under longitudinal mesh refinement at fixed transverse discretization; the asymptotic regime is not independently certified.
- The selected native-stress FEM3D `center` recovery averages eight Gauss stresses per H8 cell; it is not a native stress measurement at the cell center.
- CSF–CUF / FEM3D displacement-field comparisons are **post-selection verification**, not a criterion to choose CUF or FEM3D refinements.
- Surface-traction and volume residual checks are **outside this current benchmark workflow**.

This curated directory intentionally excludes superseded workflows, draft scratchpads, historical case manifests, optional source patches, and the separate residual-diagnostics documentation. Numerical outputs and provenance belong in their respective `diagnostics/`, `output/`, and `fem3d/convergence_gci/` folders, not in this `docs/` directory.
