# Version: CSF-CUF isolated transverse expansion plugins v21 - 2026-08-29
"""CUF transverse basis definitions extracted from :mod:`csf.utils.csf_cuf`.

This module contains only basis-related classes. The implementations are
unchanged; ``csf_cuf.py`` re-exports the public names for compatibility.
"""

from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np



class CUFBasis(ABC):
    """Generic transverse CUF basis."""

    @property
    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        raise NotImplementedError

    @abstractmethod
    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        raise NotImplementedError


class MaclaurinCUFBasis(CUFBasis):
    """
    Complete two-dimensional Maclaurin basis.

    All monomials y^p z^q with p+q <= N are included.
    """

    def __init__(self, order: int) -> None:
        if not isinstance(order, int):
            raise TypeError("Maclaurin order must be an integer")
        if order < 0:
            raise ValueError("Maclaurin order must be non-negative")

        self._order = order
        self._exponents = self._build_exponents(order)

    @staticmethod
    def _build_exponents(order: int) -> Tuple[Tuple[int, int], ...]:
        exponents = []

        for degree in range(order + 1):
            for p_y in range(degree, -1, -1):
                p_z = degree - p_y
                exponents.append((p_y, p_z))

        return tuple(exponents)

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return len(self._exponents)

    def exponents(self, tau: int) -> Tuple[int, int]:
        self._validate_tau(tau)
        return self._exponents[tau - 1]

    def value(
        self, tau: int, y: float, z: float, *, x: float | None = None
    ) -> float:
        p_y, p_z = self.exponents(tau)
        return float((y ** p_y) * (z ** p_z))

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        p_y, p_z = self.exponents(tau)

        if direction == "y":
            if p_y == 0:
                return 0.0
            return float(p_y * (y ** (p_y - 1)) * (z ** p_z))

        if direction == "z":
            if p_z == 0:
                return 0.0
            return float(p_z * (y ** p_y) * (z ** (p_z - 1)))

        raise ValueError("direction must be 'y' or 'z'")

    def _validate_tau(self, tau: int) -> None:
        if not isinstance(tau, int):
            raise TypeError("tau must be an integer")
        if not 1 <= tau <= self.size:
            raise IndexError(f"tau must be in 1..{self.size}, got {tau}")


# =============================================================================
# Hierarchical Serendipity-Lagrange transverse basis
# =============================================================================

