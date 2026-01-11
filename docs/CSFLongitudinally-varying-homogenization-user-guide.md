#  🛠  ContinuousSectionField (CSF) | Custom Weight Laws User Guide

This document provides the technical specifications for implementing and using **Custom Weight Laws** to define the variation of the Elastic Modulus ratio (`weight`) along a structural member.


> **Important — what is `weight`?**  
> In CSF, `weight` is a **scalar field** used to scale section properties (a generalized multiplier of the geometric area).  
> It can represent an **E-modulus ratio** (dimensionless) *or* the **Young’s modulus E** (e.g., MPa).  
> The only requirement is that your formulas and lookup data follow a **consistent convention**.

 **Important — what is `weight` in CSF?**

 In CSF, `weight` is a **scalar field W(z)** attached to each polygonal region.
 CSF uses it as a **multiplier inside area integrals**, i.e. it “weights” geometry to produce
 an **equivalent homogenized section**.

 **This tool is unit-system agnostic.**  
 OpenSees is also unitless: you may use mm–N–MPa or m–N–Pa, etc.  
 The only hard rule is: **all inputs must follow one consistent unit convention**.

 ### Two valid conventions for `weight`

 CSF supports two different (but equally valid) interpretations. You must pick one and
 keep it consistent across your workflow and exports:

 #### Convention A — `weight` as a dimensionless stiffness ratio (recommended)
 - `weight = E / E_ref`  (dimensionless)
 - Choose one reference modulus `E_ref` (e.g., steel, concrete, etc.)
 - Softer regions have `0 < weight < 1`, stiffer have `weight  1`.
 - Voids are represented by negative weights (see "Voids" below).

 In this convention, CSF computes **modular (weighted) section properties**:

 \[
 A^*(z) = \sum_i w_i(z)\,A_i(z), \qquad
 I^*(z) = \sum_i w_i(z)\,I_i(z)
 \]

 so that the stiffness products match:

 \[
 E_{ref} A^*(z) = \sum_i E_i(z) A_i(z), \qquad
 E_{ref} I^*(z) = \sum_i E_i(z) I_i(z)
 \]

 #### Convention B — `weight` as a real-valued field (e.g. Young’s modulus)
 - `weight = E` in your chosen units (MPa, Pa, etc.)
 - This allows data-driven modeling directly in physical units (e.g., from `E_lookup()`).

 With this convention, the section integrals become stiffness-like quantities directly
 (e.g., \(\int E\,dA\)). This is valid, but you must then export to OpenSees using a
 stiffness-encoded contract (see OpenSees mapping below).

 ### Voids: the sign rule
 A void must always subtract the same “material measure” that the solid contributes.
 If a solid region uses `+w`, the matching void must use `-w`.
 This guarantees that the overlap sum is zero and contributes no stiffness:

 \[
 w_{solid} + w_{void} = 0
 \]

---

## OpenSees integration: how CSF stiffness samples are consumed

CSF exports a **sequence of station snapshots** along the member:
each station carries the local section state (A, Iy, Iz, J, and centroid offsets Cx,Cy).
OpenSees must integrate these samples along the length of the member.

### 1) Why `beamIntegration Lobatto` alone is ambiguous for CSF
OpenSees’ standard `beamIntegration Lobatto` is typically used with **one section tag**
and a number of integration points.
If you need the solver to read **multiple different section tags** (one per CSF station),
you must use:

- `beamIntegration UserDefined`

This is the only unambiguous bridge that allows OpenSees to consume the full CSF station list.

### 2) Gauss–Lobatto stations: end conditions are exact
CSF places stations using the **Gauss–Lobatto rule**, which includes the endpoints of the domain.
Therefore:
- the first CSF station coincides with the real member start,
- the last CSF station coincides with the real member end.

This guarantees that boundary conditions and tip loads are applied at the **true ends**
of the physical member.

### 3) Real centroid axis: curvature / eccentricity is preserved (variable Cy)
The physical axis of a non-prismatic member is not always the straight line between two endpoints.
CSF explicitly tracks the centroid offsets `(Cx(z), Cy(z))`.

In the OpenSees builder:
- a **reference axis** is created for clean application of constraints and loads,
- a **centroid axis** is created using the CSF offsets `(Cx_i, Cy_i)` at each station,
- each reference node is tied to its centroid node using `rigidLink beam`.

