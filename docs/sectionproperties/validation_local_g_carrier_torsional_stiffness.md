# Verification Note - Torsional Stiffness of Composite Cross-Sections
## G-Carrier Approach in `sectionproperties` - Independent FEM Verification

---

## 1. Background

The Python library `sectionproperties` computes the Saint-Venant torsional constant *J* by solving Prandtl's stress-function (warping) problem via finite elements. For composite sections, the library uses each material's Young's modulus *E*ᵢ as the local carrier, yielding a weighted quantity *EJ* rather than the torsionally relevant *GJ*. This behaviour is documented in the [Retrieving Section Properties](https://sectionproperties.readthedocs.io/en/latest/examples/results/get_results.html) example page:

> *"If materials are specified, the values calculated for the torsion constant … are elastic modulus weighted."*

The composite torsional rigidity *EJ* is retrieved via [`get_ej()`](https://sectionproperties.readthedocs.io/en/stable/gen/sectionproperties.analysis.section.Section.html). The library also exposes [`get_e_eff()`](https://sectionproperties.readthedocs.io/en/stable/gen/sectionproperties.analysis.section.Section.html) and [`get_g_eff()`](https://sectionproperties.readthedocs.io/en/stable/gen/sectionproperties.analysis.section.Section.html) to compute area-averaged effective moduli, from which a global correction is derived:

$$GJ_\text{doc} = \frac{g_\text{eff}}{e_\text{eff}} \cdot EJ$$

This multiplier is a single scalar ratio and does not account for the spatial distribution of *G*ᵢ across the section. For sections where the stiffer material is concentrated in a specific region, the approximation introduces a non-negligible error.

---

## 2. G-Carrier Approach

The warping (Prandtl) formulation is formally identical regardless of which local scalar field is used as the carrier. The torsionally correct procedure is:

1. Assign each material's shear modulus *G*ᵢ to the `E` field of the corresponding `Material` object in `sectionproperties`.
2. Run `calculate_frame_properties()` and retrieve `get_ej()`. Because the carrier is now *G*ᵢ, the result is the correct *GJ* of the composite section.
3. Poisson's ratio inputs retain their physical values; they affect only mesh generation and have no influence on the warping solution.

No external scaling or post-processing is required. The approach is exact within the finite-element discretisation error of the mesh.

---

## 3. Verification with scikit-fem

### 3.1 Reference Solver

An independent warping FEM was implemented with `scikit-fem` (`skfem`), a Python finite-element library with no dependency on `sectionproperties`. The problem is formulated in weak form as:

$$\int G_i \, \nabla\omega \cdot \nabla v \, dA = \int G_i \, \nabla v \cdot [y_c,\, -x_c] \, dA$$

where *ω* is the warping function, *v* is the test function, and *(xc, yc)* is the *G*-weighted centroid. The torsional stiffness is recovered as:

$$GJ = I_{pp,G} - \omega^\top f$$

with *I*pp,G the *G*-weighted polar second moment of area and *f* the assembled load vector.

The mesh is a structured triangular grid (240 × 640 elements) covering the full rectangular domain, with the local *G*ᵢ field assigned point-wise at each quadrature point.

### 3.2 Test Cases

Two rectangular cross-sections (B = 300 mm, D = 400 mm) are analysed. Both sections are composed of 60 % Material A and 40 % Material B by height (STEEL_FRAC = 0.4).

| Case | Layout |
|------|--------|
| **A** | Material B split equally between bottom and top layers (symmetric) |
| **B** | Material B concentrated entirely at the bottom (asymmetric) |

#### Material Properties

| Material | *E* [N/mm²] | *ν* [–] | *G* [N/mm²] |
|----------|------------|---------|------------|
| A (concrete-like) | 30 000 | 0.20 | 12 500 |
| B (steel-like)    | 200 000 | 0.30 | 76 923 |

---

## 4. Results

| Case | SP G-carrier *GJ* [N·mm²] | `skfem` *GJ* [N·mm²] | Difference [%] | SP doc *GJ* error [%] |
|------|--------------------------|----------------------|---------------|-----------------------|
| A    | 4.5983 × 10¹³            | 4.5978 × 10¹³        | −0.012        | −4.11                 |
| B    | 5.1046 × 10¹³            | 5.1042 × 10¹³        | −0.008        | −2.63                 |

The column **SP G-carrier** refers to the result obtained from `sectionproperties` with the G-carrier substitution described in Section 2. The column **`skfem` G-carrier** is the fully independent FEM result. The column **SP doc *GJ* error** quantifies the discrepancy between the library's documented global correction and the local G-carrier result, taken as reference.

---

## 5. Discussion

The G-carrier results from `sectionproperties` and `skfem` agree to within 0.012 % across both test cases. The residual difference is attributable solely to the difference in mesh refinement between the two solvers (triangular unstructured mesh in `sectionproperties` vs. structured 240 × 640 grid in `skfem`).

The documented global correction ($g_\text{eff}/e_\text{eff}$ scaling) introduces errors of −4.1 % and −2.6 % for cases A and B respectively. The error is larger for the symmetric case (A), where the two high-stiffness layers are spatially separated, amplifying the inadequacy of a single global scalar multiplier.

---

## 6. Conclusion

Substituting *G*ᵢ for *E*ᵢ in the `sectionproperties` material definition is a correct and sufficient procedure to compute *GJ* for composite cross-sections. The approach is verified against an independent `skfem` implementation of the warping problem, with agreement better than 0.02 % for both a symmetric and an asymmetric material layout. The library's documented global correction should not be used when an accurate spatial distribution of *GJ* is required.

---
```
pip install sectionproperties scikit-fem
```

```
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
B, D = 300.0, 400.0                 # Section width and height [mm]
#STEEL_FRAC = 0.3888                 # Material B fraction of total area
STEEL_FRAC = 0.4                     # Material B fraction of total area

E_C, NU_C = 30.0e3, 0.20            # Material A: E [N/mm2], Poisson
E_S, NU_S = 200.0e3, 0.30           # Material B: E [N/mm2], Poisson

G_C = E_C / (2.0 * (1.0 + NU_C))    # Material A: G [N/mm2]
G_S = E_S / (2.0 * (1.0 + NU_S))    # Material B: G [N/mm2]

MESH_SIZE_SP = 500.0
SK_NX =240# 160
SK_NY =640# 240

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
        Standard sectionproperties input.
        get_ej() follows the local E_i carrier.

    carrier = "G":
        Local G-carrier workaround.
        Since get_ej() follows the local E carrier, setting E_SP := G_i
        makes sectionproperties compute a G_i-carrier torsional stiffness.
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


def make_geometry(case_id, carrier):
    mat_a, mat_b = make_materials(carrier)

    x1, x2 = -B / 2.0, B / 2.0
    y1, y2 = -D / 2.0, D / 2.0

    h_s = D * STEEL_FRAC

    if case_id == "A":
        # Material B split equally at bottom and top.
        h = h_s / 2.0

        parts = [
            make_rect(x1, x2, y1,     y1 + h, mat_b),
            make_rect(x1, x2, y1 + h, y2 - h, mat_a),
            make_rect(x1, x2, y2 - h, y2,     mat_b),
        ]

    elif case_id == "B":
        # Material B concentrated at the bottom.
        parts = [
            make_rect(x1, x2, y1,       y1 + h_s, mat_b),
            make_rect(x1, x2, y1 + h_s, y2,       mat_a),
        ]

    else:
        raise ValueError(f"Unknown case_id: {case_id}")

    geom = CompoundGeometry(geoms=parts)
    geom.create_mesh(mesh_sizes=MESH_SIZE_SP)

    return geom


def analyse_sp(case_id, carrier):
    sec = Section(make_geometry(case_id, carrier))
    sec.calculate_frame_properties()
    ej = sec.get_ej()
    return sec, ej


def analyse_sp_doc_gj(case_id):
    """
    sectionproperties documented global correction:

        SP doc G.J = (g_eff / e_eff) * SP E.J
    """

    sec, ej = analyse_sp(case_id, carrier="E")

    # Required before reading effective material properties.
    sec.calculate_geometric_properties()

    e_eff = sec.get_e_eff()
    g_eff = sec.get_g_eff()

    ratio = g_eff / e_eff
    gj_doc = ratio * ej

    return ej, ratio, gj_doc


def analyse_sp_g_carrier(case_id):
    """
    Local G-carrier run inside sectionproperties:

        E_SP := G_i
    """

    _, gj_gcarrier = analyse_sp(case_id, carrier="G")
    return gj_gcarrier


# -----------------------------
# skfem helpers
# -----------------------------
def carrier_g(case_id, x, y):
    """
    Return the local shear carrier G_i for the skfem formulation.
    """

    y1, y2 = -D / 2.0, D / 2.0
    h_s = D * STEEL_FRAC

    if case_id == "A":
        h = h_s / 2.0
        mask_b = (y <= y1 + h) | (y >= y2 - h)
        return np.where(mask_b, G_S, G_C)

    elif case_id == "B":
        mask_b = y <= y1 + h_s
        return np.where(mask_b, G_S, G_C)

    else:
        raise ValueError(f"Unknown case_id: {case_id}")


def analyse_skfem_g(case_id, nx=SK_NX, ny=SK_NY):
    """
    Independent warping FEM with local shear carrier M_i := G_i.

    Weak form:
        int G_i grad(omega) . grad(v) dA
        =
        int G_i grad(v) . [y, -x] dA

    Result:
        GJ = Ipp_G - omega.T @ f
    """

    x = np.linspace(-B / 2.0, B / 2.0, nx + 1)
    y = np.linspace(-D / 2.0, D / 2.0, ny + 1)

    msh = MeshTri.init_tensor(x, y)
    basis = Basis(msh, ElementTriP1())

    @LinearForm
    def m0(v, w):
        M = carrier_g(case_id, w.x[0], w.x[1])
        return M * v

    @LinearForm
    def mx(v, w):
        M = carrier_g(case_id, w.x[0], w.x[1])
        return M * w.x[0] * v

    @LinearForm
    def my(v, w):
        M = carrier_g(case_id, w.x[0], w.x[1])
        return M * w.x[1] * v

    M_area = np.sum(asm(m0, basis))
    cx = np.sum(asm(mx, basis)) / M_area
    cy = np.sum(asm(my, basis)) / M_area

    @BilinearForm
    def lhs(omega, v, w):
        M = carrier_g(case_id, w.x[0], w.x[1])
        return M * dot(grad(omega), grad(v))

    @LinearForm
    def rhs(v, w):
        M = carrier_g(case_id, w.x[0], w.x[1])
        x_c = w.x[0] - cx
        y_c = w.x[1] - cy
        return M * (grad(v)[0] * y_c - grad(v)[1] * x_c)

    @LinearForm
    def polar_term(v, w):
        M = carrier_g(case_id, w.x[0], w.x[1])
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
print(f"STEEL_FRAC  = {STEEL_FRAC:.6f}")
print()
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
    f"{'error_doc %':>13} "
    f"{'skfem M_i:=G_i':>18} "
    f"{'diff G %':>10}"
)

for case_id in ("A", "B"):
    sp_ej, ratio, sp_doc_gj = analyse_sp_doc_gj(case_id)
    sp_gcarrier = analyse_sp_g_carrier(case_id)
    skfem_gcarrier = analyse_skfem_g(case_id)

    error_doc = (sp_doc_gj / sp_gcarrier - 1.0) * 100.0
    diff_g = (skfem_gcarrier / sp_gcarrier - 1.0) * 100.0

    print(
        f"{case_id:>6} "
        f"{sp_ej:16.6e} "
        f"{ratio:14.6e} "
        f"{sp_doc_gj:16.6e} "
        f"{sp_gcarrier:16.6e} "
        f"{error_doc:13.3f} "
        f"{skfem_gcarrier:18.6e} "
        f"{diff_g:10.3f}"
    )
```


