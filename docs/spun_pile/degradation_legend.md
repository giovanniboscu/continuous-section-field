# CSF spun-pile degradation map: textual legend

## Source basis

This legend is associated with the schematic CSF degradation map of a prestressed spun pile cross-section. The geometry and material quantities used here are taken from the spun-pile case described in Refani and Nagao, *Corrosion Effects on the Mechanical Properties of Spun Pile Materials*, Applied Sciences, 2023.

The map is a cross-sectional radial degradation map. It is not an axial view of the pile.

## Cross-section geometry

The section represents a prestressed spun pile with:

- external diameter: Do = 600 mm
- internal void diameter: Di = 400 mm
- wall thickness: t = 100 mm
- PC-bar diameter: db = 9 mm
- number of PC-bars: 32
- PC-bar guide radius: Rb = 0.2455 m

The CSF cross-section is represented by four concentric concrete zones and one discrete PC-bar ring.

- `core_inner`: R = 0.200-0.225 m
- `pcbar_host_layer`: R = 0.225-0.250 m
- `cover_inner`: R = 0.250-0.275 m
- `cover_outer`: R = 0.275-0.300 m
- `pcbar_00` ... `pcbar_31`: 32 discrete PC-bars placed on the guide radius Rb = 0.2455 m

## Degradation variable

The degradation variable is the corrosion degree, denoted by psi.

In this document, psi is used as a fraction, not as a percentage. Therefore:

- psi = 0.1856 means 18.56% corrosion degree
- psi = 0.0619 means 6.19% corrosion degree

For the schematic time map, the reference value at 75 years is:

$$\psi_{75}=0.1856$$

The illustrative intermediate values are obtained from the normalized time parameter tau:

$$\tau=\frac{t}{75}$$

The corrosion degree at time t is then:

$$\psi(t)=\psi_{75}\tau$$

This gives:

| year | tau | corrosion degree psi(t) | corrosion degree [%] |
| ---: | --: | -----------------------: | -------------------: |
| 0 | 0.000 | 0.0000 | 0.00% |
| 25 | 0.333 | 0.0619 | 6.19% |
| 50 | 0.667 | 0.1237 | 12.37% |
| 75 | 1.000 | 0.1856 | 18.56% |

The values at 25 and 50 years are schematic interpolation values. They are used only to build the graphical time map.

## Reduction laws

The cover-concrete reduction factor is:

$$r_{\mathrm{cover}}(\psi)=0.25\tan^{-1}\left(\frac{0.149-\psi}{0.025}\right)+0.65$$

The core-concrete reduction factor is:

$$r_{\mathrm{core}}(\psi)=0.14\tan^{-1}\left(\frac{0.170-\psi}{0.100}\right)+0.848$$

The PC-bar area-loss participation factor used for sectional stiffness is:

$$r_{\mathrm{bar,A}}(\psi)=1-\psi$$

The PC-bar yield-strength reduction factor is:

$$r_{\mathrm{bar,fy}}(\psi)=1-0.4448\psi$$

At zero corrosion, the physical degradation factors are set to unity. The fitted cover/core expressions are therefore used for degraded states, while the 0-year state is taken as the undegraded reference condition.

The resulting schematic degradation factors are:

| year | r_cover | r_core | r_bar_A | r_bar_fy |
| ---: | ------: | -----: | ------: | -------: |
| 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| 25 | 0.973 | 0.963 | 0.938 | 0.972 |
| 50 | 0.848 | 0.909 | 0.876 | 0.945 |
| 75 | 0.407 | 0.826 | 0.814 | 0.917 |

## Meaning of the factors

The degradation laws are dimensionless correction factors applied to corresponding undegraded quantities.

General form:

$$Q_{\mathrm{degraded}}=r(\psi)Q_0$$

For cover concrete:

$$f_{c,\mathrm{cover}}(\psi)=r_{\mathrm{cover}}(\psi)f_{c,\mathrm{cover},0}$$

For core concrete:

$$f_{c,\mathrm{core}}(\psi)=r_{\mathrm{core}}(\psi)f_{c,\mathrm{core},0}$$

For PC-bar area loss:

$$A_{\mathrm{bar}}(\psi)=r_{\mathrm{bar,A}}(\psi)A_{\mathrm{bar},0}$$

For PC-bar yield strength:

$$f_{y,\mathrm{bar}}(\psi)=r_{\mathrm{bar,fy}}(\psi)f_{y,\mathrm{bar},0}$$

The concrete factors describe compressive-strength degradation in the source model. Using them as CSF participation factors for section-level stiffness is a modelling choice. The PC-bar area-loss factor is directly suitable for area-based sectional participation. The PC-bar yield-strength factor describes a strength limit, not an elastic stiffness factor.

## Radial application in the CSF map

For the CSF degradation map, the radial assignment is:

`cover_outer`, `cover_inner`:

$$r_{\mathrm{cover}}(\psi)$$

`core_inner`, `pcbar_host_layer`:

$$r_{\mathrm{core}}(\psi)$$

`pcbar_00` ... `pcbar_31`:

$$r_{\mathrm{bar,A}}(\psi)$$

This assignment means that the outer and inner cover zones receive the cover-concrete degradation factor, the internal concrete zones receive the core-concrete degradation factor, and the discrete PC-bars receive the bar area-loss factor.

## Optional yield-state map for PC-bars

The yield-strength reduction can be stored as a separate material-limit field for the PC-bars:

$$f_{y,\mathrm{bar}}(z,t)=f_{y,0}\left(1-0.4448\psi(z,t)\right)$$

A yielded/non-yielded state requires an additional stress or strain state. For example, using a bar stress field sigma_bar:

$$\eta_y(z,t)=\frac{\sigma_{\mathrm{bar}}(z,t)}{f_{y,\mathrm{bar}}(z,t)}$$

The interpretation is:

- eta_y < 1: PC-bar below yield
- eta_y = 1: incipient yielding
- eta_y > 1: PC-bar beyond the degraded yield limit

This yield-state check is separate from the elastic sectional-property map.

## Optional axial exposure field

The figure shown in the degradation map is radial. If an axial exposure field is introduced, the corrosion degree becomes:

$$\psi(z,t)=\psi_{75}\tau f(z/L)$$

where f(z/L) is a prescribed CSF exposure field.

The uniform case is recovered with:

$$f(z/L)=1$$

For a non-uniform axial exposure, f(z/L) can be prescribed as a localized, plateau, lookup-table, or multi-zone field. In all cases, the degradation laws remain functions of psi, while CSF supplies the axial field through psi(z,t).

## Notes for use in CSF

For section-property maps:

- use r_cover for `cover_outer` and `cover_inner`
- use r_core for `core_inner` and `pcbar_host_layer`
- use r_bar_A for the discrete PC-bars

For strength-limit maps:

- use r_bar_fy for the degraded PC-bar yield limit
- do not merge r_bar_A and r_bar_fy into a single factor unless the modelling assumption is stated explicitly

For bond degradation:

- bond strength is an interface property between PC-bar and concrete
- it is not a pure cross-sectional area or inertia factor
- it should be handled separately from A, Ix, Iy, and elastic sectional participation
