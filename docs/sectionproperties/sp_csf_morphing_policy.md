# == DRAFT ==
# Morphing policy for `sp_csf`

## Purpose

This note defines the intended behavior of `--morph-mode` in `sp_csf`.

The main goal is to protect the cases that are technically most important and most realistic: tapered and prismatic members of the same section family.

---

## Core rule

For same-family sections, the native `sectionproperties` vertex order must be preserved.

Examples:

```bash
i_section -> i_section
channel_section -> channel_section
circular_hollow_section -> circular_hollow_section
rectangular_hollow_section -> rectangular_hollow_section
```

These cases must not be resampled globally and must not pass through feature morphing.

They represent the most important real use case:

```text
same section type
different dimensions
same parametric topology
```

For these cases, the correct mapping is:

```text
S0 native vertex i  ->  S1 native vertex i
```

---

## Proposed `--morph-mode` options

### 1. `perimeter`

```bash
--morph-mode perimeter
```

Default mode.

This keeps the historical behavior:

```text
rotate/start-align ring
resample the whole contour to n points by global arc length
map S0[i] -> S1[i]
```

Use as fallback for simple morphs where global perimeter correspondence is acceptable.

This mode must remain the default for backward compatibility.

---

### 2. `native`

```bash
--morph-mode native
```

Preserves the native vertex order from `sectionproperties`.

Required behavior:

```text
no global resampling
no feature morph
no landmark ray logic
no insertion of extra start vertices
```

Allowed operation:

```text
remove duplicated closing point
enforce CCW orientation if needed
apply offset/twist after vertex extraction
```

This is the correct mode for tapered/prismatic same-family cases.

---

### 3. `feature`

```bash
--morph-mode feature
```

Explicit mode for strong morphology changes.

This mode should not be automatic.

It is intended for cases where parts of the section appear, disappear, or collapse, for example:

```text
i_section -> tee_section
channel_section -> i_section
i_section -> channel_section
i_section -> rectangular_section
channel_section -> rectangular_section
```

The mapping must be built by geometric blocks, not by global perimeter fraction.

Example blocks:

```text
top flange
web
bottom flange
open side
appearing side
disappearing side
radii
```

If a block exists in one section but not in the other, it must be mapped to a controlled degenerate target.

Example:

```text
bottom flange of I-section -> degenerate block at web/base target
missing side of channel -> appearing side of I-section
```

Feature morph must fail with a clear error if the section pair is not explicitly supported.

It must not silently invent a mapping.

---

## Priority order

The implementation should follow this priority:

```text
1. Same section type
   -> native mapping

2. Different section type + --morph-mode perimeter
   -> historical global perimeter resampling

3. Different section type + --morph-mode native
   -> native vertex order only if vertex counts are compatible

4. Different section type + --morph-mode feature
   -> explicit block-based feature mapping

5. Unsupported feature pair
   -> clear error
```

---

## Critical constraint

Do not break tapered same-family cases.

This command must remain stable:

```bash
python3 -m csf.utils.sp_csf i_section \
  --s0 d=300,b=150,t_f=15,t_w=10,r=15,n_r=8,z=0 \
  --s1 d=200,b=100,t_f=10,t_w=6,r=12,n_r=8,z=10 \
  --name=beam \
  --out=B2_i_tapered.yaml \
  --gen-actions
```

Expected behavior:

```text
same section type: i_section
mode effectively native
no resampling
no feature morph
no landmark morph
```

---

## Why global resampling is not enough

The historical morphing strategy distributes `n` points uniformly along the complete perimeter.

That is acceptable only when the two contours have compatible perimeter parametrization.

It fails when the morphology changes strongly, because:

```text
same perimeter fraction != same geometric feature
```

Increasing `--n` only increases point density. It does not fix wrong correspondence.

---

## Implementation rule

The safest design is additive:

```text
do not replace existing perimeter morph
do not change same-family tapered behavior
add explicit modes only
make feature morph opt-in
fail clearly for unsupported feature pairs
```

---

## Recommended CLI behavior

Parser:

```python
parser.add_argument(
    "--morph-mode",
    choices=("perimeter", "native", "feature"),
    default="perimeter",
    help=(
        "Morphing strategy: 'perimeter' keeps the historical global "
        "arc-length resampling; 'native' preserves sectionproperties "
        "vertex order; 'feature' uses explicit block-based mappings "
        "for supported strong morphology changes."
    ),
)# Morphing policy for `sp_csf`

## Purpose

This note defines the intended behavior of `--morph-mode` in `sp_csf`.

The main goal is to protect the cases that are technically most important and most realistic: tapered and prismatic members of the same section family.

---

## Core rule

For same-family sections, the native `sectionproperties` vertex order must be preserved.

Examples:

```bash
i_section -> i_section
channel_section -> channel_section
circular_hollow_section -> circular_hollow_section
rectangular_hollow_section -> rectangular_hollow_section
```

These cases must not be resampled globally and must not pass through feature morphing.

They represent the most important real use case:

```text
same section type
different dimensions
same parametric topology
```

For these cases, the correct mapping is:

```text
S0 native vertex i  ->  S1 native vertex i
```

---

## Proposed `--morph-mode` options

### 1. `perimeter`

```bash
--morph-mode perimeter
```

Default mode.

This keeps the historical behavior:

```text
rotate/start-align ring
resample the whole contour to n points by global arc length
map S0[i] -> S1[i]
```

Use as fallback for simple morphs where global perimeter correspondence is acceptable.

This mode must remain the default for backward compatibility.

---

### 2. `native`

```bash
--morph-mode native
```

Preserves the native vertex order from `sectionproperties`.

Required behavior:

```text
no global resampling
no feature morph
no landmark ray logic
no insertion of extra start vertices
```

Allowed operation:

```text
remove duplicated closing point
enforce CCW orientation if needed
apply offset/twist after vertex extraction
```

This is the correct mode for tapered/prismatic same-family cases.

---

### 3. `feature`

```bash
--morph-mode feature
```

Explicit mode for strong morphology changes.

This mode should not be automatic.

It is intended for cases where parts of the section appear, disappear, or collapse, for example:

```text
i_section -> tee_section
channel_section -> i_section
i_section -> channel_section
i_section -> rectangular_section
channel_section -> rectangular_section
```

The mapping must be built by geometric blocks, not by global perimeter fraction.

Example blocks:

```text
top flange
web
bottom flange
open side
appearing side
disappearing side
radii
```

If a block exists in one section but not in the other, it must be mapped to a controlled degenerate target.

Example:

```text
bottom flange of I-section -> degenerate block at web/base target
missing side of channel -> appearing side of I-section
```

Feature morph must fail with a clear error if the section pair is not explicitly supported.

It must not silently invent a mapping.

---

## Priority order

The implementation should follow this priority:

```text
1. Same section type
   -> native mapping

2. Different section type + --morph-mode perimeter
   -> historical global perimeter resampling

3. Different section type + --morph-mode native
   -> native vertex order only if vertex counts are compatible

4. Different section type + --morph-mode feature
   -> explicit block-based feature mapping

5. Unsupported feature pair
   -> clear error
```

---

## Critical constraint

Do not break tapered same-family cases.

This command must remain stable:

```bash
python3 -m csf.utils.sp_csf i_section \
  --s0 d=300,b=150,t_f=15,t_w=10,r=15,n_r=8,z=0 \
  --s1 d=200,b=100,t_f=10,t_w=6,r=12,n_r=8,z=10 \
  --name=beam \
  --out=B2_i_tapered.yaml \
  --gen-actions
```

Expected behavior:

```text
same section type: i_section
mode effectively native
no resampling
no feature morph
no landmark morph
```

---

## Why global resampling is not enough

The historical morphing strategy distributes `n` points uniformly along the complete perimeter.

That is acceptable only when the two contours have compatible perimeter parametrization.

It fails when the morphology changes strongly, because:

```text
same perimeter fraction != same geometric feature
```

Increasing `--n` only increases point density. It does not fix wrong correspondence.

---

## Implementation rule

The safest design is additive:

```text
do not replace existing perimeter morph
do not change same-family tapered behavior
add explicit modes only
make feature morph opt-in
fail clearly for unsupported feature pairs
```

---

## Recommended CLI behavior

Parser:

```python
parser.add_argument(
    "--morph-mode",
    choices=("perimeter", "native", "feature"),
    default="perimeter",
    help=(
        "Morphing strategy: 'perimeter' keeps the historical global "
        "arc-length resampling; 'native' preserves sectionproperties "
        "vertex order; 'feature' uses explicit block-based mappings "
        "for supported strong morphology changes."
    ),
)
```

Decision logic:

```python
if section_s0 == section_s1:
    # Same-family tapered/prismatic case.
    # Always preserve native SP order.
    mode = "native"
elif args.morph_mode == "feature":
    # Explicit block-based morph for supported pairs only.
    mode = "feature"
elif args.morph_mode == "native":
    # Native order only, with compatible vertex counts.
    mode = "native"
else:
    # Backward-compatible fallback.
    mode = "perimeter"
```

---

## Practical recommendation

For real tapered members, use same-family input and rely on native mapping.

For experimental morphology changes, use:

```bash
--morph-mode feature
```

only when the pair is explicitly supported.

For generic visualization-only morphs, use:

```bash
--morph-mode perimeter
```
```

Decision logic:

```python
if section_s0 == section_s1:
    # Same-family tapered/prismatic case.
    # Always preserve native SP order.
    mode = "native"
elif args.morph_mode == "feature":
    # Explicit block-based morph for supported pairs only.
    mode = "feature"
elif args.morph_mode == "native":
    # Native order only, with compatible vertex counts.
    mode = "native"
else:
    # Backward-compatible fallback.
    mode = "perimeter"
```

---

## Practical recommendation

For real tapered members, use same-family input and rely on native mapping.

For experimental morphology changes, use:

```bash
--morph-mode feature
```

only when the pair is explicitly supported.

For generic visualization-only morphs, use:

```bash
--morph-mode perimeter
```
