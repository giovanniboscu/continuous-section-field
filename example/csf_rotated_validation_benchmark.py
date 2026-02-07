import csf
import numpy as np
import math
import matplotlib.pyplot as plt

# Importing core CSF (Continuous Section Field) components for structural analysis
from csf import (
    Pt, Polygon, Section, ContinuousSectionField, 
    section_properties, section_full_analysis, 
    Visualizer, 
    section_statical_moment_partial, section_stiffness_matrix,
    polygon_inertia_about_origin,
    polygon_statical_moment,
    compute_saint_venant_J,
    compute_saint_venant_Jv2,
    section_print_analysis,
    write_opensees_geometry
)


# This script performs a dual-layer verification:
# 1. Theoretical approach (independent function) using raw Shoelace integration.
# 2. CSF Library approach using the ContinuousSectionField and polygon engine.
# Goal: Validate the library's ability to handle rotated cross-sections (45 degrees).

from csf import (
    Pt, Polygon, Section, ContinuousSectionField, 
    section_properties, section_full_analysis, 
    Visualizer, 
    section_statical_moment_partial, section_stiffness_matrix,
    polygon_inertia_about_origin,polygon_statical_moment
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
   # SECTION EVALUATION ANALYSIS REPORT - TECHNICAL COMMENTS (CORRECTED)
   # ==============================================================================
   #
   # 1. GEOMETRIC ACCURACY (Items 1-13)
   #    - The model is fully consistent with theoretical invariants for Area,
   #      Principal Inertias, and Polar Moment:
   #         A = 0.24000001 ~ 0.2400
   #         I1 = 0.00720000
   #         I2 = 0.00320000
   #         J  = Ix + Iy = 0.01040000
   #    - The apparent difference in (Ix, Iy, Ixy) compared to the "classical"
   #      table is due to axis orientation:
   #         CSF reports: Ix = 0.00520000, Iy = 0.00520000, Ixy = -0.00200000
   #      This is exactly the inertia tensor expressed in a rotated frame
   #      (about 45° from principal axes), not a geometric inconsistency.
   #    - Symmetry check in the current reference frame:
   #         Ix = Iy and rx = ry
   #      confirms balanced distribution in that frame, while Ixy != 0 confirms
   #      that the frame is not principal.
   #
   # 2. TORSIONAL RIGIDITY COMPARISON (Items 14-18)
   #    - J_sv (0.01040000): Saint-Venant torsional constant used by CSF in this case
   #      (alpha = 1.00000000). This is the highest value among the reported torsional
   #      proxies and is consistent with the section's full solid response.
   #    - K_torsion (0.00797538): fallback semi-empirical approximation, conservative
   #      relative to J_sv (about 23.3% lower than J_sv).
   #    - J_s_vroark (0.00751249): Roark-based proxy, slightly more conservative than
   #      K_torsion (about 5.8% lower than K_torsion) and about 27.8% lower than J_sv.
   #
   # 3. FIDELITY / RELIABILITY INDEX
   #    - J_s_vroark_fidelity = 0.66666659 (NOT 0.15).
   #    - Interpretation: this is a medium-good mapping consistency indicator for the
   #      Roark-equivalent approach in this section; it does not indicate a failure.
   #    - Practical meaning: Roark proxy is usable as a conservative estimate here,
   #      but the physical-reference torsional value remains J_sv.
   #
   # 4. STRUCTURAL INTEGRATION GUIDANCE
   #    - For realistic FE/OpenSees torsional behavior: prefer J_sv = 0.01040000.
   #    - For intentionally conservative preliminary checks: J_s_vroark = 0.00751249
   #      may be adopted with explicit note of conservatism.
   #
   # STATUS:
   #    Geometric consistency is confirmed (tensor invariants and principal values
   #    match theory). Differences in Ix/Iy/Ixy are entirely due to coordinate-frame
   #    rotation. Torsional estimates are internally coherent and ordered by expected
   #    conservatism: J_sv > K_torsion > J_s_vroark.
   # ==============================================================================

  
