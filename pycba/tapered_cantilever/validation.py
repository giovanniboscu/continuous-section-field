"""Compare independently defined physical and numerical quantities."""
import csv
import math
from csf_section import sectional_properties
from reference_solution import analytical_properties


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def relative_error(value, reference):
    return abs(value-reference)/abs(reference)


def validate_section_properties(field, case, length, E_ref, output):
    rows = []
    for i in range(21):
        x = length*i/20
        actual = sectional_properties(field, x, E_ref)
        expected = analytical_properties(case, x)
        row = {'x_mm': x}
        for key, ref in expected.items():
            row[f'{key}_csf'] = actual[key]
            row[f'{key}_ref'] = ref
            row[f'{key}_rel_error'] = relative_error(actual[key], ref)
        rows.append(row)
    write_csv(output/'section_validation.csv', rows)
    if any(v > 1e-8 or not math.isfinite(v) for row in rows
           for k, v in row.items() if k.endswith('_rel_error')):
        raise ValueError('Section validation failed; see section_validation.csv')
    return rows
