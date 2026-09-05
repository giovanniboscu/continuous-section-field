# Introduction

The CUF module provides a general and modular implementation of structural models based on the **Carrera Unified Formulation (CUF)**.

The main idea of the implementation is to keep the structural formulation independent from the particular geometry, material distribution, and transverse expansion adopted for a given problem. Rather than embedding a specific beam section or a predefined material model inside the solver, these ingredients are provided through separate components.

In this architecture, the physical description of the cross-section is supplied by the **Continuous Section Field (CSF)** model. CSF defines the geometry of the section and the associated material field, while the CUF solver uses this information through generic section and constitutive interfaces. The solver therefore does not need to know whether the section is rectangular, T-shaped, hollow, multi-domain, or characterized by spatially varying material properties.

Conceptually, the interaction can be summarized as

**CSF physical model → CUF section/material interface → CUF structural formulation**

This separation is particularly useful for sections whose geometry or material properties vary continuously, because the structural formulation can operate directly on the section model without introducing a geometry-specific implementation inside the solver.

A second independent component of the formulation is the **transverse expansion law** used to approximate the three-dimensional displacement field over the cross-section. The CUF implementation does not impose a single expansion family. Expansion laws are implemented as independent plugins and can be selected or extended without modifying the structural solver itself.

The current framework therefore separates three fundamental aspects of the model:

* the **physical cross-section**, described by CSF;
* the **transverse approximation**, described by a CUF expansion law;
* the **structural solution procedure**, handled by the generic CUF solver.

This tutorial will use this architecture to construct a simple example from the beginning: a **T-shaped section with spatially varying material properties**. The purpose of the example is not only to solve a particular structural problem, but also to show how geometry, material description, CUF expansion, and structural analysis remain distinct and interchangeable parts of the same model.
