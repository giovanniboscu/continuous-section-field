# Displacement-field verification against an independent three-dimensional finite-element solution

## Common physical domain and reference configuration

The displacement-field comparison is performed between a refined one-dimensional model based on the Carrera Unified Formulation (CUF) and an independently discretized three-dimensional finite-element (FEM3D) model. Both models are intended to represent the same physical member, whose cross-sectional geometry and constitutive description are provided by the Continuous Section Field (CSF). The comparison is restricted to displacements; it does not require stress reconstruction or the evaluation of equilibrium residuals.

Let $x\in[x_0,x_1]$ denote the longitudinal coordinate and $(y,z)$ the transverse coordinates. The physical domain is

$$
\mathcal B=\left\{(x,y,z)\,\middle|\,x\in[x_0,x_1],\ (y,z)\in\Omega(x)\right\},
\qquad
\Omega(x)=\bigcup_{k\in\mathcal K}\Omega_k(x),
$$

where $\Omega_k(x)$ are the physical cross-sectional subdomains defined by CSF. The corresponding physical and constitutive description is denoted by $\mathcal S(x)$. The displacement comparator queries the existing CSF interfaces when geometric information is required; it does not reconstruct the section from reference stations or impose any independent interpolation law for material properties.

All displacement components are expressed in the common CUF/FEM3D Cartesian frame, $\mathbf u=(u_x,u_y,u_z)^\mathsf T$. In the present implementation, the coordinate correspondence with the native CSF frame is $(X,Y,Z)_{\mathrm{CSF}}=(y,z,x)$. Consequently, no permutation, sign change, rigid-body alignment, or fitted scaling is applied between the two computed displacement fields. Consistent physical units are required; any units recorded in checkpoint metadata are retained for traceability, but no automatic conversion or dimensional-consistency correction is performed.

## Reconstruction of the two displacement fields

Within a cross-sectional subdomain $\Omega_k(x)$, the CUF displacement approximation may be written as

$$
\mathbf u_h^{\mathrm{CUF}}(x,y,z)
=\sum_{\tau\in\mathcal T_k}F_\tau^{(k)}(x,y,z)\,\mathbf q_\tau^{(k)}(x),
\qquad (y,z)\in\Omega_k(x),
$$

where $F_\tau^{(k)}$ are the selected transverse approximation functions and $\mathbf q_\tau^{(k)}$ are their longitudinal generalized displacement fields. With a longitudinal finite-element discretization, these generalized fields have the representation

$$
\mathbf q_\tau^{(k)}(x)
=\sum_{a\in\mathcal I(x)}N_a^{\parallel}(x)\,\mathbf q_{\tau a}^{(k)}.
$$

This notation permits distinct transverse expansions in different subdomains and allows the transverse functions to depend on the longitudinal position. Any coupling or continuity constraints between expansion coefficients are already reflected in the solved CUF state. In post-processing, $\mathbf u_h^{\mathrm{CUF}}$ is evaluated directly from that state using the standard compiled-displacement-field interface. The comparator does not independently implement CUF reconstruction.

For the FEM3D solution, consider an eight-node isoparametric hexahedral element $e$ with natural coordinates $\boldsymbol\xi=(r,s,t)\in[-1,1]^3$. Its trilinear shape functions are

$$
N_a^{\mathrm{H8}}(r,s,t)
=\frac{1}{8}(1+r_ar)(1+s_as)(1+t_at),
\qquad a=1,\ldots,8,
$$

with $(r_a,s_a,t_a)\in\{-1,+1\}^3$ ordered according to the element connectivity. If $\mathbf X_{ea}$ and $\mathbf d_{ea}$ denote the physical coordinates and solved displacement vectors of its nodes, respectively, the isoparametric position and displacement fields are

