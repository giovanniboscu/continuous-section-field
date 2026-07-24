# High-Level Architecture

## CSF is a continuous section-field model

A recurring difficulty in the analysis of non-prismatic and materially heterogeneous structural members is the fragmented nature of the conventional workflow. When the cross-sectional configuration varies along the longitudinal coordinate (z), the member is commonly sampled at a finite number of stations. Each station is then represented and analysed as an independent two-dimensional section, with separate geometry construction, material assignment, sectional evaluation, and subsequent interpolation of the calculated properties.

This station-based approach is appropriate for many applications. However, it becomes increasingly cumbersome when geometry, topology, or mechanical participation vary continuously along the member axis. A change in the underlying model may require rebuilding several independent section descriptions and repeating the associated analysis chain.

Continuous Section Field (CSF) addresses this modelling problem by introducing a unified representation defined along (z). Rather than treating the member as a collection of unrelated section models, CSF defines corresponding polygonal regions and participation fields whose local state can be evaluated at any admissible longitudinal position.

The two reference configurations, `S0` and `S1`, provide the boundary data for this construction. Corresponding vertices and polygons define the geometric variation, while independent axial/bending and shear/torsion participation fields define how each region contributes mechanically along the member axis.

At a requested position (z), CSF resolves the local geometry, topology, and participation state. This resolved state can be used in several ways:

* evaluated directly through the sectional quantities supported by CSF;
* exported as geometric, material, or property data;
* passed to beam-based applications or structural solvers;
* converted for use by specialized sectional-analysis backends.

CSF is therefore not dependent on a specific sectional solver. It provides the continuous model layer from which native calculations, exports, and external analyses can be performed.

---

## The objective is not more complicated mathematics

The objective is to reduce modelling and workflow complexity for members involving:

* tapered or otherwise varying geometry;
* nested polygonal regions;
* hollow or perforated configurations;
* graded or degraded material participation;
* composite regions;
* independently varying axial/bending and shear/torsion participation;
* sectional quantities that must be evaluated at arbitrary positions along (z).

---

## Conventional station-based workflow

```text
structural description
        ↓
select analysis stations
        ↓
build an independent section at each station
        ↓
assign materials and participation
        ↓
mesh or evaluate each section
        ↓
interpolate the resulting properties
```

This remains a valid workflow, but its cost grows when the number of stations increases or when the underlying geometric and mechanical definitions are repeatedly modified.

---

## CSF workflow

```text
one continuous model definition
              ↓
resolve the local state at any z
              ↓
evaluate, export, or pass it to an external tool
```

CSF replaces:

```text
many independently maintained section models
```

with:

```text
one continuously queryable SectionField
```

The model may still be sampled at discrete stations when required by an external solver. The sampling, however, is performed from a single continuous definition rather than from separately constructed section models.

---

# High-Level Architecture

```text
======================================================================
                    CSF — HIGH-LEVEL ARCHITECTURE
======================================================================


                         ┌──────────────────────┐
                         │      YAML / API      │
                         │  declarative input   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                     ┌──────────────────────────┐
                     │        CSF CORE          │
                     └──────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼

┌─────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│ Geometry Kernel │     │ Participation      │     │ Topology Engine  │
│                 │     │ Fields             │     │                  │
├─────────────────┤     ├────────────────────┤     ├──────────────────┤
│ vertices        │     │ weight(z)          │     │ containment      │
│ polygons        │     │ shear_weight(z)    │     │ nesting          │
│ correspondence  │     │ custom laws        │     │ hierarchy        │
│ interpolation   │     │ field evaluation   │     │ region meaning   │
└─────────┬───────┘     └──────────┬─────────┘     └────────┬─────────┘
          │                        │                        │
          └──────────────┬─────────┴────────────────────────┘
                         │
                         ▼

                 ┌────────────────────────────┐
                 │   Continuous SectionField  │
                 │                            │
                 │ geometry(z)                │
                 │ topology(z)                │
                 │ participation(z)           │
                 └─────────────┬──────────────┘
                               │
                               ▼

                    ┌────────────────────┐
                    │ Resolved Local     │
                    │ Section State(z)   │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼

┌───────────────────┐ ┌───────────────────┐ ┌────────────────────────┐
│ Native CSF        │ │ Data Export and   │ │ External Applications  │
│ Evaluation        │ │ Interoperability  │ │ and Backends           │
├───────────────────┤ ├───────────────────┤ ├────────────────────────┤
│ area              │ │ CSV / YAML        │ │ sectionproperties      │
│ centroid          │ │ geometry export   │ │ OpenSees               │
│ inertial terms    │ │ property fields   │ │ SAP2000                │
│ weighted fields   │ │ solver adapters   │ │ custom applications    │
│ analytical terms  │ │ sampled stations  │ │ other numerical tools  │
└─────────┬─────────┘ └─────────┬─────────┘ └────────────┬───────────┘
          │                     │                        │
          └──────────────┬──────┴────────────────────────┘
                         │
                         ▼

                 ┌────────────────────────┐
                 │ Longitudinal Outputs   │
                 ├────────────────────────┤
                 │ native CSF fields      │
                 │ exported section data  │
                 │ solver-ready inputs    │
                 │ backend-specific       │
                 │ sectional results      │
                 └────────────────────────┘
```

