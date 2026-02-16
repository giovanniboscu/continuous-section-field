# CSF User Guide — Modeling and Sectional Analysis

Programmer-oriented documentation for building, validating, and integrating **Continuous Section Field (CSF)** models.

This is a **practical programmer guide** for CSF.  
The guide uses a single thread: **learn by examples**.

---

##  Environment Setup

Before running any CSF example, install:

- Python (recommended: Python 3.10+)
- Git

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
1. [01_geometry model](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/01_geometry_model.md)
2. [02_plotting sections_and_volume](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/02_plotting_sections_and_volume.md)
3. [03_plotting properties](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/03_plotting_properties.md)
4. [04_plotting weight]()
5. `05_torsion_wall_and_cell.md`
6. `06_actions_pipeline.md`
7. `07_errors_and_diagnostics.md`
8. `08_validation_and_benchmarks.md`
9. `09_solver_integration.md`
