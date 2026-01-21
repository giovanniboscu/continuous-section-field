# CSF → SAP2000  
## Explained Example 

This document explains **how a Section(z) defined in CSF** is exported and approximated
inside **SAP2000**, which does **not** natively support Section(z) as a continuous function.

The key idea is:

> **CSF defines the model (Section(z)); SAP2000 consumes a discretized approximation of it.**

Everything below is intentionally **verbose and explicit**, to avoid conceptual confusion.

---

## Conceptual Overview

- **CSF**
  - Defines the cross-section as a *function of z*.
  - Computes exact section properties:  
    \(A(z), I_{22}(z), I_{33}(z), I_{23}(z), J(z)\).
  - Is independent of any structural solver.

- **SAP2000**
  - Does **not** store Section(z) as a function.
  - Accepts only:
    - *local sections*, and
    - *nonprismatic assemblies* of those sections.
  - Approximates variation by **segmenting the frame**.

Therefore:
- Changing the number of segments in SAP2000 **does not change the CSF model**.
- It only changes the **numerical approximation**.

---

## 1. Local Section Definitions  
### (Computed by CSF)

```text
TABLE: "FRAME SECTION PROPERTIES 01 - GENERAL"
```

Each section below corresponds to a **single evaluation of Section(z)** performed by CSF
at a user-chosen location (for example, Gauss–Lobatto points).

```text
  SectionName=SEC_GL1  Area=0.25  I33=0.0052  I22=0.0052  I23=0.0    J=0.008
  SectionName=SEC_GL2  Area=0.20  I33=0.0045  I22=0.0038  I23=0.001  J=0.006
  SectionName=SEC_GL3  Area=0.18  I33=0.0040  I22=0.0032  I23=0.0015 J=0.005
```

### Important clarifications

- These are **not** integration points used internally by SAP2000.
- SAP2000 does **not** know anything about Gauss–Lobatto.
- The choice of locations is entirely the responsibility of CSF.

#### About *I23*
- **I23 is the product of inertia** of the local section.
- It is computed **exactly by CSF from geometry and weights**.
- **I23 ≠ twist**.
- A non-zero I23 indicates:
  - non-principal local axes, or
  - asymmetric geometry.

Twist along the beam axis must be handled **separately**
(e.g. via local axis rotation or segmented orientation),
not via I23.

---

## 2. Nonprismatic Frame Assembly  
### (Approximation inside SAP2000)

```text
TABLE: "FRAME SECTION PROPERTIES 05 - NONPRISMATIC"
```

Here, SAP2000 assembles the previously defined local sections
into a **piecewise approximation** of the continuous laws
defined in CSF.

```text
  Name=TRAVE_VAR
  NumberSegs=2

  Line=1  StartSec=SEC_GL1  EndSec=SEC_GL2
          Length=1.7267
          Type=Parabolic
          VarArea=Linear

  Line=2  StartSec=SEC_GL2  EndSec=SEC_GL3
          Length=3.2733
          Type=Parabolic
          VarArea=Linear
```

### Notes

- Each *Line* is a **numerical segment**, not a design concept.
- `Type=Parabolic` improves the interpolation of bending inertias.
- Increasing the number of segments:
  - improves accuracy,
  - does **not** change the CSF definition.

---

## 3. Centroid Drift / Offsets  
### (Discrete approximation)

SAP2000 does **not** support continuous centroid drift
\(x_c(z), y_c(z)\) along a frame.

Offsets must therefore be **approximated discretely**.

```text
TABLE: "FRAME END OFFSETS"
```

```text
  Frame=1  End=I  Offset2=0.00  Offset3=0.00
  Frame=1  End=J  Offset2=0.05  Offset3=0.02
```

### Interpretation

- Offsets describe the **shift of the section centroid**
  relative to the frame axis.
- For complex centroid paths:
  - the frame must be further segmented,
  - offsets assigned per segment.

Again:
- the centroid law lives in **CSF**,
- SAP2000 only approximates it.

---

## Final Summary

- **CSF**
  - defines Section(z) as a *design function*,
  - independent of discretization and solver.

- **SAP2000**
  - receives only a segmented, nonprismatic approximation,
  - has no knowledge of the underlying continuous law.

> **CSF defines the model.  
> SAP2000 approximates it.**

This separation is intentional and fundamental.


$ =============================================================
$ EXAMPLE SAP2000 INPUT FILE (TEXT)
$ Generated as an example export from CSF
$ Purpose: illustrate how a continuous Section(z) is approximated
$          in SAP2000 using nonprismatic frame sections.
$
$ IMPORTANT:
$ - SAP2000 does NOT support Section(z) as a function.
$ - All data below are a DISCRETIZED APPROXIMATION of a CSF model.
$ - Changing the number of segments changes only the approximation,
$   NOT the original CSF definition.
$ =============================================================

$ -------------------------------------------------------------
$ LOCAL SECTION PROPERTIES (computed by CSF)
$ -------------------------------------------------------------
TABLE: "FRAME SECTION PROPERTIES 01 - GENERAL"

  SectionName=SEC_GL1  Material=STEEL  Area=0.25
    I22=0.0052  I33=0.0052  I23=0.0   J=0.008

  SectionName=SEC_GL2  Material=STEEL  Area=0.20
    I22=0.0038  I33=0.0045  I23=0.001 J=0.006

  SectionName=SEC_GL3  Material=STEEL  Area=0.18
    I22=0.0032  I33=0.0040  I23=0.0015 J=0.005


$ NOTES:
$ - Each section corresponds to a single evaluation of Section(z).
$ - The locations (e.g. Gauss–Lobatto points) are chosen by CSF.
$ - SAP2000 does not use these as integration points.
$ - I23 is the product of inertia (non-principal axes), NOT twist.

$ -------------------------------------------------------------
$ NONPRISMATIC FRAME SECTION
$ -------------------------------------------------------------
TABLE: "FRAME SECTION PROPERTIES 05 - NONPRISMATIC"

  Name=TRAVE_VAR
  NumberSegs=2

  Line=1  StartSec=SEC_GL1  EndSec=SEC_GL2
          Length=1.7267
          Type=Parabolic
          VarArea=Linear

  Line=2  StartSec=SEC_GL2  EndSec=SEC_GL3
          Length=3.2733
          Type=Parabolic
          VarArea=Linear

$ NOTES:
$ - Each segment approximates the continuous laws A(z), I(z), J(z).
$ - 'Parabolic' improves interpolation of bending inertias.
$ - Increasing segments improves accuracy but does not change the model.

$ -------------------------------------------------------------
$ FRAME ASSIGNMENT
$ -------------------------------------------------------------
TABLE: "FRAME SECTION ASSIGNMENTS"

  Frame=1  Section=TRAVE_VAR


$ -------------------------------------------------------------
$ FRAME END OFFSETS (CENTROID DRIFT APPROXIMATION)
$ -------------------------------------------------------------
TABLE: "FRAME END OFFSETS"

  Frame=1  End=I  Offset2=0.00  Offset3=0.00
  Frame=1  End=J  Offset2=0.05  Offset3=0.02

$ NOTES:
$ - SAP2000 does not support continuous centroid drift xc(z), yc(z).
$ - Offsets are assigned discretely at frame ends or per segment.
$ - The centroid law is defined in CSF, approximated here.

$ =============================================================
$ END OF EXAMPLE FILE
$ =============================================================

