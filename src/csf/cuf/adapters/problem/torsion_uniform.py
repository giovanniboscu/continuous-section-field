# Version: CSF-CUF uniform torsional line-pair adapter v1.1 - 2026-09-03
# Changelog: v1.1 removes benchmark-specific names; v1.0 introduced uniform intensity.
"""
Uniform torsional line-pair problem adapter for CSF-CUF.

Purpose
-------
This module is the uniform longitudinal counterpart of the torsional part of
``bending_torsion_halfwave.py``.  It preserves the same physical load points,
the same opposite global-z force pair, the same CSF geometry queries, and the
same constraint equations.  The only intentional mechanical change is the
longitudinal distribution:

Half-wave source adapter::

    phase(x) = sin(pi * (x - x0) / L)

Uniform adapter::

    phase(x) = 1

Therefore the two line-load intensities remain non-zero and constant at every
longitudinal coordinate, including the two end sections.


Physical loading
----------------
At every physical coordinate ``x``, CSF supplies the current section geometry.
The adapter selects exactly the same two vertices used by the validated
half-wave torsion problem:

``point_plus``
    The leftmost CSF vertex on the maximum-z boundary.

``point_minus``
    The rightmost CSF vertex on the minimum-z boundary.

A global-z line-load intensity ``+amplitude`` acts at ``point_plus`` and the
opposite intensity ``-amplitude`` acts at ``point_minus``.  The resultant
global-z force per unit longitudinal length is consequently zero.  The pair
creates a torsional moment about the global beam axis.

For one CUF transverse function ``F_tau``, the generalized load is

    q_tau,z(x)
        = amplitude
          * [F_tau(y_plus(x), z_plus(x))
             - F_tau(y_minus(x), z_minus(x))].

The ordinary longitudinal finite-element assembler then evaluates

    f_i,tau,z = integral[x0,x1] N_i(x) q_tau,z(x) dx.

No sinusoidal factor, hidden sign, fixed transverse coordinate, or material
parameter appears in this expression.


Meaning of "uniform"
--------------------
Uniform refers to the signed intensity of each member of the opposite force
pair per unit global longitudinal coordinate ``x``.  The two physical points
continue to follow the non-prismatic CSF section.

If the transverse lever arm changes with ``x``, the local distributed torque

    m_x(x) = amplitude * [y_plus(x) - y_minus(x)]

changes accordingly.  This is the physically direct result of applying a
uniform force pair to a changing section.  The adapter does not renormalise the
forces to impose an artificially constant torque.

The ``amplitude`` units are therefore force per unit longitudinal length in the
consistent model unit system.  For example, if force is expressed in newtons
and geometry in millimetres, ``amplitude`` is expressed in ``N/mm``.


YAML interface
--------------
The associated problem definition is::

    model:
      csf_yaml: ../models/model.yaml

    problem:
      type: torsion_uniform
      amplitude: 1.0

``amplitude`` is signed and defaults to ``1.0`` for compatibility with the
source half-wave adapter.  No longitudinal phase or quadrature parameter is
required from the user.

The case YAML selects this module independently::

    problem:
      yaml: ../problems/torsion_uniform.yaml
      adapter: csf.cuf.adapters.problem.torsion_uniform

The original ``bending_torsion_halfwave.py`` remains unchanged and available
for the sinusoidal validation case.


CUF projection
--------------
The displacement expansion uses physical global components.  Both members of
the applied pair act in global ``z``; therefore this adapter creates only
``component='z'`` generalized loads.  The difference of basis values preserves
the equal-and-opposite physical signs.

The basis is evaluated at the current physical CSF vertices and receives the
current ``x`` coordinate through the generic basis API.  Fixed-scale polynomial
expansions may ignore ``x``; a section-aware expansion can use it without any
change to this adapter.


Constraints
-----------
The constraint matrix is copied mechanically from the torsional half-wave
problem so that the longitudinal load law is the only changed ingredient:

* every global-y and global-z CUF amplitude is fixed at both beam ends;
* one mean global-x displacement equation removes rigid axial translation.

The mean axial gauge is deliberately preserved.  The uniform adapter does not
post-process, shift, or otherwise clean any displacement component.


Scope
-----
The selected vertex rule belongs to the supplied torsion validation problem
and is not presented as a universal arbitrary torque definition.  It is
nevertheless geometry-following: all point coordinates are obtained from the
current CSF section rather than copied into the adapter.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np

from csf.cuf.numerics import all_vertices, transverse_bounds
from csf.cuf.problem.point_bc import LinearConstraintSystem
from csf.cuf.problem.problem import GeneralizedLongitudinalLoad, ScalarLoadField


PROBLEM_TYPE = "torsion_uniform"


def _finite_float(value: Any, *, path: str) -> float:
    """Convert one YAML scalar to a finite float with a precise error path."""

    if isinstance(value, bool):
        raise TypeError(f"{path} must be a finite number, got {value!r}")

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"{path} must be a finite number, got {value!r}"
        ) from exc

    if not math.isfinite(result):
        raise ValueError(f"{path} must be finite, got {value!r}")

    return result


def _has_vertex(section_provider: Any, x: float, point) -> bool:
    """Confirm that a selected physical point is an actual current CSF vertex.

    This is retained from the source half-wave adapter.  It prevents a future
    change to the extrema-selection helper from silently turning the physical
    vertex load into an interpolated or invented point load.
    """

    target_y, target_z = map(float, point)
    scale = max(1.0, abs(target_y), abs(target_z))
    tolerance = 1.0e-10 * scale

    for y, z in all_vertices(section_provider, float(x)):
        if math.isclose(
            float(y), target_y, rel_tol=0.0, abs_tol=tolerance
        ) and math.isclose(
            float(z), target_z, rel_tol=0.0, abs_tol=tolerance
        ):
            return True

    return False


def moving_load_points(section_provider: Any, x: float):
    """Return the same two moving CSF vertices as the half-wave torsion case.

    The positive point is the leftmost vertex on the maximum-z boundary.  The
    negative point is the rightmost vertex on the minimum-z boundary.  Ties are
    resolved deterministically by the physical y coordinate.
    """

    x = float(x)
    _, _, z_min, z_max = transverse_bounds(section_provider, x)
    vertices = tuple(
        (float(y), float(z)) for y, z in all_vertices(section_provider, x)
    )

    scale = max(1.0, abs(float(z_min)), abs(float(z_max)))
    tolerance = 1.0e-10 * scale

    top_vertices = [
        (y, z)
        for y, z in vertices
        if math.isclose(z, float(z_max), rel_tol=0.0, abs_tol=tolerance)
    ]
    bottom_vertices = [
        (y, z)
        for y, z in vertices
        if math.isclose(z, float(z_min), rel_tol=0.0, abs_tol=tolerance)
    ]

    if not top_vertices:
        raise ValueError(
            f"no CSF vertex found on maximum-z boundary at x={x}"
        )
    if not bottom_vertices:
        raise ValueError(
            f"no CSF vertex found on minimum-z boundary at x={x}"
        )

    point_plus = min(top_vertices, key=lambda point: point[0])
    point_minus = max(bottom_vertices, key=lambda point: point[0])

    if not _has_vertex(section_provider, x, point_plus):
        raise ValueError(
            f"positive load point is not a CSF vertex at x={x}: "
            f"{point_plus}"
        )
    if not _has_vertex(section_provider, x, point_minus):
        raise ValueError(
            f"negative load point is not a CSF vertex at x={x}: "
            f"{point_minus}"
        )

    return point_plus, point_minus


class UniformTorsionalLinePairProjector:
    """Project the uniform opposite force pair onto all CUF functions."""

    def __init__(
        self,
        *,
        section_provider: Any,
        basis: Any,
        x0: float,
        x1: float,
        amplitude: float,
    ) -> None:
        self.section_provider = section_provider
        self.basis = basis
        self.x0 = float(x0)
        self.x1 = float(x1)
        self.amplitude = float(amplitude)

        if not (math.isfinite(self.x0) and math.isfinite(self.x1)):
            raise ValueError("CSF longitudinal endpoints must be finite")
        if self.x1 <= self.x0:
            raise ValueError(
                "CSF longitudinal domain must satisfy x1 > x0; "
                f"got x0={self.x0!r}, x1={self.x1!r}"
            )
        if not math.isfinite(self.amplitude):
            raise ValueError("problem.amplitude must be finite")

        self._cache: dict[float, np.ndarray] = {}

    def generalized_vector(self, x: float) -> np.ndarray:
        """Return the complete uniform ``q_tau,z(x)`` vector."""

        x = float(x)
        cached = self._cache.get(x)
        if cached is not None:
            return cached

        point_plus, point_minus = moving_load_points(
            self.section_provider,
            x,
        )
        y_plus, z_plus = point_plus
        y_minus, z_minus = point_minus

        values_plus = np.asarray(
            [
                self.basis.value(tau, y_plus, z_plus, x=x)
                for tau in range(1, int(self.basis.size) + 1)
            ],
            dtype=float,
        )
        values_minus = np.asarray(
            [
                self.basis.value(tau, y_minus, z_minus, x=x)
                for tau in range(1, int(self.basis.size) + 1)
            ],
            dtype=float,
        )

        # This is the only intended difference from TorsionalLinePairProjector
        # in bending_torsion_halfwave.py.  No phase(x) multiplier is applied:
        # the physical force-pair intensity is uniform over the full length.
        values = self.amplitude * (values_plus - values_minus)

        if not np.all(np.isfinite(values)):
            raise ValueError(
                "uniform torsional projection produced a non-finite "
                f"generalized load vector at x={x}"
            )

        values.setflags(write=False)
        self._cache[x] = values
        return values


class _ModeLineLoadField(ScalarLoadField):
    """Expose one tau entry through the scalar longitudinal load API."""

    def __init__(self, projector: UniformTorsionalLinePairProjector, tau: int):
        self.projector = projector
        self.tau = int(tau)

    def value(self, x: float) -> float:
        return float(
            self.projector.generalized_vector(float(x))[self.tau - 1]
        )


class UniformTorsionProblem:
    """Complete uniform counterpart of the supplied half-wave torsion problem."""

    def __init__(self, *, amplitude: float = 1.0) -> None:
        self.amplitude = float(amplitude)
        if not math.isfinite(self.amplitude):
            raise ValueError("problem.amplitude must be finite")

    def build_loads(
        self,
        *,
        section_provider: Any,
        basis: Any,
        x0: float,
        x1: float,
    ):
        """Build global-z generalized loads for every transverse mode."""

        projector = UniformTorsionalLinePairProjector(
            section_provider=section_provider,
            basis=basis,
            x0=float(x0),
            x1=float(x1),
            amplitude=self.amplitude,
        )

        loads = tuple(
            GeneralizedLongitudinalLoad(
                tau=tau,
                component="z",
                field=_ModeLineLoadField(projector, tau),
            )
            for tau in range(1, int(basis.size) + 1)
        )

        return loads, projector

    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ):
        """Apply the torsion supports with the FEM3D pointwise axial anchor."""

        layout = assembled.dof_layout
        row_count = 4 * int(basis.size) + 1
        matrix = np.zeros((row_count, layout.total_dofs), dtype=float)
        rhs = np.zeros(row_count, dtype=float)
        row = 0

        # Fix all generalized global-y and global-z amplitudes at both beam
        # ends.  Solver component numbering is 0=x, 1=y, 2=z.
        for node in (0, mesh.number_of_nodes - 1):
            for component in (1, 2):
                for tau in range(1, int(basis.size) + 1):
                    matrix[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=component,
                        ),
                    ] = 1.0
                    row += 1

        # Remove only the rigid global-x translation, using exactly the same
        # physical anchor as FEM3D: u_x(x_start, y=0, z=0) = 0.
        axial_anchor_factors = np.asarray(
            [
                basis.value(
                    tau,
                    0.0,
                    0.0,
                    x=float(mesh.x_start),
                )
                for tau in range(1, int(basis.size) + 1)
            ],
            dtype=float,
        )

        start_node = 0
        for tau, factor in enumerate(axial_anchor_factors, start=1):
            matrix[
                row,
                layout.index(
                    node=start_node,
                    tau=tau,
                    component=0,
                ),
            ] = float(factor)

        row += 1
        if row != row_count:
            raise RuntimeError("internal constraint-row count mismatch")

        return LinearConstraintSystem(
            matrix=matrix,
            rhs=rhs,
            constraints=tuple(None for _ in range(row_count)),
        )

    def tracked_points(self, section_provider: Any, x: float):
        """Expose the two physical load trajectories to output adapters."""

        point_plus, point_minus = moving_load_points(
            section_provider,
            float(x),
        )
        return (
            ("positive_corner", point_plus[0], point_plus[1]),
            ("negative_corner", point_minus[0], point_minus[1]),
        )


def build_problem(problem_type: str, options: dict):
    """Standard problem-adapter entry point used by the CSF-CUF loader."""

    if problem_type != PROBLEM_TYPE:
        raise ValueError(
            f"unsupported problem.type: {problem_type!r}; expected "
            f"{PROBLEM_TYPE!r}"
        )
    if not isinstance(options, Mapping):
        raise TypeError("problem options must be a YAML mapping")

    unsupported = sorted(str(key) for key in options if key != "amplitude")
    if unsupported:
        raise ValueError(
            "uniform torsion problem contains unsupported option(s): "
            f"{', '.join(unsupported)}; allowed: amplitude"
        )

    amplitude = _finite_float(
        options.get("amplitude", 1.0),
        path="problem.amplitude",
    )
    return UniformTorsionProblem(amplitude=amplitude)


__all__ = (
    "PROBLEM_TYPE",
    "UniformTorsionProblem",
    "UniformTorsionalLinePairProjector",
    "build_problem",
    "moving_load_points",
)
