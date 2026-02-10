# 08_opensees_integration.md

# OpenSees Integration

This document explains **how CSF outputs are consumed by OpenSees**, and—more importantly—**why the chosen integration strategy is mathematically consistent with a continuous stiffness field**.

---

## 1. Role Separation: CSF vs OpenSees

It is essential to separate responsibilities:

### CSF
- Defines a **continuous geometric and stiffness field** along the member axis \( z \)
- Computes section properties **exactly at prescribed locations**
- Controls *where* and *how* properties are sampled
- Outputs **solver-ready station data**

### OpenSees
- Solves the **structural equilibrium problem**
- Integrates section response along elements
- Does **not** know how the section properties were generated

CSF is therefore a **pre-processor with mathematical authority over section definition**.  
OpenSees is a **numerical integrator and solver**.

---

## 2. What CSF Actually Exports

CSF exports a **list of stations** along the member.

Each station contains:
- Section properties:  
  \( A, I_y, I_z, J \)
- Stiffness products (depending on mapping):  
  \( EA, EI_y, EI_z, GJ \)
- Centroid offsets:  
  \( C_x(z), C_y(z) \)

These values are **not averaged**, **not interpolated by the user**, and **not guessed**.  
They are evaluated directly from the continuous ruled-surface geometry and weight laws.

---

## 3. Why Standard `beamIntegration Lobatto` Is Not Enough

In OpenSees, the command:

beamIntegration UserDefined


This integration:
- explicitly specifies **which section tag** is used
- explicitly specifies **where** (local coordinate)
- explicitly specifies **integration weights**

This is the only OpenSees mechanism that allows a one-to-one mapping between:
- CSF stations  
- OpenSees integration points

---

## 5. Station Placement: Gauss–Lobatto Rule

CSF places stations using the **Gauss–Lobatto quadrature rule**.

Key properties:
- Endpoints **are included**
- Optimal accuracy for smooth fields
- Exact sampling at:
  - member start
  - member end

This guarantees:
- boundary conditions applied at **true physical ends**
- no artificial extrapolation at supports or tips

---

## 6. Element Construction Strategy

Because OpenSees cannot consume an arbitrary list of section tags inside a *single* element without ambiguity, the robust strategy is:

### Chain of Elements Between Stations

For stations:
\[
z_0, z_1, z_2, \dots, z_n
\]

Create:
- one OpenSees element between each consecutive pair

For element \( i \to i+1 \):
- local coordinate 0 → station \( i \)
- local coordinate 1 → station \( i+1 \)

Integration definition:

beamIntegration UserDefined <tag> <sec_i> 0.0 0.5 <sec_{i+1}> 1.0 0.5


This ensures:
- stiffness sampled **exactly at CSF stations**
- no invented intermediate section
- symmetric integration weights

---

## 7.CSF Is *Not* Piecewise-Prismatic

### CSF + OpenSees model
- CSF defines a **continuous field**
- sampling locations are **prescribed by quadrature**
- no averaging, no guessing
- OpenSees performs **numerical quadrature of a known field**

The OpenSees elements are therefore **integration carriers**, not modeling approximations.

---

## 8. Centroid Axis and Eccentricity Preservation

Non-prismatic members often have:
- variable centroid position
- eccentric stiffness relative to a reference axis

CSF explicitly tracks:
\[
C_x(z),\; C_y(z)
\]

### OpenSees implementation
- create reference nodes along a straight axis
- create centroid nodes offset by \( C_x, C_y \)
- connect them using:

## rigidLink beam

This produces:
- automatic moment–axial coupling
- correct geometric eccentricity
- no artificial offset forces

> **Note**  
> This requires `constraints Transformation` in OpenSees.

---

	
