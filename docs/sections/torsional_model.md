# CSF Torsion Model

## Theoretical Background and User-Level Specification

------------------------------------------------------------------------

# 1. Theoretical Background -- Saint-Venant Torsion

## 1.1 Solid Saint-Venant Torsion

For a prismatic member subjected to uniform torsion, the Saint-Venant
theory introduces a stress function ψ such that:

    ∇²ψ = -2      in Ω
    ψ = 0         on ∂Ω

The torsional constant J is defined as:

    J = 2 ∫_Ω ψ dA

For solid domains, J depends purely on geometry and is computed from the
full 2D domain Ω.

------------------------------------------------------------------------

## 1.2 Thin-Walled Open Sections

For thin-walled open sections, the Saint-Venant torsion constant is
approximated by:

    J ≈ Σ ( b_i * t_i³ / 3 )

where: - b_i = midline length - t_i = wall thickness

This is the basis of `J_sv_wall` in CSF.

------------------------------------------------------------------------

## 1.3 Thin-Walled Closed Sections (Bredt--Batho)

For thin-walled closed cells:

    J ≈ 4 A_m² / ∮(ds / t)

For constant thickness t:

    J ≈ 4 A_m² * t / b_m

where: - A_m = area enclosed by midline - b_m = midline perimeter

This is the basis of `J_sv_cell` in CSF.

------------------------------------------------------------------------

# 2. CSF Torsion Quantities

CSF evaluates:

-   `J_sv_cell` → closed thin-walled torsion
-   `J_sv_wall` → open thin-walled torsion
-   `J_sv` → general solid torsion non implemented

The thin-walled model uses only `J_sv_cell` and `J_sv_wall`.

------------------------------------------------------------------------

# 3. Thickness Definition and Interpolation

Thickness is defined explicitly through:

    @t=<value>

If thickness differs between start and end sections:

-   CSF interpolates thickness **linearly along z**
-   The interpolated value becomes the active thickness at each section
-   The interpolated thickness is embedded in the runtime polygon name
-   Torsional stiffness is therefore evaluated with the local
    interpolated t(z)

This means torsional stiffness may vary continuously along the member
due to thickness variation.

For `@cell` polygons: - Thickness is mandatory.

For `@wall` polygons: - Thickness is optional (if absent, a geometric
estimate may be used).

------------------------------------------------------------------------

# 4. Conceptual Thin-Walled Model

At any section z:

-   Each `@cell` polygon contributes using closed-cell formula
-   Each `@wall` polygon contributes using open-wall formula
-   Each contribution is multiplied by its polygon weight w(z)

Total thin-walled torsion:

    J_thin(z) = Σ w_i(z) * J_i(z)

Closed-cell and open-wall mechanisms are additive when both exist.

------------------------------------------------------------------------

# 5. Export Behavior

When exporting to solvers requiring a single torsional constant:

If at least one thin-walled contribution is positive:

    J_export = J_sv_cell + J_sv_wall

If neither is available:

    J_export = 0
    (with warning)

There is no fallback to solid `J_sv`.

------------------------------------------------------------------------

# 6. User Modeling Guidelines

To activate torsion mechanisms:

Closed cell:

    sectionPart@cell@t=0.012

Open wall:

    plate@wall@t=0.008

***If thickness varies between stations, define different `@t=` values at
each station. CSF automatically interpolates thickness along z.***


---
```yaml
CSF:
  sections:
    S0:
      z: 0.0   # cm
      polygons:
        web@wall@t=0.41:
          weight: 1.0
          vertices:
            - [-0.205, -4.430]
            - [ 0.205, -4.430]
            - [ 0.205,  4.430]
            - [-0.205,  4.430]

        top_flange@wall@t=0.57:
          weight: 1.0
          vertices:
            - [-2.750,  4.430]
            - [ 2.750,  4.430]
            - [ 2.750,  5.000]
            - [-2.750,  5.000]

        bottom_flange@wall@t=0.57:
          weight: 1.0
          vertices:
            - [-2.750, -5.000]
            - [ 2.750, -5.000]
            - [ 2.750, -4.430]
            - [-2.750, -4.430]

    S1:
      z: 2000.0   # cm (20 m)
      polygons:
        web@wall:
          weight: 1.0
          vertices:
            - [-0.205, -4.430]
            - [ 0.205, -4.430]
            - [ 0.205,  4.430]
            - [-0.205,  4.430]

        top_flange@wall:
          weight: 1.0
          vertices:
            - [-2.750,  4.430]
            - [ 2.750,  4.430]
            - [ 2.750,  5.000]
            - [-2.750,  5.000]

        bottom_flange@wall:
          weight: 1.0
          vertices:
            - [-2.750, -5.000]
            - [ 2.750, -5.000]
            - [ 2.750, -4.430]
            - [-2.750, -4.430]
```
---
# 7. Summary

CSF thin-walled torsion model:

-   Is based on classical Saint-Venant theory
-   Uses Bredt--Batho for closed cells
-   Uses thin-wall approximation for open walls
-   Requires explicit topology tags
-   Uses explicit thickness definition via `@t=`
-   Produces additive torsional stiffness when multiple mechanisms
    coexist
-   Exports a single deterministic J value without fallback ambiguity
