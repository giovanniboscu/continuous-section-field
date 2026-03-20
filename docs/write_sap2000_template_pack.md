# `write_sap2000_template_pack` - Reference Documentation

## Overview

`write_sap2000_template_pack` exports a **CSF (Continuous Section Field)** model to a
structured plain-text file that can be used as input data for beam solvers such as
**SAP2000** and **OpenSeesPy**, as well as for section verification and quality review.

Despite its name, the function produces a **solver-agnostic export pack** — the output
format is readable by any tool that can parse fixed-width text tables, including custom
Python scripts and the companion `csf_template_pack_opensees.py` runner.

The function also optionally generates a **plot of the geometric property variation**
along the member axis.

---

## Signature

```python
def write_sap2000_template_pack(
    field: Any,
    n_intervals: int = 20,
    template_filename: str = "export_template_pack.txt",
    *,
    mode: _Mode = "BOTH",
    section_prefix: str = "SEC",
    #joint_prefix: str = "J",
    #frame_prefix: str = "F",
    material_name: str = "S355",
    E_ref: Optional[float] = None,
    nu: Optional[float] = None,
    include_plot: bool = True,
    plot_filename: str = "section_variation.png",
    show_plot: bool = False,
    z_values: Optional[List[float]] = None,
    float_fmt: str = ".9g",
) -> str:
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `field` | `Any` | - | A `ContinuousSectionField` object with `.s0.z`, `.s1.z`, and `.section(z)`. |
| `n_intervals` | `int` | `20` | Number of Gauss-Lobatto intervals. Stations = `n_intervals + 1`. Ignored when `z_values` is provided. |
| `template_filename` | `str` | `"export_template_pack.txt"` | Output file path. |
| `mode` | `str` | `"BOTH"` | Retained for API compatibility; not used in the output. |
| `section_prefix` | `str` | `"SEC"` | Prefix for section name labels in TABLE 4 (e.g. `"SEC"` → `"SEC0001"`). |
| `material_name` | `str` | `"S355"` | Informational material label written to the file header. |
| `E_ref` | `float` or `None` | `None` | Reference Young's modulus. Required together with `nu` to populate the `G_ref` column. |
| `nu` | `float` or `None` | `None` | Poisson's ratio. Used to derive `G_ref = E_ref / (2*(1+nu))`. |
| `include_plot` | `bool` | `True` | If `True` and `matplotlib` is available, saves a plot of section property variation along z. |
| `plot_filename` | `str` | `"section_variation.png"` | Output path for the property variation plot. |
| `show_plot` | `bool` | `False` | If `True`, displays the plot interactively. |
| `z_values` | `List[float]` or `None` | `None` | Explicit station list. If provided, `n_intervals` is ignored. Must be strictly increasing and within field bounds. |
| `float_fmt` | `str` | `".9g"` | Python format spec applied to all numeric output fields. |

### Returns

`str` — the path of the file written.

### Raises

| Exception | Condition |
|-----------|-----------|
| `ValueError` | Invalid `z_values` (non-numeric, NaN, out of bounds, non-monotonic). |
| `KeyError` | `section_full_analysis()` does not return an expected key. |

---

## Station Modes

The function supports two station generation strategies with **different physical meaning**:

### Gauss-Lobatto stations (default)

```python
write_sap2000_template_pack(field, n_intervals=10, E_ref=2.1e11, nu=0.3, ...)
```

Stations are Gauss-Lobatto nodes over `[z_start, z_end]`. These are the correct
integration points for `forceBeamColumn` elements in OpenSeesPy. The companion
`csf_template_pack_opensees.py` verifies that the stations match Lobatto abscissae
before using member-level integration.

### User-defined stations

```python
write_sap2000_template_pack(field, z_values=[0, 2.5, 5.0, 7.5, 10.0], E_ref=2.1e11, nu=0.3, ...)
```

Stations are arbitrary evaluation points — useful for SAP2000 tables, verification
reports, or comparisons against reference data. These stations do **not** carry
Gauss-Lobatto weights and should not be used for OpenSeesPy member-level integration.

---

## G_ref Column

The `G_ref` column in TABLE 1 is populated **only when both `E_ref` and `nu` are
provided**:

```
G_ref = E_ref / (2 * (1 + nu))
```

If either is missing, the column is blank. This affects downstream use:

- **SAP2000**: the user must supply material constants manually.
- **OpenSeesPy** with `MATERIAL_INPUT_MODE='from_file'`: will raise an explicit error
  asking to re-export with `E_ref` and `nu`, or to switch to `MATERIAL_INPUT_MODE='override'`.

**Recommended call for full export:**

```python
write_sap2000_template_pack(
    field,
    template_filename="export_template_pack.txt",
    n_intervals=10,
    E_ref=2.1e11,
    nu=0.3,
)
```

---

## Property Variation Plot

When `include_plot=True` (default) and `matplotlib` is available, the function saves
a figure showing how the key section properties vary along the member axis z.

The plot contains two panels:

- **Upper panel**: Cross-sectional area A [m²] vs z
- **Lower panel**: Second moments of area I33 (Ix), I22 (Iy), and torsional constant
  J_tors [m⁴] vs z

Each station is marked with a point. The figure is saved to `plot_filename` and
optionally displayed interactively with `show_plot=True`.

Plot generation is **best-effort** — if it fails for any reason (missing matplotlib,
backend issues), file creation continues normally without interruption.

---

## Output File Structure

The output file is a plain-text fixed-width table file with a `#`-prefixed header
followed by four numbered tables. All numeric columns have a fixed width of 20
characters, making the file both human-readable and machine-parseable without a CSV
parser.

