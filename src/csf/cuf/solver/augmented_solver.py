# OPT-08 KKT DIAGNOSTICS AND CHECKPOINT
"""
Generic solver for an augmented linear-constraint system.

The system is assumed to have the form

    [ K   A^T ] [ q      ] = [ f ]
    [ A    0  ] [ lambda ]   [ b ]

as produced by ``LinearConstraintAugmenter``.

The validated sparse direct solve remains the primary numerical path.  If that
solution does not satisfy the requested residual tolerances and the augmented
matrix is already sufficiently dense, the same algebraic system is also solved
with dense LAPACK factorizations suitable for high-order KKT systems.

Every candidate solution is verified against the original, unmodified system.
If all numerical paths fail the residual checks, the exact assembled KKT system,
right-hand side, candidate solutions, residual vectors, scale diagnostics, and
solver warnings are checkpointed under ``diagnostics/`` for offline analysis.
No geometry, material, load, CUF basis, benchmark, tolerance, or structural
specialization is introduced here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import warnings

import numpy as np
from scipy.linalg import LinAlgError, LinAlgWarning, solve as dense_solve
from scipy.sparse import save_npz
from scipy.sparse.linalg import MatrixRankWarning, spsolve

from csf.cuf.solver.linear_constraint import (
    AugmentedLinearConstraintSystem,
)


@dataclass(frozen=True)
class AugmentedConstraintSolution:
    """
    Solution of a Lagrange-multiplier constrained system.
    """

    primal: np.ndarray
    lagrange: np.ndarray
    augmented: np.ndarray

    augmented_residual_norm: float
    augmented_relative_residual: float

    equilibrium_residual_norm: float
    equilibrium_relative_residual: float

    constraint_residual_norm: float

    converged: bool


class AugmentedSparseLinearSolver:
    """
    Direct solution of a generic augmented constraint system.

    ``spsolve`` is retained unchanged as the primary path.  A dense secondary
    path is used only when the sparse solution fails the residual checks and
    the augmented matrix is already sufficiently dense for dense storage to be
    reasonable.
    """

    # A high-order CUF matrix can become nearly full.  Below this density the
    # sparse representation remains the appropriate default numerical path.
    _DENSE_MIN_DENSITY = 0.50

    # Estimated peak for one persistent dense matrix plus one LAPACK work copy.
    # This is a numerical-memory guard, not a model-order or benchmark limit.
    _DENSE_MAX_ESTIMATED_BYTES = 2 * 1024**3

    def __init__(
        self,
        *,
        relative_tolerance: float = 1.0e-9,
        absolute_tolerance: float = 1.0e-8,
        constraint_tolerance: float = 1.0e-8,
    ) -> None:
        for name, value in (
            ("relative_tolerance", relative_tolerance),
            ("absolute_tolerance", absolute_tolerance),
            ("constraint_tolerance", constraint_tolerance),
        ):
            value = float(value)

            if not np.isfinite(value) or value <= 0.0:
                raise ValueError(
                    f"{name} must be finite and positive"
                )

        self.relative_tolerance = float(relative_tolerance)
        self.absolute_tolerance = float(absolute_tolerance)
        self.constraint_tolerance = float(constraint_tolerance)

    @staticmethod
    def _direct_sparse_solve(matrix, rhs: np.ndarray) -> np.ndarray:
        """Solve one sparse linear system and promote rank warnings to errors."""
        with warnings.catch_warnings():
            warnings.simplefilter(
                "error",
                MatrixRankWarning,
            )

            try:
                solution = np.asarray(
                    spsolve(
                        matrix,
                        rhs,
                    ),
                    dtype=float,
                )
            except MatrixRankWarning as exc:
                raise RuntimeError(
                    "augmented linear system is rank deficient"
                ) from exc

        if solution.shape != rhs.shape:
            raise RuntimeError(
                "augmented solver returned an unexpected solution shape"
            )

        if not np.all(np.isfinite(solution)):
            raise RuntimeError(
                "augmented solver returned non-finite values"
            )

        return solution

    @staticmethod
    def _direct_dense_solve(
        dense_matrix: np.ndarray,
        rhs: np.ndarray,
        *,
        assume_a: str,
    ) -> tuple[np.ndarray, list[str]]:
        """Solve a dense system and retain LAPACK ill-conditioning warnings."""
        work_matrix = np.array(
            dense_matrix,
            dtype=float,
            order="F",
            copy=True,
        )
        work_rhs = np.asarray(
            rhs,
            dtype=float,
        ).copy()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", LinAlgWarning)

            try:
                solution = np.asarray(
                    dense_solve(
                        work_matrix,
                        work_rhs,
                        assume_a=assume_a,
                        overwrite_a=True,
                        overwrite_b=True,
                        check_finite=False,
                    ),
                    dtype=float,
                )
            except LinAlgError as exc:
                raise RuntimeError(
                    f"dense LAPACK solve failed for assume_a={assume_a!r}"
                ) from exc

        warning_messages = [
            str(item.message)
            for item in caught
            if issubclass(item.category, LinAlgWarning)
        ]

        if solution.shape != rhs.shape:
            raise RuntimeError(
                "dense augmented solver returned an unexpected solution shape"
            )

        if not np.all(np.isfinite(solution)):
            raise RuntimeError(
                "dense augmented solver returned non-finite values"
            )

        return solution, warning_messages

    @classmethod
    def _dense_path_status(cls, matrix) -> tuple[bool, float, int]:
        """Return whether dense storage is appropriate for this matrix."""
        n = int(matrix.shape[0])
        total_entries = n * n
        density = (
            float(matrix.nnz) / float(total_entries)
            if total_entries > 0
            else 0.0
        )

        # One retained dense matrix plus one factorization work copy.
        estimated_bytes = 2 * total_entries * np.dtype(float).itemsize

        allowed = (
            density >= cls._DENSE_MIN_DENSITY
            and estimated_bytes <= cls._DENSE_MAX_ESTIMATED_BYTES
        )

        return allowed, density, estimated_bytes

    @staticmethod
    def _safe_key(name: str) -> str:
        """Return a stable NumPy-archive key from a solver-candidate label."""
        key = re.sub(r"[^0-9A-Za-z]+", "_", str(name)).strip("_").lower()
        return key or "candidate"

    @staticmethod
    def _positive_range(values: np.ndarray) -> dict:
        """Return min/max/dynamic-range statistics for nonzero finite magnitudes."""
        magnitude = np.abs(np.asarray(values, dtype=float).ravel())
        valid = magnitude[np.isfinite(magnitude) & (magnitude > 0.0)]

        if valid.size == 0:
            return {
                "min_abs_nonzero": None,
                "max_abs": 0.0,
                "dynamic_range": None,
            }

        minimum = float(np.min(valid))
        maximum = float(np.max(valid))
        return {
            "min_abs_nonzero": minimum,
            "max_abs": maximum,
            "dynamic_range": (
                maximum / minimum
                if minimum > 0.0
                else None
            ),
        }

    @staticmethod
    def _top_indices(values: np.ndarray, count: int = 20) -> list[int]:
        """Indices of the largest absolute entries, ordered descending."""
        values = np.asarray(values, dtype=float).ravel()
        if values.size == 0:
            return []

        count = min(int(count), int(values.size))
        absolute = np.abs(values)

        if count == values.size:
            indices = np.arange(values.size)
        else:
            indices = np.argpartition(absolute, -count)[-count:]

        order = np.argsort(absolute[indices])[::-1]
        return [int(index) for index in indices[order]]

    @staticmethod
    def _symmetry_metrics_dense(
        dense_matrix: np.ndarray | None,
        *,
        chunk_rows: int = 128,
    ) -> dict:
        """Measure symmetry without allocating a second full dense matrix."""
        if dense_matrix is None:
            return {
                "available": False,
                "max_abs_defect": None,
                "relative_frobenius_defect": None,
            }

        n = int(dense_matrix.shape[0])
        defect_sq = 0.0
        reference_sq = float(
            np.dot(dense_matrix.ravel(order="K"), dense_matrix.ravel(order="K"))
        )
        max_abs_defect = 0.0

        for start in range(0, n, int(chunk_rows)):
            stop = min(start + int(chunk_rows), n)
            difference = (
                dense_matrix[start:stop, :]
                - dense_matrix[:, start:stop].T
            )
            if difference.size:
                max_abs_defect = max(
                    max_abs_defect,
                    float(np.max(np.abs(difference))),
                )
                defect_sq += float(
                    np.dot(difference.ravel(), difference.ravel())
                )

        return {
            "available": True,
            "max_abs_defect": max_abs_defect,
            "relative_frobenius_defect": (
                float(np.sqrt(defect_sq / reference_sq))
                if reference_sq > 0.0
                else 0.0
            ),
        }

    def _write_failure_diagnostics(
        self,
        *,
        matrix,
        rhs: np.ndarray,
        K,
        f: np.ndarray,
        A: np.ndarray,
        b: np.ndarray,
        candidates: list[tuple],
        dense_warnings: dict[str, list[str]],
        dense_errors: list[str],
        reason: str,
        dense_matrix: np.ndarray | None,
        best_name: str | None,
    ) -> Path | None:
        """Persist the failed KKT system and detailed residual diagnostics."""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
            primal_size = int(K.shape[0])
            constraint_count = int(A.shape[0])
            augmented_size = int(matrix.shape[0])

            root_text = os.environ.get("CSF_CUF_DIAGNOSTICS_DIR")
            root = (
                Path(root_text).expanduser()
                if root_text
                else Path.cwd() / "diagnostics"
            )
            folder = root / (
                f"kkt_failure_q{primal_size}_c{constraint_count}_{timestamp}"
            )
            folder.mkdir(parents=True, exist_ok=False)

            # The sparse checkpoint is the authoritative system to reuse in all
            # later solver experiments.  No re-assembly is required.
            save_npz(
                folder / "kkt_matrix.npz",
                matrix.tocsr(),
                compressed=True,
            )
            np.save(folder / "rhs.npy", np.asarray(rhs, dtype=float))

            # Work from one absolute-value data vector instead of copying the
            # whole sparse matrix; this keeps the diagnostic memory overhead
            # bounded even when the KKT matrix is already very dense.
            abs_data = np.abs(matrix.data)
            row_abs_sum = np.zeros(augmented_size, dtype=float)
            row_max_abs = np.zeros(augmented_size, dtype=float)
            for row in range(augmented_size):
                start = int(matrix.indptr[row])
                stop = int(matrix.indptr[row + 1])
                if stop > start:
                    row_values = abs_data[start:stop]
                    row_abs_sum[row] = float(np.sum(row_values))
                    row_max_abs[row] = float(np.max(row_values))

            if matrix.nnz:
                col_abs_sum = np.bincount(
                    matrix.indices,
                    weights=abs_data,
                    minlength=augmented_size,
                ).astype(float, copy=False)
                col_max_abs = np.zeros(augmented_size, dtype=float)
                np.maximum.at(
                    col_max_abs,
                    matrix.indices,
                    abs_data,
                )
            else:
                col_abs_sum = np.zeros(augmented_size, dtype=float)
                col_max_abs = np.zeros(augmented_size, dtype=float)

            del abs_data

            np.savez_compressed(
                folder / "row_col_scales.npz",
                row_max_abs=row_max_abs,
                col_max_abs=col_max_abs,
                row_abs_sum=row_abs_sum,
                col_abs_sum=col_abs_sum,
            )

            symmetry = self._symmetry_metrics_dense(dense_matrix)
            matrix_range = self._positive_range(matrix.data)
            stiffness_range = self._positive_range(K.data)
            constraint_range = self._positive_range(A)
            rhs_range = self._positive_range(rhs)

            candidate_arrays = {}
            candidate_metadata = []
            report_lines = [
                "OPT-08 KKT FAILURE DIAGNOSTICS",
                "================================",
                "",
                f"reason: {reason}",
                f"timestamp_utc: {timestamp}",
                f"augmented_size: {augmented_size}",
                f"primal_size: {primal_size}",
                f"constraint_count: {constraint_count}",
                f"nnz: {int(matrix.nnz)}",
                f"density: {float(matrix.nnz) / max(augmented_size * augmented_size, 1):.12g}",
                f"relative_tolerance: {self.relative_tolerance:.16e}",
                f"absolute_tolerance: {self.absolute_tolerance:.16e}",
                f"constraint_tolerance: {self.constraint_tolerance:.16e}",
                f"best_candidate: {best_name or 'none'}",
                "",
                "MATRIX / BLOCK SCALES",
                "---------------------",
                f"||KKT||_1: {float(np.max(col_abs_sum)) if col_abs_sum.size else 0.0:.16e}",
                f"||KKT||_inf: {float(np.max(row_abs_sum)) if row_abs_sum.size else 0.0:.16e}",
                f"||KKT||_F: {float(np.linalg.norm(matrix.data)):.16e}",
                f"||rhs||_2: {float(np.linalg.norm(rhs)):.16e}",
                f"||f||_2: {float(np.linalg.norm(f)):.16e}",
                f"||b||_2: {float(np.linalg.norm(b)):.16e}",
                f"KKT min|a_ij| nonzero: {matrix_range['min_abs_nonzero']}",
                f"KKT max|a_ij|: {matrix_range['max_abs']}",
                f"KKT coefficient dynamic range: {matrix_range['dynamic_range']}",
                f"K min|k_ij| nonzero: {stiffness_range['min_abs_nonzero']}",
                f"K max|k_ij|: {stiffness_range['max_abs']}",
                f"K coefficient dynamic range: {stiffness_range['dynamic_range']}",
                f"C min|c_ij| nonzero: {constraint_range['min_abs_nonzero']}",
                f"C max|c_ij|: {constraint_range['max_abs']}",
                f"C coefficient dynamic range: {constraint_range['dynamic_range']}",
                f"symmetry available: {symmetry['available']}",
                f"max|KKT-KKT^T|: {symmetry['max_abs_defect']}",
                f"||KKT-KKT^T||_F / ||KKT||_F: {symmetry['relative_frobenius_defect']}",
                "",
                "ROW SCALE EXTREMES",
                "------------------",
            ]

            largest_rows = self._top_indices(row_max_abs, 20)
            positive_rows = np.flatnonzero(row_max_abs > 0.0)
            smallest_rows = (
                positive_rows[np.argsort(row_max_abs[positive_rows])[:20]].tolist()
                if positive_rows.size
                else []
            )

            report_lines.append("largest max-abs row coefficients:")
            for index in largest_rows:
                block = "equilibrium" if index < primal_size else "constraint"
                local = index if index < primal_size else index - primal_size
                report_lines.append(
                    f"  row={index:6d} block={block:11s} local={local:6d} "
                    f"max_abs={row_max_abs[index]:.16e} "
                    f"abs_sum={row_abs_sum[index]:.16e}"
                )

            report_lines.append("smallest nonzero max-abs row coefficients:")
            for index in smallest_rows:
                index = int(index)
                block = "equilibrium" if index < primal_size else "constraint"
                local = index if index < primal_size else index - primal_size
                report_lines.append(
                    f"  row={index:6d} block={block:11s} local={local:6d} "
                    f"max_abs={row_max_abs[index]:.16e} "
                    f"abs_sum={row_abs_sum[index]:.16e}"
                )

            report_lines.extend([
                "",
                "SOLVER CANDIDATES",
                "-----------------",
            ])

            for name, solution, metrics in candidates:
                key = self._safe_key(name)
                q_local, lagrange_local = metrics[0], metrics[1]
                augmented_residual = matrix @ solution - rhs
                equilibrium_residual = K @ q_local + A.T @ lagrange_local - f
                constraint_residual = A @ q_local - b

                candidate_arrays[f"{key}_solution"] = np.asarray(solution, dtype=float)
                candidate_arrays[f"{key}_augmented_residual"] = np.asarray(
                    augmented_residual,
                    dtype=float,
                )
                candidate_arrays[f"{key}_equilibrium_residual"] = np.asarray(
                    equilibrium_residual,
                    dtype=float,
                )
                candidate_arrays[f"{key}_constraint_residual"] = np.asarray(
                    constraint_residual,
                    dtype=float,
                )

                warnings_for_candidate = list(dense_warnings.get(name, []))
                candidate_metadata.append({
                    "name": name,
                    "augmented_residual_norm": float(metrics[2]),
                    "augmented_relative_residual": float(metrics[3]),
                    "equilibrium_residual_norm": float(metrics[4]),
                    "equilibrium_relative_residual": float(metrics[5]),
                    "constraint_residual_norm": float(metrics[6]),
                    "converged": bool(metrics[7]),
                    "solution_norm_2": float(np.linalg.norm(solution)),
                    "primal_norm_2": float(np.linalg.norm(q_local)),
                    "lagrange_norm_2": float(np.linalg.norm(lagrange_local)),
                    "warnings": warnings_for_candidate,
                })

                report_lines.extend([
                    "",
                    f"[{name}]",
                    f"  augmented_norm: {metrics[2]:.16e}",
                    f"  augmented_rel: {metrics[3]:.16e}",
                    f"  equilibrium_norm: {metrics[4]:.16e}",
                    f"  equilibrium_rel: {metrics[5]:.16e}",
                    f"  constraint_norm: {metrics[6]:.16e}",
                    f"  ||solution||_2: {float(np.linalg.norm(solution)):.16e}",
                    f"  ||q||_2: {float(np.linalg.norm(q_local)):.16e}",
                    f"  ||lambda||_2: {float(np.linalg.norm(lagrange_local)):.16e}",
                ])

                for warning_message in warnings_for_candidate:
                    report_lines.append(f"  warning: {warning_message}")

                report_lines.append("  largest augmented residual equations:")
                for index in self._top_indices(augmented_residual, 20):
                    block = "equilibrium" if index < primal_size else "constraint"
                    local = index if index < primal_size else index - primal_size
                    report_lines.append(
                        f"    row={index:6d} block={block:11s} local={local:6d} "
                        f"residual={augmented_residual[index]: .16e} "
                        f"abs={abs(augmented_residual[index]):.16e}"
                    )

                report_lines.append("  largest equilibrium residual DOFs:")
                for index in self._top_indices(equilibrium_residual, 20):
                    report_lines.append(
                        f"    dof={index:6d} residual={equilibrium_residual[index]: .16e} "
                        f"abs={abs(equilibrium_residual[index]):.16e}"
                    )

                report_lines.append("  largest constraint residual equations:")
                for index in self._top_indices(constraint_residual, 20):
                    report_lines.append(
                        f"    constraint={index:6d} residual={constraint_residual[index]: .16e} "
                        f"abs={abs(constraint_residual[index]):.16e}"
                    )

            np.savez_compressed(
                folder / "candidate_solutions_and_residuals.npz",
                **candidate_arrays,
            )

            metadata = {
                "version": "OPT-08 KKT DIAGNOSTICS AND CHECKPOINT",
                "timestamp_utc": timestamp,
                "reason": reason,
                "best_candidate": best_name,
                "sizes": {
                    "augmented": augmented_size,
                    "primal": primal_size,
                    "constraints": constraint_count,
                },
                "sparsity": {
                    "nnz": int(matrix.nnz),
                    "density": float(matrix.nnz) / max(augmented_size * augmented_size, 1),
                },
                "tolerances": {
                    "relative": self.relative_tolerance,
                    "absolute": self.absolute_tolerance,
                    "constraint": self.constraint_tolerance,
                },
                "norms": {
                    "kkt_1": float(np.max(col_abs_sum)) if col_abs_sum.size else 0.0,
                    "kkt_inf": float(np.max(row_abs_sum)) if row_abs_sum.size else 0.0,
                    "kkt_fro": float(np.linalg.norm(matrix.data)),
                    "rhs_2": float(np.linalg.norm(rhs)),
                    "load_2": float(np.linalg.norm(f)),
                    "constraint_rhs_2": float(np.linalg.norm(b)),
                },
                "ranges": {
                    "kkt": matrix_range,
                    "stiffness": stiffness_range,
                    "constraint_matrix": constraint_range,
                    "rhs": rhs_range,
                },
                "symmetry": symmetry,
                "dense_warnings": dense_warnings,
                "dense_errors": list(dense_errors),
                "candidates": candidate_metadata,
                "files": {
                    "kkt_matrix": "kkt_matrix.npz",
                    "rhs": "rhs.npy",
                    "row_col_scales": "row_col_scales.npz",
                    "candidate_data": "candidate_solutions_and_residuals.npz",
                    "report": "residual_report.txt",
                },
            }

            (folder / "metadata.json").write_text(
                json.dumps(metadata, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            (folder / "residual_report.txt").write_text(
                "\n".join(report_lines) + "\n",
                encoding="utf-8",
            )

            print(f"[solver] diagnostic checkpoint saved: {folder}")
            return folder

        except Exception as exc:  # Diagnostics must never mask the solver failure.
            print(
                "[solver] WARNING: failed to write diagnostic checkpoint: "
                f"{type(exc).__name__}: {exc}"
            )
            return None

    def solve(
        self,
        system: AugmentedLinearConstraintSystem,
    ) -> AugmentedConstraintSolution:
        matrix = system.matrix.tocsr()

        rhs = np.asarray(
            system.rhs,
            dtype=float,
        )

        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(
                "augmented matrix must be square"
            )

        if rhs.shape != (matrix.shape[0],):
            raise ValueError(
                "augmented rhs size does not match matrix"
            )

        if not np.all(np.isfinite(matrix.data)):
            raise ValueError(
                "augmented matrix contains non-finite values"
            )

        if not np.all(np.isfinite(rhs)):
            raise ValueError(
                "augmented rhs contains non-finite values"
            )

        original = system.original_system
        constraints = system.constraints

        K = original.stiffness.tocsr()
        f = np.asarray(
            original.load,
            dtype=float,
        )

        A = np.asarray(
            constraints.matrix,
            dtype=float,
        )

        b = np.asarray(
            constraints.rhs,
            dtype=float,
        )

        def residual_metrics(solution: np.ndarray) -> tuple:
            q_local, lagrange_local = system.split_solution(
                solution
            )

            augmented_residual = (
                matrix @ solution
                - rhs
            )
            augmented_residual_norm = float(
                np.linalg.norm(
                    augmented_residual
                )
            )
            augmented_relative_residual = (
                augmented_residual_norm
                / max(
                    float(np.linalg.norm(rhs)),
                    1.0,
                )
            )

            equilibrium_residual = (
                K @ q_local
                + A.T @ lagrange_local
                - f
            )
            constraint_residual = (
                A @ q_local
                - b
            )

            equilibrium_residual_norm = float(
                np.linalg.norm(
                    equilibrium_residual
                )
            )
            equilibrium_relative_residual = (
                equilibrium_residual_norm
                / max(
                    float(np.linalg.norm(f)),
                    1.0,
                )
            )
            constraint_residual_norm = float(
                np.linalg.norm(
                    constraint_residual
                )
            )

            algebraic_ok = (
                augmented_residual_norm <= self.absolute_tolerance
                or augmented_relative_residual <= self.relative_tolerance
            )
            equilibrium_ok = (
                equilibrium_residual_norm <= self.absolute_tolerance
                or equilibrium_relative_residual <= self.relative_tolerance
            )
            constraint_ok = (
                constraint_residual_norm <= self.constraint_tolerance
            )
            converged = (
                algebraic_ok
                and equilibrium_ok
                and constraint_ok
            )

            return (
                q_local,
                lagrange_local,
                augmented_residual_norm,
                augmented_relative_residual,
                equilibrium_residual_norm,
                equilibrium_relative_residual,
                constraint_residual_norm,
                converged,
            )

        def score(metrics: tuple) -> float:
            return max(
                metrics[3],
                metrics[5],
                metrics[6] / max(self.constraint_tolerance, 1.0e-300),
            )

        # Preserve the validated sparse direct solve exactly.  Cases that
        # already satisfy the tolerances never enter the dense path.
        sparse_solution = self._direct_sparse_solve(
            matrix,
            rhs,
        )
        sparse_metrics = residual_metrics(
            sparse_solution
        )

        candidates = [
            ("sparse direct", sparse_solution, sparse_metrics),
        ]
        dense_errors: list[str] = []
        dense_warnings: dict[str, list[str]] = {}
        dense_matrix = None

        if sparse_metrics[7]:
            selected_solution = sparse_solution
            selected_metrics = sparse_metrics
        else:
            dense_allowed, density, estimated_bytes = self._dense_path_status(
                matrix
            )

            print(
                "[solver] sparse direct failed residual check: "
                f"augmented_rel={sparse_metrics[3]:.6e}, "
                f"equilibrium_rel={sparse_metrics[5]:.6e}, "
                f"constraint={sparse_metrics[6]:.6e}"
            )

            if not dense_allowed:
                reason = (
                    "sparse direct failed residual checks and dense path was "
                    "not enabled by the density/memory guard"
                )
                diagnostic_path = self._write_failure_diagnostics(
                    matrix=matrix,
                    rhs=rhs,
                    K=K,
                    f=f,
                    A=A,
                    b=b,
                    candidates=candidates,
                    dense_warnings=dense_warnings,
                    dense_errors=dense_errors,
                    reason=reason,
                    dense_matrix=dense_matrix,
                    best_name="sparse direct",
                )
                raise RuntimeError(
                    "augmented sparse solution did not satisfy tolerances and "
                    "dense high-order solve was not enabled for this matrix: "
                    f"density={density:.6f}, "
                    f"estimated_dense_peak_mib={estimated_bytes / 1024**2:.1f}, "
                    f"augmented_rel={sparse_metrics[3]:.6e}, "
                    f"equilibrium_rel={sparse_metrics[5]:.6e}, "
                    f"constraint={sparse_metrics[6]:.6e}, "
                    f"diagnostics={diagnostic_path}"
                )

            print(
                "[solver] dense high-order path: "
                f"density={density:.4f}, "
                f"estimated_peak={estimated_bytes / 1024**2:.1f} MiB"
            )

            dense_matrix = matrix.toarray(order="F")

            try:
                symmetric_solution, symmetric_warning_messages = (
                    self._direct_dense_solve(
                        dense_matrix,
                        rhs,
                        assume_a="sym",
                    )
                )
                dense_warnings["dense symmetric"] = symmetric_warning_messages
                symmetric_metrics = residual_metrics(
                    symmetric_solution
                )
                candidates.append(
                    ("dense symmetric", symmetric_solution, symmetric_metrics)
                )
                print(
                    "[solver] dense symmetric: "
                    f"augmented_rel={symmetric_metrics[3]:.6e}, "
                    f"equilibrium_rel={symmetric_metrics[5]:.6e}, "
                    f"constraint={symmetric_metrics[6]:.6e}"
                )
            except RuntimeError as exc:
                symmetric_metrics = None
                dense_errors.append(f"dense symmetric: {exc}")
                print(f"[solver] dense symmetric failed: {exc}")

            if symmetric_metrics is not None and symmetric_metrics[7]:
                selected_solution = symmetric_solution
                selected_metrics = symmetric_metrics
                print("[solver] selected = dense symmetric")
            else:
                try:
                    general_solution, general_warning_messages = (
                        self._direct_dense_solve(
                            dense_matrix,
                            rhs,
                            assume_a="gen",
                        )
                    )
                    dense_warnings["dense general LU"] = general_warning_messages
                    general_metrics = residual_metrics(
                        general_solution
                    )
                    candidates.append(
                        ("dense general LU", general_solution, general_metrics)
                    )
                    print(
                        "[solver] dense general LU: "
                        f"augmented_rel={general_metrics[3]:.6e}, "
                        f"equilibrium_rel={general_metrics[5]:.6e}, "
                        f"constraint={general_metrics[6]:.6e}"
                    )
                except RuntimeError as exc:
                    general_metrics = None
                    dense_errors.append(f"dense general LU: {exc}")
                    print(f"[solver] dense general LU failed: {exc}")

                converged_candidates = [
                    item
                    for item in candidates
                    if item[2][7]
                ]

                if converged_candidates:
                    best = min(
                        converged_candidates,
                        key=lambda item: score(item[2]),
                    )
                    _, selected_solution, selected_metrics = best
                    print(f"[solver] selected = {best[0]}")
                else:
                    best = min(
                        candidates,
                        key=lambda item: score(item[2]),
                    )
                    dense_error_text = (
                        "; ".join(dense_errors)
                        if dense_errors
                        else "none"
                    )

                    detail_parts = []
                    for name, _, metrics in candidates:
                        detail_parts.append(
                            f"{name}: augmented_rel={metrics[3]:.6e}, "
                            f"equilibrium_rel={metrics[5]:.6e}, "
                            f"constraint={metrics[6]:.6e}"
                        )

                    reason = (
                        "no sparse or dense high-order KKT candidate satisfied "
                        "the original residual tolerances"
                    )
                    diagnostic_path = self._write_failure_diagnostics(
                        matrix=matrix,
                        rhs=rhs,
                        K=K,
                        f=f,
                        A=A,
                        b=b,
                        candidates=candidates,
                        dense_warnings=dense_warnings,
                        dense_errors=dense_errors,
                        reason=reason,
                        dense_matrix=dense_matrix,
                        best_name=best[0],
                    )

                    raise RuntimeError(
                        "augmented solution did not satisfy tolerances after "
                        "high-order dense KKT solves: "
                        + " | ".join(detail_parts)
                        + f" | best={best[0]}"
                        + f" | dense_errors={dense_error_text}"
                        + f" | diagnostics={diagnostic_path}"
                    )

        (
            q,
            lagrange,
            augmented_residual_norm,
            augmented_relative_residual,
            equilibrium_residual_norm,
            equilibrium_relative_residual,
            constraint_residual_norm,
            converged,
        ) = selected_metrics

        return AugmentedConstraintSolution(
            primal=q,
            lagrange=lagrange,
            augmented=selected_solution,
            augmented_residual_norm=augmented_residual_norm,
            augmented_relative_residual=augmented_relative_residual,
            equilibrium_residual_norm=equilibrium_residual_norm,
            equilibrium_relative_residual=equilibrium_relative_residual,
            constraint_residual_norm=constraint_residual_norm,
            converged=converged,
        )
