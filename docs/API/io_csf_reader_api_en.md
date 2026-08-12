# API Reference - `csf_reader.py`

This document covers the top-level classes and functions defined in `src/csf/io/csf_reader.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/io/csf_reader.py`
- Output file: `docs/API/io_csf_reader_api_en.md`
- Top-level function definitions found: `1`.
- Top-level classes found: `4`.
- Duplicate function names found: `0`.

## Module docstring

```text
csf_reader.py
=============

User-facing YAML reader + validator for CSF (Continuous Section Field).

This module is intentionally separated from the core CSF geometry/interpolation engine
(ContinuousSectionField) so that:

- The CSF core stays focused on geometry + discretization logic.
- I/O concerns (file parsing, schema validation, user-friendly error reporting) are isolated.
- The reader can evolve independently (e.g., support CLI workflows, action files, etc.).

Design principles
-----------------
1) No raw Python tracebacks for end users
   - All failures become controlled Issues (ERROR/WARNING) using CSFIssues catalog.

2) Two-phase validation
   A) "Corruption" precheck on raw YAML text (before parsing)
      - Detect frequent authoring mistakes that are otherwise hard to understand.
      - Report key name + line number when possible.
      - Stop before yaml.safe_load if corruption is detected.
   B) Formal validation on parsed YAML object
      - Structural checks (required keys, types).
      - Semantic checks (z ordering, polygon homology, etc.).

3) Object construction only after passing checks
   - If the file passes checks, instantiate:
       field = ContinuousSectionField(section0=s0, section1=s1)

4) Input flexibility (important)
   - YAML output (writer): polygons as LIST is recommended (explicit order).
   - YAML input (reader): accept BOTH
       a) polygons as LIST
       b) polygons as MAP (dict)
     If polygons is a map, it is coerced to a list preserving insertion order, and the
     reader emits ONE warning per file.

Expected YAML (minimal)
----------------------
CSF:
  sections:
    S0:
      z: 0.0
      polygons:
        - name: lowerpart
          weight: 1.0
          vertices:
            - [-0.15, -0.6]
            - [ 0.15, -0.6]
            - [ 0.15,  0.0]
            - [-0.15,  0.0]
    S1:
      z: 10.0
      polygons:
        - name: lowerpart
          weight: 1.0
          vertices:
            - [-0.15, -0.1]
            - [ 0.15, -0.1]
            - [ 0.15,  0.0]
            - [-0.15,  0.0]

Optional:
  weight_laws:
    - "lowerpart,lowerpart: w0 + (w1-w0)*(z/L)"
    - "upperpart,upperpart: w0 + (w1-w0)*(z/L)"

Notes about ordering
-------------------
CSF uses index-based homology for polygons/vertices across sections:
- polygon i in S0 corresponds to polygon i in S1
- vertex j in polygon i corresponds to vertex j in polygon i

Therefore, ordering of polygons is meaningful.
That is why YAML output should prefer list form.
For YAML input, if polygons is a dict, we preserve insertion order as defined in the file.

Dependencies
------------
- PyYAML is required to parse YAML (yaml.safe_load).
- CSFIssues comes from csf.io.csf_issues and must define the codes used below.
```

## Public API index

- `_NoDuplicateKeyLoader` - line 112
- `ReaderConfig` - line 135
- `ReadResult` - line 162
- `CSFReader` - line 181
- `def _construct_mapping_no_duplicatesloader, node, deep=False` - line 115

## API details

## Classes

### `_NoDuplicateKeyLoader`

**Source lines:** `112-113`

```python
class _NoDuplicateKeyLoader(SafeLoader)
```

**Summary:** Docstring absent.

### `ReaderConfig`

**Source lines:** `135-158`

**Decorators**

- `dataclass`

```python
class ReaderConfig
```

**Summary:** Reader behavior configuration.

**Docstring details**

```text
Keep this conservative: more permissive inputs can be accepted, but errors must stay clear.
```

### `ReadResult`

**Source lines:** `162-174`

**Decorators**

- `dataclass`

```python
class ReadResult
```

**Summary:** Output of CSFReader.

**Docstring details**

```text
- field: ContinuousSectionField instance when ok
- issues: list of Issue
```

