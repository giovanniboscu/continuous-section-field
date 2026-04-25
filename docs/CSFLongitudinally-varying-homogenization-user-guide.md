#  🛠  ContinuousSectionField (CSF) - Custom Weight Laws
> **Before you start**  
> This guide builds on the core CSF concepts - geometric pairing and polygon naming - introduced in the [CSF Fundamentals](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/CSF_Fundamentals.md).  
> A quick read of that page is enough to get the most out of this guide.  
> The purpose here is only to make the syntax of custom weight laws easy to read and use.
[04_plotting_weight](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/programmer-guide/04_plotting_weight.md)

A Custom Weight Law defines how the weight, i.e. the Elastic Modulus ratio, varies along `z` for a specific structural component of the member.

For example, the following law assigns a smooth variation to the component defined between two polygons, both named "lowerpart", changing its weight from `w0` at the base to `w1` at the top.

**API version**

```python
section_field.set_weight_laws([
    "lowerpart,lowerpart: w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))",
])
```

The same kind of law can also be defined in an action YAML file. For example:

```yaml
weight_laws:
  # parabolic increase: 72% at base (z=0), full section at top (z=10)
  - 'startsection,endsection: 1.0 - 0.28 * (1 - (z / 10.0)**2)'
```

Before proceeding, it is necessary to understand how polygons are constructed and identified, because the specified mathematical variation is defined between them.

In practice, CSF provides two ways to define  **$w(z)$**:
- through the API
- through the action YAML syntax

## Identifying the Target Component


In practice, it is very simple: you just draw the polygons and keep them in the same order in `S0` and `S1`.

To avoid relying on unclear numerical connections such as “Pair #227,” each polygon should have its own unique name within the section. The name is used by the user to explicitly associate the two polygons with the weight law. If a name is mistyped or missing, the engine will catch it immediately. For example, a polygon named `flange` can represent the flange region, while another named `web` can represent the web region. Using the same names in both sections is not required for the geometry itself.


In CSF, **`weight`**, **$W$**, and **$w(z)$** refer to the same concept.



### Polygon Pairing by Creation Order

Defining a Composite Beam

***Program format***

```
    poly_top_start = Polygon(
        vertices=(
            Pt(-b/2,  0.0), 
            Pt( b/2,  0.0),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1,# <-- Weight
        name="upperpart", 
    )


    poly_bottom_start = Polygon(
        vertices=(
            Pt(-b/2, -h/2), 
            Pt( b/2, -h/2),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=1,# <-- Weight
        name="lowerpart", 
    )


    poly_top_end = Polygon(
        vertices=(
            Pt(-b/2,  0.0), 
            Pt( b/2,  0.0),
            Pt( b/2,  h/2),
            Pt(-b/2,  h/2),
        ),
        weight=1, #  <-- Weight
        name="upperpart",
    )

    poly_bottom_end = Polygon(
        vertices=(
            Pt(-b/2, -h/2), 
            Pt( b/2, -h/2),
            Pt( b/2,  0.0),
            Pt(-b/2,  0.0),
        ),
        weight=0.9,# <-- Weight changed
        name="lowerpart",
    )
    # Define start/end sections and create the continuous field.

    # --- SECTION AND FIELD DEFINITION ---
    L = 10.0
    # Order matters: poly_bottom_start pairs with poly_bottom_end,
    # and poly_top_start pairs with poly_top_end,
    # because they appear in the same position in their respective sections.

    s0 = Section(polygons=(poly_bottom_start, poly_top_start), z=0.0)
    s1 = Section(polygons=(poly_bottom_end,  poly_top_end),  z=L)

    section_field = ContinuousSectionField(section0=s0, section1=s1)

    section_field.set_weight_laws([
        "lowerpart,lowerpart: w0 + (w1 - w0) * 0.5 * (1 - np.cos(np.pi * z / L))",
    ])


```

**Order matters**  

The geometric pairing between polygons in `S0` and `S1` is determined by their creation order, not by their names.

In this example, `poly_bottom_start` is geometrically paired with `poly_bottom_end`, and `poly_top_start` with `poly_top_end`, because they occupy the same position in the two polygon lists.

Consequently, when you later define a weight law using polygon names (names which are unique by section), CSF verifies that the named polygons occupy the same position in both lists. If they do not, the model is rejected at the input stage


