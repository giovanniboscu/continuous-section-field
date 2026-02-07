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

### 3.2 Key rules to follow

1. **Same polygon names at all stations**
   - If you call the polygon `rect` at `S0`, you must also call it `rect` at `S1`.

2. **Same number of vertices for the same polygon**
   - If `rect` has 4 vertices at `S0`, it must have 4 vertices at `S1`.

3. **Vertices must be CCW (counter-clockwise)**
   - CSF expects CCW orientation as a precondition. Do not rely on downstream “fixes”.

4. **No silent defaults**
   - If the polygon requires `weight`, provide it explicitly.

### 3.3 The actual geometry.yaml for the example

Save the following as `geometry.yaml`:

```yaml
CSF:
  # Two stations defining a linearly tapered solid rectangle along z.
  # Rectangle width is constant; height changes from S0 to S1.
  sections:
    S0:
      z: 0.0
      polygons:
        rect:
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
        rect:
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

Defining station sets avoids repeating the raw numbers everywhere.

In this example we define:

- `station_ends`: `[0.0, 5.0]`
- `station_mid`: `[2.5]`
- `station_3pt`: `[0.0, 2.5, 5.0]`

### 4.4 Actions used in the example (what each one does)

We use five actions:

1. `section_full_analysis`
   - Computes a standard set of section properties at the given stations.
   - Exports a CSV table and prints to stdout.
   - Uses `fmt_display` to control numeric formatting in text output.

2. `plot_section_2d`
   - Draws the cross-section in the (x, y) plane at the requested stations.

3. `plot_properties`
   - Plots how properties evolve along z (e.g., A, Ix, Iy, Cx, Cy).
   - Important: this action **samples internally** along z and does not take stations.

4. `export_yaml`
   - Exports the sections at two stations (typically the ends) into a new geometry YAML.

5. `plot_volume_3d`
   - Plots the ruled volume built by interpolating between S0 and S1.
   - Like `plot_properties`, it typically does internal sampling (no stations).

### 4.5 The actual actions.yaml for the example

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

### 5.1 Output files you should see

Depending on your configured output paths, you should get:

- `out/full.csv` — table of section properties at z = 0, 2.5, 5.0
- `out/sections.bmp` — 2D section plot(s)
- `out/properties.png` — curves of A, Ix, Iy, Cx, Cy along z
- `out/exported_geometry.yaml` — exported end sections
- (3D volume plot output depends on your implementation; some versions only show it, some also save it)

If an `out/` directory does not exist, create it first (or change the paths).

---

## 6. What Results Should Look Like (Sanity Checks)

Because the width is constant and height increases linearly, you should expect:

- Area:  
  \( A(z) = b \cdot h(z) \)  
  So A should increase linearly from 1.0 to 2.0.

- Centroid y-coordinate (with base at y=0):  
  \( C_y(z) = h(z)/2 \)  
  So Cy increases from 0.5 to 1.0.

- Second moment of area about x-axis for a rectangle about its base:
  If computed about centroid (common),  
  \( I_x(z) = b h(z)^3 / 12 \)  
  So Ix grows with \(h^3\): strongly non-linear.

These checks help confirm the interpolation and evaluation are working.

---

## 7. Common Mistakes and How to Fix Them

### 7.1 “Stations missing” or “Stations invalid”
- Ensure station set names exist under `CSF_ACTIONS.stations`.
- Ensure `stations:` references the station set correctly, e.g. `stations: [station_3pt]`.

### 7.2 Polygon mismatch between S0 and S1
- Same polygon name at both stations.
- Same number of vertices at both stations.

### 7.3 Wrong orientation (CW instead of CCW)
- Reverse vertex order to make it CCW.
- Do not rely on internal auto-fixes.

### 7.4 Output path errors
- Create `out/` directory or change the output paths.

### 7.5 “fmt_display does nothing”
- `fmt_display` affects text formatting (stdout/txt), not necessarily CSV formatting.
- Verify which action uses it and for which outputs.

---

## 8. Extensions (Next Steps)

Once this works, you can extend the same pattern:

1. Add more stations (S2, S3, ...) if you want piecewise-defined geometry.
2. Add multiple polygons to represent multi-material or voids (composite/nesting).
3. Add solver writers:
   - `write_opensees_geometry`
   - `write_sap2000_geometry`
4. Change station sets to concentrate evaluation where needed (e.g., near discontinuities).

---

## Summary

- `geometry.yaml` defines the “what”: cross-section polygons at station sections.
- `actions.yaml` defines the “how/when”: which z-stations to evaluate and which outputs to generate.
- With these two files, you can run full analyses and generate plots without touching Python code.
