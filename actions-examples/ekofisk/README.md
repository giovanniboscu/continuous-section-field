# Work in progress....

# Case 3: Ekofisk Jacket Platform — Foundation Piles 

## Document Information
- **Platform**: Ekofisk Complex, Block 2/4, Norwegian North Sea  
- **Initial installation era**: Early 1970s (Ekofisk development phase)  
- **Operator history**: Phillips Petroleum (now ConocoPhillips)  
- **Water depth (field-level, indicative)**: approximately 70–75 m (historical), locally affected by seabed subsidence  
- **Document date**: February 2025  
- **Status**: **Reconstructed benchmark** from public-domain sources + engineering assumptions (not an as-built certified dossier)

---

## Scope and Reliability Policy

This document is intended for **numerical benchmarking in CSF**, not for certification or forensic reconstruction.

Each parameter is tagged with one of the following evidence classes:

- **[Measured]**: directly traceable to a public source with explicit value
- **[Inferred]**: derived from published context using transparent engineering logic
- **[Assumed]**: modeling assumption introduced to complete a usable benchmark dataset

When a parameter is not publicly documented at pile-detail level, it is intentionally marked **[Assumed]**.

---

## 1) Platform Context (Field-Level)

Ekofisk is one of the earliest major North Sea developments. Public sources describe long-term seabed subsidence and major life-extension interventions.  
This benchmark uses that context to define a realistic, transparent degradation law for tubular foundation members.

| Parameter | Value | Unit | Evidence class | Notes |
|---|---:|---|---|---|
| Field water depth (order of magnitude) | 70–75 | m | [Measured] | Field-level public info |
| Seabed subsidence (historical, order of magnitude) | up to ~8 | m | [Measured] | Used only as contextual driver |
| Foundation typology | Steel driven/grouted piles | — | [Inferred] | Typical for jackets of the period |
| Long-term operation / life extension | Yes | — | [Measured] | Publicly documented at area level |

---

## 2) Foundation Pile Geometry for CSF Benchmark

### 2.1 Adopted Geometry Set (Benchmark)

> The following are **benchmark assumptions** chosen to produce a realistic and numerically stable test case.

| Parameter | Symbol | Value | Unit | Evidence class | Notes |
|---|---:|---:|---|---|---|
| Number of modeled piles | $$N_p$$ | 8 | — | [Assumed] | 4 clusters × 2 piles (modeling convention) |
| Outer diameter | $$D_o$$ | 2.400 | m | [Assumed] | Large-diameter offshore tubular pile |
| Wall thickness (minimum) | $$t_{\min}$$ | 0.050 | m | [Assumed] | Atmospheric/upper region |
| Wall thickness (maximum) | $$t_{\max}$$ | 0.075 | m | [Assumed] | Splash/corrosion-critical region |
| Free length above mudline | $$L_{\text{free}}$$ | 75 | m | [Assumed] | Benchmark value |
| Embedded length below mudline | $$L_{\text{emb}}$$ | 100 | m | [Assumed] | Benchmark value |
| Total modeled length | $$L_{\text{tot}}$$ | 175 | m | [Assumed] | $$L_{\text{free}}+L_{\text{emb}}$$ |

### 2.2 Thickness and Inner Diameter Definitions

Inner diameter:
$$
D_i(z) = D_o - 2\,t(z)
$$

Benchmark linear profile along member local axis
$$
z \in [0,L_{\text{tot}}]
$$

$$
t(z)=t_{\min}+\left(\frac{z}{L_{\text{tot}}}\right)\left(t_{\max}-t_{\min}\right)
$$

Equivalent global elevation mapping can be used in implementation; what matters is explicit, reproducible coordinate convention.

---

## 3) Degradation Weight Law (CSF)

### 3.1 Physical Interpretation

A splash-zone-centered reduction is modeled with a Gaussian envelope and a protected cutoff below a chosen elevation.

### 3.2 Parameters (Current Benchmark)

| Parameter | Symbol | Value | Unit | Evidence class | Meaning |
|---|---:|---:|---|---|---|
| Maximum degradation amplitude | $$\beta$$ | 0.35 | — | [Assumed] | Up to 35% stiffness reduction at center |
| Spread | $$\sigma$$ | 2.0 | m | [Assumed] | Splash-zone width |
| Center elevation | $$z_0$$ | +5.0 | m (MSL ref.) | [Assumed] | Peak degradation elevation |
| Protection cutoff | $$z_{\text{cut}}$$ | -2.0 | m (MSL ref.) | [Assumed] | Full protection below cutoff |

### 3.3 Weight Law

$$
w(z)=
\begin{cases}
1-\beta\exp\!\left(-\dfrac{(z-z_0)^2}{2\sigma^2}\right), & z>z_{\text{cut}}\\[6pt]
1, & z\le z_{\text{cut}}
\end{cases}
$$