> **Polygon**  
> For the user, polygon names are the way to refer to components when defining weight laws `w(z)`.  
> Internally, the geometric pairing between `S0` and `S1` is established by polygon order.  
> In a consistent model, these two refer to the same polygonal component.
>
> **Note**  
> Mismatched polygon names are not accepted at input stage.  
> If a name used in a weight law does not correspond to a valid polygon pairing in the model, the input is rejected.
>
***yaml format***
```
CSF:
  sections:
    S0:
      z: 0.0

      polygons:

        pol:
          weight: 1.0
          vertices:
            - [-0.25, -0.5]
            - [ 0.25, -0.5]
            - [ 0.25,  0.5]
            - [-0.25,  0.5]

    S1:
      z: 30.0

      polygons:
        pol:
          weight: 1.0
          vertices:
            - [-0.5, -0.1]
            - [ 0.5, -0.1]
            - [ 0.5,  0.1]
            - [-0.5,  0.1]

  weight_laws:
    - 'pol,pol: 1.0 - 0.40*np.exp(-((z-5.0)**2)/(2*(2.0**2)))'

```

> **Note**  
> Creation order defines the **geometric pairing**. Polygon names are used to **assign and track physical laws** (e.g., `W(z)`) along the section field.
> The engine connects sections based on their **creation order**. The first polygon defined at the start automatically matches the first polygon defined at the end.



Example
```
    # --- SECTION AND FIELD DEFINITION ---
    L = 10.0
    s0 = Section(polygons=(poly_bottom_start, poly_top_start), z=0.0)
    s1 = Section(polygons=(poly_bottom_end,  poly_top_end),  z=L)


```
---

## The Default Behavior: Linear Variation

By default, the variation of weight between the start and end sections is linear. If you do not specify a custom law, the software automatically interpolates the value based on the longitudinal position z.

# What is `weight`?

> In CSF, `weight` is a **scalar field** used to scale section properties (a generalized multiplier of the geometric area).  
> It can represent an **E-modulus ratio** (dimensionless) *or* the **Young’s modulus E** (e.g., MPa).  
> The only requirement is that your formulas and lookup data follow a **consistent convention**.


**Operational meaning in CSF**

 In CSF, `weight` is a user-defined **scalar field** $W(z)$ attached to each **section patch** (polygonal sub-domain), with values defined along $z$ and evaluated consistently during section-property assembly.

 CSF uses it as a **multiplier inside area integrals**, i.e. it “weights” geometry to produce
 an **equivalent homogenized section**.

 **This tool is unit-system agnostic.**  
 OpenSees is also unitless: you may use mm–N–MPa or m–N–Pa, etc.  
 The only hard rule is: **all inputs must follow one consistent unit convention**.

 ### Two valid conventions for `weight`

 CSF supports two different (but equally valid) interpretations. You must pick one and
 keep it consistent across your workflow and exports:
 
---
### 1. Normalized Logic: The Unitary Material (W = 1.0)
When working with a single material, we use **1.0** to represent "Full Material".
* **Solid:** `weight = 1.0`
* **Void (Hole):** `weight = 0.0`

**Apparent Superposition (user perspective):**
If you place a void polygon (`W = 0.0`) over a solid region (`W = 1.0`), CSF automatically treats the overlap as a true void in the section integrals.

---

###  Multi-Material Logic: Scaled Weights (Example Only)

> **This section is an illustrative example, not a mandatory rule.**  
> The numeric values below are chosen only to demonstrate the concept of using a reference material and relative scaling.

If your section includes materials with different stiffness (or other properties), you may define a **reference material** (often the one with the highest $E$) and assign **relative** `weight` values to the other patches accordingly.

**Example: Concrete (Reference) and Timber**
- **Concrete (Ref):** `weight = 1.0` | **Void within Concrete:** `weight = 0.0`
- **Timber (softer):** `weight = 0.5` | **Void within Timber:** `weight = 0.0`


A void is always declared as **zero**. CSF performs the internal bookkeeping needed to remove the underlying material contribution in the overlap.

---

### Example: Embedded reinforcement (automatic effective property)

If a steel reinforcement (**E = 210 000**) is embedded inside concrete (**E = 30 000**), the user does **not** need to modify or subtract the concrete geometry.

The reinforcement is defined using its **absolute** material property:

- `E_steel = 210 000`

CSF internally derives the effective contribution:
- `W_effective = E_steel − E_concrete = 180 000`

The user only specifies the reinforcement property.  
The subtraction of the parent material is handled internally by CSF.

> **Principle**  
> All polygon properties are defined as **absolute values**.  
> Effective contributions are derived automatically from containment relationships.



## Nesting Hierarchy and Effective Weight

When polygons are nested (one polygon inside another), CSF automatically detects the immediate container of each polygon.

