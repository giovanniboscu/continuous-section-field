
"""
CSF-PyCBA interface for the tapered cantilever benchmark.

This module connects the existing CSF public API to the PyCBA
SectionEI interface.

The procedure is organised into three steps:

1. Load the continuous geometry and material description from
   a CSF YAML file.

2. Evaluate the sectional properties at a given longitudinal
   coordinate.

3. Create a callable function EI(x) that can be passed directly
   to PyCBA.

CSF is responsible for the physical representation of the member
and the calculation of its sectional properties.

PyCBA is responsible for the structural analysis.

No sectional integration or structural analysis is implemented
directly in this module.

Coordinate convention
---------------------
PyCBA longitudinal x = CSF longitudinal z.

Within the CSF cross-section:

    CSF x : transverse width coordinate
    CSF y : transverse depth coordinate

The flexural rigidity considered here is associated with bending
about the CSF transverse x-axis.

Unit system
-----------
Length             : mm
Force              : N
Young's modulus    : MPa (N/mm^2)
Area               : mm^2
Second moment      : mm^4
Flexural rigidity  : N mm^2

Scope
-----
This interface is specifically developed for the present benchmark,
where each cross-section consists of one solid rectangular polygon
with a uniform material weight.

It is not a general adapter for heterogeneous or composite sections.
"""

import numpy as np

# Import the existing CSF function for the calculation of
# cross-sectional properties.
from csf import section_properties

# Import the native CSF reader for loading YAML model files.
from csf.io.csf_reader import CSFReader


def load_csf_model(path):
    """
    Load a continuous section field from a CSF YAML file.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the YAML file containing the geometry, material
        weights and longitudinal variation laws.

    Returns
    -------
    field
        CSF continuous section field, which can be evaluated at
        any longitudinal coordinate within its domain.

    Raises
    ------
    ValueError
        If the CSF reader reports an error or does not return
        a valid continuous section field.
    """

    # Delegate YAML reading and model construction to the native
    # CSF reader. No additional YAML parser is required.
    result = CSFReader().read_file(str(path))

    # Verify that the model has been successfully loaded and
    # that a continuous section field is available.
    if not result.ok or result.field is None:
        raise ValueError(f'Cannot load {path}: {result.issues}')

    # Return the physical model, independently of PyCBA.
    return result.field


def sectional_properties(field, x, E_ref):
    """
    Evaluate the physical and mechanical sectional properties
    at a given longitudinal coordinate.

    Parameters
    ----------
    field
        Continuous section field returned by load_csf_model().

    x : float
        Longitudinal coordinate in mm, measured from the clamp.

        This coordinate corresponds to the longitudinal
        coordinate z in CSF.

    E_ref : float
        Reference Young's modulus in MPa.

        The local material modulus is defined as:

            E(x) = E_ref * w(x)

        where w(x) is the dimensionless polygon material weight.

    Returns
    -------
    dict
        Dictionary containing:

        h_mm     : sectional depth
        b_mm     : sectional width
        E_MPa    : local Young's modulus
        A_mm2    : geometric sectional area
        Ix_mm4   : geometric second moment of area
        EI_Nmm2  : sectional flexural rigidity
    """

    # ---------------------------------------------------------
    # 1. Evaluate the continuous section field
    # ---------------------------------------------------------

    # Obtain the cross-section at the requested longitudinal
    # coordinate.
    #
    # CSF evaluates the geometry and material variation laws
    # defined in the YAML model at this position.
    #
    # The result is a cross-section containing the corresponding
    # polygons, vertices and material weights.
    section = field.section(float(x))

    # The present benchmark assumes one solid rectangular
    # polygon at every longitudinal station.
    #
    # Multiple polygons would require a more general treatment
    # of the sectional geometry and material distribution.
    if len(section.polygons) != 1:
        raise ValueError('Expected a single solid polygon')

    polygon = section.polygons[0]

    # ---------------------------------------------------------
    # 2. Obtain the local material weight
    # ---------------------------------------------------------

    # CSF represents the material variation through a
    # dimensionless polygon weight:
    #
    #     w(x) = E(x) / E_ref
    #
    # Therefore, the local Young's modulus is:
    #
    #     E(x) = E_ref * w(x)
    #
    # For example:
    #
    #     w = 1.0  -> E = E_ref
    #     w = 0.5  -> E = E_ref / 2
    w = float(polygon.weight)

    # A positive material weight is required for the present
    # linear elastic benchmark.
    #
    # This also avoids division by zero when recovering the
    # unweighted geometric properties.
    if w <= 0:
        raise ValueError('Expected positive material weight')

    # ---------------------------------------------------------
    # 3. Calculate the sectional properties using CSF
    # ---------------------------------------------------------

    # Delegate the sectional integration to the existing
    # CSF public API.
    #
    # The geometry is not integrated again in this module.
    props = section_properties(section)

    # For the single uniformly weighted polygon considered here,
    # the properties returned by CSF include the material weight:
    #
    #     A_weighted  = w * A
    #     Ix_weighted = w * Ix
    #
    # where:
    #
    #     A  = geometric sectional area
    #     Ix = geometric second moment of area
    #
    # Since the weight is uniform over the entire cross-section,
    # the unweighted geometric properties can be recovered as:
    #
    #     A  = A_weighted  / w
    #     Ix = Ix_weighted / w

    # ---------------------------------------------------------
    # 4. Recover the physical properties and flexural rigidity
    # ---------------------------------------------------------

    # The Euler-Bernoulli flexural rigidity is:
    #
    #     EI(x) = E(x) * Ix(x)
    #
    # Substituting E(x) = E_ref * w(x):
    #
    #     EI(x) = E_ref * w(x) * Ix(x)
    #
    # Since CSF already returns the weighted inertia:
    #
    #     Ix_weighted(x) = w(x) * Ix(x)
    #
    # the expression becomes:
    #
    #     EI(x) = E_ref * Ix_weighted(x)
    #
    # IMPORTANT:
    # The weighted inertia must be multiplied by E_ref,
    # not by the local Young's modulus E(x).
    #
    # Multiplying it by E(x) would introduce the material
    # weight twice.

    return {
        # Rectangular sectional depth, obtained from the
        # minimum and maximum transverse y coordinates.
        'h_mm': (
            max(p.y for p in polygon.vertices)
            - min(p.y for p in polygon.vertices)
        ),

        # Rectangular sectional width, obtained from the
        # minimum and maximum transverse x coordinates.
        'b_mm': (
            max(p.x for p in polygon.vertices)
            - min(p.x for p in polygon.vertices)
        ),

        # Local physical Young's modulus.
        'E_MPa': E_ref * w,

        # Unweighted geometric sectional area.
        'A_mm2': props['A'] / w,

        # Unweighted geometric second moment of area
        # about the CSF transverse x-axis.
        'Ix_mm4': props['Ix'] / w,

        # Physical flexural rigidity, obtained directly
        # from the CSF weighted second moment of area.
        'EI_Nmm2': E_ref * props['Ix']
    }


