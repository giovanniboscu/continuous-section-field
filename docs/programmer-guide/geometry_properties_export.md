# Geometry  and properties export

## Purpose

This guide explains how to use the main export functions of **CSF (Continuous Section Field)** to generate solver-ready section data and explicit section geometry along the beam axis.

Even when a function name mentions a specific solver, the underlying idea is broader: **CSF is a continuous geometric/material description that can be sampled and exported for a generic numerical workflow**.

In practice, CSF allows you to:

- export section properties at user-defined stations,
- export section properties at **Gauss-Lobatto integration points**,
- export the **explicit polygon geometry** of the section at selected stations,
- prepare files that can be consumed by external structural solvers,
- preserve a direct link between the continuous field and the discretized solver input.

This is one of the key strengths of CSF: the model is continuous in `z`, but the export layer can provide exact discrete samples wherever the downstream solver needs them.

---

## Core idea

A `ContinuousSectionField` is built from two boundary sections:

- `section0` at `z = z0`
- `section1` at `z = z1`

Each section contains polygons. CSF interpolates the polygon vertices between the two sections, so the section can be evaluated at any intermediate `z` coordinate.

That means the export functions do not work on a small fixed catalog of predefined sections. Instead, they sample a **continuous field**.

This distinction matters:

- in a traditional workflow, you define a few discrete sections and manually assign them,
- in CSF, you define a continuous section field and export the exact samples required by the solver or by the verification process.

---

## Main export-related functions

The most relevant functions for export workflows are:

- `write_sap2000_template_pack(...)`
- `write_opensees_geometry(...)`
- `export_polygon_vertices_csv_file(...)`
- `field.get_lobatto_integration_points(...)`

Although the naming of some functions reflects the first target solver that motivated their implementation, their logic is useful well beyond that original context.

---

## Minimal model setup

Before exporting anything, you need a continuous field.

The example below builds a simple tapered T-like section from `z = 10` to `z = 20`.

```python
from csf import Pt, Polygon, Section, ContinuousSectionField

# Start section at z = 10
poly0_start = Polygon(
    vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
    weight=1.0,
    name="flange",
)

poly1_start = Polygon(
    vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
    weight=1.0,
    name="web",
)

# End section at z = 20
poly0_end = Polygon(
    vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
    weight=1.0,
    name="flange",
)

poly1_end = Polygon(
    vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
    weight=1.0,
    name="web",
)

s0 = Section(polygons=(poly0_start, poly1_start), z=10.0)
s1 = Section(polygons=(poly0_end, poly1_end), z=20.0)

field = ContinuousSectionField(section0=s0, section1=s1)
```

### Important modeling assumptions

For this interpolation-based workflow to remain valid:

- the start and end sections must be compatible,
- polygons should be defined consistently between the two ends,
- polygon topology should be prepared upstream,
- vertices must follow the expected orientation rules enforced by your validation pipeline.

In normal CSF usage, validation should happen upstream. Export functions are not meant to repair invalid geometry.

---

## 1. Exporting section data at user-defined stations

Use `write_sap2000_template_pack(...)` when you want section data at specific `z` locations.

Despite the solver-specific name, this function is useful as a **generic section export writer**.

### Example

```python
from csf import write_sap2000_template_pack

z_stations = [10.0, 15.0, 20.0]

write_sap2000_template_pack(
    field=field,
    z_values=z_stations,
    show_plot=False,
    E_ref=210e9,
    nu=0.30,
    include_plot=False,
    plot_filename="out/custom_station_pack.jpg",
    template_filename="out/custom_station_pack.txt",
)
```

### What this does

This call samples the continuous field at the exact stations listed in `z_values` and writes an output file containing the exported section information.

This is the right choice when:

- the solver requires section data at fixed prescribed stations,
- you want full control over the sampling coordinates,
- you want repeatable station positions shared across external tools,
- you are reproducing a known reference discretization.

### When to prefer explicit stations

Explicit stations are usually better when:

- the external solver already defines the integration or segmentation scheme,
- you need matching outputs for independent verification,
- you want to compare CSF sections with external section analyzers at specific `z` values,
- you are exporting only a few meaningful checkpoints.

