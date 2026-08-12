# API Reference - `export_yaml.py`

This document covers the top-level classes and functions defined in `src/csf/actions/export_yaml.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/export_yaml.py`
- Output file: `docs/API/actions_export_yaml_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Public API index

- `def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names` - line 11

## API details

## Functions

## It intentionally avoids importing CSFActions to prevent circular imports.

### `register`

**Source lines:** `11-87`

```python
def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names
```

**Summary:** Register the export_yaml action (SPEC + RUN).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `not annotated` | `-` |
| `ActionSpec` | `keyword-only` | `not annotated` | `-` |
| `ParamSpec` | `keyword-only` | `not annotated` | `-` |
| `expand_station_names` | `keyword-only` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`ActionSpec`, `register_action`, `action.get`, `expand_station_names`, `field.write_section`, `len`, `ValueError`, `isinstance`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
