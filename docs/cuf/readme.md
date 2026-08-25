# What is the Carrera Unified Formulation?

The Carrera Unified Formulation (CUF) is a general framework for constructing structural theories through a systematic representation of the three-dimensional displacement field. Its starting point is kinematic: before constructing stiffness matrices or introducing a particular numerical discretization, one first chooses how the displacement field is allowed to vary over the cross-section.

For a beam whose longitudinal coordinate is $x$ and whose cross-section is described by $y$ and $z$, the displacement field can be written in the generic CUF form

$$\mathbf{u}(x,y,z)=\sum_{\tau=1}^{M}F_{\tau}(y,z)\,\mathbf{u}_{\tau}(x)$$

where $F_{\tau}(y,z)$ are the functions used to describe the kinematics over the cross-section and $\mathbf{u}_{\tau}(x)$ are the corresponding generalized displacement functions along the beam axis.

This equation contains the central modeling idea of CUF. The functions $F_{\tau}$ define the admissible cross-sectional kinematic space. Choosing a particular expansion therefore means choosing which displacement distributions the model is capable of representing. A low-order expansion describes a restricted set of cross-sectional deformation modes. Increasing the order enlarges that space and allows progressively more complex displacement fields to be represented.

For a polynomial expansion, the functions $F_{\tau}(y,z)$ may be monomials, Legendre polynomials, or another suitable polynomial basis. In a two-dimensional cross-section, a Maclaurin-type expansion may contain terms such as

$$1,\quad y,\quad z,\quad y^2,\quad yz,\quad z^2,\quad \ldots$$

and each term is associated with its own generalized displacement function of $x$. The complete three-dimensional displacement field is therefore obtained by combining all these cross-sectional functions with their corresponding longitudinal coefficients.

For example, a scalar displacement component may be represented schematically as

$$u(x,y,z)=u_1(x)+y\,u_2(x)+z\,u_3(x)+y^2u_4(x)+yz\,u_5(x)+z^2u_6(x)+\cdots$$

The quantities $u_1(x),u_2(x),\ldots$ are not independent displacement fields. They are the longitudinal coefficient functions of one single three-dimensional displacement field $u(x,y,z)$. Increasing the expansion order introduces additional coefficients and therefore enlarges the kinematic space available to represent the physical deformation of the cross-section.

This distinction is important. CUF does not begin from a predefined beam theory and then modify its equations. Instead, the structural theory emerges from the selected kinematic expansion. Classical and higher-order beam models can therefore be interpreted as different choices of the approximation space used for $F_{\tau}(y,z)$.

The longitudinal functions $\mathbf{u}_{\tau}(x)$ belong to the CUF representation itself. They do not intrinsically require a finite-element discretization. A numerical method may subsequently be introduced to approximate them.

If a finite-element approximation is adopted along the beam axis, one may write

$$\mathbf{u}_{\tau}(x)=\sum_{i=1}^{n}N_i(x)\,\mathbf{q}_{\tau i}$$

where $N_i(x)$ are the longitudinal finite-element shape functions and $\mathbf{q}_{\tau i}$ are the corresponding discrete unknown coefficients.

Substituting this approximation into the CUF expansion gives

$$\mathbf{u}(x,y,z)=\sum_{\tau=1}^{M}\sum_{i=1}^{n}F_{\tau}(y,z)\,N_i(x)\,\mathbf{q}_{\tau i}$$

The numerical model therefore still represents one displacement field $\mathbf{u}(x,y,z)$, but that field is now described through a finite collection of coefficients $\mathbf{q}_{\tau i}$. When both the cross-sectional expansion and the longitudinal interpolation are polynomial, the result is a piecewise-polynomial approximation of the three-dimensional displacement field along the beam.

The finite-element discretization is therefore a later numerical step. It approximates the longitudinal functions $\mathbf{u}_{\tau}(x)$, but it does not define the essential idea of CUF. The essential choice has already been made when the cross-sectional kinematic space was selected.

Once the kinematic approximation is defined, the governing equations must be generated for all combinations of cross-sectional and longitudinal functions. This is where the **Fundamental Nucleus** enters.

The Fundamental Nucleus is the reusable algebraic building block from which the element matrices are constructed. Instead of deriving a different matrix formulation for every expansion order or every structural theory, CUF expresses the generic matrix contribution in terms of the indices associated with the chosen approximation functions. The complete matrices are then obtained by expanding and assembling these contributions over all required indices.

The role of the Fundamental Nucleus is therefore different from the role of the kinematic expansion:

- the **kinematic expansion** determines what displacement fields the model can represent;
- the **longitudinal approximation** determines how the generalized displacement functions are represented numerically;
- the **Fundamental Nucleus** provides the common algebraic structure used to construct the governing matrices.

The formulation can therefore be read in the following order:

$$\text{cross-sectional kinematic space}\rightarrow\mathbf{u}(x,y,z)\rightarrow\text{longitudinal approximation}\rightarrow\text{Fundamental Nucleus}\rightarrow\text{matrix assembly}$$

This hierarchy is useful because it separates two different questions. The first is physical and kinematic: **what deformation field is the model able to represent?** The second is algebraic and computational: **how are the equations associated with that field generated efficiently and systematically?**

CUF unifies the second problem, but the first remains the fundamental modeling choice.
