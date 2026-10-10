#!/usr/bin/env python3
"""Build a source diff with red changes and a portable Overleaf review ZIP."""
from pathlib import Path
import difflib
import re
import zipfile

P=Path(__file__).resolve().parents[2]

def expand(path):
    s=path.read_text()
    def read(m):
        q=P/m[1]
        if not q.suffix: q=q.with_suffix('.tex')
        return expand(q)
    return re.sub(r'(?m)^[ \t]*\\input\{([^}]+)\}[ \t]*$',read,s)

old=(P/'revision/baseline/main.tex').read_text()
new=expand(P/'main.tex')
body=difflib.HtmlDiff(wrapcolumn=90).make_table(old.splitlines(),new.splitlines(),
    fromdesc='Archived baseline',todesc='Revised manuscript (inputs expanded)',context=True,numlines=3)
bib=difflib.HtmlDiff(wrapcolumn=90).make_table((P/'revision/baseline/citation.bib').read_text().splitlines(),
    (P/'citation.bib').read_text().splitlines(),fromdesc='Original bibliography',todesc='Revised bibliography',context=True,numlines=2)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>ARR manuscript revision review</title>
<style>body{font:16px system-ui,sans-serif;margin:2rem;color:#202020;background:white}h1{font-size:1.6rem}
p{max-width:85ch;line-height:1.5}.diff{font:12px ui-monospace,monospace;border-collapse:collapse;width:100%}
.diff td{vertical-align:top;padding:3px}.diff_header{background:#f0f0f0;color:#444}.diff_next{background:#eee}
.diff_add,.diff_chg{color:#c00000;background:#fff0f0}.diff_sub{color:#c00000;background:#fff0f0;text-decoration:line-through}
details{margin:1.5rem 0}summary{font-weight:600;cursor:pointer}a{color:#174ea6}</style>
<h1>ARR manuscript revision</h1><p>Added and changed source is red; deleted source is red with a strike-through.
This is a source comparison, not a typeset PDF. The revised manuscript shows additions and substantive rewrites in red.
The baseline preserves the previous manuscript. The clean-color version uses identical scientific text, including unresolved author-review notes.</p>
<p>The revision integrates the supplied neutrality result and the reproducible FreshQA and TopicMisinfo results.
Review the visible author notes about raw annotations, original estimator provenance, and remaining validations.
No LaTeX build, visual PDF check, or eight-page confirmation has been completed.</p>
<details open><summary>Manuscript changes, including additions and deletions</summary>'''+body+'''</details>
<details><summary>Bibliography additions</summary>'''+bib+'</details></html>'
(P/'revision/review.html').write_text(page)
(P/'revision/changes.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
    fromfile='revision/baseline/main.tex',tofile='main.tex (expanded inputs)')))
with zipfile.ZipFile(P/'arr_revision_review.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(P.rglob('*')):
        if not f.is_file(): continue
        rel=f.relative_to(P)
        if any(part in {'.git','__pycache__'} for part in rel.parts): continue
        if f.suffix in {'.zip','.pyc','.aux','.log','.out','.fls','.fdb_latexmk'}: continue
        if f.name.startswith('main') and f.suffix=='.pdf': continue
        z.write(f,rel.as_posix())
print(P/'revision/review.html')
print(P/'arr_revision_review.zip')
