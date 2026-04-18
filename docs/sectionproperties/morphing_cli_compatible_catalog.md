# == DRAFT ==
`sectionproperties` is used as the analysis backend for the generated/interpolated sections. 
Please refer to the original project and its license:
https://github.com/robbievanleeuwen/section-properties
# CLI-compatible morphing catalog for `sp_csf`

## Scope

This tool currently targets **single, non-composite sections** from the `sectionproperties` catalog.

The supported workflow is the current **scalar CLI style**:

```text
section_name --morph other_section --s0 key=value,... --s1 key=value,...
```

### What this means

- `sp_csf` does **not** define its own section catalog.
- The section name is passed through to `sectionproperties.pre.library`.
- If a section constructor exists there, `sp_csf` can attempt to use it.
- The current scope is limited to **catalog-based single sections** that fit this scalar parameter style.
- This includes the current prismatic, tapered, and supported morphing workflows already implemented in `sp_csf`.

### What is outside the current scope

- composite sections
- generic `Geometry` / `CompoundGeometry` construction
- a separate geometric DSL
- high-level generic section building beyond the current catalog-style interface

### Practical implication

`sp_csf` should currently be understood as:

**a bridge from the `sectionproperties` catalog of single sections to CSF YAML**

not as a general-purpose builder for arbitrary SP geometries.

The examples avoid section constructors that require Python lists, custom material objects, or manual geometry composition.

## Important rule

This catalog is for `--morph` cases, not same-family tapered cases.

For real tapered members, prefer the same section function at `S0` and `S1` and preserve native vertex mapping.

For morphology changes, use one of:

```text
--morph-mode perimeter
--morph-mode feature
```

`feature` should be used only for section pairs explicitly supported by the current `sp_csf` implementation.

## Excluded from this catalog

Excluded cases:

```text
solid -> hollow
hollow -> solid
single polygon -> multiple polygons
sections requiring Python lists/material objects
concrete reinforced sections with bar sub-geometries
CLT sections requiring layer/material lists
```

Reason: the current CLI parser accepts scalar `key=value` parameters, and the morph builder requires compatible polygon/hole layout.

---

# Feature-mode morphology changes

## F01. `i_section -> tee_section`

Recommended mode: `feature`

Note: Bottom flange disappears; this requires block-based mapping.

```bash
python3 -m csf.utils.sp_csf i_section \
  --morph tee_section \
  --s0 d=240,b=120,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=200,b=120,t_f=12,t_w=8,r=10,n_r=8,z=10 \
  --n=96 \
  --out=f01_i_section_to_tee_section.yaml \
  --gen-actions \
  --morph-mode feature
```

## F02. `tee_section -> i_section`

Recommended mode: `feature`

Note: Bottom flange appears; this requires block-based mapping.

```bash
python3 -m csf.utils.sp_csf tee_section \
  --morph i_section \
  --s0 d=200,b=120,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=240,b=120,t_f=12,t_w=8,r=10,n_r=8,z=10 \
  --n=96 \
  --out=f02_tee_section_to_i_section.yaml \
  --gen-actions \
  --morph-mode feature
```

## F03. `i_section -> channel_section`

Recommended mode: `feature`

Note: One side opens; this is not a simple perimeter morph.

```bash
python3 -m csf.utils.sp_csf i_section \
  --morph channel_section \
  --s0 d=240,b=120,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=240,b=100,t_f=12,t_w=8,r=10,n_r=8,z=10 \
  --n=96 \
  --out=f03_i_section_to_channel_section.yaml \
  --gen-actions \
  --morph-mode feature
```

## F04. `channel_section -> i_section`

Recommended mode: `feature`

Note: A missing side appears; this requires controlled feature mapping.

```bash
python3 -m csf.utils.sp_csf channel_section \
  --morph i_section \
  --s0 d=240,b=100,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=240,b=120,t_f=12,t_w=8,r=10,n_r=8,z=10 \
  --n=96 \
  --out=f04_channel_section_to_i_section.yaml \
  --gen-actions \
  --morph-mode feature
```

## F05. `i_section -> rectangular_section`

Recommended mode: `feature`

Note: Open-profile features collapse into a solid rectangular outline.

```bash
python3 -m csf.utils.sp_csf i_section \
  --morph rectangular_section \
  --s0 d=240,b=120,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=220,b=120,z=10 \
  --n=96 \
  --out=f05_i_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode feature
```

## F06. `rectangular_section -> i_section`

