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

Before generating the complete coefficient set, the coordinate-component correspondence and the remaining benchmark specialization must be fixed explicitly.

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

## 9. Closure requirements for the numerical benchmark

Before assembling the $N=4$ algebraic system, the reference benchmark must be completely specified in the coordinate convention adopted in the present formulation.

The remaining required data are:

- the numerical load amplitude used for the computational realization;
- the loaded face and the physical direction of the applied traction after coordinate mapping;
- the longitudinal Navier dependence associated with the selected half-wave number;
- the stress components to be recovered from the CSF-CUF solution;
- the exact longitudinal and transverse coordinates at which those stresses must be evaluated;
- the corresponding nondimensional reference values reported in Table 2 of Carrera and Giunta.

These quantities do not introduce a new mechanical model. They complete the specialization of the already defined CUF model to the specific validation problem.

Once these data are fixed, the benchmark is numerically closed: the sectional coefficients, load vector, algebraic system, displacement amplitudes, recovered strains and stresses, and final nondimensional comparison are all uniquely determined.

Only after this closure step is it appropriate to assemble and solve the complete $N=4$ CUF algebraic system.


### 9.1 Reference bending load and its CSF-CUF specialization

The loading must be specialized before the algebraic system is assembled.

This step does not modify the generalized CSF-CUF formulation. It identifies, within the general external-work representation, the particular surface traction used in the Carrera-Giunta rectangular bending benchmark.

#### Reference loading

Carrera and Giunta define the external virtual work as the sum of surface- and line-loading contributions. For the rectangular bending benchmark, the beam is subjected to a surface loading of maximum amplitude

$$ P_{xx}^{1+}. $$

The superscript $1+$ identifies the positive $x_{\mathrm{ref}}$ lateral surface of the single rectangular sub-domain, while the subscripts $xx$ identify a traction component directed along $x_{\mathrm{ref}}$ on that surface.

All other surface- and line-loading amplitudes are zero for this selected benchmark.

For the Navier solution, the reference paper assumes that the normal surface-loading components vary along the beam axis as

$$ p_{xx}^{1+}(z_{\mathrm{ref}})=P_{xx}^{1+}\sin(\alpha z_{\mathrm{ref}}) $$

with

$$ \alpha=\frac{m\pi}{l}. $$

For the selected benchmark,

$$ m=1 $$

and therefore

$$ \alpha=\frac{\pi}{l}. $$

#### Mapping to the generalized CSF-CUF coordinates

The coordinate correspondence established previously is

$$ x_{\mathrm{CSF}}=z_{\mathrm{ref}} $$

$$ y_{\mathrm{CSF}}=x_{\mathrm{ref}} $$

$$ z_{\mathrm{CSF}}=y_{\mathrm{ref}}. $$

Consequently, the reference positive surface

$$ x_{\mathrm{ref}}=+\frac{a}{2} $$

corresponds to the CSF-CUF surface

$$ y_{\mathrm{CSF}}=+\frac{a}{2}. $$

The reference traction direction $x_{\mathrm{ref}}$ corresponds to the CSF-CUF displacement and traction direction $y_{\mathrm{CSF}}$.

The benchmark loading in the present coordinate convention is therefore a normal surface traction applied only on

$$ \Gamma_p=\{(y,z):y=a/2,\;-b/2\le z\le b/2\}. $$

Its non-zero component is

$$ p_y(x,z)=P\sin(\alpha x) $$

on $\Gamma_p$, where $P$ denotes the mapped amplitude of $P_{xx}^{1+}$.

The traction is uniform over the transverse coordinate $z$ of the loaded face.

All other traction components are zero.

#### Computational load normalization

The stress results in the reference paper are finally compared in nondimensional form with respect to the loading amplitude $P_{xx}^{1+}$.

A numerical amplitude may therefore be selected without altering the nondimensional benchmark.

For the present computational realization, set

$$ P=1\ \mathrm{MPa}=1\ \mathrm{N/mm^2}. $$

This is a computational normalization introduced for the numerical validation. It is not an additional loading datum supplied by the reference paper.

With

$$ l=10000\ \mathrm{mm}, $$

the longitudinal wave parameter is

$$ \alpha=\frac{\pi}{10000}=3.14159265\times10^{-4}\ \mathrm{mm}^{-1}. $$

Hence the applied traction is completely determined:

$$ p_y(x,z)=\sin(3.14159265\times10^{-4}x)\ \mathrm{MPa} $$

for

$$ y=50\ \mathrm{mm},\qquad -0.5\le z\le0.5\ \mathrm{mm}. $$

#### Entry into the CUF external virtual work

The generalized CSF-CUF formulation evaluates external work on the current sectional boundary. In the present prismatic benchmark, the loaded boundary is constant along the longitudinal coordinate.

For the selected traction, only the virtual displacement component $\delta u_y$ contributes.

Using the $N=4$ CUF expansion,

$$ \delta u_y(x,y,z)=\sum_{\tau=1}^{15}F_\tau(y,z)\delta u_{y\tau}(x), $$

the surface-loading contribution becomes

$$ \delta L_p=\int_0^l\sum_{\tau=1}^{15}\delta u_{y\tau}(x)\,P\sin(\alpha x)\,B_\tau\,\mathrm{d}x $$

where the loaded-face sectional factors are

$$ B_\tau=\int_{-b/2}^{b/2}F_\tau(a/2,z)\,\mathrm{d}z. $$

These factors are the direct counterparts, after coordinate mapping, of the boundary integrals denoted by $E_\tau^{ky+}$ in the Carrera-Giunta external-work expression.

For the numerical dimensions

$$ a=100\ \mathrm{mm},\qquad b=1\ \mathrm{mm}, $$

the non-zero loaded-face factors for the basis of Section 5 are

$$ B_1=1\ \mathrm{mm} $$

$$ B_2=50\ \mathrm{mm^2} $$

$$ B_4=2500\ \mathrm{mm^3} $$

$$ B_6=8.33333333\times10^{-2}\ \mathrm{mm^3} $$

$$ B_7=125000\ \mathrm{mm^4} $$

$$ B_9=4.16666667\ \mathrm{mm^4} $$

$$ B_{11}=6250000\ \mathrm{mm^5} $$

$$ B_{13}=208.333333\ \mathrm{mm^5} $$

$$ B_{15}=1.25\times10^{-2}\ \mathrm{mm^5}. $$

The remaining loaded-face factors vanish by symmetry:

$$ B_3=B_5=B_8=B_{10}=B_{12}=B_{14}=0. $$

Therefore the load contribution is numerically determined for every CUF test function before assembly of the algebraic system.

#### Chain consistency

For this benchmark, the complete loading chain is

$$ \mathcal{S}_{\mathrm{ref}}\longrightarrow\Gamma_p\longrightarrow p_y(x,z)\longrightarrow B_\tau\longrightarrow f_{y\tau}(x). $$

The generalized load amplitude associated with test function $\tau$ is

$$ f_{y\tau}(x)=P\,B_\tau\sin(\alpha x). $$

No load acts in the $x_{\mathrm{CSF}}$ or $z_{\mathrm{CSF}}$ displacement equations.

This is exactly the reference surface-loading mechanism expressed in the coordinate convention and sectional-provider structure of the generalized CSF-CUF formulation.

No algebraic matrix has yet been assembled in this step.


### 9.2 Reference output quantities and Table 2 validation targets

The numerical benchmark is not completely specified by the load alone. The output quantities must also be identified exactly as they are defined in the Carrera-Giunta reference problem.

This step fixes the physical stress components, the evaluation coordinates, the nondimensionalization formulas, and the numerical target values to be recovered by the present CSF-CUF model.

No new mechanical assumption is introduced.

#### Reference stress components

For the rectangular bending benchmark, Carrera and Giunta report the three stress components

$$ \sigma_{zz}^{\mathrm{ref}} $$

$$ \sigma_{xx}^{\mathrm{ref}} $$

and

$$ \sigma_{xz}^{\mathrm{ref}}. $$

Under the coordinate and component correspondence introduced in Section 8,

$$ x_{\mathrm{CSF}}=z_{\mathrm{ref}} $$

$$ y_{\mathrm{CSF}}=x_{\mathrm{ref}} $$

$$ z_{\mathrm{CSF}}=y_{\mathrm{ref}}, $$

the corresponding CSF-CUF stress components are

$$ \sigma_{xx}^{\mathrm{CSF}}\longleftrightarrow\sigma_{zz}^{\mathrm{ref}} $$

