# DRAFT

# CSF Four-Quadrant Cross Equilibrium Formulation

## 1. Definition

At any longitudinal coordinate $z$, CSF provides the actual cross-section

```math
\mathrm{Section}(z)
```

and the corresponding longitudinal Navier stress field

```math
\sigma_{zz}(x,y,z).
```

Choose an arbitrary point in the section plane,

```math
P=(x_c,y_c),
```

and pass through it two orthogonal lines:

```math
x=x_c,
\qquad
y=y_c.
```

These two lines define a **cross** that partitions the actual section into four subdomains:

```math
\Omega_{UL},
\qquad
\Omega_{UR},
\qquad
\Omega_{LL},
\qquad
\Omega_{LR}.
```

The point $P$ is arbitrary. It does not need to coincide with the centroid, a material interface, a polygon vertex, or any other special point.

---

## 2. Four sectional subdomains

The four subdomains are defined geometrically as

```math
\Omega_{UL}
=
\Omega(z)\cap
\{x<x_c,\;y>y_c\},
```

```math
\Omega_{UR}
=
\Omega(z)\cap
\{x>x_c,\;y>y_c\},
```

```math
\Omega_{LL}
=
\Omega(z)\cap
\{x<x_c,\;y<y_c\},
```

```math
\Omega_{LR}
=
\Omega(z)\cap
\{x>x_c,\;y<y_c\}.
```

Each subdomain may contain different polygonal regions, different material participation, different geometry, disconnected components, and different portions of the Navier stress field.

Therefore the four longitudinal resultants are, in general, different physical quantities.

---

## 3. Longitudinal Navier resultant of each quadrant

For each quadrant $Q$, define

```math
N_Q(x_c,y_c,z)
=
\int_{\Omega_Q(x_c,y_c,z)}
\sigma_{zz}(x,y,z)\,dA.
```

Thus,

```math
N_{UL},
\qquad
N_{UR},
\qquad
N_{LL},
\qquad
N_{LR}
```

are directly computable from the actual CSF section and its Navier stress field.

Their longitudinal derivatives define the shear resultants required by equilibrium:

```math
R_Q
=
-
\frac{\partial N_Q}{\partial z}.
```

Hence

```math
R_{UL},
\qquad
R_{UR},
\qquad
R_{LL},
\qquad
R_{LR}
```

are four quantities obtained from four different portions of the section.

---

## 4. Internal cross resultants

The cross through $P$ introduces four internal line resultants:

```math
C_L,
\qquad
C_R,
\qquad
V_U,
\qquad
V_D.
```

where:

- $C_L$ is the shear resultant on the left part of the horizontal chord;
- $C_R$ is the shear resultant on the right part of the horizontal chord;
- $V_U$ is the shear resultant on the upper part of the vertical chord;
- $V_D$ is the shear resultant on the lower part of the vertical chord.

In integral form,

```math
C_L
=
\int_{C_L}
\tau_{yz}\,dx,
```

```math
C_R
=
\int_{C_R}
\tau_{yz}\,dx,
```

```math
V_U
=
\int_{V_U}
\tau_{xz}\,dy,
```

```math
V_D
=
\int_{V_D}
\tau_{xz}\,dy.
```

The corresponding mean stresses are obtained by dividing each resultant by the geometric length of its segment.

For example,

```math
\bar{\tau}_{C_L}
=
\frac{C_L}{L_{C_L}},
```

and similarly for the other three segments.

---

## 5. Equilibrium of the four quadrants

Each quadrant is bounded internally by one horizontal segment and one vertical segment of the cross.

With a consistent sign convention, the equilibrium equations have the form

```math
R_{UL}
=
C_L + V_U,
```

```math
R_{UR}
=
C_R - V_U,
```

```math
R_{LL}
=
- C_L + V_D,
```

```math
R_{LR}
=
- C_R - V_D.
```

The exact signs depend only on the adopted orientation convention.

The important structural fact is that every internal cross segment is shared by two adjacent quadrants and therefore enters the two corresponding equilibrium equations with opposite orientation.

---

## 6. Reconstruction of the complete horizontal chord

The two upper quadrants reconstruct the complete region above the horizontal line $y=y_c$:

```math
\Omega^{+}(y_c,z)
=
\Omega_{UL}
\cup
\Omega_{UR}.
```

