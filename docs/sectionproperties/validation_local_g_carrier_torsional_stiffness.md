== DRAFT ==
# Validation of Local G-Carrier Torsional Stiffness

This note documents a controlled validation case for computing torsional stiffness with a local shear-modulus carrier.

The purpose is to compare three approaches:

1. the native `sectionproperties` torsional result, reported as `E.J`;
2. the documentation-style global correction `G.J = (g_eff / e_eff) * E.J`;
3. a local `G_i` carrier torsional analysis, obtained in `sectionproperties` through a second run with `E_SP := G_i`, and independently checked with `skfem`.


## 0. Installation

Required Python packages:

```bash
pip install numpy matplotlib shapely sectionproperties scikit-fem
```

For an isolated environment:

```bash
python -m venv venv
source venv/bin/activate
pip install numpy matplotlib shapely sectionproperties scikit-fem
```

## 1. Test Section

The section is a rectangle:

```text
B = 300 mm
D = 400 mm
A = 120000 mm2
```

Two isotropic materials are used:

```text
Material A:
E_A  = 3.0000e+04 N/mm2
nu_A = 0.20
G_A  = 1.2500e+04 N/mm2

Material B:
E_B  = 2.0000e+05 N/mm2
nu_B = 0.30
G_B  = 7.6923e+04 N/mm2
```

The area fraction of Material B is fixed at 50% in both cases.

## 2. Two Material Distributions

The same rectangular section is analysed in two different material layouts.

### Case A

Material B is placed symmetrically at the top and bottom of the section.
Material A occupies the central band.

```text
Material B: bottom band + top band
Material A: central band
```

### Case B

Material B is placed in the lower half of the section.
Material A occupies the upper half.

```text
Material B: lower half
Material A: upper half
```

Both cases have the same material area fractions, but different spatial material distributions.

## 3. sectionproperties Documentation-Style Correction

The correction suggested for converting `E.J` into `G.J` is:

```python
# get relevant modulus weighted properties
eixx, _, _ = sec.get_eic()
ea = sec.get_ea()
ej = sec.get_ej()

# print results
print(f"Axial rigidity (E.A): {ea:.3e} N")
print(f"Flexural rigidity (E.I): {eixx:.3e} N.mm2")

# note we are usually interested in G.J not E.J
# geometric analysis required for effective material properties
sec.calculate_geometric_properties()
gj = sec.get_g_eff() / sec.get_e_eff() * ej
print(f"Torsional rigidity (G.J): {gj:.3e} N.mm2")
```

That is:

```text
SP doc G.J = (g_eff / e_eff) * SP E.J
```

This applies a single global correction factor to the native `E.J` result.

## 4. Local G-Carrier Method

The local G-carrier approach uses the shear modulus locally in the torsion problem.

In `sectionproperties`, this is obtained through a second run where the material Young's modulus passed to SP is replaced by the shear modulus:

```text
E_SP := G_i
```

Since `sectionproperties.get_ej()` follows the local `E` carrier, this run makes the returned `E.J` behave as a local `G_i` carrier torsional stiffness.

The same local carrier is checked independently with `skfem`, where the weak form directly uses:

```text
M_i := G_i
```

Here `M_i` is the local modulus carrier used in the FEM torsion formulation.

## 5. Numerical Output

```text
Material A  E = 3.0000e+04
Material B  E = 2.0000e+05
Material A  G = 1.2500e+04
Material B  G = 7.6923e+04

  CASE           SP E.J    g_eff/e_eff       SP doc G.J     SP G-carrier     skfem M_i:=G_i   diff G %
     A     1.295863e+14   3.887960e-01     5.038262e+13     5.241536e+13       5.241302e+13     -0.004
     B     1.607870e+14   3.887960e-01     6.251333e+13     6.374468e+13       6.373616e+13     -0.013
```

The same results are reported below in tabular form.

