from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Dict, Optional, List
import math
import random
import warnings
import numpy as np
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
    write_opensees_geometry,
    section_full_analysis_keys,
    section_print_analysis,
    evaluate_weight_formula,
    safe_evaluate_weight
)

def get_normalized_t(z: float, z0: float, z1: float) -> float:
    """
    Denormalizes a real Z coordinate into a 0.0 - 1.0 range (t).
    
    Args:
        z:  The current real position (e.g., 2.5m)
        z0: The start of the section (e.g., 1.0m)
        z1: The end of the section (e.g., 4.0m)
        
    Returns:
        t: A float between 0.0 and 1.0
    """
    # Safety check: avoid division by zero if the section has no length
    if abs(z1 - z0) < 1e-9:
        return 0.0
        
    # Standard normalization formula: (z - start) / total_length
    t = (z - z0) / (z1 - z0)
    
    # Optional: clamping the value to ensure it stays within [0, 1]
    return max(0.0, min(1.0, float(t)))


if __name__ == "__main__":

    h = 0.40  
    b = 0.40 

    poly_start = Polygon(
        vertices=(
            Pt(-b/2, -h/2), 
            Pt( b/2, -h/2),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=2.0, # < -- defualt is linear interpolation
        name="startsection",
    )
    poly_end = Polygon(
        vertices=(
            Pt(-b/2, -h/2), 
            Pt( b/2, -h/2),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1.0,
        name="endsection",
    )

    # --- SECTION AND FIELD DEFINITION ---
    L = 10.0
    s0 = Section(polygons=(poly_start,),z=0.0)
    s1 = Section(polygons=(poly_end,),z=L)

    section_field = ContinuousSectionField(section0=s0, section1=s1)
    #  NO COMPOSITION FORMULAS 
    #  dormula="np.maximum(w0 * 0.01, E_lookup('experimental_data.txt'))"
    #  formula="w0 + (w1 - w0) * np.power(z / L, 2)"
    #  formula="1000 + (5000 - 1000) * (z/L)**2" # where k = 2 creates a parabolic transition
    #  
    # Definition of the sigmoid (S-curve) law
    # w0: initial value (z=0)
    # w1: final value (z=L)
    #  formula = "w0 + (w1 - w0) * (1 / (1 + np.exp(-10 * (z / L - 0.5))))"
    #  formula = "w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))"
    #  formula = "w1 + (w0 - w1) * 0.5 * (1 - np.cos(np.pi * z / L))"

    # formula = "w0"  # constant ratio along the element (no transition)
    # formula = "w0 + (w1 - w0) * (z / L)**2"  # parabolic (k=2 power-law), gentle start, steeper end
    # formula = "w0 + (w1 - w0) * (z / L)**k"  # general power-law (k>1 gentler near start; 0<k<1 steeper near start)
    # formula = "w0 + (w1 - w0) * (3*(z/L)**2 - 2*(z/L)**3)"  # smoothstep (C1): zero slope at both ends
    # formula = "w0 + (w1 - w0) * (6*(z/L)**5 - 15*(z/L)**4 + 10*(z/L)**3)"  # smootherstep (C2): zero 1st and 2nd deriv. at ends
    # formula = "w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))"  # cosine S-curve: exact endpoints, zero slope at ends
    # formula = "w0 + (w1 - w0) * (1 / (1 + np.exp(-a * (z / L - 0.5))))"  # logistic sigmoid (a≈8..16 sets steepness); not exact endpoints
    # formula = "w0 + (w1 - w0) * ((1/(1+np.exp(-a*(z/L-0.5))) - 1/(1+np.exp(a*0.5))) / (1/(1+np.exp(-a*0.5)) - 1/(1+np.exp(a*0.5))))"  # normalized logistic: exact w(0)=w0, w(L)=w1
    # formula = "w0 + (w1 - w0) * (0.5*(np.tanh(a*(z/L-0.5)) + 1))"  # tanh S-curve (a sets steepness); not exact endpoints

    # with internal fixed parameter "a"
    # formula = f"w0 + (w1 - w0) * ((0.5*(np.tanh({a}*(z/L-0.5)) + 1) - 0.5*(np.tanh(-{a}*0.5) + 1)) / (0.5*(np.tanh({a}*0.5) + 1) - 0.5*(np.tanh(-{a}*0.5) + 1)))" # normalized tanh: exact endpoints
    # formula = f"w0 + (w1 - w0) * ((np.exp({a}*(z/L)) - 1) / (np.exp({a}) - 1))"  # normalized exponential: a>0 biases change toward the end; a<0 toward the start
    # formula = "w0 * (1 + np.where(np.logical_and(z/L > 0.25, z/L < 0.75), 14, 0))" # specific for L= 10 . In reinforced concrete (RC) design, the amount of longitudinal steel is often reduced near the supports where the bending moment is lower. This creates a **discontinuous stiffness profile** along the length $L$.


    # --- FORMULA COMPOSITION ---
    a= 1.5  # 
    # The file experimental_data.txt must be located in the same directory where the Python script is executed.
    mock_file = "experimental_data.txt"
    safety_margin = 0.95  # 5% safety reduction


    # We combine a Python variable (safety_margin) with the lookup function
    formula = f"{safety_margin} * E_lookup('{mock_file}')"

    section_field.set_weight_laws([
        f"startsection,endsection : {formula}", # <--You can define any polygon.
    ])

    z = 2 # this is the point where the function is evaluated 
    w = safe_evaluate_weight(formula, p0=poly_start,p1=poly_end, l_total=L , t=z,print=True)

    sec_z = section_field.section(z)

    # CALL THE TEST HERE
    viz = Visualizer(section_field)
    viz.plot_properties(plot_w=True)
    plt.show()