$$
\mathbf x_e(\boldsymbol\xi)
=\sum_{a=1}^{8}N_a^{\mathrm{H8}}(\boldsymbol\xi)\mathbf X_{ea},
\qquad
\mathbf u_{h,e}^{\mathrm{FEM}}(\boldsymbol\xi)
=\sum_{a=1}^{8}N_a^{\mathrm{H8}}(\boldsymbol\xi)\mathbf d_{ea}.
$$

This mapping is the ordinary interpolation of the *FEM element*. It is not an additional CSF geometry law. The finite-element mesh approximates the common physical geometry, while CSF remains authoritative for the underlying section definition.

## Pointwise correspondence and sampling

The comparison is carried out at an explicitly defined set of physical sample positions $\mathcal P=\{\mathbf p_i\}_{i=1}^{n_s}$. For a sample located inside H8 element $e$, its coordinate is obtained from the FEM isoparametric mapping:

$$
\mathbf p_i=\mathbf x_e(\boldsymbol\xi_i),
\qquad
\mathbf u_i^{\mathrm{FEM}}=\mathbf u_{h,e}^{\mathrm{FEM}}(\boldsymbol\xi_i),
\qquad
\mathbf u_i^{\mathrm{CUF}}=\mathbf u_h^{\mathrm{CUF}}(\mathbf p_i).
$$

Thus, **the two methods are evaluated at the identical, unmodified physical position** $\mathbf p_i$; there is no nearest-neighbour matching or interpolation between separate output grids. Three distinct sampling procedures are supported:

1. **Unique FEM nodes.** Each physical mesh node contributes one sample. The FEM value is its stored nodal displacement, and the CUF field is evaluated at the same nodal coordinate. A shared node is not counted separately for each incident element.
2. **H8 natural centers.** Each element contributes the sample $\boldsymbol\xi=\mathbf 0$, mapped to physical space through $\mathbf x_e$. This point is the image of the reference-element center; it need not coincide with the physical element's volume centroid.
3. **Interior Gaussian samples.** Each element contributes the tensor-product points $r,s,t\in\{-1/\sqrt{3},+1/\sqrt{3}\}$. Both displacement vectors are evaluated at their common mapped coordinates.

The sampling sets are analysed separately. Their statistics must not be conflated because they have different spatial distributions. Nodal samples may lie on geometric or material interfaces, where ownership of a unique CSF subdomain is not defined. The compiled CUF evaluator provides a deterministic displacement trace at such positions. Interior element samples avoid that ambiguity and are the primary basis for volume-based comparison.

## Displacement discrepancies and unweighted statistics

At each paired sample, define the signed displacement discrepancy and its Euclidean norm by

$$
\boldsymbol\delta_i
=\mathbf u_i^{\mathrm{CUF}}-\mathbf u_i^{\mathrm{FEM}},
\qquad
e_i=\|\boldsymbol\delta_i\|_2
=\sqrt{\delta_{ix}^2+\delta_{iy}^2+\delta_{iz}^2}.
$$

For a component $\alpha\in\{x,y,z\}$, the absolute root-mean-square discrepancy and the corresponding vector measure are

$$
\operatorname{RMSE}_{\alpha}
=\left(\frac{1}{n_s}\sum_{i=1}^{n_s}\delta_{i\alpha}^{\,2}\right)^{1/2},
\qquad
\operatorname{RMSE}_{\mathbf u}
=\left(\frac{1}{n_s}\sum_{i=1}^{n_s}\|\boldsymbol\delta_i\|_2^2\right)^{1/2}.
$$

The discrete relative $L^2$ discrepancies, using FEM3D as the reference in the denominator, are

$$
\varepsilon_{\alpha}^{\mathrm{rel}}
=100\left(\frac{\sum_i\delta_{i\alpha}^{\,2}}
{\sum_i(u_{i\alpha}^{\mathrm{FEM}})^2}\right)^{1/2}\%,
\qquad
\varepsilon_{\mathbf u}^{\mathrm{rel}}
=100\left(\frac{\sum_i\|\boldsymbol\delta_i\|_2^2}
{\sum_i\|\mathbf u_i^{\mathrm{FEM}}\|_2^2}\right)^{1/2}\%.
$$

