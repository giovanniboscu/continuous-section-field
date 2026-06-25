# DRAFT
# Refani–Nagao spun pile as a literature-based CSF input case

## 1. Scope of this document

This document describes a CSF procedure based on data taken from the Refani–Nagao spun-pile corrosion study.

The paper is used as a **source of input data**.

It is not used here as a direct numerical benchmark for CSF section properties, because the paper does not provide CSF-type section-property outputs such as `A_eq`, `Ix_eq`, `Iy_eq`, or `J_sv_cell` for a full member.

The chain used here is:

```text
paper data
→ CSF material-weight mapping
→ CSF lookup files
→ CSF equivalent section properties
```

The paper contributes the physical starting point:

```text
geometry
initial material quantities
corrosion degree
material degradation factors
```

CSF contributes the sectional transformation:

```text
polygonal section model
per-polygon material weights
weighted/equivalent section properties
```

## 2. What is, and is not, compared

The comparison is not:

```text
CSF section property = paper section property
```

because the paper does not provide those section properties.

The meaningful checks are:

```text
paper geometry/material data
→ correctly transferred into the CSF model

paper-derived degradation factors
→ correctly transferred into CSF lookup weights

CSF lookup weights
→ produce consistent equivalent section properties
```

Therefore, the role of the paper is upstream. It defines the input state. CSF then propagates that state to section-level quantities.

## 3. Source paper

Reference:

Refani, A. N.; Nagao, T. *Corrosion Effects on the Mechanical Properties of Spun Pile Materials*. Applied Sciences 2023, 13, 1507. DOI: 10.3390/app13031507.

The relevant information used from the paper is restricted to:

1. the spun-pile geometry;
2. the initial material quantities;
3. the corrosion degree at the selected exposure periods;
4. the degradation of cover concrete, core concrete, and PC-bars.

The local 3D nonlinear finite-element analysis performed in the paper is not reproduced here.

## 4. Primary paper data used as CSF input

### 4.1 Geometry

| quantity | paper value | CSF value used |
|---|---:|---:|
| outer diameter | 600 mm | 0.600 m |
| outer radius | 300 mm | 0.300 m |
| wall thickness | 100 mm | 0.100 m |
| inner radius | 200 mm | 0.200 m |
| cover concrete thickness | 50 mm | boundary at approximately R = 0.250 m |
| number of PC-bars | 32 | 32 PC-bar polygons |
| PC-bar diameter | 9 mm | 0.009 m |
| transverse helical rebar diameter | 4 mm | not represented as a longitudinal CSF polygon |
| transverse helical rebar spacing | 120 mm | not represented as a longitudinal CSF polygon |

The transverse helical reinforcement is part of the paper's local material-degradation analysis. In the current CSF elastic section-property mapping, the explicit longitudinal reinforcement is represented by the 32 PC-bars.

### 4.2 Initial material quantities

| quantity | paper value | CSF use |
|---|---:|---|
| cover concrete strength, fc | 52 MPa | used to derive cover equivalent weight |
| cover concrete peak strain, εc | 0.00275 | used to derive cover equivalent weight |
| core concrete strength, fcc | 52 MPa | used to derive core equivalent weight |
| core concrete peak strain, εcc | 0.00323 | used to derive core equivalent weight |
| PC-bar modulus, Es | 196500 MPa | used as undegraded PC-bar weight |

The undegraded equivalent weights used by the CSF mapping are:

```text
E_cover,0 = 52 / 0.00275 = 18909.091 MPa
E_core,0  = 52 / 0.00323 = 16099.071 MPa
E_bar,0   = 196500.000 MPa
```

The concrete values above are not claimed to be the initial elastic modulus from the paper. They are equivalent secant-type weights used in this CSF elastic mapping.

## 5. CSF section model

The CSF geometry is represented by concentric polygonal regions and discrete PC-bar polygons.

The participating polygon families are:

```text
core_inner
pcbar_host_layer
cover_inner
cover_outer
pcbar_00 ... pcbar_31
```

The central void is present geometrically but is not assigned a participating degradation lookup.

The material-family assignment is:

| CSF polygon family | material family used for the lookup |
|---|---|
| core_inner | core concrete |
| pcbar_host_layer | core concrete |
| cover_inner | cover concrete |
| cover_outer | cover concrete |
| pcbar_00 ... pcbar_31 | PC-bars |

