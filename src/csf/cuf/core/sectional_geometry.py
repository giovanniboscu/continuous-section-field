# Version: CSF-CUF net homogeneous domain slicer v19 - 2026-08-27
"""Geometry-facing support for transverse CUF sectional integration.

This module is the only sectional layer that sees the real CSF domains.
It converts a physical domain at one longitudinal coordinate into numerical
quadrature data.  The public sectional integral provider consumes those data
without seeing polygon vertices, CSF objects, or real-section topology.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .integration import SectionIntegrator
from .material import ConstitutiveProvider
from .section import SectionProvider


@dataclass(frozen=True)
class SectionalQuadratureData:
    """Numerical representation of one physical sectional domain."""

    domain_id: int
    y_points: np.ndarray
    z_points: np.ndarray
    weights: np.ndarray
    constitutive_matrices: np.ndarray
    material_weight: float | None


class SectionalGeometryProvider:
    """Hide real CSF geometry behind quadrature-ready numerical data."""

    def __init__(
        self,
        *,
        section_provider: SectionProvider,
        constitutive_provider: ConstitutiveProvider,
    ) -> None:
        self._section_provider = section_provider
        self._constitutive_provider = constitutive_provider

    def number_of_domains(self, x: float) -> int:
        return int(self._section_provider.number_of_domains(float(x)))

    def quadrature_data(
        self,
        *,
        x: float,
        domain_id: int,
        integrator: SectionIntegrator,
    ) -> SectionalQuadratureData:
        """Return points, weights and C matrices for one hidden real domain."""

        if not hasattr(integrator, "quadrature_points"):
            raise TypeError(
                "sectional matrix integration requires an integrator exposing "
                "quadrature_points(domain)"
            )

        x = float(x)
        domain_id = int(domain_id)
        domain = self._section_provider.domain(x=x, domain_id=domain_id)
        y_points, z_points, weights = integrator.quadrature_points(domain)

        y_points = np.asarray(y_points, dtype=float)
        z_points = np.asarray(z_points, dtype=float)
        weights = np.asarray(weights, dtype=float)

        if (
            y_points.ndim != 1
            or z_points.shape != y_points.shape
            or weights.shape != y_points.shape
        ):
            raise ValueError(
                "quadrature_points(domain) must return equal-sized "
                "one-dimensional y, z and weight arrays"
            )

        constitutive_matrices = np.empty((y_points.size, 6, 6), dtype=float)
        for point_index, (y, z) in enumerate(zip(y_points, z_points)):
            matrix = np.asarray(
                self._constitutive_provider.matrix(
                    x=x,
                    domain_id=domain_id,
                    y=float(y),
                    z=float(z),
                ),
                dtype=float,
            )
            if matrix.shape != (6, 6):
                raise ValueError(
                    "constitutive provider must return a 6-by-6 matrix"
                )
            constitutive_matrices[point_index, :, :] = matrix

        # Structural activity follows the absolute CSF carrier.  The relative
        # nesting weight must not decide whether a physical domain exists.
        raw_weight = getattr(domain, "weightabs", None)
        material_weight = None if raw_weight is None else float(raw_weight)

        return SectionalQuadratureData(
            domain_id=domain_id,
            y_points=y_points,
            z_points=z_points,
            weights=weights,
            constitutive_matrices=constitutive_matrices,
            material_weight=material_weight,
        )

    def integrate_scalar(
        self,
        *,
        x: float,
        domain_id: int,
        integrator: SectionIntegrator,
        integrand: Callable[[float, float, float], float],
        m: int,
        n: int,
    ) -> float:
        """Integrate a scalar callback without exposing the real domain."""

        x = float(x)
        domain_id = int(domain_id)
        domain = self._section_provider.domain(x=x, domain_id=domain_id)

        def geometry_integrand(y: float, z: float) -> float:
            coefficient = self._constitutive_provider.coefficient(
                x=x,
                domain_id=domain_id,
                m=int(m),
                n=int(n),
                y=float(y),
                z=float(z),
            )
            return float(integrand(float(y), float(z), float(coefficient)))

        return float(integrator.integrate(domain, geometry_integrand))

    def integrate_vector(
        self,
        *,
        x: float,
        domain_id: int,
        integrator: SectionIntegrator,
        integrand: Callable[[float, float, np.ndarray], np.ndarray],
        size: int,
    ) -> np.ndarray:
        """Integrate a vector callback without exposing the real domain."""

        if not hasattr(integrator, "integrate_vector"):
            raise TypeError("integrator does not expose integrate_vector")

        x = float(x)
        domain_id = int(domain_id)
        domain = self._section_provider.domain(x=x, domain_id=domain_id)

        def geometry_integrand(y: float, z: float) -> np.ndarray:
            matrix = np.asarray(
                self._constitutive_provider.matrix(
                    x=x,
                    domain_id=domain_id,
                    y=float(y),
                    z=float(z),
                ),
                dtype=float,
            )
            if matrix.shape != (6, 6):
                raise ValueError(
                    "constitutive provider must return a 6-by-6 matrix"
                )
            return np.asarray(
                integrand(float(y), float(z), matrix),
                dtype=float,
            )

        return np.asarray(
            integrator.integrate_vector(
                domain,
                geometry_integrand,
                size=int(size),
            ),
            dtype=float,
        )
