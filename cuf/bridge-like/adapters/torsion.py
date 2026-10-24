"""Local adapter: load and boundary conditions are independent components."""
from pathlib import Path
import importlib.util
from csf.cuf.adapters.problem.uniform_surface import build_problem as build_surface_load

def _load_local(name, relative):
    path = Path(__file__).resolve().parent / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_clamp = _load_local("bridge_local_full_clamp", "constraints/full_clamp.py")

class BridgeProblem:
    def __init__(self, load):
        self.load = load
    def build_load_vector(self, **kwargs):
        return self.load.build_load_vector(**kwargs)
    def build_constraints(self, **kwargs):
        return _clamp.FullClampConstraints().build_constraints(**kwargs)
    def tracked_points(self, section_provider, x):
        return self.load.tracked_points(section_provider, x)

def build_problem(problem_type, options):
    torsion_load = _load_local("bridge_local_torsion_load", "loads/bridge_top_edge_torsion_uniform.py")
    return BridgeProblem(torsion_load.build_problem(problem_type, options))
