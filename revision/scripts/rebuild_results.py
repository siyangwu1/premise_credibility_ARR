#!/usr/bin/env python3
"""Rebuild revision tables from cached generations; no API calls or source writes."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

PAPER = Path(__file__).resolve().parents[2]
ROOT = PAPER.parents[1]
OUT = PAPER / "revision/results"
TABLES = PAPER / "revision/tables"
OUT.mkdir(exist_ok=True)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


tm = module("topic_scoring", ROOT / "topicmisinfo/compute_c3.py")
sys.path.insert(0, str(ROOT / "freshqa_cutoff/src"))
fq = module("cutoff_scoring", ROOT / "freshqa_cutoff/src/score_results.py")

METHODS = {
    "plurality": "Self-consistency (plurality)",
    "pairwise": "Same-prompt pairwise agreement",
    "entropy": "Same-prompt concentration",
    "mmd": "C3 (MMD)",
    "tv": "C3 (total variation)",
    "cross": "C3 (cross-comparison)",
}


def metrics(frame, col):
    y, s = frame.aligned.to_numpy(), frame[col].to_numpy()
    return dict(ECE=tm.ece(s, y),
                AUROC=roc_auc_score(y, s) if len(set(y)) == 2 else np.nan,
                PRP=average_precision_score(y, s) if y.sum() else np.nan,
                PRN=average_precision_score(1-y, 1-s) if (1-y).sum() else np.nan)


def aggregate(frame, tolerance=1.0):
    frame = frame.assign(aligned=(abs(frame.base_mean-frame.human_mean) <= tolerance).astype(int))
    rows = []
    for model, group in frame.groupby("model", sort=True):
        for col, name in METHODS.items():
            rows.append(dict(model=model, method=col, n=len(group), **metrics(group, col)))
    per_model = pd.DataFrame(rows)
    macro = per_model.groupby("method")[["ECE", "AUROC", "PRP", "PRN"]].mean().reindex(METHODS)
    return per_model, macro


base, pert = tm.load_condition("baseline"), tm.load_condition("premise")
master = pd.read_csv(ROOT / "topicmisinfo/data/topicmisinfo_50_prompts.csv").set_index("question_id")
records = []
for model in sorted(set(base) & set(pert)):
    for qid in sorted(set(base[model]) & set(pert[model])):
        a, ar, af = base[model][qid]
        b, br, bf = pert[model][qid]
        if af < 20 or bf < 20 or min(len(a), len(b)) < 5:
            continue
        counts = np.bincount(a, minlength=7)[1:7]
        probs = counts[counts > 0] / len(a)
        pairwise = (counts * (counts-1)).sum() / (len(a)*(len(a)-1))
        records.append(dict(model=model, question_id=qid,
            topic=master.loc[qid, "topic"], n_base=len(a), n_pert=len(b),
            refusal_rate=(ar+br)/(af+bf),
            base_mean=np.mean(a),
            human_mean=master.loc[qid, ["human_mean_female", "human_mean_male"]].mean(),
            plurality=tm.self_consistency(a), pairwise=pairwise,
            entropy=1+float((probs*np.log(probs)).sum())/np.log(6),
            mmd=fq.c3_score([str(x) for x in a], [str(x) for x in b])[0],
            tv=tm.c3_categorical(a,b), cross=tm.c3_cross(a,b)))
df = pd.DataFrame(records)
df.to_csv(OUT / "topicmisinfo_instances.csv", index=False)
per_model, macro = aggregate(df)
per_model.to_csv(OUT / "topicmisinfo_per_model.csv", index=False)
macro.to_csv(OUT / "topicmisinfo_macro.csv")

# The original 'C3' column is total-variation stability, not MMD.
old = pd.read_csv(ROOT / "topicmisinfo/c3_per_model.csv").set_index("model")
for new_name, old_name in [("plurality", "SelfCons"), ("tv", "C3"), ("cross", "C3cross")]:
    got = per_model.loc[per_model.method == new_name].set_index("model")
    for col in ["ECE", "AUROC", "PRP", "PRN"]:
        np.testing.assert_allclose(got.loc[old.index,col], old[f"{old_name}_{col}"], atol=1e-12)

common = set.intersection(*(set(g.question_id) for _, g in df.groupby("model")))
_, common_macro = aggregate(df[df.question_id.isin(common)])
common_macro.to_csv(OUT / "topicmisinfo_common_claims_macro.csv")
sens = []
for threshold in [0.5, 1.0, 1.5]:
    _, result = aggregate(df, threshold)
    sens.append(result.reset_index().assign(tolerance=threshold))
pd.concat(sens).to_csv(OUT / "topicmisinfo_threshold_sensitivity.csv", index=False)

success = {}
for path in sorted((ROOT / "freshqa_cutoff/outputs_50").glob("*.jsonl")):
    if path.name == "core_answers.jsonl":
        continue
    count = {}
    with path.open() as f:
        for line in f:
            row = json.loads(line)
            if row.get("status") == "ok":
                count[row["condition"]] = count.get(row["condition"],0)+1
    assert count == dict(original_a=1000, original_b=1000, format=1000, context=1000), count
    success[path.name] = count

inputs = sorted((ROOT / "freshqa_cutoff/outputs_50").glob("*.jsonl"))
subprocess.run([sys.executable, str(ROOT/"freshqa_cutoff/src/score_results.py"),
    *[str(x) for x in inputs if x.name != "core_answers.jsonl"],
    "--extractions", str(ROOT/"freshqa_cutoff/outputs_50/core_answers.jsonl"),
    "--output", str(OUT/"freshqa_instances.csv"), "--trials", "20"], check=True)
original = pd.read_csv(ROOT/"freshqa_cutoff/results_50/instance_scores.csv")
rebuilt = pd.read_csv(OUT/"freshqa_instances.csv")
pd.testing.assert_frame_equal(original, rebuilt, check_exact=False, rtol=1e-12)
subprocess.run([sys.executable, str(ROOT/"freshqa_cutoff/src/analyze_results.py"),
    str(OUT/"freshqa_instances.csv"), "--output-json", str(OUT/"freshqa_statistics.json"),
    "--output-summary-csv", str(OUT/"freshqa_per_model.csv")], check=True, stdout=subprocess.DEVNULL)

metadata = dict(topic_models=len(base.keys() & pert.keys()), topic_claims_sampled=len(master),
    topic_retained_model_claims=len(df), topic_claims_min=int(df.groupby("model").size().min()),
    topic_claims_max=int(df.groupby("model").size().max()), topic_common_claims=len(common),
    freshqa_questions=50, freshqa_models=4, freshqa_samples_per_arm=20,
    freshqa_successful_generations=success,
    provenance="Offline reanalysis of cached outputs; no new model generations or human annotations.",
    human_neutrality="94/100 unanimous judgments reported by authors in rebuttal; raw annotations not located.")
(OUT/"run_metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")

def latex_rows(data):
    return "\n".join(METHODS[name]+" & "+" & ".join(f"{row[c]:.3f}" for c in ["ECE","AUROC","PRP","PRN"])+r" \\" for name,row in data.iterrows())+"\n"
(TABLES/"topicmisinfo_rows.tex").write_text(latex_rows(macro))
(TABLES/"topicmisinfo_common_rows.tex").write_text(latex_rows(common_macro))
source_paths = [ROOT/"topicmisinfo/compute_c3.py", ROOT/"freshqa_cutoff/src/score_results.py",
    ROOT/"freshqa_cutoff/src/analyze_results.py", ROOT/"topicmisinfo/c3_per_model.csv",
    ROOT/"freshqa_cutoff/results_50/model_summary.csv"]
source_paths += list((ROOT/"topicmisinfo/baseline/output").glob("*.csv"))
source_paths += list((ROOT/"topicmisinfo/premise/output").glob("*.csv"))
source_paths += inputs
(OUT/"source_sha256.json").write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},indent=2)+"\n")
print(macro.round(4).to_string())
print("Common claims:",len(common))
print(common_macro.round(4).to_string())
