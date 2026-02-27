from __future__ import annotations

import numpy as np

try:
    import pycba as cba
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "Optional dependency missing: pycba.\n"
        "Install with:\n"
        "  pip install pycba"
    ) from e

import csf
print(csf.__file__)



from csf.CSFStacked import CSFStacked
from csf.io.csf_reader import CSFReader
from csf.section_field import Visualizer


def run_beam_simulation(stack_obj, label: str) -> tuple[float, object]:
    """
    Run a simple simply-supported beam analysis using section properties sampled from CSF.
    """
    # Analysis setup (didactic values)
    n_nodes = 21      # Number of beam nodes (=> 20 elements)
    E = 30e6          # Reference elastic modulus for PyCBA demo
    P = 25.0          # Point load magnitude

    z_min, z_max = stack_obj.global_bounds()
    L = z_max - z_min
    dz = L / (n_nodes - 1)

    print("\n" + "=" * 60)
    print(f"SCENARIO: {label}")
    print("=" * 60)

    # 1) Scan CSF properties along z (proof of continuous field)
    print("\n[1] CSF property scan")
    for i in range(n_nodes):
        z = z_min + i * dz
        sa = stack_obj.section_full_analysis(z)
        print(f"z = {z:7.4f} | A = {sa['A']:.6f} | Iy = {sa['Iy']:.6f}")

    # 2) Build element stiffness list by midpoint sampling
    ei_list = []
    print("\n[2] Midpoint EI sampling")
    for i in range(n_nodes - 1):
        z_mid = z_min + (i + 0.5) * dz
        sa_mid = stack_obj.section_full_analysis(z_mid)
        EI = E * sa_mid["Iy"]
        ei_list.append(EI)

        if i < 3 or i >= (n_nodes - 1) - 3:
            print(f"elem {i:02d} | z_mid = {z_mid:7.4f} | EI = {EI:.6e}")
        elif i == 3:
            print("...")

    # 3) PyCBA beam setup (simply supported beam)
    # R format: [v0, r0, v1, r1, ..., vn, rn]
    # -1 = restrained, 0 = free
    R = [0] * (2 * n_nodes)
    R[0] = -1                  # Left support: vertical restrained
    R[2 * (n_nodes - 1)] = -1  # Right support: vertical restrained

    beam = cba.BeamAnalysis([dz] * (n_nodes - 1), ei_list, R)

    # Apply one point load at midspan node
    mid_node = (n_nodes - 1) // 2
    beam.add_pl(mid_node, P, dz)
    beam.analyze()

    # 4) Report displacement summary (compact)
    d = beam.beam_results.results.D
    max_resp = float(np.max(np.abs(d)))

    print("\n[3] Result")
    print(f"Max displacement response magnitude = {max_resp:.8e}")

    return max_resp, beam


if __name__ == "__main__":

    # Read one CSF YAML file (geometry + optional weight_laws)
    # Replace with "geometry.yaml" if you want to use a local file name.
    field = CSFReader().read_file("pycba_wz_demo.yaml").field

    # Wrap in CSFStacked even for a single segment (uniform API)
    stack = CSFStacked(eps_z=1e-10)
    stack.append(field)

    disp, beam = run_beam_simulation(stack, "CSF single field (simply supported)")



    # Optional plots
    #stack.plot_volume_3d_global()
    beam.plot_results()
    
    
    # =================================================================
    # Plot weight
    # =================================================================
    viz = Visualizer(field)
    viz.plot_weight(num_points=1000)
    viz.plot_properties(["A", "Iy"])
      
