from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from csf import compute_lobatto_integration_points
from csf import export_polygon_vertices_csv_file
from csf.CSFStacked import CSFStacked
from csf.io.csf_reader import CSFReader
from csf.visualizer import Visualizer


# =============================================================================
# 1. Problem definition shared by both paths
# =============================================================================
#
# This script contains two intentionally separate paths:
#
#   CSF path:
#       YAML -> CSFStack -> section_full_analysis(z)
#
#   Closed-form reference path:
#       analytical rectangular geometry and participation laws -> A, Cy, Ix, Iy
#
# The closed-form path is specific to this controlled stacked-rectangle example.
# It is not a generic replacement for CSF and it does not call CSF section
# property routines.
# =============================================================================

# Common section width.
B = 0.30

# Global axial coordinates:
# - first CSF interval  : z in [0, 5]
# - second CSF interval : z in [5, 10]
L0, L1, L = 0.0, 5.0, 10.0

# Constant upper and middle component heights.
H_UPPER = 0.20
H_MIDDLE = 0.30

# Fixed centroid coordinates of upper and middle components.
Y_UPPER = 0.10
Y_MIDDLE = -0.15

# YAML files defining the two consecutive CSF intervals.
SEGMENT_FILES = ("stacked_0.yaml", "stacked_1.yaml")

# Number of Gauss-Lobatto stations used in each interval.
N_LOBATTO_POINTS = 11

# Section properties used in the closed-form comparison.
BASE_KEYS = ("A", "Cy", "Ix", "Iy")

# Polygon order in stacked_0.yaml and stacked_1.yaml.
# This derivative demonstration is intentionally specific to this example:
#   section.polygons[0] -> upper rectangle
#   section.polygons[1] -> middle rectangle
#   section.polygons[2] -> lower rectangle
UPPER_POLYGON_INDEX = 0
MIDDLE_POLYGON_INDEX = 1
LOWER_POLYGON_INDEX = 2

# Finite-difference step used only for the derivative demonstration table.
DERIVATIVE_DZ = 1.0e-4

# Interior stations used for the derivative demonstration table.
# The internal junction z = 5.0 is intentionally excluded.
DERIVATIVE_STATIONS = (1.0, 2.5, 4.0, 6.0, 7.5, 9.0)


# =============================================================================
# 2. CSF evaluation path
# =============================================================================
#
# This block reads the YAML files, builds CSFStack, and evaluates section
# properties from the CSF model.
#
# No closed-form section-property formula is used in this block.
# =============================================================================

def load_csf_field(path):
    """Read a CSF YAML file and return the corresponding field."""
    path = Path(path)

    # Resolve relative paths with respect to the script directory.
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path

    res = CSFReader().read_file(str(path))

    # Stop execution if the YAML reader did not produce a valid field.
    if res.field is None:
        for issue in res.issues:
            print(issue)
        raise SystemExit(f"Failed to read {path}")

    return res.field


def build_csf_stack():
    """Build the stacked CSF model from the two YAML interval files."""
    stack = CSFStacked(eps_z=1e-9)

    for file_name in SEGMENT_FILES:
        stack.append(load_csf_field(file_name))

    return stack


def evaluate_csf_properties(stack, z, junction_side="left"):
    """
    Evaluate the stacked CSF model at the global coordinate z.

    This is the CSF path used in the verification table.
    """
    props = stack.section_full_analysis(float(z), junction_side=junction_side)

    missing = [key for key in BASE_KEYS if key not in props]
    if missing:
        raise KeyError(
            f"section_full_analysis() missing at z={z:.6g}: "
            + ", ".join(missing)
        )

    return props


# =============================================================================
# 3. Independent closed-form reference path
# =============================================================================
#
# IMPORTANT:
# The following functions define the independent closed-form reference path.
# They do not call CSFStack, section(), section_full_analysis(), or any CSF
# section-property routine.
#
# They compute the analytical rectangular-section reference values A, Cy, Ix,
# and Iy for this controlled stacked-rectangle example only.
# =============================================================================

