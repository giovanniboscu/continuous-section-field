
"""Plot CUF, FEM3D, displacement differences, or signed Jacobians as 3D surfaces.

This tool evaluates the CUF compiled displacement checkpoint and the native
FEM3D H8 displacement field at the same physical points. In the same interactive
window, select the CUF field, the FEM3D field, or their difference (default).

The representation has three strictly separated responsibilities:
1. Data: sample the original CUF and FEM3D fields and store the unaltered NPZ.
2. Mathematical surface: select q(y,z) (scalar, magnitude, abs, difference) or
   the full-vector displaced section (x0+ux, y+uy, z+uz).
3. Rendering: a single field-independent engine fits the bounding box of ANY
   resulting 3D surface.  Its three observed coordinate ranges are normalized
   separately to visible view units; ONLY the resulting box proportions can be
   changed with the three sliders.  Real coordinate/color values are untouched
   and remain readable on the axes and in the click inspector.
- --polygon-index uses the original zero-based CSF polygon list index without shifts;
- the raw CUF, FEM3D and difference arrays are saved to NPZ for later inspection.
The --quantity jacobian mode adds 27 signed 3x3 displacement-gradient surfaces.
All sampled quadrilaterals are rendered, including across H8 interfaces;
no face masking or near-constant-field flattening is performed.
The default output includes a native Matplotlib 3D GUI window, with mouse
rotation/zoom, field/component/value-mode selection, height-scale adjustment, sample inspection,
and save-current-view. No HTML/browser is needed. Use --no-show to save PNG/NPZ
without opening a window (useful in headless environments).

No case-specific logic is included. The script only assumes:
- the selected CSF polygon is a 4-vertex quadrilateral;
- the FEM3D checkpoint is an H8 displacement NPZ supported by the existing
  boundary-plot tool family.
"""

from dataclasses import dataclass

import argparse
import math
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib import cm, colors, ticker
from matplotlib.widgets import Button, RadioButtons, Slider
import numpy as np

FIELD_COMPONENTS = {
    "difference": ("ux", "uy", "uz", "dtotal", "umag"),
    "fem3d": ("ux", "uy", "uz", "umag", "uvec"),
    "cuf": ("ux", "uy", "uz", "umag", "uvec"),
}
COMPONENT_LABELS = {
    "difference": (r"$\Delta u_x$", r"$\Delta u_y$", r"$\Delta u_z$",
                   r"$\Delta U$", r"$\|\Delta \mathbf{u}\|$"),
    "fem3d": (r"$u_x$", r"$u_y$", r"$u_z$", r"$\|\mathbf{u}\|$", r"$\mathbf{u}(x,y,z)$"),
    "cuf": (r"$u_x$", r"$u_y$", r"$u_z$", r"$\|\mathbf{u}\|$", r"$\mathbf{u}(x,y,z)$"),
}
FIELD_LABELS = {
    "difference": "CUF - FEM3D",
    "fem3d": "FEM3D",
    "cuf": "CUF",
}
FIELD_ARRAY_KEYS = {
    "difference": "du",
    "fem3d": "u_fem",
    "cuf": "u_cuf",
}
FIELD_OUTPUT_PREFIXES = {
    "difference": "du_surface",
    "fem3d": "fem3d_surface",
    "cuf": "cuf_surface",
}
# Components are indexed explicitly for signed and absolute-value plots.
COMPONENTS = {"ux": 0, "uy": 1, "uz": 2}
VALUE_MODES = ("signed", "absolute")
VALUE_MODE_LABELS = {"signed": "Signed", "absolute": "Absolute value"}

# Complete 3x3 displacement gradient in (x,y,z). Signed components only.
JACOBIAN_COMPONENTS = tuple(f"u{disp}_{coord}" for disp in "xyz" for coord in "xyz")
JACOBIAN_INDICES = {f"u{disp}_{coord}": (i, j) for i, disp in enumerate("xyz")
                    for j, coord in enumerate("xyz")}
JACOBIAN_LABELS = tuple(
    rf"$\partial u_{name[1]}/\partial {name[-1]}$"
    for name in JACOBIAN_COMPONENTS
)
JACOBIAN_ARRAY_KEYS = {
    "difference": "J_delta", "cuf": "J_cuf", "fem3d": "J_fem",
}

def available_components(field: str, quantity: str = "displacement"):
    if quantity == "jacobian":
        return JACOBIAN_COMPONENTS
    return FIELD_COMPONENTS[field]


def available_labels(field: str, quantity: str = "displacement"):
    if quantity == "jacobian":
        return JACOBIAN_LABELS
    return COMPONENT_LABELS[field]



def is_vector_geometry_component(field: str, component: str) -> bool:
    return component == "uvec" and field in {"cuf", "fem3d"}


def field_values(sampled: dict, field: str, component: str,
                 value_mode: str = "signed") -> np.ndarray:
    """Evaluate a selected scalar component or total-displacement quantity.

    For the CUF - FEM3D field:
    - ux, uy, uz: signed component differences, or their scalar absolute values;
    - dtotal (DU): ||u_CUF|| - ||u_FEM3D||, a signed scalar;
    - umag (ABS(Du)): ||u_CUF - u_FEM3D||, the vector-difference norm.

    Both definitions are mathematically distinct and retained independently.
    The full vector field u(x,y,z) is handled separately as a geometric mode.
    """
    if value_mode not in VALUE_MODES:
        raise ValueError(f"Unknown value mode: {value_mode!r}")
    if component in JACOBIAN_INDICES:
        if value_mode != "signed":
            raise ValueError("Jacobian components are signed only; no absolute values or norms")
        key = JACOBIAN_ARRAY_KEYS[field]
        if key not in sampled:
            raise ValueError("Jacobian has not been computed. Use --quantity jacobian")
        r, c = JACOBIAN_INDICES[component]
        return np.asarray(sampled[key], dtype=float)[..., r, c]
    if component not in FIELD_COMPONENTS[field]:
        raise ValueError(f"Component {component!r} is not available for {field!r}")
    if is_vector_geometry_component(field, component):
        raise ValueError("uvec is a geometric vector mode, not a scalar surface value")
    if component == "dtotal":
        u_cuf = np.asarray(sampled["u_cuf"], dtype=float)
        u_fem = np.asarray(sampled["u_fem"], dtype=float)
        selected = np.linalg.norm(u_cuf, axis=2) - np.linalg.norm(u_fem, axis=2)
        return selected if value_mode == "signed" else np.abs(selected)
    vector = np.asarray(sampled[FIELD_ARRAY_KEYS[field]], dtype=float)
    if component == "umag":
        return np.linalg.norm(vector, axis=2)
    selected = vector[:, :, COMPONENTS[component]]
    return selected if value_mode == "signed" else np.abs(selected)


