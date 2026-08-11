import matplotlib.pyplot as plt

from csf.CSFStacked import CSFStacked
from csf.io.csf_reader import CSFReader
from csf.io.csf_issues import CSFIssues


# =============================================================================
# Load and validate the two CSF elements
# =============================================================================
# Each YAML file is parsed independently.
# If the reader detects errors, print the complete CSF issue report and stop
# before attempting to assemble the stacked geometry.
# =============================================================================

rf1 = CSFReader().read_file("element_1.yaml")

if not rf1.ok:
    print(CSFIssues.format_report(rf1.issues))
    raise SystemExit(1)

rf2 = CSFReader().read_file("element_2.yaml")

if not rf2.ok:
    print(CSFIssues.format_report(rf2.issues))
    raise SystemExit(1)


# Extract the validated ContinuousSectionField objects.
f1 = rf1.field
f2 = rf2.field


# =============================================================================
# Assemble the two fields
# =============================================================================
# CSFStacked joins consecutive ContinuousSectionField objects along the global
# z-coordinate.
#
# For this example:
#   element_1.S1 == element_2.S0
#
# so the two geometries meet at the same section and form one continuous
# stacked member.
# =============================================================================

stack = CSFStacked(eps_z=1e-10)
stack.append(f1)
stack.append(f2)


# =============================================================================
# Plot the assembled 3D geometry
# =============================================================================
# The resulting volume shows the transverse displacement of the first element
# followed by the opposite displacement of the second element.
# =============================================================================

stack.plot_volume_3d_global(
    title="CSFStacked - two connected elements",
    wire=False,
    colors=True,
    box_aspect_scale=(1.0, 1.0, 0.5),
)

plt.show()
