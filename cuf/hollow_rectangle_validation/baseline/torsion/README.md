# Version: hollow-rectangle torsion baseline v5 - 2026-08-27

The baseline is the Bredt–Batho thin-wall closed-section approximation:

`J_t = 4 A_m^2 / integral(ds/t)`

For the 100×100 mm outer square, 80×80 mm void and uniform 10 mm wall:

- mean-line dimensions: 90×90 mm;
- `A_m = 8,100 mm^2`;
- mean-line perimeter: `360 mm`;
- `J_t = 7,290,000 mm^4`.

For `m(x)=m0 sin(pi x/L)` and zero twist at both ends:

`theta(x)=m0 L^2/(pi^2 G J_t) sin(pi x/L)`.

This is an engineering approximation, not an exact thick-wall Saint-Venant solution. Internal CUF convergence must therefore be reported separately from the difference against Bredt–Batho.

The baseline can be generated without running CUF:

```bash
python baseline/torsion/calculate_torsion_baseline.py
```

It writes `torsion_baseline.txt` and `torsion_baseline.csv` under
`baseline/torsion/output/`.
