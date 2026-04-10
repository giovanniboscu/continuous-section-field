# OpenFAST Analysis Description for the Current Workflow

## What analysis this workflow is targeting

This workflow prepares an OpenFAST case for a **time-domain structural-dynamics simulation** using **ElastoDyn**.

According to the official OpenFAST documentation, OpenFAST is a framework for simulating the **coupled dynamic response** of wind turbines in the **time domain**.

In this setup, the structural module is selected through:

- `CompElast = 1`

which corresponds to **ElastoDyn**, the structural-dynamics module of OpenFAST.

---

## Scope of the analysis: structural only, no aerodynamics

This is a **pure structural case**.

The aerodynamic and inflow modules are explicitly disabled:

- `CompAero = 0` - no aerodynamic loads
- `CompInflow = 0` - no inflow wind field
- `CompSub = 0` - no sub-structural dynamics
- `CompServo = 0` - no control or electrical-drive dynamics

This means the structural response is driven entirely by **initial conditions**, not by wind loads.

The initial conditions set in `ElastoDyn.dat` are:

- `TTDspFA = 0.01 m` - a small fore-aft tower-top displacement used to excite tower motion
- `TTDspSS = 0.0 m` - side-to-side displacement, initially at rest

The simulation therefore computes the **free decay response** of the tower from this initial perturbation.

This is consistent with the intended use of the workflow: validating the structural model and the tower properties generated from CSF, before introducing aerodynamic or control complexity.

---

## What ElastoDyn defines

According to the official ElastoDyn documentation, the primary ElastoDyn input file defines:

- structural modeling options
- geometry of the structure (tower, nacelle, drivetrain, blades)
- initial conditions
- masses and inertias
- tower properties
- output configuration

The ElastoDyn module is therefore responsible for the **structural definition and dynamic behavior** of the system within OpenFAST.

---

## Nature of the analysis

The analysis performed is a **dynamic simulation in the time domain**.

ElastoDyn computes, as part of the simulation:

- structural positions
- velocities
- accelerations

This means the workflow produces a case that is executed as a **time-marching dynamic simulation**, not a static evaluation.

---

## Active degrees of freedom

The following tower DOFs are active in the current configuration:

- `TwFADOF1 = True` - first fore-aft bending mode
- `TwSSDOF1 = True` - first side-to-side bending mode

All blade, drivetrain, generator, yaw, and platform DOFs are disabled.

This isolates the structural response to **tower bending only**, which is the quantity of interest when validating the CSF-derived tower properties.

---

## Practical purpose of the workflow

The purpose of the workflow is to:

- generate a valid set of OpenFAST input files,
- define the structural system through ElastoDyn inputs,
- allow OpenFAST to run a **time-domain structural simulation** of the tower-based system.

The workflow automates the creation of:

- `*_Main.fst`
- `*_ElastoDyn.dat`
- `*_ElastoDyn_Tower.dat`
- `*_ElastoDyn_Blade.dat`

These files together define a complete structural simulation case for OpenFAST.

The tower distributed properties (`TMassDen`, `TwFAStif`, `TwSSStif`) are not defined manually.  
They are generated automatically from the CSF geometry model by `csf_to_openfast.py`.  
See `readme.md` for the full generation workflow.

---

## Summary

This workflow prepares a minimal OpenFAST structural case for a time-domain
structural-dynamics simulation using ElastoDyn. ElastoDyn defines the structural
modeling options, geometry, initial conditions, masses, inertias, tower data, and
outputs required to simulate the structural response of the system.

Aerodynamic and inflow loads are disabled. The simulation captures the free decay
response of the tower from a small initial fore-aft displacement, using tower
properties derived automatically from the CSF continuous geometry model.

---

## OpenFAST references

The description above is supported by:

1. OpenFAST documentation
   - OpenFAST is a framework for simulating the **coupled dynamic response** of wind turbines in the **time domain**.

2. OpenFAST solver documentation
   - `CompElast = 1` selects **ElastoDyn** as the structural-dynamics module.

3. ElastoDyn input documentation
   - The ElastoDyn primary input file defines structural modeling options, geometry, and initial conditions.

4. ElastoDyn theory documentation
   - ElastoDyn computes structural kinematics including positions, velocities, and accelerations.

---

> **Note on mode-shape coefficients**
> The tower mode-shape coefficients in this workflow are polynomial placeholders
> (parabolic for mode 1, `x⁶` for mode 2). They satisfy the ElastoDyn sum-to-1
> constraint and allow OpenFAST to run, but do not represent the real modal
> properties of the tower. For physically accurate mode shapes, run BModes on
> the generated tower file and inject the fitted coefficients - see
> [openfastguide.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/actions-examples/histwin/openfastguide.md).
