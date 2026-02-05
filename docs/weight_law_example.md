# 📚 Library of w(z) Functions in NumPy Syntax for CSF

This document provides a comprehensive collection of weight field (w) variation laws for advanced structural modeling. These functions use NumPy syntax and are designed to be interpreted directly by the CSF engine via the `eval()` command.

---

## 1. LINEAR & POLYNOMIAL VARIATIONS
Used for gradual changes in material properties or geometric tapering.

1. **Simple Linear Gradient:**
   `w: "eval(1.0 + 0.1 * z)"`
   (Modifies strength/mass linearly along the axis, e.g., higher concrete grade at the base).

2. **Quadratic Increase (Parabolic):**
   `w: "eval(1.0 + 0.05 * z**2)"`
   (Models a profile following a bending moment diagram).

3. **Cubic Taper:**
   `w: "eval(1.0 + 0.01 * z**3)"`
   (Used for high-performance cantilever beams with optimized mass distribution).

4. **Safety Floor (Min Threshold):**
   `w: "eval(np.maximum(0.2, 1.0 - 0.1 * z))"`
   (Models degradation while ensuring stiffness never drops below a 20% safety limit).

---

## 2. DISCONTINUITIES & STEP FUNCTIONS (np.where)
Used for sudden changes in material, reinforcement, or geometry.

5. **Single Step (Binary Material):**
   `w: "eval(np.where(z < L/2, 1.0, 2.0))"`
   (Models a beam split into two different materials, like wood and steel).

6. **Central Reinforcement Zone:**
   `w: "eval(np.where((z > 3.0) & (z < 7.0), 3.0, 1.0))"`
   (Models local reinforcement plates or carbon fiber wrapping in the max moment area).

7. **Multi-Step (Staircase):**
   `w: "eval(np.where(z < 3, 1.0, np.where(z < 6, 1.5, 2.0)))"`
   (Models a multi-stage telescopic or layered structural element).

8. **End-Cap Reinforcements:**
   `w: "eval(np.where((z < 1.0) | (z > 9.0), 2.5, 1.0))"`
   (Models thickened sections at the supports/anchors).

---

## 3. PERIODIC & CYCLIC VARIATIONS
Simulates repetitive prefabricated modules, holes, or bracing.

9. **Smooth Sinusoid:**
   `w: "eval(1.0 + 0.5 * np.sin(2 * np.pi * z / 2.0))"`
   (Models cellular beams or repetitive circular openings every 2 meters).

10. **High-Frequency Vibration Shield:**
    `w: "eval(1.0 + 0.3 * np.sin(10 * np.pi * z / L))"`
    (Models a periodic structure designed as a phononic crystal to block vibrations).

11. **Approximated Square Wave:**
    `w: "eval(1.0 + 0.5 * np.sign(np.sin(2 * np.pi * z / 1.0)))"`
    (Models the stark "solid vs void" transition in Vierendeel trusses).

12. **Damped Oscillation:**
    `w: "eval(1.0 + 0.5 * np.sin(5 * z) * np.exp(-0.1 * z))"`
    (Models a reinforcement pattern that fades out along the beam).

---

## 4. LOCALIZED CONCENTRATIONS & DECAY
Ideal for nodal masses, equipment attachments, or damage zones.

13. **Gaussian Bell (Soft Point Mass):**
    `w: "eval(1.0 + 10.0 * np.exp(-(z - 5.0)**2 / (2 * 0.2**2)))"`
    (Models a heavy engine or concentrated weight at z=5.0).

14. **Localized Damage (Pitting):**
    `w: "eval(1.0 - 0.8 * np.exp(-(z - 4.0)**2 / 0.1))"`
    (Models a local defect, hole, or severe corrosion spot).

15. **Dual Point Masses:**
    `w: "eval(1.0 + 5.0 * (np.exp(-(z-2)**2/0.1) + np.exp(-(z-8)**2/0.1)))"`
    (Models two heavy secondary beams framing into the main element).

---

## 5. COMPLEX HYBRID LAWS
Advanced combinations of the above logic for realistic engineering scenarios.

