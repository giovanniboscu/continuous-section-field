# External longitudinal basis

The existing `longitudinal.basis` key accepts either a built-in registered name
or a Python file path.

Built-in basis:

```yaml
longitudinal:
  method: finite_element
  elements: 2
  basis: lagrange
  order: 6
```

External basis:

```yaml
longitudinal:
  method: finite_element
  elements: 2
  basis: ./custom_lagrange.py
  order: 6
```

Relative file paths are resolved from the directory containing the case YAML.
A bare name such as `lagrange` keeps the existing built-in registry behavior.
A `.py` suffix, a path separator, or an explicit `Path` selects an external
file.

The external file uses the same plugin API as a built-in longitudinal basis:

```python
from csf.cuf.core.longitudinal_basis_plugins import (
    LongitudinalBasisPlugin,
    register_longitudinal_basis_plugin,
)

register_longitudinal_basis_plugin(
    LongitudinalBasisPlugin(
        name="my_basis",
        builder=my_builder,
    )
)
```

The file must register exactly one `LongitudinalBasisPlugin`. Its registration
is isolated from the built-in registry, so an external plugin may use the same
plugin name as a built-in one without replacing it globally.

The current `finite_element` discretizer still requires the resulting basis to
implement `NodalC0LongitudinalBasis`. This change does not add non-nodal
topology, extra continuity constraints, or a different global assembly.

`custom_lagrange.py` is intentionally numerically equivalent to the built-in
`lagrange` basis. It demonstrates external loading without changing the shape
functions.

External Python files are executed as ordinary Python code. Only trusted files
should be loaded.
