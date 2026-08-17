# DRAFT

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

## 7. Sectional momenta and correspondence with the generalized coefficients

The next step in the Carrera-Giunta reference formulation is the evaluation of the cross-section quantities entering the differential matrix.

In the reference paper these quantities are introduced in Eq. (4.6) as the cross-section inertial momenta. For the present validation, it is useful to separate the purely geometrical CUF integrals from the constitutive coefficients.

To keep the notation compact and robust in the present document, the index $0$ denotes absence of transverse differentiation.

Define, in the present coordinate convention,

$$ M_{\tau,\phi s,\xi}=\int_{\Omega^1}F_{\tau,\phi}(y,z)F_{s,\xi}(y,z)\,\mathrm{d}\Omega $$

with

$$ \phi,\xi\in\{0,y,z\}. $$

When $\phi=0$ or $\xi=0$, the corresponding basis function is not differentiated.

Because the present benchmark has one homogeneous isotropic sub-domain and a constant constitutive field, the generalized sectional coefficients reduce to

$$ J_{\tau,\phi s,\xi}^{mn}=C_{mn}M_{\tau,\phi s,\xi}. $$

This is the direct correspondence between the generalized CSF-CUF sectional coefficient family and the cross-section momenta of Eq. (4.6) in the reference paper.

Under the coordinate correspondence

$$ x_{\mathrm{ref}}=y $$

and

$$ y_{\mathrm{ref}}=z, $$

the reference quantities map to the present notation as follows:

$$ E_{\tau s}^{\mathrm{ref}}\longleftrightarrow M_{\tau,0s,0} $$

$$ E_{\tau,xs,x}^{\mathrm{ref}}\longleftrightarrow M_{\tau,ys,y} $$

$$ E_{\tau,ys,y}^{\mathrm{ref}}\longleftrightarrow M_{\tau,zs,z} $$

$$ E_{\tau,xs,y}^{\mathrm{ref}}\longleftrightarrow M_{\tau,ys,z} $$

$$ E_{\tau,ys,x}^{\mathrm{ref}}\longleftrightarrow M_{\tau,zs,y} $$

$$ E_{\tau,xs}^{\mathrm{ref}}\longleftrightarrow M_{\tau,ys,0} $$

$$ E_{\tau s,x}^{\mathrm{ref}}\longleftrightarrow M_{\tau,0s,y} $$

$$ E_{\tau,ys}^{\mathrm{ref}}\longleftrightarrow M_{\tau,zs,0} $$

$$ E_{\tau s,y}^{\mathrm{ref}}\longleftrightarrow M_{\tau,0s,z}. $$

No new mechanical quantity is introduced by the symbol $M$. It is used only to distinguish the geometrical cross-section integral from Young's modulus $E$.

### 7.1 Exact integration for the rectangular benchmark

For the fourth-order Maclaurin basis, every transverse approximation function can be written as

$$ F_\tau(y,z)=y^i z^j $$

and

$$ F_s(y,z)=y^\eta z^\theta, $$

with non-negative integer exponents satisfying

$$ i+j\le4 $$

and

$$ \eta+\theta\le4. $$

The reference paper evaluates these integrals analytically in Appendix B for rectangular sub-domains.

For the symmetric rectangle used here,

$$ -a/2\le y\le a/2,\qquad -b/2\le z\le b/2, $$

define the one-dimensional symmetric moment

$$ I_p(h)=\int_{-h/2}^{h/2}q^p\,\mathrm{d}q. $$

Its exact value is

$$ I_p(h)=0 $$

for odd $p$, while for even $p$,

$$ I_p(h)=\frac{h^{p+1}}{2^p(p+1)}. $$

Therefore the undifferentiated sectional momentum is

$$ M_{\tau,0s,0}=I_{i+\eta}(a)I_{j+\theta}(b). $$

The two same-direction derivative momenta are

$$ M_{\tau,ys,y}=i\eta\,I_{i+\eta-2}(a)I_{j+\theta}(b) $$

and

