# CSF User Guide: Modeling and Sectional Analysis

This guide explains how to use **Continuous Section Field (CSF)** to model structural members with variable cross-sections. CSF uses a "start-to-end" interpolation logic based on ruled surfaces.

## 1. Core Logic: The "Anchor" Sections
The library works by defining two anchor sections at different longitudinal coordinates ($Z$):
1. **Start Section** ($Z_{start}$)
2. **End Section** ($Z_{end}$)

The engine automatically calculates all intermediate geometric and structural properties through linear interpolation of the vertices.

---

## 2. Step-by-Step Construction

### Step 1: Define Polygons
A section is made of one or more polygons. 

> [!IMPORTANT]
> **The CCW Rule:** You **must** define vertices in **Counter-Clockwise (CCW)** order. This is mandatory for the internal algorithm to compute positive Area and correct Moments of Inertia.


```python
from csf.core import Pt, Polygon

# Define a simple rectangular flange for the start section
poly_flange_start = Polygon(
    vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
    weight=1.0,   # 1.0 = solid, -1.0 = hole (void)
    name="flange" # Name must be consistent for interpolation
)
```

Step 2: Define the End Section (Tapering)

To create a tapered member (where the section grows or shrinks along the Z axis), you must define the polygons for the end coordinate.

Geometric Consistency Rule:

    The end section must have the same number of polygons as the start section.

    Polygons must share the same names as those in the start section to be correctly linked for interpolation.

```# The web grows from depth 1.0 (at Z=0) to 2.5 (at Z=10)
# We define poly_web_end with the same name "web" but different coordinates
poly_web_end = Polygon(
    vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
    weight=1.0,
    name="web"
)
```

Step 3: Create the Section Containers

Group your polygons into Section objects and assign them a position along the longitudinal axis (Z).


```python
from csf.core import Section

# All polygons grouped at Z=0.0
s0 = Section(polygons=(poly_flange_start, poly_web_start), z=0.0)

# All polygons grouped at Z=10.0
s1 = Section(polygons=(poly_flange_end, poly_web_end), z=10.0)
```
3. Structural Properties & Torsion

Once initialized, you can extract properties for any point Z. For torsional rigidity (J), the library uses the following semi-empirical estimation:

4. Summary of Constraints
Feature	Requirement
Vertex Order	Must be Counter-Clockwise (CCW).
Holes/Voids	Use weight=-1.0.
Tapering	Polygon name must match between Start and End sections.
Coordinate System	Local X,Y for the section; Z for the longitudinal axis.

## 3. Calculating Sectional & Volumetric Properties

Once the `ContinuousSectionField` is initialized, you can extract structural data at any longitudinal coordinate ($Z$).

### Step 5: Querying Properties at a Specific Point
You can retrieve a section at any point (e.g., mid-span at $Z=5.0$) to compute its primary and derived geometric properties.

```python
# 1. Retrieve the interpolated section at Z = 5.0
sec_mid = field.section(5.0)

# 2. Compute Primary Properties (Centroidal)
props = section_properties(sec_mid)

print(f"A:   {props['A']:.4f}      # Net Cross-Sectional Area")
print(f"Cx:  {props['Cx']:.4f}     # Horizontal Centroid (Global X)")
print(f"Cy:  {props['Cy']:.4f}     # Vertical Centroid (Global Y)")
print(f"Ix:  {props['Ix']:.4f}     # Moment of Inertia (Centroidal X)")
print(f"Iy:  {props['Iy']:.4f}     # Moment of Inertia (Centroidal Y)")
print(f"J:   {props['J']:.4f}      # Torsional Rigidity Estimate")
```
