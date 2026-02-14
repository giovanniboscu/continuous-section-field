# 01 — Geometry Model
## First API Example — Build a Simple Shape and Print Section Results

This example shows three core steps:

1. create points/polygons with the API,  
2. instantiate a `ContinuousSectionField`,  
3. run and print section analysis at one `z` station.

### Python script 

wite the file t-shape.py

```python
from __future__ import annotations

# --- Core CSF imports used in this minimal example ---
from csf import (
    Pt, Polygon, Section, ContinuousSectionField,
    section_full_analysis, section_print_analysis
)

# -------------------------------------------------------
# 1) Geometry definition with API objects
# -------------------------------------------------------
# We build a simple section from two rectangles:
# - upperpart
# - lowerpart
# Then we define start section (S0) and end section (S1).

if __name__ == "__main__":
    # Optional file name placeholder (not used in this snippet)
    geometryfile = "geometry.tcl"

    # Geometric parameters
    h = 1.20
    hb = 0.40
    b = 0.30

    # --- S0 polygons (z = 0.0) ---
    poly_top_start = Polygon(
        vertices=(
            Pt(-b/2,  0.0),
            Pt( b/2,  0.0),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1.0,
        name="upperpart",
    )

    poly_bottom_start = Polygon(
        vertices=(
            Pt(-b/2, -h/2),
            Pt( b/2, -h/2),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1.0,
        name="lowerpart",
    )

    # --- S1 polygons (z = L) ---
    # upperpart unchanged, lowerpart modified (different depth)
    poly_top_end = Polygon(
        vertices=(
            Pt(-b/2,  0.0),
            Pt( b/2,  0.0),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1.0,
        name="upperpart",
    )

    poly_bottom_end = Polygon(
        vertices=(
            Pt(-b/2, -hb/4),
            Pt( b/2, -hb/4),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1.0,
        name="lowerpart",
    )

    # -------------------------------------------------------
    # 2) Section field instantiation
    # -------------------------------------------------------
    # Define start/end sections and create the continuous field.
    L = 10.0

    s0 = Section(polygons=(poly_bottom_start, poly_top_start), z=0.0)
    s1 = Section(polygons=(poly_bottom_end,   poly_top_end),   z=L)

    section_field = ContinuousSectionField(section0=s0, section1=s1)

    # -------------------------------------------------------
    # 3) Extract one section and print full analysis
    # -------------------------------------------------------
    # Here z = 10.0, so this is exactly the end section (S1).
    zsec_val = 10.0
    sec_at_z = section_field.section(zsec_val)

    full_analysis = section_full_analysis(sec_at_z)
    section_print_analysis(full_analysis, fmt=".5f")
```
Run the script first:

```bash
python3 t-shape.py
```

CSF will output 

```
=================================================================================================================================
FULL MODEL ANALYSIS REPORT - SECTION EVALUATION
#  Name                              Key
==================================================================================================================================
1) Area (A):                          A                     0.21000     # Total Homogenized area
2) Centroid Cx:                       Cx                    0.00000     # Horizontal geometric centroid (X-axis locus)
3) Centroid Cy:                       Cy                    0.25000     # Vertical geometric centroid (Y-axis locus)
4) Inertia Ix:                        Ix                    0.00857     # Second moment of area about the centroidal X-axis
5) Inertia Iy:                        Iy                    0.00157     # Second moment of area about the centroidal Y-axis
6) Inertia Ixy:                       Ixy                   0.00000     # Product of inertia (indicates axis symmetry)
7) Polar Moment (J):                  J                     0.01015     # Polar second moment of area (sum of Ix and Iy)
8) Principal Inertia I1:              I1                    0.00857     # Major principal second moment of area
9) Principal Inertia I2:              I2                    0.00158     # Minor principal second moment of area
10) Radius of Gyration rx:            rx                    0.20207     # Radii of gyration relative to the X-axis
11) Radius of Gyration ry:            ry                    0.08660     # Radii of gyration relative to the Y-axis
12) Elastic Modulus Wx:               Wx                    0.02450     # Elastic section modulus (flexural strength about X)
13) Elastic Modulus Wy:               Wy                    0.01050     # Elastic section modulus (flexural strength about Y)
14) Torsional Rigidity K:             K_torsion             0.00479     # Semi-empirical torsional stiffness approximation
15) First_moment:                     Q_na                  0.01838     # First moment of area at NA (governs shear capacity)
16) Torsional const K:                J_sv                  0.01015     # alpha = 1.00000 Effective St. Venant torsional constant (J)
16) Torsional const K cell            J_sv_cell             0.00000     # Saint-Venant torsional constant for closed thin-walled by applying  Bredt–Batho formula
16) Torsional const K wall            J_sv_wall             0.00000     # computes the Saint-Venant torsional constant for open thin-walled walls
17) Torsional const K roark:          J_s_vroark            0.00460     # Refined J using Roark-Young thickness correction
18) Torsional const K roark fidelity: J_s_vroark_fidelity   0.42857     # Reliability index based on aspect-ratio (1.0 = Thin-walled, 0.0 = Stout
==================================================================================================================================
```


> **Note on `J_sv = 0.01015` (with `alpha = 1`)**
>
> In this run, `J_sv` is the torsional value produced by the **global/default CSF torsion path** for the current section state.
>
> With `alpha = 1`, no extra scaling is applied, so `J_sv` is reported directly as computed by that baseline model.
>
> This value is **not** coming from thin-walled specialized paths:
> - `J_sv_cell = 0.00000` → no active/valid `@cell` contribution in this section
> - `J_sv_wall = 0.00000` → no active/valid `@wall` contribution in this section
>
> Therefore, `J_sv = 0.01015` should be interpreted as the reference torsional constant for this specific configuration and solver path.