16. **The "Hybrid Stage" Formula:**
    `w: "eval(np.where(z < 5.0, 1.0 + 0.5*np.sin(2*np.pi*z/5.0), 2.0 + 0.2*np.sin(4*np.pi*z/5.0)))"`
    (Models two spans with different materials and different reinforcement frequencies).

17. **Frequency Sweep (Chirp):**
    `w: "eval(1.0 + 0.5 * np.sin(np.pi * z**2 / L))"`
    (Models a structural grating where the spacing of elements changes along the length).

18. **Clipped Sine (One-way Reinforcement):**
    `w: "eval(1.0 + np.maximum(0, 0.8 * np.sin(2 * np.pi * z / 3.0)))"`
    (Models a beam where reinforcement is added in waves but never removed).

19. **Logarithmic Transition:**
    `w: "eval(1.0 + np.log1p(z))"`
    (Models a property that increases rapidly at the start and then stabilizes).

20. **Random Noise (Stochastic Material):**
    `w: "eval(1.0 + 0.05 * np.random.normal(0, 1, z.shape if hasattr(z, 'shape') else 1))"`
    (Used for sensitivity analysis to model material imperfections or uncertainty).

---

## TECHNICAL NOTES FOR CSF
1. **Variable 'z':** Recognized natively as the coordinate along the beam axis.
2. **Variable 'L':** Replace with the numerical length or define it in your script.
3. **Prefix 'np.':** Essential for all NumPy functions (sin, pi, exp, where, etc.).
4. **Logic:** The `eval()` string must return a value (or array of values) > 0 for physical validity.


# 📚 Extended Library of w(z, t) Functions in NumPy Syntax for CSF

This document provides 20+ advanced variation laws for the weight field (w), incorporating normalized coordinates (t) and external data lookup functions.

---

## 1. COORDINATE SYSTEMS & EXTERNAL DATA
* **z**: Absolute coordinate along the axis $[0, L]$.
* **t**: Normalized coordinate $[0, 1]$, where $t = z/L$.
* **E_lookup(file)**: Loads Elasticity/Experimental data from an external file.
* **T_lookup(file)**: Loads generic Tabular/Text data from an external file.

---

## 2. LINEAR & POLYNOMIAL VARIATIONS (Using 't' for Portability)
1. **Normalized Linear Gradient:**
   `w: "eval(1.0 + 0.5 * t)"`
   (Increases by 50% from start to end, regardless of beam length).

2. **Quadratic Taper (Normalized):**
   `w: "eval(1.0 + 0.8 * t**2)"`
   (Ideal for standardized beam designs where curvature depends on relative position).

3. **Symmetric Parabola:**
   `w: "eval(1.0 + 4 * (t - 0.5)**2)"`
   (Maximum weight at ends, minimum at center).

4. **Inverted Safety Floor:**
   `w: "eval(np.maximum(0.5, 1.5 - t))"`
   (Gradual reduction of properties, stopping at a 50% safety threshold).

---

## 3. EXTERNAL DATA & LOOKUP FUNCTIONS
5. **Experimental Data Mapping:**
   `w: "eval(E_lookup('stiffness_map.csv'))"`
   (Maps real-world test data or ultrasonic scan results directly onto the beam).

6. **Tabular Geometry Correction:**
   `w: "eval(T_lookup('as_built_measurements.txt'))"`
   (Adjusts the model based on "as-built" site measurements).

7. **Multi-File Material Blending:**
   `w: "eval(0.5 * E_lookup('mat_A.dat') + 0.5 * E_lookup('mat_B.dat'))"`
   (Blends two experimental datasets for composite material simulation).

---

## 4. DISCONTINUITIES & STEP FUNCTIONS (np.where)
8. **Normalized Half-Span Step:**
   `w: "eval(np.where(t < 0.5, 1.0, 1.5))"`
   (Simple material change at the exact midpoint).

9. **Triple-Segment Truss:**
   `w: "eval(np.where(t < 0.33, 1.0, np.where(t < 0.66, 2.0, 1.0)))"`
   (Models a reinforced central core between two standard end segments).