def surface_metadata(field: str, component: str, polygon_label: str,
                     station_fraction: float, value_mode: str = "signed") -> tuple[str, str]:
    """Return accurate labels for a scalar component or total magnitude."""
    if value_mode not in VALUE_MODES:
        raise ValueError(f"Unknown value mode: {value_mode!r}")
    if component in JACOBIAN_INDICES:
        if value_mode != "signed":
            raise ValueError("The displacement Jacobian must remain signed")
        component_axis, coordinate_axis = component[1], component[-1]
        basis = rf"\partial u_{component_axis}/\partial {coordinate_axis}"
        value = (rf"\partial (u_{{{component_axis},CUF}} - "
                 rf"u_{{{component_axis},FEM3D}})/\partial {coordinate_axis}"
                 if field == "difference" else basis)
        return (
            f"{FIELD_LABELS[field]} signed displacement Jacobian on "
            f"{polygon_label} at x/L={station_fraction:g}\n${value}$",
            rf"${value}$",
        )
    if component == "dtotal":
        if field != "difference":
            raise ValueError("DU (difference of total magnitudes) requires the CUF - FEM3D field")
        expression = (r"\Delta U = \|\mathbf{u}_{CUF}\| - "
                      r"\|\mathbf{u}_{FEM3D}\|")
        scalar = r"\Delta U"
        if value_mode == "absolute":
            scalar = r"|\Delta U|"
            expression = r"|\Delta U| = |\|\mathbf{u}_{CUF}\| - \|\mathbf{u}_{FEM3D}\||"
        return (
            f"Difference of total displacement magnitudes on {polygon_label} "
            f"at x/L={station_fraction:g}\n${expression}$",
            rf"${scalar}$",
        )
    if component == "umag":
        if field == "difference":
            return (
                f"Vector-difference magnitude on {polygon_label} at x/L={station_fraction:g}\n"
                r"$\|\Delta \mathbf{u}\| = \|\mathbf{u}_{CUF} - \mathbf{u}_{FEM3D}\|$",
                r"$\|\Delta \mathbf{u}\|$",
            )
        return (
            f"{FIELD_LABELS[field]} total displacement magnitude on {polygon_label} "
            f"at x/L={station_fraction:g}",
            r"$\|\mathbf{u}\|$",
        )

    axis_label = component[-1]
    if field == "difference":
        scalar = rf"\Delta u_{axis_label}" if value_mode == "signed" else rf"|\Delta u_{axis_label}|"
        definition = (rf"\Delta u_{axis_label} = "
                      rf"u_{{{axis_label},CUF}} - u_{{{axis_label},FEM3D}}")
        if value_mode == "absolute":
            definition = rf"|\Delta u_{axis_label}| = |u_{{{axis_label},CUF}} - u_{{{axis_label},FEM3D}}|"
        return (
            f"Displacement difference on {polygon_label} at x/L={station_fraction:g}\n"
            rf"${definition}$",
            rf"${scalar}$",
        )

    scalar = rf"u_{axis_label}" if value_mode == "signed" else rf"|u_{axis_label}|"
    qualifier = " displacement" if value_mode == "signed" else " absolute displacement"
    return (
        f"{FIELD_LABELS[field]}{qualifier} on {polygon_label} at x/L={station_fraction:g}",
        rf"${scalar}$",
    )



def vector_surface_metadata(field: str, polygon_label: str,
                            station_fraction: float) -> tuple[str, str]:
    """Title and colorbar label for the full vector field u(x,y,z)."""
    return (
        f"{FIELD_LABELS[field]} deformed section on {polygon_label} at x/L={station_fraction:g}\n"
        r"$\mathbf{u}(x,y,z) = [u_x, u_y, u_z]^T$",
        r"$\|\mathbf{u}\|$",
    )


def deformed_surface_coordinates(Y: np.ndarray, Z: np.ndarray, U: np.ndarray, *,
                                 x_station: float):
    """Physical deformed-section coordinates, with NO graphical scale factors."""
    Xd = np.full_like(Y, float(x_station)) + U[:, :, 0]
    Yd = Y + U[:, :, 1]
    Zd = Z + U[:, :, 2]
    Umag = np.linalg.norm(U, axis=2)
    return Xd, Yd, Zd, Umag



# ---------------------------------------------------------------------------
# Geometry and display are separate.  No visualization transform may be fed
# back to the displacement arrays, scalar fields, or NPZ output.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SurfaceObject:
    """A *physical* parametrized 3D surface, before any display transform.

    Coordinates are real numerical values, not screen positions.  color_values
    are always original, unscaled scalar values.  axis_roles carry ONLY
    generic display semantics: two base directions and one thin direction.
    """

    coordinates: tuple[np.ndarray, np.ndarray, np.ndarray]
    color_values: np.ndarray
    axis_labels: tuple[str, str, str]
    axis_roles: tuple[str, str, str]
    title: str
    colorbar_label: str
    tick_offsets: tuple[float, float, float] = (0.0, 0.0, 0.0)
    signed_colors: bool = False
    zero_reference: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None
    fem_element_ids: np.ndarray | None = None
    flat_tolerance: float = 0.0  # view-only roundoff floor, not applied to samples

    def __post_init__(self):
        if set(self.axis_roles) != {"base_y", "base_z", "thickness"}:
            raise ValueError("Surface axis roles must be base_y, base_z, thickness")
        if len(self.coordinates) != 3 or len(self.axis_labels) != 3:
            raise ValueError("A surface requires three coordinate arrays and labels")
        shape = np.asarray(self.color_values).shape
        if len(shape) != 2 or min(shape) < 2:
            raise ValueError("A surface requires 2D sample grids of size >= 2")
        for array in (*self.coordinates, self.color_values):
            a = np.asarray(array)
            if a.shape != shape or not np.isfinite(a).all():
                raise ValueError("Invalid or non-finite surface coordinates/colors")
        if self.zero_reference is not None:
            if any(np.asarray(a).shape != shape for a in self.zero_reference):
                raise ValueError("The zero-reference plane must match the surface grid")
        if self.fem_element_ids is not None:
            if np.asarray(self.fem_element_ids).shape != shape:
                raise ValueError("FEM element IDs must match the surface grid")
        if not np.isfinite(self.flat_tolerance) or self.flat_tolerance < 0:
            raise ValueError("Roundoff view tolerance must be finite and nonnegative")


@dataclass(frozen=True)
class DisplayFrame:
    """Axis-independent affine conversion of physical coordinates to view units.

    Each nonconstant physical axis maps its OWN observed [min,max] interval to
    [-0.5,+0.5].  This avoids the thin-domain failure (e.g., 60 x 20 x 1e-3)
    WITHOUT modifying the sampled field or changing whether a plane is a plane.
    Physical numbers are restored in the axis tick labels and on mouse click.
    """

    low: tuple[float, float, float]
    high: tuple[float, float, float]

    @classmethod
    def from_surface(cls, surface: SurfaceObject) -> "DisplayFrame":
        low = [float(np.min(c)) for c in surface.coordinates]
        high = [float(np.max(c)) for c in surface.coordinates]
        thin_axis = surface.axis_roles.index("thickness")
        if surface.flat_tolerance > 0 and high[thin_axis] - low[thin_axis] <= surface.flat_tolerance:
            # Suppress only machine-precision DISPLAY spikes on an effectively
            # constant derivative. The original field and its NPZ remain EXACT.
            center = 0.5 * (high[thin_axis] + low[thin_axis])
            low[thin_axis] = high[thin_axis] = center
        return cls(tuple(low), tuple(high))

    @property
    def spans(self):
        return tuple(hi - lo for lo, hi in zip(self.low, self.high))

    def to_display_axis(self, axis: int, raw):
        raw = np.asarray(raw, dtype=float)
        width = self.spans[axis]
        if width == 0.0:
            return np.zeros_like(raw)
        # Center around zero to avoid displaying large station coordinates.
        return (raw - (self.low[axis] + 0.5 * width)) / width

    def to_physical_axis(self, axis: int, displayed):
        width = self.spans[axis]
        return self.low[axis] + (np.asarray(displayed) + 0.5) * width

    def to_display(self, coordinates):
        return tuple(self.to_display_axis(i, c) for i, c in enumerate(coordinates))


def make_scalar_surface(Y, Z, values, *, component: str, field: str,
                        value_mode: str, title: str, axis_value_label: str,
                        fem_element_ids=None, flat_tolerance: float = 0.0):
    """The graph of a scalar q(y,z): physical geometry (y,z,q).

    Neither q nor the base coordinates are amplified.  A zero-reference plane
    is only included when zero lies within an actually signed scalar range.
    """
    Y = np.asarray(Y, dtype=float)
    Z = np.asarray(Z, dtype=float)
    V = np.asarray(values, dtype=float)
    signed = value_mode == "signed" and component not in {"umag", "uvec"}
    reference = None
    if (signed and float(np.min(V)) < 0.0 < float(np.max(V))
            and np.ptp(V) > flat_tolerance):
        reference = (Y, Z, np.zeros_like(V))
    if component in JACOBIAN_INDICES:
        label = "Signed displacement derivative (native units; unscaled)"
    else:
        label = ("Actual difference (unscaled)" if field == "difference"
                 else "Actual displacement (unscaled)")
    return SurfaceObject(
        coordinates=(Y, Z, V), color_values=V,
        axis_labels=("y", "z", axis_value_label),
        axis_roles=("base_y", "base_z", "thickness"),
        title=title, colorbar_label=label, signed_colors=signed,
        zero_reference=reference, fem_element_ids=fem_element_ids,
        flat_tolerance=flat_tolerance,
    )


