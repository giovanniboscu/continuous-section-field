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
2. an independent analytical reference based on the same geometric and material definitions, but implemented directly in the reference code without using CSF section-analysis APIs or OpenSees.
3. 
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

The script is parameterized to generate the circular tower sections as polygonal approximations of the circumference. In this validation case, the circular contour is discretized with 2048 sides, providing a high-resolution polygonal representation of the annular section used by CSF.

The script uses the CSF geometry-generation tool documented in:

[writegeometry_rio_v2 - User Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/writegeometry_rio_v2_guide.md)

This tool generates a YAML geometry file for a single segment with two boundary cross-sections:

- `S0` at the initial axial coordinate `z0`;
- `S1` at the final axial coordinate `z1`.


In this validation case, the generated geometry represents the tapered NREL 5-MW reference tower as a single CSF segment. The tower is defined by two boundary sections and by the continuous interpolation of the cross-sectional geometry along the member axis.

The geometric parameters used to generate the two boundary sections are:

| Quantity            | Base section `S0` | Top section `S1` |
| ------------------- | ----------------: | ---------------: |
| Axial coordinate    |        `z0 = 0.0` |      `z1 = 87.6` |
| Outer diameter in x |        `dx = 6.0` |      `dx = 3.87` |
| Outer diameter in y |        `dy = 6.0` |      `dy = 3.87` |
| Outer radius        |         `R = 3.0` |      `R = 1.935` |
| Wall thickness      |      `t = 0.0351` |     `t = 0.0247` |
| Inner radius        |    `R_i = 2.9649` |   `R_i = 1.9103` |
| Inner diameter      |    `D_i = 5.9298` |   `D_i = 3.8206` |

The circular contours are generated as high-resolution polygonal approximations. In this validation case, each circular contour is discretized with 2048 sides, providing a polygonal annular representation of the closed-cell section used by CSF.

Each cross-section is an annular closed cell encoded as a single `@cell` polygonal path composed of the outer and inner contours with opposite orientation.

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

* `run_csf_opensees_gaussN.py`
  

This script reads the tower YAML file, samples the continuous CSF sectional field along the tower axis, and builds a beam finite-element model in OpenSees. The tower is loaded with a transverse tip force, an axial force, a tip bending moment, a torsional tip moment, and a uniform distributed transverse load.

The tip displacement and torsional rotation are computed for several uniform beam discretizations, from 4 to 32 elements.

In the validation case reported here, the OpenSees model uses force-based beam-column elements with **two Gauss section-integration points per element**. The corresponding command is:

```bash
python3 run_csf_opensees_gaussN.py NREL-5-MW-degr.yaml --gauss-points 2
```

The number of Gauss points is exposed by the script as a parameter of the CSF-to-OpenSees projection. It controls how the continuous CSF field is sampled by the solver, but it does not change the YAML model definition.

This is the numerical path:

```text
YAML input → continuous CSF sectional field → two-point Gauss section sampling → OpenSees beam model → tip response
```

### Independent continuous baseline

* `run_analytical_reference.py`

This script computes the tip displacement and torsional rotation through an independent continuous-reference procedure. The reference path does not call CSF section-sampling APIs. Instead, it reads the same YAML input file, extracts the boundary geometry and the longitudinal stiffness law, and reconstructs the continuous functions used for the analytical integration.

The tower is loaded with the same transverse tip force, tip bending moment, torsional tip moment, and uniform distributed transverse load used in the OpenSees model. The axial force applied in OpenSees is not used in this independent reference, because this check does not evaluate axial shortening or second-order geometric effects.

The reference grid is not prescribed as a fixed number of sections. Instead, the script starts from a prescribed admissible tolerance,

```python
REF_TOL_PCT = 1.0e-10
```

and selects the first reference grid that satisfies this tolerance over the tested sequence of integration grids.

This is the independent baseline path:

```text
YAML input → continuous section-property functions → tolerance-based integration grid → analytical integration → tip response
```

The purpose of this independent path is to avoid validating the CSF-OpenSees model only against another output produced by the same computational machinery. The baseline uses the same physical input file, but follows an autonomous integration procedure. Therefore, agreement with the beam model verifies the sampled OpenSees projection against an independently reconstructed continuous reference.



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


# NREL 5-MW tower validation tables

The validation uses the NREL 5-MW tower data from NREL/TP-500-38060, Section 6, Table 6-1. The CSF geometry uses the reported base and top diameters, with the 30% wall-thickness increase stated in Section 6: 6.0 m / 0.0351 m at the base and 3.87 m / 0.0247 m at the top. The radius and thickness are linearly tapered along the 87.6 m tower height.

Agreement with the NREL reference values is better than 0.04% over the full tower height, confirming that the adopted geometry accurately reproduces the original NREL sectional stiffness distribution prior to the application of any degradation law.

## 1. NREL reference values

