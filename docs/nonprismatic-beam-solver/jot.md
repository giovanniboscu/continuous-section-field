# jot.md

# Operational workflow notes

## Current objective

The immediate goal is to move from the documented Balduzzi 2016 reduced model to a fully operational numerical workflow.

At this stage, the priority is no longer to restate the theory, but to define a step-by-step implementation path that leaves no missing quantities between model definition and numerical solution.

The final workflow must be complete: starting from geometry, material, loads, and boundary conditions, it must provide all reduced quantities required by the model and all data needed by the solver.

## General principle

For every quantity appearing in the reduced formulation, it must eventually be clear whether it is:

- directly assigned,
- numerically derived,
- numerically integrated,
- imposed as a boundary condition,
- or solved for by the reduced beam solver.

A quantity that belongs to the model but has no operational path is a missing piece in the workflow.

## Current status

The following documents are already available as first drafts:

- `geometric_material_model.md`
- `load_boundary_condition_model.md`
- `reduced_model_input_data.md`
- `balduzzi_solver.md`

These define the conceptual structure of the problem.

The next work is to turn that structure into a practical implementation workflow.

## Step 1 - Fix the minimum reference problem

Before writing code, define a minimum complete test problem consistent with the original Balduzzi 2016 formulation.

The minimum reference problem should include:

- a 2D non-prismatic beam;
- homogeneous isotropic linear-elastic material;
- prescribed geometric functions `c(x)` and `h(x)`;
- prescribed reduced loads `q(x)`, `m(x)`, and `p(x)`;
- prescribed end boundary conditions at `x = 0` and/or `x = l`.

This first case should be simple, fully controlled, and independent of CSF.

Its only purpose is to verify that the reduced model can be solved numerically from end to end.

## Step 2 - Define the reduced solver contract

The solver must receive a clear and minimal reduced input contract.

This contract must include:

### Geometry
- `c(x)`
- `h(x)`
- `c'(x)`
- `h'(x)`

### Material
- `E`
- `G`

### Loads
- `q(x)`
- `m(x)`
- `p(x)`

### Boundary conditions
Prescribed end conditions on suitable subsets of:
- `u`
- `v`
- `phi`
- `H`
- `M`
- `V`

The contract must be solver-oriented and independent of the source of the geometry.

This is the key separation point: the solver must only see the reduced problem data.

## Step 3 - Decide the numerical representation of the input functions

The reduced input functions must be given a precise numerical form.

Possible options include:

- direct analytical callables;
- tabulated sampled data with interpolation;
- wrapped functions extracted from an upstream geometry engine.

The solver should ideally work with a uniform callable interface, for example:

- `c(x) -> float`
- `h(x) -> float`
- `dc(x) -> float`
- `dh(x) -> float`
- `q(x) -> float`
- `m(x) -> float`
- `p(x) -> float`

This allows analytical and numerically reconstructed inputs to share the same downstream interface.

## Step 4 - Define the reduced problem object

A reduced problem object must be introduced before the solver.

Its purpose is to collect:

- the reduced geometric input,
- the material parameters,
- the reduced loads,
- the end boundary conditions.

This object does not solve the problem. It only states that the reduced problem is fully defined and ready to be passed to the solver.

A future implementation may use a container such as:

- `ReducedBalduzziInput`

The exact software design is open, but the logical role is already fixed.

## Step 5 - Fix the solver state variables

The reduced Balduzzi problem uses six unknown beam quantities:

- `u(x)`
- `v(x)`
- `phi(x)`
- `H(x)`
- `M(x)`
- `V(x)`

These quantities define the natural state of the problem.

From a numerical viewpoint, the solver will evolve or determine these six variables over the interval `x in [0, l]`.

## Step 6 - Translate the formulation into a numerical first-order system

The paper must now be re-read with one practical goal:

derive a numerical system of the form

`state'(x) = F(x, state(x), inputs)`

where

`state = [u, v, phi, H, M, V]`

The derivation does not need to be reproduced symbolically in the documentation.

What is required is the operational form needed by the implementation:

- what the state vector is;
- what quantities are evaluated locally along `x`;
- how the derivatives of the state are computed.

This is the first true solver-building step.

## Step 7 - Define the operational boundary-condition format

Boundary conditions must be represented explicitly and not only described conceptually.

They must identify:

- the beam variable involved;
- the beam end (`x = 0` or `x = l`);
- the prescribed value.

Examples:

- `u(0) = 0`
- `v(0) = 0`
- `phi(0) = 0`
- `H(l) = 0`
- `M(l) = 0`
- `V(l) = 0`

This means that the implementation will need a boundary-condition representation such as:

- variable name
- beam end
- assigned value

A complete reduced beam problem requires a consistent set of end conditions.

## Step 8 - Choose the numerical solution strategy

Once the reduced first-order system and the end conditions are fixed, a numerical solution strategy must be selected.

The natural candidates are:

- a boundary value problem approach;
- a shooting approach.

Since the reduced problem is naturally posed with data at both ends, a boundary value problem formulation is likely the most natural first implementation route.

This choice belongs to the numerical strategy layer and must remain separate from the reduced model itself.

## Step 9 - Implement a first fully analytical reference case

Before connecting the workflow to CSF, implement one fully analytical test case in which:

- `c(x)` is given explicitly;
- `h(x)` is given explicitly;
- `q(x)`, `m(x)`, `p(x)` are given explicitly;
- the end conditions are simple and fully known.

This first case must be used to verify:

- reduced input contract;
- first-order system assembly;
- numerical enforcement of end conditions;
- consistency of the computed solution.

This is the first end-to-end verification of the reduced solver.

## Step 10 - Prepare the future CSF adapter layer

Only after the reduced solver works on an analytical case should the geometry-source integration be addressed.

The future CSF adapter will be responsible for supplying the reduced geometric quantities required by the solver.

At that stage, the adapter will need to provide:

- `c(x)`
- `h(x)`
- `c'(x)`
- `h'(x)`

from a more general sectional description.

This means that the solver itself must remain independent of CSF, while still being fully compatible with a CSF-driven workflow.

The adapter belongs upstream of the solver.

## Step 11 - Build the first CSF-based complete example

After the analytical reference case is working, the first complete CSF-based example can be built.

That workflow will consist of:

1. obtaining the local section geometry from CSF,
2. extracting or computing the reduced geometric quantities,
3. defining the load model independently,
4. imposing the end boundary conditions,
5. solving the reduced beam problem numerically.

This will be the first realistic end-to-end test of the whole workflow.

## Step 12 - Final closure check

At the end of the workflow, no quantity required by the reduced model should remain undefined from an operational point of view.

For each quantity, it must be known whether it is:

- assigned directly,
- derived numerically,
- integrated numerically,
- prescribed at the boundary,
- or solved by the beam system.

This closure check is the practical criterion for deciding whether the workflow is complete.

## Immediate next action

The immediate next action is:

**define the reduced input contract of the solver in operational terms, without yet writing the numerical algorithm itself.**

This is the next mandatory step before implementation.
