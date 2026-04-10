# Pier50 - Urban Viaduct Bridge Pier

Parametric geometry model of a **50 m tall reinforced concrete bridge pier**
for an urban elevated highway in seismic zone 2 (Italy).

---
## Usage
### Create a virtual environment

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install csfpy sectionproperties
```

### Windows

```powershell
python3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install csfpy sectionproperties
```

```
cd  actions-examples\UrbanViaduct\geometry

# create the 3 segments geometry ymal files 
powershell -ExecutionPolicy Bypass -File  geometry_pier_seg1.ps1
powershell -ExecutionPolicy Bypass -File  geometry_pier_seg2.ps1
powershell -ExecutionPolicy Bypass -File  geometry_pier_seg3.ps1
 
cd ..\analysis
  

# the full structure report is created at \result\UrbanViaduc_report.txt
# section geometry are exported on out\sections\*csv 
# n_sez = 20 
python.exe run_pier50.py 

# perform sectionproperties for each sections
powershell -ExecutionPolicy Bypass -File   run_csf_sp_all.ps1  > ..\result\sectionproperties_par.txt

# section
powershell -ExecutionPolicy Bypass -File   run_csf_sp_all.ps1
# comparison between CSF and sectionproperties on  .\result/comparison_report.txt
python.exe .\compare_results.py

```



---

## Project overview

| Parameter | Value |
|-----------|-------|
| Structure type | Single-column hollow rectangular pier |
| Total pier height | 50 m |
| Application | Urban elevated highway (viadotto urbano) |
| Deck span | ~38 m (incremental launching) |
| Seismic zone | Zone 2 - NTC2018 §3.2 |
| Ductility class | DCM (medium ductility) - EC8-2 §4.1 |
| Concrete | C35/45 - fck = 35 MPa, Ecm = 34 GPa |
| Steel | B450C - fyk = 450 MPa, Es = 200 GPa |
| Cover | 75 mm (exposure class XC3/XD1 - urban splash zone) |

---

## Geometry - three segments

### Segment 1 - Base zone  (z = 0 → 8 m)

The base segment covers the **plastic hinge region** as defined by EC8-2 §4.1.6.
Its length equals the pier critical length `Lcr = max(D, H/6, 1.5 m)` ≈ 8.3 m
(adopted 8 m for segment boundary alignment).

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
distribution. Wall thickness `tg ≥ max(150 mm, bw/15)` per EC8-2 §5.4.1
is satisfied throughout (tg/bw = 0.60/5.20 = 0.115 at top of seg 1;
0.45/4.00 = 0.113 at bottom of seg 3 - both ≥ 1/15 = 0.067 ✓).

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
- pot-type seismic bearings at ±1.80 m from pier centreline;
- shear keys required by NTC2018 §7.4.3.2;
- cap-beam geometry for incremental launching construction.

The increased wall thickness (0.55 m) resists the concentrated bearing
reaction and the local punching demands per EC2 §6.4.

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

| Junction | z | dx | dy | R | tg |
|----------|---|----|----|---|----|
| S1-seg1 = S0-seg2 | 8 m | 5.20 m | 3.20 m | 0.30 m | 0.60 m |
| S1-seg2 = S0-seg3 | 38 m | 4.00 m | 2.60 m | 0.30 m | 0.45 m |

---

## Files

| File | Description |
|------|-------------|
| `geometry_pier_seg1.ps1` / `.sh` | Generate `pier_seg1.yaml` |
| `geometry_pier_seg2.ps1` / `.sh` | Generate `pier_seg2.yaml` |
| `geometry_pier_seg3.ps1` / `.sh` | Generate `pier_seg3.yaml` |
| `run_pier50.py` | Stack + 3D visualisation |

---


## Design notes

- **Slenderness**: λ = H/D = 50/5.60 = 8.9 - classified as a **slender pier**
  (λ > 4 per EC8-2 §4.1.2) → first-mode dominated seismic response.
- **Natural period** (estimate): T₁ ≈ 2π√(m·H³/3EI) ≈ 1.9–2.3 s → sits in
  the constant-velocity region of the NTC2018 spectrum (zone 2, soil B).
- **Plastic hinge**: length Lpl = 0.1H + 0.022fyd·dbl = 8.3 m - Segment 1
  boundary set at 8.0 m (conservative rounding).
- **Corner radius** R = 0.30 m constant along full height - enables the same
  formwork to be reused for all three segments (cost saving).
