# Project 2 Data Visualization Best Practices Audit -- Design Spec

## Goal

Audit and refine every Plotly figure in the Project 2 Dash app to comply
with the visualization best practices from four assigned readings
(Cleveland & McGill 1984, Borner et al. 2019, Borland & Taylor 2007,
Graze & Schwabish 2024). Add code comments citing reading principles in
every visualization function. Write a standalone VISUALIZATION_DESIGN.md
documenting all palette choices, per-figure rationale, and trade-off
justifications for the instructor.

## Readings -- Key Principles (same as Project 1 audit)

### Cleveland & McGill (1984): Graphical Perception Hierarchy

Perceptual accuracy ranking (best to worst):
1. Position along a common scale
2. Positions along nonaligned scales
3. Length, direction, angle
4. Area
5. Volume, curvature
6. Shading, color saturation

**Implications:** Favor bar/dot charts over pie/area charts. Stacked bars
acceptable when the total is the message (Cleveland acknowledges this).
Grouped bars preferred for per-category comparison.

### Borner et al. (2019): Data Visualization Literacy Framework

- Match data type to visual encoding: categorical = distinct hues;
  ordinal = luminance ramps; interval/ratio = sequential or diverging
- Position, size, shape, color/hue are the primary graphic variables

### Borland & Taylor (2007): Rainbow Colormap Considered Harmful

- Rainbow/jet/multi-hue colormaps lack perceptual ordering
- Grayscale and single-hue luminance-varying scales are perceptually ordered
- Diverging palettes: two hues meeting at a neutral midpoint

### Graze & Schwabish (2024): Building Color Palettes

- Three palette types: categorical (distinct hues, <=6), sequential
  (luminance ramp), diverging (two-hue + neutral midpoint)
- Consistency: same palette across all charts in a project
- Accessibility: colorblind-safe, sufficient contrast
- Style guide: define chart sizing, typography, gridlines, labels

## Current App State -- Audit Findings

### Visualization Inventory (10 figures across 4 pages)

| Page | Figure | Function | Chart Type |
|------|--------|----------|------------|
| Landscape | 1 | `_build_network_figure` | Network graph |
| Landscape | 2 | `_build_heatmap_figure` | Heatmap |
| Deep Dive | 3 | `_build_level0` | Radial network |
| Deep Dive | 4 | `_build_level1` | Radial network |
| Deep Dive | 5 | `_build_level2` | Multi-level radial network |
| Deep Dive | 6 | `_build_mapping_bar` | Diverging horizontal bar |
| Explorer | 7 | `_build_sankey` | Sankey diagram |
| Explorer | 8 | `_build_neighborhood` | Radial network |
| Coverage | 9 | `_build_radar` | Radar/polar chart |
| Coverage | 10 | `_build_coverage_bar` | Stacked horizontal bar |

### What's Already Compliant

| Principle | Evidence |
|-----------|----------|
| No pie charts | All part-to-whole uses bars |
| Categorical framework palette | 9 distinct hues in `framework_colors.py`, used consistently |
| Position-along-common-scale dominates | Diverging bar (Fig 6), coverage bar (Fig 10) |
| Shape encoding for type distinction | Circle vs. diamond for direct/transitive (Figs 5, 8) |
| Direct labeling | Heatmap cell counts, bar annotations, hover text throughout |
| Consistent theme | `plot_theme.py` applies uniform dark/light templates |
| Light-theme heatmap uses single-hue ramp | `#f6f8fa -> #a8d8f0 -> #1f6feb -> #0550ae` |
| Sankey uses conventional flow encoding | Width = quantity, standard for this chart type |
| Network sizing is conventional | Area encoding acceptable for navigational network layouts |

### Issues to Fix

