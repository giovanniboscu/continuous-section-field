# Load path and solver boundary

This diagram focuses on the architectural boundary introduced for problem loads.

```mermaid
flowchart TD
    A["Problem YAML"] --> B["Problem adapter"]

    B --> C["Parse physical load definition"]
    C --> D["Evaluate problem-specific physical law"]

    E["Generic CUF numerical services"] --> E1["Longitudinal mesh"]
    E --> E2["CUF basis"]
    E --> E3["GlobalDOFLayout"]
    E --> E4["Longitudinal integration / shape functions"]

    E1 --> F["Problem adapter numerical projection"]
    E2 --> F
    E3 --> F
    E4 --> F
    D --> F

    F --> G["build_load_vector()"]
    G --> H["Global load vector f"]

    I["CSF section provider"] --> J["Stiffness assembly"]
    E1 --> J
    E2 --> J
    E3 --> J

    J --> K["Global stiffness matrix K"]

    H --> L["Global algebraic system"]
    K --> L

    L --> M["Constraints"]
    M --> N["Linear solver"]
    N --> O["Global solution vector u"]

    O --> P["Recovery"]
    I --> P
    E1 --> P
    E2 --> P
    E3 --> P

    P --> Q["Output sampling"]
    Q --> R["Result writer"]
    R --> S["response.txt / *.npz / configured outputs"]
```

## Dependency direction

Correct dependency:

```text
problem adapter
    -> mesh
    -> basis
    -> GlobalDOFLayout
    -> generic integration / shape-function services
    -> global load vector
```

Forbidden dependency:

```text
CUF core
    -> PointLoad
    -> DistributedLoad
    -> TorqueLoad
    -> SurfaceTractionLoad
    -> any future physical load category
```

Adding a new physical load type must therefore require changes only in the problem-adapter layer, not in stiffness assembly or the numerical core.
