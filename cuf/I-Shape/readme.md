# I-Shape - Prismatic and Tapered Beam Comparison

This example considers an **I-shaped beam** in two configurations:

- a **prismatic beam**, whose cross-section remains unchanged along its length;
- a **tapered beam**, whose cross-section gradually changes from one end to the other.

The aim is to compare the results obtained with the **CSF–CUF model** against an independent **three-dimensional finite-element model (FEM3D)**.

## Starting geometry

The starting cross-section is the prismatic I-section considered in:

> E. Carrera and G. Giunta,  
> “Refined Beam Theories Based on a Unified Formulation”,  
> *International Journal of Applied Mechanics*, 2(1), 117–143, 2010.  
> DOI: [10.1142/S1758825110000500](https://doi.org/10.1142/S1758825110000500)

Only the **prismatic section geometry** is taken from the paper.

The tapered configuration described below is generated separately from this initial geometry.

## Prismatic case

In the first case, the I-shaped cross-section is identical at every position along the beam.

In other words, if the beam is cut at any longitudinal position, the same I-section is obtained.

This case provides the reference configuration.

## Tapered case

The second case starts from exactly the same I-shaped section.

The beam is then made progressively smaller in the vertical direction by reducing the height of the **web**, i.e. the central vertical part connecting the two flanges.

At the beginning of the beam, the clear web height is

$$
a = 100\ \mathrm{mm}
$$

and at the opposite end it becomes

$$
a = 20\ \mathrm{mm}.
$$

The web height is therefore reduced by **80%**.

The flange width and flange thickness are kept unchanged.

The transition between the initial and final sections is continuous along the beam length.

The two cases can therefore be pictured as:

- **prismatic case:** the same I-section along the entire beam;
- **tapered case:** the same initial I-section, with the web height gradually decreasing toward the other end.

## CSF–CUF model

In the CSF–CUF model, the changing cross-section is described directly as a function of the longitudinal position $x$.

This means that the solver can request the actual section geometry at any required position along the beam.

For the prismatic case, the section returned is always the same.

For the tapered case, the returned section gradually changes from the initial I-section to the final reduced I-section.

The two CSF–CUF cases are available here:

[CSF–CUF I-Shape cases](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape)

## Independent FEM3D comparison

The same two beams were also analysed with an independent three-dimensional finite-element model.

The comparison therefore consists of:

- prismatic CSF–CUF vs. prismatic FEM3D;
- tapered CSF–CUF vs. tapered FEM3D.

The displacement evolution along the complete beam is examined at several points located on the perimeter of the I-section.

For each selected point, the corresponding displacement obtained with CSF–CUF is plotted together with the result from the FEM3D model.

This makes it possible to examine:

- how the structural response changes when the beam becomes tapered;
- how closely the CSF–CUF solution follows the independent three-dimensional solution.

The complete set of comparison plots is available here:

[FEM3D - prismatic vs. tapered comparison plots](https://github.com/giovanniboscu/continuous-section-field/tree/main/cuf/I-Shape/fem3d/prism_vs_taper)

## Scope

The first configuration reproduces the prismatic I-shaped geometry used as the starting reference.

The second uses the same initial section but introduces a continuous geometric variation along the beam.

The comparison shows how the same CSF–CUF formulation is applied to both a constant and a continuously variable cross-section.

Details concerning the numerical settings, model construction and full reproducibility of the calculations are kept in separate documentation.
