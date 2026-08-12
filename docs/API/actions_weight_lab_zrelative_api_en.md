# API Reference - `weight_lab_zrelative.py`

This document covers the top-level classes and functions defined in `src/csf/actions/weight_lab_zrelative.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/actions/weight_lab_zrelative.py`
- Output file: `docs/API/actions_weight_lab_zrelative_api_en.md`
- Top-level function definitions found: `3`.
- Top-level classes found: `0`.
- Duplicate function names found: `0`.

## Module docstring

```text
CSF Action Module: weight_lab_zrelative
======================================

Text-only inspector action for verifying custom weight-law expressions at user-provided
*relative* z stations.

Design goals (low-impact)
-------------------------
- No side-effect registration at import time (avoids import cycles).
- Explicit registration via register(register_action, ...).
- Keep logic as-is from the monolithic CSFActions implementation.
- No matplotlib usage (does not affect deferred-show logic).
- All comments are in English (per project convention).
```

## Public API index

- `def _build_specActionSpec: Any, ParamSpec: Any` - line 29
- `def _runfield: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool=False, expand_station_names: Any, safe_evaluate_weight_zrelative: Any` - line 62
- `def registerregister_action: Any, *, ActionSpec: Any, ParamSpec: Any, expand_station_names: Any, safe_evaluate_weight_zrelative: Any` - line 230

## API details

## Functions

## Action SPEC (help/validation)

### `_build_spec`

**Source lines:** `29-56`

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

`ActionSpec`

## Runner (logic copied from the monolithic implementation; minimal adaptations)

### `_run`

**Source lines:** `62-224`

```python
def _runfield: Any, stations_map: Dict[str, List[float]], action: Dict[str, Any], *, debug_flag: bool=False, expand_station_names: Any, safe_evaluate_weight_zrelative: Any
```

**Summary:** Action: weight_lab_zrelative

**Docstring details**

```text
This action is *text-only*. It is meant as a "lab/inspector" to help users
verify that a weight law formula W(z) behaves as expected.

Why this exists
---------------
In CSF, polygon weights can be controlled by user-defined laws. A "law" is
an expression that uses:
  - w0, w1 : endpoint weights (from p0.weight, p1.weight)
  - z      : relative coordinate along the element
  - L      : total element length
  - np     : numpy (np.sin, np.cos, np.pi, ...)

The actual evaluation is delegated to:
    safe_evaluate_weight_zrelative(formula, p0, p1, l_total=L, z0, z1, z=z, print=True)

YAML contract (normalized by validator)
--------------------------------------
- stations: REQUIRED (station values are interpreted as *relative* z)
- weith_law: REQUIRED list[str] of expressions (outside params)
- output: optional, default ['stdout'] if the YAML key is missing

Output semantics
----------------
- stdout in output => print the inspector output to the terminal
- file paths in output => write the same inspector text to those files
- if output does NOT include stdout => file-only (no terminal output)

NOTE
----
This action produces NO matplotlib figures and does not affect the deferred
plotting mechanism.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `field` | `positional or keyword` | `Any` | `-` |
| `stations_map` | `positional or keyword` | `Dict[str, List[float]]` | `-` |
| `action` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `debug_flag` | `keyword-only` | `bool` | `False` |
| `expand_station_names` | `keyword-only` | `Any` | `-` |
| `safe_evaluate_weight_zrelative` | `keyword-only` | `Any` | `-` |

**Returns:** `None`

**Raises visible in the code**

- `RuntimeError`

**Function/method calls visible in the code**

`action.get`, `expand_station_names`, `RuntimeError`, `list`, `len`, `io.StringIO`, `redirect_stdout`, `print`, `enumerate`, `buf.getvalue`, `isinstance`, `float`, `_Tee`, `nullcontext`, `Path`, `st.write`, `hasattr`, `p.parent.exists`, `open`, `f.write`, `st.flush`, `zip`, `getattr`, `safe_evaluate_weight_zrelative`

## Explicit registration hook (no side effects)

### `register`

**Source lines:** `230-254`

```python
def registerregister_action: Any, *, ActionSpec: Any, ParamSpec: Any, expand_station_names: Any, safe_evaluate_weight_zrelative: Any
```

**Summary:** Register this action into the shared CSFActions registry.

**Docstring details**

```text
All dependencies are injected explicitly from CSFActions.py to avoid import cycles.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `register_action` | `positional or keyword` | `Any` | `-` |
| `ActionSpec` | `keyword-only` | `Any` | `-` |
| `ParamSpec` | `keyword-only` | `Any` | `-` |
| `expand_station_names` | `keyword-only` | `Any` | `-` |
| `safe_evaluate_weight_zrelative` | `keyword-only` | `Any` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`_build_spec`, `register_action`, `_run`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
