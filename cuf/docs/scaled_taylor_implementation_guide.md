# DRAFT

# Implementing the `scaled_taylor` Expansion in CSF-CUF

## 1. Purpose

This guide shows how to add a complete two-dimensional **scaled Taylor expansion** to CSF-CUF using the same isolated plugin architecture already used by the existing transverse expansions.

The implementation follows the same architectural rules as `scaled_lagrange`:

- do not modify the CUF formulation;
- do not add expansion-name branches to `solver/engine.py`;
- do not modify the KKT construction;
- keep plugin-specific code in `src/csf/cuf/expansions`;
- keep YAML selection declarative;
- preserve a stable meaning for every CUF index `tau`;
- keep code comments and YAML comments in English.

The proposed plugin name is:

```text
scaled_taylor
```

The expansion is a complete total-degree polynomial basis in shifted and scaled transverse coordinates. Its default centre is `(0, 0)`. With that default centre, the polynomial space is exactly the same as the existing `scaled_maclaurin` expansion.

The reason for keeping `scaled_taylor` separate is semantic and practical: it exposes an explicit Taylor expansion centre while retaining the same generic CUF plugin contract.

---

## 2. Mathematical definition

Let the Taylor centre be
```math
(y_c,z_c).
```
Let the global transverse scales supplied by the CSF geometry be
```math
y_s>0, \qquad z_s>0.
```
Define the shifted scaled coordinates
```math
Y=\frac{y-y_c}{y_s},
\qquad
Z=\frac{z-z_c}{z_s}.
```
For expansion order `N`, the complete Taylor basis contains all monomials
```math
F_{pq}(y,z)=Y^p Z^q,
\qquad p\ge 0,\ q\ge 0,\ p+q\le N.
```
The CUF displacement field remains
```math
\mathbf u(x,y,z)
=
\sum_{\tau=1}^{M}F_\tau(y,z)\,\mathbf u_\tau(x).
```
The number of transverse functions is
```math
M(N)=\frac{(N+1)(N+2)}{2}.
```
Examples:

| Order N | Functions M |
|---:|---:|
| 0 | 1 |
| 1 | 3 |
| 2 | 6 |
| 3 | 10 |
| 4 | 15 |
| 6 | 28 |
| 10 | 66 |
| 20 | 231 |

The physical transverse derivatives are
```math
\frac{\partial F_{pq}}{\partial y}
=
\begin{cases}
0, & p=0,\\
\dfrac{p}{y_s}Y^{p-1}Z^q, & p>0,
\end{cases}
```
and
```math
\frac{\partial F_{pq}}{\partial z}
=
\begin{cases}
0, & q=0,\\
\dfrac{q}{z_s}Y^pZ^{q-1}, & q>0.
\end{cases}
```
No derivative with respect to `x` is introduced by this expansion. The Taylor centre and the transverse scales are fixed for the basis instance, therefore
```math
F_\tau=F_\tau(y,z).
```
### 2.1 Relation with the existing `scaled_maclaurin`

The existing `ScaledMaclaurinBasis` evaluates
```math
\left(\frac{y}{y_s}\right)^p
\left(\frac{z}{z_s}\right)^q.
```
Therefore `scaled_taylor` with
```math
y_c=0,\qquad z_c=0
```
is algebraically identical to `scaled_maclaurin` for the same order and scales.

This gives a strong regression test: with a zero Taylor centre, both bases must produce the same values and transverse derivatives for every `tau`.

### 2.2 Why no factorial appears in the basis

In a classical Taylor series, the factorial factors arise because the coefficients are defined directly from derivatives of the expanded function at the expansion centre.

In the present CUF formulation, `scaled_taylor` instead denotes a complete polynomial basis expressed in shifted and scaled transverse coordinates. The generalized CUF amplitudes are independent unknowns determined by the structural problem; they are not identified with derivatives of the displacement field evaluated at the Taylor centre.

Therefore the factorial normalization of the classical Taylor-series coefficients is not required. The basis is written as

```math
Y^p Z^q
```

rather than

```math
\frac{Y^p Z^q}{p!q!}.
```

