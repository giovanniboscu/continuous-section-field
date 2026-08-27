# Version: hollow-rectangle bending baseline v5 - 2026-08-27

For the sinusoidal line load `q(x)=q0 sin(pi x/L)`, the Euler–Bernoulli reference is

`w(x) = -q0 L^4 / (pi^4 E I_y) sin(pi x/L)`

with `I_y=(B H^3-b h^3)/12 = 4,920,000 mm^4` and `q0=p0 B`.

The executable evaluation and report generation are in `adapters/bending/post.py`.

The baseline can also be generated without running CUF:

```bash
python baseline/bending/calculate_bending_baseline.py
```

It writes `bending_baseline.txt` and `bending_baseline.csv` under
`baseline/bending/output/`.
