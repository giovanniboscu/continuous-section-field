import re
import sys
from pathlib import Path


def extract_value(body: str, key: str) -> float:
    m = re.search(
        rf"^\s*{re.escape(key)}\s*:\s*([+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?)",
        body,
        flags=re.MULTILINE,
    )
    if not m:
        raise ValueError(f"Missing value: {key}")
    return float(m.group(1))


def parse_section_selected_analysis(text: str):
    block_re = re.compile(
        r"### SECTION SELECTED ANALYSIS @ z = "
        r"([+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?) ###"
        r"(.*?)(?=### SECTION SELECTED ANALYSIS @ z =|\Z)",
        flags=re.DOTALL,
    )

    rows = []

    for m in block_re.finditer(text):
        z = float(m.group(1))
        body = m.group(2)

        A = extract_value(body, "A")
        Ip = extract_value(body, "Ip")

        rows.append((z, A, Ip))

    return rows


def print_markdown_table(rows):
    print("| z | A | Ip |")
    print("|---:|---:|---:|")

    for z, A, Ip in rows:
        print(f"| {z:.1f} | {A:.8f} | {Ip:.8f} |")


def main():
    if len(sys.argv) != 2:
        print("Usage: python make_table.py section_selected_analysis.txt")
        sys.exit(1)

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")

    rows = parse_section_selected_analysis(text)

    if not rows:
        raise RuntimeError("No SECTION SELECTED ANALYSIS blocks found.")

    print_markdown_table(rows)


if __name__ == "__main__":
    main()
