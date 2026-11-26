# CSF-PyCBA integration: from a YAML model to a beam analysis

A practical, step-by-step guide using the existing `combined_variation` cantilever example.

This guide is intended for a PyCBA user who has never used CSF or written a YAML file. It explains how the physical member is defined, how Python reads that definition, and how the resulting continuous flexural rigidity is supplied to PyCBA. It uses the existing Case D without changing its input data, numerical settings or validation results. Familiarity with elementary beam analysis and basic Python is assumed; knowledge of the internal implementation of either library is not required.

> The central idea is to define the physical member in CSF and let PyCBA perform the structural analysis. The two libraries communicate through a Python function `EI(x)`.

For the derivations and numerical comparisons, see [THEORY.md](THEORY.md) and [VALIDATION.md](VALIDATION.md). This guide focuses on how to use the interfaces rather than on deriving the beam formulation.

>[← Back to the tapered cantilever tutorial](README.md)
>
>The main tutorial provides an overview of the CSF–PyCBA
>integration, including the benchmark configurations, analytical
>reference solutions, numerical results, convergence checks,
>and links to the theoretical and validation documentation.

## 1. Start from the physical member

The selected example is a rectangular cantilever whose depth and Young's modulus both decrease linearly from the fixed end to the free end. The width is constant.

| Physical quantity | Fixed end (S0) | Free end (S1) |
|---|---:|---:|
| Longitudinal position | 0 mm | 5000 mm |
| Width | 200 mm | 200 mm |
| Depth | 500 mm | 250 mm |
| Young's modulus | 210000 MPa | 105000 MPa |

The member is clamped at its fixed end and carries a downward point load of 10000 N at its free end. The structural model is linear elastic and Euler-Bernoulli, with no shear deformation or self-weight. The material is uniform within each individual cross-section, but its modulus changes along the member.

```text
       fixed end S0                            free end S1
       z = 0                                    z = 5000 mm
       ||\
       || \_______________________________________
       ||                                         |  ↓ P
       || /---------------------------------------
       ||/
       h = 500 mm                               h = 250 mm
       E = 210000 MPa                           E = 105000 MPa
                         b = 200 mm
```

*Schematic only; not to scale. The actual taper is symmetric about the longitudinal reference axis.*

### 1.1 Coordinate convention and units

CSF and PyCBA use different names for the longitudinal coordinate. In this example the origins coincide at the clamp.

| Meaning | CSF | PyCBA |
|---|---|---|
| Longitudinal position | `z` | `x` |
| Transverse width coordinate | `x` in a section vertex | — |
| Transverse depth coordinate | `y` in a section vertex | — |

The flexural rigidity needed here is for bending about the CSF transverse x-axis. Therefore `Ix` is the sectional second moment of area used by the adapter. The CSF vertex coordinate `x` is **not** the longitudinal coordinate used by PyCBA.

Use a consistent N-mm unit system throughout: lengths in mm, forces in N, Young's modulus in MPa (N/mm²), second moments in mm⁴ and flexural rigidity in N·mm². Do not enter dimensions in metres while retaining the modulus and load in these units.

### 1.2 What belongs to each library?

| Information | Where it is defined or calculated |
|---|---|
| Section geometry at the ends and material weight law | CSF model YAML |
| Section geometry and properties at intermediate positions | CSF API |
| Reference Young's modulus, member length and load magnitude | Python benchmark inputs |
| Clamp, point-load location and beam discretisation | PyCBA analysis adapter |
| Polynomial representation of the variable rigidity and structural solution | PyCBA |

There are no support conditions or loads in the CSF geometry YAML. The same physical description can be used in another analysis without encoding its mechanical formulation in the geometry file.

## 2. Create the CSF YAML model

### 2.1 What is a YAML file?

YAML is a plain-text format for writing structured input data. In this example it is used instead of constructing the geometry directly in Python. You can create or edit a `.yaml` file with an ordinary text editor or an editor such as VS Code. It is not a Python script and is not executed as one.

