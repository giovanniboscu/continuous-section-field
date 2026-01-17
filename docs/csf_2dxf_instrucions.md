# FreeCAD Authoring Guide for CSF-Compatible Models

> **Required FreeCAD version:** **FreeCAD 1.0.0**  
> This guide is written for **FreeCAD 1.0.0 on Linux**. Menu labels may vary slightly on other platforms or versions.

This document is a **step-by-step, beginner-friendly** guide to create a FreeCAD model that can later be **automatically exported** (by a separate tool) into a CSF-style YAML structure.

**Important:** The person modeling in FreeCAD **does not need to see or write any YAML**.  
They only need to **draw**, **fill a few properties**, and **save** the `.FCStd` file.

---

## What You Are Building (Conceptually)

Your FreeCAD file must contain:

1. **Exactly two section groups** in the model tree:
   - `S0`
   - `S1`

2. Inside each group, **one or more polygon objects** (closed 2D wires).

3. Each section group has a numeric property:
   - `CSF_z` (float)

4. Each polygon object has a numeric property:
   - `CSF_weight` (float)

5. Each polygon object has a **name** (its **Label**) that will be used as the polygon identifier later:
   - Example polygon labels: `lowerpart`, `upperpart`, `web`, `flange_left`, etc.

6. Each polygon must be a **closed polygon** with **straight segments** (recommended):
   - Any number of vertices (≥ 3).
   - Vertices should be in **counter-clockwise (CCW)** order if possible.

---

## Quick Checklist (Read This First)

Before you deliver the `.FCStd` file, confirm:

- [ ] The model tree contains **two groups** named exactly `S0` and `S1`.
- [ ] Every polygon belongs to either `S0` or `S1` (no polygons left outside).
- [ ] Every polygon is a **closed wire** (not open).
- [ ] Every polygon has a unique **Label** within its section.
- [ ] Group `S0` has `CSF_z` set (example: `0.0`).
- [ ] Group `S1` has `CSF_z` set (example: `10.0`).
- [ ] Every polygon has `CSF_weight` set (example: `1.0`).
- [ ] You saved the document as `.FCStd`.

---

## 1) Install and Start FreeCAD

1. Install **FreeCAD 1.0.0**.
2. Launch FreeCAD.
3. Create a new document:
   - **File → New**
4. Save immediately:
   - **File → Save As…**
   - Choose a project folder
   - Save as: `my_csf_model.FCStd`

Saving early prevents losing work and ensures the file remains in the right location.

---

## 2) Switch to the Draft Workbench (Recommended)

For polygonal 2D geometry, the **Draft** workbench is typically the simplest.

1. Find the **Workbench selector** (a dropdown, usually near the top toolbar).
2. Select **Draft**.

If you do not see Draft tools, ensure FreeCAD is fully installed with standard workbenches.

---

## 3) Create the Two Required Section Groups: S0 and S1

You must create **two** groups in the model tree. They are the “containers” for polygons.

### 3.1 Create the group `S0`

1. In the left panel (**Model** tree), right-click in an empty area.
2. Click **Create group**.
3. A new group appears (e.g., “Group”).
4. Rename it to `S0`:
   - Select the group
   - Press **F2** (or right-click → Rename)
   - Type: `S0`
   - Press Enter

### 3.2 Create the group `S1`

Repeat the same steps:
1. Right-click in empty space → **Create group**
2. Rename the new group to `S1`

### 3.3 Verify group names

Your model tree should now show (at minimum):

- `S0`
- `S1`

**Spelling matters.** Use exactly `S0` and `S1` (uppercase S, digit 0/1).

---

## 4) Draw Polygons (Closed 2D Wires)

You can create any number of polygons in each section.

### 4.1 Create a polygon wire (generic steps)

1. With Draft workbench active, choose the tool:
   - **Draft Polyline** or **Draft Wire** (name may vary)
2. Click in the 3D view to place vertices.
3. Add as many vertices as needed.
4. Close the polygon:
   - Many Draft polyline tools allow closing the wire:
     - Either by a “Close” option in the task panel
     - Or by clicking the first point again
   - If the tool does not close automatically, do not proceed until you have a closed wire (see “Troubleshooting”).

### 4.2 Best practices for polygons

