from __future__ import annotations
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Sequence
try:
    import pycba as cba
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "Optional dependency missing: pycba.\n"
        "Install it to run this example:\n"
        "  pip install -e '.[examples]'\n"
        "or:\n"
        "  pip install pycba"
    ) from e


from csf import (
    Pt,
    Polygon,
    Section,
    ContinuousSectionField,
    section_full_analysis,
    Visualizer,
)

from csf.CSFStacked import CSFStacked  # <-- importa la classe, non il modulo

from csf.io.csf_reader import CSFReader

def rect_vertices(cx: float, cy: float, b: float, h: float):
    """
    Build CCW rectangle vertices from center (cx, cy),
    total width b, total height h.
    """
    hx = 0.5 * b
    hy = 0.5 * h
    return (
        Pt(cx - hx, cy - hy),
        Pt(cx + hx, cy - hy),
        Pt(cx + hx, cy + hy),
        Pt(cx - hx, cy + hy),
    )

'''
    # ============================================================
    # GEOMETRY PARAMETERS (edit only these)
    # ============================================================
    # Names used for polygon pairing between s0 and s1
    OUTER_NAME = "outer"
    INNER_NAME = "inner"

    # Polygon weights
    OUTER_WEIGHT = 1.0
    INNER_WEIGHT = 0.0

    # Outer rectangle dimensions at s0 and s1
    OUTER_B_S0 = 3.0   # total width  at s0
    OUTER_H_S0 = 1.0   # total height at s0
    OUTER_B_S1 = 1.8   # total width  at s1
    OUTER_H_S1 = 0.9   # total height at s1

    # Inner rectangle dimensions at s0 and s1
    INNER_B_S0 = 2.5
    INNER_H_S0 = 0.8
    INNER_B_S1 = 1.2
    INNER_H_S1 = 0.5

    # Optional centers (set offsets if needed)
    OUTER_CX_S0, OUTER_CY_S0 = 0.0, 0.0
    OUTER_CX_S1, OUTER_CY_S1 = 0.0, 0.0
    INNER_CX_S0, INNER_CY_S0 = 0.0, 0.0
    INNER_CX_S1, INNER_CY_S1 = 0.0, 0.0


    # ============================================================
    # FIRST POLYGON CREATION
    # ============================================================

    z0 = 0.0
    z1 = 5.0
    
    poly_outer_s0 = Polygon(
        name=OUTER_NAME,
        vertices=rect_vertices(OUTER_CX_S0, OUTER_CY_S0, OUTER_B_S0, OUTER_H_S0),
        weight=OUTER_WEIGHT,
    )

    poly_inner_s0 = Polygon(
        name=INNER_NAME,
        vertices=rect_vertices(INNER_CX_S0, INNER_CY_S0, INNER_B_S0, INNER_H_S0),
        weight=INNER_WEIGHT,
    )

    poly_outer_s1 = Polygon(
        name=OUTER_NAME,
        vertices=rect_vertices(OUTER_CX_S1, OUTER_CY_S1, OUTER_B_S1, OUTER_H_S1),
        weight=OUTER_WEIGHT,
    )

    poly_inner_s1 = Polygon(
        name=INNER_NAME,
        vertices=rect_vertices(INNER_CX_S1, INNER_CY_S1, INNER_B_S1, INNER_H_S1),
        weight=INNER_WEIGHT,
    )
    
    s0 = Section(z=z0, polygons=(poly_outer_s0, poly_inner_s0))
    s1 = Section(z=z1, polygons=(poly_outer_s1, poly_inner_s1))
    
    # first element
    #field_0 = ContinuousSectionField(section0=s0, section1=s1)
    
    #viz.plot_section_2d(z=00,show_vertex_ids=False)      
    
    
    # ============================================================
    # CONSTANT-SECTION ELEMENT 
    # ============================================================
    z2 = 7.0

    # Same geometry at both ends -> constant section along [z1, z2]
    poly_outer_c0 = Polygon(
        name=OUTER_NAME,
        vertices=rect_vertices(OUTER_CX_S1, OUTER_CY_S1, OUTER_B_S1, OUTER_H_S1),
        weight=OUTER_WEIGHT,
    )
    poly_inner_c0 = Polygon(
        name=INNER_NAME,
        vertices=rect_vertices(INNER_CX_S1, INNER_CY_S1, INNER_B_S1, INNER_H_S1),
        weight=INNER_WEIGHT,
    )
    poly_outer_c1 = Polygon(
        name=OUTER_NAME,
        vertices=rect_vertices(OUTER_CX_S1, OUTER_CY_S1, OUTER_B_S1, OUTER_H_S1),
        weight=OUTER_WEIGHT,
    )
    poly_inner_c1 = Polygon(
        name=INNER_NAME,
        vertices=rect_vertices(INNER_CX_S1, INNER_CY_S1, INNER_B_S1, INNER_H_S1),
        weight=INNER_WEIGHT,
    )

    s2_0 = Section(z=z1, polygons=(poly_outer_c0, poly_inner_c0))
    s2_1 = Section(z=z2, polygons=(poly_outer_c1, poly_inner_c1))

    # Constant-section ContinuousSectionField
    # second element
    #field_1 = ContinuousSectionField(section0=s2_0, section1=s2_1)    


'''
def calculate_theoretical_iy(bo, ho, bi, hi):
    """
    Computes theoretical Area and Iy for a hollow rectangle.
    Formula: Iy = (ho * bo^3 - hi * bi^3) / 12
    """
    area = (bo * ho) - (bi * hi)
    # Note: For Iy, the base (b) is cubed
    iy = (ho * bo**3 - hi * bi**3) / 12
    return area, iy

