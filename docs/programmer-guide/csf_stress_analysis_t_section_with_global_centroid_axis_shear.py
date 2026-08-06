"""
Minimal end-to-end example of the CSF stress-analysis APIs.

The model is built directly in Python, without external geometry or
settings files. One section of a tapered T-shaped Continuous Section
Field is evaluated under prescribed internal actions.

Workflow:
    1. define the start and end T-shaped sections;
    2. create the Continuous Section Field;
    3. select one station z;
    4. prescribe the internal actions at that station;
    5. compute the section properties;
    6. compute the complete Navier normal stresses from N, Mx, and My;
    7. compute Jourawski shear stresses from the section shear resultants
       Tx and Ty obtained from equilibrium with the external actions;
    8. compute the additional flexural centroid-axis contribution from
       Mx, My, and the derivative of the global CSF centroid curve;
    9. print the two shear-stress contributions separately.

The adopted separation is:

    tau_total = tau_jourawski(Tx, Ty) + tau_centroid_axis

with:

    tau_centroid_axis = sigma_zz_M * C'(z)

where sigma_zz_M is the flexural Navier field evaluated with N = 0.

Two distinct Navier fields therefore appear in this example:

    sigma_zz_complete = sigma_zz(N, Mx, My)

which is printed in the main NAVIER block, and:

    sigma_zz_M = sigma_zz(0, Mx, My)

which is evaluated internally by
``analyse_polygon_centroid_axis_shear()`` and is used only to form the
flexural centroid-axis shear contribution.

The two fields must not be confused. In particular, the ``sigma_min`` and
``sigma_max`` values returned inside ``centroid_axis_result["polygons"]``
refer to the flexural field evaluated with N = 0, not to the complete
normal-stress field printed in the main NAVIER block.

Important:
    - Tx and Ty are passed to Jourawski without centroid-axis additions
      or subtractions;
    - the flexural centroid-axis contribution is self-equilibrated;
    - the Jourawski and centroid-axis extrema are generally found at
      different physical points;
    - their separately reported governing values must not be added;
    - a total shear stress must be formed by evaluating both contributions
      at the same physical point.

The internal actions are prescribed directly. Their derivation from a
beam or structural model is outside the scope of this section-level
example.
"""

from csf import (
    ContinuousSectionField,
    Polygon,
    Pt,
    Section,
    section_properties,
)
from csf.section_field import (
    analyse_polygon_centroid_axis_shear,
    analyse_polygon_jourawski_shear_stress,
    analyse_polygon_navier_stress,
)


# ---------------------------------------------------------------------------
# 1. DEFINE THE START T-SECTION AT z = 0
# ---------------------------------------------------------------------------

L = 5.0

# The T-section is represented by two adjacent, non-overlapping polygons:
# a horizontal flange and a vertical web.
#
# Polygon vertices are listed counter-clockwise.

# Flange: rectangle from (-1.0, -0.2) to (1.0, 0.2).
poly0_start = Polygon(
    vertices=(
        Pt(-1.0, -0.2),
        Pt(1.0, -0.2),
        Pt(1.0, 0.2),
        Pt(-1.0, 0.2),
    ),
    weight=1.0,
    name="flange",
)

# Web: rectangle from (-0.2, -1.0) to (0.2, -0.2).
poly1_start = Polygon(
    vertices=(
        Pt(-0.2, -1.0),
        Pt(0.2, -1.0),
        Pt(0.2, -0.2),
        Pt(-0.2, -0.2),
    ),
    weight=1.0,
    name="web",
)


# ---------------------------------------------------------------------------
# 2. DEFINE THE END T-SECTION AT z = L
# ---------------------------------------------------------------------------

# The end section must contain the same number of polygons as the start
# section. Corresponding polygons must have the same names, vertex counts,
# and vertex ordering so that CSF can interpolate them along z.

# The flange remains unchanged along the field.
poly0_end = Polygon(
    vertices=(
        Pt(-1.0, -0.2),
        Pt(1.0, -0.2),
        Pt(1.0, 0.2),
        Pt(-1.0, 0.2),
    ),
    weight=1.0,
    name="flange",
)

