# C3 ARR manuscript — revision for author review

The draft integrates the rebuttal evidence and reanalyses the completed local FreshQA and TopicMisinfo runs. It uses the supplied ACL/ARR style in anonymous, two-column review mode.

- **`main.tex`**: revised manuscript. Additions, substantive rewrites, new tables, and newly cited bibliography entries are marked red. Existing numerical tables are retained unchanged.
- **`main-clean.tex`**: the same manuscript with revision color disabled. It retains the visible author-review notes; it is not a submission-ready claim.
- **`revision/review.html`**: source comparison showing additions and deletions in red, including expanded appendix tables.
- **`revision/baseline/`**: immutable copies of the pre-revision manuscript, bibliography, and README, with checksums.
- **`arr_revision_review.zip`**: portable review package for Overleaf. Set the main document explicitly to `main.tex` or `main-clean.tex`.

## Build and check

Use pdfLaTeX with BibTeX, as expected by this template:

```sh
bash build.sh
python revision/scripts/check_revision.py
```

`main.tex` produces the red-marked PDF; `main-clean.tex` produces the clean-color PDF. The editing environment has no LaTeX compiler, and its network cannot resolve the compiler download host. Consequently **no manuscript PDF has been compiled, no visual layout check has been completed, and the eight-page ARR content limit remains unverified**. Static checks are recorded in `revision/results/source_checks.json`.

## Evidence reconciled in this revision

The completed FreshQA run has 50 questions (25 per cutoff group), four models, and 20 successful generations in each of four arms. Its MMD contextual scores are 0.976/0.946; the 0.771/0.469 values belong to cross-comparison. Original-replicate MMD is not ordinary within-prompt self-consistency.

The completed TopicMisinfo run has 14 models, 50 sampled claims, and 663 retained model–claim pairs. The original function named categorical MMD computes total variation. The revision labels it accurately, adds the actual indicator-kernel MMD score, and compares cross-comparison with plurality, pairwise agreement, and categorical concentration. The main text reports the weaker MMD result and the competitive same-prompt controls. The common-claim analysis uses 25 claims across all models.

The reported 94/100 unanimous-neutral human judgments are included from the supplied rebuttal. Their raw annotation records were not located; the draft visibly flags that documentation gap. Other remaining checks cover the original six-benchmark estimator and aggregation provenance, task-specific judge validation, and component-wise perturbation ablations. No new API calls or human annotations were performed.

## Reproduce the offline analysis

From this repository in the original workspace layout:

```sh
python revision/scripts/rebuild_results.py
python revision/scripts/render_tables.py
python revision/scripts/check_revision.py
python revision/scripts/package_review.py
```

The analysis scripts read `../../freshqa_cutoff/` and `../../topicmisinfo/` and write only under `revision/`. They preserve the original experiment files and validate reproduced scores against saved outputs. Source hashes, per-instance data, per-model summaries, sensitivity checks, and statistical outputs are included in `revision/results/`. Re-running the analysis requires those original cached-generation directories; compiling the manuscript does not.

The NeurIPS source manuscript is preserved. The revised ARR manuscript is the review target. No commit or push is performed by these scripts.
