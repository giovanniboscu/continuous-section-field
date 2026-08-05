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
    6. compute Navier normal stresses;
    7. compute the shear-stress contribution associated with variation
       of the global CSF centroid curve;
    8. subtract the corresponding section resultants from the externally
       prescribed shear resultants;
    9. compute the Jourawski shear-stress contribution from the residual
       shear resultants;
   10. print the two shear-stress contributions separately.

Important:
    - the Jourawski and global-centroid-axis extrema are generally found
      at different physical points;
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
# Navier stress analysis uses:
#     N, Mx, My
#
# The global-centroid-axis shear analysis uses:
#     N, Mx, My
#
# The externally prescribed shear resultants represent the total section
# shear actions:
#
#     T_external = T_jourawski + T_centroid_axis
#
# Therefore Jourawski must not receive the external shear resultants
# directly. It must receive only the residual part remaining after the
# global-centroid-axis contribution has been removed.
#
# CSF convention:
#     Tx is the shear action associated with the longitudinal variation
#     of My;
#     Ty is the shear action associated with the longitudinal variation
#     of Mx.
#
# The x and y labels below refer to global section axes.

N = -100_000.0          # Axial force [N]
Mx = 25_000.0           # Bending moment about the x axis [N·m]
My = 10_000.0           # Bending moment about the y axis [N·m]
Tx_external = 5_000.0   # External shear resultant associated with My [N]
Ty_external = 10_000.0  # External shear resultant associated with Mx [N]


# ---------------------------------------------------------------------------
# 5. COMPUTE THE SECTION PROPERTIES AT z
# ---------------------------------------------------------------------------

section_at_z = field.section(z)
properties = section_properties(section_at_z)


# ---------------------------------------------------------------------------
# 6. COMPUTE NAVIER NORMAL STRESSES
# ---------------------------------------------------------------------------

# The function returns one result dictionary for each section polygon.
navier_rows = analyse_polygon_navier_stress(
    section_field=field,
    z=z,
    N=N,
    Mx=Mx,
    My=My,
)


# ---------------------------------------------------------------------------
# 7. COMPUTE GLOBAL-CENTROID-AXIS SHEAR STRESSES
# ---------------------------------------------------------------------------

# The global CSF centroid changes along z because the web depth changes.
#
# The function performs the following operations:
#
#     1. evaluates the single global axial-flexural CSF centroid C(z);
#     2. evaluates dCx/dz and dCy/dz;
#     3. calls the public Navier API once at the selected station;
#     4. transforms the Navier normal-stress field according to:
#
#            tau_x_centroid_axis = sigma_zz * dCx/dz
#            tau_y_centroid_axis = sigma_zz * dCy/dz
#
# The centroid derivative is constant over the selected section. The local
# variation of this contribution therefore follows the Navier normal-stress
# field.
#
# The corresponding section resultants are:
#
#     Tx_centroid_axis = N * dCx/dz
#     Ty_centroid_axis = N * dCy/dz
#
# The per-polygon extrema returned by this API inherit their coordinates
# from the Navier extrema. In the present polygon implementation, these
# coordinates are polygon vertices.
#
# Because dz is not prescribed, the derivative step is selected by the
# convergence procedure implemented by the API.
centroid_axis_result = analyse_polygon_centroid_axis_shear(
    section_field=field,
    z=z,
    N=N,
    Mx=Mx,
    My=My,
    debug=False,
)

centroid_axis_section = centroid_axis_result["section"]
centroid_axis_rows = centroid_axis_result["polygons"]


# ---------------------------------------------------------------------------
# 8. COMPUTE THE RESIDUAL SHEAR RESULTANTS FOR JOURAWSKI
# ---------------------------------------------------------------------------

# Section-resultant equilibrium is decomposed component by component:
#
#     Tx_external = Tx_jourawski + Tx_centroid_axis
#     Ty_external = Ty_jourawski + Ty_centroid_axis
#
# Consequently, the residual resultants passed to Jourawski are:
#
#     Tx_jourawski = Tx_external - Tx_centroid_axis
#     Ty_jourawski = Ty_external - Ty_centroid_axis
#
# A residual component may be negative. This simply means that its
# contribution acts in the direction opposite to the corresponding
# centroid-axis contribution while their sum still reproduces the
# externally prescribed resultant.
Tx_jourawski = (
    Tx_external
    - float(centroid_axis_section["Tx_centroid_axis"])
)
Ty_jourawski = (
    Ty_external
    - float(centroid_axis_section["Ty_centroid_axis"])
)


# ---------------------------------------------------------------------------
# 9. COMPUTE JOURAWSKI SHEAR STRESSES
# ---------------------------------------------------------------------------

# The Jourawski API evaluates the residual shear-stress field by scanning
# the section with global cuts:
#
#     tau_x_jourawski: evaluated through vertical cuts x = constant;
#     tau_y_jourawski: evaluated through horizontal cuts y = constant.
#
# These component names do not mean that tau_x depends only on Tx or that
# tau_y depends only on Ty. For a general section with Ixy != 0, each local
# component may depend on both residual resultants.
#
# The coordinates returned by the Jourawski API identify representative
# points of the cut segments used by the scan. They are not generally the
# same points returned by the global-centroid-axis API.
#
# num_sudx and num_sudy control the scan resolution used to locate the
# extrema of the two Jourawski components.
jourawski_rows = analyse_polygon_jourawski_shear_stress(
    section_field=field,
    z=z,
    Tx=Tx_jourawski,
    Ty=Ty_jourawski,
    num_sudx=100,
    num_sudy=100,
    debug=False,
)


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
    f"Tx_external = {Tx_external:.6e} N, "
    f"Ty_external = {Ty_external:.6e} N"
)

