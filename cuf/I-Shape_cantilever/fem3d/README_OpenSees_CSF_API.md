# CSF–CUF / OpenSees FEM3D — API-based verification, v01 (2026-11-20)

## What this package does

Adds a **local-project** OpenSeesPy H8 (`stdBrick`) FEM3D verification driver for an existing `type: composite` CSF–CUF case. The driver reads the **same case, model, physical load and physical clamp** as CUF, without duplicating CSF geometry or YAML parsing. No CSF/CUF library file and no solver routine is changed.

**No YAML file is parsed directly in the FEM code.** The driver uses these *existing* entry points:

| Information | Reused API | Why no new implementation is needed |
|---|---|---|
| Resolve case and problem | `csf.cuf.case.load_case()`, `csf.cuf.problem.problem_api.load_problem()` | Existing case/problem YAML parser |
| Instantiate local load and constraint adapters | `build_local_composite_problem()` | Existing local composite loader and factory contract |
| Create continuous CSF field | `CSFCUFModelBridge.from_yaml()` | Uses the official `CSFReader` internally; FEM never parses CSF YAML |
| Geometry and topology | `bridge.section_provider.longitudinal_domain()`, `.number_of_domains(x)`, `.domain(x,k)`, `.inspect_section_entities(x)` | CSF section evaluation, stable domain identity, child topology |
| Materials | `bridge.domain_state(x,k)` | Absolute physical `E`, `G` and Poisson data from CSF |
| Selected loaded edges | `load.physical_surface_tractions(...)` (new public method on the existing local load) | Shares exactly the same selection/validation with CUF `build_load_vector()` |
| Physical constraint | `constraint.physical_boundary_condition()` (new public method on the existing local clamp) | Reuses the already-validated full start-section clamp choice |

What is **new**: only the conforming multi-domain 3D H8 mesh generation, FE-consistent projected-area nodal loading, `OpenSeesPy` assembly/solve, and NPZ output. The old `run_bending_fem3d_v2.py` has an I-section-only three-polygon mesher and a different load/support. `write_opensees_geometry` is for beam `forceBeamColumn` geometry/station export, not an H8 solid mesh. Neither can replace this new step without changing the mechanical problem.

## Files

```text
I-Shape_cantilever/
  adapters/loads/vertical_face_tractions.py         # v03, shared edge-selection API
  adapters/constraints/physical_start_section_clamp.py  # v03, physical BC API
  fem3d/run_opensees_csf.py                          # v01, generic Q4->H8 OpenSees driver
```

Every modified/new Python file has a version identifier on its **first line**. There is no YAML to replace. These files expect the existing `case.py`, `__main__.py`, and `problem_api.py` v01/v02 local composite support to already be installed.

Install the two `adapters/` files by replacing the same local-project paths. Copy the `fem3d/` script into the local project (create the directory if needed). Keep a backup of the previous adapter files.

## Commands

Run from the `cuf/I-Shape_cantilever` project folder with the same environment that runs `csf-cuf`:

```bash
python fem3d/run_opensees_csf.py \
  cases/i_shaped_taper80_lagrangeL9_v4_E10_web3_composite.yaml \
  fem3d/output/geometry_material_80pct_fem3d.npz \
  --nx 16 --nu 3 --nv 3
```

`OpenSeesPy` must be installed in that virtual environment (usually `python -m pip install openseespy`). It is intentionally imported only when a solve is requested.

To **validate** the CSF geometry, conforming mesh, material, force resultant and boundary selection **without solving**:

```bash
python fem3d/run_opensees_csf.py \
  cases/i_shaped_taper80_lagrangeL9_v4_E10_web3_composite.yaml \
  fem3d/output/geometry_material_80pct_mesh_only.npz \
  --nx 8 --nu 2 --nv 2 --mesh-only
```

The two NPZ files are deliberately distinguishable: `status` is `solved_opensees` only after a successful OpenSees solve, and `mesh_only` otherwise. For `mesh_only`, the `displacement` array is empty and must **never** be used as a reference solution.

## What stays identical to the CUF mechanical problem