def create_ei_function(field, E_ref):
    """
    Create a flexural rigidity function for PyCBA.

    Parameters
    ----------
    field
        Continuous section field containing the physical
        geometry and material description of the member.

    E_ref : float
        Reference Young's modulus in MPa.

    Returns
    -------
    callable
        Function EI(x) returning the sectional flexural
        rigidity in N mm^2 at the requested longitudinal
        coordinate or coordinates.

    Notes
    -----
    The returned function provides access to the continuous
    rigidity field defined by CSF.

    It supports both scalar and array inputs, allowing PyCBA
    to evaluate the rigidity at several sampling positions
    during the construction of its polynomial representation.

    The polynomial fitting is performed by PyCBA, not by
    this module.
    """

    def EI(x):
        """
        Evaluate the flexural rigidity at one or more
        longitudinal coordinates.

        Parameters
        ----------
        x : float or array-like
            Longitudinal coordinate or collection of coordinates
            in mm.

        Returns
        -------
        float or numpy.ndarray
            Flexural rigidity in N mm^2.

            For array inputs, the output has the same shape
            as the input.
        """

        # -----------------------------------------------------
        # Scalar evaluation
        # -----------------------------------------------------

        # When x represents a single longitudinal coordinate,
        # evaluate the CSF sectional properties at that position
        # and return only the flexural rigidity.
        #
        # The other sectional properties are not required
        # by the PyCBA SectionEI interface.
        if np.ndim(x) == 0:
            return sectional_properties(
                field, float(x), E_ref
            )['EI_Nmm2']

        # -----------------------------------------------------
        # Array evaluation
        # -----------------------------------------------------

        # Convert the input coordinates into a NumPy array.
        a = np.asarray(x, dtype=float)

        # Evaluate each coordinate individually using the scalar
        # branch of this function.
        #
        # a.flat provides an iterator over all input coordinates,
        # independently of the number of array dimensions.
        #
        # The resulting array is then reshaped to preserve
        # the original input shape.
        return np.array(
            [EI(v) for v in a.flat]
        ).reshape(a.shape)

    # Return the callable itself, rather than its value at
    # a particular longitudinal position.
    #
    # The function retains access to field and E_ref through
    # the Python closure mechanism.
    #
    # PyCBA can therefore evaluate EI(x) at the positions
    # required by its SectionEI polynomial fitting procedure.
    return EI