def make_vector_surface(Y, Z, vector, *, station_x: float, title: str):
    """The section displaced by ALL three components, with original values.

    This is the full-deformation view retained from v11.  The separate scalar
    surfaces q(y,z) remain available independently.  The display engine below
    does not distinguish this object from any other 3D surface.
    """
    Y = np.asarray(Y, dtype=float)
    Z = np.asarray(Z, dtype=float)
    U = np.asarray(vector, dtype=float)
    if U.shape != Y.shape + (3,):
        raise ValueError("A full-vector displacement must be a (nv,nu,3) array")
    Xd, Yd, Zd, Umag = deformed_surface_coordinates(Y, Z, U, x_station=station_x)
    return SurfaceObject(
        coordinates=(Xd, Yd, Zd), color_values=Umag,
        axis_labels=(r"$x-x_0=u_x$", r"$y+u_y$", r"$z+u_z$"),
        axis_roles=("thickness", "base_y", "base_z"),
        title=title, colorbar_label=r"$\|\mathbf{u}\|$ (unscaled)",
        tick_offsets=(float(station_x), 0.0, 0.0),
    )


def make_selected_surface(sampled: dict, *, field: str, component: str,
                          value_mode: str, station_x: float,
                          polygon_label: str, station_fraction: float) -> SurfaceObject:
    """Select the mathematical surface WITHOUT applying display scales."""
    Y = np.asarray(sampled["Y"], dtype=float)
    Z = np.asarray(sampled["Z"], dtype=float)
    if is_vector_geometry_component(field, component):
        title, _ = vector_surface_metadata(field, polygon_label, station_fraction)
        return make_vector_surface(
            Y, Z, sampled[FIELD_ARRAY_KEYS[field]],
            station_x=station_x, title=title,
        )
    value = field_values(sampled, field, component, value_mode)
    title, value_label = surface_metadata(
        field, component, polygon_label, station_fraction, value_mode,
    )
    fem_ids = (np.asarray(sampled["fem_element_id"], dtype=int)
               if component in JACOBIAN_INDICES and field != "cuf" else None)
    # Raw view: even very small numerical variations remain visible.
    return make_scalar_surface(
        Y, Z, value, field=field, component=component,
        value_mode=value_mode, title=title, axis_value_label=value_label,
        fem_element_ids=fem_ids, flat_tolerance=0.0,
    )


def jacobian_roundoff_floor(sampled, component: str) -> float:
    """View-only ULP floor for nearly constant Jacobian surfaces.

    Uses the magnitude of BOTH source gradients (not the tiny difference)
    to avoid magnifying floating-point cancellation into false mountains.
    Does not remove, interpolate, filter or alter any numerical data.
    """
    if component not in JACOBIAN_INDICES:
        return 0.0
    r, c = JACOBIAN_INDICES[component]
    source_max = max(float(np.max(np.abs(sampled[k][..., r, c])))
                     for k in ("J_cuf", "J_fem"))
    return 64.0 * np.finfo(float).eps * source_max


def make_color_mapping(surface: SurfaceObject):
    """Map original values to colors; geometry scaling cannot change colors."""
    v = surface.color_values
    lo = float(np.min(v))
    hi = float(np.max(v))
    cmap = cm.coolwarm
    if hi - lo <= surface.flat_tolerance:
        # Treat only roundoff-scale variations as constant for COLOR rendering.
        # Real samples/NPZ are never touched, and no fitting is involved.
        center = 0.5 * (lo + hi)
        half = max(surface.flat_tolerance * 2, abs(center) * 0.01, 1e-14)
        norm = colors.Normalize(vmin=center - half, vmax=center + half)
    elif surface.signed_colors and lo < 0.0 < hi:
        norm = colors.TwoSlopeNorm(vmin=lo, vcenter=0.0, vmax=hi)
    else:
        # In particular, an all-negative signed field must show local contrast.
        norm = colors.Normalize(vmin=lo, vmax=hi)
    return cmap, norm


def get_display_aspect(frame: DisplayFrame, surface: SurfaceObject, *,
                       y_scale: float = 1.0, z_scale: float = 1.0,
                       thickness_scale: float = 1.0) -> tuple[float, float, float]:
    """Aspect of the containing box, without knowing CUF/FEM/abs/u/etc.

    The two base axes retain the polygon's transverse width/height ratio;
    the thin axis is made visible by default (0.8 x the largest base extent).
    Sliders multiply only these three VISUAL proportions, after auto-fitting.
    """
    for value in (y_scale, z_scale, thickness_scale):
        if not np.isfinite(value) or value <= 0:
            raise ValueError("Display scales must be finite and strictly positive")
    iy = surface.axis_roles.index("base_y")
    iz = surface.axis_roles.index("base_z")
    width_y, width_z = frame.spans[iy], frame.spans[iz]
    base = max(width_y, width_z)
    if base == 0:
        aspect_y, aspect_z = 1.0, 1.0
    else:
        # Very thin BASE dimensions must remain visible as well.  This is a
        # screen-space lower bound, not a change of physical geometry.
        aspect_y = max(width_y / base, 0.12)
        aspect_z = max(width_z / base, 0.12)
    widths = {
        "base_y": aspect_y * y_scale,
        "base_z": aspect_z * z_scale,
        "thickness": 0.8 * thickness_scale,
    }
    return tuple(widths[role] for role in surface.axis_roles)


def _physical_tick_labels(frame: DisplayFrame, axis: int, offset: float):
    """Determine physically labeled ticks for a normalized display axis."""
    lo, hi = frame.low[axis], frame.high[axis]
    span = frame.spans[axis]
    if span == 0.0:
        raw = np.array([lo])
    else:
        raw = ticker.MaxNLocator(nbins=4).tick_values(lo, hi)
        raw = raw[(raw >= lo - 1e-10 * span) & (raw <= hi + 1e-10 * span)]
        if len(raw) < 2:
            raw = np.linspace(lo, hi, 5)
        raw = np.clip(raw, lo, hi)
        raw = np.unique(raw)

    # Enough decimals to distinguish nearby values, including large offsets.
    if span > 0:
        precision = min(13, max(0, int(math.ceil(-math.log10(span / 4.0))) + 1))
    else:
        precision = 6

    def fmt(value):
        shifted = float(value) - offset
        if abs(shifted) < 1e-12 * max(span, 1.0):
            shifted = 0.0
        if abs(shifted) >= 1e7 or (0.0 < abs(shifted) < 1e-5):
            return f"{shifted:.4g}"
        return f"{shifted:.{precision}f}"

    return frame.to_display_axis(axis, raw), [fmt(v) for v in raw]


@dataclass
class DrawnSurface:
    artist: object
    reference_artist: object | None
    display_frame: DisplayFrame
    display_coordinates: tuple[np.ndarray, np.ndarray, np.ndarray]
    mappable: object


def draw_surface(ax, surface: SurfaceObject, *, y_scale: float = 1.0,
                 z_scale: float = 1.0,
                 thickness_scale: float = 1.0) -> DrawnSurface:
    """The ONLY 3D renderer for scalar, vector, absolute and difference plots.

    It receives a geometry, builds its 3D bounding box and projects the three
    ranges to visible display intervals.  It has no field/component branches.
    All numeric and colorbar labels remain in physical units.
    """
    frame = DisplayFrame.from_surface(surface)
    display = frame.to_display(surface.coordinates)
    cmap, norm = make_color_mapping(surface)
    # Display every sampled quadrilateral, including ones crossing FEM H8
    # interfaces.  Never mask cells based on element ownership: the original
    # signed values are shown without silently removing any display faces.
    # A rendered quad spanning two elements is a visualization connection,
    # not a claim that the FEM displacement gradient is C0-continuous there.
    rgba = cmap(norm(surface.color_values))
    artist = ax.plot_surface(
        *display, rcount=display[0].shape[0], ccount=display[0].shape[1],
        facecolors=rgba,
        shade=False, linewidth=0, antialiased=True,
    )
    reference_artist = None
    if surface.zero_reference is not None:
        reference_artist = ax.plot_surface(
            *frame.to_display(surface.zero_reference),
            color="gray", alpha=0.12, linewidth=0, shade=False,
        )

    # The plotted coordinates are dimensionless view coordinates.  Real values
    # remain in the source data and are displayed on each physical axis.
    for index, axis in enumerate((ax.xaxis, ax.yaxis, ax.zaxis)):
        ticks, labels = _physical_tick_labels(frame, index, surface.tick_offsets[index])
        axis.set_major_locator(ticker.FixedLocator(ticks))
        axis.set_major_formatter(ticker.FixedFormatter(labels))
    ax.set_xlim(-0.55, 0.55)
    ax.set_ylim(-0.55, 0.55)
    ax.set_zlim(-0.55, 0.55)
    ax.set_box_aspect(
        get_display_aspect(frame, surface, y_scale=y_scale, z_scale=z_scale,
                           thickness_scale=thickness_scale), zoom=0.88,
    )
    ax.set_xlabel(surface.axis_labels[0])
    ax.set_ylabel(surface.axis_labels[1])
    ax.set_zlabel(surface.axis_labels[2])
    ax.set_title(surface.title, fontsize=10)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    return DrawnSurface(artist, reference_artist, frame, display, sm)


