from __future__ import annotations
import os
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
    Visualizer,
    section_statical_moment_partial, section_stiffness_matrix,
    polygon_inertia_about_origin,
    polygon_statical_moment,
    compute_saint_venant_J,
    compute_saint_venant_Jv2,
    write_opensees_geometry,
    section_full_analysis_keys,
    section_print_analysis,
    safe_evaluate_weight_zrelative)

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
    try:
        h = 0.40  
        b = 0.40 
        messageerror="Initializing the starting polygon geometry (poly_start)"
        poly_start = Polygon(
            vertices=(
                Pt(-b/2, -h/2), 
                Pt( b/2, -h/2),
                Pt( b/2,  h/2),
                Pt(-b/2,  h/2),
            ),
            weight=1, # < -- defualt is linear interpolation
            name="startsection",
        )
        
        messageerror="Initializing the ending polygon geometry (poly_end)"
        poly_end = Polygon(
            vertices=(
                Pt(-b/2, -h/2), 
                Pt( b/2, -h/2),
                Pt( b/2,  h/2),
                Pt(-b/2,  h/2),
            ),
            weight=0.5,
            name="endsection",
        )
        
        # --- SECTION AND FIELD DEFINITION ---
        L = 10
        messageerror="Defining the first section station (s0) at z=0"
        s0 = Section(polygons=(poly_start,),z=100.0)
        
        messageerror="Defining the second section station (s1) at z=L"
        s1 = Section(polygons=(poly_end,),z=L+100)
        
        messageerror="Creating the ContinuousSectionField (interpolator between s0 and s1)"
        section_field = ContinuousSectionField(section0=s0, section1=s1)
        
        # --- FORMULA COMPOSITION ---
        messageerror="Setting formula parameters (a, file path, safety margin)"
        section_field.to_yaml("simplebox.yaml")


        # =========================================================================
        # EXTERNAL RESOURCE CONFIGURATION
        # =========================================================================
        # Define the source file for experimental data lookup. 
        # The 'E_lookup' function will parse this file to retrieve weight or 
        # stiffness values based on the current 'z' coordinate.
        # 
        # Note: Ensure this file is located in the script's execution directory.
        # =========================================================================
        mock_file = "example/experimental_data.txt"


        if not os.path.exists(mock_file):
            # Creating a clear, instructional error message
            error_header = "="*50
            msg = (
                f"\n{error_header}\n"
                f"CRITICAL ERROR: DATA FILE MISSING\n"
                f"{error_header}\n"
                f"The required file '{mock_file}' was not found in:\n"
                f"{os.getcwd()}\n\n"
                f"Please ensure the file is in the same directory as this script\n"
                f"or provide the absolute path.\n"
                f"{error_header}\n"
            )
            raise FileNotFoundError(msg)

   
        essageerror="Evaluating the weight at a specific coordinate (z)"
        
        # =========================================================================
        # FORMULA DEFINITION & VARIABLE INJECTION
        # =========================================================================
        # IMPORTANT: The variables defined below (e.g., mock_file, safety_margin) 
        # serve as placeholders for the weight evolution logic.
        #
        # To ensure these variables are correctly evaluated within the section field,
        # you MUST define your formula using a Python 'f-string' (prefixing the 
        # string with an 'f', like f"weight * {variable}").
        #
        # Without the 'f' prefix, Python will treat the curly braces as literal 
        # text, and the calculation engine will be unable to inject the dynamic 
        # values into the formula string.
        # =========================================================================

        # formula = "w0" # constant ratio along the element (no transition)

        # formula = "w0 + (w1 - w0) * (z / L)**2" # parabolic (k=2 power-law), gentle start, steeper end

        # formula = "w0 + (w1 - w0) * (z / L)**k" # general power-law (k>1 gentler near start; 0<k<1 steeper near start)

        # formula = "w0 + (w1 - w0) * (3*(z/L)**2 - 2*(z/L)**3)" # smoothstep (C1): zero slope at both ends

        # formula = "w0 + (w1 - w0) * (6*(z/L)**5 - 15*(z/L)**4 + 10*(z/L)**3)" # smootherstep (C2): zero 1st and 2nd deriv. at ends

        # formula = "w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))" # cosine S-curve: exact endpoints, zero slope at ends

        # formula = "w0 + (w1 - w0) * (1 / (1 + np.exp(-a * (z / L - 0.5))))" # logistic sigmoid (a≈8..16 sets steepness); not exact endpoints

        # formula = "w0 + (w1 - w0) * ((1/(1+np.exp(-a*(z/L-0.5))) - 1/(1+np.exp(a*0.5))) / (1/(1+np.exp(-a*0.5)) - 1/(1+np.exp(a*0.5))))" # normalized logistic: exact w(0)=w0, w(L)=w1

        # formula = "w0 + (w1 - w0) * (0.5*(np.tanh(a*(z/L-0.5)) + 1))" # tanh S-curve (a sets steepness); not exact endpoints


        # with internal fixed parameter "a"

        # formula = f"w0 + (w1 - w0) * ((0.5*(np.tanh({a}*(z/L-0.5)) + 1) - 0.5*(np.tanh(-{a}*0.5) + 1)) / (0.5*(np.tanh({a}*0.5) + 1) - 0.5*(np.tanh(-{a}*0.5) + 1)))" # normalized tanh: exact endpoints

        # formula = f"w0 + (w1 - w0) * ((np.exp({a}*(z/L)) - 1) / (np.exp({a}) - 1))" # normalized exponential: a>0 biases change toward the end; a<0 toward the start

        # formula = d"w0 * (1 + np.where(np.logical_and(z/L > 0.25, z/L < 0.75), 14, 0))" # specific for L= 10 . In reinforced concrete (RC) design, the amount of longitudinal steel is often reduced near the supports where the bending moment is lower. This creates a **discontinuous stiffness profile** along the length $L$.
       

        z = 4 # this is ABSOLUTE this is the point where the function is evaluated 
        # --- Variables for Formula Injection ---
        safety_margin = 0.95  # 5% safety reduction
        a= 1.5  # this is used in the formula

        messageerror="Compiling the weight evolution formula string"

        # =========================================================================
        # This is the current formula string 
        # =========================================================================

        #formula =f"w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))"
        formula =f"E_lookup('{mock_file}')" # lookup file
        # --- Connecting Polygons & Laws ---
        # This tells the software which formula to apply to which component.
        #
        # You can use the names you gave to your polygons (e.g., 'startsection' 
        # at the base and 'endsection' at the top). 
        #
        # Note: The software connects them based on their position in the list. 
        # Using different names is perfectly fine—the engine knows they are 
        # the same part because they were created in the same order.

        #messageerror="Applying the weight laws to the section field"
        #section_field.set_weight_laws([
        #    "startsection,endsection : t", 
        #])
        zrel=1
        w = safe_evaluate_weight_zrelative(formula, p0=poly_start,p1=poly_end, z0=100,z1=110 , z=zrel,print=True)
        
        #messageerror="Generating the interpolated section at z height"
        #sec_z = section_field.section(z) 
        
        #messageerror="Performing full cross-section structural analysis"
        #full_analysis = section_full_analysis(sec_z)

        # CALL THE TEST HERE
        #messageerror="Initializing the Visualizer object"
        #viz = Visualizer(section_field)
        
        #messageerror="Plotting section properties ['Cy','Ix','Iy','J']"
        #viz.plot_properties(plot_w=True)
        #viz.plot_weight(num_points=100)
        #plt.show()
        #messageerror="Generating 2D section plot for the specified z coordinate"
        #viz.plot_section_2d(z=z, show_vertex_ids=True,show_weights=False)    
        #messageerror="Rendering the final plots"
        #plt.show()
        
        # Stampa i nomi delle variabili Polygon
       
    except Exception as e:                  
        errormsg=f"VALIDATION FAILED - Error during operation: [{messageerror}].\nDetails: {e}"
        print(errormsg)
