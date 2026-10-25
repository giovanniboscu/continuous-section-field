#!/usr/bin/env python3
"""Add a configurable global stiffness symmetry check to CSF-CUF engine.py.

Run from the continuous-section-field repository root:
    python3 apply_engine_symmetry_check.py

Only src/csf/cuf/solver/engine.py is changed. No line numbers are assumed.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import textwrap

TARGET = Path("src/csf/cuf/solver/engine.py")
MARKER = "CSF_CUF_SYMMETRY_RTOL"

CHECK = '''\
# Check the original assembled stiffness matrix, before constraints or solving.
# No symmetrization is performed.
from os import getenv
symmetry_rtol = float(getenv("CSF_CUF_SYMMETRY_RTOL", "1e-10"))
if not np.isfinite(symmetry_rtol) or symmetry_rtol < 0.0:
    raise ValueError("CSF_CUF_SYMMETRY_RTOL must be finite and non-negative")
asymmetry = stiffness - stiffness.T
asymmetry.eliminate_zeros()
stiffness_norm = float(np.linalg.norm(stiffness.data))
asymmetry_norm = float(np.linalg.norm(asymmetry.data))
maximum_asymmetry = (
    float(np.max(np.abs(asymmetry.data))) if asymmetry.nnz else 0.0
)
relative_asymmetry = (
    asymmetry_norm / stiffness_norm
    if stiffness_norm > 0.0
    else (0.0 if asymmetry_norm == 0.0 else float("inf"))
)
del asymmetry
print(
    "[verification] global stiffness symmetry: "
    f"relative={relative_asymmetry:.6e} "
    f"maximum_abs={maximum_asymmetry:.6e} "
    f"rtol={symmetry_rtol:.1e}",
    flush=True,
)
if (
    not np.isfinite(stiffness_norm)
    or not np.isfinite(asymmetry_norm)
    or relative_asymmetry > symmetry_rtol
):
    raise RuntimeError(
        "CSF-CUF assembled stiffness is not symmetric: "
        f"relative={relative_asymmetry:.6e}, rtol={symmetry_rtol:.1e}; "
        "no symmetrization has been applied"
    )
'''


def modify(source: str) -> str:
    if MARKER in source:
        raise ValueError("The symmetry check already appears to be installed; no changes made.")

    # Use the load-assembly marker, not a source line number. Verify that the
    # immediately preceding part is precisely the global stiffness assembly.
    matches = list(re.finditer(
        r"(?m)^(?P<indent>[ \t]*)loads_started[ \t]*=[ \t]*time\.perf_counter\(\)[ \t]*$",
        source,
    ))
    candidates = []
    for match in matches:
        preceding = source[max(0, match.start() - 900):match.start()]
        if (
            re.search(r"\bstiffness\s*=\s*CSFCUFGlobalAssembler\s*\(", preceding)
            and re.search(r"\)\.assemble\s*\(", preceding)
            and re.search(r"\bdof_layout\s*=\s*dof_layout\b", preceding)
        ):
            candidates.append(match)

    if len(candidates) != 1:
        raise ValueError(
            "Could not uniquely identify stiffness assembly followed by "
            "loads_started in engine.py; no changes made. "
            "Please share the corresponding section of your local file."
        )

    match = candidates[0]
    prefix = match.group("indent")
    insert = textwrap.indent(CHECK, prefix) + "\n"
    updated = source[:match.start()] + insert + source[match.start():]
    compile(updated, str(TARGET), "exec")  # Verify syntax before touching the file.
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without modifying engine.py")
    args = parser.parse_args()

    if not TARGET.is_file():
        print(f"ERROR: {TARGET} not found. Run from repository root.", file=sys.stderr)
        return 1
    original = TARGET.read_bytes()
    if b"\r\n" in original:
        newline = "\r\n"
    else:
        newline = "\n"
    try:
        source = original.decode("utf-8")
        modified = modify(source.replace("\r\n", "\n"))
    except (UnicodeDecodeError, ValueError, SyntaxError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.check:
        print(f"OK: insertion point found and new {TARGET} compiles; file unchanged.")
        return 0

    if newline == "\r\n":
        modified = modified.replace("\n", "\r\n")
    TARGET.write_bytes(modified.encode("utf-8"))
    print(f"Updated: {TARGET}")
    print("Default symmetry tolerance: 1e-10")
    print("Override with CSF_CUF_SYMMETRY_RTOL=1e-12 (or another value).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
