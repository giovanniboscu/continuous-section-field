# API Reference - `csf_rough_validator.py`

This document covers the top-level classes and functions defined in `src/csf/io/csf_rough_validator.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/io/csf_rough_validator.py`
- Output file: `docs/API/io_csf_rough_validator_api_en.md`
- Top-level function definitions found: `13`.
- Top-level classes found: `2`.
- Duplicate function names found: `0`.

## Module docstring

```text
csf_rough_validator.py
======================

Early-stage validator for CSF geometry YAML files.

Runs *before* CSFReader to catch common authoring mistakes and provide
friendly, actionable error messages instead of raw Python tracebacks.

What it checks
--------------
- YAML syntax errors (indentation, missing ':', missing '-' in lists)
- Quoted numbers (e.g. "10.0" instead of 10.0)
- Missing or misspelled root key 'CSF:'
- Unknown keys at CSF level (e.g. 'wight_laws' → suggests 'weight_laws')
- Missing or empty 'z:', 'weight:', vertex coordinates
- weight_laws structure: missing '-', wrong comma separator, unknown polygon ids
- weight_laws formula: Python syntax errors (with caret pointer), unrecognised
  variable names (with case-insensitive suggestions)

What it does NOT check
----------------------
- Geometric validity (CCW order, self-intersections, nesting correctness)
- Physical consistency (weight signs, @cell/@wall rules)
- Anything that requires loading the full CSF model

These belong to deeper layers (CSFReader, ContinuousSectionField).

Usage as a library
------------------
    from csf.io.csf_rough_validator import validate_text

    ok, report = validate_text(text, source="my_section.yaml")
    if not ok:
        for line in report:
            print(line)

Usage as a script
-----------------
    python -m csf.io.csf_rough_validator my_section.yaml

Returns 0 (ok), 1 (validation failed), 2 (file not found).
```

## Public API index

- `ValidationMessage` - line 76
- `ValidationError` - line 90
- `def _is_strict_numberv: Any` - line 103
- `def _make_context_snippettext: str, line_no: int, col_no: Optional[int]=None` - line 117
- `def _find_first_root_key_in_texttext: str` - line 144
- `def _find_law_item_linestext: str, key: str` - line 163
- `def _find_weight_law_item_linestext: str` - line 206
- `def _safe_yaml_parsetext: str` - line 215
- `def _scan_quoted_numbers_in_texttext: str, excluded_lines: Optional[set]=None` - line 251
- `def _require_mappingd: Any, what: str` - line 284
- `def _require_listv: Any, what: str` - line 289
- `def _coerce_polygons_containerpolys: Any` - line 294
- `def _validate_csf_structuredoc: Dict[str, Any], weight_law_item_lines: Optional[Sequence[int]]=None` - line 324
- `def validate_texttext: str, source: str='<memory>'` - line 721
- `def csf_rough_validatorfilepath: str` - line 786

## API details

## Classes

### `ValidationMessage`

**Source lines:** `76-87`

**Decorators**

- `dataclass`

```python
class ValidationMessage
```

**Summary:** A single validation message (used by validate_text()).

**Docstring details**

```text
kind: "ERROR" or "WARN"
message: human-friendly message
line/col: optional location (1-based)
```

### `ValidationError`

**Source lines:** `90-96`

```python
class ValidationError(Exception)
```

**Summary:** Raised internally when the validator wants to stop early with a message.

**Methods visible in the code**

- `__init__` - line 92

#### Method details

##### `ValidationError.__init__`

**Source lines:** `92-96`

```python
def __init__self, message: str, line: Optional[int]=None, col: Optional[int]=None
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `message` | `positional or keyword` | `str` | `-` |
| `line` | `positional or keyword` | `Optional[int]` | `None` |
| `col` | `positional or keyword` | `Optional[int]` | `None` |

**Returns:** `None`

**Function/method calls visible in the code**

`__init__`, `super`

## Functions

## Helpers: numbers and snippets

### `_is_strict_number`

**Source lines:** `103-114`

```python
def _is_strict_numberv: Any
```

**Summary:** "Super safe" numeric check.

**Docstring details**

```text
Accept ONLY:
- int or float (real YAML numeric scalars)
- NOT bool (bool is a subclass of int in Python)
- finite values only (no NaN/Inf)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `v` | `positional or keyword` | `Any` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`math.isfinite`, `type`, `float`

