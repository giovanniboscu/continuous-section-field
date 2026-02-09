# Corrosion Degradation Laws for Offshore Steel Piles in CSF

## 1) Purpose
This note explains how to choose and justify longitudinal degradation laws `w(z)` in CSF for offshore steel tubular members (e.g., jacket foundation piles), with clear physical and mechanical rationale.

This is for:
- benchmarking,
- sensitivity analysis,
- transparent model documentation.

This is not for:
- as-built certification,
- forensic reconstruction without primary records.

---

## 2) Meaning of `w(z)` in CSF

In CSF, `w(z)` is a scalar field along the member axis `z`, usually constrained to:

`0 < w(z) <= 1`

Typical effective-property scaling:

- `EA_eff(z) = w(z) * E * A(z)`
- `EI_eff(z) = w(z) * E * I(z)`
- `GJ_eff(z) = w(z) * G * J(z)`

where `A(z), I(z), J(z)` may already vary with geometry.

---

## 3) Why zone-based degradation is realistic offshore

Marine corrosion is strongly elevation-dependent:

- atmospheric zone,
- splash/tidal zone (often most aggressive),
- submerged zone,
- mudline/embedded zone.

Therefore, a localized or banded `w(z)` is physically more plausible than uniform degradation along the entire member.

---

## 4) Important standards context (what they do and do not provide)

Standards define:
- exposure classes,
- protection philosophy (coating / cathodic protection),
- design verification framework.

They usually do **not** prescribe one universal closed-form equation for `w(z)`.
So engineering practice uses parametric surrogate laws calibrated to data and assumptions.

---

## 5) Practical families of degradation laws

### 5.1 Gaussian localized law
Formula:
`w(z) = 1 - beta * exp(-((z - z0)^2) / (2 * sigma^2))`

Parameters:
- `beta`  = peak degradation amplitude
- `z0`    = center elevation of peak degradation
- `sigma` = spread (in meters)

Pros:
- smooth,
- numerically stable,
- simple calibration.

Cons:
- symmetric shape,
- long tails.

Python expression:
```python
1.0 - 0.35*np.exp(-((z-5.0)**2)/(2*(2.0**2)))
```

---

### 5.2 Double-sigmoid band law
Formula:
`w(z) = 1 - beta * [ S(z,z1,k) - S(z,z2,k) ]`

with:
`S(z,zc,k) = 1 / (1 + exp(-k*(z-zc)))`

Expanded:
`w(z) = 1 - beta * ( 1/(1+exp(-k*(z-z1))) - 1/(1+exp(-k*(z-z2))) )`, with `z2 > z1`.

Parameters:
- `z1, z2` = band start/end,
- `k`      = edge steepness,
- `beta`   = max amplitude.

Pros:
- realistic finite degradation band,
- smooth edges,
- easy to justify in reports.

Cons:
- more parameters than Gaussian.

Python expression:
```python
1.0 - 0.40 * (1.0/(1.0 + np.exp(-2.0*(z - 2.0))) - 1.0/(1.0 + np.exp(-2.0*(z - 8.0))))
```

---

### 5.3 Trapezoidal / piecewise law
Useful when inspection bands are explicit.

Example (text form):
- if `z < za`: `w=1`
- if `za <= z < zb`: linear drop from `1` to `1-beta`
- if `zb <= z <= zc`: plateau `w=1-beta`
- if `zc < z <= zd`: linear rise from `1-beta` to `1`
- if `z > zd`: `w=1`

Pros:
- very auditable,
- direct mapping to engineering zones.

Cons:
- derivative discontinuities at breakpoints.

---

### 5.4 One-sided exponential attenuation
Formula:
`w(z) = 1 - beta * exp(-alpha*(z-zr))` for a chosen side of reference `zr`.

Pros:
- very simple,
- useful for monotonic decay from a reference zone.

Cons:
- not naturally band-limited unless combined with cutoffs/blending.

---

## 6) Mechanical meaning of parameters

- `beta` controls severity of stiffness/capacity reduction.
- `z0` or `[z1,z2]` controls where the main stiffness valley appears.
- `sigma` or `k` controls how concentrated or spread the degradation is.
- cutoff/reference levels must match the actual coordinate definition (local z vs MSL elevation).

---

## 7) Mandatory consistency checks

1. Enforce bounds: `0 < w(z) <= 1`.
2. Ensure coordinate consistency: local `z` vs mapped elevation.
3. Avoid dead logic (conditions always true/false over domain).
4. Use stations at peak, flanks, and far field.
5. Run low/baseline/high scenarios.
6. Tag each parameter as Measured / Inferred / Assumed.

---

## 8) Recommended scenario envelope

- Low: lower `beta`, narrower band/spread.
- Baseline: medium `beta`, medium spread.
- High: higher `beta` and/or wider spread.

Report:
- min/max of key properties,
- z-location of min/max,
- percent reduction vs reference stations.

---

## 9) Source basis (for physical zoning framework)

These sources justify marine corrosion zoning and corrosion-control context.
They do not prescribe one mandatory closed-form `w(z)`.

1. ISO 12944-9:2018 (offshore protective systems framework)  
   https://www.iso.org/standard/64832.html

2. NORSOK M-001 (materials selection / offshore corrosion context)  
   https://aboutcorrosion.s3.amazonaws.com/Standards/NORSOK/m00001_2014%7B5%7Den.0115940830.pdf

3. DNVGL-OS-C101 (offshore steel structures design framework)  
   https://fenix.tecnico.ulisboa.pt/downloadFile/1689468335670463/DNVGL-OS-C101_2018.pdf

4. Practice-oriented marine design/corrosion zoning note (example)  
   https://ukccsrc.ac.uk/wp-content/uploads/2023/04/MDE1234-RPS-01-CX-RP-Z-0008_Marine-Design-Philosophy-Cork.pdf

---

## 10) Suggested wording for your report

"The adopted `w(z)` is a parametric degradation surrogate calibrated for offshore exposure zoning (atmospheric/splash/submerged), consistent with ISO/NORSOK/DNV corrosion-control frameworks. Since no single mandatory closed-form equation is prescribed for this purpose, the model uses transparent function families and a documented low/baseline/high sensitivity envelope."

---

## 11) Final recommendation for CSF workflow

- Use **double-sigmoid** as primary realistic band law.
- Keep **Gaussian** as comparator baseline.
- Publish assumptions and parameter classes clearly.
- Separate:
  1) geometry-driven variation,
  2) material constants,
  3) degradation-law scaling effects.