# The bottom of the web moves from y = -1.0 at z = 0
# to y = -2.5 at z = L. The web depth therefore increases
# linearly along the longitudinal z axis.
poly1_end = Polygon(
    vertices=(
        Pt(-0.2, -2.5),
        Pt(0.2, -2.5),
        Pt(0.2, -0.2),
        Pt(-0.2, -0.2),
    ),
    weight=1.0,
    name="web",
)


# ---------------------------------------------------------------------------
# 3. CREATE THE ENDPOINT SECTIONS AND THE CONTINUOUS SECTION FIELD
# ---------------------------------------------------------------------------

# Polygon order establishes the correspondence between the endpoint
# sections:
#
#     poly0_start <-> poly0_end
#     poly1_start <-> poly1_end

s0 = Section(
    polygons=(poly0_start, poly1_start),
    z=0.0,
)

s1 = Section(
    polygons=(poly0_end, poly1_end),
    z=L,
)

# CSF linearly interpolates the corresponding polygon vertices and
# properties between z = 0 and z = L.
field = ContinuousSectionField(
    section0=s0,
    section1=s1,
)


# ---------------------------------------------------------------------------
# 4. SELECT THE STATION AND PRESCRIBE THE INTERNAL ACTIONS
# ---------------------------------------------------------------------------

# Evaluate the section at the midpoint of the field.
z = 2.5

# Signed internal actions acting directly on the section at z.
#
# Navier normal-stress analysis uses:
#     N, Mx, My
#
# Jourawski shear-stress analysis uses the section shear resultants:
#     Tx, Ty
#
# These resultants are obtained from beam equilibrium with the external
# actions. They are passed to Jourawski directly, without centroid-axis
# additions or subtractions.
#
# The flexural global-centroid-axis contribution uses:
#     Mx, My
#
# and internally evaluates the Navier field with N = 0.
#
# CSF convention:
#     Tx is the shear action associated with the longitudinal variation
#     of My;
#     Ty is the shear action associated with the longitudinal variation
#     of Mx.
#
# The x and y labels below refer to global section axes.

N = -100_000.0   # Axial force [N]
Mx = 25_000.0    # Bending moment about the x axis [N·m]
My = 10_000.0    # Bending moment about the y axis [N·m]
Tx = 5_000.0     # Section shear resultant associated with My [N]
Ty = 10_000.0    # Section shear resultant associated with Mx [N]


# ---------------------------------------------------------------------------
# 5. COMPUTE THE SECTION PROPERTIES AT z
# ---------------------------------------------------------------------------

section_at_z = field.section(z)
properties = section_properties(section_at_z)


# ---------------------------------------------------------------------------
# 6. COMPUTE NAVIER NORMAL STRESSES
# ---------------------------------------------------------------------------

# This call evaluates the complete polygon-wise Navier normal-stress field:
#
#     sigma_zz_complete = sigma_zz(N, Mx, My)
#
# It includes:
#
#     - the uniform axial contribution generated by N;
#     - the flexural contribution generated by Mx;
#     - the flexural contribution generated by My.
#
# The returned ``sigma_min``, ``sigma_max``, and ``sigma_extreme`` values
# are printed later in the block labelled:
#
#     NAVIER COMPLETE: N + Mx + My
#
# These values are not the same sigma bounds stored in
# ``centroid_axis_rows``. The latter are evaluated internally with N = 0.
#
# The function returns one result dictionary for each section polygon.
navier_rows = analyse_polygon_navier_stress(
    section_field=field,
    z=z,
    N=N,
    Mx=Mx,
    My=My,
)


# ---------------------------------------------------------------------------
# 7. COMPUTE JOURAWSKI SHEAR STRESSES
# ---------------------------------------------------------------------------

# Jourawski receives the section shear resultants Tx and Ty directly.
#
# These are the internal section resultants obtained from equilibrium with
# the external actions. They are the quantities associated with the
# longitudinal variation of the bending moments under the adopted CSF sign
# convention.
#
# No centroid-axis quantity is added to or subtracted from these inputs:
#
#     Tx_for_jourawski = Tx
#     Ty_for_jourawski = Ty
#
# In particular, this example does not construct a residual shear action.
#
# The API scans the section with global cuts:
#
#     tau_x_jourawski: evaluated through vertical cuts x = constant;
#     tau_y_jourawski: evaluated through horizontal cuts y = constant.
#
# For a general section with Ixy != 0, each local component may depend on
# both Tx and Ty.
#
# The coordinates returned by the Jourawski API identify representative
# points of the cut segments used by the scan.
jourawski_rows = analyse_polygon_jourawski_shear_stress(
    section_field=field,
    z=z,
    Tx=Tx,
    Ty=Ty,
    num_sudx=100,
    num_sudy=100,
    debug=False,
)