This ensures:
- the model represents the **real eccentricity field** (variable Cy),
- the correct eccentric-load coupling appears automatically as additional moments.

> Implementation note: `rigidLink` requires `constraints Transformation` in OpenSees.

### 4) “Not fake piecewise”: stiffness is sampled at CSF stations
The goal is NOT to create arbitrary prismatic segments with invented constant properties.
The goal is to force the solver to read the **CSF station stiffness samples** at their true locations.

A robust, standard strategy is:
- build elements between consecutive centroid stations (station i → station i+1),
- for each element use `beamIntegration UserDefined` with two endpoints:
  - at `loc=0`: section = station i
  - at `loc=1`: section = station i+1
  - weights = (0.5, 0.5)

This guarantees that the longitudinal and flexural stiffness is sampled exactly as in CSF
(at the station points), while the centroid axis geometry is also preserved.

---

## OpenSees export mapping (choose one and document it)

OpenSees `section Elastic` requires parameters (E, A, Iz, Iy, G, J).
CSF can export station data in two consistent ways:

### Mapping A (recommended): reference modulus + modular properties
- Use Convention A for `weight` (dimensionless ratio).
- Export:
  - `E = E_ref` (constant reference modulus)
  - `A, Iz, Iy, J` as **modular (weighted) properties** computed by CSF
  - `Cx, Cy` appended for centroid offsets

This keeps `E` physically meaningful (a real reference modulus) and stores heterogeneity
inside the modular section integrals.

### Mapping B: stiffness-encoded fields (E is just a carrier)
- Use Convention B for `weight` in physical units (e.g., E(z) directly).
- Export a stiffness-encoded contract, e.g.:
  - set `E = 1` and store `A = EA`, `Iz = EIz`, `Iy = EIy`
  - set `G = 1` and store `J = GJ`
- Document clearly that `A, I, J` fields are stiffness-like, not geometric areas/inertias.

Both mappings are valid. The only requirement is that your exporter and your OpenSees builder
use the same mapping consistently.



---


## Identify your Polygons (Naming is Key)
### Identifying the Target Component

To ensure the engine correctly calculates the transition along the height, **you must identify the structural component to which the material property variation law $W(z)$ will be applied.**
### Unique Identification
To avoid using confusing numerical indices for the connections (like "Pair #227"), each polygon must have a **unique name** within its section. This name acts as a human-readable label for the entire component's evolution. It makes it much easier to assign physical laws $w(z)$ to a specific structural member, such as a "Web" or "Flange," as it spans from the start to the end of the section field.


### Automatic Mapping

Example: Defining a Composite Beam

```
# Start Section (z=0)
poly_bottom_start = Polygon(
    vertices=(Pt(-10,-10), Pt(10,-10), Pt(10,0), Pt(-10,0)),
    weight=210000, # Initial E-modulus
    name="lowerpart"  # <--- THIS IS THE ID
)

# End Section (z=L)
poly_bottom_end = Polygon(
    vertices=(Pt(-15,-15), Pt(15,-15), Pt(15,0), Pt(-15,0)),
    weight=180000, # Final E-modulus
    name="lowerpart"  # <--- MUST MATCH
)

#The engine connects sections based on their **creation order**. The first polygon defined at the start automatically matches the first polygon defined at the end. 

Example
```
    s0 = Section(polygons=(poly1_start,poly2_start),z=0.0)
    s1 = Section(polygons=(poly1_end, poly2_end),z=L)
```

While using the same name for both is not a technical requirement for the geometry, it is highly recommended for clarity and to ensure the correct physical properties are tracked along the height.

```
## The Default Behavior: Linear Variation

By default, the variation of weight between the start and end sections is linear. If you do not specify a custom law, the software automatically interpolates the value based on the longitudinal position z.

---
# 📑 Deep Dive: The Logic of "Weight" (W) and Voids

In CSF, the parameter `weight` (W) is a generalized multiplier of the geometric area. Understanding its sign and scale is fundamental to obtaining correct structural results.
In this guide we use weight primarily as E-modulus (or E-ratio), but the same mechanism can represent other per-area properties.

