<img width="631" height="547" alt="image" src="https://github.com/user-attachments/assets/2bf9827f-df1d-44ee-9937-bacb486373d8" />

# NREL 5-MW Tower Validation Case

## Purpose of this document

This document describes a fully reproducible validation workflow for the NREL 5-MW reference tower case.

The objective is to compare two modelling paths:

1. a CSF-to-OpenSees numerical model;
2. an independent analytical reference that reads the same YAML input but does not use CSF section-analysis APIs or OpenSees.

The workflow is used for two scenarios:

- the baseline tower, without degradation;
- the same tower with a longitudinal stiffness degradation law.

The two scenarios share the same geometry. The degraded scenario modifies only the longitudinal stiffness law through `weight_laws`.

## Files used in the workflow

### Geometry and action generation

- `create_yaml_nrel.sh`

Generates both YAML input files:

- `NREL-5-MW.yaml`
- `NREL-5-MW-degr.yaml`

It also creates the output folders used by the CSF action reports.

### CSF action reports

- `action_nrel.yaml`
- `action_nrel-degr.yaml`

These files are used with `csf-actions` to produce section-property and plotting outputs for the two scenarios.

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

This produces the CSF report outputs for the non-degraded NREL tower.

### 3. Run the CSF action report for the degraded case

```bash
csf-actions NREL-5-MW-degr.yaml action_nrel-degr.yaml
```

This produces the CSF report outputs for the degraded NREL tower.

### 4. Run the CSF-OpenSees model for the baseline case

```bash
python3 run_csf_opensees.py NREL-5-MW.yaml
```

This computes the tip displacement and torsional rotation using the CSF-to-OpenSees model.

The outputs are written to a scenario-specific directory:

```text
openseeslab_output_NREL-5-MW
```

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
