# CSF-CUF Generalized Expansion Interface

## Mathematical contract, architectural generality, and the `xyz_demo_expansion.py` reference example

**Document type:** Technical reference  
**Date:** 9 October 2026  
**Scope:** CUF expansion plugins and their interaction with CSF, the longitudinal finite-element approximation, and problem adapters  
**Companion implementation:** `xyz_demo_expansion.py`  
**Status:** Reference description of the existing demonstration plugin, with separately identified potential extensions

---

## 1. Purpose and scope

CSF-CUF separates the continuous description of a beam from the mathematical approximation of its displacement field. Its CUF expansion interface is not limited to conventional two-dimensional transverse polynomials. An expansion can depend explicitly on all three spatial coordinates and, when needed, use the continuous geometry exposed by CSF.

This document has two objectives:

1. State the general architectural meaning of the CUF expansion interface.
2. Explain, in mathematical and implementation terms, a minimal four-function plugin (`xyz_demo_expansion.py`) that illustrates dependence on the longitudinal coordinate in addition to the transverse coordinates.

It also specifies the evaluation contract that all spatially aware load, boundary-condition, and other problem adapters must respect. More advanced geometry-dependent or polygon-specific constructions are described as *capabilities enabled by the architecture*, not features implemented by this particular demonstration.

## 2. Generality of the CUF Expansion Interface

In CSF-CUF, the CUF expansion is an independent mathematical component, not restricted to predefined polynomial families or functions of the transverse coordinates alone.

An expansion plugin may define its functions in terms of all three spatial coordinates and the continuous geometry provided by CSF, including individual polygons, their interfaces, and longitudinal geometric variations.

The plugin is responsible for consistently evaluating its expansion functions and their first spatial derivatives. It may also implement its own construction procedures, higher-order derivatives, and mathematical consistency checks, including inter-polygon continuity, regularity, and linear independence.

The CUF solver remains independent of how the expansion is constructed. It operates through a common mathematical interface, allowing substantially different expansion strategies to be introduced without modifying the underlying CUF nuclei.

This generality is an architectural property of CSF-CUF. Specific consistency guarantees, such as higher-order continuity, depend on the individual plugin and its verification procedures.

### 2.1 A single definition and verification point

The principal architectural advantage is that the expansion can act as one identifiable mathematical component. Its construction, function values, spatial derivatives, numerical requirements, and applicable verification procedures can be maintained together. The solver then consumes the agreed interface instead of implementing knowledge of individual basis families.

The resulting separation is:

```text
Continuous Section Field (CSF)
  |  Continuous geometry, sections, polygon descriptions, material fields
  v
CUF expansion plugin
  |  Defines F_tau(x,y,z; G_CSF)
  |  Evaluates F_tau and its first derivatives
  |  May build and validate more advanced, geometry-adapted expansions
  v
CUF solver
  |  Longitudinal finite elements, CUF nuclei, quadrature,
  |  assembly, algebraic solution and reconstruction
  v
Continuous displacement approximation and derived fields
```

CSF remains the source of geometric information; a geometry-aware expansion *uses* this information without becoming a second definition of the geometry. Material laws, loads, constraints, and solver responsibilities remain separately defined.

## 3. Coordinates and the generalized approximation

Within the CUF solver convention:

- `x` denotes the longitudinal beam coordinate;
- `y` and `z` denote coordinates in the cross-sectional plane;
- `u_x`, `u_y`, and `u_z` denote the corresponding physical displacement components.

The coordinate mapping to the CSF geometric convention must be handled consistently wherever geometry is queried. In the established convention, `(x,y,z)_CUF = (Z,X,Y)_CSF`.

A generalized expansion function is written as

$$
F_\tau = F_\tau(x,y,z;\mathcal G_{\mathrm{CSF}}),
$$

where $\mathcal G_{\mathrm{CSF}}$ denotes optional continuous geometric information, and $\tau = 1,\ldots,M$ identifies a basis function.

For a longitudinal finite-element approximation, the displacement field is

$$
\boxed{
\mathbf u_h(x,y,z)
= \sum_{e}\sum_{i\in e}\sum_{\tau=1}^{M}
N_i^{(e)}(x)\,F_\tau(x,y,z;\mathcal G_{\mathrm{CSF}})
\,\mathbf q_{i\tau}^{(e)}
}
$$