def save_surface_png(surface: SurfaceObject, output_path: Path, *,
                     y_scale: float = 1.0, z_scale: float = 1.0,
                     thickness_scale: float = 1.0):
    """Static PNG through the same visualization engine as the GUI."""
    fig = plt.figure(figsize=(10.0, 7.8))
    ax = fig.add_subplot(111, projection="3d")
    drawn = draw_surface(
        ax, surface, y_scale=y_scale, z_scale=z_scale,
        thickness_scale=thickness_scale,
    )
    ax.view_init(elev=30, azim=-60)
    fig.colorbar(drawn.mappable, ax=ax, shrink=0.75, aspect=18, pad=0.10,
                 label=surface.colorbar_label)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(output_path, dpi=220, bbox_inches="tight", pad_inches=0.10)
    finally:
        plt.close(fig)
    return output_path

class FEM3DH8:
    """Recover native H8 displacements from the FEM3D checkpoint.

    This is a reduced, displacement-only version of the helper used by the
    boundary post-processing tool. It supports both the standardized schema and
    the legacy I-Shape raw H8 NPZ schema.
    """

    SIGNS = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
    ], dtype=float)

    def __init__(self, path: Path):
        from scipy.spatial import cKDTree

        path = Path(path).expanduser().resolve()
        with np.load(path, allow_pickle=False) as data:
            keys = set(data.files)

            standard_required = {
                "format", "coordinate_system", "element_type", "version",
                "connectivity_index_base", "coordinates", "displacements",
                "connectivity", "element_ids", "units",
            }
            legacy_i_shape_required = {
                "nodes", "elements", "displacement", "amplitude", "x0", "x1",
            }

            if standard_required.issubset(keys):
                for key, value in (
                    ("format", "fem3d_h8_displacement"),
                    ("coordinate_system", "CUF"),
                    ("element_type", "stdBrick"),
                ):
                    if str(np.asarray(data[key]).item()) != value:
                        raise ValueError(f"FEM3D requires {key}={value!r}")
                if int(np.asarray(data["version"]).item()) != 1:
                    raise ValueError("Unsupported FEM3D checkpoint version")
                base = int(np.asarray(data["connectivity_index_base"]).item())
                if base not in (0, 1):
                    raise ValueError("FEM3D connectivity_index_base must be 0 or 1")

                coords = np.asarray(data["coordinates"], dtype=float)
                disp = np.asarray(data["displacements"], dtype=float)
                raw_conn = np.asarray(data["connectivity"])
                if not np.issubdtype(raw_conn.dtype, np.integer):
                    raise ValueError("FEM3D connectivity must contain integer indices")
                conn = raw_conn.astype(np.int64) - base
                self.ids = np.asarray(data["element_ids"])
                self.units = str(np.asarray(data["units"]).item())
                self.source_schema = "fem3d_h8_displacement v1"

            elif legacy_i_shape_required.issubset(keys):
                coords = np.asarray(data["nodes"], dtype=float)
                disp = np.asarray(data["displacement"], dtype=float)
                raw_conn = np.asarray(data["elements"])
                if not np.issubdtype(raw_conn.dtype, np.integer):
                    raise ValueError("Legacy FEM3D elements must contain integer indices")
                conn = raw_conn.astype(np.int64)
                self.ids = np.arange(len(conn), dtype=np.int64)
                self.units = str(np.asarray(data["units"]).item()) if "units" in keys else "native"
                self.source_schema = "legacy I-Shape H8 NPZ"

                x0 = float(np.asarray(data["x0"]).reshape(-1)[0])
                x1 = float(np.asarray(data["x1"]).reshape(-1)[0])
                if not np.isfinite(x0) or not np.isfinite(x1) or x1 <= x0:
                    raise ValueError(f"Invalid legacy FEM3D longitudinal domain: x0={x0}, x1={x1}")
            else:
                raise ValueError(
                    "Unsupported FEM3D NPZ schema. Expected either "
                    "fem3d_h8_displacement v1 or legacy I-Shape keys "
                    "{nodes,elements,displacement,amplitude,x0,x1}. "
                    "Available keys: " + ", ".join(sorted(keys))
                )

        if coords.ndim != 2 or coords.shape[1] != 3 or disp.shape != coords.shape:
            raise ValueError("FEM3D coordinates/displacements must have shape (nodes, 3)")
        if conn.ndim != 2 or conn.shape[1] != 8 or not len(conn):
            raise ValueError("FEM3D connectivity must have shape (elements, 8)")
        if self.ids.shape != (len(conn),) or len(np.unique(self.ids)) != len(conn):
            raise ValueError("FEM3D element_ids must be unique, one per element")
        if conn.min() < 0 or conn.max() >= len(coords):
            raise ValueError("FEM3D connectivity index outside node array")
        if not np.isfinite(coords).all() or not np.isfinite(disp).all():
            raise ValueError("Non-finite FEM3D coordinates/displacements")

        self.coords = coords[conn]
        self.disp = disp[conn]
        self.low = self.coords.min(axis=1)
        self.high = self.coords.max(axis=1)
        self.centers = self.coords.mean(axis=1)
        self.tol = 1e-9 * max(1.0, float(np.ptp(coords, axis=0).max()))
        box_centers = (self.low + self.high) / 2
        self.tree = cKDTree(box_centers)
        self.radius = float(np.linalg.norm((self.high - self.low) / 2, axis=1).max())

    @classmethod
    def shape(cls, q):
        t = 1.0 + cls.SIGNS * q
        n = t.prod(axis=1) / 8.0
        d = np.stack([
            cls.SIGNS[:, i] * t[:, (i + 1) % 3] * t[:, (i + 2) % 3] / 8.0
            for i in range(3)
        ], axis=1)
        return n, d

    def evaluate_matches(self, point: np.ndarray, *, with_gradient: bool = False):
        point = np.asarray(point, dtype=float)
        candidates = self.tree.query_ball_point(point, self.radius + self.tol)
        found = []
        for ei in sorted(candidates):
            if np.any(point < self.low[ei] - self.tol) or np.any(point > self.high[ei] + self.tol):
                continue
            q = np.zeros(3)
            for _ in range(25):
                n, d = self.shape(q)
                residual = n @ self.coords[ei] - point
                jac = self.coords[ei].T @ d
                if np.linalg.det(jac) <= 0:
                    raise ValueError(f"Invalid H8 Jacobian in element {self.ids[ei]}")
                if np.max(np.abs(residual)) <= self.tol:
                    break
                q -= np.linalg.solve(jac, residual)
            n, d = self.shape(q)
            if np.max(np.abs(q)) > 1 + 1e-7 or np.max(np.abs(n @ self.coords[ei] - point)) > self.tol:
                continue
            if with_gradient:
                jac = self.coords[ei].T @ d
                if np.linalg.det(jac) <= 0:
                    raise ValueError(f"Invalid H8 Jacobian in element {self.ids[ei]}")
                physical_shape_gradients = np.linalg.solve(jac.T, d.T).T
                du = self.disp[ei].T @ physical_shape_gradients
                found.append((ei, n @ self.disp[ei], du))
            else:
                found.append((ei, n @ self.disp[ei]))
        if not found:
            raise ValueError(f"No FEM3D element contains point {tuple(point)}; check geometry and units")
        return found

    def displacement(self, point: np.ndarray, *, rtol: float = 1e-7, atol: float = 1e-9) -> np.ndarray:
        matches = self.evaluate_matches(point)
        values = np.asarray([v for _, v in matches], dtype=float)
        reference = values[0]
        if not np.allclose(values, reference[None, :], rtol=rtol, atol=atol):
            raise ValueError(
                "Multiple FEM3D elements contain the sample point but do not agree on "
                f"the interpolated displacement at {tuple(point)}"
            )
        return reference

    def displacement_and_full_gradient(self, point: np.ndarray, *,
                                             interface_policy: str = "first",
                                             gradient_atol: float = 1e-10):
        """H8 displacement and signed 3x3 gradient, selecting one FEM side.

        Multiple containing elements are permitted at FEM interfaces. The
        displacement must be continuous. When one-sided gradients
        differ, 'first' chooses the smallest native element ID (never averages)
        and marks the sample; 'error' instead stops with an explanation.
        """
        found = self.evaluate_matches(point, with_gradient=True)
        found.sort(key=lambda item: int(self.ids[item[0]]))
        disp = found[0][1]
        if any(not np.allclose(disp, item[1], rtol=1e-7, atol=1e-9)
               for item in found[1:]):
            raise ValueError(f"Discontinuous FEM displacement at {tuple(point)}")
        selected = found[0][2]
        ambiguous = any(not np.allclose(selected, item[2],
                                        rtol=1e-8, atol=gradient_atol)
                        for item in found[1:])
        if ambiguous and interface_policy == "error":
            raise ValueError(
                "One-sided FEM3D gradients disagree at "
                f"{tuple(point)}. Select --fem-interface first explicitly."
            )
        return disp, selected, int(self.ids[found[0][0]]), ambiguous


