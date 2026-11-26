"""R.1 reproducibility pilot: the pre-registered analysis, in one file.

Joins two runs that share a run_salt on (config_hash, replicate_index) -- which is
exactly the key ``executor.derive_seed(salt, config_hash, replicate_index)`` hashes,
so a joined row is a pair at identical (cfg, seed) by construction and the join
asserts it rather than assuming it.

Usage:  repro_agreement.py <RUN_A> <RUN_B>
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import beta

from poisson_prove.store import Store

# The instrument-side class: tau2's labels for the run dying rather than the
# agent deciding. Declared before the run; see the pre-registration's E2.
INSTRUMENT_SIDE = frozenset(
    {"infrastructure_error", "agent_error", "user_error", "unexpected_error"}
)
SHAPE_FIELDS = ("n_messages", "n_agent_messages", "n_user_messages", "n_tool_messages", "n_tool_calls")
BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 20260915


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def cluster_bootstrap(df: pd.DataFrame, flag: str, cluster: str = "task_id") -> tuple[float, float]:
    """Percentile interval, resampling whole tasks -- pairs of one task are not independent."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    groups = [g[flag].to_numpy() for _, g in df.groupby(cluster, sort=True)]
    if not groups:
        return (float("nan"), float("nan"))
    idx = rng.integers(0, len(groups), size=(BOOTSTRAP_B, len(groups)))
    draws = np.array([np.concatenate([groups[i] for i in row]).mean() for row in idx])
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def ne(x: pd.Series, y: pd.Series) -> pd.Series:
    """Null-safe inequality. Both absent -> equal; one absent -> different.

    Plain ``!=`` reports NaN != NaN as True, which would score a field the wrapper
    never wrote as a disagreement on every pair -- a null-vs-NaN defect found earlier.
    """
    both_null = x.isna() & y.isna()
    return (~both_null) & (x.ne(y) | (x.isna() ^ y.isna()))


def _flat(df: pd.DataFrame) -> pd.DataFrame:
    meta = df["meta"].apply(lambda m: m if isinstance(m, dict) else {})
    out = df[["config_hash", "replicate_index", "seed", "outcome", "t"]].copy()
    out["task_id"] = meta.apply(lambda m: m.get("task_id"))
    out["reward"] = meta.apply(lambda m: m.get("reward"))
    out["breakdown"] = meta.apply(lambda m: json.dumps(m.get("reward_breakdown") or {}, sort_keys=True))
    out["termination_reason"] = meta.apply(lambda m: m.get("termination_reason"))
    out["prompt_sha"] = meta.apply(lambda m: m.get("system_prompt_sha256"))
    out["cost"] = meta.apply(
        lambda m: (float((m.get("cost_tau2") or {}).get("agent") or 0.0)
                   + float((m.get("cost_tau2") or {}).get("user") or 0.0))
    )
    for f in SHAPE_FIELDS:
        out[f] = meta.apply(lambda m, f=f: m.get(f))
    for f in ("in", "out"):
        out[f"tok_{f}"] = meta.apply(lambda m, f=f: (m.get("tokens") or {}).get(f))
    return out


