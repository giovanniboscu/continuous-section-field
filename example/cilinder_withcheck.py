import numpy as np
import math
import matplotlib.pyplot as plt

from csf import (
    Pt, Polygon, Section, ContinuousSectionField, Visualizer,
    section_data, section_derived_properties, 
    section_statical_moment_partial, integrate_volume,section_stiffness_matrix
)

# =================================================================
# 1. INPUT PARAMETERS
# =================================================================
H = 87.6            
N_SIDES = 64       
D_EXT = 4.9350
THICKNESS = 0.0230
DENSITY = 7850  # kg/m^3ls -l 

R_EXT = D_EXT / 2
R_INT = R_EXT - THICKNESS

def create_circular_polygon(radius: float, n_sides: int, weight: float, name: str) -> Polygon:
    """
    Creates a circular polygon with a specified number of sides and a unique name.
    """
    vertices = []
    for i in range(n_sides):
        # Calculate vertex positions using polar coordinates
        angle = 2 * np.pi * i / n_sides
        vertices.append(Pt(radius * np.cos(angle), radius * np.sin(angle)))
    
    # We now pass the 'name' parameter to ensure uniqueness in the Section
    return Polygon(vertices=tuple(vertices), weight=weight, name=name)



if __name__ == "__main__":


    # =================================================================
    # 2. MODEL CONSTRUCTION (CORRECTED)
    # =================================================================

    # Define names once to ensure consistency
    OUTER_NAME = "outer_hull"
    INNER_NAME = "inner_void"

    s0 = Section(polygons=(
        create_circular_polygon(R_EXT, N_SIDES, 1.0, name=OUTER_NAME), 
        create_circular_polygon(R_INT, N_SIDES, -1.0, name=INNER_NAME)
    ), z=0.0)

    s1 = Section(polygons=(
        create_circular_polygon(R_EXT, N_SIDES, 1.0, name=OUTER_NAME), 
        create_circular_polygon(R_INT, N_SIDES, -1.0, name=INNER_NAME)
    ), z=H)

    field = ContinuousSectionField(section0=s0, section1=s1)


    # --- 1. DATA EXTRACTION AND MECHANICAL PARAMETERS ---
    # Data extraction at mid-height for validation
    z_mid = H / 2
    data = section_data(field, z_mid)
    p = data['properties']
    d = section_derived_properties(p)
    
    # Material constants (Steel)
    E_mod = 210e9  # Young's Modulus [Pa]
    G_mod = 80.8e9 # Shear Modulus [Pa]
    
    # Section stiffness matrix calculation (EA, EIxx, EIyy)
    K = section_stiffness_matrix(data['section'], E_ref=E_mod)
    num_eixx = K[1, 1]
    num_eiyy = K[2, 2]
    num_gj = G_mod * p['J']
    
    # --- 2. DERIVED AND THEORETICAL QUANTITIES CALCULATION ---
    # Statical Q (First moment of area for shear analysis)
    num_q = section_statical_moment_partial(data['section'], y_cut=p['Cy'] - 1e-8)
    
    # Elastic section modulus W = I / y_max
    all_y = [v.y for poly in data['section'].polygons for v in poly.vertices]
    y_max_dist = max(all_y) - p['Cy']
    num_wx = p['Ix'] / y_max_dist

    # Analytical formulas (Theoretical for perfect cylinder)
    ex_a = math.pi * (R_EXT**2 - R_INT**2)
    ex_i = (math.pi / 4) * (R_EXT**4 - R_INT**4)
    ex_j = ex_i * 2
    ex_r = math.sqrt(ex_i / ex_a)
    ex_q = (2/3) * (R_EXT**3 - R_INT**3)
    ex_w = ex_i / R_EXT
    ex_mass_den = ex_a * DENSITY

    # Global 3D properties (Volume and total tower mass)
    num_vol = integrate_volume(field)
    ex_vol = ex_a * H
    num_mass = (num_vol * DENSITY) / 1000
    ex_mass_total = (ex_vol * DENSITY) / 1000

    # =================================================================
    # 3. EXTENDED  REPORT (WIDE FORMAT)
    # =================================================================
    # Structure: (Description, Symbol, Analytical, Numerical, Unit)
    full_report = [
        ("Net material cross-section", "A", ex_a, p['A'], "m^2"),
        ("Horizontal center of mass", "Cx", 0.0, p['Cx'], "m"),
        ("Vertical center of mass", "Cy", 0.0, p['Cy'], "m"),
        ("Axial stiffness", "EA", ex_a * E_mod, K[0,0], "N"), # <--- ADDED
        ("Bending stiffness about X", "EIxx", ex_i * E_mod, num_eixx, "N*m^2"),
        ("Bending stiffness about Y", "EIyy", ex_i * E_mod, num_eiyy, "N*m^2"),
        ("Symmetry check (Ixy)", "Ixy", 0.0, p['Ixy'], "m^4"),
        ("Torsional stiffness constant", "J", ex_j, p['J'], "m^4"),
        ("Torsional stiffness (GJ)", "GJ", ex_j * G_mod, num_gj, "N*m^2"),
        ("Maximum bending stiffness", "EI_max", ex_i * E_mod, d['I1'] * E_mod, "N*m^2"),
        ("Minimum bending stiffness", "EI_min", ex_i * E_mod, d['I2'] * E_mod, "N*m^2"),
        ("Principal axis rotation", "Alpha", 0.0, d['theta_deg'], "deg"),
        ("Buckling radius about X", "rx", ex_r, d['rx'], "m"),
        ("Buckling radius about Y", "ry", ex_r, d['ry'], "m"),
        ("First moment of area (Shear)", "Q", ex_q, num_q, "m^3"),
        ("Elastic Section Modulus", "W", ex_w, num_wx, "m^3"),
        ("Mass per unit length", "m_lin", ex_mass_den, p['A'] * DENSITY, "kg/m")
    ]

    header = f"{'STRUCTURAL PROPERTY':<32} | {'SYM':<8} | {'THEORETICAL':<18} | {'NUMERICAL':<18} | {'ERROR %':<12} | {'UNIT'}"
    line = "=" * len(header)
    
    print("\n" + line)
    print(header)
    print(line)

    for desc, sym, exact, numerical, unit in full_report:
        # Error calculation logic with isotropy and zero-value handling
        if abs(exact) < 1e-12:
            if sym == "Alpha" and abs(p['Ix'] - p['Iy']) < abs(p['Ix']) * 1e-12:
                err_str = "0.0000% (Iso)"
            else:
                err_str = f"{abs(numerical):.2e} (abs)"
        else:
            err = abs(exact - numerical) / exact * 100
            err_str = f"{err:.4f}%"

        # Wide-column printing with scientific notation
        print(f"{desc:<32} | {sym:<8} | {exact:<18.8e} | {numerical:<18.8e} | {err_str:<12} | {unit}")

    print(line)
    
    # Final volumetric summary
    print(f"{'Total Calculated Tower Volume:':<42} {num_vol:>18.6f} m^3")
    print(f"{'Total Calculated Tower Mass:':<42} {num_mass:>18.6f} t")
    #print(line + "\n")
    # Final summary with Theoretical vs Numerical comparison
    err_mass = abs(ex_mass_total - num_mass) / ex_mass_total * 100
    print(f"{'Total THEORETICAL Tower Mass:':<42} | {ex_mass_total:>18.3f} | {num_mass:>18.3f} | {err_mass:>10.4f}% | t")
    print(line + "\n")   

    # =================================================================
    # 4. 3D VISUALIZATION
    # =================================================================
    viz = Visualizer(field)
    ax = viz.plot_volume_3d(line_percent=100.0, seed=42)
    ax.set_title(f"3D Structural Model - Tower Height {H}m")
    plt.show()





    # Dati di input
    D_ext = 4.9350  # m
    thickness = 0.0230  # m
    D_int = D_ext - (2 * thickness)

    # Proprietà del materiale (Esempio: Acciaio)
    E = 210e9  # Modulo di Young in Pa (N/m^2)
    G = 80.7e9 # Modulo elastico tangenziale in Pa (N/m^2)
    rho = 7850 # Densità in kg/m^3

    # --- CALCOLI GEOMETRICI ---

    # 1. Area della sezione netta
    area = (math.pi / 4) * (D_ext**2 - D_int**2)

    # 2. Momento d'inerzia (I) - Uguale per X e Y per simmetria circolare
    I = (math.pi / 64) * (D_ext**4 - D_int**4)

    # 3. Costante torsionale (J) - Per sezioni circolari J = Ix + Iy
    J = (math.pi / 32) * (D_ext**4 - D_int**4)

    # 4. Modulo di resistenza elastico (W)
    W_el = I / (D_ext / 2)

    # 5. Raggio di inerzia (Buckling radius)
    r = math.sqrt(I / area)

    # 6. Primo momento d'area (per il taglio) - Sezione semicircolare cava
    # Q = (2/3) * (R_ext^3 - R_int^3)
    Q = (1/12) * (D_ext**3 - D_int**3)

    # 7. Massa per unità di lunghezza
    mass_per_m = area * rho

    # --- OUTPUT ---

    print(f"{'STRUCTURAL PROPERTY':<35} | {'VALUE':<15}")
    print("=" * 55)
    print(f"{'Net material cross-section':<35} | {area:>10.4f} m^2")
    print(f"{'Horizontal center of mass':<35} | {0:>10.4f} m")
    print(f"{'Vertical center of mass':<35} | {0:>10.4f} m")
    print(f"{'Axial stiffness (EA)':<35} | {E*area:>10.2e} N")
    print(f"{'Bending stiffness about X (EIx)':<35} | {E*I:>10.2e} Nm^2")
    print(f"{'Bending stiffness about Y (EIy)':<35} | {E*I:>10.2e} Nm^2")
    print(f"{'Symmetry check (Ixy)':<35} | {0:>10.4f} m^4")
    print(f"{'Torsional stiffness constant (J)':<35} | {J:>10.4f} m^4")
    print(f"{'Torsional stiffness (GJ)':<35} | {G*J:>10.2e} Nm^2")
    print(f"{'Maximum bending stiffness':<35} | {E*I:>10.2e} Nm^2")
    print(f"{'Minimum bending stiffness':<35} | {E*I:>10.2e} Nm^2")
    print(f"{'Buckling radius about X':<35} | {r:>10.4f} m")
    print(f"{'Buckling radius about Y':<35} | {r:>10.4f} m")
    print(f"{'First moment of area (Shear)':<35} | {Q:>10.4f} m^3")
    print(f"{'Elastic Section Modulus':<35} | {W_el:>10.4f} m^3")
    print(f"{'Mass per unit length':<35} | {mass_per_m:>10.2f} kg/m")
