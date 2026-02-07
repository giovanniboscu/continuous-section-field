from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True)
class Issue:
    severity: Severity
    code: str
    path: str
    message: str
    hint: Optional[str] = None
    context: Optional[Any] = None


    def to_text(self) -> str:
        """
        Render an Issue to human-readable text.

        Printing rules (user-facing):
        - If the message already starts with "[ERROR]" / "[WARNING]" / "[INFO]", strip it
        to avoid duplicate severity tags.
        - If context is a dict and contains multi-line fields (e.g. "snippet",
        "validator_output", "parser"), print those fields as real multi-line blocks.
        Do NOT print them via repr() because repr escapes newlines ("\\n") and becomes unreadable.
        - Warnings are allowed to omit snippets; errors typically include them upstream.
        """
        header = f"[{self.severity.value}] {self.code} at {self.path}"

        # Avoid duplicated severity tags when upstream text already includes them.
        msg = self.message
        for tag in ("[ERROR]", "[WARNING]", "[INFO]"):
            if isinstance(msg, str) and msg.startswith(tag):
                msg = msg[len(tag):].lstrip()
                break

        lines: List[str] = [header, msg]

        if self.hint:
            lines.append(f"Hint: {self.hint}")

        if self.context is not None:
            ctx = self.context

            # Prefer structured, readable printing for dict contexts.
            if isinstance(ctx, dict):
                # Keys that commonly carry multi-line text we want to print verbatim.
                multiline_keys = ("snippet", "validator_output", "parser", "details")

                # Collect multiline blocks (in a stable order).
                blocks: List[Tuple[str, str]] = []
                for k in multiline_keys:
                    v = ctx.get(k)
                    if isinstance(v, str):
                        # If the string was serialized via repr() earlier, it may contain literal "\\n".
                        # Convert those into real newlines to improve readability.
                        if "\\n" in v and "\n" not in v:
                            v = v.replace("\\n", "\n")
                        blocks.append((k, v))

                # Print remaining context (excluding multiline blocks) on a single line.
                rest = {k: v for k, v in ctx.items() if k not in multiline_keys}
                if rest:
                    lines.append(f"Context: {rest}")

                # Print multiline blocks as proper multi-line sections.
                for k, v in blocks:
                    title = "Snippet" if k == "snippet" else k.replace("_", " ").title()
                    lines.append(f"{title}:")
                    lines.append(v)

            else:
                # Fallback: non-dict contexts
                lines.append(f"Context: {ctx}")

        return "\n".join(lines)



















    def to_text2(self) -> str:
        """
        Render an Issue to human-readable text.

        Printing rules (user-facing):
        - If the message already starts with "[ERROR]" / "[WARNING]" / "[INFO]", strip it
          to avoid duplicate severity tags.
        - If context is a dict and contains multi-line fields (e.g. "snippet",
          "validator_output", "parser"), print those fields as real multi-line blocks.
          Do NOT print them via repr() because repr escapes newlines (
) and becomes unreadable.
        - Warnings are allowed to omit snippets; errors typically include them upstream.
        """
        header = f"[{self.severity.value}] {self.code} at {self.path}"

        # Avoid duplicated severity tags when upstream text already includes them.
        msg = self.message
        for tag in ("[ERROR]", "[WARNING]", "[INFO]"):
            if isinstance(msg, str) and msg.startswith(tag):
                msg = msg[len(tag):].lstrip()
                break

        lines: List[str] = [header, msg]

        if self.hint:
            lines.append(f"Hint: {self.hint}")

        if self.context is not None:
            ctx = self.context

            # Prefer structured, readable printing for dict contexts.
            if isinstance(ctx, dict):
                # Keys that commonly carry multi-line text we want to print verbatim.
                multiline_keys = ("snippet", "validator_output", "parser", "details")

                # Collect multiline blocks (in a stable order).
                blocks: List[tuple[str, str]] = []
                for k in multiline_keys:
                    v = ctx.get(k)
                    if isinstance(v, str):
                        # If the string was serialized via repr() earlier, it may contain literal "".
                        # Convert those into real newlines to improve readability.
                        if "" in v and "" not in v:v = v.replace(", ")
                        blocks.append((k, v))

                # Print remaining context (excluding multiline blocks) on a single line.
                rest = {k: v for k, v in ctx.items() if k not in multiline_keys}
                if rest:
                    lines.append(f"Context: {rest}")

                # Print multiline blocks as proper multi-line sections.
                for k, v in blocks:
                    title = "Snippet" if k == "snippet" else k.replace("_", " ").title()
                    lines.append(f"{title}:")
                    lines.append(v)

            else:
                # Fallback: non-dict contexts
                lines.append(f"Context: {ctx}")

        return "".join(lines)


