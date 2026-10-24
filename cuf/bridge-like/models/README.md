# Bridge-like CSF model: geometry and inspection actions

This directory contains two complementary YAML files:

- [`bridge_geometry.yaml`](bridge_geometry.yaml) - the **CSF model definition**, containing the reference sections, polygon geometry, longitudinal extent, and mechanical participation parameters.
- [`action.yaml`](action.yaml) - an **inspection and post-processing recipe** for the `csf-actions` command. It does not define structural loads and is not itself consumed by the CSF–CUF coupling.

The separation is intentional: the CSF model is a continuously queryable geometric and participation field, whereas an action file merely selects how to examine that model. This distinction follows the [CSF Fundamentals](../../../docs/CSF_Fundamentals.md).

## 1. Model overview

`bridge_geometry.yaml` describes a bridge-like cross-section assembled from **four named polygonal regions**:

| Polygon | Role in the geometric assembly | Vertices in `S0` |
| --- | --- | ---: |
| `top_flange` | Wide upper flange with a nonrectangular lower boundary | 12 |
| `left_web` | Inclined left connection between flanges | 5 |
| `right_web` | Inclined right connection between flanges | 5 |
| `bottom_flange` | Lower connecting flange | 4 |

These names describe geometric regions; they do not automatically assign CUF expansion functions, degrees of freedom, boundary conditions, or external loading.

The YAML contains two reference configurations:

| Reference section | Longitudinal coordinate | Geometry |
| --- | ---: | --- |
| `S0` | `z: 0.0` | Original four-polygon assembly |
| `S1` | `z: 100.0` | Reuses the same polygon data as `S0` |

The longitudinal extent is therefore **100 coordinate units**. The file comments suggest SI units for the material parameter, but CSF's coordinates are not intrinsically unit-aware: the modeling/solver convention must be checked before asserting a physical length in metres.

Because the coordinates and polygon data are identical at both reference sections, this specific member is **prismatic**. The CSF concept itself is more general: different corresponding vertex positions in `S0` and `S1` can define a longitudinally varying section.

## 2. Continuous geometry: `S0`, `S1`, and polygon correspondence

In CSF, `S0` and `S1` are **boundary configurations for continuous interpolation**, not stations of a predefined mesh. At a longitudinal coordinate `z`, each vertex is evaluated from its corresponding endpoint vertices. For linear geometric interpolation, with

$$
\xi = \frac{z-z_0}{z_1-z_0}
$$

$$
\mathbf{r}_{i,j}(z) = (1-\xi)\mathbf{r}_{i,j}^{S0} + \xi\mathbf{r}_{i,j}^{S1}
$$

The polygon pair `i` and corresponding vertex index `j` define the local geometry without creating an explicit sequence of intermediate sections.

For this file, the corresponding vertices in `S0` and `S1` have identical coordinates:

$$
\mathbf{r}_{i,j}^{S0} = \mathbf{r}_{i,j}^{S1}
$$

Therefore, every polygon retains the same geometry along the entire longitudinal domain, resulting in a **prismatic section**.
### Ordered vertices matter

Each polygon is represented by an ordered vertex list in the local **two-dimensional sectional coordinate system**. CSF closes each polygon by joining its last vertex to its first. The ordering determines its oriented boundary and must remain consistent between reference sections; positive polygon area is expected. Correspondence is between the ordered polygons and their ordered vertices, not simply between unordered sets of points.

Several polygon boundaries share numerical coordinates: that is how flange–web interfaces are aligned geometrically. It should not be confused with a finite-element mesh connectivity definition.

### YAML anchors are not CSF interpolation operators

The model uses YAML anchors and aliases for reuse:

```yaml
S0:
  z: 0.0
  polygons: &id003
    # four polygon definitions
S1:
  z: 100.0
  polygons: *id003
```

The alias `*id003` reuses the polygon content attached to `&id003`. The vertex anchors `&id001` and `&id002` likewise allow the bottom flange to reuse corner coordinates already declared in the two webs. These are **YAML serialization features**, not CSF functions or a second geometry-generation mechanism.

For future tapered/nonprismatic versions, explicitly define separate endpoint polygon lists and preserve their order and vertex correspondence.

## 3. Material participation fields

Every polygon in this particular file declares:

```yaml
weight: 210000000000.0
```

The opening comment identifies the intended value as `E = 210 GPa`, assuming SI units, and explicitly asks the reader to verify the solver convention. **Do not interpret `weight` universally as a Young's modulus**: in CSF it is the native *axial/bending participation field* `w_i(z)`. Whether it represents a dimensionless factor or a modulus-valued stiffness in a coupled calculation depends on the adopted physical normalization and adapter/solver conventions.

The file also declares:

```yaml
shear_weight_laws:
  - iso(0.3)
```

This requests the documented isotropic shortcut with Poisson ratio `nu = 0.3` for the **shear/torsion participation** field `shear_w_i(z)`. The conceptual separation matters:

- `w_i(z)` governs axial/bending participation and the weighted sectional quantities that depend on it.
- `shear_w_i(z)` governs shear/torsion participation and is computed from the configured shear-weight law.

The `iso(0.3)` shortcut is a constitutive *relationship between participation fields* within CSF. It does not, by itself, prove that a downstream solver has assembled a complete three-dimensional isotropic constitutive tensor. That interpretation must be checked at the CUF adapter and solver level.

Because `S1` references exactly the same polygon definitions as `S0`, and no custom axial/bending weight law is listed, the endpoint weights coincide. This model is constant both geometrically and in its declared participation along the member.