with the element contributions assembled using the standard finite-element connectivity and conventions. Here $N_i^{(e)}(x)$ are longitudinal shape functions and $\mathbf q_{i\tau}^{(e)}$ are CUF displacement coefficients. The transverse expansion and the longitudinal finite-element interpolation remain separate mathematical ingredients even when $F_\tau$ itself depends on $x$.

### 3.1 Spatial derivatives and the longitudinal product rule

The transverse derivatives of the approximate displacement are

$$
\frac{\partial\mathbf u_h}{\partial y}
=\sum_{e,i,\tau} N_i^{(e)} F_{\tau,y}\,\mathbf q_{i\tau}^{(e)},
\qquad
\frac{\partial\mathbf u_h}{\partial z}
=\sum_{e,i,\tau} N_i^{(e)} F_{\tau,z}\,\mathbf q_{i\tau}^{(e)}.
$$

Its longitudinal derivative requires both contributions:

$$
\boxed{
\frac{\partial\mathbf u_h}{\partial x}
=\sum_{e,i,\tau}
\left[\frac{dN_i^{(e)}}{dx}F_\tau
+N_i^{(e)}\frac{\partial F_\tau}{\partial x}\right]
\mathbf q_{i\tau}^{(e)}.
}
$$

The second term is essential when the expansion depends explicitly on $x$, whether through a direct coordinate dependence, a geometry-dependent mapping, or another longitudinally varying construction.

For the standard small-strain, displacement-based formulation, the first spatial derivatives enter the displacement gradient and strain tensor. The internal CUF integration uses the corresponding products in its nuclei. Higher-order derivatives may be used by a plugin for construction and consistency checks; they are not part of the present first-derivative `CUFBasis` evaluation contract.

## 4. Why the XYZ demonstration was constructed

The purpose of `xyz_demo_expansion.py` is to make the generalized three-coordinate interface visible with the smallest practical example. It intentionally does *not* compose existing Legendre, Lagrange, or Maclaurin expansion plugins.

The demonstration uses four explicitly defined functions:

$$
\boxed{
\begin{aligned}
F_1(x,y,z)&=1,\\
F_2(x,y,z)&=y,\\
F_3(x,y,z)&=z,\\
F_4(x,y,z)&=xyz.
\end{aligned}}
$$

The first three functions provide a constant term and two first-order transverse terms. The fourth couples the longitudinal coordinate and the two transverse coordinates in a single polynomial. This is sufficient to demonstrate all three first-derivative directions and the nonzero contribution $F_{\tau,x}$ in the longitudinal product rule.

### 4.1 Basis dimension and order label

The implementation fixes

$$M=4,\qquad \tau\in\{1,2,3,4\}.$$

It accepts `order: 1` as its fixed configuration identifier. This does **not** mean that it generates all polynomials up to degree one or a complete order-one three-dimensional polynomial space. In particular, $F_4=xyz$ has total polynomial degree three; the example is a selected four-function basis, not a systematic polynomial hierarchy.

The functions are linearly independent on any nondegenerate open three-dimensional domain containing variation in all relevant coordinates. However, that statement is not equivalent to an assertion that the basis is complete for beam elasticity or suitable for arbitrary convergence studies.

### 4.2 Complete table of first derivatives

| $\tau$ | $F_\tau$ | $\partial F_\tau/\partial x$ | $\partial F_\tau/\partial y$ | $\partial F_\tau/\partial z$ |
|---:|---|---|---|---|
| 1 | $1$ | $0$ | $0$ | $0$ |
| 2 | $y$ | $0$ | $1$ | $0$ |
| 3 | $z$ | $0$ | $0$ | $1$ |
| 4 | $xyz$ | $yz$ | $xz$ | $xy$ |

The derivatives of the fourth function are obtained directly from the polynomial definition:

$$
F_{4,x}=yz,\qquad F_{4,y}=xz,\qquad F_{4,z}=xy.
$$

They are analytic expressions evaluated at the same physical point $(x,y,z)$ as the original function.

### 4.3 Second and mixed derivatives

Although not required by the current basic evaluation interface, the example also admits exact derivatives of higher order. All second derivatives of $F_1$, $F_2$, and $F_3$ vanish. The Hessian of $F_4$ in the coordinate order $(x,y,z)$ is

$$
\nabla^2 F_4 =
\begin{bmatrix}
0 & z & y\\
z & 0 & x\\
y & x & 0
\end{bmatrix}.
$$

