## Defining loads and boundary conditions

The structural problem is kept outside the generic CUF solver.

For the present bending example, the case YAML selects the structural
problem adapter:

``` yaml
problem:
  yaml: ../../../problems/bending/hollow_rectangle_bending_halfwave.yaml
  adapter: ../../../adapters/bending/problem.py
```

The adapter is the user-facing programmable location where loads and
boundary conditions are defined.

It does not implement a dedicated CUF solver. Instead, it connects the
particular structural problem to the generic solver through the common
CSF-CUF problem interfaces.

For this example, the adapter defines:

``` python
class HollowRectangleBendingProblem:
```

and exposes two principal operations used by the generic solver:

``` python
build_loads(...)
build_constraints(...)
```

The CUF core is therefore not modified when the structural loading or
the boundary conditions are changed.

### Loads

Loads are constructed by:

``` python
def build_loads(
    self,
    *,
    section_provider,
    basis,
    x0: float,
    x1: float,
):
```

The generic solver supplies the adapter with the current continuous
section provider, the selected CUF transverse basis, and the beginning
and end coordinates of the longitudinal domain.

For the present case, the load is a sinusoidal pressure applied to the
actual bottom material boundary of the section.

The current section is queried directly through:

``` python
for domain in section_provider.domains(float(x)):
```

and the current transverse bounds through:

``` python
transverse_bounds(section_provider, float(x))
```

Void domains are excluded and the actual material segments belonging to
the loaded boundary are identified from the current sectional state.

The load projection therefore operates on the physical boundary supplied
by

``` math
\mathcal{S}(x)
```

rather than on a boundary embedded in the CUF solver.

For every CUF transverse function the adapter evaluates:

``` python
basis.value(tau, y, z_face)
```

and computes:

``` math
B_\tau(x)=\int_{\Gamma(x)}F_\tau(y,z)\,\mathrm{d}s
```

The longitudinal pressure law is:

``` math
p(x)=p_0\sin\left(\frac{\pi(x-x_0)}{L}\right)
```

with

``` math
L=x_1-x_0
```

and the generalized load is:

``` math
q_\tau(x)=-p_0\sin\left(\frac{\pi(x-x_0)}{L}\right)B_\tau(x)
```

The adapter exposes each generalized load through:

``` python
GeneralizedLongitudinalLoad(
    tau=tau,
    component="z",
    field=ModeSurfaceLoadField(projector, tau),
)
```

The longitudinal variation implements the common interface:

``` python
class ModeSurfaceLoadField(ScalarLoadField):
    def value(self, x: float) -> float:
        ...
```

The load path is therefore:

``` text
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
ScalarLoadField
        |
        v
GeneralizedLongitudinalLoad
        |
        v
generic CUF solver
```

### Boundary conditions

Boundary conditions are constructed by:

``` python
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

``` python
layout = assembled.dof_layout
```

Individual generalized degrees of freedom are addressed through:

``` python
layout.index(
    node=node,
    tau=tau,
    component=component,
)
```

For this simply supported bending problem, transverse generalized
amplitudes are constrained at the two end sections:

``` python
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

``` python
basis.value(tau, 0.0, 0.0)
```

and the common longitudinal integration API:

``` python
longitudinal_integrator.integrate_linear(
    element=element,
    load=lambda x: 1.0,
)
```

The complete constraint system is returned through:

``` python
LinearConstraintSystem(
    matrix=A,
    rhs=b,
    constraints=...
)
```

### Problem-adapter API

  -------------------------------------------------------------------------------------
  API                                               Role
  ------------------------------------------------- -----------------------------------
  `section_provider.domains(x)`                     Query the physical domains of the
                                                    current section `S(x)`

  `transverse_bounds(section_provider, x)`          Obtain the current transverse
                                                    section bounds

  `basis.value(tau, y, z)`                          Evaluate the selected CUF
                                                    transverse function

  `basis.size`                                      Obtain the number of active
                                                    transverse functions

  `ScalarLoadField.value(x)`                        Define a generalized longitudinal
                                                    load field

  `GeneralizedLongitudinalLoad`                     Pass a generalized CUF load to the
                                                    solver

  `assembled.dof_layout`                            Access the global CUF DOF
                                                    organization

  `dof_layout.index(...)`                           Address a generalized CUF DOF

  `longitudinal_integrator.integrate_linear(...)`   Integrate a longitudinal scalar
                                                    contribution

  `LinearConstraintSystem`                          Pass the complete constraint system
                                                    to the solver
  -------------------------------------------------------------------------------------

The adapter imports the common interfaces directly from the CSF-CUF
infrastructure:

``` python
from csf.cuf.problem.point_bc import LinearConstraintSystem
from csf.cuf.problem.problem import (
    GeneralizedLongitudinalLoad,
    ScalarLoadField,
)
```

A new structural problem can therefore define different loads and
boundary conditions through the problem adapter while leaving the
continuous section representation, CUF core, transverse expansion
implementation, longitudinal finite-element machinery, and global solver
unchanged.

The structural problem is consequently a programmable external component
of the analysis rather than a specialization embedded in the CUF core.
