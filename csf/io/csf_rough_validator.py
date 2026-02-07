"""
csf_rough_validator.py
=====================

"Rough" (early) validation for CSF YAML files.

Why this exists
--------------
This validator is meant to run *before* the formal CSFReader object parsing, to provide
very user-friendly diagnostics for common authoring errors, especially:

1) YAML syntax errors (indentation, missing ":", missing "-" in lists)
2) Quoted numbers anywhere in the file (e.g. "10.0" instead of 10.0)

Important design choice
-----------------------
The validator MUST NOT produce false positives like:

- reporting "quoted number" when there are no quotes
- confusing "missing '-'" (list item) with "quoted number"

To guarantee this:
- "quoted number" detection is done ONLY by searching for explicit quotes in the raw text.
  If there are no quotes on the line, it cannot be a quoted-number error.

Interface
---------
- As a module: call `csf_rough_validator(filepath)` → returns 0/1/2 and prints diagnostics.
- As a library: call `validate_text(text, source)` → returns (ok, report_lines).

Notes
-----
- This validator is intentionally "rough": it checks a minimal CSF schema
  but does not attempt deep geometry checks or solver-related semantics.
- It accepts BOTH polygons styles:
    a) polygons as list (recommended for explicit order)
    b) polygons as mapping (dict) (order = insertion order from YAML)

"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import math
import re
import sys

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


# -----------------------------
# Configuration
# -----------------------------

NUM_SNIPPET_BEFORE = 3
NUM_SNIPPET_AFTER = 2

TOP_KEY = "CSF"


# -----------------------------
# Internal types
# -----------------------------

@dataclass
class ValidationMessage:
    """
    A single validation message (used by validate_text()).

    kind: "ERROR" or "WARN"
    message: human-friendly message
    line/col: optional location (1-based)
    """
    kind: str
    message: str
    line: Optional[int] = None
    col: Optional[int] = None


class ValidationError(Exception):
    """Raised internally when the validator wants to stop early with a message."""
    def __init__(self, message: str, line: Optional[int] = None, col: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col


# -----------------------------
# Helpers: numbers and snippets
# -----------------------------

def _is_strict_number(v: Any) -> bool:
    """
    "Super safe" numeric check.

    Accept ONLY:
    - int or float (real YAML numeric scalars)
    - NOT bool (bool is a subclass of int in Python)
    - finite values only (no NaN/Inf)
    """
    if type(v) not in (int, float):
        return False
    return math.isfinite(float(v))


def _make_context_snippet(text: str, line_no: int, col_no: Optional[int] = None) -> str:
    """
    Create a small, human-friendly snippet around a specific line.
    """
    lines = text.splitlines()
    if not lines:
        return "<empty input>"

    lo = max(1, line_no - NUM_SNIPPET_BEFORE)
    hi = min(len(lines), line_no + NUM_SNIPPET_AFTER)

    out: List[str] = []
    for ln in range(lo, hi + 1):
        prefix = ">>" if ln == line_no else "  "
        out.append(f"{prefix} {ln:4d} | {lines[ln - 1]}")
        if ln == line_no and col_no is not None and col_no > 0:
            caret_pos = len(f"{prefix} {ln:4d} | ") + (col_no - 1)
            out.append(" " * caret_pos + "^")
    return "\n".join(out)


# -----------------------------
# Phase 1: YAML parsing
# -----------------------------

def _safe_yaml_parse(text: str) -> Dict[str, Any]:
    """
    Parse YAML and raise ValidationError with line/col snippet if parsing fails.
    """
    if yaml is None:
        raise ValidationError("PyYAML is not available (cannot parse YAML).")

    try:
        doc = yaml.safe_load(text)
    except Exception as e:
        # PyYAML usually provides a "problem_mark" with line/column
        mark = getattr(e, "problem_mark", None)
        if mark is not None:
            line = int(getattr(mark, "line", 0)) + 1
            col = int(getattr(mark, "column", 0)) + 1
            raise ValidationError(f"YAML syntax error: {getattr(e, 'problem', str(e))}", line=line, col=col)
        raise ValidationError(f"YAML parse error: {e}")

    if not isinstance(doc, dict):
        raise ValidationError("YAML root must be a mapping (dictionary).")
    return doc


# -----------------------------
# Phase 2: quoted-number scan (RAW TEXT)
# -----------------------------

# Matches ONLY a numeric token wrapped in quotes: "10.0" or '-0.15' etc.
# It will NOT match:
# - unquoted numbers: 10.0
# - lists without quotes: [0.15, 0.0]
# - formulas in strings: "w0 + 0.5*(...)"  (because 0.5 is not quoted inside)
_QUOTED_NUMBER_RE = re.compile(
    r"""(?P<q>["'])\s*(?P<num>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*(?P=q)"""
)

def _scan_quoted_numbers_in_text(text: str) -> List[Tuple[int, int, str]]:
    """
    Scan the raw YAML text for quoted numbers.

    Returns a list of tuples: (line_no, col_no, matched_token)
    where matched_token includes the quotes (e.g. '"10.0"').

    Key rule to prevent false positives:
    - If a line contains no quotes, it cannot be a quoted-number error.
    """
    hits: List[Tuple[int, int, str]] = []
    lines = text.splitlines()

    for i, raw in enumerate(lines, start=1):
        # quick guard: no quotes => cannot be quoted-number
        if '"' not in raw and "'" not in raw:
            continue

        for m in _QUOTED_NUMBER_RE.finditer(raw):
            col = m.start() + 1
            token = raw[m.start():m.end()]
            hits.append((i, col, token))

    return hits


# -----------------------------
# Phase 3: rough CSF schema checks (PARSED DOC)
# -----------------------------

def _require_mapping(d: Any, what: str) -> Dict[str, Any]:
    if not isinstance(d, dict):
        raise ValidationError(f"{what} must be a mapping (dictionary). Found: {type(d).__name__}")
    return d

def _require_list(v: Any, what: str) -> List[Any]:
    if not isinstance(v, list):
        raise ValidationError(f"{what} must be a YAML list. Found: {type(v).__name__}")
    return v

def _coerce_polygons_container(polys: Any) -> List[Tuple[Optional[str], Dict[str, Any]]]:
    """
    Accept polygons as:
      - mapping: {lowerpart: {...}, upperpart: {...}}
      - list:    [{name: lowerpart, ...}, {name: upperpart, ...}]

    Return a uniform list of (name, poly_dict).
    For mapping mode: name is the key.
    For list mode: name is poly_dict.get("name") (optional for this validator).
    """
    out: List[Tuple[Optional[str], Dict[str, Any]]] = []

    if isinstance(polys, dict):
        for name, val in polys.items():
            if not isinstance(val, dict):
                raise ValidationError(f"polygons.{name} must be a mapping. Found: {type(val).__name__}")
            out.append((str(name), val))
        return out

    if isinstance(polys, list):
        for idx, item in enumerate(polys):
            if not isinstance(item, dict):
                raise ValidationError(f"polygons[{idx}] must be a mapping. Found: {type(item).__name__}")
            nm = item.get("name")
            out.append((str(nm) if isinstance(nm, str) else None, item))
        return out

    raise ValidationError(f"polygons must be a mapping or list. Found: {type(polys).__name__}")


def _validate_csf_structure(doc: Dict[str, Any]) -> None:
    """
    Minimal schema validation for CSF.

    Raises ValidationError on the first detected issue (rough validator is allowed to be strict).
    """
    if TOP_KEY not in doc:
        raise ValidationError(f"Root missing exact '{TOP_KEY}:' key.")

    csf = _require_mapping(doc[TOP_KEY], f"{TOP_KEY}")

    if "sections" not in csf:
        raise ValidationError(f"{TOP_KEY} missing required 'sections:' key.")

    sections = _require_mapping(csf["sections"], f"{TOP_KEY}.sections")
    if not sections:
        raise ValidationError(f"{TOP_KEY}.sections must be non-empty.")

    for sec_name, sec_data in sections.items():
        if not isinstance(sec_name, str) or not sec_name.startswith("S"):
            raise ValidationError(f"{TOP_KEY}.sections keys must start with 'S' (e.g. S0, S1). Found: {sec_name!r}")

        sec_path = f"{TOP_KEY}.sections.{sec_name}"
        sec_map = _require_mapping(sec_data, sec_path)

        if "z" not in sec_map:
            raise ValidationError(f"{sec_path} missing required 'z:' key.")
        if not _is_strict_number(sec_map["z"]):
            raise ValidationError(f"{sec_path}.z must be a finite number (no quotes). Found: {sec_map['z']!r} ({type(sec_map['z']).__name__})")

        if "polygons" not in sec_map:
            raise ValidationError(f"{sec_path} missing required 'polygons:' key.")

        poly_items = _coerce_polygons_container(sec_map["polygons"])
        if not poly_items:
            raise ValidationError(f"{sec_path}.polygons must be non-empty.")

        for poly_name, poly_map in poly_items:
            # If polygons is a list, poly_name may be None. That's ok for this rough validator.
            poly_path = f"{sec_path}.polygons.{poly_name}" if poly_name else f"{sec_path}.polygons[?]"

            if "weight" not in poly_map:
                raise ValidationError(f"{poly_path} missing required 'weight:' key.")
            if not _is_strict_number(poly_map["weight"]):
                raise ValidationError(f"{poly_path}.weight must be a finite number (no quotes). Found: {poly_map['weight']!r} ({type(poly_map['weight']).__name__})")

            if "vertices" not in poly_map:
                raise ValidationError(f"{poly_path} missing required 'vertices:' key.")

            verts = _require_list(poly_map["vertices"], f"{poly_path}.vertices")
            if len(verts) < 3:
                raise ValidationError(f"{poly_path}.vertices must have at least 3 vertices.")

            for j, v in enumerate(verts):
                if not isinstance(v, list) or len(v) != 2:
                    raise ValidationError(f"{poly_path}.vertices[{j}] must be [x, y]. Found: {v!r}")
                x, y = v[0], v[1]
                if not _is_strict_number(x) or not _is_strict_number(y):
                    raise ValidationError(f"{poly_path}.vertices[{j}] coordinates must be numbers (no quotes). Found: {v!r}")

    # weight_laws optional, if present must be list of strings containing ":"
    if "weight_laws" in csf:
        wl = csf["weight_laws"]
        if not isinstance(wl, list) or not wl:
            raise ValidationError(f"{TOP_KEY}.weight_laws is optional, but if present it must be a non-empty list.")
        for i, item in enumerate(wl):
            if not isinstance(item, str) or ":" not in item:
                raise ValidationError(f"{TOP_KEY}.weight_laws[{i}] must be a string in the form 'poly0,poly1: expr'.")


# -----------------------------
# Public API
# -----------------------------

def validate_text(text: str, source: str = "<memory>") -> Tuple[bool, List[str]]:
    """
    Library entry point: validate YAML text and return (ok, report_lines).

    - ok == True  → safe to proceed to the next phase (formal CSFReader parsing)
    - ok == False → report_lines contains human-friendly messages
    """
    report: List[str] = []

    # 1) YAML parse
    try:
        doc = _safe_yaml_parse(text)
    except ValidationError as e:
        report.append(f"[ERROR] YAML parse failed for {source}: {e.message}")
        if e.line is not None:
            report.append(_make_context_snippet(text, e.line, e.col))
        return False, report

    # 2) quoted-number scan (raw text)
    qhits = _scan_quoted_numbers_in_text(text)
    if qhits:
        ln, col, token = qhits[0]
        report.append("[ERROR] Quoted numbers detected. All numeric values must be raw (no quotes).")
        report.append(f"First occurrence at line {ln}, column {col}: {token}")
        report.append(_make_context_snippet(text, ln, col))
        if len(qhits) > 1:
            report.append(f"Additional quoted numbers found: {len(qhits) - 1}")
        report.append('Hint: replace "10.0" with 10.0 (remove quotes).')
        return False, report

    # 3) rough CSF structure on parsed doc
    try:
        _validate_csf_structure(doc)
    except ValidationError as e:
        report.append(f"[ERROR] CSF structure validation failed for {source}: {e.message}")
        return False, report

    return True, ["[OK] Rough CSF validation passed."]


def csf_rough_validator(filepath: str) -> int:
    """
    Script-friendly entry point.

    Returns:
      0 -> ok
      1 -> validation failed
      2 -> file missing/unreadable
    """
    p = Path(filepath)
    if not p.exists():
        print(f"ERROR: file not found: {filepath}", file=sys.stderr)
        return 2

    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR: cannot read file: {filepath}: {e}", file=sys.stderr)
        return 2

    ok, report = validate_text(text, source=str(p))
    for line in report:
        print(line)

    return 0 if ok else 1
