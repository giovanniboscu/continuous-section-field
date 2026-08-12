# API Reference - `CSFActions.py`

This document covers the top-level classes and functions defined in `src/csf/CSFActions.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/CSFActions.py`
- Output file: `docs/API/CSFActions_api_en.md`
- Top-level function definitions found: `19`.
- Top-level classes found: `3`.
- Duplicate function names found: `0`.

## Module docstring

```text
CSFReader_ver_W.py
================

User-facing runner for CSF using two declarative YAML files:

  1) geometry.yaml  -> CSF geometry (validated + loaded by CSFReader)
  2) actions.yaml   -> actions plan (FULL validation required before execution)

Design goals
------------
- This tool is meant for NON-Python users.
- Errors must be clear, friendly, and actionable.
- No raw Python tracebacks by default.
- YAML errors should show a short snippet with line numbers and a caret pointer.
- Warnings do NOT require snippets (per project spec).

Scope (v0.1)
------------
- Load geometry.yaml via CSFReader (and always print CSFReader issues).
- Load + FULL-validate actions.yaml against a flexible "action spec" catalog:
    * stations: REQUIRED
    * actions:  REQUIRED
    * each action item: a dict with exactly one action key
    * common action envelope:
        - stations (REQUIRED): list of station names
        - output   (OPTIONAL): list[str] default ["stdout"]
        - params   (OPTIONAL): mapping; action-specific
    * station lists: YAML list of numbers
        - WARNING if not sorted ascending
        - WARNING if duplicates are found
- Execute actions in order.
  Implemented actions are listed by --help-actions.
  Other actions are placeholders and will stop the run with a controlled error.

Usage
-----
python CSFActions.py geometry.yaml actions.yaml
python CSFActions.py --help-actions

Development convenience:
- If you run the script with no CLI args, it falls back to:
    geometry=case.yaml
    actions=actions_example.yaml
```

## Public API index

- `RawTextDefaultsHelpFormatter` - line 286
- `ParamSpec` - line 292
- `ActionSpec` - line 305
- `def csf_weight_catalog_by_pairfield: Any, *, include_default_linear: bool=True` - line 174
- `def csf_weights_by_pair_at_zfield: Any, z: float` - line 251
- `def register_actionspec: ActionSpec, runner: Any` - line 664
- `def _make_snippettext: str, line_no: Optional[int], col_no: Optional[int]` - line 715
- `def _find_key_linetext: str, key: str` - line 739
- `def _precheck_corruption_actionstext: str` - line 755
- `def _parse_actions_yamltext: str, filepath: str` - line 858
- `def _validate_output_writableout_str: str` - line 977
- `def _coerce_param_aliasesaction: str, params: Dict[str, Any], issues: List[Issue]` - line 1000
- `def _validate_action_paramsaction: str, params: Dict[str, Any], filepath: str, text: str, line_hint: Optional[int], action_display_name: Optional[str]=None` - line 1024
- `def _validate_actions_docdoc: Dict[str, Any], text: str, filepath: str` - line 1142
- `def print_actions_help` - line 2201
- `def _expand_station_namesstations_map: Dict[str, List[float]], station_names: List[str]` - line 2265
- `def _ensure_analysis_imports_or_errorissues: List[Issue], filepath: str, actions_list: Optional[List[Dict[str, Any]]]=None` - line 2293
- `def _get_bool_param_strictparams: Dict[str, Any], name: str, default: bool, *, path: str` - line 2394
- `def _load_actions` - line 2418
- `def _run_actionsfield: Any, actions_root: Dict[str, Any]` - line 2555
- `def _load_geometrygeometry_path: Path` - line 2638
- `def mainargv: Optional[List[str]]=None` - line 2668

## API details

## Classes

### `RawTextDefaultsHelpFormatter`

**Source lines:** `286-287`

```python
class RawTextDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter)
```

**Summary:** Docstring absent.

### `ParamSpec`

**Source lines:** `292-301`

**Decorators**

- `dataclass`

```python
class ParamSpec
```

**Summary:** Specification for one action parameter under action.params.

### `ActionSpec`

