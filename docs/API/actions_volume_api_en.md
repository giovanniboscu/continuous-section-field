# API Reference - `volume.py`

This document covers the top-level classes and functions defined in `src/csf/actions/volume.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/volume.py`
- Output file: `docs/API/actions_volume_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
actions.volume
--------------

Low-impact extraction of the 'volume' action from CSFActions.py.

Notes
- This module intentionally has NO side-effect registration to avoid circular imports.
- Registration is explicit via CSFActions._load_actions().
- The runner body is copied "as-is" except for minimal adaptations required by dependency injection.
```

## Public API index

- `def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names, volume_polygon_list_report_data, emit_volume_polygon_list_report, polygon_surface_w1_inners0=None, csf_weight_catalog_by_pair=None, csf_weights_by_pair_at_z=None, **_unused` - line 25

## API details

## Functions

## Top-level functions

### `register`

**Source lines:** `25-130`

```python
def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names, volume_polygon_list_report_data, emit_volume_polygon_list_report, polygon_surface_w1_inners0=None, csf_weight_catalog_by_pair=None, csf_weights_by_pair_at_z=None, **_unused
```

**Summary:** Register the 'volume' action.

**Docstring details**

```text
Notes
-----
- Some injected kwargs are accepted for backward compatibility but unused after consolidation.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `not annotated` | `-` |
| `ActionSpec` | `keyword-only` | `not annotated` | `-` |
| `ParamSpec` | `keyword-only` | `not annotated` | `-` |
| `expand_station_names` | `keyword-only` | `not annotated` | `-` |
| `volume_polygon_list_report_data` | `keyword-only` | `not annotated` | `-` |
| `emit_volume_polygon_list_report` | `keyword-only` | `not annotated` | `-` |
| `polygon_surface_w1_inners0` | `keyword-only` | `not annotated` | `None` |
| `csf_weight_catalog_by_pair` | `keyword-only` | `not annotated` | `None` |
| `csf_weights_by_pair_at_z` | `keyword-only` | `not annotated` | `None` |
| `**_unused` | `var keyword` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ActionSpec`, `register_action`, `params.get`, `expand_station_names`, `float`, `volume_polygon_list_report_data`, `emit_volume_polygon_list_report`, `action.get`, `print`, `len`, `ValueError`, `int`, `ParamSpec`, `isinstance`, `str`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
