# API Reference - `write_sap2000_geometry.py`

This document covers the top-level classes and functions defined in `src/csf/actions/write_sap2000_geometry.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/write_sap2000_geometry.py`
- Output file: `docs/API/actions_write_sap2000_geometry_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
actions.write_sap2000_geometry
------------------------------

Low-impact extraction of the 'write_sap2000_geometry' action from CSFActions.py.

Design constraints
- No side-effect registration (to avoid circular imports).
- Registration is explicit via CSFActions._load_actions().
- The runner body is copied as-is, with only the minimal adjustments needed:
  - A common runner signature that accepts debug_flag (ignored here).
  - Dependencies (write_sap2000_template_pack + the hub ActionSpec instance) are injected.

Behavioral contract (must remain stable)
- 'stations' is optional: if provided, explicit absolute stations are used; otherwise Lobatto is used.
- 'output' is REQUIRED and must be file-only: exactly one file path; 'stdout' is forbidden.
- include_plot writes the preview PNG and queues that PNG for deferred display without blocking.
```

## Public API index

- `def registerregister_action, *, spec, write_sap2000_template_pack` - line 26

## API details

## Functions

## Top-level functions

### `register`

**Source lines:** `26-296`

```python
def registerregister_action, *, spec, write_sap2000_template_pack
```

**Summary:** Register the 'write_sap2000_geometry' action.

**Docstring details**

```text
Parameters are injected from the CSFActions hub to avoid importing CSFActions here.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `not annotated` | `-` |
| `spec` | `keyword-only` | `not annotated` | `-` |
| `write_sap2000_template_pack` | `keyword-only` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `RuntimeError`
- `ValueError`

**Function/method calls visible in the code**

`register_action`, `params.get`, `strip`, `mode_str.upper`, `bool`, `str`, `action.get`, `Path`, `isinstance`, `RuntimeError`, `ValueError`, `len`, `template_path.parent.mkdir`, `enumerate`, `set`, `pf.parent.mkdir`, `plt.get_fignums`, `write_sap2000_template_pack`, `preview_path.exists`, `getattr`, `pf.is_absolute`, `float`, `convert`, `plt.figure`, `fig.add_axes`, `ax.imshow`, `ax.set_axis_off`, `ax.set_position`, `fig.subplots_adjust`, `fig.set_label`, `plt.close`, `fig.canvas.manager.set_window_title`, `int`, `Image.open`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