These are **norms over a specified discrete sample set**, not exact integrals over the continuous physical domain. They are reported as undefined if the corresponding reference denominator vanishes; pointwise division by a nearly zero displacement is deliberately avoided.

Additional diagnostics comprise the maximum component and vector discrepancies,

$$
\delta_{\alpha,\max}=\max_i|\delta_{i\alpha}|,
\qquad
e_{\max}=\max_i\|\boldsymbol\delta_i\|_2,
$$

with the corresponding physical sample coordinates, as well as medians and selected percentiles of absolute discrepancies. If a signed offset is of interest, it is quantified by the *mean signed discrepancy*

$$
\overline\delta_\alpha=\frac{1}{n_s}\sum_i\delta_{i\alpha}.
$$

This last quantity is **not** a mean displacement and is never used as a surrogate for displacement at a section or material point. In particular, raw displacement components are not averaged over arbitrary longitudinal groups.

## Volume-weighted measures

Uniform sample counting does not approximate a physical volume integral when element volumes vary. Accordingly, interior sampling is supplemented by FEM quadrature weights. For element $e$, define the geometric Jacobian

$$
\mathbf J_e(\boldsymbol\xi)
=\frac{\partial\mathbf x_e}{\partial\boldsymbol\xi}
=\sum_{a=1}^{8}\mathbf X_{ea}\otimes\nabla_{\boldsymbol\xi}N_a^{\mathrm{H8}}(\boldsymbol\xi),
\qquad
J_e(\boldsymbol\xi)=\det\mathbf J_e(\boldsymbol\xi).
$$

For an element quadrature point $g$ with reference-space integration weight $\omega_g$, the corresponding physical weight is

$$
w_{eg}=\omega_g J_e(\boldsymbol\xi_g)>0,
\qquad V_h=\sum_e\sum_gw_{eg}.
$$

For natural-center sampling, $\boldsymbol\xi_g=\mathbf0$ and $\omega_g=8$, giving $w_{e}=8J_e(\mathbf0)$, a one-point estimate of element volume. For the tensor-product two-point Gauss rule in each natural direction, every $\omega_g=1$. In both cases, the weights are derived solely from the **FEM H8 mapping**; they do not represent a separate interpolation of CSF geometry or constitutive properties.

The quadrature-weighted vector RMS and relative $L^2$ discrepancy are

$$
\operatorname{RMSE}_{\mathbf u,V}
=\left(\frac{\sum_e\sum_g w_{eg}\|\boldsymbol\delta_{eg}\|_2^2}
{\sum_e\sum_gw_{eg}}\right)^{1/2},
\qquad
\varepsilon_{\mathbf u,V}^{\mathrm{rel}}
=100\left(\frac{\sum_e\sum_g w_{eg}\|\boldsymbol\delta_{eg}\|_2^2}
{\sum_e\sum_g w_{eg}\|\mathbf u_{eg}^{\mathrm{FEM}}\|_2^2}\right)^{1/2}\%.
$$

Componentwise weighted measures follow by replacing the vector norms with the corresponding squared component values. These discrete expressions approximate the volume-integrated discrepancy on the FEM mesh; their accuracy depends on the selected quadrature and the finite-element geometry. The natural-center rule and the Gaussian rule therefore represent distinct quadrature approximations. **No volume weights are assigned to nodal samples**, since a set of mesh nodes is not itself a volume-integration rule.

## Spatial localisation and graphical representation

The primary pointwise visual diagnostic is a parity diagram. For each displacement component $\alpha$, it consists of the pairs

$$
\left(u_{i\alpha}^{\mathrm{FEM}},u_{i\alpha}^{\mathrm{CUF}}\right),
\qquad i=1,\ldots,n_s,
$$

