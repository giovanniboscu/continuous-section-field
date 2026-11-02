# CSF-CUF post-processing

## From the solved CUF field to physical displacement samples

The CSF-CUF solver computes a physical displacement field over the beam. The standard output adapter is the final layer that decides **where that already-solved field is evaluated** and **how the selected values are written to disk**.

The standard implementation documented here is:

```text
src/csf/cuf/adapters/output/post.py
```

and it is selected in a case YAML with:

```yaml
output:
  adapter: csf.cuf.adapters.output.post
```

A representative case is:

```text
cuf/I-Shape_L/cases/taper/
carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml
```

which contains:

```yaml
sampling:
  stations: [0.0, 0.1, 1.0]
  displacement_samples: 201
  stress_grid: 41

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../../output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3
```

The central idea is:

```text
CSF physical section at x      solved CUF displacement field
          |                               |
          v                               v
   physical coordinates              u(x,y,z)
          |                               |
          +---------------+---------------+
                          |
                          v
                 standard post-processor
                          |
                          v
                    response.txt
```

The output adapter does **not** solve the structural problem again. It does **not** assemble a stiffness matrix, modify the CUF approximation, or reconstruct the generalized CUF coefficient vector manually. It receives the solved physical displacement field and evaluates it at selected physical points.

---

# Part I - Position of `post.py` in the CSF-CUF workflow

## 1. Separation of responsibilities

The post-processing layer follows the same separation of responsibilities used throughout CSF-CUF:

```text
CSF  -> defines the current physical cross-section
CUF  -> provides the solved displacement field
post -> selects physical sampling points and writes results
```

More explicitly:

- **CSF** answers: *where is the material at longitudinal coordinate `x`?*
- **CUF** answers: *what is the displacement at physical point `(x,y,z)`?*
- **`post.py`** answers: *which physical points should be reported, and in which output file?*

This distinction is important for non-prismatic models. The standard adapter does not keep a second copy of the geometry. At every requested longitudinal station it queries the active CSF section again.

Therefore, if the section changes with `x`, the sampled coordinates change with it.

---

## 2. The physical field is the interface

The standard adapter works with the public displacement evaluator:

```text
u(x, y, z)
```

which returns the three displacement components:

```text
[ux, uy, uz]
```

Conceptually, the CUF reconstruction has already taken place before the output adapter evaluates the solution.

For a generic CUF expansion,

$$\mathbf{u}(x,y,z) = \sum_{\tau} F_{\tau}(y,z)\,\mathbf{u}_{\tau}(x),$$

where:

- $F_{\tau}(y,z)$ are the transverse expansion functions;
- $\mathbf{u}_{\tau}(x)$ are the longitudinal generalized displacement functions;
- $\mathbf{u}(x,y,z)$ is the reconstructed physical displacement vector.

`post.py` does not need to know which transverse basis produced that field. It simply evaluates the final physical function:

```python
vec = np.asarray(u(x, y, z), dtype=float)
```

and writes:

```text
vec[0] -> ux
vec[1] -> uy
vec[2] -> uz
```

This is why the same output adapter can be used with different CUF transverse expansions, provided that the solved result exposes the same physical displacement-field interface.

---

# Part II - YAML configuration

## 3. Complete sampling/output block

A case can contain:

```yaml
sampling:
  stations: [0.0, 0.1, 1.0]
  displacement_samples: 201
  stress_grid: 41

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../../output/my_case
```

The `sampling` block and the `output` block play different roles.

The `sampling` block defines sampling-related values that are parsed from the case YAML. The `output` block selects the internal output module and defines where its files are written.

For the current standard adapter, the parameters are used as follows:

| YAML key | Role | Parsed from the case YAML | Used directly inside `post.py` |
|---|---|---:|---:|
| `sampling.stations` | normalized longitudinal stations at which the response is evaluated | **Yes** | **Yes** |
| `sampling.displacement_samples` | general displacement-sampling setting stored in the case configuration | **Yes** | **No** |
| `sampling.stress_grid` | general stress-grid setting stored in the case configuration | **Yes** | **No** |
| `output.adapter` | selects the internal Python output module | **Yes** | **No** |
| `output.directory` | defines the output destination; exposed to the adapter as `case.output_dir` | **Yes** | **Yes** |