def closed_form_local_coordinate(z):
    """Return segment index and local coordinate t in [0, 1]."""
    z = float(z)

    if z <= L1:
        return 0, (z - L0) / (L1 - L0)

    return 1, (z - L1) / (L - L1)


def closed_form_upper_participation_laws(z):
    """
    Evaluate the analytical participation laws assigned to the upper component.

    These values reproduce the upper-component weight_law and shear_weight_law
    used in the corresponding YAML interval. They belong to the closed-form
    reference path and are not obtained from CSF evaluations.
    """
    segment, t = closed_form_local_coordinate(z)

    if segment == 0:
        # stacked_0.yaml, z in [0, 5]
        w_upper = 1.0 - 0.5 * (1.0 - t)
        sw_upper = 1.0 - 0.8 * (1.0 - t)
    else:
        # stacked_1.yaml, z in [5, 10]
        w_upper = 1.0 - 0.5 * t
        sw_upper = 1.0 - 0.8 * t

    return segment, t, w_upper, sw_upper


def closed_form_lower_geometry(z):
    """
    Evaluate the analytical geometry assigned to the lower component.

    The lower-component height is reconstructed from the linear law used in
    the active YAML interval. The lower top edge is fixed at y = -0.30.
    """
    segment, t = closed_form_local_coordinate(z)

    if segment == 0:
        # stacked_0.yaml: the lower height decreases from 0.30 to 0.20.
        h_lower = 0.30 - 0.10 * t
    else:
        # stacked_1.yaml: the lower height increases from 0.20 to 0.30.
        h_lower = 0.20 + 0.10 * t

    # Since the lower component is rectangular, its centroid is located
    # h_lower / 2 below the fixed top edge.
    y_lower = -0.30 - 0.5 * h_lower

    return h_lower, y_lower


def closed_form_reference_properties(z):
    """
    Compute A, Cy, Ix, and Iy from closed-form rectangular-section formulas.

    This function is the analytical reference path. It does not use any CSF
    section-property API.
    """
    _, _, w_upper, _ = closed_form_upper_participation_laws(z)
    h_lower, y_lower = closed_form_lower_geometry(z)

    # Geometric areas of the three rectangular components.
    A_upper_geom = B * H_UPPER
    A_middle_geom = B * H_MIDDLE
    A_lower_geom = B * h_lower

    # Weighted areas entering the section-property calculation.
    A_upper = w_upper * A_upper_geom
    A_middle = A_middle_geom
    A_lower = A_lower_geom

    # Total weighted area.
    A = A_upper + A_middle + A_lower

    # Weighted vertical centroid coordinate.
    Cy = (
        A_upper * Y_UPPER
        + A_middle * Y_MIDDLE
        + A_lower * y_lower
    ) / A

    # Local second moments of each rectangular component.
    Ix_upper_local = B * H_UPPER**3 / 12.0
    Ix_middle_local = B * H_MIDDLE**3 / 12.0
    Ix_lower_local = B * h_lower**3 / 12.0

    Iy_upper_local = H_UPPER * B**3 / 12.0
    Iy_middle_local = H_MIDDLE * B**3 / 12.0
    Iy_lower_local = h_lower * B**3 / 12.0

    # Weighted second moment about the global weighted centroidal x-axis.
    Ix = (
        w_upper * (Ix_upper_local + A_upper_geom * (Y_UPPER - Cy) ** 2)
        + Ix_middle_local + A_middle_geom * (Y_MIDDLE - Cy) ** 2
        + Ix_lower_local + A_lower_geom * (y_lower - Cy) ** 2
    )

    # Weighted second moment about the global y-axis.
    # The components are aligned on the same vertical axis, so no horizontal
    # parallel-axis term appears in this example.
    Iy = (
        w_upper * Iy_upper_local
        + Iy_middle_local
        + Iy_lower_local
    )

    return A, Cy, Ix, Iy


# =============================================================================
# 4. Station set shared by the verification table
# =============================================================================