This assignment is the bridge between the paper-derived degradation data and the CSF polygonal model.

## 6. Degradation mapping

### 6.1 Corrosion degree

The 75-year corrosion degree used in the case is:

```text
ψ75 = 0.1856
```

The four scenarios use a linear interpolation of corrosion degree with time:

```text
ψ(y) = ψ75 * y / 75
```

This gives:

| scenario | year | ψ |
|---:|---:|---:|
| 000y | 0 | 0.0000 |
| 025y | 25 | 0.0619 |
| 050y | 50 | 0.1237 |
| 075y | 75 | 0.1856 |

### 6.2 Cover concrete

The paper provides degradation of cover-concrete compressive strength.

In this CSF case, that degradation factor is used as a modelling input to reduce the cover-concrete equivalent section weight.

The generator uses:

```text
r_cover(ψ) = 0.25 * atan((0.149 - ψ) / 0.025) + 0.65
```

with `r_cover(0) = 1.0`.

The lookup weight for cover polygons is:

```text
w_cover(ψ) = E_cover,0 * r_cover(ψ)
```

### 6.3 Core concrete

The paper provides degradation of core-concrete compressive strength.

In this CSF case, that degradation factor is used as a modelling input to reduce the core-concrete equivalent section weight.

The generator uses:

```text
r_core(ψ) = 0.14 * atan((0.170 - ψ) / 0.100) + 0.848
```

with `r_core(0) = 1.0`.

The lookup weight for core polygons is:

```text
w_core(ψ) = E_core,0 * r_core(ψ)
```

### 6.4 PC-bars

For PC-bars, corrosion degree is treated as an area-loss factor.

Because the CSF PC-bar polygons remain geometrically fixed, the area loss is represented by an equivalent material weight:

```text
w_bar(ψ) = Es * (1 - ψ)
```

This is an equivalent fixed-geometry representation of area loss. It is not a statement that the steel elastic modulus physically degrades by the same amount.

## 7. Uniform scenario check

The uniform scenario check sets:

```text
g(z/L) = 1
```

for all participating polygons.

This means that the full degradation associated with each period is applied everywhere along the member.

The purpose of the uniform case is to isolate the material/period mapping from any axial distribution effect.

In the uniform case, each scenario must produce constant properties at all selected `z` stations.

## 8. Directory structure

A compact directory structure for this case is:

```text
spun_pile_refani/
├── create_yaml_spun_pile_refani.py
├── writegeometry_onion_rebars.py
├── attach_polygon_axial_degradation.py
├── generate_period_lookup_files_v2.py
├── spun_pile_refani_onion.yaml
├── spun_pile_refani_onion_lookup.yaml
├── degradation_lookups_uniform/
│   ├── degradation_000y/
│   │   ├── spun_pile_refani_onion_lookup.yaml -> ../../spun_pile_refani_onion_lookup.yaml
│   │   ├── axial_degradation_core_inner.txt
│   │   ├── axial_degradation_pcbar_host_layer.txt
│   │   ├── axial_degradation_cover_inner.txt
│   │   ├── axial_degradation_cover_outer.txt
│   │   ├── axial_degradation_pcbar_00.txt
│   │   ├── ...
│   │   └── axial_degradation_pcbar_31.txt
│   ├── degradation_025y/
│   │   ├── spun_pile_refani_onion_lookup.yaml -> ../../spun_pile_refani_onion_lookup.yaml
│   │   └── axial_degradation_*.txt
│   ├── degradation_050y/
│   │   ├── spun_pile_refani_onion_lookup.yaml -> ../../spun_pile_refani_onion_lookup.yaml
│   │   └── axial_degradation_*.txt
│   └── degradation_075y/
│       ├── spun_pile_refani_onion_lookup.yaml -> ../../spun_pile_refani_onion_lookup.yaml
│       └── axial_degradation_*.txt
└── results_uniform/
    ├── spun_pile_refani_section_properties_000.txt
    ├── spun_pile_refani_section_properties_025.txt
    ├── spun_pile_refani_section_properties_050.txt
    └── spun_pile_refani_section_properties_075.txt
```

The YAML geometry/lookup model is unique. The scenario is selected by the directory from which the calculation is run.

