from pathlib import Path

import matplotlib.pyplot as plt

from csf import compute_lobatto_integration_points
from csf import export_polygon_vertices_csv_file
from csf.CSFStacked import CSFStacked
from csf.io.csf_reader import CSFReader
from csf.visualizer import Visualizer


# ---------------------------------------------------------------------------
# Geometry and model constants
# ---------------------------------------------------------------------------

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


def load(path):
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


def local_coordinate(z):
    """Return segment index and local coordinate t in [0, 1]."""
    if z <= L1:
        return 0, (z - L0) / (L1 - L0)

    return 1, (z - L1) / (L - L1)


def upper_laws(z):
    """
    Evaluate the prescribed analytical laws of the upper component at the
    global coordinate z.

    The function first maps z to the corresponding CSF interval and to the
    local interpolation coordinate t in that interval. It then returns the
    axial/bending participation factor w_upper and the shear/torsion
    participation factor sw_upper assigned to the upper component in the
    corresponding YAML file.

    These values are used only for the closed-form comparison and for printing
    the verification table.
    
    segment, t = local_coordinate(z)
    """
    if segment == 0:
        # stacked_0.yaml, z in [0, 5]
        # weight_laws:
        #   upper,upper: 1.0 - 0.5*(1.0 - t)
        # shear_weight_laws:
        #   upper,upper: 1.0 - 0.8*(1.0 - t)
        w_upper = 1.0 - 0.5 * (1.0 - t)
        sw_upper = 1.0 - 0.8 * (1.0 - t)
    else:
        # stacked_1.yaml, z in [5, 10]
        # weight_laws:
        #   upper,upper: 1.0 - 0.5*t
        # shear_weight_laws:
        #   upper,upper: 1.0 - 0.8*t
        w_upper = 1.0 - 0.5 * t
        sw_upper = 1.0 - 0.8 * t

    return segment, t, w_upper, sw_upper


def lower_geometry(z):
    """
    Evaluate the analytical geometry assigned to the lower component.

    The global coordinate z is converted into the active segment and local
    coordinate t. The lower-component height is then reconstructed from the
    linear law used in the corresponding YAML interval.

    The function returns:
    - h_lower: lower-component height at z
    - y_lower: centroid coordinate of the lower component at z

    These values are used only in the closed-form reference calculation.
    """
    
    segment, t = local_coordinate(z)

    if segment == 0:
        # stacked_0.yaml: lower height decreases from 0.30 to 0.20.
        h_lower = 0.30 - 0.10 * t
    else:
        # stacked_1.yaml: lower height increases from 0.20 to 0.30.
        h_lower = 0.20 + 0.10 * t

    # The lower top edge is fixed at y = -0.30.
    # Therefore the lower centroid is shifted by h_lower / 2 below that edge.
    y_lower = -0.30 - 0.5 * h_lower

    return h_lower, y_lower


def reference(z):
    """
    Evaluate the closed-form reference section properties at the global
    coordinate z.

    The reference is built directly from the analytical rectangular-component
    geometry and from the prescribed upper-component participation law. It is
    used to compare the CSF-evaluated section properties against independent
    expressions for:

    - A  : weighted area
    - Cy : weighted vertical centroid coordinate
    - Ix : weighted second moment about the horizontal centroidal axis
    - Iy : weighted second moment about the vertical centroidal axis
    """   
    
    _, _, w_upper, _ = upper_laws(z)
    h_lower, y_lower = lower_geometry(z)

    # Geometric areas of the three rectangular components.
    A_upper_geom = B * H_UPPER
    A_middle_geom = B * H_MIDDLE
    A_lower_geom = B * h_lower

    # Weighted areas.
    # Only the upper component receives the axial/bending weight w_upper here.
    A_upper = w_upper * A_upper_geom
    A_middle = A_middle_geom
    A_lower = A_lower_geom

    # Total weighted area.
    A = A_upper + A_middle + A_lower

    # Weighted centroid coordinate.
    Cy = (
        A_upper * Y_UPPER
        + A_middle * Y_MIDDLE
        + A_lower * y_lower
    ) / A

    # Local second moments about each component centroid.
    Ix_upper_local = B * H_UPPER**3 / 12.0
    Ix_middle_local = B * H_MIDDLE**3 / 12.0
    Ix_lower_local = B * h_lower**3 / 12.0

    Iy_upper_local = H_UPPER * B**3 / 12.0
    Iy_middle_local = H_MIDDLE * B**3 / 12.0
    Iy_lower_local = h_lower * B**3 / 12.0

    # Weighted second moment about the global weighted centroid.
    # The upper component receives the same weight used for A and Cy.
    Ix = (
        w_upper * (Ix_upper_local + A_upper_geom * (Y_UPPER - Cy) ** 2)
        + Ix_middle_local + A_middle_geom * (Y_MIDDLE - Cy) ** 2
        + Ix_lower_local + A_lower_geom * (y_lower - Cy) ** 2
    )

    # Iy has no parallel-axis contribution because all rectangles share
    # the same horizontal centroid coordinate in this example.
    Iy = (
        w_upper * Iy_upper_local
        + Iy_middle_local
        + Iy_lower_local
    )

    return A, Cy, Ix, Iy


def print_law_summary():
    """Print the analytical laws used for the comparison."""
    print("Closed-form laws used for the comparison")
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


