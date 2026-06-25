# draft
**Textual legend for the CSF spun-pile degradation map**

The section represents a prestressed spun pile with external diameter $D_o=600$ mm, internal void diameter $D_i=400$ mm, wall thickness $t=100$ mm, and a single ring of 32 PC-bars with diameter $d_b=9$ mm. The CSF cross-section is represented by four concentric concrete zones and one discrete PC-bar ring:

* `core_inner`: $R=0.200$–$0.225$ m
* `pcbar_host_layer`: $R=0.225$–$0.250$ m
* `cover_inner`: $R=0.250$–$0.275$ m
* `cover_outer`: $R=0.275$–$0.300$ m
* `pcbar_00` ... `pcbar_31`: 32 discrete PC-bars on the guide radius $R_b=0.2455$ m

The degradation variable is the corrosion degree $\psi$. For the schematic time map, the reference value at 75 years is taken as:

$$
\psi_{75}=0.1856
$$

and the illustrative intermediate values are obtained from the normalized time parameter:

$$
\tau=\frac{t}{75}, \qquad \psi(t)=\psi_{75}\tau
$$

This gives:

| year | $\tau$ | $\psi(t)$ | corrosion degree |
| ---: | -----: | --------: | ---------------: |
|    0 |  0.000 |    0.0000 |            0.00% |
|   25 |  0.333 |    0.0619 |            6.19% |
|   50 |  0.667 |    0.1237 |           12.37% |
|   75 |  1.000 |    0.1856 |           18.56% |

The cover-concrete reduction factor is:

$$
r_\mathrm{cover}(\psi)
======================

0.25 \tan^{-1}\left(\frac{0.149-\psi}{0.025}\right)+0.65
$$

The core-concrete reduction factor is:

$$
r_\mathrm{core}(\psi)
=====================

0.14 \tan^{-1}\left(\frac{0.170-\psi}{0.100}\right)+0.848
$$

The PC-bar area-loss participation factor used for sectional stiffness is:

$$
r_\mathrm{bar,A}(\psi)=1-\psi
$$

The PC-bar yield-strength reduction factor is:


$$
r_\mathrm{bar,fy}(\psi)=1-0.4448\psi
$$

The resulting schematic degradation factors are:

| year | $r_\mathrm{cover}$ | $r_\mathrm{core}$ | $r_\mathrm{bar,A}$ | $r_\mathrm{bar,fy}$ |
| ---: | -----------------: | ----------------: | -----------------: | ------------------: |
|    0 |              1.001 |             0.993 |              1.000 |               1.000 |
|   25 |              0.973 |             0.963 |              0.938 |               0.972 |
|   50 |              0.848 |             0.909 |              0.876 |               0.945 |
|   75 |              0.407 |             0.826 |              0.814 |               0.917 |

For the CSF model, the degradation is applied radially as:

$$
\texttt{cover_outer},\texttt{cover_inner}
\rightarrow r_\mathrm{cover}(\psi)
$$

$$
\texttt{core_inner},\texttt{pcbar_host_layer}
\rightarrow r_\mathrm{core}(\psi)
$$

$$
\texttt{pcbar_00}\ldots\texttt{pcbar_31}
\rightarrow r_\mathrm{bar,A}(\psi)
$$

The figure is a radial degradation map. If an axial exposure field is introduced, the corrosion degree becomes:

$$
\psi(z,t)=\psi_{75}\tau, f(z/L)
$$

where $f(z/L)$ is a prescribed CSF exposure field. The uniform case is recovered with $f(z/L)=1$.