# ---------------------------------------------------------------------------
# 8. COMPUTE FLEXURAL GLOBAL-CENTROID-AXIS SHEAR STRESSES
# ---------------------------------------------------------------------------

# The global CSF axial-flexural centroid changes along z because the web
# depth changes continuously between the endpoint sections.
#
# The centroid curve is calculated from the complete CSF axial-flexural
# section, including the polygon geometry and axial-flexural participation.
# Its derivative is therefore a section-level quantity:
#
#     C'(z) = [dCx/dz, dCy/dz]
#
# The function:
#
#     1. evaluates the single global axial-flexural CSF centroid C(z);
#     2. evaluates dCx/dz and dCy/dz;
#     3. evaluates a separate flexural Navier field:
#
#            sigma_zz_M = sigma_zz(N=0, Mx, My)
#
#        The axial force N prescribed above is deliberately not passed to
#        this function and does not contribute to sigma_zz_M;
#
#     4. transforms the flexural field according to:
#
#            tau_x_centroid_axis = sigma_zz_M * dCx/dz
#            tau_y_centroid_axis = sigma_zz_M * dCy/dz
#
# Because the flexural Navier field has zero axial resultant, this
# centroid-axis contribution is self-equilibrated:
#
#     integral_A(tau_x_centroid_axis dA) = 0
#     integral_A(tau_y_centroid_axis dA) = 0
#
# The per-polygon extrema inherit their coordinates from the flexural
# Navier extrema evaluated with N = 0.
#
# Consequently, the ``sigma_min`` and ``sigma_max`` values contained in
# ``centroid_axis_rows`` are flexural-only values. They must not be compared
# directly with the complete sigma bounds printed from ``navier_rows``
# without accounting for the excluded axial contribution N/A.
#
# Because dz is not prescribed, the derivative step is selected by the
# convergence procedure implemented by the API.
centroid_axis_result = analyse_polygon_centroid_axis_shear(
    section_field=field,
    z=z,
    Mx=Mx,
    My=My,
    debug=False,
)

centroid_axis_section = centroid_axis_result["section"]
centroid_axis_rows = centroid_axis_result["polygons"]


# ---------------------------------------------------------------------------
# 9. FORMULATION USED BY THE EXAMPLE
# ---------------------------------------------------------------------------

# The two contributions are kept separate:
#
#     tau_total(x, y)
#         = tau_jourawski(x, y; Tx, Ty)
#         + tau_centroid_axis(x, y; Mx, My, C')
#
# Their separately reported extrema must not be added because they are
# generally located at different physical points.
#
# A pointwise total stress would require both fields to be evaluated at the
# same physical coordinates:
#
#     tau_total(x, y)
#         = tau_jourawski(x, y)
#         + tau_centroid_axis(x, y)
#
# This example intentionally prints the two envelopes separately and does
# not claim that the sum of their independent extrema is a total maximum.
#
#
# ---------------------------------------------------------------------------
# 10. PRINT SECTION PROPERTIES AND APPLIED ACTIONS
# ---------------------------------------------------------------------------

print(f"Station z = {z:.3f} m")

print(
    f"A = {properties['A']:.6e} m², "
    f"Ix = {properties['Ix']:.6e} m⁴, "
    f"Iy = {properties['Iy']:.6e} m⁴, "
    f"Ixy = {properties['Ixy']:.6e} m⁴"
)

print(
    f"Actions: "
    f"N = {N:.6e} N, "
    f"Mx = {Mx:.6e} N·m, "
    f"My = {My:.6e} N·m, "
    f"Tx = {Tx:.6e} N, "
    f"Ty = {Ty:.6e} N"
)

print("\nJOURAWSKI INPUT RESULTANTS")
print(f"Tx = {Tx:.6e} N")
print(f"Ty = {Ty:.6e} N")
print("No centroid-axis addition or subtraction is applied.")

