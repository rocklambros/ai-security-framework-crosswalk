# Paper Build Instructions

## Prerequisites

- A LaTeX distribution (e.g., TeX Live, MiKTeX)
- `latexmk` (included in most TeX distributions)

## Build

```bash
cd paper/
latexmk -pdf main.tex
```

Or from the repository root:

```bash
make paper
```

## Clean

```bash
latexmk -C
```
