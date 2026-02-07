import numpy as np
import math
import matplotlib.pyplot as plt


import csf  #
from csf import (
    Pt, Polygon, Section, ContinuousSectionField, Visualizer,
    section_data, section_derived_properties,
    section_statical_moment_partial, integrate_volume,section_stiffness_matrix,section_full_analysis,section_print_analysis
)

# =========================
# INPUT PARAMETERS
# =========================
H = 87.6        # TOTAL HEIGHT(m)
N_LATI = 64   # Number of edges
DENSITY = 8500  # kg/m^3

deltaz=0
z0=deltaz
z1=H+deltaz

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
            weight=0.0,
            name="Base_Interna",
        ),
    ),
    z=z0
)

# HEAD (z = H)
s1 = Section(
    polygons=(
        Polygon(
            vertices=generate_circle(R_EXT_HEAD, N_LATI),
            weight=1.0,
            name="Head_Esterna",
        ),
        Polygon(
            vertices=generate_circle(R_INT_HEAD, N_LATI),
            weight=0.0,
            name="Head_Interna",
        ),
    ),
    z=z1
)



if __name__ == "__main__":
   
    # =========================
    # Continuous model 
    # =========================
    field = ContinuousSectionField(section0=s0, section1=s1)

    #z_mid = H / 2
    # data = section_data(field, z_mid)
   
    # 
    E_mod = 210e9  # Young's Modulus [Pa]
    G_mod = 80.8e9 # Shear Modulus [Pa]
    
    # Glonal propertied  (Volume and Mass)
    num_vol = integrate_volume(field,0,H,n_points=15)
    num_mass = (num_vol * DENSITY) / 1000

    header = f"{'STRUCTURAL PROPERTY':<32} | {'SYM':<8} | {'VALUE':<18} | {'UNIT'}"
    line = "=" * 132
    
    # relative z
    nrel_stazioni = [0.00, 8.76, 17.52, 26.28, 35.04, 43.80, 52.56, 61.32, 70.08, 78.84, 87.60]
    tower_height = 87.60

   
    # =================================================================
    # 6. OFFICIAL NREL REPORT DATA (STATIC REFERENCE TABLE 6-1)
    # =================================================================
    # Static data extracted directly from the NREL/TP-500-38060 report
    # Field format: (Elevation, HtFract, TMassDen, TwFAStif, TwSSStif, TwGJStif, TwEAStif, TwFAIner, TwSSIner)
    
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
    
    # table header
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
    # 5. TABLE-1 (FORMATO FAST / NREL)
    # =================================================================


    print("\n" + "="*130)
    print(f"{'NREL 5-MW TOWER STRUCTURAL PROPERTIES (FAST FORMAT)':^130}")
    print("="*130)


    # Header with exact variable names from the NREL / FAST re
    nrel_header = (f"{'Elevation':>9} | {'HtFract':>8} | {'TMassDen':>10} | {'TwFAStif':>13} | "
                   f"{'TwSSStif':>13} | {'TwGJStif':>13} | {'TwEAStif':>12} | {'TwFAIner':>10} | {'TwSSIner':>10}")
    print(nrel_header)
    print("-" * 132)

    
    for zrelative in nrel_stazioni:
        # 1. Recupero dati già processati (quelli che usi per OpenSees)
        z=zrelative+deltaz # section requires z abosolute
        sec = field.section(z)
        res = section_full_analysis(sec) # <--- retrievs all values  
        
        E_z = E_mod 
        G_z = G_mod

        # 3. Mapping diretto sui parametri NREL
        HtFract  =  zrelative / tower_height
        TMassDen = res['A'] * DENSITY
        TwFAStif = E_z * res['Ix']   # Fore-Aft (EIxx)
        TwSSStif = E_z * res['Iy']   # Side-to-Side (EIyy)
        TwGJStif = G_z * res['J']    # Torsion (GJ)
        TwEAStif = E_z * res['A']    # Axial (EA)
        
        # Inerzie massiche sezionali (kg-m)
        TwFAIner = res['Ix'] * DENSITY
        TwSSIner = res['Iy'] * DENSITY
        
        # 4. Stampa (il print rimane lo stesso)
        print(f"{zrelative:9.2f} | {HtFract:8.2f} | {TMassDen:10.2f} | {TwFAStif:13.4e} | "
            f"{TwSSStif:13.4e} | {TwGJStif:13.4e} | {TwEAStif:12.4e} | {TwFAIner:10.2e} | {TwSSIner:10.2e}")
        
    # Riassunto finale
    print(f"{'Model polygon #'} {N_LATI} sides")
    print(f"{'Total Calculated Volume:':<42} {num_vol:>18.6f} m^3")
    print(f"{'Total Calculated Mass:':<42} {num_mass:>18.6f} t")
    print(f"\nNOTE: Calculated Mass reflects the structural steel shell only.")
    print(f"To match the 347.46 target, the NREL report applies a 'base-to-top mass density distribution adjustment' of a factor")
    print(f"This adjustment accounts for non-structural components such as flanges, ladders, and internal platforms.")

   
    # =================================================================
    # 4. 3D
    # =================================================================
    viz = Visualizer(field)
    ax = viz.plot_volume_3d(line_percent=30.0, seed=42)

   
    viz.plot_section_2d(z=00,show_vertex_ids=False)  


    ax.set_title(f"NREL 5-MW Reference Tower Height {H}m")
    plt.show()
    field.to_yaml("NREL-5-MW.yaml")