def quad_shape(a: np.ndarray, b: np.ndarray):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return np.stack([
        0.25 * (1.0 - a) * (1.0 - b),
        0.25 * (1.0 + a) * (1.0 - b),
        0.25 * (1.0 + a) * (1.0 + b),
        0.25 * (1.0 - a) * (1.0 + b),
    ], axis=-1)


def polygon_vertices_yz(polygon) -> np.ndarray:
    vertices = np.asarray([(float(v.x), float(v.y)) for v in polygon.vertices], dtype=float)
    if vertices.shape != (4, 2):
        raise ValueError(
            f"Selected polygon {getattr(polygon, 'name', '<unnamed>')!r} must have exactly 4 vertices; "
            f"got shape {vertices.shape}"
        )
    return vertices


def resolve_station(x0: float, x1: float, x: float | None, x_over_L: float | None) -> tuple[float, float]:
    if x is not None and x_over_L is not None:
        raise ValueError("Use either --x or --x-over-L, not both")
    if x is None and x_over_L is None:
        x_over_L = 0.5
    if x is not None:
        station = float(x)
        s = (station - x0) / (x1 - x0)
    else:
        s = float(x_over_L)
        station = x0 + s * (x1 - x0)
    if not (x0 <= station <= x1):
        raise ValueError(f"Requested station x={station:g} lies outside [{x0:g}, {x1:g}]")
    return station, s


def load_csf_field(csf_yaml: Path):
    from csf.io.csf_reader import CSFReader
    from csf.io.csf_issues import CSFIssues

    result = CSFReader().read_file(str(csf_yaml))
    if not result.ok or result.field is None:
        raise ValueError(CSFIssues.format_report(result.issues))
    field = result.field
    return field, float(field.s0.z), float(field.s1.z)


def load_cuf_compiled_field(checkpoint: Path):
    from csf.cuf.solver.compiled_field import CompiledDisplacementField

    return CompiledDisplacementField.load(checkpoint)


def pick_polygon(section, polygon_index: int | None, polygon_name: str | None):
    if (polygon_index is None) == (polygon_name is None):
        raise ValueError("Provide exactly one of --polygon-index or --polygon-name")
    if polygon_index is not None:
        if polygon_index < 0 or polygon_index >= len(section.polygons):
            raise IndexError(f"polygon-index {polygon_index} outside [0, {len(section.polygons) - 1}]")
        return polygon_index, section.polygons[polygon_index]
    matches = [i for i, p in enumerate(section.polygons) if getattr(p, "name", None) == polygon_name]
    if len(matches) != 1:
        raise ValueError(f"polygon-name {polygon_name!r} matched {len(matches)} polygons")
    i = matches[0]
    return i, section.polygons[i]


def checkpoint_domain_for_polygon(compiled_field, polygon, x):
    """Find saved solved CUF domain by physical polygon vertices (v4/v5).

    An explicit solved-domain side is essential on shared polygon boundaries.
    Legacy global expansions v1-v3 return None.
    """
    domains = compiled_field.domain_vertices_at(float(x))
    if domains is None:
        return None
    expected = polygon_vertices_yz(polygon)
    matches = []
    for index, candidate in enumerate(domains):
        candidate = np.asarray(candidate, dtype=float)
        if candidate.shape != expected.shape:
            continue
        tolerance = 1e-9 * max(1.0, np.max(np.abs(expected)),
                              np.max(np.abs(candidate)))
        unused = list(range(len(candidate)))
        for vertex in expected:
            ids = [j for j in unused if np.allclose(vertex, candidate[j],
                                                    rtol=0, atol=tolerance)]
            if not ids:
                break
            unused.remove(ids[0])
        else:
            matches.append(index)
    if len(matches) != 1:
        raise ValueError(
            "The compiled CUF transverse domain must match the selected CSF "
            f"polygon uniquely; candidates={matches}. Check YAML and checkpoint."
        )
    return matches[0]


def sample_polygon_surface(
    csf_field,
    compiled_field,
    fem,
    *,
    x: float,
    polygon,
    nu: int,
    nv: int,
    margin: float,
    jacobian: bool = False,
    fem_interface: str = "first",
):
    if nu < 2 or nv < 2:
        raise ValueError("--nu and --nv must both be >= 2")
    if not (0.0 <= margin < 1.0):
        raise ValueError("--margin must satisfy 0 <= margin < 1")

    a = np.linspace(-1.0 + margin, 1.0 - margin, int(nu))
    b = np.linspace(-1.0 + margin, 1.0 - margin, int(nv))
    A, B = np.meshgrid(a, b, indexing="xy")

    vertices = polygon_vertices_yz(polygon)
    N = quad_shape(A, B)
    Y = np.sum(N * vertices[:, 0], axis=-1)
    Z = np.sum(N * vertices[:, 1], axis=-1)

    cu = np.zeros((nv, nu, 3), dtype=float)
    fe = np.zeros((nv, nu, 3), dtype=float)
    du = np.zeros((nv, nu, 3), dtype=float)
    if jacobian:
        domain_index = checkpoint_domain_for_polygon(compiled_field, polygon, x)
        J_cuf = np.empty((nv, nu, 3, 3), dtype=float)
        J_fem = np.empty_like(J_cuf)
        fem_element_id = np.empty((nv, nu), dtype=int)
        fem_ambiguous = np.zeros((nv, nu), dtype=bool)

    for j in range(nv):
        for i in range(nu):
            point = np.array([x, Y[j, i], Z[j, i]], dtype=float)
            cu[j, i, :] = np.asarray(compiled_field(*point), dtype=float)
            if jacobian:
                displacement, dufem, element_id, ambiguous = fem.displacement_and_full_gradient(
                    point, interface_policy=fem_interface)
                fe[j, i, :] = displacement
                J_fem[j, i, :, :] = dufem
                fem_element_id[j, i] = element_id
                fem_ambiguous[j, i] = ambiguous
                J_cuf[j, i, :, :] = compiled_field.displacement_gradient(
                    *point, domain_index=domain_index)
            else:
                fe[j, i, :] = fem.displacement(point)
            du[j, i, :] = cu[j, i, :] - fe[j, i, :]

    result = {
        "A": A,
        "B": B,
        "Y": Y,
        "Z": Z,
        "u_cuf": cu,
        "u_fem": fe,
        "du": du,
        "vertices": vertices,
    }
    if jacobian:
        result.update(J_cuf=J_cuf, J_fem=J_fem,
                      J_delta=J_cuf-J_fem,
                      fem_element_id=fem_element_id,
                      fem_ambiguous=fem_ambiguous)
        print(f"FEM H8 gradient one-sided samples at shared faces: "
              f"{int(np.count_nonzero(fem_ambiguous))} / {nu*nv} "
              f"(policy={fem_interface}, no averaging)")
    return result



