# High-Level Architecture

## Core idea

CSF is a continuous section-field model.

The goal is not more complicated mathematics.

The goal is reducing workflow complexity for:

* tapered sections
* nested geometries
* perforated sections
* graded materials
* composite regions
* continuously varying properties

---

# Traditional workflow problem

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

# CSF approach

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

# High-Level Architecture

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