Only a few syntax conventions are needed for this model:

| Syntax | Meaning in this file |
|---|---|
| `z: 0.0` | A named field (`z`) with a numerical value |
| `sections:` | A field containing nested data |
| Indentation | Indicates which data belong to which parent; use spaces, not tabs |
| `- name: solid` | Begins an item in the list of polygons |
| `- [-100.0, -250.0]` | One entry in the list of vertex coordinate pairs |
| `"..."` | A text string; keep the quotes around the weight law |
| `# comment` | Optional explanatory text ignored by the YAML parser |

YAML defines how the information is written. CSF defines which field names and data structures it expects. For instance, `sections`, `S0`, `S1` and `polygons` have specific meanings in the CSF model format; they are not special keywords of YAML itself.

### 2.2 Define the two reference sections

Start with the top-level key `CSF` and its `sections` block. The two reference sections are `S0` and `S1`, positioned at `z: 0.0` and `z: 5000.0` respectively.

At S0 the rectangular section has a width of 200 mm and a depth of 500 mm. Centring it at the transverse origin gives width coordinates of ±100 mm and depth coordinates of ±250 mm.

At S1 the width remains 200 mm, while the depth is reduced to 250 mm. The width coordinates remain ±100 mm and the depth coordinates become ±125 mm. This produces a symmetric taper without shifting the section centre.

The rectangle is called `solid` at both stations. Its vertices must be listed in corresponding order at the two ends. CSF associates polygons and vertices by their indices: the first vertex at S0 corresponds to the first vertex at S1, and so on. Changing the order at only one end would change the geometric correspondence and could produce an invalid or unintended intermediate section.

### 2.3 Represent the material through a weight

The model uses a dimensionless polygon weight to represent the local Young's modulus relative to a reference modulus:

$$
w(z)=\frac{E(z)}{E_{\mathrm{ref}}},\qquad E_{\mathrm{ref}}=210000\ \mathrm{MPa}.
$$

At the fixed end, the weight is `1.0` because the modulus equals the reference modulus. At the free end, it is `0.5` because the modulus is half the reference value.

The numerical value of the reference modulus is supplied in Python, not in this YAML. Here `weight` is a material multiplier, not a force, mass, density or self-weight load.

### 2.4 Write the complete file

Save the following content as `models/combined_variation.yaml` (or open the [existing model](models/combined_variation.yaml)). The content is the same as in the benchmark; no new fields or values are introduced.

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        - name: solid
          weight: 1.0
          vertices:
            - [-100.0, -250.0]
            - [100.0, -250.0]
            - [100.0, 250.0]
            - [-100.0, 250.0]
    S1:
      z: 5000.0
      polygons:
        - name: solid
          weight: 0.5
          vertices:
            - [-100.0, -125.0]
            - [100.0, -125.0]
            - [100.0, 125.0]
            - [-100.0, 125.0]
  weight_laws:
    - "solid,solid: w0 + (w1-w0)*(z/L)"
