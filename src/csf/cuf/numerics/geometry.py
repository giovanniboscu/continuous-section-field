# Version: CSF-CUF numerics package reorganization v1 - 2026-09-30
"""Transverse numerical geometry helpers shared by CUF basis plugins."""

from __future__ import annotations

import numpy as np


def all_vertices(section_provider, x: float) -> np.ndarray:
    return np.asarray(
        [
            (float(y), float(z))
            for domain in section_provider.domains(float(x))
            for y, z in domain.vertices
        ],
        dtype=float,
    )


def transverse_scales(section_provider) -> tuple[float, float]:
    x0, x1 = map(float, section_provider.longitudinal_domain())
    vertices = np.vstack((all_vertices(section_provider, x0), all_vertices(section_provider, x1)))
    y_scale = float(np.max(np.abs(vertices[:, 0])))
    z_scale = float(np.max(np.abs(vertices[:, 1])))
    if y_scale <= 0.0 or z_scale <= 0.0:
        raise ValueError("CSF transverse coordinate scales must be positive")
    return y_scale, z_scale


def transverse_bounds(section_provider, x: float):
    vertices = all_vertices(section_provider, x)
    return (
        float(np.min(vertices[:, 0])), float(np.max(vertices[:, 0])),
        float(np.min(vertices[:, 1])), float(np.max(vertices[:, 1])),
    )
