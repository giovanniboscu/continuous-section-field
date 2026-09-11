# CSF-CUF post-processing

The CSF-CUF solver computes a displacement field over the beam. The output adapter is the final layer that decides **where to evaluate that solved field** and **how to write the results**.

For the standard adapter, using post-processing requires only two choices in the case YAML:

1. the longitudinal stations to sample;
2. the output directory.

The standard implementation is:

```text
src/csf/cuf/adapters/output/post.py
```

It evaluates the physical displacement field `u(x, y, z)` at four points of the current CSF cross-section and writes the values to `response.txt`.

---

## 1. The basic idea

A CSF-CUF analysis can be viewed as the following sequence:

```text
CSF physical model
       |
       v
CUF analysis
       |
       v
solved displacement field u(x,y,z)
       |
       v
output adapter
       |
       v
response.txt
```

The output adapter acts **after** the system has been solved.

It does not need to know how the CUF stiffness matrix was assembled, how the generalized degrees of freedom were numbered, or which transverse expansion was used. It receives a solved physical field and evaluates it directly at physical coordinates.

This is the main post-processing interface:

```python
u(x, y, z)
```

It returns the three displacement components at the requested physical point:

```text
[ux, uy, uz]
```

---

# Part I - Using the standard post-processor

## 2. Minimal configuration

In the case YAML, add a `sampling` block and an `output` block:

```yaml
sampling:
  stations: [0.00, 0.25, 0.50, 0.75, 1.00]

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/my_case
```

For the standard output adapter documented here, `sampling.stations` is the longitudinal sampling control used to generate `response.txt`.

### `sampling.stations`

Each value is a normalized longitudinal position.

For example:

```yaml
stations: [0.00, 0.25, 0.50, 0.75, 1.00]
```

means:

| station | physical meaning |
| ---: | --- |
| `0.00` | start of the solved beam |
| `0.25` | one quarter of the beam length |
| `0.50` | mid-span |
| `0.75` | three quarters of the beam length |
| `1.00` | end of the solved beam |

Every station **must** lie in the closed interval `[0.0, 1.0]`. The case loader rejects an empty station list or any value outside that interval. If `sampling.stations` is omitted, the current loader uses `[0.0, 0.5]`; for reproducible tutorial and validation cases, an explicit station list is recommended.

### `output.adapter`

```yaml
adapter: csf.cuf.adapters.output.post
```

selects the standard CSF-CUF output adapter.

### `output.directory`

```yaml
directory: ../output/my_case
```

selects the directory in which the adapter writes its result file. A relative output directory is resolved relative to the directory containing the case YAML.

---

## 3. Run the case

Run the CUF case normally, for example:

```bash
csf-cuf cases/my_case.yaml
```

At the end of the analysis, the output adapter creates:

```text
<output directory>/response.txt
```

and reports the written path in the terminal:

```text
written: <output directory>/response.txt
```

No separate post-processing command is required for the standard adapter.

---

## 4. Read `response.txt`

The file begins with a short header:

```text
CSF-CUF RESPONSE
======================
problem.type = ...

STATION RESPONSES
-----------------
x/L x [mm] y [mm] z [mm] point ux [mm] uy [mm] uz [mm]
```

Each subsequent line is one displacement evaluation.

The columns are:

| column | meaning |
| --- | --- |
| `x/L` | normalized longitudinal station requested in the YAML |
| `x` | physical longitudinal coordinate |
| `y` | physical cross-sectional coordinate |
| `z` | physical cross-sectional coordinate |
| `point` | name of the sampled cross-sectional point |
| `ux` | displacement component along global `x` |
| `uy` | displacement component along global `y` |
| `uz` | displacement component along global `z` |

The current standard adapter writes the coordinate and displacement column labels as `[mm]`. The model and the interpretation of the output should therefore use the same length convention as the CUF examples for which this adapter is intended. If a different unit convention is required, use a customized output adapter with appropriate labels.

For every requested longitudinal station, the standard adapter writes **four rows**, one for each cross-sectional sampling point.

Therefore, if the YAML contains five stations:

```yaml
stations: [0.00, 0.25, 0.50, 0.75, 1.00]
```

