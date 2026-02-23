# Case 3: Ekofisk Jacket Platform - Foundation Piles
## Reconstructed CSF Benchmark for Degradation Modeling

if you need to recreate the geometry

```
python3 csf_polygon_hole_builder_v2.py
```
start CSF 
```
python3 -m csf.CSFActions ekofisk_geometry_m.yaml ekofisk_action.yaml
```
![ekofisk_sections](https://github.com/user-attachments/assets/78078a19-9619-4d9c-a7c3-179e472a011b)



## Document Information
- **Platform**: Ekofisk Complex, Block 2/4, Norwegian North Sea
- **Initial installation era**: Early 1970s (Ekofisk development phase)
- **Operator history**: Phillips Petroleum (now ConocoPhillips)
- **Water depth (field-level, indicative)**: approximately 70–75 m (historical), locally affected by seabed subsidence
- **Status**: Reconstructed benchmark from public-domain context plus engineering assumptions (not an as-built certified dossier)

---

## Scope and Reliability Policy

This document is intended for **numerical benchmarking in CSF**, not for certification or forensic reconstruction.

Each input is tagged with one evidence class:

- **[Measured]**: directly traceable to a public source with explicit value
- **[Inferred]**: derived from published context using transparent engineering logic
- **[Assumed]**: modeling assumption introduced to complete a usable benchmark dataset

Where pile-level details are not publicly available, values are intentionally marked **[Assumed]**.

---

## 1) Platform Context (Field-Level)

Ekofisk is one of the earliest major North Sea developments. Public sources describe long-term seabed subsidence and major life-extension interventions. This benchmark uses that context to define a transparent degradation model for tubular foundation members.

| Parameter | Value | Unit | Evidence class | Notes |
|---|---:|---|---|---|
| Field water depth (order of magnitude) | 70–75 | m | [Measured] | Field-level public info |
| Seabed subsidence (historical, order of magnitude) | up to ~8 | m | [Measured] | Used as context driver |
| Foundation typology | Steel driven/grouted piles | — | [Inferred] | Typical jacket practice for period |
| Long-term operation / life extension | Yes | — | [Measured] | Publicly documented at area level |

---

## 2) Foundation Pile Geometry for CSF Benchmark

### 2.1 Adopted Geometry Set (Benchmark)

The following values are benchmark assumptions selected to produce a realistic and numerically stable test case.

| Parameter | Symbol | Value | Unit | Evidence class | Notes |
|---|---:|---:|---|---|---|
| Number of modeled piles | `N_p` | 8 | — | [Assumed] | 4 clusters × 2 piles (modeling convention) |
| Outer diameter | `D_o` | 2.400 | m | [Assumed] | Large-diameter offshore tubular pile |
| Wall thickness (minimum) | `t_min` | 0.050 | m | [Assumed] | Upper region |
| Wall thickness (maximum) | `t_max` | 0.075 | m | [Assumed] | Splash/corrosion-critical region |
| Free length above mudline | `L_free` | 75 | m | [Assumed] | Benchmark value |
| Embedded length below mudline | `L_emb` | 100 | m | [Assumed] | Benchmark value |
| Total modeled length | `L_tot` | 175 | m | [Assumed] | `L_free + L_emb` |

### 2.2 Thickness and Inner Diameter Definitions

Inner diameter:
`D_i(z) = D_o - 2*t(z)`

Local axis domain:
`z in [0, L_tot]`

Linear thickness profile:
`t(z) = t_min + (z / L_tot) * (t_max - t_min)`

Implementation may use a mapped global elevation convention; reproducibility requires explicit coordinate declaration.

---

## 3) Degradation Weight Law (CSF)

### 3.1 Physical Interpretation

A splash-zone-centered reduction is modeled with a smooth Gaussian envelope.

### 3.2 Parameters (Current Benchmark)

| Parameter | Symbol | Value | Unit | Evidence class | Meaning |
|---|---:|---:|---|---|---|
| Maximum degradation amplitude | `beta` | 0.40 | — | [Assumed] | Up to 40% reduction at center |
| Spread | `sigma` | 2.0 | m | [Assumed] | Splash-zone width |
| Center elevation | `z0` | +5.0 | m (local/elevation mapping declared in model) | [Assumed] | Peak degradation location |

### 3.3 Weight Law

![ekofisk_weight](https://github.com/user-attachments/assets/94235b88-1a77-4f8d-9770-983129cf53ad)


`w(z) = 1 - beta * exp(-((z - z0)^2) / (2*sigma^2))`


`1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))`

---

### Geometry
 
---

## 8) CSF Implementation Template (YAML)

```yaml
# -----------------------------------------------------------------------------
# GEOMETRY INPUTS (auto-recorded by generator)
# -----------------------------------------------------------------------------
# SCRIPT                : csf_polygon_hole_builder_v2.py
# SINGLE_POLE           : False
# GEOMETRY_YAML_FILENAME: ekofisk_geometry_m.yaml
# OUTER_POLY_NAME       : poly
# VOID_POLY_NAME        : void
# W_DEFAULT             : 1.0
# z0                    : 0.0
# z1                    : 175.0
#
# S0:
#   W0           : 1.0
#   INNER_CENTER : (0.0, 0.0)
#   INNER_LX     : 2.3
#   INNER_LY     : 2.3
#   INNER_N      : 8
#   OUTER_CENTER : (0.0, 0.0)
#   OUTER_LX     : 2.4
#   OUTER_LY     : 2.4
#   OUTER_N      : 8
#
# S1:
#   W1           : 1.0
#   INNER_CENTER : (0.0, 0.0)
#   INNER_LX     : 2.25
#   INNER_LY     : 2.25
#   INNER_N      : 8
#   OUTER_CENTER : (0.0, 0.0)
#   OUTER_LX     : 2.4
#   OUTER_LY     : 2.4
#   OUTER_N      : 8
# -----------------------------------------------------------------------------
CSF:
  sections:
    S0:
      z: 0
      polygons:
        poly:
          weight: 1
          vertices:
            - [-1.2, 1.46957615898e-16]
            - [-0.848528137424, -0.848528137424]
            - [-2.20436423847e-16, -1.2]
            - [0.848528137424, -0.848528137424]
            - [1.2, -2.93915231795e-16]
            - [0.848528137424, 0.848528137424]
            - [3.67394039744e-16, 1.2]
            - [-0.848528137424, 0.848528137424]
        void:
          weight: 0
          vertices:
            - [-1.15, 1.40834381902e-16]
            - [-0.813172798365, -0.813172798365]
            - [-2.11251572853e-16, -1.15]
            - [0.813172798365, -0.813172798365]
            - [1.15, -2.81668763804e-16]
            - [0.813172798365, 0.813172798365]
            - [3.52085954755e-16, 1.15]
            - [-0.813172798365, 0.813172798365]
    S1:
      z: 175
      polygons:
        poly:
          weight: 1
          vertices:
            - [-1.2, 1.46957615898e-16]
            - [-0.848528137424, -0.848528137424]
            - [-2.20436423847e-16, -1.2]
            - [0.848528137424, -0.848528137424]
            - [1.2, -2.93915231795e-16]
            - [0.848528137424, 0.848528137424]
            - [3.67394039744e-16, 1.2]
            - [-0.848528137424, 0.848528137424]
        void:
          weight: 0
          vertices:
            - [-1.125, 1.37772764904e-16]
            - [-0.795495128835, -0.795495128835]
            - [-2.06659147356e-16, -1.125]
            - [0.795495128835, -0.795495128835]
            - [1.125, -2.75545529808e-16]
            - [0.795495128835, 0.795495128835]
            - [3.4443191226e-16, 1.125]
            - [-0.795495128835, 0.795495128835]
  weight_laws:
         - 'poly,poly: 1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))'
     
```

---

## 9) CSF_ACTIONS Example

```yaml
CSF_ACTIONS:
  stations:
    station_midle:
      - 42.5
    station_edge:
      - 0
      - 175
    station_10:
      - 10
    station_sparse:
      - 0
      - 3
      - 5
      - 7
      - 10
      - 50
      - 175

  actions:
    - plot_volume_3d:
        params:
          line_percent: 100.0
          title: "ekifisk"

    - section_selected_analysis:
        stations: station_edge
        output:
          - stdout
          - out/section_selected_analysi_sekifisk.txt
        properties: [A, Cx, Cy, Iy,Wx,Wy,J,J_sv,J_sv_cell,J_sv_wall,K_torsion,Q_na]

    - plot_section_2d:
        stations:
          - station_edge
        show_ids: True
        show_vertex_ids: True
        output:
          - [stdout,out/one_pol_ekofisk_sections.jpg]

    - plot_properties:
        output:
          - stdout
          - out/ekofisk.jpg
        params:
          num_points: 500
        properties: [A, Ix,J,J_sv,J_sv_cell,J_sv_wall]
    - plot_weight:
        output:
          - stdout
          - out/ekofisk_weight.jpg
        params:
          num_points: 500
```

---

## 10) Traceability and Use Constraints

### What this benchmark is
- A transparent, reproducible engineering benchmark for CSF degradation modeling.
- Suitable for sensitivity studies, code verification, and method comparison.

### What this benchmark is not
- A certified as-built pile schedule for Ekofisk.
- A substitute for operator-owned drawings, fabrication books, or inspection archives.

### Recommended sensitivity envelope
Run at least three scenarios:

- **Low**: `beta=0.20`, `sigma=1.5`
- **Baseline**: `beta=0.35` to `0.40`, `sigma=2.0`
- **High**: `beta=0.50`, `sigma=2.5`

Optionally vary:
- thickness profile,
- embedded length,
- law family (Gaussian vs band-limited sigmoid).

---
