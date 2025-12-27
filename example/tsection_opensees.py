from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Dict, Optional, List
import math
import random
import warnings

# Importing core CSF (Continuous Section Field) components for structural analysis
from csf import (
    Pt, Polygon, Section, ContinuousSectionField, 
    section_properties, section_full_analysis, 
    Visualizer, export_opensees_discretized_sections,
    section_statical_moment_partial, section_stiffness_matrix,
    polygon_inertia_about_origin,export_opensees_discretized_sections,polygon_statical_moment,export_full_opensees_model
)

if __name__ == "__main__":
    # ----------------------------------------------------------------------------------
    # ----------------------------------------------------------------------------------
    # 1. DEFINE START SECTION (Z = 0)
    # ----------------------------------------------------------------------------------
    #   GUIDELINES FOR POLYGON CONSTRUCTION:
    # - COUNTER-CLOCKWISE POLYGON
    # - VERTICES ORDER: You MUST define vertices in COUNTER-CLOCKWISE (CCW) order.
    #   This is MANDATORY for the Shoelace/Green's Theorem algorithm to compute a 
    #   POSITIVE Area and correct Moments of Inertia. Clockwise order will result 
    #   in negative area values and mathematically incorrect results.
    # - WEIGHT: Use 1.0 for solid parts and -1.0 to define voids/holes.
    # - The start section here is a T-shape composed of two not overlapping polygons:
    #   a "flange" (top horizontal) and a "web" (vertical stem).
    # ----------------------------------------------------------------------------------

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
    )

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
    
    # ----------------------------------------------------------------------------------
    # 3. CREATE SECTIONS WITH Z-COORDINATES
    # ----------------------------------------------------------------------------------
    # Sections act as containers for polygons at a specific coordinate along the beam axis.
    # All polygons defined at Z=0.0 are grouped into s0, and those at Z=10.0 into s1.
    # ----------------------------------------------------------------------------------

    s0 = Section(polygons=(poly0_start, poly1_start), z=0.0)
    s1 = Section(polygons=(poly0_end, poly1_end), z=10.0)

    # ----------------------------------------------------------------------------------
    # 4. INITIALIZE CONTINUOUS SECTION FIELD (CSF)
    # ----------------------------------------------------------------------------------
    # The 'field' object manages the mathematical mapping between s0 and s1.
    # It allows the retrieval of section properties at any arbitrary Z-coordinate
    # (e.g., field.section(5.33)) via linear interpolation of vertex coordinates.
    # ----------------------------------------------------------------------------------
    field = ContinuousSectionField(section0=s0, section1=s1)


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

