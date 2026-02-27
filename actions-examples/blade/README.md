# NREL 5MW Blade — References Used (CSF Example)

This folder contains a **CSF (Continuous Section Field)** example that builds a *two-station* (`S0`, `S1`) blade geometry YAML from external reference data.

The references below document the **NREL 5MW reference turbine blade** (spanwise stations, chord, twist, and airfoil IDs) and the **airfoil coordinate sources** used to build 2D section polylines.

---

## 1) Primary blade definition references (NREL 5MW)

### 1.1 NREL 5MW reference turbine (baseline model specification)
- **Jonkman et al. (NREL)** — *Definition of a 5-MW Reference Wind Turbine for Offshore System Development* (2009).  
  PDF: https://docs.nrel.gov/docs/fy09osti/38060.pdf  
  OSTI record: https://www.osti.gov/biblio/947422

This report defines the overall NREL 5MW baseline turbine and includes the blade aerodynamic/structural specifications used widely in OpenFAST-based baseline models.

### 1.2 Blade structural/aerodynamic reference model (61.5 m blade)
- **Resor (Sandia National Laboratories)** — *Definition of a 5MW/61.5m Wind Turbine Blade Reference Model* (SAND2013-2569, 2013).  
  PDF (OSTI): https://www.osti.gov/servlets/purl/1095962  
  Publisher page (Sandia): https://www.sandia.gov/research/publications/details/definition-of-a-5mw-61-5m-wind-turbine-blade-reference-model-2013-04-01/

This document contains the spanwise table (commonly cited as **Table 2**) with:
- radial node locations (`RNodes`)
- chord distribution (`Chord`)
- aerodynamic twist (`AeroTwst`)
- airfoil identifiers (e.g., Cylinder, DU series, NACA64)

---

## 2) OpenFAST baseline model context (optional but practical)

The OpenFAST baseline model organizes the same blade schedule in **AeroDyn** and **BeamDyn** input files.
A discussion that lists the default airfoils used by the baseline model is here:

- NREL forum thread (OpenFAST) — *Replacing airfoil in 5MW_Baseline* (lists the default airfoils).  
  https://forums.nrel.gov/t/replacing-airfoil-in-5mw-baseline/4831

(When you need exact file names and formatting for AeroDyn/BeamDyn inputs, consult the OpenFAST repositories and the relevant model directories.)

---

## 3) Airfoil coordinate sources (2D polylines)

### 3.1 UIUC / Selig airfoil coordinate database
- UIUC Applied Aerodynamics Group — *UIUC Airfoil Data Site: Coordinate Database*  
  https://m-selig.ae.illinois.edu/ads/coord_database.html

This is the standard public source for many airfoil coordinate sets used in wind turbine baseline models and tutorials.

### 3.2 NACA 64(3)-618 (used as the tip-family airfoil in many NREL 5MW schedules)
A convenient index page that points to the underlying Selig-format `.dat` file:
- AirfoilTools entry (points to UIUC source):  
  https://airfoiltools.com/airfoil/details?airfoil=naca643618-il

---

## 4) Files produced in this example folder

### 4.1 `Cylinder1_coords.txt`
- A *procedurally generated* **perfect circle** in Selig coordinate order (x/c, y/c), used as a clean stand-in for a cylindrical inboard/root section.
- **Not** extracted from OpenFAST; it is intentionally idealized.

### 4.2 `NACA64_A17_coords.txt`
- Built from the **NACA 64(3)-618** coordinate set (Selig format) and then **upsampled** to high resolution using:
  - cosine spacing in x
  - monotone cubic interpolation (shape-preserving)
- This is a **geometry-only** coordinate set (no polars).

---

## 5) Modeling notes (what is and is not represented)

- These coordinate sets provide **2D polylines** only.
- They do **not** include 3D effects such as:
  - prebend / sweep (x(r), y(r), z(r) centerline)
  - thickness distribution of composite laminates
  - structural spar caps / webs geometry (unless you model them explicitly as additional polygons in CSF)
- The two-station CSF YAML approach is a **minimal educational case**; for fidelity you typically use more stations along span.

---

## 6) Recommended citation list (copy/paste)

- Jonkman, J., Butterfield, S., Musial, W., Scott, G. (2009). *Definition of a 5-MW Reference Wind Turbine for Offshore System Development*. NREL/TP-500-38060. https://docs.nrel.gov/docs/fy09osti/38060.pdf
- Resor, B. R. (2013). *Definition of a 5MW/61.5m Wind Turbine Blade Reference Model* (SAND2013-2569). https://www.osti.gov/servlets/purl/1095962
- UIUC Applied Aerodynamics Group (Selig database). *Airfoil coordinate database*. https://m-selig.ae.illinois.edu/ads/coord_database.html
