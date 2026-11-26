"""Bridge from the existing CSF public API to a scalar EI callable."""
import numpy as np
from csf import section_properties
from csf.io.csf_reader import CSFReader


def load_csf_model(path):
    result = CSFReader().read_file(str(path))
    if not result.ok or result.field is None:
        raise ValueError(f'Cannot load {path}: {result.issues}')
    return result.field


def sectional_properties(field, x, E_ref):
    # This benchmark has one solid rectangular polygon at every station.
    # CSF longitudinal z corresponds to PyCBA longitudinal x.
    section = field.section(float(x))
    if len(section.polygons) != 1:
        raise ValueError('Expected a single solid polygon')
    polygon = section.polygons[0]
    w = float(polygon.weight)
    if w <= 0:
        raise ValueError('Expected positive material weight')
    props = section_properties(section)
    # CSF already includes w = E/E_ref in the inertia. Do not multiply by E again.
    return {'h_mm': max(p.y for p in polygon.vertices)-min(p.y for p in polygon.vertices),
            'b_mm': max(p.x for p in polygon.vertices)-min(p.x for p in polygon.vertices),
            'E_MPa': E_ref*w,
            'A_mm2': props['A']/w,
            'Ix_mm4': props['Ix']/w,
            'EI_Nmm2': E_ref*props['Ix']}


def create_ei_function(field, E_ref):
    def EI(x):
        # Support scalar and vector calls from PyCBA polynomial fitting.
        if np.ndim(x) == 0:
            return sectional_properties(field, float(x), E_ref)['EI_Nmm2']
        a = np.asarray(x, dtype=float)
        return np.array([EI(v) for v in a.flat]).reshape(a.shape)
    return EI