```

Notice that `weight_laws` is aligned with `sections`, not nested under `S1`. It applies to the longitudinal variation of the corresponding polygon pair.

The string `solid,solid: w0 + (w1-w0)*(z/L)` refers to the polygon named `solid` at S0 and the corresponding polygon named `solid` at S1. In this model `w0 = 1.0`, `w1 = 0.5`, `L = 5000 mm`, and the longitudinal origin is zero. At any position in this member the expression gives the linearly varying weight.

### 2.5 What happens between S0 and S1?

The two sections are reference stations used to construct the physical geometry; they are not finite element nodes. For this model CSF interpolates corresponding vertex coordinates linearly along the longitudinal axis, independently of the specified material-weight law.

At the halfway position, `z = 2500.0`, the transverse depth coordinates are halfway between ±250 and ±125, giving ±187.5 mm. The section depth is therefore 375 mm. The material weight is `1.0 + (0.5 - 1.0) * 0.5 = 0.75`, giving a modulus of 157500 MPa.

| Position z (mm) | Width (mm) | Depth (mm) | Weight | Young's modulus (MPa) |
|---:|---:|---:|---:|---:|
| 0 | 200 | 500 | 1.0 | 210000 |
| 2500 | 200 | 375 | 0.75 | 157500 |
| 5000 | 200 | 250 | 0.5 | 105000 |

These are values implied by the physical inputs, not new numerical validation results. There is no need to add a third reference section to the YAML for the halfway position. Python can request it directly from CSF, as shown below.

## 3. Prepare and inspect the example

For a new local checkout of the review branch:

```bash
git clone --branch feature/csf-pycba https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
cd pycba/tapered_cantilever
python3 -m pip install -r requirements.txt
```

The activation command above is for a POSIX shell (Linux/macOS). On Windows PowerShell use `.venv\Scripts\Activate.ps1` from the repository root instead. If the repository and environment are already available, activate the existing environment and start from the example directory.

The example requirements specify PyCBA 1.0.2. CSF is installed from the local repository. Both packages must be installed in the same Python environment for this example; this does not make CSF a mandatory dependency of PyCBA itself.

All following commands are run from `pycba/tapered_cantilever/` unless otherwise indicated.

Before running a beam analysis, inspect the geometry using CSF alone:

```bash
csf-actions models/combined_variation.yaml models/action.yaml
```

The [action file](models/action.yaml) requests a 3D geometry view, cross-sections at the three positions listed above, the material-weight variation and sectional properties `A`, `Ix` and `Iy`. These plotted properties include the CSF weights. This is an optional visual inspection of the physical model, not a PyCBA solution or a substitute for the numerical validation. The action command is taken from the existing README and should be checked locally.

## 4. Read the YAML in Python (`csf_section.py`)

The YAML does not need to be converted manually into Python dictionaries or a stiffness polynomial. CSF already has a reader that parses and checks its own model format and constructs the continuous field.

The following sections show the essential implementation of the existing [csf_section.py](csf_section.py) adapter, with comments shortened for teaching. They are not a replacement for that file.

### 4.1 Import the public CSF interfaces

```python
import numpy as np
from csf import section_properties
from csf.io.csf_reader import CSFReader
```

`CSFReader` loads the model. `section_properties` calculates sectional properties from a section object. NumPy will be used later to accept arrays of longitudinal positions.

### 4.2 Load and check the model

```python
def load_csf_model(path):
    result = CSFReader().read_file(str(path))
    if not result.ok or result.field is None:
        raise ValueError(f'Cannot load {path}: {result.issues}')
    return result.field
```

`read_file` receives the file path, validates the CSF input and returns a result object. `result.ok` indicates whether it reported an error; `result.field` holds the constructed continuous section field when available. The adapter stops if it cannot obtain a valid field.

For example, in a Python session started from the example directory:

```python
from csf_section import load_csf_model

field = load_csf_model('models/combined_variation.yaml')
```

The Python variable `field` now refers to the physical member, not a PyCBA beam. Loading the model does not create finite elements, apply loads or solve an equilibrium equation.

### 4.3 Request a section at any longitudinal position

```python
section = field.section(2500.0)
polygon = section.polygons[0]
print(polygon.weight)
```

The weight should be `0.75` for the selected model. `field.section(...)` is the key operation: a single loaded CSF model can return the section at any position in its domain. The caller does not need to calculate the vertex interpolation or material weight itself.

The returned section can then be passed to `section_properties`:

```python
from csf import section_properties

