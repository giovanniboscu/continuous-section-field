# Version: CSF-CUF hollow-rectangle complete validation package v5 - 2026-08-27

# Hollow rectangular section - bending and torsion

Clean, complete package for the prismatic 100×100 mm hollow square section
with an 80×80 mm concentric void and 10 mm wall thickness.

## Case matrix

| Analysis | Basis | Orders | Cases |
|---|---|---:|---:|
| Bending | scaled Legendre | N01–N20 | 20 |
| Bending | scaled Maclaurin | N01–N20 | 20 |
| Torsion | scaled Legendre | N01–N20 | 20 |
| Torsion | scaled Maclaurin | N01–N20 | 20 |

Total: 80 cases.

## Independent baselines

Run without CSF–CUF:

```bash
python baseline/bending/calculate_bending_baseline.py
python baseline/torsion/calculate_torsion_baseline.py
```

The first computes the Euler–Bernoulli bending baseline; the second computes
the Bredt–Batho torsion baseline. Both create TXT and CSV output files.

## Execute cases

Make the runner executable once:

```bash
chmod +x run_discovered_cases.sh
```

All 80 cases:

```bash
./run_discovered_cases.sh
```

Examples of filtered execution:

```bash
./run_discovered_cases.sh bending legendre
./run_discovered_cases.sh bending maclaurin
./run_discovered_cases.sh torsion legendre
./run_discovered_cases.sh torsion maclaurin
```

Successful cases receive a `.done` marker under `logs/completed/`. A later run
skips those cases. Set `FORCE=1` only when completed cases must be repeated.

## Output tree

```text
output/bending/legendre/Nxx/
output/bending/maclaurin/Nxx/
output/torsion/legendre/Nxx/
output/torsion/maclaurin/Nxx/
```

The package contains no previous numerical outputs or logs.