the station-response table contains twenty displacement evaluations.

---

# Part II - Understanding the sampling

## 5. From a normalized station to the physical coordinate

The adapter first obtains the solved longitudinal interval from the displacement field:

```python
x0 = float(u.x_start)
x1 = float(u.x_end)
```

The solved beam length is:

```text
L = x1 - x0
```

A station value `r` from the YAML is converted into a physical coordinate using:

```text
x = x0 + r L
```

For example, `r = 0.50` means the midpoint of the solved longitudinal interval.

This is why the same normalized station list can be used for beams of different lengths.

---

## 6. The cross-section is queried at every station

Once the physical longitudinal coordinate `x` is known, the adapter asks the section provider for the **current CSF section at that position**:

```python
model_bridge.section_provider.domains(float(x))
```

The vertices of all returned sectional domains are collected, and the current cross-sectional limits are determined:

```text
ymin, ymax
zmin, zmax
```

This operation is repeated independently at every longitudinal station.

Consequently, the sampling points follow a section whose geometry changes along `x`. The post-processor does not freeze the geometry at one reference section.

This is particularly important for non-prismatic CSF models.

---

## 7. The four standard cross-sectional points

The standard adapter defines four named points from the current section geometry.

| point | physical coordinates used by the adapter |
| --- | --- |
| `center` | `(0, 0)` |
| `plus` | `(ymin, zmax)` |
| `minus` | `(y_bottom_right, zmin)` |
| `bottom_mid` | `(0, zmin)` |

Here `y_bottom_right` is the largest `y` coordinate among the section vertices lying on the minimum-`z` boundary.

### `center`

```text
(y,z) = (0,0)
```

This is the origin of the cross-sectional coordinate system.

It is meaningful when the section is defined with the expected centered coordinate convention.

### `plus`

```text
(y,z) = (ymin,zmax)
```

This point combines the minimum `y` coordinate and maximum `z` coordinate of the current section.

The name `plus` is a sampling label. It should not be interpreted as meaning that both coordinates are positive.

### `minus`

First, the adapter finds all vertices on the current minimum-`z` boundary. Among them, it selects the one with the largest `y` coordinate:

```text
y_bottom_right = maximum y on z = zmin
```

The sampled point is then:

```text
(y,z) = (y_bottom_right,zmin)
```

Again, `minus` is a sampling label rather than a statement about the signs of the coordinates.

### `bottom_mid`

```text
(y,z) = (0,zmin)
```

This samples the minimum-`z` level on the cross-sectional centerline `y = 0`.

---

## 8. Why the bottom boundary uses a tolerance

Section coordinates are floating-point values. A vertex that mathematically lies on `z = zmin` can therefore differ from another value by a very small numerical amount.

The adapter uses a small absolute tolerance when identifying vertices on the minimum-`z` boundary.

Its scale is based on the current section coordinates:

```python
scale = max(1.0, abs(zmin), abs(zmax))
tol = 1.0e-10 * scale
```

A vertex is treated as belonging to the bottom boundary when its `z` coordinate is numerically equal to `zmin` within that tolerance.

This tolerance is only used to identify the bottom boundary. It does not modify the CSF geometry.

---

## 9. What happens at each station

For every value in `case.sampling.stations`, the standard adapter performs the same sequence:

```text
normalized station r
        |
        v
physical coordinate x = x0 + r L
        |
        v
query current CSF section at x
        |
        v
obtain current section bounds
        |
        v
construct center / plus / minus / bottom_mid
        |
        v
evaluate u(x,y,z) at each point
        |
        v
write ux, uy, uz to response.txt
```

In compact Python form, the core operation is equivalent to:

```python
for ratio in case.sampling.stations:
    x = x0 + float(ratio) * L

    # obtain the current section geometry at x
    ...

    for name, y, z in points:
        vec = np.asarray(u(x, y, z), dtype=float)
        # write vec[0], vec[1], vec[2]
```

The important point is that the output adapter asks for the **physical solution at physical coordinates**.

---

# Part III - When the standard adapter is appropriate

## 10. Intended section convention

