# NREL 5-MW Tower Validation Case
<img width="631" height="547" alt="image" src="https://github.com/user-attachments/assets/2bf9827f-df1d-44ee-9937-bacb486373d8" />

> ### Reproducibility environment
>
> This validation case assumes that the repository and Python environment have been configured as described in:
>
> [Reproducibility environment](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/reproducibility_environment.md)
>
> The commands in this document must be executed from:
>
> ```bash
> docs/aes/nrel_case
> ```

## Purpose of this document

This document describes a fully reproducible validation workflow for the transverse tip displacement and torsional tip rotation of a cantilever tower under combined loading. The tower is the NREL 5-MW reference wind turbine tower, modelled as a tapered thin-walled steel tube fixed at the base. The validation checks that two independent computation paths produce consistent results for both the undegraded tower and a tower with localized longitudinal stiffness degradation.

The objective is to compare two modelling paths:

1. a CSF-to-OpenSees numerical model;
2. an independent analytical reference that reads the same YAML input but does not rely on CSF section-analysis APIs or OpenSees.

The workflow is applied to two scenarios:

- the baseline tower, without degradation;
- the same tower with a longitudinal stiffness degradation law.

Both scenarios use the same geometry. The degraded case modifies only the longitudinal stiffness distribution through `weight_laws`.

## The workflow

### Workflow overview

The workflow consists of four steps: generating the input files, verifying the section properties, computing the structural response with a numerical model, and checking it against an independent analytical reference.

### Geometry and action generation

CSF (Continuous Section Field) is the tool used to compute and represent the sectional properties of the tower continuously along its axis.

The first step of the workflow is the generation of the input files that describe the NREL 5-MW reference tower geometry and material stiffness distribution.

This step is executed by:

- `create_yaml_nrel.py`

The script uses the CSF geometry-generation tool documented in:

[writegeometry_rio_v2 - User Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/writegeometry_rio_v2_guide.md)

This tool generates a YAML geometry file for a single segment with two boundary cross-sections:

- `S0` at the initial axial coordinate `z0`;
- `S1` at the final axial coordinate `z1`.

In this validation case, the generated geometry represents the tapered NREL 5-MW reference tower as a CSF segment. The tower is therefore defined by two boundary sections and by the continuous interpolation of the cross-sectional geometry along the member axis.

Each cross-section is an annular closed cell encoded as a single `@cell` polygon using zero-area bridge segments between the outer and inner contours. The bridge segments are topological connections only and do not represent physical radial walls.


The script generates two YAML models:

- `NREL-5-MW.yaml` - baseline tower model, with the original stiffness distribution;
- `NREL-5-MW-degr.yaml` - degraded tower model, with the same geometry and a longitudinal stiffness reduction law.

The two files define the same tower geometry. The difference between them is limited to the stiffness weighting law assigned through `weight_laws`.

The script also creates the output directories used by the CSF action reports, so that the following analysis steps can write their results in a reproducible folder structure.

> The YAML files define the tower geometry with the steel material already incorporated. The sectional quantities - such as `EA`, `EI`, and `GJ` -  therefore already include the material stiffness. When transferring these to a structural solver such as OpenSees, the material must not be applied a second time. For this reason, the validation model uses neutral carriers (`E = G = 1.0`) and passes the weighted quantities directly as `A = EA`, `I = EI`, and `J = GJ`.

### CSF action reports

Before running the structural model, the section properties are inspected along the tower axis to verify that the geometry and stiffness distribution have been correctly defined.

The action files are:

- `action_nrel.yaml`
- `action_nrel-degr.yaml`

Each file configures the section-property inspection for one scenario. When executed, they produce plots and numerical tables of the sectional quantities along the tower height - area, bending stiffness, torsional stiffness - allowing the geometry and stiffness distribution to be checked before the structural model is run.

The baseline action file is applied to `NREL-5-MW.yaml`, while the degraded action file is applied to `NREL-5-MW-degr.yaml`.

### CSF-OpenSees model

- `run_csf_opensees.py`

This script reads the tower YAML file, extracts the sectional properties along the tower axis, and builds a beam finite-element model. The tower is loaded with a transverse tip force, a torsional tip moment, and a uniform distributed transverse load. The tip displacement and torsional rotation are computed for several uniform discretizations, from 4 to 32 elements.

The beam model uses force-based beam-column elements with two-point Gauss integration per element.

This is the numerical path:

```text
YAML input → sectional properties → beam model → tip response
```

### Independent analytical reference

- `run_analytical_reference.py`

This script reads the same geometry from the YAML file directly and computes the tip displacement and torsional rotation through direct analytical integration, without using the same tools as the numerical model.

The tower is loaded with the same transverse tip force, torsional tip moment, and uniform distributed transverse load used in the beam model.

