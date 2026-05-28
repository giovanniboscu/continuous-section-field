# A Field-Based Framework for the Continuous Modelling of Non-Prismatic Structural Members

## Abstract

Continuous Section Field (CSF) is a field-based computational framework for representing sectional geometry, material participation, and derived section properties as continuous functions along a member axis.  CSF is neither a structural solver nor a geometry kernel; instead, it connects these domains by transforming member-level geometric and material descriptions into continuous section-property fields and station-wise data suitable for beam, tower, bridge, and finite-element workflows.

The central idea of CSF is to treat the cross-section as a field defined
along `z`, rather than as a single isolated object. A user defines polygonal
cross-sections at reference stations, called `S0` and `S1`; CSF interpolates
corresponding polygon vertices to generate intermediate sections and evaluates
properties such as area, centroid, second moments of area, principal inertias,
section moduli, torsional constants, stiffness-weighted quantities, and
mass-related properties at any requested station.

The change of paradigm is the explicit separation between geometry and
sectional participation. Geometry defines where each polygonal region is
located along the member. Two independent longitudinal participation fields
define how much each region contributes: the axial/bending field `w_i(z)` and
the shear/torsion field `shear_w_i(z)`. These fields can represent stiffness
ratios, degraded regions, reinforcement, voids, density-like quantities, or
other user-defined sectional contributions. They may be interpolated from
endpoint values, derived from an isotropic relation, or specified through
custom laws depending on the longitudinal coordinate and on geometric
quantities.

The continuous model can be defined through a Python API or through a
declarative YAML workflow. In the YAML workflow, one file defines the
continuous member and another file defines the requested computations, plots,
inspections, station sampling, and exports. The YAML file does not define a
discrete table of section properties; it defines the geometry and
participation laws from which CSF constructs continuous sectional fields.

Discrete stations are therefore evaluation points of an already defined
continuous field. For example, Gauss-Lobatto stations obtained through yaml and 
API can be used as quadrature-compatible sampling points for downstream beam
formulations, but they do not define the field itself. This distinction allows
CSF to preserve a continuous member representation while generating
solver-facing station-wise data when required. 
---

## 1. Motivation

In current structural analysis practice, the definition of section properties
for non-prismatic members is typically embedded within the solver itself.
Geometry and material participation are not treated as independent fields;
instead, they are collapsed into a discrete table of section properties
evaluated at a fixed set of stations, tied to the solver mesh and conventions.
This coupling makes the sectional model difficult to inspect, reuse, or
transfer across different solvers, and it obscures the distinction between
the continuous physical model and its numerical discretisation.

Many structural and mechanical engineering problems involve members whose
cross-section changes along their length: tapered towers, variable-depth
beams, haunched bridge girders, repaired or degraded members, hybrid material
sections, and staged or homogenized structural models. In these cases, the
required input for a numerical model is not a single section, but a
longitudinal field of section properties such as $A(z)$, $I_x(z)$, $I_y(z)$,
$EI_x(z)$, $GJ(z)$, and mass-related quantities. When this field is defined
inside the solver, it cannot be validated, inspected, or reused independently.

CSF addresses this by extracting the sectional field definition into a
dedicated pre-solver layer. A member is represented as a continuous sectional
field composed of evolving polygonal geometry, axial/bending participation
$w_i(z)$, and shear/torsion participation $\kappa_i(z)$. This representation
is defined, evaluated, inspected, and validated independently of any
downstream solver. The solver receives a station-wise projection of an
already defined continuous field - not a table that defines the model itself.

The result is a clean separation between three concerns that are normally
conflated: the continuous physical model of the member, the numerical
sampling strategy required by the solver, and the exported data format
consumed by a specific tool.

Cross-section analysis tools such as VABS [REF] and BECAS [REF] provide accurate computation of beam sectional properties for arbitrary geometries and composite materials, and are widely adopted in wind-turbine and aerospace applications. Open-source alternatives such as `sectionproperties` [REF] offer similar capabilities within a Python ecosystem. These tools are primarily designed to analyse individual cross-sections: given a sectional geometry and material definition, they return the corresponding sectional properties at that station.