---

## 2. Exporting section data at Gauss-Lobatto stations

A very important CSF capability is the possibility to sample the section field at **Gauss-Lobatto points**.

This is significant because many beam and frame formulations use Gauss-Lobatto integration, where the end points are included explicitly.

Since CSF is continuous in `z`, it can provide section samples exactly at those integration points.

### Example

```python
n_intervals = 5

write_sap2000_template_pack(
    field=field,
    show_plot=True,
    n_intervals=n_intervals,
    E_ref=210e9,
    nu=0.30,
    include_plot=False,
    plot_filename="out/lobatto_station_pack.jpg",
    template_filename="out/lobatto_station_pack.txt",
)
```

### Why this matters

This is more than a convenience feature.

It means that the continuous field can be sampled **where the numerical method actually integrates the member response**.

That provides three advantages:

1. **Consistency with the solver integration scheme**  
   The exported sections match the solver points instead of being post-processed from arbitrary stations.

2. **Direct use of the continuous definition**  
   You do not need to approximate the member first with a coarse set of manual sections.

3. **Traceability**  
   The exported section data remains directly connected to the original continuous model.

### Practical interpretation

Even if the function is named after SAP2000, the conceptual workflow is generic:

- choose a continuous CSF field,
- choose a solver-oriented set of stations,
- export sections at those stations,
- feed the resulting data into an external structural pipeline.

That is why this function is useful as a bridge from **continuous modeling** to **discrete numerical analysis**.

---

## 3. Obtaining Lobatto points explicitly

Sometimes you need the Lobatto points themselves, not only the exported section file.

For that, you can query them directly from the field.

### Example

```python
nlobattopoint = 5
zlobatto = field.get_lobatto_integration_points(n_points=nlobattopoint)

print(zlobatto)
```

### Why this is useful

This is especially convenient when you want to:

- inspect the actual sampling positions,
- reuse the same stations in multiple exports,
- export both section properties and explicit geometry at identical points,
- maintain exact alignment between several downstream files.

A common workflow is:

1. compute Lobatto stations once,
2. export section packs at those stations,
3. export polygon vertices at the same stations,
4. use both files together for solver input and verification.

---

## 4. Exporting explicit polygon geometry for multiple stations

CSF can export not only equivalent section properties, but also the explicit polygon geometry of the section at selected stations.

This is an important distinction.

Many tools export only reduced section properties such as:

- area,
- inertia,
- stiffness-related coefficients,
- torsional quantities.

CSF can go further and export the actual section geometry evaluated from the continuous field.

Use `export_polygon_vertices_csv_file(...)` for this purpose.

### Example: export geometry at Lobatto points

```python
from csf import export_polygon_vertices_csv_file

fmt=".9g"

nlobattopoint = 5
zlobatto = field.get_lobatto_integration_points(n_points=nlobattopoint)

export_polygon_vertices_csv_file(
    field=field,
    z_values=zlobatto,
    exp_filename="out/lobatto_station_export.txt",
    fmt=fmt,
)
```

### What this export provides

This export writes the polygon vertices of the section at each selected station.

That is useful when you need:

- a geometry audit trail,
- a file that can be inspected independently of the solver,
- reproducible section reconstruction at exported stations,
- interoperability with custom geometry-processing tools,
- external verification with third-party software.

### Why geometry export is valuable

This is where the continuous nature of CSF becomes especially powerful.

You are not limited to saying:

> “At this station, the area is X and the inertia is Y.”

You can also say:

> “At this station, this is the exact section geometry that produced those values.”

That makes debugging, verification, reporting, and solver interfacing much more robust.

---

## 5. Exporting explicit polygon geometry for one station

You can also export the geometry of a single section at a single `z` location.

### Example

```python
fmt = ".6f"
zpos = 15.0

export_polygon_vertices_csv_file(
    field=field,
    zpos=zpos,
    exp_filename="out/custom_station_export.txt",
    fmt=fmt,
)
```

### When this is useful

A single-station geometry export is convenient when:

- you want to inspect one intermediate section,
- you are debugging the interpolation,
- you need one reference section for documentation,
- you want to compare a CSF-generated section against an independent tool.

This is often the fastest way to verify that the continuous interpolation is behaving as expected at a chosen `z`.

---

## 6. Exporting geometry for OpenSees-style workflows

Another important export function is `write_opensees_geometry(...)`.

This function targets OpenSees-oriented workflows, but the broader point remains the same: CSF can export structured data representing the member geometry and its sampled sectional properties for solver use.

### Example

```python
from csf import write_opensees_geometry

z_stations = field.get_lobatto_integration_points(n_points=5)

write_opensees_geometry(
    field=field,
    z_values=z_stations,
    E_ref=210e9,
    nu=0.30,
    filename="out/geometry.tcl",
)
```

### Conceptual role

This export is useful when the downstream solver expects a geometry/material description in a structured file rather than a plain generic template pack.

Depending on the implementation details in your CSF version, such files may contain:

- section-related values at stations,
- member length metadata,
- explicit station coordinates,
- data prepared for line-by-line solver-side parsing.

### Why this matters

A robust export file should preserve the exact station positions used by CSF.

That avoids a common problem in solver pipelines:

- the preprocessor samples one set of stations,
- the solver silently regenerates a different set,
- the model no longer matches the intended section field.

The best practice is therefore:

- generate the stations in CSF,
- export them explicitly,
- let the solver consume those exact coordinates.

---

## 7. Recommended workflow patterns

Below are the most common export workflows.

### Workflow A — fixed custom stations

Use this when you already know the stations you want.

```python
z_stations = [10.0, 12.5, 15.0, 17.5, 20.0]

write_sap2000_template_pack(
    field=field,
    z_values=z_stations,
    show_plot=False,
    E_ref=210e9,
    nu=0.30,
    include_plot=False,
    plot_filename="out/custom_pack.jpg",
    template_filename="out/custom_pack.txt",
)
```

Use this pattern when the station list is driven by:

- a project requirement,
- a benchmark definition,
- a solver segmentation rule,
- a validation matrix.

### Workflow B — solver-oriented Lobatto sampling

Use this when you want the exported sections at integration points.

```python
write_sap2000_template_pack(
    field=field,
    n_intervals=5,
    show_plot=False,
    E_ref=210e9,
    nu=0.30,
    include_plot=False,
    plot_filename="out/lobatto_pack.jpg",
    template_filename="out/lobatto_pack.txt",
)
```

Use this pattern when your main goal is consistency with a beam integration scheme.

### Workflow C — property export plus geometry export at the same stations

This is often the most complete workflow.

```python
fmt = ".6f"
zlobatto = field.get_lobatto_integration_points(n_points=5)

write_sap2000_template_pack(
    field=field,
    z_values=zlobatto,
    show_plot=False,
    E_ref=210e9,
    nu=0.30,
    include_plot=False,
    plot_filename="out/lobatto_pack.jpg",
    template_filename="out/lobatto_pack.txt",
)

export_polygon_vertices_csv_file(
    field=field,
    z_values=zlobatto,
    exp_filename="out/lobatto_geometry.txt",
    fmt=fmt,
)
```

This pattern is strong because it gives you:

- solver-oriented sampled properties,
- the exact sampled geometry,
- a reproducible relation between the two.

### Workflow D — one intermediate section for debugging

```python
fmt = ".6f"

export_polygon_vertices_csv_file(
    field=field,
    zpos=15.0,
    exp_filename="out/section_z15.txt",
    fmt=fmt,
)
```

Use this when you want a quick geometry check without exporting the entire set of stations.

---

## 8. Choosing between `z_values` and automatic Lobatto sampling

A practical question is when to use explicit `z_values` and when to rely on internal Lobatto station generation.

### Use `z_values` when:

- you already know the exact coordinates,
- you need deterministic station lists shared across tools,
- you want one common sampling set for several exports,
- you are reproducing a benchmark or a published station layout.

### Use automatic Lobatto sampling when:

- you want a beam-integration-oriented export,
- you want the end points included naturally,
- you want the export sampling to follow a standard integration rule,
- you want a compact representation aligned with a solver formulation.