**Source lines:** `305-312`

**Decorators**

- `dataclass(frozen=True)`

```python
class ActionSpec
```

**Summary:** Specification for one action (name + params schema + documentation).

## Functions

## Legacy label 'plot3d' is kept for backward compatibility with older actions.

### `csf_weight_catalog_by_pair`

**Source lines:** `174-248`

```python
def csf_weight_catalog_by_pairfield: Any, *, include_default_linear: bool=True
```

**Summary:** Build a catalog of polygon weights/laws, grouped by the polygon-name pair (S0_name, S1_name).

**Docstring details**

```text
Returns a dict:
    {
      (name0, name1): {
          "index": i+1,
          "w0": <float>,          # endpoint weight in section S0
          "w1": <float>,          # endpoint weight in section S1
          "law": <str|None>,      # custom weight law expression (if any)
          "effective": <str>,     # "linear" if no custom law (and include_default_linear=True)
      },
      ...
    }
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `include_default_linear` | `keyword-only` | `bool` | `True` |

**Returns:** `Dict[PolyPair, Dict[str, Any]]`

**Returned dictionary keys visible in the code**

`index`, `w0`, `w1`, `law`, `effective`

**Raises visible in the code**

- `TypeError`
- `ValueError`

**Function/method calls visible in the code**

`list`, `getattr`, `enumerate`, `TypeError`, `len`, `ValueError`, `isinstance`, `zip`, `str`, `float`, `_get_law_for_index`, `hasattr`, `laws.get`

## Rare case: list; your field.section() attempts 1-based access (laws[idx1]).

### `csf_weights_by_pair_at_z`

**Source lines:** `251-284`

```python
def csf_weights_by_pair_at_zfield: Any, z: float
```

**Summary:** Compute the actual interpolated weights w(z) at absolute coordinate z, grouped by (S0_name, S1_name).

**Docstring details**

```text
Returns:
    { (name0, name1): w_at_z, ... }
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `z` | `positional or keyword` | `float` | `-` |

**Returns:** `Dict[PolyPair, float]`

**Raises visible in the code**

- `TypeError`
- `ValueError`

**Function/method calls visible in the code**

`field.section`, `list`, `enumerate`, `hasattr`, `TypeError`, `float`, `ValueError`, `zip`, `str`, `len`, `getattr`

## ACTION_RUNNERS contains only the actions that are actually executable in this runner.

### `register_action`

**Source lines:** `664-676`

```python
def register_actionspec: ActionSpec, runner: Any
```

**Summary:** Register an executable action runner.

**Docstring details**

```text
This is intentionally explicit (no side-effect registration) to keep imports simple
and to avoid circular import patterns during the modularization step.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `spec` | `positional or keyword` | `ActionSpec` | `-` |
| `runner` | `positional or keyword` | `Any` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`RuntimeError`

## Friendly YAML snippet helpers for errors

### `_make_snippet`

**Source lines:** `715-736`

```python
def _make_snippettext: str, line_no: Optional[int], col_no: Optional[int]
```

**Summary:** Create a short text snippet around (line, col) with line numbers.

**Docstring details**

```text
line_no and col_no are 1-based. If line_no is None, show first lines.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `line_no` | `positional or keyword` | `Optional[int]` | `-` |
| `col_no` | `positional or keyword` | `Optional[int]` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`text.splitlines`, `max`, `min`, `range`, `join`, `len`, `out.append`

### `_find_key_line`

**Source lines:** `739-748`

```python
def _find_key_linetext: str, key: str
```

**Summary:** Best-effort line lookup: find first line matching '<indent>key:'.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `key` | `positional or keyword` | `str` | `-` |

**Returns:** `Optional[int]`

**Function/method calls visible in the code**

`re.compile`, `enumerate`, `text.splitlines`, `rstrip`, `pat.match`, `re.escape`, `raw.split`

## Actions YAML parsing + corruption precheck

### `_precheck_corruption_actions`

**Source lines:** `755-855`

```python
def _precheck_corruption_actionstext: str
```

**Summary:** Heuristic "corruption" check BEFORE YAML parsing.

**Docstring details**

