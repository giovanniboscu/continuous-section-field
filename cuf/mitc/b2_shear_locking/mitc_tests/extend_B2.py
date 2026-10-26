#!/usr/bin/env python3
"""Generate optional N16/N32/N64 paired cases, without running the solver."""
import argparse
from pathlib import Path
try: import yaml
except ImportError: raise SystemExit('Install PyYAML: python -m pip install PyYAML')
root=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--counts',nargs='+',type=int,default=[16,32,64]);a=p.parse_args()
for n in a.counts:
 if n<=0 or n>4096: p.error('counts must be 1..4096')
 for mode in ('off','on'):
  template=root/'cases'/f'mitc_locking_rect_B2_N08_{mode}.yaml'
  config=yaml.safe_load(template.read_text())
  name=f'mitc_locking_rect_B2_N{n:02d}_{mode}'
  config['case']['name']=name
  config['longitudinal']['element_boundaries']=[round(i/n,15) for i in range(n+1)]
  config['output']['directory']=f'../output/{name}'
  target=root/'cases'/f'{name}.yaml'
  target.write_text('# Generated paired B2 MITC extension; derived from N08 template.\n'+yaml.safe_dump(config,sort_keys=False))
  print(target.relative_to(root))
