"""
run_pier50.py
=============
Project Pier50 — Urban viaduct, seismic zone 2 (NTC2018 / EC8-2).

Stack the three YAML geometry files and render the full 3D pier.

Workflow
--------
1. Generate the three geometry YAML files:
       .\\geometry_pier_seg1.ps1   (Windows)
       .\\geometry_pier_seg2.ps1
       .\\geometry_pier_seg3.ps1
   or on Linux:
       ./geometry_pier_seg1.sh
       ./geometry_pier_seg2.sh
       ./geometry_pier_seg3.sh

2. Run this script:
       python run_pier50.py

Pier geometry summary
---------------------
  Seg 1 — Base zone      z =  0 →  8 m   6.40×3.60 → 5.20×3.20 m   tg 0.70→0.60 m
  Seg 2 — Main shaft     z =  8 → 38 m   5.20×3.20 → 4.00×2.60 m   tg 0.60→0.45 m
  Seg 3 — Pier head      z = 38 → 50 m   4.00×2.60 → 5.60×3.00 m   tg 0.45→0.55 m

Junction connectivity
---------------------
  z =  8 m :  dx=5.20  dy=3.20  R=0.30  tg=0.60  (S1-seg1 == S0-seg2)
  z = 38 m :  dx=4.00  dy=2.60  R=0.30  tg=0.45  (S1-seg2 == S0-seg3)
"""

import matplotlib.pyplot as plt
from csf.CSFStacked import CSFStacked
from csf.io.csf_reader import CSFReader
from csf.section_field import export_polygon_vertices_csv
import os
# =============================================================================
# Load geometry files
# =============================================================================

report_dir  = "../result"
report_path = os.path.join(report_dir, "UrbanViaduc_report.txt")
os.makedirs(report_dir, exist_ok=True)
_report_file = open(report_path, "w", encoding="utf-8")

def put(line: str = "") -> None:
    _report_file.write(line + "\n")

f1 = CSFReader().read_file("../yaml/pier_seg1.yaml").field   # base zone
f2 = CSFReader().read_file("../yaml/pier_seg2.yaml").field   # main shaft
f3 = CSFReader().read_file("../yaml/pier_seg3.yaml").field   # pier head

# =============================================================================
# Stack
# =============================================================================

stack = CSFStacked(eps_z=1e-10)
stack.append(f1)
stack.append(f2)
stack.append(f3)

z_min, z_max = stack.global_bounds()
put(f"Pier50  z: {z_min:.1f} m → {z_max:.1f} m")

# =============================================================================
# Section property scan
# =============================================================================
# n_sez : number of equally spaced stations from z_min to z_max.
# All available section properties are printed for each station.
# =============================================================================

n_sez = 20

put(f"\nSection property scan - {n_sez} stations  (z: {z_min:.1f} → {z_max:.1f} m)")
put(
    f"  {'z [m]':>7} "
    f"{'A [m²]':>10} "
    f"{'Cx [m]':>8} "
    f"{'Cy [m]':>8} "
    f"{'Ix [m⁴]':>12} "
    f"{'Iy [m⁴]':>12} "
    f"{'Ixy [m⁴]':>12} "
    f"{'Ip [m⁴]':>12} "
    f"{'I1 [m⁴]':>12} "
    f"{'I2 [m⁴]':>12} "
    f"{'rx [m]':>8} "
    f"{'ry [m]':>8} "
    f"{'Wx [m³]':>10} "
    f"{'Wy [m³]':>10} "
    f"{'J_sv_cell [m⁴]':>16} "
    f"{'t_bredt [m]':>12}"
)
put("  " + "-" * 182)

for i in range(n_sez):
    # Linearly spaced stations; clamp the last point to z_max to avoid
    # floating-point overshoot outside the stack domain.
    z = z_min + i * (z_max - z_min) / (n_sez - 1) if n_sez > 1 else z_min
    z = min(z, z_max)

    sa = stack.section_full_analysis(z)

    put(
        f"  {z:>7.3f} "
        f"{sa['A']:>10.5f} "
        f"{sa['Cx']:>8.5f} "
        f"{sa['Cy']:>8.5f} "
        f"{sa['Ix']:>12.5f} "
        f"{sa['Iy']:>12.5f} "
        f"{sa['Ixy']:>12.5f} "
        f"{sa['Ip']:>12.5f} "
        f"{sa['I1']:>12.5f} "
        f"{sa['I2']:>12.5f} "
        f"{sa['rx']:>8.5f} "
        f"{sa['ry']:>8.5f} "
        f"{sa['Wx']:>10.5f} "
        f"{sa['Wy']:>10.5f} "
        f"{sa['J_sv_cell'][0]:>16.5f} "
        f"{sa['J_sv_cell'][1]:>12.5f}"
    )

# =============================================================================
# CSV export — one file per station
# =============================================================================
# Each file contains all polygon vertices of the section at that elevation.
# Output folder: out/sections/
# File naming  : section_<z_m>.csv   (z rounded to 3 decimal places)
# =============================================================================


csv_dir = os.path.join("../out", "sections")
os.makedirs(csv_dir, exist_ok=True)

print(f"\nExporting {n_sez} section CSV files to '{csv_dir}' ...")

for i in range(n_sez):
    z = z_min + i * (z_max - z_min) / (n_sez - 1) if n_sez > 1 else z_min
    z = min(z, z_max)

    # Retrieve the field and section that own this z coordinate
    field_at_z   = stack.field_at(z)

    # Build output path
    csv_path = os.path.join(csv_dir, f"section_{z:.3f}m.csv")

    with open(csv_path, "w", encoding="utf-8") as csv_file:
        # The 'put' callable receives one formatted line at a time.
        # csv_file.write adds a newline after each line.
        export_polygon_vertices_csv(
            field=field_at_z,
            zpos=z,
            put=lambda line, f=csv_file: f.write(line + "\n"),
            fmt="{:.10g}",
        )

print(f"Export complete — {n_sez} files written to '{csv_dir}'.")

# =============================================================================
# Close report file
# =============================================================================

_report_file.close()
print(f"Report written to: '{report_path}'.")

# =============================================================================
# 3D visualisation
# =============================================================================

ax = stack.plot_volume_3d_global(
    title="Pier50 — Urban Viaduct | Seismic Zone 2 | NTC2018 / EC8-2",
    line_percent=70.0,
    seed=2,
    display_scale=(1.0, 1.0,0.5),   # true proportions — pier is 50 m tall
    wire=True,
    colors=True,
)

# Thin lines without modifying the library
for line in ax.get_lines():
    line.set_linewidth(0.15)

plt.show()
