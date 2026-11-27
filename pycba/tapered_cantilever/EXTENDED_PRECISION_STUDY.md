# Independent Euler–Bernoulli precision study

A step-by-step explanation of `extended_precision_study.py`.

[Back to theory](THEORY.md) · [Numerical validation](VALIDATION.md)

## 1. Purpose

The experiment investigates why the tip-displacement error can increase when a continuous-stiffness beam is subdivided into more elements. It uses neither CSF nor PyCBA. Instead, it constructs a small, independent Euler–Bernoulli beam solver using an analytical rigidity function and an element flexibility formulation.

The physical problem and structural discretisation remain unchanged when the arithmetic precision is increased. The experiment compares standard double precision with 32 and 50 decimal digits. It is a diagnostic of numerical sensitivity, not a direct investigation of PyCBA's internal implementation.

## 2. Run the experiment

```bash
python3 -m pip install numpy scipy mpmath
python3 extended_precision_study.py
```

The script prints 21 records (seven element counts and three precision settings) and writes `extended_precision_study.csv` alongside the script. The CSV contains `n_elements`, `precision`, `tip_mm` and `relative_error`.

## 3. Physical model

The experiment uses Case B of the tapered cantilever benchmark: constant material and width, with linearly decreasing depth. The beam is clamped at its left end and carries a downward point force at its right end. Shear deformation and self-weight are omitted.

| Symbol | Python | Meaning | Value |
|---|---|---|---:|
| $L$ | `L` | Beam length | 5000 mm |
| $P$ | `P` | Tip force magnitude | 10000 N |
| $E$ | `E` | Young's modulus | 210000 MPa |
| $B$ | `B` | Width | 200 mm |
| $H$ | `H` | Root depth | 500 mm |
| $n$ | `n` | Number of elements | 1–64 |
| $h$ | `h` | Element length | $L/n$ |

```python
L, P, E, B, H = map(mp.mpf, (5000,10000,210000,200,500))
h = L/n
def EI(x): return E*B*(H*(1-x/(2*L)))**3/12
```

Here `mp.mpf` constructs arbitrary-precision real numbers. The depth at global coordinate $x$ is

$$H(x)=H\left(1-\frac{x}{2L}\right).$$

The rectangular-section second moment of area and flexural rigidity are

$$I(x)=\frac{BH(x)^3}{12},\qquad EI(x)=\frac{EBH^3}{12}\left(1-\frac{x}{2L}\right)^3.$$

The rigidity is cubic, although the depth is linear. At the tip it is one eighth of its root value. The script evaluates this expression directly: no sectional-property library or polynomial fitting is required.

## 4. Independent analytical reference

By virtual work, the positive downward tip displacement is

$$\delta_{\mathrm{ref}}=P\int_0^L\frac{(L-x)^2}{EI(x)}\,dx.$$

Let $s=x/L$ and $K_0=EI(0)$. Substitution gives

$$\delta_{\mathrm{ref}}=\frac{PL^3}{K_0}\int_0^1\frac{(1-s)^2}{(1-s/2)^3}\,ds.$$

With $u=1-s/2$, the integral becomes

$$2\int_{1/2}^{1}(4/u-4/u^2+1/u^3)\,du=8\ln 2-5.$$

Therefore

$$\delta_{\mathrm{ref}}=\frac{PL^3}{K_0}(8\ln 2-5).$$

The reference displacement is approximately 1.55764984137017850096530563332975012744 mm. It does not depend on the number of elements. The script initially calculates `ref` inside the precision context, but this first value is redundant: the final error calculation uses a fresh 90-decimal-digit reference.

## 5. Degrees of freedom and global matrix

Each node has two degrees of freedom: transverse displacement $v$ and rotation $\theta=dv/dx$. With $n$ elements there are $n+1$ nodes and $2n+2$ degrees of freedom.

```python
K = mp.matrix(2*n+2)             # extended precision
K = np.zeros((2*n+2,2*n+2))      # float64 alternative
```

Both statements create a zero-filled square global stiffness matrix (in their respective branches). For 64 elements its size is 130 by 130. After imposing the clamp, 128 free degrees of freedom remain.

## 6. Local coordinate and moment representation

For element index `i` (starting at zero), introduce the local coordinate $t\in[0,1]$:

$$x=(i+t)h,\qquad dx=h\,dt.$$

There is no distributed load within an element. Moment equilibrium therefore permits a linear moment field:

$$M(t)=m_0+m_1t=\mathbf b(t)^T\mathbf m,$$

where $\mathbf b=[1,t]^T$ and $\mathbf m=[m_0,m_1]^T$. Both coefficients have units of N·mm because $t$ is dimensionless. The curvature convention used here is $v''=M/EI$.

## 7. Derive the transformation matrix A

The element nodal displacement vector is