### Use both together when possible

A robust workflow is often:

1. compute Lobatto points explicitly,
2. store them in `zlobatto`,
3. reuse `zlobatto` across all exports.

That removes ambiguity and ensures that every exported file refers to the same stations.

```python
zlobatto = field.get_lobatto_integration_points(n_points=5)
```

Then use `zlobatto` everywhere.

---

## 9. Understanding the role of `E_ref` and `nu`

Several export functions require reference material values such as:

- `E_ref`
- `nu`

These values are needed when the exported output includes stiffness-related quantities or solver-oriented section data.

### Example

```python
E_ref = 210e9
nu = 0.30
```

### Practical note

Keep these values consistent with the constitutive interpretation expected by the downstream solver.

In many workflows, CSF already provides section quantities in a form meant to be consumed directly by the solver-side model. The export stage should therefore remain coherent with the reference material assumptions used for those quantities.

---

## 10. About file naming and output organization

Export workflows become easier to audit when outputs are clearly separated by purpose.

A practical convention is:

- `*_pack.txt` for section-property exports,
- `*_geometry.txt` for polygon-vertex exports,
- `*.tcl` for OpenSees-oriented files,
- optional plots in `*.jpg` or `*.png`.

### Example

```python
plot_filename="out/lobatto_station_pack.jpg"
template_filename="out/lobatto_station_pack.txt"
exp_filename="out/lobatto_station_export.txt"
filename="out/geometry.tcl"
```

This is not only cosmetic. Good file naming reduces ambiguity when one model generates multiple export artifacts.

---

## 11. Complete example

The following example combines the most useful export patterns in one script.

```python
from csf import (
    Pt,
    Polygon,
    Section,
    ContinuousSectionField,
    write_sap2000_template_pack,
    export_polygon_vertices_csv_file,
    write_opensees_geometry,
)

# Build the continuous section field.
poly0_start = Polygon(
    vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
    weight=1.0,
    name="flange",
)
poly1_start = Polygon(
    vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
    weight=1.0,
    name="web",
)
poly0_end = Polygon(
    vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
    weight=1.0,
    name="flange",
)
poly1_end = Polygon(
    vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
    weight=1.0,
    name="web",
)

s0 = Section(polygons=(poly0_start, poly1_start), z=10.0)
s1 = Section(polygons=(poly0_end, poly1_end), z=20.0)
field = ContinuousSectionField(section0=s0, section1=s1)

# Define common parameters.
fmt = ".6f"
E_ref = 210e9
nu = 0.30

# Export at fixed user stations.
z_stations = [10.0, 15.0, 20.0]
write_sap2000_template_pack(
    field=field,
    z_values=z_stations,
    show_plot=False,
    E_ref=E_ref,
    nu=nu,
    include_plot=False,
    plot_filename="out/custom_station_pack.jpg",
    template_filename="out/custom_station_pack.txt",
)

# Compute Lobatto stations once and reuse them.
zlobatto = field.get_lobatto_integration_points(n_points=5)

# Export solver-oriented section data at Lobatto points.
write_sap2000_template_pack(
    field=field,
    z_values=zlobatto,
    show_plot=False,
    E_ref=E_ref,
    nu=nu,
    include_plot=False,
    plot_filename="out/lobatto_station_pack.jpg",
    template_filename="out/lobatto_station_pack.txt",
)

# Export explicit polygon geometry at the same Lobatto points.
export_polygon_vertices_csv_file(
    field=field,
    z_values=zlobatto,
    exp_filename="out/lobatto_station_export.txt",
    fmt=fmt,
)

# Export one intermediate section for inspection.
export_polygon_vertices_csv_file(
    field=field,
    zpos=15.0,
    exp_filename="out/custom_station_export.txt",
    fmt=fmt,
)

# Export an OpenSees-oriented geometry file.
write_opensees_geometry(
    field=field,
    z_values=zlobatto,
    E_ref=E_ref,
    nu=nu,
    filename="out/geometry.tcl",
)
```

---

## 12. Best practices

