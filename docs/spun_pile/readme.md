# DRAFT
# Refani–Nagao spun-pile degradation case: uniform CSF scenario generation and verification

## 1. Purpose

This document records the complete procedure used to build four uniform degradation scenarios for a prestressed spun pile modelled with CSF.

The objective is narrow:

1. start from the geometric and material data of the Refani–Nagao spun-pile study;
2. map the paper-derived material degradation quantities to CSF polygon weights;
3. generate one fixed CSF geometry/YAML model and four period-specific lookup directories;
4. run the CSF section-property extraction for the four uniform scenarios;
5. verify that the resulting CSF equivalent section properties change consistently from the undegraded to the degraded state.

The verification performed here is a mapping check. It is not a reproduction of the local 3D nonlinear finite-element analysis performed in the paper.

The paper provides local material degradation quantities. CSF then converts those material reductions into equivalent section quantities, such as axial and bending weighted properties.

## 2. Source paper data used in this case

Reference:

Refani, A. N.; Nagao, T. *Corrosion Effects on the Mechanical Properties of Spun Pile Materials*. Applied Sciences 2023, 13, 1507. DOI: 10.3390/app13031507.

The following values are used by the CSF case.

### 2.1 Geometry

| quantity | value |
|---|---:|
| outer diameter | 600 mm |
| wall thickness | 100 mm |
| inner diameter | 400 mm |
| cover concrete thickness | 50 mm |
| number of PC-bars | 32 |
| PC-bar diameter | 9 mm |
| transverse helical rebar diameter | 4 mm |
| transverse helical rebar spacing | 120 mm |

The CSF polygon model uses the main circular hollow section and the 32 longitudinal PC-bars. The transverse helical reinforcement is part of the paper's local 3D material-degradation model, but it is not represented as an explicit longitudinal CSF bar polygon in this elastic sectional mapping.

### 2.2 Material quantities

| quantity | value |
|---|---:|
| cover concrete peak strength, fc | 52 MPa |
| cover concrete peak strain, εc | 0.00275 |
| core concrete peak strength, fcc | 52 MPa |
| core concrete peak strain, εcc | 0.00323 |
| PC-bar modulus, Es | 196500 MPa |
| PC-bar 75-year corrosion degree, ψ75 | 0.1856 |

The CSF equivalent weights are expressed in MPa because the lookup files are used as absolute material weights.

## 3. CSF geometric representation

The CSF section is represented as concentric polygonal regions plus 32 discrete PC-bar polygons.

The geometric decomposition used by the case is:

| CSF polygon family | radial meaning |
|---|---|
| void | central hollow region, non-participating |
| core_inner | inner concrete layer |
| pcbar_host_layer | concrete layer hosting the PC-bar ring |
| cover_inner | inner part of cover concrete |
| cover_outer | outer part of cover concrete |
| pcbar_00 ... pcbar_31 | 32 discrete PC-bar polygons |

The void is excluded from the degradation lookup generation.

The PC-bars remain geometrically fixed. Their corrosion area loss is represented as an equivalent material weight reduction, not by changing the bar polygon diameter.

## 4. Material-to-CSF mapping

### 4.1 Corrosion degree by scenario

The four uniform scenarios are:

| scenario | year | corrosion degree |
|---:|---:|---:|
| 000y | 0 | 0.0000 |
| 025y | 25 | 0.0619 |
| 050y | 50 | 0.1237 |
| 075y | 75 | 0.1856 |

The interpolation used here is:

$$
\psi(y) = \psi_{75} \frac{y}{75}
$$

with:

$$
\psi_{75} = 0.1856
$$

### 4.2 Cover and core concrete

The paper provides degradation of concrete compressive strength, not a direct initial elastic modulus degradation law. Therefore, this CSF case uses an equivalent secant-type material weight derived from peak strength and peak strain.

The undegraded equivalent concrete weights are:

$$
E_{cover,0} = \frac{52}{0.00275} = 18909.091\;\text{MPa}
$$

$$
E_{core,0} = \frac{52}{0.00323} = 16099.071\;\text{MPa}
$$

The reduction factors used by the generator are:

$$
r_{cover}(\psi)
=
0.25\arctan\left(\frac{0.149-\psi}{0.025}\right)+0.65
$$

$$
r_{core}(\psi)
=
0.14\arctan\left(\frac{0.170-\psi}{0.100}\right)+0.848
$$

At ψ = 0, the generator forces both factors to exactly 1.0.

The CSF absolute lookup weights are then:

$$
E_{cover,eq}(\psi) = E_{cover,0} r_{cover}(\psi)
$$

$$
E_{core,eq}(\psi) = E_{core,0} r_{core}(\psi)
$$

### 4.3 PC-bars

For the PC-bars, the paper defines corrosion degree as mass loss relative to initial mass. If corrosion is uniformly distributed along the bar, this can be treated as area loss.