Thus the pure second derivatives vanish, while

$$
F_{4,xy}=z,\qquad F_{4,xz}=y,\qquad F_{4,yz}=x.
$$

The mixed third derivative is $F_{4,xyz}=1$. These formulas make this simple example suitable for demonstrating derivative-consistency checks beyond first order, even though its Python class implements only the first-derivative methods required by the solver.

### 4.4 Numerical evaluation example

At the physical point $(x,y,z)=(2,3,5)$:

$$
(F_1,F_2,F_3,F_4)=(1,3,5,30),
$$

$$
(F_{1,x},F_{2,x},F_{3,x},F_{4,x})=(0,0,0,15),
$$

$$
(F_{1,y},F_{2,y},F_{3,y},F_{4,y})=(0,1,0,10),
$$

$$
(F_{1,z},F_{2,z},F_{3,z},F_{4,z})=(0,0,1,6).
$$

This numerical point is used only to illustrate the evaluation contract; it does not represent a particular beam, polygon, load case, or geometry.

## 5. How `xyz_demo_expansion.py` implements the contract

The demonstration is one self-contained Python file. It registers a plugin and defines one `CUFBasis` subclass. Its mathematical functions do not depend on any other expansion family.

### 5.1 The basis class

```python
class XYZDemoBasis(CUFBasis):
    @property
    def order(self) -> int:
        return 1

    @property
    def size(self) -> int:
        return 4
```

`size` determines the number of expansion functions visible to the CUF solver. `order` is a fixed configuration value validated by the builder rather than a generator of higher-order functions.

### 5.2 Index and coordinate validation

The private `_check_tau()` routine requires an integer index between one and four. The `_require_x()` routine enforces availability of the longitudinal coordinate whenever the explicit polynomial evaluation needs it. No geometric properties are inferred or silently substituted.

### 5.3 Function evaluation

```python
def value(self, tau, y, z, *, x=None):
    ...
```

The function index chooses among $1$, $y$, $z$, and $xyz$. The actual implementation converts numeric values to `float` and uses `_require_x(x)` for $F_4$. The parameter `x` is keyword-only by the `CUFBasis` interface convention.

### 5.4 Transverse derivatives

```python
def derivative(self, tau, direction, y, z, *, x=None):
    ...
```

`direction='y'` returns $F_{\tau,y}$; `direction='z'` returns $F_{\tau,z}$. For $F_4$ both of these derivatives depend on $x$, so the complete spatial evaluation point matters even though the requested derivative direction is transverse. Unsupported direction labels are rejected.

### 5.5 Longitudinal derivative

```python
def longitudinal_derivative(self, tau, y, z, *, x=None):
    ...
```

The method returns zero for $\tau=1,2,3$ and returns $yz$ for $\tau=4$. This overrides the backwards-compatible default longitudinal derivative provided by `CUFBasis` and signals the explicit $x$-dependent expansion behavior to the caller.

### 5.6 Builder and contextual information

The builder uses the established registration signature:

```python
def _build(*, order, section_provider, continuous_section_field, options):
    ...
```

It accepts only `order == 1`, rejects nonempty basis options, and returns an `XYZDemoBasis` instance. The generic builder contract makes both `section_provider` and `continuous_section_field` available. **This demonstration does not consume either of them**, which is intentional: it isolates coordinate dependence from geometry dependence.

A more advanced plugin may retain the CSF context and query the section and polygons at the current longitudinal position, without redefining the CUF solver kernels.

### 5.7 Registration and quadrature metadata

```python
register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="xyz_demo",
        builder=_build,
        section_gauss_minimum=lambda basis: 3,
        longitudinal_transverse_degree=lambda basis: 6,
    )
)
```

The registered name is `xyz_demo`. The plugin supplies a minimum section Gauss-order request and a longitudinal/transverse degree estimate used by the solver's quadrature policy. The values `3` and `6` are demonstration metadata chosen conservatively for this implementation; they are **not** a general quadrature theorem, not a universal guarantee of exact integration for every CSF geometry, and not a convergence certificate.

## 6. The evaluation contract for problem adapters

**Every adapter that evaluates a spatially varying CUF expansion must supply the complete physical coordinate triplet $(x,y,z)$ of the point being evaluated.** The longitudinal coordinate must be passed using the `x=` keyword prescribed by the Python interface; `y` and `z` are the transverse positional arguments.