The longitudinal variation of the member - including tapering geometry, spatially varying material participation, or local stiffness degradation - is therefore usually represented outside the section-analysis tool, either through user-defined station tables or through the discretization adopted by the downstream structural solver. As a consequence, the sectional description is often tied to a specific mesh or analysis workflow, rather than being defined as an independent continuous model.

On the theoretical side, Balduzzi et al. [Balduzzi 2016] showed that non-prismatic beam analysis requires careful treatment of continuously varying cross-sectional quantities along the member axis. This highlights the need for programmable descriptions capable of providing consistent geometric and constitutive quantities at arbitrary axial locations.

CSF addresses this level of the workflow. It defines a continuous geometric and material participation field along the member axis, from which sectional properties can be sampled, exported, or passed to downstream beam and finite-element models. Detailed section analysis can still be delegated to tools such as `sectionproperties` when required. The two layers are therefore complementary: section-analysis tools compute the properties of a section, whereas CSF defines how the section and its participating materials vary continuously along the member. To the authors’ knowledge, existing tools do not formalise the continuous sectional field as an independent, solver-agnostic layer. Longitudinal variation is typically handled within specific solvers or beam formulations, rather than as a standalone pre-processing concern. This distinction is illustrated by the NREL 5-MW reference case considered here. The tower is based on a linearly tapered circular tube, with sectional properties evaluated analytically at 11 discrete stations. It therefore represents a minimal reference case: the geometry admits closed-form sectional properties, the material is uniform, and the longitudinal variation can be tabulated directly. CSF recovers this case as a degenerate instance of a continuous sectional field, while extending the same workflow to cases where closed-form sectional properties are not available.

---

## 2. The CSF Section Model

### 2.1 scope

In a standard beam model, section properties are expressed as a separable
product of a material function and a geometric constant:

$$EA(z) = E(z)\cdot A, \qquad EI(z) = E(z)\cdot I, \qquad GJ(z) = G(z)\cdot J$$

This formulation is adequate for prismatic members with a single homogeneous
material. It breaks down when the section is tapered, composed of multiple
materials, locally degraded, or any combination of these, because geometry
and material participation can no longer be described by a single shared
function.

CSF addresses the general case through an organisational model in which
geometry and material participation are treated as fully independent fields
along the longitudinal axis $z$, and every zone carries its own weight law
independently of all others.

### 2.2 Zone-based continuous formulation

The cross-section at station $z$ is represented as an ordered set of $n$
polygonal zones:

$$S(z) = \{\,\Omega_i(z),\; w_i(z),\; \kappa_i(z)\,\}_{i=1}^{n}$$

where:

- $\Omega_i(z)$ is the polygonal domain of zone $i$ at station $z$;
- $w_i(z)$ is the axial and bending participation weight of zone $i$;
- $\kappa_i(z)$ is the shear and torsion participation weight of zone $i$.

Any section property that can be expressed as an area integral is evaluated
as a weighted sum over the zones:

$$P(z) = \sum_{i=1}^{n} w_i(z) \iint_{\Omega_i(z)} f(x,y,z)\,\mathrm{d}A$$

where $f(x,y,z)$ is the integrand corresponding to the property of interest
(unity for area, $y^2$ for the second moment of area about the $x$-axis,
and so on). Geometry $\Omega_i$ and material weight $w_i$ are fully decoupled:
one can vary independently of the other. For polygonal domains, the area integrals in the above expression are evaluated exactly via Green's theorem, reducing each double integral to a closed-form sum over the polygon edges. No numerical quadrature is required; the result is exact for the given polygonal geometry.

The standard separable formulation is recovered as the special case in which
all zones share the same weight law: $w_i(z) = w(z)$ for all $i$.

For isotropic materials the two participation fields are linked by:

$$\kappa_i(z) = \frac{w_i(z)}{2(1+\nu)}$$

and can be specified through the `iso(nu)` shortcut. In the general case
$w_i(z)$ and $\kappa_i(z)$ are assigned independently, allowing the model
to represent non-isotropic participation, selective stiffness degradation,
or hybrid material compositions.

### 2.3 Geometric field

The user defines each polygonal zone by its vertex coordinates at two
reference stations $z_0$ and $z_1$. CSF generates the geometric field by
linear interpolation of corresponding vertices:

$$\mathbf{v}_{i,k}(z) = \mathbf{v}_{i,k}^{(0)} + \frac{z - z_0}{z_1 - z_0}
\bigl(\mathbf{v}_{i,k}^{(1)} - \mathbf{v}_{i,k}^{(0)}\bigr)$$

where superscripts $(0)$ and $(1)$ denote the values at $z_0$ and $z_1$
respectively, and $k$ indexes the vertices of zone $i$.
This produces a smooth tapered geometry at any intermediate station.
Multiple interpolation intervals can be composed in sequence to represent
members with piecewise-varying cross-sectional evolution.

### 2.4 Participation fields

The weight laws $w_i(z)$ and $\kappa_i(z)$ are user-defined functions of
the longitudinal coordinate. Supported forms include polynomials,
exponentials, piecewise-linear laws, and discrete lookup tables. The only
requirement is that the function be evaluable at any requested station.

### 2.5 Assumptions

| | Assumption | Implication |
|---|---|---|
| A | Fixed topology | Vertex count per zone is constant along $z$; zones whose boundaries appear or disappear are not supported within a single interval |
| B | Linear vertex interpolation | Zone geometry varies linearly between the two reference stations |
| C | Polygonal representation | Curved boundaries must be approximated by polygon discretisation |
| D | Straight element axis | CSF models a single element along a straight $z$-axis; curved members are not supported |

Multiple straight elements can be composed in sequence - each with its own
geometry and participation fields - to represent members of arbitrary length
and cross-sectional evolution.

### 2.6 Relation to existing tools and structural limitations


Most section properties evaluated by CSF follow directly from the weighted
area-integral formulation of Section 2.2. The Saint-Venant torsional constant
$J_\mathrm{sv}$ is the one exception: it depends on the full geometry of the
section through a warping problem and cannot be obtained from a direct area
integral.

CSF provides an internal approximation of $J_\mathrm{sv}$ when the user
explicitly tags polygons as closed cells (`@cell`) or open thin walls
(`@wall`). Untagged polygons do not contribute to the torsional constant.
For each category, CSF computes and reports the contributions independently:

$$J_\mathrm{sv,cell} = \sum_k \frac{4 A_{m,k}^2\, t_k}{b_{m,k}}, \qquad
J_\mathrm{sv,wall} = \sum_i \frac{b_i\, t_i^3}{3}$$

where the first term applies the Bredt formula to each closed cell using
mean area and perimeter quantities, and the second term sums the thin-wall
contribution of each open wall. The two quantities are presented separately
so that the user can inspect the relative weight of each contribution and
verify that each component is physically meaningful. Their combination is
left to the user and is valid only under the following hypotheses: cells and
walls do not share closed contours, all components have the same unit twist,
open walls have free ends, and thin-wall assumptions hold throughout.

Beyond these hypotheses - thick-walled sections, multi-cell configurations
with shared walls, or open walls physically connected to a cell boundary -
the internal CSF approximation is no longer valid. In those cases CSF must
export the polygonal geometry at the required stations to a finite-element
section solver such as `sectionproperties` for a full Saint-Venant warping
analysis.

More broadly, CSF is not a section-analysis tool and does not replace
finite-element section solvers. Its role is to provide a continuous,
evaluable geometric and participation field. Where the properties computed
directly by CSF are sufficient, as in many practical beam and tower models,
no external solver is required. Where they are not, the continuous geometric
field serves as the input to a more detailed analysis, with the station
sampling fully controlled by the user.

---

## 3. Declarative numerical workflow

CSF can be used as a Python library or through a file-based YAML workflow.
The YAML workflow separates the continuous member definition from the
requested numerical actions.

The geometry file defines:

- pairs of reference stations defining one or more longitudinal interpolation
  intervals;
- polygonal regions;
- vertex coordinates;
- endpoint participation values;
- longitudinal laws for `w_i(z)` and `shear_w_i(z)`.

The action file defines:

- station sets;
- plots;
- section inspections;
- property evaluations;
- exports;
- validation-oriented outputs.

This separation makes the same continuous model reusable across different
numerical studies. A single member definition can be sampled at dense
stations for inspection, at Gauss-Lobatto stations for quadrature-compatible
beam input, or at user-defined stations for comparison with external data.

---

