"""Load-side compatibility view of csf.cuf.adapters.problem.bending_torsion_halfwave.

The historical adapter remains available unchanged.  In split-adapter cases
this module is intended for problem.load_adapter; the composed problem uses
only build_load_vector() and tracked_points() from the object returned
by build_problem().
"""

from csf.cuf.adapters.problem.bending_torsion_halfwave import build_problem

__all__ = ("build_problem",)
