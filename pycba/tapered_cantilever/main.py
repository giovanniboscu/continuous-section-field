"""CSF-PyCBA tutorial: continuous sectional stiffness and independent validation."""
import argparse
from pathlib import Path
from reference_solution import CASES, L, P, E0, reference_deflection, closed_form
from csf_section import load_csf_model, create_ei_function
from pycba_analysis import solve_continuous
from validation import validate_section_properties, relative_error, write_csv
from convergence import run_convergence_study, degree_study
from plotting import plot_results

ROOT = Path(__file__).resolve().parent


def run_case(case):
    output = ROOT/'results'/case
    output.mkdir(parents=True, exist_ok=True)

    # 1. Load physical geometry and material from CSF.
    field = load_csf_model(ROOT/'models'/f'{case}.yaml')

    # 2. Validate CSF sectional properties against independent formulas.
    sections = validate_section_properties(field, case, L, E0, output)

    # 3. Expose the continuous stiffness to PyCBA.
    EI = create_ei_function(field, E0)

    # 4. Calculate an independent Euler-Bernoulli reference displacement.
    reference = reference_deflection(case)
    exact = closed_form(case)
    if exact is not None and relative_error(reference, exact) > 1e-12:
        raise ValueError('Independent quadrature disagrees with closed form')

    # 5. Solve the entire cantilever as one non-prismatic member.
    continuous = solve_continuous(EI, L, P)
    error = relative_error(continuous, reference)
    print(f'{case}: reference={reference:.9f} mm, continuous={continuous:.9f} mm, error={error:.3e}')

    # 6. Compare continuous and midpoint representations under refinement.
    convergence = run_convergence_study(EI, L, P, reference, [1, 2, 4, 8, 16, 32, 64])
    write_csv(output/'convergence.csv', convergence)

    # 7. Check the sensitivity of the single member to the SectionEI polynomial degree.
    write_csv(output/'degree_sensitivity.csv', degree_study(EI, L, P, reference))

    # 8. Save figures and the final validation status.
    plot_results(sections, convergence, output)
    passed = error <= 1e-6
    write_csv(output/'summary.csv', [{'reference_mm': reference, 'continuous_mm': continuous,
                                     'relative_error': error, 'passed': passed}])
    if not passed:
        raise ValueError('Continuous solution exceeds proposed relative tolerance 1e-6')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=[*CASES, 'all'], default='variable_geometry')
    args = parser.parse_args()
    for case in CASES if args.case == 'all' else [args.case]:
        run_case(case)


if __name__ == '__main__':
    main()
