# Visualization Design Rationale

This document explains the design choices behind every Plotly visualization in the AI Security Crosswalk Explorer, grounded in four assigned readings on data visualization best practices.

## Readings

1. **Cleveland & McGill (1984)** -- Graphical Perception: Theory, Experimentation, and Application to the Development of Graphical Methods. Establishes a perceptual accuracy hierarchy for elementary graphical tasks: position along a common scale (rank 1) > position along nonaligned scales > length, direction, angle > area > volume, curvature > shading, color saturation (rank 6).

2. **Borner et al. (2019)** -- Data Visualization Literacy. Prescribes matching data type to visual encoding: categorical data = distinct hues; ordinal data = luminance ramps; interval/ratio data = sequential or diverging scales.

3. **Borland & Taylor (2007)** -- Rainbow Color Map (Still) Considered Harmful. Demonstrates that multi-hue colormaps without monotonic luminance ordering create perceptual artifacts. Recommends single-hue luminance ramps for sequential data and two-hue diverging scales with a neutral midpoint for diverging data.

4. **Graze & Schwabish (2024)** -- Building Color Palettes in Your Data Visualization Style Guides. Defines three palette types (categorical <=6 hues, sequential luminance ramp, diverging two-hue ramp). Emphasizes consistency across all charts, explicit named palettes, and colorblind accessibility.

---

## Palette Definitions

### Framework Palette (categorical, 9 colors)

Used for nominal framework identity across all pages.

| Framework | Color | Hex |
|-----------|-------|-----|
| AIUC-1 | Blue | `#1f6feb` |
| CSA AICM | Green | `#8fd18f` |
| MITRE ATLAS | Orange | `#e8845a` |
| OWASP AI Exchange | Teal | `#4ecdc4` |
| NIST AI RMF | Magenta | `#cf85c4` |
| EU GPAI CoP | Gold | `#d9bf55` |
| CoSAI Risk Map | Sky Blue | `#7aaed4` |
| OWASP LLM Top 10 | Red | `#ff6b6b` |
| OWASP Agentic Top 10 | Light Orange | `#ffb347` |

**Type:** Categorical. **Reading:** Borner et al. (2019) -- categorical data encoded with distinct hues. Graze & Schwabish (2024) -- named, explicit palette.

**Trade-off:** Nine colors exceed the <=6 recommendation (Graze & Schwabish). Justified because framework identity is the primary categorical variable across all pages. Colors selected for maximum hue and luminance separation across the color wheel to remain distinguishable under deuteranopia and protanopia.

### Confidence Palette (ordinal, 4 levels)

Used for edge confidence badges and filter controls.

| Level | Color | Hex |
|-------|-------|-----|
| Authoritative | Dark Green | `#238636` |
| Expert | Blue | `#1f6feb` |
| Suggestive | Amber | `#d29922` |
| Unvalidated | Gray | `#6e7681` |

**Type:** Ordinal (used in badges, not as primary chart encoding). **Reading:** Borner et al. (2019) -- ordinal data ideally uses luminance variation. These appear as small UI badges rather than quantitative chart encodings, so the hue distinction aids quick identification in context.

### Heatmap Colorscale (sequential, single-hue)

Used for the pairwise mapping density heatmap on the Landscape page.

**Dark theme:**
| Stop | Hex | Purpose |
|------|-----|---------|
| 0.00 | `#0d1117` | Near-black (zero density recedes) |
| 0.25 | `#0d2847` | Very dark blue |
| 0.50 | `#1a4f7a` | Medium blue |
| 0.75 | `#2878ad` | Bright blue |
| 1.00 | `#3aa5de` | Light blue (highest density) |

**Light theme:**
| Stop | Hex | Purpose |
|------|-----|---------|
| 0.00 | `#f6f8fa` | Near-white |
| 0.30 | `#a8d8f0` | Light blue |
| 0.60 | `#1f6feb` | Medium blue |
| 1.00 | `#0550ae` | Dark blue |

