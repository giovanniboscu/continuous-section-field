# MITC in CSF–CUF - formulation and validation benchmarks

This directory documents the **Mixed Interpolation of Tensorial Components (MITC)** implementation in **CSF–CUF**. MITC is used here to reduce transverse **shear locking** in longitudinal beam finite elements without changing the physical cross-section supplied by CSF.

**Start here if you are new to the project.** This page introduces the three roles (CSF, CUF, MITC), explains why the two benchmarks are complementary, and links to their inputs, numerical results, and reproduction instructions. It is not a substitute for the detailed formulation or the individual benchmark READMEs.

## 1. What problem does MITC address?

In bending-dominated beams, a standard displacement-based finite element may introduce an artificially stiff transverse-shear response. This numerical effect is called **shear locking**. It can be especially severe for a slender beam with a coarse longitudinal mesh: the computed deflection becomes much smaller than the physically expected bending deflection.

MITC retains the displacement degrees of freedom but uses **assumed transverse-shear strains**, reconstructed from selected axial *tying points*. It modifies the strain interpolation, **not** the physical material data and **not** the complete stiffness-integral quadrature.

The reference implementation and theoretical comparison are discussed in:

> Carrera, E., de Miguel, A. G., and Pagani, A. (2017). *Extension of MITC to higher-order beam models and shear locking analysis for compact, thin-walled and composite structures*. International Journal for Numerical Methods in Engineering. [DOI: 10.1002/nme.5588](https://doi.org/10.1002/nme.5588).

## 2. How CSF, CUF, and MITC fit together

**CSF - physical description.** The Continuous Section Field defines the cross-sectional domains and constitutive properties along the beam axis:

$$
\mathcal S(x)=\{\Omega^k(x),\,\mathbf C^k(x,y,z)\}_{k=1}^{K}.
$$

Here `x` is the longitudinal coordinate, `(y,z)` are physical section coordinates, `k` labels a material/domain, `Ω^k(x)` is its cross-sectional area, and `C^k` is the constitutive matrix. CSF supplies the geometry and material data needed for the sectional integration; it does not choose the displacement approximation.

**CUF - structural description.** Carrera Unified Formulation expresses the displacement field as

$$
\mathbf u(x,y,z)=\sum_{\tau=1}^{M}F_\tau(y,z)\,\mathbf u_\tau(x),
$$

where `F_τ` is a transverse expansion function and `u_τ(x)` is a vector of longitudinal displacement amplitudes. Within a longitudinal element,

$$
\mathbf u_\tau(x)=\sum_{i=1}^{n}N_i(x)\,\mathbf q_{\tau i}.
$$

Here `N_i` is a longitudinal shape function, `n` the number of its nodes, and `q_{τi}` the unknown displacement coefficients. Substitution gives the discrete field

$$
\mathbf u(x,y,z)=\sum_{\tau=1}^{M}\sum_{i=1}^{n}F_\tau(y,z)N_i(x)\,\mathbf q_{\tau i}.
$$

**MITC - correction of the structural shear kinematics.** For example, the ordinary small-strain transverse shear is

$$
\gamma_{xz}=\frac{\partial u_z}{\partial x}+\frac{\partial u_x}{\partial z}.
$$

Rather than using this strain directly at every axial integration point, MITC samples it at tying points `ξ_m` and interpolates the samples:

$$
\bar{\boldsymbol\gamma}_S(\xi,y,z)
=\sum_{m=1}^{n-1}\bar N_m(\xi)\,\boldsymbol\gamma_S(\xi_m,y,z),
\qquad
\boldsymbol\gamma_S=(\gamma_{xy},\gamma_{xz})^T.
$$

Here `ξ` is the local longitudinal coordinate and `\bar N_m` are the interpolation functions associated with the tying points. B2 (two axial nodes) uses one tying point and **constant assumed shear**; B3 uses two and linear shear; B4 uses three and quadratic shear.

In the finite-element stiffness, **only the transverse-shear kinematic operators are replaced by their MITC counterparts**. The sectional geometry and constitutive coefficients still come from CSF, and the corrected full stiffness integrand is evaluated with the configured quadrature. This distinction also matters for mixed constitutive terms: both sides of a shear coupling must use the consistent assumed-strain operator. The present two benchmarks use an isotropic material, so they **do not validate general anisotropic coupling**.

For the step-by-step beam formulation and the precise B2/B3/B4 benchmark, see [Paper §4.1 - README](paper41/README.md). For the general variable-section CSF–CUF model, see [the formal formulation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md).



### Further study: MITC B2 stiffness derivation

The preceding equations introduce the MITC correction at the
kinematic level. To understand how this correction enters the
CUF stiffness matrix, see the
[MITC B2 stiffness nucleus derivation](theory/mitc_b2_stiffness_derivation.md).

The document provides a step-by-step derivation of the two-node
B2 element, from the CUF displacement field and MITC tying point
to the sectional stiffness coefficients supplied by CSF and
their correspondence with the Python assembly.


## 3. Two complementary numerical benchmarks

| Benchmark | What changes | Primary question | Reference |
|---|---|---|---|
| [B2 shear-locking / mesh refinement](b2_shear_locking/README.md) | Number of B2 longitudinal elements: **1, 2, 4, 8, 16, 32, 64**, with MITC OFF/ON | Does MITC reduce artificial shear stiffness as the mesh is refined? | Euler–Bernoulli slender-beam deflection (**not** an exact 3D solution) |
| [Paper §4.1 / B2–B3–B4](paper41/README.md) | **One** element per run; longitudinal polynomial order B2, B3 or B4; MITC OFF/ON | Does CSF–CUF reproduce published displacement and MITC shear-stress samples? | Table 1 in Carrera, de Miguel and Pagani (2017) |

The benchmarks use the **same kind of transverse L9 section expansion**, but answer **different** questions. They should be retained as separate examples rather than merged into a single convergence argument.

### 3.1 B2 mesh-refinement test

A **5000 mm**-long cantilever with a **100 × 100 mm** square section, `E = 75,000 MPa`, `ν = 0.33`, and an end force `F_z = −100 N` is solved using fourteen B2 cases (seven meshes × MITC OFF/ON).

The Euler–Bernoulli reference is `u_z = −6.666666667 mm`. For the 64-element mesh, the recorded end displacements are:

- MITC OFF: **−5.397726 mm** (19.03% from the reference).
- MITC ON: **−6.629803 mm** (0.553% from the reference).

This demonstrates a substantial reduction of the locking-associated stiffness effect over the tested meshes; the Euler–Bernoulli difference should **not** be read as a measured error against the exact elasticity solution.

**Read:** [benchmark and convergence results](b2_shear_locking/README.md) · [reproduce the fourteen runs](b2_shear_locking/reproducibility.md).

### 3.2 Carrera et al. (2017), §4.1 - single-element test

A **1000 mm**-long cantilever with the same square section and isotropic material, loaded with `F_z = −100 N`, is solved using **one B2, B3 or B4 element**, in each case with MITC OFF and ON.

- **Six end displacements** agree with the rounded values of Table 1 to within **0.117%**.
- **Nine MITC shear-stress samples** (two B2, three B3, four B4 nodes) agree with the **published three-decimal rounding**. The largest absolute difference is **0.000379 in the paper's scaled stress units**.
- The assumed-shear post-processing is separately reproducible from saved displacement checkpoints; the CSV regeneration was verified for **18 ON/OFF nodal samples** with an absolute tolerance of `1e-8`.

The stress comparison is essential because a matching displacement alone would not verify that the **MITC-assumed shear field** has been recovered consistently.

**Read:** [benchmark and paper comparisons](paper41/README.md) · [reproduce the six runs and shear recovery](paper41/reproducibility.md).

## 4. Where do the model and scripts live?

Each benchmark has three configuration layers:

1. **CSF geometry/material YAML** (`models/`): physical cross-section, coordinates, and material fields.
2. **Problem YAML** (`problems/`): applied forces and boundary conditions. The configured Python *adapter* translates these physical conditions into the generalized loads and constraints assembled by CUF.
3. **Case YAML** (`cases/`): links the problem and section to the selected CUF expansion, longitudinal finite elements, numerical integration, MITC ON/OFF, and output settings.

*YAML* is a human-readable configuration-file format: it describes the inputs, while Python implements the numerical operations. The same physical problem can therefore be tested with different structural discretizations without redefining its geometry or load.

Recommended repository layout:

```text
cuf/mitc/
├── README.md                  # This overview
├── b2_shear_locking/
│   ├── README.md              # B2 refinement and locking results
│   ├── reproducibility.md     # Commands and verification
│   ├── models/  problems/  cases/
│   └── ...
└── paper41/
    ├── README.md              # Paper Table 1 comparisons
    ├── reproducibility.md     # Commands and shear recovery
    ├── models/  problems/  cases/
    ├── recover_mitc_shear.py
    └── ...
```

**Links in this overview assume exactly this directory layout.** If an example is stored in a different directory, update the links instead of silently duplicating or moving its input files. For commands, dependency versions, and exact script paths, follow each benchmark's `reproducibility.md`; the core CSF–CUF solver is not bundled in this overview.

## 5. What is validated, and what remains open?

**Validated within the tested scope:** B2 longitudinal mesh-refinement behaviour with and without MITC; reproduction of published single-element B2/B3/B4 displacements and MITC shear samples; numerical checks reported by the archived runs, including global stiffness symmetry and solve diagnostics.

**Not established by these two benchmarks:** correctness for arbitrary variable sections, anisotropic or laminated constitutive coupling, every CUF matrix block, absence of zero-energy modes, an independent patch test, or agreement with an exact three-dimensional solution. The internal MITC assembly checks reported for the B2 benchmark cover the tested **CUF pair `(1,1)`**, not all pairs.

The two examples together support the MITC implementation **in this prismatic isotropic L9 setting**. Further modelling and independent tests are needed before extending the conclusion to other physical configurations.

## 6. Suggested reading order

1. Read this overview to distinguish **the physical section (CSF)**, **structural approximation (CUF)** and **assumed transverse shear (MITC)**.
2. Open [B2 shear locking](b2_shear_locking/README.md) to see *why* MITC is useful and how it behaves under mesh refinement.
3. Open [Paper §4.1](paper41/README.md) to see *what* MITC reproduces quantitatively against published displacements and stresses.
4. Use the corresponding **reproducibility.md** only when you want to execute the cases or independently check archived outputs.

For questions about variable geometry, sectional operators and constitutive fields, return to the [CSF–CUF formulation](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/model/csf_cuf_formal_variable_section_extension.md).