---
### 1. Normalized Logic: The Unitary Material (W = 1.0)
When working with a single material, we use **1.0** to represent "Full Material".
* **Solid:** `weight = 1.0`
* **Void (Hole):** `weight = -1.0`

**The Superposition Principle:**
If you place a hole (W = -1.0) over a solid (W = 1.0), the sum in the overlap area is exactly **0.0**. This area will contribute zero to the Area, First Moment of Area (Statics), and Moment of Inertia.

---

### 2. Multi-Material Logic: Scaled Weights (W = 0.5)
If your section has materials with different stiffnesses, you choose a "Reference Material" (usually the one with the highest E) and scale the others accordingly.

**Example: Concrete (Reference) and Timber**
* **Concrete (Ref):** `weight = 1.0` | **Hole in Concrete:** `weight = -1.0`
* **Timber (Softer):** `weight = 0.5` | **Hole in Timber:** `weight = -0.5`

**Crucial Rule on Signs:**
A hole MUST always have the **negative sign of the material it is subtracting from**. 
* If you subtract a hole from the Timber part using `-1.0` instead of `-0.5`, you are not just making a hole; you are creating a "negative stiffness" zone that will pull the center of gravity towards the opposite side incorrectly.

---

### 3. Real Values Logic: Using Young's Modulus (E)
You can skip normalization and enter the real Elastic Modulus (e.g., in MPa).
* **Steel:** `weight = 210000`
* **Steel Hole:** `weight = -210000`

**Advanced Technique: Material Substitution**
If you have a steel reinforcement (E=210k) inside concrete (E=30k), you don't need to cut a hole in the concrete coordinates. You can simply overlay the steel polygon with:
`W_effective = E_steel - E_concrete = 180000`
The system sums 30k (concrete) + 180k (delta) and correctly obtains 210k in that region.

---

### 4. Why "Weight" and not "E"?
You might wonder: *"If it represents the Elastic Modulus, why not call it E?"*

The name **`weight`** was chosen for two scientific reasons:
1.  **Generality:** CSF is a geometric-mathematical engine. The "weight" doesn't have to be Elastic Modulus. It could represent **density** (for mass/center of gravity calculations), **thermal conductivity**, or any physical property that scales with area.
2.  **Homogenization:** In structural mechanics, we "weight" the geometry based on its relative stiffness. The term `weight` correctly describes the process of creating an **Equivalent Homogenized Section**. Calling it `E` would limit the tool to only linear-elastic structural analysis, whereas `weight` allows for broader physical applications.

---

### ⚠️ Final Summary for Voids
| Context | Solid Value | Void Value | Result in Overlap |
| :--- | :--- | :--- | :--- |
| **Normalized** | `1.0` | `-1.0` | `0.0` (Absolute Void) |
| **Half-Stiffness** | `0.5` | `-0.5` | `0.0` (Absolute Void) |
| **Real E (Concrete)** | `30000` | `-30000` | `0.0` (Absolute Void) |

**Warning:** If the sum of weights in an area is not zero, that area still possesses residual stiffness. Always verify that $W_{solid} + W_{void} = 0$.
---


###  Custom Law Syntax
To override the default behavior, use the `set_weight_laws()` method. This method accepts a list of strings where each string maps a start-section polygon to its corresponding end-section polygon using a specific formula.

**Format:**
`"StartPolygonName, EndPolygonName : <Python_Formula_Expression>"`


#### Example
```
section_field = ContinuousSectionField(section0=s0, section1=s1)

section_field.set_weight_laws([
    "lowerpart,lowerpart : w0 * np.exp(-z / L)",  # Exponential decay over the member length
    "otherpart,otherpart : w0 / 100",
])
```

## Available Variables (What you can use in formulas)

### 📊 Weight Law Variables Reference

| Variable | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`z`** | Real position from start to end   | `w0 * (1 + 0.2 * z / L)` |
| **`w0`** | Weight (stiffness) at the start section ($z=0$) | `w0 * 1.5` |
| **`w1`** | Weight (stiffness) at the end section ($z=L$) | `w1 / 2` |
| **`L`** | Total physical length of the member | `w0 + (z * L * 0.01)` |
| **`np`** | Access to NumPy | `e.g., np.sin, np.exp, np.sqrt.` |

---

