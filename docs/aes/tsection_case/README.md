== DRAFT ==

# Prismatic composite section with localized web degradation

Structural members in composite construction often combine components with different elastic properties. When the material participation of one component varies along the member axis, the resulting sectional stiffness becomes a continuous function of the axial coordinate, even if the cross-sectional geometry remains unchanged.

This case considers a prismatic composite section in which the lower part of the web progressively degrades along the member axis, while the remaining parts of the section retain isotropic elastic behaviour. The geometry of the cross-section is identical at both ends of the member. Therefore, all longitudinal variation in the sectional properties is produced exclusively by the material participation fields assigned to the degraded web region.

The degraded web is described by two independent smooth participation laws: one associated with longitudinal stiffness and one associated with shear stiffness. Since these two fields do not follow the same axial law, the ratio between longitudinal and shear stiffness changes continuously along the member. The section therefore requires a two-modulus representation in which the effective longitudinal modulus \(E(z)\) and shear modulus \(G(z)\) are treated as independent quantities, rather than being linked through a fixed Poisson ratio.

The CSF report for this case documents the continuous evolution of the sectional properties along the member axis. The reported quantities include the effects of the independent participation laws on area, bending stiffness, and polar moment of inertia.

Torsional stiffness is intentionally omitted from this report. Because the section has open geometry, the internal thin-wall torsional approximation is not sufficiently reliable for this case, and CSF excludes the quantity rather than reporting a potentially non-physical estimate.

>When a torsional analysis is required for this type of section, the recommended repository-level workflow is to use the `csf_sp` bridge to `sectionproperties`. The `csf_sp` tool samples the same CSF definition at selected axial stations, generates the corresponding `sectionproperties` model, and allows Saint-Venant torsional quantities to be evaluated through the FEM warping analysis available in `sectionproperties`. For cases with independent longitudinal and shear participation fields, the dedicated torsion-carrier workflow should be used so that torsion is evaluated with the shear/torsional carrier required by the CSF model.
>
>Reference repository document:
>
>- [`csf_sp` User Guide](https://github.com/giovanniboscu/continuous-section-field/blob/main/docs/csf_sp_user_guide.md)

