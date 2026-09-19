# End-to-end execution flow

This diagram shows the complete execution path from the case YAML to the generated result files.

```mermaid
flowchart TD
    A["Case YAML<br/>cases/...yaml"] --> B["CLI<br/>csf-cuf"]
    B --> C["__main__.py<br/>run(case_yaml)"]

    C --> D["load_case()<br/>parse case YAML"]
    D --> D1["Case configuration<br/>problem path<br/>model path<br/>solver settings<br/>output settings"]

    D1 --> E["problem_api.load_problem()<br/>load problem adapter"]
    D1 --> F["CSF model loader<br/>load section/model provider"]

    E --> E1["Problem adapter<br/>problem-specific parsing<br/>physical problem definition"]
    F --> F1["Section provider<br/>continuous geometry<br/>material fields<br/>CSF sectional state"]

    D1 --> G["Solver engine"]
    E1 --> G
    F1 --> G

    G --> H["Build CUF basis"]
    G --> I["Build longitudinal discretization<br/>mesh / elements / nodes"]

    H --> J["Determine active basis sizes"]
    I --> J
    J --> K["Build GlobalDOFLayout"]

    K --> L["Problem adapter<br/>build_load_vector()"]
    E1 --> L
    H --> L
    I --> L

    K --> M["Stiffness assembly"]
    F1 --> M
    H --> M
    I --> M

    L --> N["Global load vector f"]
    M --> O["Global stiffness matrix K"]

    N --> P["Assembled system"]
    O --> P

    P --> Q["Build constraints / boundary conditions"]
    E1 --> Q

    Q --> R["Linear solver"]
    R --> S["Global solution vector u"]

    S --> T["Recovery / post-processing"]
    F1 --> T
    H --> T
    I --> T
    K --> T

    T --> U["Requested sampling<br/>displacements<br/>stresses<br/>tracked quantities"]
    U --> V["Output writer"]

    V --> W["response.txt"]
    V --> X["*.npz"]
    V --> Y["other configured outputs"]
```

## Key point

`GlobalDOFLayout` is built as soon as the discretization is fully known and is then shared by stiffness assembly, problem adapters, constraints, recovery, and any other numerical component that needs global DOF indexing.