### `_make_context_snippet`

**Source lines:** `117-135`

```python
def _make_context_snippettext: str, line_no: int, col_no: Optional[int]=None
```

**Summary:** Create a small, human-friendly snippet around a specific line.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `line_no` | `positional or keyword` | `int` | `-` |
| `col_no` | `positional or keyword` | `Optional[int]` | `None` |

**Returns:** `str`

**Function/method calls visible in the code**

`text.splitlines`, `max`, `min`, `range`, `join`, `len`, `out.append`

## root key "CSF:" is missing or replaced by another key.

### `_find_first_root_key_in_text`

**Source lines:** `144-161`

```python
def _find_first_root_key_in_texttext: str
```

**Summary:** Return the first top-level YAML key found in raw text, skipping blank lines and comments.

**Docstring details**

```text
Returns:
    (key, line_no) or (None, None)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |

**Returns:** `Tuple[Optional[str], Optional[int]]`

**Function/method calls visible in the code**

`enumerate`, `text.splitlines`, `raw.strip`, `_ROOT_KEY_RE.match`, `stripped.startswith`, `m.group`, `strip`

### `_find_law_item_lines`

**Source lines:** `163-203`

```python
def _find_law_item_linestext: str, key: str
```

**Summary:** Return the source line numbers for items inside CSF.<key>.

**Docstring details**

```text
This is a best-effort raw-text scan used only to enrich validator errors with
the original YAML line number. If the structure is unusual and the scan cannot
determine the positions reliably, it returns fewer items and the validator
falls back to the old message without a line number.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `key` | `positional or keyword` | `str` | `-` |

**Returns:** `List[int]`

**Function/method calls visible in the code**

`text.splitlines`, `enumerate`, `raw.strip`, `stripped.startswith`, `len`, `stripped.endswith`, `out.append`, `raw.lstrip`

## Top-level functions

### `_find_weight_law_item_lines`

**Source lines:** `206-207`

```python
def _find_weight_law_item_linestext: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |

**Returns:** `List[int]`

**Function/method calls visible in the code**

`_find_law_item_lines`

## Phase 1: YAML parsing

### `_safe_yaml_parse`

**Source lines:** `215-235`

```python
def _safe_yaml_parsetext: str
```

**Summary:** Parse YAML and raise ValidationError with line/col snippet if parsing fails.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |

**Returns:** `Dict[str, Any]`

**Raises visible in the code**

- `ValidationError`

**Function/method calls visible in the code**

`ValidationError`, `yaml.safe_load`, `isinstance`, `getattr`, `int`, `str`

## formulas in strings: "w0 + 0.5*(...)"  (because 0.5 is not quoted inside)

### `_scan_quoted_numbers_in_text`

**Source lines:** `251-277`

```python
def _scan_quoted_numbers_in_texttext: str, excluded_lines: Optional[set]=None
```

**Summary:** Scan the raw YAML text for quoted numbers.

**Docstring details**

```text
Returns a list of tuples: (line_no, col_no, matched_token)
where matched_token includes the quotes (e.g. '"10.0"').

Key rule to prevent false positives:
- If a line contains no quotes, it cannot be a quoted-number error.
- Lines in excluded_lines are skipped (e.g. weight_laws / shear_weight_laws items).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `excluded_lines` | `positional or keyword` | `Optional[set]` | `None` |

**Returns:** `List[Tuple[int, int, str]]`

**Function/method calls visible in the code**

`text.splitlines`, `enumerate`, `_QUOTED_NUMBER_RE.finditer`, `hits.append`, `m.start`, `m.end`

## Phase 3: rough CSF schema checks (PARSED DOC)

### `_require_mapping`

**Source lines:** `284-287`

