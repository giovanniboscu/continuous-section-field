# Implementing the `scaled_lagrange` Expansion in CSF-CUF v21

## 1. Purpose

This guide shows, step by step, how to add the hierarchical
`scaled_lagrange` transverse expansion to CSF-CUF v21.

The implementation uses the Serendipity-Lagrange hierarchy already provided by
`core/basis.py` and adds one new expansion module,
`expansions/scaled_lagrange.py`, which scales that reference hierarchy to the
physical transverse coordinates and registers it as a CUF plugin.

The implementation follows these constraints:

- do not modify the CUF formulation;
- do not add expansion-name branches to `solver/engine.py`;
- do not modify the KKT construction;
- keep existing YAML files compatible;
- keep the plugin-specific code in `cuf/expansions`;
- preserve a stable meaning for every CUF index `tau`;
- keep all code comments and YAML comments in English.

The completed expansion supports hierarchy orders from N1 upward. The
validated case series uses N1 through N27.

## 2. STEP 1 - Verify the reference basis in the core

`scaled_lagrange.py` does not define the Serendipity-Lagrange hierarchy. The
hierarchy is already implemented in the CUF core; the new expansion module only
converts physical coordinates to the reference coordinates used by that basis.

Before creating the plugin, verify that the reference class is present in:

```text
src/csf/cuf/core/basis.py
```

and is named:

```python
class SerendipityLagrangeReferenceBasis(CUFBasis):
```

Do not create a second copy of this class inside `scaled_lagrange.py`.
The plugin will import it and use it directly.

### What `scaled_lagrange.py` requires from `core/basis.py`

The plugin uses two names from `core/basis.py`:

| Required object | What the plugin needs from it |
|---|---|
| `CUFBasis` | The common CUF basis interface used by the solver |
| `SerendipityLagrangeReferenceBasis` | The complete hierarchical Serendipity-Lagrange basis on the reference square |

`ScaledLagrangeBasis` uses the following members of
`SerendipityLagrangeReferenceBasis(order)`:

| Member | Required meaning |
|---|---|
| `order` | Returns the requested hierarchy order `N` |
| `size` | Returns the total number of functions in orders `1..N` |
| `definition(tau)` | Returns the stable hierarchical identity of function `tau` as `(kind, r, side, n, m)` |
| `value(tau, xi, eta)` | Evaluates the reference function at the natural coordinates `(xi, eta)` |
| `derivative(tau, "y", xi, eta)` | Returns the reference derivative with respect to `xi` |
| `derivative(tau, "z", xi, eta)` | Returns the reference derivative with respect to `eta` |

The derivative labels are still `"y"` and `"z"` because the class implements
the common `CUFBasis` interface. Inside this reference class, however, the two
arguments represent the natural coordinates `xi` and `eta`.

### How `definition(tau)` is used

Every reference function has a stable descriptor returned by:

```python
kind, r, side, n, m = self.definition(tau)
```

The labels `I`, `IIA`, `IIB`, and `III` are **not a general CUF nomenclature for
transverse expansions**. They belong specifically to the
Serendipity-Lagrange hierarchy implemented by
`SerendipityLagrangeReferenceBasis`. Other expansions, such as Maclaurin or
Legendre, do not use this classification.

In this Serendipity-Lagrange hierarchy, the descriptor is interpreted as
follows:

| `kind` | Role in the Serendipity-Lagrange hierarchy | `r` | `side` | `n`, `m` |
|---|---|---:|---|---|
| `I` | Four bilinear corner functions | `1` | `1..4`, identifies the corner | not used |
| `IIA` | Edge enrichment functions | `2` or `3` | `1..4`, identifies the edge | not used |
| `IIB` | Higher-order edge enrichment functions | `>= 4` | `1..4`, identifies the edge | not used |
| `III` | Interior functions | `>= 4` | not used | `n >= 2`, `m >= 2`, `n + m = r` |

`Type II` is therefore the edge-function family. This implementation stores its
lower enrichment levels as `IIA` and its higher enrichment levels as `IIB`.
Both are evaluated as edge functions; the two labels distinguish their place
in the hierarchy.

For `kind == "I"`, the `side` field identifies the four reference-square
corners in this order:

```text
1 -> (-1, -1)
2 -> (+1, -1)
3 -> (+1, +1)
4 -> (-1, +1)
```

For `kind == "IIA"` or `kind == "IIB"`, the same field identifies the four
reference-square edges:

```text
1 -> eta = -1
2 -> xi  = +1
3 -> eta = +1
4 -> xi  = -1
```

For `kind == "III"`, `side` is not needed. The function is an interior product
of the form $p_n(\xi)p_m(\eta)$, and the two integers `n` and `m` identify the
polynomial orders used in the two natural directions.

Examples of complete descriptors are:

```text
("I",   1, 2,    None, None)
("IIA", 3, 4,    None, None)
("IIB", 6, 1,    None, None)
("III", 6, None, 2,    4)
```

The descriptor is needed because `ScaledLagrangeBasis` later builds the
physical-coordinate power coefficients of each function. It asks the reference
basis for `definition(tau)`, reconstructs that same reference polynomial, and
then applies the powers of `y_scale` and `z_scale`.

Therefore there is only one numbering of the hierarchy: the numbering defined
by `SerendipityLagrangeReferenceBasis`. `ScaledLagrangeBasis` reuses it; it does
not create or renumber the `tau` functions.

The expected hierarchy size is:

$$ M(N)=4N,\qquad N\leq3, $$

and:

$$ M(N)=4N+\frac{(N-2)(N-3)}{2},\qquad N\geq4. $$

### What is *not* required from `core/basis.py`

`core/basis.py` also contains `QuadrilateralSerendipityCUFBasis`. That class is
**not used by this `scaled_lagrange` plugin**.

`QuadrilateralSerendipityCUFBasis` performs a generic quadrilateral
reference-to-physical map. `scaled_lagrange.py` instead uses the fixed global
scaling:

$$ \xi=\frac{y}{y_{\mathrm{scale}}},\qquad \eta=\frac{z}{z_{\mathrm{scale}}}. $$

Do not replace the reference basis with `QuadrilateralSerendipityCUFBasis` in
this example.

### Other existing infrastructure required by the plugin

The plugin also imports the following existing objects:

| Object | Module | Role |
|---|---|---|
| `CUFBasisPlugin` | `csf.cuf.core.basis_plugins` | Describes the plugin to the generic registry |
| `register_cuf_basis_plugin` | `csf.cuf.core.basis_plugins` | Registers the YAML name `scaled_lagrange` |
| `transverse_scales` | `csf.cuf.numerics` | Obtains `y_scale` and `z_scale` from the CSF section provider |

These are infrastructure dependencies; they are not part of the Lagrange
hierarchy itself.

### Verify STEP 1 before creating the plugin

Run this check from the repository environment:

```bash
python - <<'PY'
from csf.cuf.core.basis import (
    CUFBasis,
    SerendipityLagrangeReferenceBasis,
)

basis = SerendipityLagrangeReferenceBasis(4)

assert isinstance(basis, CUFBasis)
assert basis.order == 4
assert basis.size == 17

for tau in range(1, basis.size + 1):
    definition = basis.definition(tau)
    assert len(definition) == 5

    value = basis.value(tau, 0.25, -0.50)
    derivative_xi = basis.derivative(tau, "y", 0.25, -0.50)
    derivative_eta = basis.derivative(tau, "z", 0.25, -0.50)

    assert isinstance(float(value), float)
    assert isinstance(float(derivative_xi), float)
    assert isinstance(float(derivative_eta), float)

print("STEP 1 core reference basis: OK")
PY
```

If this check passes, **do not modify `core/basis.py` for the steps below**.
The required reference hierarchy is already available and the implementation
can continue with `scaled_lagrange.py`.

## 3. Mathematical definition

The physical transverse coordinates are scaled to reference coordinates:

$$ \xi = \frac{y}{y_{\mathrm{scale}}}, \qquad \eta = \frac{z}{z_{\mathrm{scale}}}. $$

The reference basis is defined on the square $[-1,1]\times[-1,1]$.

The displacement field remains