| Case | SP E.J | g_eff/e_eff | SP doc G.J | SP G-carrier | skfem M_i:=G_i | diff G % |
|---:|---:|---:|---:|---:|---:|---:|
| A | 1.295863e+14 | 3.887960e-01 | 5.038262e+13 | 5.241536e+13 | 5.241302e+13 | -0.004 |
| B | 1.607870e+14 | 3.887960e-01 | 6.251333e+13 | 6.374468e+13 | 6.373616e+13 | -0.013 |

The `diff G %` column is computed as:

```text
diff G % = (skfem_GJ / SP_GJ - 1) * 100
```

where:

```text
SP_GJ    = sectionproperties result with E_SP := G_i
skfem_GJ = independent skfem result with M_i := G_i
```

## 6. Comments on the Results

### 6.1 The global ratio is identical in both cases

The ratio:

```text
g_eff / e_eff = 3.887960e-01
```

is identical for Case A and Case B.

This happens because the two cases use the same material area fractions:

```text
50% Material A
50% Material B
```

Therefore, the effective material ratio `g_eff/e_eff` is the same even though the materials are placed differently inside the section.

### 6.2 The documentation correction is global

The documentation-style correction gives:

```text
Case A: SP doc G.J = 5.038262e+13
Case B: SP doc G.J = 6.251333e+13
```

These values are obtained by multiplying the native `SP E.J` by the same global factor:

```text
g_eff / e_eff = 3.887960e-01
```

So this method scales the torsional result globally. It does not change the local carrier inside the torsion problem.

### 6.3 The local G-carrier result is different

The local G-carrier run gives:

```text
Case A: SP G-carrier = 5.241536e+13
Case B: SP G-carrier = 6.374468e+13
```

These values are not equal to the documentation-style `SP doc G.J` values.

The difference appears because the local G-carrier method assigns `G_i` inside the torsional formulation, so the result depends on where the shear stiffness is located in the section.

### 6.4 The external skfem check confirms the local G-carrier run

The independent `skfem` results are:

```text
Case A: skfem M_i:=G_i = 5.241302e+13
Case B: skfem M_i:=G_i = 6.373616e+13
```

These match the `sectionproperties` local G-carrier results very closely:

```text
Case A: diff G = -0.004 %
Case B: diff G = -0.013 %
```

This confirms that the `sectionproperties` workaround based on `E_SP := G_i` reproduces the same torsional stiffness obtained by an external FEM formulation using `G_i` directly.

## 7. Validation Statement

The relevant validation is:

```text
SP G-carrier ≈ skfem M_i:=G_i
```

or, explicitly:

```text
sectionproperties with E_SP := G_i
≈
skfem with direct local carrier M_i := G_i
```

The agreement is within numerical mesh tolerance.

## 8. Conclusion

For composite or spatially varying material sections, the global correction:

```text
G.J = (g_eff / e_eff) * E.J
```

is not equivalent to solving the torsion problem with a local `G_i` carrier.

The local carrier method is therefore preferable when the torsional stiffness must reflect the spatial distribution of shear stiffness.

In CSF terms, this validates the use of a second `sectionproperties` run for torsion:

```text
first run:  E_SP := E_i   -> axial and bending stiffnesses
second run: E_SP := G_i   -> torsional stiffness GJ
```

The second run is a workaround required by `sectionproperties`, because its torsion result follows the material `E` carrier. The independent `skfem` check does not require this workaround, since it can use `G_i` directly in the weak form.

## 9. Reproducible Python Script

The full validation script is included below so the numerical table can be reproduced directly.

