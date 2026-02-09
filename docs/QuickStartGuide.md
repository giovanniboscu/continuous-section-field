# Quick Start Guide
## Ekofisk Foundation Pile Benchmark
### Practical, didactic workflow from zero to results

This guide explains how to start from a complete **CSF geometry file**, add a **degradation law `w(z)`**, run **CSF_ACTIONS**, and interpret the outputs.

---

## 1) What you need before starting

Prepare two YAML files:

1. **Geometry file** (for example: `geometry.yaml`)  
   Contains:
   - section stations (`S0`, `S1`, ...),
   - polygons (`outer`, `inner_void`, ...),
   - optional `weight_laws` such as `w(z)`.

2. **Actions file** (for example: `actions.yaml`)  
   Contains:
   - station sets to sample,
   - plotting and analysis actions,
   - output destinations (stdout and/or files).

You should also know:
- your local axis convention (`z` along member),
- if `z` is local only, or mapped to a global elevation reference.

---

## 2) Conceptual model in one minute

For this benchmark:
- geometry is a tubular section (outer polygon + inner void polygon),
- section properties vary along `z`,
- degradation is introduced with a scalar law `w(z)`.

Typical scaled quantities:
- `EA_eff(z) = w(z) * E * A(z)`
- `EI_eff(z) = w(z) * E * I(z)`
- `GJ_eff(z) = w(z) * G * J(z)`

So you should always read results with this separation:
1. geometry-driven variation,
2. degradation-law scaling effect.

---

## 3) Build the geometry file (`geometry.yaml`)

Below is a compact template structure (replace with your exact vertices and stations):

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [x1, y1]
            - [x2, y2]
            # ...
        inner_void:
          weight: 0.0
          vertices:
            - [u1, v1]
            - [u2, v2]
            # ...

    S1:
      z: 175.0
      polygons:
        outer:
          weight: 1.0
          vertices:
            - [x1b, y1b]
            - [x2b, y2b]
            # ...
        inner_void:
          weight: 0.0
          vertices:
            - [u1b, v1b]
            - [u2b, v2b]
            # ...

  weight_laws:
    - 'outer,outer: 1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))'
```

### Important checks when building geometry
- polygon orientation and validity must satisfy your CSF preconditions,
- `outer`/`inner_void` naming must be consistent across stations,
- no missing mandatory attributes,
- avoid silent defaults in critical fields.

---

## 4) Choose and write `w(z)` correctly

### Baseline Gaussian law
```python
1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))
```

Interpretation:
- center at `z=5`,
- max reduction `40%`,
- spread `sigma=2.0`.

### If you use cutoff logic
Only use conditions that are active in your actual `z` domain.  
If local `z` is `[0, 175]`, a condition like `if z > -2.0` is always true and does not create an effective cutoff.

---

## 5) Build the actions file (`actions.yaml`)

Recommended starter structure:

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

## 6) Why these stations are recommended

Use stations that capture:
- degradation peak: `z=5`,
- flanks: `z=3, 7`,
- near-recovery: `z=0, 10`,
- far field/reference: `z=50, 175`.

This gives a clean and verifiable trend:
- minimum near `z=5`,
- symmetry around the center (if law is symmetric),
- plateau far from degraded zone.

---

## 7) How to run the analysis (generic sequence)

1. Validate YAML syntax (both files).  
2. Run CSF with the geometry file.  
3. Execute `CSF_ACTIONS` from the actions file.  
4. Inspect stdout and generated files in `out/`.  
5. Confirm trends and station values.

Use your project’s exact command-line or Python entrypoint.

---

## 8) What to check first in outputs

### A) `section_selected_analysis`
Check if:
- `A, Ix, Iy, J` reach minimum near degradation center,
- symmetric stations have similar values (`z=3` and `z=7`),
- far stations (`z=50`, `z=175`) converge to reference values.

### B) `plot_weight`
Check:
- `w_min` location is where expected,
- `w` returns close to 1 away from degraded zone,
- no constant-zero curves unless intentionally defined.

### C) `plot_properties`
Check monotonicity/shape consistency against your intended `w(z)` and geometry variation.

---

## 9) Quick theoretical consistency check (CHS formulas)

For circular hollow section:
- `A = (pi/4) * (Do^2 - Di^2)`
- `I = (pi/64) * (Do^4 - Di^4)`
- `Jp = 2*I`

Use this as a sanity baseline for selected stations.

---

## 10) Minimal troubleshooting checklist

If results look wrong, verify in this order:

1. **Geometry mismatch**  
   Declared diameters/thickness vs actual polygon radii in vertices.

2. **Law-domain mismatch**  
   Conditions in `w(z)` that never activate in your local domain.

3. **Station selection**  
   Missing peak/flank stations can hide degradation behavior.

4. **Key names in actions**  
   Keep parser-specific keys exactly as expected (for example `weith_law` if your runner requires that name).

5. **Units and scale**  
   Ensure consistent SI units across geometry/material/law interpretation.

---

## 11) Recommended reporting block (copy-ready)

Include these sections in every benchmark report:
- model scope and reliability policy,
- parameter evidence class (`Measured/Inferred/Assumed`),
- geometry summary,
- explicit `w(z)` equation and parameter values,
- station list,
- selected property table (`A, Ix, Iy, J`),
- sensitivity envelope (low / baseline / high),
- traceability table with sources and justification.

---

## 12) Suggested low-baseline-high law set

### Low
```python
1.0 - 0.20*np.exp(-((z-5.0)**2)/(2*(1.5**2)))
```

### Baseline
```python
1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))
```

### High
```python
1.0 - 0.50*np.exp(-((z-5.0)**2)/(2*(2.5**2)))
```

---

## 13) Final workflow summary

1. Define geometry and stations clearly.  
2. Add explicit, physically motivated `w(z)`.  
3. Use station sets that expose peak/flanks/reference zones.  
4. Run actions and inspect both tabular and graphical outputs.  
5. Validate against CHS theory at key stations.  
6. Publish assumptions and sensitivity envelope with traceability.

This sequence gives a fast start and a defensible benchmark result.