| Elev. [m] | HtFract | TwFAStif [N m²] | TwSSStif [N m²] | TwGJStif [N m²] | TwEAStif [N] |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0.0 | 614.340E9 | 614.340E9 | 472.750E9 | 138.130E9 |
| 8.76 | 0.1 | 534.820E9 | 534.820E9 | 411.560E9 | 129.270E9 |
| 17.52 | 0.2 | 463.270E9 | 463.270E9 | 356.500E9 | 120.710E9 |
| 26.28 | 0.3 | 399.130E9 | 399.130E9 | 307.140E9 | 112.430E9 |
| 35.04 | 0.4 | 341.880E9 | 341.880E9 | 263.090E9 | 104.450E9 |
| 43.80 | 0.5 | 291.010E9 | 291.010E9 | 223.940E9 | 96.760E9 |
| 52.56 | 0.6 | 246.030E9 | 246.030E9 | 189.320E9 | 89.360E9 |
| 61.32 | 0.7 | 206.460E9 | 206.460E9 | 158.870E9 | 82.250E9 |
| 70.08 | 0.8 | 171.850E9 | 171.850E9 | 132.240E9 | 75.430E9 |
| 78.84 | 0.9 | 141.780E9 | 141.780E9 | 109.100E9 | 68.900E9 |
| 87.60 | 1.0 | 115.820E9 | 115.820E9 | 89.100E9 | 62.660E9 |

## 2. CSF values

| Elev. [m] | HtFract | TwFAStif [N m²] | TwSSStif [N m²] | TwGJStif [N m²] | TwEAStif [N] |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0.0 | 614.341E9 | 614.341E9 | 472.586E9 | 138.127E9 |
| 8.76 | 0.1 | 534.819E9 | 534.819E9 | 411.414E9 | 129.272E9 |
| 17.52 | 0.2 | 463.266E9 | 463.266E9 | 356.371E9 | 120.707E9 |
| 26.28 | 0.3 | 399.130E9 | 399.130E9 | 307.034E9 | 112.433E9 |
| 35.04 | 0.4 | 341.881E9 | 341.881E9 | 262.995E9 | 104.450E9 |
| 43.80 | 0.5 | 291.011E9 | 291.011E9 | 223.862E9 | 96.758E9 |
| 52.56 | 0.6 | 246.026E9 | 246.026E9 | 189.258E9 | 89.357E9 |
| 61.32 | 0.7 | 206.457E9 | 206.457E9 | 158.819E9 | 82.247E9 |
| 70.08 | 0.8 | 171.851E9 | 171.851E9 | 132.198E9 | 75.427E9 |
| 78.84 | 0.9 | 141.776E9 | 141.776E9 | 109.063E9 | 68.899E9 |
| 87.60 | 1.0 | 115.820E9 | 115.820E9 | 89.096E9 | 62.661E9 |

## 3. Difference [%], CSF vs NREL

| Elev. [m] | HtFract | TwFAStif [%] | TwSSStif [%] | TwGJStif [%] | TwEAStif [%] |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0.0 | +0.0002 | +0.0002 | -0.0347 | -0.0021 |
| 8.76 | 0.1 | -0.0001 | -0.0001 | -0.0355 | +0.0012 |
| 17.52 | 0.2 | -0.0009 | -0.0009 | -0.0363 | -0.0026 |
| 26.28 | 0.3 | -0.0001 | -0.0001 | -0.0346 | +0.0028 |
| 35.04 | 0.4 | +0.0004 | +0.0004 | -0.0361 | +0.0002 |
| 43.80 | 0.5 | +0.0002 | +0.0002 | -0.0346 | -0.0019 |
| 52.56 | 0.6 | -0.0016 | -0.0016 | -0.0328 | -0.0034 |
| 61.32 | 0.7 | -0.0016 | -0.0016 | -0.0322 | -0.0041 |
| 70.08 | 0.8 | +0.0004 | +0.0004 | -0.0319 | -0.0038 |
| 78.84 | 0.9 | -0.0029 | -0.0029 | -0.0342 | -0.0022 |
| 87.60 | 1.0 | -0.0000 | -0.0000 | -0.0046 | +0.0012 |





Agreement with the NREL reference values is better than 0.04% over the full tower height, confirming that the adopted geometry accurately reproduces the original NREL sectional stiffness distribution prior to the application of any degradation law.

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

* fixed base at `z = 0`;
* free tip at `z = L`.

The OpenSees model applies:

* transverse tip force `FY_TIP = 3.4 × 10^6 N`;
* axial tip force `FZ_TIP = -5.0 × 10^6 N`;
* tip bending moment `MX_TIP = 10.0 × 10^6 N·m`;
* tip torsional moment `MZ_TIP = 5.0 × 10^6 N·m`;
* uniform transverse distributed load `WY_DIST = 8.0 × 10^3 N/m`.

The independent continuous baseline uses the load components that contribute directly to the reported checks: `FY_TIP`, `MX_TIP`, and `WY_DIST` for the transverse tip displacement `Uy`, and `MZ_TIP` for the torsional tip rotation `Rz`.

The axial tip force `FZ_TIP` is applied in the OpenSees model, but it is not included in the independent continuous baseline because the reported checks do not evaluate axial shortening or second-order geometric effects.