Interoperability with sectionproperties is provided through two companion modules, csf_sp and sp_csf, available as both Python API and CLI tools. csf_sp exports polygonal geometry at requested stations to sectionproperties for full warping analysis. sp_csf performs the inverse operation, importing single geometries from sectionproperties into CSF, enabling the definition of members with geometrically distinct S0 and S1 cross-sections

## 4. Station-wise evaluation and solver-facing output

A central feature of CSF is that station-wise data are generated from the
continuous field. The user may request properties at arbitrary stations,
including uniformly spaced stations, manually defined stations, or
integration-compatible points.

For example, a beam formulation may require section properties at
Gauss-Lobatto points. CSF can evaluate the continuous field directly at
those points and export the corresponding values. The sampling strategy is
therefore tied to the downstream numerical method, while the underlying
member model remains unchanged.

This provides a clean distinction between:

- the continuous sectional model;
- the station set used for numerical evaluation;
- the exported table consumed by an external solver.

For many practical cases the properties computed directly by CSF are
sufficient for downstream beam-level simulations. Where detailed section
analysis is required, the polygonal geometry evaluated at any station can
be passed to an external finite-element section solver such as
`sectionproperties`. CSF and section solvers are therefore complementary
layers in a pre-processing pipeline, each operating at its own level of
abstraction.

---

## 5. Validation strategy

The validation of CSF should be framed as validation of the field formulation
and of its numerical implementation. Suitable validation cases include:

- analytical sections with known area, centroid, inertia, and torsional
  quantities;
- non-prismatic members with predictable geometric evolution;
- hollow or nested sections with known reference behaviour;
- multi-region sections with independent participation fields;
- comparisons with finite-element section analysis at selected stations;
- convergence checks under station refinement or mesh refinement where
  applicable.

The validation should show that CSF correctly constructs the continuous
geometric field, evaluates the participation laws consistently, and produces
station-wise sectional quantities compatible with independent analytical or
numerical references.

---

## 6. Application examples

Representative applications should demonstrate the modelling level targeted
by CSF:

- tapered members with continuously varying sectional geometry;
- members with longitudinal stiffness degradation;
- hybrid or multi-region sections with different participation laws;
- tower-like members requiring distributed section-property tables;
- cases where axial/bending and shear/torsion participation are
  intentionally different.

The examples should emphasize that the same declarative model can generate
different station-wise projections depending on the target numerical workflow.

---

## 7. Research contribution

The main contribution of CSF is the extraction of the sectional field
definition from the solver into an independent, declarative pre-solver layer.
In conventional practice, the mapping from member geometry and material
participation to section properties is embedded within the numerical solver
and is therefore inseparable from its mesh, conventions, and output format.
CSF makes this mapping explicit, continuous, and solver-agnostic.

The framework represents a beam-like member as a coupled set of longitudinal
fields - evolving polygonal geometry, axial/bending participation $w_i(z)$,
and shear/torsion participation $\kappa_i(z)$ - that are defined and
evaluated independently of any downstream solver. Station-wise data are a
projection of this continuous model, not its definition. The same member
description can therefore be sampled at different station sets, validated
against analytical references, and exported to different solvers without
modifying the underlying model.

The continuous geometric field provided by CSF is designed to interface with
external section-analysis solvers when detailed sectional properties are
required. For many practical cases the properties computed directly by CSF
are sufficient for downstream beam-level simulations. Where additional detail
is needed, evaluating the field at any required set of stations - for example
Gauss-Lobatto points - and passing the resulting polygonal geometry to a tool
such as `sectionproperties` is a natural extension of the workflow. CSF and
section solvers are therefore complementary layers in a pre-processing
pipeline, each operating at its own level of abstraction.

The contribution is the formulation of this pre-solver layer and its
declarative implementation as a reusable computational framework for
beam-like structural members with varying geometry and material participation.

---

## Acknowledgements

The author thanks the developers of `sectionproperties` for providing an
open finite-element section-analysis ecosystem that can be used in validation
and interoperability workflows.

---

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work, the author used ChatGPT and Claude for
drafting assistance, copy-editing, and code-review suggestions. After using
these tools, the author reviewed, edited, and validated the content as needed
and takes full responsibility for the scientific claims, software
implementation, and manuscript.
