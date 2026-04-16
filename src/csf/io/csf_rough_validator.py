"""
csf_rough_validator.py
======================

Early-stage validator for CSF geometry YAML files.

Runs *before* CSFReader to catch common authoring mistakes and provide
friendly, actionable error messages instead of raw Python tracebacks.

What it checks
--------------
- YAML syntax errors (indentation, missing ':', missing '-' in lists)
- Quoted numbers (e.g. "10.0" instead of 10.0)
- Missing or misspelled root key 'CSF:'
- Unknown keys at CSF level (e.g. 'wight_laws' → suggests 'weight_laws')
- Missing or empty 'z:', 'weight:', vertex coordinates
- weight_laws structure: missing '-', wrong comma separator, unknown polygon ids
- weight_laws formula: Python syntax errors (with caret pointer), unrecognised
  variable names (with case-insensitive suggestions)

What it does NOT check
----------------------
- Geometric validity (CCW order, self-intersections, nesting correctness)
- Physical consistency (weight signs, @cell/@wall rules)
- Anything that requires loading the full CSF model

These belong to deeper layers (CSFReader, ContinuousSectionField).

Usage as a library
------------------
    from csf.io.csf_rough_validator import validate_text

    ok, report = validate_text(text, source="my_section.yaml")
    if not ok:
        for line in report:
            print(line)

Usage as a script
-----------------
    python -m csf.io.csf_rough_validator my_section.yaml

Returns 0 (ok), 1 (validation failed), 2 (file not found).
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


# Detect the first top-level YAML key directly from raw text.
# This is used only to provide a more precise diagnostic when the required
# root key "CSF:" is missing or replaced by another key.
_ROOT_KEY_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<key>[^#\s][^:]*):(?:\s|$)")


def _find_first_root_key_in_text(text: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Return the first top-level YAML key found in raw text, skipping blank lines and comments.

    Returns:
        (key, line_no) or (None, None)
    """
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()

        if not stripped or stripped.startswith("#"):
            continue

        m = _ROOT_KEY_RE.match(raw)
        if m and not m.group("indent"):
            return m.group("key").strip(), i

    return None, None


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

    # Reject misplaced top-level keys that must stay inside "CSF:".
    # Example: "weight_laws" at YAML root must raise an error.
    if "weight_laws" in doc:
        raise ValidationError(
            "Invalid YAML structure: 'weight_laws' is defined at the YAML root level.\n"
            f"In CSF files, 'weight_laws' must be placed inside the '{TOP_KEY}:' block.\n"
            "Fix example:\n"
            f"  {TOP_KEY}:\n"
            "    sections: ...\n"
            "    weight_laws:\n"
            "      - 'rect,rect: ...'"
        )

    csf = _require_mapping(doc[TOP_KEY], f"{TOP_KEY}")

    _KNOWN_CSF_KEYS = {"sections", "weight_laws"}
    unknown_csf_keys = set(csf.keys()) - _KNOWN_CSF_KEYS
    if unknown_csf_keys:
        import difflib
        for uk in sorted(unknown_csf_keys):
            matches = difflib.get_close_matches(uk, sorted(_KNOWN_CSF_KEYS), n=1, cutoff=0.6)
            if matches:
                raise ValidationError(
                    f"{TOP_KEY} contains unknown key '{uk}'.\n"
                    f"Did you mean '{matches[0]}'?\n"
                    f"Fix: rename '{uk}:' to '{matches[0]}:'"
                )
            # Only warn for keys with no suggestion — could be a future extension
            # raise ValidationError(f"{TOP_KEY} contains unknown key '{uk}'.")

    if "sections" not in csf:
        raise ValidationError(f"{TOP_KEY} missing required 'sections:' key.")

    sections = _require_mapping(csf["sections"], f"{TOP_KEY}.sections")
    if not sections:
        raise ValidationError(f"{TOP_KEY}.sections must be non-empty.")


    # Collect polygon ids while scanning sections.
    # This is used to provide friendlier diagnostics for weight_laws typos (e.g. 'web_star' vs 'web_start').
    poly_ids: set[str] = set()

    for sec_name, sec_data in sections.items():
        if not isinstance(sec_name, str) or not sec_name.startswith("S"):
            raise ValidationError(f"{TOP_KEY}.sections keys must start with 'S' (e.g. S0, S1). Found: {sec_name!r}")

        sec_path = f"{TOP_KEY}.sections.{sec_name}"
        sec_map = _require_mapping(sec_data, sec_path)

        if "z" not in sec_map:
            raise ValidationError(f"{sec_path} missing required 'z:' key.")
        if not _is_strict_number(sec_map["z"]):
            v = sec_map["z"]
            if v is None:
                raise ValidationError(
                    f"{sec_path}.z has no value.\n"
                    "You probably wrote:\n"
                    "  z:\n"
                    "Fix:\n"
                    "  z: 0.0"
                )
            raise ValidationError(f"{sec_path}.z must be a finite number (no quotes). Found: {v!r} ({type(v).__name__})")

        if "polygons" not in sec_map:
            raise ValidationError(f"{sec_path} missing required 'polygons:' key.")

        poly_items = _coerce_polygons_container(sec_map["polygons"])
        if not poly_items:
            raise ValidationError(f"{sec_path}.polygons must be non-empty.")

        for poly_name, poly_map in poly_items:
            # If polygons is a list, poly_name may be None. That's ok for this rough validator.
            poly_path = f"{sec_path}.polygons.{poly_name}" if poly_name else f"{sec_path}.polygons[?]"


            # Track named polygons for weight_laws validation.
            if isinstance(poly_name, str) and poly_name.strip():
                poly_ids.add(poly_name.strip())

            if "weight" not in poly_map:
                raise ValidationError(f"{poly_path} missing required 'weight:' key.")
            if not _is_strict_number(poly_map["weight"]):
                v = poly_map["weight"]
                if v is None:
                    raise ValidationError(
                        f"{poly_path}.weight has no value.\n"
                        "You probably wrote:\n"
                        "  weight:\n"
                        "Fix:\n"
                        "  weight: 1.0"
                    )
                raise ValidationError(f"{poly_path}.weight must be a finite number (no quotes). Found: {v!r} ({type(v).__name__})")

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
                    if x is None or y is None:
                        raise ValidationError(
                            f"{poly_path}.vertices[{j}] has a missing coordinate.\n"
                            "You probably wrote:\n"
                            "  - [0.0, ]\n"
                            "Fix:\n"
                            "  - [0.0, 0.0]"
                        )
                    raise ValidationError(f"{poly_path}.vertices[{j}] coordinates must be numbers (no quotes). Found: {v!r}")

    # weight_laws optional, if present must be list of strings containing ":"
    if "weight_laws" in csf:
        wl = csf["weight_laws"]
        if not isinstance(wl, list) or not wl:
            # Common authoring mistake: missing '-' before each law item.
            # YAML parses the block as a scalar string instead of a list.
            if isinstance(wl, str) and ":" in wl:
                raise ValidationError(
                    f"{TOP_KEY}.weight_laws must be a YAML list, but a plain string was found.\n"
                    "You are probably missing the '-' before each item.\n"
                    "You wrote:\n"
                    f"  weight_laws:\n"
                    f"    {wl}\n"
                    "Fix:\n"
                    f"  weight_laws:\n"
                    f"    - '{wl}'"
                )
            raise ValidationError(f"{TOP_KEY}.weight_laws is optional, but if present it must be a non-empty list.")

        for i, item in enumerate(wl):
            # Common YAML authoring mistake:
            #   - web_start,web_end: 1.0 - ...
            # YAML parses this as a mapping (dict), not as a string.
            # Provide a friendly message that shows the fix (quote the whole item).
            if isinstance(item, dict):
                if len(item) == 1:
                    k = next(iter(item.keys()))
                    v = item[k]
                    raise ValidationError(
                        f"{TOP_KEY}.weight_laws[{i}] must be a SINGLE QUOTED string, but YAML parsed it as a mapping.\n"
                        "You wrote something like:\n"
                        f"  - {k}: {v}\n"
                        "Correct form (quote the entire item):\n"
                        f"  - '{k}: {v}'"
                    )

                raise ValidationError(
                    f"{TOP_KEY}.weight_laws[{i}] must be a string in the form 'poly0,poly1: expr' (quoted)."
                )

            if not isinstance(item, str) or ":" not in item:
                raise ValidationError(
                    f"{TOP_KEY}.weight_laws[{i}] must be a string in the form 'poly0,poly1: expr' (quoted)."
                )

            lhs, rhs = item.split(":", 1)

            # Check comma separator between polygon ids.
            # Catch 'rect rect: ...' (space instead of comma).
            lhs_stripped = lhs.strip()
            if lhs_stripped and "," not in lhs_stripped:
                # Only raise if it looks like two tokens separated by whitespace.
                parts = lhs_stripped.split()
                if len(parts) == 2:
                    raise ValidationError(
                        f"{TOP_KEY}.weight_laws[{i}]: polygon id pair must be comma-separated.\n"
                        f"Found: '{lhs_stripped}'\n"
                        f"Fix:   '{parts[0]},{parts[1]}: {rhs.strip()}'"
                    )

            # Compile-check the formula (Python syntax only — no execution).
            # This catches unbalanced parentheses, typos in operators, etc.
            formula = rhs.strip()
            if formula:
                try:
                    compile(formula, "<weight_law>", "eval")
                except SyntaxError as e:
                    # Build a caret pointing to the error position inside the formula.
                    col_in_formula = getattr(e, "offset", None)
                    pointer = ""
                    if col_in_formula is not None:
                        pointer = "\n" + " " * (col_in_formula - 1) + "^"
                    raise ValidationError(
                        f"{TOP_KEY}.weight_laws[{i}]: formula has a Python syntax error.\n"
                        f"Formula: {formula}{pointer}\n"
                        f"Detail:  {e.msg}"
                    )

            # MAINTENANCE NOTE: keep _KNOWN_VARS and _KNOWN_FUNCS in sync with the
            # weight law expression environment defined in section_field.py.
            # If CSF adds new variables or functions, add them here to avoid false positives..
            _KNOWN_VARS = {"z", "t", "w0", "w1", "L", "np"}
            _KNOWN_FUNCS = {"d", "d0", "d1", "E_lookup", "T_lookup"}
            # Collect identifiers from the formula using a simple regex.
            # First strip string literals (single or double quoted) to avoid
            # flagging filenames like 'test.txt' as unknown identifiers.
            _STRING_RE = re.compile(r"""(?:"[^"]*"|'[^']*')""")
            formula_no_strings = _STRING_RE.sub('""', formula)
            # Exclude identifiers that are attribute access (preceded by '.'),
            # so that np.cos, np.pi, np.exp etc. are not flagged as unknown.
            _IDENT_RE = re.compile(r"(?<!\.)(\b[A-Za-z_][A-Za-z0-9_]*\b)")
            found_idents = set(_IDENT_RE.findall(formula_no_strings))
            # Filter out known vars/funcs and Python builtins.
            _BUILTINS = {"True", "False", "None", "and", "or", "not", "in", "is"}
            unknown_idents = found_idents - _KNOWN_VARS - _KNOWN_FUNCS - _BUILTINS
            if unknown_idents:
                try:
                    import difflib
                    all_known = sorted(_KNOWN_VARS | _KNOWN_FUNCS)
                    suggestions = []
                    for uid in sorted(unknown_idents):
                        # Case-insensitive match: compare lowercased.
                        matches = difflib.get_close_matches(
                            uid.lower(),
                            [k.lower() for k in all_known],
                            n=1,
                            cutoff=0.5,
                        )
                        if matches:
                            # Map back to original case.
                            original = next(k for k in all_known if k.lower() == matches[0])
                            suggestions.append(f"  '{uid}' → did you mean '{original}'?")
                        else:
                            suggestions.append(f"  '{uid}' → not a recognised weight-law variable")
                    raise ValidationError(
                        f"{TOP_KEY}.weight_laws[{i}]: formula contains unrecognised identifier(s).\n"
                        "Known variables: z, t, w0, w1, L, np\n"
                        "Known functions: d(i,j), d0(i,j), d1(i,j), E_lookup(file), T_lookup(file)\n"
                        + "\n".join(suggestions)
                    )
                except ImportError:
                    raise ValidationError(
                        f"{TOP_KEY}.weight_laws[{i}]: formula contains unrecognised identifier(s): "
                        f"{sorted(unknown_idents)}.\n"
                        "Known variables: z, t, w0, w1, L, np\n"
                        "Known functions: d(i,j), d0(i,j), d1(i,j), E_lookup(file), T_lookup(file)"
                    )

            # Optional additional check (no new schema rule):
            # validate that polygon ids on the left-hand side exist in sections,
            # to catch typos like 'web_star' vs 'web_start'.
            # If polygons are unnamed (list style without 'name'), poly_ids may be empty; skip in that case.

            if poly_ids:
                lhs, _rhs = item.split(":", 1)

                def _strip_wall_cell(name: str) -> str:
                    i_wall = name.find("@wall")
                    i_cell = name.find("@cell")
                    cut = None
                    if i_wall != -1:
                        cut = i_wall
                    if i_cell != -1:
                        cut = i_cell if cut is None else min(cut, i_cell)
                    return name[:cut] if cut is not None else name

                names = [s.strip() for s in lhs.split(",") if s.strip()]
                if not names:
                    raise ValidationError(
                        f"{TOP_KEY}.weight_laws[{i}] has an empty polygon list on the left side.\n"
                        "Expected: 'poly0,poly1: expr'"
                    )

                poly_ids_norm = {_strip_wall_cell(pid) for pid in poly_ids}
                names_norm = [_strip_wall_cell(n) for n in names]

                unknown = [n for n, nn in zip(names, names_norm) if nn not in poly_ids_norm]
                if unknown:
                    # Best-effort suggestions (stdlib only).
                    try:
                        import difflib
                        sug_lines = []
                        for u in unknown:
                            u_norm = _strip_wall_cell(u)
                            matches = difflib.get_close_matches(u_norm, sorted(poly_ids_norm), n=3, cutoff=0.6)
                            if matches:
                                sug_lines.append(f"  - did you mean '{u}' -> {matches}?")
                    except Exception:
                        sug_lines = []

                    msg = (
                        f"{TOP_KEY}.weight_laws[{i}] References unknown polygon id(s): {unknown}.\n"
                        f"Known polygon ids (from sections): {sorted(poly_ids)}"
                    )
                    if sug_lines:
                        msg += "\nSuggestions:\n" + "\n".join(sug_lines)

                    raise ValidationError(msg)


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

    # Check the first top-level key directly in raw text so that a missing
    # "CSF:" root can be reported with a clearer and more localized diagnostic.
    first_root_key, first_root_line = _find_first_root_key_in_text(text)
    if TOP_KEY not in doc:
        report.append(f"[ERROR] Missing required root key '{TOP_KEY}:'.")

        if first_root_key is not None and first_root_line is not None:
            report.append(
                f"First top-level key found at line {first_root_line}: '{first_root_key}:'"
            )
            report.append(_make_context_snippet(text, first_root_line, 1))
            report.append(f"Hint: wrap the whole file under '{TOP_KEY}:'.")
        else:
            report.append("No top-level YAML key was found.")
            report.append(f"Hint: the file must start with '{TOP_KEY}:'.")

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