print(
    "\nIMPORTANT: the Jourawski and global-centroid-axis extrema below "
    "are generally evaluated at different physical points."
)

print(
    "Their separately reported governing values must not be added. "
    "A total shear stress must be evaluated by summing both "
    "contributions at the same physical point."
)


# ---------------------------------------------------------------------------
# 11. PRINT POLYGON-WISE COMPLETE NAVIER RESULTS
# ---------------------------------------------------------------------------

print("\nNAVIER COMPLETE: N + Mx + My")

for row in navier_rows:
    # These sigma bounds belong to the complete field:
    #
    #     sigma_zz_complete = sigma_zz(N, Mx, My)
    #
    # ``sigma_extreme`` is selected by absolute magnitude while preserving
    # its original sign and governing coordinates.
    print(
        f"{row['idx']}:{row['name']}  "
        f"sigma_min = {row['sigma_min']:.6e} Pa  "
        f"sigma_max = {row['sigma_max']:.6e} Pa  "
        f"sigma_extreme = {row['sigma_extreme']:.6e} Pa  "
        f"at ({row['x']:.6e}, {row['y']:.6e})"
    )


# ---------------------------------------------------------------------------
# 12. PRINT POLYGON-WISE JOURAWSKI RESULTS
# ---------------------------------------------------------------------------

print("\nJOURAWSKI SHEAR")

print(
    "Coordinates reported in this block identify Jourawski scan "
    "cut-segment points."
)

for row in jourawski_rows:
    # Select the governing signed Jourawski contribution among the four
    # extrema returned for this polygon. This does not represent the
    # governing total shear stress because the centroid-axis contribution
    # has not been evaluated at the same physical point.
    #
    # Selection is based on absolute magnitude while preserving the
    # original sign, component direction, and Jourawski scan coordinates.
    candidates = [
        ("x", row["tau_x_min"], row["x_tau_x_min"], row["y_tau_x_min"]),
        ("x", row["tau_x_max"], row["x_tau_x_max"], row["y_tau_x_max"]),
        ("y", row["tau_y_min"], row["x_tau_y_min"], row["y_tau_y_min"]),
        ("y", row["tau_y_max"], row["x_tau_y_max"], row["y_tau_y_max"]),
    ]

    direction, tau_governing, x, y = max(
        candidates,
        key=lambda item: abs(item[1]),
    )

    print(
        f"{row['idx']}:{row['name']}  "
        f"tau_x_min = {row['tau_x_min']:.6e} Pa  "
        f"tau_x_max = {row['tau_x_max']:.6e} Pa  "
        f"tau_y_min = {row['tau_y_min']:.6e} Pa  "
        f"tau_y_max = {row['tau_y_max']:.6e} Pa"
    )

    print(
        f"  tau_jourawski_governing = {tau_governing:.6e} Pa  "
        f"direction = {direction}  "
        f"at Jourawski cut-segment point ({x:.6e}, {y:.6e})"
    )


# ---------------------------------------------------------------------------
# 13. PRINT FLEXURAL GLOBAL-CENTROID-AXIS SHEAR RESULTS
# ---------------------------------------------------------------------------

print("\nFLEXURAL GLOBAL CENTROID-AXIS SHEAR")

print(
    "Coordinates reported in this block are inherited from the "
    "polygon-wise FLEXURAL Navier extrema evaluated with N = 0."
)

print(
    "The sigma bounds referenced below are not the complete "
    "NAVIER N + Mx + My bounds printed above."
)

print(
    f"Cx = {centroid_axis_section['Cx']:.6e} m  "
    f"Cy = {centroid_axis_section['Cy']:.6e} m"
)

print(
    f"dCx/dz = {centroid_axis_section['dCx_dz']:.6e}  "
    f"dCy/dz = {centroid_axis_section['dCy_dz']:.6e}"
)