**Issue 1 (Medium): Heatmap dark-theme colorscale is multi-hue.**
`[[0, "#161b22"], [0.15, "#1a3a5c"], [0.4, "#1f6feb"], [0.7, "#39d353"],
[1, "#00d4ff"]]` transitions through dark, blue, green, and cyan.
This lacks monotonic luminance ordering. Borland & Taylor: multi-hue
scales without perceptual ordering are harmful for continuous data.
Borner: ratio data requires a sequential scale. Fix: replace with a
single-hue blue luminance ramp.

**Issue 2 (Low): Coverage percentage label colors use red-gold-cyan
traffic light.** `>=60% = #00d4ff, 30-59% = #d9bf55, <30% = #ff6b6b`.
These three thresholds represent ordinal severity (good/medium/poor).
Borner: ordinal data should use luminance variation. Graze & Schwabish:
colorblind-safe required. Red (#ff6b6b) and gold (#d9bf55) are poorly
distinguishable under protanopia. Fix: replace with single-hue
luminance-ordered blue scale.

**Issue 3 (Informational): No style guide documentation.**
Graze & Schwabish emphasize a style guide for multi-chart projects.
Project 1 has a Style Guide notebook cell. Project 2 has well-organized
palette code but no document for the instructor. Fix: write
`project2/VISUALIZATION_DESIGN.md`.

**Issue 4 (Informational): 9-color framework palette exceeds <=6.**
Graze & Schwabish recommend <=6 for categorical palettes. Nine
frameworks require nine colors. Justified exception but needs
documentation.

## Design Decisions

### 1. New heatmap dark-theme colorscale (sequential, single-hue)

Replace the multi-hue scale with a blue luminance ramp:

```python
# Sequential blue luminance ramp for ratio data (mapping density).
# Borland & Taylor (2007): single-hue scales are perceptually ordered.
# Borner et al. (2019): ratio data requires sequential encoding.
colorscale = [
    [0, "#0d1117"],      # Near-black (zero density recedes)
    [0.25, "#0d2847"],   # Very dark blue
    [0.5, "#1a4f7a"],    # Medium blue
    [0.75, "#2878ad"],   # Bright blue
    [1, "#3aa5de"],      # Light blue (highest density pops)
]
```

Single-hue blue, monotonically increasing luminance. Colorblind-safe
by definition. Consistent with the app's blue accent color family.
The light theme colorscale is already compliant and unchanged.

### 2. New coverage label colors (ordinal, luminance-ordered)

Replace the three-hue traffic light with a single-hue blue scheme
where luminance encodes ordinal severity:

```python
# Ordinal coverage labels: luminance encodes "how good is coverage?"
# Borner et al. (2019): ordinal data requires luminance variation.
# Graze & Schwabish (2024): colorblind-safe, single-hue family.
label_color = (
    "#58a6ff"   # >=60% -- bright blue (good)
    "#3a6da0"   # 30-59% -- medium blue (moderate)
    "#1e3a5c"   # <30% -- dark blue (poor)
)
```

Brightest = best coverage (draws attention to strong results).
Darkest = worst coverage (recedes, signaling absence). This matches
the semantic expectation: high coverage is the "signal," low coverage
is the background.

### 3. Coverage stacked bar: keep, document trade-off

The stacked form is justified because the total coverage percentage
is the primary message (direct + transitive + gap = 100%). A grouped
bar would lose the whole-is-the-message affordance. Per Cleveland's
own acknowledgment, stacked bars are appropriate when the total matters
more than per-segment comparison. The percentage annotations at bar
ends provide direct labeling that compensates for off-baseline segments.

Add a code comment citing Cleveland and the Project 1 precedent
(Fig 3.3A).

### 4. Code comments in all 10 visualization functions

Each `_build_*` function gets a 2-4 line comment block at the top
of the function body citing which reading principles it follows.
Style matches Project 1's code comments. Examples:

**Network graphs (Figs 1, 3-5, 8):**
```python
# Encoding: categorical framework colors for nominal identity
# (Borner et al. 2019). Node size encodes breadth via area
# (Cleveland rank 4), acceptable for navigational networks where
# the primary task is exploration, not precise comparison.
```

**Diverging bar (Fig 6):**
```python
# Encoding: position along a common scale (Cleveland & McGill 1984,
# rank 1). Two-category color (blue/green) has sufficient hue and
# luminance separation for colorblind accessibility (Graze &
# Schwabish 2024).
```

**Heatmap (Fig 2):**
```python
# Encoding: sequential single-hue luminance ramp for ratio data
# (Borland & Taylor 2007; Borner et al. 2019). Cell-value
# annotations provide direct labeling to supplement color
# (Cleveland rank 6) with precise numeric readout.
```

**Sankey (Fig 7):**
```python
# Encoding: flow width encodes mapping count (conventional Sankey).
# Two-category color (cyan/green) distinguishes direct vs.
# transitive mappings. Per-framework target colors use the global
# categorical palette (Graze & Schwabish 2024).
```

**Radar (Fig 9):**
```python
# Encoding: angle (Cleveland rank 3). Retained as a complementary
# gestalt/shape view alongside the coverage bar chart (rank 1),
# which provides precise per-framework comparison. Two traces
# (total/direct) use line encoding with distinct line styles.
```

**Stacked bar (Fig 10):**
```python
# Encoding: stacked bar with position along common scale for the
# bottom (direct) segment; upper segments use length without
# baseline (Cleveland rank 3). Stacked form justified because
# the total (100%) is the primary message (Cleveland 1984
# acknowledges this trade-off). Percentage annotations compensate
# for off-baseline segments.
```

### 5. VISUALIZATION_DESIGN.md

A standalone document in `project2/VISUALIZATION_DESIGN.md` structured as:

1. **Palette Definitions** -- framework (categorical, 9-color),
   confidence (ordinal), heatmap (sequential), accent colors. Each
   with type classification, hex values, and reading citation.
2. **Per-Figure Rationale** -- one paragraph per figure explaining
   encoding choices and which reading principles apply.
3. **Trade-Off Documentation** -- stacked bar, radar chart, 9-color
   palette: what the reading says, why we deviate, what mitigations
   are in place.
4. **Colorblind Accessibility** -- which palettes are single-hue
   (inherently safe), which use hue distinction (framework palette),
   and how the 9 colors were selected for maximum separation.
5. **Style Guide** -- typography (font scale, title weight), gridlines,
   hover conventions, annotation style, dark/light theme handling.

## Files Modified

| File | Change |
|------|--------|
| `project2/pages/landscape.py` | Heatmap colorscale fix + code comments (Figs 1-2) |
| `project2/pages/deep_dive.py` | Code comments (Figs 3-6) |
| `project2/pages/explorer.py` | Code comments (Figs 7-8) |
| `project2/pages/coverage.py` | Label color fix + code comments (Figs 9-10) |
| `project2/VISUALIZATION_DESIGN.md` | New file: full design rationale |
| `project2/components/framework_colors.py` | Code comment documenting palette rationale |

## Testing Plan

1. **App startup test**: `python project2/app.py` starts without errors.
2. **Visual regression**: Screenshot each page before/after. Compare
   heatmap colorscale and coverage label colors side-by-side.
3. **Dark/light theme toggle**: Verify both themes render correctly
   on all 4 pages after changes.
4. **Heatmap cell values**: Verify annotation counts still match
   the computed pairwise density (already validated this session).
5. **Coverage bar labels**: Verify percentage annotations still
   appear with correct values and the new ordinal blue colors.
6. **No functional regressions**: Click through all drill-down
   levels on Deep Dive, verify Sankey + neighborhood on Explorer,
   verify radar + bar on Coverage.

## Scope

- 2 functional code changes (heatmap scale, label colors)
- ~10 code comment blocks added across 4 page files
- 1 comment block in framework_colors.py
- 1 new markdown file (VISUALIZATION_DESIGN.md)
- No data changes, no layout changes, no new dependencies