The distinction for `output.adapter` is simple: it is not a numerical control used by `post.py`. It tells the case execution logic which internal output module must be loaded. Once `csf.cuf.adapters.output.post` has been selected, the module itself operates on the solved field and the case data described below.

The presence of:

```yaml
displacement_samples: 201
stress_grid: 41
```

in a case does **not** mean that the standard `csf.cuf.adapters.output.post` module creates 201 displacement samples or a 41 x 41 stress grid.

The current standard adapter reads:

```python
case.sampling.stations
```

and writes selected **displacements only**.

---

## 4. `sampling.stations`

The longitudinal stations are normalized coordinates.

For example:

```yaml
sampling:
  stations: [0.0, 0.1, 1.0]
```

means:

| value | physical location |
|---:|---|
| `0.0` | beginning of the solved beam interval |
| `0.1` | 10% of the solved beam interval |
| `1.0` | end of the solved beam interval |

The adapter obtains:

```python
x0 = float(u.x_start)
x1 = float(u.x_end)
L = x1 - x0
```

and converts every normalized station $r$ into the physical coordinate

$$x = x_0 + rL.$$

Thus, for `r = 0.1`,

$$x = x_0 + 0.1L.$$

The same normalized station list can therefore be used for beams having different physical lengths.

---

## 5. `output.adapter`

The line

```yaml
output:
  adapter: csf.cuf.adapters.output.post
```

selects the internal Python module used for this output step:

```text
csf.cuf.adapters.output.post
```

Its implementation is located at:

```text
src/csf/cuf/adapters/output/post.py
```

`output.adapter` therefore answers one question only:

```text
Which internal output module must be used for this case?
```

It is not a sampling parameter and it is not read by `post.py` to decide where or how many points to evaluate. By the time `post.py` is executed, this module has already been selected.

The parameters that affect the behavior of this module are taken from the case and from the solved objects passed to its entry point. In particular, the standard adapter directly uses `case.sampling.stations` and `case.output_dir`.

The module exposes the output entry point:

```python
def write_outputs(
    u,
    model_bridge,
    case,
    problem_definition,
    *,
    equilibration_iterations=None,
):
    ...
```

The structural solution is already available when this function is called.

---

## 6. `output.directory`

The destination directory is obtained from:

```python
Path(case.output_dir)
```

and created if it does not already exist:

```python
out.mkdir(parents=True, exist_ok=True)
```

For example:

```yaml
output:
  directory: ../../output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3
```

defines the directory in which the response file is written after the case path has been resolved by the case loader.

---

# Part III - How the current CSF section is sampled

## 7. The section is queried independently at every station

Once the physical longitudinal coordinate `x` is known, the adapter asks the active section provider for the current CSF domains:

```python
model_bridge.section_provider.domains(float(x))
```

For every returned domain, it reads the physical vertices:

```python
for domain in section_provider.domains(float(x)):
    for y, z in domain.vertices:
        vertices.append((float(y), float(z)))
```

It then computes:

```text
ymin, ymax
zmin, zmax
```

from those vertices.

The operation is repeated for every requested station.

Therefore:

$$\Omega = \Omega(x)$$

is respected naturally by the sampling procedure. The geometry used at `x = 0.1 L` is the geometry returned by the CSF model at `x = 0.1 L`; the geometry used at `x = L` is the geometry returned at `x = L`.

No frozen reference cross-section is used by the adapter.

This is particularly important for tapered and otherwise variable-section models.

---

## 8. The four standard cross-sectional points

For every requested station, the current implementation evaluates four named physical points:

```python
points = (
    ("center",     0.0,            0.0),
    ("plus",       ymin,           zmax),
    ("minus",      bottom_right_y, zmin),
    ("bottom_mid", 0.0,            zmin),
)
```

Their definitions are:

| point | coordinates `(y,z)` | construction |
|---|---|---|
| `center` | `(0,0)` | cross-sectional coordinate origin |
| `plus` | `(ymin,zmax)` | minimum `y`, maximum `z` of current section bounds |
| `minus` | `(bottom_right_y,zmin)` | largest `y` among vertices on the minimum-`z` boundary |
| `bottom_mid` | `(0,zmin)` | centerline at the minimum-`z` level |

These names are sampling labels. In particular, `plus` and `minus` do not define the signs of the coordinates.

