"""
CSF-CUF bridge.

Current implementation
----------------------
1. Constitutive provider API.
2. Constitutive transformation / condensation API.
3. Isotropic E-G constitutive specialization.
4. CSF-backed section provider.
5. Generic CUF transverse basis.
6. Maclaurin CUF basis.
7. Generalized sectional coefficient J API.
8. Generic weak-form CUF fundamental nucleus.

The longitudinal CUF discretization and solver remain outside this bridge module.
"""

# =============================================================================
# Constitutive provider
# =============================================================================

# Public compatibility imports: these names remain available from csf_cuf.py.
from .csf_cuf_material import (
    CondensedCoefficientTransform,
    ConstitutiveMatrixTransform,
    ConstitutiveModel,
    ConstitutiveProvider,
    IsotropicEGConstitutive,
    ScalarField,
    TransformedConstitutiveProvider,
    condense_constitutive_matrix,
    condensed_constitutive_coefficient,
)


# =============================================================================
# Section provider
# =============================================================================

# Public compatibility import: these names remain available from csf_cuf.py.
from .csf_cuf_section import (
    CSFSectionProvider,
    PolygonDomain,
    SectionProvider,
)


# =============================================================================
# CUF basis
# =============================================================================

from .csf_cuf_basis import (
    CUFBasis,
    MaclaurinCUFBasis,
    QuadrilateralSerendipityCUFBasis,
    SerendipityLagrangeReferenceBasis,
)


# =============================================================================
# Section integration API
# =============================================================================

from .csf_cuf_integration import (
    AdaptivePolygonIntegrator,
    SectionIntegrator,
)


# =============================================================================
# Generalized sectional coefficient J
# =============================================================================

from .csf_cuf_sectional import SectionalCoefficientProvider


# =============================================================================
# Generic CUF fundamental nucleus in weak form
# =============================================================================

from .csf_cuf_nucleus import (
    FundamentalNucleusProvider,
    JSignature,
    NucleusBlock,
    NucleusTerm,
    NucleusTermDefinition,
    StrainContribution,
)
