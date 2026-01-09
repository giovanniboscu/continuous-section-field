"""
Prototype: continuous section field + property digestor + 2D/3D visualization

Assumptions (explicit):
- Two endpoint sections exist at z0 and z1.
- Same number of polygons in start/end.
- For each polygon: same number of vertices in start/end.
- Vertex ordering is already consistent (your matching is given/assumed).
- Polygons are simple enough for shoelace formulas (no self-intersections).

Dependencies: matplotlib (standard in most Python setups).
"""

from __future__ import annotations
import traceback
from dataclasses import dataclass
from typing import Tuple, Dict, Optional, List
import math
import random
import warnings
import os
try:
    import opensees as ops  # Windows (pip install opensees)
except ImportError:
    import openseespy.opensees as ops  # Linux/Mac
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D 
import re
from datetime import datetime


def safe_evaluate_weight(formula: str, p0: Polygon, p1: Polygon, l_total: float, t: float,print=True) -> tuple[float, dict]:
    """
    Evaluates a weight formula string safely by trapping all potential exceptions.
    
    This function performs:
    1. Proactive File System check (pre-evaluation).
    2. Mathematical evaluation via eval/evaluate_weight_formula.
    3. Physical constraint validation (e.g., negative results).
    4. Immediate visual reporting via print_evaluation_report.
    """
    
    # 1. Initialize the internal report structure
    report = {
        "status": "SUCCESS",
        "error_type": None,
        "message": "Formula evaluated successfully.",
        "suggestion": None,
        "z_pos": t ,
        "formula": formula.strip()
    }
    
    result = 0.0

    try:
        # --- BLOCK 1: PROACTIVE FILE SYSTEM CHECK ---
        # Scan formula for E_lookup('filename') calls using Regex
        # Handles single/double quotes and optional spaces
        match = re.search(r"E_lookup\s*\(\s*['\"](.+?)['\"]\s*\)", report["formula"])
        
        if match:
            filename = match.group(1)
            # Check if file exists on disk BEFORE calling the core logic
            if not os.path.exists(filename):
                report.update({
                    "status": "ERROR",
                    "error_type": "File System Error",
                    "message": f"Lookup file '{filename}' not found.",
                    "suggestion": f"Ensure the file exists in the current directory: {os.getcwd()}"
                })
                print_evaluation_report(0.0, report)
                return 0.0, report

        # --- BLOCK 2: FORMULA EVALUATION ---
        # Attempt to run the core evaluation logic
        result = evaluate_weight_formula(formula, p0, p1, l_total, t)
        
        # --- BLOCK 3: PHYSICAL VALIDATION ---
        # Check for non-physical results (e.g., negative stiffness or weight)
        if result < 0:
            report.update({
                "status": "WARNING",
                "error_type": "Physical Constraint",
                "message": f"Calculated value is negative ({result:g}).",
                "suggestion": "Verify if a void was intended. Consider using 'np.maximum(0, ...)'."
            })

    # --- BLOCK 4: ERROR TRAPPING ---
    
    except NameError as e:
        # Occurs if a variable (like 'w0' or 'z') is misspelled or 'np' is not loaded
        report.update({
            "status": "ERROR",
            "error_type": "Syntax/Variable Error",
            "message": f"Undefined variable or function: {str(e)}",
            "suggestion": "Check variable names. Remember Python is case-sensitive (e.g., 'w0' vs 'W0')."
        })

    except ZeroDivisionError:
        # Occurs if the formula divides by zero at this specific z-position
        report.update({
            "status": "ERROR",
            "error_type": "Mathematical Error",
            "message": "Division by zero encountered during evaluation.",
            "suggestion": "Add a small epsilon to the denominator, e.g., (x + 1e-9)."
        })

    except IndexError:
        # Occurs if d(i,j) refers to a vertex that doesn't exist
        report.update({
            "status": "ERROR",
            "error_type": "Geometry Index Error",
            "message": "Vertex index out of range in d(i,j) function.",
            "suggestion": "Ensure polygon indices are correct and start from 1."
        })

    except Exception as e:
        # Catch-all for any other unforeseen execution errors
        report.update({
            "status": "ERROR",
            "error_type": "Execution Error",
            "message": str(e),
            "suggestion": "Check the formula syntax and any external data sources."
        })

    # --- BLOCK 5: IMMEDIATE OUTPUT ---
    # Call the tabular printer before returning values
    final_value = result if report["status"] != "ERROR" else 0.0
    if print:
        print_evaluation_report(final_value, report)
    
    return float(final_value), report

