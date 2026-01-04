# CSF User Guide — Modeling and Sectional Analysis

Continuous Section Field (CSF) models structural members whose cross-section **varies along the longitudinal axis `Z`.
CSF is built around a simple idea:

- you define the cross-section at **two known stations** along `Z`
- CSF generates any intermediate section by **linearly interpolating polygon vertices**
- from the interpolated section, you can compute **geometric and structural properties** (area, centroid, inertia, etc.)

---

## Core Concept — Anchor Sections

CSF needs two *anchor* sections:

- **Start Section** at `Z_start`
- **End Section** at `Z_end`

These two sections act as boundary conditions. Every section at an intermediate coordinate `Z` is obtained by interpolating between them.

> Think of CSF as a *continuous mapping* from `Z` → `Section`.

---

## What “interpolation” means in practice

A section is defined by one or more **named polygons** (e.g., `"flange"`, `"web"`).  
For a given polygon name, CSF matches the polygon at `Z_start` with the polygon at `Z_end` and interpolates:

- vertex coordinates `(x, y)` **point-by-point**
- producing a new polygon at the requested `Z`

This is equivalent to generating a ruled surface between corresponding polygon edges along the member length.

---

## Minimum requirements to use CSF correctly

To ensure the start/end sections can be interpolated:

- The start and end sections must contain the **same set of polygons**
- Matching polygons must have the **same number of vertices**
- Vertex ordering must be **consistent** (same CCW walk and same starting vertex)

If these constraints are not respected, interpolation may fail or produce distorted geometry.

---

## What CSF gives you

Once the field is defined, you can:
- retrieve a section at any coordinate: `field.section(Z)`
- compute section properties on that slice (area, centroid, inertias, principal axes, etc.)
- sample the member along `Z` for analysis, export, or visualization

---

## Step-by-Step Construction

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

Define the Start Section (Tapering)

To create a tapered member (where the section grows or shrinks along the Z axis), you must define the polygons for the end coordinate.

Geometric Consistency Rule:
The end section must have the same number of polygons as the start section.


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

Define the End Section (Tapering)
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


## Step 2 — Create the Section Containers

In CSF, a `Section` is a **container** that groups the polygons defining the cross-section at a specific longitudinal coordinate `z`.

You will typically build two sections:

- `section0` at `Z_start`
- `section1` at `Z_end`

These are the **anchor sections** used by `ContinuousSectionField` to interpolate any intermediate section.

---

### What a `Section` contains

A `Section` is defined by:

- `polygons`: a tuple/list of `Polygon` objects describing the cross-section at that station
- `z`: the longitudinal coordinate where that cross-section is defined

```python
s0 = Section(polygons=(poly0_start, poly1_start), z=0.0)
s1 = Section(polygons=(poly0_end,   poly1_end),   z=10.0)
```





## `ContinuousSectionField`

`ContinuousSectionField` is the core CSF object that turns two **anchor sections** into a **continuous cross-section definition** along the member axis `Z`.

It acts as a geometric mapping:
`Z  ->  Section(Z)`

where `Section(Z)` is generated by interpolating the geometry of the anchor sections.

---

### What it does

Given:

- `section0` defined at `z0`
- `section1` defined at `z1`

the field can generate an intermediate section at any coordinate `z` by **linearly interpolating polygon vertices** between the two anchors.

This is especially useful for:

- tapered beams / haunched girders
- members with variable plate thickness or depth (modeled by changing polygon geometry)
- sampling properties along `Z` for analysis/export (OpenSees, custom FE, plotting)

---

### Inputs

#### Anchor sections
`ContinuousSectionField(section0, section1)` expects:

- `section0`: a `Section` object containing polygons at `z = z0`
- `section1`: a `Section` object containing polygons at `z = z1`

Each `Section` is a container:

- `Section.polygons`: tuple/list of `Polygon`
- `Section.z`: longitudinal coordinate of that cross-section station

The resulting vertices form a new interpolated `Polygon`, and all interpolated polygons are grouped into a new `Section(z)`.

