# Hollow rectangular section - complete bending and torsion validation

This package validates a complete beam solver based on the Carrera Unified
Formulation (CUF), implemented within the Continuous Section Field (CSF)
framework. The validation is performed on a prismatic hollow square beam under
sinusoidally distributed bending and torsional loads.

The package is not only a collection of prescribed displacement fields or
post-processing examples. The CSF-CUF implementation constructs the CUF
kinematic approximation, evaluates the sectional and longitudinal integrals,
assembles the global finite-element equations, applies loads and constraints,
solves the resulting system, and exposes the continuous three-dimensional
displacement field

$$
\mathbf{u}(x,y,z)=\{u_x,u_y,u_z\}^{T}.
$$

The analytical solutions described below are independent references used to
check the results produced by this solver.

## 1. Geometry, material and beam axis

The validation beam is straight and prismatic. Its longitudinal axis is
denoted by $x$, while $y$ and $z$ are the cross-sectional coordinates.

| Quantity | Value |
|---|---:|
| Beam length $L$ | 10,000 mm |
| Outer section | 100 × 100 mm |
| Concentric void | 80 × 80 mm |
| Uniform wall thickness | 10 mm |
| Net area $A$ | 3,600 mm² |
| Second moment $I_y$ | 4,920,000 mm⁴ |
| Young's modulus $E$ | 71,700 MPa |
| Poisson's ratio $\nu$ | 0.3 |
| Shear modulus $G=E/[2(1+\nu)]$ | 27,576.9230769 MPa |

The section is represented directly by CSF as an outer domain containing a
concentric zero-material subdomain. Therefore, both the geometry and the
constitutive field are supplied to CUF through the actual net section.

## 2. Static schemes, constraints and loads

Two separate static problems are included. Both use a single half-wave along
the beam, so that the relevant generalized response is zero at $x=0$ and
$x=L$. The case files also contain the supplementary constraints required to
remove rigid-body modes from the three-dimensional CUF displacement field.

### 2.1 Sinusoidal bending

The beam is simply supported for bending at its two ends. A transverse surface
pressure is applied in the solver's negative $z$ direction and has a
sinusoidal variation along $x$. Its sectional resultant is the line load

$$
q(x)=q_0\sin\left(\frac{\pi x}{L}\right),
\qquad q_0=1.0\times10^{-3}\ \mathrm{N/mm}.
$$

The surface-pressure amplitude used to generate this resultant is

$$
p_0=1.0\times10^{-5}\ \mathrm{N/mm^2}.
$$

The transverse displacement is zero at the two supports. The maximum
Euler–Bernoulli displacement occurs at midspan.

### 2.2 Sinusoidal torsion

The torsional problem constrains the twist at both ends. A distributed side
traction is applied so that its transverse force resultant is zero while its
torque resultant is

$$
m(x)=m_0\sin\left(\frac{\pi x}{L}\right),
\qquad m_0=1.0\times10^{-1}\ \mathrm{N}.
$$

The side-traction amplitude is

$$
p_0=1.0\times10^{-5}\ \mathrm{N/mm^2}.
$$

The maximum twist occurs at midspan. The precise load distribution and the
component constraints used by the solver are defined in the corresponding
problem YAML files; those files are the authoritative executable definition of
each static scheme.

## 3. Independent analytical solutions

The analytical calculations do not call the CSF-CUF solver. They provide
independent reference values against which the numerical displacement field is
compared.

### 3.1 Euler–Bernoulli bending solution

For the sinusoidal transverse load, the Euler–Bernoulli solution is

$$
u_z^{EB}(x)=-\frac{q_0L^4}{E I_y\pi^4}
\sin\left(\frac{\pi x}{L}\right).
$$

At midspan,

$$
u_z^{EB}(L/2)=-2.910155870408\times10^{-1}\ \mathrm{mm}.
$$

### 3.2 Torsion reference solutions

The package currently contains the Bredt–Batho thin-wall reference. For the
mean-line area $A_m=8100\ \mathrm{mm^2}$, it gives

$$
J_{BB}=7,290,000\ \mathrm{mm^4}
$$

and

$$
\theta_{BB}(x)=\frac{m_0L^2}{\pi^2GJ_{BB}}
\sin\left(\frac{\pi x}{L}\right).
$$

Bredt–Batho is an approximation for closed thin-walled sections and is not the
final exact reference for this wall thickness.

An independent CSF Saint-Venant section analysis gives the torsion carrier

$$
GJ_{SP}=212,656,978,740\ \mathrm{N\,mm^2},
$$

equivalent to

$$
J_{SP}=7,711,130.33\ \mathrm{mm^4}.
$$

The corresponding midspan twist is approximately

$$
\theta_{SP}(L/2)=4.76538\times10^{-6}\ \mathrm{rad}.
$$

This Saint-Venant value is the preferred torsional baseline. The current
Bredt–Batho script may be retained as an additional engineering comparison.