---

## 9. How `bottom_right_y` is found

The adapter first determines the minimum cross-sectional coordinate:

```text
zmin
```

It then identifies all section vertices lying on that lower boundary.

Because vertex coordinates are floating-point values, the comparison uses the tolerance

$$\text{tol} = 10^{-10} \max\left(1,|z_{\min}|,|z_{\max}|\right).$$

In code:

```python
scale = max(1.0, abs(zmin), abs(zmax))
tol = 1.0e-10 * scale
```

The bottom vertices satisfy, numerically,

$$z \simeq z_{\min}.$$

Among those vertices, the adapter selects the largest `y` coordinate:

```python
bottom_right_y = max(bottom_vertices, key=lambda point: point[0])[0]
```

and defines:

```text
minus = (bottom_right_y, zmin)
```

The tolerance is used only to identify the lower boundary. It does not modify the CSF geometry.

---

# Part IV - Complete operation at one station

## 10. Step-by-step sequence

For one normalized station $r$, the standard adapter performs the following operations.

### Step 1 - Convert the normalized station to `x`

$$x=x_0+rL.$$

### Step 2 - Query the current CSF section

```python
section_provider.domains(x)
```

### Step 3 - Collect the physical section vertices

```text
(y1,z1), (y2,z2), ..., (yn,zn)
```

### Step 4 - Compute the current section bounds

```text
ymin, ymax, zmin, zmax
```

### Step 5 - Identify the lower-boundary right vertex

```text
bottom_right_y
```

### Step 6 - Construct the four physical sampling points

```text
center
plus
minus
bottom_mid
```

### Step 7 - Evaluate the solved CUF field

For every point:

```python
vec = np.asarray(u(x, y, z), dtype=float)
```

### Step 8 - Write the three displacement components

```text
ux, uy, uz
```

The complete logical chain is therefore:

```text
normalized station r
        |
        v
x = x0 + r L
        |
        v
current CSF section Omega(x)
        |
        v
current physical section bounds
        |
        v
four physical sampling points
        |
        v
u(x,y,z)
        |
        v
ux, uy, uz
        |
        v
response file
```

---

# Part V - Output files

## 11. Standard analysis: `response.txt`

When `write_outputs(...)` is called without an equilibration iteration number, the adapter writes:

```text
response.txt
```

The beginning of the file is:

```text
CSF-CUF RESPONSE
======================
problem.type = <problem type>

STATION RESPONSES
-----------------
x/L x y z point ux uy uz
```

Every following row contains one physical displacement evaluation.

The columns are:

| column | meaning |
|---|---|
| `x/L` | normalized station requested by the case |
| `x` | corresponding physical longitudinal coordinate |
| `y` | physical cross-sectional coordinate |
| `z` | physical cross-sectional coordinate |
| `point` | sampling label: `center`, `plus`, `minus`, `bottom_mid` |
| `ux` | displacement component along `x` |
| `uy` | displacement component along `y` |
| `uz` | displacement component along `z` |

The current implementation does not append a unit symbol to these column names. The values therefore follow the unit system used consistently by the model and analysis.

For `N` requested stations, the file contains:

$$4N$$

displacement rows, because four cross-sectional points are sampled at each station.

For example:

```yaml
stations: [0.0, 0.1, 1.0]
```

produces:

$$4 \times 3 = 12$$

station-response rows.

---

## 12. Equilibration outputs: `response_eqN.txt`

The same adapter can also be called with an equilibration iteration identifier.

If:

```text
equilibration_iterations = N
```

is supplied, the output file becomes:

```text
response_eqN.txt
```

For example:

```text
response_eq1.txt
response_eq2.txt
response_eq3.txt
```

The sampling procedure is otherwise the same: the adapter evaluates the physical displacement field at the same named cross-sectional points and requested longitudinal stations.

This makes the response files directly comparable across equilibration iterations.

---

# Part VI - What `displacement_samples` and `stress_grid` do not mean here

## 13. `displacement_samples` is not consumed by this adapter

A case may contain:

```yaml
displacement_samples: 201
```

but the current standard `post.py` implementation does not read this value.

It does not internally create 201 longitudinal displacement samples.

Its longitudinal sampling is controlled by:

```yaml
sampling:
  stations: [...]
```

