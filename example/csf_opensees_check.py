from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from numpy.polynomial.legendre import Legendre


"""
CSF -> OpenSeesPy Checker / Builder (single file, no CLI)

================================================================================
WHAT CHANGED (IMPORTANT)
================================================================================
This version supports a "true" Gauss–Lobatto integration strategy *without*
creating any interpolated/new sections:

  - All section tags used at integration points come strictly from geometry.tcl.
  - If the CSF export uses Gauss–Lobatto stations across the full member length,
    we can model the member with a single forceBeamColumn element and use
    N integration points equal to the number of exported stations.

Why a single element?
  - If you create one element per station-to-station segment, each element span
    contains no internal stations, therefore you have no file-provided sections
    to assign to internal integration points (unless you interpolate, which is
    forbidden by the requirement).

AUTO MODE:
  - If centroid offsets (xc,yc) are constant (no tilt), AUTO uses:
        one element over the full member + N-point Gauss–Lobatto integration
    using all station sections from geometry.tcl.

  - If (xc,yc) vary along the member (tilt), AUTO falls back to:
        multiple elements between consecutive stations + 2-point endpoint sampling
    because geometric curvature requires intermediate nodes and you cannot populate
    internal integration points from file-only sections.

IMPORTANT POLICY (strict Lobatto):
  - If CSF_Z_STATIONS are present, member-level integration is allowed ONLY if
    those stations match Gauss–Lobatto abscissae (within tolerance).
  - No trapezoid (or any other) fallback weights are allowed in "member_lobatto":
    if stations do not match Lobatto, we raise an error.

================================================================================
INPUT FILE
================================================================================
This script reads "geometry.tcl" as a DATA FILE (do NOT source it).

It parses:
  - Optional header:
      # Beam Length: 10.000 m | Int. Points: 10
      # CSF_Z_STATIONS: z0 z1 ... zN-1   (strongly recommended)
  - geomTransf Linear 1 vx vy vz
  - section Elastic tag E A Iz Iy G J [xc yc]
  - optional node lines (informational only)

================================================================================
UNITS
================================================================================
OpenSees is unitless. Be consistent.
Printing can be scaled using DISP_OUTPUT_SCALE (e.g., m -> mm).
"""


# =============================================================================
# USER SETTINGS
# =============================================================================

GEOMETRY_FILE = "geometry.tcl"

# Prefer exact station coordinates exported by CSF:
PREFER_CSF_Z_STATIONS = True

# If CSF_Z_STATIONS is missing, allow fallback station generation:
ALLOW_FALLBACK_IF_MISSING_Z_STATIONS = True

# Fallback station distribution if CSF_Z_STATIONS is missing:
#   "lobatto": Gauss–Lobatto stations (includes endpoints)
#   "uniform": equally spaced stations (debug)
DISC = "lobatto"  # "lobatto" or "uniform"

# Cantilever verification load applied at the TIP reference node (global Y)
FY_TIP = -50000.0

# If geometry.tcl has no usable "Beam Length:" header AND no CSF_Z_STATIONS,
# fall back to this length:
BEAM_LENGTH_FALLBACK = 10.0

# Output formatting (unit conversion for printing only)
DISP_OUTPUT_SCALE = 1000.0
DISP_OUTPUT_UNIT = "mm"

# ---------------------------------------------------------------------------
# MATERIAL INPUT MODE
# ---------------------------------------------------------------------------
# Demonstrates the same behavior as your Tcl builder:
# - "from_file": use E, G from geometry.tcl
# - "override": force constant E/G in OpenSees section definitions
MATERIAL_INPUT_MODE = "override"  # "override" or "from_file"
E_OVERRIDE = 2.1e11
NU_OVERRIDE = 0.30
G_OVERRIDE = None  # if None -> computed from E/(2*(1+nu))