## 9. Python scripts used

### 9.1 `attach_polygon_axial_degradation.py`

This script attaches one `T_lookup(...)` law to each participating polygon.

Typical command:

```bash
python attach_polygon_axial_degradation.py \
    spun_pile_refani_onion.yaml \
    spun_pile_refani_onion_lookup.yaml \
    axial_degradation.txt
```

The third argument is only used as a filename base. The generated YAML points to per-polygon files:

```text
axial_degradation_core_inner.txt
axial_degradation_pcbar_host_layer.txt
axial_degradation_cover_inner.txt
axial_degradation_cover_outer.txt
axial_degradation_pcbar_00.txt
...
axial_degradation_pcbar_31.txt
```

### 9.2 `generate_period_lookup_files_v2.py`

This script creates the four period directories and the corresponding lookup files.

Uniform generation command:

```bash
python generate_period_lookup_files_v2.py \
    spun_pile_refani_onion_lookup.yaml \
    degradation_lookups_uniform \
    --uniform
```

The option `--uniform` makes each lookup file constant along `t_norm`, corresponding to:

```text
g(z/L) = 1
```

The generated lookup files have this structure:

```text
# t_norm  absolute_weight
# t_norm is the normalized axial coordinate z/L.
# absolute_weight is read directly by T_lookup().
0.00000000  <absolute_weight>
0.01000000  <absolute_weight>
...
1.00000000  <absolute_weight>
```

## 10. Execution procedure

### Step 1: generate or provide the CSF geometry YAML

Expected file:

```text
spun_pile_refani_onion.yaml
```

### Step 2: attach lookup-based weight laws

Run:

```bash
python attach_polygon_axial_degradation.py \
    spun_pile_refani_onion.yaml \
    spun_pile_refani_onion_lookup.yaml \
    axial_degradation.txt
```

Expected file:

```text
spun_pile_refani_onion_lookup.yaml
```

### Step 3: generate uniform period lookup directories

Run:

```bash
python generate_period_lookup_files_v2.py \
    spun_pile_refani_onion_lookup.yaml \
    degradation_lookups_uniform \
    --uniform
```

Expected folders:

```text
degradation_lookups_uniform/degradation_000y/
degradation_lookups_uniform/degradation_025y/
degradation_lookups_uniform/degradation_050y/
degradation_lookups_uniform/degradation_075y/
```

### Step 4: run section-property extraction per scenario

The section-property extraction must be run from inside each period directory, so that `T_lookup(...)` resolves the local files.

Pattern:

```bash
cd degradation_lookups_uniform/degradation_000y
# run section-property extraction with spun_pile_refani_onion_lookup.yaml

cd ../degradation_025y
# run the same extraction

cd ../degradation_050y
# run the same extraction

cd ../degradation_075y
# run the same extraction
```

## 11. Input-to-CSF mapping results

| scenario | year | ψ | cover factor used as CSF input | core factor used as CSF input | PC-bar area factor used as CSF input | E_cover,eq [MPa] | E_core,eq [MPa] | E_bar,eq [MPa] |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 000y | 0 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 18909.091 | 16099.071 | 196500.000 |
| 025y | 25 | 0.0619 | 0.9728 | 0.9634 | 0.9381 | 18395.640 | 15510.229 | 184343.200 |
| 050y | 50 | 0.1237 | 0.8477 | 0.9087 | 0.8763 | 16028.779 | 14628.699 | 172186.400 |
| 075y | 75 | 0.1856 | 0.4071 | 0.8263 | 0.8144 | 7698.221 | 13303.220 | 160029.600 |

These are the values transferred into the CSF lookup files. This table is the actual paper-to-CSF mapping check.

## 12. CSF section-property results

| scenario | A_eq | Ix_eq | Iy_eq | J_sv_cell | rx | Wx | Q_na |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 000y | 3129.420 | 102.225 | 102.225 | 76.378 | 0.180737 | 340.749 | 253.121 |
| 025y | 3020.491 | 98.775 | 98.775 | 74.075 | 0.180836 | 329.252 | 244.445 |
| 050y | 2731.336 | 88.709 | 88.709 | 66.231 | 0.180217 | 295.697 | 220.272 |
| 075y | 1896.468 | 58.223 | 58.223 | 41.313 | 0.175217 | 194.078 | 148.689 |