Including the factor `1/(p!q!)` would only multiply each basis function by a non-zero constant and would therefore rescale the corresponding generalized CUF amplitude. It would not change the finite-dimensional polynomial approximation space spanned by the complete basis.

Thus, in `scaled_taylor`, the word *Taylor* refers to the use of a complete polynomial basis centred at `(y_c,z_c)`, not to the literal reconstruction of a known function from its derivatives as in a classical Taylor series.

The choice of normalization can still affect the numerical scaling and conditioning of the algebraic system, even though it does not change the approximation space.
---

## 3. Stable `tau` numbering

Use exactly the same complete-total-degree ordering already used by `ScaledMaclaurinBasis`:

```python
_exponents = tuple(
    (p_y, degree - p_y)
    for degree in range(order + 1)
    for p_y in range(degree, -1, -1)
)
```

This gives:

```text
tau 1  -> (0,0) -> 1

tau 2  -> (1,0) -> Y
tau 3  -> (0,1) -> Z

tau 4  -> (2,0) -> Y^2
tau 5  -> (1,1) -> Y Z
tau 6  -> (0,2) -> Z^2

...
```

The important requirement is that the mapping from `tau` to `(p_y,p_z)` never depends on geometry, material, the Taylor centre, or the longitudinal coordinate.

---

## 4. Create the expansion module

Create:

```text
src/csf/cuf/expansions/scaled_taylor.py
```

A self-contained implementation can be kept entirely inside the plugin module. No change to `core/basis.py` is required.