# ---------------------------------------------------------------------------
# INTEGRATION STRATEGY
# ---------------------------------------------------------------------------
# "auto":
#   - if no tilt -> single element, N-point Gauss–Lobatto across full member
#   - if tilt    -> segmented elements, 2-point endpoint sampling per segment
#
# "member_lobatto":
#   - force single element member with N-point Gauss–Lobatto (no segmentation)
#   - allowed only when (xc,yc) is constant (straight centroid axis)
#
# "segment_endpoints":
#   - always one element per station segment, 2-point endpoint integration
INTEGRATION_MODE = "auto"  # "auto" | "member_lobatto" | "segment_endpoints"

# Diagnostics
PRINT_PARSED_SUMMARY = True
PRINT_STATIONS_ENDS_ONLY = True

# =============================================================================
# STRICT LOBATTO SETTINGS
# =============================================================================

# When using member-level integration, CSF_Z_STATIONS must match Lobatto nodes.
LOBATTO_MATCH_TOL = 1e-6

# Tolerance used to detect whether centroid offsets vary along the member.
TILT_TOL = 1e-9


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SectionCSF:
    """
    One CSF station record.

    Notes:
      - A, Iz, Iy, J, xc, yc are always taken from the file (CSF export).
      - E, G can be taken from file or overridden by Python (see MATERIAL_INPUT_MODE).
    """
    tag: int
    E: float
    A: float
    Iz: float
    Iy: float
    G: float
    J: float
    xc: float = 0.0
    yc: float = 0.0


@dataclass
class GeometryCSF:
    """
    Parsed geometry container.
    """
    L: float
    n_stations: int
    vecxz: np.ndarray
    sections: List[SectionCSF]
    file_node1: Optional[np.ndarray] = None
    file_node2: Optional[np.ndarray] = None
    z_stations: Optional[List[float]] = None


# =============================================================================
# GAUSS–LOBATTO NODES AND WEIGHTS (for full-member integration)
# =============================================================================

def gauss_lobatto_nodes(N: int) -> np.ndarray:
    """
    Return Gauss–Lobatto nodes in [-1, 1], including endpoints -1 and +1.

    Nodes are:
      x0 = -1
      xN-1 = +1
      interior nodes are roots of d/dx P_{N-1}(x)
    """
    if N < 2:
        raise ValueError("Gauss–Lobatto requires N >= 2.")
    n = N - 1
    Pn = Legendre.basis(n)
    dPn = Pn.deriv()
    interior = dPn.roots()  # roots in (-1,1)
    xs = np.concatenate(([-1.0], interior, [1.0]))
    xs.sort()
    return xs


def gauss_lobatto_weights(N: int) -> np.ndarray:
    """
    Return Gauss–Lobatto-Legendre weights on [-1, 1] for the nodes returned
    by gauss_lobatto_nodes(N).

    Formula:
      w_i = 2 / (N*(N-1) * [P_{N-1}(x_i)]^2)
    where P_{N-1} is the Legendre polynomial of degree N-1.
    """
    if N < 2:
        raise ValueError("Gauss–Lobatto requires N >= 2.")
    xs = gauss_lobatto_nodes(N)
    n = N - 1
    Pn = Legendre.basis(n)
    Pvals = Pn(xs)
    w = 2.0 / (N * (N - 1) * (Pvals ** 2))
    return w


