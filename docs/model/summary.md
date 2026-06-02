Draft v2.5.1
# Continuous Section Fields: A Computational Modelling Framework for Axially Graded Non-Uniform Structural Members

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
  
$$A(z)$$ ,  $$I_x(z)$$ ,  $$I_y(z)$$ ,  $$(EI_x)(z)$$ , $$(GJ)(z)$$ ,  $$\rho_l(z)$$

</p>

A member is represented as a continuous sectional field composed of evolving polygonal geometry together with two material participation fields: the axial/bending field $w_i(z)$ and the shear/torsion field $\kappa_i(z)$. This representation is defined, evaluated, inspected, and validated independently of any downstream solver. The solver receives a station-wise projection of an already defined continuous field - not a table that defines the model itself.

The result is a clean separation between three concerns that are normally conflated: the continuous physical model of the member, the numerical sampling strategy required by the solver, and the exported data format consumed by a specific tool.

Cross-section analysis tools such as [VABS](#VABS) and [BECAS](#becas) provide accurate computation of beam sectional properties for arbitrary geometries and composite materials, and are widely adopted in wind-turbine and aerospace applications. Open-source alternatives such as  [sectionproperties](#SEC_PROP) offer similar capabilities within a Python ecosystem. These tools are primarily designed to analyse individual cross-sections: given a sectional geometry and material definition, they return the corresponding sectional properties at that station.

The longitudinal variation of the member - including tapering geometry, spatially varying material participation, or local stiffness degradation - is therefore usually represented outside the section-analysis tool, either through user-defined station tables or through the discretization adopted by the downstream structural solver. As a consequence, the sectional description is often tied to a specific mesh or analysis workflow, rather than being defined as an independent continuous model.

On the theoretical side,  [Balduzzi](#Balduzzi-2016) showed that non-prismatic beam analysis requires the axial derivatives of cross-sectional quantities, such as $\frac{dA}{dz}$ and $\frac{dI}{dz}$, as explicit terms in the governing equations. The formulation therefore depends on continuous sectional functions, not solely on values evaluated at discrete stations. This highlights the need for programmable descriptions capable of generating consistent geometric and constitutive quantities, and their axial variation, at arbitrary locations along the member axis.

Existing frameworks for the analysis of non-prismatic members can be grouped into three categories. First, sectional analysis tools such as VABS, BECAS, and `sectionproperties` compute the properties of individual cross-sections with high accuracy, while the longitudinal variation of the member is handled externally. Second, structural solvers such as [OpenSees](#OPENSEES), [ABAQUS](#ABAQUS), and [ANSYS](#ANSYS) incorporate non-prismaticity through the adopted finite-element formulation, typically by evaluating sectional properties at nodes, integration points, or user-defined stations. 


Third, wind-energy simulation and design workflows embed non-prismaticity in application-specific representations. Aeroelastic codes such as BeamDyn [wang](#wang)  rely on distributed sectional-property tables along the member axis, whereas systems-engineering tools such as [NREL's WISDEM](#wisdem)  represent the tower as a tapered cylindrical shell with closed-form sectional properties, analysed through the external frame finite-element code Frame3DD [Gavin](#gavin). In both cases the longitudinal variation is bound to a specific geometry or workflow rather than expressed as an independent, reusable sectional field.


In existing workflows, the longitudinal variation of sectional properties is usually handled inside section-analysis tools, structural solvers, or application-specific pipelines. It is less commonly exposed as an independent, solver-agnostic modelling layer that can define, sample, export, and reuse sectional-property fields along the member axis.

This absence of a clearly separated sectional-field layer is both a limitation and a motivation. It makes direct tool-to-tool benchmarking difficult, since most existing tools do not provide the same modelling object. At the same time, it identifies the methodological gap addressed by CSF.

---

## 2. The CSF Section Model

### 2.1 Scope

Standard beam workflows often describe sectional stiffness through prescribed sectional properties or material variations assigned along the member axis. This is restrictive for tapered, composite, or locally degraded members, where geometry and material participation may vary independently along the axis. CSF addresses this case by assigning independent geometric and participation fields to each zone of the section.

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

In CSF, a member is represented by two reference sections located at $z_0$ and $z_1$. Each section is decomposed into an arbitrary number of polygonal zones, and each zone is defined by corresponding vertex coordinates at the two stations. The geometric field is then generated by linear interpolation of the corresponding vertices:


$$
\mathbf{v}_{i,k}(z) = \mathbf{v}_{i,k}^{(0)} + \frac{z - z_0}{z_1 - z_0}
\bigl(\mathbf{v}_{i,k}^{(1)} - \mathbf{v}_{i,k}^{(0)}\bigr)
$$


>*Linear interpolation is adopted here as the baseline geometric field, providing the minimal continuous mapping between corresponding sectional zones.*


where superscripts $(0)$ and $(1)$ denote the values at $z_0$ and $z_1$ respectively, and $k$ indexes the vertices of zone $i$. This produces a continuous, linearly tapered geometry at any intermediate station. Multiple interpolation intervals can be composed in sequence through a CSF module. Each interval is instantiated as an independent CSF object with its own reference stations, zone geometry, and participation fields.
A single CSF interval describes the continuous evolution of the section between two reference stations. Members requiring multiple intervals are represented by a concatenated sectional field. This representation, implemented as CSFStack, preserves continuity of the section-property field at the junctions, while allowing each interval to retain its own closed-form polygonal evaluation.


### 2.4 Participation fields

Once the geometric field has defined the continuous evolution of each polygonal zone, CSF assigns to every zone two longitudinal participation fields: $w_i(z)$ for axial and bending partecipation, and $\kappa_i(z)$ for shear and torsional parecipation. These fields scale the contribution of the corresponding geometric zone at each station, so that geometry and material participation can vary independently along the member axis.

The functions $w_i(z)$ and $\kappa_i(z)$ are user-defined functions of the longitudinal coordinate, or, for $\kappa_i(z)$, may be obtained from $w_i(z)$ through the isotropic relation of §2.2. Supported forms include polynomials, exponentials, piecewise-linear laws, and discrete lookup tables. The only requirement is that each function be evaluable at any requested station.


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

<p align="center">
  
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

</p>

> **Note:** At high discretization levels the relative error in $U_y$ stabilises 
> near zero ($\sim 10^{-4}\,\%$), reflecting the numerical precision of the 
> 2001-point reference integration rather than a modelling inconsistency.

The continuous stiffness representation enables this convergence study. With a fixed discrete table - as in the original NREL reference definition, which provides properties at 11 stations - the structural description is tied to the prescribed stations and its axial resolution cannot be refined independently. The continuous representation decouples the member definition from its numerical discretization: the same YAML input can be sampled at any resolution, allowing convergence toward the reference solution to be progressively assessed.

The degraded case makes this distinction explicit. At 8 elements the error in $U_y$ is larger than at 6, and the sign reverses - a non-monotone behaviour indicating insufficient axial resolution near the degraded region. This diagnostic is only possible because the reference stiffness field is defined continuously. Without a continuous reference representation, convergence behaviour cannot be assessed independently of the adopted station discretization.

#### Observations

The two cases exhibit qualitatively different convergence regimes under the same beam formulation. The undegraded case converges rapidly and uniformly, whereas the degraded case is more sensitive to axial discretization before stabilising.

This behaviour is a consequence of the continuous nature of the sectional representation, rather than a limitation of the beam formulation itself. The continuous field defines the reference; the discretization quality is assessed by its convergence toward that reference. This design choice makes the validation independent of any particular downstream solver.

[Complete workflow, convergence plots, and numerical tables for the NREL validation case](https://github.com/giovanniboscu/continuous-section-field/tree/main/docs/aes/nrel_case)

  
## 6. Stacked rectangular member with isotropic and independent participation fields

A second verification case is introduced to isolate a different aspect of the CSF formulation from the NREL tower validation. The NREL case verifies the use of a continuous sectional field in a beam-response workflow. The present case removes the external structural solver and considers a deliberately elementary stacked rectangular member, so that the sectional quantities can be checked directly against closed-form expressions at every sampled station.

The purpose of the example is threefold. First, it verifies the composition of multiple continuous intervals through `CSFStack`. Second, it shows that a tapered geometric field and a participation-driven field can coexist in the same global member representation. Third, it distinguishes an isotropic participation setting from a case in which the axial/bending and shear/torsion participation fields are assigned independently.

### 6.1 Model definition

The member has total length $L=10$ and is composed of two continuous intervals joined at $z=5$. Each interval is represented by a `ContinuousSectionField`, and the two fields are concatenated through `CSFStack`. 

The cross-section is decomposed into two rectangular zones, denoted as lower and upper. In the first interval this decomposition is mechanically neutral, since both zones have unit axial/bending participation and the shear/torsion participation is obtained from the isotropic relation. The first interval is therefore modelled as an isotropic fully participating tapered section. The same zone structure is retained in the second interval, where the geometry is constant but the lower zone is assigned independent axial/bending and shear/torsion participation laws. The second interval is therefore no longer isotropic in the sense of Section 2.2, because $w_i(z)$ and $\kappa_i(z)$ are prescribed independently for the degraded zone.


<p align="center">
  <em>Figure 6. Two continuous intervals stacked through CSFStack.</em>
  <img width="795" height="489" alt="image" src="https://github.com/user-attachments/assets/f5b519a9-39eb-4605-9e0d-f759471f675c" />
</p>



The first interval, $0 \le z \le 5$, is a tapered rectangular section. The width is constant, $B=0.30$, while the total height decreases linearly from $0.60$ to $0.40$. Both zones have unit axial/bending participation,

$$
w_{\mathrm{lower}}(z)=w_{\mathrm{upper}}(z)=1 .
$$

The shear/torsion participation is defined through the isotropic relation introduced in Section 2.2,



$$
\kappa_i(z)=\frac{w_i(z)}{2(1+\nu)} .
$$

For this interval the value $\nu=-0.5$ is used as a carrier normalization, not as a physical material parameter. It gives

$$
\kappa_i(z)=w_i(z)=1 ,
$$

so that the first interval isolates the effect of geometric tapering. In the YAML definition this corresponds to the isotropic shortcut

```yaml
shear_weight_laws:
  - 'iso(-0.5)'
```

The second interval, $5 \le z \le 10$, has constant rectangular geometry with total height $0.40$, again divided into lower and upper zones of equal height. The upper zone remains fully participating,

$$
w_{\mathrm{upper}}(z)=1, \qquad \kappa_{\mathrm{upper}}(z)=1 .
$$

The lower zone is assigned two independent participation laws. With

$$
t=\frac{z-5}{5}, \qquad 0 \le t \le 1 ,
$$

the axial/bending and shear/torsion fields are

$$
w_{\mathrm{lower}}(z)=1-0.5t^2 ,
$$

$$
\kappa_{\mathrm{lower}}(z)=1-0.8t^2 .
$$

Thus the lower-zone axial/bending participation decreases nonlinearly from $1.0$ to $0.5$, whereas its shear/torsion participation decreases nonlinearly from $1.0$ to $0.2$. The shear/torsion participation decreases more strongly than the axial/bending participation over the same interval. This second interval therefore departs from the isotropic relation and tests the independent assignment of $w_i(z)$ and $\kappa_i(z)$ within the same stacked member.

The executable script and YAML input files corresponding to the verification reported in this section are provided in the accompanying open-source repository [REF-CASE], allowing the results to be inspected, modified, and rerun. A separate FEM torsion check for the same stacked member is also provided as supplementary repository material [REF-FEM]. That FEM check is not used in the closed-form verification reported here.



<p align="center">
  <em>Figure 7. Axial/bending participation fields in the variable interval.</em>
</p>

<img width="1806" height="799" alt="image" src="https://github.com/user-attachments/assets/7388d749-b345-4143-b2c3-a560c36316d7" />



<p align="center">
  <em>Figure 8. Shear/torsion participation fields in the variable interval.</em>
</p>

<img width="1825" height="810" alt="image" src="https://github.com/user-attachments/assets/81ee73ed-bd18-43d0-a25e-edbf4ce289a5" />


### 6.2 Closed-form reference

The verification is conducted station-wise. The stacked field is sampled at Gauss--Lobatto stations applied separately to the two continuous intervals, with the common junction counted once. At each station, the CSF-computed sectional quantities are compared with closed-form expressions derived from the corresponding weighted rectangular section.

For the tapered interval, the total height is

$$
H(z)=0.60-0.20\frac{z}{5}.
$$

Since both zones have unit participation and the section is symmetric about the horizontal centroidal axis, the reference quantities reduce to the standard rectangular expressions

$$
A(z)=BH(z), \qquad C_y(z)=0,
$$

$$
I_x(z)=\frac{BH(z)^3}{12}, \qquad I_y(z)=\frac{H(z)B^3}{12}.
$$

For the second interval, each zone has height $h=0.20$ and area

$$
A_z=Bh .
$$

The lower and upper zone centroids are located at

$$
y_l=-0.10, \qquad y_u=+0.10 .
$$

With $w_l=w_{\mathrm{lower}}(z)$ and $w_u=1$, the weighted area and centroid are

$$
A(z)=(w_l+w_u)A_z ,
$$

$$
C_y(z)=\frac{w_l A_z y_l+w_u A_z y_u}{A(z)} .
$$

The centroidal second moment about the $x$-axis is obtained by the parallel-axis theorem:

$$
I_x(z)= w_l\left(I_{x,z}+A_z y_l^2\right) + w_u\left(I_{x,z}+A_z y_u^2\right) - A(z)C_y(z)^2 ,
$$

where

$$
I_{x,z}=\frac{Bh^3}{12}.
$$

The second moment about the $y$-axis is

$$
I_y(z)=(w_l+w_u)\frac{hB^3}{12}.
$$

Only $A$, $C_y$, $I_x$, and $I_y$ are used as exact benchmark quantities. These quantities are direct weighted area-integral properties and therefore admit the closed-form references above.


<p align="center">
  <em>Figure 9. Section-property variation over the two stacked intervals.</em>
</p>


<img width="968" height="901" alt="image" src="https://github.com/user-attachments/assets/6c6409e8-f88d-4af8-8774-68eb3e914b74" />

### 6.3 Torsional read-out

Torsion is treated consistently with the declared scope of CSF. CSF does not compute the general Saint-Venant torsional constant of an arbitrary section; when required, warping-based torsional properties must be obtained through an external sectional-analysis procedure, including the `csf_sp` bridge to the section-analysis backend. The quantity $J_{\mathrm{roark,eq}}$ reported in the table is a CSF Roark-equivalent torsional read-out, not an exact Saint-Venant benchmark for the shear-non-uniform section.

For a solid rectangular section, the geometric carrier is evaluated through the Roark-type approximation

$$
J_{\mathrm{roark}} \simeq a b^3 \left[ \frac{1}{3} - 0.21\frac{b}{a}\left( 1 - \frac{1}{12}\left(\frac{b}{a}\right)^4 \right) \right], \qquad a \ge b > 0 ,
$$

where $a$ and $b$ denote the larger and smaller full side dimensions of the rectangle, respectively. CSF uses this expression as a lightweight equivalent torsional carrier for the sampled rectangular section. When the shear/torsion participation field is uniform, the resulting read-out coincides with the Roark-equivalent value associated with the section geometry. When the shear/torsion participation is not uniform across the sectional zones, the reported value must be interpreted as an equivalent CSF read-out rather than as an exact Saint-Venant torsional constant.

The associated fidelity indicator is reported to qualify this read-out. In the tapered interval, the shear/torsion participation is uniform and the fidelity indicator remains equal to one. In the second interval, the lower-zone value of $\kappa_i(z)$ progressively departs from the upper-zone value; the fidelity indicator correspondingly decreases. This behaviour indicates that the Roark-equivalent torsional read-out is being used outside the uniform-participation condition for which the rectangular approximation is most directly interpretable.

The implementation details of the Roark-equivalent read-out and the supplementary torsional checks are provided in the repository documentation [ROARK-REF]. In the present verification, $J_{\mathrm{roark,eq}}$ and its fidelity indicator are reported only as diagnostic CSF quantities. They are not used as benchmark values. The closed-form verification remains restricted to $A$, $C_y$, $I_x$, and $I_y$.


### 6.4 Station-wise verification results

The following table reports the CSF values and the corresponding closed-form reference values at the selected Gauss--Lobatto stations. Since the member is represented as a `CSFStack` composed of two continuous intervals, the Gauss--Lobatto stations are generated separately on the tapered interval $0 \le z \le 5$ and on the participation-degraded interval $5 \le z \le 10$. The common junction at $z=5$ is counted once. This preserves the interval-wise structure of the stacked field while producing a single global station-wise verification table.

The column `err_AIxIy%` is the maximum relative error over $A$, $I_x$, and $I_y$. Since $C_y$ is zero in the tapered interval, its discrepancy is reported as an absolute error in the column `err_Cy`.

```text
      z     w    sw |    A_csf    A_ref |   Cy_csf   Cy_ref |    Ix_csf    Ix_ref |    Iy_csf    Iy_ref |  J_roark_eq   fid |  err_AIxIy%    err_Cy
---------------------------------------------------------------------------------------------------------------------------------------------------
  0.000  1.00  1.00 |  0.18000  0.18000 |  0.00000  0.00000 |  0.005400  0.005400 |  0.001350  0.001350 |    0.003708  1.00 |     1.6e-14   0.0e+00
  0.165  1.00  1.00 |  0.17802  0.17802 |  0.00000  0.00000 |  0.005224  0.005224 |  0.001335  0.001335 |    0.003649  1.00 |     1.6e-14   0.0e+00
  0.539  1.00  1.00 |  0.17353  0.17353 |  0.00000  0.00000 |  0.004839  0.004839 |  0.001302  0.001302 |    0.003515  1.00 |     1.8e-14   0.0e+00
  1.087  1.00  1.00 |  0.16696  0.16696 |  0.00000  0.00000 |  0.004309  0.004309 |  0.001252  0.001252 |    0.003320  1.00 |     2.0e-14   0.0e+00
  1.761  1.00  1.00 |  0.15887  0.15887 |  0.00000  0.00000 |  0.003713  0.003713 |  0.001192  0.001192 |    0.003080  1.00 |     2.3e-14   0.0e+00
  2.500  1.00  1.00 |  0.15000  0.15000 |  0.00000  0.00000 |  0.003125  0.003125 |  0.001125  0.001125 |    0.002817  1.00 |     1.9e-14   0.0e+00
  3.239  1.00  1.00 |  0.14113  0.14113 |  0.00000  0.00000 |  0.002603  0.002603 |  0.001058  0.001058 |    0.002556  1.00 |     2.0e-14   0.0e+00
  3.913  1.00  1.00 |  0.13304  0.13304 |  0.00000  0.00000 |  0.002180  0.002180 |  0.000998  0.000998 |    0.002320  1.00 |     4.0e-14   0.0e+00
  4.461  1.00  1.00 |  0.12647  0.12647 |  0.00000  0.00000 |  0.001873  0.001873 |  0.000948  0.000948 |    0.002129  1.00 |     1.1e-14   0.0e+00
  4.835  1.00  1.00 |  0.12198  0.12198 |  0.00000  0.00000 |  0.001681  0.001681 |  0.000915  0.000915 |    0.002000  1.00 |     2.6e-14   0.0e+00
  5.000  1.00  1.00 |  0.12000  0.12000 |  0.00000  0.00000 |  0.001600  0.001600 |  0.000900  0.000900 |    0.001944  1.00 |     2.7e-14   0.0e+00
  5.165  1.00  1.00 |  0.11997  0.11997 |  0.00003  0.00003 |  0.001600  0.001600 |  0.000900  0.000900 |    0.001943  1.00 |     1.4e-14   0.0e+00
  5.539  0.99  0.99 |  0.11965  0.11965 |  0.00029  0.00029 |  0.001595  0.001595 |  0.000897  0.000897 |    0.001935  1.00 |     1.2e-14   0.0e+00
  6.087  0.98  0.96 |  0.11858  0.11858 |  0.00120  0.00120 |  0.001581  0.001581 |  0.000889  0.000889 |    0.001907  1.00 |     1.4e-14   0.0e+00
  6.761  0.94  0.90 |  0.11628  0.11628 |  0.00320  0.00320 |  0.001549  0.001549 |  0.000872  0.000872 |    0.001847  1.00 |     1.4e-14   0.0e+00
  7.500  0.88  0.80 |  0.11250  0.11250 |  0.00667  0.00667 |  0.001495  0.001495 |  0.000844  0.000844 |    0.001749  0.99 |     1.5e-14   0.0e+00
  8.239  0.79  0.66 |  0.10741  0.10741 |  0.01172  0.01172 |  0.001417  0.001417 |  0.000806  0.000806 |    0.001617  0.96 |     1.5e-14   1.7e-18
  8.913  0.69  0.51 |  0.10163  0.10163 |  0.01808  0.01808 |  0.001322  0.001322 |  0.000762  0.000762 |    0.001468  0.89 |     1.4e-14   6.9e-18
  9.461  0.60  0.36 |  0.09612  0.09612 |  0.02485  0.02485 |  0.001222  0.001222 |  0.000721  0.000721 |    0.001325  0.78 |     1.8e-14   3.5e-18
  9.835  0.53  0.25 |  0.09195  0.09195 |  0.03051  0.03051 |  0.001140  0.001140 |  0.000690  0.000690 |    0.001217  0.64 |     0.0e+00   3.5e-18
 10.000  0.50  0.20 |  0.09000  0.09000 |  0.03333  0.03333 |  0.001100  0.001100 |  0.000675  0.000675 |    0.001166  0.56 |     0.0e+00   0.0e+00
---------------------------------------------------------------------------------------------------------------------------------------------------




```
The numerical discrepancies remain at machine precision. The largest relative error over $A$, $I_x$, and $I_y$ is $4.0\times10^{-14}%$, while the largest absolute discrepancy in $C_y$ is $6.9\times10^{-18}$. These results confirm that the stacked CSF representation reproduces the closed-form weighted-section quantities over both intervals: the isotropic tapered interval and the lower-zone interval with independently assigned nonlinear axial/bending and shear/torsion participation fields.


The last two reported columns, $J_{\mathrm{roark,eq}}$ and the fidelity indicator, document the CSF torsional read-out over the same stations. Their trend is consistent with the imposed participation fields: the fidelity remains equal to one while the shear/torsion participation is uniform, and then decreases as the lower-zone shear/torsion participation departs from the upper-zone value. They are reported for completeness and diagnostic interpretation, not as exact torsional benchmark values.

This example complements the NREL tower validation by isolating the sectional-field construction itself. The geometry is simple by design, but the model exercises the key CSF mechanisms required for more general applications: interval composition, non-prismatic geometry, isotropic participation, independent participation fields, and station-wise extraction of solver-facing quantities from a continuous member representation.

>Note. Verification on more general, non-rectangular cross-sections, validated against independent finite-element analysis, is provided in the accompanying repository [REF-GEN],
>complementing the closed-form benchmarks reported in the paper.


---
## 7. Conclusions

The main contribution of CSF is the formulation of an independent, declarative pre-solver layer in which polygonal geometry and material participation fields are defined as continuous entities, evaluable at arbitrary axial stations and separable from the downstream numerical discretization.

The NREL tower validation shows that the same continuous sectional field can be sampled, transferred to a beam model, and compared against an independent reference response. The undegraded case verifies the smooth geometry-driven variation of a tapered structural member, while the degraded case demonstrates that localized stiffness reductions can be introduced through participation fields without modifying the geometric model. The convergence study further shows that the beam discretization can be refined independently of the underlying continuous sectional representation.

The stacked rectangular example complements this validation by isolating the sectional-field construction itself. It verifies, through closed-form station-wise references, that CSF correctly composes multiple continuous intervals through `CSFStack`, combines a tapered isotropic interval with a participation-degraded interval, and supports independent axial/bending and shear/torsion participation fields within the same global member representation. The example also clarifies the role of torsional read-outs: the Roark-equivalent quantity and its fidelity indicator are reported as diagnostic CSF quantities, while the exact verification is restricted to the area-integral properties (A), (C_y), (I_x), and (I_y).

Together, these examples show that CSF separates the definition of the sectional model from its numerical sampling and from the solver consuming the exported data. This separation makes the same member definition reusable across inspection, validation, and solver-preprocessing workflows, while preserving a continuous representation that can be sampled, exported, or externally analysed according to the needs of the downstream procedure.


### Limitations

The current formulation assumes a straight element axis, linear vertex interpolation between reference stations, and fixed topology within each interpolation interval. Curved members, disappearing or emerging zones, and higher-order geometric evolution are not supported.

For torsion, the built-in CSF approximations are limited to selected engineering read-outs. Standard thin-walled open and closed sections can be treated through the corresponding thin-walled estimates, while solid rectangular sections may be assigned a Roark-equivalent torsional read-out. This quantity is an engineering approximation and should not be interpreted as a general Saint-Venant torsional solution for arbitrary cross-sections or for shear-non-uniform participation fields. CSF therefore reports the Roark-equivalent value together with a fidelity indicator, so that its use remains explicit.

General solid sections, multi-cell configurations, and sections requiring warping-based Saint-Venant analysis must be evaluated by an external sectional-analysis backend. For isotropic cases, this role can be fulfilled through the `csf_sp` bridge to `sectionproperties`. However, when CSF is used to model non-isotropic participation fields, where the axial/bending and shear/torsion participation fields are prescribed independently, the torsional problem no longer falls within the isotropic `sectionproperties` workflow. In such cases, more general numerical sectional formulations are required, for example dedicated finite-element torsion models implemented with tools such as `scikit-fem`.

Accordingly, CSF should be interpreted as the continuous sectional-field representation and sampling layer. It defines, evaluates, and exports geometry and participation fields; torsional quantities outside its built-in approximation domain must be computed by an appropriate external sectional solver.


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


---