**Type:** Sequential. **Reading:** Borland & Taylor (2007) -- single-hue luminance ramp is perceptually ordered. Borner et al. (2019) -- ratio data (mapping counts) requires sequential encoding. Cell-value annotations provide direct labeling to supplement color (Cleveland rank 6) with precise numeric readout.

### Coverage Label Colors (ordinal, single-hue)

Used for percentage annotations on the coverage stacked bar chart.

| Threshold | Color | Hex | Meaning |
|-----------|-------|-----|---------|
| >= 60% | Bright Blue | `#58a6ff` | Good coverage |
| 30-59% | Medium Blue | `#3a6da0` | Moderate coverage |
| < 30% | Dark Blue | `#1e3a5c` | Poor coverage |

**Type:** Ordinal. **Reading:** Borner et al. (2019) -- ordinal data encoded with luminance variation within a single hue family. Graze & Schwabish (2024) -- single-hue family is inherently colorblind-safe.

### Accent Color

| Purpose | Color | Hex |
|---------|-------|-----|
| Interactive highlights, borders, primary accent | Cyan | `#00d4ff` |

Used consistently across all pages for selected states, hover borders, and directional emphasis.

---

## Per-Figure Rationale

### Landscape Page

**Figure 1: Framework Relationship Network** (`_build_network_figure`)

Radial network graph showing 9 frameworks as nodes with cross-framework edges. Node size encodes framework breadth via area (Cleveland rank 4), which is acceptable for navigational networks where the primary task is exploration and framework selection, not precise quantitative comparison. Edge width encodes mapping density proportionally. Categorical framework colors encode nominal identity (Borner et al. 2019). Edge labels at midpoints provide direct count readout. Two edge types (rationale-coded vs. category links) use distinct colors (cyan vs. gold) and line styles (solid vs. dashed) for redundant categorical encoding.

**Figure 2: Pairwise Mapping Density Heatmap** (`_build_heatmap_figure`)

9x9 symmetric heatmap of bidirectional cross-framework mapping counts. Uses a sequential single-hue blue luminance ramp (Borland & Taylor 2007) for ratio data (Borner et al. 2019). Cell-value text annotations provide direct labeling, compensating for color saturation encoding (Cleveland rank 6) with precise numeric readout. The dark theme uses a blue ramp from near-black to light blue; the light theme uses white-to-dark-blue. Both are monotonically ordered in luminance.

### Deep Dive Page

**Figures 3-4: Framework/Domain Networks** (`_build_level0`, `_build_level1`)

Radial networks for drill-down navigation. Level 0 uses domain node size to encode child count (area, Cleveland rank 4) with count labels inside nodes for direct readout. Level 1 uses uniform node size since all children are peers. Both use categorical framework color consistently (Graze & Schwabish 2024). These are navigational interfaces, not quantitative comparison charts, so area encoding is appropriate.

**Figure 5: Control Cross-Framework Network** (`_build_level2`)

Multi-level radial network showing a control's cross-framework mappings. Categorical framework colors encode target framework identity (Borner et al. 2019). Node size encodes mapping count (area, Cleveland rank 4) with count labels for direct readout. Shape encoding distinguishes mapping types: circles = direct mappings, diamonds = transitive mappings (Borner: shape for categorical distinction). Edge width proportional to total mapping count per framework.

**Figure 6: Bidirectional Mapping Bar** (`_build_mapping_bar`)

Diverging horizontal bar chart with outbound mappings extending right (positive) and inbound extending left (negative). Uses position along a common scale (Cleveland rank 1), the most perceptually accurate encoding. Two-category color (blue = outbound, green = inbound) has sufficient hue and luminance separation for colorblind accessibility (Graze & Schwabish 2024). Sorted by total bidirectional count for easy magnitude comparison.

### Explorer Page

**Figure 7: Mapping Flow Sankey** (`_build_sankey`)