This is the independent reference path:

```text
YAML input → sectional properties → analytical integration → tip response
```

The purpose of this second path is to avoid validating one numerical model only against another output produced by the same computational machinery. The analytical reference uses the same physical input file, but follows an autonomous integration procedure. Therefore, any agreement with the beam model is more significant than a comparison between two outputs generated by the same tools.

---

##  Workflow execution sequence

Run the complete validation workflow in this order.

### 1. Generate the YAML input files

```bash
python3 create_yaml_nrel.py
```

Expected result:

```text
File generated successfully: NREL-5-MW.yaml
OK -- degraded YAML generated

Generated:
  - NREL-5-MW.yaml
  - NREL-5-MW-degr.yaml
```

The script also creates the output directories for the CSF action reports.

### 2. Run the CSF action report for the baseline case

```bash
csf-actions NREL-5-MW.yaml action_nrel.yaml
```

This produces the section-property report for the baseline tower.

The generated report is then checked against the official NREL 5-MW tower data reported in Table 6-1. The CSF section-property output uses the following notation, which maps directly to the NREL reference quantities:

- `Ix` (bending stiffness, fore-aft) corresponds to `TwFAStif`;
- `Iy` (bending stiffness, side-side) corresponds to `TwSSStif`;
- `J_sv_cell` (Saint-Venant torsional stiffness) corresponds to `TwGJStif`;
- `A` (axial stiffness) corresponds to `TwEAStif`.

> **Note on the NREL tower reference data.**  
> The validation uses the official NREL 5-MW tower data from NREL/TP-500-38060, Section 6, Table 6-1, "Distributed Tower Properties". The table reports the distributed quantities along the tower elevation, including `TMassDen`, `TwFAStif`, `TwSSStif`, `TwGJStif`, and `TwEAStif`. The geometric dimensions used to generate these values require one clarification: Section 6 first reports the DOWEC-derived tower dimensions as base diameter/thickness `6.0 m / 0.027 m` and top diameter/thickness `3.87 m / 0.019 m`, but then states that the wall thickness was increased by 30% before producing the final distributed tower properties. Therefore, the CSF model uses the same diameters, but the increased wall thicknesses: `t_base = 0.027 × 1.30 = 0.0351 m` and `t_top = 0.019 × 1.30 = 0.0247 m`.

For example, at the tower base (`z = 0.00 m`), the CSF report gives:

```text
Ix        = 6.14340962544e+11
Iy        = 6.14340962544e+11
J_sv_cell = 4.72585963926e+11
A         = 1.38127060565e+11
```

These values agree with the corresponding NREL reference values to within 0.04% along the full tower height, confirming that the geometry and stiffness distribution reproduce the official NREL sectional stiffness distribution before any degradation law is applied.

> **Volume consistency note.**  
> This volume check is not intended as the main validation metric. Its role is to document that the generated CSF geometry is also integrated consistently by the same workflow used to produce the sectional reports and the downstream OpenSees model. The corresponding CSF volume report is:
>
> ```text
> out/nrel_volume.txt
> ```
>
> The theoretical shell volume of the tapered NREL tower is
>
> ```text
> V = ∫₀ᴸ π(ro(z)² - ri(z)²) dz
> ```
>
> with
>
> ```text
> ri(z) = ro(z) - t(z)
> ```
>
> Using the tower dimensions reported in Section 6 of NREL/TP-500-38060 gives:
>
> ```text
> V ≈ 40.8676 m³
> ```
>
> which is consistent with the CSF integrated volume report.

### 3. Run the CSF action report for the degraded case

```bash
csf-actions NREL-5-MW-degr.yaml action_nrel-degr.yaml
```

<img width="992" height="654" alt="image" src="https://github.com/user-attachments/assets/29232887-e724-46bb-9bb7-ff635c08742f" />

This produces the section-property report for the degraded tower.

The purpose of this step is to verify that the degradation law has been correctly introduced into the stiffness distribution before running the structural analysis. The degraded model uses the same tower geometry as the baseline model; only the longitudinal stiffness distribution is modified through `weight_laws`.

The action report provides a direct check of the degraded stiffness field, allowing the sectional quantities and plots to be inspected along the tower height and confirming that the reduction is applied correctly to the tower wall stiffness.

This step is important because the degraded structural response is meaningful only if the degradation law has first been verified at the section level. The degradation is inspected as a continuous field along the tower height before being transferred to the structural beam model.

## Longitudinal stiffness degradation law

The degraded tower configuration uses the same geometry as the undegraded NREL tower. Only the longitudinal stiffness distribution is modified.

The degradation is introduced through a continuous weight law applied to the longitudinal stiffness of the tower wall. The weight field is defined as a smooth function of the axial coordinate `z`.

The exact degradation law used in the model is:

```yaml
weight_laws:
  - 'cell_base@cell,cell_head@cell: 210000000000*np.maximum(0.84,1.0-0.10*np.exp(-((z-0.33*L)**2)/(2*(0.03*L)**2))-0.14*np.exp(-((z-0.67*L)**2)/(2*(0.03*L)**2)))'
```

The resulting distribution is shown below.

<img width="985" height="467" alt="image" src="https://github.com/user-attachments/assets/50866952-f5ca-4ca3-969b-caf1a0b69934" />

The law defines a baseline stiffness of `2.10 × 10^11` and introduces two localized Gaussian-shaped reductions along the tower height. The first reduction is centered at `z = 0.33 L` with amplitude `0.10`. The second is centered at `z = 0.67 L` with amplitude `0.14`. Both zones use the same characteristic width of `0.03 L`.

The expression `np.maximum(0.84, ...)` sets a lower bound on the stiffness reduction. With the current parameters the two Gaussian zones do not overlap significantly, so the bound is not active. It acts as a safeguard if the parameters are changed.

The degradation field is intentionally continuous and smooth. No geometric discontinuities are introduced. This allows the validation to isolate the influence of localized stiffness variation without mixing it with geometric changes.

The objective of this law is to create a more demanding convergence scenario for the beam discretization. In the undegraded tower, the stiffness varies smoothly because of the tower taper alone. In the degraded case, the additional local reductions create sharper axial gradients that are more difficult to reproduce with coarse beam discretizations. This makes the degraded configuration suitable for evaluating how the beam model converges toward the continuous stiffness function that CSF provides as the reference model.

## Structural loading configuration

The validation uses the same structural loading configuration for both the undegraded and degraded tower models.

The tower is modelled as a cantilever beam:

- fixed base at `z = 0`;
- free tip at `z = L`.

The OpenSees model applies:

- transverse tip force `FY_TIP = 1.2 × 10^6 N`;
- axial tip force `FZ_TIP = -5.0 × 10^6 N`;
- tip bending moment `MX_TIP = 8.0 × 10^6 N·m`;
- tip torsional moment `MZ_TIP = 3.0 × 10^6 N·m`;
- uniform transverse distributed load `WY_DIST = 8.0 × 10^3 N/m`.

The independent analytical reference uses the load components that contribute directly to the reported checks: `FY_TIP`, `MX_TIP`, and `WY_DIST` for the transverse tip displacement `Uy`, and `MZ_TIP` for the torsional tip rotation `Rz`.

The axial tip force `FZ_TIP` is applied in the OpenSees model, but it is not included in the analytical reference because the reported checks do not evaluate axial shortening or second-order geometric effects.

The distributed load `WY_DIST` is applied through the OpenSees `-beamUniform` element load, which acts in the element local transverse coordinate system rather than directly in the global frame. For the present vertical tower configuration, the resulting contribution to the global transverse response has opposite sign with respect to the concentrated tip force `FY_TIP`. This sign convention is reproduced consistently in both the OpenSees model and the independent analytical reference.

### 4. Run the CSF-OpenSees model for the baseline case

Once the sectional properties have been verified against the official NREL reference data and the loads have been defined, the next step is to evaluate the structural response of the tower using the stiffness distribution generated by CSF inside a beam finite-element model.

The purpose of this step is to verify that the stiffness distribution produced by CSF generates the expected structural response when transferred to a beam model.

The baseline tower model is executed with:

```bash
python3 run_csf_opensees.py NREL-5-MW.yaml
```

The script reads the tower geometry from the YAML file, extracts the sectional properties along the tower axis, and builds the corresponding beam model. The analysis computes the transverse tip displacement, the torsional tip rotation, and the nodal resultants along the tower height, using the baseline stiffness distribution.

The outputs are written to:

```text
openseeslab_output_NREL-5-MW
```

This directory contains the structural response reports, numerical outputs, and plots generated for the baseline validation case.

> The numerical results and their comparison with the independent analytical reference are reported in the validation comparison document.

### 5. Run the independent analytical reference for the baseline case

After the beam model has been executed, the same baseline YAML input is evaluated with an independent analytical reference procedure.

The purpose of this step is to provide a second response calculation that is independent from the numerical model. This reference calculation does not use the CSF library and does not use OpenSees. It reads the same YAML input data and computes the structural response directly from the stiffness distributions defined in the file.

The analytical reference is executed with:

```bash
python3 run_analytical_reference.py NREL-5-MW.yaml
```

The script reads the same `NREL-5-MW.yaml` input file used by the beam model. It then reconstructs the tower geometry and stiffness distributions required for the calculation and performs the response integration independently.

In this baseline case, no degradation law is applied. Therefore, the computed response represents the reference behaviour of the original NREL tower stiffness distribution.