The standard sampling rule is intended for **centered sections** in which:

- the origin `(y,z) = (0,0)` has the expected geometric meaning;
- the minimum-`z` boundary is a meaningful lower boundary of the section;
- the four predefined sampling locations are useful physical points for the analysis.

The implementation is suitable, for example, for centered:

- rectangular sections;
- T-sections;
- I / double-T sections;
- corresponding sections whose geometry varies along `x`.

The geometry may be non-prismatic. At every station, the bounds are recomputed from the current CSF section.

---

## 11. When to use a custom output adapter instead

The standard four-point convention is intentionally simple. It is not a universal sampling rule for every possible CSF geometry.

A custom adapter should be preferred when the section is, for example:

- translated with respect to the expected `(0,0)` origin;
- disconnected;
- highly irregular;
- defined so that `zmin` is not the boundary of physical interest;
- better described by named geometric entities or another problem-specific sampling rule;
- required to produce quantities other than the four standard displacement samples.

The rule is simple:

> If `center`, `plus`, `minus`, and `bottom_mid` are not physically meaningful for the section being studied, define the sampling rule explicitly in a custom output adapter.

Do not force an arbitrary geometry into the standard convention.

---

# Part IV - Why the post-processor is independent of the CUF expansion

## 12. The solved field is the interface

The standard adapter does not read the generalized CUF coefficient vector directly.

Instead, it evaluates:

```python
u(x, y, z)
```

The reconstruction of the CUF field is therefore handled before the output adapter sees the result.

Conceptually:

```text
CUF generalized solution
        |
        v
physical displacement field u(x,y,z)
        |
        v
output adapter
```

This keeps the post-processing rule independent of the internal indexing of the transverse basis.

The same output logic can therefore be used with different CUF transverse expansions, provided that the solved result exposes the same physical displacement-field interface.

---

## 13. The section geometry is also queried through an interface

The output adapter does not need its own independent copy of the section geometry.

For the standard sampling rule it obtains the current sectional domains through:

```python
model_bridge.section_provider.domains(float(x))
```

and reads their physical vertices.

Therefore the two pieces of information needed by the adapter come from the active analysis itself:

```text
current CSF section at x       solved CUF field
          |                         |
          v                         v
     physical (y,z)  +        u(x,y,z)
          |                         |
          +------------+------------+
                       |
                       v
                 response.txt
```

This avoids duplicating the geometry inside the post-processing code.

---

# Part V - The output-adapter contract

## 14. Entry point

An output adapter is exposed through the function:

```python
def write_outputs(u, model_bridge, case, problem_definition):
    ...
```

The standard adapter uses the arguments as follows.

| argument | role in the standard adapter |
| --- | --- |
| `u` | solved physical displacement field; also provides `x_start` and `x_end` |
| `model_bridge` | provides access to the current CSF section through `section_provider` |
| `case` | provides the resolved output directory and sampling stations |
| `problem_definition` | provides the problem type written in the file header |

### Interfaces used by the standard adapter

```python
u.x_start
u.x_end
u(x, y, z)

model_bridge.section_provider.domains(x)

case.sampling.stations
case.output_dir

problem_definition.problem_type
```

The standard adapter does not require access to the CUF assembly internals.

---

## 15. Output-file creation

The resolved output directory is obtained from:

```python
Path(case.output_dir)
```

The adapter creates the directory if necessary:

```python
out.mkdir(parents=True, exist_ok=True)
```

and writes:

```text
response.txt
```

The adapter returns the generated path as a tuple:

```python
return (path,)
```

This is the complete output of the current standard post-processor.

---

# Part VI - Writing a custom post-processor

## 16. When customization is useful

A custom output adapter is useful when you want to change **how an already solved CUF field is interpreted**, without changing the CUF formulation or solver.

Typical reasons include:

- sampling different physical points;
- following a particular boundary of the current CSF section;
- extracting one displacement component only;
- writing a problem-specific table;
- comparing selected values with an external reference;
- producing a file format required by another analysis or plotting script.

The custom adapter remains outside the CUF solver core.

---

## 17. Minimal custom adapter