**Methods visible in the code**

- `ok` - line 172

#### Method details

##### `ReadResult.ok`

**Source lines:** `172-174`

**Decorators**

- `property`

```python
def okself
```

**Summary:** True if no ERROR issues exist.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`all`

### `CSFReader`

**Source lines:** `181-1243`

```python
class CSFReader
```

**Summary:** CSF YAML reader, validator, and builder.

**Docstring details**

```text
Typical usage:

    from csf.io.csf_reader import CSFReader
    from csf.io.csf_issues import CSFIssues

    res = CSFReader().read_file("case.yaml")
    if not res.ok:
        print(CSFIssues.format_report(res.issues))
    else:
        field = res.field
```

**Methods visible in the code**

- `__init__` - line 197
- `read_file` - line 212
- `read_text` - line 348
- `_parse_yaml` - line 402
- `_make_yaml_parse_issue` - line 437
- `_make_snippet` - line 487
- `_precheck_corruption` - line 513
- `_extract_csf_root` - line 723
- `_extract_sections` - line 743
- `_parse_section` - line 777
- `_parse_polygon` - line 845
- `_parse_vertex` - line 898
- `_validate_domain_order` - line 920
- `_validate_index_homology` - line 932
- `_build_field` - line 973
- `_validate_and_apply_shear_weight_laws` - line 992
- `_validate_and_apply_weight_laws` - line 1099
- `_is_number` - line 1197
- `_is_finite_number` - line 1201
- `_paren_balance_ok` - line 1207
- `_strip_model_tags` - line 1222
- `_polygon_index_by_name` - line 1233

#### Method details

##### `CSFReader.__init__`

**Source lines:** `197-204`

```python
def __init__self, config: Optional[ReaderConfig]=None
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `config` | `positional or keyword` | `Optional[ReaderConfig]` | `None` |

**Returns:** `None`

**Function/method calls visible in the code**

`getattr`, `ReaderConfig`

##### `CSFReader.read_file`

**Source lines:** `212-346`

```python
def read_fileself, filepath: str
```

**Summary:** Read CSF YAML from a file path and return a controlled ReadResult.

**Docstring details**

```text
Goals of this function
----------------------
1) Reset any per-read state (e.g. warnings collected during parsing).
2) Run an early "rough" validator (csf_rough_validator) to catch common authoring errors
with friendly messages.
- IMPORTANT: csf_rough_validator currently prints diagnostics to console.
    Here we capture that output so we can:
    a) avoid duplicate/confusing console messages
    b) attach the real reason to the Issue context
    c) generate a coherent hint (not always "quoted numbers")
3) Read the file text (UTF-8) and then proceed with the full reader pipeline via read_text().
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `filepath` | `positional or keyword` | `str` | `-` |

**Returns:** `ReadResult`

**Returned dictionary keys visible in the code**

`filepath`, `validator_output`

**Raises visible in the code**

- `FileNotFoundError`

**Function/method calls visible in the code**

`io.StringIO`, `Path`, `strip`, `self.read_text`, `p.is_file`, `FileNotFoundError`, `redirect_stdout`, `redirect_stderr`, `csf_rough_validator`, `issues.append`, `ReadResult`, `validator_out.splitlines`, `validator_out.lower`, `buf.getvalue`, `CSFIssues.make`, `line.startswith`, `open`, `f.read`, `line.strip`, `p.resolve`, `str`

##### `CSFReader.read_text`

**Source lines:** `348-396`

```python
def read_textself, text: str
```

**Summary:** Read CSF YAML from a string.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `text` | `positional or keyword` | `str` | `-` |

**Returns:** `ReadResult`

**Function/method calls visible in the code**

`self._parse_yaml`, `self._extract_csf_root`, `self._extract_sections`, `self._parse_section`, `self._validate_domain_order`, `self._validate_index_homology`, `any`, `self._build_field`, `ReadResult`, `self._validate_and_apply_weight_laws`, `self._validate_and_apply_shear_weight_laws`

##### `CSFReader._parse_yaml`

**Source lines:** `402-435`

```python
def _parse_yamlself, text: str, issues: List[Issue]
```

**Summary:** Parse YAML with controlled error reporting.