def lobatto_stations():
    """
    Build the global list of Gauss-Lobatto stations used in the comparison.

    The stations are generated separately on the two CSF intervals. The shared
    junction station z = L1 is kept only once.
    """
    stations = list(
        compute_lobatto_integration_points(
            L0,
            L1,
            n_points=N_LOBATTO_POINTS,
        )
    )

    stations += list(
        compute_lobatto_integration_points(
            L1,
            L,
            n_points=N_LOBATTO_POINTS,
        )
    )[1:]

    return [float(z) for z in stations]


# =============================================================================
# 5. Verification: CSF path vs closed-form reference path
# =============================================================================

def print_law_summary():
    """Print the analytical laws used for the closed-form reference path."""
    print("Closed-form laws used for the reference path")
    print("- stacked_0.yaml, z in [0, 5], t = z/5")
    print("  upper weight       : w_u(t)  = 1.0 - 0.5*(1.0 - t)")
    print("  upper shear weight : sw_u(t) = 1.0 - 0.8*(1.0 - t)")
    print("  lower height       : h_l(t)  = 0.30 - 0.10*t")
    print("- stacked_1.yaml, z in [5, 10], t = (z - 5)/5")
    print("  upper weight       : w_u(t)  = 1.0 - 0.5*t")
    print("  upper shear weight : sw_u(t) = 1.0 - 0.8*t")
    print("  lower height       : h_l(t)  = 0.20 + 0.10*t")
    print("- lower shear_weight: iso(0.2)")
    print("- middle shear_weight: iso(0.2)")
    print()


def compare_csf_against_closed_form_reference(stack):
    """
    Compare CSF section properties against the closed-form reference.

    The verification table compares two separate paths:

        CSF path:
            YAML -> CSFStack -> section_full_analysis(z)

        Closed-form reference path:
            analytical rectangular geometry and participation laws
            -> A, Cy, Ix, Iy

    The closed-form reference is specific to this controlled example.
    """
    header = (
        f"{'z':>6} {'seg':>3} {'t':>5} {'w_u':>5} {'sw_u':>5} | "
        f"{'A_csf':>6} {'A_ref':>6} | "
        f"{'Cy_csf':>9} {'Cy_ref':>9} | "
        f"{'Ix_csf':>10} {'Ix_ref':>10} | "
        f"{'Iy_csf':>10} {'Iy_ref':>10} | "
        f"{'err_%':>9} {'err_Cy':>10}"
    )

    print("Closed-form verification table")
    print(header)
    print("-" * len(header))

    max_rel_err = 0.0
    max_cy_err = 0.0

    for z in lobatto_stations():
        # CSF path: evaluate the stacked CSF model at the global station.
        props = evaluate_csf_properties(stack, z, junction_side="left")

        # Closed-form reference path: compute independent rectangular values.
        A_r, Cy_r, Ix_r, Iy_r = closed_form_reference_properties(z)

        # Analytical laws printed together with the comparison table.
        segment, t, w_upper, sw_upper = closed_form_upper_participation_laws(z)

        # Maximum relative error over the scalar section quantities.
        rel_err = max(
            abs(props["A"] - A_r) / max(abs(A_r), 1e-30),
            abs(props["Ix"] - Ix_r) / max(abs(Ix_r), 1e-30),
            abs(props["Iy"] - Iy_r) / max(abs(Iy_r), 1e-30),
        ) * 100.0

        # Absolute centroid-coordinate error.
        cy_err = abs(props["Cy"] - Cy_r)

        max_rel_err = max(max_rel_err, rel_err)
        max_cy_err = max(max_cy_err, cy_err)

        print(
            f"{z:6.2f} {segment:3d} {t:5.2f} {w_upper:5.2f} {sw_upper:5.2f} | "
            f"{props['A']:6.2f} {A_r:6.2f} | "
            f"{props['Cy']:9.6f} {Cy_r:9.6f} | "
            f"{props['Ix']:10.7f} {Ix_r:10.7f} | "
            f"{props['Iy']:10.7f} {Iy_r:10.7f} | "
            f"{rel_err:9.2e} {cy_err:10.2e}"
        )

    print("-" * len(header))
    print(f"max relative error (A, Ix, Iy): {max_rel_err:.2e} %")
    print(f"max absolute error (Cy): {max_cy_err:.2e}")
    print()


