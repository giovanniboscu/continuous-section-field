# Version: CSF-CUF numerics package reorganization v1 - 2026-09-30
"""Numerical CUF basis implementations and shared numerical utilities."""

from .geometry import all_vertices, transverse_bounds, transverse_scales
from .integration import FixedGaussPolygonIntegrator
from .longitudinal_lagrange_blend import (
    LongitudinalLagrangeBlendBasis,
    LongitudinalSegmentedBasis,
)
from .scaled_lagrange import ScaledLagrangeBasis
from .scaled_lagrange_q1 import ScaledLagrangeQ1Basis
from .scaled_legendre import ScaledLegendreBasis
from .scaled_maclaurin import ScaledMaclaurinBasis
from .scaled_maclaurin_tensor import ScaledMaclaurinTensorBasis
from .scaled_taylor import ScaledTaylorBasis

__all__ = [
    "FixedGaussPolygonIntegrator",
    "LongitudinalLagrangeBlendBasis",
    "LongitudinalSegmentedBasis",
    "ScaledLagrangeBasis",
    "ScaledLagrangeQ1Basis",
    "ScaledLegendreBasis",
    "ScaledMaclaurinBasis",
    "ScaledMaclaurinTensorBasis",
    "ScaledTaylorBasis",
    "all_vertices",
    "transverse_bounds",
    "transverse_scales",
]
