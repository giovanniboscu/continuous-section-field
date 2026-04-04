#!/usr/bin/env bash
# =============================================================================
# create_yaml_histwin.sh
# HISTWIN monitored steel wind tower — circular hollow tapered tower
#
# Behavior:
#   - no arguments : generate geometry YAML only
#   - -action      : generate action YAML only
# =============================================================================

set -euo pipefail

MODE="geometry"
if [ ! -d "out" ]; then
    mkdir -p out
fi
while [[ $# -gt 0 ]]; do
    case "$1" in
        -action|--action)
            MODE="action"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [-action]"
            echo "  no arguments : generate geometry YAML only"
            echo "  -action      : generate action YAML only"
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument '$1'"
            echo "Usage: $0 [-action]"
            exit 1
            ;;
    esac
done

# =============================================================================
# PARAMETER BLOCK — edit only this section
# =============================================================================

# Longitudinal coordinates [m]
z0="0.0"       # Base elevation of the tower shell
z1="76.15"     # Top elevation of the tower shell

# Base section S0 [m]
# The generator uses a rounded-rectangle representation.
# For a circular tower, set dx = dy = external diameter and R = diameter / 2.
s0_dx="4.300"      # External diameter at the base
s0_dy="4.300"      # External diameter at the base (same as dx for a circle)
s0_R="2.150"       # Base radius used by the rounded-rectangle generator
s0_tg="0.030"      # Wall thickness at the base
s0_x="0.0"         # Base section center X coordinate
s0_y="0.0"         # Base section center Y coordinate
s0_t_cell="0.0"    # Cell thickness tag written in the polygon name (0 = omitted)

# Head section S1 [m]
# For a circular tower, again set dx = dy = external diameter and R = diameter / 2.
s1_dx="3"      # External diameter at the top
s1_dy="3"      # External diameter at the top (same as dx for a circle)
s1_R="1.5"      # Top radius used by the rounded-rectangle generator
s1_tg="0.012"      # Wall thickness at the top
s1_x="0.0"         # Top section center X coordinate
s1_y="0.0"         # Top section center Y coordinate
s1_t_cell="0.0"    # Cell thickness tag written in the polygon name (0 = omitted)

# Discretization and twist
twist_deg="0"      # Rotation of the head section relative to the base [deg]
N="128"            # Number of points used to discretize each loop
singlepolygon="True"  # True = single polygon with @cell encoding

# Dummy rebar parameters required by writegeometry_rio_v2.py
# No rebars are intended in this model.
# The generator still requires all rebar CLI arguments, so neutral placeholder
# values are passed. Counts stay at zero, therefore no rebars are written.
n_bars_row1="0"        # Number of bars in outer row (kept at zero)
n_bars_row2="0"        # Number of bars in inner row (kept at zero)
area_bar_row1="1"      # Dummy area for outer-row bars; ignored because count = 0
area_bar_row2="1"      # Dummy area for inner-row bars; ignored because count = 0
dist_row1_outer="1"    # Dummy offset for outer-row bars; ignored because count = 0
dist_row2_inner="1"    # Dummy offset for inner-row bars; ignored because count = 0
rebar_weight="1"       # Dummy weight for rebars; ignored because count = 0

# Optional weight laws
#shell_law=""       # Leave empty for constant shell weight = 1.0

shell_law="np.maximum(0.84,1.0-0.10*np.exp(-((z-0.33*L)**2)/(2*(0.03*L)**2)) - 0.14*np.exp(-((z-0.67*L)**2)/(2*(0.03*L)**2)))"
shell_law="${shell_law//[[:space:]]/}"
s0_law="$shell_law"  # Must match s1_law if used
s1_law="$shell_law"  # Must match s0_law if used

# Output files
out="histwin_tower.yaml"   # Geometry file created in default mode
action_out="action.yaml"   # Action file created with -action

# Shared values derived from the inputs
L=$(python3 -c "print(float('$z1') - float('$z0'))")
ZMID=$(python3 -c "print((float('$z0') + float('$z1')) / 2.0)")

# =============================================================================
# ACTION FILE ONLY
# =============================================================================

if [[ "$MODE" == "action" ]]; then
    mkdir -p out
    cat > "$action_out" <<ACTION_EOF
CSF_ACTIONS:
  stations:
    # Two end stations only:
    # - 0.0   = tower base
    # - 76.15 = tower top
    # Useful when you want to inspect only the boundary sections.
    station_ends: [0.0, 76.15]

    # Single control station at mid-height.
    # Useful for a quick check of the section roughly in the middle of the member.
    station_mid: [38.075]

    # Denser user-defined sampling along the tower height.
    # Includes:
    # - both ends
    # - intermediate check sections
    # - the two segment-joint elevations
    # This is useful when you want a more detailed discrete inspection.
    station_dense: [0.0, 10.0, 21.8, 30.0, 38.075, 48.4, 60.0, 76.15]

  actions:
    # -------------------------------------------------------------------------
    # 3D visualization of the ruled volume generated between S0 and S1.
    # This is a geometric check only: it helps verify that interpolation,
    # pairing, and overall shape evolution are visually consistent.
    # -------------------------------------------------------------------------
    - plot_volume_3d:
        params:
          # Draw only 60% of the available generator lines.
          # Lower values reduce visual clutter.
          line_percent: 60.0

          # Color mode:
          # seed: w  -> color/appearance driven by weight-related representation
          # Useful for visually highlighting longitudinal variation.
          seed: w

          # Plot title shown in the figure window / saved image.
          title: "Histwin"

    # -------------------------------------------------------------------------
    # Detailed section report at selected stations.
    # For each requested station, CSF evaluates the section and writes
    # the requested geometric/mechanical properties.
    # -------------------------------------------------------------------------
    - section_selected_analysis:
        # Use the station list defined above.
        stations: station_ends

        output:
          # Save the report to a text file.
          - out/histwin_properties.txt

        # geometry:
        # When included in the properties list, the report also exports
        # the section geometry description at each requested station,
        # not only the numerical section properties.
        #
        # Other properties:
        # A                  = area
        # Cx, Cy             = centroid coordinates
        # Ix, Iy, Ixy        = second moments / product of inertia
        # Ip                 = polar inertia
        # I1, I2             = principal second moments
        # rx, ry             = radii of gyration
        # Wx, Wy             = section moduli
        # J_sv_cell          = Saint-Venant torsion estimate for cell-based treatment
        # Q_na               = first moment about neutral axis
        # J_s_vroark         = Vroark-type torsion estimate
        # J_s_vroark_fidelity= fidelity/quality indicator for Vroark estimate
        properties: [geometry, A, Cx, Cy, Ix, Iy, Ixy, Ip, I1, I2, rx, ry, Wx, Wy, J_sv_cell, Q_na, J_s_vroark, J_s_vroark_fidelity]

    # -------------------------------------------------------------------------
    # Plot of polygon weights / homogenization factors along z.
    # -------------------------------------------------------------------------
    - plot_weight:
        output:
          # stdout means "standard output":
          # the result is printed directly to the terminal/console,
          # instead of being written only to a file.
          # Useful for immediate inspection while running the action.
          - stdout

          # Save the plot to an image file as well.
          - out/histwin_weights.jpg

    # -------------------------------------------------------------------------
    # Plot selected properties as continuous curves along z.
    # This action does its own internal sampling between z0 and z1,
    # so named stations are NOT used here.
    # -------------------------------------------------------------------------
    - plot_properties:
        output:
          # Print summary/info to terminal.
          - stdout

          # Save plot to file.
          - out/histwin_properties.jpg

        # Properties to plot along the member axis.
        properties: [A, I1, Ip, J_sv_cell]

        params:
          # Number of internal sampling points used to build the curves.
          # Higher values give smoother plots but require more evaluations.
          num_points: 80

    # -------------------------------------------------------------------------
    # Volume report integrated along z using Gauss-Legendre quadrature.
    #
    # Reports:
    # - occupied volume   = purely geometric material presence
    # - homogenized volume = weight-adjusted volume
    #
    # stations is used here mainly to define/report the interval endpoints.
    # n_points controls numerical integration accuracy.
    # -------------------------------------------------------------------------
    - volume:
        stations: station_ends
        output:
          # Print the report to terminal.
          - stdout

          # Save the same report to file.
          - out/histwin_volume.txt

        params:
          # Number of Gauss-Legendre integration points.
          # Larger values generally improve integration accuracy.
          n_points: 10

          # Numeric display format for printed values.
          fmt_display: ".6f"

    # -------------------------------------------------------------------------
    # Area report grouped by weight value.
    #
    # Reports:
    # - occupied area     = raw geometric area
    # - homogenized area  = area multiplied by weight
    #
    # Useful to understand how much each weight group contributes
    # to the final section response.
    # -------------------------------------------------------------------------
    - section_area_by_weight:
        stations: station_ends
        output:
          # Print report to terminal.
          - stdout

          # Save report to file.
          - out/histwin_weight.txt

        params:
          # Ignore only polygons below this threshold.
          # With 0.0, everything with nonzero presence is considered.
          w_tol: 0.0

          # false = grouped summary only
          # true  = also list each individual polygon separately
          include_per_polygon: false

          # Compact numeric formatting in the report.
          fmt_display: ".6g"

    # -------------------------------------------------------------------------
    # Export section-property tables for general-purpose structural solvers
    # (for example SAP2000, OpenSeesPy, or custom workflows).
    #
    # Produces a template pack with fixed-width tables, typically including:
    # - solver input data
    # - section quality information
    # - torsion quality information
    # - station naming/indexing
    #
    # n_intervals defines the number of Gauss-Lobatto intervals.
    # The resulting number of stations is usually n_intervals + 1.
    #
    # For the full file format, see:
    # write_sap2000_template_pack.md
    # -------------------------------------------------------------------------
    - write_sap2000_geometry:
        # stations: station_3
        # Not used here because the export builds its own stationing
        # from n_intervals.
        stations: station_dense
        output:
          - out/histwin_template_pack.txt

        params:
          # Number of Gauss-Lobatto intervals used to generate stationing.
          # not used when stations is defined
          n_intervals: 10

          # Reference material name written into the export.
          material_name: "Steel S355"

          # Reference Young's modulus used in the exported solver data.
          E_ref: 2.1e+11

          # Poisson's ratio used to derive complementary elastic quantities.
          nu: 0.30

          # Export mode:
          # "BOTH" usually means both geometry/property tables are generated
          # according to the action implementation.
          mode: "BOTH"

          # false = do not generate the accompanying variation plot
          include_plot: false

          # Output filename for the plot, if include_plot is enabled.
          plot_filename: "out/histwin_variation.jpg"
          
                
ACTION_EOF

    echo "OK -- action file generated: $action_out"
    exit 0
fi

# =============================================================================
# GEOMETRY VALIDATION
# =============================================================================

errors=0

if python3 -c "import csf.utils.writegeometry_rio_v2" >/dev/null 2>&1; then
    echo "OK: module csf.utils.writegeometry_rio_v2 found"
else
    echo "ERROR: module csf.utils.writegeometry_rio_v2 not found."
    echo "       Make sure csfpy is installed in the active environment."
    errors=$((errors + 1))
fi

if python3 -c "import sys; sys.exit(0 if float('$z1') > float('$z0') else 1)"; then
    echo "OK: tower shell height = ${L} m  (z0=${z0}, z1=${z1})"
else
    echo "ERROR: z1 must be greater than z0.  Got z0=${z0}, z1=${z1}"
    errors=$((errors + 1))
fi

min_inner_s0=$(python3 -c "print(min(float('$s0_dx') - 2*float('$s0_tg'), float('$s0_dy') - 2*float('$s0_tg')))" )
min_inner_s1=$(python3 -c "print(min(float('$s1_dx') - 2*float('$s1_tg'), float('$s1_dy') - 2*float('$s1_tg')))" )

if python3 -c "import sys; sys.exit(0 if $min_inner_s0 > 0 else 1)"; then
    echo "OK: S0 internal void diameter = $(python3 -c "print(round(float('$s0_dx') - 2*float('$s0_tg'), 6))") m"
else
    echo "ERROR: S0 wall thickness (tg=${s0_tg}) is too large for section ${s0_dx}x${s0_dy} m."
    errors=$((errors + 1))
fi

if python3 -c "import sys; sys.exit(0 if $min_inner_s1 > 0 else 1)"; then
    echo "OK: S1 internal void diameter = $(python3 -c "print(round(float('$s1_dx') - 2*float('$s1_tg'), 6))") m"
else
    echo "ERROR: S1 wall thickness (tg=${s1_tg}) is too large for section ${s1_dx}x${s1_dy} m."
    errors=$((errors + 1))
fi

s0_R_max=$(python3 -c "print(min(float('$s0_dx'), float('$s0_dy')) / 2)")
s1_R_max=$(python3 -c "print(min(float('$s1_dx'), float('$s1_dy')) / 2)")

if python3 -c "import sys; sys.exit(0 if float('$s0_R') <= $s0_R_max else 1)"; then
    echo "OK: S0 corner radius R=${s0_R} m  (max allowed = ${s0_R_max} m)"
else
    echo "ERROR: S0 corner radius R=${s0_R} exceeds min(dx,dy)/2 = ${s0_R_max} m."
    errors=$((errors + 1))
fi

if python3 -c "import sys; sys.exit(0 if float('$s1_R') <= $s1_R_max else 1)"; then
    echo "OK: S1 corner radius R=${s1_R} m  (max allowed = ${s1_R_max} m)"
else
    echo "ERROR: S1 corner radius R=${s1_R} exceeds min(dx,dy)/2 = ${s1_R_max} m."
    errors=$((errors + 1))
fi

if [ "$s0_law" != "$s1_law" ]; then
    echo "ERROR: s0_law and s1_law must be identical strings."
    echo "       s0_law = '$s0_law'"
    echo "       s1_law = '$s1_law'"
    errors=$((errors + 1))
fi

if [ "$errors" -gt 0 ]; then
    echo ""
    echo "Found ${errors} error(s). Fix them before running the generator."
    exit 1
fi

echo ""
echo "Validation passed. Running generator..."
echo "Generator: python3 -m csf.utils.writegeometry_rio_v2"
echo ""

# =============================================================================
# RUN GEOMETRY GENERATOR
# =============================================================================

args=(
    --z0 "$z0" --z1 "$z1"
    --s0-x "$s0_x" --s0-y "$s0_y"
    --s0-dx "$s0_dx" --s0-dy "$s0_dy"
    --s0-R "$s0_R" --s0-tg "$s0_tg" --s0-t-cell "$s0_t_cell"
    --s1-x "$s1_x" --s1-y "$s1_y"
    --s1-dx "$s1_dx" --s1-dy "$s1_dy"
    --s1-R "$s1_R" --s1-tg "$s1_tg" --s1-t-cell "$s1_t_cell"
    --twist-deg "$twist_deg"
    --N "$N"
    --singlepolygon "$singlepolygon"
    --n-bars-row1 "$n_bars_row1"
    --n-bars-row2 "$n_bars_row2"
    --area-bar-row1 "$area_bar_row1"
    --area-bar-row2 "$area_bar_row2"
    --dist-row1-outer "$dist_row1_outer"
    --dist-row2-inner "$dist_row2_inner"
    --rebar-weight "$rebar_weight"
    --out "$out"
)

if [[ -n "${s0_law//[[:space:]]/}" ]]; then
    args+=(--s0-law "$s0_law")
fi
if [[ -n "${s1_law//[[:space:]]/}" ]]; then
    args+=(--s1-law "$s1_law")
fi

python3 -m csf.utils.writegeometry_rio_v2 "${args[@]}"

echo ""
echo "OK -- geometry generated: $out"