Recommended mode: `feature`

Note: I-section flanges/web emerge from a rectangular outline.

```bash
python3 -m csf.utils.sp_csf rectangular_section \
  --morph i_section \
  --s0 d=220,b=120,z=0 \
  --s1 d=240,b=120,t_f=12,t_w=8,r=10,n_r=8,z=10 \
  --n=96 \
  --out=f06_rectangular_section_to_i_section.yaml \
  --gen-actions \
  --morph-mode feature
```

## F07. `channel_section -> rectangular_section`

Recommended mode: `feature`

Note: Open side closes into a rectangular outline.

```bash
python3 -m csf.utils.sp_csf channel_section \
  --morph rectangular_section \
  --s0 d=220,b=100,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=220,b=110,z=10 \
  --n=96 \
  --out=f07_channel_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode feature
```

## F08. `rectangular_section -> channel_section`

Recommended mode: `feature`

Note: Rectangular outline opens into a channel section.

```bash
python3 -m csf.utils.sp_csf channel_section \
  --morph rectangular_section \
  --s0 d=220,b=100,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=220,b=110,z=10 \
  --n=96 \
  --out=f07_channel_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode feature
```

# Solid primitive morphs

## P01. `rectangular_section -> circular_section`

Recommended mode: `perimeter`

Note: Solid rectangle to solid circle.

```bash
python3 -m csf.utils.sp_csf rectangular_section \
  --morph circular_section \
  --s0 d=220,b=140,z=0 \
  --s1 d=180,n=96,z=10 \
  --n=96 \
  --out=p01_rectangular_section_to_circular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P02. `circular_section -> rectangular_section`

Recommended mode: `perimeter`

Note: Solid circle to solid rectangle.

```bash
python3 -m csf.utils.sp_csf circular_section \
  --morph rectangular_section \
  --s0 d=180,n=96,z=0 \
  --s1 d=220,b=140,z=10 \
  --n=96 \
  --out=p02_circular_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P03. `rectangular_section -> elliptical_section`

Recommended mode: `perimeter`

Note: Solid rectangle to solid ellipse.

```bash
python3 -m csf.utils.sp_csf rectangular_section \
  --morph elliptical_section \
  --s0 d=220,b=140,z=0 \
  --s1 d_x=220,d_y=140,n=96,z=10 \
  --n=96 \
  --out=p03_rectangular_section_to_elliptical_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P04. `elliptical_section -> rectangular_section`

Recommended mode: `perimeter`

Note: Solid ellipse to solid rectangle.

```bash
python3 -m csf.utils.sp_csf elliptical_section \
  --morph rectangular_section \
  --s0 d_x=220,d_y=140,n=96,z=0 \
  --s1 d=220,b=140,z=10 \
  --n=96 \
  --out=p04_elliptical_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P05. `circular_section -> elliptical_section`

Recommended mode: `perimeter`

Note: Solid circle to solid ellipse.

```bash
python3 -m csf.utils.sp_csf circular_section \
  --morph elliptical_section \
  --s0 d=180,n=96,z=0 \
  --s1 d_x=240,d_y=140,n=96,z=10 \
  --n=96 \
  --out=p05_circular_section_to_elliptical_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P06. `elliptical_section -> circular_section`

Recommended mode: `perimeter`

Note: Solid ellipse to solid circle.

```bash
python3 -m csf.utils.sp_csf elliptical_section \
  --morph circular_section \
  --s0 d_x=240,d_y=140,n=96,z=0 \
  --s1 d=180,n=96,z=10 \
  --n=96 \
  --out=p06_elliptical_section_to_circular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P07. `rectangular_section -> triangular_section`

Recommended mode: `perimeter`

Note: Solid rectangle to solid triangle.

```bash
python3 -m csf.utils.sp_csf rectangular_section \
  --morph triangular_section \
  --s0 d=220,b=140,z=0 \
  --s1 b=160,h=220,z=10 \
  --n=96 \
  --out=p07_rectangular_section_to_triangular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P08. `triangular_section -> rectangular_section`

Recommended mode: `perimeter`

Note: Solid triangle to solid rectangle.

```bash
python3 -m csf.utils.sp_csf triangular_section \
  --morph rectangular_section \
  --s0 b=160,h=220,z=0 \
  --s1 d=220,b=140,z=10 \
  --n=96 \
  --out=p08_triangular_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P09. `rectangular_section -> triangular_radius_section`

Recommended mode: `perimeter`

