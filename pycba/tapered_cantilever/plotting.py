"""Non-interactive plots suitable for reproducible CLI runs."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_results(section_rows, convergence, output):
    fig, ax = plt.subplots()
    x = [r['x_mm'] for r in section_rows]
    ax.plot(x, [r['EI_Nmm2_ref'] for r in section_rows], label='Analytical')
    ax.plot(x, [r['EI_Nmm2_csf'] for r in section_rows], 'o', label='CSF')
    ax.set(xlabel='Longitudinal coordinate (mm)', ylabel='EI (N mm²)')
    ax.legend(); fig.tight_layout(); fig.savefig(output/'rigidity.png', dpi=160); plt.close(fig)
    fig, ax = plt.subplots()
    n = [r['elements'] for r in convergence]
    for key, label in [('midpoint_rel_error','Midpoint'), ('continuous_rel_error','Continuous')]:
        ax.loglog(n, [max(r[key], 1e-16) for r in convergence], 'o-', label=label)
    ax.set(xlabel='Number of members', ylabel='Relative tip error (floor 1e-16)')
    ax.grid(True, which='both', alpha=.3); ax.legend(); fig.tight_layout()
    fig.savefig(output/'convergence.png', dpi=160); plt.close(fig)
