# CSF Actions — Geometry Export 

These two CSF actions export section/geometry data for external workflows (OpenSees and SAP2000), starting from the CSF model along `z`.

## 1) `write_opensees_geometry`

Exports a Tcl file ready for OpenSees.

- **Required output (file-only):**
  - `out/j_sv_geometry.tcl`
- **Required parameters:**
  - `n_points` (int): number of sampled sections along the axis
  - `E_ref` (float): reference Young’s modulus
  - `nu` (float): Poisson’s ratio

**Typical use:** quickly generate a CSF-consistent discretization for OpenSees.

---

## 2) `write_sap2000_geometry`

Exports a text template pack for SAP2000 using predefined stations.

- **Stations:**
  - `stations: stations_dense`
- **Output:**
  - `out/j_sv_sap2000_template_pack.txt`
- **Main parameters:**
  - `n_intervals` (int): subdivisions between stations
  - `material_name` (str): material label (e.g., `S355`)
  - `E_ref` (float): reference Young’s modulus
  - `nu` (float): Poisson’s ratio
  - `mode` (str): export mode (e.g., `BOTH`)
  - `include_plot` (bool): include section-variation plot
  - `plot_filename` (str): image path (e.g., `out/j_sv_section_variation.png`)

**Typical use:** prepare SAP2000 input plus a visual check of section variation.

---

## Practical note

Both actions preserve consistency with the CSF definition of section variation along `z`, avoiding manual geometry rebuilds in target software.