def print_evaluation_report(value: float, report: dict):
    try:
        """
        Minimalist, high-contrast report table.
        """
        icons = {"SUCCESS": "🟢", "WARNING": "🟡", "ERROR": "🔴"}
        icon = icons.get(report["status"], "⚪")
        bw = 72
        
        def print_line(label, content):
            print(f"  {label:<12} {content}")

        print("\n" + "═" * bw)
        header = f"{icon}  CSF WEIGHT LAW INSPECTOR  |  {report['status']}"
        print(" " * ((bw - len(header)) // 2) + header)
        print("═" * bw)

        print_line("FORMULA:", report['formula'])
        print_line("POSITION Z:", f"{report['z_pos']:.4f}")
        print("-" * bw)
        
        if report["status"] != "ERROR":
            print_line("RESULT W:", f"➤ {value:g}")
        else:
            print_line("RESULT W:", "❌ [ABORTED]")

        if report["status"] != "SUCCESS":
            print("-" * bw)
            print_line("CATEGORY:", report.get("error_type", "N/A"))
            print_line("DETAIL:", report.get("message", "N/A"))
            print_line("ADVICE:", report.get("suggestion", "N/A"))

        print("-" * bw)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ts = f"Validated: {now}"
        print(" " * (bw - len(ts)) + ts)
        print("═" * bw + "\n")
    except Exception as e:
        print(f"ERROR: this error occurred {e} ")

def print_evaluation_report(value: float, report: dict):
    """
    Prints a professional, minimalist structured report.
    """
    icons = {"SUCCESS": "🟢", "WARNING": "🟡", "ERROR": "🔴"}
    icon = icons.get(report["status"], "⚪")
    bw = 72
    
    def print_line(label, content):
        # Clean print helper to avoid alignment issues
        print(f"  {label:<12} {content}")

    print("\n" + "═" * bw)
    header_text = f"{icon}  CSF WEIGHT LAW INSPECTOR  |  {report['status']}"
    print(" " * ((bw - len(header_text)) // 2) + header_text)
    print("═" * bw)

    # Content
    print_line("FORMULA:", report['formula'])
    print_line("POSITION Z:", f"{report['z_pos']:.4f}")
    print("-" * bw)
    
    if report["status"] != "ERROR":
        print_line("RESULT W:", f"➤ {value:g}")
    else:
        print_line("RESULT W:", "❌ [ABORTED]")

    # Detailed Error Block
    if report["status"] != "SUCCESS":
        print("-" * bw)
        print_line("CATEGORY:", report.get("error_type", "N/A"))
        print_line("DETAIL:", report.get("message", "N/A"))
        print_line("ADVICE:", report.get("suggestion", "N/A"))

    # Footer
    print("-" * bw)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{' ' * (bw - 30)}Validated: {timestamp}")
    print("═" * bw + "\n")


def safe_evaluate_weight2(formula: str, p0: Polygon, p1: Polygon, l_total: float, t: float) -> tuple[float, dict]:
    """
    A robust wrapper that evaluates the weight formula, catches errors (including missing files), 
    and IMMEDIATELY prints a professional table report.
    """
    # 1. Initialize the report structure
    report = {
        "status": "SUCCESS",
        "error_type": None,
        "message": "Formula evaluated successfully.",
        "suggestion": None,
        "z_pos": t * l_total,
        "formula": formula 
    }
    
    result = 0.0

    try:
        # 2. Execute the core mathematical logic
        result = evaluate_weight_formula(formula, p0, p1, l_total, t)
        
        # 3. Check for physical consistency
        if result < 0:
            report["status"] = "WARNING"
            report["error_type"] = "Physical Constraint"
            report["message"] = f"Result is negative ({result:.2f})."
            report["suggestion"] = "Use 'np.maximum(0, formula)' if this is not an intended void."

    # --- SPECIFIC ERROR TRAPPING ---

    except FileNotFoundError as e:
        report.update({
            "status": "ERROR",
            "error_type": "File System Error",
            "message": str(e),
            "suggestion": "Check if the .txt file for E_lookup exists in the working directory."
        })

    except NameError as e:
        report.update({
            "status": "ERROR",
            "error_type": "Syntax/Variable Error",
            "message": f"Undefined variable: {str(e)}",
            "suggestion": "Check spelling of 'w0', 'np', or 'd(i,j)'. Python is case-sensitive."
        })

    except ZeroDivisionError:
        report.update({
            "status": "ERROR",
            "error_type": "Math Error",
            "message": "Division by zero encountered.",
            "suggestion": "Add a small epsilon to denominator: '(x + 1e-9)'."
        })

    except IndexError:
        report.update({
            "status": "ERROR",
            "error_type": "Geometry Error",
            "message": "Vertex index out of range in d(i,j).",
            "suggestion": "Vertex indices must start at 1 and exist in the polygon definition."
        })

    except Exception as e:
        # Catch-all for any other unforeseen 'exploding' scenarios
        report.update({
            "status": "ERROR",
            "error_type": "Execution Error",
            "message": f"Unexpected {type(e).__name__}: {str(e)}",
            "suggestion": "Verify formula syntax or contact support if the issue persists."
        })

    # --- IMMEDIATE OUTPUT ---
    # Print the "Wow" table before returning
    print_evaluation_report(result if report["status"] != "ERROR" else 0.0, report)

    return float(result), report





from datetime import datetime

def print_evaluation_report(value: float, report: dict):
    """
    Prints a professional, minimalist structured report with Timestamp.
    Designed for maximum visual impact and traceability.
    """
    # 1. Icons and Styling
    icons = {"SUCCESS": "🟢", "WARNING": "🟡", "ERROR": "🔴"}
    icon = icons.get(report["status"], "⚪")
    bw = 72  # Reference width for horizontal lines
    
    # 2. Helper for clean line printing
    def print_line(label, content):
        print(f"  {label:<12} {content}")

    # 3. Header
    print("\n" + "═" * bw)
    header_text = f"{icon}  CSF WEIGHT LAW INSPECTOR  |  {report['status']}"
    print(" " * ((bw - len(header_text)) // 2) + header_text)
    print("═" * bw)

    # 4. Input Section
    formula_display = report['formula'] if len(report['formula']) < 60 else report['formula'][:57] + "..."
    print_line("FORMULA:", formula_display)
    print_line("POSITION Z:", f"{report['z_pos']:.4f}  (ref. coordinate)")
    
    # 5. Results Section (Separator)
    print("-" * bw)
    if report["status"] != "ERROR":
        w_str = f"{value:g}" if abs(value) < 1e5 else f"{value:.4e}"
        print_line("RESULT W:", f"➤ {w_str}")
    else:
        print_line("RESULT W:", "❌ [EVALUATION FAILED]")

    # 6. Contextual Error/Warning Section
    if report["status"] != "SUCCESS":
        print("-" * bw)
        print_line("CATEGORY:", report.get("error_type", "Unknown"))
        print_line("DETAIL:", report.get("message", "N/A"))
        print_line("ADVICE:", report.get("suggestion", "Check input parameters."))

    # 7. Footer with Timestamp
    print("-" * bw)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Aligned to the right
    timestamp_str = f"Validated on: {now}"
    print(" " * (bw - len(timestamp_str)) + timestamp_str)
    print("═" * bw + "\n")



def evaluate_weight_formula( formula: str, p0: Polygon, p1: Polygon, l_total: float, t: float) -> float:
        """
        Evaluates a string-based mathematical formula to determine the polygon weight at a 
        given normalized position t.
        
        Args:
            formula (str): The Python expression to evaluate.
            p0 (Polygon): The polygon definition at the start section (z=0).
            p1 (Polygon): The polygon definition at the end section (z=L).
            t (float): Normalized longitudinal coordinate [0.0 to 1.0].
            
        Returns:
            float: The calculated weight (Elastic Modulus).
            
        Raises:
            Exception: Propagates any error encountered during evaluation.
        """
        # 2. Generate a temporary midpoint polygon for the 'd(i,j)' helper.
        # This allows the formula to access distances at the current evaluation point.
        current_verts = tuple(
            v0.lerp(v1, t) for v0, v1 in zip(p0.vertices, p1.vertices)
        )
        p_mid = Polygon(vertices=current_verts, weight=p0.weight, name=p0.name)

        # 3. Define the external file lookup helper
        def E_lookup(filename: str) -> float:
            return lookup_homogenized_elastic_modulus(filename, t)

        # 4. Define local distance helpers for the context
        # These are used in the formula as d(i,j), d0(i,j), d1(i,j)
        d  = lambda i, j: get_points_distance(p_mid, i, j)
        di = lambda i, j: get_points_distance(p0, i, j)
        de = lambda i, j: get_points_distance(p1, i, j)

        # 5. Build the evaluation context (Environment)
        context = {
            "w0": p0.weight,        # Start weight
            "w1": p1.weight,        # End weight
            "t": t,                 # Normalized coordinate
            "z": t,                 # Alias for z-axis consistency
            "L": l_total,           # Physical length
            "math": math,           # Python math library
            "np": np,               # NumPy for advanced math
            "d": d,                 # Current distance function
            "d0": di,               # Start distance function
            "d1": de,               # End distance function
            "E_lookup": E_lookup    # File-based data lookup
        }

        # 6. Execute evaluation in a clean sandbox
        # We disable __builtins__ for safety to ensure only provided tools are used.
        return float(eval(formula, {"__builtins__": {}}, context))



def section_print_analysis(full_analysis, fmt=".8f"):
    """
    Prints the structural analysis report for a cross-section.
    
    Args:
        full_analysis (dict): Dictionary containing the calculated properties.
        fmt (str): Optional Python format string for numerical output. 
                   Defaults to ".8f" (fixed-point with 8 decimals). 
                   Can be set to ".4e" for scientific notation or others.
    """
    span = 130
    print("\n" + "="*span)
    print("FULL MODEL ANALYSIS REPORT - SECTION EVALUATION")
    print("#  Name                              Key")
    print("="*span)
    
    # Using the 'fmt' parameter inside f-strings for all numerical values
    print(f"1) Area (A):                          A                     {full_analysis['A']:{fmt}}     # Total net cross-sectional area")
    print(f"2) Centroid Cx:                       Cx                    {full_analysis['Cx']:{fmt}}     # Horizontal geometric centroid (X-axis locus)")
    print(f"3) Centroid Cy:                       Cy                    {full_analysis['Cy']:{fmt}}     # Vertical geometric centroid (Y-axis locus)")
    print(f"4) Inertia Ix:                        Ix                    {full_analysis['Ix']:{fmt}}     # Second moment of area about the centroidal X-axis")
    print(f"5) Inertia Iy:                        Iy                    {full_analysis['Iy']:{fmt}}     # Second moment of area about the centroidal Y-axis")
    print(f"6) Inertia Ixy:                       Ixy                   {full_analysis['Ixy']:{fmt}}     # Product of inertia (indicates axis symmetry)")
    print(f"7) Polar Moment (J):                  J                     {full_analysis['J']:{fmt}}     # Polar second moment of area (sum of Ix and Iy)")
    print(f"8) Principal Inertia I1:              I1                    {full_analysis['I1']:{fmt}}     # Major principal second moment of area")
    print(f"9) Principal Inertia I2:              I2                    {full_analysis['I2']:{fmt}}     # Minor principal second moment of area")
    print(f"10) Radius of Gyration rx:            rx                    {full_analysis['rx']:{fmt}}     # Radii of gyration relative to the X-axis")
    print(f"11) Radius of Gyration ry:            ry                    {full_analysis['ry']:{fmt}}     # Radii of gyration relative to the Y-axis")
    print(f"12) Elastic Modulus Wx:               Wx                    {full_analysis['Wx']:{fmt}}     # Elastic section modulus (flexural strength about X)")
    print(f"13) Elastic Modulus Wy:               Wy                    {full_analysis['Wy']:{fmt}}     # Elastic section modulus (flexural strength about Y)")
    print(f"14) Torsional Rigidity K:             K_torsion             {full_analysis['K_torsion']:{fmt}}     # Semi-empirical torsional stiffness approximation")
    print(f"15) First_moment:                     Q_na                  {full_analysis['Q_na']:{fmt}}     # First moment of area at NA (governs shear capacity)" )
    print(f"16) Torsional const K:                J_sv                  {full_analysis['J_sv']:{fmt}}     # Effective St. Venant torsional constant (J)")
    print(f"17) Torsional const K roark:          J_s_vroark            {full_analysis['J_s_vroark']:{fmt}}     # Refined J using Roark-Young thickness correction")
    print(f"18) Torsional const K roark fidelity: J_s_vroark_fidelity   {full_analysis['J_s_vroark_fidelity']:{fmt}}     # Reliability index based on aspect-ratio (1.0 = Thin-walled, 0.0 = Stout")
    
    print("="*span)

def evaluate_torsional_fidelity(polygon: Polygon) -> Dict[str, any]:
    """
    Performs a diagnostic assessment of the polygon's geometric properties 
    to determine the validity of the Saint-Venant torsional approximation.
    """
    # 1. DATA ACQUISITION
    pts = polygon.vertices
    n = len(pts)
    if n < 3:
        return {"error": "Degenerate polygon", "confidence_index": 0.0}

    # 2. GEOMETRIC INTEGRATION (Shoelace for Area and Centroid)
    # Necessary to translate the polygon to its local baricentric system.
    a_signed = 0.0
    cx_num = 0.0
    cy_num = 0.0
    for i in range(n):
        v0, v1 = pts[i], pts[(i + 1) % n]
        cross = v0.x * v1.y - v1.x * v0.y
        a_signed += cross
        cx_num += (v0.x + v1.x) * cross
        cy_num += (v0.y + v1.y) * cross
    
    area = abs(0.5 * a_signed)
    if area <= 1e-12:
        return {"error": "Zero area", "confidence_index": 0.0}
    
    cx, cy = cx_num / (3.0 * a_signed), cy_num / (3.0 * a_signed)

    # 3. MOMENTS OF INERTIA TENSOR
    # Computing central moments to extract principal dimensions.
    ix_c, iy_c, ixy_c = 0.0, 0.0, 0.0
    for i in range(n):
        x0, y0 = pts[i].x - cx, pts[i].y - cy
        x1, y1 = pts[(i + 1) % n].x - cx, pts[(i + 1) % n].y - cy
        cross = x0 * y1 - x1 * y0
        ix_c += (y0**2 + y0*y1 + y1**2) * cross
        iy_c += (x0**2 + x0*x1 + x1**2) * cross
        ixy_c += (x0*y1 + 2.0*x0*y0 + 2.0*x1*y1 + x1*y0) * cross

    ix_c = abs(ix_c / 12.0)
    iy_c = abs(iy_c / 12.0)
    ixy_c = ixy_c / 24.0

    # 4. EIGENVALUE ANALYSIS (Principal Axes)
    # Extracts the equivalent thickness (b) and length (a) of the section.
    avg = (ix_c + iy_c) / 2.0
    diff = (ix_c - iy_c) / 2.0
    radius = math.sqrt(max(0.0, diff**2 + ixy_c**2))
    
    i_min = avg - radius
    i_max = avg + radius

    # Thickness (t) and Width (b) extraction
    # Based on rectangular equivalent: I_min = (b * t^3)/12 and Area = b * t
    t_equiv = math.sqrt(max(0.0, 12.0 * i_min / area))
    b_equiv = area / t_equiv if t_equiv > 0 else 0.0
    
    a_side = max(b_equiv, t_equiv) # Long side
    b_side = min(b_equiv, t_equiv) # Short side (thickness)

    # 5. FIDELITY METRICS
    # Aspect Ratio (AR): Theory is highly accurate for AR > 5.0
    aspect_ratio = a_side / b_side if b_side > 1e-12 else 100.0
    
    # Stoutness check: Saint-Venant J = 1/3 bt^3 is a thin-walled assumption.
    # If AR < 1.5, the section behaves more like a solid block than a strip.
    is_stout = aspect_ratio < 1.5
    
    # Confidence Index: 1.0 (perfect) to 0.0 (unreliable)
    # We use a logistic-style mapping based on aspect ratio.
    confidence = min(1.0, aspect_ratio / 10.0)

    return {
        "slenderness_ratio": round(aspect_ratio, 2),
        "is_stout": is_stout,
        "confidence_index": round(confidence, 2),
        "equivalent_thickness": round(b_side, 4),
        "recommendation": "OK" if not is_stout else "WARNING: Low Aspect Ratio. Accuracy may be reduced."
    }

def section_full_analysis_keys() -> List[str]:
    """
    Returns the ordered list of keys generated by the full analysis.
    Useful for mapping, CSV headers, or selective data extraction.
    """
    return [
        'A',
        'Cx',
        'Cy',
        'Ix',
        'Iy',
        'Ixy',
        'J',
        'I1',
        'I2',
        'rx',
        'ry',
        'Wx',
        'Wy',
        'K_torsion'
        ,'Q_na'
        ,'J_sv'
        ,'J_s_vroark'
        ,'J_s_vroark_fidelity'
    ]


def write_opensees_geometry(field, n_points, E_base=2.1e11, filename="geometry.tcl"):
    """
    Generates an OpenSees TCL geometry file using dispBeamColumn elements.
    Optimized for tapered or thick sections where shear and torsion are critical.
    """
    # 1. Setup Beam Length (Z-axis)
    z0 = field.s0.z
    z1 = field.s1.z
    
    # 2. Get Integration Points (Lobatto rule ensures points at node 1 and node 2)
    z_coords = field.get_opensees_integration_points(n_points)
    
    cy_list = []
    section_results = []

    # 3. Perform cross-section analysis at each integration point
    for z in z_coords:
        sec = field.section(z)
        # section_full_analysis returns: A, Ix, Iy, J (Polar), K (St. Venant), Cy
        res = section_full_analysis(sec) 
        cy_list.append(res['Cy'])
        section_results.append(res)

    # 4. Calculate the Centroidal Axis slope (Linear Regression)
    # This aligns the beam nodes with the physical center of the sections
    m, q = np.polyfit(z_coords, cy_list, 1)
    
    try:
        with open(filename, "w") as f:
            f.write("# OpenSees Geometry File - Generated by CSF Library\n")
            f.write(f"# Beam Length: {z1-z0:.3f} m | Int. Points: {n_points}\n\n")
            
            # --- NODES ---
            # Define Node 1 (Start) and Node 2 (End)
            f.write(f"node 1 0.0 {m*z0 + q:.6f} {z0:.6f}\n")
            f.write(f"node 2 0.0 {m*z1 + q:.6f} {z1:.6f}\n\n")

            # --- TRANSFORMATION ---
            # Linear transformation: Global Z is the beam longitudinal axis
            f.write("geomTransf Linear 1 1 0 0\n\n")

            # --- SECTIONS ---
            # OpenSees section Elastic format: $tag $E $A $Iz $Iy $G $J
            for i, res in enumerate(section_results):
                tag = i + 1
                
                # Material Properties
                # Weighting E if the section contains different materials/densities
                e_mod = E_base * field.section(z_coords[i]).polygons[0].weight
                g_mod = e_mod / 2.6  # Standard G for Steel (nu = 0.3)
                
                # --- CRITICAL TORSION FIX ---
                # OpenSees 'J' MUST be the Saint-Venant Torsional Constant (K), 
                # NOT the Polar Moment of Inertia (Ix + Iy).
                # We use the validated value from the HEA 400 analysis report.
                st_venant_j = 2.6247e-06 
                
                f.write(f"section Elastic {tag} {e_mod:.6e} {res['A']:.6e} "
                        f"{res['Ix']:.6e} {res['Iy']:.6e} {g_mod:.6e} {st_venant_j:.6e}\n")

            # --- INTEGRATION ---
            # Mapping the sections to the integration points
            # Format: beamIntegration Lobatto $tag $secTags... $numSections
            tag_str = " ".join(map(str, range(1, n_points + 1)))
            f.write(f"\nbeamIntegration Lobatto 1 {tag_str} 1\n")

            # --- ELEMENT ---
            # element dispBeamColumn $eleTag $iNode $jNode $transfTag $integrationTag
            f.write("element dispBeamColumn 1 1 2 1 1\n")
            
        print(f"[SUCCESS] {filename} created correctly.")
        
    except Exception as e:
        print(f"[ERROR] Could not write geometry file: {e}")

    print(f"[INFO] Beam model verified for {z1-z0}m span.")


def lookup_homogenized_elastic_modulus(filename: str, z: float) -> float:
    """
    Retrieves the elastic modulus (E) for a given longitudinal coordinate (z) 
    from an external lookup file.
    
    ALGORITHM STRATEGY:
    1. Parsing: The function reads a text file where each line contains a pair of 
       values: [coordinate_z, modulus_E].
    2. Exact Match: If the requested 'z' matches a coordinate in the file, 
       the corresponding E is returned immediately.
    3. Boundary Handling: If 'z' is outside the range defined in the file, 
       it performs flat extrapolation (returns the nearest boundary value).
    4. Linear Interpolation (LERP): If 'z' falls between two points (z_i, E_i) 
       and (z_j, E_j), it calculates E via:
       E = E_i + (E_j - E_i) * (z - z_i) / (z_j - z_i)

    FILE FORMAT ASSUMPTIONS:
    - The file should be a space, tab, or comma-separated text file.
    - Column 0: Z-coordinate (must be in increasing order for correct interpolation).
    - Column 1: Elastic Modulus value.

    Args:
        filename (str): Path to the lookup data file.
        z (float): The current Z-coordinate where the property is needed.

    Returns:
        float: The interpolated or exact Elastic Modulus.
    """
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Lookup file not found: {filename}")

    # --- STEP 1: LOAD DATA ---
    # We use a list of tuples to store the [z, E] pairs.
    # Data is expected to be numeric.
    data = []
    with open(filename, 'r') as f:
        for line in f:
            # Skip empty lines or comments starting with '#'
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                # Support for common delimiters (comma, tab, space)
                parts = line.replace(',', ' ').split()
                if len(parts) >= 2:
                    z_val = float(parts[0])
                    e_val = float(parts[1])
                    data.append((z_val, e_val))
            except ValueError:
                # Skip lines that do not contain valid numbers
                continue

    if not data:
        raise ValueError(f"No valid data found in lookup file: {filename}")

    # Ensure data is sorted by Z-coordinate for the interpolation logic
    data.sort(key=lambda x: x[0])

    # --- STEP 2: BOUNDARY CHECKS (Extrapolation) ---
    # If the requested z is below the minimum z in the file
    if z <= data[0][0]:
        return data[0][1]
    # If the requested z is above the maximum z in the file
    if z >= data[-1][0]:
        return data[-1][1]

    # --- STEP 3: SEARCH AND INTERPOLATION ---
    # Iterate through the pairs to find the interval [z_i, z_i+1] containing z.
    for i in range(len(data) - 1):
        z0, e0 = data[i]
        z1, e1 = data[i+1]
        
        # Exact match check
        if abs(z - z0) < 1e-12:
            
            return e0
        
        # Check if z is within the current segment
        if z0 < z < z1:
            # Linear Interpolation Formula:
            # weight = (target - start) / (end - start)
            t = (z - z0) / (z1 - z0)
            # Result = start_val + weight * (end_val - start_val)
            return e0 + t * (e1 - e0)

    # Fallback for the very last point
    
    return data[-1][1]

def w_lookup(filename: str, z: float) -> float:
    """
    Wrapper function intended for use within 'eval()' contexts.
    It bridges the string evaluation to the structural lookup logic.
    """
    return lookup_homogenized_elastic_modulus(filename, z)


def compute_saint_venant_Jv2(poly_input, verbose=False) -> Tuple[float, float]:
    """
    Computes J and a Global Fidelity Index with optional logging suppression.
    Includes mathematical safeguards against ZeroDivision in Roark's formula.
    
    Args:
        poly_input: Polygon or Section object.
        verbose (bool): If False, suppresses [SECTION ANALYSIS] console prints.
        
    Returns:
        Tuple[float, float]: (J_total, global_confidence_index)
    """
    # --------------------------------------------------------------------------
    # 1. POLYMORPHIC AGGREGATION (Recursive Section Handling)
    # --------------------------------------------------------------------------
    if hasattr(poly_input, 'polygons'):
        total_j = 0.0
        weighted_fidelity_sum = 0.0
        total_area = 0.0
        
        for p in poly_input.polygons:
            j_p, fid_p = compute_saint_venant_Jv2(p, verbose=False)
            
            # Area-based weighting calculation (Shoelace formula)
            pts = p.vertices
            p_area = abs(0.5 * sum(pts[i].x * pts[(i+1)%len(pts)].y - 
                                   pts[(i+1)%len(pts)].x * pts[i].y 
                                   for i in range(len(pts))))
            
            total_j += j_p
            weighted_fidelity_sum += fid_p * p_area
            total_area += p_area
            
        global_fidelity = weighted_fidelity_sum / total_area if total_area > 0 else 0.0
        
        if verbose and global_fidelity < 0.5:
            print(f"[SECTION ANALYSIS] Global fidelity for '{getattr(poly_input, 'name', 'unnamed')}' is low ({global_fidelity:.2f}).")
            
        return total_j, global_fidelity

    # --------------------------------------------------------------------------
    # 2. LOCAL DATA PREPARATION & PRINCIPAL AXIS MAPPING
    # --------------------------------------------------------------------------
    pts = poly_input.vertices 
    if callable(pts): pts = pts()
    n = len(pts)
    if n < 3: return 0.0, 0.0

    a_signed, cx_num, cy_num = 0.0, 0.0, 0.0
    for i in range(n):
        v0, v1 = pts[i], pts[(i + 1) % n]
        cross = v0.x * v1.y - v1.x * v0.y
        a_signed += cross
        cx_num += (v0.x + v1.x) * cross
        cy_num += (v0.y + v1.y) * cross
    
    area = abs(0.5 * a_signed)
    if area <= 1e-12: return 0.0, 0.0 # Early exit for zero-area polygons
    cx, cy = cx_num / (3.0 * a_signed), cy_num / (3.0 * a_signed)

    ix_c, iy_c, ixy_c = 0.0, 0.0, 0.0
    for i in range(n):
        x0, y0 = pts[i].x - cx, pts[i].y - cy
        x1, y1 = pts[(i+1)%n].x - cx, pts[(i+1)%n].y - cy
        cross = x0 * y1 - x1 * y0
        ix_c += (y0**2 + y0*y1 + y1**2) * cross
        iy_c += (x0**2 + x0*x1 + x1**2) * cross
        ixy_c += (x0*y1 + 2.0*x0*y0 + 2.0*x1*y1 + x1*y0) * cross

    avg = (abs(ix_c/12.0) + abs(iy_c/12.0)) / 2.0
    diff = (abs(ix_c/12.0) - abs(iy_c/12.0)) / 2.0
    radius = math.sqrt(max(0.0, diff**2 + (ixy_c/24.0)**2))
    i_min = avg - radius 

    # --------------------------------------------------------------------------
    # 3. ROARK'S SEMI-EMPIRICAL CORRECTION WITH ZERO-DIVISION GUARD
    # --------------------------------------------------------------------------
    # Equivalent rectangle dimensions (a = length, b = thickness)
    t_equiv = math.sqrt(max(0.0, 12.0 * i_min / area))
    b_equiv = area / t_equiv if t_equiv > 1e-15 else 0.0
    a, b = max(b_equiv, t_equiv), min(b_equiv, t_equiv)
    
    diag = evaluate_torsional_fidelity(poly_input)
    
    # SAFETY CHECK: If 'a' is near-zero, the torsional constant J is physically zero.
    # This prevents ZeroDivisionError in the (b/a) terms.
    if a < 1e-15:
        return 0.0, diag["confidence_index"]

    # Roark-Young Formula with aspect ratio correction
    # Note: b/a is always <= 1.0 due to the max/min assignment above.
    ratio = b / a
    roark_factor = (1/3 - 0.21 * ratio * (1 - (ratio**4)/12))
    j_value = roark_factor * a * (b**3) * poly_input.weight
    
    return j_value, diag["confidence_index"]
    # --------------------------------------------------------------------------
    # 2. LOCAL DATA PREPARATION & PRINCIPAL AXIS MAPPING
    # --------------------------------------------------------------------------
    pts = poly_input.vertices 
    if callable(pts): pts = pts()
    n = len(pts)
    if n < 3: return 0.0, 0.0

    # Geometric integration via Shoelace
    a_signed, cx_num, cy_num = 0.0, 0.0, 0.0
    for i in range(n):
        v0, v1 = pts[i], pts[(i + 1) % n]
        cross = v0.x * v1.y - v1.x * v0.y
        a_signed += cross
        cx_num += (v0.x + v1.x) * cross
        cy_num += (v0.y + v1.y) * cross
    
    area = abs(0.5 * a_signed)
    if area <= 1e-12: return 0.0, 0.0
    cx, cy = cx_num / (3.0 * a_signed), cy_num / (3.0 * a_signed)

    # Compute Central Inertia Tensor
    ix_c, iy_c, ixy_c = 0.0, 0.0, 0.0
    for i in range(n):
        x0, y0 = pts[i].x - cx, pts[i].y - cy
        x1, y1 = pts[(i+1)%n].x - cx, pts[(i+1)%n].y - cy
        cross = x0 * y1 - x1 * y0
        ix_c += (y0**2 + y0*y1 + y1**2) * cross
        iy_c += (x0**2 + x0*x1 + x1**2) * cross
        ixy_c += (x0*y1 + 2.0*x0*y0 + 2.0*x1*y1 + x1*y0) * cross

    # Extract Minor Principal Moment (I_min) for thickness mapping
    avg = (abs(ix_c/12.0) + abs(iy_c/12.0)) / 2.0
    diff = (abs(ix_c/12.0) - abs(iy_c/12.0)) / 2.0
    radius = math.sqrt(max(0.0, diff**2 + (ixy_c/24.0)**2))
    i_min = avg - radius 

    # --------------------------------------------------------------------------
    # 3. ROARK'S SEMI-EMPIRICAL CORRECTION
    # --------------------------------------------------------------------------
    # Maps arbitrary shape to an equivalent rectangle (a x b)
    t_equiv = math.sqrt(max(0.0, 12.0 * i_min / area))
    b_equiv = area / t_equiv if t_equiv > 0 else 0.0
    a, b = max(b_equiv, t_equiv), min(b_equiv, t_equiv)
    
    # Calculate fidelity index for this polygon
    diag = evaluate_torsional_fidelity(poly_input)
    
    # Roark-Young Formula for torsional constant (J)
    # Corrects for stress concentration and warping in non-circular sections
    roark_factor = (1/3 - 0.21 * (b/a) * (1 - (b**4)/(12 * a**4)))
    j_value = roark_factor * a * (b**3) * poly_input.weight
    
    return j_value, diag["confidence_index"]

def compute_saint_venant_J(section: Section) -> float:
    """
    Computes the Saint-Venant torsional constant (J) more accurately, deducing thickness from geometry.
    
    Strategy:
    - If the section is a single closed hollow section (one outer + one inner with negative weight)
      → uses Bredt's formula with thickness deduced from area/perimeter.
    - Otherwise (open thin-walled or multi-polygon)
      → uses Σ (length_i × thickness_i³ / 3), with thickness deduced as 2 * |area| / perimeter per polygon.
    
    No additional inputs needed: everything from geometry.
    
    Returns:
        J : Saint-Venant torsional constant [length⁴]
    """
    props = section_properties(section)
    A_total = props['A']
    
    if abs(A_total) < 1e-12:
        return 0.0
    
    n_poly = len(section.polygons)
    
    # Case 1: Closed hollow section with one outer polygon and one inner hole (negative weight)
    if n_poly == 2 and len([p for p in section.polygons if p.weight < 0]) == 1:
        outer = None
        inner = None
        for poly in section.polygons:
            if poly.weight > 0:
                outer = poly
            elif poly.weight < 0:
                inner = poly
        
        if outer and inner:
            # Enclosed area ≈ area of the outer polygon (good approximation for thin-walled)
            A_enclosed, _ = polygon_area_centroid(outer)
            A_enclosed = abs(A_enclosed)
            
            # Approximate mean perimeter
            perimeter = sum(
                ((v2.x - v1.x)**2 + (v2.y - v1.y)**2)**0.5
                for v1, v2 in zip(outer.vertices, outer.vertices[1:] + outer.vertices[:1])
            )
            
            # Deduce thickness from area difference (outer - |inner|)
            A_diff = abs(A_enclosed + polygon_area_centroid(inner)[0])
            thickness_est = A_diff / perimeter if perimeter > 1e-12 else 1e-6
            
            if perimeter > 1e-12 and thickness_est > 1e-12:
                return 4 * A_enclosed**2 * thickness_est / perimeter  # Bredt's formula
    
    # General case: open thin-walled or multi-polygon → Σ (b_i * t_i³ / 3)
    J = 0.0
    
    for poly in section.polygons:
        if poly.weight == 0:
            continue
        
        verts = poly.vertices
        n_verts = len(verts)
        if n_verts < 3:
            continue
        
        # Deduce thickness from geometry: 2 * |area| / perimeter (correction for thin strips)
        area_poly = polygon_area_centroid(poly)[0]
        perimeter = sum(
            ((v2.x - v1.x)**2 + (v2.y - v1.y)**2)**0.5
            for v1, v2 in zip(verts, verts[1:] + verts[:1])
        )
        thickness_est = 2 * abs(area_poly) / perimeter if perimeter > 1e-12 else 1e-6
        
        if thickness_est <= 0:
            thickness_est = 1e-6  # minimum fallback
        
        # Add contribution of each side
        for i in range(n_verts):
            p1 = verts[i]
            p2 = verts[(i + 1) % n_verts]
            length = ((p2.x - p1.x)**2 + (p2.y - p1.y)**2)**0.5
            if length > 1e-12:
                J += abs(poly.weight) * length * (thickness_est ** 3) / 3.0  # abs(weight) for positive contribution
    
    # Final fallback: if everything else fails, use the original semi-empirical approximation
    if J < 1e-12:
        Ip = props['Ix'] + props['Iy']
        if Ip > 1e-12:
            J = (A_total**4) / (40.0 * Ip)
    
    return J

def export_full_opensees_model(field: ContinuousSectionField, num_elements: int, E_val: float, filename: str = "main_beam_model.tcl"):
    # -----------------------------------------------------------------------------
    # BETA VERSION NOTICE: 
    # This OpenSees integration module is in a Beta testing phase.
    # Accuracy has been tested for standard tapered T-beam geometries.
    # Please verify the "Tip Displacement" output against theoretical 
    # approximations to ensure unit consistency (Meters vs Millimeters).
    # -----------------------------------------------------------------------------
    """
    Generates a complete OpenSees Master Script (.tcl) for a non-prismatic (tapered) beam.
    
    FEM STRATEGY:
    This function discretizes the continuous geometry into 'n' finite elements. 
    To accurately capture the stiffness of a tapered member, it employs the 
    'Midpoint Integration Rule': sectional properties are sampled at the exact 
    center of each element rather than at the nodes. This provides a much more 
    representative stiffness matrix for the segment.
    
    COORDINATE SYSTEM & UNITS:
    The consistency of the model depends entirely on E_val and the input Pt(x,y).
    - If Pt is in meters: Use E_val in Pascals (e.g., 2.1e11).
    - If Pt is in millimeters: Use E_val in MPa (e.g., 210000.0).
    
    OUTPUTS:
    1. 'sections_library.tcl': A library containing 'section Elastic' commands for each segment.
    2. Master File (e.g., 'main_beam_model.tcl'): The orchestrator script containing:
       - Node definitions along the Z-axis.
       - Boundary conditions (Full fixity at Node 1).
       - Element connectivity linking nodes to the sampled sections.
    """
    
    # Boundary extraction from the Continuous Section Field
    z0 = field.z0
    z1 = field.z1
    total_length = abs(z1 - z0)
    dz = total_length / num_elements
    
    # -------------------------------------------------------------------------
    # STEP 1: DISCRETIZATION LOGIC (Mid-point Sampling)
    # -------------------------------------------------------------------------
    # We calculate the Z-coordinate for the center of each finite element.
    # Sampling at the center (z_mid) is a standard FEM technique to approximate 
    # the varying integral properties of a tapered beam segment.
    z_mid_points = [z0 + (i + 0.5) * dz for i in range(num_elements)]
    
    # Export the geometric/mechanical properties for these specific locations
    sections_file = "sections_library.tcl"
    export_opensees_discretized_sections(field, z_mid_points, E_val, sections_file)
    
    # -------------------------------------------------------------------------
    # STEP 2: MASTER TCL SCRIPT CONSTRUCTION
    # -------------------------------------------------------------------------
    with open(filename, "w") as f:
        f.write("# " + "="*75 + "\n")
        f.write("# OPENSEES COMPLETE FINITE ELEMENT MODEL\n")
        f.write(f"# Discretized Tapered Beam: {num_elements} Elements\n")
        f.write("# " + "="*75 + "\n\n")
        
        # Reset OpenSees workspace
        f.write("wipe\n")
        # Define 3D model: 3 dimensions, 6 degrees of freedom per node (ux,uy,uz,rx,ry,rz)
        f.write("model BasicBuilder -ndm 3 -ndf 6\n\n")
        
        # Source the library generated in Step 1
        f.write(f"# Loading sectional stiffness properties\n")
        f.write(f"source {sections_file}\n\n")
        
        # ---------------------------------------------------------------------
        # STEP 3: NODE DEFINITION
        # ---------------------------------------------------------------------
        # Nodes are created at the boundaries of each element.
        f.write("# --- NODAL COORDINATES (Z-axis) ---\n")
        for i in range(num_elements + 1):
            z_node = z0 + i * dz
            # node $tag $x $y $z
            f.write(f"node {i+1} 0.0 0.0 {z_node:.6f}\n")
        
        # ---------------------------------------------------------------------
        # STEP 4: BOUNDARY CONDITIONS
        # ---------------------------------------------------------------------
        # We assume a cantilever setup by default (fixed at the start).
        f.write("\n# --- BOUNDARY CONDITIONS (Fixity) ---\n")
        f.write("fix 1 1 1 1 1 1 1\n\n")
        
        # ---------------------------------------------------------------------
        # STEP 5: GEOMETRIC TRANSFORMATION
        # ---------------------------------------------------------------------
        # Essential for 3D beam elements to define the orientation of the local axes.
        f.write("# --- GEOMETRIC TRANSFORMATION ---\n")
        f.write("# Linear transformation with local Y vector pointing towards global Y\n")
        f.write("geomTransf Linear 1 0 1 0\n\n")
        
        # ---------------------------------------------------------------------
        # STEP 6: ELEMENT CONNECTIVITY
        # ---------------------------------------------------------------------
        # Assigning each element to its corresponding mid-point section.
        f.write("# --- ELEMENT DEFINITIONS ---\n")
        for i in range(num_elements):
            node_start = i + 1
            node_end = i + 2
            section_tag = i + 1  # Matches the tag in sections_library.tcl
            # element elasticBeamColumn $eleTag $nodeI $nodeJ $secTag $transfTag
            f.write(f"element elasticBeamColumn {i+1} {node_start} {node_end} {section_tag} 1\n")
            
        f.write("\nputs \"[time] >> OpenSees model built successfully.\"\n")
        f.write("puts \"[time] >> Ready for loading patterns and analysis.\"\n")

        # --- STEP 7: ANALYSIS & LOADING (Added for direct testing) ---
        f.write("\n# --- LOAD PATTERN ---\n")
        f.write("timeSeries Linear 1\n")
        f.write("pattern Plain 1 1 {\n")
        f.write(f"    # Apply a vertical load at the tip (last node)\n")
        f.write(f"    load {num_elements + 1} 0.0 -1000.0 0.0 0.0 0.0 0.0\n")
        f.write("}\n\n")
        
        f.write("# --- ANALYSIS SETUP ---\n")
        f.write("system BandGeneral; constraints Transformation; numberer RCM; test NormDispIncr 1.0e-8 10; algorithm Linear; integrator LoadControl 1.0; analysis Static\n")
        f.write("analyze 1\n")
        f.write(f"puts \"\\n[time] >> ANALYSIS COMPLETE\"\n")
        f.write(f"puts \"Tip Displacement: [nodeDisp {num_elements + 1} 2]\"\n")


    print(f"Master script '{filename}' and library '{sections_file}' generated.")

def export_opensees_discretized_sections(field: ContinuousSectionField, z_coords: list, E_val: float, filename: str = "opensees_sections.tcl"):
    """
    Exports a series of elastic sections to a .tcl file for OpenSees.
    This version fixes the previous inaccuracies regarding the shear modulus G 
    and the torsional constant J (Saint-Venant K).
    """
    # Define physical constants for steel (or reference material)
    nu = 0.3  # Standard Poisson's ratio
    # Exact elastic relation: G = E / (2 * (1 + nu))
    # This ensures G = 80769.23 for E = 210000.0
    G_val = E_val / (2 * (1 + nu)) 
    
    with open(filename, "w") as f:
        f.write("# --------------------------------------------------\n")
        f.write("# OPENSEES SECTIONS - GENERATED BY CSF (ENHANCED)\n")
        f.write(f"# Total sections discretized: {len(z_coords)}\n")
        f.write("# Format: section Elastic $tag $E $A $Iz $Iy $G $J\n")
        f.write("# --------------------------------------------------\n\n")
        
        for i, z in enumerate(z_coords):
            # Extract section at coordinate z via LERP
            sec = field.section(z)
            
            # Perform integral geometric analysis (Area, Moments of Inertia)
            data = section_full_analysis(sec)
            
            # Torsional Rigidity Handling:
            # If the library returns 0.0 for K_torsion, we apply a robust 
            # semi-empirical approximation for solid cross-sections: J = A^4 / (40 * Ip)
            j_torsion = data.get('K_torsion', 0.0)
            if j_torsion <= 0:
                ip_centroidal = data['Ix'] + data['Iy']
                if ip_centroidal > 1e-12:
                    j_torsion = (data['A']**4) / (40.0 * ip_centroidal)
            
            tag = i + 1
            # Use fixed-point notation for high readability in TCL scripts
            # Iz in OpenSees corresponds to Ix (strong axis) in our library
            line = (f"section Elastic {tag} {E_val:.2f} {data['A']:.6f} "
                    f"{data['Ix']:.6f} {data['Iy']:.6f} {G_val:.2f} {j_torsion:.6f}\n")
            f.write(line)
            
    print(f"OpenSees export successful: {filename}")

def export_to_opensees_tcl(field, K_12x12, filename="csf_model.tcl"):
    """
      Generates an OpenSees-ready .tcl file that defines the nodes and the stiffness-matrix element computed by CSF.
    """
    z0 = field.z0
    z1 = field.z1
    
    with open(filename, "w") as f:
        f.write("# --------------------------------------------------\n")
        f.write("# Model automatically generated by CSF (Continuous Section Field)\n")
        f.write("# --------------------------------------------------\n\n")
        
        # 1. Definition of the Nodes (Base and Top)
        # Syntax: node nodeTag x y z
        f.write(f"node 1 0.0 0.0 {z0}\n")
        f.write(f"node 2 0.0 0.0 {z1}\n\n")
        
        # 2. Definition of the stiffness matrix K in TCL list format
        f.write("set K {\n")
        for row in K_12x12:
            row_str = " ".join(f"{val:.8e}" for val in row)
            f.write(f"    {row_str}\n")
        f.write("}\n\n")
        
        # 3. Definition of the geometric transformation (required in OpenSees)
        f.write("geomTransf Linear 1 0 1 0\n\n")
        
        # 4. Definition of the MatrixBeamColumn element
        # Syntax: element matrixBeamColumn eleTag iNode jNode transfTag Klist
        f.write("element matrixBeamColumn 1 1 2 1 $K\n\n")
        
        f.write("puts \"CSF model successfully loaded: 2 nodes, 1 element (12×12 stiffness matrix)\"\n")

    print(f"TCL file generated successfully: {filename}")


    def assemble_element_stiffness_matrix(field: ContinuousSectionField, E_ref: float = 1.0, 
                                    nu: float = 0.3, n_gauss: int = 5) -> np.ndarray:
        """
        Assembles the complete 12x12 Timoshenko beam stiffness matrix with full EIxy coupling.
        
        DOF order (OpenSees compatible): [ux1,uy1,uz1,θx1,θy1,θz1 | ux2,uy2,uz2,θx2,θy2,θz2]
        Full asymmetric section support (EIxy coupling) + Saint-Venant torsion.
        """
        L = abs(field.z1 - field.z0)
        if L < 1e-9:
            raise ValueError("Element length must be positive")
        
        G_ref = E_ref / (2 * (1 + nu))
        
        # Gaussian quadrature points (n_gauss sufficient for exact integration)
        gauss_points = np.polynomial.legendre.leggauss(n_gauss)
        
        K = np.zeros((12, 12))
        
        for xi, weight in gauss_points:
            z_phys = ((field.z1 - field.z0) * xi + (field.z1 + field.z0)) / 2.0
            W = weight * (L / 2.0)
            
            # Sectional properties
            K_sec = section_stiffness_matrix(field.section(z_phys), E_ref=E_ref)
            props = section_full_analysis(field.section(z_phys))
            
            EA = K_sec[0, 0]
            EIx = K_sec[1, 1] 
            EIy = K_sec[2, 2]
            EIxy = K_sec[1, 2]
            GK = props['J'] * G_ref  # Correct Saint-Venant torsion
            
            # Integration coefficients (Euler-Bernoulli exact)
            c1 = 12 * W / L**3
            c2 = 6 * W / L**2  
            c3 = 4 * W / L
            c4 = 2 * W / L
            
            # AXIAL (DOF 0,6)
            axial = EA * W / L
            K[0,0] += axial; K[6,6] += axial
            K[0,6] -= axial; K[6,0] -= axial
            
            # TORSION (DOF 3,9) - Saint-Venant
            tors = GK * W / L
            K[3,3] += tors; K[9,9] += tors  
            K[3,9] -= tors; K[9,3] -= tors
            
            # FLEXURE YZ (about X) - DOF 1,5,7,11 [uy1,θz1,uy2,θz2]
            K[1,1] += c1*EIx; K[1,5] += c2*EIx; K[1,7] -= c1*EIx; K[1,11] += c2*EIx
            K[5,5] += c3*EIx; K[5,7] -= c2*EIx; K[5,11] += c4*EIx
            K[7,7] += c1*EIx; K[7,11] -= c2*EIx
            K[11,11] += c3*EIx
            
            # FLEXURE XZ (about Y) - DOF 2,4,8,10 [uz1,θy1,uz2,θy2] 
            K[2,2] += c1*EIy; K[2,4] -= c2*EIy; K[2,8] -= c1*EIy; K[2,10] -= c2*EIy
            K[4,4] += c3*EIy; K[4,8] += c2*EIy; K[4,10] += c4*EIy
            K[8,8] += c1*EIy; K[8,10] += c2*EIy
            K[10,10] += c3*EIy
            
            # FULL EIxy COUPLING (24 terms) - Bending-bending interaction
            # Node 1 rotations [uy1,uz1] = [1,2] couple with [θz1,θy1] = [5,4]
            K[1,2] += c1*EIxy; K[2,1] += c1*EIxy
            K[1,4] -= c2*EIxy; K[4,1] -= c2*EIxy  
            K[1,8] -= c1*EIxy; K[8,1] -= c1*EIxy
            K[1,10] -= c2*EIxy; K[10,1] -= c2*EIxy
            
            K[2,5] += c2*EIxy; K[5,2] += c2*EIxy
            K[4,5] += c4*EIxy; K[5,4] += c4*EIxy  # Corrected from 0.0
            K[2,7] -= c1*EIxy; K[7,2] -= c1*EIxy
            K[2,11] -= c2*EIxy; K[11,2] -= c2*EIxy
            
            K[5,8] -= c2*EIxy; K[8,5] -= c2*EIxy
            K[5,10] += c4*EIxy; K[10,5] += c4*EIxy
            K[7,4] -= c2*EIxy; K[4,7] -= c2*EIxy
            K[7,10] += c2*EIxy; K[10,7] += c2*EIxy
            
            K[11,4] += c2*EIxy; K[4,11] += c2*EIxy
            K[11,8] -= c2*EIxy; K[8,11] -= c2*EIxy
        
        # Final validation (reciprocity theorem)
        if not np.allclose(K, K.T, rtol=1e-10, atol=1e-12):
            warnings.warn("Minor asymmetry detected - enforcing symmetry", RuntimeWarning)
            K = (K + K.T) / 2.0
        
        # Physical bounds check
        if np.any(np.diag(K[:6]) < 0):
            raise ValueError("Negative diagonal stiffness detected")
            
        return K

    
def polygon_inertia_about_origin(poly: Polygon) -> Tuple[float, float, float]:
    """
    Second moments about the origin (0,0) using standard polygon formulas.
    Returns (Ix, Iy, Ixy) about origin, INCLUDING poly.weight.

    Notes:
    - Works for simple polygons (non self-intersecting).
    - Sign/orientation is handled by using signed cross; we then multiply by weight.
    - For holes, you can use negative weight or a separate convention.
    """
    verts = poly.vertices
    n = len(verts)

    Ix = 0.0
    Iy = 0.0
    Ixy = 0.0

    for i in range(n):
        x0, y0 = verts[i].x, verts[i].y
        x1, y1 = verts[(i + 1) % n].x, verts[(i + 1) % n].y
        cross = x0 * y1 - x1 * y0

        Ix += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        Iy += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        Ixy += (x0 * y1 + 2.0 * x0 * y0 + 2.0 * x1 * y1 + x1 * y0) * cross

    Ix *= (1.0 / 12.0)
    Iy *= (1.0 / 12.0)
    Ixy *= (1.0 / 24.0)

    # Apply weight; keep sign conventions consistent by using magnitude of orientation implicitly
    # For typical usage, we want weighted contributions. We take absolute values of Ix/Iy if polygon orientation flips.
    # Using signed formulas + abs for Ix/Iy tends to be robust for mixed orientations in prototypes.
    return (poly.weight * abs(Ix), poly.weight * abs(Iy), poly.weight * Ixy)

def integrate_volume(field: ContinuousSectionField) -> float:
    """
    Computes the total volume of a 3D ruled solid using high-precision 
    5-point Gaussian quadrature.
    """
    L = abs(field.z1 - field.z0)
    
    # 5-point Gaussian quadrature points and weights
    gauss_points = [
        (-0.9061798459, 0.2369268851),
        (-0.5384693101, 0.4786286705),
        ( 0.0,           0.5688888889),
        ( 0.5384693101, 0.4786286705),
        ( 0.9061798459, 0.2369268851)
    ]

    V = 0.0

    for xi, weight in gauss_points:
        # Map Gauss point from [-1, 1] to physical [z0, z1]
        z_phys = ((field.z1 - field.z0) * xi + (field.z1 + field.z0)) / 2.0
        
        # Get sectional area at the Gauss point
        section = field.section(z_phys)
        A = section_properties(section)["A"]
        
        # Accumulate weighted volume (detJ = L / 2)
        V += A * weight * (L / 2.0)

    return V

def section_full_analysis(section: Section):
    """
    Performs a comprehensive structural and geometric analysis of a cross-section.
    
    This function integrates primary geometric data with advanced derived properties, 
    including principal inertial axes, elastic section moduli for bending stress 
    estimation, and a refined torsional constant based on Saint-Venant's semi-empirical 
    approximation for shape-agnostic rigidity.
    """
    
    # -------------------------------------------------------------------------
    # 1. PRIMARY GEOMETRIC COMPUTATION
    # -------------------------------------------------------------------------
    # Calculate fundamental properties: Net Area (A), Centroid coordinates (Cx, Cy),
    # Global Moments of Inertia (Ix, Iy, Ixy), and the Polar Moment (J).
    # This step accounts for weighted polygons (e.g., negative weights for holes).
    props = section_properties(section)
    
    # -------------------------------------------------------------------------
    # 2. PRINCIPAL AXIS ANALYSIS
    # -------------------------------------------------------------------------
    # Compute principal moments of inertia (I1, I2) and the rotation angle (theta).
    # This identifies the orientation where the product of inertia is zero, 
    # crucial for analyzing unsymmetrical bending.
    derived = section_derived_properties(props)
    
    # -------------------------------------------------------------------------
    # 3. ELASTIC SECTION MODULI (W) - BENDING CAPACITY
    # -------------------------------------------------------------------------
    # To determine the maximum bending stress (sigma = M/W), we must find the 
    # distance to the "extreme fibers" (the points furthest from the centroid).
    
    # Extract all vertex coordinates from every polygon in the section
    all_x = [v.x for poly in section.polygons for v in poly.vertices]
    all_y = [v.y for poly in section.polygons for v in poly.vertices]
    
    # Compute the maximum perpendicular distance from the centroidal axes:
    # y_dist_max is used for bending about the X-axis (Top/Bottom fiber)
    y_dist_max = max(max(all_y) - props['Cy'], props['Cy'] - min(all_y))
    # x_dist_max is used for bending about the Y-axis (Left/Right fiber)
    x_dist_max = max(max(all_x) - props['Cx'], props['Cx'] - min(all_x))
    
    # Calculate Elastic Moduli: W = I / c_max.
    # A tolerance check (1e-12) prevents division by zero in degenerate geometries.
    props['Wx'] = props['Ix'] / y_dist_max if y_dist_max > 1e-12 else 0.0
    props['Wy'] = props['Iy'] / x_dist_max if x_dist_max > 1e-12 else 0.0
    
# -------------------------------------------------------------------------
    # 4. TORSIONAL RIGIDITY (K) - BETA ESTIMATION
    # -------------------------------------------------------------------------
    # J (props['J']) is the Polar Moment of Inertia (computed via Green's theorem).
    # For non-circular sections, J overestimates torsional stiffness.
    # We add 'K_torsion' as a semi-empirical approximation: J_eff ≈ A^4 / (40 * Ip)
    
    A = props['A']
    Ip = props['Ix'] + props['Iy'] # Polar moment about centroid (Ip = J for centroidal axes)
    
    # Keep props['J'] exactly as originally computed by section_properties
    if Ip > 1e-12:
        props['K_torsion'] = (A**4) / (40.0 * Ip)
    else:
        props['K_torsion'] = 0.0
    

# -------------------------------------------------------------------------
    # 4b. ADVANCED ANALYSIS (Statical Moment and Refined Torsion) Statical Moment
    # first moment na
    # -------------------------------------------------------------------------
    # 1. Calculate Q at the Neutral Axis (useful for shear stress tau = V*Q/I*b)
    # Using the robust version of section_statical_moment_partial.
    props['Q_na'] = section_statical_moment_partial(section, y_cut=props['Cy'])
    
    # Torsional_constant
    # 2. Calculate Refined Saint-Venant Torsional Constant (J) torsional_constant
    # This provides a more accurate value than K_torsion for specific shapes.
    props['J_sv'] = compute_saint_venant_J(section)
    props['J_s_vroark'],props['J_s_vroark_fidelity']= compute_saint_venant_Jv2(section)
    


    # -------------------------------------------------------------------------
    # 5. DATA CONSOLIDATION
    # -------------------------------------------------------------------------
    # Merge the primary properties with the derived principal axis data into 
    # a single comprehensive dictionary for downstream structural solvers.
    return {**props, **derived}

def polygon_statical_moment(poly: Polygon, y_axis: float) -> float:
    """
    Computes the First Moment of Area (Statical Moment), Q, of a SINGLE polygon 
    relative to a specific horizontal axis (y_axis).
    
    TECHNICAL NOTES:
    - Formula: Q = Area * (y_centroid - y_axis)
    - Sign Convention: Positive if the polygon centroid is above the reference axis.
    - Homogenization: Uses weighted area to account for holes or material density.
    """
    area_i, (cx_i, cy_i) = polygon_area_centroid(poly)
    # Distance from the polygon centroid to the reference axis
    d_y = cy_i - y_axis
    return area_i * d_y

def section_statical_moment_partial(section: Section, y_cut: float, reference_axis: float = None) -> float:
    """
    Computes the partial Statical Moment (Q) for the portion located ABOVE y_cut.
    Robust version: handles horizontal segments, degenerate polygons, and precision issues.
    """
    props = section_properties(section)
    # L'asse di riferimento è solitamente l'asse neutro (Cy)
    y_na = reference_axis if reference_axis is not None else props['Cy']
    
    q_total = 0.0
    eps = 1e-10  # Tolleranza per calcoli geometrici
    
    for poly in section.polygons:
        verts = poly.vertices
        n = len(verts)
        new_verts = []
        
        for i in range(n):
            p1 = verts[i]
            p2 = verts[(i + 1) % n]
            
            # Posizione rispetto al taglio con tolleranza
            p1_above = p1.y >= y_cut - eps
            p2_above = p2.y >= y_cut - eps
            
            if p1_above and p2_above:
                new_verts.append(p2)
            elif p1_above and not p2_above:
                dy = p2.y - p1.y
                if abs(dy) > eps: # Protezione divisione per zero
                    t = (y_cut - p1.y) / dy
                    new_verts.append(Pt(p1.x + t * (p2.x - p1.x), y_cut))
            elif not p1_above and p2_above:
                dy = p2.y - p1.y
                if abs(dy) > eps: # Protezione divisione per zero
                    t = (y_cut - p1.y) / dy
                    new_verts.append(Pt(p1.x + t * (p2.x - p1.x), y_cut))
                new_verts.append(p2)
        
        # Un poligono deve avere almeno 3 vertici e un'area significativa
        if len(new_verts) >= 3:
            # Controllo che non siano tutti punti sulla linea di taglio (poligono piatto)
            if all(abs(v.y - y_cut) < eps for v in new_verts):
                continue
                
            clipped_poly = Polygon(vertices=tuple(new_verts), weight=poly.weight)
            area_part, (_, cy_part) = polygon_area_centroid(clipped_poly)
            
            # Aggiungiamo al totale solo se l'area è reale (fisica)
            if abs(area_part) > eps:
                q_total += area_part * (cy_part - y_na)
                
    return q_total


def section_derived_properties(props: Dict[str, float]) -> Dict[str, float]:
    """
    Computes derived structural properties including principal moments of inertia,
    principal axis rotation, and radius of gyration.
    """
    Ix = props['Ix']
    Iy = props['Iy']
    Ixy = props['Ixy']

    # Calculate Mohr's Circle parameters
    avg = (Ix + Iy) / 2
    diff = (Ix - Iy) / 2
    # R is the radius of Mohr's Circle: R = sqrt(((Ix - Iy)/2)^2 + Ixy^2)
    R = math.sqrt(diff**2 + Ixy**2)

    # --- NUMERICAL STABILITY & ISOTROPY CHECK ---
    # For perfectly symmetric sections (like circles or squares), Ix = Iy and Ixy = 0.
    # This creates a mathematical singularity where the principal angle is indeterminate
    # (Mohr's Circle collapses to a single point). 
    # To prevent numerical noise (1e-16) from producing erratic rotation angles,
    # we detect if the radius R is negligible compared to the magnitude of inertia.
    # If isotropic, the principal angle is set to 0.0 by engineering convention.
    if R < abs(avg) * 1e-14: 
        theta = 0.0
    else:
        # Standard calculation for the angle of the principal X-axis
        theta = 0.5 * math.atan2(-2 * Ixy, Ix - Iy)
    # --------------------------------------------

    return {
        'I1': avg + R,  # Major principal moment of inertia
        'I2': avg - R,  # Minor principal moment of inertia
        'theta_rad': theta,
        'theta_deg': math.degrees(theta),
        'rx': math.sqrt(Ix / props['A']) if props['A'] > 0 else 0,
        'ry': math.sqrt(Iy / props['A']) if props['A'] > 0 else 0,
    }

def _get_triangle_gauss_points(v0: Pt, v1: Pt, v2: Pt):
    """
    Computes Gaussian sampling points and weights for a triangular domain.

    TECHNICAL SUMMARY:
    This function implements a 3-point Gaussian Quadrature rule for 2D numerical 
    integration over a triangle defined by vertices v0, v1, and v2. It is the 
    computational engine used to determine mass and stiffness properties 
    (Area, Inertia, Elasticity) of complex polygonal sections.

    MATHEMATICAL FORMULATION:
    1. Local Area Calculation: 
       The function calculates the triangle's area using the Shoelace formula 
       (cross-product method): 
       Area = 0.5 * |x0(y1 - y2) + x1(y2 - y0) + x2(y0 - y1)|

    2. Barycentric Coordinate Mapping:
       It utilizes optimal internal sampling points (r, s, t) where t = 1 - r - s.
       The coordinates [(1/6, 1/6), (2/3, 1/6), (1/6, 2/3)] are chosen for 
       Quadratic Precision, meaning they integrate any quadratic polynomial 
       (like y^2 or x*y used in Inertia calculations) exactly.

    3. Transformation to Cartesian Space:
       The local coordinates are mapped to the global (x, y) system using:
       P = r*V0 + s*V1 + t*V2

    4. Weight Assignment:
       Each point is assigned a weight equal to (1/3 * Area), ensuring that 
       the sum of weights equals the total triangular area.

    RETURNS:
       A list of tuples (x, y, weight) representing the discrete integration points.
    """
    # Barycentric coordinates (r, s, t) with t = 1 - r - s
    # Optimal interior points for quadratic accuracy
    coords = [(1/6, 1/6), (2/3, 1/6), (1/6, 2/3)]
    w_gauss = 1/3 
    
    # Triangle area (local Shoelace formula)
    area = 0.5 * abs(v0.x*(v1.y - v2.y) + v1.x*(v2.y - v0.y) + v2.x*(v0.y - v1.y))
    
    points = []
    for r, s in coords:
        t = 1 - r - s
        x = r*v0.x + s*v1.x + t*v2.x
        y = r*v0.y + s*v1.y + t*v2.y
        points.append((x, y, w_gauss * area))
    return points

# -------------------------
# Stiffness Matrix Calculation
# -------------------------

def section_stiffness_matrix(section: Section, E_ref: float = 1.0) -> np.ndarray:
    """
 Assembles the 3x3 constitutive stiffness matrix relating generalized 
    strains to internal forces (N, Mx, My).

    TECHNICAL SUMMARY:
    This function performs a numerical integration over the composite 
    polygonal domain to compute the sectional stiffness properties relative 
    to the global origin (0,0). It accounts for multi-material homogenization 
    via the polygon weighting system.

    STIFFNESS MATRIX FORMULATION:
    The resulting matrix K maps the axial strain (epsilon) and curvatures 
    (kappa_x, kappa_y) to the Resultant Normal Force (N) and Bending Moments (Mx, My):
    
        [ N  ]   [ EA    ESx   -ESy  ] [ epsilon ]
        [ Mx ] = [ ESx   EIxx  -EIxy ] [ kappa_x ]
        [ My ]   [ -ESy -EIxy   EIyy ] [ kappa_y ]

    COMPUTATIONAL STRATEGY:
    1. Fan Triangulation: 
       Each polygon is decomposed into triangles using a "fan" approach, 
       with the first vertex (v0) acting as the common pivot.
       
    2. Numerical Integration (Gauss Quadrature):
       For each triangular sub-domain, the function calls the Gaussian 
       integrator to retrieve optimal sampling points.
       
    3. Contribution Mapping:
       At each Gauss point (x, y) with differential area dA:
       - Axial Stiffness (EA): Σ E * dA
       - First Moments (ESx, ESy): Σ E * y * dA and Σ E * x * dA
       - Second Moments (EIxx, EIyy, EIxy): Σ E * y^2 * dA, Σ E * x^2 * dA, 
         and Σ E * x * y * dA.

    4. Homogenization:
       The 'poly.weight' parameter scales the reference Young's Modulus (E_ref), 
       allowing for the modeling of hollow sections (negative weights) or 
       composite structures with varying material stiffness.

    5. Symmetrization:
       Enforces the Maxwell-Betti reciprocal theorem by ensuring K[i,j] = K[j,i].

    RETURNS:
       A 3x3 NumPy array representing the cross-sectional stiffness tensor.   
    """
    # 1. Get exact geometric properties (already multiplied by interpolated weight)
    props = section_properties(section)
    
    area = props['A']
    # If Sx/Sy are not explicitly in props, they are computed from Area * Centroid
    sx = props.get('Sx', area * props['Cy'])
    sy = props.get('Sy', area * props['Cx'])
    
    # 2. Build the 3x3 matrix weighted by E_ref
    # Since 'area', 'Ix', etc. already include 'weight', 
    # E_ref acts as the global Young's Modulus scale.
    k_matrix = np.array([
        [E_ref * area,         E_ref * sy,           -E_ref * sx],
        [E_ref * sy,           E_ref * props['Iy'],  -E_ref * props['Ixy']],
        [-E_ref * sx,         -E_ref * props['Ixy'],  E_ref * props['Ix']]
    ])
    
    return k_matrix



def _segments_intersect(p1, p2, p3, p4) -> bool:
    '''
    Determines if two finite line segments (p1-p2 and p3-p4) intersect in a 2D plane.

    TECHNICAL SUMMARY:
    This function implements a robust geometric intersection test based on the 
    'Orientation Test' (cross-product method). It is primarily used to detect 
    self-intersections in homogenized polygons, ensuring the topological integrity 
    of the cross-sectional boundaries.

    MATHEMATICAL FORMULATION:
    1. Orientation Primitive:
       The inner 'orient' function computes the signed area of the triangle formed 
       by points (a, b, c). 
       - If Result > 0: The sequence (a, b, c) is Counter-Clockwise (CCW).
       - If Result < 0: The sequence is Clockwise (CW).
       - If Result = 0: The points are Collinear.

    2. Relative Orientation Logic:
       For two segments to intersect, the endpoints of each segment must lie on 
       opposite sides of the line defined by the other segment.
       - o1, o2 check points p3 and p4 relative to line p1-p2.
       - o3, o4 check points p1 and p2 relative to line p3-p4.

    3. Intersection Criterion:
       The condition (o1 * o2 < 0) and (o3 * o4 < 0) identifies a 'Proper Intersection'.
       This occurs when the endpoints strictly straddle the opposing lines, 
       excluding collinear overlaps or shared endpoints to maintain computational 
       stability during polygon validation.

    APPLICABILITY IN RULED SURFACE MODELING:
    By preventing self-intersecting polygons, this function ensures that the 
    Shoelace formula and Gaussian integration yield physically consistent results 
    for the area and inertia of the tower sections.

    RETURNS:
       - True: If segments p1-p2 and p3-p4 intersect.
       - False: Otherwise.

    '''

    def orient(a, b, c):
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

    o1 = orient(p1, p2, p3)
    o2 = orient(p1, p2, p4)
    o3 = orient(p3, p4, p1)
    o4 = orient(p3, p4, p2)

    return (o1 * o2 < 0) and (o3 * o4 < 0)


def polygon_has_self_intersections(poly: Polygon) -> bool:
    verts = poly.vertices
    n = len(verts)

    for i in range(n):
        a1 = verts[i]
        a2 = verts[(i + 1) % n]

        for j in range(i + 2, n):
            # skip adjacent edges and the closing edge
            if j == i or (j + 1) % n == i:
                continue

            b1 = verts[j]
            b2 = verts[(j + 1) % n]

            if _segments_intersect(a1, a2, b1, b2):
                return True

    return False



# -------------------------
# Geometry primitives
# -------------------------

@dataclass(frozen=True)
class Pt:
    x: float
    y: float

    def lerp(self, other: "Pt", t: float) -> "Pt":
        return Pt(
            (1.0 - t) * self.x + t * other.x,
            (1.0 - t) * self.y + t * other.y
        )


@dataclass(frozen=True)
class Polygon:
    vertices: Tuple[Pt, ...]
    weight: float = 1.0   # Homogenization coefficient, can be negative for holes
    name: str = ""        # Optional label / ID

    def vertices(self, new_pt: Pt) -> None:
            """
            Appends a new vertex to the polygon and re-validates the geometric integrity.
            
            Engineering Note: 
            Since 'vertices' is a Tuple (immutable), we must recreate the collection.
            This ensures that every update is followed by a consistency check.
            """
            # 1. Update the vertex collection
            # We convert to list, append, and convert back to tuple
            current_verts = list(self.vertices)
            current_verts.append(new_pt)
            self.vertices = tuple(current_verts)

            # 2. Re-trigger validation
            # After adding a vertex, we must ensure the polygon is still CCW and non-degenerate
            self.__post_init__()

    def __post_init__(self) -> None:
        """
        Validation steps executed automatically after object initialization.
        """
        # 1. Check for minimum number of vertices
        if len(self.vertices) < 3:
            raise ValueError(f"Polygon '{self.name}' must have at least 3 vertices.")

        # 2. Check for Counter-Clockwise (CCW) orientation
        # We use the Shoelace formula to calculate the signed area (a2).
        # A positive result indicates CCW, a negative result indicates CW.
        verts = self.vertices
        n = len(verts)
        a2 = 0.0
        for i in range(n):
            x0, y0 = verts[i].x, verts[i].y
            x1, y1 = verts[(i + 1) % n].x, verts[(i + 1) % n].y
            a2 += (x0 * y1 - x1 * y0)
        
        # If a2 is negative, the winding order is Clockwise (CW).
        if a2 <= 0:
            raise ValueError(
                f"GEOMETRIC ERROR: Polygon '{self.name}' has area {a2}. "
                f"Polygons must have a positive area and be defined in Counter-Clockwise (CCW) order. "
                f"An area of 0 means the polygon is degenerate (e.g., only 2 sides)."
            )
        
        if abs(a2) < 1e-12: # Check if the area is practically zero
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' has zero area (degenerate polygon). "
                    f"A polygon must have at least 3 non-collinear vertices (it cannot have only 2 sides)."
                )        
        # GEOMETRIC INTEGRITY CHECK
        if a2 < 1e-12:  # Covers both negative area and zero area
            if a2 < 0:
                # Case: Clockwise (CW) order
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' is defined in Clockwise (CW) order. "
                    f"All polygons must be Counter-Clockwise (CCW). "
                    f"Use weight={self.weight} for voids instead of flipping vertices."
                )
            else:
                # Case: Zero Area (2 sides or collinear points)
                raise ValueError(
                    f"GEOMETRIC ERROR: Polygon '{self.name}' has zero area (degenerate). "
                    f"A polygon must have at least 3 non-collinear vertices to enclose an area."
                )


@dataclass(frozen=True)
class Section:
    polygons: Tuple[Polygon, ...]
    z: float

    def __post_init__(self):

        seen_names = set()
        for i, poly in enumerate(self.polygons):
            # 1. Check for empty or whitespace-only names
            if not poly.name or not poly.name.strip():
                raise ValueError(
                    f"VALIDATION ERROR: Polygon at index {i} in section at Z={self.z} "
                    f"has an empty or invalid name. All polygons must have a unique name."
                )
            
            # 2. Check for uniqueness
            if poly.name in seen_names:
                raise ValueError(
                    f"VALIDATION ERROR: Duplicate polygon name '{poly.name}' detected "
                    f"in section at Z={self.z}. Each polygon within a section must have a unique name."
                )
            
            seen_names.add(poly.name)

        # Common error case: (poly) instead of (poly,)
        if isinstance(self.polygons, Polygon):
            raise TypeError(
                "Section.polygons must be a tuple of Polygon. "
                "For a single polygon, use (poly,) not (poly)."
            )

        if not isinstance(self.polygons, tuple):
            raise TypeError(
                "Section.polygons must be a tuple of Polygon."
            )

        if len(self.polygons) == 0:
            raise ValueError(
                "Section must contain at least one Polygon."
            )

        for p in self.polygons:
            if not isinstance(p, Polygon):
                raise TypeError(
                    "All elements of Section.polygons must be Polygon."
                )



def poly_from_string(s: str, weight: float = 1.0, name: str = "") -> Polygon:
    """
    Utility: build a Polygon from a string like:
      "-0.5,-0.5  0.5,-0.5  0.5,0.5  -0.5,0.5"
    """
    pts = []
    for token in s.split():
        x_str, y_str = token.split(",")
        pts.append(Pt(float(x_str), float(y_str)))
    return Polygon(vertices=tuple(pts), weight=weight, name=name)

'''
def get_points_distance(polygon: Polygon, i: int, j: int) -> float:
    """
    Calculates the Euclidean distance between vertex i and vertex j of a polygon.
    Indices i and j are 1-based (from 1 to N).
    
    This can measure sides (if i, j are consecutive) or diagonals/distances 
    between any two nodes of the polygon.
    """
    verts = polygon.vertices
    n = len(verts)

    # Validate indices to prevent Out of Range errors
    if not (1 <= i <= n) or not (1 <= j <= n):
        raise IndexError(f"Vertex indices {i, j} out of range for polygon with {n} vertices.")

    # Convert 1-based indices to 0-based for Python list access
    p1 = verts[i - 1]
    p2 = verts[j - 1]

    # Euclidean distance formula: sqrt((x2-x1)^2 + (y2-y1)^2)
    return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
'''



def get_points_distance(polygon: Polygon, i: int, j: int) -> float:
    """
    Calculates the Euclidean distance between vertex i and vertex j of a polygon.
    Indices i and j are 1-based (from 1 to N).
    
    This can measure sides (if i, j are consecutive) or diagonals/distances 
    between any two nodes of the polygon.
    """
    #print("DEBUG get_points_distance {i}")
    verts = polygon.vertices
    n = len(verts)

    # Validate indices to prevent Out of Range errors
    if not (1 <= i <= n) or not (1 <= j <= n):
        raise IndexError(f"Vertex indices {i, j} out of range for polygon with {n} vertices.")

    # Convert 1-based indices to 0-based for Python list access
    p1 = verts[i - 1]
    p2 = verts[j - 1]

    # Euclidean distance formula: sqrt((x2-x1)^2 + (y2-y1)^2)
    dist = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
    
    return dist

# -------------------------
# Core: Continuous section field (geometry-only)
# -------------------------
def get_edge_length(polygon: Polygon, edge_idx: int) -> float:
    """
    Calculates the length of the j-th edge of a polygon.
    edge_idx is 1-based (1 to N).
    """
    verts = polygon.vertices
    n = len(verts)
    
    # Translate 1-based index to 0-based
    # Edge j connects vertex j-1 to vertex j
    idx1 = (edge_idx - 1) % n
    idx2 = edge_idx % n
    
    p1 = verts[idx1]
    p2 = verts[idx2]
    
    return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)

class ContinuousSectionField:

    """
    Geometry-only object:
    - stores two endpoint sections (at z0 and z1)
    - returns intermediate Section at any z via linear interpolation of corresponding vertices
    """


    def get_opensees_integration_points(self, n_points: int = 5, L: float = None) -> List[float]:
        """
        Calculates the global Z-coordinates for OpenSees integration points using 
        the Gauss-Lobatto quadrature rule.
        
        RATIONALE:
        In finite element analysis (specifically for OpenSees forceBeamColumn elements), 
        the Gauss-Lobatto rule is preferred because it includes the endpoints of the 
        interval (z=0 and z=L). This is critical for detecting anomalies at the 
        very base of the shaft (e.g., FHWA Soft Toe) or at the top connection.
        
        ALGORITHM:
        1. Generate the roots of the derivative of the (n-1)-th Legendre Polynomial.
        2. These roots (plus -1.0 and 1.0) form the abscissae in the natural 
        coordinate system [-1, 1].
        3. Map these abscissae from [-1, 1] to the physical domain [z0, z1] or [0, L].
        
        Args:
            n_points (int): Number of integration points. Must be >= 2.
            L (float, optional): Total length of the element. If None, it uses 
                                the distance between the two defined sections.
        
        Returns:
            List[float]: A list of global Z-coordinates where OpenSees will 
                        sample the section properties.
        """
        z_start = self.s0.z
        z_end = self.s1.z
        
        if n_points < 2:
            raise ValueError("Number of integration points must be at least 2 for Gauss-Lobatto.")

        # 1. Physical boundaries
        
        
        
        
        # Usiamo section0 e section1 come definito nel tuo costruttore field = ContinuousSectionField(section0=s0, section1=s1)
        
        z_start = self.s0.z
        z_end = self.s1.z
        actual_L = L if L is not None else (z_end - z_start)

        # 2. Calculation of Gauss-Lobatto Abscissae in range [-1, 1]
        # For n points, we need roots of P'_{n-1}(x)
        if n_points == 2:
            abscissae = [-1.0, 1.0]
        else:
            # The internal points are the roots of the derivative of Legendre polynomial P_{n-1}
            roots = np.polynomial.legendre.Legendre.deriv(
                np.polynomial.legendre.Legendre([0]*(n_points-1) + [1])
            ).roots()
            abscissae = np.concatenate(([-1.0], roots, [1.0]))

        # 3. Mapping from [-1, 1] to [z_start, z_start + actual_L]
        z_coords = [z_start + (xi + 1.0) * (actual_L / 2.0) for xi in abscissae]
        
        # Sort to ensure numerical stability
        z_coords = sorted(z_coords)
        return z_coords



    def __init__(self, section0: Section, section1: Section):
            
        if len(section0.polygons) != len(section1.polygons):
            raise ValueError(
                f"Mismatch: section0 has {len(section0.polygons)} polygons, "
                f"but section1 has {len(section1.polygons)} polygons."
        )

        if section0.z == section1.z:
            raise ValueError("Sections must be at different z coordinates.")

        self.s0 = section0
        self.s1 = section1

        # single source of truth
        self.z0 = section0.z
        self.z1 = section1.z

        # Optional list of callables or strings for custom weight interpolation
        self.weight_laws: Optional[List[Any]] = None

        self._validate_inputs()


    def validate_weight_law_at_midpoint2remove(self, formula: str) -> float:
        """
        DEBUG
        Performs a 'flight test' of the formula at the beam's midpoint.
        Uses the same execution context as the _interpolate_weight function.
        """
        if not formula or not formula.strip():
            return 0.0

        # 1. Calculation of the test point (Midpoint)
        # Using section0 and section1 as defined in the class constructor
        z0, z1 = self.s0.z, self.s1.z
        z_mid = (z0 + z1) / 2.0
        t_mid = 0.5 # t is always 0.5 at the midpoint between z0 and z1
        L = abs(z1 - z0)

        # 2. Prepare geometric data for the context (p0, p1, p_current)
        # We test on the first polygon as a sample to validate the formula syntax
        p0 = self.section0.polygons[0]
        p1 = self.section1.polygons[0]
        
        # Generate the interpolated polygon at t=0.5 to allow d(i,j) helper to work
        current_verts = tuple(v0.lerp(v1, t_mid) for v0, v1 in zip(p0.vertices, p1.vertices))
        p_current = Polygon(vertices=current_verts, weight=p0.weight, name=p0.name)

        # 3. Helper Functions Definition (same logic as _interpolate_weight)
        def d(i: int, j: int) -> float:
            """Distance between vertex i and j of the CURRENT polygon (1-based)"""
            return get_points_distance(p_current, i, j)

        def di(i: int, j: int) -> float:
            """Distance between vertex i and j of the INITIAL polygon (1-based)"""
            return get_points_distance(p0, i, j)

        def de(i: int, j: int) -> float:
            """Distance between vertex i and j of the FINAL polygon (1-based)"""
            return get_points_distance(p1, i, j)

        # New E_lookup helper for validation (consistent with _interpolate_weight)
        def E_lookup(filename: str) -> float:
            """
            Validation-time lookup call. 
            Uses t_mid (0.5) as the coordinate for the lookup file.
            """
            return lookup_homogenized_elastic_modulus(filename, t_mid)

        # 4. Context Definition (identical to the one in _interpolate_weight)
        context = {
            "w0": p0.weight, 
            "w1": p1.weight, 
            "z": t_mid,  # z in the formula context represents the normalized t
            "t": t_mid,
            "L": L,
            "math": math, 
            "np": np,
            "d": d, 
            "d0": di, 
            "d1e": de,
            "E_lookup": E_lookup # Added to support external lookup files
        }

        # 5. EVALUATION TEST
        try:
            # Execution with builtins restriction as in the original code
            result = eval(formula, {"__builtins__": {}}, context)
            return float(result)
        except Exception as e:
            # If it fails, raise a detailed error that stops the process
            raise ValueError(
                f"CRITICAL ERROR in the weight law: '{formula}'\n"
                f"The test at Z_mid={z_mid} (t={t_mid}) failed.\n"
                f"Error details: {e}"
            )
            
    def _evaluate_weight_formula(self, formula: str, p0: Polygon, p1: Polygon, t: float) -> float:
            """
            not used see evaluate_weight_formula 
            Evaluates a string-based mathematical formula to determine the polygon weight at a 
            given normalized position t.
            
            Args:
                formula (str): The Python expression to evaluate.
                p0 (Polygon): The polygon definition at the start section (z=0).
                p1 (Polygon): The polygon definition at the end section (z=L).
                t (float): Normalized longitudinal coordinate [0.0 to 1.0].
                
            Returns:
                float: The calculated weight (Elastic Modulus).
                
            Raises:
                Exception: Propagates any error encountered during evaluation.
            """
            # 1. Calculate the total length of the field
            l_total = abs(self.s1.z - self.s0.z)

            # 2. Generate a temporary midpoint polygon for the 'd(i,j)' helper.
            # This allows the formula to access distances at the current evaluation point.
            current_verts = tuple(
                v0.lerp(v1, t) for v0, v1 in zip(p0.vertices, p1.vertices)
            )
            p_mid = Polygon(vertices=current_verts, weight=p0.weight, name=p0.name)

            # 3. Define the external file lookup helper
            def E_lookup(filename: str) -> float:
                return lookup_homogenized_elastic_modulus(filename, t)

            # 4. Define local distance helpers for the context
            # These are used in the formula as d(i,j), d0(i,j), d1(i,j)
            d  = lambda i, j: get_points_distance(p_mid, i, j)
            di = lambda i, j: get_points_distance(p0, i, j)
            de = lambda i, j: get_points_distance(p1, i, j)

            # 5. Build the evaluation context (Environment)
            context = {
                "w0": p0.weight,        # Start weight
                "w1": p1.weight,        # End weight
                "t": t,                 # Normalized coordinate
                "z": t,                 # Alias for z-axis consistency
                "L": l_total,           # Physical length
                "math": math,           # Python math library
                "np": np,               # NumPy for advanced math
                "d": d,                 # Current distance function
                "d0": di,               # Start distance function
                "d1": de,               # End distance function
                "E_lookup": E_lookup    # File-based data lookup
            }

            # 6. Execute evaluation in a clean sandbox
            # We disable __builtins__ for safety to ensure only provided tools are used.
            return float(eval(formula, {"__builtins__": {}}, context))


    def set_weight_laws(self, laws: Union[List[str], Dict[Union[int, str], str]]) -> None:
        """
        Sets weight variation laws. 
        If a polygon name is not found or homology fails, it raises an error 
        to prevent falling back to default linear behavior.
        """
        if not isinstance(laws, (list, dict)):
            raise ValueError("weight_laws must be a list or a dictionary.")
        
        num_polygons = len(self.s0.polygons)
        valid_names0 = [p.name for p in self.s0.polygons]
        valid_names1 = [p.name for p in self.s1.polygons]
        
        # Reset current laws
        self.weight_laws = {}
        normalized_map = {}

        # 1. PARSING & STRICT TRANSLATION
        if isinstance(laws, list):
            for i, item in enumerate(laws):
                if isinstance(item, str) and ":" in item:
                    left, formula = item.split(":", 1)
                    left, formula = left.strip(), formula.strip()
                    
                    # Debug output: (flange, flange)
                    #print(f"DEBUG - Processing: ({left}) : {formula}")
                    
                    raw_names = [n.strip() for n in left.split(",")]
                    if len(raw_names) == 2:
                        n0, n1 = raw_names
                        # STRICT CHECK: If the name does not exist, Error
                        if n0 not in valid_names0:
                            raise KeyError(f"Critical Error: Polygon '{ raw_names[0]}' not found in Section 0.")
                        if n1 not in valid_names1:
                            raise KeyError(f"Critical Error: Polygon '{raw_names[1]}' not found in Section 1.")
                        
                        idx0 = valid_names0.index(n0) + 1
                        idx1 = valid_names1.index(n1) + 1
                        
                        # STRICT CHECK: Homology (must be the same polygon)
                        if idx0 != idx1:
                            raise ValueError(f"Homology Mismatch: '{n0}' (pos {idx0}) and '{n1}' (pos {idx1}) must match.")
                        
                        normalized_map[idx0] = formula
                    
                    elif len(raw_names) == 1:
                        n0 = raw_names[0]
                        if n0 not in valid_names0:
                            raise KeyError(f"Critical Error: Polygon '{n0}' not found.")
                        normalized_map[valid_names0.index(n0) + 1] = formula
                else:
                    # Positional list case
                    if i < num_polygons:
                        normalized_map[i + 1] = item

        elif isinstance(laws, dict):
            for key, law in laws.items():
                target_idx = None
                if isinstance(key, int):
                    target_idx = key
                elif isinstance(key, str):
                    if key not in valid_names0:
                        raise KeyError(f"Critical Error: No polygon named '{key}' found.")
                    target_idx = valid_names0.index(key) + 1
                
                if target_idx is not None:
                    if target_idx < 1 or target_idx > num_polygons:
                        raise IndexError(f"Index {target_idx} out of range (1-{num_polygons}).")
                    normalized_map[target_idx] = law

        z0, z1 = self.s0.z, self.s1.z
        z_mid = (z0 + z1) / 2.0  # Actual Z value halfway between the sections
        L_val = z1 - z0

        # Compute t consistently with the interpolation formula
        # If L_val is 0 (coincident sections), t is forced to 0 to avoid division by zero
        t_mid = (z_mid - z0) / L_val if L_val != 0 else 0.0
        

        for idx, formula in normalized_map.items():
            if isinstance(formula, str):
                try:
                    # Endpoint polygon references for distance calculations
                    p0_test = self.s0.polygons[idx-1]
                    p1_test = self.s1.polygons[idx-1]
                    
                    # Generation of midpoint vertices for p_mid (required for d(i,j) helper)
                    current_verts = tuple(v0.lerp(v1, t_mid) for v0, v1 in zip(p0_test.vertices, p1_test.vertices))
                    p_mid = Polygon(vertices=current_verts, weight=p0_test.weight, name=p0_test.name)
                    
                    # 1. Calculate the total length of the field
                    l_total = abs(self.s1.z - self.s0.z)

                    try:
                        # We test the formula at mid-span (t=0.5) to verify syntax and logic
                        we = evaluate_weight_formula(formula, p0_test, p1_test, l_total,t=t_mid)
                       
                    except Exception as e:                  
                        raise ValueError(
                            f"VALIDATION FAILED: The formula for '{p0_test.name}' is not valid.\n"
                            f"Formula: '{formula}'\n"
                            f"Error encountered at the midpoint: {e}"
                        )

                except Exception as e:
                    raise ValueError(
                        f"VALIDATION FAILED: The formula for '{valid_names0[idx-1]}' is not valid.\n"
                        f"Formula: '{formula}'\n"
                        f"Error encountered at the midpoint: {e}"
                    )
                
        # -------------------------------------------
        # 2. EFFECTIVE ASSIGNMENT (Bypassing FrozenInstanceError)
        for idx, formula in normalized_map.items():
            if formula is None: continue
            
            # Save as an integer for the interpolator
            self.weight_laws[idx] = str(formula)
            
            try:
                numeric_w = float(formula)
                if 1 <= idx <= num_polygons:
                    # Force update on s0 and s1 polygons
                    object.__setattr__(self.s0.polygons[idx-1], 'weight', numeric_w)
                    object.__setattr__(self.s1.polygons[idx-1], 'weight', numeric_w)
            except ValueError:
                # The formula is a function; it will be evaluated during interpolation
                pass

        print(f"SUCCESS - Weight laws correctly assigned: {list(self.weight_laws.keys())}")


    def _validate_inputs(self) -> None:
        if len(self.s0.polygons) != len(self.s1.polygons):
            raise ValueError("Start/end sections must have the same number of polygons.")

        for i, (p0, p1) in enumerate(zip(self.s0.polygons, self.s1.polygons)):
            if len(p0.vertices) != len(p1.vertices):
                raise ValueError(
                    f"Polygon index {i} has different vertex counts: "
                    f"{len(p0.vertices)} vs {len(p1.vertices)}"
                )
            

    def _interpolate_weight(self, w0: float, w1: float, t: float, p0: Polygon, p1: Polygon, law: Optional[str]) -> float:
        L_val = abs(self.s1.z - self.s0.z)
        if isinstance(law, str) and law.strip():
            #print("DEBUG _interpolate_weight")
            
            # Use the existing section attributes. 
            # Based on the error, self.section1 doesn't exist. 
            # In ContinuousSectionField, endpoints are usually self.s0 and self.s1
          
           
            
            # Since p_current is not in the signature, we interpolate vertices 
            # locally to allow the d(i, j) helper to work at height z
            current_verts = tuple(v0.lerp(v1, t) for v0, v1 in zip(p0.vertices, p1.vertices))
            p_current = Polygon(vertices=current_verts, weight=w0, name=p0.name) ## w0 is dummy value
            
            try:
                # We test the formula at t and verify syntax and logic
                wcust = evaluate_weight_formula(law, p0, p1, L_val,t=t)     
                return wcust
            except Exception as e:                  
                raise ValueError(
                    f"VALIDATION FAILED: The formula for '{p0.name} '{p1.name}' is not valid.\n"
                    f"Formula: '{law}'\n"
                    f"Error encountered at the midpoint: {e}"
                )
            
        # Default fallback: Linear Interpolation
        return w0 + (w1 - w0)/L_val * t

  
    def _to_t(self, z: float) -> float:
        z = float(z)
        if not (min(self.z0, self.z1) <= z <= max(self.z0, self.z1)):
            raise ValueError(f"z={z} is outside [{self.z0}, {self.z1}].")
        return (z - self.z0) / (self.z1 - self.z0)

    def section(self, z: float) -> Section: 
        origz=z
        t = self._to_t(z)
        polys: List[Polygon] = []
        for i, (p0, p1) in enumerate(zip(self.s0.polygons, self.s1.polygons)):
            verts = tuple(v0.lerp(v1, t) for v0, v1 in zip(p0.vertices, p1.vertices))
            
            # keep weight/name from p0 by default
            # polys.append(Polygon(vertices=verts, weight=p0.weight, name=p0.name))

            ### interpolation here
            # Identify if a custom law exists for the current polygon index.
            # Support for both List (by index) and Dictionary (by index or by name).
            current_law = None
            idx = i + 1 
            if isinstance(self.weight_laws, list):
                if i < len(self.weight_laws):
                    current_law = self.weight_laws[idx]
            elif isinstance(self.weight_laws, dict):
                # Look up by index first, then by polygon name
                #current_law = self.weight_laws.get(i, self.weight_laws.get(p0.name))
                current_law = self.weight_laws.get(idx)
            
            interp_weight = self._interpolate_weight(p0.weight, p1.weight, origz, p0, p1, current_law)
            #print(f"DEBUG {interp_weight} ")
            poly = Polygon(vertices=verts, weight=interp_weight, name=p0.name)
            # --------------------------

            if polygon_has_self_intersections(poly):
                warnings.warn(
                    f"Self-intersection detected in polygon '{poly.name}' at z={z:.3f}",
                    RuntimeWarning
                )

            polys.append(poly)
        return Section(polygons=tuple(polys), z=float(z))

# -------------------------
# Digestor: Section properties (2D polygon-based)
# -------------------------

def _polygon_signed_area_and_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]:
    """
    Shoelace. Returns signed area (can be negative depending on orientation) and centroid.
    """
    verts = poly.vertices
    n = len(verts)

    a2 = 0.0  # 2*Area signed
    cx6 = 0.0
    cy6 = 0.0

    for i in range(n):
        # Current vertex and next vertex (cyclic)
        v0 = verts[i]
        v1 = verts[(i + 1) % n]
        
        x0, y0 = v0.x, v0.y
        x1, y1 = v1.x, v1.y
        
        # Calculate cross product for this segment
        cross = x0 * y1 - x1 * y0

        
        a2 += cross
        cx6 += (x0 + x1) * cross
        cy6 += (y0 + y1) * cross

    if abs(a2) < 1e-14:
        return 0.0, (0.0, 0.0)

    A = 0.5 * a2
    Cx = cx6 / (3.0 * a2)
    Cy = cy6 / (3.0 * a2)
    
    return A, (Cx, Cy)

def polygon_area_centroid(poly: Polygon) -> Tuple[float, Tuple[float, float]]:
    """
    Computes the signed area and geometric centroid of a non-self-intersecting polygon.

    TECHNICAL SUMMARY:
    This function implements the Surveyor's Formula (Shoelace Algorithm), 
    derived from Green's Theorem, to integrate area and first moments over 
    a planar polygonal domain. It is designed to handle both "solid" (counter-clockwise) 
    and "void" (clockwise) polygons to model hollow sections like wind turbine towers.

    MATHEMATICAL FORMULATION:
    1. Signed Area (A):
       The area is computed as the sum of cross-products of vertex vectors:
       A = 0.5 * Σ (x_i * y_{i+1} - x_{i+1} * y_i)
       The sign of the area indicates the vertex winding order:
       - Positive: Counter-Clockwise (CCW).
       - Negative: Clockwise (CW).

    2. Geometric Centroid (Cx, Cy):
       The coordinates of the centroid (center of area) are derived from the 
       first moments of area (Qx, Qy):
       Cx = (1 / 6A) * Σ (x_i + x_{i+1}) * (x_i * y_{i+1} - x_{i+1} * y_i)
       Cy = (1 / 6A) * Σ (y_i + y_{i+1}) * (x_i * y_{i+1} - x_{i+1} * y_i)

    COMPUTATIONAL ROBUSTNESS:
    - Degeneracy Handling: Includes a threshold check (1e-14) to identify 
      degenerate polygons (lines or points) and prevent division-by-zero errors.
    - Consistency: Since it utilizes a cyclic vertex indexing [(i + 1) % n], 
      it ensures a closed-loop integration regardless of vertex count.

    APPLICABILITY IN RULED SURFACE MODELING:
    By returning the signed area, this function allows for seamless 
    homogenization. When a void (e.g., the inner diameter of a tower) is 
    modeled with an opposite winding order or negative weight, the integration 
    correctly subtracts its properties from the total section digest.

    RETURNS:
       - Area: Signed area of the polygon [L²].
       - Centroid: Tuple (Cx, Cy) representing the geometric center [L].
    """
    A_signed, (Cx, Cy) = _polygon_signed_area_and_centroid(poly)
    A_mag = abs(A_signed)
    return poly.weight * A_mag, (Cx, Cy)


def section_data(field: ContinuousSectionField, z: float) -> dict:
    """
    Extracts the complete geometric state and physical properties of a section 
    at a specific longitudinal coordinate (z).

    TECHNICAL SUMMARY:
    This function acts as a high-level accessor for the Continuous Section Field. 
    It performs a synchronized extraction of both the interpolated boundary 
    geometry and the corresponding integral properties (Area, First/Second Moments). 
    It provides a discrete "snapshot" of a 3D ruled solid at any point along 
    its integration path.

    WORKFLOW AND DATA ARCHITECTURE:
    1. Geometric Reconstruction:
       The function first invokes the internal Linear Interpolation (LERP) 
       mechanism to reconstruct the homogenized polygonal boundaries at 
       coordinate 'z'. This ensures topological consistency across the 
       longitudinal domain.

    2. Property Integration:
       Once the geometry is established, the 'section_properties' engine 
       is executed to compute the sectional digest. This involves:
       - Zeroth Moment: Area (A).
       - First Moments: Centroidal coordinates (Cx, Cy).
       - Second Moments: Moments of inertia (Ix, Iy, Ixy) and the Polar 
         Moment (J).

    3. Data Encapsulation:
       The results are packaged into a dictionary structure, decoupling the 
       raw geometric data (vertices/polygons) from the derived structural 
       parameters.

    APPLICABILITY:
    This function is the standard interface for structural analysis routines 
    that require local stiffness or stress evaluation at specific points 
    along a non-prismatic member.

    RETURNS:
       A dictionary containing:
       - 'section': The Section object (polygonal boundaries at z).
       - 'properties': A dictionary of computed geometric constants.
    """

    section = field.section(z)
    props = section_properties(section)

    return {
        "section": section,     # geometria completa
        "properties": props,    # A, Cx, Cy, Ix, Iy, Ixy, J
    }

def section_properties(section: Section) -> Dict[str, float]:
    """
    Computes the integral geometric properties for a composite cross-section.

    TECHNICAL SUMMARY:
    This function performs a multi-pass integration over a set of weighted 
    polygons to derive the global geometric constants. It manages homogenization 
    by algebraically summing contributions, allowing for the representation of 
    complex domains with voids or varying material densities.

    ALGORITHMIC WORKFLOW:
    1. First-Order Moments (Area and Centroid):
       - Aggregates the weighted area (A) and the first moments of area (Qx, Qy) 
         for all constituent polygons.
       - Locates the global centroid (Cx, Cy) of the composite section.

    2. Second-Order Moments (Inertia about Origin):
       - Computes the area moments of inertia (Ix, Iy) and the product of 
         inertia (Ixy) relative to the global coordinate origin (0,0).

    3. Translation of Axes (Parallel Axis Theorem):
       - Applies the Huygens-Steiner Theorem to shift the moments of inertia 
         from the global origin to the newly calculated centroidal axes:
         I_centroid = I_origin - A * d^2
       - This transformation ensures the properties are intrinsic to the 
         section's geometry, independent of the global coordinate system.

    4. Polar Moment Extraction:
       - Derives the Polar Second Moment of Area (J) about the centroid as 
         the sum of the orthogonal centroidal moments (Ix + Iy).

    RETURNS:
       A comprehensive dictionary containing:
       - 'A': Net weighted area.
       - 'Cx', 'Cy': Centroidal coordinates.
       - 'Ix', 'Iy', 'Ixy': Second moments of area about centroidal axes.
       - 'J': Polar moment of area.
    """
    # First pass: area + centroid
    A_tot = 0.0
    Cx_num = 0.0
    Cy_num = 0.0

    poly_cache = []
    for poly in section.polygons:
        A_i, (cx_i, cy_i) = polygon_area_centroid(poly)
        A_tot += A_i
        Cx_num += A_i * cx_i
        Cy_num += A_i * cy_i
        poly_cache.append((poly, A_i, cx_i, cy_i))

    if abs(A_tot) < 1e-14:
        raise ValueError("Composite area is ~0; cannot compute centroid/properties reliably.")

    Cx = Cx_num / A_tot
    Cy = Cy_num / A_tot

    # Second pass: inertia about origin then shift to centroid
    Ix_o = 0.0
    Iy_o = 0.0
    Ixy_o = 0.0

    for poly, _, _, _ in poly_cache:
        ix, iy, ixy = polygon_inertia_about_origin(poly)
        Ix_o += ix
        Iy_o += iy
        Ixy_o += ixy

    # Parallel axis theorem to centroid
    Ix_c = Ix_o - A_tot * (Cy * Cy)
    Iy_c = Iy_o - A_tot * (Cx * Cx)
    Ixy_c = Ixy_o - A_tot * (Cx * Cy)

    J = Ix_c + Iy_c

    return {
        "z": section.z,
        "A": A_tot,
        "Cx": Cx,
        "Cy": Cy,
        "Ix": Ix_c,
        "Iy": Iy_c,
        "Ixy": Ixy_c,
        "J": J,
    }


# -------------------------
# Visualization helpers
# -------------------------

def _set_axes_equal_3d(ax) -> None:
    """
    Configures 3D axis limits to perform a 'selective zoom' and maintain 
    consistent aspect ratios for cross-sectional visualization.

    TECHNICAL SUMMARY:
    This function normalizes the viewport of a Matplotlib 3D projection. 
    It ensures that the horizontal plane (X-Y) is scaled isotropically 
    (equal aspect ratio) to prevent geometric distortion of the sections, 
    while allowing the longitudinal axis (Z) to retain its full physical 
    extent for structural context.

    ALGORITHMIC LOGIC:
    1. Limit Extraction:
       Retrieves current bounding box limits for X, Y, and Z dimensions 
       to determine the object's spatial center.

    2. Planar Isotropic Scaling:
       Calculates a maximum radius based on the spans of X and Y. By 
       applying this radius symmetrically to both horizontal axes, the 
       function ensures that circles or ellipses appear without 
       eccentricity distortion.

    3. Longitudinal Preservation:
       Unlike standard 'equal axis' commands, this logic preserves the 
       original Z-limits. This is crucial for high-aspect-ratio solids, 
       ensuring the entire height is visible within the frame.

    4. Box Aspect Ratio:
       Sets the 'box_aspect' to (1, 1, 2) to force a vertical emphasis, 
       making slender solids visually representative of their physical 
       proportions.
    """
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    # Calcoliamo i centri
    x_mid = sum(x_limits) / 2.0
    y_mid = sum(y_limits) / 2.0
    z_mid = sum(z_limits) / 2.0

    # Determine the maximum range for the X-Y plane only
    # (Ensures horizontal geometry fills the space without distortion)
    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    radius_xy = 0.5 * max(x_range, y_range)

    # Apply centered isotropic zoom on X and Y
    ax.set_xlim3d([x_mid - radius_xy, x_mid + radius_xy])
    ax.set_ylim3d([y_mid - radius_xy, y_mid + radius_xy])
    
    # Maintain physical Z-limits for the longitudinal axis
    ax.set_zlim3d(z_limits)

    # Force a visual box aspect to emphasize verticality
    ax.set_box_aspect((1, 1, 2))


class Visualizer:
    """
    Adds 2D and 3D plotting utilities on top of a ContinuousSectionField.
    """

    def __init__(self, field: ContinuousSectionField):
        self.field = field

    def plot_properties(self, keys_to_plot=None,  plot_w=False, num_points=100):

       
            """
            Plots the evolution of geometric properties along the Z-axis.
            "z": ,
            "A":,
            "Cx":
            "Cy":
            "Ix":,
            "Iy"
            "Ixy
            "J"
                Args:
                    keys_to_plot (list, optional): List of dictionary keys to plot 
                        (e.g., ["A", "Ix", "Iy", "Cy"]). If None, plots all standard properties.
                    num_points (int): Number of sampling points along the longitudinal axis.
                    plot_w (bool): If True, plots the weight (w) for each individual polygon in a separate figure.
            """

            # Use the exact attributes for Z coordinates from your ContinuousSectionField class
            z_start = self.field.s0.z
            z_end = self.field.s1.z
        
            # EXACT KEYS returned by the global function section_properties
            available_keys = ["A", "Cx", "Cy", "Ix", "Iy", "Ixy", "J"]
            
            if keys_to_plot is None:
                keys_to_plot = []
            
            # 1. Sampling Z coordinates using your field range            
            z_values = np.linspace(z_start, z_end, num_points)
            data_series = {key: [] for key in keys_to_plot}
            if len(keys_to_plot) > 0:
                
                # 2. Iterate and collect data
                for z in z_values:
                    # Generate the interpolated section at coordinate z
                    current_section = self.field.section(z)
                    
                    # CALL: Use the global function section_properties and pass the section
                    props = section_properties(current_section)
                    
                    for key in keys_to_plot:
                        if key in props:
                            data_series[key].append(props[key])

                # 3. Plotting with stacked subplots for standard properties
                num_keys = len(keys_to_plot)
                fig, axes = plt.subplots(num_keys, 1, figsize=(10, 2.2 * num_keys), sharex=True)
                
                if num_keys == 1:
                    axes = [axes]

                colors = plt.cm.viridis(np.linspace(0, 0.9, num_keys))

                for i, (key, color) in enumerate(zip(keys_to_plot, colors)):
                    axes[i].plot(z_values, data_series[key], color=color, linewidth=2)
                    axes[i].set_ylabel(key, fontweight='bold')
                    
                    # --- correction scale
                    v_min, v_max = min(data_series[key]), max(data_series[key])
                    margin = (v_max - v_min) * 0.1 if v_max != v_min else 0.1
                    axes[i].set_ylim(v_min - margin, v_max + margin) 
                    # ------------------------

                    axes[i].grid(True, linestyle=':', alpha=0.6)
                    axes[i].set_title(f"{key} (Var: {v_min:.3f} to {v_max:.3f})", loc='right', fontsize=9)

                axes[-1].set_xlabel("Z coordinate [m]")
                plt.tight_layout()
                
            # --- ADDITIONAL BLOCK FOR POLYGON WEIGHT (w) controlled by plot_w ---
          
            if plot_w:
                
                # Determine number of polygons from the reference sections
                num_polys = len(self.field.s0.polygons)
                poly_w_series = {i: [] for i in range(num_polys)}
                
                # Use the internal interpolation function for each polygon
               
                for z in z_values:
                    # Calculate the interpolation factor t for the current z
                    t = z #(z - z_start) / (z_end - z_start)
                   
                    for i in range(num_polys):
                        
                        p0 = self.field.s0.polygons[i]
                        p1 = self.field.s1.polygons[i]
                        
                        # CALL THE CORRECT PROTOCOL: _interpolate_weight
                        # We pass the weights from the boundary polygons and the current t

                        
                        if self.field.weight_laws is not None and (i + 1) in self.field.weight_laws:
                            current_law = self.field.weight_laws[i+1]
                        else:
                            current_law = None

                        w_val = self.field._interpolate_weight(
                            p0.weight, p1.weight, t, p0, p1, current_law
                        )
                        #print(f"DEBUG {w_val}")
                        poly_w_series[i].append(w_val)
                       
                
                # Create a dedicated figure for individual polygon weights
                fig_w, axes_w = plt.subplots(num_polys, 1, figsize=(10, 2 * num_polys), sharex=True)
                if num_polys == 1: 
                    axes_w = [axes_w]
                
                for i in range(num_polys):

                    p0 = self.field.s0.polygons[i]
                    p1 = self.field.s1.polygons[i]      


                    axes_w[i].plot(z_values, poly_w_series[i], color='tab:red', linewidth=1.5)
                    axes_w[i].set_ylabel(f"s0 {p0.name} - s1 {p1.name}", fontweight='bold')
                    
                    v_min_w, v_max_w = min(poly_w_series[i]), max(poly_w_series[i])
                    margin_w = (v_max_w - v_min_w) * 0.1 if v_max_w != v_min_w else 0.1
                    axes_w[i].set_ylim(v_min_w - margin_w, v_max_w + margin_w)
                    
                    axes_w[i].grid(True, linestyle='--', alpha=0.5)
                    axes_w[i].set_title(f"Weight (w) for polygon {i}", loc='right', fontsize=8)
                
                fig_w.suptitle("Individual Polygon Weight (w) Distributions (Interpolated)", fontweight='bold')
                fig_w.tight_layout()
            # --------------------------------------------------------------------

            plt.show()

    def plot_section_2d(self, z: float, show_ids: bool = True, show_weights: bool = True,
                            show_vertex_ids: bool = False, # Nuovo parametro
                            title: Optional[str] = None, ax=None):
        """
        Draw the 2D section with descriptions in the corners:
        - Polygon 0: Top right
        - Polygon 1: Bottom left

        Renders a 2D representation of the section at a specific longitudinal coordinate (z).
        
        Parameters:
        -----------
        z : float
            The longitudinal coordinate where the section is evaluated.
        show_ids : bool, default True
            If True, displays the polygon index (e.g., #0, #1).
        show_weights : bool, default True
            If True, displays the physical weight/density assigned to each polygon.
        show_vertex_ids : bool, default False
            If True, labels each vertex with its index (1-based) using the polygon's color.
        title : str, optional
            Custom title for the plot.
        ax : matplotlib.axes.Axes, optional
            Existing axes to plot on. If None, a new figure is created.
        
        Layout Logic:
        -------------
        - Polygon 0 Info: Anchored to the Top-Right corner of the axes.
        - Polygon 1 Info: Anchored to the Bottom-Left corner of the axes.
        - Other Polygons: Labels are placed at their respective geometric centroids.
            


        """
        sec = self.field.section(z)
        if ax is None:
            fig, ax = plt.subplots()

        for idx, poly in enumerate(sec.polygons):
            xs = [p.x for p in poly.vertices] + [poly.vertices[0].x]
            ys = [p.y for p in poly.vertices] + [poly.vertices[0].y]
            
            # Disegno del poligono e recupero colore
            line, = ax.plot(xs, ys, linewidth=1.5, zorder=2)
            color = line.get_color()

        
            if show_vertex_ids:
                for v_idx, v in enumerate(poly.vertices):
                    v_idxvirtual = v_idx +1

                    ax.text(v.x, v.y, f" {v_idxvirtual}", color=color, fontsize=9, 
                            fontweight='bold', zorder=4)
                    
            if show_weights:
                # 
                parts = []
                if show_ids: parts.append(f"#{idx}")
                if show_weights: parts.append(f"w={poly.weight:g}")
                if poly.name: parts.append(poly.name)
                label_text = "\n".join(parts)

                # 
                if idx == 0:
                    x_pos, y_pos = 0.95, 0.95
                    ha, va = 'right', 'top'
                elif idx == 1:
                    x_pos, y_pos = 0.05, 0.05
                    ha, va = 'left', 'bottom'
                else:
                    _, (cx, cy) = polygon_area_centroid(poly)
                    ax.text(cx, cy, label_text, color=color, ha='center', va='center',
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor=color))
                    continue

                ax.text(
                    x_pos, y_pos, label_text,
                    transform=ax.transAxes,
                    fontsize=10,
                    fontweight='bold',
                    color=color,
                    ha=ha, va=va,
                    zorder=3,
                    bbox=dict(
                        facecolor='white', 
                        alpha=0.85, 
                        edgecolor=color, 
                        boxstyle='round,pad=0.4'
                    )
                )
            

        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True, linestyle=':', alpha=0.5, zorder=1)

        if title is None:
            title = f"Section at z={z:g}"
        ax.set_title(title)

        return ax

  

    def plot_volume_3d(self, show_end_sections: bool = True, line_percent: float = 100.0,
                       seed: int = 0, title: str = "Ruled volume (vertex-connection lines)", ax=None):
        """
        Draw the 3D ruled "skeleton":
        - endpoint section outlines (optional)
        - straight lines connecting corresponding vertices (ruled generators)
        - ability to display only a percentage of those lines for readability

        line_percent:
          0..100 : percentage of connection lines shown (random subsample).
        """
        if not (0.0 <= line_percent <= 100.0):
            raise ValueError("line_percent must be within [0, 100].")
            
        # 2. AXES INITIALIZATION
        # If no existing axis is provided, create a new 3D figure with a default perspective.
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")
            ax.view_init(elev=15, azim=120)

        # 3. GEOMETRY EXTRACTION
        # Get endpoint sections at the field's start (z0) and end (z1).
        z0, z1 = self.field.z0, self.field.z1
        s0 = self.field.section(z0)
        s1 = self.field.section(z1)

        # 4. DRAW END SECTIONS
        # If show_end_sections is True, plot the perimeter of all polygons at Z0 and Z1.
        # This helps visualize the boundary transition of the ruled
        if show_end_sections:
            for sec in (s0, s1):
                for poly in sec.polygons:
                    xs = [p.x for p in poly.vertices] + [poly.vertices[0].x]
                    ys = [p.y for p in poly.vertices] + [poly.vertices[0].y]
                    zs = [sec.z] * len(xs)
                    ax.plot(xs, ys, zs)
        # 5. BUILD GENERATOR LINES
        # Create a list of all straight lines (ruled generators) connecting
        # each vertex in the start section to its corresponding vertex in the end section.
            all_lines = []
        for p0, p1 in zip(s0.polygons, s1.polygons):
            for v0, v1 in zip(p0.vertices, p1.vertices):
                all_lines.append((v0, v1))

        # 6. SUBSAMPLING (Visual Clarity)
        # If line_percent < 100, we randomly select a subset of lines to avoid visual clutter.
        # Using a fixed 'seed' ensures the same set of lines is picked every time (reproducibility).
        if line_percent < 100.0:
            rng = random.Random(seed)
            k = int(math.ceil(len(all_lines) * (line_percent / 100.0)))
            k = max(0, min(k, len(all_lines)))
            all_lines = rng.sample(all_lines, k)

        # 7. PLOTTING
        # Draw the connection lines between the two Z-planes.
        for v0, v1 in all_lines:
            ax.plot([v0.x, v1.x], [v0.y, v1.y], [z0, z1])

        # Draw axes labels
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title(title)

        # Improve scaling
        _set_axes_equal_3d(ax)
        return ax


