#!/usr/bin/env python3
"""Plot the tabulated 14 case displacement results; requires matplotlib."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parent/'reports'
rows=list(csv.DictReader((r/'mitc_B2_extended.csv').open()))
fig,ax=plt.subplots(figsize=(8,4.7))
for mode in ('off','on'):
 d=sorted((int(x['elements']),float(x['tip_uz_mm'])) for x in rows if x['mode']==mode)
 ax.plot([x[0] for x in d],[x[1] for x in d],marker='o',label='MITC '+mode.upper())
ax.axhline(-6.6666666666667,ls='--',color='gray',label='Euler-Bernoulli reference')
ax.set_xscale('log',base=2);ax.set_xticks([1,2,4,8,16,32,64],labels=['1','2','4','8','16','32','64']);ax.set_xlabel('Number of longitudinal B2 elements');ax.set_ylabel('Tip displacement [mm]');ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(r/'mitc_B2_convergence.png',dpi=180)
