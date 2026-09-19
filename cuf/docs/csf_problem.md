## Defining loads and boundary conditions

The structural problem is kept outside the generic CUF core.

For the present bending example, the case YAML selects the structural
problem adapter:

```yaml
problem:
  yaml: ../../../problems/bending/hollow_rectangle_bending_halfwave.yaml
  adapter: ../../../adapters/bending/problem.py
```

The adapter is the user-facing programmable location where loads and
boundary conditions are defined.

It does not implement a dedicated CUF solver. Instead, it uses the
general numerical services exposed by the CSF-CUF infrastructure while
keeping the physical definition of the structural problem outside the
CUF core.

For this example, the adapter defines:

```python
class HollowRectangleBendingProblem:
```

and exposes two principal operations:

```python
build_load_vector(...)
build_constraints(...)
```

The CUF core therefore does not contain any knowledge of the physical
load type or of the boundary-condition configuration used by this
problem.

A different structural loading can be introduced through the adapter
without modifying the CUF core.

### Loads

Loads are constructed by:

```python
def build_load_vector(
    self,
    *,
    section_provider,
    basis,
    mesh,
    dof_layout,
    longitudinal_integrator,
    x0: float,
    x1: float,
):
```

Before the load adapter is called, the solver has already constructed the
longitudinal discretization and the global CUF degree-of-freedom layout.

The adapter therefore receives the numerical infrastructure required to
construct its contribution directly in the global load vector.

For the present case, the physical load is a sinusoidal pressure applied
to the actual bottom material boundary of the section.

The current section is queried directly through:

```python
for domain in section_provider.domains(float(x)):
```

and the current transverse bounds through:

```python
transverse_bounds(section_provider, float(x))
```

Void domains are excluded and the actual material segments belonging to
the loaded boundary are identified from the current sectional state.

The load projection therefore operates on the physical boundary supplied
by

```math
\mathcal{S}(x)
```

rather than on a boundary embedded in the CUF core.

For every CUF transverse function the adapter evaluates:

```python
basis.value(tau, y, z_face)
```

and computes:

```math
B_\tau(x)
=
\int_{\Gamma(x)}
F_\tau(y,z)\,\mathrm{d}s
```

The longitudinal pressure law is:

```math
p(x)
=
p_0
\sin\left(
\frac{\pi(x-x_0)}{L}
\right)
```

with

```math
L=x_1-x_0
```

and the corresponding generalized longitudinal contribution is:

```math
q_\tau(x)
=
-p_0
\sin\left(
\frac{\pi(x-x_0)}{L}
\right)
B_\tau(x)
```

The adapter then uses the common longitudinal integration machinery:

```python
longitudinal_integrator.integrate_linear(
    element=element,
    load=field.value,
)
```

to project the longitudinal contribution onto the finite-element shape
functions.

For each resulting nodal contribution, the global CUF degree of freedom
is obtained through:

```python
dof_layout.index(
    node=node,
    tau=tau,
    component=component,
)
```

and the contribution is accumulated directly into the global load
vector.

The load path is therefore:

```text
physical surface pressure
        |
        v
section_provider -> current S(x)
        |
        v
actual loaded boundary
        |
        v
basis.value(tau, y, z)
        |
        v
sectional projection onto F_tau
        |
        v
q_tau(x)
        |
        v
longitudinal FE integration
        |
        v
GlobalDOFLayout
        |
        v
global load vector
        |
        v
generic CUF core
```

No load-specific object is passed to the CUF core.

In particular, the core does not distinguish between surface loads,
point loads, torsional loads, half-wave loads, or any other present or
future physical loading.

Each problem adapter is responsible for converting its physical loading
into a numerical contribution to the global load vector.

The CUF core receives only the resulting vector.

### Global degree-of-freedom layout

The global degree-of-freedom layout is constructed from the
longitudinal discretization before stiffness and load assembly.

It provides the common mapping:

```text
(node, tau, component) -> global DOF
```

and is shared by both the stiffness assembler and the problem adapter.

The adapter does not define or modify the global numbering. It only uses
the layout supplied by the CUF infrastructure:

```python
dof_layout.index(
    node=node,
    tau=tau,
    component=component,
)
```

This keeps the global CUF organization entirely under the control of the
core while allowing external problem adapters to construct their load
vectors independently.

### Boundary conditions

Boundary conditions are constructed by:

```python
def build_constraints(
    self,
    *,
    assembled,
    mesh,
    basis,
    longitudinal_integrator,
):
```

The adapter accesses the CUF degree-of-freedom layout through:

```python
layout = assembled.dof_layout
```

Individual generalized degrees of freedom are addressed through:

```python
layout.index(
    node=node,
    tau=tau,
    component=component,
)
```

For this simply supported bending problem, transverse generalized
amplitudes are constrained at the two end sections:

```python
for node in (0, mesh.number_of_nodes - 1):
    for component in (1, 2):
        for tau in range(1, int(basis.size) + 1):
            A[
                row,
                layout.index(
                    node=node,
                    tau=tau,
                    component=component,
                ),
            ] = 1.0
```

An additional scalar condition removes the free axial rigid translation
without suppressing an admissible axial deformation mode.

It uses the selected transverse basis:

```python
basis.value(tau, 0.0, 0.0)
```

and the common longitudinal integration API:

```python
longitudinal_integrator.integrate_linear(
    element=element,
    load=lambda x: 1.0,
)
```

The complete constraint system is returned through:

```python
LinearConstraintSystem(
    matrix=A,
    rhs=b,
    constraints=...
)
```

### Problem-adapter API

| API                                             | Role                                                                                     |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `section_provider.domains(x)`                   | Query the physical domains of the current section `S(x)`                                 |
| `transverse_bounds(section_provider, x)`        | Obtain the current transverse section bounds                                             |
| `basis.value(tau, y, z)`                        | Evaluate the selected CUF transverse function                                            |
| `basis.size`                                    | Obtain the number of available transverse functions                                      |
| `mesh`                                          | Access the longitudinal finite-element discretization                                    |
| `dof_layout`                                    | Access the global CUF degree-of-freedom organization                                     |
| `dof_layout.index(...)`                         | Map `(node, tau, component)` to a global CUF degree of freedom                           |
| `longitudinal_integrator.integrate_linear(...)` | Integrate a longitudinal scalar contribution against the longitudinal FE shape functions |
| `LinearConstraintSystem`                        | Return the complete constraint system to the solver                                      |

The adapter therefore depends only on general numerical services exposed
by the CSF-CUF infrastructure.

It does not require the CUF core to understand the physical meaning of a
load.

A new structural problem can define a different load law, load
localization, sectional projection, or boundary-condition configuration
while leaving unchanged:

* the continuous section representation;
* the CUF core;
* the transverse expansion implementation;
* the longitudinal finite-element machinery;
* the stiffness assembler;
* the global solver.

The structural problem is consequently a programmable external component
of the analysis.

The CUF core provides the numerical machinery, while the problem adapter
provides the physical problem definition and converts it into the
numerical quantities required by that machinery.
