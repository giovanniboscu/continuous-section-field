# API Reference - `write_opensees_geometry.py`

This document covers the top-level classes and functions defined in `src/csf/actions/write_opensees_geometry.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/write_opensees_geometry.py`
- Output file: `docs/API/actions_write_opensees_geometry_api_en.md`
- Top-level function definitions found: `3`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
CSF Action Module: write_opensees_geometry
=========================================

This module contains the logic for the `write_opensees_geometry` action.

Design goals (low-impact)
-------------------------
- No side-effect registration at import time (avoids import cycles).
- Explicit registration via register(register_action, ...).
- Keep the action runner logic identical to the monolithic CSFActions implementation.
- This is a file-only exporter: it writes exactly one Tcl file (no stdout output).

Important
---------
- This action forbids the YAML field `stations:`. Stations are generated internally
  by the exporter from `n_points`.
```

## Public API index

- `def _build_specActionSpec: Any, ParamSpec: Any` - line 28
- `def _runfield: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool=False, write_opensees_geometry: Any` - line 85
- `def registerregister_action: Any, *, ActionSpec: Any, ParamSpec: Any, write_opensees_geometry: Any` - line 147

## API details

## Functions

## Action SPEC (help/validation)

### `_build_spec`

**Source lines:** `28-79`

```python
def _build_specActionSpec: Any, ParamSpec: Any
```

**Summary:** Build ActionSpec for write_opensees_geometry.

**Docstring details**

```text
NOTE: This mirrors the baseline CSFActions catalog entry to keep help/validation coherent.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `ActionSpec` | `positional or keyword` | `Any` | `-` |
| `ParamSpec` | `positional or keyword` | `Any` | `-` |

**Returns:** `Any`

**Function/method calls visible in the code**

`ActionSpec`, `ParamSpec`

## Runner (copied from the monolithic implementation; minimal adaptations)

### `_run`

**Source lines:** `85-141`

```python
def _runfield: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool=False, write_opensees_geometry: Any
```

**Summary:** Action: write_opensees_geometry

**Docstring details**

```text
Export an OpenSees Tcl geometry file (sections + station list) by calling the
injected helper `write_opensees_geometry(...)`.

YAML shape (validated before execution):
  - write_opensees_geometry:
      output: [out/geometry.tcl]   # required, file-only (no stdout)
      params:
        n_points: 10              # required int
        E_ref: 2.1e11             # required float
        nu: 0.30                  # required float

Notes
-----
- This action does NOT use stations; 'stations:' must not be provided.
- This action is FILE-ONLY by design: it writes exactly one Tcl file.
- E_ref and nu are required here even if the underlying function defines defaults.
  This keeps the YAML plan explicit about the elastic reference assumptions.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `stations_map` | `positional or keyword` | `Dict[str, List[float]]` | `-` |
| `action` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `debug_flag` | `keyword-only` | `bool` | `False` |
| `write_opensees_geometry` | `keyword-only` | `Any` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `RuntimeError`
- `ValueError`

**Function/method calls visible in the code**

`params.get`, `action.get`, `write_opensees_geometry`, `RuntimeError`, `len`, `ValueError`, `int`, `isinstance`

## Explicit registration hook (no side effects)

### `register`

**Source lines:** `147-163`

```python
def registerregister_action: Any, *, ActionSpec: Any, ParamSpec: Any, write_opensees_geometry: Any
```

**Summary:** Register this action into the shared CSFActions registry.

**Docstring details**

```text
All dependencies are injected explicitly from CSFActions.py to avoid import cycles.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `Any` | `-` |
| `ActionSpec` | `keyword-only` | `Any` | `-` |
| `ParamSpec` | `keyword-only` | `Any` | `-` |
| `write_opensees_geometry` | `keyword-only` | `Any` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`_build_spec`, `register_action`, `_run`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