The following signatures describe the current `CUFBasis` contract:

```python
basis.value(tau, y, z, x=x)
basis.derivative(tau, "y", y, z, x=x)
basis.derivative(tau, "z", y, z, x=x)
basis.longitudinal_derivative(tau, y, z, x=x)
```

Here the symbols `x`, `y`, and `z` denote the coordinates of **one and the same physical evaluation point**, not independent reference points.

### 6.1 What this means for adapters

The requirement applies consistently wherever an adapter or associated projection operator evaluates an expansion, including:

- point, line, surface, and distributed loads;
- boundary conditions and essential-displacement projections;
- integral constraints, mean-displacement conditions, and gauge conditions;
- geometric or field-based coupling conditions;
- evaluation at longitudinal quadrature points, cross-sectional quadrature points, and physical boundary points.

A load or constraint adapter defines *what physical action or condition is imposed*. It must not embed assumptions about the specific polynomial family, nor choose an unrelated longitudinal coordinate in place of the actual point being integrated or constrained.

For a generic point-evaluation operation the expected pattern is:

```python
# x, y, z identify the physical evaluation point.
F = basis.value(tau, y, z, x=x)
Fy = basis.derivative(tau, "y", y, z, x=x)
Fz = basis.derivative(tau, "z", y, z, x=x)
Fx = basis.longitudinal_derivative(tau, y, z, x=x)
```

The first derivative contract is deliberately independent of how a plugin internally builds $F_\tau$.

### 6.2 Integration must retain spatial dependence

When a spatially dependent function occurs inside an integral, its value is to be evaluated at each integration point. For example, a general coefficient associated with a longitudinally averaged displacement on the line $(y_0,z_0)$ has the form

$$
A_{i\tau}=\frac{1}{L}\int_{x_0}^{x_1}
N_i(x)F_\tau(x,y_0,z_0)\,dx.
$$

This expression retains the possible $x$-dependence of the expansion. A factorization of the function outside the integral is justified only when its value is constant over the integration domain (or when an equivalent analytic identity has been established).

Likewise, if the geometry changes along the beam, the cross-sectional integration points and geometric weights must correspond to the CSF section at the current longitudinal position.

### 6.3 Coordinate consistency

All callers must use a consistent physical coordinate convention. If a geometric utility uses CSF's $(X,Y,Z)$ ordering while a CUF plugin uses $(x,y,z)$, the mapping must be performed deliberately at the boundary between these components. An adapter should never rely on an unstated change of coordinate ordering.

## 7. Direct use as an external expansion plugin

The existing external-basis loader accepts a trusted Python source file using the same `register_cuf_basis_plugin()` mechanism as built-in expansions. The reference may be written in the case YAML as a path under `cuf.basis`; relative paths are resolved from the directory containing the case YAML.

For example, if the case file and the plugin are located so that the following relative path is valid:

```yaml
cuf:
  basis: ../expansions/xyz_demo_expansion.py

  # Order of the transverse expansion.
  order: 1
```

The source file must be present at the referenced location, and the CSF-CUF package must be available in the Python execution environment. The filename path is illustrative; it does not prescribe a particular project directory structure.

The same `CUFBasis` methods can be evaluated from ordinary Python after creating or obtaining an instance. For a direct mathematical check:

```python
basis = XYZDemoBasis()
x, y, z = 2.0, 3.0, 5.0

assert basis.size == 4
assert basis.value(4, y, z, x=x) == 30.0
assert basis.longitudinal_derivative(4, y, z, x=x) == 15.0
assert basis.derivative(4, "y", y, z, x=x) == 10.0
assert basis.derivative(4, "z", y, z, x=x) == 6.0
```

The direct class example concerns the polynomial interface alone, rather than full structural analysis or verification of a solved boundary-value problem.

## 8. Geometry-dependent and polygon-specific extensions

The interface is general enough to motivate expansions of the form

$$
F_\tau^{(p)}(x,y,z;\mathcal G_{\mathrm{CSF}}),
$$

where $p$ labels a polygon or subdomain in the CSF cross-section. A geometry-adapted plugin could use polygon vertices, names, adjacency information, section changes along $x$, and local coordinate maps to construct functions on each domain.

