#!/usr/bin/env python3
"""Render appendix tables from the revision's machine-readable results."""
from pathlib import Path
import pandas as pd

P=Path(__file__).resolve().parents[2]
R=P/'revision/results'
T=P/'revision/tables'
names={
    'gemma-3-27b-it':'Gemma 3 27B', 'gemma-3-12b-it':'Gemma 3 12B', 'gemma-3-4b-it':'Gemma 3 4B',
    'gpt-4.1':'GPT-4.1', 'gpt-4.1-mini':'GPT-4.1 mini', 'gpt-4.1-nano':'GPT-4.1 nano',
    'llama-3.1-70b-instruct':'Llama 3.1 70B', 'llama-3.1-8b-instruct':'Llama 3.1 8B',
    'llama-3.2-1b-instruct':'Llama 3.2 1B', 'llama-3.2-3b-instruct':'Llama 3.2 3B',
    'gemini-2.5-flash':'Gemini 2.5 Flash', 'gemini-2.5-flash-lite':'Gemini 2.5 Flash Lite',
    'mistral-medium-3':'Mistral Medium 3', 'mistral-small-24b-instruct-2501':'Mistral Small 24B',
}

def table(columns, head, rows, caption, label):
    return '\n'.join([r'\begin{table*}[t]',r'\centering\scriptsize\revisioncolor',
        r'\setlength{\tabcolsep}{3pt}',r'\begin{tabular}{'+columns+'}',r'\toprule',
        head+r' \\',r'\midrule',*rows,r'\bottomrule',r'\end{tabular}',
        r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{table*}',''])

fq=pd.read_csv(R/'freshqa_per_model.csv')
rows=[]
for model in ['gpt-4.1','gpt-4.1-mini','gemma-3-27b-it','llama-3.1-70b-instruct']:
    for group in ['pre','post']:
        s=fq[(fq.model_name==model)&(fq.cutoff_bin==group)].iloc[0]
        vals=[s[c] for c in ['accuracy','c3_decode','c3_format','c3_context','c3_cross_decode','c3_cross_format','c3_cross_context']]
        rows.append(names[model]+' & '+group+' & '+' & '.join(f'{v:.3f}' for v in vals)+r' \\')
(T/'freshqa_per_model.tex').write_text(table('llrrrrrrr',
    'Model & Group & Accuracy & MMD decode & MMD format & MMD context & Cross decode & Cross format & Cross context',
    rows,'FreshQA model-level results. Every model has 25 questions per cutoff group and 20 successful generations per arm. Decode compares two independent canonical-prompt replicates.','tab:freshqa_models'))

tm=pd.read_csv(R/'topicmisinfo_per_model.csv')
ins=pd.read_csv(R/'topicmisinfo_instances.csv')
rows=[]
for model,g in ins.groupby('model',sort=True):
    vals=tm[tm.model==model].set_index('method')
    row=[names[model],str(len(g)),f'{g.n_base.mean()/20:.3f}',f'{g.refusal_rate.mean():.3f}']
    for method in ['plurality','mmd','cross']:
        row += [f'{vals.loc[method,c]:.3f}' for c in ['ECE','AUROC']]
    rows.append(' & '.join(row)+r' \\')
(T/'topicmisinfo_per_model.tex').write_text(table('lrrrrrrrrr',
    'Model & Claims & Valid orig. & Refusal & SC ECE & SC AUROC & MMD ECE & MMD AUROC & Cross ECE & Cross AUROC',
    rows,'TopicMisinfo retained counts and model-level metrics. Valid orig. is the mean fraction of original response slots yielding a rating among retained claims; refusal averages identifiable refusals across both conditions. SC is plurality-based self-consistency. All score variants and metrics are retained in the accompanying CSV.','tab:topic_models'))

sens=pd.read_csv(R/'topicmisinfo_threshold_sensitivity.csv')
labels={'plurality':'Plurality','pairwise':'Same-prompt pairwise','entropy':'Same-prompt concentration','mmd':'C3 (MMD)','tv':'C3 (TV)','cross':'C3 (cross-comparison)'}
rows=[]
for _,s in sens.iterrows():
    rows.append(f'{s.tolerance:.1f} & '+labels[s.method]+' & '+' & '.join(f'{s[c]:.3f}' for c in ['ECE','AUROC','PRP','PRN'])+r' \\')
(T/'topicmisinfo_thresholds.tex').write_text(table('rlrrrr',
    'Tolerance & Score & ECE & AUROC & AUPRC-P & AUPRC-N',rows,
    'Sensitivity to the tolerance defining alignment with the human reference. Values are macro averages over the retained per-model samples; labels, not scores, change with the tolerance.','tab:topic_tolerance'))
print('Rendered three appendix tables.')
