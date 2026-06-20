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

The workflow is applied to two scenarios:

- the baseline tower, without degradation;
- the same tower with a longitudinal stiffness degradation law.

Both scenarios use the same geometry. The degraded case modifies only the longitudinal stiffness distribution through `weight_laws`.

## The workflow

### Workflow overview

The workflow consists of four steps: generating the input files, verifying the section properties, computing the structural response with a numerical model, and checking it against an independent analytical reference.

### Geometry and participation-field definition

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

> **Geometry note.**
> The outer diameters are taken directly from NREL/TP-500-38060, Section 6. Only the wall thickness is scaled: the original values reported for the tower, 0.027 m at the base and 0.019 m at the top, are increased by 30%, giving 0.0351 m and 0.0247 m, respectively. The outer radii are computed as $R = D/2$, the inner radii as $R_i = R - t$, and the inner diameters as $D_i = 2R_i$.



Each cross-section is not represented as two independent polygons, but as a single @cell polygonal path: one ordered point list describes the outer contour together with the inner void contour, using opposite orientations to define the annular closed cell.


The script generates two YAML models:

* `NREL-5-MW.yaml` - baseline tower model, with the original stiffness distribution;
* `NREL-5-MW-degr.yaml` - degraded tower model, with the same geometry and a longitudinal stiffness-reduction law.

The two files define the same tower geometry. Their difference is limited to the stiffness weighting law assigned through `weight_laws` (participation fields).

The script also creates the output directories used by the CSF action reports, so that the following analysis steps can write their results to a reproducible folder structure.

### CSF action reports

Before running the structural model, the tower section properties are inspected for both the baseline and degraded scenarios using `csf-actions` to verify that the geometry and participation fields produce the expected stiffness distribution along the axis.

The geometry files define the tower geometry and participation fields:

* `NREL-5-MW.yaml`
* `NREL-5-MW-degr.yaml`

The corresponding action files define the inspections to be performed:

* `action_nrel.yaml`
* `action_nrel-degr.yaml`

Each action file produces plots and numerical tables of the sectional quantities along the tower height, including area, bending stiffness, and torsional stiffness.



### CSF-OpenSees model

The CSF-OpenSees model is generated by `run_csf_opensees_gaussN.py`. The script reads the tower YAML file, samples the continuous CSF sectional field along the tower axis, and builds a beam finite-element model in OpenSees.
The tower is loaded with a transverse tip force, an axial force, a tip bending moment, a torsional tip moment, and a uniform distributed transverse load.
The tip displacement and torsional rotation are computed for several uniform beam discretizations, from 4 to 32 elements.

The OpenSees model uses force-based beam-column elements with two Gauss section-integration points per element. The number of Gauss points is exposed by the script as a parameter of the OpenSees sampling of the continuous CSF field.

This is the numerical path:

```text
YAML input → continuous CSF sectional field → section sampling → OpenSees beam model → tip response
```


> In this workflow, the elastic moduli `E` and `G` are already included in the sectional stiffnesses computed by CSF. Therefore, they must not be applied again in OpenSees. The OpenSees model uses neutral material parameters and receives the CSF-computed stiffness quantities directly.

### Independent continuous baseline

The baseline is computed by `run_analytical_reference.py`. The script evaluates the tip displacement and torsional rotation without calling CSF section-sampling APIs. It does not read any YAML input file. The tower endpoint dimensions, loads, and supported material cases are defined directly inside the script, and the selected case is controlled by a single external parameter.

The tower is loaded with the same transverse tip force, tip bending moment, torsional tip moment, and uniform distributed transverse load used in the OpenSees model. The axial force applied in OpenSees is not used in this reference calculation, because this check does not evaluate axial shortening or second-order geometric effects.

This is the baseline path:

```
fixed tower data → continuous section-property functions → tolerance-based integration grid → analytical integration → tip response
```

The purpose of this path is to compare the sampled OpenSees model with a continuous reference calculation that is not obtained from CSF section sampling. The two calculations use the same tower data and loading assumptions, but they follow different computational procedures.





#### The CSF-OpenSees model and the independent continuous baseline are evaluated as paired procedures for each scenario: first for the baseline tower model, and then for the degraded tower model.


---

## Workflow execution sequence

Run the complete validation workflow in this order.

## 1. Generate the YAML input files

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

## 2. Run the CSF action report for the baseline case

```bash
csf-actions NREL-5-MW.yaml action_nrel.yaml
```

<img width="994" height="648" alt="image" src="https://github.com/user-attachments/assets/f78a6e3e-a499-4050-83b5-674aa3a6c60c" />

