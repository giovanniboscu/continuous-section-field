# What Is YAML?

## A configuration file you can actually read

Imagine you want to tell a program what to do.

You could change the source code every time you want a different analysis. But that would quickly become inconvenient: a different beam, a different load, or a different numerical approximation would require another code change.

A configuration file offers a simpler arrangement: **the program knows how to perform an analysis; the file tells it which analysis you want to perform.**

YAML is one way to write that file.

YAML is a plain-text format designed to describe information in a way that is reasonably easy for people to read and edit. You do not need a special editor. A simple text editor is enough.

A YAML file usually has the extension `.yaml` or `.yml`.

## What does it look like?

Here is a small example:

```yaml
beam:
  length: 500
  material: steel

analysis:
  name: bending_test
  enabled: true
```

You can read it almost as a sentence:

> There is a beam. Its length is 500 and its material is steel. There is an analysis named `bending_test`, and it is enabled.

There is no programming logic here: no loops, no functions, no equations to implement. It is **data**, organized into named groups.

The names `beam`, `length`, and `analysis` are just illustrative; each application defines which names it recognizes. YAML itself does not know what a beam is.

## The few rules you need at first

### 1. A colon associates a name with a value

```yaml
order: 8
```

This means: the setting named `order` has the value `8`.

### 2. Indentation shows what belongs together

```yaml
cuf:
  basis: scaled_legendre
  order: 8
```

Both `basis` and `order` belong to `cuf`.

**Use spaces, not tabs, for indentation.** Items at the same level should line up vertically. Two spaces per level is a good habit.

### 3. A dash introduces an item in a list

```yaml
stations:
  - 0.0
  - 0.5
  - 1.0
```

Here, `stations` contains three values. In many YAML files the same information can also be written on one line:

```yaml
stations: [0.0, 0.5, 1.0]
```

### 4. A `#` starts a comment

```yaml
# Transverse expansion of the displacement field
cuf:
  basis: scaled_legendre
  order: 8  # Expansion order
```

Comments are notes for the reader; they are not configuration settings.

### 5. Values have different kinds

```yaml
name: demonstration       # Text
order: 8                  # Integer
ratio: 0.25               # Decimal number
enabled: true             # Boolean (true or false)
path: ../models/beam.yaml # File path
```

Quotation marks are often optional for ordinary text, but they are useful when a value might be misread. For example, quote text that contains `: ` or ` #`.

## How YAML fits into CSF-CUF

In CSF-CUF, YAML files express modelling choices **without rewriting the solver**.

You first decide what you want to analyse: the beam, its geometry and materials, the loads and constraints, and how you want to approximate the displacement field. The configuration then records those choices in a structured form.

For example, the following fragment selects a transverse CUF expansion:

```yaml
cuf:
  basis: scaled_legendre
  order: 8
```

The structure is simple:

- `cuf` is the group of settings concerned with the transverse expansion.
- `basis` identifies the expansion to use.
- `order` selects its order.

A different case might use an expansion supplied by an external Python file:

```yaml
cuf:
  basis: ../expansions/xyz_demo_expansion.py
  order: 1
```

This is one of the useful ideas behind the configuration: **changing a modelling choice can be as simple as editing a value**, provided that the selected option is supported by the solver.

These are *fragments*, not complete runnable case files. A real analysis needs other sections and references, as described in the documentation.

## From YAML to a real beam geometry

So far, the examples have been small. Now imagine a real question: **what if the beam becomes narrower as we move along its length?**

This is where the CSF geometry file becomes useful. Instead of drawing every cross-section individually, we describe the sections at selected longitudinal stations and let CSF provide the intermediate geometry.

