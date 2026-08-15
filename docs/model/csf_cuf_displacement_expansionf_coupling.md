# DRAFT

> The following material presents the displacement expansion adopted for the CSF–CUF coupling. The CSF sectional representation and the CUF kinematic approximation are kept explicitly distinct: CSF supplies the longitudinally evolving sectional state, while CUF supplies the transverse approximation functions and the associated longitudinal displacement amplitudes.

# CUF displacement expansion for CSF coupling

## Scope

This note isolates the CUF displacement expansion used in the coupling with the Continuous Section Field representation.

The sectional state is supplied independently by CSF through

$$ \mathcal{S}(x) \longrightarrow ( \Omega^k(x), \mathbf{C}^k(x,y,z) ). $$

The present note does not define the sectional geometry or constitutive law. Its purpose is only to define the kinematic approximation of the three-dimensional displacement field that is subsequently evaluated over the section supplied by $\mathcal{S}(x)$.

No longitudinal discretization, numerical integration, load formulation, boundary-condition treatment, or solution procedure is introduced here.

---

## 1. Coordinates

Let:

- $x$ denote the longitudinal coordinate along the beam axis;
- $y$ and $z$ denote the physical transverse coordinates on the cross-section.

At each longitudinal coordinate $x$, the current cross-section is determined by the CSF representation $\mathcal{S}(x)$.

The CUF notation is retained throughout this note.

---

## 2. Three-dimensional displacement field

Let the three-dimensional displacement field be

$$ \mathbf{u}(x,y,z) = \big(u_x(x,y,z), u_y(x,y,z), u_z(x,y,z)\big)^T. $$

where:

- $u_x(x,y,z)$ is the displacement component along the longitudinal direction $x$;
- $u_y(x,y,z)$ is the displacement component along the transverse direction $y$;
- $u_z(x,y,z)$ is the displacement component along the transverse direction $z$.

The displacement field is defined at every point $(y,z)$ belonging to the current cross-section $\Omega(x)$.

---

## 3. CUF transverse approximation

Let $M$ denote the number of transverse approximation terms retained in the CUF expansion.

For each approximation index $\tau$, with

$$ \tau = 1,\ldots,M, $$

let $F_\tau(y,z)$ denote the corresponding CUF transverse approximation function.

The functions $F_\tau(y,z)$ describe the assumed variation of the displacement field over the physical transverse coordinates.

Associated with each $F_\tau(y,z)$ is a vector of longitudinal displacement amplitudes

$$ \mathbf{u}_\tau(x) = \big(u_{x\tau}(x), u_{y\tau}(x), u_{z\tau}(x)\big)^T. $$

where $u_{x\tau}(x)$, $u_{y\tau}(x)$, and $u_{z\tau}(x)$ are unknown functions of the longitudinal coordinate.

The CUF displacement expansion is therefore