```python
def _require_mappingd: Any, what: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `d` | `positional or keyword` | `Any` | `-` |
| `what` | `positional or keyword` | `str` | `-` |

**Returns:** `Dict[str, Any]`

**Raises visible in the code**

- `ValidationError`

**Function/method calls visible in the code**

`isinstance`, `ValidationError`, `type`

### `_require_list`

**Source lines:** `289-292`

```python
def _require_listv: Any, what: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `v` | `positional or keyword` | `Any` | `-` |
| `what` | `positional or keyword` | `str` | `-` |

**Returns:** `List[Any]`

**Raises visible in the code**

- `ValidationError`

**Function/method calls visible in the code**

`isinstance`, `ValidationError`, `type`

### `_coerce_polygons_container`

**Source lines:** `294-321`

```python
def _coerce_polygons_containerpolys: Any
```

**Summary:** Accept polygons as:

**Docstring details**

```text
- mapping: {lowerpart: {...}, upperpart: {...}}
  - list:    [{name: lowerpart, ...}, {name: upperpart, ...}]

Return a uniform list of (name, poly_dict).
For mapping mode: name is the key.
For list mode: name is poly_dict.get("name") (optional for this validator).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `polys` | `positional or keyword` | `Any` | `-` |

**Returns:** `List[Tuple[Optional[str], Dict[str, Any]]]`

**Raises visible in the code**

- `ValidationError`

**Function/method calls visible in the code**

`isinstance`, `ValidationError`, `polys.items`, `enumerate`, `out.append`, `item.get`, `str`, `type`

### `_validate_csf_structure`

**Source lines:** `324-711`

```python
def _validate_csf_structuredoc: Dict[str, Any], weight_law_item_lines: Optional[Sequence[int]]=None
```

**Summary:** Minimal schema validation for CSF.

**Docstring details**

```text
Raises ValidationError on the first detected issue (rough validator is allowed to be strict).
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `doc` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `weight_law_item_lines` | `positional or keyword` | `Optional[Sequence[int]]` | `None` |

**Returns:** `None`

**Raises visible in the code**

- `ValidationError`

**Function/method calls visible in the code**

`_require_mapping`, `set`, `sections.items`, `name.find`, `ValidationError`, `sorted`, `_coerce_polygons_container`, `enumerate`, `csf.keys`, `difflib.get_close_matches`, `_is_strict_number`, `_require_list`, `isinstance`, `item.split`, `lhs.strip`, `rhs.strip`, `re.compile`, `_STRING_RE.sub`, `item.strip`, `min`, `sec_name.startswith`, `poly_name.strip`, `poly_ids.add`, `len`, `lhs_stripped.split`, `_IDENT_RE.findall`, `s.split`, `next`, `compile`, `s.strip`, `_strip_wall_cell`, `swl.strip`, `iter`, `getattr`, `lhs.split`, `zip`, `n.strip`, `type`, `item.keys`, `int`, `uid.lower`, `suggestions.append`, `join`, `k.lower`, `sug_lines.append`

## Public API

### `validate_text`

**Source lines:** `721-783`

```python
def validate_texttext: str, source: str='<memory>'
```

**Summary:** Library entry point: validate YAML text and return (ok, report_lines).

**Docstring details**

```text
- ok == True  → safe to proceed to the next phase (formal CSFReader parsing)
- ok == False → report_lines contains human-friendly messages
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `source` | `positional or keyword` | `str` | `'<memory>'` |

**Returns:** `Tuple[bool, List[str]]`

**Function/method calls visible in the code**

`_find_first_root_key_in_text`, `_scan_quoted_numbers_in_text`, `_find_weight_law_item_lines`, `_safe_yaml_parse`, `report.append`, `set`, `_validate_csf_structure`, `_find_law_item_lines`, `_make_context_snippet`, `len`

## 3) rough CSF structure on parsed doc

### `csf_rough_validator`

**Source lines:** `786-810`

```python
def csf_rough_validatorfilepath: str
```

**Summary:** Script-friendly entry point.

**Docstring details**

```text
Returns:
  0 -> ok
  1 -> validation failed
  2 -> file missing/unreadable
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `filepath` | `positional or keyword` | `str` | `-` |

**Returns:** `int`

**Function/method calls visible in the code**

`Path`, `validate_text`, `p.exists`, `print`, `p.read_text`, `str`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
