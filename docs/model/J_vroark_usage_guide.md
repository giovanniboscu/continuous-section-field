# Roark-based Torsional Indicator -Engineering Note

## Purpose

`compute_saint_venant_Jv2` returns two numbers, `J_s_vroark` and `J_s_vroark_fidelity`. The first is a cheap geometric estimate of the torsional constant; the second is a reliability flag that tells whether the first should be trusted for the current geometry. They are meant to be read together, never in isolation.

## How `J_s_vroark` is built

The method does not solve the Saint-Venant problem on the real section. It replaces the section with a solid rectangle that has the same area and the same minor principal inertia as the original, then applies the standard Roark formula for a solid rectangle. The result is multiplied by a global correction factor, `w_roark = A_weighted / A_geom`, that accounts for polygon weights.

This is honest only when the section is genuinely rectangle-like. For thin-walled or void-rich shapes (T, H, I, channel) the equivalent-rectangle is a poor stand-in for the real geometry, and the resulting number overestimates torsion, sometimes by a factor of three or more. The method was never designed to handle those; it is meant as a fast, closed-form indicator for compact, approximately rectangular cross-sections.

## How fidelity is built

Fidelity answers one question only: *is this section still close enough to a filled rectangle for the Roark mapping to make sense?*

Three geometric checks are combined.

**Weighted compactness.** How well the material fills a bounding box that has been contracted toward the geometric centroid in proportion to polygon weights. Light flanges effectively disappear from this box, so the indicator reflects structural material rather than outline.

**Container gap veto.** The compactness test can be misleading when a shape has voids inside its outline -the classic T/H/I case. If the raw geometry leaves more than 10% of its minimum bounding rectangle empty, and the base fidelity would otherwise be high, fidelity is set to zero. This catches cases where the weights suggest a compact shape but the geometry says otherwise.

**Weight dispersion.** The linear correction `w_roark` cannot fully compensate for the non-linearity of the Roark mapping when weights vary significantly across the section. A gentle penalty, `fid · w_roark^0.1`, reflects this residual uncertainty without overreacting.

## How to read the two numbers

`J_s_vroark` is always a number. It should not be interpreted without checking the fidelity first.

In practice:

- **fidelity close to 1.0** -the geometry is compact and rectangle-like; the Roark value is a reasonable estimate.
- **fidelity between 0.7 and 0.9** -borderline case, typically mild asymmetry or light non-structural material; the value may still be useful but with visible error.
- **fidelity below 0.6** -the geometry is no longer rectangle-like; discard `J_s_vroark` and use another torsional method (Bredt–Batho for closed thin-walled sections, Saint-Venant FEM for general cases).

A reasonable rule of thumb for automated pipelines is to reject the Roark value whenever fidelity falls below 0.7.

## Scope

The method is intended for solid rectangular or near-rectangular cross-sections, for sections with mild weight non-uniformity, and for contexts where a low-cost closed-form estimate is acceptable.

It should not be used as the primary torsion estimator for T, H, I, channel, box-with-holes, or thin-walled shapes. For those geometries, `compute_saint_venant_J_cell` or `compute_saint_venant_J_wall` are the appropriate tools. When those are not available, the fidelity indicator will collapse toward zero and signal that the Roark value must be discarded.
