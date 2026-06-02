# Roark-based torsional indicator - engineering note

## Purpose

`compute_saint_venant_Jv2` returns two quantities: `J_s_vroark` and `J_s_vroark_fidelity`.

`J_s_vroark` is a low-cost torsional indicator based on a Roark-type rectangular approximation. `J_s_vroark_fidelity` is a reliability indicator that states whether the Roark-based value is appropriate for the sampled geometry.

The two quantities must be read together. `J_s_vroark` is always reported, but it should not be interpreted as reliable when the associated fidelity is low.

## How `J_s_vroark` is built

The method does not solve the Saint-Venant torsion problem on the actual cross-section. Instead, it maps the sampled section to an equivalent solid rectangle. The equivalent rectangle is chosen to preserve the geometric area and the minor principal inertia of the original sampled section.

The standard Roark expression for a solid rectangle is then applied to this equivalent rectangle. The resulting value is multiplied by the global weighting factor

```text
w_roark = A_weighted / A_geom
```

where `A_geom` is the unweighted geometric area and `A_weighted` is the participation-weighted area.

The resulting value is reported as `J_s_vroark`.

This construction is meaningful only when the sampled section is compact and approximately rectangle-like. For thin-walled, void-rich, flange-web, T, H, I, channel, or hollow shapes, the equivalent rectangle is generally a poor representation of the real torsional behaviour. In those cases, `J_s_vroark` may significantly overestimate the Saint-Venant torsional constant and must be treated only as a diagnostic output.

## How fidelity is built

`J_s_vroark_fidelity` answers one specific question: whether the sampled section is sufficiently close to a filled rectangle for the Roark mapping to be meaningful.

The indicator combines three checks.

### Weighted compactness

The first check measures how compactly the participating geometry fills a rectangle-like container around the section. Regions with low participation have reduced influence, so the indicator reflects the effective participating geometry rather than only the external outline.

### Container-gap veto

A compactness measure can be misleading when the section has large gaps or voids inside its outline. This is typical of T, H, I, channel, or void-rich geometries.

If the raw geometry leaves a large empty portion of its minimum bounding rectangle, the Roark mapping is rejected by setting the fidelity to zero. This prevents a section with a rectangular external envelope but non-compact internal geometry from being treated as Roark-compatible.

### Weight-dispersion penalty

The global correction `w_roark` is only a scalar area correction. It cannot fully represent the nonlinear effect of strongly non-uniform participation across the section.

For this reason, a mild penalty is applied when the participation weights vary significantly across the section. This reduces the fidelity without automatically rejecting cases with moderate participation variation.

## How to read the two quantities

`J_s_vroark` should not be interpreted without checking `J_s_vroark_fidelity`.

A practical interpretation is:

* fidelity close to `1.0`: the section is compact and rectangle-like; the Roark value can be used as a reasonable engineering estimate;
* fidelity between `0.7` and `0.9`: borderline case; the value may still be useful, but visible approximation error should be expected;
* fidelity below `0.7`: the section is no longer sufficiently rectangle-like; `J_s_vroark` should be discarded.

A conservative automated rule is to reject `J_s_vroark` whenever

```text
J_s_vroark_fidelity < 0.7
```

## Scope

The Roark-based indicator is intended for compact solid rectangular or near-rectangular cross-sections, possibly with mild participation non-uniformity, where a low-cost closed-form torsional estimate is acceptable.

It should not be used as the primary torsion estimator for T, H, I, channel, box-with-holes, thin-walled, or strongly non-compact sections.

For closed thin-walled cells, open thin walls, or general sections requiring warping-based torsion, a dedicated torsional method should be used instead. In CSF this means using the appropriate cell, wall, or external finite-element torsion workflow where applicable.

Accordingly, `J_s_vroark` is a fast equivalent torsional diagnostic, while `J_s_vroark_fidelity` indicates whether that diagnostic is admissible for the sampled section.
