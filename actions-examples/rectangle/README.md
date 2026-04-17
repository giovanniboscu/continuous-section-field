# CSF Rectangle Example - `actions-examples/rectangle`

[CSF Actions Template - complete reference with all available actions](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/actions_template.yaml)

A self-contained example demonstrating the full **CSF Actions** pipeline on a
linearly tapered solid rectangular section. Every available action is exercised
in a single run, producing plots, reports, and solver exports.

This example is intended as a **reference template** — both files (`geometry.yaml`
and `actions.yaml`) are heavily commented and designed to be read as documentation.

---

## What this example models

A linearly tapered solid rectangle along z:

- **Width**: constant 1.0 m
- **Height**: grows linearly from 1.0 m at the base (z = 0) to 2.0 m at the top (z = 5 m)
- **Material**: uniform (single polygon, weight = 1.0)
- **Weight law**: three alternatives provided, one active at a time (see `geometry.yaml`)

```
      1.0 m
  ┌─────────┐  z = 0.0 m
  │         │
  │         │  height = 1.0 m
  └─────────┘

      1.0 m
  ┌─────────┐  z = 5.0 m
  │         │
  │         │  height = 2.0 m
  │         │
  └─────────┘
```

---

## How to run

```bash
csf-actions geometry.yaml actions.yaml
```

All outputs are written to the `out/` directory.

---

## Files

| File | Description |
|------|-------------|
| `geometry.yaml` | CSF geometry definition — two boundary sections, one polygon each, three weight law options |
| `actions.yaml` | CSF actions pipeline — all available actions with parameters |
| `w_variation.txt` | Lookup table for weight law option 2 — symmetric degradation with minimum at extremes |

---

## Weight Law Options

Three weight law alternatives are provided in `geometry.yaml`. Uncomment one at a time:

| Option | Expression | Effect |
|--------|-----------|--------|
| 1 | `1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))` | Gaussian degradation centred at tip |
| 2 | `T_lookup("w_variation.txt")` | Symmetric tabular degradation — min 0.70 at extremes, max 1.0 at mid-span |
| 3 | `1.0` | Uniform weight — standard tapered section, no degradation |

---

## Actions and Outputs

| Action | Output | Description |
|--------|--------|-------------|
| `plot_volume_3d` | screen | 3D ruled-surface visualization of the interpolated solid |
| `plot_section_2d` | `out/sections2d.jpg` | 2D cross-section outlines at base and top |
| `section_selected_analysis` | `out/sel_properties.txt` | Full section analysis at z = 0, 2.5, 5 m — includes polygon geometry export compatible with [sectionproperties](https://github.com/robbievanleeuwen/section-properties) |
| `plot_properties` | `out/properties.png` | Continuous property variation A(z), Ix(z), Iy(z), Ip(z) with Gauss-Lobatto station markers |
| `plot_weight` | `out/rectangle_weights.jpg` | Per-polygon weight law w(z) along member axis |
| `export_yaml` | `out/rectangle_geometry.yaml` | CSF model re-exported to YAML |
| `section_area_by_weight` | `out/rectangle_weight.txt` | Area report by weight group — occupied and homogenized |
| `volume` | `out/rectangle.txt` | Volume report — occupied and homogenized, Gauss-Legendre integration |
| `weight_lab_zrelative` | screen | Weight law evaluation at mid-span (z = 2.5) |
| `write_opensees_geometry` | `out/rectangle_geometry.tcl` | OpenSees DATA file — 10 Gauss-Lobatto stations, parseable by `csf_template_pack_opensees.py` |
| `write_sap2000_geometry` | `out/rectangle_template_pack.txt` | General-purpose solver export — four fixed-width tables for SAP2000 / OpenSeesPy |

---

## Station Sets

Named station sets defined in `actions.yaml` and reused across actions:

| Name | z values [m] | Use |
|------|-------------|-----|
| `station_ends` | 0.0, 5.0 | Boundary sections |
| `station_mid` | 2.5 | Mid-span single point |
| `station_3pt` | 0.0, 2.5, 5.0 | Base, mid, top |
| `station_5pt` | 0.0, 1.0, 1.5, 2.5, 3.0, 3.5, 5.0 | Detail sampling |

---

## Key Observations

- **Continuous fields**: `plot_properties` shows smooth continuous curves A(z), Ix(z), Iy(z)
  — not piecewise constant segments. The Gauss-Lobatto station markers are non-uniformly
  spaced, denser at the endpoints.
- **Weight law effect**: switching from option 3 (uniform) to option 2 (lookup table)
  produces a non-monotonic A(z) curve — the section grows geometrically but the
  effective area peaks at mid-span where w = 1.0 and decreases toward the endpoints
  where w = 0.70.
- **Solver export**: both `write_opensees_geometry` and `write_sap2000_geometry` use
  Gauss-Lobatto stations — the correct integration points for `forceBeamColumn` elements.
- **Reproducibility**: the entire pipeline is defined in two YAML files, versionable
  with Git, and produces identical output on every run.

---

## Notes

- `plot_volume_3d` and `weight_lab_zrelative` write to stdout/screen only — no file output.
- `write_opensees_geometry` does not support stdout — file output only.
- The `out/` directory is created automatically if it does not exist.
- For full documentation of the solver export format see [`write_sap2000_template_pack.md`](../../docs/write_sap2000_template_pack.md).
- For full documentation of all section properties see [`sectionfullanalysis.md`](../../docs/sections/sectionfullanalysis.md).