```python
# Version: CSF-CUF scaled Taylor expansion v1 - 2026-09-20
"""Complete scaled Taylor transverse expansion."""

from __future__ import annotations

import math
import numpy as np

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import (
    CUFBasisPlugin,
    register_cuf_basis_plugin,
)
from csf.cuf.numerics import transverse_scales


class ScaledTaylorBasis(CUFBasis):
    """Complete two-dimensional Taylor basis in shifted scaled coordinates."""

    def __init__(
        self,
        order: int,
        *,
        y_scale: float,
        z_scale: float,
        y_center: float = 0.0,
        z_center: float = 0.0,
    ) -> None:
        if not isinstance(order, int) or order < 0:
            raise ValueError("scaled_taylor order must be a non-negative integer")

        y_scale = float(y_scale)
        z_scale = float(z_scale)
        y_center = float(y_center)
        z_center = float(z_center)

        if not math.isfinite(y_scale) or y_scale <= 0.0:
            raise ValueError("y_scale must be positive and finite")
        if not math.isfinite(z_scale) or z_scale <= 0.0:
            raise ValueError("z_scale must be positive and finite")
        if not math.isfinite(y_center):
            raise ValueError("y_center must be finite")
        if not math.isfinite(z_center):
            raise ValueError("z_center must be finite")

        self._order = int(order)
        self._y_scale = y_scale
        self._z_scale = z_scale
        self._y_center = y_center
        self._z_center = z_center

        self._exponents = tuple(
            (p_y, degree - p_y)
            for degree in range(order + 1)
            for p_y in range(degree, -1, -1)
        )
        self._size = len(self._exponents)

        self._p_y = np.fromiter(
            (item[0] for item in self._exponents),
            dtype=np.intp,
            count=self._size,
        )
        self._p_z = np.fromiter(
            (item[1] for item in self._exponents),
            dtype=np.intp,
            count=self._size,
        )
        self._p_y.setflags(write=False)
        self._p_z.setflags(write=False)

    @property
    def order(self) -> int:
        return self._order

    @property
    def size(self) -> int:
        return self._size

    @property
    def scales(self) -> tuple[float, float]:
        return self._y_scale, self._z_scale

    @property
    def center(self) -> tuple[float, float]:
        return self._y_center, self._z_center

    def exponents(self, tau: int) -> tuple[int, int]:
        tau = int(tau)
        if not 1 <= tau <= self._size:
            raise IndexError(f"tau must be in 1..{self._size}")
        return self._exponents[tau - 1]

    def _scaled_coordinates(self, y: float, z: float) -> tuple[float, float]:
        Y = (float(y) - self._y_center) / self._y_scale
        Z = (float(z) - self._z_center) / self._z_scale
        return Y, Z

    def value(
        self,
        tau: int,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> float:
        del x
        p_y, p_z = self.exponents(tau)
        Y, Z = self._scaled_coordinates(y, z)
        return float((Y ** p_y) * (Z ** p_z))

    def values(
        self,
        y: float,
        z: float,
        *,
        x: float | None = None,
    ) -> np.ndarray:
        del x
        Y, Z = self._scaled_coordinates(y, z)

        y_powers = np.empty(self._order + 1, dtype=float)
        z_powers = np.empty(self._order + 1, dtype=float)
        y_powers[0] = 1.0
        z_powers[0] = 1.0

        for degree in range(1, self._order + 1):
            y_powers[degree] = y_powers[degree - 1] * Y
            z_powers[degree] = z_powers[degree - 1] * Z

        return np.asarray(
            y_powers[self._p_y] * z_powers[self._p_z],
            dtype=float,
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
        del x
        p_y, p_z = self.exponents(tau)
        Y, Z = self._scaled_coordinates(y, z)

        if direction == "y":
            if p_y == 0:
                return 0.0
            return float(
                p_y
                * (Y ** (p_y - 1))
                * (Z ** p_z)
                / self._y_scale
            )

        if direction == "z":
            if p_z == 0:
                return 0.0
            return float(
                p_z
                * (Y ** p_y)
                * (Z ** (p_z - 1))
                / self._z_scale
            )

        raise ValueError("direction must be 'y' or 'z'")


def _parse_options(options):
    """Validate and return the Taylor centre from cuf.basis_options."""

    options = dict(options)
    allowed = {"y_center", "z_center"}
    unknown = sorted(set(options) - allowed)

    if unknown:
        raise ValueError(
            "scaled_taylor received unsupported cuf.basis_options: "
            f"{unknown}"
        )

    y_center = float(options.get("y_center", 0.0))
    z_center = float(options.get("z_center", 0.0))

    if not math.isfinite(y_center):
        raise ValueError("scaled_taylor y_center must be finite")
    if not math.isfinite(z_center):
        raise ValueError("scaled_taylor z_center must be finite")

    return y_center, z_center


def _build(*, order, section_provider, continuous_section_field, options):
    del continuous_section_field  # Available by contract; unused here.

    y_center, z_center = _parse_options(options)
    y_scale, z_scale = transverse_scales(section_provider)

    return ScaledTaylorBasis(
        int(order),
        y_scale=y_scale,
        z_scale=z_scale,
        y_center=y_center,
        z_center=z_center,
    )


def _section_gauss_minimum(basis):
    return int(basis.order) + 1


def _longitudinal_transverse_degree(basis):
    return 2 * int(basis.order)


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="scaled_taylor",
        builder=_build,
        section_gauss_minimum=_section_gauss_minimum,
        longitudinal_transverse_degree=_longitudinal_transverse_degree,
    )
)
```

---

## 5. YAML interface

With the default centre `(0,0)`:

```yaml
cuf:
  basis: scaled_taylor
  order: 6
```

With an explicit Taylor centre:

```yaml
cuf:
  basis: scaled_taylor
  order: 6
  basis_options:
    y_center: 12.5
    z_center: -8.0
```

The centre is expressed in the same physical transverse coordinate system used by the CSF geometry.

The scales remain automatic and are obtained from `transverse_scales(section_provider)` exactly as for the existing scaled polynomial expansions.

---

## 6. Section quadrature requirement

At order `N`, every basis function has total transverse polynomial degree at most `N`.

A product of two basis functions therefore has total degree at most
```math
2N.
```
The same degree statement holds after translation by `(y_c,z_c)`: translation changes polynomial coefficients, not polynomial degree.

Therefore the same minimum used by `scaled_maclaurin` is retained:

```python
def _section_gauss_minimum(basis):
    return int(basis.order) + 1
```

An `(N+1)`-point Gauss-Legendre rule is exact through one-dimensional polynomial degree
```math
2(N+1)-1=2N+1,
```
which provides the same conservative rule already adopted for the existing complete monomial basis.

---

## 7. Longitudinal polynomial-degree contribution

The Taylor shift does not increase polynomial degree.