This produces the section-property report for the baseline tower.

The generated report is then checked against the official NREL 5-MW tower data reported in Table 6-1. The CSF section-property output uses the following notation, which maps directly to the NREL reference quantities:

- `Ix` (bending stiffness, fore-aft) corresponds to `TwFAStif`;
- `Iy` (bending stiffness, side-side) corresponds to `TwSSStif`;
- `J_sv_cell` (Saint-Venant torsional stiffness) corresponds to `TwGJStif`;
- `A` (axial stiffness) corresponds to `TwEAStif`.

In CSF, the reported sectional quantities are weighted by the assigned participation fields; in this validation, they therefore correspond directly to stiffness quantities rather than to purely geometric section properties.

###  NREL 5-MW tower validation tables

The validation uses the NREL 5-MW tower data from NREL/TP-500-38060, Section 6, Table 6-1 ([Jonkman et al., 2009](https://doi.org/10.2172/947422)). 


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

### CSF values

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

### Difference [%], CSF vs NREL

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


Agreement with the NREL reference values is better than 0.04% over the full tower height, confirming that the CSF model reproduces the original NREL sectional stiffness distribution prior to the application of any degradation law.

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

## 3. Run the CSF action report for the degraded case

```bash
csf-actions NREL-5-MW-degr.yaml action_nrel-degr.yaml
```

<img width="992" height="654" alt="image" src="https://github.com/user-attachments/assets/29232887-e724-46bb-9bb7-ff635c08742f" />

This produces the section-property report for the degraded tower.

The purpose of this step is to verify that the degradation law has been correctly introduced into the stiffness distribution before running the structural analysis. The degraded model uses the same tower geometry as the baseline model; only the longitudinal stiffness distribution is modified through `weight_laws`.

The action report provides a direct check of the degraded stiffness field along the tower height, confirming at the section level that the reduction introduced through `weight_laws` is applied before the structural beam model is run.


## Longitudinal stiffness degradation law

The degraded tower configuration uses the same geometry as the undegraded NREL tower. Only the longitudinal stiffness distribution is modified.

The degradation is introduced through a prescribed continuous weight law applied to the tower-wall stiffness. The weight field is defined as a smooth function of the axial coordinate $z$ and is used here to represent a localized stiffness-reduction field, not a measured damage scenario.

The exact degradation law used in the model is:

```yaml
weight_laws:
  - 'cell_base@cell,cell_head@cell: 210000000000*np.maximum(0.84,1.0-0.10*np.exp(-((z-0.33*L)**2)/(2*(0.03*L)**2))-0.14*np.exp(-((z-0.67*L)**2)/(2*(0.03*L)**2)))'
```

The resulting distribution is shown below.

<img width="985" height="467" alt="image" src="https://github.com/user-attachments/assets/50866952-f5ca-4ca3-969b-caf1a0b69934" />

The law defines a baseline stiffness of `2.10 × 10^11` and introduces two localized Gaussian-shaped reductions along the tower height. The first reduction is centered at `z = 0.33 L` with amplitude `0.10`. The second is centered at `z = 0.67 L` with amplitude `0.14`. Both zones use the same characteristic width of `0.03 L`.

The expression `np.maximum(0.84, ...)` sets a lower bound on the stiffness factor. With the current parameters the two Gaussian zones do not overlap significantly, so the bound is not active. It acts as a safeguard if the parameters are changed.

The degradation field is intentionally continuous and smooth. No geometric discontinuities are introduced. This allows the validation to isolate the influence of localized stiffness variation without mixing it with geometric changes.

The objective of this law is to create a more demanding convergence scenario for the beam discretization. In the undegraded tower, the stiffness varies smoothly because of the tower taper alone. In the degraded case, the additional local reductions create sharper axial gradients that are more difficult to reproduce with coarse beam discretizations. This makes the degraded configuration suitable for evaluating how the beam model converges toward the continuous stiffness function defined by the YAML model.

## Structural loading configuration

Before the scenario-specific runs are executed, the structural loading configuration is defined once and used for both the baseline and degraded tower models.

The tower is modelled as a cantilever beam:

* fixed base at `z = 0`;
* free tip at `z = L`.

The OpenSees model applies:

* transverse tip force `FY_TIP = 1.2 × 10^6 N`;
* axial tip force `FZ_TIP = -5.0 × 10^6 N`;
* tip bending moment `MX_TIP = 8.0 × 10^6 N·m`;
* tip torsional moment `MZ_TIP = 3.0 × 10^6 N·m`;
* uniform transverse distributed load `WY_DIST = 8.0 × 10^3 N/m`.

The independent continuous baseline uses only the load components that contribute directly to the reported checks: `FY_TIP`, `MX_TIP`, and `WY_DIST` for the transverse tip displacement `Uy`, and `MZ_TIP` for the torsional tip rotation `Rz`.

The axial tip force `FZ_TIP` is applied in the OpenSees model, but it is not included in the independent continuous baseline because the reported checks do not evaluate axial shortening or second-order geometric effects.

> **Sign convention note.**  
> The distributed load `WY_DIST` is applied through the OpenSees `-beamUniform` element load. For the present vertical tower configuration, its contribution to the reported transverse tip displacement is taken with the sign convention used consistently in both the OpenSees model and the independent continuous baseline.


### 4. Run the CSF-OpenSees model for the baseline case

Once the sectional properties have been verified against the official NREL reference data and the structural loads have been defined, the next step is to evaluate the structural response of the tower by transferring the CSF stiffness distribution to a beam finite-element model.

The baseline tower model is executed with:

```bash
python3 run_csf_opensees_gaussN.py NREL-5-MW.yaml --gauss-points 2
```
>The ruled-volume lines are coloured by the participation field; when the field is constant, the lines appear with a single colour while the colour bar is retained for consistency with cases involving spatially varying participation laws.

The script reads the tower geometry and stiffness distribution from the YAML file, samples the continuous CSF sectional field along the tower axis, and builds the corresponding OpenSees beam model. The analysis computes the transverse tip displacement, the torsional tip rotation, and the nodal resultants along the tower height.

In this validation case, the CSF field is sampled with two Gauss section-integration points per beam element. The number of Gauss points is a parameter of the OpenSees sampling of the continuous CSF field and does not modify the YAML model definition.

The outputs are written to:

```text
openseeslab_output_NREL-5-MW
```

This directory contains the structural response reports, numerical outputs, and plots generated for the baseline validation case.

> The numerical results and their comparison with the independent continuous baseline are reported in the validation comparison document.

### 5. Run the independent continuous baseline for the baseline case

After the CSF-OpenSees model has been executed, the independent continuous-reference calculation is run for the baseline tower case.

The purpose of this step is to provide a second response calculation that is independent of the OpenSees beam model. This reference calculation does not use OpenSees, does not call CSF section-sampling APIs, and does not read any YAML input file. The tower endpoint dimensions, loads, and supported material cases are defined directly inside `run_analytical_reference.py`.

The independent continuous baseline for the baseline case is executed with:

```bash
python3 run_analytical_reference.py constant
```

The script does not use a fixed reference discretization prescribed a priori. Instead, it selects the reference integration grid from a prescribed admissible tolerance, `REF_TOL_PCT = 1.0e-10`.

The selected grid is then used to compute the transverse tip displacement and the torsional tip rotation.

In this baseline case, no degradation law is applied. Therefore, the computed response represents the continuous baseline behaviour of the original NREL tower stiffness distribution.

The outputs are written to:

```text
baseline_output_nrel_constant
```

This directory contains the independent continuous-reference report:

```text
analytical_reference.txt
```

These results are later compared with the CSF-OpenSees outputs to verify that the sampled beam model reproduces the same structural response when evaluated against the corresponding continuous reference calculation.



### 6. Run the CSF-OpenSees model for the degraded case

After the baseline response has been computed, the same CSF-OpenSees workflow is repeated for the degraded tower model.

The degraded model uses the same tower geometry as the baseline case. The difference is introduced only through the longitudinal stiffness reduction law defined in `NREL-5-MW-degr.yaml`. This isolates the effect of stiffness degradation from any geometric change.

The degraded model is executed with:

```bash
python3 run_csf_opensees_gaussN.py NREL-5-MW-degr.yaml --gauss-points 2
```

The script reads the degraded YAML file, samples the corresponding continuous CSF sectional field along the tower axis, and builds the OpenSees beam model. The analysis computes the transverse tip displacement, the torsional tip rotation, and the nodal resultants along the tower height.

In this validation case, the CSF field is sampled with two Gauss section-integration points per beam element. The number of Gauss points is a parameter of the OpenSees sampling of the continuous CSF field and does not modify the YAML model definition.

The outputs are written to:

```text
openseeslab_output_NREL-5-MW-degr
```

Comparing this directory with the baseline output directory allows the influence of the longitudinal degradation law to be evaluated directly.

> The numerical results and their comparison with the independent continuous baseline are reported in the validation comparison document.


### 7. Run the independent continuous baseline for the degraded case

The independent continuous baseline for the degraded case is executed with:

```bash
python3 run_analytical_reference.py degraded
```

This computes the continuous-reference response for the degraded tower case. The calculation does not use OpenSees, does not call CSF section-sampling APIs, and does not read any YAML input file. The tower endpoint dimensions, loads, and degraded material law are defined directly inside `run_analytical_reference.py`.

The purpose of this step is the same as in the baseline reference case, but applied to the degraded stiffness distribution. The reference calculation uses the same tower geometry and loading assumptions, while the selected material case introduces the prescribed longitudinal stiffness reduction.

The reference grid is selected from the prescribed admissible tolerance, `REF_TOL_PCT = 1.0e-10`, rather than from a fixed number of reference sections.

The outputs are written to:

```
baseline_output_nrel_degraded
```

This directory contains the independent continuous-reference report:

```
analytical_reference.txt
```

The degraded continuous baseline is used to compare the sampled OpenSees response against a continuous reference calculation for the same degraded stiffness case. It also provides a reference for assessing the sensitivity of the OpenSees sampling of the continuous CSF field to localized stiffness variation.



## Expected output organization

The validation workflow writes the OpenSees results and the independent continuous baselines into separate directories.

Baseline tower case:

```text
openseeslab_output_NREL-5-MW
baseline_output_NREL-5-MW
```

Degraded tower case:

```text
openseeslab_output_NREL-5-MW-degr
baseline_output_NREL-5-MW-degr
```

The `openseeslab_output_*` directories contain the results produced by the OpenSees sampling of the continuous CSF field:

* raw nodal-resultant CSV files;
* tip-response CSV files;
* a markdown report;
* convergence plots for tip displacement and torsional rotation;
* nodal-resultant plots.

The `baseline_output_*` directories contain the independent continuous-reference results:

* `analytical_reference.txt`;


This organization keeps the two validation cases separated and also keeps the two computational paths distinct: the OpenSees sampling of the continuous CSF field and the independent continuous baseline.


## Interpretation of the validation

The validation compares two computational paths applied to the same tower cases.

The first path is the OpenSees sampling of the continuous CSF field. The YAML file defines the continuous sectional field, and OpenSees receives a sampled beam-model representation of that field.

The second path is the independent continuous baseline. It does not read any YAML input file. The required tower geometry and stiffness distributions are defined directly in the reference script, and the response is computed by direct integration without using OpenSees and without calling CSF section-sampling APIs.

The purpose of the comparison is therefore not only to observe convergence with mesh refinement. The main point is to verify that the CSF-defined continuous sectional model can be transferred to a structural solver and compared against an independent continuous reference.

Two tower configurations are considered:

* the undegraded NREL tower, where the stiffness variation follows the smooth geometric taper;
* the degraded NREL tower, where the same geometry is combined with a localized longitudinal stiffness reduction law.

The undegraded case checks the response of the baseline tower model. Since the stiffness field varies smoothly along the height, the OpenSees sampling of the continuous CSF field is expected to be less sensitive to the axial discretization.

The degraded case is more demanding. The local stiffness reductions introduce sharper variations in the continuous field. Coarser beam discretizations may under-sample these variations, while denser section sampling improves the agreement with the continuous baseline.

The comparison supports the consistency of:

* the CSF model definition;
* the continuous sectional-property field;
* the stiffness degradation law;
* the CSF-OpenSees projection;
* the consistency between the sampled OpenSees model and the continuous baseline.

The final comparison is reported in:

[Validation comparison - all scenarios](validation_comparison_summary_all_b.md)

That document collects the OpenSees tip responses and compares them against the independent continuous baseline for both tower configurations. The reported quantities are the transverse tip displacement `Uy`, the torsional tip rotation `Rz`, the number of OpenSees elements, the number of CSF section evaluations, and the relative errors with respect to the continuous baseline.

The comparison therefore supports the intended validation message: CSF defines a continuous sectional model, while the beam solver receives a sampled representation of that model. The discretization controls how the field is interrogated; it does not define the field itself.


## Summary

This validation case provides a compact and reproducible workflow for checking the NREL 5-MW tower in two scenarios:

* baseline, non-degraded tower;
* tower with longitudinal stiffness degradation.

Both scenarios are defined as CSF YAML inputs for the OpenSees workflow, where the tower is represented as a continuous sectional field. The independent continuous baseline does not read those YAML files; it uses the same tower data and material cases defined directly in the reference script.

The agreement between the two paths confirms the consistency between the sampled CSF-OpenSees representation and the independent continuous-reference calculation.

The degraded case further shows why the continuous-field representation is useful: local stiffness variations are part of the same model definition, while the solver discretization only controls how that field is sampled.