def lobatto_stations():
    """
    Build the global list of Gauss-Lobatto stations used in the comparison.

    The stations are generated separately on the two CSF intervals:

    - first interval  : [L0, L1]
    - second interval : [L1, L]

    The shared junction station z = L1 appears as the last station of the
    first interval and as the first station of the second interval. The first
    station of the second interval is therefore skipped to avoid duplicating
    the junction in the comparison table.
    """
    stations = list(
        compute_lobatto_integration_points(
            L0,
            L1,
            n_points=N_LOBATTO_POINTS,
        )
    )

    # Add stations from the second interval.
    # The first point is skipped to avoid duplicating z = L1.
    stations += list(
        compute_lobatto_integration_points(
            L1,
            L,
            n_points=N_LOBATTO_POINTS,
        )
    )[1:]

    return [float(z) for z in stations]


def compare_closed_form_and_csf(stack):
    """Compare CSF section properties against the closed-form reference."""
    header = (
        f"{'z':>6} {'seg':>3} {'t':>5} {'w_u':>5} {'sw_u':>5} | "
        f"{'A_csf':>6} {'A_ref':>6} | "
        f"{'Cy_csf':>9} {'Cy_ref':>9} | "
        f"{'Ix_csf':>10} {'Ix_ref':>10} | "
        f"{'Iy_csf':>10} {'Iy_ref':>10} | "
        f"{'err_%':>9} {'err_Cy':>10}"
    )

    print(header)
    print("-" * len(header))

    max_rel_err = 0.0
    max_cy_err = 0.0

    for z in lobatto_stations():
        # Evaluate the stacked CSF model at the current global station.
        sa = stack.section_full_analysis(z, junction_side="left")

        # Ensure that all required section properties are available.
        missing = [k for k in BASE_KEYS if k not in sa]
        if missing:
            raise KeyError(
                f"section_full_analysis() missing at z={z:.6g}: "
                + ", ".join(missing)
            )

        # Closed-form reference values at the same station.
        A_r, Cy_r, Ix_r, Iy_r = reference(z)

        # Analytical laws printed together with the comparison table.
        segment, t, w_upper, sw_upper = upper_laws(z)

        # Maximum relative error over the scalar section quantities.
        rel_err = max(
            abs(sa["A"] - A_r) / max(abs(A_r), 1e-30),
            abs(sa["Ix"] - Ix_r) / max(abs(Ix_r), 1e-30),
            abs(sa["Iy"] - Iy_r) / max(abs(Iy_r), 1e-30),
        ) * 100.0

        # Absolute centroid-coordinate error.
        cy_err = abs(sa["Cy"] - Cy_r)

        max_rel_err = max(max_rel_err, rel_err)
        max_cy_err = max(max_cy_err, cy_err)

        print(
            f"{z:6.2f} {segment:3d} {t:5.2f} {w_upper:5.2f} {sw_upper:5.2f} | "
            f"{sa['A']:6.2f} {A_r:6.2f} | "
            f"{sa['Cy']:9.6f} {Cy_r:9.6f} | "
            f"{sa['Ix']:10.7f} {Ix_r:10.7f} | "
            f"{sa['Iy']:10.7f} {Iy_r:10.7f} | "
            f"{rel_err:9.2e} {cy_err:10.2e}"
        )

    print("-" * len(header))
    print(f"max relative error (A, Ix, Iy): {max_rel_err:.2e} %")
    print(f"max absolute error (Cy): {max_cy_err:.2e}\n")


def main():
    # Build the stacked model from the two CSF interval files.
    stack = CSFStacked(eps_z=1e-9)

    for file_name in SEGMENT_FILES:
        stack.append(load(file_name))

    # Print the analytical laws and compare CSF values with closed-form values.
    print_law_summary()
    compare_closed_form_and_csf(stack)

    # Export selected station-wise polygon vertices.
    fmt = ".12g"
    manual_station = [0, 3, 5, 7, 10]

    for z in manual_station:
        fieldlocal = stack.field_at(z)
        csvfile = f"out/lobatto_station_export_{z}.csv"

        export_polygon_vertices_csv_file(
            field=fieldlocal,
            z_values=[z],
            exp_filename=csvfile,
            fmt=fmt,
        )

        print(f"Wrote csf {csvfile}")

    # Global visualization of the stacked volume.
    stack.plot_volume_3d_global(
        line_width=0.3,
        box_aspect_scale=(1.0, 1.0, 0.3),
    )

    # Plot selected section properties along the member axis.
    stack.plot_properties(keys_to_plot=["A", "Cy", "Ix", "Iy"])

    # Plot one evaluated 2D section.
    stack.plot_section_2d(z=2.5, show_vertex_ids=False)

    # Plot weight and shear-weight laws for the field evaluated at z = 1.
    vis0 = Visualizer(stack.field_at(1))
    vis0.plot_weight(poly_indices_to_plot=[0])
    vis0.plot_shear_weight(poly_indices_to_plot=[0])

    # Optional plot for the second interval.
    # vis1 = Visualizer(stack.field_at(7))
    # vis1.plot_shear_weight(poly_indices_to_plot=[0])

    # Optional diagnostic plots for each segment field.
    '''
    for idx, segment in enumerate(stack.segments):
        vis = Visualizer(segment.field)
        print(f"Plotting segment {idx} weight and shear_weight laws")
        vis.plot_weight()
        vis.plot_shear_weight()
    '''
    
    plt.show()


if __name__ == "__main__":
    main()