### 📏 Geometric & Data Functions

| Function | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`d(i, j)`** | Distance between vertex $i$ and $j$ at **current** $z$ | `w0 * d(1, 2)` |
| **`d0(i, j)`** | Distance between vertex $i$ and $j$ at **start** ($z=0$) | `w0 * (d(1,2) / d0(1,2))` |
| **`d1(i, j)`** | Distance between vertex $i$ and $j$ at **end** ($z=L$) | `w1 * (d(1,2) / d1(1,2))` |
| **`E_lookup(file)`** | Interpolated value from an external text file | `E_lookup('stiffness.txt')` |

### ⚠️ Vertex Indexing Rule
When using the distance function `d(i, j)` in your weight laws:
* **1-Based Numbering**: Vertex indices start at **1**, not 0.
* **The first point** is `1`, the **second point** is `2`, etc.
* **Pro Tip**: If you use `0` as an index, the calculation will fail.

### Data-Driven Modeling: E_lookup data from external text file 

If you have experimental data (e.g., from a sensor or a thermal analysis), put it in a text file ,example stiffness.txt:
The first column in the lookup file is the physical coordinate z (same units as the model, from 0 to L).
```
# Z-coord   Value
0.0  210000
1.0  195000
5.0  150000
```

E_lookup(file) returns the value interpolated at the current longitudinal coordinate (z) for the active integration point.

---
### 3. Mathematical Operations with `E_lookup`
The `E_lookup('file.txt')` function is designed to return a **numeric value** (float) based on an external data file. Because it returns a number, you can perform any standard NumPy mathematical operation on it.

### 🛡️ Numerical Robustness & Validation Rules

When defining a custom law string, the mathematical engine enforces strict validation to ensure the integrity of the structural model. Your formulas must adhere to the following constraints:

| Requirement | Description |
| :--- | :--- |
| **Return Type** | Must be a **float**. Strings or complex numbers will trigger an error. |
| **Physical Validity** | For solids, $E(z) > 0$. Use `np.maximum(min_val, ...)` to avoid $0$ or negative results. |
| **Safety Handling** | Any law producing `NaN` or `inf` (e.g., division by zero) triggers an immediate traceback. |

> **Warning on Holes:** If your law is for a hole, the result must be **negative**. 
> Example for a dynamic hole: `"void,void : -1.0 * E_lookup('degradation.txt')"`

#### 🛠️ Best Practice: Clamping and Safety
To prevent unphysical results (like a stiffness dropping to zero or becoming negative due to extreme inputs), it is highly recommended to use a **clamping** logic. This ensures a minimum residual stiffness ($E_{min}$).

**Example of a robust law with clamping:**
```python
# Ensures the weight never drops below 1% of the initial value (w0)
section_field.set_weight_laws([
    "web,web : np.maximum(w0 * 0.01, E_lookup('experimental_data.txt'))",
])

```
#### **Common Use Cases:**
* **Scaling:** Adjust external data by the initial section weight (`w0`).
* **Non-linear mapping:** Apply power laws or trigonometric functions to the lookup value.
* **Geometric Coupling:** Multiply lookup data by section properties like distance `d(i,j)`.

**Example Implementation:**
```python
section_field.set_weight_laws([
    # Example 1: Quadratic transition for the upper part
    "upperpart,upperpart : w0 + (w1 - w0) * np.power(z / L, 2)",
    
    # Example 2: External data scaled by the initial weight (w0)
    # Useful for applying degradation factors from experimental data
    "lowerpart,lowerpart : E_lookup('material_data.txt') * w0"
])
```
## 🟢 Meet the "CSF Weight Law Inspector" 

Defining mathematical laws for structural members shouldn't feel like "guessing and hoping." To make your workflow smoother and error-free, we've introduced the **Safe Evaluation Engine**.

### 🚀 Why it is important to use it
Let’s be honest: writing Python formulas inside strings can be tricky. A missing bracket or a typo in a filename usually results in a scary, 50-line Python crash. **Not anymore.**

Our new **Inspector** acts as a professional co-pilot that talks back to you:

* **Proactive File Checks**: If you use `E_lookup('data.txt')`, the engine checks if the file exists *before* running the calculation. If it’s missing, it tells you exactly where it should be.
* **Beautiful Diagnostics**: Instead of messy code errors, you get a clean, high-contrast terminal report showing exactly what’s happening.
* **Physics-Aware**: It doesn't just check math; it checks reality. If your formula results in negative weight or stiffness, it flags a `WARNING` so you can verify your logic.
* **Friendly Advice**: Every error comes with an **ACTION** suggestion. It tells you how to fix the problem (e.g., "Add a small epsilon to avoid division by zero").

### 📊 How it looks in your terminal

When something goes wrong, you don't get a crash. You get this:

```text
════════════════════════════════════════════════════════════════════════
                🔴  CSF WEIGHT LAW INSPECTOR  |  ERROR
════════════════════════════════════════════════════════════════════════
  FORMULA:     np.maximum(w0 * 0.01, E_lookup('experimental_data.txt'))
  POSITION Z:  50.0000
------------------------------------------------------------------------
  RESULT W:    ❌ [ABORTED]
------------------------------------------------------------------------
  CATEGORY:    File System Error
  DETAIL:      Required lookup file 'experimental_data.txt' is missing.
  ADVICE:      Ensure the file exists in your current working directory.
------------------------------------------------------------------------
                                          Validated on: 2026-01-09 10:45
════════════════════════════════════════════════════════════════════════
```
---
### 🛠 How to Use It

The beauty of the **CSF Weight Law Inspector** is its simplicity: you don't need to change how you work.

**1. Define your laws as usual**
Simply pass your formulas as strings. Whether you are using basic math, NumPy functions, or external data lookups, the system is ready:

```python
# Example: Using a mix of native variables and external data
# Mock data for demonstration

formula_test = "np.maximum(w0 * 0.01, E_lookup('experimental_data.txt'))"

# Instead of printing the raw tuple, we use the printer:
weight_value, report_data = safe_evaluate_weight(formula_test, p_start, p_end, 10.0, 0.5)

# CALL THE PRINTER HERE
print_evaluation_report(weight_value, report_data)
```

## FAQ — “Is CSF + OpenSees just a piecewise-prismatic discretization?”

**Short answer:** it uses multiple OpenSees elements, but it is **not** the traditional *piecewise-prismatic* approximation.

### What “piecewise-prismatic” means (the classical approximation)
In a classical stepped model you:
- choose **how many segments** to use,
- choose **where** to sample properties,
- assign each segment a **constant** (or arbitrarily averaged) section,
- obtain results that can change significantly with the user’s discretization choices.

That *user-dependent sampling and averaging* is the key weakness of piecewise-prismatic modeling.

### What CSF actually does
CSF defines a **continuous stiffness/geometry field** along the member (ruled surfaces + weight laws).  
The exported `geometry.tcl` is a **list of station snapshots**, each one computed from the continuous field (no “invented” prismatic properties).

In the OpenSees builder:
- stations are placed using **Gauss–Lobatto** locations (endpoints included),
- each station has its own section state (A, I, centroid offsets, …),
- OpenSees is forced to read these station states **at the correct locations**.

So the OpenSees model is best described as:
> **numerical quadrature / collocation of a continuous stiffness field**, not user-chosen stepped prismatic segments.

### Why do we still create multiple OpenSees elements?
Because of a practical OpenSees limitation: the standard integration commands are not designed to consume an arbitrary list of different section tags inside a single element without ambiguity.  
Using a chain of elements + `beamIntegration UserDefined` is the **enforcement mechanism** that makes OpenSees sample the CSF stations correctly.

### The key difference (what makes it “not piecewise”)
- **No arbitrary averaging:** section properties are not collapsed into equivalent prismatic blocks.
- **Controlled sampling:** the sampling locations are prescribed by the Gauss–Lobatto rule.
- **Exact end conditions:** Lobatto stations include the endpoints, so support and tip conditions coincide with the real member ends.
- **Field fidelity:** increasing the number of stations refines the **quadrature of the same continuous field**, rather than changing a user-defined stepped approximation.

### One-sentence reply (for discussions)
> “Yes, the OpenSees realization uses multiple elements, but it is not a piecewise-prismatic approximation: the element chain is only a numerical device to enforce Gauss–Lobatto sampling of the continuous CSF stiffness field (including endpoints), avoiding user-dependent averaging choices.”