## 4. Quantities to be verified

The following physical and numerical checks are required.

### 4.1 Bending checks

1. Evaluate $u_z$ at the bottom-wall point $(y,z)=(0,-50\ \mathrm{mm})$.
2. Compare CUF and Euler–Bernoulli values at
   $x/L=0,0.25,0.50,0.75,1$.
3. Check that the end displacements satisfy the imposed supports.
4. Check symmetry about midspan.
5. Study convergence with CUF order $N$.
6. Compare scaled Legendre and scaled Maclaurin expansions.

### 4.2 Torsion checks

1. Extract the twist $\theta(x)$ from the CUF displacement field.
2. Compare it at $x/L=0,0.25,0.50,0.75,1$.
3. Check zero twist at the constrained ends and symmetry about midspan.
4. Compare first with the Saint-Venant value and secondarily with
   Bredt–Batho.
5. Study internal CUF convergence through at least $N=21$, which is the
   present minimum adopted for the torsion validation.
6. Compare the physical results and numerical conditioning of the scaled
   Legendre and scaled Maclaurin bases.

For every run, the solver residuals, equation-term scale, quadrature orders and
KKT conditioning diagnostics should also be inspected. Agreement of one output
quantity alone is not sufficient to assess numerical reliability.

## 5. The CSF-CUF solver used for the validation

The cases are solved with the CUF implementation included in CSF. This is a
general solver, not a formula specialized for the hollow rectangle.

For each case it:

1. reads the CSF geometry and constitutive fields;
2. constructs the selected transverse CUF expansion of order $N$;
3. constructs the longitudinal finite-element approximation;
4. evaluates the sectional integrals over the net domains;
5. evaluates the required longitudinal integrals;
6. assembles the global stiffness matrix and load vector;
7. applies the displacement constraints through the augmented system;
8. solves the global equations;
9. returns the continuous displacement field $\mathbf u(x,y,z)$;
10. evaluates the requested validation quantities and numerical diagnostics.

The same solver architecture can therefore be used with other CSF sections,
materials, loads and longitudinal variations by modifying the input files
rather than rewriting the governing equations.

## 6. Package files and what must be modified

The validation is intentionally separated into model, problem, case, baseline
and execution layers.

### File tree

The files used by the validation package must be organized as follows:

```text
hollow_rectangle_validation/
├── README.md
├── run_discovered_cases.sh
├── models/
│   └── hollow_rectangle_prismatic_csf.yaml
├── problems/
│   ├── bending/
│   │   └── hollow_rectangle_bending_halfwave.yaml
│   └── torsion/
│       └── hollow_rectangle_torsion_halfwave.yaml
├── cases/
│   ├── bending/
│   │   ├── legendre/
│   │   │   ├── legendre_hollow_bending_N01.yaml
│   │   │   ├── ...
│   │   │   └── legendre_hollow_bending_N20.yaml
│   │   └── maclaurin/
│   │       ├── maclaurin_hollow_bending_N01.yaml
│   │       ├── ...
│   │       └── maclaurin_hollow_bending_N20.yaml
│   └── torsion/
│       ├── legendre/
│       │   ├── legendre_hollow_torsion_N01.yaml
│       │   ├── ...
│       │   ├── legendre_hollow_torsion_N20.yaml
│       │   └── legendre_hollow_torsion_N21.yaml
│       └── maclaurin/
│           ├── maclaurin_hollow_torsion_N01.yaml
│           ├── ...
│           ├── maclaurin_hollow_torsion_N20.yaml
│           └── maclaurin_hollow_torsion_N21.yaml
├── baseline/
│   ├── bending/
│   │   └── calculate_bending_baseline.py
│   └── torsion/
│       └── calculate_torsion_baseline.py
├── logs/                         # generated by the runner
│   ├── completed/                # one .done marker per successful case
│   └── *.log                     # one execution log per case
└── output/                       # generated numerical reports
    ├── bending/
    │   ├── legendre/Nxx/
    │   └── maclaurin/Nxx/
    └── torsion/
        ├── legendre/Nxx/
        └── maclaurin/Nxx/
```

The model and problem files define the physical analysis. Each case YAML links
one problem to the CSF model and selects the CUF basis, order and numerical
integration settings. The runner discovers the case YAML files: consequently,
order N=21 is included automatically only when the corresponding
`legendre_hollow_torsion_N21.yaml` or `maclaurin_hollow_torsion_N21.yaml` file
is present in the appropriate directory.

### `models/hollow_rectangle_prismatic_csf.yaml`

This file defines the CSF geometry and material field.

Modify it when changing:

- outer or inner section dimensions;
- wall thickness or topology;
- beam length if it is part of the CSF longitudinal definition;
- Young's modulus, Poisson's ratio or material weights;
- prismatic, tapered or otherwise variable geometry/material laws.

If the geometry changes, recompute all analytical section properties used by
the baseline scripts. A void must remain a zero-weight subdomain and must not be
counted as solid material.

