"""
csf_reader.py
=============

User-facing YAML reader + validator for CSF (Continuous Section Field).

This module is intentionally separated from the core CSF geometry/interpolation engine
(ContinuousSectionField) so that:

- The CSF core stays focused on geometry + discretization logic.
- I/O concerns (file parsing, schema validation, user-friendly error reporting) are isolated.
- The reader can evolve independently (e.g., support CLI workflows, action files, etc.).

Design principles
-----------------
1) No raw Python tracebacks for end users
   - All failures become controlled Issues (ERROR/WARNING) using CSFIssues catalog.

2) Two-phase validation
   A) "Corruption" precheck on raw YAML text (before parsing)
      - Detect frequent authoring mistakes that are otherwise hard to understand.
      - Report key name + line number when possible.
      - Stop before yaml.safe_load if corruption is detected.
   B) Formal validation on parsed YAML object
      - Structural checks (required keys, types).
      - Semantic checks (z ordering, polygon homology, etc.).

3) Object construction only after passing checks
   - If the file passes checks, instantiate:
       field = ContinuousSectionField(section0=s0, section1=s1)

4) Input flexibility (important)
   - YAML output (writer): polygons as LIST is recommended (explicit order).
   - YAML input (reader): accept BOTH
       a) polygons as LIST
       b) polygons as MAP (dict)
     If polygons is a map, it is coerced to a list preserving insertion order, and the
     reader emits ONE warning per file.

Expected YAML (minimal)
----------------------
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        - name: lowerpart
          weight: 1.0
          vertices:
            - [-0.15, -0.6]
            - [ 0.15, -0.6]
            - [ 0.15,  0.0]
            - [-0.15,  0.0]
    S1:
      z: 10.0
      polygons:
        - name: lowerpart
          weight: 1.0
          vertices:
            - [-0.15, -0.1]
            - [ 0.15, -0.1]
            - [ 0.15,  0.0]
            - [-0.15,  0.0]

Optional:
  weight_laws:
    - "lowerpart,lowerpart: w0 + (w1-w0)*(z/L)"
    - "upperpart,upperpart: w0 + (w1-w0)*(z/L)"

Notes about ordering
-------------------
CSF uses index-based homology for polygons/vertices across sections:
- polygon i in S0 corresponds to polygon i in S1
- vertex j in polygon i corresponds to vertex j in polygon i

Therefore, ordering of polygons is meaningful.
That is why YAML output should prefer list form.
For YAML input, if polygons is a dict, we preserve insertion order as defined in the file.

Dependencies
------------
- PyYAML is required to parse YAML (yaml.safe_load).
- CSFIssues comes from csf.io.csf_issues and must define the codes used below.

"""

from __future__ import annotations
from .csf_rough_validator import csf_rough_validator
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import math
import re
from pathlib import Path
import io
from contextlib import redirect_stdout, redirect_stderr
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from .csf_issues import CSFIssues, Issue, Severity


# -----------------------------
# Public result / configuration
# -----------------------------

@dataclass
class ReaderConfig:
    """
    Reader behavior configuration.

    Keep this conservative: more permissive inputs can be accepted, but errors must stay clear.
    """
    precheck_corruption: bool = True
    include_yaml_parser_context: bool = False

    # Input flexibility: accept polygons as dict/map, coerce to list (warn once per file).
    allow_polygons_map: bool = True

    # Weight laws validation and application (if field is created successfully).
    validate_weight_laws: bool = True

    # Require a top-level key (default "CSF") that wraps the CSF document.
    require_top_key: bool = True

    # Optional: cap number of precheck errors to avoid flooding in badly corrupted files.
    max_precheck_errors: int = 20


@dataclass
class ReadResult:
    """
    Output of CSFReader.
    - field: ContinuousSectionField instance when ok
    - issues: list of Issue
    """
    field: Optional[Any]
    issues: List[Issue]

    @property
    def ok(self) -> bool:
        """True if no ERROR issues exist."""
        return all(i.severity != Severity.ERROR for i in self.issues)


# -----------------------------
# Main reader class
# -----------------------------

