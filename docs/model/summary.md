Draft v2.2
# A Field-Based Framework for the Continuous Modelling of Non-Prismatic Structural Members

## Abstract

Continuous Section Field (CSF) is a dedicated pre-solver layer for representing sectional geometry, material participation, and derived section properties as continuous functions along a member axis. CSF is neither a structural solver nor a geometry kernel; instead, it transforms member-level geometric and material descriptions into continuous section-property fields and station-wise data suitable for beam, tower, bridge, and finite-element workflows.

The central idea of CSF is to treat the cross-section as a field defined along the member axis, rather than as a single isolated object. The geometry is specified at reference stations and obtained by interpolating corresponding polygon vertices between them, producing continuous intermediate cross-sections. Material participation, by contrast, is not interpolated between stations but prescribed as a continuous longitudinal field along the member axis. At any requested station, CSF combines the interpolated geometry with the participation fields to evaluate properties such as area, centroid, second moments of area, principal inertias and section moduli.

CSF makes an explicit separation between the geometric description of the member and the sectional participation fields that govern its mechanical contribution. Two longitudinal material participation fields define how much each region contributes: the axial/bending field $w_i(z)$ and the shear/torsion field $\kappa_i(z)$. Their independence is foundational to CSF: the model imposes no relation between the two, so each field can be specified on its own. These fields can represent stiffness ratios, degraded regions, reinforcement, voids, density-like quantities, or other user-defined sectional contributions. When both derive from elastic behaviour, they may optionally be coupled through an isotropic relation while still varying along the longitudinal coordinate.

The continuous model can be defined through a Python API or through a declarative YAML workflow. In the YAML workflow, one file defines the continuous member and another file defines the requested computations, plots, inspections, station sampling, and exports. The YAML file does not define a discrete table of section properties; it defines the geometry and the participation fields from which CSF constructs the continuous section-property fields.

This distinction allows CSF to preserve a continuous member representation while generating solver-facing station-wise data when required.

## 1. Motivation

In current structural analysis practice, the definition of section properties for non-prismatic members is typically embedded within the solver itself. Geometry and material participation are not treated as independent fields; instead, they are collapsed into a discrete table of section properties evaluated at a fixed set of stations, tied to the solver mesh and conventions. This coupling makes the sectional model difficult to inspect, reuse, or transfer across different solvers, and it obscures the distinction between the continuous physical model and its numerical discretisation.

Many structural and mechanical engineering problems involve members whose cross-section changes along their length: tapered towers, variable-depth beams, haunched bridge girders, repaired or degraded members, hybrid material sections, and staged or homogenized structural models. In these cases, the required input for a numerical model is not a single section, but a longitudinal field of section properties such as:

<p align="center">
$$
A(z)
$$

$$
I_x(z)
$$

$$
I_y(z)
$$
  
$$
(EI_x)(z)
$$

$$
(GJ)(z)
$$

$$
and other mass-related fields
$$
</p>
A member is represented as a continuous sectional field composed of evolving polygonal geometry together with two material participation fields: the axial/bending field $w_i(z)$ and the shear/torsion field $\kappa_i(z)$. This representation is defined, evaluated, inspected, and validated independently of any downstream solver. The solver receives a station-wise projection of an already defined continuous field - not a table that defines the model itself.

The result is a clean separation between three concerns that are normally conflated: the continuous physical model of the member, the numerical sampling strategy required by the solver, and the exported data format consumed by a specific tool.