props = section_properties(section)
print(props['A'])
print(props['Ix'])
```

`props` is a dictionary, so a named quantity can be retrieved using a key in brackets. Here the returned area and inertia are weighted by the material multiplier. The following step shows how to use those quantities correctly.

## 5. Convert the CSF sectional properties into flexural rigidity

For the one uniformly weighted solid polygon in this example, the returned `props['Ix']` represents $I_x^w(x)=w(x)I_x(x)$, with $I_x$ the geometric second moment about the bending axis. Similarly, `props['A']` represents $w(x)A(x)$.

PyCBA requires the physical flexural rigidity, which is obtained as follows:

$$
\begin{aligned}
EI(x)&=E(x)I_x(x)\\
     &=E_{\mathrm{ref}}w(x)I_x(x)\\
     &=E_{\mathrm{ref}}I_x^w(x).
\end{aligned}
$$

In particular, do **not** multiply the weighted inertia by the local modulus `E_ref * w`. That would apply the material multiplier twice.

The adapter combines these operations into a reusable function:

```python
def sectional_properties(field, x, E_ref):
    section = field.section(float(x))
    if len(section.polygons) != 1:
        raise ValueError('Expected a single solid polygon')
    polygon = section.polygons[0]
    w = float(polygon.weight)
    if w <= 0:
        raise ValueError('Expected positive material weight')

    props = section_properties(section)
    return {
        'h_mm': max(p.y for p in polygon.vertices)
                - min(p.y for p in polygon.vertices),
        'b_mm': max(p.x for p in polygon.vertices)
                - min(p.x for p in polygon.vertices),
        'E_MPa': E_ref * w,
        'A_mm2': props['A'] / w,
        'Ix_mm4': props['Ix'] / w,
        'EI_Nmm2': E_ref * props['Ix'],
    }
```

The function returns geometric and mechanical properties together. Depth and width come from the current polygon coordinates. Dividing the weighted properties by `w` recovers the geometric properties in this particular single-material section; multiplying the weighted inertia by `E_ref` gives the actual rigidity.

For an initial check, use the reference modulus from the benchmark:

```python
from reference_solution import E0
from csf_section import sectional_properties

mid = sectional_properties(field, 2500.0, E0)
print(mid)
```

Check that `h_mm`, `b_mm` and `E_MPa` agree with the midpoint values in Section 2.5. The independent rectangular-section formula $I_x=bh^3/12$ can also be used to check the geometric inertia. It is a reference calculation, not the method used by the adapter to obtain it from CSF.

**Scope:** this adapter intentionally assumes one solid rectangular polygon with a positive, uniform cross-sectional weight. It is not a general heterogeneous or composite-section adapter. A more complex section would require explicit consideration of the relevant bending axes, reference modulus and sectional stiffness; dividing the weighted properties by a single polygon weight would not generally be valid.

## 6. Create the function that PyCBA can call

So far the adapter calculates properties at a single requested position. PyCBA's `SectionEI` needs a callable that can supply the rigidity at its sampling positions. A callable is simply a Python object that can be called like a function.

The existing adapter creates that callable using the loaded `field` and the reference modulus:

```python
def create_ei_function(field, E_ref):
    def EI(x):
        if np.ndim(x) == 0:
            return sectional_properties(
                field, float(x), E_ref
            )['EI_Nmm2']
        a = np.asarray(x, dtype=float)
        return np.array([EI(v) for v in a.flat]).reshape(a.shape)
    return EI
```

The outer function returns the inner function `EI` itself, without evaluating it at a particular coordinate. The returned function remembers `field` and `E_ref` (a Python closure). There is no need to read the YAML again each time PyCBA asks for a rigidity value.

The first branch deals with one coordinate; the second handles a collection of coordinates and returns a NumPy array of the same shape. This is important because PyCBA can evaluate the rigidity at several sampling positions together during polynomial fitting.

Try both forms:

```python
from csf_section import create_ei_function

