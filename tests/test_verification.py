"""
Pytest wrapper for docs/verification scripts.

Each test calls run_verification() directly — no subprocess, no argparse.
Each script's own DEFAULT_MESH_SIZE / DEFAULT_Z_STATIONS are used so the
mesh resolution matches the tolerances that were validated for that geometry.
Reports are written to docs/verification/ alongside the source scripts.
plot=False skips matplotlib windows.
"""

import sys
from pathlib import Path

# Make the verification scripts importable without installing them.
VERIFICATION_DIR = Path(__file__).parent.parent / "docs" / "verification"
sys.path.insert(0, str(VERIFICATION_DIR))

import csf_sp_cell_verification as _cell
import csf_sp_complex_integration_verification as _complex
import csf_sp_wall_complex_verification as _wall


def test_cell_verification():
    """@cell geometry + torsion: CSF ordinary reference vs csf_sp."""
    passed = _cell.run_verification(
        z_stations=_cell.DEFAULT_Z_STATIONS,
        mesh_size=_cell.DEFAULT_MESH_SIZE,
        report_path=VERIFICATION_DIR / "csf_sp_cell_verification_report.md",
        plot=False,
    )
    assert passed, "csf_sp_cell_verification FAILED — check tolerances or geometry."


def test_complex_integration_verification():
    """Complex integration: CSF-SP path on a multi-polygon section."""
    passed = _complex.run_verification(
        z_stations=_complex.DEFAULT_Z_STATIONS,
        mesh_size=_complex.DEFAULT_MESH_SIZE,
        report_path=VERIFICATION_DIR / "csf_sp_complex_integration_report.md",
        plot=False,
    )
    assert passed, "csf_sp_complex_integration_verification FAILED."


def test_wall_complex_verification():
    """Complex @wall section: geometry + torsion cross-check."""
    passed = _wall.run_verification(
        z_stations=_wall.DEFAULT_Z_STATIONS,
        mesh_size=_wall.DEFAULT_MESH_SIZE,
        report_path=VERIFICATION_DIR / "csf_sp_wall_complex_verification_report.md",
        plot=False,
    )
    assert passed, "csf_sp_wall_complex_verification FAILED."
