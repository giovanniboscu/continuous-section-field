# CSF-CUF quick start

Minimal CSF-CUF example with the same input separation used by the tutorial:

```text
.
├── models
│   └── rectangular_prismatic_csf.yaml
├── problems
│   └── torsion_halfwave.yaml
└── cases
    └── torsion_halfwave_legendre_N08.yaml
```

## Model

`models/rectangular_prismatic_csf.yaml` defines a prismatic rectangular beam:

- length: `1000`
- section: `100 x 100`
- one physical polygon: `rectangle`
- constant elastic weight: `71700`
- isotropic Poisson ratio: `0.3`

The section is prismatic because `S0` and `S1` have identical geometry and material data.

## Problem

`problems/torsion_halfwave.yaml` uses the predefined `torsion_halfwave` problem with amplitude `10.0`.

## Case

`cases/torsion_halfwave_legendre_N08.yaml` uses:

- `scaled_legendre`
- order `N = 8`
- one longitudinal finite element
- longitudinal order `6`
- fixed polygon Gauss integration

## Run

From this directory:

```bash
csf-cuf cases/torsion_halfwave_legendre_N08.yaml
```

The solver writes the results below:

```text
output/torsion_halfwave_legendre_N08
```