EI = create_ei_function(field, E0)
print(EI(2500.0))
print(EI([0.0, 2500.0, 5000.0]))
```

The first call gives one rigidity value; the second gives three. All are in N·mm². The values should decrease towards the free end in this particular model.

At this point the CSF part of the integration is complete. The function can be handed to PyCBA. CSF has not fitted a polynomial and does not need to know which structural formulation will use the function.

## 7. Supply the continuous rigidity to PyCBA (`pycba_analysis.py`)

The existing [pycba_analysis.py](pycba_analysis.py) is the second half of the integration. It receives the callable created above and uses only the PyCBA interfaces. It does not import CSF or read any YAML file.

### 7.1 Understand the `SectionEI` call

For the entire 5000 mm cantilever represented by a single member, the essential call is:

```python
import pycba as cba
from reference_solution import L

section = cba.SectionEI().add_segment(
    'poly', [0.0, L], EI, degree=12
)
```

| Argument | Meaning |
|---|---|
| `'poly'` | Use the polynomial representation of the stiffness variation in PyCBA. |
| `[0.0, L]` | Start and end coordinates of the segment, local to the beam member. |
| `EI` | The function obtained from CSF; pass the function, not `EI(0.0)`. |
| `degree=12` | Polynomial degree parameter used by the existing benchmark. |

PyCBA samples the supplied function and constructs its internal polynomial representation. The user does not have to derive or enter polynomial coefficients. In this benchmark the depth and modulus are linear, so the exact rectangular-section rigidity is a polynomial of degree four; the existing solver call nevertheless retains its original default degree of 12. The degree sensitivity study investigates this choice separately.

The number of CSF reference sections, the number of PyCBA beam elements and the polynomial degree are three different things. Neither the two YAML reference sections nor the degree of the fitting polynomial imposes a subdivision into twelve or two structural elements.

### 7.2 Handle one or several beam members

The actual tutorial uses a reusable function that also supports the convergence study:

```python
def solve_continuous(EI, length, load, n_elements=1, degree=12):
    dx = length/n_elements
    sections = []
    for i in range(n_elements):
        def local_ei(x, offset=i*dx):
            return EI(offset+x)
        section = cba.SectionEI().add_segment(
            'poly', [0.0, dx], local_ei, degree=degree
        )
        sections.append(section)
    return solve_beam([dx]*n_elements, sections, load)
```

CSF describes the complete member using its global longitudinal coordinate. `SectionEI`, on the other hand, asks for a coordinate local to each PyCBA member. The small `local_ei` function translates between the two: it adds the position of the start of the current member to the local coordinate before evaluating the original `EI` function. The default argument `offset=i*dx` preserves the correct start position for each callable.

With `n_elements=1`, the local and global coordinates are identical in this example. If the convergence study splits the beam, the offset becomes necessary. The geometry YAML is unchanged in both situations.

### 7.3 Define the structural problem and solve

The `solve_beam` function is shared by the continuous and midpoint approaches:

```python
def solve_beam(lengths, rigidities, load):
    n = len(lengths)
    restraints = [-1, -1] + [0, 0]*n
    beam = cba.BeamAnalysis(lengths, rigidities, R=restraints, GAv=None)
    beam.add_pl(n, load, lengths[-1])
    beam.analyze()
    return -float(beam.beam_results.D[-2])
```

Read this function in the following order:

| Code | What it does in this example |
|---|---|
| `lengths` | A list of beam member lengths, in mm. |
| `rigidities` | One `SectionEI` object or constant flexural rigidity per member. |
| `restraints` | Fixes the translation and rotation at the first node; all remaining nodal degrees of freedom are free. |
| `GAv=None` | Omits shear flexibility, consistently with the Euler-Bernoulli benchmark. |
| `beam.add_pl(n, load, lengths[-1])` | Applies the downward point load at the end of the final member. PyCBA uses a one-based member index for this call. |
| `beam.analyze()` | Executes the structural analysis. |
| `-float(beam.beam_results.D[-2])` | Extracts the last node's vertical displacement and changes its sign to report a positive downward tip displacement. |

For the single-member case, `lengths` contains only `5000.0`, and the restraint list is `[-1, -1, 0, 0]`. The final member has index 1, and the point load of 10000 N is placed at its local coordinate 5000 mm.

## 8. Put the entire integration together

The preceding steps explain the implementation. In practice, the two adapters can already be imported, so an end user does not have to reproduce their code.

For an initial, minimal analysis, the following is a complete example to run from `pycba/tapered_cantilever/` with the environment active. It can be entered in a Python session or saved as a separate temporary Python file in that directory. It reuses the benchmark's constants and its original solver settings:

```python
from reference_solution import L, P, E0
from csf_section import load_csf_model, create_ei_function
from pycba_analysis import solve_continuous

