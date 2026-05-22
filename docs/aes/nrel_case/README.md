
<img width="631" height="547" alt="image" src="https://github.com/user-attachments/assets/2bf9827f-df1d-44ee-9937-bacb486373d8" />

# NREL 5-MW Tower Validation Case

## Purpose of this document

This document describes a fully reproducible validation workflow for the NREL 5-MW reference tower case.

The objective is to compare two modelling paths:

1. a CSF-to-OpenSees numerical model;
2. an independent analytical reference that reads the same YAML input but does not rely on CSF section-analysis APIs or OpenSees.

The workflow is applied to two scenarios:

- the baseline tower, without degradation;
- the same tower with a longitudinal stiffness degradation law.

Both scenarios use the same geometry. The degraded case modifies only the longitudinal stiffness distribution through `weight_laws`.

## Files used in the workflow

### Geometry and action generation

The first step of the workflow is the generation of the CSF input files that describe the NREL 5-MW reference tower geometry and material stiffness distribution.

This step is executed by:

- `create_yaml_nrel.sh`

The script generates two YAML models:

- `NREL-5-MW.yaml` - baseline tower model, with the original stiffness distribution;
- `NREL-5-MW-degr.yaml` - degraded tower model, with the same geometry and a longitudinal stiffness reduction law.

The two files define the same tower geometry. The difference between them is limited to the stiffness weighting law assigned through `weight_laws`.

The script also creates the output directories used by the CSF action reports, so that the following analysis steps can write their results in a reproducible folder structure.

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

## Execution sequence

Run the complete validation workflow in this order.

### 1. Generate the YAML input files

```bash
./create_yaml_nrel.sh
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


### 3. Run the CSF action report for the degraded case

```bash
csf-actions NREL-5-MW-degr.yaml action_nrel-degr.yaml
```
<img width="992" height="654" alt="image" src="https://github.com/user-attachments/assets/29232887-e724-46bb-9bb7-ff635c08742f" />



This produces the CSF report outputs for the degraded NREL tower.
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


### 5. Run the analytical reference for the baseline case

```bash
python3 run_analytical_reference.py NREL-5-MW.yaml
```

This computes the independent continuous-reference response for the same baseline YAML input.

### 6. Run the CSF-OpenSees model for the degraded case

```bash
python3 run_csf_opensees.py NREL-5-MW-degr.yaml
```

This computes the tip displacement and torsional rotation for the degraded model.

The outputs are written to a scenario-specific directory:

```text
openseeslab_output_NREL-5-MW-degr
```

### 7. Run the analytical reference for the degraded case

```bash
python3 run_analytical_reference.py NREL-5-MW-degr.yaml
```

This computes the independent continuous-reference response for the degraded YAML input.

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

The non-degraded case is expected to converge rapidly. Since the stiffness varies smoothly and monotonically with the tower taper, even a coarse beam discretization can capture the global response reasonably well.

The degraded case is more demanding. The local stiffness reductions introduce sharper variations along the member axis. As a result, coarse discretizations can be less reliable and may show a less regular convergence trend.

This behaviour is important: the degraded case demonstrates why a continuous section-field description is useful. A simple piecewise model with too few stations may miss or underrepresent local stiffness variations, while a denser discretization converges toward the continuous reference.

The comparison therefore supports two conclusions:

1. for smooth non-degraded variation, the model converges quickly;
2. for localized degradation, the response is more sensitive to the axial discretization, and convergence requires a finer representation.

![Undegraded NREL tower - convergence](validation_comparison_summary_all_b.md)

## Summary

This validation case provides a compact and reproducible workflow for checking the NREL 5-MW tower in two scenarios:

- baseline, non-degraded tower;
- tower with longitudinal stiffness degradation.

The CSF-OpenSees model and the independent analytical reference use the same YAML inputs but follow different computational paths.

The agreement between the two paths confirms that the workflow is internally consistent, while the degraded case highlights the importance of adequate discretization when local stiffness variations are present.
