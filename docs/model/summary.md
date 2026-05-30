# A Field-Based Framework for the Continuous Modelling of Non-Prismatic Structural Members

## Abstract

Continuous Section Field (CSF) is a field-based computational framework for representing sectional geometry, material participation, and derived section properties as continuous functions along a member axis. CSF is neither a structural solver nor a geometry kernel; instead, it connects these domains by transforming member-level geometric and material descriptions into continuous section-property fields and station-wise data suitable for beam, tower, bridge, and finite-element workflows.

The central idea of CSF is to treat the cross-section as a field defined along the member axis, rather than as a single isolated object. The geometry is specified at reference stations and obtained by interpolating corresponding polygon vertices between them, producing continuous intermediate cross-sections. Material participation, by contrast, is not interpolated between stations but prescribed as a continuous longitudinal field along the member axis. At any requested station, CSF combines the interpolated geometry with the participation field to evaluate properties such as area, centroid, second moments of area, principal inertias and section moduli

CSF makes an explicit separation between the geometric description of the member and the sectional participation fields that govern its mechanical contribution. Two longitudinal material participation fields define how much each region contributes: the axial/bending field $w_i(z)$ and the shear/torsion field $\kappa_i(z)$. Their independence is foundational to CSF: the model imposes no relation between the two, so each field can be specified on its own. These fields can represent stiffness ratios, degraded regions, reinforcement, voids, density-like quantities, or other user-defined sectional contributions. When both derive from elastic behaviour, they may optionally be coupled through an isotropic relation, each varying with the longitudinal coordinate and with geometric quantities.

The continuous model can be defined through a Python API or through a declarative YAML workflow. In the YAML workflow, one file defines the continuous member and another file defines the requested computations, plots, inspections, station sampling, and exports. The YAML file does not define a discrete table of section properties; it defines the geometry and the participation fields from which CSF constructs the continuous section-property fields.

This distinction allows CSF to preserve a continuous member representation while generating solver-facing station-wise data when required.

## 1. Motivation

In current structural analysis practice, the definition of section properties for non-prismatic members is typically embedded within the solver itself. Geometry and material participation are not treated as independent fields; instead, they are collapsed into a discrete table of section properties evaluated at a fixed set of stations, tied to the solver mesh and conventions. This coupling makes the sectional model difficult to inspect, reuse, or transfer across different solvers, and it obscures the distinction between the continuous physical model and its numerical discretisation.

Many structural and mechanical engineering problems involve members whose cross-section changes along their length: tapered towers, variable-depth beams, haunched bridge girders, repaired or degraded members, hybrid material sections, and staged or homogenized structural models. In these cases, the required input for a numerical model is not a single section, but a longitudinal field of section properties such as $A(z)$, $I_x(z)$, $I_y(z)$, $EI_x(z)$, $GJ(z)$, and mass-related quantities. When this field is defined inside the solver, it cannot be validated, inspected, or reused independently.

CSF addresses this by extracting the sectional field definition into a dedicated pre-solver layer. A member is represented as a continuous sectional field composed of evolving polygonal geometry together with two material participation fields: the axial/bending field $w_i(z)$ and the shear/torsion field $\kappa_i(z)$. This representation is defined, evaluated, inspected, and validated independently of any downstream solver. The solver receives a station-wise projection of an already defined continuous field - not a table that defines the model itself.

The result is a clean separation between three concerns that are normally conflated: the continuous physical model of the member, the numerical sampling strategy required by the solver, and the exported data format consumed by a specific tool.

