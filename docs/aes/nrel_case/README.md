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

This document describes a fully reproducible validation workflow for the NREL 5-MW reference tower case.

The objective is to compare two modelling paths:

1. a CSF-to-OpenSees numerical model;
2. an independent analytical reference that reads the same YAML input but does not rely on CSF section-analysis APIs or OpenSees.

The workflow is applied to two scenarios:

- the baseline tower, without degradation;
- the same tower with a longitudinal stiffness degradation law.

Both scenarios use the same geometry. The degraded case modifies only the longitudinal stiffness distribution through `weight_laws`.

## The workflow

---

### Workflow overview
### Geometry and action generation

The first step of the workflow is the generation of the CSF input files that describe the NREL 5-MW reference tower geometry and material stiffness distribution.

This step is executed by:

- `create_yaml_nrel.py`

The script uses the CSF geometry-generation tool documented in:

[writegeometry_rio_v2 - User Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/writegeometry_rio_v2_guide.md)

This tool generates a CSF-compatible YAML geometry file for a single segment with two boundary cross-sections:

- `S0` at the initial axial coordinate `z0`;
- `S1` at the final axial coordinate `z1`.

In this validation case, the generated geometry represents the tapered NREL 5-MW reference tower as a CSF segment. The tower is therefore defined by two boundary sections and by the continuous interpolation of the cross-sectional geometry and stiffness carriers along the member axis.

The script generates two YAML models:

- `NREL-5-MW.yaml` - baseline tower model, with the original stiffness distribution;
- `NREL-5-MW-degr.yaml` - degraded tower model, with the same geometry and a longitudinal stiffness reduction law.

The two files define the same tower geometry. The difference between them is limited to the stiffness weighting law assigned through `weight_laws`.

The script also creates the output directories used by the CSF action reports, so that the following analysis steps can write their results in a reproducible folder structure.

> The CSF section field returns stiffness-weighted sectional quantities, such as `EA`, `EI`, and `GJ`. Since the OpenSees `Elastic` section expects separate scalar carriers (`E`, `G`) and geometric section terms (`A`, `I`, `J`), the validation model uses neutral carriers (`E = G = 1.0`) and passes the weighted quantities directly as `A = EA`, `I = EI`, and `J = GJ`. This avoids applying the material stiffness twice and preserves the effective sectional stiffness defined by the continuous section field.

### CSF action reports

After the YAML models have been generated, the next step is to run the CSF action files.

The action files are:

- `action_nrel.yaml`
- `action_nrel-degr.yaml`

These files define the post-processing operations applied to the two tower models. They are executed with `csf-actions` and produce the section-property reports and plots used to inspect the baseline and degraded scenarios.

In particular, the action reports make the continuous section field observable along the tower axis. They provide the sampled sectional quantities, the corresponding plots, and the intermediate outputs needed to check that the geometry and stiffness laws have been correctly interpreted before running the structural OpenSees validation.

The baseline action file is applied to `NREL-5-MW.yaml`, while the degraded action file is applied to `NREL-5-MW-degr.yaml`.

### CSF-OpenSees model

- `run_csf_opensees.py`

This script reads a CSF YAML file, samples the continuous section field, builds the OpenSees beam model, and computes the tip displacement and torsional rotation for several beam discretizations.

This is the numerical path:

```text
CSF YAML → CSF section field → OpenSees model → tip response
```

### Independent analytical reference

- `run_analytical_reference.py`

This script reads the same YAML file directly and reconstructs the analytical reference fields without using OpenSees and without using CSF section-analysis APIs.

This is the independent reference path:

```text
YAML → analytical section fields → continuous integration → tip response
```

The purpose of this second path is to avoid validating one numerical model only against another output produced by the same computational machinery. The analytical reference uses the same physical input file, but follows an autonomous integration procedure. Therefore, any agreement with the CSF-to-OpenSees model is more significant than a comparison between two outputs generated by the same analysis library.

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

<img width="991" height="663" alt="image" src="https://github.com/user-attachments/assets/6ac09363-c878-40ee-93f2-af3845db27d8" />

This produces the CSF report outputs for the non-degraded NREL tower.

The generated section-property report is then checked against the official NREL 5-MW tower data reported in Table 6-1. In this comparison, the CSF sectional quantities reproduce the reference stiffness values with direct correspondence:

[NREL/TP-500-38060 PDF](https://docs.nrel.gov/docs/fy09osti/38060.pdf)

> **Note on the NREL tower reference data.**  
> The validation uses the official NREL 5-MW tower data from NREL/TP-500-38060, Section 6, Table 6-1, “Distributed Tower Properties”. The table reports the distributed quantities along the tower elevation, including `TMassDen`, `TwFAStif`, `TwSSStif`, `TwGJStif`, and `TwEAStif`. The geometric dimensions used to generate these values require one clarification: Section 6 first reports the DOWEC-derived tower dimensions as base diameter/thickness `6.0 m / 0.027 m` and top diameter/thickness `3.87 m / 0.019 m`, but then states that the wall thickness was increased by 30% before producing the final distributed tower properties. Therefore, the CSF model uses the same diameters, but the increased wall thicknesses: `t_base = 0.027 × 1.30 = 0.0351 m` and `t_top = 0.019 × 1.30 = 0.0247 m`.




- `Ix` corresponds to `TwFAStif`;
- `Iy` corresponds to `TwSSStif`;
- `J_sv_cell` corresponds to `TwGJStif`;
- `A` corresponds to `TwEAStif`.

For example, at the tower base (`z = 0.00 m`), the CSF report gives:

```text
Ix        = 6.14340962544e+11
Iy        = 6.14340962544e+11
J_sv_cell = 4.72585963926e+11
A         = 1.38127060565e+11
```

These values match the corresponding NREL reference values:

```text
TwFAStif = 6.143e+11
TwSSStif = 6.143e+11
TwGJStif = 4.728e+11
TwEAStif = 1.381e+11
```

The same agreement is observed along the full tower height, confirming that the CSF geometry and stiffness-carrier representation reproduce the official NREL sectional stiffness distribution before any degradation law is applied.

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


This produces the CSF report outputs for the degraded NREL tower.

The purpose of this step is to verify that the degradation law has been correctly introduced into the continuous section field before running the structural analysis. The degraded model uses the same tower geometry as the baseline model; only the longitudinal stiffness distribution is modified through `weight_laws`.

The action report therefore provides a direct check of the degraded stiffness field. It allows the sampled sectional quantities and plots to be inspected along the tower height, confirming that the reduction is applied to the intended stiffness carriers and that the resulting field remains consistent with the baseline geometry.

This step is important because the degraded structural response is meaningful only if the degradation law has first been verified at section-field level. In other words, the OpenSees model should not be treated as the first place where the degradation is checked. The degradation is first inspected as a CSF continuous field, then transferred to the structural beam model.



## Longitudinal stiffness degradation law

The degraded tower configuration uses the same geometry as the undegraded NREL tower. Only the longitudinal stiffness distribution is modified.

The degradation is introduced through a continuous weight law applied to the stiffness carriers of the tower shell polygons. The weight field is defined as a smooth longitudinal function of the axial coordinate `z`.

The exact degradation law used in the model is:

```yaml
weight_laws:
  - 'cell_base@cell,cell_head@cell: 210000000000*np.maximum(0.84,1.0-0.10*np.exp(-((z-0.33*L)**2)/(2*(0.03*L)**2))-0.14*np.exp(-((z-0.67*L)**2)/(2*(0.03*L)**2)))'
```

The resulting distribution is shown below.

<img width="985" height="467" alt="image" src="https://github.com/user-attachments/assets/50866952-f5ca-4ca3-969b-caf1a0b69934" />


The law defines a baseline stiffness value of:

```text
2.10 × 10^11
```

and introduces two localized Gaussian-shaped longitudinal reductions along the tower height.

The first reduction is centered approximately at:

```text
z = 0.33 L
```

and applies a moderate stiffness decrease with amplitude:

```text
0.10
```

The second reduction is centered approximately at:

```text
z = 0.67 L
```

and applies the strongest degradation with amplitude:

```text
0.14
```

Both degradation zones use the same characteristic width:

```text
0.03 L
```

The expression:

```python
np.maximum(0.84, ...)
```

imposes a lower bound on the normalized stiffness factor. This prevents the degradation law from reducing the stiffness below:

```text
0.84 × 2.10 × 10^11 = 1.764 × 10^11
```

In the plotted field, the observed minimum is slightly above this bound because the sampled plotting points do not necessarily coincide exactly with the analytical minimum of the continuous function.

The degradation field is intentionally continuous and smooth. No geometric discontinuities are introduced. This allows the validation to isolate the influence of localized stiffness variation without mixing it with geometric changes.

The objective of this law is to create a more demanding convergence scenario for the beam discretization. In the undegraded tower, the stiffness field varies smoothly because of the tower taper alone. In the degraded case, the additional local reductions create sharper axial gradients that are more difficult to reproduce with coarse piecewise beam models.

This makes the degraded configuration suitable for evaluating how the OpenSees discretization converges toward the continuous-reference solution as the number of beam elements increases.

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

Once the sectional properties have been verified against the official NREL reference data, the next step is to evaluate the structural response of the tower using the CSF-generated stiffness distribution inside an OpenSees beam model.

The purpose of this stage is not only to run a structural analysis, but also to verify that the continuous sectional representation generated by CSF produces the expected global structural behaviour when transferred to a finite-element formulation.

The baseline tower model is executed with:

```bash
python3 run_csf_opensees.py NREL-5-MW.yaml
```

The script reads the continuous tower description from the YAML model, samples the sectional properties along the tower axis, and generates the corresponding OpenSees beam formulation.

The analysis computes:

- tower tip displacement;
- tower tip rotation;
- torsional response;

using the non-degraded stiffness distribution.

The outputs are written to the scenario-specific directory:

```text
openseeslab_output_NREL-5-MW
```

This directory contains the structural response reports, numerical outputs, and plots generated for the baseline validation case.

### 5. Run the independent analytical reference for the baseline case

After the CSF-to-OpenSees model has been executed, the same baseline YAML input is evaluated with an independent analytical reference procedure.

The purpose of this step is to provide a second response calculation that is independent from both computational paths used in the numerical model. In particular, this reference calculation does not use the CSF analysis library and does not use OpenSees. It is implemented as an autonomous integration procedure that reads the same YAML input data and computes the structural response directly from the stiffness distributions defined in the file.

The analytical reference is executed with:

```bash
python3 run_analytical_reference.py NREL-5-MW.yaml
```

The script reads the same `NREL-5-MW.yaml` input file used by the CSF-to-OpenSees model. It then reconstructs the tower geometry and stiffness distributions required for the calculation and performs the response integration independently.

In this baseline case, no degradation law is applied. Therefore, the computed response represents the reference behaviour of the original NREL tower stiffness distribution.

The autonomous integration procedure provides independent values for:

- tower tip displacement;
- tower tip rotation;
- torsional rotation.

These results are used as the baseline continuous-reference solution. They are later compared with the CSF-to-OpenSees outputs to verify that the numerical beam model reproduces the same structural response when driven by the same YAML-defined tower data.

### 6. Run the CSF-OpenSees model for the degraded case

After the baseline response has been computed, the same CSF-to-OpenSees workflow is repeated for the degraded tower model.

The degraded model uses the same tower geometry as the baseline case. The difference is introduced only through the longitudinal stiffness reduction law defined in `NREL-5-MW-degr.yaml`. This allows the effect of degradation to be isolated from any geometric change.

The degraded CSF-to-OpenSees model is executed with:

```bash
python3 run_csf_opensees.py NREL-5-MW-degr.yaml
```

The script reads the degraded YAML model, samples the modified stiffness distribution along the tower axis, and transfers the resulting sectional properties to the OpenSees beam model.

The analysis computes the degraded structural response in terms of:

- tower tip displacement;
- tower tip rotation;
- torsional response.

The outputs are written to the scenario-specific directory:

```text
openseeslab_output_NREL-5-MW-degr
```

This directory contains the numerical response reports, plots, and structural-analysis outputs for the degraded validation scenario.

Comparing this directory with the baseline output directory allows the influence of the longitudinal degradation law to be evaluated directly.

### 7. Run the independent analytical reference for the degraded case

```bash
python3 run_analytical_reference.py NREL-5-MW-degr.yaml
```

This computes the independent continuous-reference response for the degraded YAML input.

The purpose of this step is the same as in the baseline analytical reference, but applied to the degraded stiffness field. The calculation does not use the CSF analysis library and does not use OpenSees. It reads the degraded YAML input, reconstructs the required stiffness distributions, and integrates the response through an autonomous analytical procedure.

This provides an independent reference for the degraded tower response. Since the degraded case introduces local stiffness variation along the tower height, this comparison is more demanding than the baseline case. 
This model provides a reference for verifying the corresponding CSF-to-OpenSees discretized beam model.

The degraded analytical reference is therefore used to assess both:

- the correctness of the degraded stiffness interpretation;
- the sensitivity of the OpenSees beam discretization to localized stiffness variation.

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

The baseline case checks that the CSF-to-OpenSees model reproduces the response of a smooth tapered tower with no longitudinal stiffness degradation.

The degraded case checks that the same workflow remains consistent when the stiffness field varies locally along the tower height.

The analytical reference provides an independent check because it does not use OpenSees and does not rely on CSF section-analysis APIs. It only reads the same YAML input and performs the continuous analytical integration.

Agreement between the CSF-OpenSees results and the analytical reference supports the consistency of:

- the YAML definition;
- the CSF continuous section field;
- the OpenSees beam discretization;
- the stiffness degradation law;
- the independent analytical formulation.

## Convergence behaviour

The final convergence comparison is reported in:

[Validation comparison - all scenarios](validation_comparison_summary_all_b.md)


That document collects the CSF-to-OpenSees results and compares them against the independent analytical reference for both tower configurations:

- the undegraded NREL tower;
- the degraded NREL tower.

The non-degraded case is expected to converge rapidly. Since the stiffness varies smoothly and monotonically with the tower taper, even a coarse beam discretization can capture the global response reasonably well.

The degraded case is more demanding. The local stiffness reductions introduce sharper variations along the member axis. As a result, coarse discretizations can be less reliable and may show a less regular convergence trend.

This behaviour highlights one of the main motivations for using a continuous section-field representation. A simple piecewise model with too few stations may miss or underrepresent local stiffness variations, while a denser discretization converges toward the continuous analytical reference.

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