$$ \sigma_{yy}^{\mathrm{CSF}}\longleftrightarrow\sigma_{xx}^{\mathrm{ref}} $$

and

$$ \sigma_{xy}^{\mathrm{CSF}}\longleftrightarrow\sigma_{xz}^{\mathrm{ref}}. $$

Therefore the validation must compare physically corresponding stress components, not identically named tensor entries.

#### Reference evaluation coordinates

The reference paper evaluates all three reported stresses at

$$ y_{\mathrm{ref}}=0. $$

In the CSF-CUF coordinate convention this condition becomes

$$ z_{\mathrm{CSF}}=0. $$

For the normal stress components $\sigma_{zz}^{\mathrm{ref}}$ and $\sigma_{xx}^{\mathrm{ref}}$, the longitudinal coordinate is

$$ z_{\mathrm{ref}}=\frac{l}{2}. $$

Hence, in the present notation,

$$ x_{\mathrm{CSF}}=\frac{l}{2}=5000\ \mathrm{mm}. $$

For the shear stress component $\sigma_{xz}^{\mathrm{ref}}$, the reference longitudinal coordinate is

$$ z_{\mathrm{ref}}=0, $$

which becomes

$$ x_{\mathrm{CSF}}=0. $$

The transverse coordinate $x_{\mathrm{ref}}$ is varied across the section. In the present coordinate convention,

$$ x_{\mathrm{ref}}=y_{\mathrm{CSF}}. $$

The Table 2 values are evaluated at the three reference positions

$$ x_{\mathrm{ref}}=\frac{a}{2} $$

$$ x_{\mathrm{ref}}=-\frac{a}{2} $$

and

$$ x_{\mathrm{ref}}=0. $$

With the numerical normalization $a=100\ \mathrm{mm}$, these become

$$ y_{\mathrm{CSF}}=50\ \mathrm{mm} $$

$$ y_{\mathrm{CSF}}=-50\ \mathrm{mm} $$

and

$$ y_{\mathrm{CSF}}=0. $$

#### Nondimensional stress definitions

Carrera and Giunta define the nondimensional normal bending stress as

$$ \sigma_{zz}^{*}=\frac{\pi^2}{6}\frac{a^2}{l^2}\frac{\sigma_{zz}^{\mathrm{ref}}}{P}. $$

Using the CSF-CUF component mapping, the same validation quantity is evaluated from

$$ \sigma_{xx}^{\mathrm{CSF}}. $$

Therefore,

$$ \sigma_{zz}^{*}=\frac{\pi^2}{6}\frac{a^2}{l^2}\frac{\sigma_{xx}^{\mathrm{CSF}}}{P}. $$

The reference transverse normal stress is nondimensionalized as

$$ \sigma_{xx}^{*}=\frac{\sigma_{xx}^{\mathrm{ref}}}{P}. $$

In the present notation,

$$ \sigma_{xx}^{*}=\frac{\sigma_{yy}^{\mathrm{CSF}}}{P}. $$

The reference shear stress is nondimensionalized as

$$ \sigma_{xz}^{*}=\frac{2\pi}{3}\frac{a}{l}\frac{\sigma_{xz}^{\mathrm{ref}}}{P}. $$

In the present notation,

$$ \sigma_{xz}^{*}=\frac{2\pi}{3}\frac{a}{l}\frac{\sigma_{xy}^{\mathrm{CSF}}}{P}. $$

For the computational normalization

$$ a=100\ \mathrm{mm},\qquad l=10000\ \mathrm{mm},\qquad P=1\ \mathrm{MPa}, $$

the dimensional scaling factors are

$$ \frac{6l^2}{\pi^2a^2}=6079.27102 $$

and

$$ \frac{3l}{2\pi a}=47.7464829. $$

Therefore the dimensional stress values corresponding to unit nondimensional values are

$$ \sigma_{xx}^{\mathrm{CSF}}=6079.27102\ \mathrm{MPa} $$

for

$$ \sigma_{zz}^{*}=1, $$

$$ \sigma_{yy}^{\mathrm{CSF}}=1\ \mathrm{MPa} $$

for

$$ \sigma_{xx}^{*}=1, $$

and

$$ \sigma_{xy}^{\mathrm{CSF}}=47.7464829\ \mathrm{MPa} $$

for

$$ \sigma_{xz}^{*}=1. $$

These dimensional values are only consequences of the selected computational normalization. The actual validation remains nondimensional.

#### Table 2 target values for the N=4 model

For the selected benchmark with

$$ \frac{l}{a}=100 $$

and

$$ N=4, $$

Carrera and Giunta report the following nondimensional stress values.

For the longitudinal bending stress,

$$ \sigma_{zz}^{*}\bigl(x_{\mathrm{ref}}=a/2\bigr)=1.0000 $$

and

$$ \sigma_{zz}^{*}\bigl(x_{\mathrm{ref}}=-a/2\bigr)=-1.0000. $$

In the present coordinates, these correspond to

$$ \sigma_{xx}^{\mathrm{CSF}}(x=5000,y=50,z=0) $$

and

$$ \sigma_{xx}^{\mathrm{CSF}}(x=5000,y=-50,z=0). $$

For the transverse normal stress,

$$ \sigma_{xx}^{*}\bigl(x_{\mathrm{ref}}=0\bigr)=0.5000 $$

and

$$ \sigma_{xx}^{*}\bigl(x_{\mathrm{ref}}=a/2\bigr)=1.0000. $$

In the present coordinates, these correspond to

$$ \sigma_{yy}^{\mathrm{CSF}}(x=5000,y=0,z=0) $$

and

$$ \sigma_{yy}^{\mathrm{CSF}}(x=5000,y=50,z=0). $$

For the transverse shear stress,

$$ \sigma_{xz}^{*}\bigl(x_{\mathrm{ref}}=0\bigr)=1.0000 $$

and

$$ \sigma_{xz}^{*}\bigl(x_{\mathrm{ref}}=a/2\bigr)=0.0000. $$

In the present coordinates, these correspond to

$$ \sigma_{xy}^{\mathrm{CSF}}(x=0,y=0,z=0) $$

and

$$ \sigma_{xy}^{\mathrm{CSF}}(x=0,y=50,z=0). $$

The six numerical validation targets are therefore

$$ 1.0000,\;-1.0000,\;0.5000,\;1.0000,\;1.0000,\;0.0000. $$

#### Completion of the benchmark output specification

After Sections 9.1 and 9.2, the loading and the validation outputs are fully specified.

The remaining specialization required before algebraic assembly is the Navier longitudinal representation of the displacement amplitudes and its corresponding end-condition mapping.

This is introduced in the following section directly from the Carrera-Giunta closed-form solution.


### 9.3 Navier displacement specialization and end-condition correspondence

Before assembling the algebraic CUF system, the longitudinal dependence of the displacement amplitudes must be specialized exactly as in the Carrera-Giunta closed-form solution.

This step introduces no additional kinematic assumption beyond the reference model. It applies the Navier representation of the paper to the coordinate and displacement-component correspondence already established in Section 8.

#### Reference Navier displacement field

Carrera and Giunta adopt, for every CUF approximation index $\tau$,

$$ u_{x\tau}^{\mathrm{ref}}(z_{\mathrm{ref}})=U_{x\tau}^{\mathrm{ref}}\sin(\alpha z_{\mathrm{ref}}) $$

$$ u_{y\tau}^{\mathrm{ref}}(z_{\mathrm{ref}})=U_{y\tau}^{\mathrm{ref}}\sin(\alpha z_{\mathrm{ref}}) $$

and

$$ u_{z\tau}^{\mathrm{ref}}(z_{\mathrm{ref}})=U_{z\tau}^{\mathrm{ref}}\cos(\alpha z_{\mathrm{ref}}). $$

The longitudinal wave parameter is

$$ \alpha=\frac{m\pi}{l}. $$

For the present benchmark,

$$ m=1 $$

and therefore

$$ \alpha=\frac{\pi}{l}. $$

#### Mapping to the CSF-CUF displacement components

The previously established component correspondence is

$$ u_x^{\mathrm{CSF}}=u_z^{\mathrm{ref}} $$

$$ u_y^{\mathrm{CSF}}=u_x^{\mathrm{ref}} $$

$$ u_z^{\mathrm{CSF}}=u_y^{\mathrm{ref}} $$

together with

