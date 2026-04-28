# 01 - Geometry Model

## First API Example - Build a Simple Shape and Print Section Results

This example is organized into three essential steps:

1. Create points and polygons through the API  
2. Instantiate a `ContinuousSectionField`  
3. Run the section analysis at one `z` station and print the results

---

## Python script

Create the file `t-shape.py`:

```python
# --- Core CSF imports used in this minimal example ---
from csf import (
    Pt, Polygon, Section, ContinuousSectionField,
    section_full_analysis, section_print_analysis,section_full_analysis_keys
)
from csf.io.csf_reader import CSFReader

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
    # Section field instantiation
    # -------------------------------------------------------
    # Define start/end sections and create the continuous field.
    L = 10.0

    # Order matters: poly_bottom_start pairs with poly_bottom_end,
    # and poly_top_start pairs with poly_top_end,
    # because they appear in the same position in their respective sections.


    s0 = Section(polygons=(poly_bottom_start, poly_top_start), z=0.0)
    s1 = Section(polygons=(poly_bottom_end,   poly_top_end),   z=L)

    section_field = ContinuousSectionField(section0=s0, section1=s1)

    # -------------------------------------------------------
    # Extract one section and print 
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

---

## Expected CSF output (example)

```text
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
7) Polar Moment                       Ip                    0.01015     # Polar second moment of area (sum of Ix and Iy)
8) Principal Inertia I1:              I1                    0.00857     # Major principal second moment of area
9) Principal Inertia I2:              I2                    0.00158     # Minor principal second moment of area
10) Radius of Gyration rx:            rx                    0.20207     # Radii of gyration relative to the X-axis
11) Radius of Gyration ry:            ry                    0.08660     # Radii of gyration relative to the Y-axis
12) Elastic Modulus Wx:               Wx                    0.02450     # Elastic section modulus (flexural strength about X)
13) Elastic Modulus Wy:               Wy                    0.01050     # Elastic section modulus (flexural strength about Y)
14) Torsional Rigidity K:             K_torsion             0.00479     # Semi-empirical torsional stiffness approximation
15) First_moment:                     Q_na                  0.01838     # First moment of area at NA (governs shear capacity)
16) Torsional const K cell            J_sv_cell             0.00000     # Saint-Venant torsional constant for closed thin-walled by applying Bredt–Batho formula
16) Torsional const K wall            J_sv_wall             0.00000     # computes the Saint-Venant torsional constant for open thin-walled walls
17) Torsional const K roark:          J_s_vroark            0.00460     # Roark torsional indicator (equivalent-rectangle mapping)
18) Torsional const K roark fidelity: J_s_vroark_fidelity   0.42857     # Reliability index based on aspect-ratio (1.0 = Thin-walled, 0.0 = Stout)
==================================================================================================================================
```

---

## Read Available Analysis Keys and Print Only Area

Use `section_full_analysis_keys()` to list all available output keys, then read only the area from the full-analysis dictionary.

```python

# Print all available keys (ordered)
keys = section_full_analysis_keys()
print("Available keys:")
for k in keys:
    print(f"- {k}")

# Run full analysis (example: section object at z)
# If you already have a section object (e.g., sec_at_z), use:
full_analysis = section_full_analysis(sec_at_z)

#  Print only area
print(f"Area: {full_analysis['A']}")
```

Output

```python
Available keys:
- A
- Cx
- Cy
- Ix
- Iy
- Ixy
- Ip
- I1
- I2
- rx
- ry
- Wx
- Wy
- K_torsion
- Q_na
- J_sv_wall
- J_sv_cell
- J_s_vroark
- J_s_vroark_fidelity

Area: 0.21
```

snipped for specifid keys

```cpython
    # Print all keys in official order
    print("\nFull analysis results:")

    for csfkey in keys:
      value = full_analysis.get(csfkey, None)
      print(f"{csfkey}: {value}")

    # Select keys once, print in one loop
    selected_keys = ["J", "Ix"]
    print("\nPrint from the list")
    for csfkey in selected_keys:
      print(f"{csfkey}: {full_analysis[csfkey]}")
```  

output
```

Full analysis results:
A: 0.21
Cx: 0
Cy: 0.25
Ix: 0.008574999999999998
Iy: 0.0015749999999999998
Ixy: 0
J: 0.010149999999999998
I1: 0.008574999999999998
I2: 0.001575
rx: 0.202072594216369
ry: 0.08660254037844387
Wx: 0.024499999999999994
Wy: 0.010499999999999999
K_torsion: 0.004790172413793104
Q_na: 0.018375000000000013
J_sv_wall: 0.0
J_sv_cell: 0.0
J_s_vroark: 0.004603782069970846
J_s_vroark_fidelity: 0.4285714285714287


Ix: 0.008574999999999998

```
---

## Same API Pipeline, YAML-Loaded Model

This final example shows that only the data source changes.  
Once the model is loaded, the API workflow is exactly the same as in previous examples.

```python

# Load CSF model from YAML
res = CSFReader().read_file("../actions-examples/openandthin/ipe100.yaml")
field = res.field

# Same API flow as before
sec = field.section(2.5)
out = section_full_analysis(sec)

print(f"A: {out['A']}")
```
---
## Same API Pipeline, YAML-Loaded Model

This example shows that only the data source changes.  
Once the CSF model is loaded from YAML, the API workflow remains the same.

Here `A` is printed only as a simple example of a standard sectional property.

```python
# Load CSF model from YAML
res = CSFReader().read_file("../actions-examples/openandthin/ipe100.yaml")
field = res.field

# Same API flow as before
sec = field.section(2.5)
out = section_full_analysis(sec)

print(f"A: {out['A']}")
```

## Special case: `@cell` and `@wall`

The only special case is the Saint-Venant torsional result for single-polygon sections tagged as `@cell` or `@wall`.

In that case, the returned result is not just a single scalar:
it contains two values:

1. `J_sv_cell` or `J_sv_wall`
2. `t`

So the output is conceptually:

```python
(J_sv_cell, t)
```

or

```python
(J_sv_wall, t)
```


## Example

This example loads a CSF YAML file, validates it through `CSFReader`, extracts the section at `z = 10.0`, and runs the full section analysis.

The file `boxcell.yaml` is expected to contain a section with a polygon tagged as `@cell`. If the YAML file has syntax errors, missing fields, invalid polygon data, or invalid weight laws, the reader reports the issue before any analysis is executed.

```python
from csf import section_full_analysis
from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues

res = CSFReader().read_file("boxcell.yaml")

if not res.ok:
    print(CSFIssues.format_report(res.issues))
    raise SystemExit(1)

print("OK")

field = res.field

sec = field.section(10.0)
out = section_full_analysis(sec)

# Standard property example
print(f"A: {out['A']}")

# Special torsional case:
# returned values are:
#   first  -> J_sv_cell
#   second -> t
j_sv, t = out["J_sv_cell"]

print(f"J_sv: {j_sv}")
print(f"t: {t}")
```

The `if not res.ok:` block is essential: it prevents the code from using `res.field` when the YAML model has not been loaded correctly.
---

From this point, all action-style workflows can be reproduced programmatically.