```text
The goal is to catch common user mistakes and provide a friendlier message
than the raw YAML parser.

Current checks:
  A) Missing ':' after a key (bare token) when next line is more indented
  A0) 'key value' on one line -> missing ':'
  B) Under a stations list, a numeric line without '-' (common YAML mistake)

Returns:
  List of ERROR issues if corruption is detected; empty list otherwise.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |

**Returns:** `List[Issue]`

**Returned dictionary keys visible in the code**

`snippet`, `location`, `line`, `column`

**Function/method calls visible in the code**

`text.splitlines`, `enumerate`, `_find_key_line`, `rstrip`, `startswith`, `re.match`, `range`, `base.strip`, `m_kv.group`, `issues.append`, `len`, `m_key.group`, `base.lstrip`, `CSFIssues.make`, `nxt.strip`, `raw.split`, `nxt.lstrip`, `split`, `_make_snippet`

## a numeric item without '-' and with indentation suggests broken list item

### `_parse_actions_yaml`

**Source lines:** `858-970`

```python
def _parse_actions_yamltext: str, filepath: str
```

**Summary:** Parse actions.yaml into a Python dict, with controlled error reporting.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `filepath` | `positional or keyword` | `str` | `-` |

**Returns:** `Tuple[Optional[Dict[str, Any]], List[Issue]]`

**Returned dictionary keys visible in the code**

`filepath`, `snippet`, `location`, `parser`, `line`, `column`

**Raises visible in the code**

- `yaml.constructor.ConstructorError`

**Function/method calls visible in the code**

`issues.extend`, `any`, `_precheck_corruption_actions`, `_UniqueKeyLoader.add_constructor`, `yaml.load`, `isinstance`, `issues.append`, `getattr`, `str`, `re.search`, `CSFIssues.make`, `loader.construct_object`, `m_dup.group`, `yaml.constructor.ConstructorError`, `int`, `_make_snippet`

## Full actions.yaml validation (structure + per-action params)

### `_validate_output_writable`

**Source lines:** `977-997`

```python
def _validate_output_writableout_str: str
```

**Summary:** Pre-check output path writability.

**Docstring details**

```text
Returns None if OK, else a friendly error string.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `out_str` | `positional or keyword` | `str` | `-` |

**Returns:** `Optional[str]`

**Function/method calls visible in the code**

`Path`, `p.exists`, `parent.exists`, `str`, `os.access`

### `_coerce_param_aliases`

**Source lines:** `1000-1021`

```python
def _coerce_param_aliasesaction: str, params: Dict[str, Any], issues: List[Issue]
```

**Summary:** Accept parameter aliases by moving alias values to the canonical name.

**Docstring details**

```text
Adds a WARNING when an alias is used.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `action` | `positional or keyword` | `str` | `-` |
| `params` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `Dict[str, Any]`

**Returned dictionary keys visible in the code**

`action`, `alias`, `canonical`

**Function/method calls visible in the code**

`dict`, `issues.append`, `out.pop`, `CSFIssues.make`

## Top-level functions

### `_validate_action_params`

**Source lines:** `1024-1139`

```python
def _validate_action_paramsaction: str, params: Dict[str, Any], filepath: str, text: str, line_hint: Optional[int], action_display_name: Optional[str]=None
```

**Summary:** Validate params mapping for one action using its ActionSpec.

**Docstring details**

```text
Unknown params are WARNING (not ERROR), to keep evolution flexible.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `action` | `positional or keyword` | `str` | `-` |
| `params` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `filepath` | `positional or keyword` | `str` | `-` |
| `text` | `positional or keyword` | `str` | `-` |
| `line_hint` | `positional or keyword` | `Optional[int]` | `-` |
| `action_display_name` | `positional or keyword` | `Optional[str]` | `None` |

**Returns:** `Tuple[List[Issue], Dict[str, Any]]`

**Returned dictionary keys visible in the code**

`value`, `action`, `param`, `filepath`, `snippet`

**Function/method calls visible in the code**

`_coerce_param_aliases`, `params2.keys`, `isinstance`, `strip`, `v.startswith`, `float`, `issues.append`, `_type_ok`, `type`, `CSFIssues.make`, `v.lstrip`, `_make_snippet`