Sankey diagram showing flow from source control through mapping tiers (direct/transitive) to target frameworks. Flow width encodes mapping count, which is the conventional Sankey encoding. Two-category color (cyan = direct, green = transitive) distinguishes mapping types. Target framework nodes use the global categorical palette (Graze & Schwabish 2024).

**Figure 8: Control Neighborhood** (`_build_neighborhood`)

Radial network showing direct neighbors (inner ring, solid edges, circles) and transitive neighbors (outer ring, dashed edges, diamonds). Uses redundant encoding channels: ring position, line style, and marker shape all encode the direct/transitive distinction. Framework colors encode nominal identity. This redundancy ensures the mapping type distinction is robust even if one channel is hard to perceive (Borner et al. 2019).

### Coverage Page

**Figure 9: Coverage Radar** (`_build_radar`)

Polar/spider chart showing coverage percentages across target frameworks. Angle encoding ranks 3rd on Cleveland's hierarchy, which is less accurate than position along a common scale. Retained as a complementary gestalt/shape view alongside the coverage bar chart (rank 1), which provides precise per-framework comparison. The radar shows the overall coverage "shape" at a glance, while the bar chart supports detailed analysis. Two traces (total and direct-only) use distinct line styles (solid vs. dotted) for categorical distinction (Graze & Schwabish 2024).

**Figure 10: Coverage Stacked Bar** (`_build_coverage_bar`)

Stacked horizontal bar chart showing direct coverage, transitive coverage, and gap as segments summing to 100%. The bottom (direct) segment shares a common baseline, enabling position encoding (Cleveland rank 1). Upper segments (transitive, gap) require length-without-baseline judgment (Cleveland rank 3). Stacked form is justified because the total coverage percentage is the primary message -- Cleveland (1984) acknowledges that stacked bars are appropriate when the whole is more important than individual segments. Percentage annotations at bar ends provide direct labeling that compensates for off-baseline segments. Label colors use ordinal luminance within a single blue hue family (Borner et al. 2019) to encode coverage quality (bright = good, dark = poor), ensuring colorblind accessibility (Graze & Schwabish 2024).

---

## Colorblind Accessibility

| Palette | Type | Colorblind Safety |
|---------|------|-------------------|
| Framework (9 colors) | Categorical | Hue + luminance separation tested against deuteranopia/protanopia simulation |
| Heatmap (blue ramp) | Sequential | Single-hue, inherently safe |
| Coverage labels (blue ramp) | Ordinal | Single-hue, inherently safe |
| Confidence (4 colors) | Ordinal/badge | Used in small UI elements, not as primary chart encoding |
| Direct/transitive (cyan/green) | Categorical (2) | Sufficient luminance contrast; also distinguished by shape and line style |

---

## Style Guide

### Typography
- Title font size: 14px
- Axis label size: default (Plotly template)
- Annotation font size: 9-11px
- Hover text: HTML-formatted with bold labels
- Font family: system default (clean sans-serif)

### Grid and Background
- Dark theme: `#0d1117` background, `#21262d` gridlines
- Light theme: `#ffffff` background, `#d1d9e0` gridlines
- Grid style: subtle, low-contrast for minimal visual interference

### Hover Conventions
- Bold entity name on first line
- Key metric on second line
- Italic click instruction on third line (for interactive elements)
- `<extra></extra>` to suppress Plotly's default trace name box

### Annotation Style
- Direct count labels inside nodes (white text on colored background)
- Percentage labels outside bar ends (ordinal blue luminance)
- Edge count labels at edge midpoints (gray text, small font)

### Chart Sizing
- Standard height: 550px (network graphs, heatmap, radar, bars)
- Reduced height: 500px (secondary panels)
- Consistent margins: `t=50, b=10-40, l=10-40, r=10-20`

### Interactivity
- Dragmode: `pan` for network graphs (avoid accidental zoom)
- Hovermode: `closest` for networks and scatter
- Click-through drill-down on Deep Dive (Level 0 -> 1 -> 2)
- Click-to-detail on Coverage and Landscape heatmap
