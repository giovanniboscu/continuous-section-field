# Degraded Prestressed Concrete Pole

## Overview
This project concerns the structural modelling of a hollow tapered prestressed concrete pole affected by degradation that varies along its height.

The pole changes progressively from the base to the top. Its external and internal dimensions vary with elevation, as do the position of the prestressing bars and the mechanical condition of the concrete and steel components.

At any elevation along the pole, the model can generate the corresponding cross-section together with the mechanical properties assigned to each of its components. This makes it possible to describe both gradual variations and localized degradation within a single longitudinal model.

The aim of the project is to parameterize the structural behaviour of the pole. Geometry, material properties, prestress, degradation and loading are introduced as model parameters and can be varied to analyse different structural conditions.

The repository contains the model definitions, the analysis scripts and the resulting numerical outputs.


---

## 1. Physical model

The structural member is a hollow tapered prestressed concrete pole.

Its cross-section is composed of:

- concentric concrete regions;
- an internal hollow core;
- concrete cover layers;
- a region containing the prestressing reinforcement;
- individual prestressing bars distributed around the circumference.

The pole is tapered, so its external and internal dimensions change along the longitudinal axis. The position of the prestressing bars changes consistently with the section geometry.

The material condition may also vary along the pole. Each concrete region and each prestressing bar can therefore be assigned its own longitudinal degradation profile.

---

## 2. Longitudinal coordinate

The position along the pole is identified by the coordinate:

\[
z
\]

where:

- `z = 0` identifies the base;
- increasing `z` moves towards the top;
- every admissible value of `z` identifies one cross-section.

The section at a given elevation is written as:

\[
S(z)
\]

This notation means simply:

> the cross-section of the pole at elevation `z`.

For example:

```text
S(0.0)   -> section at the base
S(7.5)   -> section at an intermediate elevation
S(15.0)  -> section at the top
```

The model can generate a section at any required elevation. The analysis is therefore based on the longitudinal definition of the member rather than on a fixed list of manually prepared sections.

---

## 3. Section geometry

Each cross-section is assembled from named polygons.

A polygon represents one physical component of the section, such as:

- a concrete layer;
- the concrete cover;
- the bar-hosting region;
- one prestressing bar.

At every elevation, the model determines the coordinates of all polygons and reconstructs the complete section.

The geometry of each component may vary with `z`. Typical varying quantities are:

- external radius;
- internal radius;
- layer thickness;
- bar radius from the section centre;
- polygon vertex coordinates.

The geometric variation is defined at model level and is evaluated automatically at the requested elevation.

---

## 4. Material representation

The polygons also carry the mechanical properties used in the sectional analysis.

Two independent stiffness weights are assigned to each component:

- `weight` for axial force and bending;
- `shear_weight` for shear and torsion.

The first weight is associated with the elastic modulus \(E\). The second is associated with the shear modulus \(G\).

For a component \(i\), the initial normalized properties can be expressed as:

\[
w_{0,i} = \frac{E_i}{E_{\mathrm{ref}}}
\]

\[
w_{s0,i} = \frac{G_i}{G_{\mathrm{ref}}}
\]

where \(E_{\mathrm{ref}}\) and \(G_{\mathrm{ref}}\) are the reference moduli used by the model.

This separation allows the axial and bending behaviour to be varied independently from the shear and torsional behaviour.

---

## 5. Degradation along the pole

Degradation is represented as a change in the residual mechanical properties of each component along `z`.

A residual factor equal to `1.0` represents the initial property. A lower value represents a reduced property.

For axial force and bending:

\[
w_i(z) = w_{0,i}\,T_i(z)
\]

For shear and torsion:

\[
w_{s,i}(z) = w_{s0,i}\,T_{s,i}(z)
\]

where:

- \(w_{0,i}\) is the initial axial and bending weight;
- \(w_{s0,i}\) is the initial shear and torsional weight;
- \(T_i(z)\) is the residual axial and bending factor;
- \(T_{s,i}(z)\) is the residual shear and torsional factor.

Each concrete layer and each prestressing bar can have its own pair of longitudinal laws.

This makes it possible to represent, for example:

- uniform degradation;
- degradation limited to a specific height range;
- different degradation levels in adjacent components;
- isolated degradation of individual prestressing bars;
- separate reductions of \(E\)-related and \(G\)-related behaviour.

