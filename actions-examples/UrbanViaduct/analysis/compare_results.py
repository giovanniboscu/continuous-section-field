"""
compare_results.py
==================
Pier50 — Urban Viaduct
Tabular comparison between the results of two section-property libraries:

  - SOURCE A (CSF)  :  result/UrbanViaduc_report.txt
  - SOURCE B (SP)   :  result/sectionproperties_par.txt

For every z station common to both sources, the relative percentage
difference is computed:

    delta_rel [%] = (A - B) / |B| * 100

where A = CSF value, B = sectionproperties value.

Output
------
    result/comparison_report.txt
"""

import re
import math
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE     = Path(__file__).parent.parent   # analysis/ → UrbanViaduct/
RES      = BASE / "result"
FILE_CSF = RES / "UrbanViaduc_report.txt"
FILE_SP  = RES / "sectionproperties_par.txt"
OUT_FILE = RES / "comparison_report.txt"
os.makedirs(RES, exist_ok=True)

# ---------------------------------------------------------------------------
# Property mapping  CSF-column  ←→  sectionproperties-key
# ---------------------------------------------------------------------------
# Each entry:  (label_display, csf_key, sp_key, unit)
PROP_MAP = [
    ("A",         "A",       "area",    "m²"),
    ("Ix",        "Ix",      "e.ixx_c", "m⁴"),
    ("Iy",        "Iy",      "e.iyy_c", "m⁴"),
    ("Ixy",       "Ixy",     "e.ixy_c", "m⁴"),
    ("I1",        "I1",      "e.i11_c", "m⁴"),
    ("I2",        "I2",      "e.i22_c", "m⁴"),
    ("rx",        "rx",      "rx",      "m"),
    ("ry",        "ry",      "ry",      "m"),
    ("Wx",        "Wx",      "e.zxx+",  "m³"),
    ("Wy",        "Wy",      "e.zyy+",  "m³"),
    ("J_sv",      "J_sv",    "e.j",     "m⁴"),
]

LABELS   = [p[0] for p in PROP_MAP]
CSF_KEYS = [p[1] for p in PROP_MAP]
SP_KEYS  = [p[2] for p in PROP_MAP]
UNITS    = [p[3] for p in PROP_MAP]

# ---------------------------------------------------------------------------
# 1.  Parse  UrbanViaduc_report.txt  (CSF)
# ---------------------------------------------------------------------------

def parse_csf(path: Path) -> dict[float, dict]:
    """
    Returns  {z_rounded: {csf_key: float, ...}, ...}
    Columns (0-based after the z column):
      A Cx Cy Ix Iy Ixy Ip I1 I2 rx ry Wx Wy J_sv t_bredt
    """
    header_keys = ["A", "Cx", "Cy", "Ix", "Iy", "Ixy", "Ip",
                   "I1", "I2", "rx", "ry", "Wx", "Wy", "J_sv", "t_bredt"]
    data = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("Pier") or line.startswith("Section") \
               or line.startswith("z") or line.startswith("-"):
                continue
            parts = line.split()
            if len(parts) < len(header_keys) + 1:
                continue
            try:
                z = float(parts[0])
            except ValueError:
                continue
            row = {}
            for i, key in enumerate(header_keys):
                row[key] = float(parts[i + 1])
            z_r = round(z, 4)
            data[z_r] = row
    return data


# ---------------------------------------------------------------------------
# 2.  Parse  sectionproperties_par.txt  (SP)  — UTF-16
# ---------------------------------------------------------------------------

def parse_sp(path: Path) -> dict[float, dict]:
    """
    Returns  {z_rounded: {sp_key: float, ...}, ...}
    """
    with open(path, encoding="utf-16") as fh:
        content = fh.read()

    # Split into per-section blocks
    blocks = re.split(r'\[\d+ / \d+\]', content)[1:]   # skip header

    data = {}
    for block in blocks:
        # Extract z
        m_z = re.search(r'z\s*=\s*([\d.eE+\-]+)', block)
        if not m_z:
            continue
        z = float(m_z.group(1))
        z_r = round(z, 4)

        # Extract property table rows  | key | value |
        props = {}
        for m in re.finditer(r'\|\s*([\w.+\-]+)\s*\|\s*([+-]?[\d.eE+\-]+)\s*\|', block):
            props[m.group(1).strip()] = float(m.group(2))

        data[z_r] = props
    return data