with constraints:
$$
0 < w(z)\le 1
$$

### 3.4 Sanity Values for the Current Parameter Set

Using $$\beta=0.35,\ \sigma=2.0,\ z_0=5,\ z_{\text{cut}}=-2$$:

- $$w(5)=0.65$$ (maximum degradation)
- $$w(3)\approx 0.788$$
- $$w(0)\approx 0.984$$
- $$w(10)\approx 0.984$$
- $$w(60)\approx 1.00$$
- $$w(z)=1.00$$ for $$z\le -2$$

---

## 4) Section Formulas (Circular Hollow Section)

At any station $$z$$:

$$
A(z)=\frac{\pi}{4}\left[D_o^2-D_i(z)^2\right]
$$

$$
I(z)=\frac{\pi}{64}\left[D_o^4-D_i(z)^4\right]
$$

$$
W(z)=\frac{2I(z)}{D_o}
$$

$$
J_p(z)=\frac{\pi}{32}\left[D_o^4-D_i(z)^4\right]=2I(z)
$$

Weighted effective properties:

$$
EA_{\text{eff}}(z)=w(z)\,E\,A(z)
$$

$$
EI_{\text{eff}}(z)=w(z)\,E\,I(z)
$$

$$
GJ_{\text{eff}}(z)=w(z)\,G\,J_p(z),\quad
G=\frac{E}{2(1+\nu)}
$$

---

## 5) Material Set (Benchmark Steel)

| Parameter | Symbol | Value | Unit | Evidence class |
|---|---:|---:|---|---|
| Young’s modulus | $$E$$ | 210 | GPa | [Inferred] |
| Poisson’s ratio | $$\nu$$ | 0.30 | — | [Inferred] |
| Density | $$\rho$$ | 7850 | kg/m³ | [Inferred] |
| Yield strength (reference grade-level) | $$f_y$$ | 345 | MPa | [Inferred] |

> Grade naming in public historical sources may vary by document vintage. Keep this as a benchmark material card unless primary mill/test records are available.

---
## 6) Numerical Snapshot (Illustrative, at z = 5 m with t = 0.075 m)

Given:

$$
D_o = 2.4 \text{ m}, \quad D_i = 2.25 \text{ m}
$$

Then:

$$
A \approx 0.547 \text{ m}^2, \quad
I \approx 0.374 \text{ m}^4, \quad
J_p \approx 0.748 \text{ m}^4
$$

With $$w(5) = 0.65,\ E = 210 \text{ GPa},\ \nu = 0.30$$:

$$
EI_{\mathrm{eff}}(5) \approx 0.65 \times 210 \times 0.374 \approx 51.1 \text{ GN·m}^2
$$


(Values rounded; recompute directly in CSF pipeline for final reporting.)

---

## 7) Traceability and Use Constraints

### 7.1 What this benchmark **is**
- A transparent, reproducible **engineering benchmark** for CSF degradation modeling.
- Suitable for sensitivity studies, code verification, and method comparison.

### 7.2 What this benchmark **is not**
- A certified as-built pile schedule for Ekofisk Alpha.
- A substitute for operator-owned drawings, fabrication books, or inspection archives.

### 7.3 Recommended sensitivity envelope
Run at least three scenarios:

- **Low degradation**: $$\beta=0.20,\ \sigma=1.5$$  
- **Baseline**: $$\beta=0.35,\ \sigma=2.0$$  
- **High degradation**: $$\beta=0.50,\ \sigma=2.5$$

and optionally vary $$t_{\min},t_{\max},L_{\text{emb}}$$ within plausible engineering ranges.

---

## 8) CSF Implementation Template (YAML)

```yaml
CSF:
  sections:
    S0:
      z: 0.000000
      polygons:
        outer:
          weight: 1.000000
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
          weight: 0.000000
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
      z: 175.000000
      polygons:
        outer:
          weight: 1.000000
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
          weight: 0.000000
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
    - polygon: "outer"
      law: "1.0 - 0.35*np.exp(-((z-5.0)**2)/(2*(2.0**2))) if z > -2.0 else 1.0"

```

Notes:
- Use consistent axis/elevation mapping between geometry and weight law.
- Keep `outer` and `inner_void` conventions aligned with CSF composite rules.
- No silent defaults: missing mandatory attributes should fail validation.

---

## 9) Source Strategy (How to keep this defensible)

For each parameter, keep one row in your internal tracker:

- `parameter_name`
- `value_used`
- `class` = `[Measured|Inferred|Assumed]`
- `source_id` (URL / paper / report / page)
- `justification`

This avoids false precision and makes updates straightforward when better primary data becomes available.
