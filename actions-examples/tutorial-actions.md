# Tutorial — Running CSF with YAML Actions (No Python Coding)

This tutorial explains, step by step, how to reproduce the **tapered-rectangle example** using **only two YAML files**:

- `geometry.yaml` — defines the cross-section geometry at a few reference stations.
- `actions.yaml` — tells CSF what to compute and which plots/files to generate.

The goal is to make the workflow clear for **students and instructors** who are comfortable with geometry and structural basics, but do not want to write Python.

---

## 1. What CSF Does (Conceptual Overview)

CSF (Continuous Section Field) represents a member whose cross-section changes along the longitudinal axis **z**.

You provide:

1. A **small number of station sections** (typically two: start `S0` and end `S1`).
2. A set of **actions** describing what outputs you want (analysis tables, plots, exports, solver templates).

CSF then:
- interpolates the section geometry between the defined stations (e.g., from `S0` to `S1`),
- evaluates geometric/section properties at requested **z stations**,
- produces plots and files according to your action list.

---

## 2. Example Problem: A Rectangle That Changes Height Along z

We model a solid rectangle whose **width is constant**, but whose **height increases** from the base to the top.

- Length along z: **L = 5.0 m**
- At z = 0.0 m (station `S0`):
  - width **b = 1.0**
  - height **h0 = 1.0**
- At z = 5.0 m (station `S1`):
  - width **b = 1.0**
  - height **h1 = 2.0**

This is a classical non-prismatic example: the area and inertias vary along the member.

### Coordinate convention used in this tutorial

We define the rectangle in the local (x, y) plane:

- x is horizontal (left/right),
- y is vertical (bottom/up),
- z is the member axis (along the length).

In the example, the rectangle is centered in x and starts at y = 0:

- x ranges from `-0.5` to `+0.5`  (width = 1.0)
- y ranges from `0.0` to `h(z)`   (height varies)

You can choose a different placement (e.g., centered in y as well). The physics is the same; only the centroid coordinates change.

---

## 3. File 1 — `geometry.yaml`

### 3.1 What goes into geometry.yaml

`geometry.yaml` defines the cross-section geometry at the stations you declare.

For a tapered member, the minimum useful case is:

- `S0`: geometry at z = 0
- `S1`: geometry at z = L

CSF uses these two to build a continuous field between them.

### 3.2 Key rules to follow (corrected)

1. **Polygon names must be unique within the same section**
   - Inside `S0`, every polygon key must be unique.
   - Inside `S1`, every polygon key must be unique.

2. **Across different sections (`S0` vs `S1`), polygon names can be different**
   - You may call a polygon `start` in `S0` and `end` in `S1`.
   - Matching between sections is not based on forcing equal text labels.

3. **Topological consistency remains required**
   - The corresponding polygon pair used for interpolation must represent the same logical part.
   - Keep the same vertex count for corresponding polygons.

4. **Vertices must be CCW (counter-clockwise)**
   - CSF expects CCW orientation as a precondition.

5. **No silent defaults**
   - If a required attribute (e.g., `weight`) is expected by your model/pipeline, declare it explicitly.

> **Important correction**  
> The statement “polygon names in `S0` and `S1` must be identical” is **not generally true**.  
> What must hold is **uniqueness in each section** plus **valid correspondence/topology** between sections.

### 3.3 Naming examples: valid vs invalid

#### Valid (different names across sections)

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        start:
          weight: 1.0
          vertices:
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 1.0]
            - [-0.5, 1.0]

    S1:
      z: 5.0
      polygons:
        end:
          weight: 1.0
          vertices:
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 2.0]
            - [-0.5, 2.0]
```

#### Invalid (duplicate name in same section)

```yaml
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        rect: {weight: 1.0, vertices: [[0,0],[1,0],[1,1],[0,1]]}
        rect: {weight: 1.0, vertices: [[2,0],[3,0],[3,1],[2,1]]}  # duplicate key -> invalid
```

### 3.4 Full `geometry.yaml` for the example

Save the following as `geometry.yaml`:

```yaml
CSF:
  # Two stations defining a linearly tapered solid rectangle along z.
  # Rectangle width is constant; height changes from S0 to S1.
  sections:
    S0:
      z: 0.0
      polygons:
        start:
          weight: 1.0
          vertices:
            # CCW vertices
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 1.0]
            - [-0.5, 1.0]

    S1:
      z: 5.0
      polygons:
        end:
          weight: 1.0
          vertices:
            # CCW vertices
            - [-0.5, 0.0]
            - [ 0.5, 0.0]
            - [ 0.5, 2.0]
            - [-0.5, 2.0]
