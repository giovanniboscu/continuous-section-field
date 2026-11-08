#!/usr/bin/env bash

set -uo pipefail

ROOT="${1:-.}"

if command -v magick >/dev/null 2>&1; then
    CMD="magick"
elif command -v convert >/dev/null 2>&1; then
    CMD="convert"
else
    echo "ERROR: ImageMagick not installed"
    exit 1
fi

converted=0
skipped=0
errors=0

while IFS= read -r -d '' file; do
    output="${file%.*}.webp"

    if [[ -f "$output" ]]; then
        echo "SKIP: $output"
        ((skipped+=1))
        continue
    fi

    echo "CONVERT: $file -> $output"

    if "$CMD" "$file" -strip -quality 85 "$output"; then
        ((converted+=1))
    else
        echo "ERROR: $file"
        rm -f -- "$output"
        ((errors+=1))
    fi

done < <(find "$ROOT" -type f -iname '*.png' -print0)

echo
echo "===== SUMMARY ====="
echo "Converted: $converted"
echo "Skipped:   $skipped"
echo "Errors:    $errors"
