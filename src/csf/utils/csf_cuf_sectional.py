"""
Generalized sectional coefficients J(x) for the CSF-CUF bridge.

This module is the sectional coupling layer:

    Omega^k(x), C^k(x,y,z), F_tau(y,z)
        -> J^{mn,k}_{tau,phi s,xi}(x)
        -> J^{mn}_{tau,phi s,xi}(x)

It contains only SectionalCoefficientProvider.  Geometry, constitutive law,
CUF basis and numerical integration are injected dependencies; no
longitudinal discretization, load, boundary condition or benchmark-specific
assumption is introduced here.
"""

from typing import Tuple

import numpy as np

from .csf_cuf_basis import CUFBasis
from .csf_cuf_integration import (
    AdaptivePolygonIntegrator,
    SectionIntegrator,
)
from .csf_cuf_material import ConstitutiveProvider
from .csf_cuf_section import SectionProvider


# =============================================================================
# Generalized sectional coefficient J
# =============================================================================

class SectionalCoefficientProvider:
    """
    Evaluate generalized CSF-CUF sectional coefficients.

    Domain contribution:

        J_{tau,phi s,xi}^{mn,k}(x)
        =
        integral_{Omega^k(x)}
            C_mn^k(x,y,z)
            F_{tau,phi}(y,z)
            F_{s,xi}(y,z)
        dOmega

    ``test_derivative`` and ``trial_derivative`` may be:
        None  -> no transverse derivative
        "y"   -> derivative with respect to y
        "z"   -> derivative with respect to z

    Performance
    -----------
    Longitudinal FE assembly requests the same sectional coefficient many
    times at the same quadrature coordinate: once for different longitudinal
    matrix entries and sometimes through different assembly paths.

    The provider therefore memoizes both complete J values and individual
    domain contributions. The cache key contains the complete physical
    request, including the exact longitudinal coordinate ``x``. Consequently
    no assumption of prismatic geometry or constant material is introduced:

        Omega^k = Omega^k(x)
        C^k     = C^k(x,y,z)

    remain fully supported.

    Providers are treated as immutable dependencies during one analysis. If a
    caller deliberately mutates the section, constitutive law, basis, or
    integration backend after construction, ``clear_cache()`` must be called
    before requesting new coefficients.
    """

    def __init__(
        self,
        section_provider: SectionProvider,
        constitutive_provider: ConstitutiveProvider,
        basis: CUFBasis,
        *,
        integrator: SectionIntegrator | None = None,
        cache_enabled: bool = True,
    ) -> None:
        self.section_provider = section_provider
        self.constitutive_provider = constitutive_provider
        self.basis = basis
        self.integrator = integrator or AdaptivePolygonIntegrator()

        self.cache_enabled = bool(cache_enabled)

        self._J_cache = {}
        self._J_domain_cache = {}

        self._J_hits = 0
        self._J_misses = 0
        self._J_domain_hits = 0
        self._J_domain_misses = 0
        self._J_batch_calls = 0
        self._J_batch_integrations = 0

    @staticmethod
    def _validate_derivative(
        derivative: str | None,
    ) -> None:
        if derivative not in (None, "y", "z"):
            raise ValueError(
                "derivative selector must be None, 'y', or 'z'"
            )

    @classmethod
    def _J_key(
        cls,
        *,
        x: float,
        tau: int,
        test_derivative: str | None,
        s: int,
        trial_derivative: str | None,
        m: int,
        n: int,
    ):
        cls._validate_derivative(test_derivative)
        cls._validate_derivative(trial_derivative)

        x = float(x)

        if not np.isfinite(x):
            raise ValueError(
                "longitudinal coordinate x must be finite"
            )

        return (
            x,
            int(tau),
            test_derivative,
            int(s),
            trial_derivative,
            int(m),
            int(n),
        )

    @classmethod
    def _J_domain_key(
        cls,
        *,
        x: float,
        domain_id: int,
        tau: int,
        test_derivative: str | None,
        s: int,
        trial_derivative: str | None,
        m: int,
        n: int,
    ):
        return (
            int(domain_id),
            *cls._J_key(
                x=x,
                tau=tau,
                test_derivative=test_derivative,
                s=s,
                trial_derivative=trial_derivative,
                m=m,
                n=n,
            ),
        )

    def clear_cache(self) -> None:
        """
        Remove all memoized sectional coefficients and reset statistics.
        """

        self._J_cache.clear()
        self._J_domain_cache.clear()

        self._J_hits = 0
        self._J_misses = 0
        self._J_domain_hits = 0
        self._J_domain_misses = 0
        self._J_batch_calls = 0
        self._J_batch_integrations = 0

    def cache_info(self) -> dict:
        """
        Return cache statistics without exposing internal cache objects.
        """

        return {
            "enabled": self.cache_enabled,
            "J_entries": len(self._J_cache),
            "J_hits": self._J_hits,
            "J_misses": self._J_misses,
            "J_domain_entries": len(self._J_domain_cache),
            "J_domain_hits": self._J_domain_hits,
            "J_domain_misses": self._J_domain_misses,
            "J_batch_calls": self._J_batch_calls,
            "J_batch_integrations": self._J_batch_integrations,
        }

    def J_domain(
        self,
        *,
        x: float,
        domain_id: int,
        tau: int,
        test_derivative: str | None,
        s: int,
        trial_derivative: str | None,
        m: int,
        n: int,
    ) -> float:
        """Return one domain contribution J^{mn,k}_{tau,phi s,xi}(x)."""

        key = self._J_domain_key(
            x=x,
            domain_id=domain_id,
            tau=tau,
            test_derivative=test_derivative,
            s=s,
            trial_derivative=trial_derivative,
            m=m,
            n=n,
        )

        if self.cache_enabled and key in self._J_domain_cache:
            self._J_domain_hits += 1
            return self._J_domain_cache[key]

        self._J_domain_misses += 1

        domain = self.section_provider.domain(
            x=float(x),
            domain_id=int(domain_id),
        )

        def integrand(y: float, z: float) -> float:
            Cmn = self.constitutive_provider.coefficient(
                x=float(x),
                domain_id=int(domain_id),
                m=int(m),
                n=int(n),
                y=y,
                z=z,
            )

            Ftau = self._basis_factor(
                tau=int(tau),
                derivative=test_derivative,
                y=y,
                z=z,
            )

            Fs = self._basis_factor(
                tau=int(s),
                derivative=trial_derivative,
                y=y,
                z=z,
            )

            return Cmn * Ftau * Fs

        value = float(
            self.integrator.integrate(
                domain,
                integrand,
            )
        )

        if self.cache_enabled:
            self._J_domain_cache[key] = value

        return value

    def J(
        self,
        *,
        x: float,
        tau: int,
        test_derivative: str | None,
        s: int,
        trial_derivative: str | None,
        m: int,
        n: int,
    ) -> float:
        """Return the assembled coefficient summed over all CSF domains."""

        key = self._J_key(
            x=x,
            tau=tau,
            test_derivative=test_derivative,
            s=s,
            trial_derivative=trial_derivative,
            m=m,
            n=n,
        )

        if self.cache_enabled and key in self._J_cache:
            self._J_hits += 1
            return self._J_cache[key]

        self._J_misses += 1

        total = 0.0

        for domain_id in range(
            1,
            self.section_provider.number_of_domains(float(x)) + 1,
        ):
            total += self.J_domain(
                x=float(x),
                domain_id=domain_id,
                tau=int(tau),
                test_derivative=test_derivative,
                s=int(s),
                trial_derivative=trial_derivative,
                m=int(m),
                n=int(n),
            )

        value = float(total)

        if self.cache_enabled:
            self._J_cache[key] = value

        return value

    @staticmethod
    def _signature_fields(signature):
        """
        Normalize one J signature object/tuple.

        The normal object is ``JSignature`` but the provider is defined before
        that dataclass in this module, so the API intentionally uses a loose
        structural contract.
        """

        names = (
            "tau",
            "test_derivative",
            "s",
            "trial_derivative",
            "m",
            "n",
        )

        if all(hasattr(signature, name) for name in names):
            return tuple(
                getattr(signature, name)
                for name in names
            )

        if (
            isinstance(signature, tuple)
            and len(signature) == 6
        ):
            return signature

        raise TypeError(
            "each batch signature must expose "
            "tau, test_derivative, s, trial_derivative, m, n"
        )

    def J_batch(
        self,
        *,
        x: float,
        signatures,
    ) -> Tuple[float, ...]:
        """
        Evaluate many generalized sectional coefficients in one polygon pass.

        Values are returned in exactly the same order as ``signatures``.

        At each transverse quadrature point the constitutive matrix and all
        required basis values/derivatives are evaluated once, then reused for
        every requested J coefficient.
        """

        signatures = tuple(signatures)

        if not signatures:
            return tuple()

        self._J_batch_calls += 1

        normalized = []
        keys = []

        for signature in signatures:
            (
                tau,
                test_derivative,
                s,
                trial_derivative,
                m,
                n,
            ) = self._signature_fields(signature)

            key = self._J_key(
                x=x,
                tau=tau,
                test_derivative=test_derivative,
                s=s,
                trial_derivative=trial_derivative,
                m=m,
                n=n,
            )

            normalized.append(
                (
                    int(tau),
                    test_derivative,
                    int(s),
                    trial_derivative,
                    int(m),
                    int(n),
                )
            )
            keys.append(key)

        missing_indices = []
        output = np.zeros(len(signatures), dtype=float)

        for index, key in enumerate(keys):
            if self.cache_enabled and key in self._J_cache:
                self._J_hits += 1
                output[index] = self._J_cache[key]
            else:
                self._J_misses += 1
                missing_indices.append(index)

        if not missing_indices:
            return tuple(float(value) for value in output)

        # De-duplicate missing signatures before numerical integration.
        unique_missing = []
        unique_key_to_position = {}

        for index in missing_indices:
            key = keys[index]

            if key in unique_key_to_position:
                continue

            unique_key_to_position[key] = len(unique_missing)
            unique_missing.append(index)

        domain_count = self.section_provider.number_of_domains(
            float(x)
        )

        totals = np.zeros(
            len(unique_missing),
            dtype=float,
        )

        required_basis_factors = set()

        for index in unique_missing:
            tau, d_tau, s, d_s, _, _ = normalized[index]
            required_basis_factors.add((tau, d_tau))
            required_basis_factors.add((s, d_s))

        for domain_id in range(1, domain_count + 1):
            domain = self.section_provider.domain(
                x=float(x),
                domain_id=domain_id,
            )

            def vector_integrand(y: float, z: float) -> np.ndarray:
                C = np.asarray(
                    self.constitutive_provider.matrix(
                        x=float(x),
                        domain_id=domain_id,
                        y=float(y),
                        z=float(z),
                    ),
                    dtype=float,
                )

                if C.shape != (6, 6):
                    raise ValueError(
                        "constitutive provider must return a 6-by-6 matrix"
                    )

                factors = {}

                for tau_value, derivative in required_basis_factors:
                    factors[(tau_value, derivative)] = self._basis_factor(
                        tau=tau_value,
                        derivative=derivative,
                        y=float(y),
                        z=float(z),
                    )

                values = np.empty(
                    len(unique_missing),
                    dtype=float,
                )

                for local_index, request_index in enumerate(unique_missing):
                    (
                        tau,
                        d_tau,
                        s,
                        d_s,
                        m,
                        n,
                    ) = normalized[request_index]

                    values[local_index] = (
                        C[m - 1, n - 1]
                        * factors[(tau, d_tau)]
                        * factors[(s, d_s)]
                    )

                return values

            if not hasattr(self.integrator, "integrate_vector"):
                # Generic compatibility fallback. This path remains correct
                # for custom scalar-only SectionIntegrator implementations.
                for local_index, request_index in enumerate(unique_missing):
                    (
                        tau,
                        d_tau,
                        s,
                        d_s,
                        m,
                        n,
                    ) = normalized[request_index]

                    totals[local_index] += self.J_domain(
                        x=float(x),
                        domain_id=domain_id,
                        tau=tau,
                        test_derivative=d_tau,
                        s=s,
                        trial_derivative=d_s,
                        m=m,
                        n=n,
                    )

                continue

            self._J_batch_integrations += 1

            totals += self.integrator.integrate_vector(
                domain,
                vector_integrand,
                size=len(unique_missing),
            )

        # Populate all duplicate request positions and the scalar cache.
        for request_index in missing_indices:
            key = keys[request_index]
            unique_position = unique_key_to_position[key]
            value = float(totals[unique_position])

            output[request_index] = value

            if self.cache_enabled:
                self._J_cache[key] = value

        return tuple(float(value) for value in output)

    def _basis_factor(
        self,
        *,
        tau: int,
        derivative: str | None,
        y: float,
        z: float,
    ) -> float:
        if derivative is None:
            return self.basis.value(tau, y, z)

        if derivative in ("y", "z"):
            return self.basis.derivative(
                tau=tau,
                direction=derivative,
                y=y,
                z=z,
            )

        raise ValueError(
            "derivative selector must be None, 'y', or 'z'"
        )