@dataclass(frozen=True)
class IssueSpec:
    code: str
    severity: Severity
    message: str
    hint: Optional[str] = None


class CSFIssues:
    """
    Central catalog for controlled errors/warnings produced by CSF YAML reading/validation.

    Design goals:
      - Stable codes (testable).
      - English messages.
      - Path-aware issues (precise localization).
      - Easy to extend: add a new IssueSpec in SPECS.
    """

    # Root key expected in CSF YAML (as agreed)
    TOP_KEY = "CSF"

    
    # ---- Error / Warning specs (English) ----
    SPECS: Dict[str, IssueSpec] = {
        "CSF_E_YAML_MISSING_POLYGON_KEY": IssueSpec(
            code="CSF_E_YAML_MISSING_POLYGON_KEY",
            severity=Severity.ERROR,
            message="Missing polygon key under 'polygons:' (polygon header is missing).",
            hint="If 'polygons' is a mapping, add a polygon name key like 'lowerpart:' before 'weight:'/'vertices:'. "
                "If 'polygons' is a list, each polygon must start with '- name: ...'.",
        ),


        "CSF_E_YAML_CORRUPT": IssueSpec(
            code="CSF_E_YAML_CORRUPT",
            severity=Severity.ERROR,
            message="YAML appears corrupted (common CSF syntax issues detected).",
            hint="Fix the reported lines, then retry.",
        ),

        "CSF_E_YAML_MISSING_COLON": IssueSpec(
            code="CSF_E_YAML_MISSING_COLON",
            severity=Severity.ERROR,
            message="Missing ':' after a mapping key.",
            hint="Example: 'weight_laws:' (not 'weight_laws')",
        ),

        "CSF_E_YAML_MISSING_DASH": IssueSpec(
            code="CSF_E_YAML_MISSING_DASH",
            severity=Severity.ERROR,
            message="Missing '-' for a YAML list item.",
            hint="Example: under 'vertices:' each point must start with '- [x, y]'",
        ),




        "CSF_W_POLYGONS_MAP_COERCED": IssueSpec(
            code="CSF_W_POLYGONS_MAP_COERCED",
            severity=Severity.WARNING,
            message="Polygons mapping was coerced to a list preserving insertion order.",
            hint="Prefer a YAML list under 'polygons:' to make order explicit.",
        ),
        # A) Parsing / File
        "CSF_E_IO_READ": IssueSpec(
            code="CSF_E_IO_READ",
            severity=Severity.ERROR,
            message="Unable to read input file.",
            hint="Check the file path and permissions.",
        ),
        "CSF_E_ENCODING": IssueSpec(
            code="CSF_E_ENCODING",
            severity=Severity.ERROR,
            message="Invalid text encoding (UTF-8 expected).",
            hint="Save the file as UTF-8.",
        ),
        "CSF_E_YAML_PARSE": IssueSpec(
            code="CSF_E_YAML_PARSE",
            severity=Severity.ERROR,
            message="YAML parsing failed: the file is not valid YAML.",
            hint="Fix YAML syntax (indentation, ':' separators, list '-' markers).",
        ),
        "CSF_E_ROOT_TYPE": IssueSpec(
            code="CSF_E_ROOT_TYPE",
            severity=Severity.ERROR,
            message="Invalid root type: YAML root must be a mapping (key: value).",
        ),

        # B) Identity / Top-level key
        "CSF_E_NOT_CSF": IssueSpec(
            code="CSF_E_NOT_CSF",
            severity=Severity.ERROR,
            message=f"Not a CSF file: missing top-level key '{TOP_KEY}'.",
            hint=f"The document must start with '{TOP_KEY}:'",
        ),
        "CSF_E_TOPLEVEL_TYPE": IssueSpec(
            code="CSF_E_TOPLEVEL_TYPE",
            severity=Severity.ERROR,
            message=f"Invalid '{TOP_KEY}' type: expected a mapping.",
        ),

        # C) Sections
        "CSF_E_SECTIONS_MISSING": IssueSpec(
            code="CSF_E_SECTIONS_MISSING",
            severity=Severity.ERROR,
            message="Missing required field 'sections'.",
        ),
        "CSF_E_SECTIONS_TYPE": IssueSpec(
            code="CSF_E_SECTIONS_TYPE",
            severity=Severity.ERROR,
            message="Invalid 'sections' type: expected a mapping.",
        ),
        "CSF_E_SECTION_MISSING": IssueSpec(
            code="CSF_E_SECTION_MISSING",
            severity=Severity.ERROR,
            message="Missing required section: S0 and S1 must be present.",
        ),
        "CSF_E_SECTION_TYPE": IssueSpec(
            code="CSF_E_SECTION_TYPE",
            severity=Severity.ERROR,
            message="Invalid section type: S0/S1 must be a mapping.",
        ),
        "CSF_E_Z_MISSING": IssueSpec(
            code="CSF_E_Z_MISSING",
            severity=Severity.ERROR,
            message="Missing required field 'z' in section.",
        ),
        "CSF_E_Z_TYPE": IssueSpec(
            code="CSF_E_Z_TYPE",
            severity=Severity.ERROR,
            message="Invalid 'z' type: expected a finite number.",
        ),
        "CSF_E_Z_EQUAL": IssueSpec(
            code="CSF_E_Z_EQUAL",
            severity=Severity.ERROR,
            message="Invalid domain: S0.z equals S1.z (L=0).",
            hint="S0.z and S1.z must be different.",
        ),
        "CSF_E_Z_ORDER": IssueSpec(
            code="CSF_E_Z_ORDER",
            severity=Severity.ERROR,
            message="Invalid domain order: S0.z must be < S1.z.",
        ),

        # D) Polygons (structure)
        "CSF_E_POLYGONS_MISSING": IssueSpec(
            code="CSF_E_POLYGONS_MISSING",
            severity=Severity.ERROR,
            message="Missing required field 'polygons' in section.",
        ),
        "CSF_E_POLYGONS_TYPE": IssueSpec(
            code="CSF_E_POLYGONS_TYPE",
            severity=Severity.ERROR,
            message="expected a list or a mapping.",
            hint="Use a YAML list or map under 'polygons:' to preserve order.",
        ),
        "CSF_E_POLYGONS_EMPTY": IssueSpec(
            code="CSF_E_POLYGONS_EMPTY",
            severity=Severity.ERROR,
            message="Invalid 'polygons': the list is empty.",
        ),
        "CSF_E_POLY_TYPE": IssueSpec(
            code="CSF_E_POLY_TYPE",
            severity=Severity.ERROR,
            message="Invalid polygon item type: expected a mapping.",
        ),
        "CSF_E_POLY_NAME_MISSING": IssueSpec(
            code="CSF_E_POLY_NAME_MISSING",
            severity=Severity.ERROR,
            message="Missing required polygon field 'name'.",
        ),
        "CSF_E_POLY_NAME_TYPE": IssueSpec(
            code="CSF_E_POLY_NAME_TYPE",
            severity=Severity.ERROR,
            message="Invalid polygon 'name': expected a non-empty string.",
        ),
        "CSF_E_POLY_NAME_DUP": IssueSpec(
            code="CSF_E_POLY_NAME_DUP",
            severity=Severity.ERROR,
            message="Duplicate polygon name within the same section.",
            hint="Polygon names must be unique per section.",
        ),
        "CSF_E_POLY_WEIGHT_MISSING": IssueSpec(
            code="CSF_E_POLY_WEIGHT_MISSING",
            severity=Severity.ERROR,
            message="Missing required polygon field 'weight'.",
        ),
        "CSF_E_POLY_WEIGHT_TYPE": IssueSpec(
            code="CSF_E_POLY_WEIGHT_TYPE",
            severity=Severity.ERROR,
            message="Invalid polygon 'weight': expected a finite number.",
        ),
        "CSF_E_POLY_WEIGHT_NANINF": IssueSpec(
            code="CSF_E_POLY_WEIGHT_NANINF",
            severity=Severity.ERROR,
            message="Invalid polygon 'weight': NaN/Inf is not allowed.",
        ),

        # E) Vertices
        "CSF_E_VERTICES_MISSING": IssueSpec(
            code="CSF_E_VERTICES_MISSING",
            severity=Severity.ERROR,
            message="Missing required field 'vertices' in polygon.",
        ),
        "CSF_E_VERTICES_TYPE": IssueSpec(
            code="CSF_E_VERTICES_TYPE",
            severity=Severity.ERROR,
            message="Invalid 'vertices' type: expected a list.",
        ),
        "CSF_E_VERTICES_COUNT": IssueSpec(
            code="CSF_E_VERTICES_COUNT",
            severity=Severity.ERROR,
            message="Invalid vertices: at least 3 vertices are required.",
        ),
        "CSF_E_VERTEX_FORMAT": IssueSpec(
            code="CSF_E_VERTEX_FORMAT",
            severity=Severity.ERROR,
            message="Invalid vertex format: expected [x, y].",
            hint="Example: - [-0.15, -0.6]",
        ),
        "CSF_E_VERTEX_TYPE": IssueSpec(
            code="CSF_E_VERTEX_TYPE",
            severity=Severity.ERROR,
            message="Invalid vertex coordinates: x and y must be finite numbers.",
        ),
        "CSF_E_VERTEX_NANINF": IssueSpec(
            code="CSF_E_VERTEX_NANINF",
            severity=Severity.ERROR,
            message="Invalid vertex coordinates: NaN/Inf is not allowed.",
        ),

        # F) Homology S0↔S1 (by index)
        "CSF_E_HOMO_POLY_COUNT": IssueSpec(
            code="CSF_E_HOMO_POLY_COUNT",
            severity=Severity.ERROR,
            message="Homology failed: different number of polygons in S0 and S1.",
            hint="S0.polygons and S1.polygons must have the same length (index-based homology).",
        ),
        "CSF_E_HOMO_VERT_COUNT": IssueSpec(
            code="CSF_E_HOMO_VERT_COUNT",
            severity=Severity.ERROR,
            message="Homology failed: corresponding polygons have different vertex counts.",
            hint="For each polygon index i, S0.polygons[i] and S1.polygons[i] must have the same number of vertices.",
        ),

        # G) weight_laws
        "CSF_E_WLAWS_TYPE": IssueSpec(
            code="CSF_E_WLAWS_TYPE",
            severity=Severity.ERROR,
            message="Invalid 'weight_laws' type: expected a list of strings.",
        ),
        "CSF_E_WLAW_ITEM_TYPE": IssueSpec(
            code="CSF_E_WLAW_ITEM_TYPE",
            severity=Severity.ERROR,
            message="Invalid weight_laws item: expected a string.",
        ),
        "CSF_E_WLAW_FORMAT": IssueSpec(
            code="CSF_E_WLAW_FORMAT",
            severity=Severity.ERROR,
            message="Malformed weight law: expected 'name0,name1: expr'.",
        ),
        "CSF_E_WLAW_REF_MISSING": IssueSpec(
            code="CSF_E_WLAW_REF_MISSING",
            severity=Severity.ERROR,
            message="Weight law references a polygon name that does not exist in the corresponding section.",
        ),
        "CSF_E_WLAW_HOMO_MISMATCH": IssueSpec(
            code="CSF_E_WLAW_HOMO_MISMATCH",
            severity=Severity.ERROR,
            message="Weight law references polygons that are not homologous by index.",
        ),
        "CSF_E_WLAW_EXPR_EMPTY": IssueSpec(
            code="CSF_E_WLAW_EXPR_EMPTY",
            severity=Severity.ERROR,
            message="Weight law expression is empty.",
        ),
        "CSF_E_WLAW_EXPR_INVALID": IssueSpec(
            code="CSF_E_WLAW_EXPR_INVALID",
            severity=Severity.ERROR,
            message="Weight law expression is invalid (evaluation failed).",
            hint="Check syntax and allowed symbols (w0,w1,z,L,math,np).",
        ),

        # Warnings (optional now; add more later)
        "CSF_W_UNKNOWN_KEY": IssueSpec(
            code="CSF_W_UNKNOWN_KEY",
            severity=Severity.WARNING,
            message="Unknown key found and ignored.",
        ),
    }

    @classmethod
    def spec(cls, code: str) -> IssueSpec:
        if code not in cls.SPECS:
            # Unknown codes should still be controlled and explicit
            return IssueSpec(
                code=code,
                severity=Severity.ERROR,
                message="Unknown CSF validation code (not registered in CSFIssues.SPECS).",
                hint="Register this code in CSFIssues.SPECS.",
            )
        return cls.SPECS[code]

    @classmethod
    def make(
        cls,
        code: str,
        path: str,
        *,
        message: Optional[str] = None,
        hint: Optional[str] = None,
        context: Optional[Any] = None,
        severity: Optional[Severity] = None,
    ) -> Issue:
        sp = cls.spec(code)
        return Issue(
            severity=severity or sp.severity,
            code=sp.code,
            path=path,
            message=message or sp.message,
            hint=hint if hint is not None else sp.hint,
            context=context,
        )

    @staticmethod
    def summarize(issues: Iterable[Issue]) -> str:
        issues = list(issues)
        n_err = sum(1 for i in issues if i.severity == Severity.ERROR)
        n_wrn = sum(1 for i in issues if i.severity == Severity.WARNING)
        return f"CSF load failed: {n_err} error(s), {n_wrn} warning(s)." if n_err else f"CSF load ok: {n_wrn} warning(s)."

    @staticmethod
    def format_report(issues: Iterable[Issue]) -> str:
        issues = list(issues)
        if not issues:
            return "CSF load ok: 0 warning(s)."
        blocks = [iss.to_text() for iss in issues]
        blocks.append(CSFIssues.summarize(issues))
        return "\n\n".join(blocks)
