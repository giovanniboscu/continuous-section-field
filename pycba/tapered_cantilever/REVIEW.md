# First technical review - v0.1

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

The included results are from local executions with Python 3.11 and PyCBA 1.0.2. All 24 result files (six per case) are preserved, with the degree CSV renamed. The exact CSF commit and full dependency versions should be recorded before publication.

During the convergence study, a small increase in numerical error was observed when refining the continuous-stiffness model. This behaviour was reproduced through an independent Euler–Bernoulli numerical experiment, without either CSF or PyCBA. Repeating the experiment with 32 and 50 decimal digits of precision reduced the error dramatically, providing strong evidence that the observed behaviour is associated with finite-precision arithmetic and matrix conditioning rather than with the continuous representation of sectional rigidity.

This observation is therefore not considered a limitation of the integration. The specific numerical mechanism within PyCBA remains open to discussion with its maintainer.

The review revision changes naming, independent closed-form checks, and documentation and figure generation, without modifying the beam solution or CSF model code. Last-bit differences between computing environments are expected.

## Version notes

- v0.1: cleaned distribution; four exact reference formulas checked in code; degree-study terminology corrected; all sectional CSVs summarized; documentation figures rebuilt from the recorded data. No change to either library or to solver assembly.
