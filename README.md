# premise_credibility_ARR

ARR two-column migration of `../premise_credibility_NIPS_preprint/main.tex`, using `acl.sty` and `acl_natbib.bst` from the supplied `acl-style-files-master.zip`.

## Build

Open `main.tex` in Overleaf and select pdfLaTeX, or use a TeX Live installation:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Without latexmk, run `pdflatex main`, `bibtex main`, then `pdflatex main` twice.

The default is anonymous review mode with line numbers. Change `\usepackage[review]{acl}` to `[preprint]` for a version showing the original authors, or `[final]` for camera-ready formatting.

The main text and appendices remain in two columns. Wide figures and tables span both columns; wrapped figures become column-width floats. The manuscript, bibliography, and figure assets are preserved, with layout changes and removal of the NeurIPS-specific ethics-policy attribution. The NeurIPS checklist was inactive in the source and is not included.

Validation: source references, assets, and environment balance checked locally. This environment has no LaTeX compiler, so compilation, page count, float placement, and visual PDF review remain unverified. No content was shortened to meet a page limit.
