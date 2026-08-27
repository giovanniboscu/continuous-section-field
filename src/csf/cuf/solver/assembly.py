# Version: CSF-CUF RAM-optimized numerically pure assembly - no magnitude cleanup - 2026-08-23
"""
Generic global assembly for the longitudinal CSF-CUF finite-element solver.

This module assembles:

    {K_e^(tau,s)} -> K_global

and

    {f_e^tau} -> f_global

without applying boundary conditions and without solving the system.

No assumption is made about:
- section shape;
- section constancy;
- material homogeneity or isotropy;
- benchmark data;
- Navier specialization;
- CUF approximation family;
- longitudinal element order;
- number of longitudinal elements.

The only fixed mechanical structure retained from the CUF displacement field is
the three displacement components (x, y, z).
"""

from __future__ import annotations
from array import array
import time
from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from csf.cuf.solver.longitudinal import (
    LongitudinalIntegrator,
    LongitudinalMesh1D,
)
from csf.cuf.problem.problem import GeneralizedLongitudinalLoad


# =============================================================================
# Global degree-of-freedom layout
# =============================================================================

@dataclass(frozen=True)
class GlobalDOFLayout:
    """
    Generic global numbering for longitudinal CSF-CUF unknowns.

    A degree of freedom is identified uniquely by

        (longitudinal_node, tau, displacement_component)

    with:
        longitudinal_node = 0 .. number_of_nodes-1
        tau                = 1 .. basis_size
        component          = 0,1,2  <-> x,y,z

    The internal numbering is node-major, then CUF-index-major, then component.
    No physics depends on this ordering.
    """

    number_of_nodes: int
    basis_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.number_of_nodes, int):
            raise TypeError("number_of_nodes must be an integer")

        if self.number_of_nodes < 1:
            raise ValueError("number_of_nodes must be >= 1")

        if not isinstance(self.basis_size, int):
            raise TypeError("basis_size must be an integer")

        if self.basis_size < 1:
            raise ValueError("basis_size must be >= 1")

    @property
    def components(self) -> int:
        return 3

    @property
    def dofs_per_node(self) -> int:
        return self.basis_size * self.components

    @property
    def total_dofs(self) -> int:
        return self.number_of_nodes * self.dofs_per_node

    def index(
        self,
        *,
        node: int,
        tau: int,
        component: int,
    ) -> int:
        if not 0 <= node < self.number_of_nodes:
            raise IndexError(
                f"node must be in 0..{self.number_of_nodes - 1}"
            )

        if not 1 <= tau <= self.basis_size:
            raise IndexError(
                f"tau must be in 1..{self.basis_size}"
            )

        if component not in (0, 1, 2):
            raise IndexError("component must be 0, 1, or 2")

        return (
            node * self.dofs_per_node
            + (tau - 1) * self.components
            + component
        )

    def decode(
        self,
        dof: int,
    ) -> Tuple[int, int, int]:
        if not 0 <= dof < self.total_dofs:
            raise IndexError(
                f"dof must be in 0..{self.total_dofs - 1}"
            )

        node, remainder = divmod(
            dof,
            self.dofs_per_node,
        )

        tau_zero_based, component = divmod(
            remainder,
            self.components,
        )

        return node, tau_zero_based + 1, component


# =============================================================================
# Assembled system container
# =============================================================================

@dataclass(frozen=True)
class AssembledCSFCUFSystem:
    """
    Global unconstrained CSF-CUF system.

    Boundary conditions are intentionally not applied at this stage.
    """

    stiffness: csr_matrix
    load: np.ndarray
    dof_layout: GlobalDOFLayout

    def __post_init__(self) -> None:
        expected = self.dof_layout.total_dofs

        if self.stiffness.shape != (expected, expected):
            raise ValueError(
                "global stiffness shape is inconsistent with DOF layout"
            )

        if self.load.shape != (expected,):
            raise ValueError(
                "global load-vector shape is inconsistent with DOF layout"
            )


# =============================================================================
# Generic assembler
# =============================================================================

