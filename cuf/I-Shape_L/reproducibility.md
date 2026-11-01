## 8. Run the multi-section strong-equilibrium diagnostic

Still from:

```text
continuous-section-field/cuf/I-Shape_L
```

execute:

```bash
./equilibrium_multisection_components.sh
```

This launcher evaluates the strong-equilibrium diagnostic over multiple beam sections.

The diagnostic compares the FEM3D H8 and CSF-CUF L9 solutions at corresponding physical sampling locations and evaluates the three components of the stress-divergence residual:

$$
(\nabla\cdot\sigma)_x
=
\frac{\partial \sigma_{xx}}{\partial x}
+
\frac{\partial \tau_{xy}}{\partial y}
+
\frac{\partial \tau_{xz}}{\partial z}
$$

$$
(\nabla\cdot\sigma)_y
=
\frac{\partial \tau_{xy}}{\partial x}
+
\frac{\partial \sigma_{yy}}{\partial y}
+
\frac{\partial \tau_{yz}}{\partial z}
$$

and

$$
(\nabla\cdot\sigma)_z
=
\frac{\partial \tau_{xz}}{\partial x}
+
\frac{\partial \tau_{yz}}{\partial y}
+
\frac{\partial \sigma_{zz}}{\partial z}
$$

The corresponding total residual norm is

$$
\|\nabla\cdot\sigma\|
=
\sqrt{
(\nabla\cdot\sigma)_x^2+
(\nabla\cdot\sigma)_y^2+
(\nabla\cdot\sigma)_z^2
}
$$

The resulting comparison is an element/domain-interior strong-equilibrium diagnostic. It is a local post-processing measure and should not be interpreted as a proof of global strong-form equilibrium.
