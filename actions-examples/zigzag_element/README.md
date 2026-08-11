# Zigzag Stacked Member

[**Zigzag element example**](https://github.com/giovanniboscu/continuous-section-field/tree/main/actions-examples/zigzag_element)

This example demonstrates how two `ContinuousSectionField` elements can be assembled with `CSFStacked` to form a globally non-straight member.

Each individual CSF element is defined along a straight longitudinal coordinate, but the cross-section can move transversely between its end stations.

In this example:

- the first element moves the rectangular section outward from `S0` to `S1`;
- the second element starts exactly from the same section:

  `S1 (element 1) = S0 (element 2)`

- the second element then moves the section back toward the original position.

The assembled geometry therefore forms a continuous zigzag-shaped member.

## Files

- `element_1.yaml` - first CSF element
- `element_2.yaml` - second CSF element
- `assemble.py` - loads and joins the two elements with `CSFStacked`

## Run

```bash
python3 zigzag.py
```

The script displays the assembled 3D geometry.

## What this example shows

`CSFStacked` is not limited to globally straight members. Straight CSF segments can be continuously assembled to represent piecewise non-straight geometries.
