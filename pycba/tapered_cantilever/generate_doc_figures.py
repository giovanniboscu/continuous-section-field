"""Regenerate documentation figures from reported runs and analytical laws."""
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch

OUT = Path(__file__).resolve().parent / 'img'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 120})
BLUE, TEAL, ORANGE, GRAY = '#245b91', '#087e83', '#c16b26', '#64748b'
RESULTS = OUT.parent / 'results'
CASES = ['prismatic', 'variable_geometry', 'variable_material', 'combined_variation']


def read_results(case, filename):
    with (RESULTS / case / filename).open(newline='') as f:
        return list(csv.DictReader(f))


def column(rows, name):
    return np.array([float(row[name]) for row in rows])


def save(fig, name):
    fig.savefig(OUT / name, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def models():
    fig, ax = plt.subplots(figsize=(9,5.8))
    for j,(name,taper,mat) in enumerate([('A  Prismatic',False,False),('B  Variable geometry',True,False),('C  Variable material',False,True),('D  Combined variation',True,True)]):
        y = 3-j
        for i in range(100):
            x0,x1=i/100,(i+1)/100
            h0=.23*(1-.5*x0 if taper else 1); h1=.23*(1-.5*x1 if taper else 1)
            ax.add_patch(Polygon([[x0,y-h0],[x1,y-h1],[x1,y+h1],[x0,y+h0]],facecolor=plt.cm.Blues(.78-.45*x0 if mat else .78),edgecolor='none'))
        hh=.115 if taper else .23
        ax.plot([0,1,1,0,0],[y-.23,y-hh,y+hh,y+.23,y-.23],color=BLUE,lw=1)
        ax.plot([0,0],[y-.32,y+.32],color='#263445',lw=2.5)
        ax.annotate('',xy=(1,y+hh),xytext=(1,y+.42),arrowprops={'arrowstyle':'-|>','color':ORANGE,'lw':1.8})
        ax.text(-.04,y,name,ha='right',va='center',weight='bold')
        ax.text(1.035,y,'E/E₀: 1 → '+('0.5' if mat else '1'),va='center',fontsize=10)
    ax.text(.5,-.49,'L = 5000 mm  |  b = 200 mm  |  P = 10 kN',ha='center')
    ax.set(xlim=(-.42,1.33),ylim=(-.65,3.6),title='Four physical configurations · same loading and supports'); ax.axis('off')
    save(fig,'models.png')


def workflow():
    fig, ax=plt.subplots(figsize=(9,3.8)); ax.set(xlim=(0,10),ylim=(0,4)); ax.axis('off')
    def box(x,y,w,h,head,body):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',facecolor='#edf4f8',edgecolor=BLUE))
        ax.text(x+w/2,y+h*.67,head,ha='center',weight='bold',fontsize=11)
        ax.text(x+w/2,y+h*.28,body,ha='center',fontsize=10)
    def arr(a,b): ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':GRAY,'lw':1.6})
    box(.15,2.6,2.65,.85,'CSF YAML','Geometry + material'); box(3.6,2.6,2.65,.85,'CSF library','Weighted sectional EI'); box(7.05,2.6,2.65,.85,'SectionEI / PyCBA','Polynomial fit → analysis'); arr((2.9,3.02),(3.5,3.02)); arr((6.35,3.02),(6.95,3.02))
    box(.15,.45,2.65,.85,'Independent formulas','Analytical EI + virtual work'); box(3.6,.45,2.65,.85,'Section validation','21 longitudinal stations'); box(7.05,.45,2.65,.85,'Structural validation','Tip error + convergence'); arr((2.9,.87),(3.5,.87)); arr((6.35,.87),(6.95,.87)); arr((4.92,2.52),(4.92,1.4)); arr((8.37,2.52),(8.37,1.4)); save(fig,'workflow.png')


def rigidity():
    t=np.linspace(0,1,401); q=1-t/2
    fig,ax=plt.subplots(figsize=(8,4.3))
    for p,label,c in [(0,'A · prismatic',GRAY),(3,'B · geometry',BLUE),(1,'C · material',ORANGE),(4,'D · combined',TEAL)]: ax.plot(t,q**p,label=label,color=c,lw=2.2)
    ax.set(xlabel='Normalized position x/L',ylabel='EI / EI at root',ylim=(0,1.07),title='Analytical flexural rigidity laws'); ax.grid(alpha=.2); ax.legend(); save(fig,'rigidity.png')


def sectional():
    rows = read_results('combined_variation', 'section_validation.csv')
    x = column(rows, 'x_mm')
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for key, label, color in [('h_mm', 'Height', GRAY), ('E_MPa', 'Young modulus', ORANGE),
                              ('A_mm2', 'Area', '#9878aa'), ('Ix_mm4', 'Geometric inertia', BLUE),
                              ('EI_Nmm2', 'Flexural rigidity', TEAL)]:
        ref = column(rows, key + '_ref')
        actual = column(rows, key + '_csf')
        ax.plot(x/x[-1], ref/ref[0], color=color, label=label, lw=2)
        ax.plot(x/x[-1], actual/ref[0], 'o', mfc='white', mec=color, ms=4)
    ax.set(xlabel='Normalized position x/L', ylabel='Property / root value',
           title='Case D - sectional validation at 21 stations', ylim=(0, 1.06))
    ax.grid(alpha=.2); ax.legend()
    ax.text(.02, .04, 'Lines: analytical reference; markers: recorded CSF values',
            transform=ax.transAxes, fontsize=9)
    save(fig, 'section_validation.png')


def convergence(case, name, title):
    rows = read_results(case, 'convergence.csv')
    N = column(rows, 'elements')
    mid = column(rows, 'midpoint_rel_error')
    cont = column(rows, 'continuous_rel_error')
    fig, ax = plt.subplots(figsize=(8, 4.7))
    ax.loglog(N, mid, 'o-', color=ORANGE, label='Midpoint')
    ax.loglog(N, cont, 's-', color=TEAL, label='Continuous SectionEI')
    ax.loglog(N, mid[-1]*(N[-1]/N)**2, '--', color=GRAY, label='Second-order guide')
    ax.set_xticks(N, labels=[str(int(n)) for n in N])
    ax.set(xlabel='Number of elements', ylabel='Relative tip displacement error', title=title)
    ax.grid(which='major', alpha=.25); ax.legend(loc='center right')
    save(fig, name)


def degree():
    fig, ax = plt.subplots(figsize=(8, 4.4))
    for case, label, color, marker in [('variable_geometry', 'B - geometry', BLUE, 'o-'),
                                       ('combined_variation', 'D - combined', TEAL, 's-')]:
        rows = read_results(case, 'degree_sensitivity.csv')
        n = column(rows, 'degree_parameter')
        ax.semilogy(n, column(rows, 'relative_error'), marker, label=label, color=color)
    ax.set(xticks=n, xlabel='SectionEI degree parameter', ylabel='Relative tip displacement error',
           title='Single-member degree sensitivity')
    ax.grid(alpha=.2); ax.legend(); save(fig, 'degree_sensitivity.png')


def tip():
    rows = [read_results(case, 'summary.csv')[0] for case in CASES]
    ref = column(rows, 'reference_mm')
    actual = column(rows, 'continuous_mm')
    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(4)
    ax.barh(y, ref, color='#dce9ef', edgecolor=BLUE, label='Reference')
    ax.plot(actual, y, 'o', color=TEAL, label='Continuous (overlapping)')
    ax.set_yticks(y, labels=['A - prismatic', 'B - geometry', 'C - material', 'D - combined'])
    ax.invert_yaxis()
    ax.set(xlabel='Downward tip displacement (mm)', title='Four single-member benchmarks',
           xlim=(0, max(ref)*1.2))
    ax.legend(loc='upper right'); ax.grid(axis='x', alpha=.2)
    for i, value in enumerate(ref):
        ax.text(value+.045, i, f'{value:.6f}', va='center', fontsize=9)
    save(fig, 'tip_displacement.png')


if __name__=='__main__':
    models(); workflow(); rigidity(); sectional(); tip(); degree()
    convergence('variable_geometry','convergence_geometry.png','Case B · variable geometry')
    convergence('combined_variation','convergence_combined.png','Case D · combined variation')
