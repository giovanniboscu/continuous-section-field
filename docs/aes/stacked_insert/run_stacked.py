from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from csf import export_polygon_vertices_csv_file
from csf.CSFStacked import CSFStacked
from csf.io.csf_reader import CSFReader
from csf.visualizer import Visualizer


# =============================================================================
# 1. CSF path
# =============================================================================
#
# The YAML files are referenced only here, to build the CSFStacked object.
# After build_csf_stack() returns, the CSF path receives only the evaluated
# CSF model object and never reads or reconstructs data directly from YAML.
# =============================================================================

CSF_SEGMENT_FILES = ("stacked_0.yaml", "stacked_1.yaml")

CSF_BASE_KEYS = ("A", "Cy", "Ix", "Iy")

CSF_UPPER_INSERT_POLYGON_INDEX = 1
CSF_LOWER_POLYGON_INDEX = 3

CSF_DERIVATIVE_DZ = 1.0e-4
CSF_DERIVATIVE_STATIONS = (1.0, 2.5, 4.0, 6.0, 7.5, 9.0)


def load_csf_field(path):
    """Read a CSF YAML file and return the corresponding field."""
    path = Path(path)

    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path

    res = CSFReader().read_file(str(path))

    if res.field is None:
        for issue in res.issues:
            print(issue)
        raise SystemExit(f"Failed to read {path}")

    return res.field


def build_csf_stack():
    """Build the stacked CSF model.

    This is the only step where the CSF path references the YAML file names.
    """
    stack = CSFStacked(eps_z=1e-9)

    for file_name in CSF_SEGMENT_FILES:
        stack.append(load_csf_field(file_name))

    return stack


def evaluate_csf_properties(stack, z, junction_side="left"):
    """Evaluate the stacked CSF model at the global coordinate z."""
    props = stack.section_full_analysis(float(z), junction_side=junction_side)

    missing = [key for key in CSF_BASE_KEYS if key not in props]
    if missing:
        raise KeyError(
            f"section_full_analysis() missing at z={z:.6g}: "
            + ", ".join(missing)
        )

    return props


def polygon_y_limits(section, polygon_index):
    """Return the minimum and maximum y-coordinate of one polygon."""
    polygon = section.polygons[polygon_index]
    y_values = [vertex.y for vertex in polygon.vertices]

    return min(y_values), max(y_values)


def variable_height_from_section(section):
    """Return h_lower = top(lower0) - bottom(lower0)."""
    lower_y_min, lower_y_max = polygon_y_limits(
        section,
        CSF_LOWER_POLYGON_INDEX,
    )
    return lower_y_max - lower_y_min


def variable_height_from_csf(stack, z, junction_side="left"):
    """Evaluate CSF at z and return h_lower."""
    section = stack.section(float(z), junction_side=junction_side)
    return variable_height_from_section(section)


def centroid_y_from_csf(stack, z, junction_side="left"):
    """Return Cy from the CSF section analysis at the requested station."""
    props = evaluate_csf_properties(stack, z, junction_side=junction_side)
    return props["Cy"]


def centered_scalar_derivative_from_csf(f, stack, z, dz, junction_side="left"):
    """Compute a centered finite-difference derivative from CSF evaluations."""
    z = float(z)
    dz = float(dz)

    q_plus = f(stack, z + dz, junction_side=junction_side)
    q_minus = f(stack, z - dz, junction_side=junction_side)

    return (q_plus - q_minus) / (2.0 * dz)