The following example is adapted from the [main CSF README](https://github.com/giovanniboscu/continuous-section-field/blob/main/README.md). It is a genuine CSF configuration structure, not just invented YAML vocabulary.

```yaml
# geometry.yaml — continuous geometry and material participation
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        startsection:
          weight: 1.0
          vertices:
            - [-0.4, -0.4]
            - [ 0.4, -0.4]
            - [ 0.4,  0.4]
            - [-0.4,  0.4]
    S1:
      z: 10.0
      polygons:
        endsection:
          weight: 1.0
          vertices:
            - [-0.2, -0.2]
            - [ 0.2, -0.2]
            - [ 0.2,  0.2]
            - [-0.2,  0.2]

  shear_weight_laws:
    - 'startsection,endsection: iso(0.2)'

  weight_laws:
    - 'startsection,endsection:1.0 - 0.28 * (1 - (z / 10.0)**2)'
```

### Read the geometry like a story

At `S0`, where `z` is zero, the cross-section is a square extending from `-0.4` to `0.4` in both section coordinates. At `S1`, where `z` is ten, it is a smaller square extending from `-0.2` to `0.2`.

Each square is described by four **vertices**. Each `[a, b]` pair is simply a point in the two-dimensional plane of the cross-section. The sequence of points describes the boundary, counter-clockwise in this example.

The two section labels, `S0` and `S1`, are not magic YAML keywords. They are names that CSF uses to identify the two stations. Likewise, `startsection` and `endsection` identify polygon regions in the model.

The result is a **tapered member**. CSF can provide the geometry between the two stations through its continuous section description. You do not have to list every intermediate square.

### And what about material behaviour?

Geometry is only part of the story. CSF also associates participation information with polygon regions.

The `weight: 1.0` assigned to each polygon is its base participation value. The `weight_laws` entry then supplies a longitudinal rule for the axial/bending participation of the named polygon regions. In the example, the expression changes with `z`.

The separate `shear_weight_laws` entry defines the shear/torsional participation. Here, `iso(0.2)` is a **CSF-specific isotropic shortcut**, using Poisson's ratio `0.2` to relate the two kinds of participation.

There are two useful lessons here:

1. **The shape and the participation laws are separate ideas.** The cross-section may change shape even without a changing material law; the material contribution may vary even when the geometry does not.
2. **YAML is not evaluating the formula.** YAML stores the quoted expression as text. CSF recognizes and evaluates it according to its own rules.

The numerical values above are illustrative and carry no declared physical units. Use a consistent unit system in an actual model. Also, CSF's section coordinates and longitudinal `z` convention should not be confused with the separate CUF solver coordinate convention.

## A second file: what should CSF do with that geometry?

Once the beam has been described, you may want to inspect the model before running a structural calculation: perhaps draw its shape, display a few sections, or calculate sectional properties.

For these tasks, CSF uses a separate `actions.yaml` file. Here is a short extract in the same style as the main README:

```yaml
# actions.yaml — operations on the CSF model
CSF_ACTIONS:
  stations:
    station_edge:
      - 0
      - 10
  actions:
    - plot_volume_3d:
        params:
          title: "Not prismatic"
    - plot_section_2d:
        stations:
          - station_edge
    - section_selected_analysis:
        stations:
          - station_edge
        properties: [A, Cx, Cy, Ix, Iy]
```

Read it in ordinary language: *use stations zero and ten; show the three-dimensional member; draw its end sections; and report selected section properties there.*

With the CSF command-line utility, the files are passed together:

```bash
csf-actions geometry.yaml actions.yaml
```

**Important:** `actions.yaml` belongs to the **CSF inspection and section-analysis workflow**. It is **not** the file that defines loads, constraints, or output for a CSF-CUF structural solve. CSF-CUF uses the CSF geometry/material description, but has its own configuration for the structural problem and the numerical case.

## Three questions, three responsibilities

You can now see why having several YAML files is practical rather than complicated:

| Human question | Configuration responsibility |
| --- | --- |
| What does the member look like, and how do its properties vary? | CSF geometry and participation laws (`geometry.yaml`, or another CSF model filename) |
| What would I like to inspect in the CSF model? | CSF actions (`actions.yaml`) |
| What loads, constraints, approximations, solver settings, and results do I want? | CSF-CUF problem, case, and output configuration |

The file names are conventions in these examples; it is their **content and the command that reads them** that determine their purpose.

This is also a practical advantage: you can change the transverse CUF expansion without redesigning the physical geometry, or revise the geometry without rewriting the CUF formulation.

For more about the physical-to-numerical transition, return to the [YAML Reference introduction](readme.md).

## YAML describes choices; it does not perform the calculation

This distinction matters.

A YAML file does not create the geometry, formulate the CUF equations, assemble a matrix, or solve a system. The corresponding software components do those jobs.

The YAML file provides the information they need. It acts like a clear set of instructions handed to an already capable program.

It also makes an analysis easier to reproduce: you can keep the configuration file together with the results and know which choices produced them.

## When something goes wrong

Most early YAML problems are small formatting mistakes:

- A setting is indented at the wrong level.
- A tab is used where spaces are required.
- A colon or dash is missing.
- A file path points somewhere else than expected.
- A setting name is spelled correctly as YAML, but is not recognized by the application.

One important point: **valid YAML does not automatically mean a valid CSF-CUF case**. YAML checks the structure of the data; CSF-CUF defines which sections, names, values, and combinations are meaningful.

## Where to go next

You do not need to memorize YAML before using CSF-CUF. Start from a working example, make one small change, and compare the result.

For the available configuration fields and their meaning, follow the reference pages:

- [Case Configuration](case_configuration.md) — Numerical case, CUF expansion, longitudinal approximation, and solver choices.
- [Problem Configuration](problem_configuration.md) — Physical model, loads, and constraints.
- [Output Configuration](output_configuration.md) — Requested results and diagnostics.

For a complete example that can be run, see the [CSF-CUF Quick Start](../../quickstart/README.md).

**The main idea:** YAML is not another mathematical model to learn. It is simply a readable way to tell CSF-CUF which model and analysis you have chosen.
