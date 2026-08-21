from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from csf.io.csf_issues import CSFIssues
from csf.io.csf_reader import CSFReader
from csf.utils.csf_cuf import CSFSectionProvider, IsotropicEGConstitutive


@dataclass(frozen=True)
class CSFDomainState:
    domain_id: int
    name: str
    E: float
    G: float
    poisson: float | None


class CSFCUFModelBridge:
    """
    Boundary object between the CSF physical model and the CUF solver.

    CSF owns the section geometry and the per-polygon constitutive carriers.
    CUF receives only a generic SectionProvider and a generic
    ConstitutiveProvider. No E, G, Poisson ratio, polygon name or section shape
    is hard-coded in the solver.

    Contract used by this startup project:
        polygon.weight       -> E-like absolute normal-stiffness carrier
        polygon.shear_weight -> G-like absolute shear-stiffness carrier

    The CSF shear law ``iso(nu)`` is one valid way to create shear_weight, but
    the bridge does not impose that relation: E and G are read independently
    from the evaluated CSF polygon state.
    """

    def __init__(self, field) -> None:
        if field is None:
            raise ValueError("field must not be None")
        self.field = field
        self.section_provider = CSFSectionProvider(field)
        self._section_cache = {}
        self._state_cache = {}
        self.constitutive_provider = IsotropicEGConstitutive(
            E_field=self._E_field,
            G_field=self._G_field,
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CSFCUFModelBridge":
        result = CSFReader().read_file(str(Path(path)))
        if not result.ok or result.field is None:
            raise RuntimeError(CSFIssues.format_report(result.issues))
        bridge = cls(result.field)
        bridge.validate_material_state()
        return bridge

    def longitudinal_domain(self) -> tuple[float, float]:
        return tuple(map(float, self.section_provider.longitudinal_domain()))

    def _evaluated_section(self, x: float):
        x = float(x)
        if x not in self._section_cache:
            section = self.field.section(x)
            if section is None or not hasattr(section, "polygons"):
                raise RuntimeError(f"CSF returned no polygonal section at x={x}")
            self._section_cache[x] = section
        return self._section_cache[x]

    def _raw_polygon(self, x: float, domain_id: int):
        section = self._evaluated_section(float(x))
        domain_id = int(domain_id)
        if not 1 <= domain_id <= len(section.polygons):
            raise IndexError(
                f"domain_id must be in 1..{len(section.polygons)}, got {domain_id}"
            )
        return section.polygons[domain_id - 1]

    def domain_state(self, x: float, domain_id: int) -> CSFDomainState:
        key = (float(x), int(domain_id))
        if key in self._state_cache:
            return self._state_cache[key]

        polygon = self._raw_polygon(*key)
        E = float(polygon.weight)
        G = float(polygon.shear_weight)
        poisson_raw = getattr(polygon, "poisson", None)
        poisson = None if poisson_raw is None else float(poisson_raw)

        if not (np.isfinite(E) and E > 0.0):
            raise ValueError(
                f"CSF domain {domain_id} at x={x} has invalid E-like weight {E}"
            )
        if not (np.isfinite(G) and G > 0.0):
            raise ValueError(
                f"CSF domain {domain_id} at x={x} has invalid G-like shear_weight {G}"
            )
        if poisson is not None and not np.isfinite(poisson):
            poisson = None

        state = CSFDomainState(
            domain_id=int(domain_id),
            name=str(getattr(polygon, "name", f"domain_{domain_id}")),
            E=E,
            G=G,
            poisson=poisson,
        )
        self._state_cache[key] = state
        return state

    def _E_field(self, x, domain_id, y, z) -> float:
        return self.domain_state(float(x), int(domain_id)).E

    def _G_field(self, x, domain_id, y, z) -> float:
        return self.domain_state(float(x), int(domain_id)).G

    def validate_material_state(self) -> None:
        x0, x1 = self.longitudinal_domain()
        for x in (x0, 0.5 * (x0 + x1), x1):
            count = self.section_provider.number_of_domains(x)
            if count < 1:
                raise ValueError(f"CSF section at x={x} contains no domains")
            for domain_id in range(1, count + 1):
                self.domain_state(x, domain_id)
