"""Where each pair's two episodes first differ, and the second-pass tests on that position.

Written for this repository on 2026-11-25, after the run. On 2026-09-15 the second pass
was computed with the helpers in ``repro_r1_spans2.py`` and no driver script was kept;
only the per-pair table it wrote (``results/results-r1-p2.csv``) was. This file is that
driver, rebuilt: it writes the same table, byte for byte, from the stored spans, and
prints the statistics the thresholds in ``PASS-2-DECLARATION.md`` were declared for.

Every function that decides what "differs" is imported from the two span scripts as they
were filed. This file adds the loop, the hazard, the permutation test, the rank
correlations and the fingerprint comparison.

Usage:  first_divergence.py [--store DIR] [--out CSV] [RUN_A RUN_B]

With no arguments it reads the two arms in this repository's ``runs`` folder.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, kendalltau, spearmanr

from repro_r1_agreement import clopper_pearson
from repro_r1_spans import FP_KEY, IN_KEY, OUT_KEY, Store, attrs, side, spans_of
from repro_r1_spans2 import first_divergence

RUNS = Path(__file__).resolve().parent.parent / "runs"
ARM_R = "20260915T210140Z-4847"
ARM_R2 = "20260915T211148Z-965d"
PERMUTATIONS = 10_000
PERMUTATION_SEED = 20260915
COLUMNS = ["task", "rep", "raw_idx", "idx", "what", "nmin", "side", "dis"]


def variance_share(values: np.ndarray, task: np.ndarray) -> float:
    """Between-task share of the variance: one-way, between sum of squares over total."""
    s = pd.Series(values)
    means, sizes = s.groupby(task).mean(), s.groupby(task).size()
    grand = values.mean()
    return float((sizes * (means - grand) ** 2).sum()) / float(((values - grand) ** 2).sum())


def permutation_test(values: np.ndarray, task: np.ndarray) -> tuple[float, float, float, float]:
    """The share, the null's mean and 95th percentile, and p: task labels shuffled over pairs."""
    rng = np.random.default_rng(PERMUTATION_SEED)
    observed = variance_share(values, task)
    null = np.array([variance_share(values, rng.permutation(task)) for _ in range(PERMUTATIONS)])
    return observed, float(null.mean()), float(np.percentile(null, 95)), float((null >= observed).mean())