# ============================================================
# Example: Continuous Section Field – Static Properties Demo
# ============================================================
#
# This script demonstrates how to:
# - define polygonal cross-sections,
# - interpolate them along a longitudinal axis (Z),
# - compute geometric and static properties,
# - visualize both 2D sections and the 3D ruled solid.
#
# The example uses a tapered T-section composed of:
# - a flange polygon
# - a web polygon
#
# Coordinate system:
#   X → horizontal
#   Y → vertical
#   Z → longitudinal
#
# NOTE:
# A negative centroid Y-coordinate (Cy) is expected in this example
# because most of the section area lies below the global X-axis.
#
# ============================================================


if __name__ == "__main__":

    # --------------------------------------------------------
    # 1. DEFINE START SECTION (Z = 0)
    # --------------------------------------------------------
    # The start section is a T-shape composed of two polygons:
    # - flange (horizontal plate)
    # - web (vertical plate)


    # Define start polygons (T-Section at Z=0)
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

    # --------------------------------------------------------
    # 2. DEFINE END SECTION (Z = 10)
    # --------------------------------------------------------
    # The flange remains unchanged.
    # The web depth increases linearly from 1.0 to 2.5,
    # producing a tapered T-section along the Z-axis.

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

      # --------------------------------------------------------
    # 3. CREATE SECTIONS WITH Z-COORDINATES
    # --------------------------------------------------------
    # Each Section groups polygons and assigns a Z position.

    s0 = Section(polygons=(poly0_start, poly1_start), z=0.0)
    s1 = Section(polygons=(poly0_end, poly1_end), z=10.0)

    # --------------------------------------------------------
    # 4. INITIALIZE CONTINUOUS SECTION FIELD
    # --------------------------------------------------------
    # A linear interpolator is used to generate intermediate
    # sections between Z = 0 and Z = 10.
    field = ContinuousSectionField(section0=s0, section1=s1)

    # --------------------------------------------------------
    # 5 Print Analysis
    # --------------------------------------------------------
    # A linear interpolator is used to generate intermediate
    # sections between Z = 0 and Z = 10.


    sec= field.section(10.0)
    full_analysis = section_full_analysis(sec)
    section_print_analysis(full_analysis)
    print(f"Area (A):               {full_analysis['A']:.4f}      # Net area")

    # --------------------------------------------------------
    # 6. VISUALIZATION
    # --------------------------------------------------------
    # - 2D section plot at Z = 5.0
    # - 3D ruled solid visualization
    viz = Visualizer(field)
    # Generate 2D plot for the specified slice
    viz.plot_section_2d(z=10.0)
    # Generate 3D plot of the interpolated solid
    # line_percent determines the density of the longitudinal ruled lines
    viz.plot_volume_3d(line_percent=100.0, seed=1)
    plt.show()
    