print("\nSHEAR-RESULTANT DECOMPOSITION")

# Print each equilibrium equation over three lines. This layout keeps the
# algebraic sign attached to each contribution and avoids visually
# ambiguous expressions such as "+ Ty_centroid_axis -0.000e+00".
print(f"Tx_external = {Tx_external:.6e} N")
print(f"  = ({Tx_jourawski:+.6e} N) Jourawski residual")
print(
    f"  + ({float(centroid_axis_section['Tx_centroid_axis']):+.6e} N) "
    "global-centroid-axis"
)

print(f"Ty_external = {Ty_external:.6e} N")
print(f"  = ({Ty_jourawski:+.6e} N) Jourawski residual")
print(
    f"  + ({float(centroid_axis_section['Ty_centroid_axis']):+.6e} N) "
    "global-centroid-axis"
)

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
# 11. PRINT POLYGON-WISE NAVIER RESULTS
# ---------------------------------------------------------------------------

print("\nNAVIER")

for row in navier_rows:
    # sigma_extreme is selected by absolute magnitude while preserving
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

print("\nJOURAWSKI RESIDUAL SHEAR")

print(
    "Coordinates reported in this block identify Jourawski scan "
    "cut-segment points."
)

for row in jourawski_rows:
    # Select the governing signed JOURAWSKI contribution among the four
    # extrema returned for this polygon.
    #
    # This selection is local to the Jourawski result set. It does not
    # represent the governing total shear stress because the centroid-axis
    # contribution has not been added at the same physical point.
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
# 13. PRINT GLOBAL-CENTROID-AXIS SHEAR RESULTS
# ---------------------------------------------------------------------------

print("\nGLOBAL CENTROID-AXIS SHEAR")

print(
    "Coordinates reported in this block are inherited from the "
    "polygon-wise Navier extrema."
)

print(
    f"Cx = {centroid_axis_section['Cx']:.6e} m  "
    f"Cy = {centroid_axis_section['Cy']:.6e} m"
)

print(
    f"dCx/dz = {centroid_axis_section['dCx_dz']:.6e}  "
    f"dCy/dz = {centroid_axis_section['dCy_dz']:.6e}"
)

print(
    f"Tx_centroid_axis = "
    f"{centroid_axis_section['Tx_centroid_axis']:.6e} N  "
    f"Ty_centroid_axis = "
    f"{centroid_axis_section['Ty_centroid_axis']:.6e} N"
)

# Each row below reports extrema of the centroid-axis contribution only.
#
# These extrema are generated by scaling the polygon-wise Navier extrema
# with dCx/dz or dCy/dz. They are therefore evaluated at Navier-extreme
# polygon vertices.
#
# They must not be added directly to the Jourawski extrema printed above,
# because the two APIs generally report different physical coordinates.
#
# The helper below identifies which Navier bound generated the governing
# centroid-axis bound. Multiplication by a negative centroid derivative
# reverses minimum and maximum:
#
#     derivative > 0:
#         tau_min <- sigma_min
#         tau_max <- sigma_max
#
#     derivative < 0:
#         tau_min <- sigma_max
#         tau_max <- sigma_min
#
# When the relevant centroid derivative is zero, the centroid-axis
# contribution is zero everywhere in that direction and no unique Navier
# source bound exists.
def source_navier_bound(
    *,
    direction: str,
    tau_bound: str,
) -> str:
    if direction == "x":
        derivative = float(centroid_axis_section["dCx_dz"])
    elif direction == "y":
        derivative = float(centroid_axis_section["dCy_dz"])
    else:
        raise ValueError(f"Unsupported shear direction: {direction!r}")

    if tau_bound not in ("min", "max"):
        raise ValueError(f"Unsupported centroid-axis bound: {tau_bound!r}")

    if derivative == 0.0:
        return "indeterminate (zero centroid derivative)"

    if derivative > 0.0:
        return "sigma_min" if tau_bound == "min" else "sigma_max"

    return "sigma_max" if tau_bound == "min" else "sigma_min"


for row in centroid_axis_rows:
    print(
        f"{row['idx']}:{row['name']}  "
        f"tau_x_min = {row['tau_x_min']:.6e} Pa  "
        f"tau_x_max = {row['tau_x_max']:.6e} Pa  "
        f"tau_y_min = {row['tau_y_min']:.6e} Pa  "
        f"tau_y_max = {row['tau_y_max']:.6e} Pa"
    )

    direction = str(row["tau_governing_direction"])
    tau_bound = str(row["tau_governing_bound"])
    navier_bound = source_navier_bound(
        direction=direction,
        tau_bound=tau_bound,
    )

    print(
        f"  tau_centroid_axis_governing = "
        f"{row['tau_governing']:.6e} Pa  "
        f"direction = {direction}  "
        f"tau_bound = {tau_bound}  "
        f"source_navier_bound = {navier_bound}  "
        f"at Navier-extreme vertex "
        f"({row['x_tau_governing']:.6e}, "
        f"{row['y_tau_governing']:.6e})"
    )