class SerendipityLagrangeReferenceBasis(CUFBasis):
    """
    Hierarchical Serendipity-Lagrange (SL) basis on [-1,1] x [-1,1].

    The construction follows the SL hierarchy used in the UF-SLE literature:

      type I
          four bilinear corner functions;

      type II
          four edge functions for every enrichment order r >= 2;

      type III
          interior bubble functions p_n(xi) p_m(eta), with
          n,m >= 2 and n+m=r, for r >= 4.

    An SL model of order N contains every function from orders 1..N.

    Number of local functions
    -------------------------
        SL1 :  4
        SL2 :  8
        SL3 : 12
        SL4 : 17
        SL5 : 23

    Natural coordinates are passed through the CUFBasis interface as
    ``y=xi`` and ``z=eta``.  This class is purely a reference-element basis;
    ``QuadrilateralSerendipityCUFBasis`` provides the physical (y,z) map.
    """

    _CORNERS = (
        (-1.0, -1.0),
        (+1.0, -1.0),
        (+1.0, +1.0),
        (-1.0, +1.0),
    )

    def __init__(self, order: int) -> None:
        if not isinstance(order, int):
            raise TypeError("SL order must be an integer")

        if order < 1:
            raise ValueError("SL order must be >= 1")

        self._order = order
        self._definitions = self._build_definitions(order)
        self._poly_coefficients = {
            r: self._build_p_coefficients(r)
            for r in range(2, order + 1)
        }

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return len(self._definitions)

    @staticmethod
    def expected_size(order: int) -> int:
        if not isinstance(order, int):
            raise TypeError("SL order must be an integer")

        if order < 1:
            raise ValueError("SL order must be >= 1")

        if order <= 3:
            return 4 * order

        return (
            4 * order
            + (order - 2) * (order - 3) // 2
        )

    @classmethod
    def _build_definitions(cls, order: int):
        definitions = []

        # Order 1: four bilinear corner functions.
        for side in range(1, 5):
            definitions.append(
                ("I", 1, side, None, None)
            )

        # Orders >= 2: four edge functions for every enrichment level.
        for r in range(2, order + 1):
            edge_type = "IIA" if r <= 3 else "IIB"

            for side in range(1, 5):
                definitions.append(
                    (edge_type, r, side, None, None)
                )

            # Interior functions start at r=4.
            if r >= 4:
                for n in range(2, r - 1):
                    m = r - n

                    if m < 2:
                        continue

                    definitions.append(
                        ("III", r, None, n, m)
                    )

        expected = cls.expected_size(order)

        if len(definitions) != expected:
            raise RuntimeError(
                "internal SL basis size inconsistency: "
                f"built {len(definitions)}, expected {expected}"
            )

        return tuple(definitions)

    @staticmethod
    def _build_p_coefficients(order: int) -> np.ndarray:
        """
        Coefficients of

            p_r(mu) = product_i (mu - mu_i),

        where the r equally spaced roots include -1 and +1.
        """

        roots = np.linspace(
            -1.0,
            +1.0,
            order,
            dtype=float,
        )

        return np.poly(roots)

    def definition(self, tau: int):
        self._validate_tau(tau)
        return self._definitions[tau - 1]

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        xi = float(y)
        eta = float(z)

        return float(
            self._evaluate_reference(
                tau=tau,
                xi=xi,
                eta=eta,
            )[0]
        )

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        xi = float(y)
        eta = float(z)

        _, dxi, deta = self._evaluate_reference(
            tau=tau,
            xi=xi,
            eta=eta,
        )

        if direction == "y":
            return float(dxi)

        if direction == "z":
            return float(deta)

        raise ValueError("direction must be 'y' or 'z'")

    def reference_value_and_gradient(
        self,
        tau: int,
        xi: float,
        eta: float,
    ):
        return self._evaluate_reference(
            tau=tau,
            xi=float(xi),
            eta=float(eta),
        )

    def _p(
        self,
        order: int,
        mu: float,
    ):
        coefficients = self._poly_coefficients[order]
        derivative_coefficients = np.polyder(coefficients)

        return (
            float(np.polyval(coefficients, mu)),
            float(np.polyval(derivative_coefficients, mu)),
        )

    def _evaluate_reference(
        self,
        *,
        tau: int,
        xi: float,
        eta: float,
    ):
        self._validate_tau(tau)

        kind, r, side, n, m = self._definitions[tau - 1]

        if kind == "I":
            xi_s, eta_s = self._CORNERS[side - 1]

            value = (
                0.25
                * (1.0 + xi_s * xi)
                * (1.0 + eta_s * eta)
            )

            dxi = (
                0.25
                * xi_s
                * (1.0 + eta_s * eta)
            )

            deta = (
                0.25
                * eta_s
                * (1.0 + xi_s * xi)
            )

            return value, dxi, deta

        if kind in ("IIA", "IIB"):
            if side == 1:
                p, dp = self._p(r, xi)

                return (
                    0.5 * (1.0 - eta) * p,
                    0.5 * (1.0 - eta) * dp,
                    -0.5 * p,
                )

            if side == 2:
                p, dp = self._p(r, eta)

                return (
                    0.5 * (1.0 + xi) * p,
                    0.5 * p,
                    0.5 * (1.0 + xi) * dp,
                )

            if side == 3:
                p, dp_argument = self._p(r, -xi)

                # d/dxi p_r(-xi) = -p'_r(-xi)
                return (
                    0.5 * (1.0 + eta) * p,
                    -0.5 * (1.0 + eta) * dp_argument,
                    0.5 * p,
                )

            if side == 4:
                p, dp_argument = self._p(r, -eta)

                # d/deta p_r(-eta) = -p'_r(-eta)
                return (
                    0.5 * (1.0 - xi) * p,
                    -0.5 * p,
                    -0.5 * (1.0 - xi) * dp_argument,
                )

            raise RuntimeError("invalid SL edge index")

        if kind == "III":
            p_xi, dp_xi = self._p(n, xi)
            p_eta, dp_eta = self._p(m, eta)

            return (
                p_xi * p_eta,
                dp_xi * p_eta,
                p_xi * dp_eta,
            )

        raise RuntimeError(
            f"unsupported SL function type {kind!r}"
        )

    def _validate_tau(self, tau: int) -> None:
        if not isinstance(tau, int):
            raise TypeError("tau must be an integer")

        if not 1 <= tau <= self.size:
            raise IndexError(
                f"tau must be in 1..{self.size}, got {tau}"
            )