## 4. What `action.yaml` controls

`action.yaml` is organized around the root key `CSF_ACTIONS`:

```yaml
CSF_ACTIONS:
  stations:
    station_edge:
      - 0
  actions:
    # ordered post-processing actions
```

The station group `station_edge` contains the single longitudinal coordinate `0`; in this model, it coincides with `S0`. **Inspection stations are not additional geometric reference sections**: their purpose is to ask for output at selected positions along the existing CSF field.

The actions are executed in the order in which they appear:

| Action | Declared configuration | Purpose |
| --- | --- | --- |
| `plot_volume_3d` | `title: "C-Shaped"`, `equalize_z: false` | Visual examination of the interpolated 3D member |
| `plot_properties` | `A`, `Ix`, `Iy`, `Ip` | Plots of selected sectional properties along the member |
| `plot_section_2d` | `station_edge`; polygon and vertex IDs enabled; legend disabled | Inspection of the section and its identifiers at `z = 0` |
| `section_selected_analysis` | `station_edge`; extended list of properties | Numerical sectional inspection at `z = 0` |

The literal title `C-Shaped` is a **plot label**, not a geometrical classification of this four-polygon bridge section. It appears to be inherited from a reusable action configuration and can be renamed to avoid confusion.

### Requested sectional properties

`plot_properties` requests `A`, `Ix`, `Iy`, and `Ip`. The selected-section analysis additionally requests `Cx`, `Cy`, `Ixy`, `I1`, `I2`, `rx`, `ry`, `Wx`, and `Wy`.

In conventional sectional mechanics these names refer to area, centroid coordinates, second moments and product of area, principal moments, radii of gyration, and elastic section moduli. The precise *weighted versus geometric* interpretation and numerical units should be checked against the CSF property implementation, particularly because this file sets `weight` to a modulus-like value rather than to `1.0`.

### Interpreting plots for this specific model

Since both end sections share the same geometry and weights, any properly computed quantity depending only on the declared local section should be **constant along the longitudinal coordinate**. This makes `plot_properties` useful as a sanity check: variation would indicate another applied law, an implementation choice, or an issue worth investigating.

The 2D plot with polygon/vertex IDs is especially useful for verifying ordered polygon connectivity at the web–flange junctions before exporting the geometry to another numerical representation.

## 5. Running the inspection

From a working environment in which `csf-actions` is installed and available, run the two files together, for example from this directory:

```bash
csf-actions bridge_geometry.yaml action.yaml
```

This pairing follows the command form documented in the comments of `action.yaml` (`csf-actions <model.yaml> <actions.yaml>`). The example commands currently embedded in that file name other sample models, not `bridge_geometry.yaml`.

The location and format of generated plots or exported data depend on the installed `csf-actions` implementation and its configuration; they are not prescribed by these two YAML files.

**Important:** `action.yaml` is for model inspection. It should not be confused with a CUF case definition, which separately controls structural discretization, restraints, loading, solution parameters and output.

## 6. Model verification checklist

Before using this geometry in a coupled CSF–CUF analysis, verify the following:

1. **Geometry:** all four polygons have valid, positively oriented boundaries; shared junctions do not leave unintended gaps or create overlapped solid areas.
2. **Correspondence:** each `S0` polygon matches the intended `S1` polygon, with identical vertex counts and consistent ordering.
3. **Length and units:** `z = 0 ... 100` and all in-plane coordinates use the length unit expected by the downstream problem.
4. **Material normalization:** confirm whether `weight = 210e9` is interpreted as Young's modulus, a scaled participation, or another effective coefficient by the intended adapter.
5. **Shear relation:** confirm that `iso(0.3)` produces the intended `shear_w` in the model's constitutive convention; do not infer a full material law merely from this shortcut.
6. **Section properties:** compare geometric properties and weighted properties consistently; a `weight` of `E` may produce stiffness-weighted results rather than pure geometric results.
7. **Plot labels:** consider replacing `title: "C-Shaped"` with a bridge-specific title.
8. **Coordinate frames:** distinguish the sectional coordinates used in this YAML, the CSF longitudinal `z`, and any different axis ordering used in the CUF problem.

## 7. Connection to CSF and CUF

The two YAML files belong to different architectural layers:

```text
bridge_geometry.yaml
  └── CSF field definition
       ├── two reference section configurations (S0, S1)
       ├── corresponding polygon/vertex geometry
       └── axial/bending and shear/torsion participation
                 │
                 ├── csf-actions + action.yaml
                 │      └── inspect geometry and sectional properties
                 │
                 └── CSF–CUF adapter (separate analysis workflow)
                        └── CUF discretization, solution and output
```

The central CSF concept is preserved: **the geometry and participation fields are primary objects, independently queryable at arbitrary longitudinal positions**. `action.yaml` interrogates those objects but does not define them, while CUF consumes suitable derived quantities through its own analysis interface.

## 8. Further reading

- [CSF Fundamentals](../../../docs/CSF_Fundamentals.md) - reference sections, polygon correspondence, continuous geometry and participation laws.
- [CSF coordinate systems](../../docs/coordinate_systems.md) - coordinate-frame conventions for the CUF-related workflow.
- [Bridge-like project](../) - analyses and examples that use this family of geometry models.

---

*Scope:* this README documents the two YAML files as present in the repository and their conceptual roles. It does not claim numerical validation against FEM or confirm how a specific CUF case interprets the declared modulus-like weights.
