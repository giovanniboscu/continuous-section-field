#!/bin/sh
./run_writegeometry_v6_twist.sh
python3 -m csf.CSFActions  twist_tower.yaml twist_tower_action.yaml


INPUT="out/twist_tower.txt"
OUTCP="out/twist_tower_sp.txt"
rm $OUTCP
grep '^# z=' "${INPUT}" | sed 's/^# z=//' | while read -r z; do
  echo "Running analysis at z=${z}">>$OUTCP
  python3 -m csf.utils.csf_sp "${INPUT}" --z="${z}" >>$OUTCP
done
