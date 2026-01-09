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
    section_print_analysis
)



if __name__ == "__main__":
    # this is the file name
    geometryfile="geometry.tcl"
    
    h = 0.40  # cm
    b = 0.30  # cm
    #hf = 0.400


    poly_bottom_start = Polygon(
        vertices=(
            Pt(-b/2, -h/2), 
            Pt( b/2, -h/2),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1.0,
        name="lowerpart",
    )

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
            Pt(-b/2, -h/2), 
            Pt( b/2, -h/2),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1,
        name="lowerpart",
    )

    # --- SECTION AND FIELD DEFINITION ---
    L = 10.0
    s0 = Section(polygons=(poly_bottom_start,poly_top_start),z=0.0)
    s1 = Section(polygons=(poly_bottom_end, poly_top_end),z=L)

    section_field = ContinuousSectionField(section0=s0, section1=s1)

    zsec_val = 0.0
    sec_mid = section_field.section(zsec_val)

    full_analysis = section_full_analysis(sec_mid)
    section_print_analysis(full_analysis)

    
    viz = Visualizer(section_field)
    viz.plot_section_2d(z=0,show_vertex_ids=True,show_weights=False)    
    viz.plot_volume_3d(line_percent=100.0, seed=1)

    vizprop = Visualizer(section_field)
    vizprop.plot_properties(['Cy','Ix','Iy','J'])
    write_opensees_geometry(section_field, n_points=10, filename=geometryfile)
    plt.show()
  
    
