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

## 5. Post-processing and external conventions

An example or comparison may express results in a different reference system, including the convention of a reference publication or an external solver.

The documentation accompanying those results must specify:

- the reference system used for point coordinates;
- the reference system used for displacement components;
- the component mapping, including any changes of sign;
- the definition of the longitudinal plot coordinate.

Point coordinates and displacement components may be reported in different conventions, provided both are explicitly identified.

For comparisons, all displacement results must be expressed in the same reference system and evaluated at corresponding physical points.

Any conversion applied during post-processing leaves the solver's coordinate convention unchanged. Example-specific mappings are documented with the relevant example.

## 6. Notation used in this document

Uppercase **(X, Y, Z)** identifies CSF coordinates, while lowercase **(x, y, z)** identifies CUF solver coordinates.

This distinction makes the correspondence explicit. When reading code, configuration files, plots, or exported data, the declared reference system determines the meaning of each coordinate and displacement component.
