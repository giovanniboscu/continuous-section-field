# CUF displacement expansion for CSF coupling

## Scope

This note defines the CUF displacement approximation used in the coupling with the Continuous Section Field (CSF).

At each longitudinal coordinate \(x\), CSF supplies the physical sectional state,

```math
\mathcal{S}(x)
\longrightarrow
\left(
\Omega^k(x),
\mathbf{C}^k(x,y,z)
\right),
```

where \(\Omega^k(x)\) denotes a physical sectional domain and \(\mathbf{C}^k(x,y,z)\) its constitutive description.

The purpose of this note is limited to the **kinematic approximation of the three-dimensional displacement field** over the section supplied by CSF.

Longitudinal finite-element discretization, numerical integration, loads, boundary conditions, and solution procedures are separate parts of the formulation.

---

## 1. Coordinates and displacement field

Let

* \(x\) be the longitudinal coordinate along the beam axis;
* \(y,z\) be the physical coordinates in the transverse plane.

At each \(x\), the current cross-section is the domain

```math
\Omega(x).
```

The three-dimensional displacement field is

```math
\mathbf{u}(x,y,z)
=
\begin{bmatrix}
u_x(x,y,z)\\
u_y(x,y,z)\\
u_z(x,y,z)
\end{bmatrix},
\qquad
(y,z)\in\Omega(x).
```

---

## 2. CUF transverse expansion

CUF approximates the dependence of the displacement field on the transverse coordinates through a selected family of functions \(F_\tau(y,z)\):

```math
\mathbf{u}(x,y,z)
=
\sum_{\tau=1}^{M}
F_\tau(y,z)\,
\mathbf{u}_\tau(x),
\qquad
(y,z)\in\Omega(x).
```

Here,

* \(M\) is the number of retained transverse approximation terms;
* \(F_\tau(y,z)\) is the transverse CUF basis function associated with index \(\tau\);
* \(\mathbf{u}_\tau(x)\) is the corresponding vector of longitudinal amplitudes,

```math
\mathbf{u}_\tau(x)
=
\begin{bmatrix}
u_{x\tau}(x)\\
u_{y\tau}(x)\\
u_{z\tau}(x)
\end{bmatrix}.
```

The functions \(F_\tau\) determine the admissible variation of the displacement field over the cross-section, while the functions \(\mathbf{u}_\tau(x)\) describe how the corresponding amplitudes vary along the beam.

Thus the CUF approximation separates transverse and longitudinal dependence:

```math
F_\tau(y,z)
\quad\text{and}\quad
\mathbf{u}_\tau(x).
```

The choice of transverse basis and approximation order belongs to CUF and is independent of the CSF description.

---

## 3. Variable cross-section

The CUF displacement expansion does not require the section to remain constant along \(x\).

For a prismatic beam,

```math
\Omega(x)=\Omega.
```

For a non-prismatic beam represented by CSF,

```math
x
\longmapsto
\mathcal{S}(x)
\longmapsto
\Omega(x).
```

The same CUF kinematic form is retained:

```math
\mathbf{u}(x,y,z)
=
\sum_{\tau=1}^{M}
F_\tau(y,z)\,
\mathbf{u}_\tau(x),
\qquad
(y,z)\in\Omega(x).
```

The longitudinal variation of the physical section therefore enters through the domain over which the approximation is evaluated.

It does not require geometry-specific transverse functions of the form \(F_\tau(x,y,z)\).

In the present CSF-CUF coupling,

```math
F_\tau = F_\tau(y,z),
```

while geometry and material variation are supplied independently by

```math
\mathcal{S}(x).
```

This distinction is central to the coupling: **CSF describes the evolving physical section; CUF describes the displacement approximation evaluated on that section.**

---

## 4. Longitudinal amplitudes

The quantities

```math
\mathbf{u}_\tau(x)
```

remain functions of the longitudinal coordinate.

Their numerical approximation is a separate modelling choice.

For example, if a longitudinal finite-element approximation is subsequently introduced, one may write

```math
\mathbf{u}_\tau(x)
\simeq
\sum_i
N_i(x)\,
\mathbf{q}_{\tau i},
```

