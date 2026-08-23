# Longitudinal Quadrature for the CSF-CUF Variable-Section Extension

## 1. Scope

In the classical prismatic CUF formulation, the cross-sectional domain is
independent of the longitudinal coordinate. In the CSF-CUF extension, the
cross-sectional domain and the constitutive properties may vary continuously
along the beam axis.

This additional longitudinal dependence must be taken into account when
determining the Gauss-Legendre quadrature order.

## 2. Variable CSF domain

The sectional coefficients entering the CUF fundamental nucleus have the form

$$J_{\tau s}^{mn}(x) = \sum_k \int_{\Omega_{\mathrm{CSF},k}(x)} C_k^{mn}(x,y,z) \, D_\phi F_\tau(y,z) \, D_\xi F_s(y,z) \, d\Omega$$

Therefore, the longitudinal dependence of $J_{\tau s}^{mn}(x)$ is not
determined only by the CUF expansion functions and the longitudinal finite
element interpolation.

The varying CSF domain $\Omega_{\mathrm{CSF}}(x)$ also contributes to the
polynomial degree.

For polygonal sections whose vertex coordinates vary affinely along $x$,
the domain variation can introduce a polynomial contribution up to degree two:

$$p_{\Omega} = 2$$

This contribution must therefore be included explicitly in the estimate of
the longitudinal polynomial degree.

## 3. Material variation

The constitutive field may also vary along the beam axis:

$$C_{\mathrm{CSF}} = C_{\mathrm{CSF}}(x,y,z)$$

If its longitudinal variation is polynomial of degree $p_C$, and the
constitutive term enters multiplicatively in the sectional coefficient, then
$p_C$ must also contribute to the longitudinal degree estimate.

For the current linear material-variation cases:

$$p_C = 1$$

For a user-defined constitutive law, $p_C$ cannot in general be inferred by
CUF and must be supplied by the material provider or by the user defining the
law.

## 4. Polynomial-degree propagation

For multiplicative polynomial factors, polynomial degrees are additive.
Accordingly, a conservative longitudinal degree estimate can be written as

$$p_{\mathrm{long}} = p_{\mathrm{CUF}} + p_{\Omega} + p_C + p_{\mathrm{FE}}$$

where the individual terms must be evaluated according to the actual
algebraic operations appearing in the integrand.

The geometric contribution of the CSF polygonal domain is $p_{\Omega} = 2$
for affine vertex variation.

## 5. Gauss-Legendre requirement

An $n$-point Gauss-Legendre rule integrates exactly a polynomial of degree
up to $2n-1$.

Therefore the minimum longitudinal quadrature order is

$$n_G = \left\lceil \frac{p_{\mathrm{long}}+1}{2} \right\rceil$$

The CSF geometric and material contributions must be included in
$p_{\mathrm{long}}$ before this relation is applied.

## 6. Constant-section limit

A constant cross-section is a degenerate case of the general CSF description.
Its actual geometric longitudinal degree is zero.

The CSF-CUF implementation may nevertheless retain the general upper bound
$p_{\Omega} = 2$ in the automatic quadrature estimate. This produces harmless
over-integration for prismatic cases while avoiding any need for CUF to
classify the section as constant or variable.