These are CSF outputs. They are not reported by the paper.

They are the equivalent section properties obtained after applying the paper-derived input degradation factors to the CSF polygonal model.

## 13. Relative changes in CSF section properties

| scenario | ΔA_eq vs 000y | ΔIx_eq vs 000y | ΔJ_sv_cell vs 000y |
|---:|---:|---:|---:|
| 000y | 0.00% | 0.00% | 0.00% |
| 025y | -3.48% | -3.37% | -3.02% |
| 050y | -12.72% | -13.22% | -13.29% |
| 075y | -39.40% | -43.04% | -45.91% |

The decreasing trend is consistent with the applied degradation.

The reduction in section properties is not expected to be numerically identical to the material degradation factors, because the section properties are obtained by integrating multiple weighted polygon families at different radial positions.

## 14. Scenario details

### Scenario 000y

Input side:

- corrosion degree: ψ = 0.0000
- cover-concrete reduction factor used in the CSF lookup: 1.0000
- core-concrete reduction factor used in the CSF lookup: 1.0000
- PC-bar area-loss equivalent factor used in the CSF lookup: 1.0000

CSF lookup weights:

- cover polygons: E_cover,eq = 18909.091 MPa
- core polygons: E_core,eq = 16099.071 MPa
- PC-bar polygons: E_bar,eq = 196500.000 MPa

CSF section-property output:

- A_eq = 3129.420
- Ix_eq = Iy_eq = 102.225
- J_sv_cell = 76.378
- Cx = 0, Cy = 0, Ixy = 0 in the printed output

### Scenario 025y

Input side:

- corrosion degree: ψ = 0.0619
- cover-concrete reduction factor used in the CSF lookup: 0.9728
- core-concrete reduction factor used in the CSF lookup: 0.9634
- PC-bar area-loss equivalent factor used in the CSF lookup: 0.9381

CSF lookup weights:

- cover polygons: E_cover,eq = 18395.640 MPa
- core polygons: E_core,eq = 15510.229 MPa
- PC-bar polygons: E_bar,eq = 184343.200 MPa

CSF section-property output:

- A_eq = 3020.491
- Ix_eq = Iy_eq = 98.775
- J_sv_cell = 74.075
- Cx = 0, Cy = 0, Ixy = 0 in the printed output

### Scenario 050y

Input side:

- corrosion degree: ψ = 0.1237
- cover-concrete reduction factor used in the CSF lookup: 0.8477
- core-concrete reduction factor used in the CSF lookup: 0.9087
- PC-bar area-loss equivalent factor used in the CSF lookup: 0.8763

CSF lookup weights:

- cover polygons: E_cover,eq = 16028.779 MPa
- core polygons: E_core,eq = 14628.699 MPa
- PC-bar polygons: E_bar,eq = 172186.400 MPa

CSF section-property output:

- A_eq = 2731.336
- Ix_eq = Iy_eq = 88.709
- J_sv_cell = 66.231
- Cx = 0, Cy = 0, Ixy = 0 in the printed output

### Scenario 075y

Input side:

- corrosion degree: ψ = 0.1856
- cover-concrete reduction factor used in the CSF lookup: 0.4071
- core-concrete reduction factor used in the CSF lookup: 0.8263
- PC-bar area-loss equivalent factor used in the CSF lookup: 0.8144

CSF lookup weights:

- cover polygons: E_cover,eq = 7698.221 MPa
- core polygons: E_core,eq = 13303.220 MPa
- PC-bar polygons: E_bar,eq = 160029.600 MPa

CSF section-property output:

- A_eq = 1896.468
- Ix_eq = Iy_eq = 58.223
- J_sv_cell = 41.313
- Cx = 0, Cy = 0, Ixy = 0 in the printed output


## 15. Uniformity check along the member axis

For each scenario, the section-property output was constant at the selected stations:

```text
z = 0.0
z = 1.0
z = 3.0
z = 3.5
z = 4.5
z = 5.5
z = 10.0
z = 15.0
z = 20.0
```

This confirms that the uniform lookup generation did not introduce an axial variation.

In all four scenarios, the printed symmetry quantities were:

