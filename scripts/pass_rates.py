"""Each arm's pass rate, and the paired 2x2 behind the count of disagreeing pairs.

Written for this repository on 2026-11-25, after the run. The pre-registered analysis
(``repro_r1_agreement.py``) prints how many pairs disagree; it does not print each arm's
own rate, the 2x2, the McNemar test or the net swing. Those were first read from the
stored ``outcome`` column on 2026-09-15 with no script kept. This file computes them the
same way: the same stored column, the same join key, and the pre-registered script's own
interval functions.

Usage:  pass_rates.py [--store DIR] [RUN_A RUN_B]

With no arguments it reads the two arms in this repository's ``runs`` folder.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from scipy.stats import binomtest

from repro_r1_agreement import Store, _flat, clopper_pearson, cluster_bootstrap

RUNS = Path(__file__).resolve().parent.parent / "runs"
ARM_R = "20260915T210140Z-4847"
ARM_R2 = "20260915T211148Z-965d"
EVENT = "solved"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", type=Path, default=RUNS, help="the folder holding the runs")
    ap.add_argument("runs", nargs="*", default=[ARM_R, ARM_R2], metavar="RUN")
    args = ap.parse_args()
    if len(args.runs) != 2:
        ap.error("give two run ids, or none")
    run_a, run_b = args.runs

    store = Store(args.store)
    ma, mb = store.manifest(run_a), store.manifest(run_b)
    raw_a, raw_b = store.read(run_a), store.read(run_b)
    a, b = _flat(raw_a), _flat(raw_b)
    print(f"same salt: {ma.run_salt == mb.run_salt} ({ma.run_salt})"
          f" | same target: {ma.target_id == mb.target_id} ({ma.target_id})")

    print("\nEach arm on its own:")
    for label, run, raw, f in (("R ", run_a, raw_a, a), ("R′", run_b, raw_b, b)):
        f = f.assign(event=(f["outcome"] == EVENT).astype(int))
        k, n = int(f["event"].sum()), len(f)
        lo, hi = clopper_pearson(k, n)
        blo, bhi = cluster_bootstrap(f, "event", "task_id")
        print(f"  {label} {run}  {EVENT} {k}/{n} = {pct(k / n)}"
              f"   Clopper-Pearson 95% [{lo:.4f}, {hi:.4f}]"
              f"   task-clustered boot [{blo:.4f}, {bhi:.4f}]")
        print(f"     outcomes {dict(sorted(Counter(f['outcome']).items()))}"
              f" | termination reasons {dict(sorted(Counter(f['termination_reason']).items()))}"
              f" | rows with an error {int(raw['error'].notna().sum())}")

    key = ["config_hash", "replicate_index"]
    m = a.merge(b, on=key, suffixes=("_a", "_b"), how="inner")
    seeds = int((m["seed_a"] == m["seed_b"]).sum())
    print(f"\nPairs joined on (config_hash, replicate_index): {len(m)}"
          f" | seeds equal within the pair: {seeds}/{len(m)}")
    m = m[m["seed_a"] == m["seed_b"]]

    ea, eb = m["outcome_a"] == EVENT, m["outcome_b"] == EVENT
    n11, n10 = int((ea & eb).sum()), int((ea & ~eb).sum())
    n01, n00 = int((~ea & eb).sum()), int((~ea & ~eb).sum())
    n = len(m)
    print(f"\n{'':14s}{'R′ solved':>12s}{'R′ unsolved':>14s}")
    print(f"{'R solved':14s}{n11:12d}{n10:14d}{n11 + n10:8d}")
    print(f"{'R unsolved':14s}{n01:12d}{n00:14d}{n01 + n00:8d}")
    print(f"{'':14s}{n11 + n01:12d}{n10 + n00:14d}{n:8d}")

    flips = n10 + n01
    print(f"\nPairs whose two outcomes disagree: {flips} of {n} = {pct(flips / n)}")
    p = binomtest(min(n10, n01), flips, 0.5, alternative="two-sided").pvalue
    print(f"Exact McNemar on the {flips} disagreeing pairs ({n10} against {n01}): p = {p:.3f}")

    m = m.assign(swing=ea.astype(int) - eb.astype(int))
    lo, hi = cluster_bootstrap(m, "swing", "task_id_a")
    print(f"Net swing ({n10} - {n01})/{n} = {100 * (n10 - n01) / n:+.1f} points"
          f"   task-clustered boot 95% [{100 * lo:+.1f}, {100 * hi:+.1f}]")


if __name__ == "__main__":
    main()
