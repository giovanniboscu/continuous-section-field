# Reference C-section -  E. Carrera and M. Petrolo, *Refined beam elements with only displacement variables and plate/shell capabilities*

The document is organized into two parts, devoted respectively to the description of the models and their application to a reference case.

**Part I – Models and organization of the computation** presents the overall system architecture, distinguishing the roles of the CSF physical model, the CSF–CUF structural model, and the three-dimensional FEM3D model. Their respective formulations, the organization of the computational components, and the procedure leading from the geometric and material description to the structural solution are described.

**Part II – Application to the C-section cantilever benchmark** illustrates a practical application of the models described in the first part. It presents the structural problem, the numerical configurations, the execution and reproducibility procedures, and the comparison between the CSF–CUF and FEM3D solutions through the analysis of displacement, strain, and stress fields.

The appendices reproduce in full the configuration files used, allowing the analyzed case to be reconstructed.

## Part I - Models and organization of the computation

Roles of CSF, CSF–CUF, and FEM3D and relationships among the three approaches.


### 1.1 The fundamental distinction


| Object | What it represents | What it receives | What it produces |
|---|---|---|---|
| **CSF - Continuous Section Field** | The **physical model of the section** along the axis: geometric domains, coordinates, and material properties | Description of geometry, length, stations, and materials | Standalone model for the continuous description of geometry and materials along the longitudinal axis, the generation of geometries and material distributions, and the calculation of classical sectional properties, also through integration with sectionproperties. Accessible via a graphical interface, CLI, and Python library |
| **CSF–CUF** | The **structural model** that uses the CUF formulation and queries CSF for geometry and materials | CSF + CUF transverse functions + longitudinal elements + loads and constraints | General system not restricted to specific geometries or kinematics; assembly of the stiffness matrix and load vector, solution of the generalized CUF unknowns, and reconstruction of the three-dimensional displacement, strain, and stress fields. |
| **FEM3D** | Independent three-dimensional reference model developed with OpenSeesPy and H8 hexahedral solid elements (stdBrick) | Geometry and materials obtained from CSF, conforming volumetric mesh, loads and constraints consistent with CUF, linear elastic analysis | Displacements, strains, and stresses, evaluated element by element without smoothing |



The name **CSF–CUF** therefore denotes a *coupling*: **CSF describes the physical domain**, while **CUF defines the displacement approximation and equilibrium equations**. In this document, FEM3D represents a **second numerical solution to the same physical problem**, obtained with different unknowns and a different discretization from CSF–CUF.

### 1.2 Logical diagram of the models

                      SHARED PHYSICAL PROBLEM
                   geometry, materials,
                       loads and constraints
                              |
                              v
                     CSF PHYSICAL MODEL
                    geometry and materials
                     continuous along the axis
                              |
               +--------------+--------------+
               |                             |
               v                             v
      STRUCTURAL MODEL                  FEM3D MODEL
           CSF–CUF                     H8 volumetric mesh
      - L9 expansion                   - solid elements
      - elements along x               - 3D discretization
      - numerical integration          - assembly/equilibrium
      - assembly/equilibrium                 |
               |                             |
               v                             v
      displacements u(x,y,z)           displacements u(x,y,z)
      and CSF–CUF stresses             and FEM3D stresses
               |                             |
               +-------------+---------------+
                             |
                             v
                     NUMERICAL COMPARISON
                same points and physical components


**CSF supplies both solvers**, CSF–CUF and FEM3D, providing a common, continuous physical description of geometry and materials. The two solvers retain independent structural formulations and numerical discretizations.

### 1.3 CSF–CUF: how the CSF infrastructure is used in CUF

The configuration of a CSF–CUF analysis is organized into three readable YAML text files, separating the physical description, the definition of the structural problem, and the choices of discretization and numerical solution. The contents and structure of all three files are reproduced in full in the appendices.

| YAML file | Function |
|---|---|
| **`model`** | Defines the CSF physical model: geometry, longitudinal stations, and material properties. |
| **`problem`** | Defines the structural problem, including loads and boundary conditions. |
| **`case`** | Links the model and problem, selects the transverse expansions, longitudinal discretization, and integration and solution parameters. |

This organization makes it possible to combine different physical models, structural problems, and numerical approximations without modifying the core CUF formulation.


For the numerical case examined, the three configuration files are:

| Configuration | YAML file | Reference |
|---|---|---|
| **Model** | `c_section_chapter9_5_3_9L9_`<br>`csf.yaml` | Appendix A |
| **Problem** | `c_section_cantilever_`<br>`point_9L9.yaml` | Appendix B |
| **Case** | `c_section_table_9_13_`<br>`lagrangeL9_E10.yaml` | Appendix C |

The three files are reproduced in full in their respective appendices and described in the following sections.


The **structural formulation remains CUF**. What distinguishes the CSF–CUF implementation is the organization of the computation: geometry/materials, transverse expansion, and longitudinal discretization are defined in separate components and connected during assembly. The continuous description of the section provided by CSF enters directly into the representation of the CUF sectional nuclei, without requiring the derivation of expressions specialized for the specific geometry, as in the case of the C-section.





