# Version: CSF-CUF section provider v20 - 2026-09-03
# Changelog: v20 delegates the public CSF entity-inspection API; v19 introduced net homogeneous domain slicing.
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
    """One homogeneous transverse domain prepared for numerical slicing.

    ``vertices`` describe the polygon boundary owned by this material domain.
    ``excluded_vertices`` contain only its direct children.  They are removed
    geometrically by the numerical slicer, irrespective of their material.
    A child is integrated later as its own homogeneous domain when its
    ``weightabs`` is non-zero.
    """

    vertices: Tuple[Tuple[float, float], ...]
    name: str | None = None
    weight: float | None = None
    domain_id: int | None = None
    weightabs: float | None = None
    excluded_vertices: Tuple[Tuple[Tuple[float, float], ...], ...] = ()


class SectionDomainSlicer:
    """Attach stable CSF topology to the geometry sampled at each x.

    CSF polygon identity and containment are index based and remain stable
    along the member.  Therefore ``build_direct_children_map`` is called once
    here.  Subsequent calls reuse that map and update only polygon vertices
    and absolute material weights from the section sampled at the requested x.
    """

    def __init__(self, field: Any) -> None:
        if not hasattr(field, "build_direct_children_map"):
            raise TypeError(
                "ContinuousSectionField must expose "
                "build_direct_children_map(z)"
            )
        if not hasattr(field, "s0") or not hasattr(field.s0, "z"):
            raise TypeError("ContinuousSectionField must expose s0.z")
        if not hasattr(field.s0, "polygons"):
            raise TypeError("ContinuousSectionField must expose s0.polygons")

        polygon_count = len(field.s0.polygons)
        raw_map = field.build_direct_children_map(float(field.s0.z))
        if not isinstance(raw_map, dict):
            raise TypeError("build_direct_children_map(z) must return a dict")

        # CSF topology is zero based.  CUF domain identifiers are one based.
        # The conversion is performed once and kept entirely in this class.
        children_by_domain_id = {
            domain_id: () for domain_id in range(1, polygon_count + 1)
        }
        normalized = {}
        for parent_index, child_indices in raw_map.items():
            if not isinstance(parent_index, int):
                raise TypeError("CSF parent polygon index must be an integer")
            if not 0 <= parent_index < polygon_count:
                raise ValueError(
                    f"CSF parent polygon index {parent_index} is out of range"
                )
            converted_children = []
            for child_index in child_indices:
                if not isinstance(child_index, int):
                    raise TypeError(
                        "CSF direct-child polygon index must be an integer"
                    )
                if not 0 <= child_index < polygon_count:
                    raise ValueError(
                        f"CSF child polygon index {child_index} is out of range"
                    )
                converted_children.append(child_index + 1)
            normalized[parent_index + 1] = tuple(converted_children)
        children_by_domain_id.update(normalized)

        self._polygon_count = int(polygon_count)
        self._children_by_domain_id = children_by_domain_id

    @staticmethod
    def _vertices(polygon) -> Tuple[Tuple[float, float], ...]:
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
        if len(vertices) < 3:
            raise ValueError("CSF polygon must contain at least three vertices")
        return tuple(vertices)

    def domains(self, section) -> Tuple[PolygonDomain, ...]:
        """Return net-domain descriptors for one already sampled section."""
        if not hasattr(section, "polygons"):
            raise TypeError("CSF section has no polygons attribute")
        polygons = tuple(section.polygons)
        if len(polygons) != self._polygon_count:
            raise ValueError(
                "sampled CSF section changed polygon count; stable index "
                "topology cannot be applied"
            )

        vertices_by_domain_id = {
            index + 1: self._vertices(polygon)
            for index, polygon in enumerate(polygons)
        }
        result = []
        for index, polygon in enumerate(polygons):
            domain_id = index + 1
            weightabs_raw = getattr(polygon, "weightabs", None)
            if weightabs_raw is None:
                raise ValueError(
                    f"CSF domain {domain_id} has no absolute weightabs"
                )
            weightabs = float(weightabs_raw)
            if not np.isfinite(weightabs) or weightabs < 0.0:
                raise ValueError(
                    f"CSF domain {domain_id} has invalid weightabs "
                    f"{weightabs}"
                )

            # Only direct children are excluded.  A deeper descendant is
            # already contained in its direct parent and must not be
            # subtracted twice from the current domain.
            excluded_vertices = tuple(
                vertices_by_domain_id[child_domain_id]
                for child_domain_id in self._children_by_domain_id[domain_id]
            )
            result.append(
                PolygonDomain(
                    domain_id=domain_id,
                    vertices=vertices_by_domain_id[domain_id],
                    name=getattr(polygon, "name", None),
                    weight=(
                        float(polygon.weight)
                        if getattr(polygon, "weight", None) is not None
                        else None
                    ),
                    weightabs=weightabs,
                    excluded_vertices=excluded_vertices,
                )
            )
        return tuple(result)


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
        if not hasattr(field, "inspect_section_entities"):
            raise TypeError("field must expose inspect_section_entities(z)")
        self._field = field
        self._domain_slicer = SectionDomainSlicer(field)

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

        return self._domain_slicer.domains(section)

    def inspect_section_entities(self, x: float):
        """Delegate stable polygon metadata to the public CSF inspection API.

        ``ContinuousSectionField.inspect_section_entities`` is authoritative
        for the zero-based polygon ``idx`` and the declared ``s0_name`` and
        ``s1_name`` labels.  Exposing the same operation through the section
        provider lets load adapters resolve a user-facing S0 name without
        accessing ``_field`` or interpreting interpolated runtime labels.
        """

        if not np.isfinite(x):
            raise ValueError("longitudinal coordinate x must be finite")
        return self._field.inspect_section_entities(float(x))