### 1. Reuse one station list across multiple exports

If the workflow depends on a specific station set, compute it once and reuse it.

```python
zlobatto = field.get_lobatto_integration_points(n_points=5)
```

This avoids silent mismatches between property exports and geometry exports.

### 2. Export geometry when verification matters

Do not rely only on reduced section properties when you are validating a complex model. Exporting the explicit polygon vertices gives you a direct trace of what CSF actually sampled.

### 3. Keep exported stations solver-consistent

If the solver integrates at Gauss-Lobatto points, exporting arbitrary intermediate sections may be less meaningful than exporting exactly those integration points.

### 4. Prefer explicit output files for reproducibility

Store exported files under version control or in an organized output folder so the solver input can always be traced back to the CSF model.

### 5. Validate geometry upstream

The export layer assumes the field is valid. It should not be the first place where geometry consistency problems are discovered.

---

## 13. Common mistakes

### Undefined format string

If you use `fmt`, define it first.

```python
fmt = ".6f"
```

### Mixing different station sets accidentally

This is a common source of confusion:

- one file is exported at fixed stations,
- another file is exported at Lobatto points,
- later both are compared as if they referred to the same coordinates.

Avoid this by computing one common `z` list and reusing it.

### Treating the export as solver-specific only

Even if a function name references one solver, the exported logic may still be perfectly suitable for a generic pipeline.

The essential question is not the function name, but:

- what stations are sampled,
- what quantities are written,
- whether the downstream tool can consume those data.

---

## 14. Conceptual summary

The export layer of CSF is important because it turns a **continuous section description** into **explicit discrete artifacts** usable by numerical tools.

The main idea is simple:

- CSF models the section continuously along `z`,
- export functions sample that field where needed,
- the sampled data can include both section properties and explicit geometry,
- Gauss-Lobatto sampling lets the export match solver integration points directly.

This is why the export functionality is not just a utility feature. It is a central part of how CSF connects geometric continuity with practical solver workflows.

In short:

- `write_sap2000_template_pack(...)` is useful as a generic section export mechanism,
- `field.get_lobatto_integration_points(...)` gives solver-relevant stations,
- `export_polygon_vertices_csv_file(...)` exposes the actual sampled geometry,
- `write_opensees_geometry(...)` supports structured solver-oriented exports.

Together, these functions let CSF exploit the full value of the continuous field instead of reducing it prematurely to a few manually chosen discrete sections.