$$ x_{\mathrm{CSF}}=z_{\mathrm{ref}}. $$

Therefore, for every $\tau$,

$$ u_{x\tau}^{\mathrm{CSF}}(x)=U_{x\tau}^{\mathrm{CSF}}\cos(\alpha x) $$

$$ u_{y\tau}^{\mathrm{CSF}}(x)=U_{y\tau}^{\mathrm{CSF}}\sin(\alpha x) $$

and

$$ u_{z\tau}^{\mathrm{CSF}}(x)=U_{z\tau}^{\mathrm{CSF}}\sin(\alpha x). $$

The corresponding amplitude mapping is

$$ U_{x\tau}^{\mathrm{CSF}}=U_{z\tau}^{\mathrm{ref}} $$

$$ U_{y\tau}^{\mathrm{CSF}}=U_{x\tau}^{\mathrm{ref}} $$

$$ U_{z\tau}^{\mathrm{CSF}}=U_{y\tau}^{\mathrm{ref}}. $$

Using the $N=4$ transverse basis, the full displacement field becomes

$$ u_x(x,y,z)=\sum_{\tau=1}^{15}F_\tau(y,z)U_{x\tau}\cos(\alpha x) $$

$$ u_y(x,y,z)=\sum_{\tau=1}^{15}F_\tau(y,z)U_{y\tau}\sin(\alpha x) $$

and

$$ u_z(x,y,z)=\sum_{\tau=1}^{15}F_\tau(y,z)U_{z\tau}\sin(\alpha x). $$

The $45$ longitudinal unknown functions of the differential CUF model are therefore reduced to the $45$ constant Navier amplitudes

$$ \{U_{x\tau},U_{y\tau},U_{z\tau}\}_{\tau=1}^{15}. $$

#### Longitudinal derivatives

The longitudinal derivatives required by the fundamental nucleus follow directly.

For the longitudinal displacement component,

$$ \frac{\mathrm{d}u_{x\tau}}{\mathrm{d}x}=-\alpha U_{x\tau}\sin(\alpha x) $$

and

$$ \frac{\mathrm{d}^2u_{x\tau}}{\mathrm{d}x^2}=-\alpha^2U_{x\tau}\cos(\alpha x). $$

For the two transverse displacement components,

$$ \frac{\mathrm{d}u_{y\tau}}{\mathrm{d}x}=\alpha U_{y\tau}\cos(\alpha x) $$

$$ \frac{\mathrm{d}^2u_{y\tau}}{\mathrm{d}x^2}=-\alpha^2U_{y\tau}\sin(\alpha x) $$

$$ \frac{\mathrm{d}u_{z\tau}}{\mathrm{d}x}=\alpha U_{z\tau}\cos(\alpha x) $$

and

$$ \frac{\mathrm{d}^2u_{z\tau}}{\mathrm{d}x^2}=-\alpha^2U_{z\tau}\sin(\alpha x). $$

These substitutions are the CSF-CUF counterpart of the reference passage from the differential fundamental nucleus to the algebraic fundamental nucleus.

#### End-condition correspondence

The reference Navier field satisfies the longitudinal end conditions

$$ u_{x\tau}^{\mathrm{ref}}(0)=u_{x\tau}^{\mathrm{ref}}(l)=0 $$

$$ u_{y\tau}^{\mathrm{ref}}(0)=u_{y\tau}^{\mathrm{ref}}(l)=0 $$

and

$$ \frac{\mathrm{d}u_{z\tau}^{\mathrm{ref}}}{\mathrm{d}z_{\mathrm{ref}}}(0)=\frac{\mathrm{d}u_{z\tau}^{\mathrm{ref}}}{\mathrm{d}z_{\mathrm{ref}}}(l)=0. $$

After coordinate and component mapping, the corresponding CSF-CUF conditions are

$$ u_{y\tau}^{\mathrm{CSF}}(0)=u_{y\tau}^{\mathrm{CSF}}(l)=0 $$

$$ u_{z\tau}^{\mathrm{CSF}}(0)=u_{z\tau}^{\mathrm{CSF}}(l)=0 $$

and

$$ \frac{\mathrm{d}u_{x\tau}^{\mathrm{CSF}}}{\mathrm{d}x}(0)=\frac{\mathrm{d}u_{x\tau}^{\mathrm{CSF}}}{\mathrm{d}x}(l)=0. $$

These conditions are satisfied identically by the mapped sine-cosine representation above.

#### Closure before algebraic assembly

At this point, no longitudinal function remains to be determined.

The benchmark is now completely specialized in the same sense as the Carrera-Giunta model immediately before construction of the algebraic fundamental nucleus.

The remaining steps are deterministic:

1. substitute the Navier field into the constant-coefficient CSF-CUF fundamental nucleus;
2. identify the resulting algebraic $3\times3$ block associated with each pair $(\tau,s)$;
3. evaluate the required sectional coefficients for all $\tau,s=1,\ldots,15$;
4. assemble the complete $45\times45$ algebraic system;
5. solve for the $45$ amplitudes $U_{x\tau}$, $U_{y\tau}$, and $U_{z\tau}$;
6. recover the stress components and compare the nondimensional values with Table 2.

No additional physical assumption is introduced by these steps.


## 10. Algebraic fundamental nucleus after Navier specialization

The benchmark has now reached the same stage at which Carrera and Giunta pass from the differential fundamental nucleus to the algebraic fundamental nucleus.

This section performs only that specialization.

No new constitutive, kinematic, loading, or sectional assumption is introduced.

The starting point is the constant-section limit of the generalized CSF-CUF fundamental nucleus. Because

$$ \mathcal{S}(x)=\mathcal{S}_{\mathrm{ref}} $$

for the present benchmark, every sectional coefficient is constant along the beam axis:

$$ J_{\tau,\phi s,\xi}^{mn}(x)=J_{\tau,\phi s,\xi}^{mn}. $$

Therefore the longitudinally varying CSF-CUF operators reduce exactly to their constant-coefficient forms before the Navier substitution is applied.

### 10.1 Algebraic block for one CUF pair

For each pair of transverse approximation indices

$$ (\tau,s), $$


define the Navier amplitude vector

$$ \mathbf{U}_s= \begin{bmatrix} U_{xs}\\ U_{ys}\\ U_{zs} \end{bmatrix} $$

The mapped bending load established in Section 9.1 gives the generalized algebraic right-hand-side components

$$ F_{x\tau}=0, $$

$$ F_{y\tau}=P B_\tau, $$

and

$$ F_{z\tau}=0. $$

For each pair $(\tau,s)$, denote by $\mathbf{A}_{\tau s}$ the corresponding $3\times3$ algebraic fundamental-nucleus block.

Collecting the three right-hand-side components in the present CSF-CUF notation as $\mathbf{F}_\tau$, for every test index $\tau$ the algebraic governing equation is

$$ \sum_{s=1}^{15}\mathbf{A}_{\tau s}\mathbf{U}_s=\mathbf{F}_\tau. $$

### 10.2 Diagonal algebraic terms

The constant-coefficient differential diagonal terms of the generalized CSF-CUF nucleus are

$$ K_{xx}^{\tau s} = J_{\tau,y s,y}^{66} + J_{\tau,z s,z}^{55} - J_{\tau,0s,0}^{11}\partial_x^2, $$

$$ K_{yy}^{\tau s} = J_{\tau,y s,y}^{22} + J_{\tau,z s,z}^{44} - J_{\tau,0s,0}^{66}\partial_x^2, $$

and

$$ K_{zz}^{\tau s} = J_{\tau,y s,y}^{44} + J_{\tau,z s,z}^{33} - J_{\tau,0s,0}^{55}\partial_x^2. $$

Using the Navier fields of Section 9.3,

$$ u_{xs}(x)=U_{xs}\cos(\alpha x), $$

$$ u_{ys}(x)=U_{ys}\sin(\alpha x), $$

and

$$ u_{zs}(x)=U_{zs}\sin(\alpha x), $$

each second derivative contributes

$$ -\partial_x^2\longrightarrow \alpha^2. $$

Hence,

$$ A_{xx}^{\tau s} = J_{\tau,y s,y}^{66} + J_{\tau,z s,z}^{55} + \alpha^2J_{\tau,0s,0}^{11}, $$

$$ A_{yy}^{\tau s} = J_{\tau,y s,y}^{22} + J_{\tau,z s,z}^{44} + \alpha^2J_{\tau,0s,0}^{66}, $$