**Docstring details**

```text
If corruption precheck finds ERROR(s), stop before calling yaml.safe_load.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `text` | `positional or keyword` | `str` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `Optional[Any]`

**Function/method calls visible in the code**

`self._precheck_corruption`, `any`, `issues.append`, `yaml.load`, `isinstance`, `CSFIssues.make`, `self._make_yaml_parse_issue`, `type`

##### `CSFReader._make_yaml_parse_issue`

**Source lines:** `437-484`

```python
def _make_yaml_parse_issueself, text: str, exc: Exception
```

**Summary:** Convert a PyYAML parsing exception into a user-friendly Issue.

**Docstring details**

```text
The goal is to tell the user:
- line number
- column (if available)
- a small snippet around the problem
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `text` | `positional or keyword` | `str` | `-` |
| `exc` | `positional or keyword` | `Exception` | `-` |

**Returns:** `Issue`

**Returned dictionary keys visible in the code**

`location`, `snippet`, `line`, `column`

**Function/method calls visible in the code**

`str`, `getattr`, `self._make_snippet`, `CSFIssues.make`, `re.search`, `int`, `m.group`

##### `CSFReader._make_snippet`

**Source lines:** `487-511`

**Decorators**

- `staticmethod`

```python
def _make_snippettext: str, line_no: Optional[int], col_no: Optional[int]
```

**Summary:** Create a small snippet of lines around the reported error line.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `text` | `positional or keyword` | `str` | `-` |
| `line_no` | `positional or keyword` | `Optional[int]` | `-` |
| `col_no` | `positional or keyword` | `Optional[int]` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`text.splitlines`, `max`, `min`, `range`, `join`, `len`, `out.append`

##### `CSFReader._precheck_corruption`

**Source lines:** `513-717`

```python
def _precheck_corruptionself, text: str, issues: List[Issue]
```

**Summary:** Corruption checks on the raw YAML text.

**Docstring details**

```text
This is intentionally heuristic: it does NOT try to parse YAML.
It targets common CSF authoring mistakes that otherwise produce confusing
YAML parser errors.

Checks implemented:
A0) Missing ':' between key and value  (e.g. "z 10.0")
A1) Missing ':' after a bare key followed by indented children (e.g. "S0" then block)
C ) Missing polygon header key under polygons: mapping (scans entire block)
B ) Missing '-' for list items under vertices:
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `text` | `positional or keyword` | `str` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`line`, `key`, `text`, `next_line`, `next_text`

**Function/method calls visible in the code**

`text.splitlines`, `max`, `enumerate`, `int`, `issues.append`, `rstrip`, `startswith`, `re.match`, `m_key.group`, `len`, `line.strip`, `m_kv.group`, `_add`, `cand_raw.rstrip`, `m.group`, `line.lstrip`, `CSFIssues.make`, `cand.strip`, `first_child.lstrip`, `line_k.strip`, `child.strip`, `raw.split`, `cand.lstrip`, `line_k.lstrip`, `mkey.group`, `child.lstrip`, `cand_raw.split`, `raw_k.split`, `child_raw.split`, `raw.rstrip`, `child_raw.rstrip`, `raw_k.rstrip`

##### `CSFReader._extract_csf_root`

**Source lines:** `723-741`

```python
def _extract_csf_rootself, doc: Dict[str, Any], issues: List[Issue]
```

**Summary:** Extract the CSF root mapping.

**Docstring details**

```text
Default behavior: require top-level key (self._top_key, usually "CSF").
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `doc` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `Optional[Dict[str, Any]]`

**Function/method calls visible in the code**

`issues.append`, `isinstance`, `CSFIssues.make`, `list`, `doc.keys`, `type`

##### `CSFReader._extract_sections`

**Source lines:** `743-775`

```python
def _extract_sectionsself, csf_root: Dict[str, Any], issues: List[Issue]
```