$$ M_{\tau,zs,z}=j\theta\,I_{i+\eta}(a)I_{j+\theta-2}(b). $$

The mixed derivative momenta are

$$ M_{\tau,ys,z}=i\theta\,I_{i+\eta-1}(a)I_{j+\theta-1}(b) $$

and

$$ M_{\tau,zs,y}=j\eta\,I_{i+\eta-1}(a)I_{j+\theta-1}(b). $$

The one-sided derivative momenta are

$$ M_{\tau,ys,0}=i\,I_{i+\eta-1}(a)I_{j+\theta}(b) $$

$$ M_{\tau,0s,y}=\eta\,I_{i+\eta-1}(a)I_{j+\theta}(b) $$

$$ M_{\tau,zs,0}=j\,I_{i+\eta}(a)I_{j+\theta-1}(b) $$

and

$$ M_{\tau,0s,z}=\theta\,I_{i+\eta}(a)I_{j+\theta-1}(b). $$

If a derivative coefficient such as $i$, $j$, $\eta$, or $\theta$ is zero, the corresponding momentum is zero and no negative-order integral is evaluated.

### 7.2 First numerical checks

With

$$ a=100\ \mathrm{mm} $$

and

$$ b=1\ \mathrm{mm}, $$

the area of the section is

$$ M_{1,0\,1,0}=ab=100\ \mathrm{mm}^2. $$

Since

$$ F_2=y, $$

the corresponding second moment is

$$ M_{2,0\,2,0}=\int_{\Omega^1}y^2\,\mathrm{d}\Omega=\frac{ba^3}{12}=83333.3333\ \mathrm{mm}^4. $$

Since

$$ F_3=z, $$

the other transverse second moment is

$$ M_{3,0\,3,0}=\int_{\Omega^1}z^2\,\mathrm{d}\Omega=\frac{ab^3}{12}=8.33333333\ \mathrm{mm}^4. $$

For a derivative example,

$$ F_{2,y}=1, $$

and therefore

$$ M_{2,y\,2,y}=\int_{\Omega^1}1\,\mathrm{d}\Omega=100\ \mathrm{mm}^2. $$

The corresponding constitutive sectional coefficient for the $66$ component is

$$ J_{2,y\,2,y}^{66}=C_{66}M_{2,y\,2,y}. $$

Using

$$ C_{66}=27576.9231\ \mathrm{MPa}, $$

one obtains

$$ J_{2,y\,2,y}^{66}=2.75769231\times10^6\ \mathrm{N}. $$

These checks establish the numerical bridge between the generalized sectional coefficients and the cross-section momenta used by Carrera and Giunta.

The next step is to generate the complete set of non-zero sectional coefficients required by the $N=4$ fundamental nucleus before applying the Navier specialization.**

## 8. Coordinate and displacement-component correspondence

Before assembling the numerical CUF system, one additional correspondence must be made explicit.

This step is necessary because the generalized CSF-CUF formulation and the Carrera-Giunta reference formulation use different labels for the longitudinal and transverse coordinates. The coordinate relabelling introduced in Section 3 must therefore be applied consistently not only to the spatial coordinates and transverse basis functions, but also to the displacement components and, consequently, to the component labels of the fundamental nucleus.

No new kinematic or mechanical assumption is introduced in this section. The purpose is exclusively to establish the one-to-one correspondence required for a term-by-term comparison with the reference formulation.

### 8.1 Coordinate correspondence

The coordinate mapping already established in Section 3 is

$$ x_{\mathrm{CSF}}=z_{\mathrm{ref}} $$

$$ y_{\mathrm{CSF}}=x_{\mathrm{ref}} $$

$$ z_{\mathrm{CSF}}=y_{\mathrm{ref}}. $$

Thus the longitudinal direction of the reference formulation, $z_{\mathrm{ref}}$, corresponds to the longitudinal direction $x_{\mathrm{CSF}}$ of the generalized formulation.

### 8.2 Displacement-component correspondence