$$\mathbf d_e=[v_1,\theta_1,v_2,\theta_2]^T.$$

Define the two generalised deformations by integrating curvature against the moment basis:

$$q_0=\int_0^1 h\,v''(x)\,dt=\theta_2-\theta_1,$$

$$q_1=\int_0^1 ht\,v''(x)\,dt=\theta_2-\frac{v_2-v_1}{h}.$$

The second identity follows by integration by parts, using $dt=dx/h$ and $dt/dx=1/h$ within the element. Thus

$$\mathbf q=\mathbf A\mathbf d_e,\qquad \mathbf A=\begin{bmatrix}0&-1&0&1\\1/h&0&-1/h&1\end{bmatrix}.$$

```python
A = mp.matrix([[0,-1,0,1],[1/h,0,-1/h,1]])
```

The NumPy branch constructs the same matrix using `float(h)`. Both generalised deformations vanish for rigid translation or rigid rotation. This explains the two independent deformation modes of the four-degree-of-freedom bending element.

## 8. Construct the element flexibility matrix

Using the curvature relation and the moment representation,

$$q_j=\int_0^1 \frac{h\,b_j(t)}{EI((i+t)h)}\sum_{k=0}^1 b_k(t)m_k\,dt.$$

Consequently $\mathbf q=\mathbf F_e\mathbf m$, with

$$F_{jk}=\int_0^1\frac{h\,t^{j+k}}{EI((i+t)h)}\,dt,\qquad j,k\in\{0,1\}.$$

Expanding the four entries gives

$$\mathbf F_e=\begin{bmatrix}\int_0^1 h/EI(x)\,dt&\int_0^1 ht/EI(x)\,dt\\\int_0^1 ht/EI(x)\,dt&\int_0^1 ht^2/EI(x)\,dt\end{bmatrix}.$$

The extended-precision branch implements exactly these integrals:

```python
F = mp.matrix([
    [mp.quad(lambda t: h*t**(j+k)/EI((i+t)*h), [0,1])
     for k in range(2)]
    for j in range(2)
])
```

The nested comprehensions enumerate the row and column indices. `mp.quad` integrates each scalar function over the local interval. The factor `h` is the coordinate transformation Jacobian. The float64 branch uses `scipy.integrate.quad` and a separate float-valued rigidity function, with `epsabs=1e-30` and `epsrel=1e-12`. The `[0]` selects the integral value rather than its estimated quadrature error.

The rigidity is evaluated throughout each element, not replaced by its midpoint value. The matrix is symmetric and positive definite because the rigidity is positive and the two basis functions are linearly independent.

## 9. Convert flexibility into stiffness

From $\mathbf q=\mathbf F_e\mathbf m$ and $\mathbf q=\mathbf A\mathbf d_e$,

$$\mathbf m=\mathbf F_e^{-1}\mathbf A\mathbf d_e.$$

By work conjugacy, $\mathbf m^T\delta\mathbf q=\mathbf f_e^T\delta\mathbf d_e$, hence $\mathbf f_e=\mathbf A^T\mathbf m$. Substitution gives

$$\mathbf f_e=\mathbf K_e\mathbf d_e,\qquad \mathbf K_e=\mathbf A^T\mathbf F_e^{-1}\mathbf A.$$

```python
Ke = A.T*(F**-1)*A                 # mpmath
Ke = A.T @ np.linalg.solve(F,A)    # equivalent NumPy expression
```

| Matrix | Dimensions |
|---|---|
| $\mathbf A$ | 2 × 4 |
| $\mathbf F_e$ | 2 × 2 |
| $\mathbf A^T$ | 4 × 2 |
| $\mathbf K_e$ | 4 × 4 |

In NumPy, `solve(F,A)` solves $\mathbf F_e\mathbf X=\mathbf A$ without explicitly constructing the inverse. In mpmath, `F**-1` constructs the inverse. The element stiffness is positive semidefinite, with two rigid-body modes.

## 10. Assemble the global stiffness matrix

Element `i` connects nodes `i` and `i+1`. Its global degree-of-freedom indices are `2*i`, `2*i+1`, `2*i+2`, `2*i+3`.

```python
for j in range(4):
    for k in range(4):
        K[2*i+j,2*i+k] += Ke[j,k]
```

The NumPy branch performs the same operation using a matrix slice:

```python
K[2*i:2*i+4,2*i:2*i+4] += A.T@np.linalg.solve(F,A)
```

For three elements the index sets are `[0,1,2,3]`, `[2,3,4,5]` and `[4,5,6,7]`. Shared nodal contributions are added, not overwritten. The `+=` operator is the assembly operation.

## 11. Apply the clamp and tip force

The first node is clamped, so $v_0=\theta_0=0$. The reduced stiffness matrix is `K[2:,2:]`: the first two rows and columns are removed. Since the prescribed displacements are zero, no additional correction to the reduced load vector is required.