If the transverse physical coordinates vary affinely along `x`, a basis monomial of total degree `N` contributes at most degree `N` in `x`. A product of two transverse basis functions therefore contributes at most
```math
2N.
```
Use:

```python
def _longitudinal_transverse_degree(basis):
    return 2 * int(basis.order)
```

This is identical to the declaration used by `scaled_maclaurin` and `scaled_legendre`.

---

## 8. Plugin discovery

No edit to `src/csf/cuf/expansions/__init__.py` is required.

The generic registry imports every module under `csf.cuf.expansions` and the new module registers itself with:

```python
register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="scaled_taylor",
        ...
    )
)
```

Verify syntax:

```bash
python -m py_compile src/csf/cuf/expansions/scaled_taylor.py
```

Verify automatic discovery:

```bash
python -c "from csf.cuf.core.basis_plugins import available_cuf_basis_plugins; print(available_cuf_basis_plugins())"
```

The output must contain:

```text
scaled_taylor
```

---

## 9. Minimum mathematical tests

Create focused tests before running structural validation cases.

### 9.1 Size

```python
for order in range(0, 10):
    basis = ScaledTaylorBasis(
        order,
        y_scale=2.0,
        z_scale=3.0,
    )
    expected = (order + 1) * (order + 2) // 2
    assert basis.size == expected
```

### 9.2 Stable exponent ordering

For `N=2`:

```python
basis = ScaledTaylorBasis(2, y_scale=2.0, z_scale=3.0)

assert basis.exponents(1) == (0, 0)
assert basis.exponents(2) == (1, 0)
assert basis.exponents(3) == (0, 1)
assert basis.exponents(4) == (2, 0)
assert basis.exponents(5) == (1, 1)
assert basis.exponents(6) == (0, 2)
```

### 9.3 Centre property

At the Taylor centre, all non-constant terms must vanish:

```python
basis = ScaledTaylorBasis(
    4,
    y_scale=10.0,
    z_scale=20.0,
    y_center=3.0,
    z_center=-5.0,
)

assert basis.value(1, 3.0, -5.0) == 1.0

for tau in range(2, basis.size + 1):
    assert basis.value(tau, 3.0, -5.0) == 0.0
```

### 9.4 Analytical derivatives versus finite differences

```python
basis = ScaledTaylorBasis(
    6,
    y_scale=12.0,
    z_scale=7.0,
    y_center=1.5,
    z_center=-0.75,
)

h = 1.0e-6

y = 2.25
z = -1.10

for tau in range(1, basis.size + 1):
    dy_fd = (
        basis.value(tau, y + h, z)
        - basis.value(tau, y - h, z)
    ) / (2.0 * h)

    dz_fd = (
        basis.value(tau, y, z + h)
        - basis.value(tau, y, z - h)
    ) / (2.0 * h)

    assert abs(basis.derivative(tau, "y", y, z) - dy_fd) < 1.0e-8
    assert abs(basis.derivative(tau, "z", y, z) - dz_fd) < 1.0e-8
```

### 9.5 Regression against `ScaledMaclaurinBasis`

This is the strongest basic regression test.

For zero centre, the two implementations must agree function by function:

```python
from csf.cuf.numerics import ScaledMaclaurinBasis

order = 8
y_scale = 13.0
z_scale = 9.0

mac = ScaledMaclaurinBasis(
    order,
    y_scale=y_scale,
    z_scale=z_scale,
)

tay = ScaledTaylorBasis(
    order,
    y_scale=y_scale,
    z_scale=z_scale,
    y_center=0.0,
    z_center=0.0,
)

for y, z in [
    (-4.0, -2.0),
    (0.0, 0.0),
    (1.25, -3.5),
    (7.0, 4.0),
]:
    for tau in range(1, tay.size + 1):
        assert tay.value(tau, y, z) == mac.value(tau, y, z)
        assert tay.derivative(tau, "y", y, z) == mac.derivative(tau, "y", y, z)
        assert tay.derivative(tau, "z", y, z) == mac.derivative(tau, "z", y, z)
```

The equality can be exact because both implementations use the same arithmetic when the centre is zero.

---

## 10. Structural regression

After the basis-level tests pass, run one already validated CSF-CUF case twice:

1. with `scaled_maclaurin`;
2. with `scaled_taylor` and the default centre `(0,0)`.

