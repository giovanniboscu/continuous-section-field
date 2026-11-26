# Theory and independent reference solutions

[Back to tutorial](README.md)

## 1. Coordinates and assumptions

Let x be the longitudinal coordinate measured from the clamp (CSF z), and y the transverse depth coordinate. The rectangular section is symmetric about its centroid. The elastic modulus is positive and uniform in each section but may vary along x. Euler–Bernoulli kinematics, small displacements and linear elasticity are assumed. All quantities use a consistent N–mm system.

Define $t=x/L$, $I_0=bh_0^3/12$, $K_0=E_0I_0$, with $L=5000$ mm, $P=10000$ N, $b=200$ mm, $h_0=500$ mm and $E_0=210000$ MPa. Then $I_0=2.083333333333333\times10^9$ mm⁴ and $K_0=4.375\times10^{14}$ N mm².

## 2. From physical fields to rigidity

For tip values $h_1,E_1$:

$$h(t)=h_0+(h_1-h_0)t,\qquad E(t)=E_0+(E_1-E_0)t.$$

Integration over the rectangular section gives

$$A=\int_A dA=bh,\qquad I_x=\int_A y^2dA=b\int_{-h/2}^{h/2} y^2dy=\frac{bh^3}{12}.$$

The flexural rigidity is

$$K(t)=EI(t)=\int_A E(t)y^2dA=E(t)I_x(t).$$

For the four cases, let $q=1-t/2$:

| Case | h/h₀ | E/E₀ | I/I₀ | K/K₀ |
|---|---|---|---|---|
| A | 1 | 1 | 1 | 1 |
| B | q | 1 | q³ | q³ |
| C | 1 | q | 1 | q |
| D | q | q | q³ | q⁴ |

![Normalized rigidity](img/rigidity.png)

### CSF material weights

The YAML stores a dimensionless polygon weight $w=E/E_0$. In case D the root weight is 1 and the tip weight is 0.5, with the law `solid,solid: w0 + (w1-w0)*(z/L)`. The end polygons have vertices at ±100 mm in transverse x and ±250 or ±125 mm in transverse y.

The library returns a weighted inertia $I_x^w=w I_x$ in this benchmark. Hence $K=E_0 I_x^w$. Recovering unweighted area and inertia by division by w is valid here only because the section contains one uniformly weighted polygon. General heterogeneous sections require the appropriate elastic centroid and weighted integration; the present bridge is not a general composite adapter.

## 3. Independent displacement by virtual work

The actual moment magnitude is $M(x)=P(L-x)$, and the moment per unit virtual downward tip force is $m(x)=L-x$. The displacement in the downward direction is

$$\delta=\int_0^L\frac{M(x)m(x)}{K(x)}dx=P\int_0^L\frac{(L-x)^2}{K(x)}dx.$$

Substituting $x=Lt$, $dx=Ldt$, and $K=K_0q^p$ gives

$$\delta=\frac{PL^3}{K_0}J_p,\qquad J_p=\int_0^1\frac{(1-t)^2}{(1-t/2)^p}dt.$$

For case A, $p=0$; for B, C and D, $p=3,1,4$ respectively. Using $u=1-t/2$ gives $1-t=2u-1$, $dt=-2du$ and

$$J_p=2\int_{1/2}^1(4u^2-4u+1)u^{-p}du.$$

Termwise integration yields:

| Case | Integral | Exact dimensionless value |
|---|---|---|
| A | $J_0$ | $1/3$ |
| B | $J_3$ | $8\ln 2-5$ |
| C | $J_1$ | $2\ln 2-1$ |
| D | $J_4$ | $2/3$ |

For example, for D the antiderivative is $2[-4/u+2/u^2-1/(3u^3)]$, evaluated between 1/2 and 1. The combined displacement is exactly twice the prismatic displacement under these assumptions.

`reference_solution.py` computes all four using independent SciPy adaptive integration, with `epsabs=1e-25` and `epsrel=1e-12` for the scaled integrand containing 1/K. The revised `closed_form()` provides exact expressions for all four cases, and `main.py` checks them against the independent numerical integral.

## 4. Midpoint versus continuous representation

For N equal elements of length $\ell=L/N$, the midpoint approximation is

$$K_i=K((i+1/2)\ell),\qquad i=0,\ldots,N-1.$$

The corresponding stiffness is constant on each element, so the taper enters only through a sequence of scalar values. For the smooth positive rigidity laws and this tip-load problem the observed global displacement error decreases as $O(N^{-2})$. This is a property of the approximation in this benchmark, not a general claim about all FEM errors.

In the continuous approach PyCBA uses a variable rigidity inside each element, with flexibility contributions of the form

$$F_{ij}=\int_0^\ell\frac{m_i(s)m_j(s)}{K(s)}ds,$$

where $m_i$ are member equilibrium moment influence functions and s is the local member coordinate. In the refined model, the callable uses $x=i\ell+s$ to query the global CSF field. No additional physical CSF sections are needed for refinement.

### Important implementation detail: `degree`

The published PyCBA 1.0.2 [SectionEI source](https://ccaprani.github.io/pycba/_modules/pycba/section.html) shows that the callable branch samples the function at `degree + 2` evenly spaced positions, fits a polynomial using `numpy.polyfit`, then stores the coefficients and degree. This degree also informs the integration scheme. Although the API accepts a callable, the actual rigidity used later is the fitted polynomial. The docstring describes an integration-order role but the source reveals the fitting step as well.

Consequently degree 2 under-represents cubic and quartic rigidity laws, while degree 4 can represent both. The observed error plateau near floating-point precision is consistent with this mechanism and sufficiently accurate flexibility integration. Integration of 1/K is not polynomial in general; degree 4 alone does not mathematically guarantee exact integration. The precise installed source should be confirmed before publication:

```bash
python3 -c "import inspect; from pycba import SectionEI; print(inspect.getsource(SectionEI.add_segment))"
```

The output is named `degree_sensitivity.csv` (formerly `quadrature.csv`), since fitting and integration effects are not isolated.

## 5. Further reading

- [CSF repository](https://github.com/giovanniboscu/continuous-section-field)
- [PyCBA beam definition](https://ccaprani.github.io/pycba/general.html)
- [PyCBA non-prismatic stiffness](https://ccaprani.github.io/pycba/gen/pycba.beam.Beam.html#pycba.beam.Beam.k_nonprismatic)