Note: Solid rectangle to rounded triangular section.

```bash
python3 -m csf.utils.sp_csf rectangular_section \
  --morph triangular_radius_section \
  --s0 d=220,b=140,z=0 \
  --s1 b=180,n_r=16,z=10 \
  --n=96 \
  --out=p09_rectangular_section_to_triangular_radius_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P10. `triangular_radius_section -> rectangular_section`

Recommended mode: `perimeter`

Note: Rounded triangular section to solid rectangle.

```bash
python3 -m csf.utils.sp_csf triangular_radius_section \
  --morph rectangular_section \
  --s0 b=180,n_r=16,z=0 \
  --s1 d=220,b=140,z=10 \
  --n=96 \
  --out=p10_triangular_radius_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P11. `rectangular_section -> cruciform_section`

Recommended mode: `perimeter`

Note: Solid rectangle to cruciform section.

```bash
python3 -m csf.utils.sp_csf rectangular_section \
  --morph cruciform_section \
  --s0 d=220,b=140,z=0 \
  --s1 d=220,b=160,t=28,r=12,n_r=8,z=10 \
  --n=96 \
  --out=p11_rectangular_section_to_cruciform_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## P12. `cruciform_section -> rectangular_section`

Recommended mode: `perimeter`

Note: Cruciform section to solid rectangle.

```bash
python3 -m csf.utils.sp_csf cruciform_section \
  --morph rectangular_section \
  --s0 d=220,b=160,t=28,r=12,n_r=8,z=0 \
  --s1 d=220,b=140,z=10 \
  --n=96 \
  --out=p12_cruciform_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

# Hollow-to-hollow morphs

## H01. `circular_hollow_section -> rectangular_hollow_section`

Recommended mode: `perimeter`

Note: Both sections have one exterior ring and one inner void.

```bash
python3 -m csf.utils.sp_csf circular_hollow_section \
  --morph rectangular_hollow_section \
  --s0 d=300,t=12,n=128,z=0 \
  --s1 d=280,b=180,t=10,r_out=18,n_r=12,z=10 \
  --n=128 \
  --out=h01_circular_hollow_section_to_rectangular_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H02. `rectangular_hollow_section -> circular_hollow_section`

Recommended mode: `perimeter`

Note: Both sections have one exterior ring and one inner void.

```bash
python3 -m csf.utils.sp_csf rectangular_hollow_section \
  --morph circular_hollow_section \
  --s0 d=280,b=180,t=10,r_out=18,n_r=12,z=0 \
  --s1 d=300,t=12,n=128,z=10 \
  --n=128 \
  --out=h02_rectangular_hollow_section_to_circular_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H03. `circular_hollow_section -> elliptical_hollow_section`

Recommended mode: `perimeter`

Note: Round hollow tube to elliptical hollow tube.

```bash
python3 -m csf.utils.sp_csf circular_hollow_section \
  --morph elliptical_hollow_section \
  --s0 d=300,t=12,n=128,z=0 \
  --s1 d_x=320,d_y=200,t=10,n=128,z=10 \
  --n=128 \
  --out=h03_circular_hollow_section_to_elliptical_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H04. `elliptical_hollow_section -> circular_hollow_section`

Recommended mode: `perimeter`

Note: Elliptical hollow tube to round hollow tube.

```bash
python3 -m csf.utils.sp_csf elliptical_hollow_section \
  --morph circular_hollow_section \
  --s0 d_x=320,d_y=200,t=10,n=128,z=0 \
  --s1 d=300,t=12,n=128,z=10 \
  --n=128 \
  --out=h04_elliptical_hollow_section_to_circular_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H05. `rectangular_hollow_section -> elliptical_hollow_section`

Recommended mode: `perimeter`

Note: Rectangular hollow tube to elliptical hollow tube.

```bash
python3 -m csf.utils.sp_csf rectangular_hollow_section \
  --morph elliptical_hollow_section \
  --s0 d=280,b=180,t=10,r_out=18,n_r=12,z=0 \
  --s1 d_x=320,d_y=200,t=10,n=128,z=10 \
  --n=128 \
  --out=h05_rectangular_hollow_section_to_elliptical_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H06. `elliptical_hollow_section -> rectangular_hollow_section`

Recommended mode: `perimeter`

Note: Elliptical hollow tube to rectangular hollow tube.

```bash
python3 -m csf.utils.sp_csf elliptical_hollow_section \
  --morph rectangular_hollow_section \
  --s0 d_x=320,d_y=200,t=10,n=128,z=0 \
  --s1 d=280,b=180,t=10,r_out=18,n_r=12,z=10 \
  --n=128 \
  --out=h06_elliptical_hollow_section_to_rectangular_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H07. `polygon_hollow_section -> circular_hollow_section`