Since the CSF geometry keeps the PC-bar polygons fixed, the bar area loss is mapped to an equivalent material weight:

$$
E_{bar,eq}(\psi) = E_s(1-\psi)
$$

This is a computational equivalent for a fixed bar polygon. It should not be read as a physical degradation of the steel elastic modulus itself.

The PC-bar yield-strength degradation and bond-strength degradation from the paper are not used in the present elastic section-property mapping. They would be relevant for a nonlinear fiber or bond-slip model, not for this elastic equivalent-property extraction.

## 5. Uniform scenario definition

The uniform verification uses:

$$
g(z/L)=1
$$

for every participating polygon and for every station along the member.

The lookup value generated for each polygon is:

$$
w(z) = E_0\left(1-d_{period}g(z/L)\right)
$$

Since g(z/L) = 1 everywhere in this verification, each period produces constant lookup values along z.

This removes the axial-shape variable from the verification. The only tested operation is:

$$
\text{paper-derived degradation} \rightarrow \text{CSF polygon weight} \rightarrow \text{CSF equivalent section properties}
$$

## 6. Directory structure

The procedure assumes a case directory of this form:

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

The important structural point is that the geometry YAML is unique. The period-specific physical state is selected by the local lookup files in the active scenario directory.

## 7. Python scripts

Two Python scripts are used.

### 7.1 `attach_polygon_axial_degradation.py`

This script creates or updates the CSF YAML so that every participating polygon receives a `T_lookup(...)` weight law.

It does not generate the numeric lookup files. It only attaches the lookup-file references to the YAML.

Typical command:

```bash
python attach_polygon_axial_degradation.py \
    spun_pile_refani_onion.yaml \
    spun_pile_refani_onion_lookup.yaml \
    axial_degradation.txt
```

The third argument is used as a base name. The script expands it into per-polygon file names such as:

```text
axial_degradation_core_inner.txt
axial_degradation_cover_outer.txt
axial_degradation_pcbar_00.txt
...
axial_degradation_pcbar_31.txt
```

The resulting YAML contains a block of this form:

```yaml
weight_laws:
  - "core_inner,core_inner: T_lookup('axial_degradation_core_inner.txt')"
  - "pcbar_host_layer,pcbar_host_layer: T_lookup('axial_degradation_pcbar_host_layer.txt')"
  - "cover_inner,cover_inner: T_lookup('axial_degradation_cover_inner.txt')"
  - "cover_outer,cover_outer: T_lookup('axial_degradation_cover_outer.txt')"
  - "pcbar_00,pcbar_00: T_lookup('axial_degradation_pcbar_00.txt')"
  - "pcbar_01,pcbar_01: T_lookup('axial_degradation_pcbar_01.txt')"
  - "..."
  - "pcbar_31,pcbar_31: T_lookup('axial_degradation_pcbar_31.txt')"
```

### 7.2 `generate_period_lookup_files_v2.py`

This script generates the period folders and all per-polygon lookup files.

Uniform verification command:

```bash
python generate_period_lookup_files_v2.py \
    spun_pile_refani_onion_lookup.yaml \
    degradation_lookups_uniform \
    --uniform
```

The option `--uniform` forces:

$$
g(z/L)=1
$$

for all generated lookup values.

Non-uniform axial-shape generation is still available by omitting `--uniform`:

```bash
python generate_period_lookup_files_v2.py \
    spun_pile_refani_onion_lookup.yaml \
    degradation_lookups
```

The generated lookup files have the format:

```text
# t_norm  absolute_weight
# t_norm is the normalized axial coordinate z/L.
# absolute_weight is read directly by T_lookup().
0.00000000  <absolute_weight>
0.01000000  <absolute_weight>
...
1.00000000  <absolute_weight>
```

For the uniform verification, each file is constant along t_norm within a given period.

## 8. Execution procedure

### Step 1: create the fixed geometry YAML

The geometry-generation scripts create the onion/rebar polygonal CSF section.

Expected output:

```text
spun_pile_refani_onion.yaml
```

This file contains the geometric polygon definitions.

### Step 2: attach per-polygon lookup laws

Run:

```bash
python attach_polygon_axial_degradation.py \
    spun_pile_refani_onion.yaml \
    spun_pile_refani_onion_lookup.yaml \
    axial_degradation.txt
```

Expected output:

```text
spun_pile_refani_onion_lookup.yaml
```

This is still one unique YAML model. The physical period is not hard-coded in the YAML.

### Step 3: generate the four uniform period directories

Run:

```bash
python generate_period_lookup_files_v2.py \
    spun_pile_refani_onion_lookup.yaml \
    degradation_lookups_uniform \
    --uniform
```

Expected output:

```text
degradation_lookups_uniform/degradation_000y/
degradation_lookups_uniform/degradation_025y/
degradation_lookups_uniform/degradation_050y/
degradation_lookups_uniform/degradation_075y/
```

Each directory contains:

```text
spun_pile_refani_onion_lookup.yaml
axial_degradation_core_inner.txt
axial_degradation_pcbar_host_layer.txt
axial_degradation_cover_inner.txt
axial_degradation_cover_outer.txt
axial_degradation_pcbar_00.txt
...
axial_degradation_pcbar_31.txt
```

The YAML in each period directory is a symlink to the same fixed geometry/lookup YAML.

### Step 4: run the CSF section-property extraction per period

The section-property extraction is run from inside each period directory, so that `T_lookup(...)` resolves the local lookup files.

Example execution pattern:

```bash
cd degradation_lookups_uniform/degradation_000y
# run the CSF section-property extraction using spun_pile_refani_onion_lookup.yaml

cd ../degradation_025y
# run the same extraction command

cd ../degradation_050y
# run the same extraction command

cd ../degradation_075y
# run the same extraction command
```

The output files recorded for this verification are:

```text
spun_pile_refani_section_properties_000.txt
spun_pile_refani_section_properties_025.txt
spun_pile_refani_section_properties_050.txt
spun_pile_refani_section_properties_075.txt
```

## 9. Generated paper-derived factors and CSF equivalents

| scenario | ψ | cover factor | core factor | PC-bar area factor | E_cover,eq [MPa] | E_core,eq [MPa] | E_bar,eq [MPa] | A_eq | Ix = Iy_eq | J_sv_cell |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 000y | 0.0000 | 1.000 | 1.000 | 1.000 | 18909.091 | 16099.071 | 196500.000 | 3129.420 | 102.225 | 76.378 |
| 025y | 0.0619 | 0.973 | 0.963 | 0.938 | 18395.640 | 15510.229 | 184343.200 | 3020.491 | 98.775 | 74.075 |
| 050y | 0.1237 | 0.848 | 0.909 | 0.876 | 16028.779 | 14628.699 | 172186.400 | 2731.336 | 88.709 | 66.231 |
| 075y | 0.1856 | 0.407 | 0.826 | 0.814 | 7698.221 | 13303.220 | 160029.600 | 1896.468 | 58.223 | 41.313 |

## 10. Relative change of CSF equivalent section properties

| scenario | ΔA_eq vs 000y | ΔIx = ΔIy vs 000y | ΔJ_sv_cell vs 000y |
|---:|---:|---:|---:|
| 000y | 0.00% | 0.00% | 0.00% |
| 025y | -3.48% | -3.37% | -3.02% |
| 050y | -12.72% | -13.22% | -13.29% |
| 075y | -39.40% | -43.04% | -45.91% |

## 11. Scenario-by-scenario comparison tables

### Scenario 000y

| item | paper / paper-derived quantity | CSF equivalent used | CSF uniform section result |
|---|---:|---:|---:|
| corrosion degree | ψ = 0.0000 | full period degradation because g(z/L) = 1 | constant along z |
| cover concrete | r_cover = 1.000 | E_cover,eq = 18909.091 MPa | included in weighted section properties |
| core concrete | r_core = 1.000 | E_core,eq = 16099.071 MPa | included in weighted section properties |
| PC-bars | area factor = 1 - ψ = 1.000 | E_bar,eq = 196500.000 MPa | included through fixed bar polygons |
| axial equivalent property | not given by the paper | computed by CSF from polygon weights | A_eq = 3129.420 |
| bending equivalent property | not given by the paper | computed by CSF from polygon weights | Ix = Iy = 102.225 |
| torsion cell estimate | not given by the paper | computed by the selected CSF/SP torsion carrier | J_sv_cell = 76.378 |
| symmetry check | circular section with symmetric PC-bar layout | no centroid drift expected | Cx = 0, Cy = 0, Ixy = 0 |

### Scenario 025y

| item | paper / paper-derived quantity | CSF equivalent used | CSF uniform section result |
|---|---:|---:|---:|
| corrosion degree | ψ = 0.0619 | full period degradation because g(z/L) = 1 | constant along z |
| cover concrete | r_cover = 0.973 | E_cover,eq = 18395.640 MPa | included in weighted section properties |
| core concrete | r_core = 0.963 | E_core,eq = 15510.229 MPa | included in weighted section properties |
| PC-bars | area factor = 1 - ψ = 0.938 | E_bar,eq = 184343.200 MPa | included through fixed bar polygons |
| axial equivalent property | not given by the paper | computed by CSF from polygon weights | A_eq = 3020.491 |
| bending equivalent property | not given by the paper | computed by CSF from polygon weights | Ix = Iy = 98.775 |
| torsion cell estimate | not given by the paper | computed by the selected CSF/SP torsion carrier | J_sv_cell = 74.075 |
| symmetry check | circular section with symmetric PC-bar layout | no centroid drift expected | Cx = 0, Cy = 0, Ixy = 0 |

