import csf
print("Percorso libreria caricata:", csf.__file__)
import numpy as np
import math
import matplotlib.pyplot as plt

# Importing core CSF (Continuous Section Field) components for structural analysis
from csf import (
    Pt, Polygon, Section, ContinuousSectionField, 
    section_properties, section_full_analysis, 
    Visualizer, export_opensees_discretized_sections,
    section_statical_moment_partial, section_stiffness_matrix,
    polygon_inertia_about_origin,
    export_opensees_discretized_sections,
    polygon_statical_moment,export_full_opensees_model,
    compute_saint_venant_J,
    compute_saint_venant_Jv2,
    section_print_analysis,
    write_opensees_geometry
)



# EXTENSIVE ENGLISH COMMENTS FOR STRUCTURAL ANALYSIS VALIDATION
# This script performs a dual-layer verification:
# 1. Theoretical approach (independent function) using raw Shoelace integration.
# 2. CSF Library approach using the ContinuousSectionField and polygon engine.
# Goal: Validate the library's ability to handle rotated cross-sections (45 degrees).

from csf import (
    Pt, Polygon, Section, ContinuousSectionField, 
    section_properties, section_full_analysis, 
    Visualizer, export_opensees_discretized_sections,
    section_statical_moment_partial, section_stiffness_matrix,
    polygon_inertia_about_origin,export_opensees_discretized_sections,polygon_statical_moment
)

def independent_section_analysis(width_cm, height_cm):
    """
    Computes geometric properties of a rectangular section using 
    direct integration formulas (Green's Theorem / Shoelace).
    This serves as the 'True' reference for a non-rotated section.
    """
    # Conversion to meters for SI consistency
    b = width_cm / 100.0
    h = height_cm / 100.0
    
    # 1. Define Vertices (Centered at origin, Counter-Clockwise order)
    vertices = [
        (-b/2, -h/2), # Bottom-Left
        ( b/2, -h/2), # Bottom-Right
        ( b/2,  h/2), # Top-Right
        (-b/2,  h/2)  # Top-Left
    ]
    
    n = len(vertices)
    area = 0.0
    cx_num = 0.0
    cy_num = 0.0
    ix_origin = 0.0
    iy_origin = 0.0
    ixy_origin = 0.0

    # 2. Integral Calculation via Green's Theorem (Gauss/Shoelace Formulas)
    # These formulas integrate across the boundary to find area and second moments.
    for i in range(n):
        x0, y0 = vertices[i]
        x1, y1 = vertices[(i + 1) % n]
        
        # Cross product (signed area of the triangle from origin to the edge)
        cross = x0 * y1 - x1 * y0
        
        area += cross
        cx_num += (x0 + x1) * cross
        cy_num += (y0 + y1) * cross
        
        # Second moments of area relative to the global origin
        ix_origin += (y0**2 + y0*y1 + y1**2) * cross
        iy_origin += (x0**2 + x0*x1 + x1**2) * cross
        ixy_origin += (x0*y1 + 2*x0*y0 + 2*x1*y1 + x1*y0) * cross

    area = 0.5 * area
    cx = cx_num / (6.0 * area)
    cy = cy_num / (6.0 * area)
    
    # 3. Centroidal Properties (Parallel Axis Theorem / Steiner's Theorem)
    # Correcting moments from origin-based to centroid-based.
    ix_c = (ix_origin / 12.0) - area * (cy**2)
    iy_c = (iy_origin / 12.0) - area * (cx**2)
    ixy_c = (ixy_origin / 24.0) - area * (cx * cy)
    
    # 4. Derived Quantities for Structural Design
    # Polar Moment: Represents resistance to torsion for circular shapes.
    ip_c = ix_c + iy_c
    
    # Principal Moments (Mohr's Circle analysis)
    # Even if Ixy is zero now, these formulas are kept for general consistency.
    avg_i = (ix_c + iy_c) / 2.0
    diff_i = (ix_c - iy_c) / 2.0
    r_mohr = math.sqrt(diff_i**2 + ixy_c**2)
    i1 = avg_i + r_mohr
    i2 = avg_i - r_mohr
    
    # Radius of Gyration: Used for slenderness and buckling checks (L/r).
    rx = math.sqrt(ix_c / area) if area > 0 else 0
    ry = math.sqrt(iy_c / area) if area > 0 else 0
    
    # Elastic Moduli (Wx, Wy): Used to calculate max bending stress (sigma = M/W).
    # For a centered rectangle, max distance is half the total dimension.
    y_max = h / 2.0
    x_max = b / 2.0
    wx = ix_c / y_max if y_max > 0 else 0
    wy = iy_c / x_max if x_max > 0 else 0
    
    # Torsional Rigidity K (Saint-Venant fallback approximation for solid shapes)
    k_torsion = (area**4) / (40.0 * ip_c) if ip_c > 0 else 0.0

    # Generate a formatted report to allow line-by-line comparison with CSF.
    report = (
        f"1) Area (A):               {area:10.4f} # Net area\n"
        f"2) Centroid Cx:            {cx:10.4f} # Horizontal CG\n"
        f"3) Centroid Cy:            {cy:10.4f} # Vertical CG\n"
        f"4) Inertia Ix:             {ix_c:10.4f} # Centroidal X Inertia\n"
        f"5) Inertia Iy:             {iy_c:10.4f} # Centroidal Y Inertia\n"
        f"6) Inertia Ixy:            {ixy_c:10.4f} # Product of Inertia\n"
        f"7) Polar Moment (J):       {ip_c:10.4f} # Ix + Iy\n"
        f"8) Principal Inertia I1:   {i1:10.4f} # Max Principal Moment\n"
        f"9) Principal Inertia I2:   {i2:10.4f} # Min Principal Moment\n"
        f"10) Radius of Gyration rx: {rx:10.4f} # sqrt(Ix/A)\n"
        f"11) Radius of Gyration ry: {ry:10.4f} # sqrt(Iy/A)\n"
        f"12) Elastic Modulus Wx:    {wx:10.4f} # Ix / y_max\n"
        f"13) Elastic Modulus Wy:    {wy:10.4f} # Iy / x_max\n"
        f"14) Torsional Rigidity K:  {k_torsion:10.4f} # Saint-Venant K"
    )
    
    return report