def print_csf_derivative_table(stack):
    """Print CSF-derived h_lower, Cy, and centered finite-difference derivatives."""
    header = (
        f"{'z':>6} | "
        f"{'h_lower':>10} {'dh_lower_dz':>14} | "
        f"{'c=Cy_csf':>12} {'dc_dz':>12}"
    )

    print("CSF non-constant geometric height at interior derivative stations")
    print(header)
    print("-" * len(header))

    for z in CSF_DERIVATIVE_STATIONS:
        h_lower = variable_height_from_csf(stack, z)

        dh_lower_dz = centered_scalar_derivative_from_csf(
            variable_height_from_csf,
            stack,
            z,
            CSF_DERIVATIVE_DZ,
        )

        c = centroid_y_from_csf(stack, z)

        c_prime = centered_scalar_derivative_from_csf(
            centroid_y_from_csf,
            stack,
            z,
            CSF_DERIVATIVE_DZ,
        )

        print(
            f"{z:6.2f} | "
            f"{h_lower:10.6f} {dh_lower_dz:14.6e} | "
            f"{c:12.6f} {c_prime:12.6e}"
        )

    print("-" * len(header))
    print(f"finite-difference step dz = {CSF_DERIVATIVE_DZ:.1e}")
    print("junction z = 5.0 is excluded from this derivative table")
    print()


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
    """Generate visual checks for the CSF path."""
    stack.plot_volume_3d_global(
        line_width=0.3,
        box_aspect_scale=(1.0, 1.0, 0.3),
    )

    stack.plot_properties(keys_to_plot=["A", "Cy", "Ix", "Iy"])

    stack.plot_section_2d(z=0, show_vertex_ids=False)

    vis0 = Visualizer(stack.field_at(1))
    vis0.plot_weight(poly_indices_to_plot=[CSF_UPPER_INSERT_POLYGON_INDEX])
    vis0.plot_shear_weight(poly_indices_to_plot=[CSF_UPPER_INSERT_POLYGON_INDEX])
    vis0.plot_volume_3d(
        show_end_sections=True,
        line_percent=100.0,
        seed="w",
        title="",
        ax=None,
    )
    vis0.plot_volume_3d(
        show_end_sections=True,
        line_percent=100.0,
        seed="s",
        title="",
        ax=None,
    )

    vis1 = Visualizer(stack.field_at(6))
    vis1.plot_weight(poly_indices_to_plot=[CSF_UPPER_INSERT_POLYGON_INDEX])
    vis1.plot_shear_weight(poly_indices_to_plot=[CSF_UPPER_INSERT_POLYGON_INDEX])

    plt.show()


# =============================================================================
# 2. Closed-form reference path
# =============================================================================
#
# This path is autonomous: all geometric dimensions, participation laws, and
# stations needed by the reference formulas are defined in code. It does not
# call CSFReader, CSFStacked, section(), section_full_analysis(), or field_at().
# =============================================================================

REF_L0, REF_L1, REF_L = 0.0, 5.0, 10.0

REF_UPPER_OUTER_WIDTH = 0.50
REF_UPPER_OUTER_HEIGHT = 0.25
REF_UPPER_OUTER_Y = 0.125

REF_UPPER_INSERT_WIDTH = 0.40
REF_UPPER_INSERT_HEIGHT = 0.20
REF_UPPER_INSERT_Y = 0.125

REF_UPPER_HOLE_WIDTH = 0.20
REF_UPPER_HOLE_HEIGHT = 0.10
REF_UPPER_HOLE_Y = 0.125

REF_LOWER_WIDTH = 0.30
REF_LOWER_TOP_Y = 0.00

REF_HEIGHT_VALUE_STATIONS = (0.0, 5.0, 10.0)


def comparison_lobatto_stations():
    """Return the station set used only by the comparison layer."""
    first = [
        REF_L0 + (REF_L1 - REF_L0) * u
        for u in COMPARISON_LOBATTO_11_UNIT
    ]

    second = [
        REF_L1 + (REF_L - REF_L1) * u
        for u in COMPARISON_LOBATTO_11_UNIT
    ][1:]

    return [float(z) for z in first + second]


def closed_form_local_coordinate(z):
    """Return segment index and local coordinate t in [0, 1]."""
    z = float(z)

    if z <= REF_L1:
        return 0, (z - REF_L0) / (REF_L1 - REF_L0)

    return 1, (z - REF_L1) / (REF_L - REF_L1)


def closed_form_insert_weight_law(z):
    """Evaluate the autonomous axial/bending participation law of upper0_insert."""
    segment, t = closed_form_local_coordinate(z)

    if segment == 0:
        w_insert = 1.5 + 0.5 * t
    else:
        w_insert = 2.0 - 0.5 * t

    return segment, t, w_insert


def closed_form_lower_geometry(z):
    """Evaluate the autonomous lower-component geometry."""
    segment, t = closed_form_local_coordinate(z)

    if segment == 0:
        h_lower = 0.30 - 0.10 * t
    else:
        h_lower = 0.20 + 0.10 * t

    y_lower = REF_LOWER_TOP_Y - 0.5 * h_lower

    return h_lower, y_lower


def rectangle_terms(width, height, y_centroid):
    """Return A, y, Ix_local, Iy_local for an axis-aligned rectangle."""
    A = width * height
    Ix_local = width * height**3 / 12.0
    Iy_local = height * width**3 / 12.0
    return A, y_centroid, Ix_local, Iy_local