# Each row below reports extrema of the flexural centroid-axis
# contribution only:
#
#     tau_x_centroid_axis = sigma_zz_M * dCx/dz
#     tau_y_centroid_axis = sigma_zz_M * dCy/dz
#
# where:
#
#     sigma_zz_M = sigma_zz(N=0, Mx, My)
#
# The ``sigma_min`` and ``sigma_max`` values stored in each row therefore
# belong to the FLEXURAL Navier field, not to the complete Navier field
# evaluated earlier with N, Mx, and My.
#
# The centroid derivative is constant over the selected section. Scaling
# an affine Navier field by a section-constant value preserves the
# governing vertex, but the sign of the derivative controls whether the
# original minimum or maximum becomes the new minimum or maximum:
#
#     derivative > 0:
#         tau_min <- sigma_flexural_min
#         tau_max <- sigma_flexural_max
#
#     derivative < 0:
#         tau_min <- sigma_flexural_max
#         tau_max <- sigma_flexural_min
#
# For example, when dCy/dz < 0, the largest flexural normal stress produces
# the smallest tau_y value because multiplication reverses the ordering.
#
# When the relevant centroid derivative is exactly zero, the corresponding
# centroid-axis shear component is zero over the complete section. In that
# case there is no unique source sigma bound because both scaled candidates
# produce zero.
#
# This small helper is local to the reporting logic. It does not recalculate
# stresses and does not alter the analysis results. Its only purpose is to
# attach an unambiguous label to the flexural Navier bound that generated
# the reported centroid-axis bound.
def source_flexural_navier_bound(
    *,
    direction: str,
    tau_bound: str,
) -> str:
    """Return the flexural Navier bound that generated one tau bound."""

    # Select the section-constant centroid derivative associated with the
    # requested global shear component.
    if direction == "x":
        derivative = float(centroid_axis_section["dCx_dz"])
    elif direction == "y":
        derivative = float(centroid_axis_section["dCy_dz"])
    else:
        raise ValueError(f"Unsupported shear direction: {direction!r}")

    # The centroid-axis API reports signed minima and maxima only.
    if tau_bound not in ("min", "max"):
        raise ValueError(f"Unsupported centroid-axis bound: {tau_bound!r}")

    # A zero derivative produces a zero shear field in this direction.
    # No unique source bound can therefore be assigned.
    if derivative == 0.0:
        return "indeterminate (zero centroid derivative)"

    # A positive scale preserves the ordering of sigma_min and sigma_max.
    if derivative > 0.0:
        return (
            "sigma_flexural_min"
            if tau_bound == "min"
            else "sigma_flexural_max"
        )

    # A negative scale reverses the ordering.
    return (
        "sigma_flexural_max"
        if tau_bound == "min"
        else "sigma_flexural_min"
    )


for row in centroid_axis_rows:
    # These sigma values are returned by the internal Navier call performed
    # by ``analyse_polygon_centroid_axis_shear()`` with N = 0.
    #
    # Printing them explicitly makes the stress source traceable:
    #
    #     sigma_flexural -> multiply by C' -> tau_centroid_axis
    print(
        f"{row['idx']}:{row['name']}  "
        f"sigma_flexural_min = {row['sigma_min']:.6e} Pa  "
        f"sigma_flexural_max = {row['sigma_max']:.6e} Pa"
    )

    print(
        f"  tau_x_min = {row['tau_x_min']:.6e} Pa  "
        f"tau_x_max = {row['tau_x_max']:.6e} Pa  "
        f"tau_y_min = {row['tau_y_min']:.6e} Pa  "
        f"tau_y_max = {row['tau_y_max']:.6e} Pa"
    )

    # The API has already selected the signed centroid-axis value with the
    # largest absolute magnitude among:
    #
    #     tau_x_min, tau_x_max, tau_y_min, tau_y_max.
    direction = str(row["tau_governing_direction"])
    tau_bound = str(row["tau_governing_bound"])

    # Recover only the label of the flexural sigma bound that generated the
    # governing tau value. No numerical stress is recomputed here.
    flexural_navier_bound = source_flexural_navier_bound(
        direction=direction,
        tau_bound=tau_bound,
    )

    print(
        f"  tau_centroid_axis_governing = "
        f"{row['tau_governing']:.6e} Pa  "
        f"direction = {direction}  "
        f"tau_bound = {tau_bound}  "
        f"source_flexural_navier_bound = {flexural_navier_bound}  "
        f"at flexural-Navier-extreme vertex "
        f"({row['x_tau_governing']:.6e}, "
        f"{row['y_tau_governing']:.6e})"
    )