> Conceptually, this generates **ruled surfaces** between corresponding polygon edges along the member length.


Example:

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

## Step 3 — Section properties as a function of `Z`



Once the `ContinuousSectionField` is created, the cross-section becomes a **function of the longitudinal coordinate**:

- `Section(Z)` is obtained by interpolating polygon vertices between the two anchor sections.
- Any geometric/structural property you compute from that section is therefore also a **function of `Z`**:
  - `A(Z), Cx(Z), Cy(Z), Ix(Z), Iy(Z), ...`

In practice, the workflow is always:

1. **Choose a coordinate** `Z`
2. **Generate the section slice** at that coordinate  
   `sec = field.section(Z)`
3. **Compute properties** from that slice  
   `props = section_properties(sec)` *(basic)* or `full = section_full_analysis(sec)` *(extended)*

---

### What can be evaluated at any `Z`

#### A) Basic section properties (`section_properties`)
Use this when you only need core geometric values (fast).

Typical outputs include:
- `A` — net area (holes subtract area)
- `Cx`, `Cy` — centroid coordinates (neutral axis location)
- `Ix`, `Iy` — centroidal second moments of area about global axes
- `Ixy` — centroidal product of inertia

> Tip: if you are unsure about what the function returns in your version, print:
> `print(props.keys())`

#### B) Extended analysis (`section_full_analysis`)
Use this when you need a complete report (includes derived and torsional quantities).

The example below prints these keys (all evaluated at the requested `Z`):

1. **Primary integrated geometric properties**
- `A` — net area  
- `Cx`, `Cy` — centroid coordinates  
- `Ix`, `Iy` — centroidal second moments of area  
- `Ixy` — centroidal product of inertia  
- `J` — **polar second moment about the centroidal axes** (by definition `J = Ix + Iy`)  
  > Note: `J` is a geometric polar moment, **not** the Saint-Venant torsional constant for non-circular sections.

2. **Principal properties**
- `I1`, `I2` — principal second moments (`I1 ≥ I2`)  
  (principal axes are the orientation where the product of inertia is zero)
- `rx`, `ry` — radii of gyration  
  `rx = sqrt(Ix / A)`, `ry = sqrt(Iy / A)`

3. **Strength and torsion**
- `Wx`, `Wy` — elastic section moduli (used for bending stress `σ = M / W`)  
  Typically computed as:
  - `Wx = Ix / y_max`
  - `Wy = Iy / x_max`  
  where `x_max`, `y_max` are the extreme distances from centroid to the furthest fiber.
- `K_torsion` — Saint-Venant torsional constant (used for torsional stiffness)

> Tip: to see every available quantity in your build:
> `print(sorted(full_analysis.keys()))`

---

### Verification utilities (optional, but useful for debugging)

These functions are helpful to cross-check results on a single interpolated slice:

- `polygon_inertia_about_origin(poly)`  
  returns polygon inertia terms about the **global origin** (not centroidal)
- `polygon_statical_moment(poly, y_axis=...)`  
  returns first moment (useful for shear flow checks)
- `section_statical_moment_partial(sec, y_cut=...)`  
  returns first moment of the portion above/below a cut line (e.g., at the neutral axis)

---

### Stiffness quantities (require material input)

`section_stiffness_matrix(sec, E_ref=...)` computes stiffness terms that depend on the reference modulus `E_ref`.

- Output is a matrix (commonly containing terms like `EA`, `EIx`, `EIy` depending on the chosen formulation).
- **Unit consistency is mandatory**:
  - If `Pt(x, y)` is in **mm** → use `E_ref` in **N/mm² (MPa)**
  - If `Pt(x, y)` is in **m**  → use `E_ref` in **N/m² (Pa)**

---

### Sampling along `Z` (turn “properties at one Z” into “properties vs Z”)

To study how properties vary along the member, evaluate at multiple stations:

- use element **centers** for beam discretizations (recommended), or
- use a uniform grid of `Z` points for plotting/reporting.

