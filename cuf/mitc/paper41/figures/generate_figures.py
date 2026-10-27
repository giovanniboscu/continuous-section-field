#!/usr/bin/env python3
"""Regenerate the self-contained didactic MITC tying-point figures.

Requires numpy and matplotlib. All curves are illustrative polynomials;
none is claimed to be an exact 3D elasticity shear solution.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from numpy.polynomial.legendre import Legendre

ROOT = Path(__file__).resolve().parent
X = np.linspace(-1.0, 1.0, 1601)
NAVY = '#243b53'
TEAL = '#167d8d'
ORANGE = '#c27b31'
PURPLE = '#8652a1'
GRAY = '#64748b'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10.3,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.labelcolor': NAVY, 'text.color': NAVY,
    'axes.titlecolor': NAVY,
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
})

def save(fig, stem):
    fig.savefig(ROOT / f'{stem}.png', dpi=180, bbox_inches='tight', pad_inches=0.18)
    fig.savefig(ROOT / f'{stem}.svg', bbox_inches='tight', pad_inches=0.18)
    plt.close(fig)

# Polynomial examples: coefficients of highest powers can vary; the locations
# of derivative-error zeros do not depend on the lower-degree coefficients.
examples = [
    (1, np.array([-1., 1.]), np.poly1d([1., 0.30, 0.20]),
     np.array([0.]), '2 nodes | linear displacement interpolation'),
    (2, np.array([-1., 0., 1.]), np.poly1d([1., 0.50, -0.20, 0.10]),
     np.array([-1./np.sqrt(3.), 1./np.sqrt(3.)]),
     '3 nodes | quadratic displacement interpolation'),
    (3, np.array([-1., -1./3., 1./3., 1.]),
     np.poly1d([1., 0.30, -0.20, 0.15, 0.05]),
     np.array([-np.sqrt(5.)/3., 0., np.sqrt(5.)/3.]),
     '4 nodes | cubic displacement interpolation'),
]
for p, nodes, f, err_roots, title in examples:
    coeff = np.polyfit(nodes, f(nodes), p)
    i_f = np.poly1d(coeff)
    err_prime = np.polyder(f - i_f)
    tying_gauss = np.polynomial.legendre.leggauss(p)[0]
    # Assertions for the illustrative mathematical claim.
    assert np.allclose(f(nodes), i_f(nodes), rtol=0, atol=1e-11)
    assert np.allclose(err_prime(err_roots), 0., atol=2e-12)
    # Exact identity e' = derivative of the monic nodal polynomial for a monic test f.
    omega = np.poly1d(np.poly(nodes))
    assert np.allclose(err_prime(X), np.polyder(omega)(X), atol=3e-11)
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.2), constrained_layout=True)
    ax, bx = axes
    ax.plot(X, f(X), lw=2.1, color=NAVY, label='Known polynomial f (reference)')
    ax.plot(X, i_f(X), lw=2.1, ls='--', color=TEAL, label=f'Degree-{p} interpolant I{p} f')
    ax.scatter(nodes, f(nodes), s=46, c=ORANGE, edgecolors='white', zorder=4, label='Displacement nodes')
    ax.set(xlabel='Natural coordinate xi', ylabel='Function value', title='Function and nodal interpolation')
    ax.grid(alpha=0.20)
    ax.legend(loc='best', fontsize=8.5, frameon=False)
    bx.plot(X, err_prime(X), lw=2.3, color=PURPLE, label="Derivative error: f' - (I f)'")
    bx.axhline(0, lw=1.0, color=GRAY, alpha=0.65)
    bx.scatter(err_roots, np.zeros_like(err_roots), c=TEAL, marker='o', s=67,
               edgecolors='white', zorder=5, label='Zero error (for this polynomial)')
    if p == 3:
        bx.scatter(tying_gauss, err_prime(tying_gauss), facecolors='none',
                   edgecolors=ORANGE, linewidths=2, s=110, marker='s', zorder=6,
                   label='MITC / Gauss tying point')
        for t in tying_gauss:
            if abs(t) > 1e-8:
                bx.axvline(t, color=ORANGE, alpha=0.32, linestyle=':', lw=1.2)
        bx.annotate('Distinct locations', xy=(tying_gauss[-1], err_prime(tying_gauss[-1])),
                    xytext=(0.16, 0.83), textcoords='axes fraction',
                    arrowprops={'arrowstyle': '->', 'color': ORANGE},
                    fontsize=8.8, color=ORANGE)
    else:
        bx.text(0.04, 0.96, 'Here the zeros coincide with Gauss tying points.',
                transform=bx.transAxes, va='top', fontsize=8.5, color=GRAY)
    bx.set(xlabel='Natural coordinate xi', ylabel='Derivative error', title='Where does the derivative error vanish?')
    bx.grid(alpha=0.20)
    bx.legend(loc='lower left' if p == 3 else 'best', fontsize=8.4, frameon=False)
    fig.suptitle(title, fontsize=14.4, weight='bold')
    save(fig, f'interpolation_p{p}')

# Distinguish why Gauss points are used as a lower-order MITC interpolation
# operator from the derivative-error superconvergence example above.
p = 3
P3 = Legendre.basis(3)
r = np.poly1d([0.25, 0.5])
shear = lambda x: r(x) + 0.35 * P3(x)
xis = np.polynomial.legendre.leggauss(3)[0]
fit = np.poly1d(np.polyfit(xis, shear(xis), 2))
assert np.allclose(shear(xis), r(xis), atol=1e-14)
assert np.allclose(fit(X), r(X), atol=1e-12)
fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.0), constrained_layout=True)
ax, bx = axes
ax.plot(X, shear(X), color=NAVY, lw=2.2, label='Raw example shear g = r + 0.35 P3')
ax.plot(X, fit(X), color=TEAL, lw=2.1, ls='--', label='Reconstructed MITC shear r')
ax.scatter(xis, shear(xis), c=ORANGE, marker='o', s=56, zorder=5, label='3 Gauss tying points')
ax.set(xlabel='Natural coordinate xi', ylabel='Illustrative shear strain', title='Sample at zeros of the Legendre P3 polynomial')
ax.legend(loc='best', fontsize=8.2, frameon=False)
ax.grid(alpha=0.2)
bx.plot(X, shear(X) - fit(X), color=PURPLE, lw=2.2,
        label='Removed mode g - reconstructed g')
bx.axhline(0, color=GRAY, lw=1.0)
bx.scatter(xis, np.zeros_like(xis), c=ORANGE, s=57, zorder=5, label='P3 roots')
bx.set(xlabel='Natural coordinate xi', ylabel='Difference (not physical error)', title='MITC removes this polynomial mode')
bx.grid(alpha=0.2)
bx.legend(loc='best', fontsize=8.8, frameon=False)
fig.suptitle('Why Gauss points? An exact polynomial projection identity', fontsize=14.4, weight='bold')
save(fig, 'mitc_legendre_projection')

print('B4 derivative-error zeros:', [-np.sqrt(5)/3, 0, np.sqrt(5)/3])
print('B4 Gauss tying points:', list(np.polynomial.legendre.leggauss(3)[0]))
print('Max absolute g - (r + aP3) projection verification:',
      np.max(np.abs(fit(X) - r(X))))
print('Generated 4 figures, each PNG and SVG.')
