#!/usr/bin/env python3
"""
Generate Markdown API documentation for one or more explicit Python files.

Examples from repository root:

    python tools/generate_api_doc.py src/csf/section_field.py
    python tools/generate_api_doc.py src/csf/CSFActions.py src/csf/continuous_section_field.py
    python tools/generate_api_doc.py CSFActions.py continuous_section_field.py src/csf/utils/csf_sp.py
    python tools/generate_api_doc.py --all

Default output directory:

    src/doc/

Output filename examples:

    src/csf/section_field.py              -> src/doc/section_field_api_en.md
    src/csf/continuous_section_field.py   -> src/doc/continuous_section_field_api_en.md
    src/csf/utils/csf_sp.py               -> src/doc/utils_csf_sp_api_en.md
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = REPO_ROOT / "src" / "csf"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "src" / "doc"


def annotation_to_str(node: ast.AST | None) -> str:
    if node is None:
        return "not annotated"
    try:
        return ast.unparse(node)
    except Exception:
        return "not annotated"


def default_to_str(node: ast.AST | None) -> str:
    if node is None:
        return "-"
    try:
        return ast.unparse(node)
    except Exception:
        return "..."


def signature_to_str(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def" if isinstance(fn, ast.AsyncFunctionDef) else "def"
    try:
        return f"{prefix} {fn.name}{ast.unparse(fn.args)}"
    except Exception:
        return f"{prefix} {fn.name}(...)"


def class_signature_to_str(cls: ast.ClassDef) -> str:
    bases: list[str] = []
    for base in cls.bases:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            bases.append("...")
    if bases:
        return f"class {cls.name}({', '.join(bases)})"
    return f"class {cls.name}"


def clean_docstring(node: ast.AST) -> str:
    doc = ast.get_docstring(node)
    return "" if not doc else doc.strip()


def summary_from_docstring(node: ast.AST) -> str:
    doc = clean_docstring(node)
    if not doc:
        return "Docstring absent."
    for line in doc.splitlines():
        line = line.strip()
        if line:
            return line
    return "Docstring absent."


def docstring_body(node: ast.AST) -> str:
    doc = clean_docstring(node)
    if not doc:
        return ""

    lines = doc.splitlines()
    first_nonempty_idx: int | None = None

    for i, line in enumerate(lines):
        if line.strip():
            first_nonempty_idx = i
            break

    if first_nonempty_idx is None:
        return ""

    rest = lines[first_nonempty_idx + 1 :]
    while rest and not rest[0].strip():
        rest.pop(0)

    return "\n".join(rest).strip()


def decorators_to_str(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
    out: list[str] = []
    for dec in node.decorator_list:
        try:
            out.append(ast.unparse(dec))
        except Exception:
            out.append("...")
    return out


def parameters(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[tuple[str, str, str, str]]:
    args = fn.args
    rows: list[tuple[str, str, str, str]] = []

    positional_only = list(args.posonlyargs)
    normal_args = list(args.args)
    positional = positional_only + normal_args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)

    for i, (arg, default) in enumerate(zip(positional, defaults)):
        kind = "positional-only" if i < len(positional_only) else "positional or keyword"
        rows.append((arg.arg, kind, annotation_to_str(arg.annotation), default_to_str(default)))

    if args.vararg is not None:
        rows.append((f"*{args.vararg.arg}", "var positional", annotation_to_str(args.vararg.annotation), "-"))

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        rows.append((arg.arg, "keyword-only", annotation_to_str(arg.annotation), default_to_str(default)))

    if args.kwarg is not None:
        rows.append((f"**{args.kwarg.arg}", "var keyword", annotation_to_str(args.kwarg.annotation), "-"))

    return rows


def exception_name(node: ast.AST | None) -> str:
    if node is None:
        return "raise"
    if isinstance(node, ast.Call):
        return exception_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = exception_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    try:
        return ast.unparse(node)
    except Exception:
        return "raise"


def raised_exceptions(node: ast.AST) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    for child in ast.walk(node):
        if isinstance(child, ast.Raise):
            name = exception_name(child.exc)
            if name not in seen:
                seen.add(name)
                found.append(name)

    return found


def literal_string_keys(node: ast.AST) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()

    for child in ast.walk(node):
        if isinstance(child, ast.Dict):
            for key in child.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    if key.value not in seen:
                        seen.add(key.value)
                        keys.append(key.value)

    return keys


def visible_calls(node: ast.AST) -> list[str]:
    calls: list[str] = []
    seen: set[str] = set()

    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue

        name = ""
        if isinstance(child.func, ast.Name):
            name = child.func.id
        elif isinstance(child.func, ast.Attribute):
            parts: list[str] = []
            cur: ast.AST = child.func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            name = ".".join(reversed(parts))

        if name and name not in seen:
            seen.add(name)
            calls.append(name)

    return calls


def function_block(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    level: int = 3,
    display_name: str | None = None,
    include_calls: bool = True,
) -> str:
    h = "#" * level
    end_lineno = getattr(fn, "end_lineno", fn.lineno)
    title = display_name or fn.name
    lines: list[str] = []

    lines.append(f"{h} `{title}`")
    lines.append("")
    lines.append(f"**Source lines:** `{fn.lineno}-{end_lineno}`")
    lines.append("")

    decorators = decorators_to_str(fn)
    if decorators:
        lines.append("**Decorators**")
        lines.append("")
        for dec in decorators:
            lines.append(f"- `{dec}`")
        lines.append("")

    lines.append("```python")
    lines.append(signature_to_str(fn))
    lines.append("```")
    lines.append("")
    lines.append(f"**Summary:** {summary_from_docstring(fn)}")
    lines.append("")

    body = docstring_body(fn)
    if body:
        lines.append("**Docstring details**")
        lines.append("")
        lines.append("```text")
        lines.append(body)
        lines.append("```")
        lines.append("")

    rows = parameters(fn)
    if rows:
        lines.append("**Parameters**")
        lines.append("")
        lines.append("| Name | Kind | Type | Default |")
        lines.append("|---|---|---|---|")
        for name, kind, typ, default in rows:
            lines.append(f"| `{name}` | `{kind}` | `{typ}` | `{default}` |")
        lines.append("")

    lines.append(f"**Returns:** `{annotation_to_str(fn.returns)}`")
    lines.append("")

    keys = literal_string_keys(fn)
    if keys:
        lines.append("**Returned dictionary keys visible in the code**")
        lines.append("")
        lines.append("`" + "`, `".join(keys) + "`")
        lines.append("")

    raises = raised_exceptions(fn)
    if raises:
        lines.append("**Raises visible in the code**")
        lines.append("")
        for exc in raises:
            lines.append(f"- `{exc}`")
        lines.append("")

    if include_calls:
        calls = visible_calls(fn)
        if calls:
            lines.append("**Function/method calls visible in the code**")
            lines.append("")
            shown = calls[:80]
            lines.append("`" + "`, `".join(shown) + "`")
            if len(calls) > len(shown):
                lines.append("")
                lines.append(f"Additional calls omitted: `{len(calls) - len(shown)}`.")
            lines.append("")

    return "\n".join(lines)


def class_block(cls: ast.ClassDef, *, include_private_methods: bool, include_calls: bool) -> str:
    end_lineno = getattr(cls, "end_lineno", cls.lineno)
    lines: list[str] = []

    lines.append(f"### `{cls.name}`")
    lines.append("")
    lines.append(f"**Source lines:** `{cls.lineno}-{end_lineno}`")
    lines.append("")

    decorators = decorators_to_str(cls)
    if decorators:
        lines.append("**Decorators**")
        lines.append("")
        for dec in decorators:
            lines.append(f"- `{dec}`")
        lines.append("")

    lines.append("```python")
    lines.append(class_signature_to_str(cls))
    lines.append("```")
    lines.append("")
    lines.append(f"**Summary:** {summary_from_docstring(cls)}")
    lines.append("")

    body = docstring_body(cls)
    if body:
        lines.append("**Docstring details**")
        lines.append("")
        lines.append("```text")
        lines.append(body)
        lines.append("```")
        lines.append("")

    methods = [
        node for node in cls.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (include_private_methods or not node.name.startswith("_"))
    ]

    if methods:
        lines.append("**Methods visible in the code**")
        lines.append("")
        for method in methods:
            lines.append(f"- `{method.name}` - line {method.lineno}")
        lines.append("")
        lines.append("#### Method details")
        lines.append("")
        for method in methods:
            lines.append(
                function_block(
                    method,
                    level=5,
                    display_name=f"{cls.name}.{method.name}",
                    include_calls=include_calls,
                )
            )

    return "\n".join(lines)


def section_title_for_line(source_lines: list[str], lineno: int) -> str:
    start = max(0, lineno - 45)
    candidates: list[str] = []

    for line in source_lines[start : lineno - 1]:
        s = line.strip()
        if not s.startswith("#"):
            continue
        text = s.lstrip("#").strip(" -=")
        if text and len(text) <= 90:
            candidates.append(text)

    return candidates[-1] if candidates else "Top-level functions"


def output_filename_for(source_file: Path, source_root: Path) -> str:
    try:
        rel = source_file.relative_to(source_root)
        stem = "_".join(rel.with_suffix("").parts)
    except ValueError:
        stem = source_file.stem
    return f"{stem}_api_en.md"


def resolve_source(raw: str, source_root: Path) -> Path:
    p = Path(raw)

    candidates: list[Path] = []

    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.append(REPO_ROOT / p)
        candidates.append(source_root / p)

        if len(p.parts) == 1:
            matches = sorted(source_root.rglob(p.name))
            candidates.extend(matches)

    existing = []
    seen: set[Path] = set()
    for c in candidates:
        try:
            cc = c.resolve()
        except Exception:
            cc = c
        if cc in seen:
            continue
        seen.add(cc)
        if cc.exists() and cc.is_file():
            existing.append(cc)

    if not existing:
        raise FileNotFoundError(f"Cannot resolve source path: {raw}")

    if len(existing) > 1:
        joined = "\n".join(f"  - {x}" for x in existing)
        raise RuntimeError(f"Ambiguous source path: {raw}\n{joined}")

    return existing[0]


def build_markdown(
    source_file: Path,
    *,
    source_root: Path,
    output_file: Path,
    include_private: bool,
    include_private_methods: bool,
    include_calls: bool,
) -> str:
    source_text = source_file.read_text(encoding="utf-8")
    source_lines = source_text.splitlines()
    module = ast.parse(source_text)

    module_doc = ast.get_docstring(module) or ""

    functions = [
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (include_private or not node.name.startswith("_"))
    ]
    classes = [
        node for node in module.body
        if isinstance(node, ast.ClassDef)
        and (include_private or not node.name.startswith("_"))
    ]

    duplicates: dict[str, list[int]] = {}
    seen: dict[str, list[int]] = {}
    for fn in functions:
        seen.setdefault(fn.name, []).append(fn.lineno)
    duplicates = {name: lines for name, lines in seen.items() if len(lines) > 1}

    rel_source = source_file.relative_to(REPO_ROOT) if source_file.is_relative_to(REPO_ROOT) else source_file
    rel_output = output_file.relative_to(REPO_ROOT) if output_file.is_relative_to(REPO_ROOT) else output_file

    out: list[str] = []
    out.append(f"# API Reference - `{source_file.name}`")
    out.append("")
    out.append(f"This document covers the top-level classes and functions defined in `{rel_source}`. Imported symbols are not documented as standalone APIs here.")
    out.append("")
    out.append("## Module summary")
    out.append("")
    out.append(f"- Source file: `{rel_source}`")
    out.append(f"- Output file: `{rel_output}`")
    out.append(f"- Top-level function definitions found: `{len(functions)}`.")
    out.append(f"- Top-level classes found: `{len(classes)}`.")
    if duplicates:
        out.append("- Duplicate function names found:")
        for name, lines in duplicates.items():
            joined = ", ".join(str(x) for x in lines)
            out.append(f"  - `{name}` at lines {joined}. The later definition is the active binding at import time.")
    else:
        out.append("- Duplicate function names found: `0`.")
    out.append("")

    if module_doc:
        out.append("## Module docstring")
        out.append("")
        out.append("```text")
        out.append(module_doc.strip())
        out.append("```")
        out.append("")

    out.append("## Public API index")
    out.append("")

    for cls in classes:
        out.append(f"- `{cls.name}` - line {cls.lineno}")

    for fn in functions:
        out.append(f"- `{signature_to_str(fn)}` - line {fn.lineno}")

    out.append("")
    out.append("## API details")
    out.append("")

    if classes:
        out.append("## Classes")
        out.append("")
        for cls in classes:
            out.append(
                class_block(
                    cls,
                    include_private_methods=include_private_methods,
                    include_calls=include_calls,
                )
            )

    if functions:
        grouped: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
        for fn in functions:
            title = section_title_for_line(source_lines, fn.lineno)
            grouped.setdefault(title, []).append(fn)

        out.append("## Functions")
        out.append("")
        for title, fns in grouped.items():
            out.append(f"## {title}")
            out.append("")
            for fn in fns:
                out.append(function_block(fn, include_calls=include_calls))

    out.append("# Notes from the source structure")
    out.append("")
    out.append("- The generator reads the Python source through `ast` and does not import the package.")
    out.append("- `Source lines` are derived from Python AST line numbers.")
    out.append("- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.")
    out.append("- `Raises visible in the code` lists exception names from explicit `raise` statements.")
    out.append("- `Function/method calls visible in the code` is a static list of call expressions found in the function body.")
    out.append("")

    return "\n".join(out)


def generate_one(
    source_file: Path,
    *,
    source_root: Path,
    output_dir: Path,
    include_private: bool,
    include_private_methods: bool,
    include_calls: bool,
) -> Path:
    output_file = output_dir / output_filename_for(source_file, source_root)
    markdown = build_markdown(
        source_file,
        source_root=source_root,
        output_file=output_file,
        include_private=include_private,
        include_private_methods=include_private_methods,
        include_calls=include_calls,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown, encoding="utf-8")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Markdown API documentation for explicit Python source files."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Python source paths. Bare filenames are resolved recursively under src/csf.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate docs for every .py file under src/csf.",
    )
    parser.add_argument(
        "--source-root",
        default=str(DEFAULT_SOURCE_ROOT),
        help="Source root used for bare-name resolution and output filename mapping.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory. Default: src/doc.",
    )
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Exclude names starting with underscore.",
    )
    parser.add_argument(
        "--no-calls",
        action="store_true",
        help="Do not include static function/method call lists.",
    )

    args = parser.parse_args()

    source_root = Path(args.source_root)
    if not source_root.is_absolute():
        source_root = REPO_ROOT / source_root
    source_root = source_root.resolve()

    output_dir = Path(args.out_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir = output_dir.resolve()

    if args.all:
        sources = sorted(
            p.resolve()
            for p in source_root.rglob("*.py")
            if "__pycache__" not in p.parts
        )
    else:
        if not args.paths:
            parser.error("Provide at least one .py path, or use --all.")
        sources = [resolve_source(raw, source_root) for raw in args.paths]

    include_private = not args.public_only
    include_private_methods = not args.public_only
    include_calls = not args.no_calls

    written: list[Path] = []

    for source in sources:
        written.append(
            generate_one(
                source,
                source_root=source_root,
                output_dir=output_dir,
                include_private=include_private,
                include_private_methods=include_private_methods,
                include_calls=include_calls,
            )
        )

    print("Generated API documentation:")
    for path in written:
        try:
            display = path.relative_to(REPO_ROOT)
        except ValueError:
            display = path
        print(f"  - {display}")


if __name__ == "__main__":
    main()
