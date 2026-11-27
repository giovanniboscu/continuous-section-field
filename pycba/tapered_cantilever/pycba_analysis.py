"""Only public PyCBA 1.0.2 APIs; Euler-Bernoulli, N and mm."""
import pycba as cba


def solve_beam(lengths, rigidities, load):
    n = len(lengths)

    # PyCBA restraint vector R has length 2*(n+1): two entries per node,
    # ordered left to right as [vertical DOF, rotational DOF].
    #
    # PyCBA restraint convention:
    # -1 = fully restrained degree of freedom
    #  0 = free degree of freedom
    #
    # A beam with n elements has n+1 nodes. Both degrees of freedom of the
    # first node are restrained (clamped end); all other nodes are free.
    restraints = [-1, -1] + [0, 0]*n
    # GAv=None neglects shear deformation, consistently
    # with the Euler-Bernoulli beam theory adopted in
    # the analytical reference solutions.    
    beam = cba.BeamAnalysis(lengths, rigidities, R=restraints, GAv=None)

    # add_pl(member, load, a):
    #   member = 1-based member index (n = last element),
    #   load   = magnitude, positive downward in PyCBA,
    #   a      = distance from the LEFT end of that member to the load.
    # With a = lengths[-1] the load sits at the right end of the last
    # member, i.e. at the free tip of the cantilever.
    beam.add_pl(n, load, lengths[-1])
    beam.analyze()

    # D is the global nodal displacement vector, ordered as
    # [v0, theta0, v1, theta1, ..., vn, thetan]
    # (v = vertical displacement, theta = rotation).
    #
    # D[-2] is therefore the vertical displacement vn of the last node,
    # the free end of the cantilever.
    #
    # PyCBA uses "positive load downward" but "positive displacement
    # upward", so for a downward load D[-2] is negative. The minus sign
    # returns the downward deflection as a positive number, to compare
    # directly with the analytical reference solution.
    return -float(beam.beam_results.D[-2])


def solve_continuous(EI, length, load, n_elements=1, degree=12):
    """One SectionEI polynomial per element (flexibility-based member).

    `degree` is the degree of the polynomial that PyCBA fits to EI inside
    each element; see THEORY.md, section 6, for its role and its
    relationship with the numerical integration.
    """
    dx = length/n_elements
    sections = []
    for i in range(n_elements):
        # SectionEI calls the function with coordinates LOCAL to the
        # member, x in [0, dx], while EI(...) expects the GLOBAL
        # coordinate along the whole beam. So we shift by the element
        # start, i*dx.
        #
        # `offset=i*dx` is a default argument on purpose: it freezes the
        # current value of i inside this function. Without it, Python's
        # late-binding closures would make every local_ei see the final
        # value of i from the loop, and all elements would use the
        # rigidity of the last one.
        def local_ei(x, offset=i*dx):
            return EI(offset+x)
        section = cba.SectionEI().add_segment('poly', [0.0, dx], local_ei, degree=degree)
        sections.append(section)
    return solve_beam([dx]*n_elements, sections, load)


def solve_midpoint(EI, length, load, n_elements):
    """Baseline: constant EI per element, sampled at the element midpoint."""
    dx = length/n_elements
    rigidities = [EI((i+0.5)*dx) for i in range(n_elements)]
    return solve_beam([dx]*n_elements, rigidities, load)
