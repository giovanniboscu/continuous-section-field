from pycba_analysis import solve_continuous, solve_midpoint
from validation import relative_error


def run_convergence_study(EI, length, load, reference, counts):
    rows = []
    for n in counts:
        midpoint = solve_midpoint(EI, length, load, n)
        continuous = solve_continuous(EI, length, load, n)
        rows.append({'elements': n, 'reference_mm': reference,
                     'midpoint_mm': midpoint, 'continuous_mm': continuous,
                     'midpoint_rel_error': relative_error(midpoint, reference),
                     'continuous_rel_error': relative_error(continuous, reference)})
    return rows


def degree_study(EI, length, load, reference):
    rows = []
    for degree in [2, 4, 8, 12, 16]:
        value = solve_continuous(EI, length, load, degree=degree)
        rows.append({'degree_parameter': degree, 'tip_mm': value,
                     'relative_error': relative_error(value, reference)})
    return rows
