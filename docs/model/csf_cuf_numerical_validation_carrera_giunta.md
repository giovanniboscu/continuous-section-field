## 1. Scope

This document applies the completed CSF-CUF formulation to the reference problem presented by Carrera and Giunta in *Refined Beam Theories Based on a Unified Formulation*. The objective is not to introduce a new formulation, but to specialize the general model developed previously to the same kinematic assumptions, sectional description, constitutive data, loading conditions, boundary conditions, and longitudinal solution strategy adopted in the reference work. The resulting CUF system is then compared with the corresponding reference equations and numerical results in order to verify that the generalized formulation recovers the established CUF model when reduced to the same assumptions.

## 2. Reference problem adopted for validation

The first validation case is the rectangular beam under bending considered by Carrera and Giunta.

The purpose of this section is only to define the reference problem to which the completed CSF-CUF formulation will be specialized. No sectional coefficient, fundamental nucleus, or algebraic system is evaluated yet.

The beam is prismatic and its cross-section is constant along the longitudinal coordinate. A rectangular cross-section is considered.

The material is the aluminium alloy adopted in the reference work, with

$$
E=71700\ \mathrm{MPa}
$$

and

$$
\nu=0.30.
$$

The beam is simply supported and subjected to the bending loading considered in the rectangular-section validation problem of the reference paper.

The longitudinal dependence is treated using the same Navier-type solution strategy adopted by Carrera and Giunta. For the first validation case, the half-wave number is

$$
m=1.
$$

Accordingly, the longitudinal wave parameter is

$$
\alpha=\frac{\pi}{l}.
$$

The CUF approximation across the cross-section is constructed using the Maclaurin polynomial expansion adopted in the reference formulation. The approximation order $N$ remains a model parameter at this stage and will be fixed when the corresponding CUF system is explicitly assembled.

The present benchmark therefore introduces no modification of the generalized CSF-CUF formulation. It selects a particular constant sectional state, material law, loading case, boundary conditions, transverse CUF approximation family, and longitudinal solution strategy so that the resulting specialized model can be compared directly with the reference solution.

The next step is to express this reference problem in the notation of the generalized CSF-CUF formulation.


## 3. Reference coordinates and exact benchmark specialization

Before evaluating any sectional coefficient, the coordinate systems of the generalized CSF-CUF formulation and of the Carrera-Giunta reference problem must be placed in one-to-one correspondence.

In the reference paper, the beam axis is the coordinate $z$, while $x$ and $y$ are the two transverse coordinates on the cross-section.

In the generalized CSF-CUF formulation used here, the beam axis is denoted by $x$, while $y$ and $z$ are the transverse coordinates.

The coordinate correspondence adopted throughout this validation document is therefore

$$
x_{\mathrm{CSF}}=z_{\mathrm{ref}}
$$

$$
y_{\mathrm{CSF}}=x_{\mathrm{ref}}
$$

$$
z_{\mathrm{CSF}}=y_{\mathrm{ref}}.
$$

This is only a relabelling of coordinates. It does not modify the mechanics or the CUF approximation.

For the first validation, select the first rectangular bending benchmark reported in the reference numerical results:

$$
\frac{l}{a}=100
$$

and

$$
\frac{a}{b}=100.
$$

The rectangular cross-section is represented by a single transverse domain,

$$
N_\Omega=1,
$$

with constant geometry along the beam axis.

In the generalized notation,

$$
\Omega^1(x)=\Omega^1
$$

for every longitudinal coordinate $x$.

Using the coordinate correspondence above, the rectangular domain is

$$
-\frac{a}{2}\le y\le\frac{a}{2}
$$

and

$$
-\frac{b}{2}\le z\le\frac{b}{2}.
$$

The material is homogeneous and isotropic, so the constitutive field is also constant along the beam and over the cross-section:

$$
\mathbf{C}^1(x,y,z)=\mathbf{C}_{\mathrm{Al}}.
$$

The material parameters are

$$
E=71700\ \mathrm{MPa}
$$

and

$$
\nu=0.30.
$$

Because the reference stresses are reported in nondimensional form with respect to the loading amplitude, the absolute value of the bending-load amplitude is not required for comparison with the tabulated nondimensional stresses. The validation may therefore retain the reference amplitude symbol until the load vector is assembled.

The target of the first validation is the rectangular bending case corresponding to Table 2 of the reference work, namely the slender-beam case with $l/a=100$.


## 4. Specialization of the CSF sectional state to the reference beam

The generalized CSF-CUF formulation assumes that, at every longitudinal coordinate, the sectional provider returns the current transverse domain and constitutive field.

For the present validation case, the Carrera-Giunta reference beam is prismatic: the cross-section is constant along the beam axis. In the reference paper this is stated explicitly before the CUF kinematic expansion is introduced.

With the coordinate correspondence defined in Section 3, the CSF sectional state therefore becomes independent of the longitudinal coordinate.

For the single rectangular transverse domain,

$$
N_\Omega=1
$$

and

$$
\Omega^1(x)=\Omega^1.
$$

The domain is

$$
\Omega^1=\{(y,z):-a/2\le y\le a/2,\;-b/2\le z\le b/2\}.
$$

The aluminium material adopted in the reference numerical example is homogeneous and isotropic. Consequently, the constitutive field is also independent of the longitudinal and transverse coordinates:

$$
\mathbf{C}^1(x,y,z)=\mathbf{C}_{\mathrm{Al}}.
$$

The material parameters are

$$
E=71700\ \mathrm{MPa}
$$

and

$$
\nu=0.30.
$$

Therefore the generalized sectional provider reduces, for this benchmark, to the constant response

$$
\mathcal{S}_{\mathrm{ref}}\longrightarrow\{\Omega^1,\mathbf{C}_{\mathrm{Al}}\}.
$$

Equivalently,

$$
\mathcal{S}(x)=\mathcal{S}_{\mathrm{ref}}
$$

for every longitudinal coordinate.

This is the prismatic constant-section limit of the generalized formulation.

As a direct consequence, every sectional coefficient generated from this state is independent of the longitudinal coordinate:

$$
J_\bullet(x)=J_\bullet.
$$

Accordingly, the variable-coefficient operators of the generalized CSF-CUF formulation reduce automatically to the constant-coefficient CUF operators used in the Carrera-Giunta reference model.

No CUF approximation order has yet been fixed in this step. The sectional state has been specialized, but the transverse CUF basis remains to be selected exactly as in the reference formulation.

The next step is therefore to introduce the Maclaurin CUF approximation used by Carrera and Giunta and to identify the basis functions associated with a chosen approximation order.