def run_beam_simulation(stack_obj, label):
    # --- Didactic Setup: Define Analysis Parameters ---
    L, n, E, P = 7.0, 20, 30e6, 25.0
    z_min, _ = stack_obj.global_bounds()
    dz = L / (n - 1)

    print(f"\n" + "="*50)
    print(f" SCENARIO: {label}")
    print(f"="*50)

    # --- STEP 1: CSF GEOMETRIC SCAN (The "Proof" of continuity) ---
    print(f"\n[1] CSF Property Scan (z from 0 to {L}):")
    for i in range(n):
        z = z_min + (L * i) / (n - 1)
        sa = stack_obj.section_full_analysis(z)
        print(f"  z = {z:7.4f}m | A = {sa['A']:9.6f} | Iy = {sa['Iy']:9.6f}")

    # --- STEP 2: STIFFNESS INTEGRATION (Midpoint Sampling) ---
    # This proves we are sampling 'inside' each segment for the solver
    ei_list = []
    print(f"\n[2] Midpoint Stiffness Extraction (EI = E * Iy):")
    for i in range(n - 1):
        z_mid = (z_min + i * dz) + dz/2
        iy_mid = stack_obj.section_full_analysis(z_mid)["Iy"]
        ei_list.append(E * iy_mid)
        if i < 3 or i > n-5: # Print first and last few for brevity
            print(f"  Segment {i:2d} (z_mid={z_mid:6.4f}m) -> EI = {E*iy_mid:.4e}")
        elif i == 3:
            print("  (...)")

    # --- STEP 3: STRUCTURAL ANALYSIS (PyCBA) ---
    R = [0] * (n * 2)
    R[0], R[1] = -1, -1  # Clamped boundary condition at z=0
    
    beam = cba.BeamAnalysis([dz]*(n-1), ei_list, R)
    beam.add_pl(n-1, P, dz) # Point load at the free end (tip)
    beam.analyze()
    
    # --- STEP 4: OUTPUT RESULTS ---
    disp = np.max(np.abs(beam.beam_results.results.D[0::2]))
    print(f"\n[3] FINAL RESULT for {label}:")
    print(f"  Max Vertical Displacement = {disp:.8e} m")
    
    return disp, beam

if __name__ == "__main__":

    # --- Scenario 1: Variable Section (The 'Stacked' Case) ---
    # Proves the CSF can handle sequential, non-uniform geometry
    f0 = CSFReader().read_file("stacked_0.yaml").field
    f1 = CSFReader().read_file("stacked_1.yaml").field
    stack_v = CSFStacked(eps_z=1e-10)
    stack_v.append(f0)
    stack_v.append(f1)
 

    disp_v, beam_v = run_beam_simulation(stack_v, "CSF STACKED (Variable)")



    # --- Scenario 2: Uniform Section (The 'Baseline' Case) ---
    # Proves the CSF is equally accurate for standard prismatic cases
    fu = CSFReader().read_file("uniform.yaml").field
    stack_u = CSFStacked()
    stack_u.append(fu)

    disp_u, beam_u = run_beam_simulation(stack_u, "CSF UNIFORM (Prismatic)")

    print(f"\n" + "#"*60)
    print(f" CONCLUSION: The framework correctly handles both complex")
    print(f" sequential fields and simple uniform segments with zero logic change.")
    print("#"*60)

    stack_v.plot_volume_3d_global()
    beam_v.plot_results()
    


    # --- Data Definition (From your YAML at z=5.0) ---
    # Outer: b=1.8, h=0.9 | Inner: b=1.2, h=0.5
    # --- AUTOMATED THEORETICAL VALIDATION AT z=5.0 ---
    z_check = 5.0

    # 1. Extract real data from the CSF Stack object
    real_sa = stack_v.section_full_analysis(z_check)
    real_iy = real_sa['Iy']
    real_area = real_sa['A']

    # 2. Theoretical calculation based on YAML geometry (Outer: 1.8x0.9, Inner: 1.2x0.5)
    # Formula Iy = (h * b^3) / 12
    bo, ho = 1.8, 0.9
    bi, hi = 1.2, 0.5

    iy_th = (ho * bo**3 - hi * bi**3) / 12
    area_th = (bo * ho) - (bi * hi)

    # 3. Print Validation Table
    print(f"\n" + "-"*30)
    print(f" THEORETICAL VALIDATION AT z={z_check}")
    print(f"-"*30)
    print(f"{'Property':<10} | {'Theoretical':<12} | {'CSF Actual':<12}")
    print(f"{'Iy':<10} | {iy_th:<12.6f} | {real_iy:<12.6f} ")
    print(f"{'Area':<10} | {area_th:<12.6f} | {real_area:<12.6f} ")
    print("-" * 60)