- CSF evaluated continuously by the same field and domain providers; no nine-domain or I-section assumption.
- `lower_z_MPa: -7.17` and the polygon names are supplied **only by the already-existing composite problem**; no parallel FEM YAML options are introduced.
- Load direction **global Z**, with density relative to the **projected XY area**, exactly as in the CUF adapter: `t = pz * abs(n_z) * e_z` per unit physical face area. It is **not** a normal pressure or a traction constant per actual inclined area.
- All translations on the initial end section are fixed; the far end is free. The CUF SVD clamp and the FEM fixed nodal translations represent the same physical condition but have different discretized algebraic forms.
- `axial_gauss` and `edge_gauss` from the load adapter also control the FE-consistent surface quadrature; `face_gauss` stays unused, as in the old adapter.

## Geometric and material scope; no silent approximations

The domain count comes from CSF and is not hardcoded. The initial **H8 mesher** accepts:

- Any positive number of **convex, counterclockwise Q4** solid domains, with stable CSF topology from S0 to S1.
- Shared interfaces only if they match as **entire edges**; shared nodes are merged, and a nonconforming interface or T-junction is rejected with a specific error. The same subdivision counts `nu` and `nv` apply to each Q4; when shared edges use different local orientations, incompatible counts are rejected.
- No void material domains, nested polygons, cut-outs, changing connectivity, inverted or concave Q4s. These require future meshing work, not a special case for nine domains.

The **loaded-edge adapter** additionally requires exactly two edges parallel to global Y on each selected Q4; longitudinally inclined/tapered physical surfaces are supported. The selected edge must be externally exposed. Unselected domains do not need Y-parallel edges to be meshed.

OpenSees `ElasticIsotropic` requires `G = E / [2(1+nu)]`. This relation is checked for each CSF material state at each H8 element midpoint. A material not satisfying the isotropic relation raises an error. Variable `E(x)` is approximated **piecewise constant per H8 element** at its longitudinal midpoint and is resolved by subsequent **FEM convergence refinement**; it is not silently treated as constant across the whole beam.

## NPZ data contract

The compressed NPZ contains, among others:

- `nodes`, `elements` (standard H8 local ordering, zero-based indices), `element_region`, `element_region_names`, `element_xmid`;
- `element_E`, `element_G`, `element_nu`, `element_material_tag`;
- `loaded_faces`, `loaded_face_pz`, `loaded_face_domain`, `nodal_loads`, `force_resultant_N`, `moment_resultant_Nmm`;
- `end0_nodes`, `end1_nodes`, `support_reactions`;
- `displacement` (N x 3, only when solved), `status`, `mesh_divisions`, `case_name`, `model_path`, `problem_path`, `x0`, `x1`.

The principal geometry/displacement arrays follow the convention of the supplied older OpenSees FEM3D NPZ. No legacy three-polygon vertex-track assumptions are imposed. A generic FEM–CUF comparison can be developed separately after the two convergence studies.

## Verification performed for this package

**Executed without OpenSees:**

1. CUF `build_load_vector()` original v02 versus new v03 on the same CSF model and test CUF basis/mesh: **byte-identical vector, resultant and moment**.
2. Selected loaded CSF domains: **7, 8, 9**, with exactly three lower exterior faces.
3. Physical resultant: **F = (0,0,-473220) N**; reference **M_y = +236610000 Nmm**, for the 1000 mm taper and bottom flange width 66 mm.
4. Actual CSF model: conforming meshes at `(nx,nu,nv)` of `(1,1,1)`, `(4,2,2)` and `(8,3,3)`; all H8 Gauss Jacobians positive.
5. Synthetic CSF-compatible providers: **1, 2, 5, 12** domains; shared-edge conformity passes; a partial-edge T-junction is rejected.
6. `--mesh-only` executes all the way through NPZ output with `status=mesh_only`.

**NOT executed in this environment:** the actual OpenSees solve, because `openseespy` is not installed here. There is no claim yet of a verified OpenSees displacement solution; run the first modest mesh on the user's OpenSees-enabled machine and check reactions and displacement sanity before launching convergence.

Official OpenSees references for the `stdBrick` node contract and `ElasticIsotropic` are:
- https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/stdBrick.html
- https://openseespydoc.readthedocs.io/en/stable/src/stdBrick.html
