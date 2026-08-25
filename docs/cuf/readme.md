# What is the Carrera Unified Formulation?

The Carrera Unified Formulation (CUF) is a general framework for constructing structural theories through a systematic representation of the three-dimensional displacement field. For a beam whose longitudinal coordinate is $x$ and whose cross-section is described by $y$ and $z$, the displacement field can be written in the generic form

$$
\mathbf{u}(x,y,z)
=
\sum_{\tau=1}^{M}
F_{\tau}(y,z)\,
\mathbf{u}_{\tau}(x),
$$

where $F_{\tau}(y,z)$ are the functions chosen to describe the kinematics over the cross-section and $\mathbf{u}_{\tau}(x)$ are the corresponding generalized displacement functions along the beam axis. The essential modeling choice is therefore the definition of the cross-sectional approximation space. A low-order expansion provides a restricted kinematic description, while increasing or changing the expansion enriches the set of displacement fields that the structural model is able to represent. In this sense, the choice of expansion is not merely an algebraic or implementation detail: it determines the kinematic content of the model.

For polynomial CUF expansions, the functions $F_{\tau}(y,z)$ may consist, for example, of monomials or other polynomial bases. The three-dimensional displacement field is then represented through a finite set of cross-sectional modes, each multiplied by a function of the longitudinal coordinate. The unknowns are therefore not initially a collection of unrelated nodal quantities, but the functions $\mathbf{u}_{\tau}(x)$ that weight the selected cross-sectional basis. Taken together, these functions define a single approximation of the physical displacement field $\mathbf{u}(x,y,z)$. Increasing the expansion order increases the number of coefficients and enlarges the admissible kinematic space, allowing more complex displacement distributions over the cross-section to be represented.

The longitudinal dependence does not intrinsically have to be introduced by the finite element method. The functions $\mathbf{u}_{\tau}(x)$ are part of the CUF representation and may subsequently be approximated by a numerical procedure. If a finite element discretization is adopted along the beam axis, one may write

$$
\mathbf{u}_{\tau}(x)
=
\sum_{i=1}^{n}
N_i(x)\,
\mathbf{q}_{\tau i},
$$

so that the complete displacement field becomes

$$
\mathbf{u}(x,y,z)
=
\sum_{\tau=1}^{M}
\sum_{i=1}^{n}
F_{\tau}(y,z)\,
N_i(x)\,
\mathbf{q}_{\tau i}.
$$

In this form, the coefficients $\mathbf{q}_{\tau i}$ are the discrete unknowns of the numerical model. When both the cross-sectional expansion and the longitudinal interpolation are polynomial, the result is a polynomial representation of the three-dimensional displacement field within each longitudinal finite element. The finite element discretization is therefore a subsequent numerical approximation of the generalized functions $\mathbf{u}_{\tau}(x)$, not the defining idea of CUF itself.

Once the kinematic approximation has been selected, the governing equations must be generated for all combinations of cross-sectional functions and longitudinal interpolation functions. This is where the **Fundamental Nucleus** enters. Its role is algebraic: it provides a reusable expression for the elementary matrix contributions associated with generic indices $\tau$, $s$, $i$, and $j$. The complete structural matrices are obtained by expanding and assembling this nucleus over the selected approximation spaces. The Fundamental Nucleus is therefore what makes the formulation *unified* at the matrix-construction level, while the physical content of a particular CUF model is established first by the chosen kinematic space.

A useful way to read the formulation is therefore

$$
\boxed{
\text{cross-sectional kinematic space}
\;\longrightarrow\;
\mathbf{u}(x,y,z)
\;\longrightarrow\;
\text{longitudinal approximation}
\;\longrightarrow\;
\text{Fundamental Nucleus and matrix assembly}
}
$$

This ordering separates two ideas that are often presented together: **what displacement field the model is able to represent**, and **how the equations associated with that field are assembled efficiently**. CUF unifies the second problem without removing the importance of the first.