```

---

## 4. File 2 — `actions.yaml`

### 4.1 What actions.yaml controls

`actions.yaml` is a **script** (but written in YAML) telling CSF:

- which z-stations to evaluate (via station sets),
- which actions to run,
- what to print and what to save to files.

### 4.2 Structure of actions.yaml

The root key must be:

- `CSF_ACTIONS`

Inside it:

1. `stations`: a dictionary of named station sets (each is a list of absolute z values).
2. `actions`: an ordered list of actions to execute.

### 4.3 Station sets (why they matter)

Many actions are evaluated at specific z coordinates, such as:

- full analysis at z = 0, 2.5, 5.0
- 2D plots at those same positions
- exporting the end sections

Defining station sets avoids repeating raw numbers everywhere.

In this example we define:

- `station_ends`: `[0.0, 5.0]`
- `station_mid`: `[2.5]`
- `station_3pt`: `[0.0, 2.5, 5.0]`

### 4.4 Actions used in the example (what each one does)

1. `section_full_analysis`
   - Computes a standard set of section properties at the given stations.
   - Exports a CSV table and prints to stdout.
   - Uses `fmt_display` to control numeric formatting in text output.

2. `plot_section_2d`
   - Draws the cross-section in the (x, y) plane at the requested stations.

3. `plot_properties`
   - Plots how properties evolve along z (e.g., A, Ix, Iy, Cx, Cy).
   - This action samples internally along z and does not use station sets.

4. `export_yaml`
   - Exports the sections at two stations (typically the ends) into a new geometry YAML.

5. `plot_volume_3d`
   - Plots the ruled volume built by interpolating between S0 and S1.
   - It usually uses internal sampling.

### 4.5 Full `actions.yaml` for the example

Save the following as `actions.yaml`:

```yaml
CSF_ACTIONS:
  # Station sets are lists of absolute z coordinates [m].
  stations:
    station_ends:  [0.0, 5.0]
    station_mid:   [2.5]
    station_3pt:   [0.0, 2.5, 5.0]

  actions:
    - section_full_analysis:
        stations: [station_3pt]
        output: [stdout, out/full.csv]
        params:
          fmt_display: ".6g"

    - plot_section_2d:
        stations: [station_3pt]
        output: [stdout, out/sections.bmp]

    - plot_properties:
        # This action samples internally between z0 and z1; stations are not used.
        output: [stdout, out/properties.png]
        properties: [A, Ix, Iy, Cx, Cy]
        params:
          num_points: 80

    - export_yaml:
        # Must contain exactly two z values.
        stations: [station_ends]
        output: [out/exported_geometry.yaml]

    - plot_volume_3d:
        params:
          line_percent: 100.0
          title: "Ruled volume"
```

---

## 5. Running the Example

From the directory containing both files:

```bash
python CSFActions.py geometry.yaml actions.yaml
```

### 5.1 Expected output files

Depending on your configured output paths, you should get:

- `out/full.csv` — table of section properties at z = 0, 2.5, 5.0
- `out/sections.bmp` — 2D section plot(s)
- `out/properties.png` — curves of A, Ix, Iy, Cx, Cy along z
- `out/exported_geometry.yaml` — exported end sections
- (3D volume plot behavior depends on your implementation: show only, or show + save)

If `out/` does not exist, create it first (or change output paths).

---

## 6. Sanity Checks (Quick Validation)

Because width is constant and height increases linearly, you should expect:

- Area:  
  \( A(z) = b \cdot h(z) \)  
  so A increases linearly from 1.0 to 2.0.

- Centroid y-coordinate (base at y=0):  
  \( C_y(z) = h(z)/2 \)  
  so Cy increases from 0.5 to 1.0.

- Rectangle centroidal inertia around x:
  \( I_x(z) = b h(z)^3 / 12 \)  
  so Ix grows nonlinearly with \(h^3\).

If your trends are qualitatively different, check geometry correspondence and orientation first.

---

## 7. Common Mistakes and Fixes

### 7.1 Incorrect belief: “names must be identical in S0 and S1”
- **Correction**: names may differ across sections.
- Required: unique names within each section + valid correspondence/topology.

### 7.2 Duplicate polygon key in same section
- Fix by making each polygon key unique in that section.

### 7.3 Vertex mismatch on corresponding polygons
- Ensure corresponding polygons have the same vertex count/order convention.

### 7.4 Wrong orientation (CW instead of CCW)
- Reverse vertex order to CCW.

### 7.5 Output path errors
- Create `out/` first or update paths.

### 7.6 `fmt_display` expectations
- It generally affects text display formatting, not every file format.

---

## 8. Extensions (Next Steps)

1. Add more stations (`S2`, `S3`, ...) for piecewise evolution.
2. Add multiple polygons for composite parts/void modeling.
3. Add solver-writer actions:
   - `write_opensees_geometry`
   - `write_sap2000_geometry`
4. Refine station sets to increase sampling near critical z zones.

---

## 9. Final Rule to Remember

For polygon naming in CSF station sections:

- **Within one section (e.g., S0), names must be unique.**
- **Between different sections (S0 vs S1), names can be different.**
- Geometry interpolation correctness depends on correspondence/topology, not string equality alone.
