# API Reference - `plot_shear_weight.py`

This document covers the top-level classes and functions defined in `src/csf/actions/plot_shear_weight.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/plot_shear_weight.py`
- Output file: `docs/API/actions_plot_shear_weight_api_en.md`
- Top-level function definitions found: `3`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
CSF Action Module: plot_shear_weight
=============================

This module contains the logic for the `plot_shear_weight` action.

Design goals (low-impact)
-------------------------
- No side-effect registration at import time (avoids import cycles).
- The module exposes:
    - SPEC: ActionSpec
    - RUN:  action runner (only action logic)
    - register(register_action, ...): explicit registration hook
- The runner does NOT call plt.show(). It only creates/labels figures.
  Final GUI display is handled centrally by CSFActions' deferred-show logic.

Notes
-----
- This action does NOT use `stations:`. It samples internally between CSF endpoints.
- The runner temporarily monkey-patches `matplotlib.pyplot.show` to a no-op because
  the current Visualizer implementation ends with a direct `plt.show()`.
```

## Public API index

- `def _build_specActionSpec: Any, ParamSpec: Any` - line 36
- `def _runfield: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool=False, SPEC: Any, Visualizer: Any` - line 67
- `def registerregister_action: Any, *, ActionSpec: Any, ParamSpec: Any, Visualizer: Any` - line 294

## API details

## Functions

## This is duplicated here so the module is self-contained.

### `_build_spec`

**Source lines:** `36-61`

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

**Source lines:** `67-288`

```python
def _runfield: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool=False, SPEC: Any, Visualizer: Any
```

**Summary:** Action: plot_shear_weight

**Docstring details**

```text
Contract
--------
- stations_map is unused (forbidden by validation).
- Output behavior:
    * output omitted -> ["stdout"] -> label figures as showable
    * output includes file path(s) -> save a composite image
    * if "stdout" is NOT included -> file-only (label figures as file-only)
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

**Returned dictionary keys visible in the code**

`figure.max_open_warning`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`params.get`, `action.get`, `Visualizer`, `set`, `sorted`, `RuntimeError`, `int`, `plt.get_fignums`, `plt.figure`, `fig.set_label`, `matplotlib.rc_context`, `viz.plot_shear_weight`, `join`, `cleaned.strip`, `getattr`, `Path`, `hasattr`, `strip`, `line.strip`, `len`, `outp.parent.exists`, `list`, `fig.canvas.draw`, `fig.canvas.get_renderer`, `plt.close`, `plt.gcf`, `ylabel.splitlines`, `startswith`, `_sanitize_filename_fragment`, `expanded`, `bbox.transformed`, `_axis_polygon_tags`, `outp.with_name`, `used_target_paths.add`, `fig.savefig`, `text.strip`, `label.startswith`, `split`, `ax.get_ylabel`, `fig.dpi_scale_trans.inverted`, `str`, `ch.isalnum`, `ax.get_tightbbox`, `line.get_label`

## Explicit registration hook (no side effects)

### `register`

**Source lines:** `294-315`

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