and

$$ A_{zz}^{\tau s} = J_{\tau,y s,y}^{44} + J_{\tau,z s,z}^{33} + \alpha^2J_{\tau,0s,0}^{55}. $$

These are the mapped counterparts of the three diagonal terms of the Carrera-Giunta algebraic nucleus.

### 10.3 Mixed first-order algebraic terms

For constant sectional coefficients, the four mixed first-order operators are

$$ K_{xy}^{\tau s} = \left( -J_{\tau,0s,y}^{12} + J_{\tau,y s,0}^{66} \right)\partial_x, $$

$$ K_{yx}^{\tau s} = \left( J_{\tau,y s,0}^{12} - J_{\tau,0s,y}^{66} \right)\partial_x, $$

$$ K_{xz}^{\tau s} = \left( -J_{\tau,0s,z}^{13} + J_{\tau,z s,0}^{55} \right)\partial_x, $$

and

$$ K_{zx}^{\tau s} = \left( J_{\tau,z s,0}^{13} - J_{\tau,0s,z}^{55} \right)\partial_x. $$

The sign generated by the longitudinal derivative depends on whether the source displacement uses the sine or cosine Navier function.

Since

$$ \frac{\mathrm{d}}{\mathrm{d}x}\sin(\alpha x)=\alpha\cos(\alpha x) $$

and

$$ \frac{\mathrm{d}}{\mathrm{d}x}\cos(\alpha x)=-\alpha\sin(\alpha x), $$

the resulting algebraic terms are

$$ A_{xy}^{\tau s} = \alpha \left( -J_{\tau,0s,y}^{12} + J_{\tau,y s,0}^{66} \right), $$

$$ A_{yx}^{\tau s} = -\alpha \left( J_{\tau,y s,0}^{12} - J_{\tau,0s,y}^{66} \right), $$

$$ A_{xz}^{\tau s} = \alpha \left( -J_{\tau,0s,z}^{13} + J_{\tau,z s,0}^{55} \right), $$

and

$$ A_{zx}^{\tau s} = -\alpha \left( J_{\tau,z s,0}^{13} - J_{\tau,0s,z}^{55} \right). $$

Equivalently,

$$ A_{yx}^{\tau s} = \alpha \left( J_{\tau,0s,y}^{66} - J_{\tau,y s,0}^{12} \right) $$

and

$$ A_{zx}^{\tau s} = \alpha \left( J_{\tau,0s,z}^{55} - J_{\tau,z s,0}^{13} \right). $$

No derivative of a sectional coefficient appears because all sectional coefficients are constant for this prismatic validation case.

### 10.4 Zero-order off-diagonal terms

The two remaining off-diagonal terms contain no longitudinal derivative.

They are

$$ A_{yz}^{\tau s} = J_{\tau,y s,z}^{23} + J_{\tau,z s,y}^{44} $$

and

$$ A_{zy}^{\tau s} = J_{\tau,z s,y}^{23} + J_{\tau,y s,z}^{44}. $$

They are therefore unchanged by the Navier substitution.

### 10.5 Complete algebraic nucleus

For each pair $(\tau,s)$, the complete algebraic block is

$$ \mathbf{A}_{\tau s} = \begin{bmatrix} J_{\tau,y s,y}^{66}+J_{\tau,z s,z}^{55}+\alpha^2J_{\tau,0s,0}^{11} & \alpha\left(-J_{\tau,0s,y}^{12}+J_{\tau,y s,0}^{66}\right) & \alpha\left(-J_{\tau,0s,z}^{13}+J_{\tau,z s,0}^{55}\right) \\ \alpha\left(J_{\tau,0s,y}^{66}-J_{\tau,y s,0}^{12}\right) & J_{\tau,y s,y}^{22}+J_{\tau,z s,z}^{44}+\alpha^2J_{\tau,0s,0}^{66} & J_{\tau,y s,z}^{23}+J_{\tau,z s,y}^{44} \\ \alpha\left(J_{\tau,0s,z}^{55}-J_{\tau,z s,0}^{13}\right) & J_{\tau,z s,y}^{23}+J_{\tau,y s,z}^{44} & J_{\tau,y s,y}^{44}+J_{\tau,z s,z}^{33}+\alpha^2J_{\tau,0s,0}^{55} \end{bmatrix}. $$

This block is written entirely in the coordinate convention of the generalized CSF-CUF formulation.

Under the coordinate and displacement-component permutation established in Section 8, it is the same physical algebraic fundamental nucleus obtained from the Carrera-Giunta differential nucleus after the Navier substitution.

### 10.6 Required sectional coefficient families

The algebraic block shows explicitly which sectional quantities must be evaluated for every pair $(\tau,s)$.

The required families are

$$ J_{\tau,0s,0}^{11}, \qquad J_{\tau,0s,0}^{55}, \qquad J_{\tau,0s,0}^{66}, $$

$$ J_{\tau,y s,y}^{22}, \qquad J_{\tau,y s,y}^{44}, \qquad J_{\tau,y s,y}^{66}, $$

$$ J_{\tau,z s,z}^{33}, \qquad J_{\tau,z s,z}^{44}, \qquad J_{\tau,z s,z}^{55}, $$

$$ J_{\tau,0s,y}^{12}, \qquad J_{\tau,y s,0}^{12}, $$

$$ J_{\tau,0s,y}^{66}, \qquad J_{\tau,y s,0}^{66}, $$

$$ J_{\tau,0s,z}^{13}, \qquad J_{\tau,z s,0}^{13}, $$

$$ J_{\tau,0s,z}^{55}, \qquad J_{\tau,z s,0}^{55}, $$

and

$$ J_{\tau,y s,z}^{23}, \qquad J_{\tau,z s,y}^{23}, \qquad J_{\tau,z s,y}^{44}, \qquad J_{\tau,y s,z}^{44}. $$

For the homogeneous isotropic rectangular benchmark, each of these coefficients is obtained directly from the corresponding geometrical momentum introduced in Section 7 through

$$ J_{\tau,\phi s,\xi}^{mn}=C_{mn}M_{\tau,\phi s,\xi}. $$

No additional sectional definition is required.

### 10.7 Status before numerical matrix generation

The derivation has now reached the algebraic-nucleus stage corresponding to the Carrera-Giunta closed-form formulation.

For

$$ N=4, $$

there are

$$ N_u=15 $$

transverse functions and therefore

$$ 15\times15=225 $$

ordered CUF pairs $(\tau,s)$.

Each pair generates one $3\times3$ block $\mathbf{A}_{\tau s}$.

Their assembly produces the final system

$$ \mathbf{A}\mathbf{U}=\mathbf{F} $$

with

$$ \mathbf{A}\in\mathbb{R}^{45\times45}. $$

At this point the remaining work is numerical rather than formulational: generate the required sectional momenta for the fixed $N=4$ basis, multiply them by the already specified constitutive coefficients, populate the $225$ algebraic blocks, and assemble the complete matrix and load vector.

No additional physical assumption is required.

### 10.8 Direct term-by-term verification against Carrera-Giunta Eq. (5.5)

Before generating any numerical matrix entry, the algebraic nucleus obtained above is compared directly with Eq. (5.5) of Carrera and Giunta.

No numerical datum and no additional assumption are introduced in this verification.

The comparison uses only the coordinate and component correspondence already established:

$$ x_{\mathrm{CSF}}=z_{\mathrm{ref}},\qquad y_{\mathrm{CSF}}=x_{\mathrm{ref}},\qquad z_{\mathrm{CSF}}=y_{\mathrm{ref}}. $$

Therefore the displacement-component ordering is

$$ (u_x,u_y,u_z)_{\mathrm{CSF}}=(u_z,u_x,u_y)_{\mathrm{ref}}. $$

The transverse derivative correspondence is

$$ \partial_{x_{\mathrm{ref}}}\longleftrightarrow\partial_{y_{\mathrm{CSF}}},\qquad \partial_{y_{\mathrm{ref}}}\longleftrightarrow\partial_{z_{\mathrm{CSF}}}. $$

The constitutive-component correspondence induced by the same permutation is

$$ C_{33}^{\mathrm{ref}}\longleftrightarrow C_{11}^{\mathrm{CSF}},\qquad C_{11}^{\mathrm{ref}}\longleftrightarrow C_{22}^{\mathrm{CSF}},\qquad C_{22}^{\mathrm{ref}}\longleftrightarrow C_{33}^{\mathrm{CSF}}, $$

