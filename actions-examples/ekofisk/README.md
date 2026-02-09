# Case 3: Ekofisk Jacket Platform — Foundation Piles
## Reconstructed CSF Benchmark for Degradation Modeling

![ekofisk_sections](https://github.com/user-attachments/assets/78078a19-9619-4d9c-a7c3-179e472a011b)



## Document Information
- **Platform**: Ekofisk Complex, Block 2/4, Norwegian North Sea
- **Initial installation era**: Early 1970s (Ekofisk development phase)
- **Operator history**: Phillips Petroleum (now ConocoPhillips)
- **Water depth (field-level, indicative)**: approximately 70–75 m (historical), locally affected by seabed subsidence
- **Document date**: February 2025
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

Constraint:
`0 < w(z) <= 1`

### 3.4 Sanity Values for Current Parameter Set

Using `beta=0.40`, `sigma=2.0`, `z0=5`:

- `w(5) = 0.60` (maximum degradation)
- `w(3) ≈ 0.757`
- `w(0) ≈ 0.982`
- `w(10) ≈ 0.982`
- `w(60) ≈ 1.000`

---

## 4) Section Formulas (Circular Hollow Section)

At station `z`:

- `A(z) = (pi/4) * (D_o^2 - D_i(z)^2)`
- `I(z) = (pi/64) * (D_o^4 - D_i(z)^4)`
- `W(z) = 2*I(z)/D_o`
- `J_p(z) = (pi/32) * (D_o^4 - D_i(z)^4) = 2*I(z)`

Weighted effective properties:

- `EA_eff(z) = w(z) * E * A(z)`
- `EI_eff(z) = w(z) * E * I(z)`
- `GJ_eff(z) = w(z) * G * J_p(z)`, with `G = E / (2*(1+nu))`

---

## 5) Material Set (Benchmark Steel)

| Parameter | Symbol | Value | Unit | Evidence class |
|---|---:|---:|---|---|
| Young’s modulus | `E` | 210 | GPa | [Inferred] |
| Poisson’s ratio | `nu` | 0.30 | — | [Inferred] |
| Density | `rho` | 7850 | kg/m³ | [Inferred] |
| Yield strength (reference grade-level) | `fy` | 345 | MPa | [Inferred] |

Material naming in historical public sources may vary; keep this as a benchmark material card unless primary mill/test records are available.

---

## 6) Numerical Snapshot (Illustrative)

Example station near peak degradation (`z=5 m`), with model-generated section properties and current `w(5)=0.60`:

- `A(5) = 1.96377841 m²`
- `Ix(5) = 3.16726828 m⁴`
- `Iy(5) = 3.16726840 m⁴`
- `J(5) = 6.33453668 m⁴`

If `E = 210 GPa`:
- `EIx_eff(5) = w(5)*E*Ix(5) ≈ 0.60 * 210 * 3.16726828 ≈ 399.08 GN·m²`
- `EIy_eff(5) = w(5)*E*Iy(5) ≈ 399.08 GN·m²`

Values rounded for reporting; use direct CSF pipeline outputs for final tables.

---

## 7) Selected-Station Benchmark Output
![ekofisk](https://github.com/user-attachments/assets/199edbee-2915-4e9d-b177-b855c877a92d)

Stations used: `z = [0, 3, 5, 7, 10, 50, 175]`

### z = 0.0
- `A = 3.23873931`
- `Ix = 5.22358134`
- `J = 10.44716288`

### z = 3.0
- `A = 2.11293062`
- `Ix = 3.40782753`
- `J = 6.81565519`

### z = 5.0
- `A = 1.96377841`
- `Ix = 3.16726828`
- `J = 6.33453668`

### z = 7.0
- `A = 2.11293062`
- `Ix = 3.40782753`
- `J = 6.81565519`

### z = 10.0
- `A = 3.23873931`
- `Ix = 5.22358134`
- `J = 10.44716288`

### z = 50.0
- `A = 3.26220907`
- `Ix = 5.26143441`
- `J = 10.52286902`

### z = 175.0
- `A = 3.26220907`
- `Ix = 5.26143441`
- `J = 10.52286902`

---

## 8) CSF Implementation Template (YAML)

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [2.000000, 0.000000]
            - [1.618034, 1.175571]
            - [0.618034, 1.902113]
            - [-0.618034, 1.902113]
            - [-1.618034, 1.175571]
            - [-2.000000, 0.000000]
            - [-1.618034, -1.175571]
            - [-0.618034, -1.902113]
            - [0.618034, -1.902113]
            - [1.618034, -1.175571]
        inner_void:
          weight: 0.0
          vertices:
            - [1.700000, 0.000000]
            - [1.375329, 0.999235]
            - [0.525329, 1.616796]
            - [-0.525329, 1.616796]
            - [-1.375329, 0.999235]
            - [-1.700000, 0.000000]
            - [-1.375329, -0.999235]
            - [-0.525329, -1.616796]
            - [0.525329, -1.616796]
            - [1.375329, -0.999235]

    S1:
      z: 175.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [2.000000, 0.000000]
            - [1.618034, 1.175571]
            - [0.618034, 1.902113]
            - [-0.618034, 1.902113]
            - [-1.618034, 1.175571]
            - [-2.000000, 0.000000]
            - [-1.618034, -1.175571]
            - [-0.618034, -1.902113]
            - [0.618034, -1.902113]
            - [1.618034, -1.175571]
        inner_void:
          weight: 0.0
          vertices:
            - [1.700000, 0.000000]
            - [1.375329, 0.999235]
            - [0.525329, 1.616796]
            - [-0.525329, 1.616796]
            - [-1.375329, 0.999235]
            - [-1.700000, 0.000000]
            - [-1.375329, -0.999235]
            - [-0.525329, -1.616796]
            - [0.525329, -1.616796]
            - [1.375329, -0.999235]

  weight_laws:
    - 'outer,outer: 1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))'
```

---

## 9) CSF_ACTIONS Example

```yaml
CSF_ACTIONS:
  stations:
    station_mid:
      - 42.5
    station_edge:
      - 0
      - 175
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
          title: "Steel degraded"

    - section_selected_analysis:
        stations: station_sparse
        output:
          - stdout
        properties: [A, Cx, Cy, Ix, Iy, J]

    - plot_section_2d:
        stations:
          - station_mid
        show_ids: false
        show_vertex_ids: false
        output:
          - out/ekofisk_sections.jpg

    - plot_properties:
        output:
          - stdout
          - out/ekofisk_props.jpg
        params:
          num_points: 70
        properties: [A, Ix, Iy, J]

    - weight_lab_zrelative:
        stations:
          - station_edge
        output:
          - stdout
          - out/ekofisk_weight_lab.txt
        weith_law:
          - "1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))"

    - plot_weight:
        output:
          - stdout
          - out/ekofisk_weight.jpg
        params:
          num_points: 200
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

## 11) Source Strategy (Defensibility)

Maintain a tracker with one row per parameter:

- `parameter_name`
- `value_used`
- `class` = `[Measured|Inferred|Assumed]`
- `source_id` (URL/report/page)
- `justification`

This avoids false precision and keeps updates straightforward when higher-quality primary data becomes available.