Keep all other YAML fields identical.

The following should match to numerical precision:

- KKT dimensions;
- KKT sparsity pattern / `nnz`;
- effective section Gauss order;
- estimated longitudinal degree;
- effective longitudinal Gauss order;
- generalized solution after accounting for identical basis normalization;
- reconstructed displacement field `u(x,y,z)`;
- stresses derived from that field;
- reported maxima and their locations.

Only after this zero-centre equivalence test should non-zero Taylor centres be used in convergence experiments.

---

## 11. Expected numerical interpretation

Changing the Taylor centre does **not** change the finite-dimensional polynomial space when the same complete order `N` is retained.

For any fixed `N`, the bases
```math
\{y^p z^q : p+q\le N\}
```
and
```math
\{(y-y_c)^p(z-z_c)^q : p+q\le N\}
```
span the same polynomial space.

Therefore, in exact arithmetic and with a complete basis, changing `(y_c,z_c)` is a change of coordinates inside the same approximation space, not a richer or poorer kinematic model.

Its practical effect is numerical: the translation changes the basis coefficients and can change the conditioning and scaling of the assembled algebraic system.

This distinction should be stated explicitly in the documentation.

---

## 12. Optional physical power-coefficient export

If the displacement checkpoint requires `power_coefficients()`, the shifted basis can be converted exactly to powers of physical `y` and `z` using the binomial theorem:
```math
\left(\frac{y-y_c}{y_s}\right)^p
\left(\frac{z-z_c}{z_s}\right)^q.
```
Expand each factor as
```math
(y-y_c)^p
=
\sum_{i=0}^{p}
\binom{p}{i}
y^i(-y_c)^{p-i},
```
and
```math
(z-z_c)^q
=
\sum_{j=0}^{q}
\binom{q}{j}
z^j(-z_c)^{q-j}.
```
Hence
```math
F_{pq}(y,z)
=
\sum_{i=0}^{p}
\sum_{j=0}^{q}
\frac{\binom{p}{i}\binom{q}{j}
(-y_c)^{p-i}(-z_c)^{q-j}}
{y_s^p z_s^q}
\,y^i z^j.
```
This gives a direct exact `power_coefficients()` implementation without symbolic algebra.

A compact implementation is:

```python
def _build_power_coefficients(self) -> np.ndarray:
    count = self.order + 1
    coefficients = np.zeros((self.size, count, count), dtype=float)

    for tau in range(1, self.size + 1):
        p, q = self.exponents(tau)

        for i in range(p + 1):
            cy = (
                math.comb(p, i)
                * ((-self._y_center) ** (p - i))
                / (self._y_scale ** p)
            )

            for j in range(q + 1):
                cz = (
                    math.comb(q, j)
                    * ((-self._z_center) ** (q - j))
                    / (self._z_scale ** q)
                )

                coefficients[tau - 1, i, j] += cy * cz

    return coefficients
```

If checkpoint compatibility is required from the first version, add this export immediately. Otherwise it can remain a second implementation step, because it is not part of the mandatory `CUFBasis` contract.

---

## 13. Recommended first version

For the first implementation, keep the scope deliberately small:

- complete total-degree Taylor basis only;
- fixed global centre `(y_center,z_center)`;
- automatic global transverse scales from CSF;
- no explicit `x` dependence;
- no per-polygon centre;
- no adaptive centre;
- no change to the solver;
- no new KKT logic.

This gives a clean new expansion plugin while keeping the architectural separation already established by CSF-CUF.

---

## 14. Summary

The proposed `scaled_taylor` plugin is the shifted counterpart of the existing complete scaled Maclaurin basis:
```math
F_{pq}(y,z)
=
\left(\frac{y-y_c}{y_s}\right)^p
\left(\frac{z-z_c}{z_s}\right)^q,
\qquad p+q\le N.
```
It requires no solver-specific branch and no modification of the CUF equations.

The default centre `(0,0)` provides an exact regression bridge to `scaled_maclaurin`. A non-zero centre then allows the same polynomial CUF space to be represented around an arbitrary physical point, making the Taylor interpretation explicit and providing a controlled way to study the numerical effect of basis translation.