### Scenario 050y

| item | paper / paper-derived quantity | CSF equivalent used | CSF uniform section result |
|---|---:|---:|---:|
| corrosion degree | ψ = 0.1237 | full period degradation because g(z/L) = 1 | constant along z |
| cover concrete | r_cover = 0.848 | E_cover,eq = 16028.779 MPa | included in weighted section properties |
| core concrete | r_core = 0.909 | E_core,eq = 14628.699 MPa | included in weighted section properties |
| PC-bars | area factor = 1 - ψ = 0.876 | E_bar,eq = 172186.400 MPa | included through fixed bar polygons |
| axial equivalent property | not given by the paper | computed by CSF from polygon weights | A_eq = 2731.336 |
| bending equivalent property | not given by the paper | computed by CSF from polygon weights | Ix = Iy = 88.709 |
| torsion cell estimate | not given by the paper | computed by the selected CSF/SP torsion carrier | J_sv_cell = 66.231 |
| symmetry check | circular section with symmetric PC-bar layout | no centroid drift expected | Cx = 0, Cy = 0, Ixy = 0 |

### Scenario 075y

| item | paper / paper-derived quantity | CSF equivalent used | CSF uniform section result |
|---|---:|---:|---:|
| corrosion degree | ψ = 0.1856 | full period degradation because g(z/L) = 1 | constant along z |
| cover concrete | r_cover = 0.407 | E_cover,eq = 7698.221 MPa | included in weighted section properties |
| core concrete | r_core = 0.826 | E_core,eq = 13303.220 MPa | included in weighted section properties |
| PC-bars | area factor = 1 - ψ = 0.814 | E_bar,eq = 160029.600 MPa | included through fixed bar polygons |
| axial equivalent property | not given by the paper | computed by CSF from polygon weights | A_eq = 1896.468 |
| bending equivalent property | not given by the paper | computed by CSF from polygon weights | Ix = Iy = 58.223 |
| torsion cell estimate | not given by the paper | computed by the selected CSF/SP torsion carrier | J_sv_cell = 41.313 |
| symmetry check | circular section with symmetric PC-bar layout | no centroid drift expected | Cx = 0, Cy = 0, Ixy = 0 |


## 12. Uniformity check along z

For each scenario, the extracted properties are constant at all selected stations:

```text
z = 0.0, 1.0, 3.0, 3.5, 4.5, 5.5, 10.0, 15.0, 20.0
```

This confirms that `--uniform` generated `g(z/L)=1` lookup files and that the period variation is not being introduced through the axial coordinate.

The four outputs show:

| scenario | A_eq | Ix = Iy_eq | J_sv_cell | Cx | Cy | Ixy |
|---:|---:|---:|---:|---:|---:|---:|
| 000y | 3129.420 | 102.225 | 76.378 | 0 | 0 | 0 |
| 025y | 3020.491 | 98.775 | 74.075 | 0 | 0 | 0 |
| 050y | 2731.336 | 88.709 | 66.231 | 0 | 0 | 0 |
| 075y | 1896.468 | 58.223 | 41.313 | 0 | 0 | 0 |

The symmetry checks remain exact in the printed output:

```text
Cx = 0
Cy = 0
Ixy = 0
Ix = Iy
```

## 13. Interpretation of the verification

The verification confirms the following points.

1. The unique CSF geometry remains fixed across all four scenarios.

2. The period state is controlled only by lookup files.

3. With `g(z/L)=1`, all stations in a given period have identical material weights and identical equivalent section properties.

4. The degradation sequence is monotonic:

```text
000y > 025y > 050y > 075y
```

for `A_eq`, `Ix = Iy`, and `J_sv_cell`.

5. The 75-year scenario applies approximately:

| material family | paper-derived degradation factor used by CSF |
|---|---:|
| cover concrete | 0.407 |
| core concrete | 0.826 |
| PC-bars | 0.814 |

This is consistent with the intended use of the paper-derived degradation quantities in an elastic CSF section-property mapping.

## 14. Interpretation limits

The comparison is not a direct comparison between CSF and the paper's 3D finite-element results.

The paper's FEM model is a local nonlinear 3D model used to extract material degradation behaviour. It does not provide global beam response or CSF-style section functions such as:

```text
A(z)
Ix(z)
Iy(z)
J(z)
EA(z)
EI(z)
GJ(z)
```

The CSF procedure instead uses the paper-derived degradation quantities as input and computes equivalent section properties for a continuous-section model.

The PC-bar yield-strength degradation and bond-strength degradation reported by the paper are not part of this elastic equivalent-property verification. They would require a nonlinear material/fiber or bond-slip formulation.

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
