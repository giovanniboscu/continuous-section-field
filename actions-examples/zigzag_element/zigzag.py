import matplotlib.pyplot as plt

from csf.CSFStacked import CSFStacked
from csf.io.csf_reader import CSFReader


# Load the two CSF elements
f1 = CSFReader().read_file("element_1.yaml").field
f2 = CSFReader().read_file("element_2.yaml").field


# Assemble
stack = CSFStacked(eps_z=1e-10)
stack.append(f1)
stack.append(f2)


# Plot assembled geometry
stack.plot_volume_3d_global(
    title="CSFStacked - two connected elements",
    wire=False,
    colors=True,
    box_aspect_scale=(1.0, 1.0, 0.5),
)

plt.show()