if __name__ == "__main__":
    # -------------------------------------------------------------------------
    # PART 1: INDEPENDENT THEORETICAL REPORT
    # -------------------------------------------------------------------------
    print("============================================================")
    print("CLASSICAL (INDEPENDENT) REPORT - SECTION 40x60 cm")
    print("============================================================")
    print(independent_section_analysis(40, 60))
    print("============================================================")
    
    # Manual theoretical double check for Ix: (b*h^3)/12
    ix_theo = (0.4 * 0.6**3) / 12
    
    # -------------------------------------------------------------------------
    # PART 2: CSF LIBRARY VALIDATION (ROTATED SECTION)
    # -------------------------------------------------------------------------
    # In this section, we define the rectangle as ROTATED by 45 degrees.
    # Theoretical Check: 
    # 1. Area should remain 0.2400.
    # 2. I1 and I2 (Principal) MUST remain 0.0072 and 0.0032.
    # 3. Ixy should appear (approx -0.0020) because the axes are no longer principal.
    
    b = 0.40
    h = 0.60
    
    # Definition of the Start Section (Z=0.0) - Rotated by 45°
    # Coordinates calculated via: x' = x*cos(45) - y*sin(45), y' = x*sin(45) + y*cos(45)
    poly_ext = Polygon(
        vertices=(
            Pt( 0.0707107, -0.3535534), # Più vicino a (sqrt(2)/20, -5*sqrt(2)/20)
            Pt( 0.3535534, -0.0707107), 
            Pt(-0.0707107,  0.3535534), 
            Pt(-0.3535534,  0.0707107)
        ),
        weight=1.0,
        name="outer_rect_start_45deg"
    )

    # Definition of the End Section (Z=10.0) - Identical to the start
    poly_ext1 = Polygon(
        vertices=(
            Pt( 0.0707107, -0.3535534), 
            Pt( 0.3535534, -0.0707107), 
            Pt(-0.0707107,  0.3535534), 
            Pt(-0.3535534,  0.0707107)
        ),
        weight=1.0,
        name="outer_rect_end_45deg"
    )

    # Initialize the field and perform analysis on the mid-section (Z=5.0)
    s0 = Section(polygons=(poly_ext,), z=0.0)
    s1 = Section(polygons=(poly_ext1,), z=10.0)
    field = ContinuousSectionField(section0=s0, section1=s1)
 
    sec_mid = field.section(5.0)
    full_analysis = section_full_analysis(sec_mid)
    section_print_analysis(full_analysis)


    # 1–7) Primary Section Properties
    # NOTE: Ix and Iy in CSF (0.0052) differ from Independent (0.0072) 
    # because the section is rotated. However, their sum (J=0.0104) is identical.
    print(f"1) Area (A):               {full_analysis['A']:.8f}      # Net area")
    print(f"2) Centroid Cx:            {full_analysis['Cx']:.8f}     # Horizontal CG")
    print(f"3) Centroid Cy:            {full_analysis['Cy']:.8f}     # Vertical CG")
    print(f"4) Inertia Ix:             {full_analysis['Ix']:.8f}     # Centroidal X Inertia")
    print(f"5) Inertia Iy:             {full_analysis['Iy']:.8f}     # Centroidal Y Inertia")
    print(f"6) Inertia Ixy:            {full_analysis['Ixy']:84f}    # Product of Inertia")
    print(f"7) Polar Moment (J):       {full_analysis['J']:.8f}      # Ix + Iy")

    # 8–11) Principal Inertia & Radii of Gyration
    # VALIDATION POINT: Principal Inertia I1/I2 MUST match the Independent Report.
    print(f"8) Principal Inertia I1:   {full_analysis['I1']:.8f}     # Max Principal Moment")
    print(f"9) Principal Inertia I2:   {full_analysis['I2']:.8f}     # Min Principal Moment")
    print(f"10) Radius of Gyration rx: {full_analysis['rx']:.8f}     # sqrt(Ix/A)")
    print(f"11) Radius of Gyration ry: {full_analysis['ry']:.8f}     # sqrt(Iy/A)")

    # 12–14) Elastic and Torsional Properties
    print(f"12) Elastic Modulus Wx:    {full_analysis['Wx']:.8f}     # Ix / y_max")
    print(f"13) Elastic Modulus Wy:    {full_analysis['Wy']:.8f}     # Iy / x_max")
    print(f"14) Torsional Rigidity K:  {full_analysis['K_torsion']:.8f} # Saint-Venant K")


    # --------------------------------------------------------
    # 9. VISUALIZATION
    # --------------------------------------------------------
    # - 2D section plot at Z = 5.0
    # - 3D ruled solid visualization
    viz = Visualizer(field)
    # Generate 2D plot for the specified slice
    viz.plot_section_2d(z=5.0)
    # Generate 3D plot of the interpolated solid
    # line_percent determines the density of the longitudinal ruled lines
    viz.plot_volume_3d(line_percent=100.0, seed=1)
    import matplotlib.pyplot as plt
    plt.show()

    # ==============================================================================
    # SECTION EVALUATION ANALYSIS REPORT - TECHNICAL COMMENTS
    # ==============================================================================
    # 
    # 1. GEOMETRIC ACCURACY (Items 1-13)
    #    - The model shows perfect alignment with theoretical values for Area, 
    #      Inertia, and Centroids (0.0% error). 
    #    - Symmetry Check: Ix = Iy and rx = ry confirms the cross-section maintains 
    #      equidistant mass distribution relative to the principal axes, even 
    #      under rotation.
    #    - Product of Inertia (Ixy = -0.002): The non-zero value correctly reflects 
    #      the 45-degree rotation, indicating that the local coordinate system 
    #      is not aligned with the principal axes (which are confirmed by I1 and I2).
    #
    # 2. TORSIONAL RIGIDITY COMPARISON (Items 14-18)
    #    - J_sv (0.009216): This is the most accurate physical representation. 
    #      It represents the full Saint-Venant solution and shows the highest 
    #      stiffness, capturing the actual shape's resistance to twisting.
    #    - K_torsion (0.007975): This "fallback" approximation (A^4/40Ip) is 
    #      conservative (~13.5% lower than J_sv). It provides a reliable safety 
    #      margin for standard solid shapes.
    #    - J_s_vroark (0.007512): The most conservative value. Roark's formulas 
    #      are designed for manual engineering checks and penalize non-circular 
    #      sections more heavily to ensure structural safety.
    #
    # 3. FIDELITY & RELIABILITY INDEX
    #    - J_s_vroark_fidelity (0.15): This low index (15%) suggests the section 
    #      has high "stoutness" (solid/compact). 
    #    - Interpretation: In compact sections, the shear stress distribution 
    #      is non-linear and warping is significant. The discrepancy between 
    #      numerical (J_sv) and empirical (Roark) values is expected and typical 
    #      for this type of geometry.
    #
    # 4. STRUCTURAL INTEGRATION
    #    - For OpenSees/Finite Element Analysis: It is recommended to use J_sv 
    #      for realistic behavior, or J_s_vroark for a conservative design approach.
    #
    # STATUS: Geometric properties are exact; Torsional range is consistent
    # ==============================================================================