Recommended mode: `perimeter`

Note: Polygonal hollow tower section to circular hollow section.

```bash
python3 -m csf.utils.sp_csf polygon_hollow_section \
  --morph circular_hollow_section \
  --s0 d=320,t=12,n_sides=8,r_in=8,n_r=8,rot=0,z=0 \
  --s1 d=200,t=12,n=128,z=10 \
  --n=128 \
  --out=h07_polygon_hollow_section_to_circular_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H08. `circular_hollow_section -> polygon_hollow_section`

Recommended mode: `perimeter`

Note: Circular hollow section to polygonal hollow tower section.

```bash
python3 -m csf.utils.sp_csf circular_hollow_section \
  --morph polygon_hollow_section \
  --s0 d=300,t=12,n=128,z=0 \
  --s1 d=320,t=12,n_sides=8,r_in=8,n_r=8,rot=0,z=10 \
  --n=128 \
  --out=h08_circular_hollow_section_to_polygon_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H09. `polygon_hollow_section -> rectangular_hollow_section`

Recommended mode: `perimeter`

Note: Polygonal hollow section to rectangular hollow section.

```bash
python3 -m csf.utils.sp_csf polygon_hollow_section \
  --morph rectangular_hollow_section \
  --s0 d=320,t=12,n_sides=8,r_in=8,n_r=8,rot=0,z=0 \
  --s1 d=280,b=180,t=10,r_out=18,n_r=12,z=10 \
  --n=128 \
  --out=h09_polygon_hollow_section_to_rectangular_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## H10. `rectangular_hollow_section -> polygon_hollow_section`

Recommended mode: `perimeter`

Note: Rectangular hollow section to polygonal hollow section.

```bash
python3 -m csf.utils.sp_csf rectangular_hollow_section \
  --morph polygon_hollow_section \
  --s0 d=280,b=180,t=10,r_out=18,n_r=12,z=0 \
  --s1 d=320,t=12,n_sides=8,r_in=8,n_r=8,rot=0,z=10 \
  --n=128 \
  --out=h10_rectangular_hollow_section_to_polygon_hollow_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```


## H11. `hexagonal-to-circular hollow tower`

Note: Hexagonal hollow base tapering to circular hollow top over 80 m:

```bash
python3 -m csf.utils.sp_csf polygon_hollow_section \
  --morph circular_hollow_section \
  --s0 d=5.0,t=0.035,n_sides=6,r_in=0,n_r=8,z=0 \
  --s1 d=3.5,t=0.022,n=48,z=80 \
  --n=96 --name=tower \
  --out=tower_poly_to_round.yaml \
  --gen-actions
```


## H12. `rounded square hollow to circular hollow tower`

Note: Rounded square hollow base tapering to circular hollow top over 80: 

```bash
python3 -m csf.utils.sp_csf rectangular_hollow_section \
  --morph circular_hollow_section \
  --s0 d=4.2,b=4.2,t=0.028,r_out=0.30,n_r=16,z=0 \
  --s1 d=2.2,t=0.014,n=48,z=80 \
  --n=96 --name=tower --gen-actions \
  --out=tower.yaml
```

# Open steel morphs

## S01. `channel_section -> tee_section` - x

Recommended mode: `perimeter`

Note: Open profile to open profile; inspect 3D output.

```bash
python3 -m csf.utils.sp_csf channel_section \
  --morph tee_section \
  --s0 d=220,b=100,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=200,b=120,t_f=12,t_w=8,r=10,n_r=8,z=10 \
  --n=96 \
  --out=s01_channel_section_to_tee_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## S02. `tee_section -> channel_section` -x 

Recommended mode: `perimeter`

Note: Open profile to open profile; inspect 3D output.

```bash
python3 -m csf.utils.sp_csf tee_section \
  --morph channel_section \
  --s0 d=200,b=120,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=220,b=100,t_f=12,t_w=8,r=10,n_r=8,z=10 \
  --n=96 \
  --out=s02_tee_section_to_channel_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## S03. `tee_section -> angle_section` - x

Recommended mode: `perimeter`

Note: Tee to angle visual morph.

```bash
python3 -m csf.utils.sp_csf tee_section \
  --morph angle_section \
  --s0 d=200,b=120,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=160,b=120,t=10,r_r=8,r_t=4,n_r=8,z=10 \
  --n=96 \
  --out=s03_tee_section_to_angle_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## S04. `angle_section -> tee_section` + x

