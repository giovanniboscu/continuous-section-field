# DRAFT

# Model - C-section geometry and material

[← C-section benchmark](../readme.md) · [Problem](cshape-problem.md) · [Case](cshape-cases.md)

## What does the model describe?

The **model** describes the physical beam independently of its loading and of the numerical approximation. In this example, CSF defines a prismatic open C-section through its polygonal cross-section and material data.

Source: [`models/c_section_chapter9_5_3_9L9_csf.yaml`](../models/c_section_chapter9_5_3_9L9_csf.yaml).

## Physical data

| Quantity | Value |
| --- | ---: |
| Beam length, $L$ | 20,000 mm |
| Section height, $h$ | 1,000 mm |
| Upper flange width, $b_2$ | 1,000 mm |
| Lower flange width, $b_1$ | 500 mm |
| Wall thickness, $t$ | 100 mm |
| Young's modulus, $E$ | 75,000 MPa |
| Poisson's ratio, $\nu$ | 0.33 |

The section opens toward the negative local transverse coordinate; its web is on the right and its longer flange is at the top.

## How the YAML represents it

The `CSF.sections` mapping specifies two stations, `S0` at `z: 0.0` and `S1` at `z: 20000.0`. Each station contains the **same nine named quadrilateral polygons**, so the geometry is prismatic.

The nine domains are grouped as follows:

- **Upper flange:** `top_1`, `top_2`, `top_3`, `top_4`, `top_web_corner`.
- **Web:** `web`.
- **Lower flange:** `bottom_1`, `bottom_2`, `bottom_web_corner`.

Each polygon lists four physical vertices and `weight: 75000.0`. In this CUF example, that weight represents the elastic modulus in the adopted N–mm–MPa system. The section also specifies `shear_weight_laws: ['iso(0.33)']`, corresponding to the isotropic relation between $E$, $G$ and $\nu$.

A representative fragment (the actual file provides all nine polygons at both stations):

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        - name: top_1
          weight: 75000.0
          vertices:
            - [-1000.0, 400.0]
            - [-775.0,  400.0]
            - [-775.0,  500.0]
            - [-1000.0, 500.0]
    S1:
      z: 20000.0
      polygons: # same nine domains and coordinates as S0
  shear_weight_laws:
    - 'iso(0.33)'
```

The fragment is **illustrative**, not a complete input file; use the linked YAML to reproduce the model.

## Nine polygons

The layout follows the nine-domain L9 partition shown in Carrera and Petrolo's reference figure. CSF supplies the physical domains; the independent transverse basis later supplies the Lagrange interpolation on those domains. **A polygon is a geometric domain, not a longitudinal finite element.**

The paper illustrates the subdivision but does not tabulate its internal coordinates. The flange partition used here reconstructs them from the figure: four 225 mm subdivisions of the upper free flange and two 200 mm subdivisions of the lower free flange, with 100 mm corner domains adjoining the web. These internal coordinates are modelling choices, not tabulated values from the paper.

## What is deliberately not defined here

No support, force, transverse polynomial basis, longitudinal element count or solver setting is defined by this model. Those belong to the [Problem](cshape-problem.md) and [Case](cshape-cases.md) respectively.

## References

- [Actual CSF model](../models/c_section_chapter9_5_3_9L9_csf.yaml)
- [General CUF documentation](../../docs/)
- [C-section benchmark overview](../readme.md)
