#  🛠  ContinuousSectionField (CSF) | Custom Weight Laws User Guide

This document provides the technical specifications for implementing and using **Custom Weight Laws** to define the variation of the Elastic Modulus ratio (`weight`) along a structural member.


> **Important — what is `weight`?**  
> In CSF, `weight` is a **scalar field** used to scale section properties (a generalized multiplier of the geometric area).  
> It can represent an **E-modulus ratio** (dimensionless) *or* the **Young’s modulus E** (e.g., MPa).  
> The only requirement is that your formulas and lookup data follow a **consistent convention**.

---


### Identify your Polygons (Naming is Key)

To apply a law, your polygons must have a name. This name acts as a "link" between the start and end sections.

#### The Same-Element Requirement
* **Correspondence:** The name must belong to the **same sub-element**. You are describing the evolution of one physical component (e.g., the "Web") as it travels from $z=0$ to $z=L$.
* **Continuity:** If a name exists at the start but not at the end, the "interpolation bridge" is broken. The engine cannot calculate intermediate properties because the **chain of continuity** is interrupted.
* **Case Sensitivity:** `Web` is not the same as `web`. A naming mismatch will cause the element to "vanish," leading to calculation errors.

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