$$ \mathbf{u}(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,\mathbf{u}_\tau(x). $$

Equivalently, component by component,

$$ u_x(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,u_{x\tau}(x), $$

$$ u_y(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,u_{y\tau}(x), $$

and

$$ u_z(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,u_{z\tau}(x). $$

---

## 4. Separation between transverse and longitudinal dependence

The CUF expansion separates the transverse dependence from the longitudinal unknowns.

The functions

$$ F_\tau(y,z) $$

carry the transverse approximation, while the vectors

$$ \mathbf{u}_\tau(x) $$

carry the unknown longitudinal amplitudes.

Thus the three-dimensional displacement field is constructed from products of the form

$$ F_\tau(y,z)\,\mathbf{u}_\tau(x). $$

The approximation order and the specific family of functions $F_\tau$ are CUF choices and are not prescribed by CSF.

---

## 5. Relation with the longitudinally varying CSF section

The CSF representation determines the physical sectional state at each longitudinal coordinate:

$$ x \longrightarrow \mathcal{S}(x) \longrightarrow \Omega(x). $$

In the present coupling, the CUF transverse functions are written in the physical transverse coordinates:

$$ F_\tau = F_\tau(y,z). $$

Therefore the longitudinal dependence of the section does not enter the displacement expansion by replacing $F_\tau(y,z)$ with a geometry-specific function.

Instead, at each coordinate $x$, the same transverse approximation structure is evaluated over the current physical domain supplied by CSF:

$$ (y,z)\in\Omega(x). $$

The resulting kinematic statement is

$$ \mathbf{u}(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,\mathbf{u}_\tau(x), \qquad (y,z)\in\Omega(x). $$

Hence the evolving section enters through the domain on which the CUF approximation is evaluated, while the longitudinal unknowns remain the functions $\mathbf{u}_\tau(x)$.

---

## 6. Source and test approximation indices

For the variational formulation, it is useful to distinguish the approximation index associated with the displacement field from the index associated with the virtual displacement field.

Let $s$ denote a source approximation index.

The corresponding displacement contribution is

$$ \mathbf{u}^{(s)}(x,y,z) = F_s(y,z)\,\mathbf{u}_s(x). $$

Let $\tau$ denote a test approximation index.

The corresponding virtual displacement contribution is

$$ \delta\mathbf{u}^{(\tau)}(x,y,z) = F_\tau(y,z)\,\delta\mathbf{u}_\tau(x). $$

The complete displacement and virtual displacement fields are therefore

$$ \mathbf{u}(x,y,z) = \sum_{s=1}^{M} F_s(y,z)\,\mathbf{u}_s(x), $$

and

$$ \delta\mathbf{u}(x,y,z) = \sum_{\tau=1}^{M} F_\tau(y,z)\,\delta\mathbf{u}_\tau(x). $$

This distinction between $s$ and $\tau$ is subsequently used in the construction of the CUF fundamental nucleus.

---

## 7. Transverse derivatives of the approximation functions

The strain field requires transverse derivatives of the CUF approximation functions.

For each approximation function $F_\tau(y,z)$, define its derivative with respect to $y$ as

$$ F_{\tau,y}(y,z) = \partial_y F_\tau(y,z). $$

Similarly, define its derivative with respect to $z$ as

$$ F_{\tau,z}(y,z) = \partial_z F_\tau(y,z). $$

For compact notation, let $\phi$ denote a transverse derivative label.

The label $\phi$ may be $\emptyset$, $y$, or $z$, where $\emptyset$ denotes the absence of a transverse derivative.

Accordingly,

$$ F_{\tau,\emptyset}(y,z) = F_\tau(y,z). $$

The same notation applies to the source approximation functions $F_s(y,z)$.

These functions and their transverse derivatives are supplied by the CUF kinematic approximation, not by CSF.

---

## 8. Boundary between CSF and CUF

The two descriptions remain distinct.

### CSF supplies

$$ \mathcal{S}(x) \longrightarrow ( \Omega^k(x), \mathbf{C}^k(x,y,z) ). $$

### CUF supplies

$$ (F_\tau(y,z), F_{\tau,y}(y,z), F_{\tau,z}(y,z), \mathbf{u}_\tau(x)). $$

The displacement field is therefore a CUF kinematic construction evaluated over the sectional state provided by CSF.

CSF does not determine the CUF approximation functions, and CUF does not replace the CSF sectional representation.

---

## 9. Coupling chain

At the kinematic level, the coupling can be summarized as

$$ \mathcal{S}(x) \longrightarrow \Omega(x), $$

together with

$$ (F_\tau(y,z), \mathbf{u}_\tau(x)) \longrightarrow \mathbf{u}(x,y,z). $$

Combining the two statements gives

$$ \mathcal{S}(x) + (F_\tau,\mathbf{u}_\tau) \longrightarrow \mathbf{u}(x,y,z)\ \text{on}\ \Omega(x). $$

The subsequent strain expansion, sectional integrations, generalized sectional coefficients, and fundamental nuclear operator are separate steps of the CSF–CUF formulation.

---

### References

- G. Giunta, S. Belouettar, E. Carrera, **“Analysis of FGM Beams by Means of Classical and Advanced Theories”**, *Mechanics of Advanced Materials and Structures*, 17 (2010), 622–635.
