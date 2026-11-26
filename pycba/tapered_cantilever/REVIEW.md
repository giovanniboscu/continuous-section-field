# First technical review — v0.1

**Prepared for Colin Caprani | 26 November 2026**

This is a working review draft, not a released PyCBA tutorial. The primary example is case B (tapered cantilever); A provides a baseline, and C/D are optional material-variation extensions.

## Suggested review sequence

1. Read [README.md](README.md) and `main.py` for the physical problem and executable workflow.
2. Inspect `csf_section.py` and `pycba_analysis.py` for the coupling, including local member coordinates and weighted inertia.
3. Review [THEORY.md](THEORY.md) and [VALIDATION.md](VALIDATION.md) for the independent reference, convergence and degree sensitivity.
4. Run the tapered case using the documented CLI, then optionally run all four cases.

## Questions for joint review

- Is the public SectionEI callable interface used in the intended way for PyCBA 1.0.2, including polynomial fitting and local member coordinates?
- Is the description of the degree parameter and its relationship to flexibility integration accurate?
- Should the initial PyCBA tutorial focus on B alone, with C/D as optional extensions?
- What tutorial format and dependency-installation instructions best fit the PyCBA documentation?

## Evidence and reproducibility

The included results are from the original local executions with Python 3.11 and PyCBA 1.0.2. All 24 result files (six per case) are preserved, with the degree CSV renamed. The exact CSF commit and full dependency versions of the original runs were not supplied; record these before publication. The review revision changes naming, independent closed-form checks and documentation/figure generation, not the beam solution or CSF model code. The revised end-to-end solver run is pending local confirmation. Last-bit differences between environments are expected.

The current tests concern polynomial rigidity laws, a rectangular section with uniform modulus within each section, and a tip-loaded Euler–Bernoulli cantilever. Direct off-sample checks of the fitted SectionEI function, non-polynomial laws and other load cases are possible future extensions, not completed tests.

## Version notes

- v0.1: cleaned distribution; four exact reference formulas checked in code; degree-study terminology corrected; all sectional CSVs summarized; documentation figures rebuilt from the recorded data. No change to either library or to solver assembly.
