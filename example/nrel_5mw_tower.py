import numpy as np
import math
import matplotlib.pyplot as plt

from section_field import (
    Pt, Polygon, Section, ContinuousSectionField, Visualizer,
    section_data, section_derived_properties, 
    section_statical_moment_partial, integrate_volume,section_stiffness_matrix
)

# =========================
# INPUT PARAMETERS
# =========================
H = 87.6        # TOTAL HEIGHT(m)
N_LATI =256     # Number of edges
DENSITY = 8500  # kg/m^3

# BAS
D_EXT_BASE = 6.0
SPESSORE_BASE = 0.0351
R_EXT_BASE = D_EXT_BASE / 2
R_INT_BASE = R_EXT_BASE - SPESSORE_BASE

# HEAD
D_EXT_HEAD = 3.87
SPESSORE_HEAD = 0.0247
R_EXT_HEAD = D_EXT_HEAD / 2
R_INT_HEAD = R_EXT_HEAD - SPESSORE_HEAD

# =========================
#  UTILITY FUNCTION
# =========================
def generate_circle(radius, n_lati):
    """Generates a list of Pt objects for a regular polygon."""
    point = []
    for i in range(n_lati):
        # radiant
        alpha = 2 * math.pi * i / n_lati
        x = radius * math.cos(alpha)
        y = radius * math.sin(alpha)
        point.append(Pt(x, y))
    return tuple(point)

# =========================
# SECTION MODELLING
# =========================

# Sezione BASE (z = 0)
s0 = Section(
    polygons=(
        Polygon(
            vertices=generate_circle(R_EXT_BASE, N_LATI),
            weight=1.0,
            name="Base_Esterna",
        ),
        Polygon(
            vertices=generate_circle(R_INT_BASE, N_LATI),
            weight=-1.0,
            name="Base_Interna",
        ),
    ),
    z=0.0
)

# Sezione TESTA (z = H)
s1 = Section(
    polygons=(
        Polygon(
            vertices=generate_circle(R_EXT_HEAD, N_LATI),
            weight=1.0,
            name="Head_Esterna",
        ),
        Polygon(
            vertices=generate_circle(R_INT_HEAD, N_LATI),
            weight=-1.0,
            name="Head_Interna",
        ),
    ),
    z=H
)

# =========================
# Continuous model 
# =========================
field = ContinuousSectionField(section0=s0, section1=s1)


