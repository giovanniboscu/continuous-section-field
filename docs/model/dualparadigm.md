# DRAFT

# The dual-path paradigm of CSF

A defining feature of the Continuous Section Field approach is its inherent dual-path nature. The same cross-sectional representation, described by the continuous field $\mathcal{S}(z)$, simultaneously feeds two independent mechanical formulations that share no common governing equations or discretization schemes.

- **The sectional (CSF-based) path** applies the operatorial Jourawski-type formulation directly to the sectional field, yielding a computationally efficient beam model that naturally generalises classical shear stress formulas to non-prismatic, heterogeneous, or degraded members.
- **The three-dimensional (reference) path** constructs the exact three-dimensional solid domain $\mathcal{B}$ from the evolution of $\mathcal{S}(z)$ along the member axis, and then solves the full 3D continuum problem using standard finite elements. No assumptions from beam theory are introduced.

Because both paths originate from the identical geometric and material definition, their results can be compared pointwise at any physical location. The 3D solution therefore acts as an independent, high-fidelity reference for assessing the accuracy of the CSF sectional model, while the sectional model provides an engineering tool that retains the full descriptive power of the original representation.

This dual-path architecture is more than a validation strategy: it establishes a unified framework in which the abstract mathematical description of the structural member, its practical engineering model, and its rigorous three-dimensional verification coexist without sacrificing traceability or physical consistency. The paradigm can be summarised by the following principle:

> *Same structural representation — different mechanical formulations — independent numerical discretisations.*

By embedding both the simplified model and its reference counterpart into a single formal language, CSF bridges the gap between advanced beam theory and practical computational analysis, opening the way to systematically validated, reuse-oriented structural models.