### Header

```
# CSF SECTION EXPORT
# z_start      : 0
# z_end        : 10
# length       : 10
# stations     : 11
# station_mode : lobatto
# stations_list: 0 0.329992848 1.07758263 ...
# material     : S355
# E_ref        : 2.1e+11
# nu           : 0.3
# G_ref        : 8.07692308e+10
# doc          : docs/sections/sectionfullanalysis.md
```

`stations_list` provides all z-coordinates on a single line — useful for a quick
overview without scrolling through the tables.

`E_ref`, `nu`, and `G_ref` are written only when provided. `doc` points to the
CSF section analysis reference documentation.

---

### TABLE 1 — SOLVER INPUT

Direct input for SAP2000 and OpenSeesPy beam elements.

| Column | Source | Notes |
|--------|--------|-------|
| `z` | station coordinate | |
| `A` | net cross-sectional area | weighted sum of polygon areas |
| `Ix` | second moment about centroidal X-axis | mapped to `Iz` in OpenSees convention |
| `Iy` | second moment about centroidal Y-axis | |
| `Ixy` | product of inertia | zero for symmetric sections |
| `Ip` | polar second moment = Ix + Iy | |
| `J_tors` | torsional constant | = J_sv_cell + J_sv_wall; see TABLE 3 for breakdown |
| `G_ref` | reference shear modulus | blank if E_ref / nu not provided |
| `Cx` | horizontal centroid offset | centroid offset in section plane |
| `Cy` | vertical centroid offset | non-zero when centroid axis is tilted |
| `method` | torsion selection method | `J_sv_cell`, `J_sv_wall`, `J_sv_cell+J_sv_wall`, or `J_tors skip` |

---

### TABLE 2 — SECTION QUALITY

Derived verification properties — not consumed directly by solvers.

| Column | Description | Notes |
|--------|-------------|-------|
| `z` | station coordinate | |
| `I1` | major principal second moment | from Mohr's circle on Ix, Iy, Ixy |
| `I2` | minor principal second moment | |
| `theta_deg` | principal axis rotation angle [deg] | 0 for symmetric sections; deducible from Ix, Iy, Ixy |
| `rx` | radius of gyration about X | = sqrt(Ix/A) |
| `ry` | radius of gyration about Y | = sqrt(Iy/A) |
| `Wx` | elastic section modulus about X | = Ix / c_y,max |
| `Wy` | elastic section modulus about Y | = Iy / c_x,max |
| `Q_na` | first moment of area at neutral axis | used for shear stress τ = VQ/(Ib) |
| `K_torsion` | semi-empirical torsional stiffness | = A⁴/(40·Ip); low fidelity, for completeness only |

---

### TABLE 3 — TORSION QUALITY

Per-method torsion breakdown with reliability indicator.

| Column | Description | Notes |
|--------|-------------|-------|
| `z` | station coordinate | |
| `J_sv_cell` | Bredt-Batho closed-cell torsion constant | requires `@cell` polygon tag |
| `J_sv_cell_t` | wall thickness used by Bredt-Batho | present only for single-polygon `@cell` sections |
| `J_sv_wall` | open thin-wall torsion constant | requires `@wall` polygon tag |
| `J_sv_wall_t` | wall thickness used | present only for single-polygon `@wall` sections |
| `J_s_vroark` | Roark equivalent-rectangle proxy | heuristic internal to CSF; use only when fidelity >= 0.6 |
| `J_s_vroark_fidelity` | CSF polygon-based reliability index | >= 0.6 reliable \| 0.3–0.6 borderline \| < 0.3 do not use |
| `J_tors` | total torsional constant exported to solver | = J_sv_cell + J_sv_wall |
| `method` | torsion selection label | |

The `_t` columns appear only when at least one station carries the thickness value
(single-polygon `@cell` or `@wall` sections). They are omitted entirely for
multi-polygon sections where thickness is not uniquely defined.

`J_s_vroark_fidelity` is a **CSF-internal polygon-based reliability index** — it has
no counterpart in the literature and is not attributable to Roark. It quantifies how
well the equivalent-rectangle mapping represents the actual polygon geometry.

---

### TABLE 4 — STATION NAMES

Section name list for SAP2000 frame property assignment.

| Column | Description |
|--------|-------------|
| `id` | 1-based station index |
| `z` | station coordinate |
| `section_name` | label = `section_prefix` + zero-padded id |

---

## Complete Annotated Example

