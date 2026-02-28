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

This formulation applies to: - Solid sections - Thick-walled sections -
Arbitrary filled polygonal domains

------------------------------------------------------------------------

## 1.2 Thin-Walled Open Sections

For thin-walled open sections, the Saint-Venant torsion constant is
approximated by:

    J ≈ Σ ( b_i * t_i³ / 3 )

where: - b_i = midline length of wall segment i - t_i = wall thickness

This model assumes: - Thin walls (t \<\< characteristic dimension) -
Shear flow approximately uniform across thickness - No closed shear flow
circulation

This is the basis of `J_sv_wall` in CSF.

------------------------------------------------------------------------

## 1.3 Thin-Walled Closed Sections (Bredt--Batho)

For thin-walled closed cells, torsion is governed by shear flow
circulation.

For a single cell:

    J ≈ 4 A_m² / ∮(ds / t)

For constant thickness t:

    J ≈ 4 A_m² * t / b_m

where: - A_m = area enclosed by midline - b_m = total midline perimeter

This is the basis of `J_sv_cell` in CSF.

Closed-cell torsion is typically much stiffer than open-wall torsion due
to shear flow continuity.

------------------------------------------------------------------------

# 2. CSF Torsion Quantities

CSF can evaluate two torsional measures:

-   `J_sv_cell` → thin-walled closed-cell torsion (Bredt--Batho)
-   `J_sv_wall` → thin-walled open-wall torsion

-   `J_sv` → general solid Saint-Venant torsion is not implemented

Only `J_sv_cell` and `J_sv_wall` are used in the thin-walled torsion
model described here.

------------------------------------------------------------------------

# 3. Conceptual Model in CSF

CSF distinguishes torsional mechanisms based on polygon topology tags:

-   `@cell` or `@closed` → closed thin-walled cell
-   `@wall` → open thin-walled wall
-   no tag → not treated as thin-walled

Thickness is defined explicitly via:

    @t=<value>

Thickness may vary along z and is interpolated between stations.

At any section z:

-   Each `@cell` polygon contributes via closed-cell formula
-   Each `@wall` polygon contributes via open-wall formula
-   Contributions are weighted by the polygon weight w(z)

Total thin-walled torsion:

    J_thin(z) = Σ w_i(z) * J_i(z)

------------------------------------------------------------------------

# 4. Export Behavior

When exporting to solvers requiring a single torsional constant J:

If at least one thin-walled contribution is positive:

    J_export = J_sv_cell + J_sv_wall

If both exist, they are additive.

If neither exists:

    J_export = 0
    (with warning)

No automatic fallback to general solid J_sv is performed.

This guarantees:

-   Deterministic behavior
-   Explicit modeling intent
-   No silent substitutions

------------------------------------------------------------------------

# 5. How the User Must Define Torsion

## 5.1 Closed Thin-Walled Cells

To activate closed-cell torsion:

-   Tag polygon with `@cell` (or `@closed`)
-   Provide thickness using `@t=<value>`

Example:

    box@cell@t=0.012

If thickness varies along z, define `@t=` at both end stations. CSF
interpolates thickness linearly.

------------------------------------------------------------------------

## 5.2 Open Thin-Walled Walls

To activate open-wall torsion:

-   Tag polygon with `@wall`
-   Optionally define `@t=<value>`

Example:

    plate@wall@t=0.008

If `@t=` is omitted, thickness may be derived geometrically.

------------------------------------------------------------------------

## 5.3 Mixed Sections

If both closed cells and open walls exist in the same section:

-   Each mechanism is evaluated independently
-   Their torsional constants are summed

This reflects the physical superposition of independent shear flow
mechanisms.

------------------------------------------------------------------------

# 6. What the Model Does Not Do

-   It does not automatically convert solid domains into thin-walled
    models.
-   It does not infer topology without explicit tags.
-   It does not replace missing thin-walled torsion with solid torsion
    during export.
-   It does not modify user-defined thickness laws.

------------------------------------------------------------------------

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