def closed_form_reference_properties(z):
    """Compute autonomous A, Cy, Ix, and Iy."""
    _, _, w_insert = closed_form_insert_weight_law(z)
    h_lower, y_lower = closed_form_lower_geometry(z)

    components = [
        (
            1.0,
            rectangle_terms(
                REF_UPPER_OUTER_WIDTH,
                REF_UPPER_OUTER_HEIGHT,
                REF_UPPER_OUTER_Y,
            ),
        ),
        (
            w_insert - 1.0,
            rectangle_terms(
                REF_UPPER_INSERT_WIDTH,
                REF_UPPER_INSERT_HEIGHT,
                REF_UPPER_INSERT_Y,
            ),
        ),
        (
            -w_insert,
            rectangle_terms(
                REF_UPPER_HOLE_WIDTH,
                REF_UPPER_HOLE_HEIGHT,
                REF_UPPER_HOLE_Y,
            ),
        ),
        (
            1.0,
            rectangle_terms(
                REF_LOWER_WIDTH,
                h_lower,
                y_lower,
            ),
        ),
    ]

    weighted_areas = [w_eff * terms[0] for w_eff, terms in components]

    A = sum(weighted_areas)

    Cy = sum(
        weighted_area * terms[1]
        for weighted_area, (_, terms) in zip(weighted_areas, components)
    ) / A

    Ix = sum(
        w_eff * (Ix_local + A_geom * (y_centroid - Cy) ** 2)
        for w_eff, (A_geom, y_centroid, Ix_local, _) in components
    )

    Iy = sum(
        w_eff * Iy_local
        for w_eff, (_, _, _, Iy_local) in components
    )

    return A, Cy, Ix, Iy


def print_law_summary():
    """Print the autonomous laws used for the closed-form reference."""
    print("Closed-form laws used for the reference path")
    print("- z in [0, 5], t = z/5")
    print("  upper0 weight             : 1.0")
    print("  upper0_insert weight      : w_i(t) = 1.5 + 0.5*t")
    print("  upper0_insert_hole weight : 0.0")
    print("  lower height              : h_l(t) = 0.30 - 0.10*t")
    print("- z in [5, 10], t = (z - 5)/5")
    print("  upper0 weight             : 1.0")
    print("  upper0_insert weight      : w_i(t) = 2.0 - 0.5*t")
    print("  upper0_insert_hole weight : 0.0")
    print("  lower height              : h_l(t) = 0.20 + 0.10*t")
    print()


def print_closed_form_height_boundary_table():
    """Print autonomous h_lower at boundary stations."""
    header = f"{'z':>6} | {'h_lower_ref':>12}"

    print("Closed-form non-constant geometric height at boundary stations")
    print(header)
    print("-" * len(header))

    for z in REF_HEIGHT_VALUE_STATIONS:
        h_lower, _ = closed_form_lower_geometry(z)
        print(f"{z:6.2f} | {h_lower:12.6f}")

    print("-" * len(header))
    print()


# =============================================================================
# 3. Comparison layer: evaluated CSF values vs autonomous closed-form values
# =============================================================================

COMPARISON_LOBATTO_11_UNIT = (
    0.0,
    0.03299928479597031,
    0.10775826316842801,
    0.21738233650189726,
    0.3521209322065302,
    0.5,
    0.6478790677934697,
    0.7826176634981024,
    0.8922417368315718,
    0.96700071520403,
    1.0,
)


def compare_csf_against_closed_form_reference(stack):
    """Compare evaluated outputs from the two separated paths."""
    header = (
        f"{'z':>6} {'seg':>3} {'t':>5} {'w_i':>5} | "
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

    for z in comparison_lobatto_stations():
        props = evaluate_csf_properties(stack, z, junction_side="left")
        A_r, Cy_r, Ix_r, Iy_r = closed_form_reference_properties(z)

        segment, t, w_insert = closed_form_insert_weight_law(z)

        rel_err = max(
            abs(props["A"] - A_r) / max(abs(A_r), 1e-30),
            abs(props["Ix"] - Ix_r) / max(abs(Ix_r), 1e-30),
            abs(props["Iy"] - Iy_r) / max(abs(Iy_r), 1e-30),
        ) * 100.0

        cy_err = abs(props["Cy"] - Cy_r)

        max_rel_err = max(max_rel_err, rel_err)
        max_cy_err = max(max_cy_err, cy_err)

        print(
            f"{z:6.2f} {segment:3d} {t:5.2f} {w_insert:5.2f} | "
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
# 4. Main script
# =============================================================================

def main():
    stack = build_csf_stack()

    print_law_summary()
    compare_csf_against_closed_form_reference(stack)
    print_closed_form_height_boundary_table()
    print_csf_derivative_table(stack)

    export_selected_polygon_vertices(stack)
    show_visual_checks(stack)


if __name__ == "__main__":
    main()
