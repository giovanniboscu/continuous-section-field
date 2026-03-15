# Generating CSF Section Geometry with an LLM

CSF section geometry is defined as lists of polygon vertices in YAML format.
While simple sections can be written by hand, complex or high-resolution geometries
benefit from programmatic generation. A large language model (LLM) with code and
vision capabilities can generate CSF-ready YAML directly from images, analytical
descriptions, or parametric scripts - with arbitrary vertex resolution.

---

## 1. From an image

If you have a drawing or screenshot of a cross-section, an LLM with vision can
read the geometry and return a vertex list directly.

**Prompt example:**

> "This image shows a cross-section. Sample 64 points uniformly along the outer
> perimeter and return them as a CSF YAML polygon with weight 1.0, vertices in
> CCW order."

**When to use:**
- Scanned drawings or PDF details
- Screenshots from CAD or reports
- Approximate geometry where high precision is not critical

**Notes:**
- For dimensionally critical work, verify the output against known reference dimensions.
- Increase the point count for smoother morphing along z.

---

## 2. From an analytical description

For sections defined by geometric primitives --- circles, arcs, intersections,
fillets --- describe the geometry analytically. The LLM computes the vertices
exactly, with no approximation from image reading.

**Prompt example:**

> "Generate 128 points uniformly distributed along the perimeter of a section
> defined by the intersection of two circles of radius R=50, centered at
> (+d, 0) and (-d, 0) with d=20. Return the result as a CSF YAML polygon,
> vertices in CCW order, weight 1.0."

**When to use:**
- Sections defined by known curves (arcs, ellipses, Bezier, splines)
- Hollow sections with inner voids defined analytically
- Any geometry you can describe mathematically

---

## 3. Parametric script generation

The most powerful approach: ask the LLM to write a Python script that generates
the YAML programmatically. The script becomes a reusable asset --- change the
parameters, re-run, get updated geometry instantly.

**Prompt example:**

> "Write a Python script that generates a CSF YAML file for a hollow rounded
> rectangle section. Parameters: outer width W, outer height H, corner radius R,
> wall thickness t, number of points per side n. The section should have two
> polygons: outer contour with weight 1.0 and inner void with weight 0.0.
> Vertices in CCW order. Export S0 and S1 with the same geometry (prismatic member)."

**Example output structure** (n=4 per side, simplified):

```yaml
# CSF geometry definition with two reference sections (S0 -> S1).
# IMPORTANT: Polygon pairing is index-based, not name/proximity-based.
# Pairing rule:
#   S0.polygons[0] <-> S1.polygons[0]
#   S0.polygons[1] <-> S1.polygons[1]
# This ordering must remain consistent across all sections.
CSF:
  sections:
    S0:
      # ---------------------------
      # Reference section at z = 0
      # ---------------------------
      z: 0.000000
      polygons:
        outer:
          weight: 1.000000  # Full contribution (container domain)
          # Polygon index 0 in S0
          # Paired with polygon index 0 in S1
          vertices:  # CCW point order required
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
        inner:
          weight: 0.000000  # void
          # Polygon index 1 in S0
          # Paired with polygon index 1 in S1
          vertices:
            - [3.0, 2.0]
            - [7.0, 2.0]
            - [7.0, 4.0]
            - [3.0, 4.0]
    S1:
      # ---------------------------
      # Reference section at z = 10
      # ---------------------------
      z: 10.000000
      polygons:
        outer:
          weight: 1.000000  # Full contribution (container domain)
          # Polygon index 0 in S1
          # Must correspond to S0 polygon index 0 (outer)
          vertices:
            - [0.0, 0.0]
            - [10.0, 0.0]
            - [10.0, 6.0]
            - [0.0, 6.0]
        inner:
          weight: 0.000000  # void
          # Polygon index 1 in S1
          # Must correspond to S0 polygon index 1 (inner)
          vertices:
            - [3.0, 2.0]
            - [7.0, 2.0]
            - [7.0, 4.0]
            - [3.0, 4.0]
```

**When to use:**
- Any section you will reuse or iterate on
- Morphing geometries: run the script twice with different parameters to generate S0 and S1
- High vertex counts (hundreds to thousands of points) for smooth curved boundaries

---

## 4. Morphing sections with a parametric script

For members where the section changes along z, generate S0 and S1 independently
from the same script with different parameter sets.

**Prompt example:**

> "Write a Python script that generates a CSF YAML with two sections:
> S0 at z=0 is a circular hollow section with outer radius R0=500mm, thickness t0=20mm.
> S1 at z=12000 is a rounded rectangle with width W=800mm, height H=600mm,
> corner radius Rc=80mm, thickness t=16mm.
> Use 256 points per contour, uniformly distributed along the perimeter.
> Polygon pairing must be consistent: outer contour index 0, inner void index 1."

The script handles the parametric geometry, the uniform sampling, and the YAML
formatting. Vertex resolution is a free parameter --- increase n for smoother
interpolation along z with no additional effort.

---

## Key rules to include in every LLM prompt

When asking an LLM to generate CSF geometry, always specify:

- **CCW vertex order** --- counterclockwise is required
- **Polygon pairing is index-based** --- S0 and S1 must have the same number of
  polygons in the same order
- **Uniform perimeter sampling** - for morphing, uniform distribution along the
  perimeter gives the best interpolation quality
- **Weight assignment** - solid regions use `weight: 1.0`, voids use `weight: 0.0`,
  multi-material regions use the appropriate scalar
- **Units** - specify the unit system explicitly (meters, millimeters) to avoid
  scaling errors

---

## Vertex resolution guide

| Section type | Suggested n (per contour) |
|---|---|
| Simple polygon (rectangle, T, I) | 4-20 (one per side) |
| Circular or elliptical section | 64-128 |
| Rounded rectangle or complex outline | 64-256 |
| Morphing between dissimilar shapes | 128-512 |
| High-fidelity curved boundary | 256-1024 |

Higher vertex counts have negligible computational cost in CSF and improve
interpolation quality for morphing members.