### `problems/bending/hollow_rectangle_bending_halfwave.yaml`

This file defines the bending static scheme, constraints, distributed pressure,
load direction and requested output sampling.

Modify it when changing:

- support conditions;
- rigid-body suppression constraints;
- pressure amplitude or longitudinal law;
- load direction;
- longitudinal stations or cross-sectional sampling points.

The analytical bending script must be updated consistently if $q_0$, $L$,
$E$, $I_y$ or the sinusoidal load law changes.

### `problems/torsion/hollow_rectangle_torsion_halfwave.yaml`

This file defines the torsional constraints and the side-traction distribution
that produces the prescribed torque with zero transverse resultant.

Modify it when changing:

- end constraints;
- traction amplitude or application boundary;
- longitudinal torque law;
- torque normalization;
- twist extraction stations.

After changing the section or material, recompute the Saint-Venant torsion
carrier and update the torsional reference. The Bredt–Batho value must also be
recomputed if it is retained.

### `cases/bending/{legendre,maclaurin}/*.yaml`

These files connect the CSF model, bending problem, CUF expansion and
longitudinal discretization.

Modify them when changing:

- the path to the model or problem file;
- expansion type;
- CUF order $N$;
- transverse Gauss order;
- longitudinal finite-element order or mesh;
- longitudinal Gauss order and polynomial-degree metadata.

### `cases/torsion/{legendre,maclaurin}/*.yaml`

These files have the same role for torsion. The torsion series should currently
extend through at least `N21`. When a new order is added, copy the corresponding
basis case, change both the case name and CUF order, and preserve all other
parameters unless the purpose of the test is to study them.

### `baseline/bending/calculate_bending_baseline.py`

This independent script computes the Euler–Bernoulli displacement. Update its
geometry, material, length and load parameters whenever the corresponding YAML
inputs change. It must not import or call the CUF solution.

### `baseline/torsion/calculate_torsion_baseline.py`

This script currently computes the Bredt–Batho comparison. It should be extended
or accompanied by a Saint-Venant baseline using the CSF-SP torsion carrier. The
report should clearly label Bredt–Batho as a thin-wall approximation and SP as
the preferred sectional reference.

### `run_discovered_cases.sh`

This script discovers and executes the case matrix, writes one log per case and
creates `.done` markers for successful runs.

Modify its order limits or filters when extending the matrix. Preserve the
restart behaviour: completed cases are skipped unless `FORCE=1` is set.

### `logs/` and `output/`

These directories contain execution evidence and numerical reports. They are
generated data and must not be used as model inputs. When a model, problem,
quadrature rule or solver version changes, rerun the affected cases rather than
mixing outputs from different configurations.

## 7. Recommended modification sequence

When adapting the package to a new section or test:

1. modify the CSF model;
2. verify net area, centroid and second moments;
3. recompute the independent bending and torsion baselines;
4. modify the bending and torsion problem definitions;
5. update or generate the CUF case files;
6. run low-order cases to verify loads, constraints, signs and output points;
7. execute the complete order sweep;
8. inspect convergence, residuals and conditioning;
9. compare the final CUF sequence with the independent references.

## 8. Original README content

The following is the operational content present in the previous README,
retained here without changing its meaning.

### Hollow rectangular section - bending and torsion

Clean, complete package for the prismatic 100×100 mm hollow square section
with an 80×80 mm concentric void and 10 mm wall thickness.

### Case matrix

| Analysis | Basis | Orders | Cases |
|---|---|---:|---:|
| Bending | scaled Legendre | N01–N20 | 20 |
| Bending | scaled Maclaurin | N01–N20 | 20 |
| Torsion | scaled Legendre | N01–N20 | 20 |
| Torsion | scaled Maclaurin | N01–N20 | 20 |

Total: 80 cases.

### Independent baselines

Run without CSF–CUF:

```bash
python baseline/bending/calculate_bending_baseline.py
python baseline/torsion/calculate_torsion_baseline.py
```

The first computes the Euler–Bernoulli bending baseline; the second computes
the Bredt–Batho torsion baseline. Both create TXT and CSV output files.

### Execute cases

Make the runner executable once:

```bash
chmod +x run_discovered_cases.sh
```

All 80 cases:

```bash
./run_discovered_cases.sh
```

Examples of filtered execution:

```bash
./run_discovered_cases.sh bending legendre
./run_discovered_cases.sh bending maclaurin
./run_discovered_cases.sh torsion legendre
./run_discovered_cases.sh torsion maclaurin
```

Successful cases receive a `.done` marker under `logs/completed/`. A later run
skips those cases. Set `FORCE=1` only when completed cases must be repeated.

### Output tree

```text
output/bending/legendre/Nxx/
output/bending/maclaurin/Nxx/
output/torsion/legendre/Nxx/
output/torsion/maclaurin/Nxx/
```

The package contains no previous numerical outputs or logs.
