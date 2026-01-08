#  🛠  ContinuousSectionField (CSF) | Custom Weight Laws User Guide

This document provides the technical specifications for implementing and using **Custom Weight Laws** to define the variation of the Elastic Modulus (`weight`) along a structural member.



### Identify your Polygons (Naming is Key)

To apply a law, your polygons must have a name. This name acts as a "link" between the start and end sections.

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

###  Custom Law Syntax
To override the default behavior, use the `set_weight_laws()` method. This method accepts a list of strings where each string maps a start-section polygon to its corresponding end-section polygon using a specific formula.

**Format:**
`"StartPolygonName, EndPolygonName : <Python_Formula_Expression>"`


#### Example
```
section_field = ContinuousSectionField(section0=s0, section1=s1)

section_field.set_weight_laws([
    "lowerpart,lowerpart : w0 * np.exp(-z)" # Exponential decay
    "otherpart,otherpart : w0 /100"
])
```

## Available Variables (What you can use in formulas)

### 📊 Weight Law Variables Reference

| Variable | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`z`** | Real position from start to end   | `w0 * (1 + z)` |
| **`w0`** | Weight (stiffness) at the start section ($z=0$) | `w0 * 1.5` |
| **`w1`** | Weight (stiffness) at the end section ($z=L$) | `w1 / 2` |
| **`L`** | Total physical length of the member | `w0 + (z * L * 0.01)` |
| **`t`** | Alias for `z` (interpolation parameter) | `w0 + (w1 - w0) * t` |
| **`np`** | Access to NumPy | `e.g., np.sin, np.exp, np.sqrt.` |

---

### 📏 Geometric & Data Functions

| Function | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`d(i, j)`** | Distance between vertex $i$ and $j$ at **current** $z$ | `w0 * d(1, 2)` |
| **`d0(i, j)`** | Distance between vertex $i$ and $j$ at **start** ($z=0$) | `w0 * (d(1,2) / d0(1,2))` |
| **`d1(i, j)`** | Distance between vertex $i$ and $j$ at **end** ($z=L$) | `w1 * (d(1,2) / d1(1,2))` |
| **`E_lookup(file)`** | Interpolated value from an external text file | `E_lookup('stiffness.txt')` |


### Data-Driven Modeling: E_lookup data from external text file 

If you have experimental data (e.g., from a sensor or a thermal analysis), put it in a text file ,example stiffness.txt:

```
# Z-coord   Value
0.0         210000
0.5         195000
1.0         150000
```


---
### 3. Mathematical Operations with `E_lookup`
The `E_lookup('file.txt')` function is designed to return a **numeric value** (float) based on an external data file. Because it returns a number, you can perform any standard NumPy mathematical operation on it.

#### **Common Use Cases:**
* **Scaling:** Adjust external data by the initial section weight (`w0`).
* **Non-linear mapping:** Apply power laws or trigonometric functions to the lookup value.
* **Geometric Coupling:** Multiply lookup data by section properties like distance `d(i,j)`.

**Example Implementation:**
```python
field.set_weight_laws([
    # Example 1: Quadratic transition for the upper part
    "upperpart,upperpart : w0 + (w1 - w0) * np.power(z, 2)",
    
    # Example 2: External data scaled by the initial weight (w0)
    # Useful for applying degradation factors from experimental data
    "lowerpart,lowerpart : E_lookup('material_data.txt') * w0"
])
```

---

