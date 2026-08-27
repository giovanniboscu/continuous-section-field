#!/usr/bin/env bash
# Version: CSF-CUF discovered-cases runner v1 - 2026-08-27
set -uo pipefail

# Put this file in the root of hollow_rectangle_validation_v5.
# Optional filters, examples:
#   bash run_discovered_cases.sh torsion
#   bash run_discovered_cases.sh torsion legendre
#   FORCE=1 bash run_discovered_cases.sh torsion legendre

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASES_DIR="${PROJECT_DIR}/cases"
LOGS_DIR="${PROJECT_DIR}/logs"
STATUS_DIR="${LOGS_DIR}/completed"

FILTER_1="${1:-}"
FILTER_2="${2:-}"
FORCE="${FORCE:-0}"

if ! command -v csf-cuf >/dev/null 2>&1; then
    echo "ERROR: csf-cuf is not available in the active environment." >&2
    exit 127
fi

if [[ ! -d "${CASES_DIR}" ]]; then
    echo "ERROR: cases directory not found: ${CASES_DIR}" >&2
    exit 2
fi

mkdir -p "${LOGS_DIR}" "${STATUS_DIR}"

mapfile -d '' ALL_CASES < <(find "${CASES_DIR}" -type f -name '*.yaml' -print0 | sort -z)

CASES=()
for case_file in "${ALL_CASES[@]}"; do
    relative_case="${case_file#${PROJECT_DIR}/}"
    if [[ -n "${FILTER_1}" && "${relative_case}" != *"${FILTER_1}"* ]]; then
        continue
    fi
    if [[ -n "${FILTER_2}" && "${relative_case}" != *"${FILTER_2}"* ]]; then
        continue
    fi
    CASES+=("${case_file}")
done

if (( ${#CASES[@]} == 0 )); then
    echo "No YAML cases matched the requested filters." >&2
    exit 3
fi

echo "Project : ${PROJECT_DIR}"
echo "Cases   : ${#CASES[@]}"
echo "Logs    : ${LOGS_DIR}"
echo

completed=0
skipped=0
failed=0

for case_file in "${CASES[@]}"; do
    relative_case="${case_file#${PROJECT_DIR}/}"
    case_id="${relative_case#cases/}"
    case_id="${case_id%.yaml}"
    case_id="${case_id//\//__}"

    log_file="${LOGS_DIR}/${case_id}.log"
    done_file="${STATUS_DIR}/${case_id}.done"

    if [[ "${FORCE}" != "1" && -s "${done_file}" ]]; then
        echo "SKIP ${relative_case}"
        ((skipped += 1))
        continue
    fi

    echo "RUN  ${relative_case}"
    start_epoch=$(date +%s)

    {
        echo "# Version: CSF-CUF case execution log v1 - 2026-08-27"
        echo "case=${relative_case}"
        echo "started=$(date --iso-8601=seconds)"
        echo
        csf-cuf "${case_file}"
    } 2>&1 | tee "${log_file}"
    solver_status=${PIPESTATUS[0]}

    finish_epoch=$(date +%s)
    elapsed=$((finish_epoch - start_epoch))

    if (( solver_status == 0 )); then
        {
            echo "case=${relative_case}"
            echo "completed=$(date --iso-8601=seconds)"
            echo "elapsed_seconds=${elapsed}"
            echo "exit_status=0"
        } > "${done_file}"
        echo "DONE ${relative_case} (${elapsed} s)"
        ((completed += 1))
    else
        echo "FAIL ${relative_case}: exit ${solver_status}" >&2
        echo "Log: ${log_file}" >&2
        ((failed += 1))
        break
    fi

    echo
done

echo
echo "SUMMARY completed=${completed} skipped=${skipped} failed=${failed}"

if (( failed > 0 )); then
    exit 1
fi