```python
f = mp.matrix(2*n,1)
f[2*n-2] = -P
```

The negative sign denotes a downward force. The penultimate free degree of freedom is the final transverse displacement; the last is the final rotation. For two elements the reduced load vector is $[0,0,-P,0]^T$.

## 12. Solve the structural equations

$$\mathbf K_r\mathbf u_r=\mathbf f_r.$$

```python
tip = -mp.lu_solve(K[2:,2:],f)[2*n-2]
```

The NumPy alternative is:

```python
tip = mp.mpf(float(-np.linalg.solve(K[2:,2:],f)[-2]))
```

Both extract the final vertical displacement and reverse its sign to report a positive downward magnitude. Conversion of the float64 result to `mp.mpf` permits high-precision comparison but cannot recover digits lost during the float64 solution.

## 13. Control arithmetic precision and measure error

```python
with mp.workdps(digits or 80):
```

For `digits=32` or `50`, mpmath performs the structural operations at the requested decimal precision. For `digits=0`, the structural calculations use NumPy and SciPy float64; the surrounding mpmath context does not increase their precision.

The final reference is recomputed at 90 decimal digits:

```python
with mp.workdps(90):
    ref = mp.mpf(10000)*5000**3/(mp.mpf(210000)*200*500**3/12)*(8*mp.log(2)-5)
    err = abs(tip-ref)/ref
    return mp.nstr(tip, digits or 17), mp.nstr(err,12)
```

The relative error is dimensionless:

$$\varepsilon=\frac{|\delta_{\mathrm{num}}-\delta_{\mathrm{ref}}|}{\delta_{\mathrm{ref}}}.$$

The reference is positive and nonzero. `mp.nstr` formats the result as a string; it does not change the precision of the preceding calculation. The returned displacement uses 17 significant digits for float64 or the requested number for mpmath, while the error is formatted with 12 significant digits.

## 14. Execution loop and recorded results

The main block iterates over element counts `(1,2,4,8,16,32,64)` and precision settings `(0,32,50)`. Each result is printed and appended to a list. `csv.DictWriter` writes the header and records to a file whose name is obtained by replacing the script's `.py` suffix with `.csv`.

The following relative errors are from the supplied local execution, rounded for readability.

| Elements | Float64 | 32 decimal digits | 50 decimal digits |
|---:|---:|---:|---:|
| 1 | 1.447e-17 | 2.017e-33 | 1.362e-51 |
| 2 | 1.126e-15 | 3.006e-33 | 1.489e-49 |
| 4 | 1.427e-14 | 1.648e-27 | 5.183e-50 |
| 8 | 4.306e-14 | 9.680e-28 | 5.031e-49 |
| 16 | 3.781e-13 | 3.173e-29 | 6.180e-48 |
| 32 | 2.306e-13 | 1.806e-29 | 9.970e-47 |
| 64 | 2.387e-11 | 1.505e-28 | 7.985e-46 |

At 64 elements, the error at 50 decimal digits is approximately $3\times10^{34}$ times smaller than the float64 error. The error does not grow monotonically at every refinement step.

## 15. Numerical evidence and interpretation

For this load case, the exact bending moment is linear within every element. The flexibility formulation captures that moment field and integrates the actual varying rigidity. With exact arithmetic and exact integration, the nodal solution is therefore exact for any of the tested subdivisions. This is not the usual displacement-interpolation error of a conventional polynomial displacement element.

As the mesh is refined, the assembled stiffness system can become increasingly ill-conditioned, amplifying perturbations from numerical integration, assembly and the linear solve. The strong reduction in error with increased precision supports a finite-precision explanation rather than an inherent limitation of continuous rigidity representation.

However, this particular script does not calculate a condition number. Moreover, its float64 and extended-precision branches use different quadrature and linear-algebra implementations. It does not isolate their individual contributions, nor establish the precise cause of the behaviour inside PyCBA. A separate conditioning study, preferably using consistently scaled degrees of freedom, can provide complementary evidence.

## 16. Computational workflow

```text
Analytical EI(x)
       |
       v
Element flexibility F (numerical integration)
       |
       v
Element stiffness Ke = A^T F^-1 A
       |
       v
Global stiffness assembly
       |
       v
Clamp and tip force
       |
       v
Reduced linear system -> tip displacement
       |
       v
90-digit analytical reference -> relative error -> CSV
```

The script is short because it implements only the mechanics needed for this specific benchmark: a two-node bending element, a straight cantilever, positive continuous rigidity and a nodal tip load. It is not a general-purpose beam analysis library.

The numerical table records the supplied execution; this explanatory document does not claim a new solver run. Exact last-digit results may depend on the numerical library versions and computing environment.