field = load_csf_model('models/combined_variation.yaml')
EI = create_ei_function(field, E0)
tip_mm = solve_continuous(EI, L, P, n_elements=1, degree=12)
print(f'Downward tip displacement: {tip_mm:.9f} mm')
```

The three main operations are loading the model, creating the rigidity function, and passing it to the beam analysis. Everything else belongs to either the implementation of the adapters or the verification workflow.

This minimal example is a teaching entry point, not a substitute for the full benchmark. It deliberately does not duplicate the validation or convergence code. The official entry point remains `main.py`.

## 9. Run the complete existing benchmark

Use the command already supported by [main.py](main.py):

```bash
python3 main.py --case combined_variation
```

This command performs the preceding integration and also runs the independent checks and output generation. The execution order is:

1. Load `models/combined_variation.yaml`.
2. Compare CSF sectional properties with independent rectangular-section formulas.
3. Create the continuous rigidity callable.
4. Calculate an independent reference tip displacement and check it against the closed-form result.
5. Solve the complete cantilever using a single variable-rigidity PyCBA member.
6. Compare continuous and midpoint stiffness representations for 1, 2, 4, 8, 16, 32 and 64 members.
7. Check sensitivity to the polynomial degree parameter (2, 4, 8, 12 and 16).
8. Save the results and apply the existing acceptance criterion.

The midpoint comparison uses the same physical CSF model and callable. Its only difference is that `solve_midpoint` samples a single rigidity at the midpoint of each member and sends the resulting list of constants to `solve_beam`:

```python
def solve_midpoint(EI, length, load, n_elements):
    dx = length/n_elements
    rigidities = [EI((i+0.5)*dx) for i in range(n_elements)]
    return solve_beam([dx]*n_elements, rigidities, load)
