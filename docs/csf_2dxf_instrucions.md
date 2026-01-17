# CSF → DXF (and FreeCAD → CSF) Instructions

> **Required FreeCAD version:** **FreeCAD 1.0.0** (tested workflow).  
> The steps below are written for FreeCAD 1.0.0 on Linux. The UI names may differ slightly on other versions.

This document describes, step by step, how to:

1. **Author the CSF data in FreeCAD** (geometry + metadata).
2. **Export a CSF YAML file** from FreeCAD.
3. **Generate a DXF** that encodes the CSF information (2 sections, any number of polygons per section, any number of vertices per polygon).
4. **Validate** the DXF and round-trip it back to YAML.

The goal is a DXF that is:
- **Viewable** in CAD tools (FreeCAD, LibreCAD, etc.).
- **Machine-readable** by a tolerant DXF-to-YAML parser (pair-based parsing, no strict DXF object model required).
- **Deterministic** (same input → same output ordering when possible).

---

## Table of Contents

- [1. Concepts and Data Model](#1-concepts-and-data-model)
- [2. Repository Files](#2-repository-files)
- [3. Prerequisites on Linux](#3-prerequisites-on-linux)
- [4. Authoring the Data in FreeCAD](#4-authoring-the-data-in-freecad)
  - [4.1 Create (or import) polygon geometry](#41-create-or-import-polygon-geometry)
  - [4.2 Create the two section groups (S0 and S1)](#42-create-the-two-section-groups-s0-and-s1)
  - [4.3 Assign polygon names (formal keys)](#43-assign-polygon-names-formal-keys)
  - [4.4 Assign metadata (z and weight) inside FreeCAD](#44-assign-metadata-z-and-weight-inside-freecad)
- [5. Export CSF YAML from FreeCAD (Macro)](#5-export-csf-yaml-from-freecad-macro)
  - [5.1 Install the macro](#51-install-the-macro)
  - [5.2 Run the macro and set metadata](#52-run-the-macro-and-set-metadata)
  - [5.3 Unit conversion (mm ↔ m)](#53-unit-conversion-mm--m)
- [6. Generate a DXF from CSF YAML](#6-generate-a-dxf-from-csf-yaml)
  - [6.1 DXF encoding rules used](#61-dxf-encoding-rules-used)
  - [6.2 YAML → DXF generator script (copy/paste)](#62-yaml--dxf-generator-script-copypaste)
  - [6.3 Run the generator](#63-run-the-generator)
- [7. Validate and Round-trip](#7-validate-and-round-trip)
  - [7.1 Convert DXF back to YAML](#71-convert-dxf-back-to-yaml)
  - [7.2 Inspect raw DXF metadata](#72-inspect-raw-dxf-metadata)
- [8. Visualize the DXF in Linux](#8-visualize-the-dxf-in-linux)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Notes on DXF Conformance](#10-notes-on-dxf-conformance)

---

## 1. Concepts and Data Model

Your CSF YAML is assumed to have this *fixed key structure*:

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        lowerpart:
          weight: 1.0
          vertices:
            - [x0, y0]
            - [x1, y1]
            - ...
        upperpart:
          weight: 1.0
          vertices:
            - [x0, y0]
            - [x1, y1]
            - ...
    S1:
      z: 10.0
      polygons:
        lowerpart:
          weight: 1.0
          vertices:
            - [x0, y0]
            - [x1, y1]
            - ...
        upperpart:
          weight: 1.0
          vertices:
            - [x0, y0]
            - [x1, y1]
            - ...
  weight_laws:
    - "..."
```

**Rules you should follow:**
- There are **exactly two sections**: `S0` and `S1`.
- Each section contains **any number of polygons**.
- Each polygon has **any number of vertices (>= 3)**.
- Vertex lists should be **counter-clockwise (CCW)** for consistency (recommended).
- Vertex lists **should not repeat** the first vertex as the last vertex (recommended). Closed-ness is implied by the polygon concept.

---

## 2. Repository Files

Typical files involved in this workflow:

- `csf_freecad_export_yaml.FCMacro`  
  A FreeCAD macro that exports the active document to CSF YAML by reading:
  - Group names `S0` and `S1`
  - Group property `CSF_z`
  - Polygon property `CSF_weight`
  - Polygon vertex coordinates (and enforces CCW orientation)

- `csf_dxf_converter.py`  
  A tolerant DXF → CSF YAML converter that reads ASCII DXF as raw group code/value pairs.
  It groups polygons by:
  - **Layer** (`8`) for the section name (`S0`, `S1`)
  and reads:
  - **Elevation** (`38`) as `z`
  - **Thickness** (`39`) as `weight`
  - Vertices from `(10,20)` pairs

- Example DXF:
  - `csf_2sections_4polygons.dxf`

---

## 3. Prerequisites on Linux

### 3.1 Install FreeCAD 1.0.0
Install FreeCAD **1.0.0** (matching the required version at the top of this document).  
Use your distribution packages or an official package format you prefer.

### 3.2 Install Python (recommended: 3.10+)
You will need Python to run conversion scripts.

Verify:
```bash
python3 --version
```

### 3.3 Create and activate a virtual environment (recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 3.4 Optional: install PyYAML
If you want to parse YAML natively in the generator script (recommended):

```bash
python -m pip install pyyaml
```

---

## 4. Authoring the Data in FreeCAD

### 4.1 Create (or import) polygon geometry

You need **closed 2D polygon wires**, one FreeCAD object per polygon.

#### Option A — Create polygons in Draft workbench
1. Start FreeCAD.
2. Switch workbench (top dropdown): **Draft**.
3. Create a polygon wire:
   - Use **Draft Polyline** (or **Draft Wire**).
4. Click points to define vertices.
5. **Close the wire**:
   - Some tools have a “Close” option.
   - Otherwise, ensure the last point coincides with the first, then use “Close” if available.
6. Repeat for all polygons.

#### Option B — Import from DXF
1. `File → Open...` and select your `.dxf`  
2. Verify each polygon becomes a separate closed wire object in the tree.

> Important: If an imported shape becomes a sketch, face, or compound, you may need to convert it to a wire suitable for vertex extraction.

---

### 4.2 Create the two section groups (S0 and S1)

You must have **exactly two groups** in the Model tree:

- `S0`
- `S1`

Steps:
1. In the Model tree, right-click in empty space.
2. Choose **Create group**.
3. Rename the group:
   - Select it → press **F2** (or right-click → Rename).
   - Name it **S0**.
4. Repeat to create **S1**.

Now assign polygon objects to groups:
- Drag each polygon object onto `S0` or `S1` in the tree.
- Or right-click object → “Move to group” (if available).

---

### 4.3 Assign polygon names (formal keys)

The polygon name in YAML will come from the object **Label** (preferred).

Example required names:
- `lowerpart`
- `upperpart`

Steps:
1. Select a polygon object in the Model tree.
2. Rename its **Label** to the desired YAML key:
   - Press **F2** and type `lowerpart` / `upperpart`, etc.
3. Repeat for all polygons.

**Naming recommendations:**
- Use only letters, digits, underscore.
- Avoid spaces and colons in keys.

---

### 4.4 Assign metadata (z and weight) inside FreeCAD

FreeCAD does not provide “CSF z” and “CSF weight” as standard properties for imported polylines, so we store them as **custom properties**.

The macro will create these if missing:

- On group (`S0` / `S1`): `CSF_z` (float)
- On polygon objects: `CSF_weight` (float)

After the macro runs once, edit them here:

#### Edit `CSF_z` (group z)
1. Select group `S0`.
2. Property editor (usually bottom-left): **Data** tab.
3. Find category **CSF**.
4. Set `CSF_z` (example: `0.0`).
5. Repeat for group `S1` (example: `10.0`).

#### Edit `CSF_weight` (polygon weight)
1. Select a polygon object.
2. Property editor → **Data** tab → **CSF**.
3. Set `CSF_weight` (example: `1.0`).
4. Repeat for all polygons.

---

## 5. Export CSF YAML from FreeCAD (Macro)

### 5.1 Install the macro

1. Download/copy `csf_freecad_export_yaml.FCMacro` into your FreeCAD macros folder:
   - `Macro → Macros...`
   - Note the “Macros folder” path shown in that dialog.
2. Put the `.FCMacro` file in that folder.

Alternative (manual creation):
1. `Macro → Macros...`
2. Click **Create**.
3. Name it: `csf_freecad_export_yaml`
4. Paste the macro content.
5. Save.

### 5.2 Run the macro and set metadata

1. Open your FreeCAD document that contains groups `S0` and `S1`.
2. Run:
   - `Macro → Macros...`
   - Select `csf_freecad_export_yaml`
   - Click **Execute**
3. First run behavior:
   - The macro ensures `CSF_z` exists on `S0` and `S1`.
   - The macro ensures `CSF_weight` exists on each polygon object.
4. Set the values (see section 4.4).
5. Run the macro again.
6. Choose where to save the YAML (`.yaml`).

### 5.3 Unit conversion (mm ↔ m)

FreeCAD often models in **mm**.
If you need YAML in **meters**, set `SCALE = 0.001` inside the macro.

- `SCALE = 1.0`  → export in FreeCAD units (commonly mm)
- `SCALE = 0.001` → mm → m

---

## 6. Generate a DXF from CSF YAML

### 6.1 DXF encoding rules used

Each CSF polygon becomes a DXF `LWPOLYLINE` entity with:

- **Section name** stored as:
  - Layer name (`group code 8`) = `S0` or `S1`
- **z** stored as:
  - Elevation (`group code 38`)
- **weight** stored as:
  - Thickness (`group code 39`)
- **vertices** stored as:
  - Repeated coordinate pairs:
    - `10` = x
    - `20` = y
- `70 = 1` to mark the polyline as **closed**
- Optional `999` comment line storing a redundant key-value record:
  - `CSF; section: ...; z: ...; name: ...; weight: ...`

This is intentionally simple and readable.

---

### 6.2 YAML → DXF generator script (copy/paste)

Create a file named `csf_yaml2dxf.py` (in your project folder) with the following content:

```python
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

try:
    import yaml  # pip install pyyaml
except Exception as e:
    raise SystemExit("PyYAML is required: pip install pyyaml") from e

Point = Tuple[float, float]

def lwpolyline_entity(handle_hex: str, section: str, z: float, name: str, weight: float, pts: List[Point]) -> str:
    # pts should be CCW; the generator does not reorder them.
    lines: List[str] = []
    lines += ["0", "LWPOLYLINE"]
    lines += ["5", handle_hex]
    lines += ["999", f"CSF; section: {section}; z: {z}; name: {name}; weight: {weight}"]
    lines += ["100", "AcDbEntity"]
    lines += ["8", section]            # layer = section (S0/S1)
    lines += ["39", str(weight)]       # thickness = weight
    lines += ["100", "AcDbPolyline"]
    lines += ["38", str(z)]            # elevation = z
    lines += ["90", str(len(pts))]     # vertex count
    lines += ["70", "1"]               # closed polyline
    for x, y in pts:
        lines += ["10", str(x), "20", str(y)]
    return "\n".join(lines) + "\n"

def build_dxf_from_csf(csf: Dict[str, Any]) -> str:
    sections = csf["CSF"]["sections"]
    # The spec says these always exist:
    s0 = sections["S0"]
    s1 = sections["S1"]

    # Layer table declares S0 and S1 (helps some viewers).
    layer_table = (
        "0\nTABLE\n2\nLAYER\n70\n2\n"
        "0\nLAYER\n5\n10\n100\nAcDbSymbolTableRecord\n100\nAcDbLayerTableRecord\n2\nS0\n70\n0\n62\n7\n6\nCONTINUOUS\n"
        "0\nLAYER\n5\n11\n100\nAcDbSymbolTableRecord\n100\nAcDbLayerTableRecord\n2\nS1\n70\n0\n62\n7\n6\nCONTINUOUS\n"
        "0\nENDTAB\n"
    )

    entities = ""
    handle = 1

    for sec_name in ["S0", "S1"]:
        z = float(sections[sec_name].get("z", 0.0))
        polys = sections[sec_name].get("polygons", {})
        for poly_name, poly in polys.items():
            w = float(poly.get("weight", 1.0))
            verts = poly.get("vertices", [])
            pts: List[Point] = [(float(x), float(y)) for x, y in verts]
            entities += lwpolyline_entity(f"{handle:X}", sec_name, z, poly_name, w, pts)
            handle += 1

    dxf = (
        "0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1015\n0\nENDSEC\n"
        "0\nSECTION\n2\nTABLES\n"
        + layer_table +
        "0\nENDSEC\n"
        "0\nSECTION\n2\nBLOCKS\n0\nENDSEC\n"
        "0\nSECTION\n2\nENTITIES\n"
        + entities +
        "0\nENDSEC\n0\nEOF\n"
    )
    return dxf

def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("input_yaml", help="Input CSF YAML")
    p.add_argument("output_dxf", help="Output DXF (ASCII)")
    args = p.parse_args()

    csf = yaml.safe_load(Path(args.input_yaml).read_text(encoding="utf-8"))
    dxf = build_dxf_from_csf(csf)
    Path(args.output_dxf).write_text(dxf, encoding="ascii")
    print(f"Wrote DXF: {args.output_dxf}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

---

### 6.3 Run the generator

With venv activated and PyYAML installed:

```bash
python csf_yaml2dxf.py your_csf.yaml out.dxf
```

You can now open `out.dxf` in FreeCAD / LibreCAD.

---

## 7. Validate and Round-trip

### 7.1 Convert DXF back to YAML

Use the tolerant converter:

```bash
python csf_dxf_converter.py out.dxf
```

Write to file:

```bash
python csf_dxf_converter.py out.dxf -o roundtrip.yaml
```

Compare `your_csf.yaml` and `roundtrip.yaml` to ensure the encoding is correct.

---

### 7.2 Inspect raw DXF metadata

To print all `999` comment lines (where section/z/name/weight are redundantly stored):

```bash
python - <<'PY'
from pathlib import Path
lines = Path("out.dxf").read_text(errors="ignore").splitlines()
for i in range(0, len(lines)-1, 2):
    if lines[i].strip() == "999":
        print(lines[i+1])
PY
```

To print per-entity key group codes (`8`, `38`, `39`, `10`, `20`, `999`):

```bash
python - <<'PY'
from pathlib import Path

def pairs(path):
    L = Path(path).read_text(errors="ignore").splitlines()
    out=[]
    for i in range(0, len(L)-1, 2):
        out.append((int(L[i].strip()), L[i+1].rstrip("\n")))
    return out

p = pairs("out.dxf")

# find ENTITIES section
i=0
while i+1 < len(p):
    if p[i]==(0,"SECTION") and p[i+1]==(2,"ENTITIES"):
        i += 2
        break
    i += 1

k=0
while i < len(p) and p[i]!=(0,"ENDSEC"):
    if p[i]==(0,"LWPOLYLINE"):
        k += 1
        i += 1
        keep=[]
        while i < len(p) and p[i][0] != 0:
            c,v = p[i]
            if c in (5,8,38,39,70,90,999,10,20):
                keep.append((c,v))
            i += 1
        print(f"\n=== ENTITY {k} ===")
        for c,v in keep:
            print(f"{c:>3} : {v}")
        continue
    i += 1
PY
```

---

## 8. Visualize the DXF in Linux

### Option A — FreeCAD
- `File → Open...` and select the DXF.
- You can usually see section grouping by **layers** (`S0` and `S1`).

### Option B — LibreCAD (2D)
Install and open the DXF for a fast 2D view.

### Option C — QCAD (2D)
Another reliable DXF viewer/editor.

---

## 9. Troubleshooting

### 9.1 “I can’t see the CSF metadata inside FreeCAD”
FreeCAD generally **does not show DXF comment (group code 999) metadata** after import.
That is expected.

What you *can* see:
- Layer/group separation (`S0`, `S1`) often survives as layers/groups.

What you should do to reconstruct CSF:
- Use `csf_dxf_converter.py` to extract the metadata and geometry.

### 9.2 Wrong polygon orientation (CW instead of CCW)
- The FreeCAD macro enforces CCW at export time (it reverses vertices if needed).
- If you generate DXF from YAML, make sure your YAML vertices are already CCW.

### 9.3 Duplicate polygon names inside the same section
- The exporter will suffix names: `lowerpart`, `lowerpart_2`, etc.
- Best practice: ensure unique labels per group.

### 9.4 Imported geometry contains arcs/splines
This pipeline exports **vertices only**.
If you need arc sampling (bulge discretization), you must implement a discretizer.

### 9.5 Units are wrong (too big / too small)
- Decide one standard (mm or meters).
- Use `SCALE` in the FreeCAD macro to convert.
- Keep the same unit convention across YAML ↔ DXF.

---

## 10. Notes on DXF Conformance

The generated DXF is intentionally minimal but follows standard section layout:

- `SECTION HEADER` with `$ACADVER = AC1015` (R2000)
- `SECTION TABLES` containing a minimal `LAYER` table with `S0` and `S1`
- `SECTION BLOCKS` (empty but present)
- `SECTION ENTITIES` containing `LWPOLYLINE` entities with required subclass markers:
  - `100 AcDbEntity`
  - `100 AcDbPolyline`

This structure is compatible with many DXF viewers and avoids common “strict parser” failures.
