# CSF-CUF independent longitudinal convergence

## Objective and scope

The numerical stabilization of the CSF-CUF solution is assessed independently of the FEM3D reference. The physical model, boundary conditions, applied loads and transverse CUF approximation are unchanged during the study. The transverse kinematics use the nine-domain quadratic Lagrange expansion (**L9**); **the L9 subdivision is not refined** here. The convergence variables are solely the discretization of the one-dimensional longitudinal problem:

- **Longitudinal h-refinement:** number of beam finite elements \(N\), holding the longitudinal Lagrange degree \(p\) fixed.
- **Longitudinal p-refinement:** degree \(p\) of the longitudinal shape functions, holding \(N\) fixed.

The available independent CUF studies consist of \(N=2,4,6,8,10,12,16,20\) at \(p=12\), and \(p=2,3,\ldots,12\) at \(N=10\). Their CUF results have already been calculated and archived.

## Monitored quantity

The primary observable is the vertical displacement at the **same physical point for every CUF discretization**:

\[
P=(x,y,z)=(1000,-33,35)\;\mathrm{mm},\qquad q_k=u_z^{(k)}(P).
\]

The values are read from the existing CUF response output (`response_eq1.txt`), which records the evaluated physical position and all three displacement components. The script matches the requested coordinates and rejects a missing or non-unique sample. It does **not** approximate geometry, material fields or the CUF displacement field anew. The corresponding solved CUF NPZ files are checked for consistency and traceability.

## Successive-change criterion

For the \(k\)-th computed configuration in one refinement sequence, define

\[
\delta_k=100\frac{|q_k-q_{k-1}|}{|q_k|}\quad[\%].
\]

The first configuration for which **two consecutive available differences** satisfy

\[
\delta_{k-1}\leq\varepsilon,\qquad \delta_k\leq\varepsilon,
\qquad \varepsilon=0.5\%,
\]

is identified as *stabilized according to the adopted study criterion*. A zero denominator makes the relative criterion undefined and is rejected. This is a study-specific stabilization threshold, rather than a GCI/Richardson error estimate. It applies to the monitored displacement only and must not be described as proof of convergence of the entire three-dimensional displacement or stress field.

The two studies are evaluated independently; **the difference between CUF and FEM3D displacements does not enter this criterion**.

## Results from the available archived solutions

| Study | Fixed numerical parameter | First configuration meeting the two-increment rule | \(u_z(P)\) [mm] |
|---|---|---|---:|
| h-refinement | \(p=12\) | \(N=6\) | \(-80.41228804958\) |
| p-refinement | \(N=10\) | \(p=4\) | \(-80.34557893389\) |

These are the **first configurations passing the stated rule**, not a claim that the uncomputed joint combination \((N,p)=(6,4)\) has been solved or verified. The available series share the explicitly computed configuration \((N,p)=(10,12)\), for which both give \(u_z(P)=-80.41303677339\) mm. The series extends through \(N=20\) and \(p=12\), respectively.

When choosing a CSF-CUF solution for a final sectional-force comparison, use an **actually solved** configuration (for example the common \(N=10,p=12\) solution), document the choice, and check the stabilization of the sectional resultants separately. The displacement probe alone does not establish the accuracy of \(N(x)\), \(T_z(x)\) or \(M_y(x)\).

## Source integrity and reproducibility

The postprocessor reads the archived runs organized as follows:

```text
output/cuf_convergence/
  h_v02/step_001/...step_008/
  p_v02/step_001/...step_011/
```

For every step it checks the SHA-256 hashes of `response_eq1.txt` and the solved `*.cuf.npz` against `step_manifest.json`; checks the NPZ's longitudinal element count and coefficient order; and checks that the CSF-model, problem, load-adapter and constraint-adapter hashes agree across all runs. If the numerical case YAML files are provided through `--cases`, it also validates their hashes, unchanged quadratic L9 expansion, and unchanged numerical settings other than \(N\) and \(p\). The case YAML is used only for **numerical configuration verification**, never to reconstruct a CSF geometry, domain or material law.

The script does not call a FEM solver, a CUF solver, or FEM3D field evaluation. It uses only archived CUF solution data; it does not need to interrogate CSF physical APIs because it does not compute any new physical quantity.

## Paper-ready methodological paragraph

> The longitudinal discretization of the CSF-CUF model was assessed through two independent refinement studies with a fixed transverse quadratic Lagrange (L9) expansion. In the h-study, the number of one-dimensional finite elements was increased while keeping the longitudinal polynomial degree fixed at \(p=12\); in the p-study, the polynomial degree was increased at fixed \(N=10\). At each configuration, the vertical displacement was evaluated at the same physical point \(P=(1000,-33,35)\) mm. A study-specific stabilization criterion required two successive relative changes in this displacement not exceeding 0.5%. The criterion was evaluated exclusively from CSF-CUF solutions, without reference to FEM3D displacements. The resulting stabilization assessment concerns this displacement observable and does not constitute an independent convergence estimate for the recovered sectional stress resultants.

## Exclusions

- No CUF-FEM3D displacement discrepancy is used to establish CUF convergence.
- No external surface stress/traction recovery is analyzed.
- No FEM3D results or reactions are included in the convergence decision.
- The L9 transverse basis is fixed, not refined.
- Sectional forces and moments \(N(x),T_z(x),M_y(x)\) require their own evaluation on the chosen solved configuration.