```text
Cx = 0
Cy = 0
Ixy = 0
Ix = Iy
```

This is consistent with the circular geometry and symmetric 32-bar layout.

## 16. What the procedure demonstrates

The procedure demonstrates the following.

1. A published corrosion/material degradation study can be used as a literature-based input source.

2. The published degradation information can be transferred to CSF through polygon-specific lookup weights.

3. A single fixed CSF geometry can support multiple physical scenarios by changing only the local lookup files.

4. CSF converts the mapped degradation inputs into equivalent section properties.

5. The resulting section properties are internally consistent: they are uniform along `z` for the uniform case, symmetric, and monotonically degraded from 000y to 075y.

## 17. What the procedure does not demonstrate

This procedure does not reproduce the local 3D nonlinear FEM of the paper.

It does not validate CSF against paper-provided values of `A_eq`, `Ix_eq`, `Iy_eq`, or `J_sv_cell`, because the paper does not provide those quantities.

It does not use the paper's PC-bar yield-strength degradation as a nonlinear steel law.

It does not use the paper's bond-strength degradation as a bond-slip model.

It does not represent the transverse helical reinforcement as an explicit longitudinal CSF polygon.

## 18. Technical interpretation

The correct interpretation is:

```text
Paper:
  corrosion and local FEM/material analysis
  → material degradation quantities

CSF:
  material degradation quantities
  → polygon weights
  → equivalent section properties
```

The paper is therefore an input source, not a final-output benchmark.

## Appendix A: full `attach_polygon_axial_degradation.py`

```python
#!/usr/bin/env python3
"""
Attach one axial T_lookup weight law to each CSF polygon.

Usage:
    python attach_polygon_axial_degradation.py input.yaml output.yaml axial_degradation.txt

Example generated law:
    - "pcbar_00,pcbar_00: T_lookup('axial_degradation_pcbar_00.txt')"

The script does not create the lookup tables.
It only writes the YAML references to the per-polygon lookup files.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def line_indent(line: str) -> int:
    """Return the number of leading spaces in a YAML line."""
    return len(line) - len(line.lstrip(" "))


def logical_polygon_name(raw_name: str) -> str:
    """Return the law name used by CSF.

    Some geometry generators may use suffixes such as '@cell' in the polygon
    key. The weight law uses the logical polygon name before that suffix.
    """
    return raw_name.split("@", 1)[0]


def lookup_file_for_polygon(base_lookup: Path, polygon_name: str) -> str:
    """Build the lookup file name for one polygon."""
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", polygon_name)
    suffix = base_lookup.suffix
    stem = base_lookup.stem if suffix else base_lookup.name

    if suffix:
        out = base_lookup.with_name(f"{stem}_{safe_name}{suffix}")
    else:
        out = base_lookup.with_name(f"{stem}_{safe_name}")

    return out.as_posix()


def find_polygon_names(yaml_text: str) -> list[str]:
    """Find polygon names from all 'polygons:' blocks, preserving order."""
    lines = yaml_text.splitlines()

    names: list[str] = []
    seen: set[str] = set()

    inside_polygons = False
    polygons_indent = -1
    polygon_indent: int | None = None

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        indent = line_indent(line)

        if stripped == "polygons:":
            inside_polygons = True
            polygons_indent = indent
            polygon_indent = None
            continue

        if not inside_polygons:
            continue

        if indent <= polygons_indent:
            inside_polygons = False
            polygon_indent = None
            continue

        if polygon_indent is None:
            polygon_indent = indent

        if indent != polygon_indent:
            continue

        match = re.match(r"^\s*([A-Za-z0-9_@.-]+)\s*:\s*$", line)
        if not match:
            continue

        raw_name = match.group(1)
        name = logical_polygon_name(raw_name)

        if name == "void":
            continue

        if name not in seen:
            names.append(name)
            seen.add(name)

    if not names:
        raise ValueError("No CSF polygons found in the input YAML.")

    return names


def remove_existing_weight_laws(yaml_text: str) -> str:
    """Remove an existing CSF-level weight_laws block, if present."""
    lines = yaml_text.splitlines()
    out: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^(\s*)weight_laws\s*:\s*$", line)

        if not match:
            out.append(line)
            i += 1
            continue

        block_indent = len(match.group(1))
        i += 1

        while i < len(lines):
            next_line = lines[i]

            if not next_line.strip():
                i += 1
                continue

            next_indent = line_indent(next_line)
            if next_indent <= block_indent:
                break

            i += 1

    return "\n".join(out).rstrip() + "\n"


def make_weight_laws_block(polygon_names: list[str], base_lookup: Path) -> str:
    """Create the YAML weight_laws block."""
    lines = ["  weight_laws:"]

    for name in polygon_names:
        lookup_file = lookup_file_for_polygon(base_lookup, name)
        law = f"{name},{name}: T_lookup('{lookup_file}')"
        lines.append(f'    - "{law}"')

    return "\n".join(lines) + "\n"


def attach_weight_laws(input_yaml: Path, output_yaml: Path, base_lookup: Path) -> None:
    """Read the input YAML, attach per-polygon lookup laws, and write output."""
    yaml_text = input_yaml.read_text(encoding="utf-8")

    polygon_names = find_polygon_names(yaml_text)
    yaml_text = remove_existing_weight_laws(yaml_text)

    weight_laws_block = make_weight_laws_block(polygon_names, base_lookup)
    output_text = yaml_text.rstrip() + "\n" + weight_laws_block

    output_yaml.write_text(output_text, encoding="utf-8")

    print(f"Written: {output_yaml}")
    print(f"Polygons with axial degradation laws: {len(polygon_names)}")
    print("Lookup files to provide:")
    for name in polygon_names:
        print(f"  {lookup_file_for_polygon(base_lookup, name)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Attach per-polygon axial degradation lookup laws to a CSF YAML file."
    )
    parser.add_argument("input_yaml", type=Path, help="Input CSF YAML file.")
    parser.add_argument("output_yaml", type=Path, help="Output CSF YAML file.")
    parser.add_argument(
        "axial_degradation_lookup",
        type=Path,
        help="Base lookup file name, e.g. axial_degradation.txt.",
    )

    args = parser.parse_args()

    attach_weight_laws(
        input_yaml=args.input_yaml,
        output_yaml=args.output_yaml,
        base_lookup=args.axial_degradation_lookup,
    )


if __name__ == "__main__":
    main()

```