if __name__ == "__main__":
   
    z_mid = H / 2
    data = section_data(field, z_mid)
    p = data['properties']
    d = section_derived_properties(p)
    
    # Costanti materiale (Acciaio)
    E_mod = 210e9  # Young's Modulus [Pa]
    G_mod = 80.8e9 # Shear Modulus [Pa]
    
    # Calcolo della matrice di rigidezza della sezione (EA, EIxx, EIyy)
    K = section_stiffness_matrix(data['section'], E_ref=E_mod)
    num_eixx = K[1, 1]
    num_eiyy = K[2, 2]
    num_gj = G_mod * p['J']
    
    # --- 2. CALCOLO GRANDEZZE DERIVATE ---
    # Statical Q (Momento statico per analisi del taglio)
    num_q = section_statical_moment_partial(data['section'], y_cut=p['Cy'] - 1e-8)
    
    # Modulo di resistenza elastico W = I / y_max
    all_y = [v.y for poly in data['section'].polygons for v in poly.vertices]
    y_max_dist = max(all_y) - p['Cy']
    num_wx = p['Ix'] / y_max_dist

    # Proprietà globali 3D (Volume e Massa totale torre)
    num_vol = integrate_volume(field, n=200)
    num_mass = (num_vol * DENSITY) / 1000

    header = f"{'STRUCTURAL PROPERTY':<32} | {'SYM':<8} | {'VALUE':<18} | {'UNIT'}"
    line = "=" * 132
    #print(line)
    
    # Riassunto finale
    print(f"{'Model polygon #'} {N_LATI} sides")
    print(f"{'Total Calculated Volume:':<42} {num_vol:>18.6f} m^3")
    print(f"{'Total Calculated Mass:':<42} {num_mass:>18.6f} t")
    print(f"\nNOTE: Calculated Mass reflects the structural steel shell only.")
    print(f"To match the 347.46 target, the NREL report applies a 'base-to-top mass density distribution adjustment' of a factor")
    print(f"This adjustment accounts for non-structural components such as flanges, ladders, and internal platforms.")

   # =================================================================
    # 5. TABLE-1 (FORMATO FAST / NREL)
    # =================================================================
    nrel_stazioni = [0.00, 8.76, 17.52, 26.28, 35.04, 43.80, 52.56, 61.32, 70.08, 78.84, 87.60]
    tower_height = 87.60

    print("\n" + "="*130)
    print(f"{'NREL 5-MW TOWER STRUCTURAL PROPERTIES (FAST FORMAT)':^130}")
    print("="*130)
    
    # Header with exact variable names from the NREL / FAST re
    nrel_header = (f"{'Elevation':>9} | {'HtFract':>8} | {'TMassDen':>10} | {'TwFAStif':>13} | "
                   f"{'TwSSStif':>13} | {'TwGJStif':>13} | {'TwEAStif':>12} | {'TwFAIner':>10} | {'TwSSIner':>10}")
    print(nrel_header)
    print("-" * 132)

    for z in nrel_stazioni:
        # 1. Quote z
        data = section_data(field, z)
        p = data['properties']
        K_z = section_stiffness_matrix(data['section'], E_ref=E_mod)
        
        # 2. varible mapping for pdf
        HtFract  = z / tower_height       # Height Fraction [0-1]
        TMassDen = p['A'] * DENSITY       # Mass per unit length [kg/m]
        TwFAStif = K_z[1, 1]              # Fore-Aft Bending Stiffness (EIxx)
        TwSSStif = K_z[2, 2]              # Side-to-Side Bending Stiffness (EIyy)
        TwGJStif = G_mod * p['J']         # Torsional Stiffness (GJ)
        TwEAStif = K_z[0, 0]              # Axial Stiffness (EA)
        
        # Sectional rotational inertia (I = m * r^2)
        # Note: In FAST these are often expressed as mass moment of inertia per unit length [kg-m]
        TwFAIner = p['Ix'] * DENSITY      # Fore-Aft mass inertia
        TwSSIner = p['Iy'] * DENSITY      # Side-to-Side mass inertia

        # 3. Stampa riga formattata
        print(f"{z:9.2f} | {HtFract:8.3f} | {TMassDen:10.2f} | {TwFAStif:13.4e} | "
              f"{TwSSStif:13.4e} | {TwGJStif:13.4e} | {TwEAStif:12.4e} | {TwFAIner:10.2e} | {TwSSIner:10.2e}")

    #print("="*130)



    
    # =================================================================
    # 6. OFFICIAL NREL REPORT DATA (STATIC REFERENCE TABLE 6-1)
    # =================================================================
    # Static data extracted directly from the NREL/TP-500-38060 report
    # Field format: (Elevation, HtFract, TMassDen, TwFAStif, TwSSStif, TwGJStif, TwEAStif, TwFAIner, TwSSIner)
    '''
    nrel_static_table = [
        (0.00,  0.000, 4306.0, 4.744e11, 4.744e11, 3.651e11, 1.064e11, 1.916e4, 1.916e4),
        (8.76,  0.100, 4030.0, 4.130e11, 4.130e11, 3.178e11, 9.957e10, 1.668e4, 1.668e4),
        (17.52, 0.200, 3763.1, 3.578e11, 3.578e11, 2.753e11, 9.298e10, 1.445e4, 1.445e4),
        (26.28, 0.300, 3505.2, 3.082e11, 3.082e11, 2.372e11, 8.661e10, 1.245e4, 1.245e4),
        (35.04, 0.400, 3256.3, 2.640e11, 2.640e11, 2.032e11, 8.046e10, 1.066e4, 1.066e4),
        (43.80, 0.500, 3016.6, 2.248e11, 2.248e11, 1.730e11, 7.453e10, 9.077e3, 9.077e3),
        (52.56, 0.600, 2785.8, 1.900e11, 1.900e11, 1.462e11, 6.883e10, 7.674e3, 7.674e3),
        (61.32, 0.700, 2564.2, 1.595e11, 1.595e11, 1.227e11, 6.335e10, 6.440e3, 6.440e3),
        (70.08, 0.800, 2351.6, 1.327e11, 1.327e11, 1.021e11, 5.810e10, 5.361e3, 5.361e3),
        (78.84, 0.900, 2148.1, 1.095e11, 1.095e11, 8.427e10, 5.307e10, 4.423e3, 4.423e3),
        (87.60, 1.000, 1953.7, 8.947e10, 8.947e10, 6.885e10, 4.827e10, 3.614e3, 3.614e3)
    ]
    '''
    
    nrel_static_table = [
    (0.00,  0.000, 5590.87, 6.1434e11, 6.1434e11, 4.7275e11, 1.3813e11, 2.48663e4, 2.48663e4),
    (8.76,  0.100, 5232.43, 5.3482e11, 5.3482e11, 4.1156e11, 1.2927e11, 2.16475e4, 2.16475e4),
    (17.52, 0.200, 4885.76, 4.6327e11, 4.6327e11, 3.5650e11, 1.2071e11, 1.87513e4, 1.87513e4),
    (26.28, 0.300, 4550.87, 3.9913e11, 3.9913e11, 3.0714e11, 1.1243e11, 1.61553e4, 1.61553e4),
    (35.04, 0.400, 4227.75, 3.4188e11, 3.4188e11, 2.6309e11, 1.0445e11, 1.38381e4, 1.38381e4),
    (43.80, 0.500, 3916.41, 2.9101e11, 2.9101e11, 2.2394e11, 9.6760e10, 1.17790e4, 1.17790e4),
    (52.56, 0.600, 3616.83, 2.4603e11, 2.4603e11, 1.8932e11, 8.9360e10, 9.95820e3, 9.95820e3),
    (61.32, 0.700, 3329.03, 2.0646e11, 2.0646e11, 1.5887e11, 8.2250e10, 8.35660e3, 8.35660e3),
    (70.08, 0.800, 3053.01, 1.7185e11, 1.7185e11, 1.3224e11, 7.5430e10, 6.95590e3, 6.95590e3),
    (78.84, 0.900, 2788.75, 1.4178e11, 1.4178e11, 1.0910e11, 6.8900e10, 5.73860e3, 5.73860e3),
    (87.60, 1.000, 2536.27, 1.1582e11, 1.1582e11, 8.9130e10, 6.2660e10, 4.68800e3, 4.68800e3),
    ]
    
    print("\n" + "="*132)
    print(f"{'OFFICIAL NREL 5-MW TOWER DATA (REFERENCE TABLE 6-1)':^145}")
    print("="*132)
    
    # Intestazione con lo stesso stile del report dinamico
    nrel_header = (f"{'Elevation':>9} | {'HtFract':>8} | {'TMassDen':>10} | {'TwFAStif':>13} | "
                   f"{'TwSSStif':>13} | {'TwGJStif':>13} | {'TwEAStif':>12} | {'TwFAIner':>10} | {'TwSSIner':>10}")
    print(nrel_header)
    print("-" * len(nrel_header))

    for row in nrel_static_table:
        elev, frac, mass, fa_stif, ss_stif, gj_stif, ea_stif, fa_iner, ss_iner = row
        
        print(f"{elev:9.2f} | {frac:8.3f} | {mass:10.1f} | {fa_stif:13.3e} | "
              f"{ss_stif:13.3e} | {gj_stif:13.3e} | {ea_stif:12.3e} | {fa_iner:10.2e} | {ss_iner:10.2e}")

    print("="*132)

   
    # =================================================================
    # 4. 3D
    # =================================================================
    viz = Visualizer(field)
    ax = viz.plot_volume_3d(line_percent=30.0, seed=42)
    ax.set_title(f"NREL 5-MW Reference Tower Height {H}m")
    plt.show()