where \(N_i(x)\) belongs to the selected longitudinal basis.

The resulting displacement approximation becomes

```math
\mathbf{u}(x,y,z)
\simeq
\sum_{\tau=1}^{M}
\sum_i
F_\tau(y,z)
N_i(x)
\mathbf{q}_{\tau i}.
```

The transverse basis \(F_\tau(y,z)\) and the longitudinal basis \(N_i(x)\) are therefore distinct approximation choices.

This note concerns primarily the transverse CUF expansion. The definition of the longitudinal basis and of the finite-element topology belongs to the longitudinal discretization.

---

## 5. Source and test indices

In the variational formulation it is useful to distinguish the approximation index associated with the displacement field from that associated with the virtual displacement field.

Let \(s\) denote the source index:

```math
\mathbf{u}^{(s)}(x,y,z)
=
F_s(y,z)\,
\mathbf{u}_s(x).
```

Let \(\tau\) denote the test index:

```math
\delta\mathbf{u}^{(\tau)}(x,y,z)
=
F_\tau(y,z)\,
\delta\mathbf{u}_\tau(x).
```

The complete fields are therefore

```math
\mathbf{u}(x,y,z)
=
\sum_{s=1}^{M}
F_s(y,z)\,
\mathbf{u}_s(x),
```

and

```math
\delta\mathbf{u}(x,y,z)
=
\sum_{\tau=1}^{M}
F_\tau(y,z)\,
\delta\mathbf{u}_\tau(x).
```

This distinction is used later in the construction of the CUF fundamental nucleus.

---

## 6. Transverse derivatives

The strain field requires derivatives of the transverse basis functions.

For each \(F_\tau(y,z)\),

```math
F_{\tau,y}
=
\frac{\partial F_\tau}{\partial y},
\qquad
F_{\tau,z}
=
\frac{\partial F_\tau}{\partial z}.
```

For compact notation, a derivative label

```math
\phi\in\{\emptyset,y,z\}
```

may be introduced, with

```math
F_{\tau,\emptyset}=F_\tau.
```

The same notation applies to the source functions \(F_s\).

The basis functions and their transverse derivatives belong to the CUF approximation; they are not supplied by CSF.

---

## 7. CSF-CUF interface

The two descriptions remain distinct.

### CSF supplies the physical sectional state

```math
\mathcal{S}(x)
\longrightarrow
\left(
\Omega^k(x),
\mathbf{C}^k(x,y,z)
\right).
```

### CUF supplies the kinematic approximation

```math
F_\tau(y,z),
\qquad
F_{\tau,y}(y,z),
\qquad
F_{\tau,z}(y,z),
\qquad
\mathbf{u}_\tau(x).
```

The displacement field is therefore a CUF kinematic construction evaluated on the physical section supplied by CSF.

Schematically,

```math
\mathcal{S}(x)
\longrightarrow
\Omega(x),
```

while

```math
\left(
F_\tau(y,z),
\mathbf{u}_\tau(x)
\right)
\longrightarrow
\mathbf{u}(x,y,z).
```

Together,

```math
\mathcal{S}(x)
+
\left(
F_\tau,
\mathbf{u}_\tau
\right)
\longrightarrow
\mathbf{u}(x,y,z)
\quad\text{on}\quad
\Omega(x).
```

CSF does not determine the CUF basis functions, and CUF does not replace the CSF sectional description.

The subsequent construction of strains, sectional integrals, generalized coefficients, and the CUF fundamental nucleus follows from this kinematic statement.

---

### References

* E. Carrera, G. Giunta, **“Refined Beam Theories Based on a Unified Formulation”**, *International Journal of Applied Mechanics*, 2(1) (2010), 117–143. [DOI](https://doi.org/10.1142/S1758825110000500).

* G. Giunta, S. Belouettar, E. Carrera, **“Analysis of FGM Beams by Means of Classical and Advanced Theories”**, *Mechanics of Advanced Materials and Structures*, 17 (2010), 622–635.

* S. O. Ojo, P. M. Weaver, **“Efficient strong Unified Formulation for stress analysis of non-prismatic beam structures”**, 2021.