Minimal pattern:


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
### Step  3. Structural Properties & Torsion



Once initialized, you can extract properties for any point Z. For torsional rigidity (J), the library uses the following 

```python

    # ----------------------------------------------------------------------------------
    # 5. PRIMARY SECTION PROPERTIES (EVALUATED AT Z = 5.0)
    # ----------------------------------------------------------------------------------
    # Generating an intermediate section exactly at mid-span.
    sec_mid = field.section(5.0)
    props = section_properties(sec_mid)

    # ==================================================================================
    # COMPLETE MODEL CAPABILITIES VERIFICATION (18 POINTS)
    # ==================================================================================
    # This block verifies the cross-validation between the library's outputs and 
    # analytical expectations. 
    # IMPORTANT: Principal Moments (I1, I2) will reveal the "true" stiffness even
    # if the section were rotated, while Ixy monitors the axis coupling.
    # ==================================================================================
    print("\n" + "="*60)
    print("FULL MODEL ANALYSIS REPORT - SECTION AT Z=10.0")
    print("="*60)

    # Run full integrated analysis including Saint-Venant torsional constants
    full_analysis = section_full_analysis(sec_mid)
    
    # 1-7) Primary Integrated Geometric Properties
    # Area must be positive (CCW vertex check). Centroids define the Neutral Axis.
    print(f"1) Area (A):               {full_analysis['A']:.4f}      # Net area")
    print(f"2) Centroid Cx:            {full_analysis['Cx']:.4f}     # Horizontal CG")
    print(f"3) Centroid Cy:            {full_analysis['Cy']:.4f}     # Vertical CG")
    print(f"4) Inertia Ix:             {full_analysis['Ix']:.4f}     # Centroidal X Inertia")
    print(f"5) Inertia Iy:             {full_analysis['Iy']:.4f}     # Centroidal Y Inertia")
    print(f"6) Inertia Ixy:            {full_analysis['Ixy']:.4f}    # Product of Inertia")
    print(f"7) Polar Moment (J):       {full_analysis['J']:.4f}      # Ix + Iy")

    # 8-11) Derived Principal Properties
    # Principal axes represent the orientation where Ixy is zero.
    print(f"8) Principal Inertia I1:   {full_analysis['I1']:.4f}     # Max Principal Moment")
    print(f"9) Principal Inertia I2:   {full_analysis['I2']:.4f}     # Min Principal Moment")
    print(f"10) Radius of Gyration rx: {full_analysis['rx']:.4f}     # sqrt(Ix/A)")
    print(f"11) Radius of Gyration ry: {full_analysis['ry']:.4f}     # sqrt(Iy/A)")

    # 12-14) Strength and Torsion
    # Wx and Wy are critical for stress calculation (Sigma = M/W).
    print(f"12) Elastic Modulus Wx:    {full_analysis['Wx']:.4f}     # Ix / y_max")
    print(f"13) Elastic Modulus Wy:    {full_analysis['Wy']:.4f}     # Iy / x_max")
    print(f"14) Torsional Rigidity K:  {full_analysis['K_torsion']:.4f} # Saint-Venant K")

    # 15-16) Individual Polygon Verification
    # These calls verify the internal mathematical engine for single components.
    poly0 = sec_mid.polygons[0] # Selecting the interpolated flange
    ix_orig, _, _ = polygon_inertia_about_origin(poly0)
    q_poly0 = polygon_statical_moment(poly0, y_axis=full_analysis['Cy'])

    print(f"15) Polygon 0 Ix (Origin): {ix_orig:.4f}     # Direct call verification")
    print(f"16) Polygon 0 Q_local:     {q_poly0:.4f}     # Direct call verification")

    # 17) Static moment for Shear Analysis
    # Q_na represents the statical moment of the area above or below the Neutral Axis.
    q_na = section_statical_moment_partial(sec_mid, y_cut=full_analysis['Cy'])
    print(f"17) Section Q_na:          {q_na:.4f}     # Statical moment for shear (at Neutral Axis)")

    # 18) Stiffness matrix (Constitutive Relation)
    # Generates the [EA, EIy, EIx] diagonal matrix (if axes are principal).
    k_matrix = section_stiffness_matrix(sec_mid, E_ref=210000) # Example for Steel in MPa/m^2
    print(f"18) Stiffness Matrix Shape: {k_matrix.shape}       # Direct call verification (3x3 Matrix)")
    
    print("="*60)
    
    # --------------------------------------------------------
    # 10. OPENSEES EXPORT
    # --------------------------------------------------------

    # --------------------------------------------------------
    # 10. OPENSEES Tcl EXPORT
    # --------------------------------------------------------
    # IMPORTANT: This function exports ONLY the 'section Elastic' 
    # definitions to a .tcl file.
    #
    # REQUIRED ACTIONS FOR THE USER:
    # 1. This is not a complete OpenSees model. You must create a 
    #    Master Tcl script to 'source' this file.
    # 2. In your Master script, you must define:
    #    - Nodes (using the same z_points used here).
    #    - Boundary conditions (fixities).
    #    - Elements (linking nodes to these sections).
    #    - Loading patterns and Analysis commands.
    # 3. UNIT CONSISTENCY: Ensure your Master script uses units 
    #    consistent with E_val and the Pt(x,y) coordinates 
    #    (e.g., Meters/Newtons if E_val=2.1e11).
    
    # Define Z-coordinates for sampling (segment centers are recommended)   
    # We define the Z coordinates at which we want to "sample" the beam.
    # For example, we divide the 10 m beam into 5 segments (6 points)
    # -------------------------------------------------------------------------
    # 10. FULL OPENSEES MODEL GENERATION
    # -------------------------------------------------------------------------
    # We choose the number of elements (divisions) for the beam.
    # More elements = better approximation of the tapering effect.

    n_elements = 10 

    # Define Young's Modulus based on your units:
    # Use 210000.0 if your Pt() coordinates are in MILLIMETERS
    # Use 2.1e11    if your Pt() coordinates are in METERS
    E_steel = 210000.0 

    print(f"\nGenerating full OpenSees model with {n_elements} elements...")
    
  # 10. FULL OPENSEES MODEL GENERATION
    # --------------------------------------------------------
    # IMPORTANT: Your Pt coordinates are [-1, 1], which implies METERS.
    # Therefore, we MUST use Pascals (2.1e11) for the analysis to be physically correct.
    n_elements = 10 
    E_reference = 2.1e11 # N/m^2 (Pascals) for Steel

    print(f"\nGenerating full OpenSees model with {n_elements} elements...")
    
    # Generate the whole thing
    export_full_opensees_model(
        field=field, 
        num_elements=n_elements, 
        E_val=E_reference, 
        filename="main_beam_model.tcl"
    )

    print("\n" + "!"*60)
    print("CAUTION: OpenSees Export is currently in BETA PHASE.")
    print("Verify displacement results and unit consistency (E_val vs Pt).")
    print("!"*60 + "\n")

    print("="*60)
    print("DONE. To run: OpenSees.exe main_beam_model.tcl")
    print("="*60)
    print("Files 'main_beam_model.tcl' and 'sections_library.tcl' are ready.")
```

### Step 4 Visualization and plotting

```python

  # ----------------------------------------------------------------------------------
    # 9. VISUALIZATION AND PLOTTING
    # ----------------------------------------------------------------------------------
    # - plot_section_2d: Renders the cross-section slice at the requested Z.
    # - plot_volume_3d: Renders the longitudinal ruled solid. 
    #   'line_percent' controls the density of the mesh wires.
    # ----------------------------------------------------------------------------------
    viz = Visualizer(field)
    viz.plot_section_2d(z=5.0)    
    viz.plot_volume_3d(line_percent=100.0, seed=1)
    
    import matplotlib.pyplot as plt
    plt.show()
```
