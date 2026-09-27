# Coordinate Systems and Displacement Conventions

This document defines the coordinate correspondence between CSF and the CSF–CUF solver, and the displacement convention used in the I-Shape comparison.

The term **CUF solver** refers here to the implementation in this repository.

## 1. CSF coordinate system

CSF uses the coordinates **(X, Y, Z)**:

- **X, Y** define the cross-section plane;
- **Z** is the longitudinal coordinate along the beam.

The corresponding displacement components are u<sub>X</sub>, u<sub>Y</sub>, and u<sub>Z</sub>. The longitudinal component is **u<sub>Z</sub>**.

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

## 4. I-Shape comparison: paper convention

The I-Shape example retains the displacement notation of Carrera and Giunta (2010) in its reported results and comparison plots.

Both CUF and FEM3D displacement results are converted to this convention using the same mapping:

| Reported component (paper notation) | Solver component | CSF direction |
| --- | --- | --- |
| u<sub>x</sub> | −u<sub>z</sub> | −Y |
| u<sub>y</sub> | u<sub>y</sub> | +X |
| u<sub>z</sub> | u<sub>x</sub> | +Z (longitudinal) |

Therefore, **u<sub>z</sub> in the I-Shape plots is the longitudinal displacement**. It corresponds to u<sub>x</sub> in the solver and u<sub>Z</sub> in CSF.

The minus sign in the first reported component accounts for the reversed transverse direction in the paper convention.

This transformation is applied during post-processing. The solver continues to use its own coordinate system.

### Point coordinates

Point coordinates in the I-Shape plot titles and CSV coordinate columns are expressed in the **CSF system (X, Y, Z)**.

These coordinate labels must be distinguished from the displacement labels, which follow the paper convention.

### Longitudinal plot coordinate

The plot abscissa **x/L** uses the CUF longitudinal coordinate, where L is the beam length.

For the I-Shape models, the longitudinal origin is at the initial section, so **x/L = Z/L**.

## 5. Documentation convention

Throughout the documentation:

- **CSF coordinates** are identified as (X, Y, Z).
- **CUF solver coordinates** are identified as (x, y, z).
- Displacement components presented in another convention are accompanied by an explicit mapping.
- The paper convention described in Section 4 applies specifically to the I-Shape comparison and must not be assumed for other examples.
