# Version: CSF-CUF net homogeneous domain slicer v19 - 2026-08-27
"""Experimental closed-form transverse integration used only for comparison."""

from __future__ import annotations

import math
import time

import numpy as np


class ClosedFormSectionalComparator:
    """Evaluate polynomial CUF sectional families from polygon moments."""

    def __init__(self, section_provider, constitutive_provider, basis) -> None:
        self.section_provider = section_provider
        self.constitutive_provider = constitutive_provider
        self.basis = basis
        self.elapsed = 0.0
        self.calls = 0
        self._moment_cache = {}
        self._factor_cache = {}
        self._product_plan_cache = {}
        self._formal_moment_plan_cache = {}

    def _formal_moment_plan(self, p: int, q: int):
        key = (int(p), int(q))
        plan = self._formal_moment_plan_cache.get(key)
        if plan is None:
            plan = tuple(
                (
                    i,
                    j,
                    math.comb(p + 1, i)
                    * math.comb(q, j)
                    / (float(p + 1) * float(i + j + 1)),
                )
                for i in range(p + 2)
                for j in range(q + 1)
            )
            self._formal_moment_plan_cache[key] = plan
        return plan

    def _polygon_moment(self, vertices, p: int, q: int) -> float:
        """Return integral y**p z**q dA from the polygon boundary."""
        vertices = tuple((float(y), float(z)) for y, z in vertices)
        twice_area = sum(
            y0 * z1 - y1 * z0
            for (y0, z0), (y1, z1) in zip(
                vertices,
                vertices[1:] + vertices[:1],
            )
        )
        orientation = 1.0 if twice_area >= 0.0 else -1.0
        total = 0.0

        for (y0, z0), (y1, z1) in zip(
            vertices,
            vertices[1:] + vertices[:1],
        ):
            dy = y1 - y0
            dz = z1 - z0
            y0_powers = [y0 ** degree for degree in range(p + 2)]
            dy_powers = [dy ** degree for degree in range(p + 2)]
            z0_powers = [z0 ** degree for degree in range(q + 1)]
            dz_powers = [dz ** degree for degree in range(q + 1)]
            edge = sum(
                coefficient
                * y0_powers[p + 1 - i]
                * dy_powers[i]
                * z0_powers[q - j]
                * dz_powers[j]
                for i, j, coefficient in self._formal_moment_plan(p, q)
            )
            total += dz * edge

        return float(orientation * total)

    def _factor_data(self, derivative):
        cached = self._factor_cache.get(derivative)
        if cached is not None:
            return cached
        y_scale, z_scale = self.basis.scales
        exponents = [self.basis.exponents(tau) for tau in range(1, self.basis.size + 1)]
        py = np.empty(self.basis.size, dtype=np.intp)
        pz = np.empty(self.basis.size, dtype=np.intp)
        coefficient = np.empty(self.basis.size, dtype=float)

        for index, (ey, ez) in enumerate(exponents):
            if derivative is None:
                py[index], pz[index] = ey, ez
                coefficient[index] = 1.0 / ((y_scale ** ey) * (z_scale ** ez))
            elif derivative == "y":
                py[index], pz[index] = max(ey - 1, 0), ez
                coefficient[index] = (
                    0.0 if ey == 0 else ey / ((y_scale ** ey) * (z_scale ** ez))
                )
            else:
                py[index], pz[index] = ey, max(ez - 1, 0)
                coefficient[index] = (
                    0.0 if ez == 0 else ez / ((y_scale ** ey) * (z_scale ** ez))
                )

        result = (py, pz, coefficient)
        self._factor_cache[derivative] = result
        return result

    def _product_plan(self, test_derivative, trial_derivative):
        key = (test_derivative, trial_derivative)
        plan = self._product_plan_cache.get(key)
        if plan is not None:
            return plan
        py_t, pz_t, a_t = self._factor_data(test_derivative)
        py_s, pz_s, a_s = self._factor_data(trial_derivative)
        exponent_y = py_t[:, None] + py_s[None, :]
        exponent_z = pz_t[:, None] + pz_s[None, :]
        coefficient = a_t[:, None] * a_s[None, :]
        required = tuple(
            sorted(
                set(
                    zip(
                        exponent_y.ravel().tolist(),
                        exponent_z.ravel().tolist(),
                    )
                )
            )
        )
        plan = (exponent_y, exponent_z, coefficient, required)
        self._product_plan_cache[key] = plan
        return plan

    def _domain_moments(self, x: float, required_moments):
        required_moments = tuple(required_moments)
        key = (float(x), required_moments)
        cached = self._moment_cache.get(key)
        if cached is not None:
            return cached

        domains = tuple(self.section_provider.domains(float(x)))
        max_py = max(p for p, _ in required_moments)
        max_pz = max(q for _, q in required_moments)
        raw = []
        for domain in domains:
            table = np.zeros((max_py + 1, max_pz + 1), dtype=float)
            for p, q in required_moments:
                table[p, q] = self._polygon_moment(domain.vertices, p, q)
            raw.append(table)

        occupied = []
        for domain, table in zip(domains, raw):
            current = table.copy()
            # Reuse the direct-child geometries already attached by the
            # SectionDomainSlicer.  The comparator must never ask CSF to build
            # the topology a second time.
            for child_vertices in domain.excluded_vertices:
                for p, q in required_moments:
                    current[p, q] -= self._polygon_moment(
                        child_vertices, p, q
                    )
            occupied.append(current)

        result = (domains, tuple(occupied))
        self._moment_cache[key] = result
        return result

    def compute(self, *, x: float, family_keys):
        started = time.perf_counter()
        family_keys = tuple(family_keys)
        product_plans = {}
        required_moments = set()
        for _, test_derivative, trial_derivative, _, _ in family_keys:
            pair = (test_derivative, trial_derivative)
            plan = self._product_plan(*pair)
            product_plans[pair] = plan
            required_moments.update(plan[3])

        required_moments = tuple(sorted(required_moments))
        domains, moments_by_domain = self._domain_moments(x, required_moments)
        totals = {key: None for key in family_keys}

        for domain_index, (domain, moments) in enumerate(zip(domains, moments_by_domain)):
            if domain.weightabs is not None and float(domain.weightabs) == 0.0:
                continue
            y0, z0 = domain.vertices[0]
            C = np.asarray(
                self.constitutive_provider.matrix(
                    x=float(x),
                    domain_id=domain_index + 1,
                    y=float(y0),
                    z=float(z0),
                ),
                dtype=float,
            )

            for family_key in family_keys:
                _, test_derivative, trial_derivative, m, n = family_key
                Cmn = float(C[int(m) - 1, int(n) - 1])
                if Cmn == 0.0:
                    continue
                exponent_y, exponent_z, coefficient, _ = product_plans[
                    (test_derivative, trial_derivative)
                ]
                matrix = (
                    Cmn
                    * coefficient
                    * moments[exponent_y, exponent_z]
                )
                if totals[family_key] is None:
                    totals[family_key] = matrix
                else:
                    totals[family_key] += matrix

        self.elapsed += time.perf_counter() - started
        self.calls += 1
        return totals
