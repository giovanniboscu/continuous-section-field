## Programmable post-processing adapter

The post-processing stage is kept outside the generic CUF solver.

For the present bending example, the case YAML selects the output adapter and
the destination directory:

```yaml
output:
  adapter: ../../../adapters/bending/post.py
  directory: ../../../output/bending/legendre/N01
```

The output adapter is the user-facing programmable location where the generic
CUF solution is interpreted for a specific application or validation problem.

It does not modify the CUF formulation, the assembly procedure, or the solver.
Instead, it receives the already computed solution and uses the public
CSF-CUF interfaces to extract the physical quantities required by the case.

The main entry point used by the framework is:

```python
def write_outputs(u, model_bridge, case, problem_definition):
```

The adapter receives:

- `u`, the solved displacement field;
- `model_bridge`, the interface to the CSF physical model;
- `case`, the active case configuration;
- `problem_definition`, the structural problem definition associated with the run.

The post-processing logic is therefore external to the solver core.

---

### Querying the physical section

The adapter does not duplicate the geometry or material data required by the
validation procedure.

Instead, it queries the current CSF model through:

```python
domains = tuple(model_bridge.section_provider.domains(float(x)))
```

The section is therefore obtained from the same continuous sectional
representation used by the solver.

The adapter distinguishes material and void domains through the CSF
`weightabs` information and reconstructs the dimensions required by the
analytical hollow-rectangle validation.

For the present case, the following quantities are derived from the current
section:

- outer width and height;
- inner void width and height;
- net area;
- bending moment of inertia;
- section center coordinates.

The Young modulus is also read from the active CSF material state:

```python
material_state = model_bridge.domain_state(
    float(x),
    int(outer["domain_id"]),
)

E = float(material_state.E)
```

The post-processor therefore uses the physical section state supplied by

```math
\mathcal{S}(x)
```

rather than defining a second independent copy of the geometry and material
properties.

The corresponding information flow is:

```text
model_bridge
     |
     v
section_provider
     |
     |  query at x
     v
current S(x)
     |
     +-- geometry
     |
     +-- material state
     |
     v
validation quantities
```

---

### Querying the solved displacement field

The post-processing adapter does not access the global CUF degree-of-freedom
vector directly.

The solved field is exposed as a physical callable:

```python
u(x, y, z)
```

which returns the three displacement components at the requested physical
point.

The adapter checks that the result has the form:

```text
[u_x, u_y, u_z]
```

and extracts the required displacement component for the validation.

When available, the adapter can also request a section-specific evaluator:

```python
u.section_evaluator(x)
```

This allows repeated evaluations over the same cross-section without requiring
the post-processing code to know how the CUF field is internally reconstructed.

The abstraction is therefore:

```text
CUF generalized DOFs
        |
        v
generic solved field
        |
        v
u(x,y,z)
        |
        v
problem-specific post-processing
```

The output adapter is independent of the internal CUF basis indexing and of
the global algebraic numbering used by the solver.

---

### Problem-specific analytical reference

The analytical Euler-Bernoulli comparison belongs only to this validation
adapter.

It is not part of the CUF solver.

The surface-pressure amplitude is read from the problem definition:

```python
pressure = float(
    problem_definition.problem_options.get("amplitude", 1.0)
)
```

The corresponding line-load amplitude is computed as:

```math
q_0=p_0B
```

where `B` is obtained from the current CSF section.

For the sinusoidal load used in this case, the Euler-Bernoulli maximum
displacement is:

```math
u_{z,\max}
=
-\frac{q_0L^4}{\pi^4EI_y}
```

where:

- `L` is obtained from the solved longitudinal domain;
- `E` is obtained from the CSF material state;
- `I_y` is computed from the CSF geometry.

The analytical reference is therefore constructed from the same physical
model used by the CUF solution.

This prevents the validation code from maintaining a separate independent
copy of the section data.

---

### Sampling the CUF solution

The sampling locations are configured in the case YAML:

```yaml
sampling:
  stations: [0.00, 0.25, 0.50, 0.75, 1.00]
  displacement_samples: 201
  stress_grid: 31
```

The post-processing adapter consumes the requested longitudinal stations
through:

```python
for fraction in tuple(float(v) for v in case.sampling.stations):
```

Each normalized station is converted into a physical longitudinal coordinate:

```python
x = x0 + fraction * length
```

The CUF displacement is then evaluated at the required physical point and
compared with the analytical solution.

For the present bending validation, the exact longitudinal profile is:

```math
u_z(x)
=
u_{z,\max}
\sin\left(\pi\frac{x-x_0}{L}\right)
```

The adapter computes the relative magnitude error only where the analytical
reference is non-zero.

The sampling configuration therefore controls the evaluation of the already
computed solution without changing the underlying CUF model.

---

### Cross-sectional field verification

The adapter can also perform local checks over the physical section.

For the present example, the solved vertical displacement is sampled along
the complete outer bottom wall at mid-span.

The bottom-wall field check computes:

- minimum displacement;
- maximum displacement;
- mean displacement;
- maximum-minus-minimum spread.

This provides a direct check that the reconstructed CUF displacement field is
consistent over the physical loaded boundary.

The section is queried again through the same CSF representation, while the
displacement is obtained through the same solved-field interface.

The post-processing layer therefore combines:

```text
current physical section S(x)
              +
solved physical field u(x,y,z)
              |
              v
problem-specific verification
```

without requiring access to the CUF assembly internals.

---

### Output generation

The output directory is selected in the case YAML:

```yaml
output:
  directory: ../../../output/bending/legendre/N01
```

The adapter obtains the resolved directory through:

```python
output_dir = Path(case.output_dir)
```

and writes the analytical comparison report to:

```text
hollow_rectangle_analytical.txt
```

The generated report includes:

- geometry and material data obtained from CSF;
- applied load information;
- mid-span CUF displacement;
- Euler-Bernoulli reference displacement;
- relative error;
- bottom-wall displacement-field check;
- station-by-station CUF/analytical comparison.

The output format is therefore specific to this validation case, while the
computed CUF solution remains generic.

---

### Post-processing adapter interfaces

The adapter interacts with the general CSF-CUF infrastructure through a small
set of explicit interfaces.

| API | Role |
|---|---|
| `model_bridge.section_provider.domains(x)` | Query the physical domains of the current section |
| `model_bridge.domain_state(x, domain_id)` | Query the current material state of a section domain |
| `u(x, y, z)` | Evaluate the solved physical displacement field |
| `u.section_evaluator(x)` | Obtain an optimized evaluator for one cross-section, when available |
| `u.x_start`, `u.x_end` | Obtain the solved longitudinal domain |
| `problem_definition.problem_options` | Access problem-specific parameters such as load amplitude |
| `case.sampling.stations` | Access user-selected longitudinal sampling stations |
| `case.output_dir` | Access the configured output directory |

The post-processing adapter therefore depends only on public problem,
section, solution, and case interfaces.

It does not need to know:

- how the stiffness matrix was assembled;
- how the generalized CUF degrees of freedom were numbered;
- which linear solver was used;
- how the transverse basis was internally implemented;
- how the global algebraic system was constrained.

---

### Architectural role of `post.py`

The complete analysis chain can be written as:

```text
physical model
     |
     v
problem adapter
     |
     v
generic CUF solver
     |
     v
generic solved field
     |
     v
post-processing adapter
     |
     v
problem-specific validation / output
```

The case-specific code therefore remains at the boundary of the architecture.

The input side is handled by the structural problem adapter:

```text
problem.py
```

The output side is handled by the post-processing adapter:

```text
post.py
```

Between them, the generic CUF solver remains unchanged.

A new application can therefore introduce a different output adapter without
modifying the CUF core, just as a different structural problem can introduce a
different problem adapter without modifying the solver.

The post-processing layer is consequently a programmable external component
of the CSF-CUF framework rather than a specialization embedded in the CUF
implementation.