10. **Anchor Zone Reinforcement:**
    `w: "eval(np.where((t < 0.1) | (t > 0.9), 2.5, 1.0))"`
    (Strengthens the first and last 10% of the beam length).

---

## 5. PERIODIC & CYCLIC VARIATIONS (Prefabricated Modules)
11. **Normalized Sinusoid (Fixed Cycles):**
    `w: "eval(1.0 + 0.5 * np.sin(2 * np.pi * 5 * t))"`
    (Models exactly 5 cycles of variation along any beam length).

12. **Square Wave Phase Shift:**
    `w: "eval(1.0 + 0.4 * np.sign(np.sin(2 * np.pi * 10 * (t - 0.1))))"`
    (Models 10 prefabricated ribs with a specific starting offset).

13. **Beating Frequency Pattern:**
    `w: "eval(1.0 + 0.5 * np.sin(2 * np.pi * 5 * t) * np.sin(2 * np.pi * 0.5 * t))"`
    (Models complex interference patterns in acoustic or high-tech structures).

---

## 6. LOCALIZED CONCENTRATIONS & DECAY
14. **Normalized Gaussian Bell:**
    `w: "eval(1.0 + 8.0 * np.exp(-(t - 0.5)**2 / (2 * 0.05**2)))"`
    (Concentrated mass exactly at mid-span with a 5% spread).

15. **End-Load Impact Zone:**
    `w: "eval(1.0 + 5.0 * np.exp(-t / 0.1))"`
    (High reinforcement at the start ($t=0$) that decays within the first 10% of the beam).

16. **Point Defect at 1/4 Span:**
    `w: "eval(1.0 - 0.7 * np.exp(-(t - 0.25)**2 / 0.001))"`
    (Simulates a local crack or hole at 25% of the length).

---

## 7. ADVANCED HYBRID & LOGIC LAWS
17. **Frequency Sweep (Normalized Chirp):**
    `w: "eval(1.0 + 0.5 * np.sin(np.pi * 20 * t**2))"`
    (A pattern that gets denser toward the end of the beam).

18. **Clipped Periodic Growth:**
    `w: "eval(1.0 + np.maximum(0, t * np.sin(10 * np.pi * t)))"`
    (Reinforcements that appear periodically and grow in intensity along the span).

19. **Logarithmic Saturation:**
    `w: "eval(1.0 + np.log1p(9 * t))"`
    (Property that scales from 1.0 to approx 3.3 following a log curve).

20. **Combined Lookup & Sine:**
    `w: "eval(E_lookup('data.csv') * (1.0 + 0.2 * np.sin(2 * np.pi * t)))"`
    (Applies a periodic correction/fluctuation to an experimental data baseline).

---

## TECHNICAL NOTES
- **t vs z**: Use `t` for generic templates and `z` for absolute physical constraints.
- **Lookup Performance**: Data files are typically cached; large files may impact initial load time.
- **Data Validation**: Ensure `E_lookup` or `T_lookup` files contain no negative values if used for mass/stiffness.


# 📚 Extended Library of w(z, t) Functions in NumPy Syntax for CSF

This library explores the power of combining mathematical functions with external data lookups. 
In CSF, `E_lookup` and `T_lookup` return values that can be used directly as operands in any algebraic expression.

---

## 1. COORDINATE SYSTEMS & EXTERNAL DATA
* **z**: Absolute coordinate along the axis [0, L].
* **t**: Normalized coordinate [0, 1] (where t = z/L).
* **E_lookup(file)**: Loads elasticity/stiffness data from an external file.
* **T_lookup(file)**: Loads generic tabular data (e.g., thickness, weight coefficients).

---# 📚 Library of w(z, t) Functions - Native CSF Syntax

In CSF, the `w` field is automatically evaluated as a Python expression. You can use math constants, NumPy functions, and external data lookups directly.

---

## 1. VARIABLES & DATA SOURCES
* **z**: Absolute coordinate along the axis [0, L].
* **t**: Normalized coordinate [0, 1] (where t = z/L).
* **E_lookup(file)**: Returns numerical values from an external elasticity/stiffness file.
- **T_lookup(file)**: Returns numerical values from a generic tabular data file.