$$ C_{44}^{\mathrm{ref}}\longleftrightarrow C_{55}^{\mathrm{CSF}},\qquad C_{55}^{\mathrm{ref}}\longleftrightarrow C_{66}^{\mathrm{CSF}},\qquad C_{66}^{\mathrm{ref}}\longleftrightarrow C_{44}^{\mathrm{CSF}}, $$

and

$$ C_{13}^{\mathrm{ref}}\longleftrightarrow C_{12}^{\mathrm{CSF}},\qquad C_{23}^{\mathrm{ref}}\longleftrightarrow C_{13}^{\mathrm{CSF}},\qquad C_{12}^{\mathrm{ref}}\longleftrightarrow C_{23}^{\mathrm{CSF}}. $$

For the present isotropic benchmark these permutations do not change the numerical constitutive values, but they are retained here because they are necessary for a literal term-by-term comparison.

#### Diagonal blocks

The reference $zz$ equation becomes the CSF $xx$ equation. Its diagonal term maps to

$$ A_{xx}^{\tau s}=J_{\tau,y s,y}^{66}+J_{\tau,z s,z}^{55}+\alpha^2J_{\tau,0s,0}^{11}. $$

The reference $xx$ equation becomes the CSF $yy$ equation. Its diagonal term maps to

$$ A_{yy}^{\tau s}=J_{\tau,y s,y}^{22}+J_{\tau,z s,z}^{44}+\alpha^2J_{\tau,0s,0}^{66}. $$

The reference $yy$ equation becomes the CSF $zz$ equation. Its diagonal term maps to

$$ A_{zz}^{\tau s}=J_{\tau,y s,y}^{44}+J_{\tau,z s,z}^{33}+\alpha^2J_{\tau,0s,0}^{55}. $$

These are exactly the three diagonal terms obtained in Section 10.2.

#### First-order coupling blocks

The reference $zx$ block becomes the CSF $xy$ block:

$$ A_{xy}^{\tau s}=\alpha\left(-J_{\tau,0s,y}^{12}+J_{\tau,y s,0}^{66}\right). $$

The reference $xz$ block becomes the CSF $yx$ block:

$$ A_{yx}^{\tau s}=\alpha\left(J_{\tau,0s,y}^{66}-J_{\tau,y s,0}^{12}\right). $$

The reference $zy$ block becomes the CSF $xz$ block:

$$ A_{xz}^{\tau s}=\alpha\left(-J_{\tau,0s,z}^{13}+J_{\tau,z s,0}^{55}\right). $$

The reference $yz$ block becomes the CSF $zx$ block:

$$ A_{zx}^{\tau s}=\alpha\left(J_{\tau,0s,z}^{55}-J_{\tau,z s,0}^{13}\right). $$

These are exactly the four first-order terms obtained in Section 10.3.

#### Zero-order transverse coupling blocks

The reference $xy$ block becomes the CSF $yz$ block:

$$ A_{yz}^{\tau s}=J_{\tau,y s,z}^{23}+J_{\tau,z s,y}^{44}. $$

The reference $yx$ block becomes the CSF $zy$ block:

$$ A_{zy}^{\tau s}=J_{\tau,z s,y}^{23}+J_{\tau,y s,z}^{44}. $$

These are exactly the two zero-order terms obtained in Section 10.4.

#### Load-vector correspondence

The selected Carrera-Giunta benchmark applies only the normal surface loading amplitude $P_{xx}^{1+}$.

Under the established coordinate and component mapping, this load contributes only to the CSF $y$ equation on the positive $y$ face.

Accordingly, for the selected benchmark, the three generalized algebraic right-hand-side components reduce to

$$ F_{x\tau}=0, $$

$$ F_{y\tau}=P B_\tau, $$

and

$$ F_{z\tau}=0. $$

This is the CSF-coordinate representation of the non-zero $P_{xx}^{1+}$ contribution appearing in the corresponding Carrera-Giunta algebraic equation.


#### Verification result

All nine entries of the $3\times3$ algebraic fundamental nucleus and the non-zero load-vector component are obtained by direct permutation of Eq. (5.5) of Carrera and Giunta.

Therefore,

$$ \boxed{\mathbf{A}_{\tau s}^{\mathrm{CSF}}\equiv\mathbf{A}_{\tau s}^{\mathrm{Carrera-Giunta}}} $$

after the coordinate, displacement-component, derivative, and constitutive-index correspondences stated above.

This equivalence is established before any complete numerical coefficient table or $45\times45$ matrix is generated.

The next step may therefore evaluate the required sectional momenta for the already fixed $N=4$ basis and populate the algebraic blocks without introducing any new physical datum.





### 11.10 Explicit reconstructed displacement field and direct verification of the first Table 2 value

The solution of the assembled 45-by-45 algebraic system determines all 45 Navier amplitudes of the fourth-order CUF approximation.

For the present benchmark, the dimensional normalization is:

- `a = 100 mm`
- `b = 1 mm`
- `l = 10000 mm`

The corresponding longitudinal wave parameter is

$$ \alpha=\frac{\pi}{l}=3.141592653589793\times 10^{-4}\;\mathrm{mm}^{-1}. $$

With `x`, `y`, and `z` expressed in millimetres, the reconstructed displacement field contains no remaining unknown generalized coordinate.

The complete displacement field is

$$ \mathbf{u}(x,y,z)=\left[u_x(x,y,z),\;u_y(x,y,z),\;u_z(x,y,z)\right]^T. $$

The longitudinal component is

$$ u_x(x,y,z)=\cos(\alpha x)\,P_x(y,z). $$

The corresponding transverse polynomial is

$$
\begin{aligned}
P_x(y,z)=\;&
0.00666011537210657
-5.39728020173845\,y
-1.09529132604698\times10^{-9}y^2\\
&+3.28604964388473\times10^{-10}z^2
-2.04222057253354\times10^{-7}y^3
+7.99151215448526\times10^{-8}yz^2\\
&-2.07202568142699\times10^{-17}y^4
+1.62130477403799\times10^{-17}y^2z^2\\
&+5.40563082485546\times10^{-18}z^4.
\end{aligned}
$$

The first transverse component is

$$ u_y(x,y,z)=\sin(\alpha x)\,P_y(y,z). $$

The corresponding transverse polynomial is

$$
\begin{aligned}
P_y(y,z)=\;&
17185.5875869867
+6.97358670064822\times10^{-6}y
-2.54245650407800\times10^{-4}y^2\\
&+2.54381631921103\times10^{-4}z^2
-3.44085339398371\times10^{-14}y^3\\
&+1.03231983451457\times10^{-13}yz^2
-1.11576498142161\times10^{-11}y^4\\
&+1.25509796913857\times10^{-11}y^2z^2
+4.18437513454488\times10^{-12}z^4.
\end{aligned}
$$

The second transverse component is

$$ u_z(x,y,z)=\sin(\alpha x)\,P_z(y,z). $$

The corresponding transverse polynomial is

$$
\begin{aligned}
P_z(y,z)=\;&
-2.09196417628091\times10^{-6}z
-5.08763263843358\times10^{-4}yz\\
&-1.03236112958000\times10^{-13}y^2z
+9.36480077442161\times10^{-19}z^3\\
&-8.36899311952235\times10^{-12}y^3z
+3.55782082541376\times10^{-16}yz^3.
\end{aligned}
$$

Terms of the fourth-order Maclaurin basis that do not appear in these three polynomials have zero numerical amplitude for this benchmark solution.

The field above is therefore directly evaluable at any point of the beam.

#### Direct reconstruction of the first Table 2 quantity

The first numerical quantity reported in the `N = 4` row of Carrera-Giunta Table 2 is

$$ \sigma_{zz}^{*}=1.0000. $$

The corresponding reference-paper point is:

- `x_ref = a/2`
- `y_ref = 0`
- `z_ref = l/2`

Carrera and Giunta define this nondimensional quantity in Eq. (6.1), page 130, as

$$ \sigma_{zz}^{*}=\frac{\pi^2}{6}\frac{a^2}{l^2}\frac{\sigma_{zz}}{P_{xx}^{1+}}. $$

The target value `1.0000` is not inserted into the CSF-CUF solution.

Only the physical evaluation point specified by the reference paper is inserted.

Using the coordinate correspondence