# =============================================================================
# 6. CSF-only derivative extraction demonstration
# =============================================================================
#
# This block is not a closed-form validation.
#
# It demonstrates that interface coordinates and derived quantities can be
# sampled from evaluated CSF Section objects and differentiated by repeated CSF
# evaluations.
# =============================================================================

def polygon_y_limits(section, polygon_index):
    """Return the minimum and maximum y-coordinate of one polygon.

    This helper is deliberately simple and specific to the stacked rectangular
    example. It reads only the Section evaluated by CSF.
    """
    polygon = section.polygons[polygon_index]
    y_values = [vertex.y for vertex in polygon.vertices]

    return min(y_values), max(y_values)


def interface_heights_from_stacked_section(section):
    """Return h1, h2, h3, h4 for the three-rectangle stacked section.

    The section is assumed to contain exactly the three polygons used in this
    example, in the YAML order:

        0 -> upper rectangle
        1 -> middle rectangle
        2 -> lower rectangle

    The four interfaces are read directly from the evaluated CSF Section:

        h1 = bottom of lower polygon
        h2 = top of lower polygon
        h3 = top of middle polygon
        h4 = top of upper polygon

    This is intentionally not a generic layer-detection routine. If the polygon
    order changes, this function must be changed with the model.
    """
    lower_y_min, lower_y_max = polygon_y_limits(section, LOWER_POLYGON_INDEX)
    middle_y_min, middle_y_max = polygon_y_limits(section, MIDDLE_POLYGON_INDEX)
    upper_y_min, upper_y_max = polygon_y_limits(section, UPPER_POLYGON_INDEX)

    h1 = lower_y_min
    h2 = lower_y_max
    h3 = middle_y_max
    h4 = upper_y_max
    return h1, h2, h3, h4


def interface_heights_from_csf(stack, z, junction_side="left"):
    """Evaluate CSF at z and return h1, h2, h3, h4 from the Section."""
    section = stack.section(float(z), junction_side=junction_side)
    return interface_heights_from_stacked_section(section)


def centroid_y_from_csf(stack, z, junction_side="left"):
    """Return Cy from the CSF section analysis at the requested station."""
    props = evaluate_csf_properties(stack, z, junction_side=junction_side)
    return props["Cy"]


def centered_scalar_derivative_from_csf(f, stack, z, dz, junction_side="left"):
    """
    Compute a centered finite-difference derivative from CSF evaluations.

    The sampled values come from the evaluated CSF Section at z - dz and
    z + dz. The step dz is only the local differentiation perturbation.
    """
    z = float(z)
    dz = float(dz)

    q_plus = f(stack, z + dz, junction_side=junction_side)
    q_minus = f(stack, z - dz, junction_side=junction_side)

    return (q_plus - q_minus) / (2.0 * dz)


def centered_interface_derivatives_from_csf(stack, z, dz, junction_side="left"):
    """
    Compute h1', h2', h3', h4' from CSF Section evaluations.

    The function evaluates the stacked CSF model at z - dz and z + dz,
    extracts h1..h4 from each evaluated Section, and then differentiates each
    interface coordinate with the same centered finite-difference rule.
    """
    z = float(z)
    dz = float(dz)

    h_minus = interface_heights_from_csf(
        stack,
        z - dz,
        junction_side=junction_side,
    )
    h_plus = interface_heights_from_csf(
        stack,
        z + dz,
        junction_side=junction_side,
    )

    derivatives = []
    for h_minus_i, h_plus_i in zip(h_minus, h_plus):
        derivatives.append((h_plus_i - h_minus_i) / (2.0 * dz))

    return tuple(derivatives)


