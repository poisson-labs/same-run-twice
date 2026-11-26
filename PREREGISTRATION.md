# The pre-registration, as published

This is the pre-registration behind the post
[45.0% and 44.0%](https://poissonlabs.ai/research/the-same-run-twice/). Sections 0 to 9 were
written on 2026-09-15 before any episode ran. Section 10 holds the addenda, each dated,
written during and after the run. The body was not edited once episodes existed.

Names used in it:

- **R.1** is this experiment: τ²-bench airline, run twice at the same configuration and seeds.
- **T.4** is a separate three-arm comparison on the same benchmark. R.1 was run to give T.4 a
  measured disagreement rate to size against. T.4's pre-registration is not in this repository.
- **`proofload`** is the name the `poisson-prove` package had before its first release.
- Commit ids and `file.py:line` references point into that package's pre-release source,
  which is not public. The τ²-bench commit `2174a60` is public.

Several readings recorded in the addenda were later narrowed or withdrawn. The post states
the narrower claim in each case, and the README lists them under "What the post withdrew".

## What differs from the filed text

The filed text is a private working note. This copy differs from it in 23 passages and in
its metadata block, listed here, and nowhere else. No definition, threshold, count, result
or date was changed.

| Where | What changed | Why |
|---|---|---|
| Metadata block at the top | Replaced by this header. Its facts: written 2026-09-15 before any episode, with nothing spent at the provider; source tree at commit `7929fe6`, branched from `main` at `339c75a`; the benchmark wrapper as of `dbb89c5`; τ²-bench pinned at `2174a60`. | The block is note metadata and names a local folder. |
| Opening note; addendum 3; the closing "Related" list | Three links to private notes: the first now reads "T.4's pre-registration", the second "the project log", and the closing list is removed. | The links resolve only inside the private notes. |
| §2.1, §3 (E2), §4 (S0), §5.2, §8, addendum 2 | Six citations of a numbered section or addendum of T.4's pre-registration now read "T.4's pre-registration", "T.4's preparation" or "T.4's cost table". | They point into a document that is not published. |
| §2.2, §4 (S1 and the paragraph under the table), §8 (twice) | Five identifiers of internal defect reports are replaced by a description of the defect, or removed where the sentence already describes it. | The identifiers resolve only in a private tracker. |
| §4, §8, addendum 3 | Three citations of numbered working rules are removed. The rule itself stays stated in the sentence. | The numbering is private. |
| §9 | Three local folder paths are replaced by `<the development worktree>` and `<the run store>`. | Paths on one machine. |
| Addendum 1 (twice), addendum 4 | A person's name is removed in three places: who approved addendum 1, whose addition it records, and a closing clause on who had predicted addendum 4's result. | The copy records what was decided and found. |

---

# R.1 — τ²-bench airline reproducibility: pre-registration

> **This is not T.4 and does not feed T.4.** It adds no episode to T.4's dataset,
> touches no line of T.4's pre-registration, and runs from
> its own sweep file on its own branch. §1.2 states exactly how strong the
> separation is and where it stops being mechanical.
>
> **Written before any episode runs.** The only data in front of it are the twenty
> stored smoke episodes (`20260913T113444Z-d44e` / `20260913T113537Z-a06a`), which
> are discovery and which R.1's own seeds do not reuse. Every definition below was
> fixed, and the analysis script committed and run, before a single new call.
>
> **Amendments are dated addenda under §10**, never edits to the body.

---

## 0. The question

**At identical `(cfg, seed)`, how often does this substrate return a different
answer?** The smoke measured 7/10 agreement on ten pairs. That point estimate
carries a 95 % Clopper–Pearson interval of **[0.067, 0.653]** — measured, not
quoted: `scripts/repro_r1_agreement.py` reproduces it from the stored pair — and an
interval 58 points wide is compatible with a substrate that is nearly
deterministic and with one that is nearly a coin flip. Every paired design
downstream, T.4's included, is sized against that number.

R.1 buys one number: the disagreement rate with an interval narrow enough to size
against.

---

## 1. Design

### 1.1 200 pairs, 400 episodes

| | |
|---|---|
| Cells | 50 — τ²-bench airline tasks `0`–`49`, the whole set, as `[axes.task_id]` |
| Replicates | 4 |
| Episodes per arm | 200 |
| Arms | 2 — **R** (fresh salt) and **R′** (`--pair-with R`) |
| **Episodes total** | **400** |
| **Pairs** | **200** |

**All 50 tasks × 4, not 10 tasks × 20.** The rate has to generalise to T.4, which
runs all 50; a rate measured on tasks 0–9 is a rate for tasks 0–9. Four replicates
also buy **D7** (§2.3) free, which one replicate cannot buy at any N.

**Why the pairs are at identical `(cfg, seed)` by construction, not by assertion.**
`executor.derive_seed(run_salt, config_hash, replicate_index)` is
`sha256(f"{salt}:{hash}:{replicate}")[:4]` big-endian. `--pair-with R` makes R′
inherit R's salt verbatim (`executor.py:184`–`:191`). The sweep file is byte-identical
between arms, so `config_hash` is identical per cell. Same salt, same hash, same
replicate index ⇒ **the same 32-bit seed**, which `rollout` passes to τ²'s
`TextRunConfig(seed=…)`, which `LLMConfigMixin.set_seed` writes into
`llm_args["seed"]`, which LiteLLM forwards as OpenAI's `seed` request parameter —
on both the agent and the user simulator. Temperature is 0.0 on both sides.

Verified on this tree before writing this line:

```
derive_seed(salt, hash, k) for k=0..3  →  [3160103663, 1829444793, 3215111995, 1303955136]
same salt + hash + k reproduces:  True
different salt differs:           True
```

The join in §2 keys on `(config_hash, replicate_index)` — the same tuple the seed
hashes — and **re-asserts seed equality per pair anyway (E3)** rather than trusting
the derivation. A pair whose two seeds differ is a construction failure, not a
disagreement.

**Per-cell MDE is 0.5, the cap** (`mde_two_proportion(0.5, 4, 4) == 0.5`, measured),
so `preflight_mde` returns 0.5 and the sweep needs `--max-mde 0.5`. **That refusal is
correct and is not being worked around.** R.1 is not a design with power to detect an
effect between arms; it estimates one proportion over 200 pairs, and its precision is
§1.3's interval, not an MDE.

### 1.2 How separate from T.4 this actually is

**Mechanical:** R.1's salt is fresh, and `diff.py:835` makes `mcnemar_bh` **refuse**
any pair of runs whose salts differ. No R.1 row can ever be paired with a T.4 arm by
the paired method.

**Recorded:** the manifest's `environment` carries the whole spec, so an R.1 run
(`replicates = 4`, axis set `{task_id}`) is told from a T.4 arm (`replicates = 44`,
axis set `{task_family, task_id}`) by reading it. `target_id` is **deliberately
unchanged** — it names the system under test, the system genuinely is the same one,
and that identity is the whole reason R.1's rate is usable as T.4's prior. A distinct
`target_id` would have been a tidier label and a false claim.

**Where it stops.** `diff` does **not** check `target_id` or spec identity — that check
exists only on `--resume` (`executor.py:169`). So nothing mechanically prevents
someone pooling R.1's rows with T.4's under an **unpaired** method. The guard there is
this document enumerating R.1's two run ids, and that is a filing convention, not a
guarantee. Stated rather than glossed.

### 1.3 What 200 pairs buys, computed

Clopper–Pearson 95 %, at the smoke's point estimate:

| | n | point | 95 % CP | width |
|---|---|---|---|---|
| smoke (measured) | 10 | 0.300 | [0.0667, 0.6525] | **0.586** |
| R.1 at the same rate | 200 | 0.300 | [0.2374, 0.3686] | **0.131** |

**A 4.5× narrower interval.** At other rates the width runs 0.066 (at 0.05) to 0.142
(at 0.45), so the precision claim holds across the plausible range and is not a
best case. **200 is committed and is not conditional on what the numbers look like.**
If the interval is wider than hoped, that is the result.

---

## 2. Agreement, defined now

### 2.1 The primary definition — D1

> **Two episodes of a pair agree iff their stored `outcome` strings are equal.**
> The **disagreement rate** is the fraction of eligible pairs that do not agree.

`outcome` takes one of the wrapper's ten labels: `solved`, `unsolved`, and τ²'s eight
`TerminationReason` names. **Equality is over the full vocabulary, not over
solved/unsolved** — an `unsolved` against a `max_steps` is a disagreement, and
collapsing them would hide exactly the competing-event case T.4's pre-registration exists to keep
visible. On all twenty smoke episodes the label was `solved` or `unsolved`, so in
practice this will read binary; the definition does not assume it will.

D1 is the headline because `outcome` is the field every downstream statistic reads.

**The interval is reported twice, and both are declared now.**

- **Clopper–Pearson 95 %** over the 200 pairs. Exact, and the direct comparison to
  the smoke's [0.067, 0.653].
- **A task-clustered bootstrap 95 %** (10,000 resamples of the 50 tasks with
  replacement, seed `20260915`). The 200 pairs share no episodes, but four of them
  come from each task and a task's difficulty is common to all four, so they are not
  iid Bernoulli and Clopper–Pearson will be optimistic.

**Where the two disagree, the clustered interval is the one quoted.** Fixed here so it
cannot be chosen later.

### 2.2 The secondaries, ranked now

Reported for every eligible pair, none of them the headline:

| | agreement on | why it is asked |
|---|---|---|
| **D2** | `meta.reward` exact | two `unsolved` episodes can differ in reward; D1 would not see it |
| **D3** | `meta.reward_breakdown` (`DB`, `COMMUNICATE`) | which half of the grader moved |
| **D4** | `t`, τ²'s step count | trajectory length |
| **D5** | any of `n_messages`, `n_agent_messages`, `n_user_messages`, `n_tool_messages`, `n_tool_calls` | conversation shape — the attribution signal |
| **D6** | `meta.system_prompt_sha256` | a control: both arms are the stock agent, so this **must** be 200/200. Anything else means the arms were not the same system and D1 is void |

**All comparisons are null-safe**: two absent values agree, one absent disagrees.
Plain `!=` scores `NaN != NaN` as a disagreement, which would report a field the
wrapper never wrote as a 100 % disagreement — a null-vs-NaN defect found earlier in this project. The
committed script implements this (`ne()`), and D6 **already exercised it**: the
smoke rows predate `system_prompt_sha256` (added `0ef8c3c`, 2026-09-14, a day after
the smoke), so the script reports it *not scored* rather than 0/10.

### 2.3 D7 — the seed contrast, which costs nothing extra

Four replicates per task means every within-task pair of episodes at **different**
replicate indices shares `cfg` and differs in `seed`. Their disagreement rate is the
natural reference for D1:

> **If the same-seed rate and the different-seed rate coincide, the OpenAI `seed`
> parameter is buying nothing measurable on this substrate.**

That is a finding about every paired design downstream and it needs no extra episode.
**Its interval is a task-clustered bootstrap and never a binomial one** — these pairs
share episodes with each other and are not independent. Declared now so that the
non-independence cannot be forgotten once there is a number to quote.

---

## 3. Eligibility

Fixed before the run. Every criterion is reported with its count, so each exclusion's
size is visible.

| | criterion | disposition |
|---|---|---|
| **E1** | both episodes carry a non-null `outcome` | a pair failing it is excluded and **counted** |
| **E2** | neither `outcome` is instrument-side — `infrastructure_error`, `agent_error`, `user_error`, `unexpected_error` | excluded from the eligible set and **reported separately as an instrument-failure rate** |
| **E3** | the two episodes carry the same `seed` | excluded and reported as a **construction failure** — see K1 |
| **E4** | exactly one row per `(config_hash, replicate_index)` per run | a duplicated or missing cell is not a pair; counted |
| **E5** | the two manifests carry the same `run_salt` and the same `target_id` | asserted and printed; a failure voids the run |
| **E6** | the two episodes' spans carry the same `gen_ai.request.seed` | *added by addendum 2, after C0 and before arm R's analysis.* The seed asserted **at the provider boundary**, not the executor's. A failure is a construction failure, as E3 |

**E2 is the only judgement call here, so D1 is reported both ways.** T.4's pre-registration already
classes those four as τ²'s labels for *the run dying rather than the agent deciding*,
which is why the exclusion is defensible — but an exclusion that moves the headline is
exactly the thing this project exists to distrust. **The script prints D1 with E2
applied and with E2 not applied, side by side, every time.** If they differ materially,
that difference is reported as a finding rather than resolved by preference.

---

## 4. Stopping rule

**Nothing stops on the disagreement rate, at any point, for any reason.** The 400 episodes are committed; there is no top-up, no second look, and no
extension if the interval is wider than hoped.

The stops that exist are all on cost or on instrument failure, and all are declared
with their thresholds here:

| | gate | threshold | action |
|---|---|---|---|
| **S0** | canary, 1 episode | `cost_tau2` > **$0.050** | abort. (The most expensive *legitimate* episode measured is $0.0246, in T.4's preparation, so $0.050 is clear of the known distribution and n=1 is too noisy for a tighter band) |
| **S1** | first complete wave of arm R, read from the partial store | mean `cost_tau2` > **$0.022**/episode | stop the sweep |
| **S2** | arm R complete | mean `cost_tau2` > **$0.022**/episode | stop; **do not launch R′** |
| **S3** | cumulative, both arms | total `cost_tau2` > **$8.80** | stop and report |
| **S4** | arm R complete | > **10 %** of 200 rows errored or instrument-side | stop; do not launch R′ — provider conditions this unstable mean the rate bounds nothing |

**$0.022 is the 2× trigger**, from $0.011/episode measured. **$8.80 is 2× $4.40.**
Every threshold reads `meta.cost_tau2` — litellm's own cache-aware, per-call accounting
— and **never `estimate_cost`**, which is known to price a full core where containers run
at the 0.125-core minimum and to price memory at nothing.

**If a stop fires, the episodes already run are reported with whatever interval they
support and the shortfall is stated.** A truncated run is not re-planned into a
different experiment.

---

## 5. Attribution, and the honest prior on it

**The default position is that attribution is open**, and it will be reported open
unless the measurement below actually resolves it. No cause is inferred from a rate.

### 5.1 What the smoke already shows, measured today

Re-run over the stored pair before writing this section:

- **10 of 10 pairs disagree on conversation shape** (D5).
- **7 of 7 pairs that agree on `outcome` still disagree on shape.**

So on the only data that exists, the trajectory is **never** reproduced step-for-step
at identical `(cfg, seed)`, and the ~30 % outcome disagreement is the fraction of a
100 % upstream divergence that survives to the verdict. n = 10; R.1 is what turns that
into a number.

**This says divergence is upstream of the outcome. It does not say where upstream.**
Shape counts are aggregates: they cannot distinguish the agent model sampling
differently, the user simulator sampling differently, a tool returning something
different, or ordering.

### 5.2 The measurement that could resolve it

`repro.toml` carries `[capture]` with `content = true` and **`max_span_bytes =
131072`**. This is R.1's one deliberate departure from `t4.toml`, and the reason is
narrow: T.4 keeps the shipped **8192 because 8192 is the number T.4 is testing**, and
at 8192 every agent-side request is dropped for a truncation marker — the airline
`policy.md` alone is 7,676 bytes — which leaves the user simulator legible and the
agent opaque, i.e. exactly half of the question. R.1 is not testing that default.

**The procedure, declared now.** For each pair, align the two episodes' span sequences
in start order and find the first index `i` where they differ. Then:

1. **`i`'s request identical, response different** → the divergence entered at a model
   sample. The span's own side (agent vs user simulator) attributes it.
2. **`i`'s request already different, while `i-1`'s response was identical** → the
   divergence entered from something that is not an LLM call: a tool response or
   ordering. τ²'s airline tools are deterministic Python over a fixed DB, so this
   case is the one that would implicate ordering.
3. **Neither** → report open, and say which pattern was seen instead.

Content lives in `attrs["gen_ai.input.messages"]` / `["gen_ai.output.messages"]`
(`capture._CONTENT_KEYS`). **The exact mapping is confirmed on the canary before 400
episodes commit**, not assumed from a source read.

**Cost and risk.** Nothing at the provider — the instrumentor wraps a call that was
going to happen (measured in T.4's preparation). Storage: ~18.5 LLM calls/episode measured,
at up to ~128 kB retained per span, forecast **~90 MB** over 400 episodes against a
12 MB store and 19 GiB free — an estimate with measured inputs, and the run is what
turns it into a number.

**Capture is a secondary objective and must not endanger the primary.** If the canary
shows capture inactive, or the span content absent, **the run proceeds without it and
attribution is reported open.** That is K3, not a kill.

---

## 6. Kill criteria

| | fires when | consequence |
|---|---|---|
| **K1** | any pair fails E3 (seeds differ) | the pairing mechanism is broken. **Report and investigate; do not analyse.** The count is the finding |
| **K2** | > 10 % of either arm errored or instrument-side | the rate bounds nothing. Report the instrument-failure rate as the result (this is S4's analysis half) |
| **K3** | capture inactive or contentless on the canary | **not a kill.** Run without it; attribution reported open |
| **K4** | D6 is not 200/200 | the two arms were not the same system. **D1 is void** |
| **K5** | any cost gate S0–S3 fires | §4 |

**There is no null here and no unpublishable result.** 0/200 would mean the substrate
is reproducible and the smoke's 3/10 was a small-sample artefact; 200/200 would mean
seeds do nothing. Both are findings. That is a property of measuring a rate rather
than testing an effect, and it is why R.1 needs no publishability clause.

---

## 7. What R.1 cannot measure

1. **Reproducibility across time.** Both arms run back-to-back in one window. The
   wall-clock gap between them is recorded. **A rate measured across a ~10-minute gap
   does not bound a rate across a week**, and provider-side serving changes are
   entirely outside it.
2. **Reproducibility at other concurrency.** Fixed at 10, because $0.011/episode and
   21 s were measured at 10.
3. **Any other model, temperature, or domain.** One pinned model on both sides of the
   conversation, temperature 0.0, airline only.
4. **Whether OpenAI honours `seed` at all.** D7 gives evidence, not a mechanism: a
   null contrast is consistent with the parameter being ignored and with it being
   honoured over a process that is nondeterministic for other reasons.
5. **Anything about arm B.** The guardrail patch is T.4's and is not run here.

---

## 8. Cost

| | figure | basis |
|---|---|---|
| Provider (OpenAI), expected | **$4.40** | `list`-free: 400 × **$0.011/episode**, itself `provider-reported` — `meta.cost_tau2` over the smoke pair measures **$0.2122 / 20 episodes = $0.01061** |
| Provider, at list | ~$9.32 | 400 × $0.0233. A bound, not a forecast: list has been a 2.2× over-estimate on every measurement, the gap being OpenAI prompt caching |
| Modal compute | **$0.11–$0.28** | `list`, scaled from the 4,400-episode row of T.4's cost table ($1.21 attributable / $3.03 whole-container) × 400/4,400 |
| `estimate_cost` will print | ~$0.079/arm | 200 × 30 s × $0.0000131/s, prices as of 2026-09-03 — **and it is wrong in a known direction** |
| **Total expected** | **~$4.51–$4.68** | |

**The Modal half is list-derived and known-defective in both directions** — `estimate_cost`
is known to over-price CPU 8× and to price memory, the dominant term, at zero.
It is quoted as a range and should not be read as measured.

**The figure that governs is `meta.cost_tau2`**, read back from the store. The project log's
`**Spend:**` line is filed against it, actual against this expectation, when R.1
reports.

---

## 9. The exact commands

Run from the development worktree (`7929fe6`, branch
`repro-pilot`, off `main` `339c75a`). **The main tree is not written.** `src/` in the
worktree is `diff -rq`-identical to `main`'s but for `__pycache__`; no source is
edited by R.1, and the only two files it adds are the sweep file and the analysis.

```bash
cd <the development worktree>
export PYTHONPATH="$PWD/examples${PYTHONPATH:+:$PYTHONPATH}"
export PROOFLOAD_STORE=<the run store>
export MODAL_IMAGE_BUILDER_VERSION=2024.10        # required; Dockerfile note 6

# C0 — the canary. One episode. Proves capture is active and the span content is
# there before 400 episodes commit. Gate S0.
proofload sweep examples/tau2_pilot/repro.toml --target tau2_pilot.rollout:rollout \
  --backend modal --max-mde 0.5 --max-rollouts 1 --yes

# R1 — arm R, fresh salt. 200 episodes. Gates S1, S2, S4.
proofload sweep examples/tau2_pilot/repro.toml --target tau2_pilot.rollout:rollout \
  --backend modal --max-mde 0.5 --yes

# R2 — arm R′. --pair-with makes it inherit R's salt, so every seed is identical.
proofload sweep examples/tau2_pilot/repro.toml --target tau2_pilot.rollout:rollout \
  --backend modal --max-mde 0.5 --pair-with <R> --yes

# The analysis. Committed at 7929fe6, before any new episode, and already run
# against the smoke pair, where it reproduces 3/10 and CP [0.0667, 0.6525].
python scripts/repro_r1_agreement.py <R> <R'>
```

`--max-mde 0.5` is required and is not a workaround: §1.1.

**The canary's episode is a real episode and it is not a pair.** It enters no
analysis; it exists to fail cheaply.

---

## 10. Addenda

### Addendum 1 — §7 item 1 is a sentence the post has to carry (2026-09-15)

**Approved before arm R launched**, and recorded here rather than edited into
§7 because the body is not edited after episodes run.

§7 item 1 stands as written: both arms run back-to-back in one window, and a rate
measured across a ~10-minute gap does not bound a rate across a week. The addition:
**that gap is the optimistic case**, so whatever R.1 measures is a **floor on a floor** —
the disagreement rate across a week can only be worse. **It is therefore not a footnote
but a sentence any post built on this number has to carry**, in the post's own words, in
the place the number appears.

---

### Addendum 2 — the canary found two span fields §5.2 did not know it had (2026-09-15)

**Written after C0 (`20260915T205836Z-50ce`, one episode, $0.00641) and before arm R's
analysis.** It changes what §5.2 can measure; it changes **nothing** about D1–D7, the
eligibility criteria, the stopping rule, or N, all of which were fixed before any
episode and are untouched.

**C0's gates, both met.** S0: `cost_tau2` $0.00641 against the $0.050 abort threshold.
K3: capture `active: true`, **12 spans, 0 dropped, 0 truncated**, content present in both
directions, largest span **13,212 B against the 131,072 limit**. *At T.4's 8192 every one
of the six agent-side spans would have been dropped for a marker* — the departure §5.2
argued for is now measured rather than reasoned.

**Two attributive fields, neither anticipated:**

1. **`gen_ai.request.seed`** — the seed **as the provider received it**, on every call,
   identical across all 12 (`3925470706`). R.1 can now assert that the seed reached
   OpenAI rather than inferring it from the wrapper's source. **Added as E6**: a pair
   whose two episodes carry different `gen_ai.request.seed` values is a construction
   failure, on the same footing as E3, and the assertion is now made at the provider
   boundary rather than at the executor's.
2. **`openai.response.system_fingerprint`** — OpenAI's own identifier for the backend
   configuration that served the call. C0 shows **two distinct fingerprints alternating
   with the side of the conversation** (`fp_0f45d14ea7` on the six agent calls,
   `fp_98cd73c4ab` on the six user-simulator calls), so within one episode the
   fingerprint tracks *which side is calling*, not drift.

   **Declared now, before the pair data exists:** if a pair's two episodes differ in the
   fingerprint at the same span index, **the provider served them from different backend
   configurations, and that is a named cause rather than an inference.** If they agree
   everywhere and the outputs still differ, the divergence is sampling within one
   configuration. This is reported as a count and **is not a substitute for §5.2's first-
   divergence alignment** — it says which configuration, never which turn.

**The storage forecast is revised down, with its basis.** C0 stored 89,669 bytes of span
content over 12 spans. At the 18.5 calls/episode measured in T.4's preparation that scales to
~138 kB/episode and **~55 MB over 400**, against §5.2's ~90 MB forecast.


### Addendum 3 — the run, and the fingerprint test's declared reading is refuted (2026-09-15)

**Both arms complete.** R `20260915T210140Z-4847` and R′ `20260915T211148Z-965d`, same
salt `d2ebb5be1d394d12`, 200/200 each, **zero errored, zero timeouts, zero infra
retries** in 400 episodes. Gates: S0–S4 all pass, cumulative **$5.4494** against the
$8.80 stop and the **$15** live provider limit. **The full result is in the project log for
2026-09-15.**

**§7 item 1, the number it asked for:** the two arms started **607.6 s** apart, the gap
between R finishing and R′ starting was **27.1 s**, and the whole window was **20.4
minutes**. Addendum 1's sentence binds on that number.

**The refutation, filed because a refuted claim is filed and not discarded.** Addendum 2 declared, before any pair data existed, that *"if a pair's two episodes
differ in the fingerprint at the same span index, the provider served them from different
backend configurations, and that is a named cause rather than an inference."* **The
declared reading does not survive its own control and is withdrawn.**

Two things went wrong with it, both measured:

1. **C0's "two fingerprints alternating with the side of the conversation" was an
   artefact of one twelve-span episode.** Across the 400 episodes there are **23 distinct
   fingerprints**, the top two covering about half the calls. The alternation addendum 2
   described is not the general picture.
2. **The rate at the first divergence is not distinguishable from chance.** At span index
   0 the request is identical *by construction*, so the fingerprint-difference rate there
   is the pure routing base rate: **99/200 = 49.5 %** [0.424, 0.566]. At the first
   divergence it is **113/200 = 56.5 %** [0.493, 0.635]. Fisher exact **p = 0.193**,
   odds ratio 1.33. **A differing fingerprint at a divergence is routing, not a cause**,
   and the claim addendum 2 licensed must not be made.

**What the fingerprint did establish, in the other direction, and it is the useful
half.** In **87 of 200** pairs the first divergence happened with the **same**
fingerprint on both sides — the same backend configuration, the same byte-identical
request, temperature 0.0, the same seed, **and a different response**. That is sampling
nondeterminism *within* one configuration, and it needs no appeal to routing at all.

**The base-rate control was not pre-registered and should have been.** §5.2 declared the
comparison without declaring what it would be compared against, which is the shape that
lets a 56.5 % look like a finding. It is recorded here as a defect in this
pre-registration, not as a detail of the analysis.

### Addendum 4 — pass 2: position carries task structure, not workflow structure; and pass 1's index distribution was contaminated (2026-09-15)

**No new episodes, no provider call.** Re-analysis of the frozen pair. Thresholds declared
and committed at `fc117cc` **before** computing; results at `ff58857`.

**A defect in pass 1, found first and reported first because it moves the numbers.**
Pass 1 compared span content byte-for-byte. OpenAI mints a fresh random `call_<22 chars>`
id for every tool call and echoes it into the next request, so **two episodes emitting the
same tool call with the same arguments differed in bytes and were scored as diverged**.
Inspected at index 3: two of three pairs differed *only* in that id — identical arguments,
identical function, identical length. `call_` ids are now normalised to a constant;
`user_id` and every other payload id is **domain data and deliberately left alone**, since
normalising those would hide real divergence.

| | pass 1 | corrected |
|---|---|---|
| first-divergence index | `{0:94, 1:64, 2:20, 3:22}` | `{0:94, 1:63, 2:21, 3:3, 4:13, 5:4, 6:1, 7:1}` |
| hazard at index 3 | 1.0000 | **0.1364** |

**What survives untouched:** **200/200 pairs still diverge**; all 200 first divergences are
still **response-only at a byte-identical request**, so the `model_sample` attribution is
unchanged and is now cleaner; 94/200 still diverge at call 0. **D1's 22.0 % does not move
at all** — it is computed from stored `outcome` strings and never touched a span.

**P5 — the structural check, and it settles the sentence in dispute.** Span index is
**not** a clock. τ²'s user simulator makes call 0 in **400/400** episodes and the agent
makes call 1 in **400/400**. "Median first-divergence index 1" therefore means *"by the
agent's first turn"* — a fact about who speaks when, not about timing.

**P4 — hazard: memoryless.** Of pairs still identical entering call `i`, the fraction
diverging at `i`: **0.470, 0.594, 0.488** over indices 0–2, all three CP intervals mutually
overlapping. **Declared verdict: FLAT.** Not increasing, so **not accumulating**; not
decreasing, so not front-loaded. Divergence is approximately **a constant ~50 % per LLM
call**, and with a median of 15 calls per episode that compounds to certainty. Censoring is
not an explanation: every pair has **at least 6** calls (median 15).

> **So the post's sentence must change.** *"Not accumulated"* is supported. *"Immediate"* is
> **not** — there is nothing special about the start; a ~50 % per-call hazard simply reaches
> the median by call 1.

**P2 — clustering by task: PRESENT.** Between-task variance share **0.399** against a
permutation null (10,000 shuffles, seed 20260915) whose mean is 0.247 and 95th percentile
0.322; **p = 0.0018**. Both declared criteria met. Concretely: **16 of 50 tasks have all
four pairs diverging at the same index**, and task means run from 0.00 to 3.50.

**P3 — does outcome disagreement track divergence position? ABSENT.** Spearman
**rho = +0.155, p = 0.281**; Kendall tau +0.129, p = 0.270. Declared threshold |rho| ≥ 0.30
and p < 0.05; neither met. **Position predicts nothing about whether the verdict flips.**

**Together these say the structure is in the task, not in the workflow position.**

**Exploratory, not pre-declared, and reported as such:** outcome disagreement may itself
cluster by task — share 0.330 against a null 95th percentile of 0.315, **p = 0.045**. That
is marginal, it was not declared in advance, and **it is not a finding**; it is a question
for a design with more than four replicates per task.

**A third methodological miss, and it is now a pattern rather than an incident.** P2's
declared effect-size floor of **0.10 sits below the permutation null's own mean of 0.247** —
data with *less* structure than chance would have cleared it. The verdict is unaffected
(both criteria fired), but the conjunction did no work, and the p-value carried it alone.
This is the same error as §5.2's missing fingerprint base rate (addendum 3) and P4's
declared window stopping at index 2 without first checking how far the support ran:
**three times in one day, a test was declared without declaring what it would be compared
against.** Recorded here as a defect of this pre-registration.