$$ x_{\mathrm{CSF}}=z_{\mathrm{ref}},\qquad y_{\mathrm{CSF}}=x_{\mathrm{ref}},\qquad z_{\mathrm{CSF}}=y_{\mathrm{ref}}, $$

the Table 2 evaluation point becomes:

- `x_CSF = 5000 mm`
- `y_CSF = 50 mm`
- `z_CSF = 0 mm`

At this point,

$$ \sin(\alpha x)=1 $$

and

$$ \cos(\alpha x)=0. $$

The normal strain components reconstructed from the explicit displacement field are

$$ \varepsilon_{xx}=\frac{\partial u_x}{\partial x}=0.08478620746049834, $$

$$ \varepsilon_{yy}=\frac{\partial u_y}{\partial y}=-0.025423170537050465, $$

and

$$ \varepsilon_{zz}=\frac{\partial u_z}{\partial z}=-0.025441301538574407. $$

For the isotropic constitutive law already fixed in Section 6,

- `C11 = 96519.23076923077 MPa`
- `C12 = 41365.38461538461 MPa`

Because the reference longitudinal direction `z_ref` corresponds to the CSF longitudinal direction `x_CSF`,

$$ \sigma_{zz}^{\mathrm{ref}}=\sigma_{xx}^{\mathrm{CSF}}. $$

Therefore,

$$ \sigma_{xx}^{\mathrm{CSF}}=C_{11}\varepsilon_{xx}+C_{12}\left(\varepsilon_{yy}+\varepsilon_{zz}\right). $$

Substitution gives

$$ \sigma_{xx}^{\mathrm{CSF}}=6079.471073261\ \mathrm{MPa}. $$

Using

- `a = 100 mm`
- `l = 10000 mm`
- `Pxx(1+) = 1 MPa`

the nondimensional stress reconstructed from the CSF-CUF solution is

$$ \sigma_{zz}^{*}=\frac{\pi^2}{6}\frac{100^2}{10000^2}\frac{6079.471073261}{1}. $$

Hence,

$$ \boxed{\sigma_{zz,\mathrm{CSF-CUF}}^{*}=1.00003290768}. $$

Carrera-Giunta Table 2, page 130, row `N = 4`, reports

$$ \boxed{\sigma_{zz,\mathrm{reference}}^{*}=1.0000}. $$

The absolute difference is therefore




$$ \left|1.00003290768-1.0000\right|=3.290768\times10^{-5}. $$

The relative difference with respect to the tabulated reference value is approximately

$$ 0.00329\%. $$

The complete first validation chain is therefore visible numerically:

$$ \mathbf{u}(x,y,z)\longrightarrow\boldsymbol{\varepsilon}(x,y,z)\longrightarrow\boldsymbol{\sigma}(x,y,z)\longrightarrow\sigma_{zz}^{*}=1.00003290768\longrightarrow\text{Table 2: }1.0000. $$

This is a direct output comparison.

The Table 2 value is used only as the final reference target and does not enter the construction of the displacement field, the strain field, the stress field, or the algebraic solution.

**Reference check in the paper:** Carrera and Giunta, *Refined Beam Theories Based on a Unified Formulation*, Eq. (6.1) and Table 2, page 130, row `N = 4`.

---

## 12. Relation between the analytical validation and the current runtime solver

The preceding sections validate the generalized CSF-CUF formulation by reducing it to the same prismatic, constant-coefficient and Navier-specialized setting used by Carrera and Giunta. That validation remains useful because it establishes a direct term-by-term correspondence with the published CUF formulation.

The current operational solver retains the same underlying three-dimensional CUF kinematics and the same generalized sectional coefficient family, but its longitudinal computational treatment is formulated directly in weak form.

### 12.1 Generalized sectional coefficient used by the runtime

For a transverse sub-domain indexed by $k$, let:

- $x$ be the longitudinal coordinate;
- $(y,z)$ be the transverse coordinates;
- $\Omega^k(x)$ be the current transverse domain supplied by CSF;
- $C_{mn}^k(x,y,z)$ be one constitutive-matrix component;
- $F_\tau(y,z)$ and $F_s(y,z)$ be CUF transverse approximation functions;
- $\phi,\xi\in\{\varnothing,y,z\}$ identify the transverse derivatives applied to the test and trial functions.

The runtime sectional coefficient is the same generalized quantity introduced in the formal derivation:

$$J_{\tau,\phi s,\xi}^{mn,k}(x) = \int_{\Omega^k(x)} C_{mn}^{k}(x,y,z) F_{\tau,\phi}(y,z) F_{s,\xi}(y,z) \,\mathrm d\Omega.$$

The global coefficient is

$$J_{\tau,\phi s,\xi}^{mn}(x) = \sum_{k=1}^{N_\Omega} J_{\tau,\phi s,\xi}^{mn,k}(x).$$

The runtime evaluates this quantity at the physical longitudinal coordinate requested by the longitudinal integration procedure. The coordinate $x$ is therefore part of the complete physical request: geometry and constitutive properties may change between two integration coordinates.

### 12.2 Weak-form fundamental nucleus

The runtime fundamental nucleus is generated from the complete three-dimensional small-strain kinematics in the Voigt order

$$(\varepsilon_{xx},\varepsilon_{yy},\varepsilon_{zz}, \gamma_{yz},\gamma_{xz},\gamma_{xy}).$$

For one generic term, define:

- $r\in\{0,1\}$ as the longitudinal derivative order acting on the test amplitude;
- $q\in\{0,1\}$ as the longitudinal derivative order acting on the trial amplitude;
- $N_a(x)$ and $N_b(x)$ as longitudinal finite-element shape functions;
- $J(x)$ as the corresponding generalized sectional coefficient selected by the CUF kinematics.

The elemental weak-form contribution has the structure

$$K_{ab}^{(e)} = \int_{x_e^-}^{x_e^+} D_x^rN_a(x)\, J(x)\, D_x^qN_b(x) \,\mathrm dx.$$

The coefficient $J(x)$ remains inside the longitudinal integral. For a variable section, the solver therefore evaluates the current sectional state at each longitudinal quadrature coordinate and obtains the required value of $J(x)$ from that state.

This runtime representation is the computational counterpart of the variable-coefficient divergence-form operators derived in the formal formulation. The analytical strong-form expressions remain useful for interpretation, while the weak form is the implemented solution path.

### 12.3 Longitudinal finite-element representation

Let:

- $n_e$ be the number of longitudinal finite elements;
- $p$ be the polynomial order of each one-dimensional Lagrange element.

For a conforming mesh with equal polynomial order, the number of longitudinal nodes is

$$n_{\mathrm{node}} = n_e\,p + 1.$$

The current double-T validation cases use

$$n_e=1, \; p=6.$$

and therefore

$$n_{\mathrm{node}}=7.$$

The longitudinal integrals are evaluated by Gauss-Legendre quadrature. The current double-T cases use nine longitudinal Gauss points per element.

This choice is independent of the CUF transverse order $N$: the longitudinal finite-element interpolation and the transverse CUF approximation are two distinct approximation levels.

---

## 13. Current transverse CUF basis implementation

### 13.1 Pluggable transverse basis

The runtime selects the transverse approximation through a basis-plugin registry.

The currently validated runtime basis is identified by

```yaml
cuf:
  basis: scaled_maclaurin
```

The symbolic name selects the registered implementation and its numerical integration requirements. The solver engine therefore depends on the generic CUF basis interface rather than on a hard-coded Maclaurin implementation.

### 13.2 Scaled complete Maclaurin basis

For the current validated plugin, define the transverse scales

$$y_{\mathrm{scale}}>0, \; z_{\mathrm{scale}}>0.$$

obtained from the CSF geometry, and the scaled coordinates

$$Y=\frac{y}{y_{\mathrm{scale}}}, \; Z=\frac{z}{z_{\mathrm{scale}}}.$$

For CUF order $N$, the basis contains every monomial

$$Y^pZ^q$$

with

$$p+q\le N.$$

The number $M$ of transverse basis functions is therefore

$$M=\frac{(N+1)(N+2)}{2}.$$

For example, at

$$N=20,$$

the transverse basis contains

$$M=\frac{21\cdot22}{2}=231$$

functions.

The scaling changes the numerical representation of the polynomial basis but preserves the complete polynomial approximation space for a fixed order $N$, because $y_{\mathrm{scale}}$ and $z_{\mathrm{scale}}$ are non-zero constants for the analysis.

### 13.3 Primary displacement DOFs for the current N=20 cases

With:

- $M=231$ transverse functions;
- three displacement components per transverse function;
- seven longitudinal nodes;

the number of primary displacement DOFs is

$$n_{\mathrm{dof}} = 231\cdot3\cdot7 = 4851.$$

Constraint equations are applied separately by the problem layer.

### 13.4 Order-aware section quadrature

The scaled complete Maclaurin plugin declares the minimum section Gauss order required by its approximation space.

For order $N$,

$$n_{\mathrm{Gauss,section}}^{\min}=N+1.$$

If the case requests a section Gauss order $n_{\mathrm{req}}$, the runtime uses

$$n_{\mathrm{eff}}=\max(n_{\mathrm{req}},N+1).$$

For the current $N=20$ double-T cases,

$$n_{\mathrm{req}}=6, \; N+1=21.$$

so that

$$n_{\mathrm{eff}}=21.$$

This rule is associated with the selected basis plugin and is evaluated by the runtime when the case is built.

---

## 14. Completed prismatic validation program

The analytical reconstruction in Sections 2-11 established the first direct Carrera-Giunta validation. The subsequent implementation program extended the verification to the reusable runtime components.

### 14.1 Constitutive and reduced-coefficient verification

The constitutive layer was verified independently from geometry, loads and longitudinal discretization.

For the Carrera-Giunta aluminium parameters

$$E=71700\,\mathrm{MPa}, \; \nu=0.30.$$

the shear modulus is

$$G = \frac{E}{2(1+\nu)} = 27576.9231\,\mathrm{MPa}.$$

The full isotropic three-dimensional constitutive matrix gives

$$C_{11}=C_{22}=C_{33}=96519.2308\,\mathrm{MPa},$$

$$C_{12}=C_{13}=C_{23}=41365.3846\,\mathrm{MPa},$$

and

$$C_{44}=C_{55}=C_{66}=27576.9231\,\mathrm{MPa}.$$

The explicit Schur-complement reduction used by the first-order benchmark gives the reduced axial coefficient

$$Q=E=71700\,\mathrm{MPa}.$$

The reduction was checked both as a direct algebraic operation and through the generic constitutive-provider transformation layer. The stiffness and stress-recovery constitutive roles remain distinct, so a theory-specific reduction can be selected explicitly without changing the generic sectional integration or the CUF nucleus.

### 14.2 Carrera-Giunta Table 2 bending validation

The detailed $N=4$ reconstruction above gives

$$\sigma_{zz}^{*}(a/2) = 1.00003290768$$

against the tabulated target

$$1.0000.$$

The absolute difference is

$$3.290768\times10^{-5}.$$

The extended numerical gate also verified the additional Table 2 quantities required by the benchmark. Representative $N=4$ results include

$$\sigma_{xx}^{*}(0)\approx0.5000000$$

and

$$\sigma_{xx}^{*}(a/2)\approx0.9999945.$$

The Table 2 tests were subsequently repeated for higher CUF orders so that the generalized coefficient generation, basis evaluation and algebraic assembly were exercised beyond the single $N=4$ reconstruction.

### 14.3 Carrera-Giunta Table 7 torsion validation

The torsional rectangular benchmark was used as an independent verification of the complete CUF nucleus.

For the long-beam case $l/a\ge50$, a high-order calculation with

$$N=12$$

gave the nondimensional shear-stress quantity

$$4.806593298$$

against the reference value

$$4.807.$$

For the short case

$$l/a=2,$$

the corresponding calculation gave

$$4.699770286$$

against the reference value

$$4.700.$$

These tests exercise a different coupling pattern from the bending benchmark and provide an independent check of the transverse derivatives and off-diagonal nucleus terms.

### 14.4 Prismatic double-T bending: Table 9

The prismatic double-T geometry from the Carrera-Giunta reference problem was then solved with the runtime CSF-CUF architecture.

For

$$l/a=10$$

and transverse order

$$N=10,$$

the current runtime produced

| Quantity | CSF-CUF $N=10$ | Carrera-Giunta |
|---|---:|---:|
| $10|u_x^*|$ | 4.037848 | 4.038 |
| $10^3|u_y^*|$ | 2.972402 | 2.973 |
| $10^2u_z^*$ | 8.741618 | 8.742 |

The relative differences are approximately

$$-0.00376\%, \; -0.02011\%, \; -0.00437\%.$$

This benchmark is important because the runtime result is obtained through the generic CSF section provider, generic sectional coefficient provider, weak-form CUF nucleus and longitudinal finite-element solver rather than through the Navier algebraic system used in the analytical reconstruction.

### 14.5 Prismatic double-T torsion: Table 10

For the corresponding prismatic torsional benchmark with

$$N=10,$$

the runtime produced

| Quantity | CSF-CUF $N=10$ | Carrera-Giunta |
|---|---:|---:|
| $10|u_x^*|$ | 2.031073 | 2.031 |
| $10|u_y^*|$ | 4.411842 | 4.412 |
| $10^2u_z^*$ | 4.112417 | 4.112 |

The relative differences are approximately

$$+0.00359\%, \; -0.00358\%, \; +0.01014\%.$$

The agreement of both Table 9 and Table 10 establishes that the weak-form longitudinal runtime reproduces the prismatic double-T reference response for both bending and torsion.

---

## 15. Variable-section and variable-material extension

### 15.1 Purpose of the extended test

After the prismatic benchmark recovery, the same double-T model was extended longitudinally while retaining the same generic solver architecture.

The purpose of this test is to exercise the dependency

$$x \longrightarrow \mathcal S(x) \longrightarrow (\Omega^k(x),\mathbf C^k(x,y,z)) \longrightarrow J_{\tau,\phi s,\xi}^{mn}(x).$$

inside the longitudinal numerical integration.

The three-dimensional FEM model is used here as the numerical baseline for the extended variable case. Carrera-Giunta remains the source of the original prismatic benchmark geometry and normalization, while the longitudinally varying geometry/material configuration is the CSF-CUF extension.

### 15.2 Geometry of the tapered test

The reference section at the initial end is retained.

Using the dimensional normalization adopted for the double-T $l/a=10$ benchmark:

$$a=100\,\mathrm{mm},$$

$$b=66.6667\,\mathrm{mm},$$

$$s_1=25\,\mathrm{mm}.$$

$$s_2=25\,\mathrm{mm}.$$

and

$$l=1000\,\mathrm{mm}.$$

At the final section, the clear web height is reduced to

$$20\,\mathrm{mm},$$

corresponding to an $80\%$ reduction from the initial clear web height. The flange thickness remains

$$25\,\mathrm{mm},$$

so the final total outer height is

$$20+25+25=70\,\mathrm{mm}.$$

The CSF representation supplies the intermediate sections continuously along the longitudinal coordinate.

### 15.3 Material evolution

The material carriers are attached to the CSF polygonal domains and vary longitudinally according to the model definition.

The CSF-CUF bridge reads the evaluated normal-stiffness carrier as $E$ and the evaluated shear-stiffness carrier as $G$. The constitutive provider then constructs the local $6\times6$ matrix used by the sectional coefficient integration.

Geometry and constitutive variation therefore enter through the same requested longitudinal coordinate $x$, while the CUF nucleus remains independent of the specific double-T shape.

### 15.4 Common baseline strategy

The same CSF model definition is used to generate the sectional state supplied to the CUF solver and the corresponding geometry/material distribution used for the three-dimensional FEM baseline.

The comparison therefore targets the numerical response of two distinct solution paths applied to the same intended physical configuration:

$$\text{CSF model} \longrightarrow (\text{CSF-CUF weak-form beam solver},\;\text{3D FEM baseline}).$$

The comparison is made using the same Carrera-style nondimensional displacement report used for the prismatic Table 9 and Table 10 cases.

---

## 16. Variable-case Table 9 bending results

### 16.1 CSF-CUF order N=15

For the tapered and variable-material Table 9 case, the $N=15$ calculation gives the global maxima

$$10|u_x^*|=11.121168,$$

$$10^3|u_y^*|=6.075601,$$

and

$$10^2u_z^*=20.508320.$$

The corresponding longitudinal locations are

$$x_{u_x}=565\,\mathrm{mm},$$

$$x_{u_y}=650\,\mathrm{mm},$$

and

$$x_{u_z}=0\,\mathrm{mm}.$$

### 16.2 CSF-CUF order N=20

Increasing the transverse CUF order to

$$N=20$$

gives

$$10|u_x^*|=11.129124,$$

