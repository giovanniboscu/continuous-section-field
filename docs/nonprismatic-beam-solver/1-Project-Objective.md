# 1. Project Objective

This project aims to develop a numerical solver based on the non-prismatic beam model introduced by **Giuseppe Balduzzi** and co-authors, with explicit recognition of the originality and importance of their formulation for tapered and non-prismatic members.

The immediate objective is **not** to replace or reinterpret the original theory, but to make it operational within a practical computational workflow. In particular, the project focuses on:

- implementing a solver consistent with the **Balduzzi beam formulation** for planar non-prismatic members;
- defining a clear separation between:
  - the **model input data** required by the formulation, and
  - the **numerical solver** that uses those data;
- adopting a fully **numerical perspective**, avoiding any requirement for closed-form geometric or constitutive expressions;
- preparing the ground for integration with **continuous geometric-sectional descriptions**, so that realistic non-prismatic members can be analyzed without reducing the problem to a few manually segmented idealized parts.

A second, more advanced objective is to explore the **generalization of the Balduzzi framework to non-rectangular and more general cross-sections**. This is recognized from the outset as a substantially harder step, likely deserving independent treatment. It is therefore considered a future development, separate from the first implementation of the original model.

The broader motivation is practical: many advanced beam formulations for non-prismatic members are mathematically sound, but their use in realistic applications is often limited by the absence of a programmable geometric pipeline capable of supplying the required data in a consistent form. This project is intended to address that gap incrementally.

Accordingly, the project is structured around three progressive goals:

1. **implement the original Balduzzi-based solver in numerical form;**
2. **formalize the reduced model data required to drive that solver;**
3. **investigate how the same framework may be extended to richer sectional geometries.**

This work is developed as an evolving technical effort and documented progressively in Markdown form on GitHub.

# Main Reference

Balduzzi, G., Aminbaghai, M., Sacco, E., Füssl, J., Eberhardsteiner, J., & Auricchio, F. (2016). *Non-prismatic beams: A simple and effective Timoshenko-like model*. *International Journal of Solids and Structures*, 90, 236–250. https://doi.org/10.1016/j.ijsolstr.2016.02.017