---

## 2. OPERATIONAL LOOKUPS (Data + Algebra)
Since CSF treats the string as code, you can perform math directly on the file results.

1. **Safety Factor Scaling:**
   `w: "E_lookup('data.csv') * 1.15"`
   (Boosts experimental data by 15%).

2. **Trend Correction:**
   `w: "E_lookup('sensors.txt') + (0.2 * t)"`
   (Adjusts sensor data with a linear growth factor).

3. **Noise Filtering/Simulation:**
   `w: "E_lookup('stiffness.csv') * (1.0 + 0.05 * np.sin(2 * np.pi * t))"`
   (Adds a 5% cyclic "imperfection" to measured data).

4. **Composite Merging:**
   `w: "E_lookup('core.csv') + T_lookup('coating.csv')"`
   (Sums contributions from two different data files).

---

## 3. GEOMETRIC & LINEAR VARIATIONS
5. **Standard Taper:**
   `w: "1.0 + 0.8 * t"`
   (Increases properties linearly from 100% to 180%).

6. **Parabolic Distribution:**
   `w: "1.0 + 4 * (t - 0.5)**2"`
   (Material concentrated at the ends, minimum at the center).

7. **Exponential Growth:**
   `w: "np.exp(t)"`
   (Natural exponential increase along the length).

---

## 4. PERIODIC & MODULAR (Prefabrication)
8. **Fixed Module Count:**
   `w: "1.0 + 0.5 * np.sin(2 * np.pi * 8 * t)"`
   (Exactly 8 modules/cycles over any beam length).

9. **Pulsed Reinforcement:**
   `w: "1.0 + 0.5 * np.sign(np.sin(2 * np.pi * 10 * t))"`
   (Alternates between 0.5 and 1.5 in sharp blocks).

10. **Increasing Frequency (Chirp):**
    `w: "1.0 + 0.5 * np.sin(np.pi * 10 * t**2)"`
    (Variation frequency increases towards the end).

---

## 5. LOCALIZED EVENTS (Mass & Damage)
11. **Central Point Mass:**
    `w: "1.0 + 5.0 * np.exp(-(t - 0.5)**2 / 0.002)"`
    (Sharp Gaussian peak at mid-span).

12. **Support Reinforcement:**
    `w: "1.0 + 2.0 * np.exp(-20 * t) + 2.0 * np.exp(-20 * (1-t))"`
    (Concentrated reinforcement at both supports).

13. **Local Defect Simulation:**
    `w: "1.0 - 0.9 * np.exp(-(t - 0.3)**2 / 0.0001)"`
    (Simulates a severe local crack or hole at t=0.3).

---

## 6. LOGIC & CONDITIONALS
14. **Material Switch:**
    `w: "np.where(t < 0.5, 1.0, 2.0)"`
    (Abrupt change at the midpoint).

15. **Clamping Values:**
    `w: "np.clip(E_lookup('raw.csv'), 0.1, 3.0)"`
    (Ensures data stays within physical bounds).

16. **Data-Driven Switch:**
    `w: "np.where(E_lookup('test.csv') > 1.0, 1.2, 0.8)"`
    (Assigns values based on an experimental threshold).

---

## 7. ADVANCED MATHEMATICS
17. **Logarithmic Saturation:**
    `w: "1.0 + np.log1p(5 * t)"`
    (Rapid initial growth that levels off).

18. **Clipped Sine:**
    `w: "1.0 + np.maximum(0, np.sin(10 * np.pi * t))"`
    (Only adds material in cycles, never subtracts).

19. **Root Scaling:**
    `w: "np.sqrt(1 + t)"`
    (Mild non-linear increase).

20. **Dynamic Stiffness Mapping:**
    `w: "E_lookup('map.csv') / (1.0 + t)"`
    (Reduces experimental stiffness as a function of distance).

---

### PRO TIP
Since CSF interprets the string directly, you can even use complex Python one-liners, but remember that **scannability is key** for your future self!