```
  CSF: geometry + materials         CUF MODULE: transverse expansion
  ┌────────────────────────┐        ┌───────────────────────────────┐
  │9 quadrilateral domains │        │ L9: functions and derivatives │
  │ coordinates + material │        │ shared_points connectivity    │
  └───────────┬────────────┘        └───────────────┬───────────────┘
              │                                     │
              └─────────────────┬───────────────────┘
                                ▼
                   SECTIONAL EVALUATION
                   ┌───────────────────────────────┐
                   │ Physical quadrature points    │
                   │ mappings and Jacobians        │
                   │ L9 functions/derivatives      │
                   │ local elastic properties      │
                   │ CUF nuclei/contributions      │
                   └───────────────┬───────────────┘
                                   │
        LONGITUDINAL ELEMENTS     │
        ┌────────────────────────┐ │
        │ E10, order 12           ├─┤
        │ quadrature along x     │ │
        └────────────────────────┘ ▼
                       CUF ASSEMBLY
                   ┌───────────────────────────────┐
                   │ stiffness, loads, constraints │
                   │ solution of CUF unknowns      │
                   └───────────────┬───────────────┘
                                   ▼
                         POSTPROCESSING
                    displacements and stresses
                    reconstructed in space

```
The operational sequence is as follows:

1. The CUF case selects a **CSF model** and a **problem** (loads and constraints).
2. The external transverse plugin selects the **L9** family, without containing the dimensions of the C-section.
3. The sectional computation queries CSF at the integration points and evaluates the L9 functions on the resulting domains.
4. The sectional contributions are combined with the longitudinal elements; the CUF equations are assembled and solved.
5. Displacements are reconstructed from the field of generalized CUF unknowns; strains and stresses are subsequently calculated using the kinematic and constitutive relations, for comparison with the FEM3D volumetric model.

**Separation of responsibilities:** CSF specifies *where the material is and what properties it has*; the CUF expansion specifies *how the transverse field is represented*; the longitudinal element specifies *how it varies along the beam*; the CUF engine performs *equilibrium, assembly, and solution*. 


To enable direct use of the continuous section description provided by CSF, an explicit dependence of the sectional nuclei on the longitudinal coordinate has been introduced. Using the continuous description leaves the kinematics, the principle of virtual work, and the general structure of the original CUF formulation unchanged.


For a formal treatment, see [CSF–CUF: Formulation for Directly Prescribed Variable Sections](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md).



>CUF transverse expansions and longitudinal shape functions are implemented as Python components independent of the physical description of the section. Their respective functions and derivatives are defined once and can be reused with different geometric and material models, without modifying the general formulation or the CUF assembly core.


### 1.4 FEM3D: independent structural solution

FEM3D is a **second solution model**, built with three-dimensional H8 solid elements in OpenSees, in which nodal displacements are the unknowns of the volumetric discretization.


```text
       SAME PHYSICAL PROBLEM
                 │
                 ▼
       C-SECTION OUTLINE
       single 8-vertex polygon
                 │
                 ▼
       H8 VOLUMETRIC MESH
       (discretization of the entire volume)
                 │
                 ▼
       OpenSees: assembly and solution
                 │
                 ▼
       3D nodal displacements
       + element-derived stresses
                 │
                 ▼
       COMPARISON WITH CSF–CUF
```

The single eight-vertex outline is used **solely for convenience in generating the FEM3D mesh**; it describes the same C-section that CSF–CUF divides into nine domains. The comparison is independent in terms of displacement discretization, but not in terms of the shared physical problem. 

## 2. CSF model: geometric and material representation

### 2.1 Purpose of the Continuous Section Field

CSF is the **layer representing physical reality**. At a requested longitudinal station, it returns the sectional domain, its geometry, and material properties. It does not select the kinematics, build a stiffness matrix on its own, or solve the equilibrium problem.






```
      CSF MODEL (physical description)
      ┌──────────────────────────────────────┐
      │ Stations along the axis              │
      │  └─ sectional domains                │
      │      ├─ vertices and boundaries      │
      │      ├─ materials                    │
      │      └─ longitudinal variations      │
      └──────────────────┬───────────────────┘
                         │ queries
                         ▼
            Local geometry and materials
            available to the CUF model
```

CSF provides the geometric and material support on which a transverse expansion can be evaluated and integrated.

### 2.2 Meaning of geometry–approximation independence

The description of shape, dimensions, and material remains within the CSF field. The transverse basis instead represents displacements over the given domain. This separation, rather than the specific C-section case, is the infrastructural contribution of the experiment: an L9 basis can be selected externally to the assembly core without hard-coding the C-section dimensions into the global formulation.

## 3. CUF model and its discretization

### 3.1 Organization of the CUF unknowns

The three-dimensional field is represented through **transverse functions** and **generalized degrees of freedom that evolve along the axis**. In this case, no mesh of solid elements is constructed to determine the CUF unknowns.

```text
 L9 functions on the section    Finite elements along the axis
           │                              │
           └──────────────┬───────────────┘
                          ▼
                Generalized unknowns
                   of the CUF model
                          │
                          ▼
                3D displacement field
                          │
                          ▼
                  Strains / stresses
```

The approach is standard CUF: what distinguishes this work is **where the geometry and sectional properties come from**, not the introduction of new unknowns or new equilibrium laws.


### 3.2 L9 transverse expansion

Each physical CSF quadrilateral is associated with a parametric domain and is assigned an **L9 expansion with nine interpolation points**, arranged on a 3 × 3 grid. The functions and their derivatives are provided by the transverse module, whereas geometry and material come from CSF.

```text
 CSF quadrilateral domain         L9 transverse interpolation
 ┌──────────────────────┐          o────────o────────o
 │                      │          │        │        │
 │ geometry and material│  ───►    o────────o────────o
 │                      │          │        │        │
 └──────────────────────┘          o────────o────────o
                                 9 points per domain
```

Geometrically coincident points on the boundaries of adjacent domains are shared through the transverse connectivity; therefore, the global number of unknowns is **not** obtained simply by multiplying nine by nine. As a separate module, the L9 basis does not contain hard-coded values for the C-section dimensions.

In the present implementation, the L9 module requires the section to be divided into quadrilateral domains compatible with the adopted isoparametric transformation. This requirement is specific to the transverse expansion used and does not constitute a general limitation of the CSF geometric representation or the CUF formulation.



>The transverse expansion is implemented in a Python module conforming to a predefined interface, which specifies how the functions and their derivatives are evaluated. This organization allows the same expansion to be used with different geometries and material distributions, independently of the CSF physical model.


### 3.3 From sectional integration to the solution

The engine uses contributions obtained at sectional quadrature points to assemble the CUF problem, together with information from the longitudinal elements. After solving, stresses and strains are derived from the reconstructed displacement field and the elastic constitutive law of the material.

```text
 physical coordinates + material (CSF)
                  +
 functions, derivatives and connectivity (L9)
                  │
                  ▼
           SECTIONAL QUADRATURE
       numerical evaluation of CUF nuclei
                  │
                  + elements along the axis
                  │
                  ▼
       ASSEMBLY + CONSTRAINTS + LOADS
                  │
                  ▼
          CUF MODEL SOLUTION
                  │
                  ▼
     RECONSTRUCTED 3D FIELDS AND STRESSES
```

The architectural benefit is to avoid integrated expressions or sectional routines **specific to each new geometry**, while leaving the CUF formulation unchanged. The MITC settings are reported in the case file without attributing unverified numerical effects to them.

## 4. FEM3D model: formulation of the solid reference

The numerical comparison is carried out using a three-dimensional finite-element model implemented with **OpenSeesPy**, employing eight-node hexahedral solid elements (`stdBrick`, H8) and a linear isotropic elastic material (`ElasticIsotropic`).

The model is generated by the driver [run_c_section_table_9_13_fem3d.py](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/fem3d/run_c_section_table_9_13_fem3d.py), version v8 dated 12 October 2026.

Geometry and material properties are obtained from the CSF model by querying the section along the beam's longitudinal axis. The FEM3D model uses the same reference physical data as the CSF–CUF problem, making it possible to compare the two discretizations without introducing an independent geometric description.

The mesh is structured and conforming, divided into three regions corresponding to the upper flange, web, and lower flange of the C-section, with nodes shared at the interfaces.

## Part II - Application to the C-section cantilever benchmark

## 5. Benchmark: objectives and structural problem

This case examines **two distinct questions**:

- **Model architecture:** whether the same CUF L9 expansion can be applied to geometry constructed externally in CSF, without deriving and programming sectional nuclei specific to the C-section.
- **Solution accuracy:** what differences arise relative to a solid FEM3D reference with this particular L9 expansion, the chosen longitudinal discretization, and the quadrature rules employed.



### 5.1 Geometry and coordinate system

The beam is prismatic, with its longitudinal axis identified by the physical coordinate **x** of the CUF/FEM3D model, over the interval `0 ≤ x ≤ 20000 mm`. The section plane uses the physical coordinates **(y,z)**. In the CSF file, for reasons related to the library interface, the longitudinal station is also denoted by the field's `z`: this **must not** be confused with the physical transverse coordinate `z`.

| Quantity | Value |
|---|---:|
| Cantilever length, L | 20.000 mm |
| Overall height, h | 1.000 mm |
| Thickness, t | 100 mm |
| Upper flange, b₂ | 1.000 mm |
| Lower flange, b₁ | 500 mm |
| Initial/final section | identical (prismatic beam) |

In the `(y,z)` plane, the section has the web on the right and the opening facing left. The bounds are: upper flange `−1000 ≤ y ≤ 0`, `400 ≤ z ≤ 500`; web `−100 ≤ y ≤ 0`, `−400 ≤ z ≤ 400`; lower flange `−500 ≤ y ≤ 0`, `−500 ≤ z ≤ −400`. The union of the three rectangles has no overlapping areas.

One representation is:


![Partition of the C-section into nine quadrilaterals](CSF_CUF_Carrera_assets/sezione_c_nove_domini.png)

*Figure 1 - Physical outline and sectional partition into the nine CSF domains used by the L9 expansion. Figure reconstructed directly from the YAML coordinates reported in this document*


### 5.2 Material

Linear isotropic elasticity is assumed, with `E = 75000 MPa` and `ν = 0.33`. The corresponding shear modulus is approximately **28.195,49 MPa**.

The units used consistently are **mm, N, MPa**. In the CSF file, the parameter `weight: 75000.0`, present in each polygon, represents **Young's elastic modulus \(E = 75\,000\) MPa**, not a volumetric density. The declaration `shear_weight_laws: ['iso(0.33)']` specifies an isotropic constitutive law with **Poisson's ratio \(\nu = 0.33\)**. These parameters are interpreted by the CSF–CUF coupling to define the elastic properties of the material used in the experiment.

### 5.3 Constraint and force

The initial section at `x = 0` is fully clamped. In the solid model, the constraint is imposed as `u_x = u_y = u_z = 0` for all nodes belonging to the initial section; in the CUF model, it acts on the generalized degrees of freedom in a manner consistent with a vanishing displacement field at the clamped section.

The load specified by the problem is a **concentrated force of magnitude −1 N in the global z direction**, applied at `(x,y,z) = (20000,0,−500) mm`. The action is therefore localized at the free end, at a point on the section. Representing a point force can produce highly localized, discretization-dependent stress fields near the point of application. Direct comparison of pointwise stress maxima in these regions should be treated with caution.

## 6. Numerical configuration of the benchmark

### 6.1 CSF partition into nine quadrilateral domains

In this case, CSF describes a prismatic C-section divided into nine physical quadrilaterals. **The quadrilaterals are not FEM3D solid elements**: they provide the geometric and material support on which CSF–CUF evaluates the L9 basis and sectional integrals. The division into nine domains corresponds to the L9 transverse representation selected for the benchmark.

| CSF domain | y range (mm) | z range (mm) | Region |
|---|---|---|---|
| `top_1` | −1000 … −775 | 400 … 500 | upper flange |
| `top_2` | −775 … −550 | 400 … 500 | upper flange |
| `top_3` | −550 … −325 | 400 … 500 | upper flange |
| `top_4` | −325 … −100 | 400 … 500 | upper flange |
| `top_web_corner` | −100 … 0 | 400 … 500 | upper junction |
| `web` | −100 … 0 | −400 … 400 | web |
| `bottom_1` | −500 … −300 | −500 … −400 | lower flange |
| `bottom_2` | −300 … −100 | −500 … −400 | lower flange |
| `bottom_web_corner` | −100 … 0 | −500 … −400 | lower junction |

The free portion of the upper flange, 900 mm wide, is divided into four 225 mm segments; the lower one, 400 mm wide, into two 200 mm segments. The two junction regions with the web each occupy 100 mm in the y direction. Each polygon is defined by vertices ordered along its boundary and appears with the same identity in `S0` and `S1`.

### 6.2 Longitudinal discretization and integration of case E10

The case file selects ten intervals with normalized longitudinal boundaries:

`[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]`.

The boundaries correspond to `x = 0,2000,…,20000 mm`. A Lagrange basis of **order 12** and longitudinal quadrature of **order 15** are specified for each element. Sectional integration is `fixed_gauss_polygon` with `gauss_order: 9`. The model is prismatic and the material has no polynomial variation along the axis (`material_polynomial_degree: 0`).


In this case, a Lagrange longitudinal shape function already available in the Python library is used. As with the transverse expansions, new shape functions can nevertheless be developed in Python, provided they comply with the interface and implementation rules defined by the CSF–CUF model. The functions defined in this way remain independent of the physical model and can be reused with different geometries and materials.



### 6.3 Operational choices for the case

The external expansion is loaded from `lagrangeL9_v4.py`; the domains are selected with `domain_source: csf_polygons`; the mapping is `isoparametric`; connectivity is `shared_points`; the declared geometric tolerance is `1.0e-10`; `require_prismatic: true` prevents unintended use with a non-prismatic case. The `correctionMITC: true` and `verifyMITCAssembly: true` checks/corrections are enabled, with requested equilibration iterations `[1,2,3,4,5]`. 
The sampling stations in the file are `[0.0,0.1,1.0]`, interpreted in the interface context as longitudinal parameters to be checked with the postprocessor; `displacement_samples: 201` and `stress_grid: 41` control output sampling.

### 6.4 FEM3D discretization and application of the problem

The discretization used in the reference simulation is as follows:

| Region or direction | Subdivisions |
|---|---:|
| Longitudinal direction (`nx`) | 200 |
| Free extent of the upper flange (`ny-top-free`) | 18 |
| Free extent of the lower flange (`ny-bottom-free`) | 18 |
| Web width (`ny-web`) | 10 |
| Flange thickness (`nz-flange`) | 10 |
| Free web height (`nz-web`) | 18 |

The beam has length \(L=20000\ \mathrm{mm}\). The concentrated force \(F_z=-1\ \mathrm{N}\) is applied at the free end, at the point with CUF coordinates \((x,y,z)=(20000,0,-500)\ \mathrm{mm}\), corresponding to a vertex of the C-section.

This point already coincides with a node of the adopted FEM3D discretization; therefore, no additional subdivisions are needed to apply the load. The force is applied directly to the corresponding node, without distribution among adjacent nodes.

The clamped boundary condition is imposed over the entire initial section of the beam, setting all three displacement components to zero at the nodes belonging to that section.

The analysis is linear static. The coordinate system and physical units are consistent with those adopted in the CSF–CUF model (mm, N, MPa).

The algebraic system is solved using OpenSees, with `UmfPack` and `RCM` ordering, with the possibility of falling back to the `SparseGeneral -piv` solver in case of failure.

## 7. Execution and reproducibility

### 7.1 Running the FEM3D model

From the `cuf/c-shape` directory, the reference FEM3D model is run using:

```bash
python3 fem3d/run_c_section_table_9_13_fem3d.py \
  models/c_section_chapter9_5_3_csf.yaml \
  problems/c_section_table_9_13.yaml \
  fem3d/c_section_table_9_13_a.npz \
  --nx 200 \
  --ny-top-free 18 \
  --ny-bottom-free 18 \
  --ny-web 10 \
  --nz-flange 10 \
  --nz-web 18
```

The numerical solution is exported to the file:

`fem3d/c_section_table_9_13_a.npz`

This file is the FEM3D reference used in subsequent postprocessing operations and comparison with the CSF–CUF solution.

### 7.2 Running the CSF–CUF process

The CSF–CUF analysis is started from the `continuous-section-field/cuf/c-shape` directory using the command:

```bash
csf-cuf cases/c_section_table_9_13_lagrangeL9_E10.yaml
```

The command carries out the assembly and solution process for the structural system according to the configurations of the physical model, the problem, and the numerical approximation described in the preceding sections.

The execution results are available in the directory:

```text
cuf/c-shape/output/c_section_table_9_13_lagrangeL9_v4_E10/
```

For the run with one equilibration iteration (`eq1`), two files are present:

| File | Contents |
|---|---|
| `c_section_table_9_13_lagrangeL9_v4_E10_eq1.cuf.npz` | Numerical archive of the CUF solution, used to reconstruct and postprocess displacement fields and derived quantities. |
| `response_eq1.txt` | Text output of the execution, containing results and diagnostic information recorded by the process. |

The `.cuf.npz` file is the numerical reference for subsequent postprocessing operations, while `response_eq1.txt` allows the textual response produced by the solver to be consulted.


### 7.3 Postprocessing and comparison with FEM3D

Postprocessing of the CSF–CUF solution is performed using the tool 

`csf.cuf.tools.plot_strain_stress_boundary_v10`

which uses the numerical `.cuf.npz` checkpoint produced by the solver and the original CSF model to reconstruct displacement, strain, and stress fields.

From the `cuf/c-shape` directory, postprocessing and comparison with FEM3D are performed using the command:


```bash
python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 \
  --csf-yaml models/c_section_chapter9_5_3_9L9_csf.yaml \
  --checkpoint output/c_section_table_9_13_lagrangeL9_v4_E10/\
c_section_table_9_13_lagrangeL9_v4_E10_eq1.cuf.npz \
  --fem3d fem3d/c_section_table_9_13_a.npz \
  --fem-stress-from-csf
```



The evaluation is carried out along the beam axis at the vertices of the polygons defining the cross-section. Each vertex retains its polygon affiliation, allowing stress values on different sides of the interfaces to be distinguished. The reconstructed fields are represented by PNG plots, organized by component and vertex.

The numerical values used for plotting are also available in NPZ format and can be exported to a single CSV file using the `--csv` option. For each sampled point, the CSV includes the coordinates, polygon and vertex identifiers, and all displacement, strain, and stress components, making it possible to reconstruct the curves shown in the plots and perform independent quantitative analyses.

The comparison with FEM3D is performed at the same physical sampling positions, evaluating displacements and strains directly from the H8 solid elements. FEM3D stresses are reconstructed by applying the constitutive law defined by the CSF model to the strains, provided the physical material distribution is consistent between the two models.

The sampled FEM3D results are saved separately in NPZ and CSV formats, making the numerical values used in the comparison available.

The postprocessing procedure operates on the already computed solutions without introducing regularization or re-equilibration of the stress fields.

## 8. Presentation of results

### 8.1 Presentation of results

The results of the CSF–CUF/FEM3D comparison are presented through graphical representations of displacements, strains, and stresses, evaluated at the vertices of each polygon in the CSF section. Sampling thus covers numerous points distributed over the entire section, while maintaining the same physical positions and reference conventions for both models.

The plots make it possible to examine the agreement between the two solutions, highlighting both the overall field behavior and any local differences.

The results are organized by physical component and sampling position, distinguishing displacements from derived quantities.




### 8.2 Selection of CSF–CUF / FEM3D plots

**Case:** `c_section_table_9_13_lagrangeL9_v4_E10_eq1`  
**Source:** [Original gallery of 75 plots](https://github.com/giovanniboscu/continuous-section-field/blob/main/cuf/c-shape/strain_stress_boundary/README.md)




### Transverse displacement `u_z`

Component directly related to the load direction; first comparison of the displacement field.

![Transverse displacement `u_z` - uz_along_boundary_part01.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uz_along_boundary_part01.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uz_along_boundary_part01.png)

### Transverse displacement `u_z`

Extension of the comparison to another group of vertices.

![Transverse displacement `u_z` - uz_along_boundary_part03.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uz_along_boundary_part03.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uz_along_boundary_part03.png)

### Transverse displacement `u_z`

Further group of vertices: check of representativeness across the section.

![Transverse displacement `u_z` - uz_along_boundary_part05.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uz_along_boundary_part05.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uz_along_boundary_part05.png)

### Longitudinal displacement `u_x`

Also show the axial component, as distinct from transverse bending.

![Longitudinal displacement `u_x` - ux_along_boundary_part03.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/ux_along_boundary_part03.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/ux_along_boundary_part03.png)

### Displacement `u_y`

Complete the examination of the three kinematic components.

![Displacement `u_y` - uy_along_boundary_part03.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uy_along_boundary_part03.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/uy_along_boundary_part03.png)

### Normal stress `σ_xx`

Begin the comparison of longitudinal normal stresses.

![Normal stress `σ_xx` - sigma_xx_along_boundary_part01.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/sigma_xx_along_boundary_part01.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/sigma_xx_along_boundary_part01.png)

###  Normal stress `σ_xx`

Extend the comparison to a second group of vertices.

![Normal stress `σ_xx` - sigma_xx_along_boundary_part03.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/sigma_xx_along_boundary_part03.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/sigma_xx_along_boundary_part03.png)

### Shear stress `τ_xz`

Consider the shear component associated with the longitudinal–transverse plane of the load.

![Shear stress `τ_xz` - tau_xz_along_boundary_part03.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xz_along_boundary_part03.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xz_along_boundary_part03.png)

### Shear stress `τ_xy`

Include the other longitudinal shear component, useful for highlighting the three-dimensional response.

![Shear stress `τ_xy` - tau_xy_along_boundary_part03.png](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xy_along_boundary_part03.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xy_along_boundary_part03.png)


### Shear stress τ_xz 

![Shear stress τ_xz - group 5](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xz_along_boundary_part05.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/tau_xz_along_boundary_part05.png)

### Strain γ_xz

![Strain γ_xz](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/gamma_xz_along_boundary_part03.png)

[Open the original PNG](https://raw.githubusercontent.com/giovanniboscu/continuous-section-field/main/cuf/c-shape/strain_stress_boundary/c_section_table_9_13_lagrangeL9_v4_E10_eq1/gamma_xz_along_boundary_part03.png)

## 9. Conclusions

### Interpretation of the CSF–CUF and FEM3D comparison

The comparison shows very close agreement between the displacement fields obtained with CSF–CUF and FEM3D, with trends and values that almost overlap along the beam.

The stress fields also show good agreement, although some considerations are required because of the different ways in which the results are represented.

In FEM3D, stresses are evaluated on individual finite elements, without nodal averaging or regularization. Consequently, different values of the same stress component may be present at the same geometric vertex shared by adjacent elements. This behavior is consistent with the finite-element formulation, in which continuity of displacements does not necessarily imply continuity of stresses.

In CSF–CUF, by contrast, stresses are derived directly from the solution field through kinematic and constitutive relations. It is therefore consistent that CSF–CUF values often lie between those returned by adjacent FEM3D elements. This behavior does not arise from any averaging of FEM3D results, but emerges from the independent solution provided by CSF–CUF.

The overall agreement between the results is good for stresses as well, although local deviations and, in some cases, more pronounced oscillations can be observed, especially in regions near the constraints. These differences must be assessed by distinguishing interelement variability in FEM3D stresses from actual differences between the solution fields.

Overall, the results show that the close agreement observed in displacements is accompanied by good agreement in stresses too, albeit with the local differences highlighted by the plots.

# Appendix A - Complete CSF model configuration

This file is the physical model `c_section_chapter9_5_3_9L9_csf.yaml`.
The coordinates of sections `S0` and `S1` define two identical representations of the same section, so the geometry is prismatic.

```yaml
# CSF model for the Carrera-Petrolo C-section benchmark.
# Transverse partition reproduces the 9-L9 layout shown in Fig. 13(b).
#
# Version: v1 - 2026-10-10
#
# Changelog:
# - Preserved the original C-section geometry and material.
# - Replaced the single C-shaped polygon with 9 non-overlapping quadrilateral
#   CSF polygons arranged as the 9 transverse L9 domains of Fig. 13(b).
# - The internal flange split coordinates are reconstructed from the figure by
#   equally subdividing the free flange portions:
#       top free flange:    900 mm / 4 = 225 mm
#       bottom free flange: 400 mm / 2 = 200 mm
#   The 100 mm web-width corner domains are kept as separate polygons.
#
# Units: mm, N, MPa.
#
# Geometry:
#   h = 1000 mm
#   t = 100 mm
#   long flange b2 = 1000 mm
#   short flange b1 = 500 mm
#   L = 20000 mm
#
# Material:
#   E  = 75 GPa = 75000 MPa
#   nu = 0.33
#
# Coordinate mapping:
#   paper y (beam axis) -> CSF section station z
#   paper x             -> CSF section y
#   paper z             -> CSF section z-coordinate inside each polygon
#
# Section orientation:
#   paper/section x positive to the right
#   paper/section z positive upward
#   web on the right
#   opening toward the left
#   long flange on top
#
# 9-L9 transverse partition (CSF y coordinates):
#   top flange:    [-1000,-775], [-775,-550], [-550,-325], [-325,-100], [-100,0]
#   web:           [-100,0] x z[-400,400]
#   bottom flange: [-500,-300], [-300,-100], [-100,0]
#
# NOTE:
# The paper shows the 9-L9 topology graphically but does not tabulate the
# internal split coordinates. The equal subdivisions above are therefore a
# geometric reconstruction of Fig. 13(b), not quoted numerical data.
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        # --- Top flange: 5 transverse domains ---
        - name: top_1
          weight: 75000.0
          vertices:
            - [-1000.0, 400.0]
            - [-775.0,  400.0]
            - [-775.0,  500.0]
            - [-1000.0, 500.0]

        - name: top_2
          weight: 75000.0
          vertices:
            - [-775.0, 400.0]
            - [-550.0, 400.0]
            - [-550.0, 500.0]
            - [-775.0, 500.0]

        - name: top_3
          weight: 75000.0
          vertices:
            - [-550.0, 400.0]
            - [-325.0, 400.0]
            - [-325.0, 500.0]
            - [-550.0, 500.0]

        - name: top_4
          weight: 75000.0
          vertices:
            - [-325.0, 400.0]
            - [-100.0, 400.0]
            - [-100.0, 500.0]
            - [-325.0, 500.0]

        - name: top_web_corner
          weight: 75000.0
          vertices:
            - [-100.0, 400.0]
            - [0.0,    400.0]
            - [0.0,    500.0]
            - [-100.0, 500.0]

        # --- Web: 1 transverse domain ---
        - name: web
          weight: 75000.0
          vertices:
            - [-100.0, -400.0]
            - [0.0,    -400.0]
            - [0.0,     400.0]
            - [-100.0,  400.0]

        # --- Bottom flange: 3 transverse domains ---
        - name: bottom_1
          weight: 75000.0
          vertices:
            - [-500.0, -500.0]
            - [-300.0, -500.0]
            - [-300.0, -400.0]
            - [-500.0, -400.0]

        - name: bottom_2
          weight: 75000.0
          vertices:
            - [-300.0, -500.0]
            - [-100.0, -500.0]
            - [-100.0, -400.0]
            - [-300.0, -400.0]

        - name: bottom_web_corner
          weight: 75000.0
          vertices:
            - [-100.0, -500.0]
            - [0.0,    -500.0]
            - [0.0,    -400.0]
            - [-100.0, -400.0]

    S1:
      z: 20000.0
      polygons:
        # Same 9-domain partition: prismatic section.
        - name: top_1
          weight: 75000.0
          vertices:
            - [-1000.0, 400.0]
            - [-775.0,  400.0]
            - [-775.0,  500.0]
            - [-1000.0, 500.0]

        - name: top_2
          weight: 75000.0
          vertices:
            - [-775.0, 400.0]
            - [-550.0, 400.0]
            - [-550.0, 500.0]
            - [-775.0, 500.0]

        - name: top_3
          weight: 75000.0
          vertices:
            - [-550.0, 400.0]
            - [-325.0, 400.0]
            - [-325.0, 500.0]
            - [-550.0, 500.0]

        - name: top_4
          weight: 75000.0
          vertices:
            - [-325.0, 400.0]
            - [-100.0, 400.0]
            - [-100.0, 500.0]
            - [-325.0, 500.0]

        - name: top_web_corner
          weight: 75000.0
          vertices:
            - [-100.0, 400.0]
            - [0.0,    400.0]
            - [0.0,    500.0]
            - [-100.0, 500.0]

        - name: web
          weight: 75000.0
          vertices:
            - [-100.0, -400.0]
            - [0.0,    -400.0]
            - [0.0,     400.0]
            - [-100.0,  400.0]

        - name: bottom_1
          weight: 75000.0
          vertices:
            - [-500.0, -500.0]
            - [-300.0, -500.0]
            - [-300.0, -400.0]
            - [-500.0, -400.0]

        - name: bottom_2
          weight: 75000.0
          vertices:
            - [-300.0, -500.0]
            - [-100.0, -500.0]
            - [-100.0, -400.0]
            - [-300.0, -400.0]

        - name: bottom_web_corner
          weight: 75000.0
          vertices:
            - [-100.0, -500.0]
            - [0.0,    -500.0]
            - [0.0,    -400.0]
            - [-100.0, -400.0]

  shear_weight_laws:
    - 'iso(0.33)'
```

## Reading the model parameters

`CSF.sections.S0/S1` identifies the two physical end sections; `z` is the **station along the CSF axis**. `polygons` lists the actual portions of material, `name` preserves the identity of each region, `vertices` contains the sectional 2D coordinates, and `weight` provides the material value used by the model. `shear_weight_laws` describes the isotropic treatment associated with `ν=0.33`. The CSF domains represent portions of the physical geometry of the beam, defined through the sections along the longitudinal axis, and at the same time provide the geometric support for the CUF transverse expansion functions. They must not be confused with the three-dimensional solid finite elements used in the FEM3D discretization.

# Appendix B - Complete problem configuration

```yaml
# Version: Carrera Table 9.13 L9 problem v1 - 2026-10-10
#
# Changelog:
# - Uses the 9-polygon CSF model reproducing the transverse partition of
#   Carrera & Petrolo's 9-L9 C-section benchmark.
# - Keeps the physical point load separated from the CUF case definition.
#
# Units: mm, N, MPa.

model:
  csf_yaml: ../models/c_section_chapter9_5_3_9L9_csf.yaml

problem:
  type: c_section_cantilever
  force:
    type: point
    amplitude: -1.0
    x: 20000.0
    y: 0.0
    z: -500.0
```

## Reading the problem parameters

`model.csf_yaml` identifies the geometric and material description reproduced in Appendix A.

`problem.type: c_section_cantilever` selects an **adapter implemented in Python**, responsible for defining the structural problem, including loads and boundary conditions.

In CSF–CUF, **geometry and materials are described in YAML, whereas the logic for applying loads and constraints is implemented in Python**. This separation allows the same adapter to be reused in multiple analyses by changing the problem parameters through YAML files, without having to rewrite the corresponding implementation.

`force.type: point` specifies a concentrated load; `amplitude: -1.0` provides its signed value in N; `x`, `y`, and `z` are the **physical coordinates of the application point** in mm, not YAML interpolation stations. The negative sign refers to the force direction associated with the adapter, in this case the global z direction.



# Appendix C - Numerical configuration of the analysis

This appendix describes the numerical configuration used for the CSF–CUF analysis of the C-section cantilever.

Geometry and material properties are defined in the CSF model described in Appendix A, while loads and boundary conditions are handled by the problem's Python adapter, illustrated in Appendix B.

The case YAML file brings together these elements and specifies the choices needed to construct and solve the CUF model.

In particular, the configuration specifies:

- **The physical model:** the reference to the CSF description of geometry and materials.
- **The structural problem:** the Python adapter implementing loads and constraints, together with the corresponding parameters.
- **The transverse approximation:** the family of functions used to represent the displacement field over the section and its expansion order.
- **The longitudinal discretization:** the number of finite elements, the shape-function order, and the numerical integration settings.
- **The execution options:** the parameters controlling the solution and the production of results.

These choices are independent of the physical description of the section. It is therefore possible to modify the CUF approximation or longitudinal discretization without redefining the geometry, materials, or Python implementation of the structural problem.

The YAML file reproduced below is the configuration actually used in the analysis. The comments associated with its parameters explain their meaning and make it possible to reproduce the numerical case.


```yaml
# CSF-CUF C-section cantilever benchmark
#
# PURPOSE
# Geometry and materials come from CSF via the problem YAML.
# The external L9 Python module defines the transverse approximation.
# Longitudinal finite elements and numerical integration are selected here.
# The nine quadrilateral CSF domains are specific to this L9 benchmark;
# they are not three-dimensional finite elements or a general CSF restriction.
# Units in the physical model: mm, N, MPa (= N/mm^2).

# Case identifier (descriptive; discretization is configured below).
case:
  name: c_section_table_9_13_lagrangeL9_v4_E10

# Structural problem: separate physical model, loading and constraints.
problem:
  # Relative path to the physical problem configuration.
  yaml: ../problems/c_section_cantilever_point_9L9.yaml
  # Python adapter interpreting the problem's loading and boundary conditions.
  adapter: csf.cuf.adapters.problem.c_section_cantilever_point_load

# CUF transverse approximation, independent of the longitudinal FE basis.
cuf:
  # External Python implementation of the nine-node Lagrange expansion.
  # The module provides transverse functions, derivatives and connectivity.
  basis: ../expansions/lagrangeL9_v4.py
  # Quadratic polynomial interpolation in each natural coordinate (L9).
  order: 2
  basis_options:
    # Build transverse L9 domains from CSF polygons (nine quadrilaterals here).
    domain_source: csf_polygons
    # Map each reference quadrilateral to its physical CSF quadrilateral.
    # The mapping Jacobian transforms derivatives and sectional measures;
    # it is a numerical mapping, not a new term in the CUF nuclei.
    mapping: isoparametric
    # Share coincident interpolation points across adjacent domain edges.
    connectivity: shared_points
    # Geometric tolerance for boundary/connectivity comparisons;
    # not a linear solver tolerance or a convergence criterion.
    boundary_tolerance: 1.0e-10
    # Require the prismatic geometry supported by this L9 configuration.
    # Both CSF stations describe the same section in this benchmark.
    require_prismatic: true

# One-dimensional finite-element approximation along the beam axis.
longitudinal:
  # Generalized CUF displacement variables use longitudinal finite elements.
  method: finite_element
  # Ten elements in normalized axial coordinates [0, 1].
  # For L = 20000 mm each interval is 2000 mm long.
  element_boundaries: [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
  # Lagrange interpolation along the axis; distinct from transverse L9.
  basis: lagrange
  # Polynomial degree 12 for each longitudinal finite element.
  order: 12
  # Requested Gauss integration order along the beam axis.
  gauss_order: 15
  # Declared degree of longitudinal material variation (constant here).
  material_polynomial_degree: 0

# Sectional numerical integration of CUF contributions.
section_integration:
  # Numerical quadrature on the physical CSF polygon domains.
  method: fixed_gauss_polygon
  # Requested sectional quadrature order; not the number of L9 nodes.
  gauss_order: 9

# Solver-specific options; numerical effects require run diagnostics.
solver:
  # Request MITC treatment of the strain terms handled by the implementation.
  # Enabling it does not itself establish the presence/removal of locking.
  correctionMITC: true
  # Request the solver's MITC assembly verification procedure.
  # The precise checks are determined by the solver implementation.
  verifyMITCAssembly: true
  equilibration:
    # Requested solver equilibration iteration settings.
    # Not a stress-recovery procedure or a convergence certificate.
    iterations: [1,2,3,4,5]

# Postprocessing sampling; does not change the solution discretization.
sampling:
  # Normalized longitudinal stations: x = 0, 2000, 20000 mm.
  stations: [0.0, 0.1, 1.0]
  # Requested displacement output sampling resolution.
  displacement_samples: 201
  # Requested stress sampling-grid resolution (not a CUF FE mesh).
  stress_grid: 41

# Output handling, separate from the structural problem adapter.
output:
  # Python postprocessing/output adapter.
  adapter: csf.cuf.adapters.output.post
  # Relative destination; actual generated files depend on execution.
  directory: ../output/c_section_table_9_13_lagrangeL9_v4_E10
```

## Detailed reading of the case parameters

| YAML path | Function in the model |
|---|---|
| `case.name` | descriptive identifier of the configuration |
| `problem.yaml` | selection of the physical problem from Appendix B |
| `problem.adapter` | code that translates the problem description into loads and constraints |
| `cuf.basis` | path to the independent L9 expansion module |
| `cuf.order` | declared transverse polynomial order: 2 |
| `cuf.basis_options.domain_source` | construction of L9 domains on CSF polygons |
| `cuf.basis_options.mapping` | quadrilateral–natural-domain isoparametric transformation |
| `cuf.basis_options.connectivity` | sharing of coincident points among domains |
| `cuf.basis_options.boundary_tolerance` | numerical tolerance for geometry/connectivity checks |
| `cuf.basis_options.require_prismatic` | requires no sectional variation along the axis |
| `longitudinal.method` | finite-element approximation along the beam |
| `longitudinal.element_boundaries` | eleven boundaries of ten elements, in normalized coordinates |
| `longitudinal.basis` | family of longitudinal shape functions: Lagrange |
| `longitudinal.order` | longitudinal order 12 |
| `longitudinal.gauss_order` | longitudinal quadrature, order 15 |
| `longitudinal.material_polynomial_degree` | degree of longitudinal material variation, zero |
| `section_integration.method` | fixed numerical integration on polygons |
| `section_integration.gauss_order` | sectional quadrature parameter, 9 |
| `solver.correctionMITC` | activation of the MITC correction provided by the engine |
| `solver.verifyMITCAssembly` | request for MITC assembly verification |
| `solver.equilibration.iterations` | values of the requested equilibration iterations |
| `sampling.stations` | query/postprocessing stations |
| `sampling.displacement_samples` | requested number of displacement samples |
| `sampling.stress_grid` | resolution of the stress sampling grid |
| `output.adapter` | component for writing/postprocessing results |
| `output.directory` | destination directory for the numerical data produced |


# Appendix D - Definition of the solid reference and traceability checks

The FEM3D driver consulted is identified as `run_c_section_table_9_13_fem3d.py`. Its default discretization parameters are:

```python
@dataclass(frozen=True)
class MeshSettings:
    nx: int = 200
    ny_top_free: int = 18
    ny_bottom_free: int = 8
    ny_web: int = 2
    nz_flange: int = 2
    nz_web: int = 16
```

The traceability chain required for each result is: (1) geometry/material actually read by the driver, (2) problem and load actually acquired, (3) mesh options and any overrides, (4) code version, (5) output file, (6) routine used to evaluate stresses and displacements. The FEM3D representation intentionally uses **a single eight-vertex outline polygon** to facilitate OpenSees mesh generation, rather than the nine quadrilaterals used for L9. 

# Bibliographical references and note on sources

1. E. Carrera and M. Petrolo, *Refined beam elements with only displacement variables and plate/shell capabilities*, §4.3, figures 12 and 13.
