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

Step 2: Define the Star Section (Tapering)

To create a tapered member (where the section grows or shrinks along the Z axis), you must define the polygons for the end coordinate.

Geometric Consistency Rule:
The end section must have the same number of polygons as the start section.
Polygons must share the same names as those in the start section to be correctly linked for interpolation.

```python
    # Flange Definition: Rectangle from (-1, -0.2) to (1, 0.2)
    # Order: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left (CCW)
    poly0_start = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )

    # Web Definition: Rectangle from (-0.2, -1.0) to (0.2, 0.2)
    # Order: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left (CCW)
    poly1_start = Polygon(
        vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0),  Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    
```

Step 2: Define the End Section (Tapering)
```python

    # ----------------------------------------------------------------------------------
    # 2. DEFINE END SECTION (Z = 10)
    # ----------------------------------------------------------------------------------
    # GEOMETRIC CONSISTENCY:
    # - To enable linear interpolation (tapering), the end section must contain the 
    #   same number of polygons with the same names as the start section.
    # - The web depth here increases linearly from 1.0 down to 2.5 (negative Y direction),
    #   creating a tapered profile along the longitudinal Z-axis.
    # ----------------------------------------------------------------------------------

    # Flange remains unchanged for this prismatic top part
    poly0_end = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    # Web becomes deeper: Y-bottom moves from -1.0 to -2.5
    # MAINTAIN CCW ORDER: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left
    poly1_end = Polygon(
        vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )
```

Step 3: Create the Section Containers

Group your polygons into Section objects and assign them a position along the longitudinal axis (Z).


```python
    # ----------------------------------------------------------------------------------
    # 3. CREATE SECTIONS WITH Z-COORDINATES
    # ----------------------------------------------------------------------------------
    # Sections act as containers for polygons at a specific coordinate along the beam axis.
    # All polygons defined at Z=0.0 are grouped into s0, and those at Z=10.0 into s1.
    # ----------------------------------------------------------------------------------

    s0 = Section(polygons=(poly0_start, poly1_start), z=0.0)
    s1 = Section(polygons=(poly0_end, poly1_end), z=10.0)
```
```python
    # ----------------------------------------------------------------------------------
    # 4. INITIALIZE CONTINUOUS SECTION FIELD (CSF)
    # ----------------------------------------------------------------------------------
    # The 'field' object manages the mathematical mapping between s0 and s1.
    # It allows the retrieval of section properties at any arbitrary Z-coordinate
    # (e.g., field.section(5.33)) via linear interpolation of vertex coordinates.
    # ----------------------------------------------------------------------------------
    field = ContinuousSectionField(section0=s0, section1=s1)
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

Step 6: Derived Properties & Shear Analysis

The library also computes advanced engineering properties such as principal moments and statical moments of area (Q) for shear stress analysis.

```python
# Compute Principal Axes and Radii of Gyration
derived = section_derived_properties(props)
print(f"I1:  {derived['I1']:.4f}     # Max Principal Moment")
print(f"Deg: {derived['theta_deg']:.2f}°   # Rotation Angle")

# Compute Statical Moment (Q) at the Neutral Axis (y = Cy)
Q_na = section_statical_moment_partial(sec_mid, y_cut=props['Cy'])
```

Step 7: Volumetric Integration (3D)

Since CSF treats the member as a 3D ruled solid, it can integrate the area along the Z axis to find the total volume of the component.

```python
total_vol = integrate_volume(field)
print(f"Total Volume: {total_vol:.4f}")
```

4. Technical Note on Coordinate Systems

When analyzing results , you might encounter negative values for the centroid (Cy​).

This is physically correct: If your polygons (like the web of a T-section) extend mostly below the global origin (y=0), the centroid must result in a negative Y coordinate. This indicates that the geometric center of mass is located below your drawing's reference origin.
Property	Description
Cx, Cy	Centroid coordinates relative to the global origin.
I1, I2	Principal moments of area.
Q_na	Statical moment above the neutral axis (for τ=VQ/It)
