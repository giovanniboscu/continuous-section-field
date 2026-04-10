# Pier50 - Urban Viaduct Bridge Pier

Parametric geometry model of a **50 m tall reinforced concrete bridge pier**
for an urban elevated highway in seismic zone 2 (Italy).

<img width="565" height="715" alt="Pier50 3D render" src="https://github.com/user-attachments/assets/6db23d13-abb5-47fc-96d6-3b431ea6f629" />

---

## Purpose

This example serves as a self-contained demonstration of three distinct
capabilities of the `csfpy` library:

1. **Stacked field composition** - Three independently defined `CSFField`
   objects (base zone, main shaft, pier head) are assembled into a single
   continuous structural member via `CSFStacked`. Once stacked, the composite
   object exposes a unified interface: section properties and 3D
   visualisation are all requested through `stack.*` calls without any
   knowledge of the internal segment boundaries.

2. **Programmatic geometry generation** - Each segment's YAML descriptor is
   produced by the `csf.utils.writegeometry_rio_v2` module, invoked from a
   platform-specific shell script (`.ps1` on Windows, `.sh` on Linux/macOS).
   This approach keeps the geometry parameters explicit, version-controllable,
   and independent of any GUI.

3. **Cross-library section property validation** - The section properties
   computed analytically by `csfpy` are compared against the FEM-based results
   of the `sectionproperties` library. For each of the 20 exported cross-
   sections, relative differences are tabulated and a global statistical report
   is produced, providing a quantitative validation benchmark.

---

## Project overview

| Parameter | Value |
|-----------|-------|
| Structure type | Single-column hollow rectangular pier |
| Total pier height | 50 m |
| Application | Urban elevated highway |
| Deck span | ~38 m (incremental launching) |
| Seismic zone | Zone 2 - NTC2018 §3.2 |
| Ductility class | DCM (medium ductility) - EC8-2 §4.1 |
| Concrete | C35/45 - fck = 35 MPa, Ecm = 34 GPa |
| Steel | B450C - fyk = 450 MPa, Es = 200 GPa |
| Cover | 75 mm (exposure class XC3/XD1 - urban splash zone) |

---

## Usage

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install csfpy sectionproperties
git clone https://github.com/giovanniboscu/continuous-section-field.git

cd continuous-section-field/actions-examples/UrbanViaduct

# Create the output directories
mkdir -p yaml out/sections result

cd geometry

# Generate the three YAML geometry files (one per segment)
bash geometry_pier_seg1.sh
bash geometry_pier_seg2.sh
bash geometry_pier_seg3.sh

cd ../analysis

# Compute section properties for all 20 stations.
# Writes result/UrbanViaduc_report.txt and out/sections/*.csv
python3 run_pier50.py

# Run sectionproperties on each exported CSV section.
# Redirecting stdout captures the full tabular output.
bash run_csf_sp_all.sh > ../result/sectionproperties_par.txt

# Compare CSF vs sectionproperties and write the statistical report.
# Output: result/comparison_report.txt
python3 compare_results.py
```

### Windows

```powershell
python3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install csfpy sectionproperties
git clone https://github.com/giovanniboscu/continuous-section-field.git

cd continuous-section-field\actions-examples\UrbanViaduct

# Create the output directories
mkdir yaml, out\sections, result

cd geometry

# Generate the three YAML geometry files (one per segment)
powershell -ExecutionPolicy Bypass -File geometry_pier_seg1.ps1
powershell -ExecutionPolicy Bypass -File geometry_pier_seg2.ps1
powershell -ExecutionPolicy Bypass -File geometry_pier_seg3.ps1

cd ..\analysis

# Compute section properties for all 20 stations.
# Writes result\UrbanViaduc_report.txt and out\sections\*.csv
python.exe run_pier50.py

# Run sectionproperties on each exported CSV section.
# Redirecting stdout captures the full tabular output.
powershell -ExecutionPolicy Bypass -File run_csf_sp_all.ps1 > ..\result\sectionproperties_par.txt

