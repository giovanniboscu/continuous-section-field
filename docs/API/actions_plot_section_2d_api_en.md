# API Reference - `plot_section_2d.py`

This document covers the top-level classes and functions defined in `src/csf/actions/plot_section_2d.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/plot_section_2d.py`
- Output file: `docs/API/actions_plot_section_2d_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Public API index

- `def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names, get_bool_param_strict, Visualizer` - line 24

## API details

## Functions

## manual window interaction.

### `register`

**Source lines:** `24-289`

```python
def registerregister_action, *, ActionSpec, ParamSpec, expand_station_names, get_bool_param_strict, Visualizer
```

**Summary:** Register the action (explicit registration; no side-effects).

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `not annotated` | `-` |
| `ActionSpec` | `keyword-only` | `not annotated` | `-` |
| `ParamSpec` | `keyword-only` | `not annotated` | `-` |
| `expand_station_names` | `keyword-only` | `not annotated` | `-` |
| `get_bool_param_strict` | `keyword-only` | `not annotated` | `-` |
| `Visualizer` | `keyword-only` | `not annotated` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`ActionSpec`, `register_action`, `get_bool_param_strict`, `params.get`, `int`, `action.get`, `expand_station_names`, `Visualizer`, `RuntimeError`, `float`, `plt.subplots`, `isinstance`, `viz.plot_section_2d`, `fig.set_label`, `figs.append`, `ParamSpec`, `title_tpl.replace`, `io.BytesIO`, `dict`, `fig.savefig`, `buf.seek`, `convert`, `im.load`, `buf.close`, `images.append`, `Path`, `str`, `ax.get_children`, `fig.set_constrained_layout`, `fig.canvas.draw`, `p.parent.exists`, `len`, `save`, `enumerate`, `getattr`, `Image.open`, `p.with_name`, `im.save`, `extra_artists.append`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