class CSFReader:
    """
    CSF YAML reader, validator, and builder.

    Typical usage:

        from csf.io.csf_reader import CSFReader
        from csf.io.csf_issues import CSFIssues

        res = CSFReader().read_file("case.yaml")
        if not res.ok:
            print(CSFIssues.format_report(res.issues))
        else:
            field = res.field
    """

    def __init__(self, config: Optional[ReaderConfig] = None) -> None:
        self.config = config or ReaderConfig()

        # Accumulator: record coercions (polygons dict -> list) and emit a single warning per file.
        self._polygons_map_coercions: List[Dict[str, Any]] = []

        # Convenience for paths
        self._top_key = getattr(CSFIssues, "TOP_KEY", "CSF")  # should be "CSF" per your convention

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------



    def read_file(self, filepath: str) -> ReadResult:
        """
        Read CSF YAML from a file path and return a controlled ReadResult.

        Goals of this function
        ----------------------
        1) Reset any per-read state (e.g. warnings collected during parsing).
        2) Run an early "rough" validator (csf_rough_validator) to catch common authoring errors
        with friendly messages.
        - IMPORTANT: csf_rough_validator currently prints diagnostics to console.
            Here we capture that output so we can:
            a) avoid duplicate/confusing console messages
            b) attach the real reason to the Issue context
            c) generate a coherent hint (not always "quoted numbers")
        3) Read the file text (UTF-8) and then proceed with the full reader pipeline via read_text().
        """
        # Reset state collected during a previous read (this is per-run state, not persistent config).
        self._polygons_map_coercions = []
        issues: List[Issue] = []

        # ------------------------------------------------------------------
        # STEP 1: Early rough validation (captures console output)
        # ------------------------------------------------------------------
        # csf_rough_validator returns:
        #   0 -> OK
        #   1 -> validation failed (it prints a detailed reason)
        #   2 -> file missing/unreadable
        #
        # We capture stdout/stderr because the rough validator is "script-like".
        # This lets us show one controlled error (CSF_E_VALIDATOR) instead of:
        #   - rough validator printing something
        #   - then us printing another generic message unrelated to the actual failure


        buf = io.StringIO()
        p = Path(filepath)

        if not p.is_file():
            raise FileNotFoundError(f"File not found: {p.resolve()}")

        with redirect_stdout(buf), redirect_stderr(buf):
            validator_result = csf_rough_validator(filepath)
        validator_out = buf.getvalue().strip()

        if validator_result == 2:
            # Missing file or not readable: report as IO error (controlled).
            issues.append(
                CSFIssues.make(
                    "CSF_E_IO_READ",
                    path="$",
                    message="File not found or not readable.",
                    hint="Check the file path and permissions.",
                    context={"filepath": filepath},
                )
            )
            return ReadResult(field=None, issues=issues)

        if validator_result == 1:
            # Rough validation failed. Use the captured output as the authoritative reason.
            #
            # We keep the Issue message short, but attach full validator output in context.
            # Also, generate an *appropriate* hint based on the failure (no fixed 'quoted numbers' hint).
            msg = "CSF rough validation failed."
            hint = "Fix the YAML according to the validator output (see Context)."

            # Try to pick a more specific headline line from the validator output.
            # Example lines the validator may print:
            #   "[ERROR] CSF structure validation failed for case.yaml: CSF.sections.S0 missing required 'z:' key."
            for line in validator_out.splitlines():
                if "CSF structure validation failed" in line:
                    msg = line.strip()
                    break
                if line.startswith("[ERROR]"):
                    msg = line.strip()
                    break

            low = validator_out.lower()
            if "quoted numbers" in low:
                hint = 'Remove quotes around numbers (use 1.0 not "1.0").'
            elif "missing required 'z:'" in low or 'missing required "z:"' in low:
                hint = "Add the required 'z:' key under each section (e.g. z: 0.0)."
            elif "missing required 'polygons:'" in low or 'missing required "polygons:"' in low:
                hint = "Add the required 'polygons:' key under each section."
            elif "yaml syntax error" in low or "yaml parse" in low:
                hint = "Fix YAML syntax (indentation, ':' separators, list '-' markers)."

            issues.append(
                CSFIssues.make(
                    "CSF_E_VALIDATOR",
                    path="$",
                    message=msg,
                    hint=hint,
                    context={
                        "filepath": filepath,
                        "validator_output": validator_out,
                    },
                )
            )
            return ReadResult(field=None, issues=issues)

        # ------------------------------------------------------------------
        # STEP 2: Read the file content (UTF-8)
        # ------------------------------------------------------------------
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError as e:
            issues.append(
                CSFIssues.make(
                    "CSF_E_ENCODING",
                    path="$",
                    message="File is not valid UTF-8.",
                    hint="Save the file as UTF-8 (no BOM) and try again.",
                    context=str(e),
                )
            )
            return ReadResult(field=None, issues=issues)
        except Exception as e:
            issues.append(
                CSFIssues.make(
                    "CSF_E_IO_READ",
                    path="$",
                    message="Cannot read the file.",
                    hint="Check the file path and permissions.",
                    context=str(e),
                )
            )
            return ReadResult(field=None, issues=issues)

        # ------------------------------------------------------------------
        # STEP 3: Run the full CSFReader pipeline on the loaded text
        # ------------------------------------------------------------------
        # If your read_text() supports it, prefer: return self.read_text(text, source=filepath)
        # so error messages can reference the file name.
        
        return self.read_text(text)
    
    def read_text(self, text: str) -> ReadResult:
        """
        Read CSF YAML from a string.
        """
        self._polygons_map_coercions = []
        issues: List[Issue] = []

        doc = self._parse_yaml(text, issues)
        if doc is None:
            return ReadResult(field=None, issues=issues)

        csf_root = self._extract_csf_root(doc, issues)
        if csf_root is None:
            return ReadResult(field=None, issues=issues)

        s0_data, s1_data = self._extract_sections(csf_root, issues)
        if s0_data is None or s1_data is None:
            return ReadResult(field=None, issues=issues)

        s0 = self._parse_section("S0", s0_data, issues)
        s1 = self._parse_section("S1", s1_data, issues)

        # Emit a single warning if any polygons mapping was coerced.
        if self._polygons_map_coercions:
            issues.append(
                CSFIssues.make(
                    "CSF_W_POLYGONS_MAP_COERCED",
                    path=f"{self._top_key}.sections",
                    context=self._polygons_map_coercions,
                )
            )

        if s0 is None or s1 is None:
            return ReadResult(field=None, issues=issues)

        # Cross-section checks (order + homology)
        self._validate_domain_order(s0, s1, issues)
        self._validate_index_homology(s0, s1, issues)

        if any(i.severity == Severity.ERROR for i in issues):
            return ReadResult(field=None, issues=issues)

        field = self._build_field(s0, s1, issues)

        if field is None:
            return ReadResult(field=None, issues=issues)

        if self.config.validate_weight_laws:
            self._validate_and_apply_weight_laws(field, csf_root, issues)

        if any(i.severity == Severity.ERROR for i in issues):
            return ReadResult(field=None, issues=issues)
       
        return ReadResult(field=field, issues=issues)

    # ------------------------------------------------------------------
    # Phase 0: corruption precheck + YAML parsing
    # ------------------------------------------------------------------

    def _parse_yaml(self, text: str, issues: List[Issue]) -> Optional[Any]:
        """
        Parse YAML with controlled error reporting.

        If corruption precheck finds ERROR(s), stop before calling yaml.safe_load.
        """
        if self.config.precheck_corruption:
            self._precheck_corruption(text, issues)
            if any(i.severity == Severity.ERROR for i in issues):
                return None

        if yaml is None:
            issues.append(
                CSFIssues.make(
                    "CSF_E_YAML_PARSE",
                    path="$",
                    message="PyYAML is not available (cannot parse YAML).",
                    hint="Install PyYAML (pip install pyyaml).",
                )
            )
            return None

        try:
            doc = yaml.safe_load(text)
        except Exception as e:
            issues.append(self._make_yaml_parse_issue(text, e))
            return None

        if not isinstance(doc, dict):
            issues.append(CSFIssues.make("CSF_E_ROOT_TYPE", path="$", context=type(doc).__name__))
            return None

        return doc

    def _make_yaml_parse_issue(self, text: str, exc: Exception) -> Issue:
        """
        Convert a PyYAML parsing exception into a user-friendly Issue.

        The goal is to tell the user:
        - line number
        - column (if available)
        - a small snippet around the problem
        """
        parser_msg = str(exc)

        line_no: Optional[int] = None
        col_no: Optional[int] = None

        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            # PyYAML uses 0-based indexing internally
            line_no = int(getattr(mark, "line", 0)) + 1
            col_no = int(getattr(mark, "column", 0)) + 1
        else:
            m = re.search(r"line\s+(\d+),\s+column\s+(\d+)", parser_msg)
            if m:
                line_no = int(m.group(1))
                col_no = int(m.group(2))

        snippet = self._make_snippet(text, line_no, col_no)

        if line_no is not None and col_no is not None:
            human_loc = f"at line {line_no}, column {col_no}"
        elif line_no is not None:
            human_loc = f"at line {line_no}"
        else:
            human_loc = "at an unknown location"

        ctx: Any = {
            "location": {"line": line_no, "column": col_no},
            "snippet": snippet,
        }
        if self.config.include_yaml_parser_context:
            ctx["parser"] = parser_msg

        return CSFIssues.make(
            "CSF_E_YAML_PARSE",
            path="$",
            message=f"YAML parsing failed {human_loc}. Fix the file at the indicated location.",
            hint="Common causes: missing ':' after a key, wrong indentation, missing '-' in lists.",
            context=ctx,
        )

    @staticmethod
    def _make_snippet(text: str, line_no: Optional[int], col_no: Optional[int]) -> str:
        """
        Create a small snippet of lines around the reported error line.
        """
        lines = text.splitlines()
        if not lines:
            return "<empty input>"

        if line_no is None:
            # No location info: show top of file (still useful)
            head = "\n".join(f"{k+1}: {lines[k]}" for k in range(min(6, len(lines))))
            return head

        lo = max(1, line_no - 2)
        hi = min(len(lines), line_no + 2)

        out: List[str] = []
        for k in range(lo, hi + 1):
            prefix = ">>" if k == line_no else "  "
            out.append(f"{prefix} {k}: {lines[k - 1]}")
            if k == line_no and col_no is not None and col_no > 0:
                caret_pos = len(f"{prefix} {k}: ") + (col_no - 1)
                out.append(" " * caret_pos + "^")

        return "\n".join(out)

    def _precheck_corruption(self, text: str, issues: List[Issue]) -> None:
        """
        Corruption checks on the raw YAML text.

        This is intentionally heuristic: it does NOT try to parse YAML.
        It targets common CSF authoring mistakes that otherwise produce confusing
        YAML parser errors.

        Checks implemented:
        A0) Missing ':' between key and value  (e.g. "z 10.0")
        A1) Missing ':' after a bare key followed by indented children (e.g. "S0" then block)
        C ) Missing polygon header key under polygons: mapping (scans entire block)
        B ) Missing '-' for list items under vertices:
        """
        lines = text.splitlines()
        max_err = max(1, int(self.config.max_precheck_errors))
        err_count = 0

        def _add(issue: Issue) -> None:
            nonlocal err_count
            issues.append(issue)
            if issue.severity == Severity.ERROR:
                err_count += 1

        # --------------------------------------------------------------
        # A) Missing ':' in mapping keys (generic)
        # --------------------------------------------------------------
        for i, raw in enumerate(lines, start=1):
            if err_count >= max_err:
                return

            line = raw.split("#", 1)[0].rstrip("\n")

            if line.strip() == "":
                continue
            if line.lstrip().startswith("-"):
                continue
            if ":" in line:
                continue

            # A0) key + value but missing colon (e.g. "z 10.0")
            m_kv = re.match(r"^\s*([A-Za-z_][\w-]*)\s+(\S.*)\s*$", line)
            if m_kv:
                key = m_kv.group(1)
                value = m_kv.group(2)
                _add(
                    CSFIssues.make(
                        "CSF_E_YAML_MISSING_COLON",
                        path="$",
                        message=f"Missing ':' between key '{key}' and its value.",
                        hint=f"Use '{key}: {value}'",
                        context={"line": i, "key": key, "text": raw.rstrip("\n")},
                    )
                )
                continue

            # A1) bare key token, but has indented children => missing colon
            m_key = re.match(r"^\s*([A-Za-z_][\w-]*)\s*$", line)
            if not m_key:
                continue

            key = m_key.group(1)
            indent = len(line) - len(line.lstrip(" "))

            next_indent: Optional[int] = None
            next_raw: Optional[str] = None
            j = i
            while j < len(lines):
                j += 1
                cand_raw = lines[j - 1]
                cand = cand_raw.split("#", 1)[0].rstrip("\n")
                if cand.strip() == "":
                    continue
                next_indent = len(cand) - len(cand.lstrip(" "))
                next_raw = cand_raw.rstrip("\n")
                break

            if next_indent is not None and next_indent > indent:
                _add(
                    CSFIssues.make(
                        "CSF_E_YAML_MISSING_COLON",
                        path="$",
                        message=f"Missing ':' after key '{key}'.",
                        hint=f"Use '{key}:' (with a colon).",
                        context={"line": i, "key": key, "text": raw.rstrip("\n"), "next_line": j, "next_text": next_raw},
                    )
                )

        # --------------------------------------------------------------
        # C) Missing polygon header key under polygons: mapping
        #    (scan entire polygons block)
        # --------------------------------------------------------------
        polygon_field_keys = {"name", "weight", "vertices"}

        for i, raw in enumerate(lines, start=1):
            if err_count >= max_err:
                return

            base = raw.split("#", 1)[0].rstrip("\n")
            m = re.match(r"^(\s*)polygons\s*:\s*$", base)
            if not m:
                continue

            parent_indent = len(m.group(1))

            # Find first meaningful child line (to decide list vs mapping)
            j = i
            first_child: Optional[str] = None
            first_child_indent: Optional[int] = None
            while j < len(lines):
                j += 1
                cand_raw = lines[j - 1]
                cand = cand_raw.split("#", 1)[0].rstrip("\n")
                if cand.strip() == "":
                    continue

                ind = len(cand) - len(cand.lstrip(" "))
                if ind <= parent_indent:
                    break  # block ended
                first_child = cand
                first_child_indent = ind
                break

            if first_child is None or first_child_indent is None:
                continue

            # If polygons is a list ("- ..."), skip (header is list-based)
            if first_child.lstrip().startswith("-"):
                continue

            polygon_key_indent = first_child_indent

            # Scan the entire block and flag 'weight:'/'vertices:'/'name:' at polygon-key indent
            k = j  # 1-based line index
            while k <= len(lines):
                if err_count >= max_err:
                    return

                raw_k = lines[k - 1]
                line_k = raw_k.split("#", 1)[0].rstrip("\n")

                if line_k.strip() == "":
                    k += 1
                    continue

                indent_k = len(line_k) - len(line_k.lstrip(" "))
                if indent_k <= parent_indent:
                    break  # end polygons block

                if indent_k == polygon_key_indent:
                    mkey = re.match(r"^\s*([A-Za-z_][\w-]*)\s*:\s*", line_k)
                    if mkey:
                        key = mkey.group(1)
                        if key in polygon_field_keys:
                            _add(
                                CSFIssues.make(
                                    "CSF_E_YAML_MISSING_POLYGON_KEY",
                                    path="$",
                                    message=f"Missing polygon key under 'polygons:' before '{key}:'.",
                                    hint="Add a polygon header like 'lowerpart:' before 'weight:'/'vertices:'.",
                                    context={"line": k, "text": raw_k.rstrip("\n")},
                                )
                            )

                k += 1

        # --------------------------------------------------------------
        # B) Missing '-' under vertices:
        # --------------------------------------------------------------
        for i, raw in enumerate(lines, start=1):
            if err_count >= max_err:
                return

            base = raw.split("#", 1)[0].rstrip("\n")
            m = re.match(r"^(\s*)vertices\s*:\s*$", base)
            if not m:
                continue

            parent_indent = len(m.group(1))

            # Look ahead for the first non-empty, more-indented line
            j = i
            while j < len(lines):
                j += 1
                child_raw = lines[j - 1]
                child = child_raw.split("#", 1)[0].rstrip("\n")

                if child.strip() == "":
                    continue

                child_indent = len(child) - len(child.lstrip(" "))
                if child_indent <= parent_indent:
                    break  # vertices block ended

                if not child.lstrip().startswith("-"):
                    _add(
                        CSFIssues.make(
                            "CSF_E_YAML_MISSING_DASH",
                            path="$",
                            message="Under 'vertices:' each vertex must start with '-' (YAML list item).",
                            hint="Example:\n  vertices:\n    - [-0.15, -0.6]\n    - [0.15, -0.6]",
                            context={"line": j, "text": child_raw.rstrip("\n")},
                        )
                    )
                break

    # ------------------------------------------------------------------
    # Formal extraction and parsing
    # ------------------------------------------------------------------

    def _extract_csf_root(self, doc: Dict[str, Any], issues: List[Issue]) -> Optional[Dict[str, Any]]:
        """
        Extract the CSF root mapping.

        Default behavior: require top-level key (self._top_key, usually "CSF").
        """
        if self.config.require_top_key:
            if self._top_key not in doc:
                issues.append(CSFIssues.make("CSF_E_NOT_CSF", path="$", context=list(doc.keys())))
                return None

            root = doc[self._top_key]
            if not isinstance(root, dict):
                issues.append(CSFIssues.make("CSF_E_TOPLEVEL_TYPE", path=self._top_key, context=type(root).__name__))
                return None
            return root

        # Not recommended: treat entire document as csf root
        return doc

    def _extract_sections(self, csf_root: Dict[str, Any], issues: List[Issue]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Validate and return raw section mappings for S0 and S1.
        """
        path = f"{self._top_key}.sections"

        if "sections" not in csf_root:
            issues.append(CSFIssues.make("CSF_E_SECTIONS_MISSING", path=self._top_key))
            return None, None

        sections = csf_root["sections"]
        if not isinstance(sections, dict):
            issues.append(CSFIssues.make("CSF_E_SECTIONS_TYPE", path=path, context=type(sections).__name__))
            return None, None

        if "S0" not in sections or "S1" not in sections:
            issues.append(CSFIssues.make("CSF_E_SECTION_MISSING", path=path, context=list(sections.keys())))
            return None, None

        s0 = sections["S0"]
        s1 = sections["S1"]

        if not isinstance(s0, dict) or not isinstance(s1, dict):
            issues.append(
                CSFIssues.make(
                    "CSF_E_SECTION_TYPE",
                    path=path,
                    context={"S0": type(s0).__name__, "S1": type(s1).__name__},
                )
            )
            return None, None

        return s0, s1

    def _parse_section(self, sec_name: str, sec_data: Dict[str, Any], issues: List[Issue]) -> Optional[Any]:
        """
        Parse a section mapping into a core Section object.
        """
        base_path = f"{self._top_key}.sections.{sec_name}"

        # z
        if "z" not in sec_data:
            issues.append(CSFIssues.make("CSF_E_Z_MISSING", path=base_path))
            return None

        z = sec_data["z"]
        if not self._is_finite_number(z):
            issues.append(CSFIssues.make("CSF_E_Z_TYPE", path=f"{base_path}.z", context=z))
            return None

        # polygons
        if "polygons" not in sec_data:
            issues.append(CSFIssues.make("CSF_E_POLYGONS_MISSING", path=base_path))
            return None

        polys = sec_data["polygons"]

        # Input: polygons may be a dict (mapping) or a list.
        # If dict: coerce to list preserving insertion order and inject name if missing.
        if isinstance(polys, dict) and self.config.allow_polygons_map:
            self._polygons_map_coercions.append({"section": sec_name, "keys": list(polys.keys())})

            poly_list: List[Dict[str, Any]] = []
            for k, v in polys.items():
                if not isinstance(v, dict):
                    issues.append(CSFIssues.make("CSF_E_POLY_TYPE", path=f"{base_path}.polygons.{k}", context=type(v).__name__))
                    return None
                vv = dict(v)
                vv.setdefault("name", str(k))
                poly_list.append(vv)

            polys = poly_list

        if not isinstance(polys, list):
            issues.append(CSFIssues.make("CSF_E_POLYGONS_TYPE", path=f"{base_path}.polygons", context=type(polys).__name__))
            return None

        if len(polys) == 0:
            issues.append(CSFIssues.make("CSF_E_POLYGONS_EMPTY", path=f"{base_path}.polygons"))
            return None

        parsed_polys: List[Any] = []
        seen_names: set[str] = set()

        for i, p in enumerate(polys):
            p_path = f"{base_path}.polygons[{i}]"
            poly = self._parse_polygon(p, p_path, issues)
            if poly is None:
                continue

            if poly.name in seen_names:
                issues.append(CSFIssues.make("CSF_E_POLY_NAME_DUP", path=f"{p_path}.name", context=poly.name))
                continue

            seen_names.add(poly.name)
            parsed_polys.append(poly)

        if any(i.severity == Severity.ERROR for i in issues):
            return None

        from csf.section_field import Section
        return Section(polygons=tuple(parsed_polys), z=float(z))

    def _parse_polygon(self, p: Any, p_path: str, issues: List[Issue]) -> Optional[Any]:
        """
        Parse polygon mapping into Polygon object.
        """
        if not isinstance(p, dict):
            issues.append(CSFIssues.make("CSF_E_POLY_TYPE", path=p_path, context=type(p).__name__))
            return None

        # name
        if "name" not in p:
            issues.append(CSFIssues.make("CSF_E_POLY_NAME_MISSING", path=p_path))
            return None
        name = p["name"]
        if not isinstance(name, str) or name.strip() == "":
            issues.append(CSFIssues.make("CSF_E_POLY_NAME_TYPE", path=f"{p_path}.name", context=name))
            return None
        name = name.strip()

        # weight
        if "weight" not in p:
            issues.append(CSFIssues.make("CSF_E_POLY_WEIGHT_MISSING", path=p_path))
            return None
        w = p["weight"]
        if not self._is_number(w):
            issues.append(CSFIssues.make("CSF_E_POLY_WEIGHT_TYPE", path=f"{p_path}.weight", context=w))
            return None
        if not self._is_finite_number(w):
            issues.append(CSFIssues.make("CSF_E_POLY_WEIGHT_NANINF", path=f"{p_path}.weight", context=w))
            return None

        # vertices
        if "vertices" not in p:
            issues.append(CSFIssues.make("CSF_E_VERTICES_MISSING", path=p_path))
            return None
        verts = p["vertices"]
        if not isinstance(verts, list):
            issues.append(CSFIssues.make("CSF_E_VERTICES_TYPE", path=f"{p_path}.vertices", context=type(verts).__name__))
            return None
        if len(verts) < 3:
            issues.append(CSFIssues.make("CSF_E_VERTICES_COUNT", path=f"{p_path}.vertices", context=len(verts)))
            return None

        parsed_pts: List[Any] = []
        for j, v in enumerate(verts):
            pt = self._parse_vertex(v, f"{p_path}.vertices[{j}]", issues)
            if pt is not None:
                parsed_pts.append(pt)

        if any(i.severity == Severity.ERROR for i in issues):
            return None

        from csf.section_field import Polygon
        return Polygon(vertices=tuple(parsed_pts), weight=float(w), name=name)

    def _parse_vertex(self, v: Any, v_path: str, issues: List[Issue]) -> Optional[Any]:
        """
        Parse one vertex: expected [x, y], both finite numbers.
        """
        if not isinstance(v, (list, tuple)) or len(v) != 2:
            issues.append(CSFIssues.make("CSF_E_VERTEX_FORMAT", path=v_path, context=v))
            return None

        x, y = v[0], v[1]
        if not self._is_number(x) or not self._is_number(y):
            issues.append(CSFIssues.make("CSF_E_VERTEX_TYPE", path=v_path, context=v))
            return None
        if not self._is_finite_number(x) or not self._is_finite_number(y):
            issues.append(CSFIssues.make("CSF_E_VERTEX_NANINF", path=v_path, context=v))
            return None

        from csf.section_field import Pt
        return Pt(float(x), float(y))

    # ------------------------------------------------------------------
    # Cross checks: z-domain + homology
    # ------------------------------------------------------------------

    def _validate_domain_order(self, s0: Any, s1: Any, issues: List[Issue]) -> None:
        """
        Enforce the CSF model rule: field domain is exactly [S0.z, S1.z], and S0.z < S1.z.
        """
        z0 = float(s0.z)
        z1 = float(s1.z)

        if z0 == z1:
            issues.append(CSFIssues.make("CSF_E_Z_EQUAL", path=f"{self._top_key}.sections", context=(z0, z1)))
        elif z0 > z1:
            issues.append(CSFIssues.make("CSF_E_Z_ORDER", path=f"{self._top_key}.sections", context=(z0, z1)))

    def _validate_index_homology(self, s0: Any, s1: Any, issues: List[Issue]) -> None:
        """
        Index-based homology checks:
        - same number of polygons
        - per index i: same number of vertices
        """
        p0 = list(s0.polygons)
        p1 = list(s1.polygons)

        if len(p0) != len(p1):
            issues.append(
                CSFIssues.make(
                    "CSF_E_HOMO_POLY_COUNT",
                    path=f"{self._top_key}.sections",
                    context={"S0": len(p0), "S1": len(p1)},
                )
            )
            return

        for i, (a, b) in enumerate(zip(p0, p1)):
            na = len(a.vertices)
            nb = len(b.vertices)
            if na != nb:
                issues.append(
                    CSFIssues.make(
                        "CSF_E_HOMO_VERT_COUNT",
                        path=f"{self._top_key}.sections.S1.polygons[{i}].vertices",
                        context={
                            "index": i,
                            "S0_name": a.name,
                            "S1_name": b.name,
                            "S0_vertices": na,
                            "S1_vertices": nb,
                        },
                    )
                )

    # ------------------------------------------------------------------
    # Field construction + weight laws
    # ------------------------------------------------------------------

    def _build_field(self, s0: Any, s1: Any, issues: List[Issue]) -> Optional[Any]:
        """
        Instantiate ContinuousSectionField with controlled error reporting.
        """
        try:
            from csf.section_field import ContinuousSectionField
            return ContinuousSectionField(section0=s0, section1=s1)
        except Exception as e:
            issues.append(
                CSFIssues.make(
                    "CSF_E_FIELD_BUILD",
                    path=self._top_key,
                    message="Failed to instantiate ContinuousSectionField.",
                    context=str(e),
                )
            )
            return None

    def _validate_and_apply_weight_laws(self, field: Any, csf_root: Dict[str, Any], issues: List[Issue]) -> None:
        """
        Validate and apply weight_laws.

        Rules:
        - weight_laws must be a list of strings
        - each item: "name0,name1: expr"
        - referenced polygon names must exist in S0 and S1
        - names must refer to polygons with the SAME index in S0 and S1 (index homology)
        """
        if "weight_laws" not in csf_root:
            return  # optional

        wl = csf_root["weight_laws"]
        wl_path = f"{self._top_key}.weight_laws"

        if not isinstance(wl, list):
            issues.append(CSFIssues.make("CSF_E_WLAWS_TYPE", path=wl_path, context=type(wl).__name__))
            return

        laws_out: List[str] = []

        for i, item in enumerate(wl):
            ip = f"{wl_path}[{i}]"

            if not isinstance(item, str):
                issues.append(CSFIssues.make("CSF_E_WLAW_ITEM_TYPE", path=ip, context=type(item).__name__))
                continue

            s = item.strip()
            if ":" not in s:
                issues.append(CSFIssues.make("CSF_E_WLAW_FORMAT", path=ip, context=item))
                continue

            left, expr = s.split(":", 1)
            left = left.strip()
            expr = expr.strip()

            if "," not in left:
                issues.append(CSFIssues.make("CSF_E_WLAW_FORMAT", path=ip, context=item))
                continue
            if expr == "":
                issues.append(CSFIssues.make("CSF_E_WLAW_EXPR_EMPTY", path=ip, context=item))
                continue
            if not self._paren_balance_ok(expr):
                issues.append(CSFIssues.make("CSF_E_WLAW_EXPR_INVALID", path=ip, context=expr))
                continue

            n0, n1 = [t.strip() for t in left.split(",", 1)]
            if n0 == "" or n1 == "":
                issues.append(CSFIssues.make("CSF_E_WLAW_FORMAT", path=ip, context=item))
                continue

            idx0 = self._polygon_index_by_name(field.s0, n0)
            idx1 = self._polygon_index_by_name(field.s1, n1)
            
            if idx0 is None or idx1 is None:
                issues.append(CSFIssues.make("CSF_E_WLAW_REF_MISSING", path=ip, context={"S0_name": n0, "S1_name": n1}))
                continue
            
            if idx0 != idx1:
                issues.append(
                    CSFIssues.make(
                        "CSF_E_WLAW_HOMO_MISMATCH",
                        path=ip,
                        context={"S0_name": n0, "S1_name": n1, "S0_index": idx0, "S1_index": idx1},
                    )
                )
                continue
            
            # Normalize for internal use
            laws_out.append(f"{n0},{n1}: {expr}")

        if any(i.severity == Severity.ERROR for i in issues):

            return
       
        try:
            field.set_weight_laws(laws_out)
           

        except Exception as e:
            issues.append(
                CSFIssues.make(
                    "CSF_E_WLAW_EXPR_INVALID",
                    path=wl_path,
                    message="Failed to apply weight laws (set_weight_laws raised an error).",
                    context=str(e),
                )
            )

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_number(x: Any) -> bool:
        return isinstance(x, (int, float))

    @staticmethod
    def _is_finite_number(x: Any) -> bool:
        if not isinstance(x, (int, float)):
            return False
        return math.isfinite(float(x))

    @staticmethod
    def _paren_balance_ok(expr: str) -> bool:
        """
        Lightweight syntax sanity check (not an evaluator):
        ensures parentheses are balanced.
        """
        n = 0
        for ch in expr:
            if ch == "(":
                n += 1
            elif ch == ")":
                n -= 1
                if n < 0:
                    return False
        return n == 0
    @staticmethod
    def _strip_model_tags(name: str) -> str:
        """
        Normalize polygon name for matching:
        - trim spaces
        - remove everything starting from @cell, @wall, or @closed (case-insensitive)
        """
        s = str(name or "").strip()
        return re.sub(r'(?i)@(cell|wall|closed)\b.*$', '', s).strip()


    @staticmethod
    def _polygon_index_by_name(section: Any, name: str) -> Optional[int]:
    
        for i, p in enumerate(section.polygons):
               
            model_p_name= CSFReader._strip_model_tags(p.name)
            model_name= CSFReader._strip_model_tags(name)


            if model_p_name == model_name:
                return i
        return None