The rule is direct and physically consistent: each polygon subtracts its weight from its immediate container-the material it directly displaces. Ancestors higher in the nesting chain remain unaffected, exactly as a steel bar displaces only the concrete immediately surrounding it, not the formwork outside.

> *"Like diving into a swimming pool: you displace only the water in the pool, not the lawn around it nor the hill underneath."*

This means:
- A void (`weight = 0.0`) removes material only from its direct parent.
- An embedded reinforcement (`weight = 210000`) inside concrete (`weight = 30000`) contributes `210000 - 30000 = 180000` to the homogenized section.
- Three or more levels of nesting work the same way: each level subtracts from its immediate parent. No special cases, no exceptions.

CSF handles this automatically. No manual subtraction or containment correction is required from the user.

### Example: embedded steel reinforcement in concrete

| Polygon | Absolute weight W | Container | W_eff |
|---------|-------------------|-----------|-------|
| Concrete | 30 000 | none (root) | 30 000 |
| Steel bar | 210 000 | Concrete | 210 000 − 30 000 = 180 000 |

The user declares only the absolute material property of each polygon. The effective contribution is derived automatically from the containment relationship.

This means the effective contribution of an inclusion is always computed relative to its immediate parent. Ancestors higher in the hierarchy are already correctly represented by their own material properties and nested contents.

>**Note on identical nested polygons:**  
>If two polygons have identical geometry and one is treated as nested inside the other, CSF assigns the immediate container according to polygon order. In this case, the first valid polygon in the section order acts as the container, and the effective weight is computed relative to it:

```text
W_eff = W_child - W_parent
---

### Why "Weight" and not "E"?
You might wonder: *"If it represents the Elastic Modulus, why not call it E?"*

The name **`weight`** was chosen for two scientific reasons:
1.  **Generality:** CSF is a geometric-mathematical engine. The "weight" doesn't have to be Elastic Modulus. It could represent **density** (for mass/center of gravity calculations), **thermal conductivity**, or any physical property that scales with area.
2.  **Homogenization:** In structural mechanics, we "weight" the geometry based on its relative stiffness. The term `weight` correctly describes the process of creating an **Equivalent Homogenized Section**. Calling it `E` would limit the tool to only linear-elastic structural analysis, whereas `weight` allows for broader physical applications.

---

### Final Summary for Voids

A void must be declared with `weight = 0.0`. If you use a non-zero weight, that region will retain residual stiffness/property.

---


##  Custom Law Syntax
To override the default behavior, use the `set_weight_laws()` method. This method accepts a list of strings where each string maps a start-section polygon to its corresponding end-section polygon using a specific formula.

**Format:**
`"StartPolygonName,EndPolygonName : <Python_Formula_Expression>"`


#### Example
```
section_field = ContinuousSectionField(section0=s0, section1=s1)

