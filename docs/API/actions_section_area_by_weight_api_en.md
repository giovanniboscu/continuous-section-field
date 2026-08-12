# API Reference - `section_area_by_weight.py`

This document covers the top-level classes and functions defined in `src/csf/actions/section_area_by_weight.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/section_area_by_weight.py`
- Output file: `docs/API/actions_section_area_by_weight_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
actions.section_area_by_weight
-----------------------------

Low-impact extraction of the 'section_area_by_weight' action from CSFActions.py.

Notes
- This module intentionally has NO side-effect registration to avoid circular imports.
- Registration is explicit via CSFActions._load_actions().
- The runner body is copied "as-is" except for minimal adaptations required by dependency injection.
```

## Public API index

- `def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names, polygon_surface_w1_inners0` - line 24

## API details

## Functions

## Top-level functions

### `register`

**Source lines:** `24-390`

```python
def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names, polygon_surface_w1_inners0
```

**Summary:** Register the 'section_area_by_weight' action.

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
| `expand_station_names` | `keyword-only` | `not annotated` | `-` |
| `polygon_surface_w1_inners0` | `keyword-only` | `not annotated` | `-` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`z`, `id`, `w`, `s0_name`, `s1_name`, `A_net`, `A_w`

**Raises visible in the code**

- `RuntimeError`
- `KeyError`
- `ValueError`
- `TypeError`

**Function/method calls visible in the code**

`ActionSpec`, `register_action`, `params.get`, `expand_station_names`, `any`, `callable`, `RuntimeError`, `hasattr`, `action.get`, `KeyError`, `_default`, `ValueError`, `isinstance`, `str`, `float`, `polygon_surface_w1_inners0`, `field.inspect_section_entities`, `Path`, `ParamSpec`, `TypeError`, `e.get`, `_wbin`, `sorted`, `max`, `io.StringIO`, `report_blocks.append`, `p.parent.exists`, `p.suffix.lower`, `format`, `round`, `r.get`, `len`, `redirect_stdout`, `print`, `buf.getvalue`, `int`, `csv_rows.append`, `open`, `csv.DictWriter`, `w.writeheader`, `suffix.lower`, `_fmt`, `join`, `w.writerow`, `f.write`, `blk.endswith`, `abs`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