def lobatto_locs_weights_01(N: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Map Gauss–Lobatto nodes/weights from [-1,1] to [0,1].

    If x in [-1,1], map to s in [0,1] by:
      s = (x + 1)/2

    Integration weights scale by half:
      integral_0^1 f(s) ds = 0.5 * integral_-1^1 f((x+1)/2) dx
    Therefore:
      w01 = w / 2
    """
    xs = gauss_lobatto_nodes(N)
    ws = gauss_lobatto_weights(N)
    s = (xs + 1.0) / 2.0
    w01 = ws / 2.0
    return s, w01


def trapezoid_weights_on_01(s: np.ndarray) -> np.ndarray:
    """
    Generic trapezoid-rule weights on [0,1] for arbitrary monotone abscissae s.

    NOTE:
      This remains in the file for possible future use, but strict member-level
      Lobatto integration does NOT use this fallback.
    """
    N = len(s)
    if N < 2:
        raise ValueError("Need at least 2 points for trapezoid weights.")
    w = np.zeros(N, dtype=float)
    w[0] = 0.5 * (s[1] - s[0])
    for i in range(1, N - 1):
        w[i] = 0.5 * (s[i + 1] - s[i - 1])
    w[-1] = 0.5 * (s[-1] - s[-2])
    return w


# =============================================================================
# PARSING geometry.tcl as CSF DATA
# =============================================================================

def _strip_comments(line: str) -> str:
    """Remove Tcl-style comments (anything after '#')."""
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.strip()


def _is_strictly_increasing(xs: List[float], eps: float = 0.0) -> bool:
    """Station coordinates must be strictly increasing to define a valid axis."""
    for i in range(1, len(xs)):
        if not (xs[i] > xs[i - 1] + eps):
            return False
    return True


def parse_csf_geometry(file_path: str) -> GeometryCSF:
    """
    Parse geometry.tcl as a CSF data file.

    Reads:
      - Optional header beam length
      - Optional header line: "# CSF_Z_STATIONS: z0 z1 ... zN-1"
      - geomTransf Linear orientation vector (vecxz)
      - first two node lines (informational only)
      - all section Elastic lines (station properties + optional xc,yc)

    Ignores:
      - beamIntegration / element lines
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    header_len_re = re.compile(r"Beam\s*Length\s*:\s*([0-9.+-eE]+)")

    L_from_header: Optional[float] = None
    vecxz = np.array([1.0, 0.0, 0.0], dtype=float)

    z_stations: Optional[List[float]] = None
    sections: List[SectionCSF] = []
    file_nodes: List[np.ndarray] = []

    with open(file_path, "r", encoding="utf-8") as f:
        for raw in f:
            # Parse CSF_Z_STATIONS from raw (commented) line BEFORE stripping comments
            if "CSF_Z_STATIONS:" in raw:
                try:
                    tail = raw.split("CSF_Z_STATIONS:", 1)[1].strip()
                    z_stations = [float(x) for x in tail.split()]
                except Exception:
                    z_stations = None
                continue

            # Parse beam length from commented header
            mL = header_len_re.search(raw)
            if mL:
                try:
                    L_from_header = float(mL.group(1))
                except ValueError:
                    pass

            line = _strip_comments(raw)
            if not line:
                continue

            parts = line.split()

            # node tag x y z (informational only)
            if parts[0] == "node" and len(parts) >= 5:
                try:
                    x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                    file_nodes.append(np.array([x, y, z], dtype=float))
                except ValueError:
                    pass

            # geomTransf Linear 1 vx vy vz
            if parts[0] == "geomTransf" and len(parts) >= 6:
                try:
                    vecxz = np.array([float(parts[3]), float(parts[4]), float(parts[5])], dtype=float)
                except ValueError:
                    pass

            # section Elastic tag E A Iz Iy G J [xc yc]
            if len(parts) >= 9 and parts[0] == "section" and parts[1] == "Elastic":
                try:
                    tag = int(parts[2])
                    E = float(parts[3])
                    A = float(parts[4])
                    Iz = float(parts[5])
                    Iy = float(parts[6])
                    G = float(parts[7])
                    J = float(parts[8])

                    # If present, centroid offsets are appended as the last two fields.
                    # We detect them by total token count.
                    has_xy = len(parts) >= 11
                    xc = float(parts[9]) if has_xy else 0.0
                    yc = float(parts[10]) if has_xy else 0.0

                    sections.append(SectionCSF(tag, E, A, Iz, Iy, G, J, xc, yc))
                except ValueError:
                    continue

    if not sections:
        raise ValueError("No 'section Elastic' lines found. geometry.tcl does not look like CSF data.")

    N = len(sections)

    # Validate CSF_Z_STATIONS if present
    if z_stations is not None:
        if len(z_stations) != N:
            raise ValueError(
                f"CSF_Z_STATIONS length mismatch: expected {N}, got {len(z_stations)}. "
                "Regenerate geometry.tcl with consistent station export."
            )
        if not _is_strictly_increasing(z_stations, eps=0.0):
            raise ValueError("CSF_Z_STATIONS must be strictly increasing.")

    # Determine beam length L
    if L_from_header is not None:
        L = float(L_from_header)
    elif z_stations is not None:
        L = float(z_stations[-1] - z_stations[0])
    else:
        L = float(BEAM_LENGTH_FALLBACK)

    if L <= 0.0:
        raise ValueError("Invalid beam length (L<=0).")

    node1 = file_nodes[0] if len(file_nodes) >= 1 else None
    node2 = file_nodes[1] if len(file_nodes) >= 2 else None

    return GeometryCSF(
        L=L,
        n_stations=N,
        vecxz=vecxz,
        sections=sections,
        file_node1=node1,
        file_node2=node2,
        z_stations=z_stations,
    )


# =============================================================================
# LOCAL BASIS (for interpreting xc,yc consistently)
# =============================================================================

def build_local_basis(axis_e3: np.ndarray, vecxz: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a right-handed orthonormal basis (e1,e2,e3) for mapping CSF offsets.

    e3 = unit vector along the reference axis (member axis)
    e1 = projection of vecxz onto plane normal to e3 (local x)
    e2 = cross(e3, e1) (local y)
    """
    e3 = axis_e3 / np.linalg.norm(axis_e3)

    v = np.array(vecxz, dtype=float)
    if np.linalg.norm(v) < 1e-14:
        v = np.array([1.0, 0.0, 0.0], dtype=float)

    v_perp = v - np.dot(v, e3) * e3
    if np.linalg.norm(v_perp) < 1e-10:
        trial = np.array([1.0, 0.0, 0.0], dtype=float)
        if abs(np.dot(trial, e3)) > 0.9:
            trial = np.array([0.0, 1.0, 0.0], dtype=float)
        v_perp = trial - np.dot(trial, e3) * e3

    e1 = v_perp / np.linalg.norm(v_perp)
    e2 = np.cross(e3, e1)
    e2 = e2 / np.linalg.norm(e2)
    return e1, e2, e3


# =============================================================================
# MATERIAL HANDLING
# =============================================================================

def get_EG(sec: SectionCSF) -> Tuple[float, float]:
    """
    Decide where (E,G) come from:
      - from_file: use sec.E, sec.G
      - override:  use constants E_OVERRIDE and computed/forced G
    """
    mode = MATERIAL_INPUT_MODE.strip().lower()

    if mode == "from_file":
        return float(sec.E), float(sec.G)

    if mode == "override":
        E = float(E_OVERRIDE)

        if G_OVERRIDE is not None:
            G = float(G_OVERRIDE)
        else:
            nu = float(NU_OVERRIDE)
            G = E / (2.0 * (1.0 + nu))
        return E, G

    raise ValueError("MATERIAL_INPUT_MODE must be 'from_file' or 'override'.")


# =============================================================================
# STATION Z COORDINATES
# =============================================================================

def gauss_lobatto_nodes_01(N: int) -> np.ndarray:
    """Gauss–Lobatto nodes mapped to [0,1]."""
    xs = gauss_lobatto_nodes(N)
    return (xs + 1.0) / 2.0


def _compute_station_z(geom: GeometryCSF) -> Tuple[np.ndarray, bool]:
    """
    Return station z coordinates and whether they come from CSF_Z_STATIONS.
    """
    N = geom.n_stations

    if PREFER_CSF_Z_STATIONS and geom.z_stations is not None:
        z = np.array([float(v) for v in geom.z_stations], dtype=float)
        return z, True

    if not ALLOW_FALLBACK_IF_MISSING_Z_STATIONS:
        raise ValueError("CSF_Z_STATIONS missing but fallback disabled.")

    if DISC.strip().lower() == "lobatto":
        s = gauss_lobatto_nodes_01(N)
    elif DISC.strip().lower() == "uniform":
        s = np.linspace(0.0, 1.0, N)
    else:
        raise ValueError("DISC must be 'lobatto' or 'uniform'.")

    z = s * float(geom.L)
    return z, False


# =============================================================================
# OPENSEESPY MODEL BUILDER
# =============================================================================

def run_csf_opensees(geom: GeometryCSF, verbose: bool = True) -> float:
    """
    Build and run a cantilever analysis.

    Integration behavior depends on INTEGRATION_MODE (see top of file).
    """
    try:
        import openseespy.opensees as ops
    except Exception as e:
        raise RuntimeError("openseespy not available. Install openseespy.") from e

    secs = geom.sections
    N = geom.n_stations

    # Station longitudinal coordinates
    z_stations, using_csf_z = _compute_station_z(geom)

    # Reference axis: default aligned with global Z spanning station range
    z0 = float(z_stations[0])
    zN = float(z_stations[-1])
    start = np.array([0.0, 0.0, z0], dtype=float)
    end = np.array([0.0, 0.0, zN], dtype=float)

    axis = end - start
    if np.linalg.norm(axis) < 1e-12:
        raise ValueError("Invalid axis (zero length).")

    # Local basis for mapping centroid offsets
    e1, e2, e3 = build_local_basis(axis, geom.vecxz)

    # Tilt detection (robust): check variation across ALL stations (not only endpoints).
    xc_all = np.array([float(s.xc) for s in secs], dtype=float)
    yc_all = np.array([float(s.yc) for s in secs], dtype=float)
    tilt = (xc_all.max() - xc_all.min() > TILT_TOL) or (yc_all.max() - yc_all.min() > TILT_TOL)

    # Decide integration strategy
    mode = INTEGRATION_MODE.strip().lower()
    if mode == "auto":
        integration_member = (not tilt)  # single-element Lobatto only if no centroid variation
    elif mode == "member_lobatto":
        # Fail-fast: a single element cannot represent a varying centroid axis.
        if tilt:
            raise ValueError(
                "INTEGRATION_MODE='member_lobatto' requires constant (xc,yc). "
                "Use 'auto' or 'segment_endpoints'."
            )
        integration_member = True
    elif mode == "segment_endpoints":
        integration_member = False
    else:
        raise ValueError("INTEGRATION_MODE must be auto | member_lobatto | segment_endpoints")

    if verbose:
        print("\nSCANNING CSF DATA...")
        print(f"   => Stations N: {N}")
        print(f"   => Using CSF_Z_STATIONS: {'YES' if using_csf_z else 'NO'}")
        print(f"   => Centroid variation detected: {'YES' if tilt else 'NO'}")
        print(f"   => Integration mode: {INTEGRATION_MODE} (member_lobatto={integration_member})")
        E0, G0 = get_EG(secs[0])
        print(f"   => MATERIAL_INPUT_MODE: {MATERIAL_INPUT_MODE} (E={E0:.6g}, G={G0:.6g})")

    # ---------------- OpenSees domain ----------------
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    transfTag = 1
    ops.geomTransf("Linear", transfTag, float(geom.vecxz[0]), float(geom.vecxz[1]), float(geom.vecxz[2]))

    # Define all station sections (tags are taken from file; E/G maybe overridden)
    for s in secs:
        E, G = get_EG(s)
        ops.section(
            "Elastic",
            int(s.tag),
            float(E),
            float(s.A),
            float(s.Iz),
            float(s.Iy),
            float(G),
            float(s.J),
        )

    # -------------------------------------------------------------------------
    # NODE + ELEMENT TOPOLOGY
    # -------------------------------------------------------------------------
    # Reference nodes carry BC/load, centroid nodes carry elements, connected by rigidLink("beam").
    # This requires ops.constraints("Transformation").
    # -------------------------------------------------------------------------

    base_ref = 1
    base_cen = 10000

    if integration_member:
        # ============================================================
        # SINGLE ELEMENT OVER THE FULL MEMBER
        # - Use only endpoints nodes
        # - Use N-point Gauss–Lobatto integration using the station sections from geometry.tcl
        # - Allowed only when centroid offsets are constant
        # ============================================================

        ref_nodes = [base_ref, base_ref + 1]
        cen_nodes = [base_cen, base_cen + 1]

        # Since tilt is false here, centroid offsets are constant (use station 0).
        xc0 = float(secs[0].xc)
        yc0 = float(secs[0].yc)

        # Base nodes
        ref0 = start
        cen0 = ref0 + xc0 * e1 + yc0 * e2
        ops.node(ref_nodes[0], float(ref0[0]), float(ref0[1]), float(ref0[2]))
        ops.node(cen_nodes[0], float(cen0[0]), float(cen0[1]), float(cen0[2]))
        ops.rigidLink("beam", ref_nodes[0], cen_nodes[0])

        # Tip nodes
        ref1 = end
        cen1 = ref1 + xc0 * e1 + yc0 * e2
        ops.node(ref_nodes[1], float(ref1[0]), float(ref1[1]), float(ref1[2]))
        ops.node(cen_nodes[1], float(cen1[0]), float(cen1[1]), float(cen1[2]))
        ops.rigidLink("beam", ref_nodes[1], cen_nodes[1])

        if verbose:
            print("\nNODES (MEMBER-LEVEL):")
            print(f"   REF base({ref_nodes[0]}) = {ref0}")
            print(f"   CEN base({cen_nodes[0]}) = {cen0}")
            print(f"   REF tip ({ref_nodes[1]}) = {ref1}")
            print(f"   CEN tip ({cen_nodes[1]}) = {cen1}")

        # Strict Lobatto integration:
        # - Stations must match Lobatto abscissae. No trapezoid fallback.
        Lphys = float(zN - z0)
        if Lphys <= 0.0:
            raise ValueError("Invalid station span length.")

        s_from_file = (z_stations - z0) / Lphys  # normalize to [0,1]
        s_theory, w_theory = lobatto_locs_weights_01(N)

        if len(s_from_file) != len(s_theory):
            raise ValueError("Station count mismatch in Lobatto check.")

        max_diff = float(np.max(np.abs(s_from_file - s_theory)))
        if max_diff >= LOBATTO_MATCH_TOL:
            raise ValueError(
                "CSF_Z_STATIONS do not match Gauss–Lobatto nodes for N stations. "
                "Regenerate geometry.tcl with true Lobatto stations. "
                f"max |Δs| = {max_diff:.3e}"
            )

        locs = s_theory
        wts = w_theory

        if verbose:
            print(f"\n   Integration points match Gauss–Lobatto (max |Δs|={max_diff:.3e}). Using Lobatto weights.")

        sec_tags = [int(s.tag) for s in secs]

        intTag = 20000
        eleTag = 1

        # beamIntegration UserDefined intTag N secTags... locs... wts...
        ops.beamIntegration(
            "UserDefined",
            intTag,
            int(N),
            *sec_tags,
            *[float(x) for x in locs],
            *[float(w) for w in wts],
        )

        ops.element("forceBeamColumn", eleTag, cen_nodes[0], cen_nodes[1], transfTag, intTag)

        base_ref_node = ref_nodes[0]
        tip_ref_node = ref_nodes[1]

    else:
        # ============================================================
        # SEGMENTED ELEMENTS BETWEEN CONSECUTIVE STATIONS
        # - Create a node at each station to represent centroid axis (tilt/curvature)
        # - Use 2-point endpoint sampling per segment (Lobatto-2)
        # ============================================================

        ref_nodes: List[int] = []
        cen_nodes: List[int] = []

        if verbose:
            print("\nCREATING NODES (PER STATION) + RIGID LINKS:")

        for i, s in enumerate(secs):
            zpos = float(z_stations[i])
            ref_xyz = start + (zpos - z0) * e3
            cen_xyz = ref_xyz + float(s.xc) * e1 + float(s.yc) * e2

            refTag = base_ref + i
            cenTag = base_cen + i

            ops.node(refTag, float(ref_xyz[0]), float(ref_xyz[1]), float(ref_xyz[2]))
            ops.node(cenTag, float(cen_xyz[0]), float(cen_xyz[1]), float(cen_xyz[2]))
            ops.rigidLink("beam", refTag, cenTag)

            ref_nodes.append(refTag)
            cen_nodes.append(cenTag)

            if verbose and PRINT_STATIONS_ENDS_ONLY and (i == 0 or i == N - 1):
                print(
                    f"   Station {i+1:2}: REF({refTag})=({ref_xyz[0]:.4f},{ref_xyz[1]:.4f},{ref_xyz[2]:.4f})  "
                    f"CEN({cenTag})=({cen_xyz[0]:.4f},{cen_xyz[1]:.4f},{cen_xyz[2]:.4f})"
                )

        eleTag0 = 1
        intTag0 = 20000

        for i in range(N - 1):
            eleTag = eleTag0 + i
            intTag = intTag0 + i

            secI = int(secs[i].tag)
            secJ = int(secs[i + 1].tag)

            # Lobatto-2 on [0,1]: locs=[0,1], wts=[0.5,0.5]
            ops.beamIntegration(
                "UserDefined",
                intTag,
                2,
                secI, secJ,
                0.0, 1.0,
                0.5, 0.5,
            )

            ops.element("forceBeamColumn", eleTag, cen_nodes[i], cen_nodes[i + 1], transfTag, intTag)

        base_ref_node = ref_nodes[0]
        tip_ref_node = ref_nodes[-1]

    # -------------------------------------------------------------------------
    # ANALYSIS SETUP
    # -------------------------------------------------------------------------
    ops.fix(int(base_ref_node), 1, 1, 1, 1, 1, 1)

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    ops.load(int(tip_ref_node), 0.0, float(FY_TIP), 0.0, 0.0, 0.0, 0.0)

    # rigidLink => multi-point constraints => Transformation constraints handler
    ops.constraints("Transformation")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")

    ok = ops.analyze(1)
    if ok != 0:
        raise RuntimeError(f"OpenSees analysis failed (code={ok}).")

    uy = float(ops.nodeDisp(int(tip_ref_node), 2))  # DOF 2 = global Y

    if verbose:
        print("\nANALYSIS SUCCESSFUL")
        disp_print = abs(uy) * float(DISP_OUTPUT_SCALE)
        print(f"   Tip displacement Uy (reference node) = {disp_print:.6f} {DISP_OUTPUT_UNIT}")

    return uy


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    geom = parse_csf_geometry(GEOMETRY_FILE)

    if PRINT_PARSED_SUMMARY:
        print("\n================ PARSED geometry.tcl SUMMARY ================")
        print(f"File: {GEOMETRY_FILE}")
        print(f"Stations: {geom.n_stations}")
        print(f"Beam length L (fallback) = {geom.L} (units follow your model)")
        print(f"vecxz (geomTransf orientation) = {geom.vecxz}")
        if geom.z_stations is not None:
            print(f"CSF_Z_STATIONS: present (N={len(geom.z_stations)}), z0={geom.z_stations[0]}, zN={geom.z_stations[-1]}")
        else:
            print("CSF_Z_STATIONS: missing (fallback distribution will be used if allowed)")
        print("Section lines: tag, E, A, Iz, Iy, G, J, [xc, yc]")
        print("  - A/Iz/Iy/J/xc/yc are ALWAYS read from file.")
        print("  - E/G are taken from file only if MATERIAL_INPUT_MODE='from_file'.")
        print("=============================================================\n")

    uy = run_csf_opensees(geom, verbose=True)
    print(f"\nUy_tip = {uy:.6e} (in model length units)")


if __name__ == "__main__":
    main()