section_field.set_weight_laws([
    "upperpart,upperpart : w0 * np.exp(-z / L)",  # Exponential decay over the member length
    "lowerpart,lowerpart : w0 / 100",
])
```

## Available Variables (What you can use in formulas)

### 📊 Weight Law Variables Reference


| Variable | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`z`** | Physical coordinate along the member (from start to end) | `w0 * (1 + 0.2 * z / L)` |
| **`t`** | Normalized coordinate in `[0, 1]` | `w0 + (w1 - w0) * t` |
| **`w0`** | Weight at the start section (`z = z0`) | `w0 * 1.5` |
| **`w1`** | Weight at the end section (`z = z1`) | `w1 / 2` |
| **`L`** | Total physical length of the member | `w0 + (z / L) * 0.1` |
| **`np`** | NumPy namespace | `np.sin(...)`, `np.exp(...)`, `np.sqrt(...)` |


---

### 📏 Geometric & Data Functions

| Function | Meaning | Example Law Expression |
| :--- | :--- | :--- |
| **`d(i, j)`** | Distance between vertex $i$ and $j$ at **current** $z$ | `w0 * d(1, 2)` |
| **`d0(i, j)`** | Distance between vertex $i$ and $j$ at **start** ($z=0$) | `w0 * (d(1,2) / d0(1,2))` |
| **`d1(i, j)`** | Distance between vertex $i$ and $j$ at **end** ($z=L$) | `w1 * (d(1,2) / d1(1,2))` |
| **`E_lookup(file)`** | Interpolated value from an external text file | `E_lookup('stiffness.txt')` |
| **`T_lookup(file)`** |  Interpolated value from an external text file, evaluated against normalized `t` in `[0, 1]` | `T_lookup('t_stiffness.txt')` |

### ⚠️ Vertex Indexing Rule
When using the distance function `d(i, j)` in your weight laws:
* **0-Based Numbering**: Vertex indices start at **0**


### Data-Driven Modeling: E_lookup data from external text file 

If you have experimental data (e.g., from a sensor or a thermal analysis), put it in a text file, for example `stiffness.txt`:
The first column in the lookup file is the physical coordinate z (same units as the model, from 0 to L). 
Intermediate values are interpolated linearly.
```
# Z-coord   Value
0.0  210000
1.0  195000
5.0  150000
```

E_lookup(file) returns the value interpolated at the current longitudinal coordinate (z) for the active integration point.
### Data-Driven Modeling: `T_lookup` data from external text file

If you want to drive the law using a **normalized coordinate**, you can use `T_lookup(file)`.

In this case, the first column in the lookup file is the normalized coordinate `t` in `[0, 1]`, not the physical coordinate `z`.

Intermediate values are interpolated linearly.

```text
# t   Value
0.0   210000
0.2   205000
0.5   180000
1.0   150000
```

`T_lookup(file)` returns the value interpolated at the current normalized coordinate `t` for the active integration point.

---

### 🛡️ Numerical Robustness & Validation Rules

When defining a custom law string, the mathematical engine enforces strict validation to ensure the integrity of the structural model. Your formulas must adhere to the following constraints:

| Requirement | Description |
| :--- | :--- |
| **Return Type** | Must be a **float**. Strings or complex numbers will trigger an error. |
| **Physical Validity** | For solids, $E(z) > 0$. Use `np.maximum(min_val, ...)` to avoid $0$ or negative results. |
| **Safety Handling** | Any law producing `NaN` or `inf` (e.g., division by zero) triggers an immediate traceback. |

> **Warning on Voids/Holes:** If your law is for a void, the result should be **0.0** (not negative).  
> Example: `"void,void : 0.0"`

> **Negative weights**
>  
> Negative values are **not forbidden** by CSF.  
> They are allowed but require **explicit user awareness**, as they may represent
> subtractive or corrective modeling choices rather than standard physical properties.
>  
> CSF issues a **warning** whenever negative weights are detected, but the computation
> proceeds without modification.



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
##  "CSF Weight Law Inspector" 

Defining mathematical laws for structural members shouldn't feel like "guessing and hoping." To make your workflow smoother and error-free, we've introduced the **Safe Evaluation Engine**.

### 🚀 Why it is important to use it
Let’s be honest: writing Python formulas inside strings can be tricky. A missing bracket or a typo in a filename usually results in a scary, 50-line Python crash. **Not anymore.**

Our new **Inspector** acts as a professional co-pilot that talks back to you:

* **Proactive File Checks**: If you use `E_lookup('data.txt')`, the engine checks if the file exists *before* running the calculation. If it’s missing, it tells you exactly where it should be.
* **Diagnostics**: Instead of messy code errors, you get a clean, high-contrast terminal report showing exactly what’s happening.
* **Physics-Aware**: It doesn't just check math; it checks reality. If your formula results in negative weight or stiffness, it flags a `WARNING` so you can verify your logic.
* **Friendly Advice**: Every error comes with an **ACTION** suggestion. It tells you how to fix the problem (e.g., "Add a small epsilon to avoid division by zero").

### 📊 How it looks in your terminal

When something goes wrong, you don't get a crash. You get this:

```text
════════════════════════════════════════════════════════════════════════
                  CSF WEIGHT LAW INSPECTOR  |  ERROR
════════════════════════════════════════════════════════════════════════
  FORMULA:     np.maximum(w0 * 0.01, E_lookup('experimental_data.txt'))
  POSITION Z:  50.0000
------------------------------------------------------------------------
  RESULT W:     [ABORTED]
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
zrel=104
w = safe_evaluate_weight_zrelative(formula, p0=poly_start,p1=poly_end, z0=100,z1=110 , z=zrel,print=True)

  

# CALL THE PRINTER HERE
print_evaluation_report(weight_value, report_data)
```

full example see
[csf_weights_lab.py](https://github.com/giovanniboscu/continuous-section-field/blob/main/example/csf_weights_lab.py)


### CSF Weight Law Inspector

The **CSF Weight Law Inspector** is available as an action within the CSF framework.

It allows direct inspection and verification of longitudinal weight laws `w(z)` assigned to polygons, enabling validation of their definition and behavior along the structure.

### Availability

The action is documented and accessible at the following link:

```
weight_lab_zrelative
```
👉 https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_actions.md