with the identity line $u_\alpha^{\mathrm{CUF}}=u_\alpha^{\mathrm{FEM}}$. It displays agreement over the sampled displacement range but does not encode the positions of the samples in the structure. For legibility, the plotted points may be subsampled; the numerical statistics always use the full selected sampling set.

Longitudinal displacement profiles are constructed along **actual chains of connected H8 mesh nodes**. For a selected nodal chain $\ell$, let

$$
\mathcal C_\ell^h
=\left\{\mathbf p_{\ell j}=(x_{\ell j},y_{\ell j},z_{\ell j})\right\}_{j=1}^{n_\ell},
\qquad x_{\ell,j+1}>x_{\ell j}.
$$

At each node, the stored FEM nodal vector and the compiled CUF displacement at the same physical coordinate are plotted against $x_{\ell j}$; $\|\boldsymbol\delta_{\ell j}\|_2$ is plotted separately. The transverse coordinates $y_{\ell j}$ and $z_{\ell j}$ may change along the chain, particularly for a non-prismatic member. These profiles are therefore **mesh-defined longitudinal tracks**, not necessarily straight paths with fixed transverse coordinates or independently constructed material trajectories. Their starting-node identities and full coordinates are retained in the numerical output.

To locate discrepancies along the member without constructing artificial displacement fields, the normalised axial coordinate $\widehat x=(x-x_0)/(x_1-x_0)$ may be partitioned into non-overlapping intervals $I_b$. For the indices $S_b=\{i:\widehat x_i\in I_b\}$, the reported local indicator is

$$
\operatorname{RMSE}_{\mathbf u}^{(b)}
=\left(\frac{1}{|S_b|}\sum_{i\in S_b}\|\boldsymbol\delta_i\|_2^2\right)^{1/2},
\qquad
 e_{\max}^{(b)}=\max_{i\in S_b}\|\boldsymbol\delta_i\|_2,
$$

for nonempty groups only. The abscissa of such a grouped diagnostic labels an **interval**, not the coordinate of a point where a displacement has been evaluated. Analogous error statistics can be grouped by identified CSF/FEM subdomain. No longitudinal-bin mean of $\mathbf u^{\mathrm{FEM}}$ or $\mathbf u^{\mathrm{CUF}}$ is calculated.

## Consistency checks, interpretation and reproducibility

The comparison requires solved displacement checkpoints in the same physical coordinate system and consistent units. The implementation verifies the H8 connectivity and positive Jacobian determinants at the FEM Gauss locations. Where the CUF checkpoint stores sectional-domain geometry, that geometry is checked against cross sections evaluated through the authoritative CSF interface. Region labels and representative interior-point ownership are also checked through the CSF API when the relevant metadata are available. Interface nodes are not assigned artificial unique material owners.

These checks establish the correspondence of the evaluated spatial coordinates and support the consistency of the physical models. They do **not**, on their own, prove equality of the loads, boundary conditions or constitutive states originally used by the two solvers; those inputs must be documented and verified as part of the numerical benchmark. In particular, the comparator neither interprets constitutive laws independently nor recomputes stresses.

For traceability, the numerical post-processing retains, for every sample, its physical coordinates, FEM element or node identity, region label when available, both displacement vectors, the signed componentwise discrepancies, the vector discrepancy and, for interior samples, the physical quadrature weight. Aggregate statistics, maximum-error locations, profile definitions and checkpoint hashes are exported separately. This permits the reported indicators to be recomputed from the paired output data without rerunning either solver.

Finally, the measures above quantify **agreement between two discretised solutions**. They are not an estimate of the error relative to an unknown exact solution. Numerical credibility must therefore be assessed together with independent refinement studies of the FEM3D discretisation and of the CUF approximation. The displacement comparison is intentionally distinct from stress recovery and strong-form equilibrium verification.