Cross-section analysis tools such as [VABS](#VABS) and [BECAS](#becas) provide accurate computation of beam sectional properties for arbitrary geometries and composite materials, and are widely adopted in wind-turbine and aerospace applications. Open-source alternatives such as  [sectionproperties](#SEC_PROP) offer similar capabilities within a Python ecosystem. These tools are primarily designed to analyse individual cross-sections: given a sectional geometry and material definition, they return the corresponding sectional properties at that station.

The longitudinal variation of the member - including tapering geometry, spatially varying material participation, or local stiffness degradation - is therefore usually represented outside the section-analysis tool, either through user-defined station tables or through the discretization adopted by the downstream structural solver. As a consequence, the sectional description is often tied to a specific mesh or analysis workflow, rather than being defined as an independent continuous model.

On the theoretical side,  [Balduzzi](#Balduzzi-2016) showed that non-prismatic beam analysis requires the axial derivatives of cross-sectional quantities, such as $\frac{dA}{dz}$ and $\frac{dI}{dz}$, as explicit terms in the governing equations. The formulation therefore depends on continuous sectional functions, not solely on values evaluated at discrete stations. This highlights the need for programmable descriptions capable of generating consistent geometric and constitutive quantities, and their axial variation, at arbitrary locations along the member axis.

Existing frameworks for the analysis of non-prismatic members can be grouped into three categories. First, sectional analysis tools such as VABS, BECAS, and `sectionproperties` compute the properties of individual cross-sections with high accuracy, while the longitudinal variation of the member is handled externally. Second, structural solvers such as [OpenSees](#OPENSEES), [ABAQUS](#ABAQUS), and [ANSYS](#ANSYS) incorporate non-prismaticity through the adopted finite-element formulation, typically by evaluating sectional properties at nodes, integration points, or user-defined stations. 


Third, wind-energy simulation and design workflows embed non-prismaticity in application-specific representations. Aeroelastic codes such as BeamDyn [wang](#wang)  rely on distributed sectional-property tables along the member axis, whereas systems-engineering tools such as [NREL's WISDEM](#wisdem)  represent the tower as a tapered circular tube with closed-form sectional properties, analysed through the external frame finite-element code Frame3DD [Gavin](#gavin). In both cases the longitudinal variation is bound to a specific geometry or workflow rather than expressed as an independent, reusable sectional field.


To the authors' knowledge, the continuous representation of a member as a solver-agnostic sectional-property field is generally not formalised as an independent modelling layer. Existing approaches typically embed longitudinal variation within section-analysis tools, structural solvers, or application-specific workflows, rather than representing it as an explicit reusable field.

The lack of established continuous sectional-field tools is both a limitation and a motivation: it makes direct tool-to-tool benchmarking difficult, but it also defines the methodological gap addressed by CSF.

---

## 2. The CSF Section Model

### 2.1 Scope

Standard beam workflows often describe sectional stiffness through a single material variation applied to a fixed geometric section. This is insufficient for tapered, composite, or locally degraded members, where geometry and material participation may vary independently along the axis. CSF represents this case by assigning independent geometric and participation fields to each zone of the section.

### 2.2 Zone-based continuous formulation

The cross-section at station $z$ is represented as an ordered set of $n$ polygonal zones:

$$
S(z) = \{\,\Omega_i(z),\; w_i(z),\; \kappa_i(z)\,\}_{i=1}^{n}
$$

where:

- $\Omega_i(z)$ is the polygonal domain of zone $i$ at station $z$;
- $w_i(z)$ is the axial/bending field of zone $i$ (its participation in axial and bending stiffness);
- $\kappa_i(z)$ is the shear/torsion field of zone $i$ (its participation in shear and torsion).

Collectively, $w_i(z)$ and $\kappa_i(z)$ are the participation fields.

Any section property that can be expressed as an area integral is evaluated as a weighted sum over the zones:

$$
P(z) = \sum_{i=1}^{n} w_i(z)
\iint_{\Omega_i(z)} f(x,y)\,\mathrm{d}A
$$

where $f(x,y)$ is the integrand corresponding to the property of interest (unity for area, $y^2$ for the second moment of area about the $x$-axis, and so on). Geometry $\Omega_i$ and the axial/bending field $w_i$ are fully decoupled: one can vary independently of the other.

For polygonal domains, the area integrals are evaluated exactly via Green's theorem, reducing each double integral to a closed-form sum over the polygon edges. This applies to all integrals whose spatial integrands $f(x,y)$ are polynomial in $x$ and $y$ - area, first moments ($Q_x$, $Q_y$), second moments ($I_x$, $I_y$), and product of inertia ($I_{xy}$). The participation fields $w_i(z)$ and $\kappa_i(z)$ depend on $z$ only, not on $x$ and $y$; they factor out of the area integral as station-wise scalars, so the spatial integration remains polynomial at each fixed $z$ and the spatial integrals remain closed-form polygonal quantities.

The standard separable formulation is recovered as the special case in which the axial/bending field is uniform across zones:

$$
w_i(z) = w(z)
\qquad \forall i .
$$

For isotropic materials, when the axial/bending field $w_i(z)$ represents a Young's-modulus quantity, the shear/torsion field follows from the isotropic shortcut

$$
\kappa_i(z) = \frac{w_i(z)}{2(1+\nu)} ,
$$

parametrised by the Poisson ratio $\nu$. This shortcut fixes only the ratio $\kappa_i/w_i = G/E$; it does not constrain the absolute scale of the fields. In the general case $w_i(z)$ and $\kappa_i(z)$ are assigned independently, allowing the model to represent non-isotropic participation, selective stiffness degradation, or hybrid material compositions.

When the participation fields are constant and the vertex coordinates are interpolated linearly between reference stations, the resulting sectional quantities are not arbitrary interpolants. The geometric quantities

$$
A(z), \quad Q(z), \quad I(z)
$$

are polynomial functions of the axial coordinate $z$. Centroidal quantities such as

$$
I_x^c(z), \quad I_y^c(z), \quad I_{xy}^c(z)
$$

generally become rational functions, because they depend on the section centroid. For example,

$$
I_x^c(z) = I_x(z) - A(z)\,\bar{y}(z)^2 ,
\qquad
\bar{y}(z) = \frac{Q_x(z)}{A(z)} .
$$

Once the participation fields are introduced, the sectional laws are the composition of geometric variation and participation variation. A generic sectional quantity can be written as

$$
P(z) = \sum_i w_i(z)\,P_i^{\mathrm{geom}}(z),
$$

where $P_i^{\mathrm{geom}}(z)$ denotes the geometric contribution associated with zone $i$.

The longitudinal variation therefore arises from two independent mechanisms:

1. the geometric evolution of the polygonal domains $\Omega_i(z)$, which generates polynomial or rational sectional quantities under linear vertex interpolation;
2. the participation fields $w_i(z)$ and $\kappa_i(z)$, which may follow arbitrary user-defined functions of the axial coordinate.

The resulting sectional field is obtained through the composition of these two contributions.

CSF does not prescribe or perform axial integration of these functions; it provides an evaluable continuous field. Any integration or discretisation along the member axis must therefore be driven by the downstream workflow - for example through uniform sampling, Gauss-Lobatto stations, solver integration points, or dense reference grids.

For all quantities that can be expressed as weighted area integrals, the combination of polygonal geometry and participation fields yields a direct closed-form evaluation at any station, without numerical quadrature in the cross-sectional plane.

The Saint-Venant torsional constant is a notable exception. Area-integral properties are separable - geometry and participation factor cleanly - but Saint-Venant torsion is not: the torsional constant cannot be reduced to a weighted area integral, because the warping field couples geometry and material across the section. CSF therefore treats torsion separately [saint_ven](#SAINT_VEN). For sections tagged as closed cells or open thin walls, CSF evaluates an internal geometric torsional constant from thin-walled approximations (the Bredt formula for closed cells and the $b\,t^3/3$ estimate for open walls), and the shear/torsion participation enters as a single section-level value rather than zone by zone. For general solid sections, multi-cell configurations, connected cell–wall systems, or cases requiring higher accuracy, the continuous geometric field can be passed to `sectionproperties` through the CSF bridge [csf_sp](#CSF_SP) for a full warping analysis, while retaining the same continuous geometric and participation-field description.

---

### 2.3 Geometric field

The user defines each polygonal zone by its vertex coordinates at two reference stations $z_0$ and $z_1$. CSF generates the geometric field by linear interpolation of corresponding vertices:

$$
\mathbf{v}_{i,k}(z) = \mathbf{v}_{i,k}^{(0)} + \frac{z - z_0}{z_1 - z_0}
\bigl(\mathbf{v}_{i,k}^{(1)} - \mathbf{v}_{i,k}^{(0)}\bigr)
$$

where superscripts $(0)$ and $(1)$ denote the values at $z_0$ and $z_1$ respectively, and $k$ indexes the vertices of zone $i$. This produces a continuous, linearly tapered geometry at any intermediate station. Multiple interpolation intervals can be composed in sequence through a CSF module. Each interval is instantiated as an independent CSF object with its own reference stations, zone geometry, and participation fields; CSFStack concatenates them along the member axis, preserving continuity of the section-property field at the junctions. The resulting stack represents members of arbitrary length with piecewise-varying cross-sectional evolution, while each segment retains the same closed-form polygonal evaluation.

### 2.4 Participation fields

The participation fields $w_i(z)$ and $\kappa_i(z)$ are user-defined functions of the longitudinal coordinate (or, for $\kappa_i$, obtained from $w_i$ through the isotropic relation of §2.2). Supported forms include polynomials, exponentials, piecewise-linear laws, and discrete lookup tables. The only requirement is that the function be evaluable at any requested station.

### 2.5 Assumptions

| | Assumption | Implication |
|---|---|---|
| A | Fixed topology | Vertex count per zone is constant along $z$; zones whose boundaries appear or disappear are not supported within a single interval |
| B | Linear vertex interpolation | Zone geometry varies linearly between the two reference stations |
| C | Polygonal representation | Curved boundaries must be approximated by polygon discretisation |
| D | Straight element axis | CSF models a single element along a straight $z$-axis; curved members are not supported |

Multiple straight elements can be composed in sequence - each with its own geometry and participation fields - to represent members of arbitrary length and cross-sectional evolution.

---

## 3. Declarative numerical workflow

CSF can be used as a Python library or through a file-based YAML workflow. The YAML workflow separates the continuous member definition from the requested numerical actions.

The geometry file defines:

- pairs of reference stations defining one or more longitudinal interpolation intervals;
- polygonal regions;
- vertex coordinates;
- endpoint values of the participation fields;
- longitudinal laws for $w_i(z)$ and $\kappa_i(z)$.

The action file defines:

- station sets;
- plots;
- section inspections;
- property evaluations;
- exports;
- validation-oriented outputs.

This separation makes the same continuous model reusable across different numerical studies. A single member definition can be sampled at dense stations for inspection, at Gauss-Lobatto stations for quadrature-compatible beam input, or at user-defined stations for comparison with external data.


### 3.1 Implementation structure

CSF is implemented as a Python module organized around two main abstractions. `ContinuousSectionField` represents a single interpolation interval between two reference stations, while `CSFStack` concatenates multiple intervals into a piecewise-continuous member representation. The geometric field is generated by linear interpolation of corresponding polygon vertices, whereas the participation fields are provided as user-defined functions of the axial coordinate. Interoperability with external workflows is provided through YAML export and dedicated bridges, including `csf_sp` and `sp_csf`.

### 3.2 Geometry file

The geometry file defines the continuous sectional model. The example below describes a tapered polygonal section between two reference stations. The cross-section tapers from `S0` to `S1`, while the axial/bending field follows a parabolic law along the member axis.

```yaml
CSF:
  weight_laws:
    # parabolic increase: 72% at base (z=0), full section at top (z=5)
    - 'tower_wall,tower_wall: 1.0 - 0.28 * (1 - (z / 5.0)**2)'

  shear_weight_laws:
    - 'iso(0.3)'

  sections:
    S0:
      z: 0.0
      polygons:
        tower_wall:
          weight: 210000000000
          vertices:
            - [ 3.000,  0.000]
            - [ 0.000,  3.000]
            - [-3.000,  0.000]
            - [ 0.000, -3.000]

    S1:
      z: 5.0
      polygons:
        tower_wall:
          weight: 210000000000
          vertices:
            - [ 1.935,  0.000]
            - [ 0.000,  1.935]
            - [-1.935,  0.000]
            - [ 0.000, -1.935]
```

The example separates three ingredients that are often collapsed into a single tabulated section-property description: the reference geometry, the longitudinal geometric interpolation, and the material participation law. Changing the station set or the requested output does not require modifying this member definition.

### 3.3 Action file

The action file specifies how the continuous model is sampled and which quantities are extracted. It does not redefine the member geometry.

```yaml
CSF_ACTIONS:
  stations:
    station_edge: [0,5]
  actions:
    - plot_volume_3d:
        params:
          title: "Non-prismatic member"         
    - section_selected_analysis:
        stations: [station_edge]
        output:
          - [stdout,section_selected_analysis.txt]
        params:
          fmt_display: ".10g"
        properties: [A, Cx, Cy, Ix, Iy, Ixy, Ip,I1, I2, rx, ry, Wx,            
                     Wy, J_sv_wall,Q_na, J_s_vroark, J_s_vroark_fidelity]
```

The same geometry file can therefore support visual inspection, property evaluation, solver export, or validation-oriented sampling. In each case the continuous field is evaluated at the stations requested by the action file.

### 3.4 Reusability across studies

The decoupling between the member definition and the numerical operations applied to it is the principal design choice of the YAML workflow. The following table illustrates three typical uses of the same geometry file.

| Study | Station set | Purpose |
|---|---|---|
| Visual inspection | Dense uniform grid (100+ stations) | Section plots, centroid locus |
| Beam model input | 11 Gauss-Lobatto stations | OpenSees / BeamDyn tables |
| Reference comparison | Stations from external dataset | Validation against tabulated data |

In all cases the continuous geometric field is evaluated on demand; no re-meshing or re-definition of the member is required.

### 3.5 Interoperability with `sectionproperties`

Interoperability with `sectionproperties` is provided through two companion modules, [csf_sp](#CSF_SP) and [sp_csf](#SP_CSF), available as both Python API and CLI tools. `csf_sp` exports polygonal geometry at requested stations to `sectionproperties` for full warping analysis. `sp_csf` performs the inverse operation, importing individual section geometries from `sectionproperties` into CSF, enabling the definition of members with geometrically distinct `S0` and `S1` cross-sections. For torsional analyses, CSF supplies the shear/torsion participation field $\kappa_i(z)$ to the station-level analysis, so that the torsional response is evaluated using the appropriate shear-modulus quantity rather than the axial/bending participation field $w_i(z)$.


---

## 4. Station-wise evaluation and solver-facing output


A central feature of CSF is that solver-facing data are generated from the continuous field. The user may request properties at arbitrary axial locations, including uniformly spaced stations, manually defined stations, or integration-compatible points.

For example, a beam formulation may require section properties at Gauss-Lobatto points. CSF evaluates the continuous field directly at those points and exports the corresponding values. The sampling strategy is therefore tied to the downstream numerical method, while the underlying member model remains unchanged.

This provides a clean distinction between:

- the continuous sectional model;
- the station set used for numerical evaluation;
- the exported table consumed by an external solver.

Where the properties computed directly by CSF are sufficient, the sampled field can be exported directly to downstream beam-level models. Where additional section analysis is required, the polygonal geometry evaluated at any station can be passed to an external section solver. CSF and section solvers are therefore complementary layers in the same pre-processing pipeline.

---

## 5. Application examples

### 5.1 NREL 5-MW reference tower

#### Overview

The NREL 5-MW reference wind turbine tower [Jonkman et al. 2009] is used as
the application case. The verification has two objectives: first, to compare
the sectional properties generated by CSF with the analytical NREL reference
values for the linearly tapered circular tube; second, to assess the
structural response obtained from the CSF-generated beam model. The response
quantities considered are the tower-head transverse displacement $U_y$ and
the torsional rotation $R_z$.

The tower is a linearly tapered circular steel tube, 87.6 m tall, with outer
diameter tapering from 6.0 m at the base to 3.87 m at the top and wall
thickness from 0.027 m to 0.019 m. Material properties are uniform:
$E = 210$ GPa, $G = 80.8$ GPa, effective density $\rho = 8500$ kg/m$^3$.

Two configurations are analysed:

- **Case A**: the undegraded tower, representing a smooth reference case in
  which sectional stiffness varies regularly along the height.
- **Case B**: the same tower with a localized longitudinal stiffness
  degradation introduced through the participation field $w_i(z)$, leaving
  the polygonal geometry unchanged.

Both configurations are defined in a single YAML geometry file. Only the
weight law differs between the two cases.

#### Validation design

The validation compares two independent computational paths that share the same YAML input:

```text
Path 1:  YAML → CSF sectional properties → OpenSees beam model → tip response
Path 2:  YAML → CSF continuous field → dense numerical integration → reference response
```

Path 1 samples the continuous stiffness field at a finite number of stations, transfers the resulting sectional properties to an OpenSees beam model, and computes the structural response. Path 2 evaluates the same continuous field through high-resolution numerical integration over 2001 axial points, independently of any beam implementation.

The use of two independent computational procedures provides a more robust validation basis than comparing outputs generated by the same numerical backend, since the two paths differ both in discretization strategy and in their computational implementation.

The key response quantities are the transverse tip displacement $U_y$ and the torsional tip rotation $R_z$. The relative error is reported as

$$
\varepsilon =
100 \cdot
\frac{\text{OpenSees} - \text{reference}}
{\text{reference}}
\quad [\%]
$$


The independent reference is computed directly from the YAML definition without using the CSF section-sampling APIs. The reference procedure reads the end-section geometry and the longitudinal `weight_laws`, reconstructs the outer and inner radii along the tower height, and evaluates the stiffness fields on a dense axial grid of 2001 points.

At each axial location, the circular annulus is reconstructed from the interpolated radii. The bending stiffness is evaluated as

$$EI(z)=E(z)\frac{\pi}{4}\left(R_o(z)^4-R_i(z)^4\right),$$

while the torsional stiffness is evaluated as

$$GJ(z)=G(z)\frac{\pi}{2}\left(R_o(z)^4-R_i(z)^4\right),
\qquad
G(z)=\frac{E(z)}{2(1+\nu)}.$$

The reference transverse displacement is then obtained by direct numerical integration of the bending-curvature contribution induced by the transverse tip force, the tip bending moment, and the uniform transverse load. The torsional reference rotation is obtained by integrating $M_z/GJ(z)$ along the tower height. Simpson integration over the dense axial grid is used for both response quantities.

This reference is therefore independent of the OpenSees beam discretization and of the CSF station-wise section export. It uses the same YAML-defined physical model, but evaluates the response through a separate continuous-integration procedure.
The NREL tower provides a convenient reference because its sectional properties admit analytical expressions. The continuous-field representation adopted by CSF is more general: it is not restricted to circular sections or to cases for which closed-form sectional laws are available. The same framework can be applied to arbitrary polygonal geometries while retaining the continuous description of geometry and participation fields.


#### Loading configuration

Both NREL configurations are analysed under the same loading conditions. The tower is modelled as a cantilever beam, fixed at the base and loaded at the free end. The structural model includes a transverse tip force, a torsional tip moment, and a uniform transverse distributed load. These loads are not intended to reproduce a full aeroelastic operating condition; they define a controlled static test case for comparing the CSF-to-OpenSees response with the independent reference integration.

The same loading definition is used for the undegraded and degraded towers. Therefore, differences in the computed response are caused only by the sectional stiffness field and by the axial discretization used by the beam model, not by changes in loading or geometry.

The NREL validation uses both CSF interaction modes, but for different purposes. The declarative YAML workflow is used to define the tower model, inspect the sectional-property distributions, and generate plots and station-wise reports. The Python API is used in the response calculations, where the continuous sectional field is evaluated programmatically to compute the tip displacement and torsional rotation. The two modes therefore serve complementary roles within the same validation workflow: YAML supports reproducible model definition and inspection, while the API supports direct numerical evaluation.

#### Case A - undegraded tower

For the undegraded configuration, the stiffness field varies smoothly and monotonically. Convergence is rapid: a small number of beam elements is sufficient to reproduce the reference response with negligible error.

The transverse displacement $U_y$ converges at low discretization levels. The torsional rotation $R_z$ stabilises quickly and exhibits a small residual offset of approximately $3.44 \times 10^{-3}\,\%$ across all tested discretization levels. This offset is attributed to the thin-walled torsional approximation adopted internally by the CSF workflow, whereas the analytical reference uses the exact circular torsional constant $J = \tfrac{\pi}{2}(R_o^4 - R_i^4)$.

#### Case B - degraded tower


<p align="center">
  <em>Figure 1. CSF 3D representation of the degraded NREL tower case. The geometry remains tapered and continuous, while the longitudinal stiffness reduction is introduced through the participation field.</em>
  <img width="631" height="547" alt="image" src="https://github.com/user-attachments/assets/2bf9827f-df1d-44ee-9937-bacb486373d8" />
</p>

<p align="center">
  <em>Figure 2. Longitudinal stiffness degradation law applied to the NREL tower through the axial/bending participation field. The two localized reductions are centred at 0.33L and 0.67L.</em>
  <img width="985" height="467" alt="image" src="https://github.com/user-attachments/assets/50866952-f5ca-4ca3-969b-caf1a0b69934" />

</p>

In the degraded configuration, the geometry is unchanged but the participation field $w_i(z)$ introduces localized stiffness reductions along a portion of the tower height. This produces sharper axial variation in the sectional stiffness distribution.

The convergence behaviour changes markedly relative to Case A. At low discretization levels the relative errors do not decrease monotonically with element count: the accuracy depends not only on the number of beam elements, but also on how well the sampling locations represent the degraded region of the stiffness field. Convergence stabilises once the discretization becomes sufficiently refined to resolve the localized variation.

This behaviour illustrates the main motivation for a continuous sectional representation. A coarse piecewise model with too few stations may miss or underrepresent local stiffness reductions, whereas the continuous field retains the full spatial description and the beam discretization can be refined independently until convergence is achieved.

#### Convergence results


<p align="center">
   <em>Figure 3. Continuous variation of selected sectional properties for the degraded NREL tower case. The localized reductions arise from the prescribed axial/bending participation field and are reflected in the sectional area and bending stiffness distributions.</em>
  <img width="992" height="654" alt="image" src="https://github.com/user-attachments/assets/29232887-e724-46bb-9bb7-ff635c08742f" />
</p>

<p align="center">
  <em>Figure 4. Tip-displacement convergence for the undegraded NREL tower case.</em>
    <img width="1600" height="1000" alt="Degraded NREL tower tip displacement convergence" src="https://github.com/user-attachments/assets/202ff4b8-5752-4b01-93ac-2c223057124f" />

</p>



<p align="center">
  <em>Figure 5. Tip-displacement convergence for the degraded NREL tower case.</em>

<img width="1600" height="1000" alt="image" src="https://github.com/user-attachments/assets/220ea5ec-d42e-4b75-b04f-16b9e9303161" />

</p>

Table 1 reports the relative errors in tip displacement $U_y$ and torsional rotation $R_z$ as a function of the number of beam elements, for both configurations.

| Scenario   | Elements | $\varepsilon_{U_y}$ (%) | $\varepsilon_{R_z}$ (%) |
|-------------|----------:|------------------------:|------------------------:|
| Undegraded | 4  | −2.08×10⁻² | −6.49×10⁻³ |
| Undegraded | 6  | −3.99×10⁻³ | −4.05×10⁻³ |
| Undegraded | 8  | −1.06×10⁻³ | −3.63×10⁻³ |
| Undegraded | 12 | +3.93×10⁻⁵ | −3.48×10⁻³ |
| Undegraded | 16 | +2.27×10⁻⁴ | −3.45×10⁻³ |
| Undegraded | 24 | +2.97×10⁻⁴ | −3.44×10⁻³ |
| Undegraded | 32 | +3.08×10⁻⁴ | −3.44×10⁻³ |
| Degraded   | 4  | +1.04×10⁻¹ | +2.16×10⁻¹ |
| Degraded   | 6  | +1.56×10⁻¹ | +1.55×10⁻¹ |
| Degraded   | 8  | −1.73×10⁻¹ | −2.01×10⁻¹ |
| Degraded   | 12 | +8.28×10⁻² | +7.69×10⁻² |
| Degraded   | 16 | −4.29×10⁻³ | −5.67×10⁻³ |
| Degraded   | 24 | +9.57×10⁻⁴ | −2.75×10⁻³ |
| Degraded   | 32 | +2.80×10⁻⁴ | −3.48×10⁻³ |


> **Note:** At high discretization levels the relative error in $U_y$ stabilises 
> near zero ($\sim 10^{-4}\,\%$), reflecting the numerical precision of the 
> 2001-point reference integration rather than a modelling inconsistency.

The continuous stiffness representation enables this convergence study. With a fixed discrete table - as in the original NREL reference definition, which provides properties at 11 stations - the structural description is tied to the prescribed stations and its axial resolution cannot be refined independently. The continuous representation decouples the member definition from its numerical discretization: the same YAML input can be sampled at any resolution, allowing convergence toward the reference solution to be progressively assessed.

The degraded case makes this distinction explicit. At 8 elements the error in $U_y$ is larger than at 6, and the sign reverses - a non-monotone behaviour indicating insufficient axial resolution near the degraded region. This diagnostic is only possible because the reference stiffness field is defined continuously. Without a continuous reference representation, convergence behaviour cannot be assessed independently of the adopted station discretization.

#### Observations

The two cases exhibit qualitatively different convergence regimes under the same beam formulation. The undegraded case converges rapidly and uniformly, whereas the degraded case is more sensitive to axial discretization before stabilising.

This behaviour is a consequence of the continuous nature of the sectional representation, rather than a limitation of the beam formulation itself. The continuous field defines the reference; the discretization quality is assessed by its convergence toward that reference. This design choice makes the validation independent of any particular downstream solver.

[Complete workflow, convergence plots, and numerical tables for the NREL validation case](https://github.com/giovanniboscu/continuous-section-field/tree/main/docs/aes/nrel_case)



## 6. T-section with independent participation fields

A second example is introduced to illustrate a different capability of the framework: the independent specification of axial/bending and shear/torsion participation fields on a non-axisymmetric open section.
  

<p align="center">
  <em>Figure 6. T-section geometry and region subdivision used in the example.</em>
</p>
<p align="center">

<p align="center">
<img width="673" height="468" alt="tsec_s2b" src="https://github.com/user-attachments/assets/01928485-883c-4c0c-aeac-f427a6566eef" />
 
</p>

The test case consists of a continuous T-section of length $L=10$. The geometry is fixed along the member axis, while the participation fields vary continuously with $z$. The continuous field is evaluated at eleven Gauss-Lobatto stations.

Two constitutive scenarios are considered.

In the first scenario, the section is treated as isotropic. The axial/bending participation field $w(z)$ is prescribed directly, and the shear/torsion participation field is obtained through the isotropic relation introduced in Section 2.2:

$$
\kappa(z)=\frac{w(z)}{2(1+\nu)}.
$$

This configuration is compatible with station-wise Saint-Venant torsional analysis through the `sectionproperties` backend.

In the second scenario, the same geometry is retained, but the participation fields are assigned independently. The quantities $w(z)$ and $\kappa(z)$ are prescribed separately, and no isotropic relation is imposed between them. 
The resulting sectional field is therefore not described by the isotropic relation of Section 2.2.


A representative YAML fragment is reported below. The repeated polygon block defines the fixed T-section geometry at both end stations, while the longitudinal variation is introduced only through `weight_laws` and `shear_weight_laws`.

```yaml
CSF:
  sections:
    S0:
      z: 0
      polygons: &t_section_geometry
        fc:  { weight: 3.0e10, vertices: [...] }
        wu:  { weight: 3.0e10, vertices: [...] }
        wl:  { weight: 3.0e10, vertices: [...] }
        sf1: { weight: 2.1e11, vertices: [...] }
        sf2: { weight: 2.1e11, vertices: [...] }
        sf3: { weight: 2.1e11, vertices: [...] }
        sf4: { weight: 2.1e11, vertices: [...] }
        sw1: { weight: 2.1e11, vertices: [...] }
        sw2: { weight: 2.1e11, vertices: [...] }

    S1:
      z: 10
      polygons: *t_section_geometry

  weight_laws:
    - 'wl,wl: 30000000000 * (0.35 + (1.0 - 0.35) * (((z/10 - 0.5)*(z/10 - 0.5)) / 0.25)**1)'

  shear_weight_laws:
    - 'iso(0.30)'
    - 'fc,fc: iso(0.20)'
    - 'wu,wu: iso(0.20)'
    - 'wl,wl: 12500000000 * (0.2 + (1.0 - 0.2) * (((z/10 - 0.5)*(z/10 - 0.5)) / 0.25)**2)'
```

The two cases share the same geometry, interpolation rule, sampling stations, and export procedure. The constitutive field is therefore the only difference between the two configurations. This makes the comparison suitable for isolating the effect of independent participation fields while keeping all geometric aspects unchanged.

For both cases, CSF generates a station-wise sectional-property table at the Gauss-Lobatto locations. These stations can be transferred directly to downstream beam formulations or used as input to external sectional solvers. The example therefore illustrates the separation between the continuous sectional representation and the numerical sampling strategy adopted by a specific analysis workflow.

The isotropic configuration provides a reference case in which the torsional response can be evaluated through a conventional sectional-analysis backend. The anisotropic configuration demonstrates that the CSF representation remains valid even when no isotropic relation exists between axial/bending and shear/torsion participation, leaving the corresponding torsional solution to a dedicated finite-element sectional formulation.

This example complements the NREL tower validation by demonstrating that the CSF representation is not restricted to axisymmetric thin-walled structures. The same continuous-field formulation can be applied to non-axisymmetric open sections while preserving the distinction between geometry, participation fields, and numerical sampling.


### Results and discussion

The T-section example highlights a different aspect of the CSF formulation than the NREL tower validation. In this case, the geometry remains fixed along the member axis, while the participation fields vary continuously with $z$. The resulting variation of the sectional properties is therefore produced entirely by the participation-field definition rather than by geometric interpolation.

The sectional properties were evaluated at eleven Gauss-Lobatto stations. The sampled distributions are symmetric with respect to the mid-span station, reflecting the symmetry of the prescribed participation laws. The minimum values of area and bending stiffness occur near $z=L/2$, where the participation reduction reaches its maximum, while the end stations recover the original sectional properties.


The principal bending stiffness $I_x$ exhibits a pronounced reduction toward the centre of the member, whereas $I_y$ remains comparatively less affected. Consequently, the sectional response evolves continuously despite the absence of any geometric modification. This behaviour demonstrates that CSF can represent longitudinal stiffness variation independently of geometric variation.


In the sampled anisotropic case, the axial/bending participation of the lower web reaches its minimum at mid-span, decreasing from its end value to 35% of that value. The corresponding shear/torsion participation law reaches 20% of its end value at the same station.


<p align="center">
  <em>Figure 7. Axial/bending participation field used in the T-section example.</em>
</p>

<img width="1483" height="682" alt="rectangle_weights__fig_002" src="https://github.com/user-attachments/assets/46f56cdf-0642-4645-a891-414bcfdcb824" />


<p align="center">
  <em>Figure 8. Shear/torsion participation field used in the T-section example.</em>
</p>

<img width="1483" height="682" alt="rectangle_shear_weights__fig_002" src="https://github.com/user-attachments/assets/cf20a7ac-0e3c-41a4-b5aa-68d863c70935" />


<p align="center">
  <em>Figure 9. Sectional properties sampled at the Gauss-Lobatto stations.</em>
</p>


<img width="1000" height="800" alt="aes_tsection_anisotropic_lobatto_variation" src="https://github.com/user-attachments/assets/b9f8c0cb-b381-47ee-9458-1a1b7b8d06b1" />


<p align="center">
  <em>Figure 10. Continuous variation of selected sectional properties along the member axis.</em>
</p>

<img width="1484" height="1647" alt="aes_tsection_anisotropic_lobatto_properties" src="https://github.com/user-attachments/assets/996a7e13-a7b5-4ad7-a403-9b8ca61cbf60" />

</br>


The station-wise export generated by CSF is reported in Table 2. Each row corresponds to one Gauss-Lobatto station and represents the solver-facing values obtained from the same continuous anisotropic field. The table is intentionally reported as a single block, rather than split into several derived tables, because its purpose is to show the continuous-field sampling process row by row.

**Table 1. Solver-facing station-wise export generated at the Gauss-Lobatto stations.**

| $z$ | $A$ | $I_x$ | $I_y$ | $I_{xy}$ | $I_p$ | $J_{\mathrm{tors}}$ | $C_x$ | $C_y$ | method |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| 0.000000 | 3.64992e+15 | 1.28962443e+20 | 7.36535758e+19 | 0 | 2.02616019e+20 | 0 | 0 | -190.227512 | J_tors skip |
| 0.329993 | 3.60797527e+15 | 1.24522650e+20 | 7.36187730e+19 | 0 | 1.98141423e+20 | 0 | 0 | -186.511089 | J_tors skip |
| 1.077583 | 3.52353976e+15 | 1.15272176e+20 | 7.35487142e+19 | 0 | 1.88820891e+20 | 0 | 0 | -178.761528 | J_tors skip |
| 2.173823 | 3.42629521e+15 | 1.04066189e+20 | 7.34680273e+19 | 0 | 1.77534216e+20 | 0 | 0 | -169.363083 | J_tors skip |
| 3.521209 | 3.35005081e+15 | 9.48348972e+19 | 7.34047649e+19 | 0 | 1.68239662e+20 | 0 | 0 | -161.612642 | J_tors skip |
| 5.000000 | 3.32130600e+15 | 9.12468460e+19 | 7.33809144e+19 | 0 | 1.64627760e+20 | 0 | 0 | -158.598291 | J_tors skip |
| 6.478791 | 3.35005081e+15 | 9.48348972e+19 | 7.34047649e+19 | 0 | 1.68239662e+20 | 0 | 0 | -161.612642 | J_tors skip |
| 7.826177 | 3.42629521e+15 | 1.04066189e+20 | 7.34680273e+19 | 0 | 1.77534216e+20 | 0 | 0 | -169.363083 | J_tors skip |
| 8.922417 | 3.52353976e+15 | 1.15272176e+20 | 7.35487142e+19 | 0 | 1.88820891e+20 | 0 | 0 | -178.761528 | J_tors skip |
| 9.670007 | 3.60797527e+15 | 1.24522650e+20 | 7.36187730e+19 | 0 | 1.98141423e+20 | 0 | 0 | -186.511089 | J_tors skip |
| 10.000000 | 3.64992e+15 | 1.28962443e+20 | 7.36535758e+19 | 0 | 2.02616019e+20 | 0 | 0 | -190.227512 | J_tors skip |


Quantitatively, the weighted area decreases from 3.65e15 at the end stations to 3.32e15 at mid-span, corresponding to a reduction of about 9.0%. The bending stiffness I<sub>x</sub> decreases from 1.29e20 to 9.12e19, a reduction of about 29.2%, while I<sub>y</sub> changes by less than 0.4%. The polar quantity I<sub>p</sub> decreases by about 18.7%. The centroid coordinate C<sub>y</sub> shifts from approximately -190.2 at the end stations to -158.6 at mid-span, reflecting the localized reduction of the lower-web participation.

The anisotropic configuration further illustrates the separation between axial/bending and shear/torsion participation fields. In this case, the axial/bending field w<sub>i</sub>(z) and the shear/torsion field κ<sub>i</sub>(z) are prescribed independently for selected regions. The resulting sectional field therefore departs from the isotropic relation of Section 2.2.

As discussed in Section 2.2, CSF's internal torsion evaluation is limited to thin-walled open and closed sections. General solid sections, multi-cell configurations, and anisotropic torsional problems require a dedicated sectional-analysis backend rather than the internal CSF approximation. The export reports `J_tors skip`; therefore, the anisotropic case is used here to document the sampled continuous fields, rather than to provide a torsional constant from the isotropic backend. The continuous field representation, however, remains fully defined and exportable at all Gauss-Lobatto stations.


This example complements the NREL tower case by showing that CSF is able to represent continuous variation arising solely from participation fields, independently of any geometric tapering. The same framework therefore supports both geometry-driven and participation-driven sectional evolution within a unified continuous representation.


---
## 6. Conclusions

The main contribution of CSF is the formulation of an independent, declarative pre-solver layer in which polygonal geometry and material participation fields are defined as continuous entities, evaluable at arbitrary axial stations and separable from the downstream numerical discretization.

The NREL tower validation shows that the same continuous sectional field can be sampled, transferred to a beam model, and compared against an independent reference response. The degraded tower case further demonstrates that localized stiffness reductions can be represented without changing the geometric model, and that the beam discretization can be refined independently of the underlying continuous field. The T-section example complements this validation by showing that CSF is not limited to tapered or axisymmetric members. A fixed non-axisymmetric open section can be combined with independently prescribed axial/bending and shear/torsion participation fields, producing station-wise solver-facing data at Gauss-Lobatto points.

Together, these examples show that CSF separates the definition of the sectional model from its numerical sampling and from the solver consuming the exported data. This separation makes the same member definition reusable across inspection, validation, and solver-preprocessing workflows.

### Limitations

The current formulation assumes a straight element axis, linear vertex interpolation between reference stations, and fixed topology per interval. Curved members, disappearing or emerging zones, and higher-order geometric evolution are not supported. For torsion, the built-in thin-walled approximations are suitable for standard open and closed sections but not for general solid sections or multi-cell configurations, for which CSF delegates to `sectionproperties`.

### Future work

Three extensions are planned. First, the implementation of automatic differentiation for sectional-property derivatives, such as $dA/dz$, $dI_x/dz$, $dI_y/dz$, and derivatives of the participation-weighted stiffness fields, would facilitate coupling with non-prismatic beam formulations that explicitly require longitudinal gradients of geometric and constitutive quantities.. Second, support for curved member axes would extend the applicability of the framework beyond straight beam-like structures. Third, tighter integration with nonlinear structural solvers could allow participation fields to evolve during the analysis, enabling applications beyond the current static sectional representation.



---

## Acknowledgements

The author thanks the developers of `sectionproperties` for providing an open finite-element section-analysis ecosystem that can be used in validation and interoperability workflows.

---

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work, the author used ChatGPT and Claude for drafting assistance, copy-editing, and code-review suggestions. After using these tools, the author reviewed, edited, and validated the content as needed and takes full responsibility for the scientific claims, software implementation, and manuscript.


## References

- **[Balduzzi 2016]** <a id="Balduzzi-2016"></a>  *Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). Non-prismatic beams: A simple and effective Timoshenko-like model. International Journal of Solids and Structures*, 90, 236–250.
  https://doi.org/10.1016/j.ijsolstr.2016.02.017

- **[KENNA]** <a id="KENNA"></a> *A. Kenna and B. Basu, “Damage Detection in Wind Turbine Towers using a Finite Element Model and Discrete Wavelet Transform of Strain Signals,”* Journal of Physics: Conference Series, vol. 628, no. 1, p. 012067, 2015. doi:10.1088/1742-6596/628/1/012067.

- **[VABS]** <a id="vabs"></a> *Variational Asymptotic Beam Sectional Analysis*.  https://analyswift.com/vabs/

- **[NRELOpenFAST]**  <a id="NRELOpenFAST"></a> *National Renewable Energy Laboratory. OpenFAST: open-source wind turbine simulation tool*. https://github.com/OpenFAST/openfast
- **[NREL WISDEM]** <a id="wisdem"></a>  *National Renewable Energy Laboratory. WISDEM: Wind-Plant Integrated System Design and Engineering Model*. https://github.com/WISDEM/WISDEM

- **[SEC_PROP]** <a id="sec_prop"></a>  *python package for the analysis of arbitrary cross-sections using the finite element method.*.
https://github.com/robbievanleeuwen/section-properties

- **[WANG]**  <a id="wang"></a>   *Wang et al. 2017 - Wang, Q., Sprague, M. A., Jonkman, J., Johnson, N., & Jonkman, B. (2017). BeamDyn: A High-Fidelity Wind Turbine Blade Solver in the FAST Modular Framework. Wind Energy, 20(8), 1439–1462*.  https://doi.org/10.1002/we.2101
    
- **[Gavin]**  <a id="gavin"></a>  *Gavin, H. P. Frame3DD: Static and dynamic structural analysis of 2D and 3D frames*. http://frame3dd.sourceforge.net/

- **[BECAS]**  <a id="becas"></a> *Finite-element-based cross-sectional analysis software*. https://becas.dtu.dk/

- **[ANSYS]**  <a id="ansys"></a> *engineering simulation software*. https://www.ansys.com/

- **[ABAQUS]**  <a id="ABAQUS"></a> *Dassault Systèmes Simulia Corp. ABAQUS*. https://www.3ds.com/products/simulia/abaqus/

- **[OPENSEES]** <a id="OPENSEES"></a> *McKenna, F. OpenSees: A Framework for Earthquake Engineering Simulation. Computing in Science & Engineering, 13(4), 58–66, 2011*. https://doi.org/10.1109/MCSE.2011.66  
  Project website: https://opensees.berkeley.edu/
---
  
- **[SUMMB_NREL]** <a id="SUMMB_NREL"></a>  *G. Boscu, Continuous Section Field: NREL validation comparison summary*. Repository documentation, 2026.
https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/nrel_case/validation_comparison_summary_all_b.md

- **[CSF_SP]** <a id="CSF_SP"></a>  *G. Boscu, Continuous Section Field: Continuous Section Field csf_sp User Guide*.  Repository documentation, 2026.
 https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_user_guide.md


- **[SP_CSF]** <a id="SP_CSF"></a>  *G. Boscu, Continuous Section Field: Continuous Section Field csf_sp User Guide*.  Repository documentation, 2026.
 https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sectionproperties/sp_csf_guide.md

- **[FULL_AN]** <a id="FULL_AN"></a> *G. Boscu, Continuous Section Field: Section Full Analysis Output*. Repository documentation, 2026.
https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md

- **[SAINT_VEN]** <a id="SAINT_VEN"></a> *G. Boscu, Continuous Section Field: Saint-Venant Torsional Constant*. Repository documentation, 2026.
Available: https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md