- Use **straight segments** (line edges).
- Avoid splines/arcs unless you are sure your downstream pipeline supports them.
- Avoid self-intersecting shapes (no “bow-tie” polygons).
- Keep polygons planar (2D). Ideally draw them in the **XY plane**.

### 4.3 Verify the polygon is closed

After creating a wire:
1. Select the polygon object in the Model tree.
2. Check its properties in the **Property editor** (usually bottom-left):
   - Look for a boolean property like `Closed` (common for Draft wires).
   - It should be **True**.
3. If you cannot confirm closed status via a property:
   - Zoom in and visually confirm the first and last vertex are connected.
   - If in doubt, remake the wire and ensure it is closed.

---

## 5) Put Each Polygon Into the Correct Section Group

Each polygon must belong to exactly one group:

- Polygons for section `S0` must be inside group `S0`
- Polygons for section `S1` must be inside group `S1`

### 5.1 Move a polygon into a group

1. In the Model tree, find the polygon object you created.
2. Drag it onto the group `S0` or `S1`.
3. Confirm it now appears “under” that group in the tree.

Repeat for all polygons.

---

## 6) Name Polygons Using Labels (Formal Keys)

The polygon name used later is taken from the object’s **Label** (human-friendly name).

### 6.1 Rename a polygon

1. Select the polygon object in the Model tree.
2. Press **F2** (or right-click → Rename).
3. Set the label to a formal name, for example:
   - `lowerpart`
   - `upperpart`
4. Press Enter.

### 6.2 Naming rules (strongly recommended)

- Use only: `a-z`, `A-Z`, `0-9`, `_`
- No spaces
- No colon `:`
- Keep names unique **within the same section**:
  - In `S0`, you can have `lowerpart` once.
  - In `S1`, you can also have `lowerpart` once (that is OK).

---

## 7) Add Required CSF Metadata Properties in FreeCAD

You must store numeric metadata in the FreeCAD document so that later export can reconstruct the CSF structure.

### Required properties

- On group objects `S0` and `S1`:
  - `CSF_z` (float) → the z-coordinate of the section

- On each polygon object:
  - `CSF_weight` (float) → the polygon weight

### How to add these properties

FreeCAD does not always provide a purely GUI-based “Add custom property” flow that is easy for beginners.  
The most reliable beginner workflow is:

1) **Run a small macro inside FreeCAD** once to add the properties.  
2) Then edit the values normally in the Property editor.

This macro **does not export YAML** and does not require any scripting knowledge beyond copy/paste.

---

## 8) Create a Simple “CSF Initialize” Macro (Beginner-Friendly)

### 8.1 Open the Macro editor

1. Go to **Macro → Macros…**
2. Click **Create**
3. Name the macro:
   - `CSF_Initialize_Properties`
4. Click OK (an editor opens)

### 8.2 Copy/paste this macro code

Copy everything below into the macro editor:

```python
import FreeCAD as App

doc = App.ActiveDocument
if doc is None:
    raise RuntimeError("No active document. Open your .FCStd file first.")

def ensure_float_prop(obj, prop_name, group, default, docstring):
    if hasattr(obj, prop_name):
        return
    obj.addProperty("App::PropertyFloat", prop_name, group, docstring)
    setattr(obj, prop_name, float(default))

# Find groups S0 and S1
groups = {o.Name: o for o in doc.Objects if hasattr(o, "Group")}
for sec in ["S0", "S1"]:
    grp = None
    for o in doc.Objects:
        if hasattr(o, "Group") and (o.Name == sec or o.Label == sec):
            grp = o
            break
    if grp is None:
        raise RuntimeError(f"Group {sec} not found. Create groups named {sec} first.")

    # Add CSF_z to the group
    ensure_float_prop(grp, "CSF_z", "CSF", 0.0, "Section z value for CSF export.")

    # Add CSF_weight to every object inside the group
    for child in list(grp.Group):
        ensure_float_prop(child, "CSF_weight", "CSF", 1.0, "Polygon weight for CSF export.")

App.Console.PrintMessage("CSF properties initialized: CSF_z on S0/S1, CSF_weight on polygons.\n")
```

### 8.3 Save and run the macro

1. Save the macro (disk icon in the macro editor).
2. Close the editor.
3. Go to **Macro → Macros…**
4. Select `CSF_Initialize_Properties`
5. Click **Execute**

If everything is correct, FreeCAD prints a message in the report/console area:
- `CSF properties initialized...`