class CSFCUFGlobalAssembler:
    """
    Assemble the unconstrained global longitudinal CSF-CUF system.

    Parameters
    ----------
    element_matrix_builder:
        Any object exposing

            build_pair(element=..., tau=..., s=...)

        and returning an object exposing

            block(test_component, trial_component)

        where every block is the local longitudinal matrix associated with one
        ordered CUF pair and one displacement-component pair.

        CUFElementMatrixBuilder is the normal production implementation.

    longitudinal_integrator:
        Generic longitudinal integration backend used for generalized loads.
    """

    def __init__(
        self,
        *,
        element_matrix_builder,
        longitudinal_integrator: LongitudinalIntegrator,
    ) -> None:
        if not hasattr(element_matrix_builder, "build_pair"):
            raise TypeError(
                "element_matrix_builder must expose build_pair(...)"
            )

        if not isinstance(
            longitudinal_integrator,
            LongitudinalIntegrator,
        ):
            raise TypeError(
                "longitudinal_integrator must implement "
                "LongitudinalIntegrator"
            )

        self.element_matrix_builder = element_matrix_builder
        self.longitudinal_integrator = longitudinal_integrator

    def assemble(
        self,
        *,
        mesh: LongitudinalMesh1D,
        basis_size: int,
        loads: Iterable[GeneralizedLongitudinalLoad] = (),
    ) -> AssembledCSFCUFSystem:
        """
        Assemble global stiffness and generalized load vector.

        The result is unconstrained. Essential boundary conditions are handled
        by the next solver layer.
        """

        layout = GlobalDOFLayout(
            number_of_nodes=mesh.number_of_nodes,
            basis_size=basis_size,
        )

        # MEM-01: keep assembly triplets in compact typed buffers instead of
        # Python lists.  The append order and every numerical value are
        # unchanged, but each entry now occupies its native scalar width rather
        # than a Python object plus a list pointer.
        #
        # Use 32-bit indices whenever the global numbering permits it, matching
        # the compact index representation normally selected by SciPy for
        # matrices of this size.  Fall back to 64-bit indices generically.
        if layout.total_dofs <= np.iinfo(np.int32).max:
            index_typecode = "i"
            index_dtype = np.int32
        else:
            index_typecode = "q"
            index_dtype = np.int64

        rows = array(index_typecode)
        cols = array(index_typecode)
        values = array("d")

        # ---------------------------------------------------------------------
        # Minimal assembly instrumentation.
        # No mechanics, quadrature, matrix values, or assembly ordering changes.
        # ---------------------------------------------------------------------
        assembly_started = time.perf_counter()
        number_of_elements = len(mesh.elements)
        pairs_per_element = basis_size * basis_size

        for element_index, element in enumerate(
            mesh.elements,
            start=1,
        ):
            element_started = time.perf_counter()
            build_pair_time = 0.0
            scatter_time = 0.0
            local_size = len(element.node_ids)

            print(
                f"[assembly] element {element_index}/{number_of_elements} "
                f"started: {pairs_per_element} CUF pairs",
                flush=True,
            )

            for tau in range(1, basis_size + 1):
                for s in range(1, basis_size + 1):

                    pair_started = time.perf_counter()
                    local_pair = (
                        self.element_matrix_builder.build_pair(
                            element=element,
                            tau=tau,
                            s=s,
                        )
                    )
                    build_pair_time += (
                        time.perf_counter() - pair_started
                    )

                    scatter_started = time.perf_counter()

                    for test_component in range(3):
                        for trial_component in range(3):

                            local_block = np.asarray(
                                local_pair.block(
                                    test_component,
                                    trial_component,
                                ),
                                dtype=float,
                            )

                            expected_shape = (
                                local_size,
                                local_size,
                            )

                            if local_block.shape != expected_shape:
                                raise ValueError(
                                    "local CUF block has shape "
                                    f"{local_block.shape}, expected "
                                    f"{expected_shape}"
                                )

                            if not np.all(
                                np.isfinite(local_block)
                            ):
                                raise ValueError(
                                    "local CUF block contains "
                                    "non-finite values"
                                )

                            for a, global_node_a in enumerate(
                                element.node_ids
                            ):
                                global_row = layout.index(
                                    node=global_node_a,
                                    tau=tau,
                                    component=test_component,
                                )

                                for b, global_node_b in enumerate(
                                    element.node_ids
                                ):
                                    value = float(
                                        local_block[a, b]
                                    )

                                    if value == 0.0:
                                        continue

                                    global_col = layout.index(
                                        node=global_node_b,
                                        tau=s,
                                        component=trial_component,
                                    )

                                    rows.append(global_row)
                                    cols.append(global_col)
                                    values.append(value)

                    scatter_time += (
                        time.perf_counter() - scatter_started
                    )

                # One line every 10 tau values, plus first and last.
                if (
                    tau == 1
                    or tau % 10 == 0
                    or tau == basis_size
                ):
                    element_elapsed = (
                        time.perf_counter() - element_started
                    )
                    completed_pairs = tau * basis_size

                    print(
                        f"[assembly] element "
                        f"{element_index}/{number_of_elements} "
                        f"tau={tau}/{basis_size} "
                        f"pairs={completed_pairs}/{pairs_per_element} "
                        f"entries={len(values)} "
                        f"elapsed={element_elapsed:.1f}s "
                        f"build_pair={build_pair_time:.1f}s "
                        f"scatter={scatter_time:.1f}s",
                        flush=True,
                    )

            element_elapsed = (
                time.perf_counter() - element_started
            )

            print(
                f"[assembly] element "
                f"{element_index}/{number_of_elements} complete "
                f"elapsed={element_elapsed:.1f}s "
                f"build_pair={build_pair_time:.1f}s "
                f"scatter={scatter_time:.1f}s "
                f"entries={len(values)}",
                flush=True,
            )

        triplet_elapsed = (
            time.perf_counter() - assembly_started
        )

        print(
            f"[assembly] triplets complete "
            f"elapsed={triplet_elapsed:.1f}s "
            f"entries={len(values)}",
            flush=True,
        )

        sparse_started = time.perf_counter()

        # Zero-copy NumPy views over the compact triplet buffers.  COO -> CSR
        # receives entries in exactly the same sequence as before.
        row_data = np.frombuffer(rows, dtype=index_dtype)
        col_data = np.frombuffer(cols, dtype=index_dtype)
        value_data = np.frombuffer(values, dtype=np.float64)

        stiffness = coo_matrix(
            (
                value_data,
                (
                    row_data,
                    col_data,
                ),
            ),
            shape=(
                layout.total_dofs,
                layout.total_dofs,
            ),
        ).tocsr()

        # The CSR matrix owns the assembled sparse data.  Release the much
        # larger triplet representation immediately instead of retaining it
        # until assemble() returns.
        del row_data, col_data, value_data
        del rows, cols, values

        # Duplicate COO entries are summed during conversion to CSR.
        # No magnitude-based filtering, thresholding, regularization, or
        # coefficient modification is applied after assembly.
        stiffness.sum_duplicates()

        print(
            f"[assembly] COO->CSR complete "
            f"elapsed={time.perf_counter() - sparse_started:.1f}s "
            f"nnz={stiffness.nnz}",
            flush=True,
        )

        loads_started = time.perf_counter()

        load_vector = self._assemble_loads(
            mesh=mesh,
            layout=layout,
            loads=tuple(loads),
        )

        print(
            f"[assembly] loads complete "
            f"elapsed={time.perf_counter() - loads_started:.1f}s "
            f"total={time.perf_counter() - assembly_started:.1f}s",
            flush=True,
        )

        return AssembledCSFCUFSystem(
            stiffness=stiffness,
            load=load_vector,
            dof_layout=layout,
        )

    def _assemble_loads(
        self,
        *,
        mesh: LongitudinalMesh1D,
        layout: GlobalDOFLayout,
        loads: Tuple[GeneralizedLongitudinalLoad, ...],
    ) -> np.ndarray:
        vector = np.zeros(
            layout.total_dofs,
            dtype=float,
        )

        component_index = {
            "x": 0,
            "y": 1,
            "z": 2,
        }

        for generalized_load in loads:
            if not 1 <= generalized_load.tau <= layout.basis_size:
                raise ValueError(
                    f"load tau={generalized_load.tau} exceeds "
                    f"basis size {layout.basis_size}"
                )

            component = component_index[
                generalized_load.component
            ]

            for element in mesh.elements:
                local_vector = (
                    self.longitudinal_integrator.integrate_linear(
                        element=element,
                        load=generalized_load.value,
                    )
                )

                expected_size = len(element.node_ids)

                if local_vector.shape != (expected_size,):
                    raise ValueError(
                        "local load vector has inconsistent size"
                    )

                for a, global_node in enumerate(
                    element.node_ids
                ):
                    global_dof = layout.index(
                        node=global_node,
                        tau=generalized_load.tau,
                        component=component,
                    )

                    vector[global_dof] += float(
                        local_vector[a]
                    )

        return vector