$$ \mathbf u(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,\mathbf u_\tau(x). $$

The physical transverse derivatives follow from the chain rule:

$$ F_{\tau,y} = \frac{1}{y_{\mathrm{scale}}} F_{\tau,\xi}, \qquad F_{\tau,z} = \frac{1}{z_{\mathrm{scale}}} F_{\tau,\eta}. $$

The hierarchy size is

$$ M(N)=4N,\qquad N\leq3, $$

and

$$ M(N) = 4N+\frac{(N-2)(N-3)}{2}, \qquad N\geq4. $$

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

## 4. Create the expansion module

Create this file:

```text
src/csf/cuf/expansions/scaled_lagrange.py
```

Do not rename or overwrite `scaled_lagrange_q1.py`. The Q1 plugin remains a
separate expansion.

Copy the following module **as a whole**. The class, the power-coefficient
export, the quadrature declarations, the builder, and the plugin registration
are all contained in this single file.

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


# =============================================================================
# STEP 2
# Adapt the hierarchical reference basis to scaled physical coordinates
# =============================================================================

class ScaledLagrangeBasis(CUFBasis):
    """
    Hierarchical Serendipity-Lagrange basis in scaled coordinates.

    The physical coordinates are converted to reference coordinates as:

        xi  = y / y_scale
        eta = z / z_scale

    The underlying reference basis constructs the complete hierarchy
    associated with the requested order.
    """

    def __init__(
        self,
        *,
        order: int,
        y_scale: float,
        z_scale: float,
    ) -> None:
        """Construct the scaled hierarchical basis."""

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

        # This object owns the hierarchical term definitions,
        # reference values, and reference derivatives.
        self._reference_basis = (
            SerendipityLagrangeReferenceBasis(order)
        )

        self._y_scale = y_scale
        self._z_scale = z_scale

        # Build the physical-coordinate power representation once.  The
        # solver-side displacement checkpoint consumes this optional generic
        # representation without knowing which concrete expansion produced
        # it.  Future polynomial expansions may expose the same
        # power_coefficients() method to opt into self-contained displacement
        # checkpoints; the CUFBasis core contract remains unchanged.
        self._power_coefficients = self._build_power_coefficients()
        self._power_coefficients.setflags(write=False)

    @property
    def order(self) -> int:
        """Return the hierarchy order requested by the YAML file."""

        return self._reference_basis.order

    @property
    def size(self) -> int:
        """Return the total number of transverse expansion functions."""

        return self._reference_basis.size

    @property
    def scales(self) -> tuple[float, float]:
        """Return the fixed transverse coordinate scales."""

        return self._y_scale, self._z_scale

    def definition(self, tau: int):
        """Return the hierarchical definition associated with tau."""

        return self._reference_basis.definition(tau)

    def power_coefficients(self) -> np.ndarray:
        """Return F_tau coefficients in ascending physical powers of y and z.

        The returned array has shape ``(size, order + 1, order + 1)`` and
        follows

            F_tau(y,z) = sum_{p,q} coefficients[tau-1,p,q] y**p z**q.

        This optional expansion-owned export is used only to create a
        self-contained displacement checkpoint.  It is deliberately outside
        the CUFBasis core interface so future non-polynomial expansions can
        choose a different checkpoint representation without changing core.
        """

        return self._power_coefficients.copy()

    @staticmethod
    def _reference_polynomial(order: int, *, reverse: bool = False):
        """Return p_order(mu) or p_order(-mu) in ascending powers."""

        roots = np.linspace(-1.0, 1.0, int(order), dtype=float)
        coefficients = np.poly(roots)[::-1]
        if reverse:
            coefficients = coefficients * np.power(
                -1.0,
                np.arange(coefficients.size),
            )
        return np.asarray(coefficients, dtype=float)

    def _build_power_coefficients(self) -> np.ndarray:
        """Compile every hierarchy term into physical y,z power coefficients."""

        count = self.order + 1
        coefficients = np.zeros((self.size, count, count), dtype=float)

        for tau in range(1, self.size + 1):
            kind, r, side, n, m = self.definition(tau)

            if kind == "I":
                corner_signs = (
                    (-1.0, -1.0),
                    (+1.0, -1.0),
                    (+1.0, +1.0),
                    (-1.0, +1.0),
                )
                sign_y, sign_z = corner_signs[side - 1]
                reference = 0.25 * np.outer(
                    np.asarray((1.0, sign_y)),
                    np.asarray((1.0, sign_z)),
                )
            elif kind in ("IIA", "IIB"):
                if side == 1:
                    reference = 0.5 * np.outer(
                        self._reference_polynomial(r),
                        np.asarray((1.0, -1.0)),
                    )
                elif side == 2:
                    reference = 0.5 * np.outer(
                        np.asarray((1.0, +1.0)),
                        self._reference_polynomial(r),
                    )
                elif side == 3:
                    reference = 0.5 * np.outer(
                        self._reference_polynomial(r, reverse=True),
                        np.asarray((1.0, +1.0)),
                    )
                elif side == 4:
                    reference = 0.5 * np.outer(
                        np.asarray((1.0, -1.0)),
                        self._reference_polynomial(r, reverse=True),
                    )
                else:
                    raise RuntimeError("invalid SL edge index")
            elif kind == "III":
                reference = np.outer(
                    self._reference_polynomial(n),
                    self._reference_polynomial(m),
                )
            else:
                raise RuntimeError(
                    f"unsupported SL function type {kind!r}"
                )

            rows, columns = reference.shape
            y_scaling = np.power(
                self._y_scale,
                -np.arange(rows, dtype=float),
            )
            z_scaling = np.power(
                self._z_scale,
                -np.arange(columns, dtype=float),
            )
            coefficients[tau - 1, :rows, :columns] = (
                reference
                * y_scaling[:, None]
                * z_scaling[None, :]
            )

        return coefficients

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        """
        Evaluate one basis function at physical coordinates.

        The current expansion uses fixed global scales and therefore
        does not depend explicitly on x.
        """

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
        """
        Evaluate one physical transverse derivative.

        The reference derivatives are converted through:

            d/dy = (1/y_scale) d/dxi
            d/dz = (1/z_scale) d/deta
        """

        xi = float(y) / self._y_scale
        eta = float(z) / self._z_scale

        if direction == "y":
            derivative_xi = (
                self._reference_basis.derivative(
                    tau,
                    "y",
                    xi,
                    eta,
                )
            )

            return float(
                derivative_xi / self._y_scale
            )

        if direction == "z":
            derivative_eta = (
                self._reference_basis.derivative(
                    tau,
                    "z",
                    xi,
                    eta,
                )
            )

            return float(
                derivative_eta / self._z_scale
            )

        raise ValueError(
            "direction must be 'y' or 'z'"
        )


# =============================================================================
# STEP 3
# Validate expansion-specific YAML options
# =============================================================================

def _reject_options(options):
    """
    Reject unsupported cuf.basis_options.

    The expansion obtains its transverse scales directly from the CSF
    geometry and currently requires no expansion-specific parameters.
    """

    if options:
        raise ValueError(
            "scaled_lagrange does not accept "
            "cuf.basis_options; "
            f"received {sorted(options)}"
        )


# =============================================================================
# STEP 4
# Build the basis selected by the YAML file
# =============================================================================

def _build(*, order, section_provider, options):
    """
    Construct a complete ScaledLagrangeBasis instance.

    This builder is called by the generic plugin registry.
    """

    # No expansion-specific YAML options are currently supported.
    _reject_options(options)

    # The hierarchy starts at order one.
    if not isinstance(order, int):
        raise TypeError(
            "scaled_lagrange order must be an integer"
        )

    if order < 1:
        raise ValueError(
            "scaled_lagrange order must be >= 1"
        )

    # Obtain fixed scales from the complete CSF geometry.
    y_scale, z_scale = transverse_scales(
        section_provider
    )

    return ScaledLagrangeBasis(
        order=order,
        y_scale=y_scale,
        z_scale=z_scale,
    )


# =============================================================================
# STEP 5
# Declare the minimum sectional quadrature order
# =============================================================================

def _section_gauss_minimum(basis):
    """
    Return a conservative sectional Gauss order.

    At hierarchy order N, the edge functions may contain a polynomial
    of degree N multiplied by a transverse linear factor.

    Products of two basis functions can therefore reach total degree:

        2 * (N + 1)

    During polygon slicing, the affine integration bounds may add one
    further degree to the outer one-dimensional integrand.

    An (N + 2)-point Gauss-Legendre rule is exact through degree:

        2 * (N + 2) - 1 = 2*N + 3

    The selected rule is therefore conservative for the polynomial
    products used by the sectional CUF nuclei.
    """

    if not isinstance(basis, ScaledLagrangeBasis):
        raise TypeError(
            "scaled_lagrange received an incompatible basis"
        )

    return int(basis.order) + 2


# =============================================================================
# STEP 6
# Declare the transverse contribution to longitudinal quadrature
# =============================================================================

def _longitudinal_transverse_degree(basis):
    """
    Return the conservative longitudinal degree contribution.

    An edge function of hierarchy order N can contain a polynomial
    contribution of total degree N + 1 in the transverse coordinates.

    If the physical transverse coordinates vary affinely along x,
    one basis function may therefore acquire longitudinal degree N + 1.

    A product of two basis functions may reach:

        2 * (N + 1)

    This contribution is combined by the solver with the independent
    geometry, material, and longitudinal finite-element contributions.
    """

    if not isinstance(basis, ScaledLagrangeBasis):
        raise TypeError(
            "scaled_lagrange received an incompatible basis"
        )

    return 2 * (int(basis.order) + 1)


# =============================================================================
# STEP 7
# Register the expansion
# =============================================================================

register_cuf_basis_plugin(
    CUFBasisPlugin(
        # This exact identifier is used in the YAML file.
        name="scaled_lagrange",

        # Construct the concrete scaled hierarchy.
        builder=_build,

        # Declare the minimum sectional integration order.
        section_gauss_minimum=_section_gauss_minimum,

        # Declare the longitudinal polynomial-degree contribution.
        longitudinal_transverse_degree=(
            _longitudinal_transverse_degree
        ),
    )
)

```

## 5. How the module is organized

The numbered comments inside the module divide the implementation into these
operations:

| Step in `scaled_lagrange.py` | What it does |
|---|---|
| `STEP 2` | Wraps the reference Lagrange hierarchy in physical scaled coordinates and implements `CUFBasis` |
| `STEP 3` | Rejects unsupported `cuf.basis_options` |
| `STEP 4` | Builds the basis selected by the YAML file and obtains `y_scale` and `z_scale` from CSF |
| `STEP 5` | Declares the minimum sectional Gauss order |
| `STEP 6` | Declares the transverse contribution to the longitudinal polynomial degree |
| `STEP 7` | Registers the plugin under the YAML name `scaled_lagrange` |

Inside `ScaledLagrangeBasis`, `_power_coefficients` is built once during
construction. The methods `power_coefficients()`, `_reference_polynomial()` and
`_build_power_coefficients()` are part of the class shown in Section 4; no
additional code needs to be added later.

The basis uses fixed global transverse scales. The optional `x` argument is
kept because it belongs to the common `CUFBasis` calling convention, but this
expansion does not use it explicitly.

## 6. Verify syntax and plugin registration

First verify that the module is syntactically valid:

```bash
python -m py_compile src/csf/cuf/expansions/scaled_lagrange.py
```

Then verify plugin discovery:

```bash
python -c "from csf.cuf.core.basis_plugins import available_cuf_basis_plugins; print(available_cuf_basis_plugins())"
```

The output must include:

```text
scaled_lagrange
```

No import is required in `expansions/__init__.py` if the v21 registry is using
its automatic discovery of modules below `csf.cuf.expansions`.

## 7. YAML case

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


## 8. Power-coefficient export and optional displacement checkpoint

`ScaledLagrangeBasis` also exports each basis function as physical power
coefficients. The representation is

$$ F_\tau(y,z) = \sum_{p,q}C_{\tau pq}y^p z^q. $$

The public method returns a copy of the coefficients:

```python
def power_coefficients(self) -> np.ndarray:
    return self._power_coefficients.copy()
```

The coefficients are constructed in `__init__` by calling
`_build_power_coefficients()` and the stored array is then marked read-only.
This is already part of the class created in Section 4.

The solver may use this export after the KKT solve to create a self-contained
displacement checkpoint:

```text
<case.name>.cuf.npz
```

Using the checkpoint is optional. The coefficient export itself is part of
this `ScaledLagrangeBasis` implementation.

At fixed `x`, the solved CUF amplitudes and transverse coefficients can be
contracted into the section polynomials $u_x(y,z)$, $u_y(y,z)$ and $u_z(y,z)$.

## 9. Verification tests

Run the following tests only after Sections 2, 4 and 6 succeed. Each test
imports the `ScaledLagrangeBasis` created in Section 4; none of them defines a
second implementation.

## 9.1 Hierarchy, size, and finite values

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

## 9.2 Q1 Kronecker property

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

## 9.3 Hierarchical prefix stability

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

## 9.4 Analytical derivatives versus finite differences

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

## 9.5 Exact N1 equivalence with `scaled_lagrange_q1`

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

## 9.6 Power-coefficient export

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

## 9.7 Compiled displacement checkpoint round-trip

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

## 10. Full solver regression

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

## 11. Convergence campaign N1-N27

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

## 12. Completion checklist

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