def plot_surface(Y, Z, V, *, component: str, title: str, zlabel: str, output_path: Path,
                 height_scale: float = 1.0, field: str = "difference",
                 value_mode: str = "signed"):
    """Backward-compatible scalar export using the universal renderer."""
    obj = make_scalar_surface(
        Y, Z, V, component=component, field=field,
        value_mode=value_mode, title=title, axis_value_label=zlabel,
    )
    return save_surface_png(obj, output_path, thickness_scale=height_scale)


def plot_vector_surface(Y, Z, U, *, station_x: float, title: str, output_path: Path,
                        x_scale: float = 1.0, y_scale: float = 1.0, z_scale: float = 1.0,
                        field: str = "cuf"):
    """Backward-compatible full-vector export using the universal renderer."""
    if field not in {"cuf", "fem3d"}:
        raise ValueError("The full-vector surface is available for CUF or FEM3D")
    obj = make_vector_surface(Y, Z, U, station_x=station_x, title=title)
    return save_surface_png(
        obj, output_path,
        y_scale=y_scale, z_scale=z_scale, thickness_scale=x_scale,
    )

def component_iter(choice: str, field: str = "difference",
                   quantity: str = "displacement") -> Iterable[str]:
    """Components available for a selected field, without placeholders."""
    options = available_components(field, quantity)
    if choice == "all":
        return options
    if choice not in options:
        raise ValueError(f"Component {choice!r} is not available for {field!r}/{quantity!r}")
    return (choice,)