Full source code
```python

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Dict, Optional, List
import math
import random
import warnings
import numpy as np
import matplotlib.pyplot as plt

# Importing core CSF (Continuous Section Field) components for structural analysis
from csf import (
    Pt, Polygon, Section, ContinuousSectionField,
    section_properties, section_full_analysis,
    Visualizer,
    section_statical_moment_partial, section_stiffness_matrix,
    polygon_inertia_about_origin,
    polygon_statical_moment,
    compute_saint_venant_Jv2,
    section_print_analysis,
    write_opensees_geometry,
    write_sap2000_template_pack,
    export_polygon_vertices_csv_file
)


if __name__ == "__main__":
    # ----------------------------------------------------------------------------------
    # 1. DEFINE START SECTION (Z = 10)
    # ----------------------------------------------------------------------------------
    # The start section is defined at z = 10.0.
    # Each polygon must be defined with vertices in CCW order so that
    # geometric quantities derived from Green's theorem keep the correct sign.
    # A positive weight represents solid material.
    # ----------------------------------------------------------------------------------

    # Flange polygon at the start section.
    # This is a horizontal rectangle centered on the x-axis.
    poly0_start = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )

    # Web polygon at the start section.
    # This is the vertical part below the flange, forming a T-like section.
    poly1_start = Polygon(
        vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0),  Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )

    # ----------------------------------------------------------------------------------
    # 2. DEFINE END SECTION (Z = 20)
    # ----------------------------------------------------------------------------------
    # The end section is defined at z = 20.0.
    # The same polygon layout is preserved so that CSF can interpolate
    # polygon-by-polygon from the start section to the end section.
    # In this example, the flange remains unchanged while the web becomes deeper.
    # ----------------------------------------------------------------------------------

    # Flange polygon at the end section.
    # Geometry is unchanged with respect to the start section.
    poly0_end = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )

    # Web polygon at the end section.
    # The lower edge moves from y = -1.0 to y = -2.5, creating a tapered member.
    poly1_end = Polygon(
        vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )

    # ----------------------------------------------------------------------------------
    # 3. CREATE SECTIONS WITH Z-COORDINATES
    # ----------------------------------------------------------------------------------
    # The two discrete sections are assembled with their corresponding z positions.
    # These are the boundary sections used by the continuous field.
    # ----------------------------------------------------------------------------------
    s0 = Section(polygons=(poly0_start, poly1_start), z=10.0)
    s1 = Section(polygons=(poly0_end, poly1_end), z=20.0)

    # ----------------------------------------------------------------------------------
    # 4. INITIALIZE CONTINUOUS SECTION FIELD (CSF)
    # ----------------------------------------------------------------------------------
    # The continuous field interpolates the section geometry between s0 and s1
    # along the member axis z.
    # ----------------------------------------------------------------------------------
    field = ContinuousSectionField(section0=s0, section1=s1)

    # ----------------------------------------------------------------------------------
    # 5. EXPORT USING USER-DEFINED STATIONS
    # ----------------------------------------------------------------------------------
    # The first export uses explicitly selected stations.
    # Here only the two boundary sections are exported: z = 10 and z = 20.
    # Although the function name refers to SAP2000, the exported section pack
    # can conceptually serve as data for a generic solver workflow.
    # ----------------------------------------------------------------------------------
    z_stations = [10, 20]  # fixed stations chosen by the user

    # Export template pack at custom stations.
    write_sap2000_template_pack(
        field=field,
        z_values=z_stations,
        show_plot=False,
        E_ref=210e9,
        nu=0.30,
        include_plot=False,
        plot_filename="out/cust_station_pack.jpg",
        template_filename="out/cust_station_pack.txt",
    )

    # ----------------------------------------------------------------------------------
    # 6. EXPORT USING LOBATTO STATIONS
    # ----------------------------------------------------------------------------------
    # The second export lets the routine generate stations according to
    # a Lobatto distribution with 5 intervals/points as configured here.
    # This is useful because CSF can sample the continuous section field
    # directly at integration points meaningful for beam/frame solvers.
    # ----------------------------------------------------------------------------------
    n_intervals = 5

    write_sap2000_template_pack(
        field=field,
        show_plot=True,
        n_intervals=n_intervals,
        E_ref=210e9,
        nu=0.30,
        include_plot=False,
        plot_filename="out/lobatto_station_pack.jpg",
        template_filename="out/lobatto_station_pack.txt",
    )

    # ----------------------------------------------------------------------------------
    # 7. GET LOBATTO POINTS EXPLICITLY AND EXPORT GEOMETRY
    # ----------------------------------------------------------------------------------
    # Here the Lobatto integration points are requested explicitly from the field.
    # These z-coordinates are then used to export the polygon vertices of each
    # corresponding section into a CSV-like text file.
    # This makes it possible to export not only equivalent properties,
    # but also the actual section geometry at solver-relevant stations.
    # ----------------------------------------------------------------------------------
    nlobattopoint = 5
    zlobatto = field.get_lobatto_integration_points(n_points=nlobattopoint)
    fmt=".9g"
    export_polygon_vertices_csv_file(
        field=field,
        z_values=zlobatto,
        exp_filename="out/lobatto_station_export.txt",
        fmt=fmt,
    )

    # ----------------------------------------------------------------------------------
    # 8. EXPORT A SINGLE SECTION GEOMETRY AT A CUSTOM POSITION
    # ----------------------------------------------------------------------------------
    # This final export writes the polygon vertices for one section only,
    # evaluated at z = 15, i.e. an intermediate position inside the field.
    # ----------------------------------------------------------------------------------
    zpos = 15
    export_polygon_vertices_csv_file(
        field=field,
        zpos=zpos,
        exp_filename="out/cust_station_export.txt",
        fmt=fmt,
    )
```
