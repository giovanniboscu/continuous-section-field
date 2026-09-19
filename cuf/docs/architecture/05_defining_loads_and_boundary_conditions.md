# Defining loads and boundary conditions

Loads and boundary conditions are defined outside the CUF core.

This is an important design principle of CSF-CUF: the generic solver provides the numerical machinery, while the structural problem adapter defines the physical problem.

For the present bending example, the case YAML selects the problem description and the corresponding adapter:

```yaml
problem:
  yaml: ../../../problems/bending/hollow_rectangle_bending_halfwave.yaml
  adapter: ../../../adapters/bending/problem.py
```

The adapter is therefore the place to modify when a different loading or a different set of boundary conditions is required.

There is no need to modify the CUF solver itself.

## What the problem adapter does

For this example, the adapter defines:

```python
class HollowRectangleBendingProblem:
```

Its two main responsibilities are:

```python
build_load_vector(...)
build_constraints(...)
```

`build_load_vector(...)` converts the physical loading into the global numerical load vector used by the solver.

`build_constraints(...)` defines the boundary conditions of the structural problem.

The CUF core does not need to know whether the applied load is a surface pressure, a point force, a torsional load, a sinusoidal load, or another type of loading.

It only receives the final numerical quantities required to solve the system.

---

## Defining the load

The load vector is constructed by:

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

The solver supplies the adapter with the numerical tools required to construct the load:

- `section_provider` gives access to the current physical section;
- `basis` gives access to the CUF transverse expansion functions;
- `mesh` describes the longitudinal finite-element discretization;
- `dof_layout` identifies the position of each CUF degree of freedom in the global system;
- `longitudinal_integrator` performs the longitudinal finite-element integration;
- `x0` and `x1` define the longitudinal domain.

The adapter uses these services but remains responsible for the physical definition of the load.

### Example: sinusoidal pressure on the bottom boundary

In this example, a sinusoidal pressure is applied to the actual bottom material boundary of the section.

At any longitudinal coordinate `x`, the adapter queries the current CSF section:

```python
for domain in section_provider.domains(float(x)):
```

and obtains its current transverse bounds through:

```python
transverse_bounds(section_provider, float(x))
```

This is important for non-prismatic members.

The loaded boundary is not stored as a fixed geometry inside the CUF solver. It is obtained from the current physical section $`\mathcal{S}(x)`$ provided by CSF.

Void regions are excluded, and only the actual material segments belonging to the loaded boundary contribute to the load.

For each CUF transverse function $`F_\tau`$, the adapter evaluates:

```python
basis.value(tau, y, z_face)
```

and computes the sectional projection:

```math
B_\tau(x)
=
\int_{\Gamma(x)} F_\tau(y,z)\,\mathrm{d}s
```

The prescribed pressure varies longitudinally as:

```math
p(x)
=
p_0
\sin\left(
\frac{\pi(x-x_0)}{L}
\right),
\qquad
L=x_1-x_0
```

The corresponding generalized CUF contribution is:

```math
q_\tau(x)
=
-p_0
\sin\left(
\frac{\pi(x-x_0)}{L}
\right)
B_\tau(x)
```

The adapter then projects this quantity onto the longitudinal finite-element shape functions using the common integration service:

```python
longitudinal_integrator.integrate_linear(
    element=element,
    load=field.value,
)
```

Each resulting contribution is finally placed in the correct position of the global load vector through:

```python
dof_layout.index(
    node=node,
    tau=tau,
    component=component,
)
```

The complete load path is therefore:

```text
physical load
    |
    v
current CSF section S(x)
    |
    v
physical loaded boundary
    |
    v
CUF transverse projection
    |
    v
longitudinal FE integration
    |
    v
global CUF DOF
    |
    v
global load vector
```

The CUF core receives only the resulting global load vector.

It does not contain any load-specific logic.

---

## Why the DOF layout is provided to the adapter

The global solver stores all unknowns in a single vector.

A CUF degree of freedom is identified by:

```text
(longitudinal node, transverse term tau, displacement component)
```

The `GlobalDOFLayout` converts this information into the corresponding position in the global vector.

For example:

```python
dof = dof_layout.index(
    node=node,
    tau=tau,
    component=component,
)
```

The adapter does not define this numbering.

The numbering is created by the CUF infrastructure and then made available to the adapter.

This guarantees that the load vector constructed by the adapter and the stiffness matrix constructed by the CUF core use exactly the same global organization.

---

## Defining the boundary conditions

Boundary conditions are constructed independently through:

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

The adapter obtains the global degree-of-freedom layout through:

```python
layout = assembled.dof_layout
```

and can therefore address any generalized CUF degree of freedom.

For the present simply supported bending problem, transverse generalized amplitudes are constrained at both ends:

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

An additional scalar condition removes the free axial rigid-body translation without suppressing an admissible axial deformation mode.

The constraint uses the selected CUF transverse basis:

```python
basis.value(tau, 0.0, 0.0)
```

together with the same longitudinal integration machinery used elsewhere in the solver:

```python
longitudinal_integrator.integrate_linear(
    element=element,
    load=lambda x: 1.0,
)
```

The complete set of constraints is returned as:

```python
LinearConstraintSystem(
    matrix=A,
    rhs=b,
    constraints=...
)
```

---

## What a user normally needs to change

To define a new structural problem, the usual workflow is:

1. create or modify the problem YAML;
2. create or modify the corresponding problem adapter;
3. define how the physical load is projected into the global load vector;
4. define the required boundary conditions.

The CUF core does not need to be changed.

The adapter can use the following general services:

| Service | Purpose |
|---|---|
| `section_provider.domains(x)` | Query the current physical section |
| `transverse_bounds(section_provider, x)` | Obtain the current section bounds |
| `basis.value(tau, y, z)` | Evaluate a CUF transverse function |
| `basis.size` | Obtain the number of transverse functions |
| `mesh` | Access the longitudinal FE discretization |
| `dof_layout.index(...)` | Locate a CUF degree of freedom in the global system |
| `longitudinal_integrator.integrate_linear(...)` | Perform longitudinal FE integration |
| `LinearConstraintSystem` | Return the boundary-condition system |

The important distinction is:

```text
Problem adapter
    defines the physics

CUF core
    provides the numerical machinery
```

A new load or a new structural problem should therefore require changes only in the problem-side code.

The CUF core remains unchanged.