Recommended mode: `perimeter`

Note: Angle to tee visual morph.

```bash
python3 -m csf.utils.sp_csf angle_section \
  --morph tee_section \
  --s0 d=160,b=120,t=10,r_r=8,r_t=4,n_r=8,z=0 \
  --s1 d=200,b=120,t_f=12,t_w=8,r=10,n_r=8,z=10 \
  --n=96 \
  --out=s04_angle_section_to_tee_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## S05. `cee_section -> zed_section` -x 

Recommended mode: `perimeter`

Note: Cold-formed C to Z visual morph.

```bash
python3 -m csf.utils.sp_csf cee_section \
  --morph zed_section \
  --s0 d=160,b=60,l=25,t=2.5,r_out=6,n_r=8,z=0 \
  --s1 d=160,b_l=55,b_r=65,l=22,t=2.5,r_out=6,n_r=8,z=10 \
  --n=96 \
  --out=s05_cee_section_to_zed_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## S06. `zed_section -> cee_section` -x 

Recommended mode: `perimeter`

Note: Cold-formed Z to C visual morph.

```bash
python3 -m csf.utils.sp_csf zed_section \
  --morph cee_section \
  --s0 d=160,b_l=55,b_r=65,l=22,t=2.5,r_out=6,n_r=8,z=0 \
  --s1 d=160,b=60,l=25,t=2.5,r_out=6,n_r=8,z=10 \
  --n=96 \
  --out=s06_zed_section_to_cee_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## S07. `angle_section -> rectangular_section` -x 

Recommended mode: `perimeter`

Note: Angle to solid rectangle; visual reduction.

```bash
python3 -m csf.utils.sp_csf angle_section \
  --morph rectangular_section \
  --s0 d=160,b=120,t=10,r_r=8,r_t=4,n_r=8,z=0 \
  --s1 d=180,b=120,z=10 \
  --n=96 \
  --out=s07_angle_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## S08. `tee_section -> rectangular_section`

Recommended mode: `perimeter`

Note: Tee to solid rectangle; visual reduction.

```bash
python3 -m csf.utils.sp_csf tee_section \
  --morph rectangular_section \
  --s0 d=200,b=120,t_f=12,t_w=8,r=10,n_r=8,z=0 \
  --s1 d=200,b=120,z=10 \
  --n=96 \
  --out=s08_tee_section_to_rectangular_section.yaml \
  --gen-actions \
  --morph-mode perimeter
```

# NASTRAN scalar morphs

## N01. `nastran_i -> nastran_h` -x 

Recommended mode: `perimeter`

Note: Solver-oriented I/H open-section morph.

```bash
python3 -m csf.utils.sp_csf nastran_i \
  --morph nastran_h \
  --s0 dim_1=5.0,dim_2=2.0,dim_3=3.0,dim_4=0.25,dim_5=0.375,dim_6=0.5,z=0 \
  --s1 dim_1=2.0,dim_2=0.75,dim_3=3.5,dim_4=0.2,z=10 \
  --n=96 \
  --out=n01_nastran_i_to_nastran_h.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N02. `nastran_h -> nastran_i` -x

Recommended mode: `perimeter`

Note: Solver-oriented H/I open-section morph.

```bash
python3 -m csf.utils.sp_csf nastran_h \
  --morph nastran_i \
  --s0 dim_1=2.0,dim_2=0.75,dim_3=3.5,dim_4=0.2,z=0 \
  --s1 dim_1=5.0,dim_2=2.0,dim_3=3.0,dim_4=0.25,dim_5=0.375,dim_6=0.5,z=10 \
  --n=96 \
  --out=n02_nastran_h_to_nastran_i.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N03. `nastran_chan -> nastran_tee` -x

Recommended mode: `perimeter`

Note: Solver-oriented channel to tee morph.

