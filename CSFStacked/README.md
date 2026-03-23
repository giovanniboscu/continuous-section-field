# CSFStacked - Stack multiple `ContinuousSectionField` segments

if you want to only try CSFStacked then run 

**linux / Mac**
```
python3 -m venv venv
source venv/bin/activate
```
**Windows**
```
python3 -m venv venv
.\venv\Scripts\activate 
```
get the source from the repository  (not full clone)

```
git clone --filter=blob:none --no-checkout https://github.com/giovanniboscu/continuous-section-field.git
cd continuous-section-field
git sparse-checkout init --cone
git sparse-checkout set CSFStacked
git checkout main
```
install and run 
```
pip install pycba
pip install csfpy
cd CSFStacked
python3 stacked_csf_example.py

```

 python3 stacked_csf_example.py
`CSFStacked` is a small container that **impila (stacks)** multiple `ContinuousSectionField` objects along the **global** member axis `z`, providing:

- deterministic **global z → segment dispatch**
- explicit handling of **internal junctions**
- optional strict **contiguity** validation (no overlaps, no gaps)
- convenience wrappers for `section(z)` and `section_full_analysis(z)`
- a global 3D plotting helper (`plot_volume_3d_global`)

This is useful when a member is naturally described by **multiple consecutive CSF fields** (e.g., left taper + constant middle + right taper, segmented blades, repairs/patch segments, etc.).

---
## PyCBA integration 

CSFStacked integration with **PyCBA**: sample `EI(z)` (or other section properties) from the stacked CSF along the global axis and feed them into a 1D beam model to run fast deflection checks on members with **piecewise-varying stiffness**.  
The example uses midpoint sampling per solver element to avoid ambiguity at segment junctions and to keep the mapping `z → segment → properties` deterministic.


Below is a minimal pattern used in `stacked_csf_example.py`: extract `EI(z)` from the stacked CSF and run a 1D beam analysis with PyCBA.

Assumptions:
- Euler–Bernoulli bending with `EI = E * Iy`
```python
if __name__ == "__main__":

    # --- Scenario 1: Variable Section (The 'Stacked' Case) ---
    # Proves the CSF can handle sequential, non-uniform geometry
    f0 = CSFReader().read_file("stacked_0.yaml").field
    f1 = CSFReader().read_file("stacked_1.yaml").field
    stack_v = CSFStacked(eps_z=1e-10)
    stack_v.append(f0)
    stack_v.append(f1)
 

    disp_v, beam_v = run_beam_simulation(stack_v, "CSF STACKED (Variable)")



    # --- Scenario 2: Uniform Section (The 'Baseline' Case) ---
    # Proves the CSF is equally accurate for standard prismatic cases
    fu = CSFReader().read_file("uniform.yaml").field
    stack_u = CSFStacked()
    stack_u.append(fu)

    disp_u, beam_u = run_beam_simulation(stack_u, "CSF UNIFORM (Prismatic)")

    print(f"\n" + "#"*60)
    print(f" CONCLUSION: The framework correctly handles both complex")
    print(f" sequential fields and simple uniform segments with zero logic change.")
    print("#"*60)

    stack_v.plot_volume_3d_global()
    beam_v.plot_results()
    


    # --- Data Definition (From your YAML at z=5.0) ---
    # Outer: b=1.8, h=0.9 | Inner: b=1.2, h=0.5
    # --- AUTOMATED THEORETICAL VALIDATION AT z=5.0 ---
    z_check = 5.0

    # 1. Extract real data from the CSF Stack object
    real_sa = stack_v.section_full_analysis(z_check)
    real_iy = real_sa['Iy']
    real_area = real_sa['A']

    # 2. Theoretical calculation based on YAML geometry (Outer: 1.8x0.9, Inner: 1.2x0.5)
    # Formula Iy = (h * b^3) / 12
    bo, ho = 1.8, 0.9
    bi, hi = 1.2, 0.5

    iy_th = (ho * bo**3 - hi * bi**3) / 12
    area_th = (bo * ho) - (bi * hi)

    # 3. Print Validation Table
    print(f"\n" + "-"*30)
    print(f" THEORETICAL VALIDATION AT z={z_check}")
    print(f"-"*30)
    print(f"{'Property':<10} | {'Theoretical':<12} | {'CSF Actual':<12}")
    print(f"{'Iy':<10} | {iy_th:<12.6f} | {real_iy:<12.6f} ")
    print(f"{'Area':<10} | {area_th:<12.6f} | {real_area:<12.6f} ")
    print("-" * 60)

```
---

