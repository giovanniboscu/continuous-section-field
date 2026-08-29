# DRADFT

# Implementing the `scaled_lagrange` Expansion in CSF-CUF v21

## 1. Purpose

This guide documents the complete procedure used to add the hierarchical
`scaled_lagrange` transverse expansion to CSF-CUF v21.

The implementation follows these constraints:

- do not modify the CUF formulation;
- do not add expansion-name branches to `solver/engine.py`;
- do not modify the KKT construction;
- keep existing YAML files compatible;
- keep the transverse expansion isolated in `cuf/expansions`;
- preserve a stable meaning for every CUF index `tau`;
- validate the scalar implementation before adding performance features;
- keep all code comments and YAML comments in English.

The completed expansion supports hierarchy orders from N1 upward. The
validated case series uses N1 through N27.

## 2. Mathematical definition

The physical transverse coordinates are scaled to reference coordinates:

$$
\xi = \frac{y}{y_{\mathrm{scale}}}, \qquad \eta = \frac{z}{z_{\mathrm{scale}}}.
$$

The expansion uses the existing hierarchical
`SerendipityLagrangeReferenceBasis` on the reference square
$[-1,1]\times[-1,1]$.

The displacement field remains

$$
\mathbf u(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,\mathbf u_\tau(x).
$$

The physical transverse derivatives follow from the chain rule:

$$
F_{\tau,y} = \frac{1}{y_{\mathrm{scale}}} F_{\tau,\xi}, \qquad F_{\tau,z} = \frac{1}{z_{\mathrm{scale}}} F_{\tau,\eta}.
$$

The hierarchy size is

$$
M(N)=4N,\qquad N\leq3,
$$

and

$$
M(N) = 4N+\frac{(N-2)(N-3)}{2}, \qquad N\geq4.
$$

Examples:

| Order | Functions |
|---:|---:|
| 1 | 4 |
| 2 | 8 |
| 3 | 12 |
| 4 | 17 |
| 5 | 23 |
| 6 | 30 |
| 10 | 68 |
| 27 | 408 |

## 3. Create the expansion module

Create the following new file:

```text
src/csf/cuf/expansions/scaled_lagrange.py
```

Do not rename or overwrite `scaled_lagrange_q1.py`. The Q1 plugin remains a
separate, independently validated expansion.

Start with these imports:

```python
# Version: CSF-CUF scaled hierarchical Lagrange expansion v1 - 2026-08-29
"""Scaled hierarchical Serendipity-Lagrange transverse expansion."""

import math
import numpy as np

from csf.cuf.core.basis import (
    CUFBasis,
    SerendipityLagrangeReferenceBasis,
)
from csf.cuf.core.basis_plugins import (
    CUFBasisPlugin,
    register_cuf_basis_plugin,
)
from csf.cuf.numerics import transverse_scales
```

## 4. Implement the common `CUFBasis` interface

The scaled wrapper owns the physical coordinate transformation. The existing
reference basis owns the hierarchy, term definitions, values, and reference
derivatives.

```python
class ScaledLagrangeBasis(CUFBasis):
    """Hierarchical Serendipity-Lagrange basis in scaled coordinates."""

    def __init__(
        self,
        *,
        order: int,
        y_scale: float,
        z_scale: float,
    ) -> None:
        if not isinstance(order, int):
            raise TypeError(
                "scaled_lagrange order must be an integer"
            )

        if order < 1:
            raise ValueError(
                "scaled_lagrange order must be >= 1"
            )

        y_scale = float(y_scale)
        z_scale = float(z_scale)

        if not math.isfinite(y_scale) or y_scale <= 0.0:
            raise ValueError(
                "y_scale must be positive and finite"
            )

        if not math.isfinite(z_scale) or z_scale <= 0.0:
            raise ValueError(
                "z_scale must be positive and finite"
            )

        self._reference_basis = (
            SerendipityLagrangeReferenceBasis(order)
        )
        self._y_scale = y_scale
        self._z_scale = z_scale

    @property
    def order(self) -> int:
        return self._reference_basis.order

    @property
    def size(self) -> int:
        return self._reference_basis.size

    @property
    def scales(self) -> tuple[float, float]:
        return self._y_scale, self._z_scale

    def definition(self, tau: int):
        return self._reference_basis.definition(tau)

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        xi = float(y) / self._y_scale
        eta = float(z) / self._z_scale

        return float(
            self._reference_basis.value(
                tau,
                xi,
                eta,
            )
        )

    def derivative(
        self,
        tau: int,
        direction: str,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        xi = float(y) / self._y_scale
        eta = float(z) / self._z_scale

        if direction == "y":
            derivative_xi = self._reference_basis.derivative(
                tau,
                "y",
                xi,
                eta,
            )
            return float(derivative_xi / self._y_scale)

        if direction == "z":
            derivative_eta = self._reference_basis.derivative(
                tau,
                "z",
                xi,
                eta,
            )
            return float(derivative_eta / self._z_scale)

        raise ValueError(
            "direction must be 'y' or 'z'"
        )
```

The expansion currently ignores `x` because it uses fixed global transverse
scales. The optional argument remains part of the common interface.

## 5. Validate `basis_options`

The expansion does not require YAML-specific parameters. Unknown options must
be rejected rather than silently ignored.

```python
def _reject_options(options):
    """Reject unsupported cuf.basis_options."""

    if options:
        raise ValueError(
            "scaled_lagrange does not accept "
            "cuf.basis_options; "
            f"received {sorted(options)}"
        )
```

The YAML therefore contains no `basis_options` mapping.

## 6. Implement the plugin builder

The builder validates the order, obtains the scales from the CSF geometry,
and returns a ready-to-use basis.

```python
def _build(*, order, section_provider, options):
    """Construct a complete ScaledLagrangeBasis instance."""

    _reject_options(options)

    if not isinstance(order, int):
        raise TypeError(
            "scaled_lagrange order must be an integer"
        )

    if order < 1:
        raise ValueError(
            "scaled_lagrange order must be >= 1"
        )

    y_scale, z_scale = transverse_scales(
        section_provider
    )

    return ScaledLagrangeBasis(
        order=order,
        y_scale=y_scale,
        z_scale=z_scale,
    )
```

## 7. Declare sectional quadrature

An order-N edge function may contain a degree-N polynomial multiplied by a
linear transverse factor. Products may therefore reach total degree
$2(N+1)$. Polygon slicing can add one degree to the outer integrand.

The selected conservative minimum is

$$
n_{G,\Omega}=N+2.
$$

```python
def _section_gauss_minimum(basis):
    """Return a conservative sectional Gauss order."""

    if not isinstance(basis, ScaledLagrangeBasis):
        raise TypeError(
            "scaled_lagrange received an incompatible basis"
        )

    return int(basis.order) + 2
```

The solver retains any larger order requested by the YAML:

```python
effective_order = max(
    requested_order,
    plugin_minimum,
)
```

## 8. Declare the longitudinal transverse degree

If both physical transverse coordinates vary affinely along `x`, one
hierarchical function may contribute longitudinal degree $N+1$. A product
of two functions may therefore contribute

$$
p_{x,\mathrm{transverse}}=2(N+1).
$$

```python
def _longitudinal_transverse_degree(basis):
    """Return the conservative longitudinal degree contribution."""

    if not isinstance(basis, ScaledLagrangeBasis):
        raise TypeError(
            "scaled_lagrange received an incompatible basis"
        )

    return 2 * (int(basis.order) + 1)
```

The solver combines this value with geometry, material, and longitudinal FE
contributions.

## 9. Register the expansion

```python
register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="scaled_lagrange",
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=(
            _longitudinal_transverse_degree
        ),
    )
)
```

No import is required in `expansions/__init__.py`. The v21 registry discovers
modules below `csf.cuf.expansions` automatically.

Verify syntax and registration:

```bash
python -m py_compile \
    src/csf/cuf/expansions/scaled_lagrange.py

python -c \
"from csf.cuf.core.basis_plugins import available_cuf_basis_plugins; print(available_cuf_basis_plugins())"
```

The output must include:

```text
scaled_lagrange
```

## 10. YAML case

Example N6 case:

```yaml
# Version: CSF-CUF scaled hierarchical Lagrange case v1 - 2026-08-29
case:
  name: cuf_scaled_lagrange_taper40_deg20_table10_N06

problem:
  yaml: ../../../../problems/taper40_deg20_table10.yaml
  adapter: ../../../../validation/carrera_problem.py

cuf:
  basis: scaled_lagrange
  order: 6

longitudinal:
  method: finite_element
  elements: 1
  order: 6

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6

sampling:
  stations:
    - 0.00
    - 0.25
    - 0.50
    - 0.75
    - 1.00
  displacement_samples: 201
  stress_grid: 31

output:
  adapter: ../../../../validation/carrera_post.py
  directory: ../../../../output/taper40_deg20_scaled_lagrange/table10_N06
```

For the N1-N27 series, change only:

- `case.name`;
- `cuf.order`;
- `output.directory`.

## 11. Optional self-contained displacement checkpoint

The final implementation also exports the expansion as physical power
coefficients for the optional displacement checkpoint. This does not change
assembly or KKT evaluation.

The export follows

$$
F_\tau(y,z) = \sum_{p,q}C_{\tau pq}y^p z^q.
$$

The method contract is:

```python
def power_coefficients(self) -> np.ndarray:
    """Return F_tau coefficients in ascending physical powers of y and z."""

    return self._power_coefficients.copy()
```

The coefficients are constructed once in `__init__` and marked read-only.
They are used after the KKT solve to create:

```text
<case.name>.cuf.npz
```

The checkpoint is autonomous for displacement queries and does not require
the original YAML. It does not currently persist geometry, materials, strains,
or stresses.

At fixed `x`, the solved CUF amplitudes and transverse coefficients are
contracted once into the final section polynomials
$u_x(y,z),u_y(y,z),u_z(y,z)$. This keeps repeated post-processing queries
independent of the number of CUF functions.

## 12. Final test: hierarchy, size, and finite values

```python
import math

from csf.cuf.expansions.scaled_lagrange import (
    ScaledLagrangeBasis,
)


def expected_size(order):
    if order <= 3:
        return 4 * order

    return (
        4 * order
        + (order - 2) * (order - 3) // 2
    )


orders_to_test = (
    1,
    2,
    3,
    4,
    5,
    10,
    17,
    27,
)

test_points = (
    (0.0, 0.0),
    (0.25, -0.50),
    (-0.75, 0.80),
)


for order in orders_to_test:
    basis = ScaledLagrangeBasis(
        order=order,
        y_scale=2.0,
        z_scale=3.0,
    )

    assert basis.order == order
    assert basis.size == expected_size(order)

    for tau in range(1, basis.size + 1):
        for y, z in test_points:
            value = basis.value(tau, y, z)
            derivative_y = basis.derivative(
                tau,
                "y",
                y,
                z,
            )
            derivative_z = basis.derivative(
                tau,
                "z",
                y,
                z,
            )

            assert math.isfinite(value)
            assert math.isfinite(derivative_y)
            assert math.isfinite(derivative_z)


print("scaled_lagrange hierarchy test: PASSED")
```

## 13. Final test: Q1 Kronecker property

```python
from csf.cuf.expansions.scaled_lagrange import (
    ScaledLagrangeBasis,
)


basis = ScaledLagrangeBasis(
    order=1,
    y_scale=2.0,
    z_scale=3.0,
)

physical_corners = (
    (-2.0, -3.0),
    (+2.0, -3.0),
    (+2.0, +3.0),
    (-2.0, +3.0),
)

tolerance = 1.0e-14

for corner_index, (y, z) in enumerate(
    physical_corners,
    start=1,
):
    values = [
        basis.value(tau, y, z)
        for tau in range(1, basis.size + 1)
    ]

    expected = [
        1.0 if tau == corner_index else 0.0
        for tau in range(1, basis.size + 1)
    ]

    for computed, reference in zip(values, expected):
        assert abs(computed - reference) <= tolerance


print("scaled_lagrange Q1 Kronecker test: PASSED")
```

## 14. Final test: hierarchical prefix stability

Every function already present at order N must retain the same definition,
value, derivative, and `tau` index at order N+1.

```python
from csf.cuf.expansions.scaled_lagrange import (
    ScaledLagrangeBasis,
)


test_points = (
    (0.0, 0.0),
    (0.25, -0.50),
    (-0.75, 0.80),
)

for order in range(1, 10):
    lower = ScaledLagrangeBasis(
        order=order,
        y_scale=2.0,
        z_scale=3.0,
    )

    higher = ScaledLagrangeBasis(
        order=order + 1,
        y_scale=2.0,
        z_scale=3.0,
    )

    for tau in range(1, lower.size + 1):
        assert lower.definition(tau) == higher.definition(tau)

        for y, z in test_points:
            assert (
                lower.value(tau, y, z)
                == higher.value(tau, y, z)
            )
            assert (
                lower.derivative(tau, "y", y, z)
                == higher.derivative(tau, "y", y, z)
            )
            assert (
                lower.derivative(tau, "z", y, z)
                == higher.derivative(tau, "z", y, z)
            )


print("scaled_lagrange hierarchy stability test: PASSED")
```

## 15. Final test: analytical derivatives versus finite differences

```python
from csf.cuf.expansions.scaled_lagrange import (
    ScaledLagrangeBasis,
)


orders_to_test = (1, 2, 3, 5, 10, 27)
test_points = (
    (0.0, 0.0),
    (0.25, -0.50),
    (-0.75, 0.80),
)

step = 1.0e-6
absolute_tolerance = 1.0e-8
relative_tolerance = 1.0e-6


for order in orders_to_test:
    basis = ScaledLagrangeBasis(
        order=order,
        y_scale=2.0,
        z_scale=3.0,
    )

    for tau in range(1, basis.size + 1):
        for y, z in test_points:
            analytical_y = basis.derivative(
                tau,
                "y",
                y,
                z,
            )
            finite_difference_y = (
                basis.value(tau, y + step, z)
                - basis.value(tau, y - step, z)
            ) / (2.0 * step)

            analytical_z = basis.derivative(
                tau,
                "z",
                y,
                z,
            )
            finite_difference_z = (
                basis.value(tau, y, z + step)
                - basis.value(tau, y, z - step)
            ) / (2.0 * step)

            error_y = abs(analytical_y - finite_difference_y)
            error_z = abs(analytical_z - finite_difference_z)

            tolerance_y = (
                absolute_tolerance
                + relative_tolerance
                * max(
                    abs(analytical_y),
                    abs(finite_difference_y),
                )
            )
            tolerance_z = (
                absolute_tolerance
                + relative_tolerance
                * max(
                    abs(analytical_z),
                    abs(finite_difference_z),
                )
            )

            assert error_y <= tolerance_y
            assert error_z <= tolerance_z


print("scaled_lagrange derivative test: PASSED")
```

## 16. Final test: exact N1 equivalence with `scaled_lagrange_q1`

```python
from csf.cuf.expansions.scaled_lagrange import (
    ScaledLagrangeBasis,
)
from csf.cuf.expansions.scaled_lagrange_q1 import (
    ScaledLagrangeQ1Basis,
)


hierarchical = ScaledLagrangeBasis(
    order=1,
    y_scale=2.0,
    z_scale=3.0,
)

q1 = ScaledLagrangeQ1Basis(
    y_scale=2.0,
    z_scale=3.0,
)

test_points = (
    (-2.0, -3.0),
    (+2.0, -3.0),
    (+2.0, +3.0),
    (-2.0, +3.0),
    (0.0, 0.0),
    (0.25, -0.50),
    (-0.75, 0.80),
)

assert hierarchical.size == q1.size == 4

for tau in range(1, 5):
    for y, z in test_points:
        assert (
            hierarchical.value(tau, y, z)
            == q1.value(tau, y, z)
        )
        assert (
            hierarchical.derivative(tau, "y", y, z)
            == q1.derivative(tau, "y", y, z)
        )
        assert (
            hierarchical.derivative(tau, "z", y, z)
            == q1.derivative(tau, "z", y, z)
        )


print(
    "scaled_lagrange N1 versus "
    "scaled_lagrange_q1: EXACT EQUALITY"
)
```

## 17. Final test: power-coefficient export

```python
import numpy as np

from csf.cuf.expansions.scaled_lagrange import (
    ScaledLagrangeBasis,
)


for order in (1, 2, 3, 4, 6, 10, 27):
    basis = ScaledLagrangeBasis(
        order=order,
        y_scale=33.333,
        z_scale=75.0,
    )
    coefficients = basis.power_coefficients()

    for y, z in (
        (0.0, 0.0),
        (12.5, -31.25),
        (-33.0, 74.0),
    ):
        y_powers = np.power(
            y,
            np.arange(coefficients.shape[1]),
        )
        z_powers = np.power(
            z,
            np.arange(coefficients.shape[2]),
        )

        exported = np.einsum(
            "tpq,p,q->t",
            coefficients,
            y_powers,
            z_powers,
            optimize=True,
        )

        scalar = np.asarray(
            [
                basis.value(tau, y, z)
                for tau in range(1, basis.size + 1)
            ],
            dtype=float,
        )

        np.testing.assert_allclose(
            exported,
            scalar,
            rtol=1.0e-10,
            atol=1.0e-12,
        )


print("scaled_lagrange power export test: PASSED")
```

## 18. Final test: compiled displacement checkpoint round-trip

```python
from pathlib import Path

import numpy as np

from csf.cuf.expansions.scaled_lagrange import (
    ScaledLagrangeBasis,
)
from csf.cuf.solver.assembly import GlobalDOFLayout
from csf.cuf.solver.compiled_field import (
    CompiledDisplacementField,
)
from csf.cuf.solver.longitudinal import (
    LongitudinalElement1D,
    LongitudinalMesh1D,
)


element = LongitudinalElement1D(
    index=0,
    node_ids=tuple(range(7)),
    coordinates=tuple(np.linspace(0.0, 1000.0, 7)),
)

mesh = LongitudinalMesh1D(
    x_start=0.0,
    x_end=1000.0,
    nodes=element.coordinates,
    elements=(element,),
    order=6,
)

basis = ScaledLagrangeBasis(
    order=6,
    y_scale=33.333,
    z_scale=75.0,
)

layout = GlobalDOFLayout(
    number_of_nodes=7,
    basis_size=basis.size,
)

solved_dofs = np.random.default_rng(20260829).normal(
    size=layout.total_dofs
)

field = CompiledDisplacementField.from_solution_data(
    mesh=mesh,
    dof_layout=layout,
    solved_dofs=solved_dofs,
    basis=basis,
    metadata={"case_name": "roundtrip"},
)

path, digest = field.save_atomic(
    Path("roundtrip.cuf.npz")
)

loaded = CompiledDisplacementField.load(path)

for point in (
    (0.0, 0.0, 0.0),
    (530.0, 33.0, -64.4),
    (1000.0, -33.0, 30.0),
):
    np.testing.assert_array_equal(
        loaded(*point),
        field(*point),
    )


print("checkpoint SHA256:", digest)
print("compiled displacement round-trip: PASSED")
```

## 19. Full solver regression

Run `scaled_lagrange_q1` N1 and `scaled_lagrange` N1 with identical problem,
geometry, longitudinal discretization, quadrature, loads, constraints, and
sampling.


The validated N1 comparison produced exact equality of:

- `M=4`;
- `DOFs=84`;
- effective sectional Gauss order `6`;
- longitudinal degree estimate `19`;
- effective longitudinal Gauss order `10`;
- KKT shape `(101,101)`;
- KKT `nnz=7144`;
- residual mean and standard deviation;
- KKT structure, KKT data, and RHS hashes.

Validated hashes:

```text
indptr  = 373e66685f86612ba35a5a5b6a4c0d3682891cb201cd7e1aa1d9acb23df088b3
indices = b010c3f4a0a2574b4a560b8dbaee66c1945fd7d2639e427047c27a01ab0d98e9
data    = 171b1966c2700562e40e31c0979c5735f52463fc39fcd4f4a194275e34251e9a
rhs     = afcbb97af98435b02400c19f21e0edc9ab42a449a5e5d11687e155364ae1635f
```

The only acceptable log differences are case name, output directory, and
elapsed time.

## 20. Convergence campaign N1-N27

For every order, retain:

- unchanged YAML input;
- complete log;
- effective sectional and longitudinal Gauss orders;
- basis size and DOF count;
- KKT shape and `nnz`;
- constraint rank;
- original and equilibrated reciprocal condition estimates;
- KKT and RHS hashes;
- residual statistics;
- maximum displacements and locations;
- generated `<case.name>.cuf.npz` checkpoint;
- post-processing elapsed time.

Do not compare `scaled_lagrange` N with Legendre or Maclaurin N as if the bases
were algebraically identical. Use consecutive Lagrange orders to assess
hierarchical convergence, and use independent analytical or FEM references to
assess physical accuracy.

## 21. Completion checklist

- [ ] `scaled_lagrange.py` compiles.
- [ ] Plugin discovery lists `scaled_lagrange`.
- [ ] Orders N1-N27 construct finite functions and derivatives.
- [ ] Hierarchical prefix ordering is stable.
- [ ] Analytical derivatives pass finite-difference checks.
- [ ] N1 is exactly equal to `scaled_lagrange_q1`.
- [ ] N1 KKT and RHS hashes match the Q1 baseline.
- [ ] Section and longitudinal quadrature convergence are verified.
- [ ] Constraint matrices retain full numerical rank.
- [ ] Equilibrated KKT solves have acceptable residuals.
- [ ] Checkpoint save/load reproduces displacement queries.
- [ ] Consecutive N results demonstrate convergence.
- [ ] No expansion-specific branch is added to the CUF solver core.
