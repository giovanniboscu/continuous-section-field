# Version: CSF-CUF YAML-configurable equilibration iterations v16 - 2026-09-12
"""
Generic direct solver for an augmented linear-constraint system.

The complete system is assumed to have the form

    [ K   A^T ] [ q      ] = [ f ]
    [ A    0  ] [ lambda ]   [ b ]

as produced by ``LinearConstraintAugmenter``.

After the numerical solution has been obtained, the solver performs a purely
descriptive algebraic verification.  No residual tolerance is used as an
acceptance threshold and no PASS/FAIL status is assigned to a finite solution.

The verification reports three quantities for the complete augmented system:

1. the arithmetic mean of the equation residuals;
2. the population standard deviation of the equation residuals;
3. the population standard deviation of the individual active equation terms
   M_ij * x_j, used as the numerical scale of the terms forming the equations.

A calculation is stopped only when a usable numerical solution cannot be
obtained, for example because the system is rank deficient, dimensions are
invalid, or non-finite values are present.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import hashlib
import os
import warnings

import numpy as np
from scipy.linalg import LinAlgWarning
from scipy.sparse import diags, save_npz
from scipy.sparse.linalg import MatrixRankWarning, spsolve

from csf.cuf.solver.linear_constraint import (
    AugmentedLinearConstraintSystem,
)


@dataclass(frozen=True)
class AugmentedConstraintSolution:
    """Solution and descriptive verification of an augmented linear system."""

    primal: np.ndarray
    lagrange: np.ndarray
    augmented: np.ndarray

    # One residual for every equation of the complete augmented system.
    residuals: np.ndarray

    # Descriptive statistics of the residual vector.
    residual_mean: float
    residual_standard_deviation: float

    # Standard deviation of the individual active terms M_ij * x_j.
    equation_term_scale: float


class AugmentedSparseLinearSolver:
    """
    Direct sparse solution of a generic augmented constraint system.

    ``spsolve`` is the numerical solution path.  Once a finite solution exists,
    it is returned regardless of the magnitude of its residuals.  Residuals are
    measured and reported descriptively; they are not compared with acceptance
    tolerances.

    Diagnostic v3 writes the exact CSR matrix and RHS presented to ``spsolve``
    immediately before the solve.  The checkpoint does not modify either object.
    """

    def __init__(self, *, equilibration_iterations: int = 8):
        equilibration_iterations = int(equilibration_iterations)
        if equilibration_iterations < 0:
            raise ValueError("equilibration_iterations must be >= 0")
        self.equilibration_iterations = equilibration_iterations

    @staticmethod
    def _sha256_array(array) -> str:
        """Return SHA256 of the exact contiguous bytes of a NumPy array."""
        values = np.ascontiguousarray(array)
        return hashlib.sha256(values.view(np.uint8)).hexdigest()

    @staticmethod
    def _positive_min_max(values) -> tuple[float, float, int]:
        values = np.asarray(values, dtype=float).ravel()
        positive = values[values > 0.0]
        if positive.size == 0:
            return 0.0, 0.0, int(values.size)
        return (
            float(np.min(positive)),
            float(np.max(positive)),
            int(values.size - positive.size),
        )

    @staticmethod
    def _sparse_abs_min_max(matrix) -> tuple[float, float]:
        """Return nonzero absolute extrema without copying all matrix data."""
        data = np.asarray(matrix.data, dtype=float)
        if data.size == 0:
            return 0.0, 0.0

        minimum = np.inf
        maximum = 0.0
        chunk_size = 1_000_000
        for start in range(0, data.size, chunk_size):
            chunk = np.abs(data[start:start + chunk_size])
            active = chunk[chunk > 0.0]
            if active.size:
                minimum = min(minimum, float(np.min(active)))
                maximum = max(maximum, float(np.max(active)))

        if not np.isfinite(minimum):
            return 0.0, 0.0
        return float(minimum), float(maximum)

    @staticmethod
    def _sparse_axis_l2(matrix, *, axis: int) -> np.ndarray:
        matrix = matrix.tocsr()
        data = np.asarray(matrix.data, dtype=float)

        if axis == 1:
            result = np.zeros(matrix.shape[0], dtype=float)
            for row in range(matrix.shape[0]):
                start = int(matrix.indptr[row])
                stop = int(matrix.indptr[row + 1])
                result[row] = np.linalg.norm(data[start:stop])
            return result

        if axis == 0:
            squared_sums = np.zeros(matrix.shape[1], dtype=float)
            chunk_size = 1_000_000
            for start in range(0, data.size, chunk_size):
                stop = min(start + chunk_size, data.size)
                squared_sums += np.bincount(
                    matrix.indices[start:stop],
                    weights=data[start:stop] ** 2,
                    minlength=matrix.shape[1],
                )
            return np.sqrt(squared_sums)

        raise ValueError("axis must be 0 or 1")

    @staticmethod
    def _summary(values) -> tuple[float, float, float]:
        values = np.asarray(values, dtype=float).ravel()
        if values.size == 0:
            return 0.0, 0.0, 0.0
        return (
            float(np.min(values)),
            float(np.median(values)),
            float(np.max(values)),
        )

    @staticmethod
    def _matrix_value_profile(matrix) -> dict:
        """Return an algebra-agnostic profile of stored matrix magnitudes."""
        matrix = matrix.tocsr()
        data = np.asarray(matrix.data)
        decade_counts: dict[int, int] = {}
        exact_zero_count = 0
        nonfinite_count = 0
        nonzero_count = 0
        absolute_minimum = np.inf
        absolute_maximum = 0.0

        chunk_size = 1_000_000
        for start in range(0, data.size, chunk_size):
            values = np.asarray(data[start:start + chunk_size])
            finite = np.isfinite(values)
            nonfinite_count += int(values.size - np.count_nonzero(finite))
            finite_absolute = np.abs(values[finite])
            exact_zero_count += int(np.count_nonzero(finite_absolute == 0.0))
            active = finite_absolute[finite_absolute > 0.0]
            if active.size == 0:
                continue

            nonzero_count += int(active.size)
            absolute_minimum = min(absolute_minimum, float(np.min(active)))
            absolute_maximum = max(absolute_maximum, float(np.max(active)))
            decades = np.floor(np.log10(active)).astype(np.int64)
            unique, counts = np.unique(decades, return_counts=True)
            for decade, count in zip(unique, counts):
                key = int(decade)
                decade_counts[key] = decade_counts.get(key, 0) + int(count)

        if not np.isfinite(absolute_minimum):
            absolute_minimum = 0.0

        total_entries = int(matrix.shape[0]) * int(matrix.shape[1])
        return {
            "decade_counts": decade_counts,
            "stored_count": int(matrix.nnz),
            "nonzero_count": nonzero_count,
            "exact_zero_count": exact_zero_count,
            "implicit_zero_count": total_entries - int(matrix.nnz),
            "nonfinite_count": nonfinite_count,
            "absolute_minimum": absolute_minimum,
            "absolute_maximum": absolute_maximum,
        }

    @staticmethod
    def _print_matrix_value_distribution(
        matrix,
        *,
        label: str,
        profile: dict | None = None,
    ) -> None:
        """Describe stored values of one matrix without changing the matrix.

        The analysis is deliberately algebra-agnostic: it uses neither block
        boundaries nor physical meanings.  Absolute nonzero values are counted
        by decimal decade.  No threshold is selected and no entry is removed.
        """
        matrix = matrix.tocsr()
        if profile is None:
            profile = AugmentedSparseLinearSolver._matrix_value_profile(matrix)
        decade_counts = profile["decade_counts"]
        nonzero_count = int(profile["nonzero_count"])
        print(
            "[matrix-values] "
            f"label={label} shape={matrix.shape} "
            f"stored={profile['stored_count']} "
            f"nonzero={nonzero_count} "
            f"explicit_zeros={profile['exact_zero_count']} "
            f"implicit_zeros={profile['implicit_zero_count']} "
            f"nonfinite={profile['nonfinite_count']} "
            f"abs_nonzero_min={profile['absolute_minimum']:.12e} "
            f"abs_nonzero_max={profile['absolute_maximum']:.12e}",
            flush=True,
        )

        if not decade_counts:
            print(
                f"[matrix-values] label={label} decades=none",
                flush=True,
            )
            return

        minimum_decade = min(decade_counts)
        maximum_decade = max(decade_counts)
        for decade in range(minimum_decade, maximum_decade + 1):
            count = decade_counts.get(decade, 0)
            fraction = (
                float(count) / float(nonzero_count)
                if nonzero_count > 0
                else 0.0
            )
            print(
                "[matrix-values] "
                f"label={label} decade=1e{decade:+d} "
                f"count={count} fraction_nonzero={fraction:.12e}",
                flush=True,
            )

    @staticmethod
    def _print_structural_matrix_diagnostic(system) -> None:
        """Report scale and independence indicators for K, A, and KKT."""
        K = system.original_system.stiffness.tocsr()
        A = np.asarray(system.constraints.matrix, dtype=float)
        M = system.matrix.tocsr()

        k_abs_min, k_abs_max = AugmentedSparseLinearSolver._sparse_abs_min_max(K)
        k_row = AugmentedSparseLinearSolver._sparse_axis_l2(K, axis=1)
        k_col = AugmentedSparseLinearSolver._sparse_axis_l2(K, axis=0)
        k_diag = np.abs(np.asarray(K.diagonal(), dtype=float))
        k_diag_min, k_diag_max, k_diag_zeros = (
            AugmentedSparseLinearSolver._positive_min_max(k_diag)
        )
        k_fro = float(np.linalg.norm(np.asarray(K.data, dtype=float)))

        print(
            "[matrix-diagnostic] K "
            f"shape={K.shape} nnz={K.nnz} "
            f"abs_nonzero_min={k_abs_min:.12e} "
            f"abs_nonzero_max={k_abs_max:.12e} "
            f"frobenius={k_fro:.12e} "
            f"diag_abs_positive_min={k_diag_min:.12e} "
            f"diag_abs_max={k_diag_max:.12e} "
            f"diag_zeros={k_diag_zeros}",
            flush=True,
        )
        print(
            "[matrix-diagnostic] K norms "
            "row_l2_min_median_max="
            f"{AugmentedSparseLinearSolver._summary(k_row)} "
            "col_l2_min_median_max="
            f"{AugmentedSparseLinearSolver._summary(k_col)}",
            flush=True,
        )

        a_abs = np.abs(A)
        a_nonzero = a_abs[a_abs > 0.0]
        a_abs_min = float(np.min(a_nonzero)) if a_nonzero.size else 0.0
        a_abs_max = float(np.max(a_nonzero)) if a_nonzero.size else 0.0
        a_row = np.linalg.norm(A, axis=1)
        a_col = np.linalg.norm(A, axis=0)
        a_fro = float(np.linalg.norm(A))

        gram = np.asarray(A @ A.T, dtype=float)
        gram = 0.5 * (gram + gram.T)
        eigenvalues = np.linalg.eigvalsh(gram)
        eigenvalues[eigenvalues < 0.0] = 0.0
        singular_values = np.sqrt(eigenvalues)
        sigma_max = float(singular_values[-1]) if singular_values.size else 0.0
        rank_tolerance = (
            max(A.shape) * np.finfo(float).eps * sigma_max
        )
        numerical_rank = int(np.count_nonzero(singular_values > rank_tolerance))
        positive_sigma = singular_values[singular_values > rank_tolerance]
        sigma_min = float(positive_sigma[0]) if positive_sigma.size else 0.0
        condition = (
            float(sigma_max / sigma_min)
            if sigma_min > 0.0
            else float("inf")
        )

        print(
            "[matrix-diagnostic] A "
            f"shape={A.shape} nnz={int(np.count_nonzero(A))} "
            f"abs_nonzero_min={a_abs_min:.12e} "
            f"abs_nonzero_max={a_abs_max:.12e} "
            f"frobenius={a_fro:.12e} "
            f"row_l2_min_median_max={AugmentedSparseLinearSolver._summary(a_row)} "
            f"col_l2_min_median_max={AugmentedSparseLinearSolver._summary(a_col)}",
            flush=True,
        )
        print(
            "[matrix-diagnostic] A spectrum "
            f"numerical_rank={numerical_rank}/{A.shape[0]} "
            f"rank_tolerance={rank_tolerance:.12e} "
            f"sigma_min={sigma_min:.12e} "
            f"sigma_max={sigma_max:.12e} "
            f"condition={condition:.12e}",
            flush=True,
        )

        m_abs_min, m_abs_max = AugmentedSparseLinearSolver._sparse_abs_min_max(M)
        m_row = AugmentedSparseLinearSolver._sparse_axis_l2(M, axis=1)
        m_fro = float(np.linalg.norm(np.asarray(M.data, dtype=float)))
        block_ratio = float(k_fro / a_fro) if a_fro > 0.0 else float("inf")
        print(
            "[matrix-diagnostic] KKT "
            f"shape={M.shape} nnz={M.nnz} "
            f"abs_nonzero_min={m_abs_min:.12e} "
            f"abs_nonzero_max={m_abs_max:.12e} "
            f"frobenius={m_fro:.12e} "
            f"row_l2_min_median_max={AugmentedSparseLinearSolver._summary(m_row)} "
            f"K_to_A_frobenius_ratio={block_ratio:.12e}",
            flush=True,
        )

    @staticmethod
    def _write_pre_spsolve_checkpoint(matrix, rhs: np.ndarray) -> None:
        """Persist the exact matrix and RHS immediately before ``spsolve``."""
        root_text = os.environ.get("CSF_CUF_KKT_CHECKPOINT_DIR")
        root = (
            Path(root_text).expanduser()
            if root_text
            else Path.cwd() / "diagnostics" / "kkt_checkpoint"
        )
        root.mkdir(parents=True, exist_ok=True)

        matrix_path = root / "kkt_matrix.npz"
        rhs_path = root / "rhs.npy"

        save_npz(
            matrix_path,
            matrix,
            compressed=False,
        )
        np.save(
            rhs_path,
            rhs,
            allow_pickle=False,
        )

        print(
            "[diagnostic-v3] pre-spsolve checkpoint saved: "
            f"matrix={matrix_path} rhs={rhs_path} "
            f"shape={matrix.shape} nnz={matrix.nnz} "
            f"data_dtype={matrix.data.dtype} "
            f"indices_dtype={matrix.indices.dtype} "
            f"indptr_dtype={matrix.indptr.dtype} "
            f"rhs_dtype={rhs.dtype} "
            f"has_sorted_indices={matrix.has_sorted_indices} "
            f"has_canonical_format={matrix.has_canonical_format}"
        )

        print(
            "[diagnostic-v3] SHA256 "
            f"indptr={AugmentedSparseLinearSolver._sha256_array(matrix.indptr)} "
            f"indices={AugmentedSparseLinearSolver._sha256_array(matrix.indices)} "
            f"data={AugmentedSparseLinearSolver._sha256_array(matrix.data)} "
            f"rhs={AugmentedSparseLinearSolver._sha256_array(rhs)}"
        )

    @staticmethod
    def _direct_sparse_solve_many(
        matrix,
        rhs: np.ndarray,
        *,
        primal_size: int,
        equilibration_iterations: tuple[int, ...],
    ) -> Iterator[tuple[int, np.ndarray]]:
        """Yield solved vectors at requested progressive equilibration steps.

        The KKT matrix is prepared once. Iteration 0 denotes the original,
        unequilibrated KKT system. For positive values, equilibration advances
        monotonically up to the largest requested iteration count; at each
        requested checkpoint a separate solve is attempted. A numerical failure
        at one checkpoint is local to that checkpoint and does not prevent later,
        more strongly equilibrated checkpoints from being tried.
        """

        requested = tuple(sorted(set(int(v) for v in equilibration_iterations)))
        if not requested or requested[0] < 0:
            raise ValueError(
                "equilibration_iterations must contain values >= 0"
            )

        with warnings.catch_warnings():
            warnings.simplefilter(
                "error",
                MatrixRankWarning,
            )

            AugmentedSparseLinearSolver._write_pre_spsolve_checkpoint(
                matrix,
                rhs,
            )

            from scipy.linalg import norm
            from scipy.linalg.lapack import get_lapack_funcs

            # The original system diagnostic is common to every candidate.
            matrix_dense = np.asarray(matrix.toarray(), dtype=float)
            getrf, getrs, gecon = get_lapack_funcs(
                ("getrf", "getrs", "gecon"),
                (matrix_dense,),
            )

            original_norm = float(norm(matrix_dense, 1))
            original_lu, original_piv, original_info = getrf(
                matrix_dense.copy(),
                overwrite_a=True,
            )
            if original_info != 0:
                raise RuntimeError(
                    f"original KKT LU factorization failed with info={original_info}"
                )
            original_rcond, original_info = gecon(
                original_lu,
                original_norm,
                norm="1",
            )
            if original_info != 0:
                raise RuntimeError(
                    f"original KKT condition estimate failed with info={original_info}"
                )

            if float(original_rcond) < np.finfo(float).eps:
                warnings.warn(
                    "Original KKT matrix is ill-conditioned "
                    f"(rcond={float(original_rcond):.5e}).",
                    LinAlgWarning,
                    stacklevel=2,
                )

            # Iteration 0 is a valid checkpoint: solve the original KKT system
            # exactly as assembled, with no equilibration scaling applied.
            # Reuse the LU factorization already computed for the original
            # condition estimate so requesting eq0 adds no extra factorization.
            zero_candidate = None
            if 0 in requested:
                try:
                    zero_solution, zero_info = getrs(
                        original_lu,
                        original_piv,
                        rhs,
                        trans=0,
                        overwrite_b=False,
                    )
                    if zero_info != 0:
                        raise RuntimeError(
                            f"original KKT solve failed with info={zero_info}"
                        )

                    zero_candidate = np.asarray(zero_solution, dtype=float)
                    if zero_candidate.shape != rhs.shape:
                        raise RuntimeError(
                            "augmented solver returned an unexpected solution shape"
                        )
                    if not np.all(np.isfinite(zero_candidate)):
                        raise RuntimeError(
                            "augmented solver returned non-finite values"
                        )

                    print(
                        "[kkt-equilibration] "
                        "iterations=0 "
                        "iterations_requested=0 "
                        "iterations_performed=0 "
                        f"original_rcond={float(original_rcond):.12e} "
                        f"equilibrated_rcond={float(original_rcond):.12e} "
                        "scale_min=1.000000000000e+00 "
                        "scale_max=1.000000000000e+00",
                        flush=True,
                    )
                    unit_scale = np.ones(matrix.shape[0], dtype=float)
                    primal_scale = unit_scale[:primal_size]
                    multiplier_scale = unit_scale[primal_size:]
                    print(
                        "[matrix-diagnostic] equilibration-scales "
                        "primal_min_median_max="
                        f"{AugmentedSparseLinearSolver._summary(primal_scale)} "
                        "multiplier_min_median_max="
                        f"{AugmentedSparseLinearSolver._summary(multiplier_scale)}",
                        flush=True,
                    )
                except RuntimeError as exc:
                    print(
                        "[kkt-equilibration] "
                        f"iterations=0 failed: {exc}; "
                        "continuing with later requested iterations",
                        flush=True,
                    )
                    zero_candidate = None

            # Dense factors are not needed by the progressive equilibration
            # path and should not remain live while recovery/post uses eq0.
            del original_lu, original_piv, matrix_dense

            if zero_candidate is not None:
                yield 0, zero_candidate
                del zero_candidate

            equilibrated = matrix.copy().tocsr()
            equilibrated_rhs = np.asarray(rhs, dtype=float).copy()
            accumulated_scale = np.ones(matrix.shape[0], dtype=float)
            requested_set = set(requested)
            maximum_iterations = requested[-1]

            distribution_enabled = os.environ.get(
                "CSF_CUF_MATRIX_VALUE_DISTRIBUTION",
                "",
            ).strip().lower() in {"1", "true", "yes", "on"}

            for current_iteration in range(1, maximum_iterations + 1):
                row_max = np.asarray(
                    abs(equilibrated).max(axis=1).toarray(),
                    dtype=float,
                ).ravel()
                step = np.ones_like(row_max)
                active = row_max > 0.0
                step[active] = 1.0 / np.sqrt(row_max[active])
                D = diags(step, offsets=0, format="csr")
                equilibrated = (D @ equilibrated @ D).tocsr()
                equilibrated_rhs *= step
                accumulated_scale *= step

                if current_iteration not in requested_set:
                    continue

                equilibrated_dense = None
                equilibrated_lu = None
                equilibrated_piv = None
                scaled_solution = None
                candidate_solution = None

                try:
                    value_profile = None
                    if distribution_enabled:
                        value_profile = (
                            AugmentedSparseLinearSolver._matrix_value_profile(
                                equilibrated
                            )
                        )
                        AugmentedSparseLinearSolver._print_matrix_value_distribution(
                            equilibrated,
                            label=(
                                "final-equilibrated-matrix"
                                if len(requested) == 1
                                else f"equilibrated-matrix-eq{current_iteration}"
                            ),
                            profile=value_profile,
                        )

                    equilibrated_dense = np.asarray(
                        equilibrated.toarray(),
                        dtype=float,
                    )
                    equilibrated_norm = float(norm(equilibrated_dense, 1))
                    equilibrated_lu, equilibrated_piv, equilibrated_info = getrf(
                        equilibrated_dense,
                        overwrite_a=True,
                    )
                    if equilibrated_info != 0:
                        raise RuntimeError(
                            "equilibrated KKT LU factorization failed "
                            f"with info={equilibrated_info}"
                        )

                    equilibrated_rcond, equilibrated_info = gecon(
                        equilibrated_lu,
                        equilibrated_norm,
                        norm="1",
                    )
                    if equilibrated_info != 0:
                        raise RuntimeError(
                            "equilibrated KKT condition estimate failed "
                            f"with info={equilibrated_info}"
                        )

                    scaled_solution, solve_info = getrs(
                        equilibrated_lu,
                        equilibrated_piv,
                        equilibrated_rhs,
                        trans=0,
                        overwrite_b=False,
                    )
                    if solve_info != 0:
                        raise RuntimeError(
                            f"equilibrated KKT solve failed with info={solve_info}"
                        )

                    candidate_solution = np.asarray(
                        accumulated_scale * scaled_solution,
                        dtype=float,
                    )

                    if candidate_solution.shape != rhs.shape:
                        raise RuntimeError(
                            "augmented solver returned an unexpected solution shape"
                        )
                    if not np.all(np.isfinite(candidate_solution)):
                        raise RuntimeError(
                            "augmented solver returned non-finite values"
                        )

                    print(
                        "[kkt-equilibration] "
                        f"iterations={current_iteration} "
                        f"iterations_requested={current_iteration} "
                        f"iterations_performed={current_iteration} "
                        f"original_rcond={float(original_rcond):.12e} "
                        f"equilibrated_rcond={float(equilibrated_rcond):.12e} "
                        f"scale_min={float(np.min(accumulated_scale)):.12e} "
                        f"scale_max={float(np.max(accumulated_scale)):.12e}",
                        flush=True,
                    )
                    primal_scale = accumulated_scale[:primal_size]
                    multiplier_scale = accumulated_scale[primal_size:]
                    print(
                        "[matrix-diagnostic] equilibration-scales "
                        "primal_min_median_max="
                        f"{AugmentedSparseLinearSolver._summary(primal_scale)} "
                        "multiplier_min_median_max="
                        f"{AugmentedSparseLinearSolver._summary(multiplier_scale)}",
                        flush=True,
                    )

                except (RuntimeError, MatrixRankWarning) as exc:
                    print(
                        "[kkt-equilibration] "
                        f"iterations={current_iteration} failed: {exc}; "
                        "continuing with later requested iterations",
                        flush=True,
                    )
                    candidate_solution = None
                finally:
                    # Dense factors are candidate-local and can be large. They
                    # must be released before control is yielded to recovery/post.
                    del (
                        equilibrated_dense,
                        equilibrated_lu,
                        equilibrated_piv,
                        scaled_solution,
                    )

                if candidate_solution is not None:
                    yield current_iteration, candidate_solution
                    del candidate_solution

    @staticmethod
    def _direct_sparse_solve(
        matrix,
        rhs: np.ndarray,
        *,
        primal_size: int,
        equilibration_iterations: int,
    ) -> np.ndarray:
        """Solve one sparse system using the historical scalar interface."""

        results = AugmentedSparseLinearSolver._direct_sparse_solve_many(
            matrix,
            rhs,
            primal_size=primal_size,
            equilibration_iterations=(int(equilibration_iterations),),
        )
        try:
            try:
                _iterations, solution = next(results)
            except StopIteration as exc:
                raise RuntimeError(
                    "augmented linear solve failed at the requested "
                    "equilibration iteration"
                ) from exc
            return solution
        finally:
            results.close()

    @staticmethod
    def _verification(
        matrix,
        solution: np.ndarray,
        rhs: np.ndarray,
    ) -> tuple[np.ndarray, float, float, float]:
        """
        Verify the solved complete linear system without acceptance thresholds.

        For the complete system M x = d, one residual is retained for every
        equation:

            r = M x - d

        The residual population is summarized by its arithmetic mean and its
        population standard deviation.

        For each active sparse coefficient M_ij, the corresponding equation
        term is

            t_ij = M_ij * x_j

        The population standard deviation of all active t_ij values is reported
        as the equation-term scale.  Implicit zero coefficients are not counted:
        they are not terms participating in the assembled sparse equations.
        """
        residuals = np.asarray(
            matrix @ solution - rhs,
            dtype=float,
        )

        if residuals.shape != rhs.shape:
            raise RuntimeError(
                "algebraic verification returned an unexpected residual shape"
            )

        if not np.all(np.isfinite(residuals)):
            raise RuntimeError(
                "algebraic verification produced non-finite residuals"
            )

        residual_mean = (
            float(np.mean(residuals))
            if residuals.size
            else 0.0
        )
        residual_standard_deviation = (
            float(np.std(residuals, ddof=0))
            if residuals.size
            else 0.0
        )

        # In CSR format, matrix.data[k] belongs to column matrix.indices[k].
        # Therefore every stored coefficient contributes exactly one active
        # equation term M_ij * x_j.
        if matrix.nnz:
            equation_terms = (
                np.asarray(matrix.data, dtype=float)
                * solution[np.asarray(matrix.indices, dtype=int)]
            )
            equation_term_scale = float(
                np.std(equation_terms, ddof=0)
            )
        else:
            equation_term_scale = 0.0

        if not np.isfinite(residual_mean):
            raise RuntimeError(
                "algebraic verification produced a non-finite residual mean"
            )
        if not np.isfinite(residual_standard_deviation):
            raise RuntimeError(
                "algebraic verification produced a non-finite residual standard deviation"
            )
        if not np.isfinite(equation_term_scale):
            raise RuntimeError(
                "algebraic verification produced a non-finite equation-term scale"
            )

        residuals.setflags(write=False)

        return (
            residuals,
            residual_mean,
            residual_standard_deviation,
            equation_term_scale,
        )

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

        self._print_structural_matrix_diagnostic(system)

        solution = self._direct_sparse_solve(
            matrix,
            rhs,
            primal_size=system.primal_size,
            equilibration_iterations=self.equilibration_iterations,
        )

        q, lagrange = system.split_solution(
            solution
        )

        (
            residuals,
            residual_mean,
            residual_standard_deviation,
            equation_term_scale,
        ) = self._verification(
            matrix,
            solution,
            rhs,
        )

        return AugmentedConstraintSolution(
            primal=q,
            lagrange=lagrange,
            augmented=solution,
            residuals=residuals,
            residual_mean=residual_mean,
            residual_standard_deviation=residual_standard_deviation,
            equation_term_scale=equation_term_scale,
        )

    def solve_many(
        self,
        system: AugmentedLinearConstraintSystem,
        *,
        equilibration_iterations,
    ) -> Iterator[tuple[int, AugmentedConstraintSolution]]:
        """Yield ``(iterations, solution)`` for successful sweep checkpoints.

        Structural validation and diagnostics are performed once. A failed
        candidate produces no yielded solution; later requested iteration
        counts are still attempted. If no requested candidate succeeds, the
        method raises ``RuntimeError`` after all candidates have been tried.
        """

        requested = tuple(
            sorted(set(int(value) for value in equilibration_iterations))
        )
        if not requested or requested[0] < 0:
            raise ValueError(
                "equilibration_iterations must contain values >= 0"
            )

        matrix = system.matrix.tocsr()
        rhs = np.asarray(system.rhs, dtype=float)

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

        self._print_structural_matrix_diagnostic(system)

        successful = 0
        for iterations, solution in self._direct_sparse_solve_many(
            matrix,
            rhs,
            primal_size=system.primal_size,
            equilibration_iterations=requested,
        ):
            try:
                q, lagrange = system.split_solution(solution)
                (
                    residuals,
                    residual_mean,
                    residual_standard_deviation,
                    equation_term_scale,
                ) = self._verification(
                    matrix,
                    solution,
                    rhs,
                )
            except RuntimeError as exc:
                print(
                    "[kkt-equilibration] "
                    f"iterations={iterations} verification failed: {exc}; "
                    "continuing with later requested iterations",
                    flush=True,
                )
                continue

            successful += 1
            yield iterations, AugmentedConstraintSolution(
                primal=q,
                lagrange=lagrange,
                augmented=solution,
                residuals=residuals,
                residual_mean=residual_mean,
                residual_standard_deviation=residual_standard_deviation,
                equation_term_scale=equation_term_scale,
            )

        if successful == 0:
            raise RuntimeError(
                "all requested equilibration solves failed"
            )

