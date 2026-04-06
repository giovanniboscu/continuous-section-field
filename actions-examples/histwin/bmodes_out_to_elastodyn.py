"""
Update ElastoDyn tower mode-shape coefficients from a BModes .out file.
This script only edits coefficient lines and does not rewrite the tower-file format.

Role in the pipeline
--------------------
In the standard NREL/NLR workflow, the step between BModes output and
ElastoDyn input is performed manually using the Excel spreadsheet
ModeShapePolyFitting.xls: the user pastes BModes modal data into the
sheet, reads back the polynomial coefficients, and copies them into the
ElastoDyn tower .dat file by hand.

This script replaces that manual step with an automated, scriptable
equivalent that can be run from the command line or called from a
launcher script.  It adds two controls that the spreadsheet does not
provide:

  - Automatic mode identification with twist-ratio filtering, so that
    bending-dominated modes are preferred over mixed or torsional modes.
  - Tip-displacement threshold filtering, which rejects modes whose tip
    displacement in the relevant axis is less than 1% of the peak value
    among all candidates.  Without this filter, a mode with a near-zero
    tip value would be normalized by that small number, amplifying noise
    by a factor of 1/tip and producing an ill-conditioned polynomial fit
    with large oscillating coefficients (condition numbers above 1000,
    coefficient magnitudes above 1000) that satisfy sum=1.0 formally but
    do not represent the physical mode shape.

This script is intentionally separate from csf_to_elastodyn.py.
It only:
  1. parses BModes modal output (.out)
  2. selects the four tower bending modes (FA1, FA2, SS1, SS2)
  3. fits ElastoDyn polynomials a2*x^2 + ... + a6*x^6
  4. rewrites TwFAM*Sh / TwSSM*Sh lines in the ElastoDyn tower .dat file

Usage examples
--------------
Automatic mode selection:
    python bmodes_out_to_elastodyn.py histwin_tower_BModes_tower.out \
        histwin_tower_ElastoDyn_Tower.dat

Manual mode selection:
    python bmodes_out_to_elastodyn.py histwin_tower_BModes_tower.out \
        histwin_tower_ElastoDyn_Tower.dat \
        --fa1 1 --ss1 2 --fa2 3 --ss2 5

Notes
-----
- BModes mode shapes are normalized internally so that the selected tip
  displacement component equals 1.0 before polynomial fitting.
- The fit enforces sum(coeffs) = 1.0 exactly, which is the ElastoDyn
  normalization at x = 1 for the polynomial terms x^2..x^6.
- Automatic selection prefers low-frequency bending-dominated modes and
  penalizes strong twist participation, but manual override is available.
- If automatic selection fails or selects an unexpected mode, use the
  --fa1/--fa2/--ss1/--ss2 flags to specify BModes mode numbers directly.

"""

from __future__ import annotations

import argparse
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


MODE_HEADER_RE = re.compile(
    r"^\s*-+\s*Mode\s+No\.\s*(\d+)\s*\(freq\s*=\s*([0-9Ee+\-.]+)\s*Hz\)",
    re.IGNORECASE,
)
DATA_LINE_RE = re.compile(
    r"^\s*([0-9Ee+\-.]+)\s+([0-9Ee+\-.]+)\s+([0-9Ee+\-.]+)\s+([0-9Ee+\-.]+)\s+([0-9Ee+\-.]+)\s+([0-9Ee+\-.]+)\s*$"
)
COEFF_RE = re.compile(
    r"^(\s*)([-+0-9Ee\.]+)(\s+)(Tw(?:FA|SS)M[12]Sh\(([2-6])\))(.*)$"
)


@dataclass
class ModeShape:
    mode_no: int
    freq_hz: float
    x: np.ndarray
    ss_disp: np.ndarray
    ss_slope: np.ndarray
    fa_disp: np.ndarray
    fa_slope: np.ndarray
    twist: np.ndarray

    def dominant_axis(self) -> str:
        ss = float(np.max(np.abs(self.ss_disp)))
        fa = float(np.max(np.abs(self.fa_disp)))
        return "SS" if ss >= fa else "FA"

    def dominance_value(self) -> float:
        ss = float(np.max(np.abs(self.ss_disp)))
        fa = float(np.max(np.abs(self.fa_disp)))
        return max(ss, fa)

    def twist_ratio(self) -> float:
        dom = self.dominance_value()
        tw = float(np.max(np.abs(self.twist)))
        if dom <= 1e-14:
            return math.inf
        return tw / dom


@dataclass
class SelectedModes:
    fa1: ModeShape
    fa2: ModeShape
    ss1: ModeShape
    ss2: ModeShape