```python
import numpy as np
import matplotlib.pyplot as plt

from shapely import Polygon

from sectionproperties.analysis import Section
from sectionproperties.pre import CompoundGeometry, Geometry, Material

from skfem import (
    MeshTri,
    Basis,
    ElementTriP1,
    BilinearForm,
    LinearForm,
    asm,
    solve,
    condense,
)

from skfem.helpers import dot, grad


# -----------------------------
# Input data
# -----------------------------
B, D = 300.0, 400.0                 # section width, height [mm]
STEEL_FRAC = 0.50                   # Material B fraction of total area

E_C, NU_C = 30.0e3, 0.20            # Material A: E [N/mm2], Poisson
E_S, NU_S = 200.0e3, 0.30           # Material B: E [N/mm2], Poisson

G_C = E_C / (2.0 * (1.0 + NU_C))    # Material A: G [N/mm2]
G_S = E_S / (2.0 * (1.0 + NU_S))    # Material B: G [N/mm2]

MESH_SIZE_SP = 1000.0
DO_PLOT = True


# -----------------------------
# sectionproperties helpers
# -----------------------------
def make_rect(x1, x2, y1, y2, mat):
    return Geometry(
        geom=Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)]),
        material=mat,
    )


def make_materials(carrier):
    """
    Build sectionproperties materials.

    carrier = "E":
        Native sectionproperties material input.
        get_ej() follows the local E_i carrier.

    carrier = "G":
        Torsion-carrier material input.
        Since get_ej() follows the local E carrier, setting E_SP := G_i
        gives a local G_i-carrier torsional stiffness.
    """

    if carrier == "E":
        e_a = E_C
        e_b = E_S
        suffix = "E-carrier"

    elif carrier == "G":
        e_a = G_C
        e_b = G_S
        suffix = "G-carrier"

    else:
        raise ValueError(f"Unknown carrier: {carrier}")

    mat_a = Material(
        f"Material A {suffix}",
        e_a,
        NU_C,
        30.0,
        2.4e-6,
        "lightgrey",
    )

    mat_b = Material(
        f"Material B {suffix}",
        e_b,
        NU_S,
        500.0,
        7.85e-6,
        "grey",
    )

    return mat_a, mat_b


def make_geometry(case_id, carrier="E"):
    mat_a, mat_b = make_materials(carrier)

    x1, x2 = -B / 2.0, B / 2.0
    y1, y2 = -D / 2.0, D / 2.0
    h_s = D * STEEL_FRAC

    if case_id == "A":
        h = h_s / 2.0
        parts = [
            make_rect(x1, x2, y1,     y1 + h, mat_b),
            make_rect(x1, x2, y1 + h, y2 - h, mat_a),
            make_rect(x1, x2, y2 - h, y2,     mat_b),
        ]

    elif case_id == "B":
        parts = [
            make_rect(x1, x2, y1,       y1 + h_s, mat_b),
            make_rect(x1, x2, y1 + h_s, y2,       mat_a),
        ]

    else:
        raise ValueError(f"Unknown case_id: {case_id}")

    geom = CompoundGeometry(geoms=parts)
    geom.create_mesh(mesh_sizes=MESH_SIZE_SP)
    return geom


def analyse_sp(case_id, carrier="E"):
    sec = Section(make_geometry(case_id, carrier=carrier))
    sec.calculate_frame_properties()
    ej = sec.get_ej()
    return sec, ej


def analyse_sp_doc_gj(case_id):
    """
    sectionproperties documentation-style torsional correction:

        G.J = g_eff / e_eff * E.J

    This is a global effective-modulus correction applied to the native E.J.
    """

    sec, ej = analyse_sp(case_id, carrier="E")

    # Geometric analysis is required before reading effective material properties.
    sec.calculate_geometric_properties()

    e_eff = sec.get_e_eff()
    g_eff = sec.get_g_eff()

    ratio = g_eff / e_eff
    gj_doc = ratio * ej

    return ratio, gj_doc


# -----------------------------
# scikit-fem helpers
# -----------------------------
def carrier_M(case_id, x, y, carrier):
    """
    Return the local material carrier M_i.

    carrier = "G":
        M_i := G_i
    """

    if carrier == "G":
        m_a = G_C
        m_b = G_S

    else:
        raise ValueError(f"Unknown carrier: {carrier}")

    y1, y2 = -D / 2.0, D / 2.0
    h_s = D * STEEL_FRAC

    if case_id == "A":
        h = h_s / 2.0
        mask_b = (y <= y1 + h) | (y >= y2 - h)
        return np.where(mask_b, m_b, m_a)

    elif case_id == "B":
        mask_b = y <= y1 + h_s
        return np.where(mask_b, m_b, m_a)

    else:
        raise ValueError(f"Unknown case_id: {case_id}")


def analyse_skfem_g(case_id, nx=80, ny=100):
    """
    Independent warping FEM with material carrier M_i := G_i.

    Weak form:
        int G_i grad(omega) . grad(v) dA
        =
        int G_i grad(v) . [y, -x] dA

    Carrier torsion result:
        GJ = Ipp_G - omega.T @ f
    """

    x = np.linspace(-B / 2.0, B / 2.0, nx + 1)
    y = np.linspace(-D / 2.0, D / 2.0, ny + 1)

    msh = MeshTri.init_tensor(x, y)
    basis = Basis(msh, ElementTriP1())

    @LinearForm
    def m0(v, w):
        M = carrier_M(case_id, w.x[0], w.x[1], "G")
        return M * v

    @LinearForm
    def mx(v, w):
        M = carrier_M(case_id, w.x[0], w.x[1], "G")
        return M * w.x[0] * v

    @LinearForm
    def my(v, w):
        M = carrier_M(case_id, w.x[0], w.x[1], "G")
        return M * w.x[1] * v

    M_area = np.sum(asm(m0, basis))
    cx = np.sum(asm(mx, basis)) / M_area
    cy = np.sum(asm(my, basis)) / M_area

    @BilinearForm
    def lhs(omega, v, w):
        M = carrier_M(case_id, w.x[0], w.x[1], "G")
        return M * dot(grad(omega), grad(v))

    @LinearForm
    def rhs(v, w):
        M = carrier_M(case_id, w.x[0], w.x[1], "G")
        x_c = w.x[0] - cx
        y_c = w.x[1] - cy
        return M * (grad(v)[0] * y_c - grad(v)[1] * x_c)

    @LinearForm
    def polar_term(v, w):
        M = carrier_M(case_id, w.x[0], w.x[1], "G")
        x_c = w.x[0] - cx
        y_c = w.x[1] - cy
        return M * (x_c**2 + y_c**2) * v

    K = asm(lhs, basis)
    f = asm(rhs, basis)

    # Remove the constant null mode.
    omega = solve(*condense(K, f, D=np.array([0])))

    Ipp = np.sum(asm(polar_term, basis))
    gj = Ipp - omega @ f

    return gj


# -----------------------------
# Plot SP meshes
# -----------------------------
if DO_PLOT:
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    for ax, case_id in zip(axes, ("A", "B")):
        sec, _ = analyse_sp(case_id, carrier="E")
        sec.plot_mesh(materials=True, ax=ax)
        ax.set_title(f"Case {case_id}")

    plt.tight_layout()
    plt.show()


# -----------------------------
# Print comparison
# -----------------------------
print(f"Material A  E = {E_C:.4e}")
print(f"Material B  E = {E_S:.4e}")
print(f"Material A  G = {G_C:.4e}")
print(f"Material B  G = {G_S:.4e}")
print()

print(
    f"{'CASE':>6} "
    f"{'SP E.J':>16} "
    f"{'g_eff/e_eff':>14} "
    f"{'SP doc G.J':>16} "
    f"{'SP G-carrier':>16} "
    f"{'skfem M_i:=G_i':>18} "
    f"{'diff G %':>10}"
)

for case_id in ("A", "B"):
    _, ej_sp = analyse_sp(case_id, carrier="E")

    ratio_doc, gj_sp_doc = analyse_sp_doc_gj(case_id)

    _, gj_sp_g = analyse_sp(case_id, carrier="G")
    gj_sk_g = analyse_skfem_g(case_id)

    diff_g = (gj_sk_g / gj_sp_g - 1.0) * 100.0

    print(
        f"{case_id:>6} "
        f"{ej_sp:16.6e} "
        f"{ratio_doc:14.6e} "
        f"{gj_sp_doc:16.6e} "
        f"{gj_sp_g:16.6e} "
        f"{gj_sk_g:18.6e} "
        f"{diff_g:10.3f}"
    )
```
