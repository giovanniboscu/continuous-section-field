"""Only public PyCBA 1.0.2 APIs; Euler-Bernoulli, N and mm."""
import pycba as cba


def solve_beam(lengths, rigidities, load):
    n = len(lengths)
    restraints = [-1, -1] + [0, 0]*n
    beam = cba.BeamAnalysis(lengths, rigidities, R=restraints, GAv=None)
    beam.add_pl(n, load, lengths[-1])  # 1-based member index
    beam.analyze()
    # Global nodal displacement vector, not sampled member deflections.
    return -float(beam.beam_results.D[-2])


def solve_continuous(EI, length, load, n_elements=1, degree=12):
    dx = length/n_elements
    sections = []
    for i in range(n_elements):
        # SectionEI coordinates are local to each member.
        def local_ei(x, offset=i*dx):
            return EI(offset+x)
        section = cba.SectionEI().add_segment('poly', [0.0, dx], local_ei, degree=degree)
        sections.append(section)
    return solve_beam([dx]*n_elements, sections, load)


def solve_midpoint(EI, length, load, n_elements):
    dx = length/n_elements
    rigidities = [EI((i+0.5)*dx) for i in range(n_elements)]
    return solve_beam([dx]*n_elements, rigidities, load)