class BmodesParseError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Parse BModes .out and update ElastoDyn tower mode coefficients."
    )
    p.add_argument("bmodes_out", help="BModes .out file")
    p.add_argument("elastodyn_dat", help="ElastoDyn tower .dat file to update")
    p.add_argument("--out", default=None, help="Output .dat file (default: overwrite input)")
    p.add_argument("--backup", action="store_true", help="Create .bak backup of original .dat")
    p.add_argument("--fa1", type=int, default=None, help="Manual BModes mode number for FA1")
    p.add_argument("--fa2", type=int, default=None, help="Manual BModes mode number for FA2")
    p.add_argument("--ss1", type=int, default=None, help="Manual BModes mode number for SS1")
    p.add_argument("--ss2", type=int, default=None, help="Manual BModes mode number for SS2")
    return p.parse_args()


def parse_bmodes_out(path: Path) -> List[ModeShape]:
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    modes: List[ModeShape] = []
    i = 0
    while i < len(text):
        m = MODE_HEADER_RE.match(text[i])
        if not m:
            i += 1
            continue

        mode_no = int(m.group(1))
        freq_hz = float(m.group(2).replace("D", "E"))
        i += 1

        # Skip blank/header lines until data rows start.
        while i < len(text) and not DATA_LINE_RE.match(text[i]):
            i += 1

        rows: List[Tuple[float, float, float, float, float, float]] = []
        while i < len(text):
            dm = DATA_LINE_RE.match(text[i])
            if not dm:
                break
            rows.append(tuple(float(dm.group(k).replace("D", "E")) for k in range(1, 7)))
            i += 1

        if not rows:
            raise BmodesParseError(f"No data rows found for mode {mode_no} in {path}")

        arr = np.array(rows, dtype=float)
        modes.append(
            ModeShape(
                mode_no=mode_no,
                freq_hz=freq_hz,
                x=arr[:, 0],
                ss_disp=arr[:, 1],
                ss_slope=arr[:, 2],
                fa_disp=arr[:, 3],
                fa_slope=arr[:, 4],
                twist=arr[:, 5],
            )
        )
    if not modes:
        raise BmodesParseError(f"No BModes blocks found in {path}")
    return modes


def choose_modes_automatic(modes: List[ModeShape]) -> SelectedModes:
    # Keep only modes with non-trivial displacement in the relevant axis.
    fa_candidates = [m for m in modes if np.max(np.abs(m.fa_disp)) > 1e-8]
    ss_candidates = [m for m in modes if np.max(np.abs(m.ss_disp)) > 1e-8]

    if len(fa_candidates) < 2 or len(ss_candidates) < 2:
        raise BmodesParseError(
            "Automatic selection failed: fewer than two FA or SS displacement modes found."
        )

    # Filter out modes whose tip displacement is too small relative to the
    # best candidate in each axis.  A near-zero tip value causes the
    # normalization step to amplify noise by 1/tip, making the subsequent
    # polynomial fit ill-conditioned (condition numbers > 1000 and large
    # oscillating coefficients).  The threshold of 1% of the peak tip
    # displacement rejects clearly unsuitable modes while remaining loose
    # enough not to discard legitimate higher modes.
    fa_tip_max = max(abs(float(m.fa_disp[-1])) for m in fa_candidates)
    ss_tip_max = max(abs(float(m.ss_disp[-1])) for m in ss_candidates)
    fa_candidates = [m for m in fa_candidates if abs(float(m.fa_disp[-1])) >= 0.01 * fa_tip_max]
    ss_candidates = [m for m in ss_candidates if abs(float(m.ss_disp[-1])) >= 0.01 * ss_tip_max]

    if len(fa_candidates) < 2 or len(ss_candidates) < 2:
        raise BmodesParseError(
            "Automatic selection failed: fewer than two FA or SS modes passed the "
            "tip-displacement threshold. Use --fa1/--fa2/--ss1/--ss2 to select manually."
        )

    # Sort first by twist penalty, then by frequency.
    fa_candidates.sort(key=lambda m: (m.twist_ratio(), m.freq_hz))
    ss_candidates.sort(key=lambda m: (m.twist_ratio(), m.freq_hz))

    # Among the best twist-penalized candidates, retain order by frequency.
    fa_best = sorted(fa_candidates[: max(2, min(6, len(fa_candidates)))], key=lambda m: m.freq_hz)
    ss_best = sorted(ss_candidates[: max(2, min(6, len(ss_candidates)))], key=lambda m: m.freq_hz)

    return SelectedModes(
        fa1=fa_best[0],
        fa2=fa_best[1],
        ss1=ss_best[0],
        ss2=ss_best[1],
    )