Therefore

```math
N^{+}(y_c,z)
=
N_{UL}
+
N_{UR}.
```

Differentiating along $z$,

```math
-
\frac{\partial N^{+}}{\partial z}
=
R_{UL}
+
R_{UR}.
```

Using the quadrant equilibrium equations, the vertical internal contribution cancels:

```math
R_{UL}+R_{UR}
=
C_L+C_R.
```

Hence the complete horizontal chord resultant is

```math
\boxed{
q_y(y_c,z)
=
C_L+C_R
=
-
\frac{\partial N^{+}(y_c,z)}{\partial z}
}
```

This gives the total shear resultant on the horizontal chord.

---

## 7. Reconstruction of the complete vertical chord

The two left quadrants reconstruct the region to the left of the vertical line $x=x_c$:

```math
\Omega^{L}(x_c,z)
=
\Omega_{UL}
\cup
\Omega_{LL}.
```

Define

```math
N^{L}(x_c,z)
=
N_{UL}
+
N_{LL}.
```

Then

```math
q_x(x_c,z)
=
-
\frac{\partial N^{L}(x_c,z)}{\partial z}.
```

The corresponding quadrant equations cancel the internal horizontal contribution and reconstruct the complete vertical chord resultant:

```math
\boxed{
q_x(x_c,z)
=
V_U+V_D
}
```

with signs consistent with the adopted orientation.

Thus the same equilibrium construction applies in the two orthogonal directions.

---

## 8. Compatibility of the four quadrant resultants

The four subdomains form a partition of the complete section:

```math
\Omega
=
\Omega_{UL}
\cup
\Omega_{UR}
\cup
\Omega_{LL}
\cup
\Omega_{LR}.
```

Therefore the longitudinal Navier resultants satisfy

```math
N
=
N_{UL}
+
N_{UR}
+
N_{LL}
+
N_{LR}.
```

Differentiating,

```math
-
\frac{dN}{dz}
=
R_{UL}
+
R_{UR}
+
R_{LL}
+
R_{LR}.
```

The four quadrant resultants are therefore generally different, but they are not arbitrary: they are automatically compatible because they originate from the same complete Navier stress field.

This gives the formulation two simultaneous properties:

```math
\boxed{
\text{different subdomain resultants}
}
```

and

```math
\boxed{
\text{global recomposition}
}
```

within the adopted Navier model.

---

## 9. Arbitrary location of the cross point

The cross point

```math
P=(x_c,y_c)
```

may be placed anywhere in the section plane.

Changing $P$ changes

```math
\Omega_{UL},
\Omega_{UR},
\Omega_{LL},
\Omega_{LR},
```

and therefore also changes

```math
R_{UL},
R_{UR},
R_{LL},
R_{LR}.
```

The cross is therefore not a fixed decomposition of the section.

It is an equilibrium interrogation operator that can be applied at an arbitrary location:

```math
\boxed{
P=(x_c,y_c)
\longmapsto
\left[
R_{UL},
R_{UR},
R_{LL},
R_{LR}
\right].
}
```

Because `Section(z)` is continuously available, the same construction can be evaluated at any longitudinal coordinate $z$ and at any cross point $P$.

# DRAFT

---

## 10. Core formulation

The four-quadrant cross formulation uses only:

- `Section(z)`;
- the complete Navier field $\sigma_{zz}(x,y,z)$;
- geometric partitioning of the actual section;
- longitudinal equilibrium.

Its basic chain is

```math
\boxed{
\mathrm{Section}(z)
\rightarrow
\sigma_{zz}(x,y,z)
\rightarrow
\{\Omega_Q\}_{Q=1}^{4}
\rightarrow
\{N_Q\}_{Q=1}^{4}
\rightarrow
\{R_Q\}_{Q=1}^{4}
\rightarrow
\text{cross-line shear resultants}
}
```

The horizontal and vertical chord resultants are recovered by recombining pairs of adjacent quadrants.

This provides a direct route from complete-chord shear resultants toward mean shear resultants on smaller chord portions.

---

## 11. Present scope

The four-quadrant construction is an equilibrium framework.

The next mathematical step is to establish the rank and independence of the resulting equations for arbitrary polygonal, heterogeneous, and non-prismatic sections.

No additional constitutive redistribution law is assumed in the formulation above.
