# API Reference - `csf_issues.py`

This document covers the top-level classes and functions defined in `src/csf/io/csf_issues.py`. Imported symbols are not documented as standalone APIs here.

## Module summary

- Source file: `src/csf/io/csf_issues.py`
- Output file: `docs/API/io_csf_issues_api_en.md`
- Top-level function definitions found: `0`.
- Top-level classes found: `4`.
- Duplicate function names found: `0`.

## Public API index

- `Severity` - line 8
- `Issue` - line 15
- `IssueSpec` - line 168
- `CSFIssues` - line 175

## API details

## Classes

### `Severity`

**Source lines:** `8-11`

```python
class Severity(str, Enum)
```

**Summary:** Docstring absent.

### `Issue`

**Source lines:** `15-164`

**Decorators**

- `dataclass(frozen=True)`

```python
class Issue
```

**Summary:** Docstring absent.

**Methods visible in the code**

- `to_text` - line 24
- `to_text2` - line 104

#### Method details

##### `Issue.to_text`

**Source lines:** `24-84`

```python
def to_textself
```

**Summary:** Render an Issue to human-readable text.

**Docstring details**

```text
Printing rules (user-facing):
- If the message already starts with "[ERROR]" / "[WARNING]" / "[INFO]", strip it
to avoid duplicate severity tags.
- If context is a dict and contains multi-line fields (e.g. "snippet",
"validator_output", "parser"), print those fields as real multi-line blocks.
Do NOT print them via repr() because repr escapes newlines ("\n") and becomes unreadable.
- Warnings are allowed to omit snippets; errors typically include them upstream.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`join`, `lines.append`, `isinstance`, `msg.startswith`, `lstrip`, `ctx.get`, `blocks.append`, `ctx.items`, `title`, `v.replace`, `len`, `k.replace`

##### `Issue.to_text2`

**Source lines:** `104-164`

```python
def to_text2self
```

**Summary:** Render an Issue to human-readable text.

**Docstring details**

```text
Printing rules (user-facing):
        - If the message already starts with "[ERROR]" / "[WARNING]" / "[INFO]", strip it
          to avoid duplicate severity tags.
        - If context is a dict and contains multi-line fields (e.g. "snippet",
          "validator_output", "parser"), print those fields as real multi-line blocks.
          Do NOT print them via repr() because repr escapes newlines (
) and becomes unreadable.
        - Warnings are allowed to omit snippets; errors typically include them upstream.
```

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `self` | `positional or keyword` | `not annotated` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`join`, `lines.append`, `isinstance`, `msg.startswith`, `lstrip`, `ctx.get`, `blocks.append`, `ctx.items`, `title`, `v.replace`, `len`, `k.replace`

### `IssueSpec`

**Source lines:** `168-172`

**Decorators**

- `dataclass(frozen=True)`

```python
class IssueSpec
```

**Summary:** Docstring absent.

### `CSFIssues`

**Source lines:** `175-506`

```python
class CSFIssues
```

**Summary:** Central catalog for controlled errors/warnings produced by CSF YAML reading/validation.

**Docstring details**

```text
Design goals:
  - Stable codes (testable).
  - English messages.
  - Path-aware issues (precise localization).
  - Easy to extend: add a new IssueSpec in SPECS.
```

**Methods visible in the code**

- `spec` - line 460
- `make` - line 472
- `summarize` - line 493
- `format_report` - line 500

#### Method details

##### `CSFIssues.spec`

**Source lines:** `460-469`

**Decorators**

- `classmethod`

```python
def speccls, code: str
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cls` | `positional or keyword` | `not annotated` | `-` |
| `code` | `positional or keyword` | `str` | `-` |

**Returns:** `IssueSpec`

**Function/method calls visible in the code**

`IssueSpec`

##### `CSFIssues.make`

**Source lines:** `472-490`

**Decorators**

- `classmethod`

```python
def makecls, code: str, path: str, *, message: Optional[str]=None, hint: Optional[str]=None, context: Optional[Any]=None, severity: Optional[Severity]=None
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `cls` | `positional or keyword` | `not annotated` | `-` |
| `code` | `positional or keyword` | `str` | `-` |
| `path` | `positional or keyword` | `str` | `-` |
| `message` | `keyword-only` | `Optional[str]` | `None` |
| `hint` | `keyword-only` | `Optional[str]` | `None` |
| `context` | `keyword-only` | `Optional[Any]` | `None` |
| `severity` | `keyword-only` | `Optional[Severity]` | `None` |

**Returns:** `Issue`

**Function/method calls visible in the code**

`cls.spec`, `Issue`

##### `CSFIssues.summarize`

**Source lines:** `493-497`

**Decorators**

- `staticmethod`

```python
def summarizeissues: Iterable[Issue]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `issues` | `positional or keyword` | `Iterable[Issue]` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`list`, `sum`

##### `CSFIssues.format_report`

**Source lines:** `500-506`

**Decorators**

- `staticmethod`

```python
def format_reportissues: Iterable[Issue]
```

**Summary:** Docstring absent.

**Parameters**

| Name | Kind | Type | Default |
|---|---|---|---|
| `issues` | `positional or keyword` | `Iterable[Issue]` | `-` |

**Returns:** `str`

**Function/method calls visible in the code**

`list`, `blocks.append`, `join`, `iss.to_text`, `CSFIssues.summarize`

# Notes from the source structure

- The generator reads the Python source through `ast` and does not import the package.
- `Source lines` are derived from Python AST line numbers.
- `Returned dictionary keys visible in the code` are literal string keys found in dictionary expressions inside the function body.
- `Raises visible in the code` lists exception names from explicit `raise` statements.
- `Function/method calls visible in the code` is a static list of call expressions found in the function body.
