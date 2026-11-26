"""R.1 §5.2: where the nondeterminism enters, measured by aligning the two span sequences.

Pre-registered procedure, run over a pair of runs that share a salt. For each pair, walk
both episodes' spans in start order and find the first index where they differ. Then:

  1. request identical, response different -> the divergence entered at a MODEL SAMPLE.
     The span's own side (agent vs user simulator) attributes it.
  2. request already different while the previous response was identical -> the divergence
     entered from something that is NOT an llm call: a tool response, or ordering.
  3. neither -> reported open, with the pattern that was seen instead.

Nothing here infers a cause from a rate. A pair that matches no case is counted as
unattributed and stays unattributed.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter

import pandas as pd

from poisson_prove.store import Store

IN_KEY = "gen_ai.input.messages"
OUT_KEY = "gen_ai.output.messages"
SEED_KEY = "gen_ai.request.seed"
FP_KEY = "openai.response.system_fingerprint"
INSTRUMENT_SIDE = frozenset({"infrastructure_error", "agent_error", "user_error", "unexpected_error"})


def spans_of(meta: dict) -> list[dict]:
    trace = (meta or {}).get("trace") or {}
    sp = list(trace.get("spans") or [])
    sp.sort(key=lambda s: s.get("start_ns") or 0)
    return sp


def attrs(span: dict) -> dict:
    return span.get("attrs") or {}


def side(span: dict) -> str:
    """Agent or user simulator, from the request itself.

    The agent's prompt carries the airline policy (7,676 B) and its requests carry tool
    definitions; the user simulator's do neither. Size is the discriminator that does not
    depend on a fingerprint value staying put.
    """
    text = attrs(span).get(IN_KEY) or ""
    return "agent" if len(text) > 6000 else "user_sim"


def classify(sa: list[dict], sb: list[dict]) -> tuple[str, int | None, str | None]:
    n = min(len(sa), len(sb))
    for i in range(n):
        ra, rb = attrs(sa[i]).get(IN_KEY), attrs(sb[i]).get(IN_KEY)
        oa, ob = attrs(sa[i]).get(OUT_KEY), attrs(sb[i]).get(OUT_KEY)
        if ra == rb and oa == ob:
            continue
        if ra == rb and oa != ob:
            return "model_sample", i, side(sa[i])          # case 1
        if ra != rb:
            if i == 0:
                return "diverged_at_first_request", i, side(sa[i])
            prev_out_same = attrs(sa[i - 1]).get(OUT_KEY) == attrs(sb[i - 1]).get(OUT_KEY)
            if prev_out_same:
                return "not_an_llm_call", i, side(sa[i])   # case 2: tool or ordering
            return "downstream_of_earlier", i, side(sa[i])
    if len(sa) != len(sb):
        return "length_only", n, None
    return "identical", None, None


def main(run_a: str, run_b: str) -> None:
    store = Store(os.environ["PROOFLOAD_STORE"])
    fa, fb = store.read(run_a), store.read(run_b)
    key = ["config_hash", "replicate_index"]
    m = fa.merge(fb, on=key, suffixes=("_a", "_b"), how="inner")

    cases: Counter[str] = Counter()
    sides: Counter[str] = Counter()
    seed_fail = fp_diff = no_spans = 0
    outcome_agree_but_spans_differ = 0
    rows = []

    for _, r in m.iterrows():
        if r["outcome_a"] is None or r["outcome_b"] is None:
            continue
        if r["outcome_a"] in INSTRUMENT_SIDE or r["outcome_b"] in INSTRUMENT_SIDE:
            continue
        sa, sb = spans_of(r["meta_a"]), spans_of(r["meta_b"])
        if not sa or not sb:
            no_spans += 1
            continue
        # E6, at the provider boundary
        seeds_a = {attrs(s).get(SEED_KEY) for s in sa}
        seeds_b = {attrs(s).get(SEED_KEY) for s in sb}
        if seeds_a != seeds_b or len(seeds_a) != 1:
            seed_fail += 1
        # fingerprint, per span index
        n = min(len(sa), len(sb))
        if any(attrs(sa[i]).get(FP_KEY) != attrs(sb[i]).get(FP_KEY) for i in range(n)):
            fp_diff += 1
        case, idx, sd = classify(sa, sb)
        cases[case] += 1
        if sd:
            sides[f"{case}:{sd}"] += 1
        if case != "identical" and r["outcome_a"] == r["outcome_b"]:
            outcome_agree_but_spans_differ += 1
        rows.append({"task_id": (r["meta_a"] or {}).get("task_id"), "case": case,
                     "first_divergence_index": idx, "side": sd,
                     "n_spans_a": len(sa), "n_spans_b": len(sb),
                     "outcome_agree": r["outcome_a"] == r["outcome_b"]})

    total = sum(cases.values())
    print(f"pairs with spans on both sides: {total}   (skipped: {no_spans} without spans)")
    print(f"\nE6  pairs whose provider-side seed disagrees or is not unique: {seed_fail}  (must be 0)")
    print(f"FP  pairs differing in system_fingerprint at some span index: {fp_diff}/{total}"
          f"  = {fp_diff/total:.4f}" if total else "")
    print("\nFirst divergence, classified:")
    for case, n in cases.most_common():
        print(f"  {case:28s} {n:4d}/{total}  = {n/total:.4f}")
    if sides:
        print("\n  by side:")
        for k, n in sides.most_common():
            print(f"    {k:40s} {n:4d}")
    print(f"\npairs agreeing on outcome whose spans still differ: {outcome_agree_but_spans_differ}")
    out = os.environ.get("R1_SPANS_OUT")
    if out:
        pd.DataFrame(rows).to_csv(out, index=False)
        print(f"\nper-pair detail -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