def interactive_surface(sampled, *, polygon_label: str, station_fraction: float,
                        station_x: float, initial_component: str, height_scale: float,
                        output_dir: Path, initial_field: str = "difference",
                        initial_value_mode: str = "signed", show: bool = True,
                        quantity: str = "displacement"):
    """Explore mathematical surfaces via one field-independent display engine.

    Processing order for EVERY mode:
        source arrays -> physical SurfaceObject -> DisplayFrame -> Matplotlib.
    The last two steps never mutate source arrays; the click inspector always
    reports the original physical field, never the normalized view coordinates.
    """
    backend = str(plt.get_backend()).lower()
    non_gui = (
        backend in {"agg", "pdf", "svg", "ps", "pgf", "cairo", "template"}
        or "inline" in backend
    )
    if show and non_gui:
        raise RuntimeError(
            "The current Matplotlib backend does not support interactive windows "
            f"({plt.get_backend()}). Run from a graphical session with TkAgg/QtAgg "
            "(for example: MPLBACKEND=TkAgg python3 script.py ...), or "
            "use --no-show to generate PNG and NPZ files only."
        )

    from dataclasses import replace
    from mpl_toolkits.mplot3d import proj3d

    fig = plt.figure(figsize=(11.9, 8.0))
    ax = fig.add_axes([0.025, 0.18, 0.68, 0.75], projection="3d")
    cax = fig.add_axes([0.725, 0.26, 0.022, 0.53])
    field_ax = fig.add_axes([0.818, 0.825, 0.165, 0.125])
    rax = fig.add_axes([0.818, 0.55, 0.165, 0.25])
    value_mode_ax = fig.add_axes([0.818, 0.42, 0.165, 0.10])
    y_scale_ax = fig.add_axes([0.22, 0.124, 0.46, 0.017])
    z_scale_ax = fig.add_axes([0.22, 0.081, 0.46, 0.017])
    height_ax = fig.add_axes([0.22, 0.038, 0.46, 0.017])
    reset_ax = fig.add_axes([0.822, 0.33, 0.15, 0.052])
    save_ax = fig.add_axes([0.822, 0.255, 0.15, 0.052])
    info = fig.text(
        0.038, 0.008, "Drag: rotate | Wheel: zoom | Click: inspect physical values",
        fontsize=9, va="bottom", ha="left",
    )

    raw_fields = {
        name: np.asarray(sampled[array_key], dtype=float)
        for name, array_key in FIELD_ARRAY_KEYS.items()
    }
    Y = np.asarray(sampled["Y"], dtype=float)
    Z = np.asarray(sampled["Z"], dtype=float)
    if Y.ndim != 2 or Z.shape != Y.shape or not (np.isfinite(Y).all() and np.isfinite(Z).all()):
        raise ValueError("Expected finite Y and Z 2D grids of equal shape")
    for field, vector in raw_fields.items():
        if vector.shape != Y.shape + (3,) or not np.isfinite(vector).all():
            raise ValueError(f"Invalid sampled displacement vector {field}")
    if not np.isfinite(height_scale) or height_scale <= 0.0:
        raise ValueError("height_scale must be finite and strictly positive")
    if initial_field not in FIELD_LABELS:
        raise ValueError(f"Unsupported initial field: {initial_field!r}")
    if initial_value_mode not in VALUE_MODES:
        raise ValueError(f"Unsupported value mode: {initial_value_mode!r}")
    if quantity not in {"displacement", "jacobian"}:
        raise ValueError(f"Unsupported quantity: {quantity!r}")
    if quantity == "jacobian":
        if initial_value_mode != "signed":
            raise ValueError("Jacobian surfaces preserve the sign; use --value-mode signed")
        for key in JACOBIAN_ARRAY_KEYS.values():
            if key not in sampled or np.asarray(sampled[key]).shape != Y.shape + (3, 3):
                raise ValueError(f"Missing or invalid sampled Jacobian {key}")

    state = {
        "field": initial_field,
        "component": (initial_component if initial_component in available_components(initial_field, quantity)
                      else ("uz_z" if quantity == "jacobian" else "ux")),
        "value_mode": initial_value_mode,
        "scale": float(height_scale),
        "y_scale": 1.0,
        "z_scale": 1.0,
        "surface": None,
        "reference_plane": None,
        "colorbar": None,
        "geometry": None,
        "drawn": None,
    }

    field_ax.set_title("Field", fontsize=10, loc="left", pad=9)
    field_radio = RadioButtons(
        field_ax, tuple(FIELD_LABELS.values()),
        active=tuple(FIELD_LABELS).index(state["field"]),
    )
    label_to_field = {label: key for key, label in FIELD_LABELS.items()}

    rax.set_title("Component", fontsize=10, loc="left", pad=9)
    radio = RadioButtons(
        rax, available_labels(state["field"], quantity),
        active=available_components(state["field"], quantity).index(state["component"]),
    )
    value_mode_ax.set_title("Value", fontsize=10, loc="left", pad=9)
    value_mode_radio = RadioButtons(
        value_mode_ax, ("Signed",) if quantity == "jacobian" else tuple(VALUE_MODE_LABELS.values()),
        active=0 if quantity == "jacobian" else VALUE_MODES.index(state["value_mode"]),
    )
    label_to_value_mode = {label: key for key, label in VALUE_MODE_LABELS.items()}

    # The three sliders control ONLY the final drawing box, *after* automatic
    # fitting of the complete physical bounding box. No slider changes u.
    y_scale_slider = Slider(y_scale_ax, "log10 Y box scale", -2.0, 2.0,
                            valinit=0.0, valfmt="%.2f")
    z_scale_slider = Slider(z_scale_ax, "log10 Z box scale", -2.0, 2.0,
                            valinit=0.0, valfmt="%.2f")
    y_scale_slider.valtext.set_text("x 1")
    z_scale_slider.valtext.set_text("x 1")
    logscale0 = math.log10(height_scale)
    logscale_min = min(-2.0, float(math.floor(logscale0) - 1.0))
    logscale_max = max(2.0, float(math.ceil(logscale0) + 1.0))
    scale_slider = Slider(height_ax, "log10 thickness box scale", logscale_min,
                          logscale_max, valinit=logscale0, valfmt="%.2f")
    scale_slider.valtext.set_text(f"x {height_scale:.3g}")
    reset_button = Button(reset_ax, "Reset view")
    save_button = Button(save_ax, "Save view")

    def clear_info_default():
        label = ("full vector field u(x,y,z)" if is_vector_geometry_component(
            state["field"], state["component"])
            else f"{state['component']} ({state['value_mode']})")
        info.set_text(
            f"Current view | {FIELD_LABELS[state['field']]} | {polygon_label} | "
            f"x/L={station_fraction:.6g} | {label} | bounding box auto-fit"
        )

    def render():
        if state["surface"] is not None:
            state["surface"].remove()
        if state["reference_plane"] is not None:
            state["reference_plane"].remove()

        # Field interpretation stops HERE. The generic renderer receives only
        # a parametrized physical surface, its observed color values and labels.
        obj = make_selected_surface(
            sampled, field=state["field"], component=state["component"],
            value_mode=state["value_mode"], station_x=float(station_x),
            polygon_label=polygon_label, station_fraction=station_fraction,
        )
        full_vector = is_vector_geometry_component(state["field"], state["component"])
        scale_slider.label.set_text(
            "log10 X box scale" if full_vector else "log10 height box scale"
        )
        if full_vector:
            description = "u(x,y,z): deformed section"
        elif state["component"] == "umag":
            description = ("Vector-difference magnitude" if state["field"] == "difference"
                           else "Total displacement magnitude")
        elif state["component"] == "dtotal":
            description = "Difference of total magnitudes"
        elif quantity == "jacobian":
            description = (f"signed d(u_{state['component'][1]})/"
                           f"d{state['component'][-1]} (no norm / fitting)")
        else:
            description = f"{state['component']} ({state['value_mode']})"
        short_title = (
            f"{FIELD_LABELS[state['field']]} | {polygon_label} | x/L={station_fraction:.4g}\n"
            f"{description} | auto bbox | thickness x {state['scale']:.3g} "
            f"| Y x {state['y_scale']:.3g} | Z x {state['z_scale']:.3g}"
        )
        if (obj.flat_tolerance > 0 and
                np.ptp(obj.color_values) <= obj.flat_tolerance):
            short_title += " | flat to floating-point precision"
        presented = replace(obj, title=short_title)
        drawn = draw_surface(
            ax, presented, y_scale=state["y_scale"], z_scale=state["z_scale"],
            thickness_scale=state["scale"],
        )
        state["surface"] = drawn.artist
        state["reference_plane"] = drawn.reference_artist
        state["geometry"] = obj
        state["drawn"] = drawn

        if state["colorbar"] is None:
            state["colorbar"] = fig.colorbar(drawn.mappable, cax=cax)
        else:
            state["colorbar"].update_normal(drawn.mappable)
        state["colorbar"].set_label(obj.colorbar_label)
        clear_info_default()
        fig.canvas.draw_idle()

    def on_radio(label):
        state["component"] = dict(zip(
            available_labels(state["field"], quantity),
            available_components(state["field"], quantity)
        ))[label]
        render()

    def on_value_mode_radio(label):
        if quantity == "jacobian":
            return  # Jacobian is signed; never offer absolute value or a norm.
        state["value_mode"] = label_to_value_mode[label]
        render()

    def on_field_radio(label):
        nonlocal radio
        state["field"] = label_to_field[label]
        available = available_components(state["field"], quantity)
        if state["component"] not in available:
            state["component"] = "uz_z" if quantity == "jacobian" else "umag"
        radio.disconnect_events()
        rax.clear()
        rax.set_title("Component", fontsize=10, loc="left", pad=9)
        radio = RadioButtons(
            rax, available_labels(state["field"], quantity),
            active=available.index(state["component"]),
        )
        radio.on_clicked(on_radio)
        refresh_widget_references()
        render()

    def on_scale(log_value):
        state["scale"] = 10.0 ** float(log_value)
        render()
        scale_slider.valtext.set_text(f"x {state['scale']:.3g}")
        fig.canvas.draw_idle()

    def on_y_scale(log_value):
        state["y_scale"] = 10.0 ** float(log_value)
        render()
        y_scale_slider.valtext.set_text(f"x {state['y_scale']:.3g}")
        fig.canvas.draw_idle()

    def on_z_scale(log_value):
        state["z_scale"] = 10.0 ** float(log_value)
        render()
        z_scale_slider.valtext.set_text(f"x {state['z_scale']:.3g}")
        fig.canvas.draw_idle()

    def on_reset(_event):
        ax.view_init(elev=30, azim=-60)
        fig.canvas.draw_idle()

    def save_view(_event):
        suffix = ("_abs" if state["component"] not in {"umag", "uvec"}
                  and state["value_mode"] == "absolute" else "")
        selected_prefix = ("jacobian_" + state["field"] if quantity == "jacobian"
                           else FIELD_OUTPUT_PREFIXES[state["field"]])
        out = Path(output_dir) / (
            f"{selected_prefix}_{polygon_label}_{state['component']}"
            f"{suffix}_x{station_fraction:g}_view.png"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=220, bbox_inches="tight")
        info.set_text(f"View saved: {out}")
        print(f"[ok] {out}")
        fig.canvas.draw_idle()

    def on_click(event):
        if event.inaxes != ax or event.button != 1:
            return
        drawn = state["drawn"]
        if drawn is None:
            return
        # The nearest point is found in *display* coordinates; all reported
        # values are from the original unmodified physical sample arrays.
        coords = drawn.display_coordinates
        xp, yp, _ = proj3d.proj_transform(
            *(c.ravel() for c in coords), ax.get_proj(),
        )
        pixels = ax.transData.transform(np.column_stack((xp, yp)))
        d2 = (pixels[:, 0] - event.x) ** 2 + (pixels[:, 1] - event.y) ** 2
        index = int(np.argmin(d2))
        if d2[index] > 30.0 ** 2:
            return
        ij = np.unravel_index(index, Y.shape)
        vector = raw_fields[state["field"]][ij]
        base = f"sample | y={Y[ij]:.6g}, z={Z[ij]:.6g} | "
        components = (f"{FIELD_LABELS[state['field']]}: ux={vector[0]:+.6g}, "
                      f"uy={vector[1]:+.6g}, uz={vector[2]:+.6g}")
        if is_vector_geometry_component(state["field"], state["component"]):
            displacement_magnitude = float(np.linalg.norm(vector))
            info.set_text(
                base + components +
                f" | deformed X-x0={vector[0]:+.6g}, Y={Y[ij]+vector[1]:.6g}, "
                f"Z={Z[ij]+vector[2]:.6g} | ||u||={displacement_magnitude:.6g}"
            )
        else:
            value = field_values(
                sampled, state["field"], state["component"], state["value_mode"]
            )
            info.set_text(base + components + f" | selected={float(value[ij]):+.6g}")
        fig.canvas.draw_idle()

    def on_key(event):
        available = available_components(state["field"], quantity)
        keys = {str(i + 1): item for i, item in enumerate(available)}
        if event.key in keys:
            radio.set_active(available.index(keys[event.key]))
        elif event.key == "a" and quantity != "jacobian":
            value_mode_radio.set_active(1 if state["value_mode"] == "signed" else 0)
        elif event.key == "r":
            on_reset(event)
        elif event.key == "s":
            save_view(event)

    radio.on_clicked(on_radio)
    field_radio.on_clicked(on_field_radio)
    value_mode_radio.on_clicked(on_value_mode_radio)
    scale_slider.on_changed(on_scale)
    y_scale_slider.on_changed(on_y_scale)
    z_scale_slider.on_changed(on_z_scale)
    reset_button.on_clicked(on_reset)
    save_button.on_clicked(save_view)
    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_key)

    def refresh_widget_references():
        # Preserve the v11 control positions for existing user scripts/tests.
        fig._csf_controls = (
            radio, scale_slider, reset_button, save_button, state, info,
            y_scale_slider, z_scale_slider, field_radio, value_mode_radio,
        )

    refresh_widget_references()
    render()
    if show:
        print(
            "[gui] Drag: rotate; wheel: zoom; click: inspect raw samples. "
            "The 3D bounding box is auto-fitted before applying slider ratios. "
            + ("1-6: signed Jacobian components; r: reset; s: save."
             if quantity == "jacobian" else
             "1-5: components; a: signed/absolute; r: reset; s: save.")
        )
        plt.show(block=True)
    return fig