$$10^3|u_y^*|=6.089971,$$

and

$$10^2u_z^*=20.494914.$$

The longitudinal locations of the global maxima remain

$$x_{u_x}=565\,\mathrm{mm}, \; x_{u_y}=650\,\mathrm{mm}, \; x_{u_z}=0\,\mathrm{mm}.$$

### 16.3 Three-dimensional FEM baseline

The corresponding three-dimensional FEM baseline gives

$$10u_x^*=11.129717,$$

$$10^3|u_y^*|=6.135546,$$

and

$$10^2u_z^*=20.549984.$$

The FEM longitudinal locations of the global maxima are approximately

$$x_{u_x}=566.667\,\mathrm{mm},$$

$$x_{u_y}=650\,\mathrm{mm},$$

and

$$x_{u_z}=0\,\mathrm{mm}.$$

### 16.4 Comparison

The global displacement comparison is

| Quantity | CSF-CUF $N=15$ | CSF-CUF $N=20$ | FEM3D baseline |
|---|---:|---:|---:|
| $10|u_x^*|$ | 11.121168 | 11.129124 | 11.129717 |
| $10^3|u_y^*|$ | 6.075601 | 6.089971 | 6.135546 |
| $10^2u_z^*$ | 20.508320 | 20.494914 | 20.549984 |

Relative to FEM3D, the $N=20$ differences are approximately

$$-0.00533\%,$$

$$-0.74280\%,$$

and

$$-0.26798\%.$$

The change from $N=15$ to $N=20$ is already small:

$$+0.0715\%$$

for $10|u_x^*|$,

$$+0.2365\%$$

for $10^3|u_y^*|$, and

$$-0.0654\%$$

for $10^2u_z^*$.

The bending response is therefore already close to its high-order transverse approximation regime by $N=15$-$20$ for this test.

---

## 17. Variable-case Table 10 torsion results

The torsional case is more demanding with respect to the transverse CUF order and therefore provides a useful convergence test.

### 17.1 Earlier N=10 result

The $N=10$ CSF-CUF result gives

$$10|u_x^*|=2.719152,$$

$$10|u_y^*|=4.380481,$$

and

$$10^2u_z^*=4.506256.$$

### 17.2 N=20 result

For

$$N=20,$$

the global maxima become

$$10|u_x^*|=3.094646,$$

$$10|u_y^*|=4.954810,$$

and

$$10^2u_z^*=5.094652.$$

Their longitudinal locations are

$$x_{u_x}=545\,\mathrm{mm},$$

$$x_{u_y}=475\,\mathrm{mm},$$

and

$$x_{u_z}=35\,\mathrm{mm}.$$

### 17.3 Three-dimensional FEM baseline

The FEM3D baseline gives

$$10|u_x^*|=3.257099,$$

$$10|u_y^*|=5.204712,$$

and

$$10^2u_z^*=5.220727.$$

The corresponding FEM longitudinal locations are approximately

$$x_{u_x}=550\,\mathrm{mm},$$

$$x_{u_y}=475\,\mathrm{mm},$$

and

$$x_{u_z}=41.667\,\mathrm{mm}.$$

### 17.4 Convergence toward the FEM3D baseline

The global displacement comparison is

| Quantity | CSF-CUF $N=10$ | CSF-CUF $N=20$ | FEM3D baseline |
|---|---:|---:|---:|
| $10|u_x^*|$ | 2.719152 | 3.094646 | 3.257099 |
| $10|u_y^*|$ | 4.380481 | 4.954810 | 5.204712 |
| $10^2u_z^*$ | 4.506256 | 5.094652 | 5.220727 |

For $N=10$, the relative differences with respect to FEM3D are approximately

$$-16.52\%, \; -15.84\%, \; -13.69\%.$$

For $N=20$, they reduce to approximately

$$-4.99\%, \; -4.80\%, \; -2.41\%.$$

All three global displacement quantities move systematically toward the FEM3D baseline when the transverse order is increased from $N=10$ to $N=20$.

The location of the $u_y$ maximum coincides with the FEM3D baseline at

$$x=475\,\mathrm{mm},$$

while the $u_x$ and $u_z$ maxima are also close in longitudinal position.

---

## 18. Current case organization used by the runtime validation

The operational validation separates the physical model, the physical problem and the numerical solver case.

### 18.1 Model

The model YAML contains the CSF geometry and constitutive carriers.

For the variable double-T case, it defines the longitudinally evolving polygonal geometry and material state.

### 18.2 Problem

The problem YAML selects the physical loading family and references the CSF model.

For the bending case, the problem type is

```yaml
problem:
  type: carrera_bending_bottom_surface_halfwave
  amplitude: 1.0
```

For the torsional case, the problem type is

```yaml
problem:
  type: carrera_torsion_halfwave
  amplitude: 1.0
```

The problem adapter converts these physical problem definitions into the generic load and constraint interface used by the solver.

### 18.3 Numerical case

The case YAML selects the CUF and numerical approximation settings.

A current $N=20$ configuration uses

```yaml
cuf:
  basis: scaled_maclaurin
  order: 20

longitudinal:
  method: finite_element
  elements: 1
  order: 6
  gauss_order: 9

section_integration:
  method: fixed_gauss_polygon
  gauss_order: 6
```

For this case, the scaled-Maclaurin plugin raises the effective section integration order to

$$21.$$

### 18.4 Post-processing

The solved runtime object exposes the continuous displacement field

$$\mathbf u(x,y,z).$$

The Carrera-Giunta post-processing adapter receives this continuous field and produces the Table 9 or Table 10 normalized displacement report.

The post-processing stage therefore performs:

1. component mapping to the Carrera-Giunta convention;
2. nondimensionalization;
3. section extrema search;
4. longitudinal global-extrema search;
5. report generation.

The mechanical solution is already complete when this post-processing begins.

---

## 19. Validation status and demonstrated scope

The combined validation chain now establishes the following sequence.

### 19.1 Formulation-level correspondence

The generalized sectional coefficient family

$$J_{\tau,\phi s,\xi}^{mn}(x)$$

reduces to the Carrera-Giunta sectional momenta and constitutive coefficients for the prismatic homogeneous reference beam.

The complete algebraic nucleus obtained after Navier specialization is mapped term by term to the reference Carrera-Giunta nucleus.

### 19.2 Direct reference-result recovery

The explicit $N=4$ Table 2 displacement/stress reconstruction reproduces the first published nondimensional stress target with an absolute difference of approximately

$$3.29\times10^{-5}.$$

Additional Table 2 and Table 7 gates extend the verification to other stress components, transverse orders and torsional coupling terms.

### 19.3 Independent runtime recovery of prismatic double-T benchmarks

The weak-form longitudinal finite-element runtime reproduces the Carrera-Giunta prismatic double-T Table 9 and Table 10 displacement results at $N=10$ with differences of order $10^{-2}\%$ or smaller for the reported global quantities.

This establishes the connection between the analytical reference validation and the reusable runtime solver.

### 19.4 Longitudinally varying geometry and material

The same runtime architecture is then applied to a double-T member with continuously varying geometry and longitudinally varying constitutive carriers.

The solver obtains the current section and material state through CSF at the longitudinal coordinates requested by the numerical integration. No section-specific stiffness formula is introduced into the generic CUF nucleus.

### 19.5 High-order behavior

For the variable bending case, the $N=15$ and $N=20$ results are already close to each other and to the FEM3D baseline.

For the variable torsion case, the transition from $N=10$ to $N=20$ produces a clear systematic movement toward the FEM3D baseline in all three reported global displacement components.

The demonstrated validation scope therefore includes:

- rectangular prismatic bending;
- rectangular prismatic torsion;
- prismatic double-T bending;
- prismatic double-T torsion;
- longitudinally varying double-T geometry;
- longitudinally varying material stiffness;
- high-order complete Maclaurin transverse expansions;
- generic weak-form longitudinal finite-element solution;
- comparison with both published CUF reference results and an independent three-dimensional FEM baseline.

---

## 20. Reference

The primary CUF benchmark reference used throughout this document is:

E. Carrera and G. Giunta, **"Refined Beam Theories Based on a Unified Formulation"**, *International Journal of Applied Mechanics*, Vol. 2, No. 1 (2010), pp. 117-143.

The analytical validation sections retain the notation and benchmark structure required for direct comparison with that work, while the later runtime sections document the current implemented CSF-CUF architecture and its numerical validation state.
