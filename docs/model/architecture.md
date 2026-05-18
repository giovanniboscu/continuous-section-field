# High-Level Architecture

## CSF is a continuous section-field model.

A recurring difficulty in the analysis of non-prismatic and materially heterogeneous structural members is the fragmented nature of the conventional workflow. When the cross-section varies along the longitudinal coordinate, the geometry is typically sampled at a finite number of stations. Each station is then treated as an independent two-dimensional section, requiring separate geometry extraction, material assignment, meshing, sectional analysis, and subsequent interpolation of the resulting properties.

This station-based workflow is effective for isolated analyses, but it becomes inefficient when geometry, topology, or material participation vary continuously along the member axis. In such cases, any modification of the underlying model may require rebuilding several disconnected section models and repeating the downstream analysis chain.

The Continuous Section Field (CSF) model addresses this issue by introducing a continuous intermediate representation of the member cross-section. Instead of defining a sequence of independent sections, CSF defines a single SectionField in which geometry, topology, material participation, and carrier fields are expressed as functions of the longitudinal coordinate z.

The purpose of CSF is not to replace sectional solvers or finite element backends. Rather, CSF acts as a continuous model layer between the structural description and the numerical evaluation tools. The model can be sampled at arbitrary stations, and each resolved section can then be passed to analytical routines or external sectional analysis backends such as sectionproperties.

In this sense, CSF shifts the workflow from a collection of disconnected section models to a unified continuous section description. The following diagram summarizes this positioning and illustrates the role of CSF as an intermediate layer between declarative input, local section resolution, backend analysis, and continuous beam-ready sectional properties.

---

## The goal is not more complicated mathematics.

The goal is reducing workflow complexity for:

* tapered sections
* nested geometries
* perforated sections
* graded materials
* composite regions
* continuously varying properties

---

## Traditional workflow problem

```text
CAD
 -> mesh rebuild
 -> material remap
 -> section extraction
 -> interpolation outside solver
 -> repeat for every station
```

Complexity explodes when geometry and materials vary continuously.

---

## CSF approach

```text
one continuous model
        ↓
sample anywhere
        ↓
continuous results
```

CSF replaces:

```text
many disconnected section models
```

with:

```text
one continuous SectionField
```

---

## High-Level Architecture

```text
======================================================================
                    CSF - HIGH LEVEL ARCHITECTURE
======================================================================


                         ┌──────────────────────┐
                         │      YAML / API      │
                         │  declarative model   │
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
│                 │     │ / Carrier Fields   │     │                  │
├─────────────────┤     ├────────────────────┤     ├──────────────────┤
│ polygons        │     │ weight(z)          │     │ nesting          │
│ interpolation   │     │ shear_weight(z)    │     │ containment      │
│ geometry laws   │     │ material fields    │     │ hierarchy        │
│ sampling        │     │ carrier evaluation     │     │ boolean meaning  │
└─────────┬───────┘     └──────────┬─────────┘     └────────┬─────────┘
          │                        │                        │
          └──────────────┬─────────┴────────────────────────┘
                         │                         
                         ▼                         

                 ┌────────────────────────────┐
                 │   Continuous SectionField  │
                 │                            │
                 │       Section(z)           │
                 └─────────────┬──────────────┘
                               │
                               ▼

                    ┌────────────────────┐
                    │  Resolved Section  │
                    │     State(z)       │
                    └─────────┬──────────┘
                              │
                              ▼

                    ┌────────────────────┐
                    │    Analysis API    │
                    └─────────┬──────────┘
                              │
      ┌───────────────────────┼────────────────────────┐
      │                       │                        │
      ▼                       ▼                        ▼

┌────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│ Analytical     │  │ sectionproperties│  │ Future FEM backend │
│ backend        │  │ backend          │  │                    │
├────────────────┤  ├──────────────────┤  ├────────────────────┤
│ closed form    │  │ FEM warping      │  │ Abaqus             │
│ thin wall      │  │ composite props  │  │ Calculix           │
│ fast torsion   │  │ mesh solver      │  │ FEniCS             │
└────────┬───────┘  └─────────┬────────┘  └──────────┬─────────┘
         │                    │                      │
         └────────────┬───────┴──────────────────────┘
                      │
                      ▼

               ┌──────────────────────┐
               │ Continuous Results   │
               ├──────────────────────┤
               │ A(z)                 │
               │ EIx(z)               │
               │ EIy(z)               │
               │ GJ(z)                │
               │ shear center(z)      │
               │ warping(z)           │
               │ mass(z)              │
               └──────────────────────┘
```

---

# Core Responsibility Table

```text
======================================================================
CORE RESPONSIBILITY TABLE
======================================================================


+---------------------------+------------------------------------------+
| LAYER                     | RESPONSIBILITY                           |
+---------------------------+------------------------------------------+
| YAML/API                  | Declarative model definition             |
| Geometry Kernel           | Pure geometry handling                   |
| Topology Engine           | Nesting and containment                  |
| Participation Fields      | Continuous material participation        |
| Carrier Fields            | Axial/bending/shear/torsion carriers     |
| SectionField              | Continuous interpolation along z         |
| SectionState(z)           | Resolved local section                   |
| Analysis API              | Unified analysis interface               |
| Analytical Backend        | Fast closed-form computations            |
| SP Backend                | FEM local section analysis               |
| Future FEM Backend        | External solver integration              |
| Continuous Results        | Beam-ready continuous property fields    |
+---------------------------+------------------------------------------+
```

---

# Responsibility Separation

## CSF

Owns:

* geometry
* interpolation
* topology
* material participation
* carrier fields
* continuous section definition

CSF is the continuous model layer.

---

## csf_sp

Owns:

* CSF → solver conversion
* material mapping
* station sampling
* torsion-carrier bridge
* interoperability

csf_sp is the bridge layer.

---

## sectionproperties

Owns:

* FEM meshing
* warping FEM
* torsion FEM
* shear centre
* composite section analysis

sectionproperties is the numerical backend.

---

# Torsion Carrier Concept

CSF separates:

```text
axial/bending carrier
≠
shear/torsion carrier
```

This allows:

```text
axial/bending FEM run
+
independent shear/torsion-carrier run
```

without changing geometry or topology.

---

# Final positioning

```text
CSF defines the continuous section field.
csf_sp maps each sampled section to the solver.
sectionproperties performs the local FEM section analysis.
```
