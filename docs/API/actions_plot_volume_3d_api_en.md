# API Reference - `plot_volume_3d.py`

This document covers the top-level classes and functions defined in `src/csf/actions/plot_volume_3d.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/plot_volume_3d.py`
- Output file: `docs/API/actions_plot_volume_3d_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
actions.plot_volume_3d
----------------------

Low-impact extraction of the 'plot_volume_3d' action from CSFActions.py.

Notes
-----
- This module intentionally has NO side-effect registration to avoid circular imports.
- Registration is explicit via CSFActions._load_actions().
- The runner body is copied "as-is" except for minimal adaptations required by dependency injection.
- This action is interactive-only: it does not write files; it creates a 3D figure and labels it so that
  CSFActions can show it at the end of the run (deferred display).
```

## Public API index

- `def registerregister_action, *, ActionSpec, ParamSpec, Visualizer` - line 32

## API details

## Functions

## CSFActions will show figures at the end of the run (deferred display).

### `register`

**Source lines:** `32-187`

```python
def registerregister_action, *, ActionSpec, ParamSpec, Visualizer
```

**Summary:** Register the 'plot_volume_3d' action.

**Docstring details**

```text
Parameters are injected from the CSFActions hub to avoid importing CSFActions here.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `not annotated` | `-` |
| `ActionSpec` | `keyword-only` | `not annotated` | `-` |
| `ParamSpec` | `keyword-only` | `not annotated` | `-` |
| `Visualizer` | `keyword-only` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`ActionSpec`, `register_action`, `bool`, `float`, `params.get`, `action.get`, `isinstance`, `Visualizer`, `plt.figure`, `fig.add_subplot`, `viz.plot_volume_3d`, `fig.set_label`, `RuntimeError`, `str`, `int`, `ParamSpec`, `plt.close`, `lower`, `seed.strip`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
