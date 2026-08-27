# SOURCE VERSION: CSF-CUF-MACLAURIN-TENSOR-v1.0.0
"""Tensor-product scaled Maclaurin transverse basis for CSF-CUF.

This module adds a richer Maclaurin expansion without modifying the validated
``ScaledMaclaurinBasis`` implementation.

For CUF order N, the basis contains every monomial

    Y**p_y * Z**p_z

with

    0 <= p_y <= N
    0 <= p_z <= N

for a total of (N + 1)**2 transverse terms.
"""
from __future__ import annotations

import numpy as np

from csf.cuf.numerics import ScaledMaclaurinBasis


class ScaledMaclaurinTensorBasis(ScaledMaclaurinBasis):
    """Tensor-product extension of the validated scaled Maclaurin basis.

    The complete-total-degree terms already present in
    ``ScaledMaclaurinBasis`` are kept first and in exactly the same order.
    Additional tensor-product terms are appended by increasing total degree.

    This preserves the indices of the validated basis functions at a fixed N
    and makes complete-vs-tensor comparisons controlled.
    """

    def __init__(self, order: int, *, y_scale: float, z_scale: float):
        super().__init__(order, y_scale=y_scale, z_scale=z_scale)

        complete_exponents = self._exponents
        complete_set = set(complete_exponents)

        additional_exponents = tuple(
            (p_y, degree - p_y)
            for degree in range(order + 1, 2 * order + 1)
            for p_y in range(
                min(order, degree),
                max(-1, degree - order - 1),
                -1,
            )
            if (p_y, degree - p_y) not in complete_set
        )

        self._exponents = complete_exponents + additional_exponents
        self._size = len(self._exponents)

        expected_size = (order + 1) ** 2
        if self._size != expected_size:
            raise RuntimeError(
                "tensor Maclaurin exponent construction produced "
                f"{self._size} terms; expected {expected_size}"
            )

        self._p_y = np.fromiter(
            (item[0] for item in self._exponents),
            dtype=np.intp,
            count=self._size,
        )
        self._p_z = np.fromiter(
            (item[1] for item in self._exponents),
            dtype=np.intp,
            count=self._size,
        )
        self._p_y.setflags(write=False)
        self._p_z.setflags(write=False)
