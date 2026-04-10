# OpenFAST Analysis Description for the Current Workflow

## What analysis this workflow is targeting

This workflow prepares an OpenFAST case for a **time-domain structural-dynamics simulation** using **ElastoDyn**.

According to the official OpenFAST documentation, OpenFAST is a framework for simulating the **coupled dynamic response** of wind turbines in the **time domain**.

In this setup, the structural module is selected through:

- `CompElast = 1`

which corresponds to **ElastoDyn**, the structural-dynamics module of OpenFAST.

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

---

## Reference wording

The following wording is directly consistent with the OpenFAST documentation:

> This workflow prepares a minimal OpenFAST structural case for a time-domain structural-dynamics simulation using ElastoDyn. ElastoDyn defines the structural modeling options, geometry, initial conditions, masses, inertias, tower data, and outputs required to simulate the structural response of the system.

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

## Final definition

> The workflow generates a valid OpenFAST input set that enables a time-domain structural-dynamics simulation of the system using ElastoDyn.
