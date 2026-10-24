#!/usr/bin/env python3
"""Generate the GitHub README gallery for the bridge bending N15 eq1 results."""
from pathlib import Path
from urllib.parse import quote
import argparse

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
DEFAULT_DIR = Path('cuf/bridge-like/strain_stress_boundary/carrera_bridge_bending_scaled_lagrange_N15_eq1')


def gallery(folder, root, heading):
    images = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS), key=lambda p:p.name.lower()) if folder.is_dir() else []
    parts = [f'## {heading}', '']
    if not images:
        parts += ['_No image files found in this directory._', '']
        return parts, 0
    parts += [f'{len(images)} figures. Select any preview to open the original image at full size.', '']
    # Markdown image inside a link: portable within GitHub Markdown and supports original-size click-through.
    for i, item in enumerate(images, 1):
        relative = item.relative_to(root).as_posix()
        url = quote(relative, safe='/')
        label = item.stem.replace('_', ' ').replace('-', ' ')
        parts += [f'### {i}. {label}', '', f'[![{label}]({url})]({url})', '', f'[{item.name}]({url})', '']
    return parts, len(images)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT_DIR,
                        help='Target results directory, relative to repository root')
    args = parser.parse_args()
    root = args.directory.resolve()
    if not root.is_dir():
        parser.error(f'Directory does not exist: {root}')
    parts = [
        '# CSF-CUF Bridge: Bending N15 (Equilibration 1) — Results Gallery', '',
        'This page collects the displacement, strain and stress visualizations for the '
        '`carrera_bridge_bending_scaled_lagrange_N15_eq1` solution.', '',
        '**How to browse:** Every figure is visible directly below. Click an image to '
        'open its standalone file in GitHub, where it can be inspected at full resolution.', '',
        '- [Longitudinal and boundary results](#longitudinal-and-boundary-results)',
        '- [Transverse maps at x = 20](#transverse-maps-at-x--20)', '',
        '---', ''
    ]
    first, n1 = gallery(root, root, 'Longitudinal and boundary results')
    second, n2 = gallery(root / 'transverse_x_20', root, 'Transverse maps at x = 20')
    parts.extend(first)
    parts.extend(['---', ''])
    parts.extend(second)
    parts.extend(['---', '',
                  f'**Total: {n1+n2} figures** ({n1} in the main results folder; '
                  f'{n2} in `transverse_x_20/`).', '',
                  '## Reproduction', '',
                  'From `cuf/bridge-like`:', '',
                  '```bash',
                  'csf-cuf cases/bending_scaled_lagrange_N15_FEM10.yaml',
                  'python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 \\',
                  '  --csf-yaml models/bridge_geometry.yaml \\',
                  '  --checkpoint output/bending_scaled_lagrange_N15/carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz',
                  '',
                  'python3 -m csf.cuf.tools.plot_strain_stress_boundary_v10 \\',
                  '  --csf-yaml models/bridge_geometry.yaml \\',
                  '  --checkpoint output/bending_scaled_lagrange_N15/carrera_bridge_bending_scaled_lagrange_N15_eq1.cuf.npz \\',
                  '  --transverse-x 20 --transverse-grid 120 --transverse-vector-grid 50',
                  '```', '',
                  'The gallery is an index of generated figures, not an independent numerical validation.', ''])
    dest = root / 'README.md'
    dest.write_text('\n'.join(parts), encoding='utf-8')
    print(f'Wrote {dest} with {n1+n2} embedded figures ({n1} main, {n2} transverse).')

if __name__ == '__main__':
    main()
