# API Reference - `section_selected_analysis.py`

This document covers the top-level classes and functions defined in `src/csf/actions/section_selected_analysis.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/section_selected_analysis.py`
- Output file: `docs/API/actions_section_selected_analysis_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Public API index

- `def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names, section_full_analysis` - line 50

## API details

## Functions

## Allowed keys + meaning (kept in one place to avoid drift between help and output)

### `register`

**Source lines:** `50-267`

```python
def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names, section_full_analysis
```

**Summary:** Register the section_selected_analysis action (SPEC + RUN).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `not annotated` | `-` |
| `ActionSpec` | `keyword-only` | `not annotated` | `-` |
| `ParamSpec` | `keyword-only` | `not annotated` | `-` |
| `expand_station_names` | `keyword-only` | `not annotated` | `-` |
| `section_full_analysis` | `keyword-only` | `not annotated` | `-` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`z`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`ActionSpec`, `register_action`, `params.get`, `list`, `expand_station_names`, `action.get`, `RuntimeError`, `len`, `set`, `print`, `isinstance`, `str`, `field.section`, `section_full_analysis`, `io.StringIO`, `buf.getvalue`, `report_blocks.append`, `Path`, `ParamSpec`, `seen.add`, `float`, `redirect_stdout`, `rows.append`, `flat_outputs.extend`, `flat_outputs.append`, `p.parent.exists`, `p.suffix.lower`, `lower`, `dups.append`, `format`, `_ALLOWED_KEYS_MEANING.get`, `export_polygon_vertices_csv`, `full.get`, `open`, `csv.DictWriter`, `w.writeheader`, `f.write`, `strip`, `w.writerow`, `blk.endswith`, `_format_value`, `r.get`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
