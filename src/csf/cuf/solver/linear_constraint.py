"""
Generic enforcement of linear constraints on a CSF-CUF global system by
Lagrange multipliers.

Given

    K q = f

and linear constraints

    A q = b,

the augmented system is

    [ K   A^T ] [ q      ] = [ f ]
    [ A    0  ] [ lambda ]   [ b ]

This layer introduces no penalty parameter and does not assume that constraints
are single-DOF prescriptions.

No geometry, material, load case, CUF basis family, benchmark, or solver
discretization is hard-coded.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import bmat, csr_matrix, issparse

from csf.cuf.solver.assembly import AssembledCSFCUFSystem
from csf.cuf.problem.point_bc import LinearConstraintSystem


@dataclass(frozen=True)
class AugmentedLinearConstraintSystem:
    """
    Augmented algebraic system with Lagrange multipliers.
    """

    matrix: csr_matrix
    rhs: np.ndarray
    primal_size: int
    constraint_count: int
    original_system: AssembledCSFCUFSystem
    constraints: LinearConstraintSystem

    def __post_init__(self) -> None:
        total = self.primal_size + self.constraint_count

        if self.matrix.shape != (total, total):
            raise ValueError(
                "augmented matrix shape is inconsistent"
            )

        if self.rhs.shape != (total,):
            raise ValueError(
                "augmented rhs shape is inconsistent"
            )

    def split_solution(
        self,
        solution: np.ndarray,
    ):
        solution = np.asarray(
            solution,
            dtype=float,
        )

        expected = (
            self.primal_size
            + self.constraint_count
        )

        if solution.shape != (expected,):
            raise ValueError(
                "augmented solution has inconsistent size"
            )

        q = solution[:self.primal_size]
        lagrange = solution[self.primal_size:]

        return q, lagrange


class LinearConstraintAugmenter:
    """
    Build an exact Lagrange-multiplier augmentation for A q = b.
    """

    def apply(
        self,
        *,
        system: AssembledCSFCUFSystem,
        constraints: LinearConstraintSystem,
    ) -> AugmentedLinearConstraintSystem:
        K = system.stiffness

        if not issparse(K):
            raise TypeError(
                "global stiffness must be sparse"
            )

        K = K.tocsr()

        A = np.asarray(
            constraints.matrix,
            dtype=float,
        )

        b = np.asarray(
            constraints.rhs,
            dtype=float,
        )

        n = system.dof_layout.total_dofs
        m = A.shape[0]

        if A.shape[1] != n:
            raise ValueError(
                "constraint matrix width must equal total DOFs"
            )

        if b.shape != (m,):
            raise ValueError(
                "constraint rhs size mismatch"
            )

        if not np.all(np.isfinite(A)):
            raise ValueError(
                "constraint matrix contains non-finite values"
            )

        if not np.all(np.isfinite(b)):
            raise ValueError(
                "constraint rhs contains non-finite values"
            )

        A_sparse = csr_matrix(A)
        zero = csr_matrix((m, m), dtype=float)

        augmented = bmat(
            [
                [K, A_sparse.T],
                [A_sparse, zero],
            ],
            format="csr",
        )

        rhs = np.concatenate(
            (
                np.asarray(system.load, dtype=float),
                b,
            )
        )

        return AugmentedLinearConstraintSystem(
            matrix=augmented,
            rhs=rhs,
            primal_size=n,
            constraint_count=m,
            original_system=system,
            constraints=constraints,
        )