## Appendix B: full `generate_period_lookup_files_v2.py`

```python
#!/usr/bin/env python3
"""
Generate absolute per-polygon axial degradation lookup files for a CSF YAML model.

The YAML remains unique and fixed. Each physical scenario is represented by
lookup files stored in a period directory.

Usage:
    python generate_period_lookup_files_v2.py input.yaml output_dir
    python generate_period_lookup_files_v2.py input.yaml output_dir --uniform

With --uniform, the full period degradation is applied everywhere:
    g(z/L) = 1

Without --uniform, the default axial shape is used.
"""

from __future__ import annotations

import argparse
import math
import os
import re
from pathlib import Path


PERIODS_YEARS = (0, 25, 50, 75)

PSI_75 = 0.1856

FC_CONCRETE_MPA = 52.0
EPS_COVER_PEAK = 0.00275
EPS_CORE_PEAK = 0.00323

ES_BAR_MPA = 196_500.0


# Default non-uniform axial shapes.
# g(t) = 0 -> no local degradation
# g(t) = 1 -> full degradation for the selected period
DEFAULT_SHAPES = {
    "cover": {
        "type": "double_gaussian",
        "centers": (0.30, 0.70),
        "sigma": 0.08,
        "amplitude": 1.00,
    },
    "core": {
        "type": "double_gaussian",
        "centers": (0.30, 0.70),
        "sigma": 0.10,
        "amplitude": 0.70,
    },
    "bar": {
        "type": "double_gaussian",
        "centers": (0.30, 0.70),
        "sigma": 0.08,
        "amplitude": 1.00,
    },
}


# Optional polygon-specific shape overrides.
# Example:
# POLYGON_SHAPES = {
#     "pcbar_00": {"type": "gaussian", "center": 0.30, "sigma": 0.06, "amplitude": 1.00},
# }
POLYGON_SHAPES = {}


def psi_from_year(year: int) -> float:
    """Return corrosion degree psi for one period."""
    return PSI_75 * (year / 75.0)


def r_cover_fit(psi: float) -> float:
    """Cover-concrete compressive-strength reduction fit."""
    return 0.25 * math.atan((0.149 - psi) / 0.025) + 0.65


def r_core_fit(psi: float) -> float:
    """Core-concrete compressive-strength reduction fit."""
    return 0.14 * math.atan((0.170 - psi) / 0.100) + 0.848


def r_cover(psi: float) -> float:
    """Cover factor, with the undegraded state fixed to 1.0."""
    return 1.0 if abs(psi) < 1e-15 else r_cover_fit(psi)


def r_core(psi: float) -> float:
    """Core factor, with the undegraded state fixed to 1.0."""
    return 1.0 if abs(psi) < 1e-15 else r_core_fit(psi)


def material_data(material: str, year: int) -> tuple[float, float]:
    """Return undegraded absolute weight E0 and period degradation intensity d.

    The generated value is:
        w(t) = E0 * (1 - d * g(t))
    """
    psi = psi_from_year(year)

    if material == "cover":
        e0 = FC_CONCRETE_MPA / EPS_COVER_PEAK
        d = 1.0 - r_cover(psi)
        return e0, d

    if material == "core":
        e0 = FC_CONCRETE_MPA / EPS_CORE_PEAK
        d = 1.0 - r_core(psi)
        return e0, d

    if material == "bar":
        e0 = ES_BAR_MPA
        d = psi
        return e0, d

    raise ValueError(f"Unknown material class: {material}")


def line_indent(line: str) -> int:
    """Return the number of leading spaces in a line."""
    return len(line) - len(line.lstrip(" "))


def logical_polygon_name(raw_name: str) -> str:
    """Remove non-logical suffixes such as '@cell' from a polygon key."""
    return raw_name.split("@", 1)[0]


def find_polygon_names(yaml_text: str) -> list[str]:
    """Find polygon names from all 'polygons:' blocks, preserving order."""
    lines = yaml_text.splitlines()

    names: list[str] = []
    seen: set[str] = set()

    inside_polygons = False
    polygons_indent = -1
    polygon_indent: int | None = None

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        indent = line_indent(line)

        if stripped == "polygons:":
            inside_polygons = True
            polygons_indent = indent
            polygon_indent = None
            continue

        if not inside_polygons:
            continue

        if indent <= polygons_indent:
            inside_polygons = False
            polygon_indent = None
            continue

        if polygon_indent is None:
            polygon_indent = indent

        if indent != polygon_indent:
            continue

        match = re.match(r"^\s*([A-Za-z0-9_@.-]+)\s*:\s*$", line)
        if not match:
            continue

        name = logical_polygon_name(match.group(1))

        if name == "void":
            continue

        if name not in seen:
            names.append(name)
            seen.add(name)

    if not names:
        raise ValueError("No CSF polygons found in the input YAML.")

    return names


def material_for_polygon(name: str) -> str:
    """Assign one material class to one polygon name."""
    if name in {"cover_outer", "cover_inner"}:
        return "cover"

    if name in {"core_inner", "pcbar_host_layer"}:
        return "core"

    if re.fullmatch(r"pcbar_\d+", name):
        return "bar"

    raise ValueError(f"No material class defined for polygon: {name}")


def clip01(value: float) -> float:
    """Clamp a number to the [0, 1] interval."""
    return max(0.0, min(1.0, value))


def gaussian(t: float, center: float, sigma: float) -> float:
    """Unit Gaussian shape."""
    if sigma <= 0.0:
        raise ValueError("sigma must be positive")
    return math.exp(-0.5 * ((t - center) / sigma) ** 2)


def shape_value(t: float, params: dict) -> float:
    """Evaluate a normalized axial degradation shape."""
    shape_type = params.get("type", "uniform")
    amplitude = float(params.get("amplitude", 1.0))

    if shape_type == "uniform":
        return clip01(amplitude)

    if shape_type == "gaussian":
        value = amplitude * gaussian(
            t=t,
            center=float(params["center"]),
            sigma=float(params["sigma"]),
        )
        return clip01(value)

    if shape_type == "double_gaussian":
        centers = params["centers"]
        sigma = float(params["sigma"])
        value = amplitude * max(
            gaussian(t=t, center=float(centers[0]), sigma=sigma),
            gaussian(t=t, center=float(centers[1]), sigma=sigma),
        )
        return clip01(value)

    if shape_type == "plateau":
        start = float(params["start"])
        end = float(params["end"])
        return clip01(amplitude if start <= t <= end else 0.0)

    raise ValueError(f"Unknown shape type: {shape_type}")


def shape_for_polygon(name: str) -> dict:
    """Return the shape parameters for one polygon."""
    if name in POLYGON_SHAPES:
        return POLYGON_SHAPES[name]

    material = material_for_polygon(name)
    return DEFAULT_SHAPES[material]


def lookup_filename(name: str) -> str:
    """Return the final T_lookup file name for one polygon."""
    return f"axial_degradation_{name}.txt"


def generate_lookup_rows(
    name: str,
    year: int,
    n_points: int,
    uniform: bool,
) -> list[tuple[float, float]]:
    """Generate rows (t_norm, absolute_weight) for one polygon and period."""
    material = material_for_polygon(name)
    e0, d = material_data(material, year)
    params = shape_for_polygon(name)

    rows: list[tuple[float, float]] = []

    for i in range(n_points):
        t = i / (n_points - 1)

        if uniform:
            g = 1.0
        else:
            g = shape_value(t, params)

        weight = e0 * (1.0 - d * g)
        rows.append((t, weight))

    return rows


def write_lookup_file(path: Path, rows: list[tuple[float, float]]) -> None:
    """Write one lookup file."""
    lines = [
        "# t_norm  absolute_weight",
        "# t_norm is the normalized axial coordinate z/L.",
        "# absolute_weight is read directly by T_lookup().",
    ]

    for t, weight in rows:
        lines.append(f"{t:.8f}  {weight:.12g}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_relative_symlink(source: Path, link_path: Path) -> None:
    """Create or replace a relative symbolic link."""
    source = source.resolve()
    link_path.parent.mkdir(parents=True, exist_ok=True)

    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()

    relative_source = Path(os.path.relpath(source, start=link_path.parent.resolve()))
    link_path.symlink_to(relative_source)


def generate_all(input_yaml: Path, output_dir: Path, n_points: int, uniform: bool) -> None:
    """Generate all period directories and per-polygon lookup files."""
    yaml_text = input_yaml.read_text(encoding="utf-8")
    polygon_names = find_polygon_names(yaml_text)

    output_dir.mkdir(parents=True, exist_ok=True)

    mode = "uniform g=1" if uniform else "default axial shapes"
    print(f"Generation mode: {mode}")

    for year in PERIODS_YEARS:
        period_dir = output_dir / f"degradation_{year:03d}y"
        period_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nPeriod {year} years -> {period_dir}")

        for name in polygon_names:
            rows = generate_lookup_rows(
                name=name,
                year=year,
                n_points=n_points,
                uniform=uniform,
            )
            file_path = period_dir / lookup_filename(name)
            write_lookup_file(file_path, rows)

            material = material_for_polygon(name)
            e0, d = material_data(material, year)
            print(f"  {file_path.name:<42} material={material:<5} E0={e0:.6g} d={d:.6g}")

        yaml_link = period_dir / input_yaml.name
        make_relative_symlink(input_yaml, yaml_link)
        print(f"  geometry YAML link: {yaml_link.name} -> {yaml_link.readlink()}")

    print("\nDone.")
    print(f"Polygons processed: {len(polygon_names)}")
    print("The YAML remains fixed. Select a period by running from the corresponding lookup directory.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate absolute axial degradation lookup files for each CSF polygon and period."
    )
    parser.add_argument("input_yaml", type=Path, help="Input CSF YAML file, used to discover polygon names.")
    parser.add_argument("output_dir", type=Path, help="Output directory for period lookup folders.")
    parser.add_argument("--points", type=int, default=101, help="Number of points per lookup file. Default: 101.")
    parser.add_argument(
        "--uniform",
        action="store_true",
        help="Use g(z/L)=1 everywhere. This applies the full period degradation uniformly.",
    )

    args = parser.parse_args()

    if args.points < 2:
        raise ValueError("--points must be at least 2")

    generate_all(
        input_yaml=args.input_yaml,
        output_dir=args.output_dir,
        n_points=args.points,
        uniform=args.uniform,
    )


if __name__ == "__main__":
    main()

```
