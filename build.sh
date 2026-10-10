#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
  latexmk -pdf -interaction=nonstopmode -halt-on-error main-clean.tex
elif command -v pdflatex >/dev/null 2>&1 && command -v bibtex >/dev/null 2>&1; then
  for document in main main-clean; do
    pdflatex -interaction=nonstopmode -halt-on-error "$document.tex"
    bibtex "$document"
    pdflatex -interaction=nonstopmode -halt-on-error "$document.tex"
    pdflatex -interaction=nonstopmode -halt-on-error "$document.tex"
  done
else
  echo 'No LaTeX compiler found. Import arr_revision_review.zip into Overleaf and select main.tex (marked) or main-clean.tex (clean color).'
  exit 2
fi