### `_run_actions`

**Source lines:** `2555-2631`

```python
def _run_actionsfield: Any, actions_root: Dict[str, Any]
```

**Summary:** Execute actions sequentially.

**Docstring details**

```text
Returns:
  (ok, issues)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `actions_root` | `positional or keyword` | `Dict[str, Any]` | `-` |

**Returns:** `Tuple[bool, List[Issue]]`

**Returned dictionary keys visible in the code**

`action`, `details`

**Function/method calls visible in the code**

`_load_actions`, `bool`, `enumerate`, `_ensure_analysis_imports_or_error`, `actions_root.get`, `action.get`, `print`, `ACTION_RUNNERS.get`, `issues.append`, `runner`, `CSFIssues.make`, `len`, `str`

## Action-specific semantic checks

### `_validate_actions_doc`

**Source lines:** `1142-2194`

```python
def _validate_actions_docdoc: Dict[str, Any], text: str, filepath: str
```

**Summary:** FULL validation of actions.yaml.

**Docstring details**

```text
Returns (normalized_root, issues).
- normalized_root is the TOP_KEY mapping if validation passes enough to use it.
- issues includes warnings and errors.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `doc` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `text` | `positional or keyword` | `str` | `-` |
| `filepath` | `positional or keyword` | `str` | `-` |

**Returns:** `Tuple[Optional[Dict[str, Any]], List[Issue]]`

**Returned dictionary keys visible in the code**

`name`, `display_name`, `stations`, `output`, `params`, `filepath`, `snippet`, `duplicates`, `values`, `found_keys`, `found`, `missing_station`, `missing_stations_str`, `found_type`, `value`

**Function/method calls visible in the code**

`_load_actions`, `root.get`, `stations.items`, `any`, `enumerate`, `dict`, `issues.append`, `isinstance`, `next`, `payload.get`, `_validate_action_params`, `issues.extend`, `normalized_actions.append`, `_find_key_line`, `CSFIssues.make`, `len`, `zvals.append`, `iter`, `station_map.get`, `_validate_output_writable`, `sname.strip`, `type`, `float`, `set`, `item.keys`, `flat_output_list.extend`, `flat_output_list.append`, `endswith`, `it.keys`, `i.path.startswith`, `sorted`, `range`, `params_obj.get`, `outp.strip`, `str`, `_make_snippet`, `zvals.count`, `missing.append`, `text.splitlines`, `outp.lower`, `props_norm.append`, `tmp.append`, `list`, `sref.strip`, `bad.append`, `expr.strip`, `repr`, `join`, `line.startswith`, `pkey.strip`, `line.strip`, `ACTION_SPECS.keys`, `line.lstrip`

## Help printing

### `print_actions_help`

**Source lines:** `2201-2258`

```python
def print_actions_help
```

**Summary:** Docstring absent.

**Returns:** `None`

**Function/method calls visible in the code**

`_load_actions`, `print`, `sorted`, `ACTION_SPECS.keys`, `spec.description.replace`, `chr`, `join`

## Execution engine

### `_expand_station_names`

**Source lines:** `2265-2289`

```python
def _expand_station_namesstations_map: Dict[str, List[float]], station_names: List[str]
```

**Summary:** Expand a list of station set names into a single list of z-values, preserving order.

**Docstring details**

```text
User-friendly behavior:
- trims station names (handles accidental spaces)
- if a station is missing, raises a clear error listing available station names
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `stations_map` | `positional or keyword` | `Dict[str, List[float]]` | `-` |
| `station_names` | `positional or keyword` | `List[str]` | `-` |

**Returns:** `List[float]`

**Raises visible in the code**

- `ValueError`

**Function/method calls visible in the code**

`z_all.extend`, `sorted`, `ValueError`, `isinstance`, `raw_name.strip`, `str`, `missing.append`, `stations_map.keys`

### `_ensure_analysis_imports_or_error`

**Source lines:** `2293-2392`

```python
def _ensure_analysis_imports_or_errorissues: List[Issue], filepath: str, actions_list: Optional[List[Dict[str, Any]]]=None
```

**Summary:** Ensure required runtime imports exist.

**Docstring details**

```text
We check only what is needed for the requested actions.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `issues` | `positional or keyword` | `List[Issue]` | `-` |
| `filepath` | `positional or keyword` | `str` | `-` |
| `actions_list` | `positional or keyword` | `Optional[List[Dict[str, Any]]]` | `None` |