---

## 6. Continuous Section Field representation

The project uses the Continuous Section Field approach.

The central object is the section-generating field:

\[
S(z)
\]

Given an elevation `z`, the model generates:

- the complete section geometry;
- the polygons present at that elevation;
- the material weights assigned to each polygon;
- the degradation level of each component;
- the data required for sectional and structural analysis.

The continuous field is the structural representation of the member. Sampled sections, sectional properties and solver inputs are derived from it at the elevations required by the analysis.

---

## 7. YAML model

The YAML files provide the input representation of the pole.

They contain the definitions required to construct the field, including:

- longitudinal stations;
- polygon geometry;
- interpolation rules;
- material weights;
- degradation laws;
- lookup data;
- analysis settings.

The YAML syntax is introduced after the physical model because each key corresponds to a specific geometric or mechanical concept.

A polygon typically refers to two independent laws:

```yaml
weight_law: weight_law_component_name
shear_weight_law: shear_weight_law_component_name
```

The corresponding laws define the longitudinal variation of the axial/bending and shear/torsional properties.

Conceptually:

```yaml
weight_law_component_name:
  type: lookup
  values:
    - [z_0, axial_bending_factor_0]
    - [z_1, axial_bending_factor_1]

shear_weight_law_component_name:
  type: lookup
  values:
    - [z_0, shear_torsion_factor_0]
    - [z_1, shear_torsion_factor_1]
```

The exact schema used by the project is contained in the YAML files included in the repository.

---

## 8. Structural analysis

The generated sections are used in an elastic structural model of the pole.

At the required integration points, the analysis obtains the section directly from the CSF model and evaluates its current properties.

The structural model may include:

- residual prestress;
- axial force;
- lateral loading;
- bending;
- shear;
- torsion;
- degradation varying along the member.

The analysis therefore uses the actual section and material state associated with each elevation.

---

## 9. Sectional results

The project evaluates the sectional response at selected elevations along the pole.

The main quantities include:

- area;
- centroid coordinates;
- second moments of area;
- product of inertia;
- axial stiffness;
- bending stiffness;
- shear-related properties;
- torsional properties;
- normal stresses;
- shear stresses.

Normal stresses are evaluated from the general Navier stress field using:

\[
N,\quad M_x,\quad M_y
\]

Shear stresses are evaluated using the Jourawski-based section procedure for:

\[
T_x,\quad T_y
\]

The results retain the signed stress values and the coordinates of the governing points.

---

## 10. Parametric use

The model is intended to support parametric studies.

A study can vary:

- pole geometry;
- concrete-layer dimensions;
- prestressing-bar position;
- elastic properties;
- residual prestress;
- degradation intensity;
- degradation location;
- degradation extent;
- external loads;
- analysis discretization.

The structural response can then be compared across different scenarios while preserving the same model architecture.

This is particularly useful when analysing a population of poles whose geometry and degradation state differ from one member to another.

---

## 11. Project workflow

The project follows this sequence:

1. Define the physical geometry of the pole.
2. Define the polygons representing concrete and prestressing steel.
3. Define the longitudinal geometric variation.
4. Assign the initial axial/bending and shear/torsional weights.
5. Define the degradation laws for each component.
6. Generate \(S(z)\) at the elevations required by the analysis.
7. Compute the sectional properties.
8. Build the elastic structural model.
9. Apply prestress and external loads.
10. Evaluate global response and sectional stresses.
11. Export reports, tables and plots.

---

## 12. Repository contents

The repository includes:

- YAML files describing the pole and its degradation laws;
- Python scripts used to generate and analyse the sections;
- structural-analysis scripts;
- sectional verification utilities;
- numerical reports;
- CSV result files;
- plots and comparison outputs.

The YAML files and numerical results should be read together with this document: the README explains the model concepts, while the repository files provide their direct implementation.

---

## 13. Scope

The project focuses on the elastic structural response of a geometrically and mechanically variable prestressed concrete pole.

Its main objective is to provide a reproducible connection between:

- the physical pole;
- its longitudinally varying section;
- the component-level degradation laws;
- the sectional properties;
- the structural response;
- the resulting stress fields.

The model is designed so that every reported structural quantity can be traced back to the geometry and mechanical condition of the section at the corresponding elevation.