```bash
python3 -m csf.utils.sp_csf nastran_chan \
  --morph nastran_tee \
  --s0 dim_1=2.0,dim_2=4.0,dim_3=0.25,dim_4=0.5,z=0 \
  --s1 dim_1=3.0,dim_2=4.0,dim_3=0.375,dim_4=0.25,z=10 \
  --n=96 \
  --out=n03_nastran_chan_to_nastran_tee.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N04. `nastran_tee -> nastran_chan` -x

Recommended mode: `perimeter`

Note: Solver-oriented tee to channel morph.

```bash
python3 -m csf.utils.sp_csf nastran_tee \
  --morph nastran_chan \
  --s0 dim_1=3.0,dim_2=4.0,dim_3=0.375,dim_4=0.25,z=0 \
  --s1 dim_1=2.0,dim_2=4.0,dim_3=0.25,dim_4=0.5,z=10 \
  --n=96 \
  --out=n04_nastran_tee_to_nastran_chan.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N05. `nastran_l -> nastran_tee` -x

Recommended mode: `perimeter`

Note: Solver-oriented L to tee morph.

```bash
python3 -m csf.utils.sp_csf nastran_l \
  --morph nastran_tee \
  --s0 dim_1=3.0,dim_2=6.0,dim_3=0.375,dim_4=0.625,z=0 \
  --s1 dim_1=3.0,dim_2=4.0,dim_3=0.375,dim_4=0.25,z=10 \
  --n=96 \
  --out=n05_nastran_l_to_nastran_tee.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N06. `nastran_tee -> nastran_l` -x

Recommended mode: `perimeter`

Note: Solver-oriented tee to L morph.

```bash
python3 -m csf.utils.sp_csf nastran_tee \
  --morph nastran_l \
  --s0 dim_1=3.0,dim_2=4.0,dim_3=0.375,dim_4=0.25,z=0 \
  --s1 dim_1=3.0,dim_2=6.0,dim_3=0.375,dim_4=0.625,z=10 \
  --n=96 \
  --out=n06_nastran_tee_to_nastran_l.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N07. `nastran_hat -> nastran_zed` -x

Recommended mode: `perimeter`

Note: Folded thin-walled hat to zed morph.

```bash
python3 -m csf.utils.sp_csf nastran_hat \
  --morph nastran_zed \
  --s0 dim_1=1.25,dim_2=0.25,dim_3=1.5,dim_4=0.5,z=0 \
  --s1 dim_1=1.125,dim_2=0.5,dim_3=3.5,dim_4=4.0,z=10 \
  --n=96 \
  --out=n07_nastran_hat_to_nastran_zed.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N08. `nastran_zed -> nastran_hat` -x

Recommended mode: `perimeter`

Note: Folded thin-walled zed to hat morph.

```bash
python3 -m csf.utils.sp_csf nastran_zed \
  --morph nastran_hat \
  --s0 dim_1=1.125,dim_2=0.5,dim_3=3.5,dim_4=4.0,z=0 \
  --s1 dim_1=1.25,dim_2=0.25,dim_3=1.5,dim_4=0.5,z=10 \
  --n=96 \
  --out=n08_nastran_zed_to_nastran_hat.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N09. `nastran_box -> nastran_tube`

Recommended mode: `perimeter`

Note: Closed box to circular tube; both should retain one void.

```bash
python3 -m csf.utils.sp_csf nastran_box \
  --morph nastran_tube \
  --s0 dim_1=4.0,dim_2=3.0,dim_3=0.375,dim_4=0.5,z=0 \
  --s1 dim_1=3.0,dim_2=2.5,n=128,z=10 \
  --n=96 \
  --out=n09_nastran_box_to_nastran_tube.yaml \
  --gen-actions \
  --morph-mode perimeter
```

## N10. `nastran_tube -> nastran_box`

Recommended mode: `perimeter`

Note: Circular tube to closed box; both should retain one void.

```bash
python3 -m csf.utils.sp_csf nastran_tube \
  --morph nastran_box \
  --s0 dim_1=3.0,dim_2=2.5,n=128,z=0 \
  --s1 dim_1=4.0,dim_2=3.0,dim_3=0.375,dim_4=0.5,z=10 \
  --n=96 \
  --out=n10_nastran_tube_to_nastran_box.yaml \
  --gen-actions \
  --morph-mode perimeter
```

# Practical checks after generation

For every generated geometry:

```bash
csf-actions <geometry.yaml> <geometry_actions.yaml>
```

Minimum checks:

```text
plot_volume_3d
plot_section_2d
plot_properties
```

If ruled lines cross or `plot_properties` fails, the morph is geometrically invalid for that pair/mode.

# Recommended interpretation

Use these commands as CLI-compatible morphing test cases.

For production-like tapered members, use the tapered same-family catalog instead.
