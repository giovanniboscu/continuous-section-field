# Version: CSF-CUF sectional geometry/integration separation v16 - 2026-08-27
# OPT-02 MATRIX SECTIONAL INTEGRATION
"""
Generalized sectional coefficients J(x) for the CSF-CUF bridge.

This module is the public transverse-integration layer:

    Omega^k(x), C^k(x,y,z), F_tau(y,z)
        -> J^{mn,k}_{tau,phi s,xi}(x)
        -> J^{mn}_{tau,phi s,xi}(x)

It contains only SectionalCoefficientProvider.  Real CSF geometry and the
constitutive lookup are hidden behind SectionalGeometryProvider; this module
receives only quadrature-ready numerical data.  No longitudinal
discretization, load, boundary condition or benchmark-specific assumption is
introduced here.
"""

from typing import Tuple
from pathlib import Path
from datetime import datetime, timezone
import os

import numpy as np

from .basis import CUFBasis
from .integration import (
    AdaptivePolygonIntegrator,
    SectionIntegrator,
)
from .sectional_geometry import SectionalGeometryProvider


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
    caller deliberately mutates the sectional geometry provider, basis, or
    integration backend after construction, ``clear_cache()`` must be called
    before requesting new coefficients.
    """

    def __init__(
        self,
        geometry_provider: SectionalGeometryProvider,
        basis: CUFBasis,
        *,
        integrator: SectionIntegrator | None = None,
        cache_enabled: bool = True,
    ) -> None:
        if not isinstance(geometry_provider, SectionalGeometryProvider):
            raise TypeError(
                "geometry_provider must be a SectionalGeometryProvider"
            )
        self.geometry = geometry_provider
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

        # OPT-01: cache x-independent request/factor plans.  The plans contain
        # only CUF indices, derivative selectors and constitutive matrix indices;
        # no sectional geometry or material value is cached here.
        self._batch_factor_plan_cache = {}

        # OPT-02: cache complete M x M sectional coefficient families.
        # A family is identified by (x, test derivative, trial derivative, m, n)
        # and contains every ordered CUF pair (tau, s) at once.
        self._J_matrix_family_cache = {}
        self._matrix_basis_plan_cache = {}
        self._J_matrix_family_hits = 0
        self._J_matrix_family_misses = 0
        self._J_matrix_family_integrations = 0

        # Diagnostic v3: optional Gauss-order stability check for the actual
        # sectional J families used by the CUF core.  The diagnostic is purely
        # observational: it never replaces, rescales, filters or otherwise
        # modifies the coefficient matrices used by the normal analysis.
        self._gauss_diagnostic_enabled = self._env_flag(
            "CSF_CUF_J_GAUSS_DIAGNOSTIC"
        )
        self._gauss_diagnostic_orders = self._parse_gauss_diagnostic_orders()
        self._gauss_diagnostic_report_path = self._gauss_diagnostic_report()
        self._gauss_diagnostic_header_written = False

        # Upstream diagnostic: inspect the transverse basis on the actual CSF
        # integration domains before any constitutive nucleus, element matrix,
        # global assembly, constraint, or KKT operation is performed.
        self._basis_diagnostic_enabled = self._env_flag(
            "CSF_CUF_UPSTREAM_BASIS_DIAGNOSTIC"
        )
        self._basis_diagnostic_seen_x = set()
        self._basis_diagnostic_report_path = Path(
            os.environ.get(
                "CSF_CUF_UPSTREAM_BASIS_REPORT",
                str(
                    Path.cwd()
                    / "diagnostics"
                    / "upstream_basis_quality_v2.tsv"
                ),
            )
        ).expanduser()

        if self._basis_diagnostic_enabled:
            print(
                "[upstream-basis] enabled - analysis occurs before "
                "the CUF nucleus and element assembly; "
                f"report={self._basis_diagnostic_report_path}",
                flush=True,
            )

        if self._gauss_diagnostic_enabled:
            if not hasattr(self.integrator, "quadrature_points"):
                raise TypeError(
                    "J Gauss diagnostic requires an integrator exposing "
                    "quadrature_points(domain)"
                )
            if not hasattr(self.integrator, "order"):
                raise TypeError(
                    "J Gauss diagnostic requires an integrator exposing "
                    "its quadrature order"
                )

            print(
                "[J-diagnostic] sectional Gauss stability enabled: "
                f"base_order={int(self.integrator.order)} "
                f"test_orders={self._gauss_diagnostic_orders} "
                f"report={self._gauss_diagnostic_report_path}",
                flush=True,
            )

    @staticmethod
    def _env_flag(name: str) -> bool:
        value = os.environ.get(name, "").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _parse_gauss_diagnostic_orders(self) -> tuple[int, ...]:
        if not self._gauss_diagnostic_enabled:
            return tuple()

        raw = os.environ.get(
            "CSF_CUF_J_GAUSS_ORDERS",
            "36,48",
        )

        orders = []
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            order = int(item)
            if order < 2:
                raise ValueError(
                    "CSF_CUF_J_GAUSS_ORDERS values must be integers >= 2"
                )
            if order not in orders:
                orders.append(order)

        if not orders:
            raise ValueError(
                "CSF_CUF_J_GAUSS_ORDERS must contain at least one order"
            )

        return tuple(orders)

    def _basis_exponents_text(self, tau_indices) -> str:
        items = []
        for tau_index in tau_indices:
            tau = int(tau_index) + 1
            if hasattr(self.basis, "exponents"):
                try:
                    exponent = tuple(
                        int(value)
                        for value in self.basis.exponents(tau)
                    )
                    items.append(f"tau{tau}:{exponent}")
                    continue
                except (TypeError, ValueError, IndexError):
                    pass
            items.append(f"tau{tau}")
        return ",".join(items)

    def _analyse_basis_samples(self, *, x: float, label: str, blocks) -> None:
        """Inspect weighted basis samples directly, without forming ``B.T @ W @ B``.

        Forming a Gram matrix squares the condition number and can create an
        artificial numerical rank loss.  The diagnostic instead stacks
        ``sqrt(W) @ B`` from every active CSF domain, normalizes its columns,
        and computes singular values directly.
        """
        if not blocks:
            samples = np.empty((0, int(self.basis.size)), dtype=float)
        else:
            samples = np.vstack(blocks)

        column_norms = np.linalg.norm(samples, axis=0)
        # Derivative families contain exact zero columns (for example d/dy of
        # a function independent of y).  Exclude exact zeros only; do not use
        # a tolerance expressed in the unrelated scale of a Gram matrix.
        active = np.flatnonzero(column_norms > 0.0)

        if active.size == 0:
            rank = 0
            condition = float("inf")
            sigma_min = 0.0
            sigma_max = 0.0
            dominant_text = "none"
        else:
            normalized = (
                samples[:, active]
                / column_norms[active][None, :]
            )
            _, singular_values, right_vectors = np.linalg.svd(
                normalized,
                full_matrices=False,
            )
            sigma_max = (
                float(singular_values[0])
                if singular_values.size
                else 0.0
            )
            sigma_min = (
                float(singular_values[-1])
                if singular_values.size
                else 0.0
            )
            rank_tolerance = (
                max(1, *normalized.shape)
                * np.finfo(float).eps
                * sigma_max
            )
            rank = int(np.count_nonzero(singular_values > rank_tolerance))
            condition = (
                float(sigma_max / sigma_min)
                if sigma_min > 0.0
                else float("inf")
            )

            smallest_vector = np.abs(right_vectors[-1, :])
            dominant_local = np.argsort(smallest_vector)[-5:][::-1]
            dominant_text = self._basis_exponents_text(
                active[dominant_local]
            )

        independent = rank == int(active.size)
        print(
            "[upstream-basis] "
            f"x={float(x):.12g} matrix={label} "
            f"active={active.size} rank={rank} "
            f"status={'FULL-RANK' if independent else 'RANK-LOSS'} "
            f"normalized_condition={condition:.6e} "
            f"sigma_min={sigma_min:.6e} sigma_max={sigma_max:.6e} "
            f"weakest_direction={dominant_text}",
            flush=True,
        )

        path = self._basis_diagnostic_report_path
        path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", encoding="utf-8") as stream:
            if write_header:
                stream.write(
                    "timestamp_utc\tbasis\torder\tx\tmatrix\tactive\trank\t"
                    "full_rank\tnormalized_condition\tsigma_min\t"
                    "sigma_max\tweakest_direction\n"
                )
            stream.write(
                f"{datetime.now(timezone.utc).isoformat()}\t"
                f"{type(self.basis).__name__}\t"
                f"{int(self.basis.order)}\t{float(x):.17g}\t{label}\t"
                f"{int(active.size)}\t{rank}\t{str(independent).lower()}\t"
                f"{condition:.17g}\t{sigma_min:.17g}\t{sigma_max:.17g}\t"
                f"{dominant_text}\n"
            )

    def _run_upstream_basis_diagnostic(self, *, x: float, samples) -> None:
        x = float(x)
        if not self._basis_diagnostic_enabled or x in self._basis_diagnostic_seen_x:
            return
        self._basis_diagnostic_seen_x.add(x)

        for derivative, label in ((None, "G00"), ("y", "Gyy"), ("z", "Gzz")):
            self._analyse_basis_samples(
                x=x,
                label=label,
                blocks=samples[derivative],
            )

    def _gauss_diagnostic_report(self) -> Path:
        raw = os.environ.get("CSF_CUF_J_GAUSS_REPORT")
        if raw:
            return Path(raw).expanduser()
        return Path.cwd() / "diagnostics" / "j_gauss_stability.tsv"

    @staticmethod
    def _matrix_or_zeros(matrix, *, size: int) -> np.ndarray:
        if matrix is None:
            return np.zeros((size, size), dtype=float)
        values = np.asarray(matrix, dtype=float)
        if values.shape != (size, size):
            raise RuntimeError(
                "diagnostic J matrix family has an invalid shape"
            )
        return values

    def _diagnostic_J_matrix_families_with_integrator(
        self,
        *,
        x: float,
        family_keys,
        integrator,
    ):
        """Recompute J families with another quadrature order for diagnostics only."""
        x = float(x)
        family_keys = tuple(dict.fromkeys(family_keys))
        basis_size = int(self.basis.size)

        totals = {family_key: None for family_key in family_keys}

        required_derivatives = set()
        for family_key in family_keys:
            _, test_derivative, trial_derivative, _, _ = family_key
            required_derivatives.add(test_derivative)
            required_derivatives.add(trial_derivative)

        domain_count = self.geometry.number_of_domains(x)

        for domain_id in range(1, domain_count + 1):
            quadrature = self.geometry.quadrature_data(
                x=x,
                domain_id=domain_id,
                integrator=integrator,
            )
            y_points = quadrature.y_points
            z_points = quadrature.z_points
            quadrature_weights = quadrature.weights

            basis_by_derivative = {
                derivative: self._basis_matrix_at_points(
                    derivative=derivative,
                    y_points=y_points,
                    z_points=z_points,
                )
                for derivative in required_derivatives
            }

            constitutive_values = quadrature.constitutive_matrices

            for family_key in family_keys:
                (
                    _,
                    test_derivative,
                    trial_derivative,
                    m,
                    n,
                ) = family_key

                weighted_coefficient = (
                    quadrature_weights
                    * constitutive_values[:, int(m) - 1, int(n) - 1]
                )

                if not np.any(weighted_coefficient != 0.0):
                    continue

                B_test = basis_by_derivative[test_derivative]
                B_trial = basis_by_derivative[trial_derivative]

                contribution = (
                    B_test.T
                    @ (weighted_coefficient[:, None] * B_trial)
                )

                if contribution.shape != (basis_size, basis_size):
                    raise RuntimeError(
                        "diagnostic matrix sectional integration produced "
                        "an invalid shape"
                    )

                if totals[family_key] is None:
                    totals[family_key] = contribution
                else:
                    totals[family_key] += contribution

        return totals

    def _append_gauss_diagnostic_rows(
        self,
        *,
        x: float,
        reference_order: int,
        test_order: int,
        family_keys,
        reference_totals,
        test_totals,
    ) -> None:
        path = self._gauss_diagnostic_report_path
        path.parent.mkdir(parents=True, exist_ok=True)

        header = (
            "x\ttest_derivative\ttrial_derivative\tm\tn\t"
            "basis_size\tbase_gauss\ttest_gauss\t"
            "reference_fro\ttest_fro\tdiff_fro\trelative_fro\t"
            "reference_max_abs\ttest_max_abs\t"
            "max_abs_diff\tmax_abs_diff_over_family_scale\t"
            "max_abs_tau\tmax_abs_s\t"
            "reference_at_max_abs\ttest_at_max_abs\n"
        )

        mode = "a"
        if not self._gauss_diagnostic_header_written:
            mode = "w"

        basis_size = int(self.basis.size)

        with path.open(mode, encoding="utf-8") as handle:
            if not self._gauss_diagnostic_header_written:
                handle.write(header)
                self._gauss_diagnostic_header_written = True

            for family_key in family_keys:
                (
                    _,
                    test_derivative,
                    trial_derivative,
                    m,
                    n,
                ) = family_key

                reference = self._matrix_or_zeros(
                    reference_totals[family_key],
                    size=basis_size,
                )
                test = self._matrix_or_zeros(
                    test_totals[family_key],
                    size=basis_size,
                )

                difference = test - reference
                abs_difference = np.abs(difference)

                reference_fro = float(np.linalg.norm(reference))
                test_fro = float(np.linalg.norm(test))
                diff_fro = float(np.linalg.norm(difference))
                family_scale = max(reference_fro, test_fro)
                relative_fro = (
                    diff_fro / family_scale
                    if family_scale > 0.0
                    else 0.0
                )

                flat_abs = int(np.argmax(abs_difference))
                abs_tau0, abs_s0 = np.unravel_index(
                    flat_abs,
                    abs_difference.shape,
                )

                reference_max_abs = float(np.max(np.abs(reference)))
                test_max_abs = float(np.max(np.abs(test)))
                coefficient_family_scale = max(
                    reference_max_abs,
                    test_max_abs,
                )
                max_abs_diff = float(abs_difference[abs_tau0, abs_s0])
                max_abs_diff_over_family_scale = (
                    max_abs_diff / coefficient_family_scale
                    if coefficient_family_scale > 0.0
                    else 0.0
                )

                handle.write(
                    "\t".join(
                        (
                            f"{float(x):.17e}",
                            str(test_derivative),
                            str(trial_derivative),
                            str(int(m)),
                            str(int(n)),
                            str(basis_size),
                            str(int(reference_order)),
                            str(int(test_order)),
                            f"{reference_fro:.17e}",
                            f"{test_fro:.17e}",
                            f"{diff_fro:.17e}",
                            f"{relative_fro:.17e}",
                            f"{reference_max_abs:.17e}",
                            f"{test_max_abs:.17e}",
                            f"{max_abs_diff:.17e}",
                            f"{max_abs_diff_over_family_scale:.17e}",
                            str(abs_tau0 + 1),
                            str(abs_s0 + 1),
                            f"{reference[abs_tau0, abs_s0]:.17e}",
                            f"{test[abs_tau0, abs_s0]:.17e}",
                        )
                    )
                    + "\n"
                )

    def _run_gauss_stability_diagnostic(
        self,
        *,
        x: float,
        family_keys,
        reference_totals,
    ) -> None:
        if not self._gauss_diagnostic_enabled:
            return

        reference_order = int(self.integrator.order)
        integrator_type = type(self.integrator)

        for test_order in self._gauss_diagnostic_orders:
            if int(test_order) == reference_order:
                continue

            try:
                diagnostic_integrator = integrator_type(order=int(test_order))
            except TypeError as exc:
                raise TypeError(
                    "J Gauss diagnostic requires the active integrator type "
                    "to be constructible with order=<integer>"
                ) from exc

            test_totals = self._diagnostic_J_matrix_families_with_integrator(
                x=float(x),
                family_keys=family_keys,
                integrator=diagnostic_integrator,
            )

            self._append_gauss_diagnostic_rows(
                x=float(x),
                reference_order=reference_order,
                test_order=int(test_order),
                family_keys=family_keys,
                reference_totals=reference_totals,
                test_totals=test_totals,
            )

            print(
                "[J-diagnostic] "
                f"x={float(x):.9g} base={reference_order} "
                f"test={int(test_order)} families={len(tuple(family_keys))}",
                flush=True,
            )

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

        # OPT-01: cache x-independent request/factor plans.  The plans contain
        # only CUF indices, derivative selectors and constitutive matrix indices;
        # no sectional geometry or material value is cached here.
        self._batch_factor_plan_cache = {}
        self._J_matrix_family_cache.clear()
        self._matrix_basis_plan_cache.clear()
        self._J_matrix_family_hits = 0
        self._J_matrix_family_misses = 0
        self._J_matrix_family_integrations = 0

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
            "batch_factor_plans": len(self._batch_factor_plan_cache),
            "J_matrix_family_entries": len(self._J_matrix_family_cache),
            "J_matrix_family_hits": self._J_matrix_family_hits,
            "J_matrix_family_misses": self._J_matrix_family_misses,
            "J_matrix_family_integrations": self._J_matrix_family_integrations,
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

        def integrand(y: float, z: float, Cmn: float) -> float:
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
            self.geometry.integrate_scalar(
                x=float(x),
                domain_id=int(domain_id),
                integrator=self.integrator,
                integrand=integrand,
                m=int(m),
                n=int(n),
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
            self.geometry.number_of_domains(float(x)) + 1,
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

    @classmethod
    def _J_matrix_family_key(
        cls,
        *,
        x: float,
        test_derivative: str | None,
        trial_derivative: str | None,
        m: int,
        n: int,
    ):
        """Key for one complete M x M generalized-J family."""

        cls._validate_derivative(test_derivative)
        cls._validate_derivative(trial_derivative)

        x = float(x)
        if not np.isfinite(x):
            raise ValueError("longitudinal coordinate x must be finite")

        m = int(m)
        n = int(n)
        if not 1 <= m <= 6 or not 1 <= n <= 6:
            raise IndexError("constitutive indices m and n must be in 1..6")

        return (
            x,
            test_derivative,
            trial_derivative,
            m,
            n,
        )

    @staticmethod
    def _matrix_family_value(matrix, tau: int, s: int) -> float:
        """Read one (tau,s) value; ``None`` represents an identically zero family."""

        if matrix is None:
            return 0.0

        return float(matrix[int(tau) - 1, int(s) - 1])

    def _basis_matrix_at_points(
        self,
        *,
        derivative: str | None,
        y_points: np.ndarray,
        z_points: np.ndarray,
    ) -> np.ndarray:
        """
        Evaluate every transverse CUF function for one derivative selector.

        The result has shape (number of quadrature points, M).  For bases that
        expose ``compile_factors`` the complete factor plan is compiled once and
        reused.  Generic CUFBasis implementations retain a scalar fallback.
        """

        self._validate_derivative(derivative)

        y_points = np.asarray(y_points, dtype=float)
        z_points = np.asarray(z_points, dtype=float)

        if y_points.shape != z_points.shape or y_points.ndim != 1:
            raise ValueError("quadrature coordinate arrays must be one-dimensional and equal-sized")

        basis_size = int(self.basis.size)
        compiled = self._matrix_basis_plan_cache.get(derivative)

        if derivative not in self._matrix_basis_plan_cache:
            compiled = None

            if hasattr(self.basis, "compile_factors"):
                factor_keys = tuple(
                    (tau, derivative)
                    for tau in range(1, basis_size + 1)
                )
                compiled = self.basis.compile_factors(factor_keys)

                if not callable(compiled):
                    raise TypeError(
                        "basis.compile_factors(...) must return a callable"
                    )

            self._matrix_basis_plan_cache[derivative] = compiled

        if compiled is not None:
            values = np.empty(
                (y_points.size, basis_size),
                dtype=float,
            )

            for point_index, (y, z) in enumerate(
                zip(y_points, z_points)
            ):
                row = np.asarray(
                    compiled(float(y), float(z)),
                    dtype=float,
                )

                if row.shape != (basis_size,):
                    raise ValueError(
                        "compiled basis factor plan returned an invalid shape"
                    )

                values[point_index, :] = row

            return values

        values = np.empty(
            (y_points.size, basis_size),
            dtype=float,
        )

        for point_index, (y, z) in enumerate(
            zip(y_points, z_points)
        ):
            for tau in range(1, basis_size + 1):
                values[point_index, tau - 1] = self._basis_factor(
                    tau=tau,
                    derivative=derivative,
                    y=float(y),
                    z=float(z),
                )

        return values

    def _compute_J_matrix_families(
        self,
        *,
        x: float,
        family_keys,
    ) -> None:
        """
        Compute complete M x M J families in matrix form.

        Each transverse quadrature point is visited once per CSF domain.  The
        constitutive matrix and the required CUF basis vectors are evaluated
        once at that point.  The full ordered (tau,s) family is then integrated
        by weighted matrix multiplication:

            J = B_test.T @ diag(w*C_mn) @ B_trial

        No prismatic-section or constant-material assumption is introduced;
        ``x`` remains the physical coordinate requested by the longitudinal
        solver and C(x,y,z) is evaluated at every transverse quadrature point.
        """

        family_keys = tuple(dict.fromkeys(family_keys))
        if not family_keys:
            return

        if not hasattr(self.integrator, "quadrature_points"):
            raise TypeError(
                "matrix sectional integration requires an integrator exposing "
                "quadrature_points(domain)"
            )

        x = float(x)
        basis_size = int(self.basis.size)

        # Families are cached as either an M x M array or None when the
        # constitutive contribution is identically zero over all domains.
        totals = {
            family_key: None
            for family_key in family_keys
        }

        required_derivatives = set()
        for family_key in family_keys:
            _, test_derivative, trial_derivative, _, _ = family_key
            required_derivatives.add(test_derivative)
            required_derivatives.add(trial_derivative)

        if self._basis_diagnostic_enabled:
            required_derivatives.update((None, "y", "z"))

        basis_samples = (
            {
                derivative: []
                for derivative in (None, "y", "z")
            }
            if self._basis_diagnostic_enabled
            and x not in self._basis_diagnostic_seen_x
            else None
        )

        domain_count = self.geometry.number_of_domains(x)

        for domain_id in range(1, domain_count + 1):
            quadrature = self.geometry.quadrature_data(
                x=x,
                domain_id=domain_id,
                integrator=self.integrator,
            )
            y_points = quadrature.y_points
            z_points = quadrature.z_points
            quadrature_weights = quadrature.weights

            basis_by_derivative = {
                derivative: self._basis_matrix_at_points(
                    derivative=derivative,
                    y_points=y_points,
                    z_points=z_points,
                )
                for derivative in required_derivatives
            }

            # Zero-weight CSF polygons carry no structural material and are
            # excluded from the upstream basis space diagnostic.
            domain_is_active = (
                quadrature.material_weight is None
                or quadrature.material_weight != 0.0
            )
            if basis_samples is not None and domain_is_active:
                if np.any(quadrature_weights < 0.0):
                    raise ValueError(
                        "upstream SVD diagnostic requires non-negative "
                        "quadrature weights"
                    )
                sqrt_weights = np.sqrt(quadrature_weights)[:, None]
                for derivative in (None, "y", "z"):
                    B = basis_by_derivative[derivative]
                    basis_samples[derivative].append(
                        sqrt_weights * B
                    )

            constitutive_values = quadrature.constitutive_matrices

            self._J_matrix_family_integrations += 1

            for family_key in family_keys:
                (
                    _,
                    test_derivative,
                    trial_derivative,
                    m,
                    n,
                ) = family_key

                weighted_coefficient = (
                    quadrature_weights
                    * constitutive_values[:, int(m) - 1, int(n) - 1]
                )

                # Exact structural zeros are common for isotropic and many
                # orthotropic constitutive laws. Avoid allocating and
                # multiplying a dense M x M zero matrix in those cases.
                if not np.any(weighted_coefficient != 0.0):
                    continue

                B_test = basis_by_derivative[test_derivative]
                B_trial = basis_by_derivative[trial_derivative]

                contribution = (
                    B_test.T
                    @ (weighted_coefficient[:, None] * B_trial)
                )

                if contribution.shape != (basis_size, basis_size):
                    raise RuntimeError(
                        "matrix sectional integration produced an invalid shape"
                    )

                if totals[family_key] is None:
                    totals[family_key] = contribution
                else:
                    totals[family_key] += contribution

        if basis_samples is not None:
            self._run_upstream_basis_diagnostic(
                x=x,
                samples=basis_samples,
            )

        # Diagnostic v3 re-integrates the same J families with explicitly
        # requested higher Gauss orders.  The normal ``totals`` above remain
        # untouched and are the only values stored in the physical cache.
        self._run_gauss_stability_diagnostic(
            x=x,
            family_keys=family_keys,
            reference_totals=totals,
        )

        for family_key, matrix in totals.items():
            self._J_matrix_family_cache[family_key] = matrix

    def J_batch(
        self,
        *,
        x: float,
        signatures,
    ) -> Tuple[float, ...]:
        """
        Evaluate many generalized sectional coefficients in one polygon pass.

        Values are returned in exactly the same order as ``signatures``.

        OPT-02 first uses complete M x M coefficient-family integration when
        supported by the injected fixed-Gauss backend.  All ordered CUF pairs
        are then available from one sectional pass.  The OPT-01 vector path is
        retained as the generic compatibility fallback.
        """

        signatures = tuple(signatures)

        if not signatures:
            return tuple()

        self._J_batch_calls += 1

        normalized = []
        keys = []
        matrix_family_keys = []

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
            matrix_family_keys.append(
                self._J_matrix_family_key(
                    x=x,
                    test_derivative=test_derivative,
                    trial_derivative=trial_derivative,
                    m=m,
                    n=n,
                )
            )

        missing_indices = []
        output = np.zeros(len(signatures), dtype=float)

        for index, key in enumerate(keys):
            if self.cache_enabled and key in self._J_cache:
                self._J_hits += 1
                output[index] = self._J_cache[key]
                continue

            family_key = matrix_family_keys[index]

            if (
                self.cache_enabled
                and family_key in self._J_matrix_family_cache
            ):
                self._J_hits += 1
                self._J_matrix_family_hits += 1
                output[index] = self._matrix_family_value(
                    self._J_matrix_family_cache[family_key],
                    normalized[index][0],
                    normalized[index][2],
                )
                continue

            self._J_misses += 1
            self._J_matrix_family_misses += 1
            missing_indices.append(index)

        if not missing_indices:
            return tuple(float(value) for value in output)

        # OPT-02 matrix path.  The first (tau,s) request at a given x normally
        # contains every nucleus family; computing those families now makes all
        # subsequent ordered CUF pairs at the same x direct matrix lookups.
        if (
            self.cache_enabled
            and hasattr(self.integrator, "quadrature_points")
        ):
            missing_family_keys = tuple(
                dict.fromkeys(
                    matrix_family_keys[index]
                    for index in missing_indices
                )
            )

            self._compute_J_matrix_families(
                x=float(x),
                family_keys=missing_family_keys,
            )

            for index in missing_indices:
                family_key = matrix_family_keys[index]
                output[index] = self._matrix_family_value(
                    self._J_matrix_family_cache[family_key],
                    normalized[index][0],
                    normalized[index][2],
                )

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

        domain_count = self.geometry.number_of_domains(float(x))

        totals = np.zeros(
            len(unique_missing),
            dtype=float,
        )

        # ------------------------------------------------------------------
        # OPT-01: compile all data that do not depend on (x, y, z).
        # The plan is keyed only by the normalized missing signatures.
        # ------------------------------------------------------------------
        request_plan_key = tuple(
            normalized[index]
            for index in unique_missing
        )

        plan = self._batch_factor_plan_cache.get(request_plan_key)

        if plan is None:
            required_basis_factors = set()

            for index in unique_missing:
                tau, d_tau, s, d_s, _, _ = normalized[index]
                required_basis_factors.add((tau, d_tau))
                required_basis_factors.add((s, d_s))

            derivative_rank = {None: 0, "y": 1, "z": 2}
            factor_keys = tuple(
                sorted(
                    required_basis_factors,
                    key=lambda item: (
                        int(item[0]),
                        derivative_rank[item[1]],
                    ),
                )
            )
            factor_position = {
                key: position
                for position, key in enumerate(factor_keys)
            }

            test_factor_positions = np.asarray(
                [
                    factor_position[
                        (
                            normalized[index][0],
                            normalized[index][1],
                        )
                    ]
                    for index in unique_missing
                ],
                dtype=np.intp,
            )
            trial_factor_positions = np.asarray(
                [
                    factor_position[
                        (
                            normalized[index][2],
                            normalized[index][3],
                        )
                    ]
                    for index in unique_missing
                ],
                dtype=np.intp,
            )
            constitutive_rows = np.asarray(
                [normalized[index][4] - 1 for index in unique_missing],
                dtype=np.intp,
            )
            constitutive_cols = np.asarray(
                [normalized[index][5] - 1 for index in unique_missing],
                dtype=np.intp,
            )

            compiled_basis_factors = None
            if hasattr(self.basis, "compile_factors"):
                compiled_basis_factors = self.basis.compile_factors(
                    factor_keys
                )
                if not callable(compiled_basis_factors):
                    raise TypeError(
                        "basis.compile_factors(...) must return a callable"
                    )

            plan = (
                factor_keys,
                test_factor_positions,
                trial_factor_positions,
                constitutive_rows,
                constitutive_cols,
                compiled_basis_factors,
            )
            self._batch_factor_plan_cache[request_plan_key] = plan

        (
            factor_keys,
            test_factor_positions,
            trial_factor_positions,
            constitutive_rows,
            constitutive_cols,
            compiled_basis_factors,
        ) = plan

        factor_count = len(factor_keys)

        for domain_id in range(1, domain_count + 1):
            def vector_integrand(
                y: float,
                z: float,
                C: np.ndarray,
            ) -> np.ndarray:
                if compiled_basis_factors is not None:
                    factor_values = np.asarray(
                        compiled_basis_factors(float(y), float(z)),
                        dtype=float,
                    )
                else:
                    factor_values = np.fromiter(
                        (
                            self._basis_factor(
                                tau=tau_value,
                                derivative=derivative,
                                y=float(y),
                                z=float(z),
                            )
                            for tau_value, derivative in factor_keys
                        ),
                        dtype=float,
                        count=factor_count,
                    )

                if factor_values.shape != (factor_count,):
                    raise ValueError(
                        "compiled basis factor plan returned an invalid shape"
                    )

                return (
                    C[constitutive_rows, constitutive_cols]
                    * factor_values[test_factor_positions]
                    * factor_values[trial_factor_positions]
                )

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

            totals += self.geometry.integrate_vector(
                x=float(x),
                domain_id=domain_id,
                integrator=self.integrator,
                integrand=vector_integrand,
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
