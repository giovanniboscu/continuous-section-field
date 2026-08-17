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

The CUF approximation across the cross-section is constructed using the Maclaurin polynomial expansion adopted in the reference formulation. The approximation order $N$ remains a model parameter at this stage and will be fixed before the corresponding CUF system is explicitly assembled.

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

## 5. CUF Maclaurin approximation for the first validation model

The reference formulation introduces the generic CUF kinematic field

$$
\mathbf{u}=F_\tau\,\mathbf{u}_\tau
$$

with the approximation order $N$ treated as a free parameter.

Carrera and Giunta then specialize the transverse approximation functions to Maclaurin polynomials. For a polynomial order $N$, the number of transverse functions is

$$
N_u=\frac{(N+1)(N+2)}{2}.
$$

The first rectangular bending benchmark selected in Section 3 is compared in Table 2 of the reference paper for the approximation orders $N=1$, $N=2$, $N=3$, and $N=4$.

For the present first validation, select

$$
N=4.
$$

This choice identifies one specific CUF model among those reported in the reference table and avoids introducing the first-order constitutive correction used in the reference work for classical and first-order models.

For $N=4$,

$$
N_u=15.
$$

In the reference coordinates, the Maclaurin basis contains all monomials in the two transverse coordinates up to total degree four.

Using the coordinate correspondence established in Section 3,

$$
x_{\mathrm{ref}}=y
$$

and

$$
y_{\mathrm{ref}}=z,
$$

the CUF transverse basis used in the present notation is

$$
F_1=1
$$

$$
F_2=y
$$

$$
F_3=z
$$

$$
F_4=y^2
$$

$$
F_5=yz
$$

$$
F_6=z^2
$$

$$
F_7=y^3
$$

$$
F_8=y^2z
$$

$$
F_9=yz^2
$$

$$
F_{10}=z^3
$$

$$
F_{11}=y^4
$$

$$
F_{12}=y^3z
$$

$$
F_{13}=y^2z^2
$$

$$
F_{14}=yz^3
$$

$$
F_{15}=z^4.
$$

The displacement field for this validation model is therefore

$$
\mathbf{u}(x,y,z)=\sum_{\tau=1}^{15}F_\tau(y,z)\mathbf{u}_\tau(x).
$$

Equivalently, each displacement component contains the same 15 transverse monomials, with its own longitudinal amplitudes.

No Navier specialization has yet been applied in this section. The quantities

$$
\mathbf{u}_\tau(x)
$$

remain the longitudinal unknown functions of the completed CUF differential model.

This reproduces the fourth-order Maclaurin CUF approximation used among the rectangular bending results reported by Carrera and Giunta, expressed only in the coordinate convention of the generalized CSF-CUF formulation.

The next step is to evaluate the sectional coefficient families required by the fundamental nucleus for this fixed $N=4$ basis and for the constant rectangular sectional state established in Section 4.


## 6. Computational normalization of the reference geometry

The Carrera-Giunta rectangular bending benchmark is defined by geometric ratios rather than by an absolute dimensional scale.

For the first validation case, the reference work specifies

$$
\frac{l}{a}=100
$$

and

$$
\frac{a}{b}=100.
$$

To evaluate the sectional coefficients numerically in the present CSF-CUF formulation, an explicit dimensional section must be supplied to the sectional integrals.

A computational reference scale is therefore introduced by setting

$$
a=100\ \mathrm{mm}.
$$

The remaining dimensions then follow directly from the reference ratios:

$$
b=\frac{a}{100}=1\ \mathrm{mm}
$$

and

$$
l=100a=10000\ \mathrm{mm}.
$$

This dimensional choice is a computational normalization introduced in the present validation document. It is not an additional geometric datum taken from the Carrera-Giunta paper.

It preserves exactly the reference ratios

$$
\frac{l}{a}=100
$$

and

$$
\frac{a}{b}=100.
$$

With the coordinate correspondence introduced in Section 3, the numerical transverse domain used by the CSF sectional provider is therefore

$$
\Omega^1=\{(y,z):-50\le y\le50,\;-0.5\le z\le0.5\}
$$

with transverse coordinates expressed in millimetres.

The longitudinal interval is

$$
0\le x\le10000
$$

with $x$ expressed in millimetres.

The material parameters remain those specified in the reference work:

$$
E=71700\ \mathrm{MPa}
$$

and

$$
\nu=0.30.
$$

For the isotropic three-dimensional constitutive law used in the present numerical specialization,

$$
G=\frac{E}{2(1+\nu)}=27576.9231\ \mathrm{MPa}
$$

and

$$
\lambda=\frac{E\nu}{(1+\nu)(1-2\nu)}=41365.3846\ \mathrm{MPa}.
$$

Therefore,

$$
C_{11}=C_{22}=C_{33}=96519.2308\ \mathrm{MPa},
$$

$$
C_{12}=C_{13}=C_{23}=41365.3846\ \mathrm{MPa},
$$

and

$$
C_{44}=C_{55}=C_{66}=27576.9231\ \mathrm{MPa}.
$$

The constant constitutive field supplied by the sectional provider is thus numerically determined.

For the Navier half-wave number selected in the reference case,

$$
m=1,
$$

the longitudinal wave parameter becomes

$$
\alpha=\frac{\pi}{l}
$$

and numerically

$$
\alpha=3.14159265\times10^{-4}\ \mathrm{mm}^{-1}.
$$

At this stage, the sectional geometry, material field, longitudinal scale, CUF approximation order, and Navier wave parameter are all numerically fixed.

The next step is to evaluate the generalized sectional coefficients required by the $N=4$ CUF fundamental nucleus over this explicitly defined rectangular domain.
