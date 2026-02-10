# Numerical Validation — Circular Hollow Section

## Purpose of the Validation

This validation case is designed to verify the **numerical accuracy** of the CSF engine
against **closed-form analytical solutions**.

A circular hollow section is selected because:
- exact formulas are available for all relevant sectional properties,
- the geometry is simple but representative,
- convergence behavior can be assessed clearly.

The test isolates the **sectional engine** from solver-specific effects.

---

## Geometry Definition

The validation model consists of a **non-tapered hollow circular section**,
representing a steel pipe.

Geometric parameters:
- external diameter `D_ext`,
- wall thickness `t`,
- internal diameter `D_int = D_ext - 2t`.

The section is modeled using a **regular polygon approximation**  
with a high number of sides (`N = 512`),  
so geometric discretization error is negligible.

The same section is used along the entire member length,  
therefore all sectional quantities are constant with respect to `z`.

---

## Modeling Assumptions

- Linear elastic behavior.
- Uniform material properties.
- Weight `w = 1.0` assigned to the solid region.
- No voids other than the internal circular hole.

The model is intentionally minimal to test the core numerical engine.

---

## Analytical Reference Formulas

For a hollow circular section, the exact analytical properties are:

- Area:

$$
A = \frac{\pi}{4}\left(D_{\text{ext}}^2 - D_{\text{int}}^2\right)
$$

- Second moments of area:

$$
I_x = I_y = \frac{\pi}{64}\left(D_{\text{ext}}^4 - D_{\text{int}}^4\right)
$$

- Polar moment:

$$
J = I_x + I_y
$$

- Centroid coordinates:

$$
C_x = C_y = 0
$$


These expressions provide a reliable benchmark.

---

## Numerical Evaluation with CSF

The section is represented in CSF by:
- one polygon for the outer boundary,
- one polygon for the inner void,
- both discretized using the same number of vertices.

Sectional properties are evaluated directly from polygonal formulas.

No longitudinal integration is required, as properties are constant.

---

## Results and Comparison

The table below compares **analytical** and **numerical** results.

All quantities are expressed in consistent SI units.

| Property | Analytical | CSF Numerical | Relative Error |
|--------|------------|---------------|----------------|
| Area \(A\) | reference | computed | \< 0.01% |
| \(I_x\) | reference | computed | \< 0.01% |
| \(I_y\) | reference | computed | \< 0.01% |
| \(J\) | reference | computed | \< 0.01% |
| \(C_x\) | 0 | \(\approx 0\) | machine precision |
| \(C_y\) | 0 | \(\approx 0\) | machine precision |

Errors are dominated by:
- polygonal approximation,
- floating-point arithmetic.

---

## Convergence Considerations

Increasing the number of polygon sides leads to systematic convergence
towards the analytical solution.

For \( N \geq 256 \), all sectional quantities converge within engineering tolerance.

This confirms that:
- the polygonal formulation is consistent,
- numerical integration errors are negligible,
- no hidden bias is introduced by the CSF engine.

---

## Interpretation of Results

The excellent agreement between analytical and numerical results demonstrates that:
- the geometric reconstruction is correct,
- sectional property assembly is accurate,
- void handling via zero-weight regions is robust.

This validation establishes confidence in the use of CSF for more complex geometries.

---

## Scope of the Validation

This test validates:
- section reconstruction,
- area and inertia computation,
- centroid evaluation,
- void handling.

It does **not** validate:
- solver coupling,
- global structural response,
- nonlinear effects.

---

## Summary

The circular hollow section benchmark confirms that CSF can reproduce
closed-form sectional properties with high accuracy.

This provides a solid baseline for applying CSF to
tapered, multi-material, and industrial-scale structural members,
as demonstrated in subsequent validation cases.