The following is a minimal example that evaluates the displacement at the cross-sectional origin for every requested station and writes the values to a text file.

```python
from pathlib import Path

import numpy as np


def write_outputs(u, model_bridge, case, problem_definition):
    del model_bridge
    del problem_definition

    x0 = float(u.x_start)
    x1 = float(u.x_end)
    length = x1 - x0

    out = Path(case.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    path = out / "center_response.txt"

    lines = [
        "x/L x ux uy uz",
    ]

    for ratio in tuple(float(v) for v in case.sampling.stations):
        x = x0 + ratio * length
        vec = np.asarray(u(x, 0.0, 0.0), dtype=float)

        lines.append(
            f"{ratio:.6f} {x:.12e} "
            f"{vec[0]:.12e} {vec[1]:.12e} {vec[2]:.12e}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written: {path}")

    return (path,)
```

The important operation is still:

```python
u(x, y, z)
```

Everything around it simply chooses points and organizes the output.

---

## 18. Querying the current section in a custom adapter

When the sampling position depends on the current cross-section, query the section provider at the same longitudinal coordinate:

```python
domains = tuple(model_bridge.section_provider.domains(float(x)))
```

For example, the standard adapter obtains all domain vertices with:

```python
vertices = []

for domain in model_bridge.section_provider.domains(float(x)):
    for y, z in domain.vertices:
        vertices.append((float(y), float(z)))
```

From those physical coordinates, a custom adapter can construct the sampling rule required by the problem.

The key methodological point is:

> Derive sampling locations from the current CSF section whenever the geometry itself determines where the physical quantity should be evaluated.

This is what allows a post-processing rule to follow a non-prismatic section correctly.

---

## 19. Selecting a custom adapter in the case YAML

The current loader accepts an output adapter in **two forms**:

1. an importable Python module name;
2. a Python file path.

Both forms use the same `output.adapter` YAML key.

### Option A - importable module

If the adapter is importable as:

```text
my_project.my_post
```

use:

```yaml
output:
  adapter: my_project.my_post
  directory: ../output/my_case
```

### Option B - Python file

A standalone `.py` file can also be selected directly:

```yaml
output:
  adapter: ../adapters/my_post.py
  directory: ../output/my_case
```

Relative adapter file paths are resolved relative to the directory containing the case YAML. Absolute paths are also accepted.

In both cases, the loaded adapter must provide a callable:

```python
def write_outputs(u, model_bridge, case, problem_definition):
    ...
```

If `write_outputs` is missing or is not callable, the runner stops with an error.

Keep the CUF solver unchanged; only the output adapter changes.

---

# Part VII - Recommended methodology

## 20. Start with the simplest useful output

When creating a new analysis, first ask:

**Which physical displacement values do I actually need to inspect?**

If the four standard points are sufficient, use:

```yaml
output:
  adapter: csf.cuf.adapters.output.post
```

and only choose the required longitudinal stations.

Do not create a custom post-processor unless the physical question requires a different sampling rule or output format.

---

## 21. Add stations progressively

For a first check, a small station set is usually easier to inspect:

```yaml
sampling:
  stations: [0.00, 0.50, 1.00]
```

Once the result is understood, increase the longitudinal resolution when needed:

```yaml
sampling:
  stations: [0.00, 0.10, 0.20, 0.30, 0.40, 0.50,
             0.60, 0.70, 0.80, 0.90, 1.00]
```

The sampling stage evaluates the already solved physical field. Changing this list changes where results are reported; it does not redefine the CUF approximation itself.

---

## 22. Verify that the predefined points match the geometry

Before interpreting `center`, `plus`, `minus`, or `bottom_mid`, check that their definitions make physical sense for the section.

For a centered T- or I-section, for example, the origin and the minimum-`z` boundary can naturally support this convention.

For an unusual geometry, first determine which physical points are meaningful, then encode those points in a custom adapter.

This separates two questions that should not be mixed:

```text
How is the CUF solution computed?

            versus

Where do I want to inspect that solution?
```

The first belongs to the analysis model. The second belongs to post-processing.

---

## 23. Let CSF provide geometry and CUF provide the field