# ---------------------------------------------------------------------------
# 3.  Relative difference  (A - B) / |B| * 100   [%]
# ---------------------------------------------------------------------------

def rel_diff(a: float, b: float) -> float | None:
    """
    Returns % relative difference, or None if |b| is negligibly small
    (centroid coordinates are numerically zero → skip).
    """
    if abs(b) < 1e-10:
        return None
    return (a - b) / abs(b) * 100.0


# ---------------------------------------------------------------------------
# 4.  Main
# ---------------------------------------------------------------------------

def main() -> None:
    csf_data = parse_csf(FILE_CSF)
    sp_data  = parse_sp(FILE_SP)

    # Match z stations with tolerance (handles floating-point rounding
    # between e.g. 5.556 in CSF and 5.5556 in SP)
    TOL = 0.01   # metres
    z_csf_list = sorted(csf_data.keys())
    z_sp_list  = sorted(sp_data.keys())

    # For each CSF z find the nearest SP z within tolerance
    pairs = []   # [(z_csf, z_sp), ...]
    for zc in z_csf_list:
        best = min(z_sp_list, key=lambda zs: abs(zs - zc))
        if abs(best - zc) <= TOL:
            pairs.append((zc, best))

    common = [p[0] for p in pairs]   # ordered by CSF z

    if not common:
        raise RuntimeError("No common z stations found — check file parsing.")

    n_z   = len(common)
    n_p   = len(PROP_MAP)

    # Build delta matrix  [n_z × n_p]  — None if not computable
    delta: list[list[float | None]] = []
    for zc, zs in pairs:
        row_csf = csf_data[zc]
        row_sp  = sp_data[zs]
        row_d   = []
        for csf_k, sp_k in zip(CSF_KEYS, SP_KEYS):
            a = row_csf.get(csf_k)
            b = row_sp.get(sp_k)
            if a is None or b is None:
                row_d.append(None)
            else:
                row_d.append(rel_diff(a, b))
        delta.append(row_d)

    # ------------------------------------------------------------------
    # Statistics per property  (only finite values)
    # ------------------------------------------------------------------
    def stats(vals):
        v = [x for x in vals if x is not None]
        if not v:
            return dict(n=0, mean=None, std=None, absmean=None,
                        absmax=None, absmin=None, p95=None)
        n    = len(v)
        mean = sum(v) / n
        std  = math.sqrt(sum((x - mean) ** 2 for x in v) / n)
        absv = [abs(x) for x in v]
        absv_sorted = sorted(absv)
        absmean = sum(absv) / n
        absmax  = max(absv)
        absmin  = min(absv)
        # 95th percentile
        idx95 = min(int(math.ceil(0.95 * n)) - 1, n - 1)
        p95   = absv_sorted[idx95]
        return dict(n=n, mean=mean, std=std,
                    absmean=absmean, absmax=absmax, absmin=absmin, p95=p95)

    stat_cols = [stats([delta[i][j] for i in range(n_z)]) for j in range(n_p)]

    # ------------------------------------------------------------------
    # Write report
    # ------------------------------------------------------------------
    W_Z  = 8
    W_V  = 12

    # Column widths: label + unit header
    col_headers = [f"{LABELS[j]}\n[{UNITS[j]}]" for j in range(n_p)]

    def fmt(v):
        if v is None:
            return " " * W_V
        return f"{v:+{W_V}.4f}"

    def fmt_stat(v, decimals=4):
        if v is None:
            return " " * W_V
        return f"{v:{W_V}.{decimals}f}"

    sep_outer = "=" * (W_Z + 3 + n_p * (W_V + 3) + 1)
    sep_inner = "-" * (W_Z + 3 + n_p * (W_V + 3) + 1)
    sep_thick = "=" * (W_Z + 3 + n_p * (W_V + 3) + 1)

    def col_header_row(labels, units):
        h1 = f"  {'z [m]':>{W_Z}}  |"
        h2 = f"  {'':>{W_Z}}  |"
        for lbl, unit in zip(labels, units):
            h1 += f"  {lbl:>{W_V}}  |"
            h2 += f"  {('['+unit+']'):>{W_V}}  |"
        return h1, h2

    with open(OUT_FILE, "w", encoding="utf-8") as out:
        def p(s=""):
            out.write(s + "\n")

        # ── Title ─────────────────────────────────────────────────────
        p(sep_outer)
        p("  PIER 50 — Urban Viaduct  |  Section Property Comparison")
        p("  SOURCE A : CSF     (UrbanViaduc_report.txt)")
        p("  SOURCE B : SP      (sectionproperties_par.txt)")
        p()
        p("  delta_rel [%] = (A − B) / |B| × 100")
        p("  Positive → CSF overestimates  |  Negative → CSF underestimates")
        p(sep_outer)
        p()

        # ── Table ─────────────────────────────────────────────────────
        p("  RELATIVE DIFFERENCE TABLE  [%]")
        p()

        h1, h2 = col_header_row(LABELS, UNITS)
        p(h1)
        p(h2)
        p(sep_inner)

        for i, (zc, zs) in enumerate(pairs):
            row_str = f"  {zc:{W_Z}.4f}  |"
            for j in range(n_p):
                row_str += f"  {fmt(delta[i][j])}  |"
            p(row_str)

        p(sep_thick)
        p()

        # ── Statistics ────────────────────────────────────────────────
        p("  GLOBAL STATISTICAL REPORT")
        p()
        p(f"  {'Stations compared':30s}: {n_z}")
        p(f"  {'Properties compared':30s}: {n_p}")
        p()

        stat_rows = [
            ("Mean  Δ [%]",        "mean"),
            ("StdDev  Δ [%]",      "std"),
            ("Mean |Δ| [%]",       "absmean"),
            ("Min  |Δ| [%]",       "absmin"),
            ("Max  |Δ| [%]",       "absmax"),
            ("95th pct |Δ| [%]",   "p95"),
        ]

        W_STAT = 22
        header_stat = f"  {'':>{W_STAT}}  |"
        for lbl in LABELS:
            header_stat += f"  {lbl:>{W_V}}  |"
        p(header_stat)
        p(sep_inner)

        for stat_label, stat_key in stat_rows:
            row_str = f"  {stat_label:>{W_STAT}}  |"
            for j in range(n_p):
                v = stat_cols[j][stat_key]
                row_str += f"  {fmt_stat(v)}  |"
            p(row_str)

        p(sep_thick)
        p()

        # ── Narrative summary ─────────────────────────────────────────
        p("  NARRATIVE SUMMARY")
        p()
        p("  The following properties are compared between CSF and sectionproperties.")
        p("  Values near 0% indicate excellent agreement between the two libraries.")
        p()

        for j in range(n_p):
            st = stat_cols[j]
            if st["n"] == 0:
                continue
            absmax = st["absmax"]
            absmean = st["absmean"]
            flag = "✓ EXCELLENT" if absmax < 0.1  else \
                   "✓ GOOD"      if absmax < 1.0  else \
                   "✓ ACCEPTABLE" if absmax < 2.0  else \
                   "~ FAIR"      if absmax < 5.0  else \
                   "! REVIEW"
            p(f"  {LABELS[j]:6s} [{UNITS[j]:3s}]  "
              f"max|Δ|={absmax:8.4f}%   mean|Δ|={absmean:8.4f}%   {flag}")

        p()
        p("  Thresholds:  < 0.1% → EXCELLENT  |  < 1.0% → GOOD  |  "
          "< 2.0% → ACCEPTABLE  |  < 5.0% → FAIR  |  ≥ 5.0% → REVIEW")
        p()
        p(sep_outer)

    print(f"Report written to: {OUT_FILE}")


if __name__ == "__main__":
    main()