**Summary:** Validate and return raw section mappings for S0 and S1.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `csf_root` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]`

**Returned dictionary keys visible in the code**

`S0`, `S1`

**Function/method calls visible in the code**

`issues.append`, `isinstance`, `CSFIssues.make`, `list`, `type`, `sections.keys`

##### `CSFReader._parse_section`

**Source lines:** `777-843`

```python
def _parse_sectionself, sec_name: str, sec_data: Dict[str, Any], issues: List[Issue]
```

**Summary:** Parse a section mapping into a core Section object.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `sec_name` | `positional or keyword` | `str` | `-` |
| `sec_data` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `Optional[Any]`

**Returned dictionary keys visible in the code**

`section`, `keys`

**Function/method calls visible in the code**

`set`, `enumerate`, `any`, `Section`, `issues.append`, `self._is_finite_number`, `isinstance`, `self._polygons_map_coercions.append`, `polys.items`, `len`, `self._parse_polygon`, `seen_names.add`, `parsed_polys.append`, `CSFIssues.make`, `dict`, `vv.setdefault`, `poly_list.append`, `tuple`, `float`, `list`, `str`, `polys.keys`, `type`

##### `CSFReader._parse_polygon`

**Source lines:** `845-896`

```python
def _parse_polygonself, p: Any, p_path: str, issues: List[Issue]
```

**Summary:** Parse polygon mapping into Polygon object.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `p` | `positional or keyword` | `Any` | `-` |
| `p_path` | `positional or keyword` | `str` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `Optional[Any]`

**Function/method calls visible in the code**

`name.strip`, `enumerate`, `any`, `Polygon`, `isinstance`, `issues.append`, `self._is_number`, `self._is_finite_number`, `len`, `self._parse_vertex`, `CSFIssues.make`, `parsed_pts.append`, `tuple`, `float`, `type`

##### `CSFReader._parse_vertex`

**Source lines:** `898-914`

```python
def _parse_vertexself, v: Any, v_path: str, issues: List[Issue]
```

**Summary:** Parse one vertex: expected [x, y], both finite numbers.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `v` | `positional or keyword` | `Any` | `-` |
| `v_path` | `positional or keyword` | `str` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `Optional[Any]`

**Function/method calls visible in the code**

`Pt`, `issues.append`, `float`, `isinstance`, `len`, `CSFIssues.make`, `self._is_number`, `self._is_finite_number`

##### `CSFReader._validate_domain_order`

**Source lines:** `920-930`

```python
def _validate_domain_orderself, s0: Any, s1: Any, issues: List[Issue]
```

**Summary:** Enforce the CSF model rule: field domain is exactly [S0.z, S1.z], and S0.z < S1.z.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `s0` | `positional or keyword` | `Any` | `-` |
| `s1` | `positional or keyword` | `Any` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `None`

**Function/method calls visible in the code**

`float`, `issues.append`, `CSFIssues.make`

##### `CSFReader._validate_index_homology`

**Source lines:** `932-967`

```python
def _validate_index_homologyself, s0: Any, s1: Any, issues: List[Issue]
```

**Summary:** Index-based homology checks:

**Docstring details**

```text
- same number of polygons
- per index i: same number of vertices
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `s0` | `positional or keyword` | `Any` | `-` |
| `s1` | `positional or keyword` | `Any` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`S0`, `S1`, `index`, `S0_name`, `S1_name`, `S0_vertices`, `S1_vertices`

**Function/method calls visible in the code**

`list`, `enumerate`, `len`, `issues.append`, `zip`, `CSFIssues.make`

##### `CSFReader._build_field`

**Source lines:** `973-989`

```python
def _build_fieldself, s0: Any, s1: Any, issues: List[Issue]
```

**Summary:** Instantiate ContinuousSectionField with controlled error reporting.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `s0` | `positional or keyword` | `Any` | `-` |
| `s1` | `positional or keyword` | `Any` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `Optional[Any]`

**Function/method calls visible in the code**

`ContinuousSectionField`, `issues.append`, `CSFIssues.make`, `str`

##### `CSFReader._validate_and_apply_shear_weight_laws`

**Source lines:** `992-1092`

```python
def _validate_and_apply_shear_weight_lawsself, field: Any, csf_root: Dict[str, Any], issues: List[Issue]
```

**Summary:** Validate and apply shear weight_laws.

**Docstring details**