This is **not an implemented feature of `XYZDemoBasis`**. The present example has four global polynomial functions, does not identify individual polygons, and does not impose inter-polygon continuity conditions. Geometry awareness is a design option permitted by the builder's CSF context; it requires additional logic in the specific plugin.

### 8.1 Continuity across adjacent domains

For two adjacent domains $\Omega_p$ and $\Omega_q$ sharing an interface $\Gamma_{pq}$, a construction intended to be $C^0$ must ensure matching function traces where appropriate:

$$
F_\tau^{(p)}\big|_{\Gamma_{pq}}
=F_\tau^{(q)}\big|_{\Gamma_{pq}}.
$$

For $C^1$, first spatial derivatives must also match in common physical coordinates; for $C^2$, all second partial derivatives, including the mixed derivatives, must match. Such higher-order continuity conditions are mathematical design choices, not universal requirements of linear elasticity.

The coefficients used in the displacement expansion must also be shared, transformed, or coupled consistently. Matching locally defined basis functions alone does not guarantee continuity of the *assembled displacement field* if the corresponding unknown coefficients are independent.

At interfaces between different elastic materials, physical admissibility normally requires continuity of displacement and appropriate traction equilibrium, rather than an unconditional requirement that the entire displacement gradient be continuous.

### 8.2 Derivatives needed for optional higher-order checks

A geometry-aware plugin can compute second and higher derivatives internally to verify its own construction. The current solver-facing interface expects function values and first derivatives; extending the plugin's private verification machinery does not imply that the solver calls a public second-derivative method.

An interface verification may be based on analytic identities, symbolic differentiation, interval bounds, or high-resolution numerical checks. Numerical samples are useful diagnostics but must not be described as an exact proof of global continuity unless an appropriate mathematical argument supports them.

### 8.3 The physical meaning of continuity

Continuity of basis functions is not the only relevant requirement. For a physically valid structural model, geometry regularity, boundary conditions, constitutive properties, displacement compatibility, and equilibrium must remain consistent. A plugin can validate properties of its own expansion; it cannot by itself certify the entire mechanical problem or the accuracy of its computed solution.

## 9. Recommended consistency and verification workflow

A rigorous plugin can expose a local verification procedure, separate from any regression against a FEM or analytical beam result. The following checks are relevant, with applicability depending on the expansion:

1. **Definition and domain:** confirm the declared number and indexing of functions; reject coordinates, geometry states, or options outside the supported domain.
2. **Analytic derivatives:** compare all first derivatives against symbolic expressions or independently computed numerical differences at interior sample points.
3. **Higher derivatives (if implemented):** check mixed-derivative agreement, Hessian symmetry under the regularity assumptions, and appropriate chain rules for geometry-adapted functions.
4. **Geometric consistency (if geometry-aware):** inspect valid polygon/domain associations, nondegenerate mappings, section evolution, and consistent physical coordinates.
5. **Inter-domain compatibility (if piecewise):** check the required interface traces and derivatives and verify consistent coefficient coupling.
6. **Linear independence:** check the mathematical rank of the function family on the intended domain and use appropriately scaled numerical tests to detect near-dependence.
7. **Numerical conditioning:** assess scaling, Gram matrices or representative assembled operators, and sensitivity to geometry, coordinate magnitude, and polynomial order.
8. **Quadrature adequacy:** verify that integration settings are appropriate for the actual functions, geometry, and constitutive variation rather than relying on a metadata estimate alone.
9. **Structural validation:** after local plugin checks, perform solver-level convergence and independent benchmark comparisons as distinct validation activities.

The XYZ demonstration is deliberately too small to establish broad approximation quality. Its strongest role is to illustrate how the spatial function and all first derivatives are supplied through one stable plugin interface.

### 9.1 Dimensional scaling

The four functions have different physical dimensions if coordinates are expressed in physical length units: $1$ is dimensionless, $y$ and $z$ have units of length, and $xyz$ has units of length cubed. Their associated CUF coefficients therefore carry different dimensions. This is mathematically permissible, but coordinate scaling or normalization would generally be desirable in a production basis to improve conditioning.

### 9.2 Local and global verification are different

A correct implementation of $F_\tau$ and $\nabla F_\tau$ establishes a necessary ingredient of the formulation, not automatically convergence, solution stability, or physically accurate stresses. The plugin can own its mathematical consistency checks while the solver and problem-specific comparisons remain responsible for their respective levels of validation.

