# Version: CSF-CUF self-contained displacement checkpoint v1 - 2026-08-29
"""Compiled displacement field independent of case and model YAML files.

The persisted format contains only the solved displacement representation:
longitudinal interpolation coefficients, transverse physical power
coefficients, element bounds, and solved generalized coefficients.  It does
not contain KKT data, material laws, geometry domains, strains, or stresses.

Polynomial transverse expansions opt in by exposing a callable
``power_coefficients()`` method returning an array with shape
``(basis.size, y_degree + 1, z_degree + 1)`` in ascending physical powers:

    F_tau(y,z) = sum_{p,q} C[tau-1,p,q] y**p z**q.

This optional contract deliberately lives outside ``cuf.core``.  A future
non-polynomial expansion may add another checkpoint representation here
without changing the CUFBasis mechanics contract.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

import numpy as np


_FORMAT_NAME = "csf-cuf-compiled-displacement"
_FORMAT_VERSION = 1


class CompiledDisplacementField:
    """Self-contained callable representation of the solved displacement."""

    def __init__(
        self,
        *,
        element_x_starts,
        element_x_ends,
        element_coefficients,
        longitudinal_shape_coefficients,
        transverse_power_coefficients,
        metadata=None,
    ) -> None:
        self._element_x_starts = np.asarray(element_x_starts, dtype=float)
        self._element_x_ends = np.asarray(element_x_ends, dtype=float)
        self._element_coefficients = np.asarray(
            element_coefficients,
            dtype=float,
        )
        self._longitudinal_shape_coefficients = np.asarray(
            longitudinal_shape_coefficients,
            dtype=float,
        )
        self._transverse_power_coefficients = np.asarray(
            transverse_power_coefficients,
            dtype=float,
        )
        self._metadata = dict(metadata or {})
        self._validate()

        for value in (
            self._element_x_starts,
            self._element_x_ends,
            self._element_coefficients,
            self._longitudinal_shape_coefficients,
            self._transverse_power_coefficients,
        ):
            value.setflags(write=False)

    @classmethod
    def from_solution_data(
        cls,
        *,
        mesh,
        dof_layout,
        solved_dofs,
        basis,
        metadata=None,
    ):
        """Compile the solved FE/CUF coefficients into a reusable field.

        Return ``None`` when the selected expansion does not expose the
        optional polynomial checkpoint representation.  Unsupported
        expansions continue to use the existing in-memory recovery path and
        are not altered by this feature.
        """

        export = getattr(basis, "power_coefficients", None)
        if not callable(export):
            return None

        solved_dofs = np.asarray(solved_dofs, dtype=float)
        if solved_dofs.shape != (dof_layout.total_dofs,):
            raise ValueError(
                "solved_dofs size is inconsistent with DOF layout"
            )
        if not np.all(np.isfinite(solved_dofs)):
            raise ValueError("solved_dofs contains non-finite values")

        elements = tuple(mesh.elements)
        if not elements:
            raise ValueError("compiled displacement requires an element")

        local_node_count = len(elements[0].node_ids)
        if any(len(element.node_ids) != local_node_count for element in elements):
            raise ValueError(
                "compiled displacement requires one longitudinal order"
            )

        element_coefficients = np.empty(
            (
                len(elements),
                local_node_count,
                dof_layout.basis_size,
                3,
            ),
            dtype=float,
        )
        for element_index, element in enumerate(elements):
            for local_node, global_node in enumerate(element.node_ids):
                first = global_node * dof_layout.dofs_per_node
                last = first + dof_layout.dofs_per_node
                element_coefficients[element_index, local_node, :, :] = (
                    solved_dofs[first:last].reshape(dof_layout.basis_size, 3)
                )

        reference_nodes = np.asarray(
            elements[0].reference_nodes,
            dtype=float,
        )
        longitudinal_coefficients = cls._lagrange_power_coefficients(
            reference_nodes
        )
        transverse_coefficients = np.asarray(export(), dtype=float)

        combined_metadata = dict(metadata or {})
        combined_metadata.update(
            {
                "format": _FORMAT_NAME,
                "format_version": _FORMAT_VERSION,
                "basis_class": (
                    f"{basis.__class__.__module__}."
                    f"{basis.__class__.__qualname__}"
                ),
                "basis_order": int(basis.order),
                "basis_size": int(basis.size),
                "components": ["ux", "uy", "uz"],
            }
        )

        return cls(
            element_x_starts=[element.x_start for element in elements],
            element_x_ends=[element.x_end for element in elements],
            element_coefficients=element_coefficients,
            longitudinal_shape_coefficients=longitudinal_coefficients,
            transverse_power_coefficients=transverse_coefficients,
            metadata=combined_metadata,
        )

    @staticmethod
    def _lagrange_power_coefficients(nodes: np.ndarray) -> np.ndarray:
        """Return Lagrange shape functions in ascending reference powers."""

        count = int(nodes.size)
        result = np.empty((count, count), dtype=float)
        for index in range(count):
            other_nodes = np.delete(nodes, index)
            denominator = np.prod(nodes[index] - other_nodes)
            result[index, :] = np.poly(other_nodes)[::-1] / denominator
        return result

    def _validate(self) -> None:
        starts = self._element_x_starts
        ends = self._element_x_ends
        coefficients = self._element_coefficients
        longitudinal = self._longitudinal_shape_coefficients
        transverse = self._transverse_power_coefficients

        if starts.ndim != 1 or ends.shape != starts.shape or starts.size < 1:
            raise ValueError("element bounds have invalid shape")
        if not np.all(np.isfinite(starts)) or not np.all(np.isfinite(ends)):
            raise ValueError("element bounds contain non-finite values")
        if np.any(ends <= starts):
            raise ValueError("every element must have positive length")
        if np.any(starts[1:] != ends[:-1]):
            raise ValueError("element bounds must be contiguous")
        if coefficients.ndim != 4 or coefficients.shape[0] != starts.size:
            raise ValueError("element coefficients have invalid shape")
        if coefficients.shape[3] != 3:
            raise ValueError("displacement coefficients require 3 components")
        if longitudinal.shape != (
            coefficients.shape[1],
            coefficients.shape[1],
        ):
            raise ValueError("longitudinal coefficients have invalid shape")
        if transverse.ndim != 3 or transverse.shape[0] != coefficients.shape[2]:
            raise ValueError("transverse coefficients have invalid shape")
        if not all(
            np.all(np.isfinite(value))
            for value in (coefficients, longitudinal, transverse)
        ):
            raise ValueError("compiled displacement contains non-finite data")

    @property
    def metadata(self) -> dict:
        return dict(self._metadata)

    @property
    def x_start(self) -> float:
        return float(self._element_x_starts[0])

    @property
    def x_end(self) -> float:
        return float(self._element_x_ends[-1])

    def _element_index(self, x: float) -> int:
        if not np.isfinite(x):
            raise ValueError("x must be finite")
        if x < self.x_start or x > self.x_end:
            raise ValueError(
                f"x={x} lies outside longitudinal domain "
                f"[{self.x_start}, {self.x_end}]"
            )
        index = int(np.searchsorted(self._element_x_ends, x, side="right"))
        return min(index, self._element_x_ends.size - 1)

    def section_evaluator(self, x: float):
        """Compile one fixed-x section evaluator from persisted coefficients."""

        x = float(x)
        index = self._element_index(x)
        start = float(self._element_x_starts[index])
        end = float(self._element_x_ends[index])
        xi = 2.0 * (x - start) / (end - start) - 1.0

        xi_powers = np.power(
            xi,
            np.arange(self._longitudinal_shape_coefficients.shape[1]),
        )
        shape_values = self._longitudinal_shape_coefficients @ xi_powers
        amplitudes = np.tensordot(
            shape_values,
            self._element_coefficients[index],
            axes=(0, 0),
        )

        # Compile the three final section-displacement polynomials once for
        # this x.  This contracts the CUF tau dimension here instead of at
        # every (y,z) query:
        #
        #   U[p,q,i] = sum_tau C[tau,p,q] * u_tau,i(x)
        #
        # Dense post-processing can then evaluate u_x, u_y and u_z together
        # with one small matrix product, independent of basis.size.
        section_power_coefficients = np.tensordot(
            self._transverse_power_coefficients,
            amplitudes,
            axes=(0, 0),
        )
        section_power_coefficients = np.asarray(
            section_power_coefficients,
            dtype=float,
        ).reshape(-1, 3)
        section_power_coefficients.setflags(write=False)

        def evaluate(y: float, z: float) -> np.ndarray:
            y = float(y)
            z = float(z)
            if not np.isfinite(y) or not np.isfinite(z):
                raise ValueError("y and z must be finite")
            y_powers = np.power(
                y,
                np.arange(self._transverse_power_coefficients.shape[1]),
            )
            z_powers = np.power(
                z,
                np.arange(self._transverse_power_coefficients.shape[2]),
            )
            monomials = np.multiply.outer(y_powers, z_powers).reshape(-1)
            displacement = monomials @ section_power_coefficients
            return np.asarray(displacement, dtype=float)

        return evaluate

    def __call__(self, x: float, y: float, z: float) -> np.ndarray:
        return self.section_evaluator(float(x))(float(y), float(z))

    def save_atomic(self, path: str | Path) -> tuple[Path, str]:
        """Atomically save and verify the self-contained NPZ checkpoint."""

        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata_json = json.dumps(
            self._metadata,
            sort_keys=True,
            separators=(",", ":"),
        )

        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                np.savez_compressed(
                    stream,
                    format_version=np.asarray(_FORMAT_VERSION, dtype=np.int64),
                    metadata_json=np.asarray(metadata_json),
                    element_x_starts=self._element_x_starts,
                    element_x_ends=self._element_x_ends,
                    element_coefficients=self._element_coefficients,
                    longitudinal_shape_coefficients=(
                        self._longitudinal_shape_coefficients
                    ),
                    transverse_power_coefficients=(
                        self._transverse_power_coefficients
                    ),
                )
                stream.flush()
                os.fsync(stream.fileno())

            verified = type(self).load(temporary_path)
            if verified.metadata != self.metadata:
                raise RuntimeError("checkpoint metadata verification failed")
            os.replace(temporary_path, path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return path, digest

    @classmethod
    def load(cls, path: str | Path):
        """Load a self-contained displacement checkpoint without YAML files."""

        path = Path(path).resolve()
        with np.load(path, allow_pickle=False) as archive:
            version = int(np.asarray(archive["format_version"]).item())
            if version != _FORMAT_VERSION:
                raise ValueError(
                    f"unsupported displacement checkpoint version {version}"
                )
            metadata = json.loads(str(np.asarray(archive["metadata_json"]).item()))
            if metadata.get("format") != _FORMAT_NAME:
                raise ValueError("invalid displacement checkpoint format")
            return cls(
                element_x_starts=archive["element_x_starts"],
                element_x_ends=archive["element_x_ends"],
                element_coefficients=archive["element_coefficients"],
                longitudinal_shape_coefficients=(
                    archive["longitudinal_shape_coefficients"]
                ),
                transverse_power_coefficients=(
                    archive["transverse_power_coefficients"]
                ),
                metadata=metadata,
            )
