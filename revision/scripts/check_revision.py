#!/usr/bin/env python3
"""Static manuscript/data checks. These do not replace a LaTeX/PDF build."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

P=Path(__file__).resolve().parents[2]

def active(s):
    return re.sub(r'(?<!\\)%[^\n]*','',s)

def expand(path, chain=()):
    assert path not in chain, f'Recursive input: {path}'
    s=active(path.read_text())
    def read(m):
        name=m[1] if m[1].endswith('.tex') else m[1]+'.tex'
        q=P/name
        assert q.exists(), f'Missing input: {q}'
        return expand(q,chain+(path,))
    return re.sub(r'\\input\{([^}]+)\}',read,s)

source=expand(P/'main.tex')
stack=[]
for m in re.finditer(r'\\(begin|end)\{([^}]+)\}',source):
    if m[1]=='begin': stack.append(m[2])
    else:
        assert stack and stack[-1]==m[2], (m[2],stack[-3:])
        stack.pop()
assert not stack, stack
group_source=re.sub(r'\\begin\{PromptBox\}.*?\\end\{PromptBox\}', '', source, flags=re.S)
depth=0
for m in re.finditer(r'(?<!\\)[{}]',group_source):
    depth += 1 if m[0]=='{' else -1
    assert depth>=0, f'Unmatched closing brace near {m.start()}'
assert depth==0, depth
labels=re.findall(r'\\label\{([^}]+)\}',source)
refs={x.strip() for g in re.findall(r'\\(?:ref|eqref|cref|Cref)\{([^}]+)\}',source) for x in g.split(',')}
assert len(labels)==len(set(labels)), Counter(labels)
assert not refs-set(labels), refs-set(labels)
keys={x.strip() for g in re.findall(r'\\cite\w*(?:\[[^]]*\])*\{([^}]+)\}',source) for x in g.split(',')}
bibkeys=re.findall(r'@\w+\s*\{\s*([^,]+),',(P/'citation.bib').read_text())
assert len(bibkeys)==len(set(bibkeys))
assert not keys-set(bibkeys), keys-set(bibkeys)
for name in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',source):
    assert (P/name).exists(),name
assert '\\onecolumn' not in source
assert source.index('\\section*{Limitations}') < source.index('\\bibliography{citation}')
baseline=P/'revision/baseline'
for name,digest in json.loads((baseline/'sha256.json').read_text()).items():
    assert hashlib.sha256((baseline/name).read_bytes()).hexdigest()==digest,name
old=active((baseline/'main.tex').read_text())
def table_cells(s):
    return re.findall(r'\\begin\{tabular\*?\}.*?\\end\{tabular\*?\}',s,re.S)
for t in table_cells(old):
    assert t in table_cells(source), 'An original numerical table changed unexpectedly.'
clean=expand(P/'main-clean.tex')
assert clean.split('\\begin{document}',1)[1].strip() == source.split('\\begin{document}',1)[1].strip()
main=source.split('\\begin{document}',1)[1].split('\\section*{Limitations}',1)[0]
main=re.sub(r'\\begin\{(?:table|figure)\*?\}.*?\\end\{(?:table|figure)\*?\}','',main,flags=re.S)
result=dict(status='passed', checks=['balanced environments and braces','all inputs and figure assets present',
    'unique labels and bibliography keys','all references and citations resolve in source',
    'original table contents unchanged','baseline checksums unchanged','clean/marked body identical',
    'two-column format retained','ARR limitations before bibliography'],
    cited_references=len(keys), approximate_main_text_words_excluding_floats=len(re.findall(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b",main)),
    latex_compiled=False, pdf_visual_review=False, page_limit_verified=False)
(P/'revision/results/source_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
