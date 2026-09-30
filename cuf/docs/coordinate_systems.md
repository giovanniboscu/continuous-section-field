# Coordinate Systems and Displacement Conventions

This document defines the coordinate systems used by CSF and the CSF–CUF solver, together with the correspondence between their coordinates and displacement components.

The term **CUF solver** refers to the implementation in this repository.

## 1. CSF coordinate system

CSF uses the coordinates **(X, Y, Z)**:

- **X, Y** define the cross-section plane;
- **Z** is the longitudinal coordinate along the beam.

Displacement components expressed in this system are denoted by u<sub>X</sub>, u<sub>Y</sub>, and u<sub>Z</sub>. The longitudinal component is **u<sub>Z</sub>**.

## 2. CUF solver coordinate system

The CSF–CUF solver uses the coordinates **(x, y, z)**:

- **x** is the longitudinal coordinate along the beam;
- **y, z** define the cross-section plane.

The solver returns the displacement field **u(x, y, z)**, with components u<sub>x</sub>, u<sub>y</sub>, and u<sub>z</sub>. The longitudinal component is **u<sub>x</sub>**.

## 3. CSF–CUF correspondence

The same physical point is represented by:

**(x, y, z)<sub>CUF</sub> = (Z, X, Y)<sub>CSF</sub>**

| Physical direction | CSF coordinate | CUF coordinate |
| --- | --- | --- |
| Longitudinal | Z | x |
| First transverse direction | X | y |
| Second transverse direction | Y | z |

The displacement components follow the same correspondence:

| Displacement direction | CSF component | CUF component |
| --- | --- | --- |
| Longitudinal | u<sub>Z</sub> | u<sub>x</sub> |
| First transverse direction | u<sub>X</sub> | u<sub>y</sub> |
| Second transverse direction | u<sub>Y</sub> | u<sub>z</sub> |

This correspondence changes the coordinate labels and component order without reversing any direction.

To evaluate the solver displacement field at a point expressed in CSF coordinates **(X, Y, Z)**, the solver arguments are therefore **u(Z, X, Y)**. The returned components remain ordered according to the CUF system.

## 4. Longitudinal position

The longitudinal coordinates satisfy **x = Z**.

For a beam of length L whose initial section is located at x<sub>0</sub> = Z<sub>0</sub>, the normalized longitudinal position is:

**s = (x − x<sub>0</sub>)/L = (Z − Z<sub>0</sub>)/L**

When the longitudinal origin coincides with the initial section, this reduces to **s = x/L = Z/L**.



