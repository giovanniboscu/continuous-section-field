# API Reference - `plot_properties.py`

This document covers the top-level classes and functions defined in `src/csf/actions/plot_properties.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/plot_properties.py`
- Output file: `docs/API/actions_plot_properties_api_en.md`
- Top-level function definitions found: `3`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
CSF Action Module: plot_properties
=================================

This module contains the logic for the `plot_properties` action.

Design goals (low-impact)
-------------------------
- No side-effect registration at import time (avoids import cycles).
- The module exposes:
    - SPEC: ActionSpec
    - RUN:  action runner (pure action logic)
    - register(register_action, ...): explicit registration hook
- The runner does NOT call plt.show(). It only creates/labels figures.
  Final GUI display is handled centrally by CSFActions' deferred-show logic.

Notes
-----
- This action does NOT use `stations:`. It samples internally between CSF endpoints.
- `properties:` must be validated/normalized by the manager before RUN is called.
```

## Public API index

- `def _build_specActionSpec: Any, ParamSpec: Any` - line 35
- `def _runfield: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool=False, SPEC: Any, Visualizer: Any` - line 67
- `def registerregister_action: Any, *, ActionSpec: Any, ParamSpec: Any, Visualizer: Any` - line 235

## API details

## Functions

## This is intentionally duplicated here so the action module is self-contained.

### `_build_spec`

**Source lines:** `35-61`

```python
def _build_specActionSpec: Any, ParamSpec: Any
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `ActionSpec` | `positional or keyword` | `Any` | `-` |
| `ParamSpec` | `positional or keyword` | `Any` | `-` |

**Returns:** `Any`

**Function/method calls visible in the code**

`ActionSpec`, `ParamSpec`

## Runner

### `_run`

**Source lines:** `67-229`

```python
def _runfield: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool=False, SPEC: Any, Visualizer: Any
```

**Summary:** Action: plot_properties

**Docstring details**

```text
Contract
--------
- stations_map is unused (forbidden by validation).
- action["properties"] must be a non-empty list (normalized by validation).
- Output behavior:
    * output omitted -> ["stdout"] -> keep figures for deferred final display
    * output includes file path(s) -> save a composite image
    * if "stdout" is NOT included -> file-only (figures are labelled as file-only)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `stations_map` | `positional or keyword` | `Dict[str, List[float]]` | `-` |
| `action` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `debug_flag` | `keyword-only` | `bool` | `False` |
| `SPEC` | `keyword-only` | `Any` | `-` |
| `Visualizer` | `keyword-only` | `Any` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`params.get`, `action.get`, `float`, `Visualizer`, `set`, `sorted`, `RuntimeError`, `int`, `plt.get_fignums`, `viz.plot_properties`, `plt.figure`, `fig.set_label`, `isinstance`, `len`, `io.BytesIO`, `fig.savefig`, `buf.seek`, `convert`, `im.load`, `buf.close`, `images.append`, `max`, `Image.new`, `Path`, `composite.save`, `print`, `sum`, `composite.paste`, `outp.parent.exists`, `str`, `plt.close`, `plt.gcf`, `Image.open`

## Explicit registration hook (no side effects)

### `register`

**Source lines:** `235-256`

```python
def registerregister_action: Any, *, ActionSpec: Any, ParamSpec: Any, Visualizer: Any
```

**Summary:** Register this action into the shared CSFActions registry.

**Docstring details**

```text
Parameters are injected explicitly from CSFActions.py to avoid:
- importing CSFActions from here (import cycles)
- duplicating shared helpers in multiple modules
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `Any` | `-` |
| `ActionSpec` | `keyword-only` | `Any` | `-` |
| `ParamSpec` | `keyword-only` | `Any` | `-` |
| `Visualizer` | `keyword-only` | `Any` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`_build_spec`, `register_action`, `_run`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