The displacement components must follow the same physical-direction mapping.

Therefore,

$$ u_x^{\mathrm{CSF}}=u_z^{\mathrm{ref}} $$

$$ u_y^{\mathrm{CSF}}=u_x^{\mathrm{ref}} $$

$$ u_z^{\mathrm{CSF}}=u_y^{\mathrm{ref}}. $$

For every CUF expansion index $\tau$, the corresponding amplitude mapping is

$$ u_{x\tau}^{\mathrm{CSF}}=u_{z\tau}^{\mathrm{ref}} $$

$$ u_{y\tau}^{\mathrm{CSF}}=u_{x\tau}^{\mathrm{ref}} $$

$$ u_{z\tau}^{\mathrm{CSF}}=u_{y\tau}^{\mathrm{ref}}. $$

Equivalently, the reference displacement-amplitude vector

$$ \mathbf{u}_{\tau}^{\mathrm{ref}}=\{u_{x\tau}^{\mathrm{ref}},u_{y\tau}^{\mathrm{ref}},u_{z\tau}^{\mathrm{ref}}\}^{T} $$

corresponds to the generalized-formulation vector

$$ \mathbf{u}_{\tau}^{\mathrm{CSF}}=\{u_{x\tau}^{\mathrm{CSF}},u_{y\tau}^{\mathrm{CSF}},u_{z\tau}^{\mathrm{CSF}}\}^{T} $$

through the component ordering

$$ \{u_{x\tau}^{\mathrm{CSF}},u_{y\tau}^{\mathrm{CSF}},u_{z\tau}^{\mathrm{CSF}}\}^{T}=\{u_{z\tau}^{\mathrm{ref}},u_{x\tau}^{\mathrm{ref}},u_{y\tau}^{\mathrm{ref}}\}^{T}. $$

### 8.3 Consequence for the fundamental nucleus

The same permutation must be applied when the component blocks of the two fundamental nuclei are compared.

For example,

$$ K_{xx}^{\mathrm{CSF}}\longleftrightarrow K_{zz}^{\mathrm{ref}} $$

$$ K_{yy}^{\mathrm{CSF}}\longleftrightarrow K_{xx}^{\mathrm{ref}} $$

$$ K_{zz}^{\mathrm{CSF}}\longleftrightarrow K_{yy}^{\mathrm{ref}}. $$

For the off-diagonal blocks,

$$ K_{xy}^{\mathrm{CSF}}\longleftrightarrow K_{zx}^{\mathrm{ref}} $$

$$ K_{xz}^{\mathrm{CSF}}\longleftrightarrow K_{zy}^{\mathrm{ref}} $$

$$ K_{yx}^{\mathrm{CSF}}\longleftrightarrow K_{xz}^{\mathrm{ref}} $$

$$ K_{yz}^{\mathrm{CSF}}\longleftrightarrow K_{xy}^{\mathrm{ref}} $$

$$ K_{zx}^{\mathrm{CSF}}\longleftrightarrow K_{yz}^{\mathrm{ref}} $$

$$ K_{zy}^{\mathrm{CSF}}\longleftrightarrow K_{yx}^{\mathrm{ref}}. $$

This permutation does not alter the operator. It only expresses the same physical component coupling in the two coordinate conventions.

Accordingly, a direct comparison of identically named matrix blocks would be incorrect unless this mapping were first applied.

### 8.4 Role of this correspondence in the validation

The validation can now distinguish three operations that must not be conflated:

1. evaluation of the transverse sectional momenta;
2. multiplication by the constitutive coefficients to obtain the generalized sectional coefficients;
3. permutation of coordinate and displacement-component labels when comparing the resulting CSF-CUF nucleus with the Carrera-Giunta nucleus.

The first two operations construct the mechanical coefficients. The third operation changes only their representation.

The next step is therefore to apply this correspondence to the constant-coefficient fundamental nucleus and verify its term-by-term equivalence with the corresponding Carrera-Giunta differential nucleus before generating the complete numerical system for the $N=4$ model.