because the implemented loop is over:

```python
case.sampling.stations
```

This distinction prevents two different concepts from being mixed:

```text
sampling configuration available in the case
                versus
sampling actually consumed by this output adapter
```

---

## 14. `stress_grid` is not consumed by this adapter

Likewise, a case may contain:

```yaml
stress_grid: 41
```

but the standard `csf.cuf.adapters.output.post` module does not generate a stress grid and does not reconstruct stresses.

The module evaluates only:

```text
u(x,y,z)
```

and reports:

```text
ux, uy, uz
```

A stress-oriented post-processing workflow must use the appropriate stress reconstruction/sampling implementation rather than assuming that `post.py` uses `stress_grid` automatically.

---

## 15. Why the distinction matters

Consider again:

```yaml
sampling:
  stations: [0.0, 0.1, 1.0]
  displacement_samples: 201
  stress_grid: 41

output:
  adapter: csf.cuf.adapters.output.post
```

For the standard adapter documented here, the effective operation is:

```text
stations -> used to create response.txt / response_eqN.txt
```

while:

```text
displacement_samples -> not read by post.py
stress_grid          -> not read by post.py
```

The values may still be useful to other components or workflows that share the same case definition, but they are not controls of this specific adapter.

---

# Part VII - Applicability of the four-point convention

## 16. Intended geometry convention

The standard point rule is designed for centered sections for which:

- `(y,z) = (0,0)` has the expected physical meaning;
- the minimum-`z` boundary represents the lower boundary of interest;
- the four predefined points are meaningful for the analysis.

It is suitable, for example, for centered:

- rectangular sections;
- T-sections;
- I / double-T sections;
- corresponding variable sections whose geometry changes along `x`.

The geometry may be non-prismatic because the section bounds are recomputed independently at each station.

---

## 17. When a custom output adapter is preferable

The four-point rule is not a universal geometric sampling definition.

A custom adapter is appropriate when the section is:

- translated relative to the expected origin;
- disconnected;
- highly irregular;
- better described through named boundaries or features;
- required to be sampled at other physical locations;
- required to produce quantities other than the standard displacement rows.

The decision belongs to post-processing, not to the CUF solver.

The structural formulation remains unchanged; only the rule used to interrogate the already-solved field changes.

---

# Part VIII - The output-adapter contract

## 18. Inputs used by the standard adapter

The current entry point receives:

```python
write_outputs(
    u,
    model_bridge,
    case,
    problem_definition,
    *,
    equilibration_iterations=None,
)
```

The arguments are used as follows:

| argument | role |
|---|---|
| `u` | solved physical displacement field; provides `x_start`, `x_end`, and `u(x,y,z)` |
| `model_bridge` | provides the active CSF `section_provider` |
| `case` | provides `sampling.stations` and the resolved output directory |
| `problem_definition` | provides `problem_type` for the response header |
| `equilibration_iterations` | selects `response.txt` or `response_eqN.txt` |

The standard adapter therefore requires only a small, explicit interface:

```text
u.x_start
u.x_end
u(x,y,z)

model_bridge.section_provider.domains(x)

case.sampling.stations
case.output_dir

problem_definition.problem_type
```

It does not need the internal CUF matrix assembly or generalized-DOF numbering.

---

## 19. Return value

After writing the file, the adapter prints:

```text
written: <path>
```

and returns the generated path as a tuple:

```python
return (path,)
```

This is the complete file output of the current standard `post.py` implementation for each call.

---

# Part IX - Worked example: tapered I-section

## 20. Case configuration

The tapered I-section case contains:

```yaml
sampling:
  stations: [0.0, 0.1, 1.0]
  displacement_samples: 201
  stress_grid: 41

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../../output/taper/carrera_i_shaped_taper80_lagrangeL9_v4_web3
```

For `post.py`, the active sampling list is:

```text
r = 0.0, 0.1, 1.0
```

Let the solved interval be:

$$[x_0,x_1], \qquad L=x_1-x_0.$$

The three physical coordinates are then:

$$x^{(1)}=x_0,$$

$$x^{(2)}=x_0+0.1L,$$

$$x^{(3)}=x_1.$$

At each one of these coordinates the adapter performs a new call to:

```python
model_bridge.section_provider.domains(x)
```

so the tapered geometry is evaluated at the actual station.

