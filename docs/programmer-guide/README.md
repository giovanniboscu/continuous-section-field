# CSF User Guide - Modeling and Sectional Analysis

Programmer-oriented documentation for building, validating, and integrating **Continuous Section Field (CSF)** models.

This is a **practical programmer guide** for CSF.  
The guide uses a single thread: **learn by examples**.

---

##  Get the Project and Create a Virtual Environment

```bash
# Clone the repository
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .

```

After activating the environment, create a dedicated working folder where all project files will be stored:

```bash
mkdir csf_project
cd csf_project
```


## Chapters
1. [01 geometry model](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/01_geometry_model.md)
2. [02 plotting sections_and_volume](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/02_plotting_sections_and_volume.md)
3. [03 plotting properties](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/03_plotting_properties.md)
4. [04 plotting weight & shear_weight ](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/04_plotting_weight.md)
5. [05 Stacked field](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/07_csf_stacked.md)
6. [06 opensees export](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/opensees_export.md)
8. [07 geometry and properties export](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/geometry_properties_export.md)
9. [08 Parametric vs materialized YAML export](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/to_yaml-write_section.md)
10. [09 CSF Stress APIs](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/to_yaml-write_section.md)
11. `...` 
