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
    section_print_analysis,
    write_opensees_geometry
)



if __name__ == "__main__":
    # ----------------------------------------------------------------------------------
    # 1. DEFINE START SECTION (Z = 0)
    # ----------------------------------------------------------------------------------
    # POLYGON CONSTRUCTION GUIDELINES:
    # - Vertices MUST be defined in COUNTER-CLOCKWISE (CCW) order.
    # - This ensures positive Area and correct Moments of Inertia via Green's Theorem.
    # - Weight: 1.0 for solid material, -1.0 for voids/holes.
    # ----------------------------------------------------------------------------------

    # Flange Definition: Horizontal rectangle
    poly0_start = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    # Web Definition: Vertical stem
    poly1_start = Polygon(
        vertices=(Pt(-0.2, -1.0), Pt(0.2, -1.0),  Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )

    # ----------------------------------------------------------------------------------
    # 2. DEFINE END SECTION (Z = 10)
    # ----------------------------------------------------------------------------------
    # CONSISTENCY RULES:
    # - Same number of polygons and same names as the start section for interpolation.
    # - Here, the web depth increases from 1.0 to 2.5 (Tapered section).
    # ----------------------------------------------------------------------------------

    poly0_end = Polygon(
        vertices=(Pt(-1, -0.2), Pt(1, -0.2), Pt(1, 0.2), Pt(-1, 0.2)),
        weight=1.0,
        name="flange",
    )
    
    poly1_end = Polygon(
        vertices=(Pt(-0.2, -2.5), Pt(0.2, -2.5), Pt(0.2, -0.2), Pt(-0.2, -0.2)),
        weight=1.0,
        name="web",
    )
    # ----------------------------------------------------------------------------------
    # 3. CREATE SECTIONS WITH Z-COORDINATES
    # ----------------------------------------------------------------------------------
    s0 = Section(polygons=(poly0_start, poly1_start), z=10.0)
    s1 = Section(polygons=(poly0_end, poly1_end), z=20.0)

    # ----------------------------------------------------------------------------------
    # 4. INITIALIZE CONTINUOUS SECTION FIELD (CSF)
    # ----------------------------------------------------------------------------------
    # Manages vertex interpolation between s0 and s1 along the Z-axis.
    field = ContinuousSectionField(section0=s0, section1=s1)

    # ----------------------------------------------------------------------------------
    # 5. PRIMARY SECTION PROPERTIES (EVALUATED AT Z = 0.0)
    # ----------------------------------------------------------------------------------
    zsec_val = 10.0
    sec_mid = field.section(zsec_val)
 
    full_analysis = section_full_analysis(sec_mid)
    section_print_analysis(full_analysis)
    # ----------------------------------------------------------------------------------
    # 6. VISUALIZATION
    # ----------------------------------------------------------------------------------
    viz = Visualizer(field)
    viz.plot_section_2d(z=zsec_val, show_vertex_ids=True,show_weights=True)    
    viz.plot_volume_3d(line_percent=100.0, seed=1)
    viz.plot_properties(plot_w=True)
    
    plt.show()

