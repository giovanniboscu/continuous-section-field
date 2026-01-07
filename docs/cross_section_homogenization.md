# Continuous Section Field (CSF)

The **Continuous Section Field (CSF)** framework provides a continuous description of non-prismatic and multi-material beam members by generating longitudinally varying cross-section properties without resorting to piecewise-prismatic discretization.

CSF models stiffness and mass properties as continuous fields derived from geometry and material layout, enabling accurate representation of tapered sections, composite layouts, and gradual material participation along the beam axis.

---

## Key Features

- Continuous cross-section properties along the beam axis
- Support for non-prismatic and multi-material sections
- Geometry defined by ruled surfaces between arbitrary end sections
- Section-level homogenization based on elastic equivalence
- Longitudinally varying homogenization factors
- Direct export of sectional properties and structural models
- Native Python library with optional file-based wrapper
- OpenSees-ready output

---

## Conceptual Overview

In CSF, a beam is described by:
1. A **geometric definition** (axis, end sections, ruled surfaces)
2. A **cross-section layout** composed of multiple material sub-domains (patches)
3. A **continuous homogenization process** that produces equivalent linear-elastic section properties as functions of the longitudinal coordinate

The beam is *not* discretized into prismatic elements.  
Instead, sectional properties such as area, inertia, and stiffness are evaluated continuously.

---

## Cross-Section Homogenization

Each cross-section may contain multiple material patches.  
For each patch, a reference elastic modulus is defined.

The effective elastic modulus of each patch is obtained through a **homogenization factor**:

```text
E_i(z) = w_i(z) * E_ref,i
where:

z is the longitudinal coordinate along the beam axis

i identifies a specific cross-section patch

w_i(z) is a dimensionless homogenization factor

E_ref,i is the reference elastic modulus of the patch

Multiple homogenization factors may coexist within the same section:



