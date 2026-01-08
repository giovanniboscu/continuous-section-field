# ContinuousSectionField (CSF) User Guide

The **Continuous Section Field (CSF)** framework provides a continuous description of non-prismatic and multi-material beam members by generating longitudinally varying cross-section properties without using piecewise-prismatic discretization.

---

## Advanced Material Variation: Custom Weight Laws

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

### The set_weight_laws Syntax

The law is a string that connects the start polygon to the end polygon and defines the math.


- Syntax: "Polygon StartName, Polygon  EndName : Formula"

#### Example
```
section_field = ContinuousSectionField(section0=s0, section1=s1)

section_field.set_weight_laws([
    "lowerpart,lowerpart : w0 * np.exp(-z)" # Exponential decay
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

---

### 📏 Geometric & Data Functions

| Function | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`d(i, j)`** | Distance between vertex $i$ and $j$ at **current** $z$ | `w0 * d(1, 2)` |
| **`d0(i, j)`** | Distance between vertex $i$ and $j$ at **start** ($z=0$) | `w0 * (d(1,2) / d0(1,2))` |
| **`d1(i, j)`** | Distance between vertex $i$ and $j$ at **end** ($z=L$) | `w1 * (d(1,2) / d1(1,2))` |
| **`E_lookup(file)`** | Interpolated value from an external text file | `E_lookup('stiffness.txt')` |


### Data-Driven Modeling: E_lookup

If you have experimental data (e.g., from a sensor or a thermal analysis), put it in a text file ,example stiffness.txt:

```
# Z-coord   Value
0.0         210000
0.5         195000
1.0         150000
```

## The Default Behavior: Linear Variation

By default, the variation of weight between the start and end sections is linear. If you do not specify a custom law, the software automatically interpolates the value based on the longitudinal position z.

---

## Cross-Section Homogenization

Each cross-section may include multiple material patches.  
For each patch, a reference elastic modulus is defined.

An elastic homogenization factor is associated with each patch.  
This factor scales the contribution of that patch to the equivalent section properties.

Multiple homogenization factors may coexist within the same cross-section, each acting on a different portion of the section.

---

## Longitudinal Variability

Homogenization factors may vary along the beam axis.

Their variation is:
- not required to be linear
- defined by the user
- independent for each material patch

They can be specified either through tabulated data or through analytical functions supported by the Python environment.

CSF evaluates these factors continuously along the beam axis and applies them locally, section by section, during all internal computations.

---

## Equivalent Section Properties

Using the homogenized material layout, CSF computes continuous sectional properties such as:

- Cross-section area
- Second moments of area
- Torsional constant
- Axial, bending, and torsional stiffness quantities

All properties can be visualized, exported as tables, or used as input for structural analysis.

---

## Workflow

CSF can be used in two complementary ways:

### File-Based Workflow
- Geometry definition file
- Output and processing definition file
- Automatic generation of section properties, plots, and solver-ready models

### Python API
- Full control over geometry and homogenization
- User-defined functions for longitudinal variation
- Advanced scripting and customization

---

## Documentation

Additional documentation is available in the `docs/` directory:

- `homogenization.md` — homogenization concepts and assumptions
- `geometry.md` — geometric modeling
- `opensees_export.md` — solver integration

---

## Status

CSF is under active development.  
The API and file formats may evolve as new features are introduced.
