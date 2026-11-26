"""Independent Euler-Bernoulli benchmark; no CSF or PyCBA imports."""
from math import log
from scipy.integrate import quad

L = 5000.0       # mm
P = 10000.0      # N, downward
B = 200.0        # mm
H0 = 500.0       # mm
E0 = 210000.0    # N/mm^2
CASES = {
    'prismatic': (500.0, 210000.0),
    'variable_geometry': (250.0, 210000.0),
    'variable_material': (500.0, 105000.0),
    'combined_variation': (250.0, 105000.0),
}


def analytical_properties(case, x):
    h1, e1 = CASES[case]
    h = H0 + (h1 - H0) * x / L
    e = E0 + (e1 - E0) * x / L
    inertia = B * h**3 / 12
    return {'h_mm': h, 'b_mm': B, 'E_MPa': e, 'A_mm2': B*h,
            'Ix_mm4': inertia, 'EI_Nmm2': e*inertia}


def reference_deflection(case):
    """Positive downward tip displacement, via virtual work."""
    def integrand(t):
        return (1-t)**2 / analytical_properties(case, t*L)['EI_Nmm2']
    integral, _ = quad(integrand, 0, 1, epsabs=1e-25, epsrel=1e-12)
    return P * L**3 * integral


def closed_form(case):
    """Exact virtual-work integral for each of the four benchmarks."""
    scale = P * L**3 / (E0 * (B * H0**3 / 12))
    integrals = {
        'prismatic': 1/3,
        'variable_geometry': 8*log(2)-5,
        'variable_material': 2*log(2)-1,
        'combined_variation': 2/3,
    }
    return scale * integrals[case]
