# Base numerical tolerance coefficients.
# Effective runtime tolerances are derived from these values
# according to the characteristic size of the current model.

EPS_L = 1e-12       # Linear/length tolerance. Scales as S.
                    # Use for: orientation tests, point-on-segment, segment intersection.

EPS_A = 1e-12       # Area tolerance. Scales as S².
                    # Use for: "area nearly zero" checks, summed areas, section integrals.

EPS_K_RTOL = 1e-10  # Relative numerical tolerance. Scale-free.
                    # Primary guard for matrix/inertia comparisons.

EPS_K_ATOL = 1e-12  # Absolute numerical tolerance. Scales as S⁴.
                    # Fallback for near-zero inertia cases.

EPS_K = EPS_K_ATOL  # Alias for backward compatibility.