def build_parser():
    p = argparse.ArgumentParser(
        description=(
            "Plot CUF, FEM3D or their difference as native 3D displacement "
            "surfaces or the nine signed full-gradient derivatives per field "
            "(a 3x3 Jacobian), on one CSF polygon at one longitudinal station."
        )
    )
    p.add_argument("--csf-yaml", type=Path, required=True, help="Original CSF YAML")
    p.add_argument("--quantity", choices=("displacement", "jacobian"),
                   default="displacement",
                   help="Preserve old displacement views or show 3x3 signed full displacement Jacobian")
    p.add_argument("--checkpoint", type=Path, required=True, help="Compiled CUF .cuf.npz checkpoint")
    p.add_argument("--fem3d", type=Path, required=True, help="Native FEM3D H8 displacement NPZ")
    p.add_argument("--polygon-index", type=int, default=None,
                   help="Zero-based polygon index matching CSF section.polygons (no index shift)")
    p.add_argument("--polygon-name", type=str, default=None, help="CSF polygon name")
    p.add_argument("--x", type=float, default=None, help="Physical longitudinal station")
    p.add_argument("--x-over-L", type=float, default=None, help="Normalized station in [0,1]")
    p.add_argument("--nu", type=int, default=41, help="Natural-grid samples along a (default: 41)")
    p.add_argument("--nv", type=int, default=41, help="Natural-grid samples along b (default: 41)")
    p.add_argument(
        "--margin", type=float, default=1e-4,
        help=(
            "Inset in natural coordinates to avoid exact polygon boundaries; "
            "0 samples the full closed quadrilateral, positive values stay inside."
        ),
    )
    p.add_argument(
        "--field", choices=tuple(FIELD_LABELS), default="difference",
        help="Initial GUI field and source of automatically saved PNGs (default: difference)",
    )
    p.add_argument(
        "--component", choices=("ux", "uy", "uz", "dtotal", "umag", "uvec",
                                *JACOBIAN_COMPONENTS, "all"), default="all",
        help=("ux/uy/uz; dtotal = signed CUF - FEM3D difference of total magnitudes; "
              "umag = total vector norm; uvec = full displacement field u(x,y,z) for FEM3D/CUF; "
              "all = all available (default)"),
    )
    p.add_argument(
        "--value-mode", choices=VALUE_MODES, default="signed",
        help="Signed or absolute value of scalar components; total magnitude is nonnegative (default: signed)",
    )
    p.add_argument(
        "--height-scale", type=float, default=1.0,
        help="Display-only thickness ratio AFTER auto-fitting the 3D bounding box (default: 1)",
    )
    p.add_argument("--output-dir", type=Path, default=Path("displacement_difference_surface"))
    p.add_argument("--fem-interface", choices=("first", "error"), default="first",
                   help="Signed Jacobian at H8 interfaces: select smallest native element ID "
                        "one-sided (default), or fail; NEVER average")
    p.add_argument("--export-all-fields", action="store_true",
                   help="When --quantity jacobian, export all 27 signed views as PNG")
    p.add_argument(
        "--no-show", action="store_true",
        help="Save PNG and NPZ without opening the native Matplotlib interactive 3D window",
    )
    return p


def main():
    args = build_parser().parse_args()
    if not math.isfinite(args.height_scale) or args.height_scale <= 0.0:
        raise ValueError("--height-scale must be finite and positive")
    if args.quantity == "jacobian" and args.value_mode != "signed":
        raise ValueError("Jacobian is signed only; do not use --value-mode absolute")
    if args.export_all_fields and args.quantity != "jacobian":
        raise ValueError("--export-all-fields is only for --quantity jacobian")

    csf_field, x0, x1 = load_csf_field(args.csf_yaml)
    compiled_field = load_cuf_compiled_field(args.checkpoint)
    fem = FEM3DH8(args.fem3d)

    station, s = resolve_station(x0, x1, args.x, args.x_over_L)
    section = csf_field.section(float(station))
    polygon_index, polygon = pick_polygon(section, args.polygon_index, args.polygon_name)

    sampled = sample_polygon_surface(
        csf_field,
        compiled_field,
        fem,
        x=float(station),
        polygon=polygon,
        nu=int(args.nu),
        nv=int(args.nv),
        margin=float(args.margin),
        jacobian=args.quantity == "jacobian",
        fem_interface=args.fem_interface,
    )

    polygon_label = getattr(polygon, "name", None) or f"polygon_{polygon_index}"
    out_root = args.output_dir.expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    npz_prefix = "jacobian_surface" if args.quantity == "jacobian" else "du_surface"
    npz_path = out_root / f"{npz_prefix}_{polygon_label}_x{s:g}.npz"
    extra_npz = ({
        "J_cuf": sampled["J_cuf"],
        "J_fem": sampled["J_fem"],
        "J_delta": sampled["J_delta"],
        "fem_element_id": sampled["fem_element_id"],
        "fem_ambiguous": sampled["fem_ambiguous"],
        "jacobian_columns": np.array(["x", "y", "z"]),
        "jacobian_rows": np.array(["ux", "uy", "uz"]),
    } if args.quantity == "jacobian" else {})
    np.savez_compressed(
        npz_path,
        polygon_index=np.array(polygon_index, dtype=int),
        polygon_name=np.array(polygon_label),
        x=np.array(float(station)),
        x_over_L=np.array(float(s)),
        height_scale=np.array(float(args.height_scale)),
        A=sampled["A"],
        B=sampled["B"],
        Y=sampled["Y"],
        Z=sampled["Z"],
        u_cuf=sampled["u_cuf"],
        u_fem=sampled["u_fem"],
        du=sampled["du"],
        vertices=sampled["vertices"],
        **extra_npz,
    )
    print(f"[ok] {npz_path}")

    export_fields = (tuple(FIELD_LABELS) if args.export_all_fields else (args.field,))
    for selected_field in export_fields:
        export_component = "all" if args.export_all_fields else args.component
        for component in component_iter(export_component, selected_field, args.quantity):
            prefix = ("jacobian_" + selected_field if args.quantity == "jacobian"
                      else FIELD_OUTPUT_PREFIXES[selected_field])
            suffix = "_abs" if component not in {"umag", "uvec"} and args.value_mode == "absolute" else ""
            png_path = out_root / f"{prefix}_{polygon_label}_{component}{suffix}_x{s:g}.png"
            if is_vector_geometry_component(selected_field, component):
                title, _ = vector_surface_metadata(selected_field, polygon_label, s)
                plot_vector_surface(sampled["Y"], sampled["Z"], sampled[FIELD_ARRAY_KEYS[selected_field]],
                                    station_x=float(station), title=title, output_path=png_path,
                                    x_scale=float(args.height_scale), y_scale=1.0, z_scale=1.0,
                                    field=selected_field)
            else:
                values = field_values(sampled, selected_field, component, args.value_mode)
                title, zlabel = surface_metadata(
                    selected_field, component, polygon_label, s, args.value_mode)
                fem_ids = (sampled["fem_element_id"]
                           if args.quantity == "jacobian" and selected_field != "cuf" else None)
                obj = make_scalar_surface(
                    sampled["Y"], sampled["Z"], values, component=component,
                    field=selected_field, value_mode=args.value_mode,
                    title=title, axis_value_label=zlabel, fem_element_ids=fem_ids,
                    flat_tolerance=0.0)
                save_surface_png(obj, png_path, thickness_scale=float(args.height_scale))
            print(f"[ok] {png_path}")

    if not args.no_show:
        interactive_surface(
            sampled, polygon_label=polygon_label, station_fraction=s,
            station_x=float(station),
            initial_component=("uz_z" if args.quantity == "jacobian" else "ux")
                              if args.component == "all" else args.component,
            height_scale=float(args.height_scale), output_dir=out_root,
            initial_field=args.field, initial_value_mode=args.value_mode,
            quantity=args.quantity,
        )
if __name__ == "__main__":
    main()
