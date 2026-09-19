"""
Generic double-clamped beam problem with one concentrated physical point load.

The adapter is independent of section shape, material and CUF expansion family.
The longitudinal domain is obtained from CSF.  The point-load position is given
as a fraction of that domain, while the transverse point is expressed in the
physical CSF-CUF section coordinates (y, z).

For a physical force component P_c applied at

    (x_p, y_p, z_p),

the CUF generalized point load is

    Q_(tau,c) = F_tau(x_p, y_p, z_p) P_c.

The adapter then evaluates the longitudinal FE shape functions at x_p.  If x_p is a shared FE node (for example x_fraction=0.5 with an even
number of equal elements), the force is applied exactly to that shared node;
it is not integrated as a distributed load.

Both longitudinal end sections are fully clamped by setting every generalized
CUF amplitude of all three displacement components to zero at the first and
last longitudinal nodes.

Problem YAML
------------

model:
  csf_yaml: ../models/model.yaml

problem:
  type: double_clamped_point_load
  x_fraction: 0.5
  point:
    y: 0.095
    z: 0.05
  components:
    z: -1000.0

``x_fraction`` is measured from the CSF longitudinal start section and must lie
in [0, 1].  ``point.y`` and ``point.z`` are physical transverse coordinates.
``components`` may contain any combination of x, y and z; omitted components
are zero.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

import numpy as np

from csf.cuf.problem.point_bc import LinearConstraintSystem


PROBLEM_TYPE = "double_clamped_point_load"


def _require_mapping(value: Any, *, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{path} must be a YAML mapping")
    return value


def _reject_unknown_keys(
    mapping: Mapping[str, Any],
    *,
    allowed: set[str],
    path: str,
) -> None:
    unknown = sorted(str(key) for key in mapping if key not in allowed)
    if unknown:
        raise ValueError(
            f"{path} contains unsupported key(s): {', '.join(unknown)}; "
            f"allowed: {', '.join(sorted(allowed))}"
        )


def _finite_float(value: Any, *, path: str) -> float:
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


@dataclass(frozen=True)
class PhysicalPointLoadState:
    """Resolved physical location and force vector used by the adapter."""

    x: float
    y: float
    z: float
    components: tuple[tuple[str, float], ...]


def _assemble_point_load(
    *,
    vector: np.ndarray,
    mesh: Any,
    dof_layout: Any,
    tau: int,
    component: int,
    x: float,
    value: float,
) -> None:
    """Project one concentrated longitudinal load through FE shapes."""

    x = float(x)
    scale = max(1.0, abs(float(mesh.x_start)), abs(float(mesh.x_end)))
    tol = 1.0e-12 * scale

    if x < float(mesh.x_start) - tol or x > float(mesh.x_end) + tol:
        raise ValueError(
            f"point load x={x} lies outside longitudinal domain "
            f"[{mesh.x_start}, {mesh.x_end}]"
        )

    if abs(x - float(mesh.x_start)) <= tol:
        x = float(mesh.x_start)
    elif abs(x - float(mesh.x_end)) <= tol:
        x = float(mesh.x_end)

    selected = None
    for element in mesh.elements:
        if element is mesh.elements[-1]:
            inside = element.x_start - tol <= x <= element.x_end + tol
        else:
            inside = element.x_start - tol <= x < element.x_end - tol
        if inside:
            selected = element
            break

    if selected is None:
        for element in mesh.elements:
            if element.x_start - tol <= x <= element.x_end + tol:
                selected = element
                break

    if selected is None:
        raise RuntimeError(
            f"could not locate longitudinal element for point load x={x}"
        )

    if tau > dof_layout.basis_size_at_node(selected.node_ids[0]):
        return

    xi = (
        2.0 * x - float(selected.x_start) - float(selected.x_end)
    ) / float(selected.length)
    shape = np.asarray(selected.shape_values(xi), dtype=float)

    for a, global_node in enumerate(selected.node_ids):
        coefficient = float(shape[a])
        if coefficient == 0.0:
            continue
        dof = dof_layout.index(
            node=global_node,
            tau=tau,
            component=component,
        )
        vector[dof] += coefficient * float(value)


class DoubleClampedPointLoadProblem:
    """Full clamp at both ends plus one concentrated physical point force."""

    def __init__(
        self,
        *,
        x_fraction: float,
        y: float,
        z: float,
        components: Mapping[str, float],
    ) -> None:
        self.x_fraction = float(x_fraction)
        self.y = float(y)
        self.z = float(z)
        self.components = {
            str(component): float(value)
            for component, value in components.items()
        }

    def build_load_vector(
        self,
        *,
        section_provider: Any,
        basis: Any,
        mesh: Any,
        dof_layout: Any,
        longitudinal_integrator: Any,
        x0: float,
        x1: float,
    ):
        del section_provider, longitudinal_integrator

        x0 = float(x0)
        x1 = float(x1)
        x = x0 + self.x_fraction * (x1 - x0)

        load_vector = np.zeros(dof_layout.total_dofs, dtype=float)
        component_index = {
            "x": 0,
            "y": 1,
            "z": 2,
        }

        for component, physical_force in self.components.items():
            if physical_force == 0.0:
                continue
            component_number = component_index[component]
            for tau in range(1, int(basis.size) + 1):
                factor = float(
                    basis.value(
                        tau,
                        self.y,
                        self.z,
                        x=x,
                    )
                )
                _assemble_point_load(
                    vector=load_vector,
                    mesh=mesh,
                    dof_layout=dof_layout,
                    tau=tau,
                    component=component_number,
                    x=x,
                    value=physical_force * factor,
                )

        state = PhysicalPointLoadState(
            x=x,
            y=self.y,
            z=self.z,
            components=tuple(self.components.items()),
        )
        return load_vector, state

    def build_constraints(
        self,
        *,
        assembled: Any,
        mesh: Any,
        basis: Any,
        longitudinal_integrator: Any,
    ):
        del longitudinal_integrator

        layout = assembled.dof_layout
        end_nodes = (0, mesh.number_of_nodes - 1)
        end_basis_sizes = tuple(
            int(layout.basis_size_at_node(node))
            for node in end_nodes
        )
        row_count = 3 * sum(end_basis_sizes)
        matrix = np.zeros((row_count, layout.total_dofs), dtype=float)
        rhs = np.zeros(row_count, dtype=float)

        row = 0
        for node, node_basis_size in zip(end_nodes, end_basis_sizes):
            for component in (0, 1, 2):
                for tau in range(1, node_basis_size + 1):
                    matrix[
                        row,
                        layout.index(
                            node=node,
                            tau=tau,
                            component=component,
                        ),
                    ] = 1.0
                    row += 1

        if row != row_count:
            raise RuntimeError("internal constraint-row count mismatch")

        return LinearConstraintSystem(
            matrix=matrix,
            rhs=rhs,
            constraints=tuple(None for _ in range(row_count)),
        )

    def tracked_points(self, section_provider: Any, x: float):
        del section_provider, x
        return (("point_load", self.y, self.z),)


def _parse_point(options: Mapping[str, Any]) -> tuple[float, float]:
    if "point" not in options:
        raise ValueError("problem.point is required")
    point = _require_mapping(options["point"], path="problem.point")
    _reject_unknown_keys(
        point,
        allowed={"y", "z"},
        path="problem.point",
    )
    missing = {"y", "z"} - set(point)
    if missing:
        raise ValueError(
            "problem.point is missing key(s): " + ", ".join(sorted(missing))
        )
    return (
        _finite_float(point["y"], path="problem.point.y"),
        _finite_float(point["z"], path="problem.point.z"),
    )


def _parse_components(options: Mapping[str, Any]) -> dict[str, float]:
    if "components" not in options:
        raise ValueError("problem.components is required")
    components = _require_mapping(
        options["components"],
        path="problem.components",
    )
    _reject_unknown_keys(
        components,
        allowed={"x", "y", "z"},
        path="problem.components",
    )
    if not components:
        raise ValueError("problem.components must contain at least one component")

    parsed = {
        str(component): _finite_float(
            value,
            path=f"problem.components.{component}",
        )
        for component, value in components.items()
    }
    if not any(value != 0.0 for value in parsed.values()):
        raise ValueError("problem.components must contain a non-zero force")
    return parsed


def build_problem(problem_type: str, options: dict):
    """Standard problem-adapter entry point used by the CSF-CUF loader."""

    if problem_type != PROBLEM_TYPE:
        raise ValueError(
            f"unsupported problem.type: {problem_type!r}; expected "
            f"{PROBLEM_TYPE!r}"
        )

    options = _require_mapping(options, path="problem")
    _reject_unknown_keys(
        options,
        allowed={"x_fraction", "point", "components"},
        path="problem",
    )

    if "x_fraction" not in options:
        raise ValueError("problem.x_fraction is required")
    x_fraction = _finite_float(
        options["x_fraction"],
        path="problem.x_fraction",
    )
    if not 0.0 <= x_fraction <= 1.0:
        raise ValueError("problem.x_fraction must lie in [0, 1]")

    y, z = _parse_point(options)
    components = _parse_components(options)

    return DoubleClampedPointLoadProblem(
        x_fraction=x_fraction,
        y=y,
        z=z,
        components=components,
    )


__all__ = (
    "DoubleClampedPointLoadProblem",
    "PhysicalPointLoadState",
    "PROBLEM_TYPE",
    "build_problem",
)
