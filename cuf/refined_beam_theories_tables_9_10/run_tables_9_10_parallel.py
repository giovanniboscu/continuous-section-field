
"""Run the CSF-CUF Carrera-Giunta Table 9 and Table 10 case series.

Usage:
    python3 run_tables_9_10.py 21
    python3 run_tables_9_10.py 21 --parallel 4

The positional argument is a ceiling, not an expected last case.  Each table is
handled independently: if Table 9 exists only through N18 and Table 10 through
N21, requesting 21 runs N01..N18 for Table 9 and N01..N21 for Table 10.

After the runs, the script reads the GLOBAL MAXIMUM DISPLACEMENTS row written
by carrera_post.py for each successful case and writes one combined text report:

    carrera_giunta_tables_9_10.txt

Case discovery is recursive below ./cases and uses the filenames
maclaurin_table9_Nxx.yaml and maclaurin_table10_Nxx.yaml.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent
CASES_ROOT = ROOT / "cases"
REPORT_PATH = ROOT / "carrera_giunta_tables_9_10.txt"


@dataclass(frozen=True)
class CaseEntry:
    table: int
    order: int
    case_path: Path
    result_path: Path


@dataclass(frozen=True)
class ResultRow:
    order: int
    headers: tuple[str, str, str]
    values: tuple[float, float, float]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Maclaurin CSF-CUF series for Carrera-Giunta Tables 9 and 10 "
            "and collect the generated global displacement values."
        )
    )
    parser.add_argument(
        "max_n",
        type=int,
        help=(
            "maximum CUF order to run. This is only a ceiling: each table stops "
            "at its highest case file actually present."
        ),
    )
    parser.add_argument(
        "--parallel",
        type=int,
        metavar="N",
        default=None,
        help=(
            "run up to N csf-cuf cases concurrently. If omitted, cases are run "
            "serially exactly as before."
        ),
    )
    args = parser.parse_args()
    if args.max_n < 1:
        parser.error("max_n must be >= 1")
    if args.parallel is not None and args.parallel < 1:
        parser.error("--parallel must be >= 1")
    return args


def _load_output_path(case_path: Path, table: int) -> Path:
    data = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid YAML mapping: {case_path}")

    output = data.get("output")
    if not isinstance(output, dict) or "directory" not in output:
        raise ValueError(f"missing output.directory in {case_path}")

    output_dir = Path(str(output["directory"]))
    if not output_dir.is_absolute():
        output_dir = case_path.parent / output_dir

    return output_dir.resolve() / f"table{table}_style.txt"


def _discover_table_cases(table: int, max_n: int) -> list[CaseEntry]:
    pattern = re.compile(rf"^maclaurin_table{table}_N(\d+)\.ya?ml$", re.IGNORECASE)
    by_order: dict[int, Path] = {}

    for path in CASES_ROOT.rglob("*.yaml"):
        match = pattern.match(path.name)
        if match is None:
            continue

        order = int(match.group(1))
        if order > max_n:
            continue

        if order in by_order:
            raise RuntimeError(
                f"duplicate Table {table} case for N={order}:\n"
                f"  {by_order[order]}\n"
                f"  {path}"
            )
        by_order[order] = path.resolve()

    entries = []
    for order, case_path in sorted(by_order.items()):
        entries.append(
            CaseEntry(
                table=table,
                order=order,
                case_path=case_path,
                result_path=_load_output_path(case_path, table),
            )
        )
    return entries


def _describe_discovery(table: int, cases: list[CaseEntry], max_n: int) -> None:
    if not cases:
        print(f"Table {table}: no cases found with N <= {max_n}")
        return

    orders = [entry.order for entry in cases]
    rendered = ", ".join(f"N{order:02d}" for order in orders)
    print(f"Table {table}: {rendered}")
    if orders[-1] < max_n:
        print(
            f"  requested ceiling N{max_n:02d}; highest available "
            f"Table {table} case is N{orders[-1]:02d}"
        )


def _print_case_header(entry: CaseEntry, index: int, total: int) -> None:
    print()
    print(
        f"[{index}/{total}] Table {entry.table} N{entry.order:02d}: "
        f"{entry.case_path.relative_to(ROOT)}"
    )
    print("-" * 78)


def _run_case(
    executable: str,
    entry: CaseEntry,
    *,
    capture_output: bool = False,
) -> tuple[bool, str, str | None]:
    run_kwargs = {}
    if capture_output:
        run_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "errors": "replace",
        }

    completed = subprocess.run(
        [executable, str(entry.case_path)],
        cwd=ROOT,
        check=False,
        **run_kwargs,
    )

    output = completed.stdout if capture_output and completed.stdout else ""

    if completed.returncode != 0:
        error = (
            f"ERROR: Table {entry.table} N{entry.order:02d} failed "
            f"with exit code {completed.returncode}"
        )
        return False, output, error

    if not entry.result_path.is_file():
        error = f"ERROR: solver finished but output was not found: {entry.result_path}"
        return False, output, error

    return True, output, None


def _run_cases_serial(
    executable: str,
    all_cases: list[CaseEntry],
) -> tuple[list[CaseEntry], list[CaseEntry]]:
    successful: list[CaseEntry] = []
    failures: list[CaseEntry] = []
    total = len(all_cases)

    for index, entry in enumerate(all_cases, start=1):
        _print_case_header(entry, index, total)
        ok, _, error = _run_case(executable, entry)
        if ok:
            successful.append(entry)
        else:
            failures.append(entry)
            if error is not None:
                print(error, file=sys.stderr)

    return successful, failures


def _run_cases_parallel(
    executable: str,
    all_cases: list[CaseEntry],
    parallelism: int,
) -> tuple[list[CaseEntry], list[CaseEntry]]:
    successful: list[CaseEntry] = []
    failures: list[CaseEntry] = []
    total = len(all_cases)

    print()
    print(f"Running {total} cases with parallelism={parallelism}")

    with ThreadPoolExecutor(max_workers=parallelism) as executor:
        futures = {
            executor.submit(
                _run_case,
                executable,
                entry,
                capture_output=True,
            ): (index, entry)
            for index, entry in enumerate(all_cases, start=1)
        }

        for future in as_completed(futures):
            index, entry = futures[future]
            _print_case_header(entry, index, total)

            try:
                ok, output, error = future.result()
            except Exception as exc:
                ok = False
                output = ""
                error = (
                    f"ERROR: Table {entry.table} N{entry.order:02d} raised "
                    f"an exception: {exc}"
                )

            if output:
                print(output.rstrip())

            if ok:
                successful.append(entry)
            else:
                failures.append(entry)
                if error is not None:
                    print(error, file=sys.stderr)

    return successful, failures


def _read_global_row(entry: CaseEntry) -> ResultRow:
    lines = entry.result_path.read_text(encoding="utf-8").splitlines()

    marker_index = None
    for index, line in enumerate(lines):
        if line.strip() == "GLOBAL MAXIMUM DISPLACEMENTS - PAPER FORMAT":
            marker_index = index
            break

    if marker_index is None:
        raise ValueError(
            f"GLOBAL MAXIMUM DISPLACEMENTS block not found in {entry.result_path}"
        )

    header_line = None
    data_line = None
    for line in lines[marker_index + 1 :]:
        if header_line is None and line.startswith("model"):
            header_line = line
            continue
        if line.startswith("CSF-CUF"):
            data_line = line
            break

    if header_line is None or data_line is None:
        raise ValueError(f"global table header/data row not found in {entry.result_path}")

    # carrera_post.py writes the global row with these fixed field widths:
    # model: 12, value/header 1: 18, value/header 2: 20, value/header 3: 18.
    headers = (
        header_line[12:30].strip(),
        header_line[30:50].strip(),
        header_line[50:].strip(),
    )

    value_tokens = data_line[12:].split()
    if len(value_tokens) != 3:
        raise ValueError(
            f"expected three global displacement values in {entry.result_path}, "
            f"got: {data_line!r}"
        )

    values = tuple(float(value) for value in value_tokens)
    return ResultRow(
        order=entry.order,
        headers=headers,
        values=(values[0], values[1], values[2]),
    )


def _format_table(table: int, rows: list[ResultRow]) -> list[str]:
    lines: list[str] = []
    title = f"TABLE {table} - CSF-CUF"
    lines.append(title)
    lines.append("=" * len(title))

    if not rows:
        lines.append("No successful results available.")
        return lines

    headers = rows[0].headers
    for row in rows[1:]:
        if row.headers != headers:
            raise ValueError(
                f"Table {table} output headers are not identical across N: "
                f"{headers!r} != {row.headers!r}"
            )

    lines.append(
        f"{'N':>6}"
        f"{headers[0]:>18}"
        f"{headers[1]:>20}"
        f"{headers[2]:>18}"
    )
    lines.append("-" * 62)

    for row in rows:
        lines.append(
            f"{row.order:>6d}"
            f"{row.values[0]:>18.6f}"
            f"{row.values[1]:>20.6f}"
            f"{row.values[2]:>18.6f}"
        )

    return lines


def _write_report(
    max_n: int,
    table9_rows: list[ResultRow],
    table10_rows: list[ResultRow],
    failures: list[CaseEntry],
) -> None:
    lines = [
        "CARRERA & GIUNTA 2010 - CSF-CUF VALIDATION",
        "============================================",
        f"Requested maximum order: N{max_n:02d}",
        "Each table uses only the case files that actually exist up to that ceiling.",
        "",
    ]

    lines.extend(_format_table(9, table9_rows))
    lines.append("")
    lines.extend(_format_table(10, table10_rows))

    if failures:
        lines.extend(["", "FAILED CASES", "============"])
        for entry in failures:
            lines.append(f"Table {entry.table} N{entry.order:02d}: {entry.case_path}")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()

    if not CASES_ROOT.is_dir():
        print(f"ERROR: cases directory not found: {CASES_ROOT}", file=sys.stderr)
        return 2

    executable = shutil.which("csf-cuf")
    if executable is None:
        print("ERROR: csf-cuf executable not found in PATH", file=sys.stderr)
        return 2

    try:
        table9_cases = _discover_table_cases(9, args.max_n)
        table10_cases = _discover_table_cases(10, args.max_n)
    except Exception as exc:
        print(f"ERROR during case discovery: {exc}", file=sys.stderr)
        return 2

    if not table9_cases:
        print("ERROR: no Table 9 cases found", file=sys.stderr)
        return 2
    if not table10_cases:
        print("ERROR: no Table 10 cases found", file=sys.stderr)
        return 2

    print(f"Requested maximum order: N{args.max_n:02d}")
    _describe_discovery(9, table9_cases, args.max_n)
    _describe_discovery(10, table10_cases, args.max_n)

    all_cases = table9_cases + table10_cases

    # Reuse cases whose final post-processing file already exists.
    # This avoids rerunning completed CUF analyses while still including
    # their values in the combined Table 9 / Table 10 report.
    reused = [entry for entry in all_cases if entry.result_path.is_file()]
    pending = [entry for entry in all_cases if not entry.result_path.is_file()]

    if reused:
        print()
        print(f"Reusing {len(reused)} completed case(s):")
        for entry in reused:
            print(
                f"  SKIP Table {entry.table} N{entry.order:02d}: "
                f"{entry.result_path.relative_to(ROOT)} already exists"
            )

    if pending:
        if args.parallel is None:
            newly_successful, failures = _run_cases_serial(executable, pending)
        else:
            newly_successful, failures = _run_cases_parallel(
                executable,
                pending,
                args.parallel,
            )
    else:
        print()
        print("All requested cases already have their final output files.")
        newly_successful = []
        failures = []

    successful = reused + newly_successful

    table9_rows: list[ResultRow] = []
    table10_rows: list[ResultRow] = []

    for entry in successful:
        try:
            row = _read_global_row(entry)
        except Exception as exc:
            print(
                f"ERROR reading Table {entry.table} N{entry.order:02d}: {exc}",
                file=sys.stderr,
            )
            failures.append(entry)
            continue

        if entry.table == 9:
            table9_rows.append(row)
        else:
            table10_rows.append(row)

    failed_keys = {(entry.table, entry.order) for entry in failures}
    table9_rows = [row for row in table9_rows if (9, row.order) not in failed_keys]
    table10_rows = [row for row in table10_rows if (10, row.order) not in failed_keys]

    table9_rows.sort(key=lambda row: row.order)
    table10_rows.sort(key=lambda row: row.order)

    try:
        _write_report(args.max_n, table9_rows, table10_rows, failures)
    except Exception as exc:
        print(f"ERROR writing combined report: {exc}", file=sys.stderr)
        return 2

    print()
    print(f"Combined report written: {REPORT_PATH}")
    print(f"Table 9 rows:  {len(table9_rows)}")
    print(f"Table 10 rows: {len(table10_rows)}")

    if failures:
        print(f"Completed with {len(failures)} failed case(s).", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