```

In other words, the physical model remains fixed while the representation of its stiffness in the structural analysis changes.

Inspect the files under `results/combined_variation/`:

| File | What to inspect |
|---|---|
| `section_validation.csv` | Agreement of CSF properties with independently calculated values at 21 longitudinal stations. |
| `convergence.csv` | Tip displacement and relative error for both stiffness representations at each member count. |
| `degree_sensitivity.csv` | Effect of the polynomial degree parameter with a single beam member. |
| `summary.csv` | Reference and continuous tip displacements, relative error and acceptance status. |

See [VALIDATION.md](VALIDATION.md) for the numerical results and their interpretation. The existing script checks the section-property relative errors against `1e-8` and the continuous tip-displacement relative error against `1e-6`; this guide does not change those thresholds or report a new validation run.

If preparing a reproducible record of your local execution, also record the versions:

```bash
git rev-parse HEAD
python3 -m pip show pycba csfpy
python3 -m pip freeze
```

## 10. Use the same workflow for the other existing models

The example provides four configurations with the same length, root section, reference modulus, load and support conditions. Only the tip depth and the longitudinal modulus variation change.

| Case | File under `models/` | Tip depth (mm) | Tip modulus (MPa) |
|---|---|---:|---:|
| A — constant geometry and material | `prismatic.yaml` | 500 | 210000 |
| B — variable geometry | `variable_geometry.yaml` | 250 | 210000 |
| C — variable material | `variable_material.yaml` | 500 | 105000 |
| D — combined variation | `combined_variation.yaml` | 250 | 105000 |

The same adapter functions are used for all four configurations. To run them together:

```bash
python3 main.py --case all
```

For a new rectangular cantilever outside the four predefined cases, the integration functions can be reused with a suitable YAML, member length, reference modulus and load. However, the independent reference formulas, the case selection in `main.py` and the validation data are specific to the four existing benchmark definitions. Editing a benchmark YAML alone would make it inconsistent with its reference solution. For a genuinely new case, provide its own independent checks rather than changing the existing benchmark numbers.

## 11. Practical checklist and summary

| Step | Question to check | Interface or file |
|---|---|---|
| 1. Physical input | Are the dimensions, weights, coordinates and units consistent? | `models/combined_variation.yaml` |
| 2. Load | Did the reader construct a valid continuous field? | `CSFReader().read_file(...)` |
| 3. Evaluate | Do the intermediate sections and weights match the intended member? | `field.section(...)` |
| 4. Calculate rigidity | Is the weighted inertia multiplied by the reference modulus only once? | `section_properties`, `sectional_properties` |
| 5. Expose the function | Does `EI` accept both individual positions and arrays? | `create_ei_function` |
| 6. Transfer | Are the segment coordinates local to each PyCBA member? | `SectionEI`, `local_ei` |
| 7. Solve | Do the restraints, load, units and displacement sign match the problem? | `BeamAnalysis`, `add_pl`, `analyze` |
| 8. Verify | Does the result agree with the independent reference? | `main.py`, `validation.py`, `convergence.py` |

The entire integration can be summarised as:

```text
CSF YAML: geometry + relative material properties
                    |
                    v
CSFReader --> continuous field --> section at any position
                    |
                    v
section_properties --> weighted sectional inertia
                    |
                    v
create_ei_function --> physical EI(x) callable
                    |
                    v
PyCBA SectionEI --> internal polynomial representation
                    |
                    v
PyCBA BeamAnalysis --> structural response
```

CSF supplies the physical information; PyCBA decides how to represent it in its beam formulation and solves the structural problem. No changes to either library are necessary for this integration, and CUF is not involved.

### Source files and further reading

This guide follows the existing [review branch tutorial](https://github.com/giovanniboscu/continuous-section-field/tree/feature/csf-pycba/pycba/tapered_cantilever). Relative links above assume this Markdown file is placed in the `tapered_cantilever/` directory alongside `README.md`. For a reader viewing the guide elsewhere, use the following direct links:

- [Tutorial README](https://github.com/giovanniboscu/continuous-section-field/blob/feature/csf-pycba/pycba/tapered_cantilever/README.md) — physical problem and execution instructions.
- [combined_variation.yaml](https://github.com/giovanniboscu/continuous-section-field/blob/feature/csf-pycba/pycba/tapered_cantilever/models/combined_variation.yaml) — exact model used here.
- [csf_section.py](https://github.com/giovanniboscu/continuous-section-field/blob/feature/csf-pycba/pycba/tapered_cantilever/csf_section.py) — geometry reader, property evaluation and rigidity callable.
- [pycba_analysis.py](https://github.com/giovanniboscu/continuous-section-field/blob/feature/csf-pycba/pycba/tapered_cantilever/pycba_analysis.py) — PyCBA integration and analysis.
- [reference_solution.py](https://github.com/giovanniboscu/continuous-section-field/blob/feature/csf-pycba/pycba/tapered_cantilever/reference_solution.py) — constants and independent reference formulas.
- [main.py](https://github.com/giovanniboscu/continuous-section-field/blob/feature/csf-pycba/pycba/tapered_cantilever/main.py) — full benchmark execution.
- [PyCBA documentation](https://ccaprani.github.io/pycba/) — beam analysis library.

*Documentation status: practical companion to the review draft. Code excerpts follow the branch files inspected when preparing this guide. The example has not been independently executed as part of preparing this document; the existing validation workflow remains the authority for numerical acceptance.*
