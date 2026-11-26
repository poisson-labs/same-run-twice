# R.1 pass 2 — first-divergence position: what counts as structure, declared before computing

Written 2026-09-15 against the frozen pair R `20260915T210140Z-4847` / R′
`20260915T211148Z-965d`. **No new episodes. No provider call.** Same discipline as D1:
every threshold below is fixed before the numbers exist, because a threshold chosen after
seeing them is the failure this project attacks.

**The question.** Pass 1 reported a median first-divergence span index of 1 and read it as
*"divergence is immediate, not accumulated."* Two distinct claims are bundled there — a
negative (not accumulated) and a positive (immediate, i.e. position carries meaning). This
pass tests which the data supports, and whether position carries any task-level structure
at all.

## P1 — Per-task distribution

The 200 pairs are 50 tasks × 4 replicates. Report, per task: the four first-divergence
indices, their mean, and the task's outcome-disagreement count (0–4).

## P2 — Clustering by task. **Declared test and thresholds.**

**Statistic:** the between-task share of variance in first-divergence index (ICC-style:
between-task variance / total variance, one-way).

**Null distribution:** permutation. Shuffle the task label across all 200 pairs, recompute,
**10,000 times, seed 20260915**. Chosen over asymptotic Kruskal–Wallis because there are
**4 observations per group** over a discrete index taking about four values, where
asymptotic approximations are not trustworthy.

> **Clustering is declared PRESENT iff `p < 0.05` AND the between-task variance share is
> `>= 0.10`.** Both, not either. A p-value alone at n = 200 can certify an effect too small
> to mean anything; an effect size alone has no null to beat. Below 0.10, task membership
> explains under a tenth of the variance, which is not a "distinct divergence profile" in
> any sense that would change what anyone does.

## P3 — Does outcome disagreement track divergence position, at task level?

**Statistic:** Spearman rank correlation across the **50 tasks** between the task's mean
first-divergence index and its outcome-disagreement rate (k/4). Spearman because both are
discrete and bounded and the relation need not be linear. **Kendall tau reported beside it
as a robustness check, declared now rather than chosen after.**

> **Correlation is declared PRESENT iff `|rho| >= 0.30` AND `p < 0.05`.** Below 0.30, with
> 50 points, under 9 % of rank variance is explained — not a claim worth making.

## P4 — The claim actually in dispute: accumulated, immediate, or memoryless?

**The three hypotheses make different predictions about the hazard** — of the pairs still
identical entering call `i`, the fraction that diverge **at** call `i`:

| | hazard shape |
|---|---|
| **accumulated** (drift builds over turns) | **increasing** in `i` |
| **immediate / front-loaded** (something special about the start) | **decreasing** in `i` |
| **memoryless** (constant per-call probability) | **flat** |

> **Declared: the hazard is called FLAT iff the 95 % Clopper–Pearson intervals for the
> hazard at indices 0, 1 and 2 all mutually overlap.** Increasing or decreasing is declared
> only if the interval at index 0 and the interval at index 2 are **disjoint**, and the
> direction is then whichever it is.

**A confound declared now, not discovered later.** First-divergence index is **censored by
episode length** — a pair cannot diverge at call 5 if it only has 4 calls. So a naive
correlation between episode length and divergence index is biased upward and **will not be
reported as evidence of accumulation.** The hazard formulation is used precisely because it
conditions on being at risk at call `i`.

## P5 — The structural explanation that would make P4 moot

τ²'s user simulator speaks first, so **span index may simply encode which side is calling.**
Report the index → side mapping and the per-side divergence rate. **If index 0 is
near-universally the user simulator and index 1 the agent, then "median index 1" is a fact
about conversation structure and not about timing**, and the pass-1 sentence must be
withdrawn regardless of what P2–P4 say.

## What gets reported either way

**A null is a finding here and is stated as one.** If P2, P3 and P4 all come back negative,
the report says *position carries no structure we can detect at this N*, with the intervals
that bound how much structure could still be hiding — not silence, and not a softened
positive.