def main(run_a: str, run_b: str) -> None:
    store = Store(os.environ["PROOFLOAD_STORE"])
    ma, mb = store.manifest(run_a), store.manifest(run_b)
    print(f"A  {run_a}  salt={ma.run_salt}  target={ma.target_id}  status={ma.status}")
    print(f"B  {run_b}  salt={mb.run_salt}  target={mb.target_id}  status={mb.status}")
    # E5: a construction check, not a filter. Stated before the run.
    print(f"E5 same salt: {ma.run_salt == mb.run_salt} | same target: {ma.target_id == mb.target_id}")

    a, b = _flat(store.read(run_a)), _flat(store.read(run_b))
    key = ["config_hash", "replicate_index"]
    print(f"\nrows A={len(a)} B={len(b)}")
    for name, f in (("A", a), ("B", b)):
        dup = f.duplicated(key).sum()
        print(f"  {name}: {dup} duplicate cells (E4 requires 0)")

    m = a.merge(b, on=key, suffixes=("_a", "_b"), how="inner")
    print(f"joined pairs: {len(m)}")

    seed_ok = (m["seed_a"] == m["seed_b"])
    print(f"E3 seeds equal within pair: {int(seed_ok.sum())}/{len(m)}")
    m = m[seed_ok]

    has_outcome = m["outcome_a"].notna() & m["outcome_b"].notna()
    instr = m["outcome_a"].isin(INSTRUMENT_SIDE) | m["outcome_b"].isin(INSTRUMENT_SIDE)
    print(f"E1 both outcomes present: {int(has_outcome.sum())}/{len(m)}")
    print(f"E2 instrument-side either side: {int((has_outcome & instr).sum())}")

    all_pairs = m[has_outcome].copy()          # headline WITHOUT the E2 exclusion
    elig = m[has_outcome & ~instr].copy()      # headline WITH it

    for label, d in (("eligible (E1-E5, E2 applied)", elig), ("E2 NOT applied", all_pairs)):
        if len(d) == 0:
            print(f"\n{label}: 0 pairs")
            continue
        d = d.assign(disagree=(d["outcome_a"] != d["outcome_b"]).astype(int))
        k, n = int(d["disagree"].sum()), len(d)
        lo, hi = clopper_pearson(k, n)
        blo, bhi = cluster_bootstrap(d, "disagree", "task_id_a")
        print(f"\n{label}: n={n}")
        print(f"  D1 outcome disagreement {k}/{n} = {k/n:.4f}")
        print(f"     Clopper-Pearson 95%   [{lo:.4f}, {hi:.4f}]  width {hi-lo:.4f}")
        print(f"     task-clustered boot   [{blo:.4f}, {bhi:.4f}]  width {bhi-blo:.4f}")

    if len(elig):
        d = elig
        print("\nSecondaries (eligible set):")
        for name, col_a, col_b in (
            ("D2 reward",     "reward_a",     "reward_b"),
            ("D3 breakdown",  "breakdown_a",  "breakdown_b"),
            ("D4 step count", "t_a",          "t_b"),
        ):
            if d[col_a].isna().all() and d[col_b].isna().all():
                print(f"  {name:16s} field absent on both runs - not scored")
                continue
            dis = int(ne(d[col_a], d[col_b]).sum())
            print(f"  {name:16s} disagree {dis}/{len(d)} = {dis/len(d):.4f}")
        shape_dis = np.zeros(len(d), dtype=bool)
        for f in SHAPE_FIELDS:
            diff_f = ne(d[f"{f}_a"], d[f"{f}_b"])
            shape_dis |= diff_f.to_numpy()
            n_f = int(diff_f.sum())
            print(f"    {f:20s} {n_f}/{len(d)} = {n_f/len(d):.4f}")
        print(f"  D5 any shape field  disagree {int(shape_dis.sum())}/{len(d)} = {shape_dis.mean():.4f}")
        if d["prompt_sha_a"].isna().all():
            print("  D6 system_prompt_sha256 absent on both runs - not scored "
                  "(the field postdates the smoke pair; present from 0ef8c3c on)")
        else:
            same_prompt = int((~ne(d["prompt_sha_a"], d["prompt_sha_b"])).sum())
            print(f"  D6 system prompt identical {same_prompt}/{len(d)} "
                  f"(must be {len(d)}: both arms are the stock agent)")
        print(f"\n  A1 outcome-agreeing pairs with a shape disagreement: "
              f"{int((shape_dis & (d['outcome_a'] == d['outcome_b']).to_numpy()).sum())}")
        seed_contrast(a, b, float(d["disagree"].mean()) if "disagree" in d else
                      float((d["outcome_a"] != d["outcome_b"]).mean()))

        cost = float(d["cost_a"].sum() + d["cost_b"].sum())
        print(f"\n  provider-reported cost over eligible pairs: ${cost:.4f} "
              f"({len(d)*2} episodes, ${cost/(len(d)*2):.5f}/episode)")


def seed_contrast(a: pd.DataFrame, b: pd.DataFrame, same_seed_rate: float) -> None:
    """D7: same-seed disagreement against different-seed disagreement, same task.

    Every within-task pair of episodes that does NOT share a replicate_index shares cfg
    and differs in seed. If the two rates coincide, the OpenAI ``seed`` parameter is
    buying nothing measurable on this substrate -- which is a finding about the design
    of every paired run downstream, and it costs no extra episode.

    The different-seed pairs share episodes, so they are not independent: the interval
    is a task-clustered bootstrap and never a binomial one.
    """
    both = pd.concat([a.assign(arm="A"), b.assign(arm="B")], ignore_index=True)
    both = both[both["outcome"].notna() & ~both["outcome"].isin(INSTRUMENT_SIDE)]
    rows = []
    for task, g in both.groupby("task_id", sort=True):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                if g.at[i, "replicate_index"] == g.at[j, "replicate_index"]:
                    continue  # that is a same-seed pair; it is D1's, not D7's
                rows.append({
                    "task_id": task,
                    "disagree": int(g.at[i, "outcome"] != g.at[j, "outcome"]),
                })
    d = pd.DataFrame(rows)
    if d.empty:
        print("\nD7 seed contrast: no different-seed pairs (replicates == 1)")
        return
    k, n = int(d["disagree"].sum()), len(d)
    blo, bhi = cluster_bootstrap(d, "disagree", "task_id")
    print(f"\nD7 seed contrast (different seed, same task, same cfg): {k}/{n} = {k/n:.4f}")
    print(f"    task-clustered boot 95% [{blo:.4f}, {bhi:.4f}]   (NOT binomial: pairs share episodes)")
    print(f"    same-seed rate (D1)     {same_seed_rate:.4f}")
    print(f"    difference (different - same) = {k/n - same_seed_rate:+.4f}")
    print("    a difference near zero means the seed parameter is buying nothing here")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