def print_section_derivative_table(stack):
    """
    Print the four CSF-derived interface coordinates and their derivatives.

    This table uses only values extracted from the evaluated CSF Section:

        h1, h2, h3, h4 = interface_heights_from_csf(stack, z)

    The derivatives h1'..h4' are computed by re-evaluating the same CSF field
    at z - dz and z + dz. The analytical closed-form laws are not used here.
    """
    header = (
        f"{'z':>6} | "
        f"{'h1':>10} {'h2':>10} {'h3':>10} {'h4':>10} | "
        f"{'dh1_dz':>12} {'dh2_dz':>12} "
        f"{'dh3_dz':>12} {'dh4_dz':>12} | "
        f"{'c=Cy_csf':>12} {'dc_dz':>12}"
    )

    print("Section-derived interface quantities")
    print(header)
    print("-" * len(header))

    for z in DERIVATIVE_STATIONS:
        h1, h2, h3, h4 = interface_heights_from_csf(stack, z)
        hp1, hp2, hp3, hp4 = centered_interface_derivatives_from_csf(
            stack,
            z,
            DERIVATIVE_DZ,
        )

        c = centroid_y_from_csf(stack, z)
        c_prime = centered_scalar_derivative_from_csf(
            centroid_y_from_csf,
            stack,
            z,
            DERIVATIVE_DZ,
        )

        print(
            f"{z:6.2f} | "
            f"{h1:10.6f} {h2:10.6f} {h3:10.6f} {h4:10.6f} | "
            f"{hp1:12.6e} {hp2:12.6e} {hp3:12.6e} {hp4:12.6e} | "
            f"{c:12.6f} {c_prime:12.6e}"
        )

    print("-" * len(header))
    print(f"finite-difference step dz = {DERIVATIVE_DZ:.1e}")
    print("h1..h4 and h1_prime..h4_prime are extracted from CSF Section evaluations")
    print("junction z = 5.0 is excluded from this derivative table")
    print()


# =============================================================================
# 7. Optional exports and visual checks
# =============================================================================

def export_selected_polygon_vertices(stack):
    """Export selected station-wise polygon vertices to CSV files."""
    fmt = ".12g"
    manual_stations = [0, 3, 5, 7, 10]

    for z in manual_stations:
        field_local = stack.field_at(z)
        csv_file = f"out/lobatto_station_export_{z}.csv"

        export_polygon_vertices_csv_file(
            field=field_local,
            z_values=[z],
            exp_filename=csv_file,
            fmt=fmt,
        )

        print(f"Wrote csf {csv_file}")

    print()


def show_visual_checks(stack):
    """Generate the same visual checks used for the stacked example."""
    stack.plot_volume_3d_global(
        line_width=0.3,
        box_aspect_scale=(1.0, 1.0, 0.3),
    )

    stack.plot_properties(keys_to_plot=["A", "Cy", "Ix", "Iy"])

    stack.plot_section_2d(z=0, show_vertex_ids=False)

    # Plot weight and shear-weight laws for the field selected at z = 1.
    vis0 = Visualizer(stack.field_at(1))
    vis0.plot_weight(poly_indices_to_plot=[0])
    vis0.plot_shear_weight(poly_indices_to_plot=[0])
    vis0.plot_volume_3d(
      show_end_sections=True,
      line_percent=100.0,
      seed='w',
      title="",
      ax=None
    )
    vis0.plot_volume_3d(
      show_end_sections=True,
      line_percent=100.0,
      seed='s',
      title="",
      ax=None
    )   
    
    # Plot weight and shear-weight laws for the field selected at z = 6.
    vis1 = Visualizer(stack.field_at(6))
    vis1.plot_weight(poly_indices_to_plot=[0])
    vis1.plot_shear_weight(poly_indices_to_plot=[0])

    plt.show()


# =============================================================================
# 8. Main script
# =============================================================================

def main():
    stack = build_csf_stack()

    print_law_summary()
    compare_csf_against_closed_form_reference(stack)
    print_section_derivative_table(stack)

    export_selected_polygon_vertices(stack)
    show_visual_checks(stack)


if __name__ == "__main__":
    main()