Cross-section analysis tools such as [VABS](#VABS) and BECAS [BECAS](#becas) provide accurate computation of beam sectional properties for arbitrary geometries and composite materials, and are widely adopted in wind-turbine and aerospace applications. Open-source alternatives such as  [sectionproperties](#SEC_PROP) offer similar capabilities within a Python ecosystem. These tools are primarily designed to analyse individual cross-sections: given a sectional geometry and material definition, they return the corresponding sectional properties at that station.

The longitudinal variation of the member - including tapering geometry, spatially varying material participation, or local stiffness degradation - is therefore usually represented outside the section-analysis tool, either through user-defined station tables or through the discretization adopted by the downstream structural solver. As a consequence, the sectional description is often tied to a specific mesh or analysis workflow, rather than being defined as an independent continuous model.

On the theoretical side, Balduzzi [Balduzzi 2016](#Balduzzi-2016) showed that non-prismatic beam analysis requires the axial derivatives of cross-sectional quantities, such as $\frac{dA}{dz}$ and $\frac{dI}{dz}$, as explicit terms in the governing equations. The formulation therefore depends on continuous sectional functions, not solely on values evaluated at discrete stations. This highlights the need for programmable descriptions capable of generating consistent geometric and constitutive quantities, and their axial variation, at arbitrary locations along the member axis.

Existing frameworks for the analysis of non-prismatic members can be grouped into three categories. First, sectional analysis tools such as VABS, BECAS, and `sectionproperties` compute the properties of individual cross-sections with high accuracy, while the longitudinal variation of the member is handled externally. Second, structural solvers such as OpenSees, ABAQUS, and ANSYS incorporate non-prismaticity through the adopted finite-element formulation, typically by evaluating sectional properties at nodes, integration points, or user-defined stations. 


Third, wind-energy simulation and design workflows embed non-prismaticity in application-specific representations. Aeroelastic codes such as [wang](#wang);  rely on distributed sectional-property tables along the member axis, whereas systems-engineering tools such as [NREL's WISDEM](#wisdem)  represent the tower as a tapered circular tube with closed-form sectional properties, analysed through the external frame finite-element code Frame3DD [Gavin](#gavin). In both cases the longitudinal variation is bound to a specific geometry or workflow rather than expressed as an independent, reusable sectional field.


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

The Saint-Venant torsional constant is a notable exception. Area-integral properties are separable - geometry and participation factor cleanly - but Saint-Venant torsion is not: the torsional constant cannot be reduced to a weighted area integral, because the warping field couples geometry and material across the section. CSF therefore treats torsion separately. For sections tagged as closed cells or open thin walls, CSF evaluates an internal geometric torsional constant from thin-walled approximations (the Bredt formula for closed cells and the $b\,t^3/3$ estimate for open walls), and the shear/torsion participation enters as a single section-level value rather than zone by zone. For general solid sections, multi-cell configurations, connected cell–wall systems, or cases requiring higher accuracy, the continuous geometric field can be passed to `sectionproperties` through the CSF bridge `csf_sp` for a full warping analysis, while retaining the same continuous geometric and participation-field description.

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
- endpoint participation values;
- longitudinal laws for $w_i(z)$ and $\kappa_i(z)$.

The action file defines:

- station sets;
- plots;
- section inspections;
- property evaluations;
- exports;
- validation-oriented outputs.

This separation makes the same continuous model reusable across different numerical studies. A single member definition can be sampled at dense stations for inspection, at Gauss-Lobatto stations for quadrature-compatible beam input, or at user-defined stations for comparison with external data.

### 3.1 Geometry file

The geometry file defines the continuous sectional model. The example below describes a tapered polygonal section between two reference stations. The cross-section is reduced from `S0` to `S1`, while the axial/bending field follows an independent parabolic law along the member axis. The shear/torsion field is derived from $w_i$ through an isotropic relation.

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

The example separates three ingredients that are usually collapsed into a single tabulated section-property description: the reference geometry, the longitudinal geometric interpolation, and the material participation law. Changing the station set or the requested output does not require modifying this member definition.

### 3.2 Action file

The action file specifies how the continuous model is sampled and which quantities are extracted. It does not redefine the member geometry.

```yaml
CSF_ACTIONS:
  stations:
    station_edge: [0,5]
  actions:
    - plot_volume_3d:
        params:
          title: "Not prismatic"         
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

### 3.3 Reusability across studies

The decoupling between member definition and numerical action is the principal design choice of the YAML workflow. Table 1 illustrates three typical uses of the same geometry file.

| Study | Station set | Purpose |
|---|---|---|
| Visual inspection | Dense uniform grid (100+ stations) | Section plots, centroid locus |
| Beam model input | 11 Gauss-Lobatto stations | OpenSees / BeamDyn tables |
| Reference comparison | Stations from external dataset | Validation against tabulated data |

In all cases the continuous geometric field is evaluated on demand; no re-meshing or re-definition of the member is required.

### 3.4 Interoperability with `sectionproperties`

Interoperability with `sectionproperties` is provided through two companion modules, `csf_sp` and `sp_csf`, available as both Python API and CLI tools. `csf_sp` exports polygonal geometry at requested stations to `sectionproperties` for full warping analysis. `sp_csf` performs the inverse operation, importing single geometries from `sectionproperties` into CSF, enabling the definition of members with geometrically distinct `S0` and `S1` cross-sections.

---

## 4. Station-wise evaluation and solver-facing output

A central feature of CSF is that station-wise data are generated from the continuous field. The user may request properties at arbitrary axial locations, including uniformly spaced stations, manually defined stations, or integration-compatible points.

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

#### Case A - undegraded tower

For the undegraded configuration, the stiffness field varies smoothly and monotonically. Convergence is rapid: a small number of beam elements is sufficient to reproduce the reference response with negligible error.

The transverse displacement $U_y$ converges at low discretization levels. The torsional rotation $R_z$ stabilises quickly and exhibits a small residual offset of approximately $3.44 \times 10^{-3}\,\%$ across all tested discretization levels. This offset is attributed to the thin-walled torsional approximation adopted internally by the CSF workflow, whereas the analytical reference uses the exact circular torsional constant $J = \tfrac{\pi}{2}(R_o^4 - R_i^4)$.

#### Case B - degraded tower

In the degraded configuration, the geometry is unchanged but the participation field $w_i(z)$ introduces localized stiffness reductions along a portion of the tower height. This produces sharper axial variation in the sectional stiffness distribution.

The convergence behaviour changes markedly relative to Case A. At low discretization levels the relative errors do not decrease monotonically with element count: the accuracy depends not only on the number of beam elements, but also on how well the sampling locations represent the degraded region of the stiffness field. Convergence stabilises once the discretization becomes sufficiently refined to resolve the localized variation.

This behaviour illustrates the main motivation for a continuous sectional representation. A coarse piecewise model with too few stations may miss or underrepresent local stiffness reductions, whereas the continuous field retains the full spatial description and the beam discretization can be refined independently until convergence is achieved.

#### Convergence results

Table 2 reports the relative errors in tip displacement $U_y$ and torsional rotation $R_z$ as a function of the number of beam elements, for both configurations.

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

---

## 6. Conclusion

The main contribution of CSF is the formulation of an independent, declarative pre-solver layer in which polygonal geometry and material participation fields are defined as continuous entities, evaluable at arbitrary axial stations and separable from the downstream numerical discretization.

---

## Acknowledgements

The author thanks the developers of `sectionproperties` for providing an open finite-element section-analysis ecosystem that can be used in validation and interoperability workflows.

---

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work, the author used ChatGPT and Claude for drafting assistance, copy-editing, and code-review suggestions. After using these tools, the author reviewed, edited, and validated the content as needed and takes full responsibility for the scientific claims, software implementation, and manuscript.


## References

- **[SUMMB_NREL]** G. Boscu, *Continuous Section Field: NREL validation comparison summary*, repository documentation, 2026.
Available: https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/nrel_case/validation_comparison_summary_all_b.md

- **[CSF_SP]** G. Boscu, *Continuous Section Field: Continuous Section Field csf_sp User Guide*  repository documentation, 2026.
Available: https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_user_guide.md

- **[FULL_AN]** G. Boscu, *Continuous Section Field: Section Full Analysis Output*  repository documentation, 2026.
Available: [https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_user_guide.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md)

- **[SAINT_VEN]** G. Boscu, *Continuous Section Field: Saint-Venant Torsional Constant* repository documentation, 2026.
Available:[ [https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_user_guide.md](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md)](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md)](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md)

# A Field-Based Framework for the Continuous Modelling of Non-Prismatic Structural Members

## Abstract

Continuous Section Field (CSF) is a field-based computational framework for representing sectional geometry, material participation, and derived section properties as continuous functions along a member axis. CSF is neither a structural solver nor a geometry kernel; instead, it connects these domains by transforming member-level geometric and material descriptions into continuous section-property fields and station-wise data suitable for beam, tower, bridge, and finite-element workflows.

The central idea of CSF is to treat the cross-section as a field defined along the member axis, rather than as a single isolated object. The geometry is specified at reference stations and obtained by interpolating corresponding polygon vertices between them, producing continuous intermediate cross-sections. Material participation, by contrast, is not interpolated between stations but prescribed as a continuous longitudinal field along the member axis. At any requested station, CSF combines the interpolated geometry with the participation field to evaluate properties such as area, centroid, second moments of area, principal inertias and section moduli

CSF makes an explicit separation between the geometric description of the member and the sectional participation fields that govern its mechanical contribution. Two longitudinal material participation fields define how much each region contributes: the axial/bending field $w_i(z)$ and the shear/torsion field $\kappa_i(z)$. Their independence is foundational to CSF: the model imposes no relation between the two, so each field can be specified on its own. These fields can represent stiffness ratios, degraded regions, reinforcement, voids, density-like quantities, or other user-defined sectional contributions. When both derive from elastic behaviour, they may optionally be coupled through an isotropic relation, each varying with the longitudinal coordinate and with geometric quantities.

The continuous model can be defined through a Python API or through a declarative YAML workflow. In the YAML workflow, one file defines the continuous member and another file defines the requested computations, plots, inspections, station sampling, and exports. The YAML file does not define a discrete table of section properties; it defines the geometry and the participation fields from which CSF constructs the continuous section-property fields.

This distinction allows CSF to preserve a continuous member representation while generating solver-facing station-wise data when required.

## 1. Motivation

In current structural analysis practice, the definition of section properties for non-prismatic members is typically embedded within the solver itself. Geometry and material participation are not treated as independent fields; instead, they are collapsed into a discrete table of section properties evaluated at a fixed set of stations, tied to the solver mesh and conventions. This coupling makes the sectional model difficult to inspect, reuse, or transfer across different solvers, and it obscures the distinction between the continuous physical model and its numerical discretisation.

Many structural and mechanical engineering problems involve members whose cross-section changes along their length: tapered towers, variable-depth beams, haunched bridge girders, repaired or degraded members, hybrid material sections, and staged or homogenized structural models. In these cases, the required input for a numerical model is not a single section, but a longitudinal field of section properties such as $A(z)$, $I_x(z)$, $I_y(z)$, $EI_x(z)$, $GJ(z)$, and mass-related quantities. When this field is defined inside the solver, it cannot be validated, inspected, or reused independently.

CSF addresses this by extracting the sectional field definition into a dedicated pre-solver layer. A member is represented as a continuous sectional field composed of evolving polygonal geometry together with two material participation fields: the axial/bending field $w_i(z)$ and the shear/torsion field $\kappa_i(z)$. This representation is defined, evaluated, inspected, and validated independently of any downstream solver. The solver receives a station-wise projection of an already defined continuous field - not a table that defines the model itself.

The result is a clean separation between three concerns that are normally conflated: the continuous physical model of the member, the numerical sampling strategy required by the solver, and the exported data format consumed by a specific tool.

Cross-section analysis tools such as VABS [REF] and BECAS [REF] provide accurate computation of beam sectional properties for arbitrary geometries and composite materials, and are widely adopted in wind-turbine and aerospace applications. Open-source alternatives such as `sectionproperties` [REF] offer similar capabilities within a Python ecosystem. These tools are primarily designed to analyse individual cross-sections: given a sectional geometry and material definition, they return the corresponding sectional properties at that station.

The longitudinal variation of the member - including tapering geometry, spatially varying material participation, or local stiffness degradation - is therefore usually represented outside the section-analysis tool, either through user-defined station tables or through the discretization adopted by the downstream structural solver. As a consequence, the sectional description is often tied to a specific mesh or analysis workflow, rather than being defined as an independent continuous model.

On the theoretical side, Balduzzi et al. [Balduzzi 2016] showed that non-prismatic beam analysis requires the axial derivatives of cross-sectional quantities, such as $\frac{dA}{dz}$ and $\frac{dI}{dz}$, as explicit terms in the governing equations. The formulation therefore depends on continuous sectional functions, not solely on values evaluated at discrete stations. This highlights the need for programmable descriptions capable of generating consistent geometric and constitutive quantities, and their axial variation, at arbitrary locations along the member axis.

Existing frameworks for the analysis of non-prismatic members can be grouped into three categories. First, sectional analysis tools such as VABS, BECAS, and `sectionproperties` compute the properties of individual cross-sections with high accuracy, while the longitudinal variation of the member is handled externally. Second, structural solvers such as OpenSees, ABAQUS, and ANSYS incorporate non-prismaticity through the adopted finite-element formulation, typically by evaluating sectional properties at nodes, integration points, or user-defined stations. 


Third, wind-energy simulation and design workflows embed non-prismaticity in application-specific representations. Aeroelastic codes such as [NREL OpenFAST; Wang et al. 2017](#) rely on distributed sectional-property tables along the member axis, whereas systems-engineering tools such as NREL's WISDEM [NREL WISDEM] represent the tower as a tapered circular tube with closed-form sectional properties, analysed through the external frame finite-element code Frame3DD [Gavin]. In both cases the longitudinal variation is bound to a specific geometry or workflow rather than expressed as an independent, reusable sectional field.


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

The Saint-Venant torsional constant is a notable exception. Area-integral properties are separable - geometry and participation factor cleanly - but Saint-Venant torsion is not: the torsional constant cannot be reduced to a weighted area integral, because the warping field couples geometry and material across the section. CSF therefore treats torsion separately. For sections tagged as closed cells or open thin walls, CSF evaluates an internal geometric torsional constant from thin-walled approximations (the Bredt formula for closed cells and the $b\,t^3/3$ estimate for open walls), and the shear/torsion participation enters as a single section-level value rather than zone by zone. For general solid sections, multi-cell configurations, connected cell–wall systems, or cases requiring higher accuracy, the continuous geometric field can be passed to `sectionproperties` through the CSF bridge `csf_sp` for a full warping analysis, while retaining the same continuous geometric and participation-field description.

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
- endpoint participation values;
- longitudinal laws for $w_i(z)$ and $\kappa_i(z)$.

The action file defines:

- station sets;
- plots;
- section inspections;
- property evaluations;
- exports;
- validation-oriented outputs.

This separation makes the same continuous model reusable across different numerical studies. A single member definition can be sampled at dense stations for inspection, at Gauss-Lobatto stations for quadrature-compatible beam input, or at user-defined stations for comparison with external data.

### 3.1 Geometry file

The geometry file defines the continuous sectional model. The example below describes a tapered polygonal section between two reference stations. The cross-section is reduced from `S0` to `S1`, while the axial/bending field follows an independent parabolic law along the member axis. The shear/torsion field is derived from $w_i$ through an isotropic relation.

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

The example separates three ingredients that are usually collapsed into a single tabulated section-property description: the reference geometry, the longitudinal geometric interpolation, and the material participation law. Changing the station set or the requested output does not require modifying this member definition.

### 3.2 Action file

The action file specifies how the continuous model is sampled and which quantities are extracted. It does not redefine the member geometry.

```yaml
CSF_ACTIONS:
  stations:
    station_edge: [0,5]
  actions:
    - plot_volume_3d:
        params:
          title: "Not prismatic"         
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

### 3.3 Reusability across studies

The decoupling between member definition and numerical action is the principal design choice of the YAML workflow. Table 1 illustrates three typical uses of the same geometry file.

| Study | Station set | Purpose |
|---|---|---|
| Visual inspection | Dense uniform grid (100+ stations) | Section plots, centroid locus |
| Beam model input | 11 Gauss-Lobatto stations | OpenSees / BeamDyn tables |
| Reference comparison | Stations from external dataset | Validation against tabulated data |

In all cases the continuous geometric field is evaluated on demand; no re-meshing or re-definition of the member is required.

### 3.4 Interoperability with `sectionproperties`

Interoperability with `sectionproperties` is provided through two companion modules, `csf_sp` and `sp_csf`, available as both Python API and CLI tools. `csf_sp` exports polygonal geometry at requested stations to `sectionproperties` for full warping analysis. `sp_csf` performs the inverse operation, importing single geometries from `sectionproperties` into CSF, enabling the definition of members with geometrically distinct `S0` and `S1` cross-sections.

---

## 4. Station-wise evaluation and solver-facing output

A central feature of CSF is that station-wise data are generated from the continuous field. The user may request properties at arbitrary axial locations, including uniformly spaced stations, manually defined stations, or integration-compatible points.

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

#### Case A - undegraded tower

For the undegraded configuration, the stiffness field varies smoothly and monotonically. Convergence is rapid: a small number of beam elements is sufficient to reproduce the reference response with negligible error.

The transverse displacement $U_y$ converges at low discretization levels. The torsional rotation $R_z$ stabilises quickly and exhibits a small residual offset of approximately $3.44 \times 10^{-3}\,\%$ across all tested discretization levels. This offset is attributed to the thin-walled torsional approximation adopted internally by the CSF workflow, whereas the analytical reference uses the exact circular torsional constant $J = \tfrac{\pi}{2}(R_o^4 - R_i^4)$.

#### Case B - degraded tower

In the degraded configuration, the geometry is unchanged but the participation field $w_i(z)$ introduces localized stiffness reductions along a portion of the tower height. This produces sharper axial variation in the sectional stiffness distribution.

The convergence behaviour changes markedly relative to Case A. At low discretization levels the relative errors do not decrease monotonically with element count: the accuracy depends not only on the number of beam elements, but also on how well the sampling locations represent the degraded region of the stiffness field. Convergence stabilises once the discretization becomes sufficiently refined to resolve the localized variation.

This behaviour illustrates the main motivation for a continuous sectional representation. A coarse piecewise model with too few stations may miss or underrepresent local stiffness reductions, whereas the continuous field retains the full spatial description and the beam discretization can be refined independently until convergence is achieved.

#### Convergence results

Table 2 reports the relative errors in tip displacement $U_y$ and torsional rotation $R_z$ as a function of the number of beam elements, for both configurations.

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

---

## 6. Conclusion

The main contribution of CSF is the formulation of an independent, declarative pre-solver layer in which polygonal geometry and material participation fields are defined as continuous entities, evaluable at arbitrary axial stations and separable from the downstream numerical discretization.

---

## Acknowledgements

The author thanks the developers of `sectionproperties` for providing an open finite-element section-analysis ecosystem that can be used in validation and interoperability workflows.

---

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work, the author used ChatGPT and Claude for drafting assistance, copy-editing, and code-review suggestions. After using these tools, the author reviewed, edited, and validated the content as needed and takes full responsibility for the scientific claims, software implementation, and manuscript.


## References

- **[Balduzzi 2016]** <a id="Balduzzi-2016"></a>  *Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). Non-prismatic beams: A simple and effective Timoshenko-like model. International Journal of Solids and Structures*, 90, 236–250.
  https://doi.org/10.1016/j.ijsolstr.2016.02.017

- **[VABS]** <a id="vabs"></a> *Variational Asymptotic Beam Sectional Analysis*.  https://analyswift.com/vabs/

- **[NRELOpenFAST]**  <a id="NRELOpenFAST "></a> *National Renewable Energy Laboratory. OpenFAST: open-source wind turbine simulation tool*. https://github.com/OpenFAST/openfast
- **[NREL WISDEM]** <a id="wisdem "></a>  *National Renewable Energy Laboratory. *WISDEM: Wind-Plant Integrated System Design and Engineering Model*. https://github.com/WISDEM/WISDEM

- **[SEC_PROP]** <a id="sec_prop"></a>  *python package for the analysis of arbitrary cross-sections using the finite element method.*.
https://github.com/robbievanleeuwen/section-properties
- **[WANG]**  <a id="wang"></a>   *Wang et al. 2017 - Wang, Q., Sprague, M. A., Jonkman, J., Johnson, N., & Jonkman, B. (2017). BeamDyn: A High-Fidelity Wind Turbine Blade Solver in the FAST Modular Framework. Wind Energy, 20(8), 1439–1462*.  https://doi.org/10.1002/we.2101
  
- **[NRELOpenFAST]**  <a id="NRELOpenFAST"></a>  *National Renewable Energy Laboratory. OpenFAST: open-source wind turbine simulation tool.*.
  https://github.com/OpenFAST/openfast
  
- **[Gavin]**  <a id="gavin"></a>  *Gavin, H. P. *Frame3DD: Static and dynamic structural analysis of 2D and 3D frames.* http://frame3dd.sourceforge.net/

- **[BECAS]**  <a id="becas"></a> *Finite-element-based cross-sectional analysis software*. https://becas.dtu.dk/

---
  
- **[SUMMB_NREL]** *G. Boscu, Continuous Section Field: NREL validation comparison summary*, repository documentation, 2026.
https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/aes/nrel_case/validation_comparison_summary_all_b.md

- **[CSF_SP]** *G. Boscu, Continuous Section Field: Continuous Section Field csf_sp User Guide*  repository documentation, 2026.
 https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_user_guide.md

- **[FULL_AN]** *G. Boscu, Continuous Section Field: Section Full Analysis Output*  repository documentation, 2026.
https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/sectionfullanalysis.md

- **[SAINT_VEN]** G. Boscu, *Continuous Section Field: Saint-Venant Torsional Constant* repository documentation, 2026.
Available: https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/sections/DeSaintVenantTorsionalConstant%20.md

---


  


