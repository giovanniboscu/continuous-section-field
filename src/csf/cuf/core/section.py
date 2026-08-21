"""Section representation and CSF adapter for the CSF-CUF bridge.

This module is an architectural extraction from ``csf_cuf.py``.
No section-provider logic is changed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Tuple

import numpy as np


@dataclass(frozen=True)
class PolygonDomain:
    """Generic polygonal transverse domain represented by (y, z) vertices."""

    vertices: Tuple[Tuple[float, float], ...]
    name: str | None = None
    weight: float | None = None


class SectionProvider(ABC):
    """
    Generic provider of the longitudinal CSF domain and transverse domains
    Omega^k(x).

    The longitudinal interval belongs to the sectional model. The solver must
    query it here rather than duplicate x_start, x_end, or length in its own
    configuration.
    """

    @abstractmethod
    def longitudinal_domain(self) -> Tuple[float, float]:
        """
        Return the physical longitudinal interval (x_start, x_end).
        """
        raise NotImplementedError

    @abstractmethod
    def domains(self, x: float) -> Tuple[PolygonDomain, ...]:
        raise NotImplementedError

    def domain(self, x: float, domain_id: int) -> PolygonDomain:
        domains = self.domains(x)

        if not 1 <= domain_id <= len(domains):
            raise IndexError(
                f"domain_id must be in 1..{len(domains)}, got {domain_id}"
            )

        return domains[domain_id - 1]

    def number_of_domains(self, x: float) -> int:
        return len(self.domains(x))


class CSFSectionProvider(SectionProvider):
    """
    Adapter from ContinuousSectionField to SectionProvider.

    YAML parsing remains the responsibility of CSFReader.
    """

    def __init__(self, field: Any) -> None:
        if field is None:
            raise ValueError("field must not be None")
        if not hasattr(field, "section"):
            raise TypeError("field must expose section(z)")
        self._field = field

    def longitudinal_domain(self) -> Tuple[float, float]:
        """
        Return the longitudinal interval owned by the ContinuousSectionField.

        ContinuousSectionField exposes its two defining end sections as
        ``s0`` and ``s1``; their ``z`` coordinates are the authoritative
        longitudinal endpoints of the CSF model.
        """

        if not hasattr(self._field, "s0") or not hasattr(self._field, "s1"):
            raise TypeError(
                "ContinuousSectionField must expose s0 and s1 end sections"
            )

        if not hasattr(self._field.s0, "z") or not hasattr(self._field.s1, "z"):
            raise TypeError(
                "CSF end sections s0 and s1 must expose z coordinates"
            )

        x0 = float(self._field.s0.z)
        x1 = float(self._field.s1.z)

        if not np.isfinite(x0) or not np.isfinite(x1):
            raise ValueError("CSF longitudinal endpoints must be finite")

        if x1 <= x0:
            raise ValueError(
                f"CSF longitudinal domain must satisfy x_end > x_start; "
                f"got ({x0}, {x1})"
            )

        return x0, x1

    def domains(self, x: float) -> Tuple[PolygonDomain, ...]:
        if not np.isfinite(x):
            raise ValueError("longitudinal coordinate x must be finite")

        section = self._field.section(float(x))

        if section is None:
            raise ValueError(f"CSF returned no section at x={x}")
        if not hasattr(section, "polygons"):
            raise TypeError("CSF section has no polygons attribute")

        result = []

        for polygon in section.polygons:
            if not hasattr(polygon, "vertices"):
                raise TypeError("CSF polygon has no vertices attribute")

            vertices = []

            for vertex in polygon.vertices:
                if hasattr(vertex, "x") and hasattr(vertex, "y"):
                    vertices.append((float(vertex.x), float(vertex.y)))
                elif isinstance(vertex, (tuple, list)) and len(vertex) == 2:
                    vertices.append((float(vertex[0]), float(vertex[1])))
                else:
                    raise TypeError("unsupported CSF vertex representation")

            result.append(
                PolygonDomain(
                    vertices=tuple(vertices),
                    name=getattr(polygon, "name", None),
                    weight=(
                        float(polygon.weight)
                        if hasattr(polygon, "weight")
                        else None
                    ),
                )
            )

        return tuple(result)


