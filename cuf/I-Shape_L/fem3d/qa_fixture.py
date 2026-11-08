"""QA ONLY: independent YAML section interpolator for supplied I-shape benchmark.
Production driver MUST use CSFReader. This module is not used by production.
"""
from dataclasses import dataclass
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import yaml

@dataclass
class Point:
    x: float
    y: float

@dataclass
class Poly:
    name: str
    weight: float
    vertices: list
    shear_weight: float
    poisson: float

class FixtureField:
    def __init__(self, filename):
        data=yaml.safe_load(Path(filename).read_text())['CSF']['sections']
        self.data=data
        self.s0=self.section(float(data['S0']['z']))
        self.s1=self.section(float(data['S1']['z']))
    def section(self,z):
        aa=self.data['S0'];bb=self.data['S1']
        t=(z-aa['z'])/(bb['z']-aa['z'])
        ps=[]
        for a,b in zip(aa['polygons'],bb['polygons']):
            assert a['name']==b['name']
            coords=(1-t)*np.array(a['vertices'],float)+t*np.array(b['vertices'],float)
            E=(1-t)*a['weight']+t*b['weight']
            ps.append(Poly(a['name'],float(E),[Point(*map(float,p)) for p in coords],
                           float(E/2.6),0.3))
        return SimpleNamespace(z=z,polygons=ps)