For every station, four points are then constructed from the current section and passed to:

```python
u(x, y, z)
```

The final standard response therefore contains 12 displacement evaluations:

```text
3 stations x 4 cross-sectional points = 12 rows
```

This example shows the intended CSF-CUF separation particularly clearly:

```text
taper law / variable geometry
          |
          v
        CSF
          |
          v
current section Omega(x)
          |
          +--------------------+
                               |
CUF solved field u(x,y,z) -----+
                               |
                               v
                           post.py
                               |
                               v
                         response.txt
```

The taper is not reimplemented in `post.py`. The adapter simply asks CSF for the physical section that exists at each requested `x`.

---

# Part X - Reading the implementation

## 21. `_bounds(...)`

The helper:

```python
def _bounds(section_provider, x: float):
    ...
```

has one geometric purpose: derive the quantities needed by the four-point sampling convention from the current physical section.

It:

1. obtains all current sectional domains at `x`;
2. collects their vertices;
3. computes `ymin`, `ymax`, `zmin`, `zmax`;
4. identifies vertices on the minimum-`z` boundary;
5. returns the largest `y` value on that boundary.

The return values are:

```text
ymin, ymax, zmin, zmax, bottom_right_y
```

If the section contains no vertices, it raises an error identifying `x`.

If no lower-boundary vertex can be identified, it also raises an explicit error.

---

## 22. `write_outputs(...)`

The main function performs four tasks:

```text
1. determine the solved longitudinal interval
2. create/select the output file
3. loop over case.sampling.stations
4. evaluate u(x,y,z) at four points and write the rows
```

In compact form, its core is equivalent to:

```python
for ratio in case.sampling.stations:
    x = x0 + float(ratio) * L

    ymin, ymax, zmin, zmax, bottom_right_y = _bounds(
        model_bridge.section_provider,
        x,
    )

    points = (
        ("center", 0.0, 0.0),
        ("plus", ymin, zmax),
        ("minus", bottom_right_y, zmin),
        ("bottom_mid", 0.0, zmin),
    )

    for name, y, z in points:
        vec = np.asarray(u(x, y, z), dtype=float)
        # write x/L, x, y, z, name, ux, uy, uz
```

This compact loop contains the complete physical logic of the standard adapter.

---

# Part XI - Methodological summary

## 23. The correct reading of `post.py`

The standard CSF-CUF output adapter should be read as a **physical sampling layer**.

It is not a second solver and it is not a stress-recovery module.

Its job is:

$$\boxed{ \text{current CSF geometry} + \text{solved CUF displacement field} \longrightarrow \text{selected physical displacement samples} }$$

The three responsibilities remain separate:

```text
CSF
  defines Omega(x) and therefore the physical sampling coordinates

CUF
  provides the solved field u(x,y,z)

post.py
  chooses four points at each requested station and writes ux, uy, uz
```

For variable-section problems this separation is particularly useful: the output adapter automatically follows the geometry because it queries the CSF section at the same longitudinal coordinate at which the displacement field is evaluated.

---

# Part XII - Quick reference

## 24. Standard YAML

```yaml
sampling:
  stations: [0.0, 0.1, 1.0]
  displacement_samples: 201
  stress_grid: 41

output:
  adapter: csf.cuf.adapters.output.post
  directory: ../../output/my_case
```

For this adapter:

```text
stations             -> used
displacement_samples -> not used by post.py
stress_grid          -> not used by post.py
```

---

## 25. Standard sampled points

```text
center     = (0, 0)
plus       = (ymin, zmax)
minus      = (bottom_right_y, zmin)
bottom_mid = (0, zmin)
```

with all geometric bounds evaluated from the **current CSF section at the requested x**.

---

## 26. Standard output

Normal call:

```text
<output directory>/response.txt
```

Equilibration call:

```text
<output directory>/response_eqN.txt
```

Columns:

```text
x/L  x  y  z  point  ux  uy  uz
```

---

## 27. Source references

Standard output adapter:

```text
https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/adapters/output/post.py
```

Representative tapered I-section case:

```text
https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/I-Shape_L/cases/taper/carrera_i_shaped_taper80_lagrangeL9_v4_E10_web3.yaml
```

Documentation location:

```text
cuf/docs/csf_post.md
```