The following is a complete output file for a mixed thin-walled section
(rectangular closed cell + open wall flange) over a 10 m member,
exported at 11 Gauss-Lobatto stations with `E_ref=2.1e11`, `nu=0.3`.

```
# CSF SECTION EXPORT
# z_start      : 0
# z_end        : 10
# length       : 10
# stations     : 11
# station_mode : lobatto
# stations_list: 0 0.329992848 1.07758263 2.17382337 3.52120932 5 6.47879068 7.82617663 8.92241737 9.67000715 10
# material     : S355
# E_ref        : 2.1e+11
# nu           : 0.3
# G_ref        : 8.07692308e+10
# doc          : docs/sections/sectionfullanalysis.md

# TABLE 1 — SOLVER INPUT
# z  A  Ix  Iy  Ixy  Ip  J_tors  G_ref  Cx  Cy  method
  z                   A                   Ix                  Iy                  Ixy                 Ip                  J_tors              G_ref               Cx                  Cy                  method
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  0                   0.36                0.0432              0.0027              0                   0.0459              0.0048              8.07692308e+10      0                   0                   J_sv_wall
  0.329992848         0.355050107         0.0414424278        0.0026628758        0                   0.0441053036        0.00469061674       8.07692308e+10      0                   0.0082498212        J_sv_wall
  ...
  10                  0.21                0.008575            0.001575            0                   0.01015             0.00245625          8.07692308e+10      0                   0.25                J_sv_wall

# TABLE 2 — SECTION QUALITY
# z  I1  I2  theta_deg  rx  ry  Wx  Wy  Q_na  K_torsion
  z                   I1                  I2                  theta_deg           rx                  ry                  Wx                  Wy                  Q_na                K_torsion
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  0                   0.0432              0.0027              0                   0.346410162         0.0866025404        0.072               0.018               0.054               0.00914823529
  ...
  10                  0.008575            0.001575            0                   0.202072594         0.0866025404        0.0245              0.0105              0.018375            0.00479017241

# TABLE 3 — TORSION QUALITY
# J_s_vroark_fidelity: >=0.6 reliable | 0.3-0.6 borderline | <0.3 do not use
  z                   J_sv_cell           J_sv_wall           J_s_vroark          J_s_vroark_fidelity J_tors              method
  --------------------------------------------------------------------------------------------------------------------------------------------
  0                   0                   0.0048              0.00909955371       0.25                0.0048              J_sv_wall
  ...
  10                  0                   0.00245625          0.00460378207       0.428571429         0.00245625          J_sv_wall

# TABLE 4 — STATION NAMES
  id                  z                   section_name
  ------------------------------------------------------------
  1                   0                   SEC0001
  ...
  11                  10                  SEC0011
```

### Reading the example

- **Centroid tilt**: `Cy` increases from 0 to 0.25 m along z — the centroid axis is
  not aligned with the reference axis. This triggers segmented integration in
  `csf_template_pack_opensees.py`.
- **Torsion method**: all stations use `J_sv_wall` - the section has no `@cell` polygon,
  only open thin-walled components.
- **J_s_vroark_fidelity**: values between 0.25 and 0.43 - below 0.6, confirming that
  the Roark proxy is unreliable for this thin-walled geometry. `J_sv_wall` is the
  correct torsion source here.
- **theta_deg = 0**: the section is symmetric about X, so principal axes coincide with
  reference axes.

---

## Downstream Use

### OpenSeesPy

Use the companion script `csf_template_pack_opensees.py`:

```python
# Set TEMPLATE_FILE = "export_template_pack.txt" in the script
# Set MATERIAL_INPUT_MODE = "from_file"  (requires E_ref and nu in the file)
python csf_template_pack_opensees.py
```

The script reads TABLE 1, reconstructs the beam model, and runs a cantilever
static analysis. It automatically detects centroid tilt and switches between
member-level Gauss-Lobatto integration and segmented integration.

### SAP2000

Import the section properties from TABLE 1 into SAP2000 frame section definitions.
Each row corresponds to one station; the `section_name` from TABLE 4 can be used
as the SAP2000 section label. Units must be consistent with the CSF export.

---

## Notes and Limitations

- The file is **not** a direct SAP2000 import file — it requires manual or scripted
  mapping to the specific SAP2000 table format for the installed version.
- `G_ref` is a scalar reference shear modulus derived from the user-supplied `E_ref`
and `nu`. It is intended as a solver input only — it does not reflect any material
variation along z that may be encoded in the CSF weight laws.
- The `mode` parameter (`BOTH`, `CENTROIDAL_LINE`, `REFERENCE_LINE`) is retained for
  API compatibility but does not affect the output in the current implementation.
- For torsion: always check `J_s_vroark_fidelity` before using `J_s_vroark`. For
  thin-walled sections use `J_sv_cell` or `J_sv_wall` instead.

---

## See Also

- `csf_template_pack_opensees.py` - companion OpenSeesPy runner
- `write_opensees_geometry()` - alternative export in TCL-compatible format
- `docs/sections/sectionfullanalysis.md` — full reference for all section properties
- `docs/sections/DeSaintVenantTorsionalConstant.md` — torsion method details