The analytical procedure provides independent values for the transverse tip displacement and the torsional tip rotation. These results are used as the baseline continuous-reference solution and are later compared with the beam model outputs to verify that the numerical model reproduces the same structural response when driven by the same YAML-defined tower data.

### 6. Run the CSF-OpenSees model for the degraded case

After the baseline response has been computed, the same workflow is repeated for the degraded tower model.

The degraded model uses the same tower geometry as the baseline case. The difference is introduced only through the longitudinal stiffness reduction law defined in `NREL-5-MW-degr.yaml`. This allows the effect of degradation to be isolated from any geometric change.

The degraded model is executed with:

```bash
python3 run_csf_opensees.py NREL-5-MW-degr.yaml
```

The script reads the degraded YAML file, extracts the modified stiffness distribution along the tower axis, and builds the corresponding beam model. The analysis computes the transverse tip displacement, the torsional tip rotation, and the nodal resultants along the tower height.

The outputs are written to:

```text
openseeslab_output_NREL-5-MW-degr
```

Comparing this directory with the baseline output directory allows the influence of the longitudinal degradation law to be evaluated directly.

> The numerical results and their comparison with the independent analytical reference are reported in the validation comparison document.

### 7. Run the independent analytical reference for the degraded case

```bash
python3 run_analytical_reference.py NREL-5-MW-degr.yaml
```

This computes the independent analytical reference response for the degraded YAML input.

The purpose of this step is the same as in the baseline analytical reference, but applied to the degraded stiffness field. The calculation does not use the CSF library and does not use OpenSees. It reads the degraded YAML input, reconstructs the required stiffness distributions, and integrates the response through an autonomous analytical procedure.

This provides an independent reference for the degraded tower response. Since the degraded case introduces local stiffness variation along the tower height, this comparison is more demanding than the baseline case.

The degraded analytical reference is therefore used to assess both:

- the correctness of the degraded stiffness interpretation;
- the sensitivity of the beam discretization to localized stiffness variation.

## Expected output organization

The OpenSees results are written into separate directories for each scenario.

Baseline case:

```text
openseeslab_output_NREL-5-MW
```

Degraded case:

```text
openseeslab_output_NREL-5-MW-degr
```

This avoids overwriting results and keeps the two validation cases clearly separated.

Each OpenSees output directory contains:

- raw nodal-resultant CSV files;
- tip-response CSV files;
- a markdown report;
- convergence plots for tip displacement and torsional rotation;
- nodal-resultant plots.

## Interpretation of the validation

The baseline and degraded cases are intended to verify different aspects of the workflow.

The baseline case checks that the beam model reproduces the response of a smooth tapered tower with no longitudinal stiffness degradation.

The degraded case checks that the same workflow remains consistent when the stiffness field varies locally along the tower height.

The analytical reference provides an independent check because it does not use OpenSees and does not use the same computational tools. It only reads the same YAML input and performs the analytical integration directly.

Agreement between the beam model results and the analytical reference supports the consistency of:

- the YAML definition;
- the sectional property distribution;
- the beam discretization;
- the stiffness degradation law;
- the independent analytical formulation.

## Convergence behaviour

The final convergence comparison is reported in:

[Validation comparison - all scenarios](validation_comparison_summary_all_b.md)

That document collects the beam model results and compares them against the independent analytical reference for both tower configurations:

- the undegraded NREL tower;
- the degraded NREL tower.

The non-degraded case is expected to converge rapidly. Since the stiffness varies smoothly and monotonically with the tower taper, even a coarse beam discretization can capture the global response reasonably well.

The degraded case is more demanding. The local stiffness reductions introduce sharper variations along the member axis. As a result, coarse discretizations can be less reliable and may show a less regular convergence trend.

This behaviour highlights one of the main motivations for using a continuous stiffness representation. A simple piecewise model with too few stations may miss or underrepresent local stiffness variations, while a denser discretization converges toward the continuous analytical reference.

The comparison report provides the final validation evidence through:

- numerical tables of tip displacement and torsional rotation;
- relative errors against the independent analytical reference;
- convergence plots for both undegraded and degraded scenarios.

The comparison therefore supports two conclusions:

1. for smooth non-degraded variation, the model converges quickly;
2. for localized degradation, the response is more sensitive to axial discretization, and convergence requires a finer representation.

## Summary

This validation case provides a compact and reproducible workflow for checking the NREL 5-MW tower in two scenarios:

- baseline, non-degraded tower;
- tower with longitudinal stiffness degradation.

The CSF-OpenSees model and the independent analytical reference use the same YAML inputs but follow different computational paths.

The agreement between the two paths confirms that the workflow is internally consistent, while the degraded case highlights the importance of adequate discretization when local stiffness variations are present.