```text
Rules:
- weight_laws must be a list of strings
- each item: "name0,name1: expr"
- referenced polygon names must exist in S0 and S1
- names must refer to polygons with the SAME index in S0 and S1 (index homology)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `field` | `positional or keyword` | `Any` | `-` |
| `csf_root` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`S0_name`, `S1_name`, `S0_index`, `S1_index`

**Function/method calls visible in the code**

`enumerate`, `any`, `isinstance`, `issues.append`, `item.strip`, `s.split`, `left.strip`, `expr.strip`, `self._polygon_index_by_name`, `laws_out.append`, `field.set_shear_weight_laws`, `CSFIssues.make`, `self._paren_balance_ok`, `t.strip`, `left.split`, `type`, `str`

##### `CSFReader._validate_and_apply_weight_laws`

**Source lines:** `1099-1190`

```python
def _validate_and_apply_weight_lawsself, field: Any, csf_root: Dict[str, Any], issues: List[Issue]
```

**Summary:** Validate and apply weight_laws.

**Docstring details**

```text
Rules:
- weight_laws must be a list of strings
- each item: "name0,name1: expr"
- referenced polygon names must exist in S0 and S1
- names must refer to polygons with the SAME index in S0 and S1 (index homology)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |
| `field` | `positional or keyword` | `Any` | `-` |
| `csf_root` | `positional or keyword` | `Dict[str, Any]` | `-` |
| `issues` | `positional or keyword` | `List[Issue]` | `-` |

**Returns:** `None`

**Returned dictionary keys visible in the code**

`S0_name`, `S1_name`, `S0_index`, `S1_index`

**Function/method calls visible in the code**

`enumerate`, `any`, `isinstance`, `issues.append`, `item.strip`, `s.split`, `left.strip`, `expr.strip`, `self._polygon_index_by_name`, `laws_out.append`, `field.set_weight_laws`, `CSFIssues.make`, `self._paren_balance_ok`, `t.strip`, `left.split`, `type`, `str`

##### `CSFReader._is_number`

**Source lines:** `1197-1198`

**Decorators**

- `staticmethod`

```python
def _is_numberx: Any
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `x` | `positional or keyword` | `Any` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`isinstance`

##### `CSFReader._is_finite_number`

**Source lines:** `1201-1204`

**Decorators**

- `staticmethod`

```python
def _is_finite_numberx: Any
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `x` | `positional or keyword` | `Any` | `-` |

**Returns:** `bool`

**Function/method calls visible in the code**

`math.isfinite`, `isinstance`, `float`

##### `CSFReader._paren_balance_ok`

**Source lines:** `1207-1220`

**Decorators**

- `staticmethod`

```python
def _paren_balance_okexpr: str
```

**Summary:** Lightweight syntax sanity check (not an evaluator):

**Docstring details**

```text
ensures parentheses are balanced.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `expr` | `positional or keyword` | `str` | `-` |

**Returns:** `bool`

##### `CSFReader._strip_model_tags`

**Source lines:** `1222-1229`

**Decorators**

- `staticmethod`

```python
def _strip_model_tagsname: str
```

**Summary:** Normalize polygon name for matching:

**Docstring details**

```text
- trim spaces
- remove everything starting from @cell, @wall, or @closed (case-insensitive)
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `name` | `positional or keyword` | `str` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`strip`, `str`, `re.sub`

##### `CSFReader._polygon_index_by_name`

**Source lines:** `1233-1243`

**Decorators**

- `staticmethod`

```python
def _polygon_index_by_namesection: Any, name: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `section` | `positional or keyword` | `Any` | `-` |
| `name` | `positional or keyword` | `str` | `-` |

**Returns:** `Optional[int]`

**Function/method calls visible in the code**

`enumerate`, `CSFReader._strip_model_tags`

## Functions

## Public result / configuration

### `_construct_mapping_no_duplicates`

**Source lines:** `115-127`

```python
def _construct_mapping_no_duplicatesloader, node, deep=False
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `loader` | `positional or keyword` | `not annotated` | `-` |
| `node` | `positional or keyword` | `not annotated` | `-` |
| `deep` | `positional or keyword` | `not annotated` | `False` |

**Returns:** `not annotated`

**Raises visible in the code**

- `ConstructorError`

**Function/method calls visible in the code**

`loader.construct_object`, `ConstructorError`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
