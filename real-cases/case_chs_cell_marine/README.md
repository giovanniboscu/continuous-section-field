![Figure_1](https://github.com/user-attachments/assets/f6bed297-4e1f-4793-a3a5-6921ff1d7711)

# CSF Benchmark Case: Closed-Cell CHS with Marine Corrosion Degradation
##  Get the Project and Create a Virtual Environment

```bash
# Clone the repository
git clone https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .

```

 Suggested Folder Layout

```text
case_chs_cell_marine/
├─ geometry.yaml
├─ action.yaml
├─ w_splash_lookup.txt
├─ out/
└─ README.md
```
From inside case_chs_cell_marine/:
to perfor the project run
```
python3 ../csf/CSFActions.py geometry.yaml action.yaml
```


## 1) Objective

This benchmark reproduces a **realistic offshore steel member scenario** using CSF:

- Geometry: Circular Hollow Section (CHS), modeled as a **closed thin-walled cell** (`@cell`).
- Baseline check: no degradation (`w(z)=1.0`) to validate `J_sv_cell` against theory.
- Corroded check: longitudinal degradation law via lookup (`T_lookup`) to emulate marine exposure severity variation.

The goal is to provide a **reproducible reference workflow** for:
1. geometric/stiffness evolution along `z`,
2. Saint-Venant torsion metrics (`J_sv`, `J_sv_cell`),
3. bibliographically grounded degradation motivation.

---

## 2) Case Definition

- Member type: CHS (steel)
- Axis: global `z`
- Length: `L = 30.0 m`
- Outer radius: `R_o = 3.000 m`
- Inner radius: `R_i = 2.965 m`
- Wall thickness: `t = 0.035 m`
- Material:
  - `E = 2.10e11 Pa`
  - `nu = 0.30`
  - `rho = 7850 kg/m^3`
- CSF tag path: `@cell` (closed-cell torsion path)

In the provided geometry, the ring is represented as a **single `@cell` polygonal path** (outer loop + bridge + inner loop + return bridge), with index-based pairing between stations.

---

## 3) Theoretical Check for `J_sv_cell` (No Degradation)

For a closed thin-walled cell (Bredt–Batho form, constant thickness):

`J = 4 * A_m^2 / ∮(ds/t) = 4 * A_m^2 * t / L_m`

Where:
- `A_m` = area enclosed by the **midline**
- `L_m` = perimeter of the midline
- `t` = constant thickness

In this benchmark, the midline is polygonal (octagonal approximation), therefore the correct reference is the **polygonal midline theoretical value** (not the continuous-circle formula).

### Baseline numerical outcome (from CSF run)

At `z = 0, 15, 30 m` (with `w=1.0`), the section properties are invariant and:

- `J_sv_cell = 4.8439324865 m^4`
- `J_sv_wall = 0.0` (expected for pure `@cell` path)

This matches the polygonal-theory value for the same midline discretization.

---

## 4) Corrosion/Degradation Modeling Strategy

A marine corrosion profile is introduced through **weight law**:

- `w(z)` via `T_lookup('w_splash_lookup.txt')`
- Applied to the `@cell` polygon name pair between `S0` and `S1`
- This modifies effective properties along `z` while preserving topology/tags.

Example lookup shape used in tests:
- stronger reduction near splash-zone region,
- partial recovery away from maximum attack zone,
- bounded positive values.

---

## 5) Why This Is a “Real Case” Style Benchmark

This setup emulates practical offshore reliability workflows where:
- structural capacity evolves with environmental deterioration,
- corrosion is non-uniform along member height,
- torsional resistance of closed steel tubes is critical.

It is intentionally minimal and reproducible, while keeping direct traceability to published corrosion modeling literature.

---

## 6) Reproducibility Notes

1. Keep polygon orientation and parser preconditions consistent with CSF validation rules.
2. Use `@cell` (not `@wall`) for closed-cell torsion checks.
3. For strict baseline comparison, disable degradation (`w=1.0`) before activating lookup laws.
4. Compare:
   - baseline (`w=1`) vs degraded (`w(z)`),
   - `J_sv_cell(z)` trend,
   - section invariants under no degradation.

---

## 7) Bibliographic References

### Core corrosion modeling references

1. **Melchers, R. E. (2003a)**.  
   *Modeling of Marine Immersion Corrosion for Mild and Low-Alloy Steels — Part 1: Phenomenological Model*.  
   **Corrosion**, 59(4), 319–334.

2. **Melchers, R. E. (2003b)**.  
   *Modeling of Marine Immersion Corrosion for Mild and Low-Alloy Steels — Part 2: Uncertainty Estimation*.  
   **Corrosion**, 59(4), 335–344.

3. **Melchers, R. E. (2003)**.  
   *Mathematical Modelling of the Diffusion Controlled Phase in Marine Immersion Corrosion of Mild Steel*.  
   **Corrosion Science**, 45, 923–940.

4. **Melchers, R. E. (2019)**.  
   *Predicting long-term corrosion of steel in marine and atmospheric environments: methods, trends and challenges*.  
   (Review paper; use as synthesis/background reference for long-term prediction context.)

### Beam/taper benchmark reference previously discussed

5. **Ece, M. C., Aydogdu, M., & Taskin, V. (2007)**.  
   *Vibration of a variable cross-section beam*.  
   **Mechanics Research Communications**, 34(1), 78–84.  
   DOI: `10.1016/j.mechrescom.2006.06.005`

---

## 8) Folder Layout

```text
case_chs_cell_marine/
├─ geometry.yaml
├─ action.yaml
├─ w_splash_lookup.txt
├─ out/
└─ README.md
```

---

## 9) Recommended Outputs to Archive

- `section_selected_analysis` at edge/mid stations
- `plot_properties` (`A, Ix, Iy, J_sv, J_sv_cell`)
- versioned copy of lookup files used for each run

This guarantees auditability of each benchmark run.

---

## 10) Geometry Rationale for `ring@cell@t=0.035`

1. **Why `@cell`**  
   The section is a closed CHS ring; torsion must be evaluated with the closed-cell path (`J_sv_cell`), not open-wall path.

2. **Why `t=0.035`**  
   Thickness is defined as a model input and kept constant along `z` in this benchmark to isolate degradation effects from geometry changes.

3. **Why single-path outer+inner+bridges**  
   The ring is encoded as one `@cell` polygonal chain (outer loop, bridge, inner loop, return bridge) to enforce one closed-cell entity in the parser path.

4. **Why octagonal discretization**  
   An 8-side polygon is used as a minimal, reproducible approximation of circular loops with low input size and stable numerics.

5. **Why index-based pairing `S0` ↔ `S1`**  
   CSF pairing is positional; same polygon index and same naming guarantee deterministic interpolation/rule application across stations.

6. **Known modeling consequence**  
   The theoretical reference for validation is the **polygonal midline** formula.  
   Therefore `J_sv_cell` must match the octagonal-midline theory (not the continuous perfect-circle formula).

8. **Validation outcome (this case)**  
   With `w(z)=1.0`, properties are invariant along `z`, `J_sv_wall=0`, and `J_sv_cell` matches polygonal-theory baseline.
![chs-weight](https://github.com/user-attachments/assets/c8b419bd-42c3-48a4-b072-9d176ecf085d)


![chs_props](https://github.com/user-attachments/assets/c73904b1-ebb1-4146-83f5-ca6305018e21)

![chs-sections](https://github.com/user-attachments/assets/30973ba4-73c7-4864-aa02-6e40aa41fcc0)
