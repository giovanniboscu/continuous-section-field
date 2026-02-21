# actions/export_yaml.py
#
# This action module is part of the low-impact CSFActions modularization.
# It intentionally avoids importing CSFActions to prevent circular imports.

from __future__ import annotations

from typing import Any, Dict, List


def register(
    register_action,
    *,
    ActionSpec,
    ParamSpec,
    expand_station_names,
) -> None:
    """Register the export_yaml action (SPEC + RUN)."""

    SPEC = ActionSpec(
        name="export_yaml",
        summary="Export a new CSF geometry YAML extracted from exactly two stations (z0 and z1).",
        description=(
            "Creates a new CSF geometry YAML by extracting exactly two sections from the current field.\n"
            "\n"
            "YAML fields\n"
            "- stations: REQUIRED. The referenced station set MUST expand to exactly two z values (z0, z1).\n"
            "- output:   REQUIRED. File-only: exactly one YAML path (*.yaml / *.yml). 'stdout' is forbidden.\n"
            "\n"
            "Behavior\n"
            "- Calls ContinuousSectionField.write_section(z0, z1, yaml_path).\n"
            "- The underlying writer performs its own geometry validation.\n"
            "\n"
            "Use cases\n"
            "- Create a reduced two-station geometry file for sharing/reproducibility.\n"
            "- Freeze an intermediate state as an explicit data contract."
        ),
        params=(),
    )

    def RUN(
        field: Any,
        stations_map: Dict[str, List[float]],
        action: Dict[str, Any],
        *,
        debug_flag: bool = False,
    ) -> None:
        """Execute export_yaml action.

        Notes
        -----
        - IMPORTANT: The runner executes on the *normalized* action dictionary produced by the validator.
          That normalized dictionary has the form:
              {'name': 'export_yaml', 'stations': [...], 'output': [...], 'params': {...}, ...}
          It is NOT the original one-key YAML mapping {'export_yaml': {...}}.
        - This action is file-only by design: it must not print to stdout.
        """

        # Expand station-set name(s) into actual z values.
        # Validation guarantees: one station-set name and exactly two z values.
        stations_ref = action.get("stations", [])
        z_list = expand_station_names(stations_map, stations_ref)

        if len(z_list) != 2:
            # Defensive check (should not happen if validation passed).
            raise ValueError(f"export_yaml requires exactly 2 station z values, got {len(z_list)}: {z_list}")

        z0, z1 = z_list[0], z_list[1]

        # For safety, ensure ordering (most geometry pipelines expect z0 <= z1).
        if z0 > z1:
            z0, z1 = z1, z0

        output_list = action.get("output", [])
        out_files = [o for o in output_list if isinstance(o, str) and o != "stdout"]

        if len(out_files) != 1:
            # Defensive check (should not happen if validation passed).
            raise ValueError(f"export_yaml requires exactly one output YAML path, got: {output_list}")

        yaml_path = out_files[0]

        # Delegate export to the CSF field implementation.
        # The method is responsible for validating and writing the new YAML.
        field.write_section(z0, z1, yaml_path)

    register_action(SPEC, RUN)