def choose_modes_manual(modes: List[ModeShape], fa1: int, fa2: int, ss1: int, ss2: int) -> SelectedModes:
    by_no: Dict[int, ModeShape] = {m.mode_no: m for m in modes}
    missing = [n for n in [fa1, fa2, ss1, ss2] if n not in by_no]
    if missing:
        raise BmodesParseError(f"Requested BModes mode numbers not found: {missing}")
    return SelectedModes(
        fa1=by_no[fa1],
        fa2=by_no[fa2],
        ss1=by_no[ss1],
        ss2=by_no[ss2],
    )


def constrained_fit_coeffs(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Fit y ~= c2*x^2 + ... + c6*x^6 enforcing sum(c2..c6)=1 exactly.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    # Eliminate c6 = 1 - (c2+c3+c4+c5)
    b2 = x**2 - x**6
    b3 = x**3 - x**6
    b4 = x**4 - x**6
    b5 = x**5 - x**6
    rhs = y - x**6

    A = np.column_stack([b2, b3, b4, b5])
    coeff_2345, *_ = np.linalg.lstsq(A, rhs, rcond=None)
    c2, c3, c4, c5 = coeff_2345
    c6 = 1.0 - (c2 + c3 + c4 + c5)
    return np.array([c2, c3, c4, c5, c6], dtype=float)


def normalize_component(x: np.ndarray, disp: np.ndarray) -> np.ndarray:
    disp = np.asarray(disp, dtype=float)
    tip = float(disp[-1])
    if abs(tip) <= 1e-14:
        raise BmodesParseError("Selected mode has near-zero tip displacement in the chosen component.")
    return disp / tip


def mode_to_coeffs(mode: ModeShape, axis: str) -> np.ndarray:
    if axis == "FA":
        y = normalize_component(mode.x, mode.fa_disp)
    elif axis == "SS":
        y = normalize_component(mode.x, mode.ss_disp)
    else:
        raise ValueError(axis)
    return constrained_fit_coeffs(mode.x, y)


def update_elastodyn_dat(
    dat_path: Path,
    out_path: Path,
    coeffs: Dict[str, np.ndarray],
    backup: bool = False,
) -> None:
    text = dat_path.read_text(encoding="utf-8", errors="replace").splitlines()

    if backup and out_path.resolve() == dat_path.resolve():
        shutil.copy2(dat_path, dat_path.with_suffix(dat_path.suffix + ".bak"))

    updated: List[str] = []
    seen: Dict[str, int] = {}

    for line in text:
        m = COEFF_RE.match(line)
        if not m:
            updated.append(line)
            continue

        prefix_ws, _old_num, gap, label_full, power_str, tail = m.groups()
        key_match = re.match(r"(Tw(?:FA|SS)M[12]Sh)\(([2-6])\)", label_full)
        if not key_match:
            updated.append(line)
            continue

        block = key_match.group(1)
        power = int(key_match.group(2))
        if block not in coeffs:
            updated.append(line)
            continue

        value = coeffs[block][power - 2]
        seen.setdefault(block, 0)
        seen[block] += 1
        updated.append(f"{prefix_ws}{value:.10E}{gap}{label_full}{tail}")

    out_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    bmodes_out = Path(args.bmodes_out)
    elastodyn_dat = Path(args.elastodyn_dat)
    out_dat = Path(args.out) if args.out else elastodyn_dat

    modes = parse_bmodes_out(bmodes_out)

    manual = all(v is not None for v in [args.fa1, args.fa2, args.ss1, args.ss2])
    if manual:
        sel = choose_modes_manual(modes, args.fa1, args.fa2, args.ss1, args.ss2)
    else:
        sel = choose_modes_automatic(modes)

    coeffs = {
        "TwFAM1Sh": mode_to_coeffs(sel.fa1, "FA"),
        "TwFAM2Sh": mode_to_coeffs(sel.fa2, "FA"),
        "TwSSM1Sh": mode_to_coeffs(sel.ss1, "SS"),
        "TwSSM2Sh": mode_to_coeffs(sel.ss2, "SS"),
    }

    update_elastodyn_dat(elastodyn_dat, out_dat, coeffs, backup=args.backup)

    print("Selected BModes -> ElastoDyn mapping")
    print(f"  FA1 <- mode {sel.fa1.mode_no}  ({sel.fa1.freq_hz:.6f} Hz)")
    print(f"  FA2 <- mode {sel.fa2.mode_no}  ({sel.fa2.freq_hz:.6f} Hz)")
    print(f"  SS1 <- mode {sel.ss1.mode_no}  ({sel.ss1.freq_hz:.6f} Hz)")
    print(f"  SS2 <- mode {sel.ss2.mode_no}  ({sel.ss2.freq_hz:.6f} Hz)")
    print()
    for name, arr in coeffs.items():
        pretty = ", ".join(f"{v:.8f}" for v in arr)
        print(f"  {name}(2..6) = [{pretty}]")
    print()
    print(f"Updated ElastoDyn file: {out_dat}")


if __name__ == "__main__":
    main()
