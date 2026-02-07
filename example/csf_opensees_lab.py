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
    Visualizer,
    section_statical_moment_partial, section_stiffness_matrix,
    polygon_inertia_about_origin,
    polygon_statical_moment,
    compute_saint_venant_J,
    compute_saint_venant_Jv2,
    write_opensees_geometry,
    section_full_analysis_keys,
    section_print_analysis
)



if __name__ == "__main__":
    # this is the file name
    geometryfile="geometry.tcl"
    
    h = 1.20  # cm
    hb= 0.40
    b = 0.30  # cm
    #hf = 0.400

    poly_top_start = Polygon(
        vertices=(
            Pt(-b/2,  0.0), 
            Pt( b/2,  0.0),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1, # 
        name="upperpart",
    )

    
    poly_bottom_start = Polygon(
        vertices=(
            Pt(-b/2, -h/2), 
            Pt( b/2, -h/2),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1,
        name="lowerpart",
    )
    

    poly_top_end = Polygon(
        vertices=(
            Pt(-b/2,  0.0), 
            Pt( b/2,  0.0),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1, # 
        name="upperpart",
    )

    poly_bottom_end = Polygon(
        vertices=(
            Pt(-b/2, -hb/4), 
            Pt( b/2, -hb/4),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1,
        name="lowerpart",
    )

    # --- SECTION AND FIELD DEFINITION ---
    L = 10.0

    #s0 = Section(polygons=(poly_top_start,),z=0.0)
    #s1 = Section(polygons=(poly_top_end,),z=L)


    s0 = Section(polygons=(poly_bottom_start,poly_top_start),z=0.0)
    s1 = Section(polygons=(poly_bottom_end, poly_top_end),z=L)

    section_field = ContinuousSectionField(section0=s0, section1=s1)

    zsec_val = 10.0
    sec_mid = section_field.section(zsec_val)

    full_analysis = section_full_analysis(sec_mid)
    section_print_analysis(full_analysis,fmt=".2f")
   
    
    viz = Visualizer(section_field)
    viz.plot_section_2d(z=00,show_vertex_ids=True,show_weights=False)  
    viz.plot_section_2d(z=10,show_vertex_ids=True,show_weights=False)     
    viz.plot_volume_3d(line_percent=100.0, seed=1)

    vizprop = Visualizer(section_field)
    vizprop.plot_properties(['Cy','Ix','Iy','J'])
    write_opensees_geometry(section_field,E_ref=1, nu=0, n_points=10, filename=geometryfile)
    plt.show()
  
    section_field.set_weight_laws([
        f"upperpart,upperpart : 7.85", 
        f"lowerpart,lowerpart: 2.5"
    ])


    section_field.to_yaml("csf_opensees_lab.yaml")