def fingerprint_differs(sa: list[dict], sb: list[dict], i: int) -> bool:
    return attrs(sa[i]).get(FP_KEY) != attrs(sb[i]).get(FP_KEY)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", type=Path, default=RUNS, help="the folder holding the runs")
    ap.add_argument("--out", type=Path, help="also write the per-pair table to this CSV file")
    ap.add_argument("runs", nargs="*", default=[ARM_R, ARM_R2], metavar="RUN")
    args = ap.parse_args()
    if len(args.runs) != 2:
        ap.error("give two run ids, or none")

    store = Store(args.store)
    fa, fb = store.read(args.runs[0]), store.read(args.runs[1])
    m = fa.merge(fb, on=["config_hash", "replicate_index"], suffixes=("_a", "_b"), how="inner")

    rows = []
    speakers: Counter[tuple[int, str]] = Counter()
    for _, r in m.iterrows():
        sa, sb = spans_of(r["meta_a"]), spans_of(r["meta_b"])
        raw, _ = first_divergence(sa, sb, attrs, IN_KEY, OUT_KEY, normalise=False)
        idx, what = first_divergence(sa, sb, attrs, IN_KEY, OUT_KEY, normalise=True)
        if raw is None or idx is None:
            raise SystemExit("a pair has no first divergence; the tests below assume every pair has one")
        for episode in (sa, sb):
            for i in (0, 1):
                speakers[(i, side(episode[i]))] += 1
        rows.append({
            "task": r["meta_a"]["task_id"], "rep": r["replicate_index"],
            "raw_idx": raw, "idx": idx, "what": what,
            "nmin": min(len(sa), len(sb)), "side": side(sa[idx]),
            "dis": int(r["outcome_a"] != r["outcome_b"]),
            "raw_side": side(sa[raw]),
            "fp_first_call": fingerprint_differs(sa, sb, 0),
            "fp_raw": fingerprint_differs(sa, sb, raw),
            "fp_idx": fingerprint_differs(sa, sb, idx),
        })
    d = pd.DataFrame(rows)
    n = len(d)
    if args.out:
        d[COLUMNS].to_csv(args.out, index=False)

    print(f"pairs: {n} | pairs with a first divergence: {n} | identical pairs: 0")
    print(f"model calls per pair (the shorter episode): min {int(d['nmin'].min())},"
          f" median {float(d['nmin'].median()):.0f}")

    print("\nFirst-divergence call index, pairs at each index:")
    print(f"  spans compared byte for byte (first pass)   {dict(sorted(Counter(d['raw_idx']).items()))}")
    print(f"  provider tool-call ids normalised (second)  {dict(sorted(Counter(d['idx']).items()))}")
    print(f"  what differed first, second pass            {dict(Counter(d['what']))}")
    print(f"  side of the first divergence, first pass    {dict(Counter(d['raw_side']))}")
    print(f"  side of the first divergence, second pass   {dict(Counter(d['side']))}")

    print("\nWho makes each call (P5), over both episodes of every pair:")
    for i in (0, 1):
        counts = {s: c for (j, s), c in sorted(speakers.items()) if j == i}
        print(f"  call {i}: {counts}")

    print("\nHazard (P4): of pairs still identical entering call i, the share diverging at i")
    for label, col in (("first pass", "raw_idx"), ("second pass", "idx")):
        print(f"  {label}:")
        for i in range(int(d[col].max()) + 1):
            at_risk = int(((d[col] >= i) & (d["nmin"] > i)).sum())
            if at_risk == 0:
                break
            k = int(((d[col] == i) & (d["nmin"] > i)).sum())
            lo, hi = clopper_pearson(k, at_risk)
            print(f"    call {i}: {k}/{at_risk} = {k / at_risk:.4f}   Clopper-Pearson 95% [{lo:.4f}, {hi:.4f}]")

    task = d["task"].to_numpy()
    share, null_mean, null_95, p = permutation_test(d["idx"].to_numpy(float), task)
    print(f"\nClustering by task (P2), second pass: between-task variance share {share:.4f}")
    print(f"  permutation null ({PERMUTATIONS} shuffles, seed {PERMUTATION_SEED}):"
          f" mean {null_mean:.4f}, 95th percentile {null_95:.4f}, p = {p:.4f}")
    per_task = d.groupby("task")["idx"]
    print(f"  tasks whose four pairs all diverge at the same index: {int(per_task.nunique().eq(1).sum())}"
          f" of {per_task.ngroups}; task means run {per_task.mean().min():.2f} to {per_task.mean().max():.2f}")

    t = d.groupby("task").agg(mean_index=("idx", "mean"), disagreement=("dis", "mean"))
    rho, kendall = spearmanr(t["mean_index"], t["disagreement"]), kendalltau(t["mean_index"], t["disagreement"])
    print(f"\nPosition against outcome disagreement (P3), over {len(t)} tasks:")
    print(f"  Spearman rho {rho.statistic:+.3f}, p = {rho.pvalue:.3f}"
          f" | Kendall tau {kendall.statistic:+.3f}, p = {kendall.pvalue:.3f}")

    base = int(d["fp_first_call"].sum())
    lo, hi = clopper_pearson(base, n)
    print("\nBackend fingerprint differs between the pair's two episodes:")
    print(f"  at call 0, where the request is identical by construction: {base}/{n} = {base / n:.3f}"
          f"   [{lo:.3f}, {hi:.3f}]")
    for label, col in (("first pass", "fp_raw"), ("second pass", "fp_idx")):
        k = int(d[col].sum())
        lo, hi = clopper_pearson(k, n)
        odds, p = fisher_exact([[k, n - k], [base, n - base]])
        print(f"  at the first divergence, {label}: {k}/{n} = {k / n:.3f}   [{lo:.3f}, {hi:.3f}]"
              f"   Fisher exact against call 0: p = {p:.3f}, odds ratio {odds:.2f}"
              f" | same fingerprint: {n - k}/{n}")

    share, _, null_95, p = permutation_test(d["dis"].to_numpy(float), task)
    print("\nExploratory, not declared in advance: outcome disagreement by task")
    print(f"  between-task variance share {share:.4f}; permutation null 95th percentile {null_95:.4f}, p = {p:.4f}")


if __name__ == "__main__":
    main()