---

# Core Responsibility Table

```text
======================================================================
CORE RESPONSIBILITY TABLE
======================================================================


+---------------------------+---------------------------------------------+
| LAYER                     | RESPONSIBILITY                              |
+---------------------------+---------------------------------------------+
| YAML / API                | Declarative model definition                |
| Geometry Kernel           | Polygonal geometry and variation along z    |
| Topology Engine           | Containment, nesting, and region hierarchy  |
| Participation Fields      | Axial/bending and shear/torsion fields      |
| SectionField              | Unified continuous representation          |
| Section State(z)          | Resolved local state at a requested z       |
| Native CSF Evaluation     | Quantities supported directly by CSF        |
| Export / Interoperability | Data exchange and solver preparation        |
| External Backends         | Specialized numerical section analysis     |
| Longitudinal Outputs      | Native, exported, or backend-derived fields |
+---------------------------+---------------------------------------------+
```

---

# Responsibility Separation

## CSF

CSF owns the continuous model definition:

* reference configurations;
* vertex and polygon correspondence;
* geometric variation along (z);
* containment and nesting relationships;
* axial/bending participation fields;
* shear/torsion participation fields;
* local-state resolution at arbitrary positions;
* native sectional quantities supported by its formulation;
* export of geometry, participation, and derived property fields.

CSF is the continuous modelling and evaluation layer.

It is not a general three-dimensional structural solver and does not replace specialized FEM, warping, or beam-analysis tools.

---

## External applications and solvers

External applications may consume CSF data in different forms:

* resolved polygonal geometry;
* material or participation assignments;
* section-property fields;
* sampled beam properties;
* solver-specific input files;
* local states prepared for further numerical analysis.

These tools remain responsible for the structural or sectional calculations implemented within their own formulations.

---

## `csf_sp`

`csf_sp` is a dedicated interoperability layer between CSF and `sectionproperties`.

It is responsible for:

* resolving CSF states at requested positions;
* converting CSF polygonal regions into `sectionproperties` geometry;
* mapping participation values to solver-compatible material definitions;
* preparing the axial/bending representation;
* preparing the corresponding shear/torsion-carrier representation;
* invoking the relevant `sectionproperties` calculations;
* returning backend-derived results to the surrounding application.

`csf_sp` is one available bridge. It is not required by the CSF core model.

---

## `sectionproperties`

`sectionproperties` is an external sectional-analysis backend.

Within the `csf_sp` integration, it is responsible for operations such as:

* finite-element meshing of the local section;
* warping analysis;
* Saint-Venant torsion analysis through its FEM formulation;
* shear-centre calculation;
* composite sectional analysis;
* other properties supported by its numerical model.

These quantities complement the native CSF representation but do not define it.

---

# Independent Participation Fields

For each corresponding polygon pair, CSF distinguishes between:

```text
axial/bending participation
```

and:

```text
shear/torsion participation
```

The corresponding fields may be related, but they do not have to be identical:

```text
weight_i(z) ≠ shear_weight_i(z)
```

This separation allows the same continuously varying geometric region to contribute differently to the two classes of sectional behaviour.

When a backend requires a single material definition for a given analysis, an interoperability layer may construct separate backend representations from the same resolved CSF state. For example:

```text
resolved CSF state
        │
        ├── axial/bending-compatible backend representation
        │
        └── shear/torsion-compatible backend representation
```

This is a conversion strategy used by the integration layer. The two participation fields remain native components of the CSF model.

---

# Result Ownership

The source of a result should remain explicit.

## Native CSF results

Depending on the active CSF formulation and polygon classification, these may include fields such as:

```text
A(z)
Cx(z)
Cy(z)
Ix(z)
Iy(z)
Ixy(z)
weighted axial/bending quantities
weighted shear/torsion quantities
analytical cell or wall contributions
```

## Exported or solver-ready data

CSF may also produce:

```text
resolved polygons at z
participation values at z
sampled property tables
CSV or YAML property fields
beam-solver input data
```

## Backend-derived results

Specialized backends may provide additional quantities such as:

```text
FEM torsional constants
warping properties
shear-centre coordinates
mesh-dependent section results
backend-specific composite properties
```

These results may be evaluated at multiple positions and assembled into longitudinal fields, but their numerical formulation belongs to the selected backend.

---

# Final Positioning

```text
CSF defines and evaluates a continuous polygon-based representation of
geometry, topology, and mechanical participation along the member axis.

At any requested position z, CSF resolves the corresponding local state
and computes the sectional quantities supported by its native formulation.

The same local state can also be exported to structural applications or
converted for specialized sectional-analysis backends.

csf_sp is an optional adapter between CSF and sectionproperties.

sectionproperties performs the local FEM section analyses supported by
that backend.

Neither csf_sp nor sectionproperties is required to define or query the
continuous CSF model.
```