**Returns:** `bool`

**Returned dictionary keys visible in the code**

`filepath`

**Function/method calls visible in the code**

`set`, `bool`, `any`, `issues.append`, `a.get`, `isinstance`, `CSFIssues.make`, `requested.add`

## SAP2000 template-pack exporter (sap2000_v2.write_sap2000_template_pack)

### `_get_bool_param_strict`

**Source lines:** `2394-2415`

```python
def _get_bool_param_strictparams: Dict[str, Any], name: str, default: bool, *, path: str
```

**Summary:** Strict boolean parameter reader.

**Docstring details**

```text
Rationale
---------
Using Python's builtin `bool(x)` on non-bool values is dangerous:
  - bool("False") == True   (non-empty string is truthy)
For CSF Actions we want a non-ambiguous contract:
  - YAML booleans MUST be real booleans (true/false), not quoted strings.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `params` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `name` | `positional or keyword` | `str` | `-` |
| `default` | `positional or keyword` | `bool` | `-` |
| `path` | `keyword-only` | `str` | `-` |

**Returns:** `bool`

**Raises visible in the code**

- `TypeError`

**Function/method calls visible in the code**

`isinstance`, `TypeError`, `type`

### `_load_actions`

**Source lines:** `2418-2552`

```python
def _load_actions
```

**Summary:** Populate ACTION_RUNNERS with the set of implemented actions.

**Docstring details**

```text
Baseline step (low-impact):
- Actions are still defined in this file.
- We register them explicitly to drive a single dispatch path.

This is a no-op after the first call.
```

**Returns:** `None`

**Function/method calls visible in the code**

`register_section_selected_analysis`, `register_section_area_by_weight`, `register_volume`, `register_export_yaml`, `register_write_opensees_geometry`, `register_write_sap2000_geometry`, `register_weight_lab_zrelative`, `register_plot_volume_3d`, `register_plot_properties`, `register_plot_weight`, `register_plot_shear_weight`, `register_plot_section_2d`, `fn`

## Geometry loading

### `_load_geometry`

**Source lines:** `2638-2661`

```python
def _load_geometrygeometry_path: Path
```

**Summary:** Load CSF geometry using CSFReader.

**Docstring details**

```text
Always return CSFReader issues (warnings/errors) so they can be printed.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `geometry_path` | `positional or keyword` | `Path` | `-` |

**Returns:** `Tuple[Optional[Any], List[Issue]]`

**Returned dictionary keys visible in the code**

`details`

**Function/method calls visible in the code**

`list`, `read_file`, `getattr`, `str`, `CSFReader`, `CSFIssues.make`

## CLI main

### `main`

**Source lines:** `2668-3239`

```python
def mainargv: Optional[List[str]]=None
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `argv` | `positional or keyword` | `Optional[List[str]]` | `None` |

**Returns:** `int`

**Returned dictionary keys visible in the code**

`filepath`, `details`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `_load_geometry`, `isinstance`, `print`, `_parse_actions_yaml`, `_validate_actions_doc`, `bool`, `_run_actions`, `print_actions_help`, `Path`, `geometry_path.exists`, `actions_path.exists`, `actions_path.read_text`, `str`, `any`, `CSFIssues.format_report`, `hasattr`, `ContinuousSectionField`, `plt.figure`, `strip`, `_show_figs_sequentially`, `RuntimeError`, `CSFIssues.make`, `plt.get_fignums`, `plt.close`, `plt.ioff`, `_fig.get_label`, `PLOT_2D_VISIBILITY.get`, `keep_figs.append`, `PLOT_3D_VISIBILITY.get`, `plt.fignum_exists`, `plt.pause`, `_f.get_label`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