# Compare CSF vs sectionproperties and write the statistical report.
# Output: result\comparison_report.txt
python.exe compare_results.py
```

---

## Geometry - three segments

### Segment 1 - Base zone  (z = 0 → 8 m)

The base segment encompasses the **plastic hinge region** as defined by
EC8-2 §4.1.6. Its length corresponds to the pier critical length
`Lcr = max(D, H/6, 1.5 m)` ≈ 8.3 m (rounded down to 8 m for segment
boundary alignment).

The section is enlarged at the pile-cap interface to:
- resist the maximum seismic moment demand (first mode);
- satisfy the minimum confinement requirements of NTC2018 §7.4.4.1;
- achieve the required curvature ductility factor µφ ≥ 13 (DCM, ag/g = 0.25).

| Property | S0 (z = 0 m) | S1 (z = 8 m) |
|----------|-------------|-------------|
| Outer section | 6.40 × 3.60 m | 5.20 × 3.20 m |
| Wall thickness tg | 0.70 m | 0.60 m |
| Inner void | 5.00 × 2.20 m | 4.00 × 2.00 m |
| Corner radius R | 0.30 m | 0.30 m |
| Main bars (outer) | 48 Ø28 | 48 Ø28 |
| Main bars (inner) | 32 Ø22 | 32 Ø22 |

### Segment 2 - Main shaft  (z = 8 → 38 m)

The shaft tapers linearly to reduce self-weight and optimise stiffness
distribution along the pier height. The wall thickness condition
`tg ≥ max(150 mm, bw/15)` per EC8-2 §5.4.1 is satisfied throughout
(tg/bw = 0.60/5.20 = 0.115 at the top of Segment 1;
0.45/4.00 = 0.113 at the bottom of Segment 3 - both ≥ 1/15 = 0.067 ✓).

| Property | S0 (z = 8 m) | S1 (z = 38 m) |
|----------|-------------|--------------|
| Outer section | 5.20 × 3.20 m | 4.00 × 2.60 m |
| Wall thickness tg | 0.60 m | 0.45 m |
| Inner void | 4.00 × 2.00 m | 3.10 × 1.70 m |
| Corner radius R | 0.30 m | 0.30 m |
| Main bars (outer) | 40 Ø25 | 40 Ø25 |
| Main bars (inner) | 28 Ø20 | 28 Ø20 |

### Segment 3 - Pier head  (z = 38 → 50 m)

The pier head widens to accommodate:
- pot-type seismic bearings at ±1.80 m from the pier centreline;
- shear keys required by NTC2018 §7.4.3.2;
- cap-beam geometry for incremental launching construction.

The increased wall thickness (0.55 m) is required to resist the concentrated
bearing reaction and the local punching demands per EC2 §6.4.

| Property | S0 (z = 38 m) | S1 (z = 50 m) |
|----------|--------------|--------------|
| Outer section | 4.00 × 2.60 m | 5.60 × 3.00 m |
| Wall thickness tg | 0.45 m | 0.55 m |
| Inner void | 3.10 × 1.70 m | 4.50 × 1.90 m |
| Corner radius R | 0.30 m | 0.30 m |
| Main bars (outer) | 44 Ø25 | 44 Ø25 |
| Main bars (inner) | 32 Ø20 | 32 Ø20 |

---

## Junction connectivity

Continuity between adjacent segments is enforced by requiring that the
terminal section of each segment (S1) coincides exactly with the initial
section (S0) of the following one.

| Junction | z | dx | dy | R | tg |
|----------|---|----|----|---|----|
| S1-seg1 = S0-seg2 | 8 m | 5.20 m | 3.20 m | 0.30 m | 0.60 m |
| S1-seg2 = S0-seg3 | 38 m | 4.00 m | 2.60 m | 0.30 m | 0.45 m |

---

## Files

| File | Location | Description |
|------|----------|-------------|
| `geometry_pier_seg1.ps1` / `.sh` | `geometry/` | Generate `pier_seg1.yaml` |
| `geometry_pier_seg2.ps1` / `.sh` | `geometry/` | Generate `pier_seg2.yaml` |
| `geometry_pier_seg3.ps1` / `.sh` | `geometry/` | Generate `pier_seg3.yaml` |
| `run_pier50.py` | `analysis/` | Stack segments, compute properties, export CSVs |
| `run_csf_sp_all.ps1` / `.sh` | `analysis/` | Run `sectionproperties` on all exported CSVs |
| `compare_results.py` | `analysis/` | Cross-library comparison and statistical report |

---

## Design notes

- **Slenderness**: λ = H/D = 50/5.60 = 8.9 - classified as a **slender pier**
  (λ > 4 per EC8-2 §4.1.2), implying a first-mode dominated seismic response.
- **Natural period** (estimate): T₁ ≈ 2π√(m·H³/3EI) ≈ 1.9–2.3 s, placing the
  structure in the constant-velocity region of the NTC2018 design spectrum
  (zone 2, soil class B).
- **Plastic hinge length**: Lpl = 0.1H + 0.022·fyd·dbl = 8.3 m - Segment 1
  boundary set at 8.0 m (conservative rounding).
- **Corner radius**: R = 0.30 m is held constant along the full pier height,
  allowing the same formwork to be reused across all three segments.
