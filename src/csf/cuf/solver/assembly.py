# Version: CSF-CUF RAM-optimized numerically pure assembly - no magnitude cleanup - 2026-08-23
"""
Generic global assembly for the longitudinal CSF-CUF finite-element solver.

This module assembles:

    {K_e^(tau,s)} -> K_global

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
from typing import Tuple

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from csf.cuf.solver.longitudinal import LongitudinalMesh1D


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
    node_basis_sizes: Tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.number_of_nodes, int):
            raise TypeError("number_of_nodes must be an integer")

        if self.number_of_nodes < 1:
            raise ValueError("number_of_nodes must be >= 1")

        if not isinstance(self.basis_size, int):
            raise TypeError("basis_size must be an integer")

        if self.basis_size < 1:
            raise ValueError("basis_size must be >= 1")

        sizes = self.node_basis_sizes
        if sizes is None:
            sizes = tuple(self.basis_size for _ in range(self.number_of_nodes))
        else:
            sizes = tuple(int(value) for value in sizes)
            if len(sizes) != self.number_of_nodes:
                raise ValueError("node_basis_sizes must have one entry per node")
            if any(value < 1 for value in sizes):
                raise ValueError("every node basis size must be >= 1")
            if max(sizes) > self.basis_size:
                raise ValueError("node basis size cannot exceed basis_size")
        object.__setattr__(self, "node_basis_sizes", sizes)

        offsets = [0]
        for value in sizes:
            offsets.append(offsets[-1] + value * self.components)
        object.__setattr__(self, "_node_offsets", tuple(offsets))

    @property
    def components(self) -> int:
        return 3

    @property
    def dofs_per_node(self) -> int:
        return self.basis_size * self.components

    @property
    def total_dofs(self) -> int:
        return self._node_offsets[-1]

    @property
    def is_uniform(self) -> bool:
        return all(value == self.basis_size for value in self.node_basis_sizes)

    def basis_size_at_node(self, node: int) -> int:
        if not 0 <= node < self.number_of_nodes:
            raise IndexError(f"node must be in 0..{self.number_of_nodes - 1}")
        return self.node_basis_sizes[node]

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

        node_basis_size = self.basis_size_at_node(node)
        if not 1 <= tau <= node_basis_size:
            raise IndexError(
                f"tau must be in 1..{node_basis_size} at node {node}"
            )

        if component not in (0, 1, 2):
            raise IndexError("component must be 0, 1, or 2")

        return (
            self._node_offsets[node]
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

        node = int(np.searchsorted(self._node_offsets, dof, side="right") - 1)
        remainder = dof - self._node_offsets[node]
        tau_zero_based, component = divmod(remainder, self.components)
        return node, tau_zero_based + 1, component




def build_global_dof_layout(
    *,
    mesh: LongitudinalMesh1D,
    basis_size: int,
    element_basis_sizes: Tuple[int, ...] | None = None,
) -> GlobalDOFLayout:
    """Build the global DOF numbering from the resolved discretization."""

    if element_basis_sizes is None:
        element_basis_sizes = tuple(int(basis_size) for _ in mesh.elements)
    else:
        element_basis_sizes = tuple(int(value) for value in element_basis_sizes)
        if len(element_basis_sizes) != len(mesh.elements):
            raise ValueError("element_basis_sizes must have one entry per element")
        if any(value < 1 or value > basis_size for value in element_basis_sizes):
            raise ValueError("invalid element basis size")

    node_sizes = [None] * mesh.number_of_nodes
    for element, element_basis_size in zip(mesh.elements, element_basis_sizes):
        for node in element.node_ids:
            current = node_sizes[node]
            if current is None:
                node_sizes[node] = element_basis_size
            elif current != element_basis_size:
                raise ValueError(
                    "a shared longitudinal node belongs to elements with different "
                    "basis sizes; expansion interfaces must use independent traces"
                )

    return GlobalDOFLayout(
        number_of_nodes=mesh.number_of_nodes,
        basis_size=basis_size,
        node_basis_sizes=tuple(int(value) for value in node_sizes),
    )


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
    """Assemble the unconstrained global longitudinal CSF-CUF stiffness matrix."""

    def __init__(
        self,
        *,
        element_matrix_builder,
    ) -> None:
        if not hasattr(element_matrix_builder, "build_pair"):
            raise TypeError(
                "element_matrix_builder must expose build_pair(...)"
            )

        self.element_matrix_builder = element_matrix_builder

    def assemble(
        self,
        *,
        mesh: LongitudinalMesh1D,
        dof_layout: GlobalDOFLayout,
    ) -> csr_matrix:
        """Assemble the unconstrained global stiffness matrix."""

        layout = dof_layout
        element_basis_sizes = tuple(
            layout.basis_size_at_node(element.node_ids[0])
            for element in mesh.elements
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
        for element_index, (element, element_basis_size) in enumerate(
            zip(mesh.elements, element_basis_sizes),
            start=1,
        ):
            pairs_per_element = element_basis_size * element_basis_size
            element_started = time.perf_counter()
            build_pair_time = 0.0
            scatter_time = 0.0
            local_size = len(element.node_ids)

            print(
                f"[assembly] element {element_index}/{number_of_elements} "
                f"started: {pairs_per_element} CUF pairs",
                flush=True,
            )

            for tau in range(1, element_basis_size + 1):
                for s in range(1, element_basis_size + 1):

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
                    or tau == element_basis_size
                ):
                    element_elapsed = (
                        time.perf_counter() - element_started
                    )
                    completed_pairs = tau * element_basis_size

                    print(
                        f"[assembly] element "
                        f"{element_index}/{number_of_elements} "
                        f"tau={tau}/{element_basis_size} "
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

        return stiffness