A robust custom post-processing rule should keep these responsibilities separate:

```text
CSF -> where is the current physical section?
CUF -> what is the solved displacement at this physical point?
post.py -> which points do I want to report, and in what format?
```

This is the central methodology of the output layer.

Avoid recreating the section geometry independently inside the adapter when the required location can be obtained from the current CSF section.

Avoid reconstructing the displacement from generalized CUF coefficients when the public physical field `u(x,y,z)` already provides the required value.

---

# Part VIII - Troubleshooting

## 24. `response.txt` is not created

Check that the case contains an output adapter and directory:

```yaml
output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/my_case
```

Also verify that the CUF analysis reaches the output stage successfully.

When the adapter runs, it prints:

```text
written: .../response.txt
```

---

## 25. A requested station is outside the beam

The adapter converts each station using:

```text
x = x0 + r L
```

The case definition requires normalized values from `0.0` to `1.0`. A value outside this interval is rejected while the case YAML is loaded, before the CUF solve starts.

---

## 26. The section is reported as empty

The standard adapter requires sectional domains at every requested `x`.

If the section provider returns no vertices, the adapter raises an error identifying the physical longitudinal coordinate.

Check that:

- the station lies within the valid solved interval;
- the CSF model defines a section at that location;
- the section provider returns the expected domains.

---

## 27. The sampled points are not physically meaningful

This is not a reason to modify the CUF solver.

It means that the standard sampling convention does not match the geometry.

Create a custom output adapter and define the required points from the current CSF section.

---

## 28. The displacement component is not the one you need

The physical evaluator returns all three components:

```python
vec = np.asarray(u(x, y, z), dtype=float)

ux = vec[0]
uy = vec[1]
uz = vec[2]
```

A custom adapter can report only the component required by the analysis or combine the components into another derived output.

---

# Part IX - Quick reference

## 29. Standard YAML

```yaml
sampling:
  stations: [0.00, 0.25, 0.50, 0.75, 1.00]

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../output/my_case
```

## 30. Standard output

```text
<output directory>/response.txt
```

## 31. Standard sampled points

```text
center     -> (0, 0)
plus       -> (ymin, zmax)
minus      -> (largest y on zmin, zmin)
bottom_mid -> (0, zmin)
```

## 32. Physical-field evaluation

```python
u(x, y, z)
```

returns:

```text
[ux, uy, uz]
```

## 33. Current-section query

```python
model_bridge.section_provider.domains(x)
```

## 34. Custom-adapter entry point

```python
def write_outputs(u, model_bridge, case, problem_definition):
    ...
```

---

# 35. Final checklist

For standard post-processing:

- [ ] choose the longitudinal `sampling.stations`;
- [ ] select `csf.cuf.adapters.output.post`;
- [ ] set `output.directory`;
- [ ] run the case;
- [ ] open `response.txt`;
- [ ] interpret four rows for each requested station;
- [ ] verify that the four predefined points are meaningful for the section.

For custom post-processing:

- [ ] keep the CUF solver unchanged;
- [ ] implement `write_outputs(...)`;
- [ ] use `u(x,y,z)` for physical displacement values;
- [ ] query the current CSF section when geometry determines the sampling position;
- [ ] write outputs under `case.output_dir`;
- [ ] return the generated path or paths;
- [ ] select the custom module through `output.adapter`.

---

## 36. Summary

The standard CSF-CUF post-processing workflow is deliberately small:

```text
choose stations
      |
      v
run the CUF case
      |
      v
query the current CSF section at each station
      |
      v
evaluate u(x,y,z) at four physical points
      |
      v
write response.txt
```

The output layer does not need to understand the internal CUF algebra. Its job is to connect two physical interfaces:

1. **the current CSF section**, which determines where relevant cross-sectional points are located;
2. **the solved CUF displacement field `u(x,y,z)`**, which gives the response at those physical points.

Use the standard adapter when its four-point convention matches the section. When it does not, keep the same methodology and replace only the sampling/output logic with a custom `write_outputs(...)` adapter.

This keeps geometry, structural solution, and result interpretation separate and makes the post-processing layer simple to use, inspect, and extend.