class QuadrilateralSerendipityCUFBasis(CUFBasis):
    """
    Physical Serendipity-Lagrange basis on one generic quadrilateral.

    The physical quadrilateral is mapped from the master square using the
    four type-I bilinear functions.  Vertices must follow the standard cyclic
    order corresponding to natural corners

        (-1,-1), (+1,-1), (+1,+1), (-1,+1).

    The class supports convex non-degenerate bilinear quadrilaterals and
    computes physical transverse derivatives by the exact Jacobian chain
    rule.

    This is a *local sub-domain basis*.  It deliberately does not impose a
    particular cross-sectional mesh topology.  Global sharing of corner/edge
    amplitudes across multiple SL sub-domains is a separate assembly layer.
    """

    def __init__(
        self,
        *,
        order: int,
        vertices,
        inverse_tolerance: float = 1.0e-12,
        inverse_max_iterations: int = 30,
    ) -> None:
        vertices = tuple(
            (float(point[0]), float(point[1]))
            for point in vertices
        )

        if len(vertices) != 4:
            raise ValueError(
                "SL quadrilateral requires exactly four vertices"
            )

        coordinates = np.asarray(
            vertices,
            dtype=float,
        )

        if not np.all(np.isfinite(coordinates)):
            raise ValueError(
                "quadrilateral vertices must be finite"
            )

        if inverse_tolerance <= 0.0:
            raise ValueError(
                "inverse_tolerance must be positive"
            )

        if inverse_max_iterations < 1:
            raise ValueError(
                "inverse_max_iterations must be >= 1"
            )

        self.reference_basis = (
            SerendipityLagrangeReferenceBasis(order)
        )

        self.vertices = vertices
        self._coordinates = coordinates

        self.inverse_tolerance = float(inverse_tolerance)
        self.inverse_max_iterations = int(
            inverse_max_iterations
        )

        # Basic degeneracy/orientation check at the reference centre.
        _, jacobian = self.map_reference(
            xi=0.0,
            eta=0.0,
        )

        determinant = float(
            np.linalg.det(jacobian)
        )

        if not np.isfinite(determinant) or determinant <= 0.0:
            raise ValueError(
                "quadrilateral must have a positive non-zero "
                "reference-to-physical Jacobian"
            )

    @property
    def order(self) -> int:
        return self.reference_basis.order

    @property
    def size(self) -> int:
        return self.reference_basis.size

    def definition(self, tau: int):
        return self.reference_basis.definition(tau)

    @staticmethod
    def _type_I_shape(
        xi: float,
        eta: float,
    ):
        corners = (
            (-1.0, -1.0),
            (+1.0, -1.0),
            (+1.0, +1.0),
            (-1.0, +1.0),
        )

        values = np.empty(4, dtype=float)
        dxi = np.empty(4, dtype=float)
        deta = np.empty(4, dtype=float)

        for index, (xi_s, eta_s) in enumerate(corners):
            values[index] = (
                0.25
                * (1.0 + xi_s * xi)
                * (1.0 + eta_s * eta)
            )

            dxi[index] = (
                0.25
                * xi_s
                * (1.0 + eta_s * eta)
            )

            deta[index] = (
                0.25
                * eta_s
                * (1.0 + xi_s * xi)
            )

        return values, dxi, deta

    def map_reference(
        self,
        *,
        xi: float,
        eta: float,
    ):
        xi = float(xi)
        eta = float(eta)

        N, dN_dxi, dN_deta = self._type_I_shape(
            xi,
            eta,
        )

        physical = N @ self._coordinates

        jacobian = np.empty(
            (2, 2),
            dtype=float,
        )

        # Rows are physical coordinates (y,z);
        # columns are natural coordinates (xi,eta).
        jacobian[:, 0] = (
            dN_dxi @ self._coordinates
        )

        jacobian[:, 1] = (
            dN_deta @ self._coordinates
        )

        return (
            (float(physical[0]), float(physical[1])),
            jacobian,
        )

    def inverse_map(
        self,
        *,
        y: float,
        z: float,
    ):
        target = np.array(
            [float(y), float(z)],
            dtype=float,
        )

        if not np.all(np.isfinite(target)):
            raise ValueError(
                "physical transverse coordinates must be finite"
            )

        xi_eta = np.zeros(
            2,
            dtype=float,
        )

        scale = max(
            1.0,
            float(
                np.max(
                    np.ptp(
                        self._coordinates,
                        axis=0,
                    )
                )
            ),
        )

        for _ in range(
            self.inverse_max_iterations
        ):
            physical, jacobian = self.map_reference(
                xi=xi_eta[0],
                eta=xi_eta[1],
            )

            residual = np.asarray(
                physical,
                dtype=float,
            ) - target

            if (
                np.linalg.norm(
                    residual,
                    ord=np.inf,
                )
                <= self.inverse_tolerance * scale
            ):
                return (
                    float(xi_eta[0]),
                    float(xi_eta[1]),
                )

            determinant = float(
                np.linalg.det(jacobian)
            )

            if abs(determinant) <= 1.0e-15:
                raise RuntimeError(
                    "singular quadrilateral Jacobian during inverse map"
                )

            correction = np.linalg.solve(
                jacobian,
                residual,
            )

            xi_eta -= correction

        physical, _ = self.map_reference(
            xi=xi_eta[0],
            eta=xi_eta[1],
        )

        residual = (
            np.asarray(
                physical,
                dtype=float,
            )
            - target
        )

        if (
            np.linalg.norm(
                residual,
                ord=np.inf,
            )
            > self.inverse_tolerance * scale
        ):
            raise RuntimeError(
                "quadrilateral inverse map did not converge"
            )

        return (
            float(xi_eta[0]),
            float(xi_eta[1]),
        )

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        xi, eta = self.inverse_map(
            y=y,
            z=z,
        )

        return self.reference_basis.value(
            tau,
            xi,
            eta,
            x=x,
        )

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        if direction not in ("y", "z"):
            raise ValueError(
                "direction must be 'y' or 'z'"
            )

        xi, eta = self.inverse_map(
            y=y,
            z=z,
        )

        _, dF_dxi, dF_deta = (
            self.reference_basis.reference_value_and_gradient(
                tau,
                xi,
                eta,
            )
        )

        _, jacobian = self.map_reference(
            xi=xi,
            eta=eta,
        )

        # grad_physical = J^{-T} grad_natural
        gradient_physical = np.linalg.solve(
            jacobian.T,
            np.array(
                [dF_dxi, dF_deta],
                dtype=float,
            ),
        )

        if direction == "y":
            return float(
                gradient_physical[0]
            )

        return float(
            gradient_physical[1]
        )