---

## 9) Set Section z Values (CSF_z)

Now you must set `CSF_z` for each section group.

### 9.1 Set z for S0

1. Select group `S0` in the Model tree.
2. In the Property editor, open the **Data** tab.
3. Find the section/group called **CSF**.
4. Set:
   - `CSF_z = 0.0` (example)

### 9.2 Set z for S1

Repeat:
1. Select group `S1`
2. Data tab → CSF
3. Set:
   - `CSF_z = 10.0` (example)

**You can use any floats you need**. The important part is that `S0` and `S1` both have a numeric `CSF_z`.

---

## 10) Set Polygon Weights (CSF_weight)

Each polygon object must have a `CSF_weight` float.

### 10.1 Set polygon weight

1. Select a polygon object (e.g., `lowerpart`) under `S0`.
2. Property editor → **Data** tab.
3. Find category **CSF**.
4. Set `CSF_weight` (example: `1.0`).

Repeat for every polygon under `S0` and `S1`.

---

## 11) Orientation Rule (CCW) — What You Should Do

The downstream pipeline expects polygon vertices in a stable order.  
The recommended convention is **Counter-Clockwise (CCW)**.

### Practical advice for beginners
- When you click points to create the polygon, click them in a CCW order.
- Example: to draw a rectangle CCW:
  1. bottom-left
  2. bottom-right
  3. top-right
  4. top-left
  5. close

If you accidentally draw clockwise, **do not panic**—export tools can often correct orientation.  
But the safest approach is to draw CCW from the beginning.

---

## 12) Example: Build the Exact Structure (S0 + S1, 2 Polygons Each)

This example shows what your **FreeCAD tree and properties** should look like for a common case.

### Target structure in the Model tree

- `S0` (Group)
  - `lowerpart` (Polygon object)
  - `upperpart` (Polygon object)
- `S1` (Group)
  - `lowerpart` (Polygon object)
  - `upperpart` (Polygon object)

### Required property values

- Select `S0`:
  - `CSF_z = 0.0`
- Select `S1`:
  - `CSF_z = 10.0`

- Select each polygon:
  - `CSF_weight = 1.0`

### Suggested beginner geometry (simple rectangles)

In `S0`:
- `lowerpart`: rectangle at the bottom
- `upperpart`: rectangle above it

In `S1`:
- similar rectangles (can be the same XY shape or different)

**Important:** The exact dimensions do not matter for the workflow.  
What matters is:
- Closed polygons
- Correct grouping
- Correct labels
- Required properties filled

---

## 13) Final Step: Save and Deliver the File

When everything is ready:

1. **File → Save**
2. Deliver the `.FCStd` file to the person/system that will run the export pipeline.

Recommended filename format:
- `projectname_csf.FCStd`
- `beam_section_csf.FCStd`

---

## 14) Common Mistakes and How to Fix Them

### Mistake A: “I forgot to put polygons into S0/S1”
Fix:
- Drag the polygon objects into the correct group in the Model tree.

### Mistake B: “My polygon is open (not closed)”
Fix:
- Edit the wire and close it, or remake it carefully and ensure closure.

### Mistake C: “I used spaces or weird characters in names”
Fix:
- Rename polygon labels to safe keys like `upperpart`, `lower_part`, etc.

### Mistake D: “I can’t find CSF_z or CSF_weight”
Fix:
- Run the macro **CSF_Initialize_Properties** again.
- Then re-check the Data tab.

### Mistake E: “I renamed S0/S1 incorrectly”
Fix:
- Ensure groups are named exactly `S0` and `S1`.
- Do not use `s0`, `Section0`, or `S-0`.

---

## 15) What to Do If You Imported From DXF

If you import DXF and objects come in grouped or as compounds:

- Make sure you end up with **one object per polygon** (each one closed).
- Put them into `S0` / `S1`.
- Rename labels.
- Initialize properties (macro).
- Set `CSF_z` and `CSF_weight`.
- Save.

---

## Summary

To create a CSF-compatible FreeCAD model:

1. Create groups `S0` and `S1`.
2. Create closed polygon wires and move them into the correct group.
3. Rename polygon **Labels** to formal names.
4. Add/set `CSF_z` on each group and `CSF_weight` on each polygon.
5. Save the `.FCStd`.

That’s all the modeler needs to do—no YAML required.