The distributed load `WY_DIST` is applied through the OpenSees `-beamUniform` element load. For the present vertical tower configuration, its contribution to the reported transverse tip displacement is taken with the sign convention used consistently in both the OpenSees model and the independent continuous baseline.
eference.

### 4. Run the CSF-OpenSees model for the baseline case

Once the sectional properties have been verified against the official NREL reference data and the structural loads have been defined, the next step is to evaluate the structural response of the tower by transferring the CSF stiffness distribution to a beam finite-element model.

The purpose of this step is to verify that the continuous sectional field defined by CSF produces the expected structural response when sampled and projected into OpenSees.

The baseline tower model is executed with:

```bash
python3 run_csf_opensees_gaussN.py NREL-5-MW.yaml --gauss-points 2
```

The script reads the tower geometry and stiffness distribution from the YAML file, samples the continuous CSF sectional field along the tower axis, and builds the corresponding OpenSees beam model. The analysis computes the transverse tip displacement, the torsional tip rotation, and the nodal resultants along the tower height.

In this validation case, the CSF field is sampled with two Gauss section-integration points per beam element. The number of Gauss points is a parameter of the CSF-to-OpenSees projection and does not modify the YAML model definition.

The outputs are written to:

```text
openseeslab_output_NREL-5-MW
```

This directory contains the structural response reports, numerical outputs, and plots generated for the baseline validation case.

> The numerical results and their comparison with the independent continuous baseline are reported in the validation comparison document.

### 5. Run the independent continuous baseline for the baseline case

After the CSF-OpenSees model has been executed, the same baseline YAML input is evaluated with an independent continuous-reference procedure.

The purpose of this step is to provide a second response calculation that is independent from the OpenSees beam model. This reference calculation does not use OpenSees and does not call CSF section-sampling APIs. It reads the same YAML input data, reconstructs the geometry and stiffness distributions required for the calculation, and computes the structural response by direct integration.

The independent continuous baseline is executed with:

```bash
python3 run_analytical_reference.py NREL-5-MW.yaml
```

The script does not use a fixed reference discretization prescribed a priori. Instead, it selects the reference integration grid from a prescribed admissible tolerance:

```python
REF_TOL_PCT = 1.0e-10
```

The selected grid is then used to compute the transverse tip displacement and the torsional tip rotation.

In this baseline case, no degradation law is applied. Therefore, the computed response represents the continuous baseline behaviour of the original NREL tower stiffness distribution.

The outputs are written to:

```text
baseline_output_NREL-5-MW
```

This directory contains the independent continuous-reference report, the reference-grid convergence table, and the adaptive grid-selection table.

These results are later compared with the CSF-OpenSees outputs to verify that the sampled beam model reproduces the same structural response when driven by the same YAML-defined tower data.

### 6. Run the CSF-OpenSees model for the degraded case

After the baseline response has been computed, the same CSF-OpenSees workflow is repeated for the degraded tower model.

The degraded model uses the same tower geometry as the baseline case. The difference is introduced only through the longitudinal stiffness reduction law defined in `NREL-5-MW-degr.yaml`. This isolates the effect of stiffness degradation from any geometric change.

The degraded model is executed with:

```bash
python3 run_csf_opensees_gaussN.py NREL-5-MW-degr.yaml --gauss-points 2
```

The script reads the degraded YAML file, samples the corresponding continuous CSF sectional field along the tower axis, and builds the OpenSees beam model. The analysis computes the transverse tip displacement, the torsional tip rotation, and the nodal resultants along the tower height.

In this validation case, the CSF field is sampled with two Gauss section-integration points per beam element. The number of Gauss points is a parameter of the CSF-to-OpenSees projection and does not modify the YAML model definition.

The outputs are written to:

```text
openseeslab_output_NREL-5-MW-degr
```

Comparing this directory with the baseline output directory allows the influence of the longitudinal degradation law to be evaluated directly.

> The numerical results and their comparison with the independent continuous baseline are reported in the validation comparison document.


### 7. Run the independent continuous baseline for the degraded case

```bash
python3 run_analytical_reference.py NREL-5-MW-degr.yaml
```

This computes the independent continuous-reference response for the degraded YAML input.

The purpose of this step is the same as in the baseline reference case, but applied to the degraded stiffness field. The calculation does not use OpenSees and does not call CSF section-sampling APIs. It reads the degraded YAML input, reconstructs the geometry and stiffness distributions required for the calculation, and integrates the response through an autonomous continuous-reference procedure.

The reference grid is selected from the prescribed admissible tolerance:

```python
REF_TOL_PCT = 1.0e-10
```

rather than from a fixed number of reference sections.

The outputs are written to:

```text
baseline_output_NREL-5-MW-degr
```

This directory contains the independent continuous-reference report, the reference-grid convergence table, and the adaptive grid-selection table for the degraded case.

The degraded continuous baseline is used to assess both:

* the interpretation of the degraded stiffness law from the YAML input;
* the sensitivity of the CSF-OpenSees projection to localized stiffness variation.


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