## 10. What this example proves, and what it does not

**Demonstrated directly by the plugin source:**

- A CUF expansion may explicitly depend on $(x,y,z)$.
- One file can provide the function family and its first derivatives.
- The longitudinal derivative has a distinct interface method.
- Plugin registration and quadrature metadata are independent of the solver's CUF nuclei.
- A generic problem adapter must use physical coordinates when evaluating a spatially dependent expansion.

**Not demonstrated or guaranteed by this four-function example:**

- Polynomial completeness or high-order convergence.
- Use of CSF geometry or per-polygon basis construction.
- $C^0$, $C^1$, or $C^2$ compatibility of independent polygon-specific fields.
- Robustness for arbitrary section changes or material interfaces.
- Quadrature exactness for arbitrary geometric and constitutive laws.
- A full verified structural solution.

## 11. Implementation references

The following source paths describe the interface and loading mechanism used in this document:

- [`src/csf/cuf/core/basis.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/core/basis.py): base class `CUFBasis` and derivative interface.
- [`src/csf/cuf/core/basis_plugins.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/core/basis_plugins.py): `CUFBasisPlugin`, builder context, registration, quadrature metadata.
- [`src/csf/cuf/core/external_basis.py`](https://github.com/giovanniboscu/continuous-section-field/blob/main/src/csf/cuf/core/external_basis.py): trusted external-file plugin loading and case-YAML path resolution.
- [`src/csf/cuf/expansions/`](https://github.com/giovanniboscu/continuous-section-field/tree/main/src/csf/cuf/expansions): built-in expansion examples.
- `xyz_demo_expansion.py`: accompanying minimal external demonstration supplied with this reference.

The repository references describe the source structure consulted when preparing this document (9 October 2026). The companion example is provided as a separate file and reproduced below for completeness.

---

## Appendix A. Complete `xyz_demo_expansion.py` source

The listing below is reproduced from the accompanying example, without modifying the source file.

```python
"""Minimal CUF demonstration: F = (1, y, z, x*y*z).

This is a fixed four-term example, not a complete convergence basis.
"""

from csf.cuf.core.basis import CUFBasis
from csf.cuf.core.basis_plugins import CUFBasisPlugin, register_cuf_basis_plugin


class XYZDemoBasis(CUFBasis):
    @property
    def order(self) -> int:
        return 1

    @property
    def size(self) -> int:
        return 4

    @staticmethod
    def _check_tau(tau: int) -> None:
        if not isinstance(tau, int) or not 1 <= tau <= 4:
            raise IndexError("tau must be an integer in 1..4")

    @staticmethod
    def _require_x(x: float | None) -> float:
        if x is None:
            raise ValueError("xyz_demo requires the longitudinal coordinate x")
        return float(x)

    def value(
        self, tau: int, y: float, z: float, *, x: float | None = None
    ) -> float:
        self._check_tau(tau)
        if tau == 1:
            return 1.0
        if tau == 2:
            return float(y)
        if tau == 3:
            return float(z)
        return self._require_x(x) * float(y) * float(z)

    def derivative(
        self, tau: int, direction: str, y: float, z: float,
        *, x: float | None = None
    ) -> float:
        self._check_tau(tau)
        if direction == "y":
            if tau == 2:
                return 1.0
            return self._require_x(x) * float(z) if tau == 4 else 0.0
        if direction == "z":
            if tau == 3:
                return 1.0
            return self._require_x(x) * float(y) if tau == 4 else 0.0
        raise ValueError("direction must be 'y' or 'z'")

    def longitudinal_derivative(
        self, tau: int, y: float, z: float, *, x: float | None = None
    ) -> float:
        self._check_tau(tau)
        return float(y) * float(z) if tau == 4 else 0.0


def _build(*, order, section_provider, continuous_section_field, options):
    # The example has one fixed four-term bilinear transverse level.
    if not isinstance(order, int) or order != 1:
        raise ValueError("xyz_demo accepts only order: 1")
    if options:
        raise ValueError("xyz_demo does not accept basis_options")
    return XYZDemoBasis()


register_cuf_basis_plugin(
    CUFBasisPlugin(
        name="xyz_demo",
        builder=_build,
        section_gauss_minimum=lambda basis: 3,
        # Conservative for affine section variation plus explicit x*y*z.
        longitudinal_transverse_degree=lambda basis: 6,
    )
)

```
