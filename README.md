# The same run, twice

The two stored runs, the analysis and the pre-registration behind the Poisson Labs post
[45.0% and 44.0%](https://poissonlabs.ai/research/the-same-run-twice/).

The post ran one agent benchmark twice with the same configuration, the same tasks and the
same seeds: τ²-bench airline, 50 tasks, 4 replicates per task, 200 episodes per run. The
first run solved 45.0% of its episodes and the second solved 44.0%. Matched episode by
episode, 44 of the 200 pairs ended with different outcomes.

Everything in this repository reads the stored runs. No command here calls a model, and the
rerun below takes a few seconds once the packages are installed.

## The three numbers

| Number | What it is | Where it comes from |
|---|---|---|
| **45.0%** | Arm R: 90 of its 200 episodes are stored with the outcome `solved`. | `scripts/pass_rates.py`, the line `R  20260915T210140Z-4847  solved 90/200 = 45.0%` in [`results/expected/pass_rates.txt`](results/expected/pass_rates.txt) |
| **44.0%** | Arm R′: 88 of its 200 episodes are stored with the outcome `solved`. | `scripts/pass_rates.py`, the line `R′ 20260915T211148Z-965d  solved 88/200 = 44.0%` in the same file |
| **44 of 200** | Pairs whose two stored outcomes differ. A pair is the episode of arm R and the episode of arm R′ with the same task and the same replicate index, which gives them the same seed. | `scripts/repro_r1_agreement.py`, the pre-registered analysis: the line `D1 outcome disagreement 44/200 = 0.2200` in [`results/expected/repro_r1_agreement.txt`](results/expected/repro_r1_agreement.txt). `scripts/pass_rates.py` prints the same count beside the 2×2 it comes from. |

The pre-registered analysis was committed before the first episode ran. It prints how many
pairs disagree. It does not print each arm's own rate. The two rates, the 2×2 and the
McNemar test were first read from the stored `outcome` column on 2026-09-15, with no script
kept. `scripts/pass_rates.py` was written for this repository on 2026-11-25 and computes
them from that column, with the pre-registered script's own join key and interval code.

## What was run

- **Benchmark.** [τ²-bench](https://github.com/sierra-research/tau2-bench) 1.0.1 at commit
  `2174a60`, airline domain, tasks 0 to 49, with its stock agent and its user simulator.
- **Model.** `gpt-4.1-mini-2025-04-14` through OpenAI's API on both sides of the
  conversation, temperature 0.0, with the `seed` request parameter set.
- **Design.** 50 tasks × 4 replicates = 200 episodes per arm, two arms, 400 episodes,
  200 pairs. The two arms share the salt `d2ebb5be1d394d12`. An episode's seed is derived
  from the salt, the hash of its configuration and its replicate index, so the two
  episodes of a pair were sent the same seed. The analysis checks that per pair (200 of
  200) and the span script checks the seed the provider received (200 of 200).
- **When.** 2026-09-15. Arm R (`20260915T210140Z-4847`) was created at 21:01:41 UTC and
  arm R′ (`20260915T211148Z-965d`) at 21:11:49 UTC, 608 seconds later. The last reply of
  R′ arrived 20.2 minutes after the first call of R.
- **Where.** Containers on Modal, 10 episodes at a time. The harness was the pre-release
  build of [Prove](https://github.com/poisson-labs/prove).
- **How it ended.** All 400 episodes ended with τ²-bench's `user_stop`, the simulated
  customer ending the conversation, and are stored as `solved` or `unsolved` by reward.
  No episode errored, timed out or was retried.
- **Cost.** $5.4494 as the provider reported it per call, $0.01362 per episode.

## Rerun it

You need Python 3.11 and git.

```console
git clone https://github.com/poisson-labs/same-run-twice.git
cd same-run-twice
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt

python scripts/pass_rates.py
PROOFLOAD_STORE=runs python scripts/repro_r1_agreement.py 20260915T210140Z-4847 20260915T211148Z-965d
```

`pass_rates.py` prints, in full in [`results/expected/pass_rates.txt`](results/expected/pass_rates.txt):

```text
Each arm on its own:
  R  20260915T210140Z-4847  solved 90/200 = 45.0%   Clopper-Pearson 95% [0.3798, 0.5218]   task-clustered boot [0.3400, 0.5650]
  R′ 20260915T211148Z-965d  solved 88/200 = 44.0%   Clopper-Pearson 95% [0.3701, 0.5117]   task-clustered boot [0.3350, 0.5500]

                 R′ solved   R′ unsolved
R solved                67            23      90
R unsolved              21            89     110
                        88           112     200

Pairs whose two outcomes disagree: 44 of 200 = 22.0%
Exact McNemar on the 44 disagreeing pairs (23 against 21): p = 0.880
Net swing (23 - 21)/200 = +1.0 points   task-clustered boot 95% [-5.5, +7.5]
```

`repro_r1_agreement.py` prints, in full in
[`results/expected/repro_r1_agreement.txt`](results/expected/repro_r1_agreement.txt):

```text
eligible (E1-E5, E2 applied): n=200
  D1 outcome disagreement 44/200 = 0.2200
     Clopper-Pearson 95%   [0.1646, 0.2839]  width 0.1192
     task-clustered boot   [0.1550, 0.2850]  width 0.1300
...
D7 seed contrast (different seed, same task, same cfg): 280/1200 = 0.2333
...
  provider-reported cost over eligible pairs: $5.4494 (400 episodes, $0.01362/episode)
```

To check first that the runs are the files that were stored on 2026-09-15:

```console
(cd runs && shasum -a 256 -c --quiet SHA256SUMS)
```

The span analysis behind the post's sections on divergence reruns the same way:

```console
PROOFLOAD_STORE=runs python scripts/repro_r1_spans.py 20260915T210140Z-4847 20260915T211148Z-965d
python scripts/first_divergence.py
```

## Which package reads these runs

- The runs were written by the package under its pre-release name, `proofload`, version
  0.0.1. Both manifests record `proofload_version: 0.0.1`. That version was never
  published. The `proofload` distribution on PyPI is an empty placeholder (0.0.0) and
  cannot read them.
- The package was released as [`poisson-prove`](https://pypi.org/project/poisson-prove/).
  Version **0.4.0**, the current release, reads both runs as they were stored: a
  `manifest.json` and one Parquet file per episode. `requirements.txt` pins it, with
  numpy 2.4.6, pandas 3.1.1, pyarrow 26.0.1, scipy 1.17.1 and what those need: 17
  packages at exact versions.
- The rerun was checked on Python 3.11.15 on macOS (arm64). The runs were written under
  Python 3.11.7.
- The filed scripts imported `proofload.store`. Here they import `poisson_prove.store`,
  the same class in the released package. The environment variable keeps its filed name,
  `PROOFLOAD_STORE`. The filed scripts on the pre-release source and the scripts here on
  0.4.0 print the same output, character for character.

## What poisson-prove 0.4.0 does with these two runs

`poisson-prove diff` compares the two runs. It pairs them on their shared seeds and tests
each of the 50 tasks on its own. With four replicates a task, no single task can be
flagged, and it reports `too small to tell`. It does not print the pooled rates.

```console
poisson-prove --store runs diff 20260915T210140Z-4847 20260915T211148Z-965d
```

`poisson-prove paired`, the request-level pair check, refuses them:

```console
$ poisson-prove --store runs paired --declaration scripts/pair-check.toml
error: no eligible pairs: of 200 keys 200 matched and none was eligible (retry_or_multicall 200); there is nothing to analyse, and nothing was written
```

It exits 1 and writes nothing. The development head of Prove on 2026-11-25 (commit
`00daf79`) prints the same refusal.

The refusal is correct for what that command checks. `paired` is built for a replay in
which each episode sends one request: a grader scoring an answer, a classifier routing a
ticket. It asserts that the two arms sent the same single request, and it reads the request
body from the request span's `input` field. These episodes are conversations. Each makes
between 6 and 44 model calls, 7,369 across the 400 episodes, all recorded under one span
name. `paired` counts a second call under the request span's name as a retry and excludes
the pair as `retry_or_multicall`. The spans here also store their message text in span
attributes (`gen_ai.input.messages`, `gen_ai.output.messages`) and leave `input` empty.

None of the three numbers passes through that check. They are counted from the stored
`outcome` of each episode, joined on configuration hash and replicate index, with the seed
compared within every pair. The request-level claim the post does make, that every pair's
requests were byte-identical up to the first reply that differed, comes from the span
scripts in this repository, which compare the two episodes call by call.

## The post's other numbers

| In the post | Script | Recorded output |
|---|---|---|
| The 2×2 (67, 23, 21, 89); exact McNemar p = 0.880; net swing +1.0 points, task-clustered interval −5.5 to +7.5 | `scripts/pass_rates.py` | `results/expected/pass_rates.txt` |
| 44 of 200 = 22.0%, task-clustered 95% interval 0.155 to 0.285; same seed 22.0% against different seed 23.3%; $5.45, $0.0136 per episode | `scripts/repro_r1_agreement.py` | `results/expected/repro_r1_agreement.txt` |
| All 200 pairs diverge; all 200 first divergences are a different reply to an identical request; none starts at a tool result or at ordering | `scripts/repro_r1_spans.py` | `results/expected/repro_r1_spans.txt`, `results/results-r1-spans.csv` |
| Hazard 0.470, 0.594, 0.488 over the first three calls; 1.00 before the correction and 0.14 after it at call 3; 94 of 200 diverge at call 0; the user simulator makes call 0 and the agent call 1 in all 400 episodes | `scripts/first_divergence.py` | `results/expected/first_divergence.txt`, `results/results-r1-p2.csv` |
| Between-task variance share 0.399 against a permutation null averaging 0.247, p = 0.0018; 16 of 50 tasks with all four pairs at one index; Spearman rho +0.155, p = 0.281 | `scripts/first_divergence.py` | `results/expected/first_divergence.txt` |
| Fingerprint differs at call 0 in 49.5% of pairs and at the first divergence in 56.5%, Fisher p = 0.193; 87 of 200 diverge under the same fingerprint; 114 pairs diverge first in the user simulator and 86 in the agent | `scripts/first_divergence.py`, the lines marked `first pass` | `results/expected/first_divergence.txt` |

Two passes were made over the spans, and the post explains why. The first compared spans
byte for byte. The second replaces the provider's random tool-call ids with a constant
before comparing, and changes nothing else. `scripts/first_divergence.py` prints both.

The post takes its hazard figures from the second pass. The three figures in the last row
of the table are first-pass figures. With tool-call ids normalized they read 54.5% at the
first divergence (Fisher p = 0.368), 91 of 200 under the same fingerprint, and 116 pairs
first diverging in the user simulator against 84 in the agent. On either pass the rate at
the first divergence is within sampling error of the 49.5% base rate.

`results/results-r1-spans.csv` and `results/results-r1-p2.csv` are the per-pair tables
written on 2026-09-15. The scripts here rewrite both from the stored runs, byte for byte.
The second pass was made that day with the helpers in `scripts/repro_r1_spans2.py` and no
driver script was kept. `scripts/first_divergence.py` is that driver, written for this
repository on 2026-11-25.

Addendum 4 of the pre-registration reports one exploratory figure, a permutation p of
0.045 for outcome disagreement clustering by task. The driver here prints 0.046 for it
(0.0459), with the same variance share and null percentile. The post does not use it.

## Definitions filed before the run

[`PREREGISTRATION.md`](PREREGISTRATION.md) is the full text, with its addenda. It was
written on 2026-09-15 before any episode. In short:

- **Agreement.** Two episodes of a pair agree when their stored `outcome` strings are
  equal, over the whole outcome vocabulary. The disagreement rate is the share of eligible
  pairs that do not agree.
- **Intervals.** Clopper-Pearson, and a bootstrap over the 50 tasks (10,000 resamples, seed
  20260915) because the four pairs of a task are not independent. Where the two differ,
  the task-clustered interval is the one quoted.
- **Eligibility.** Both outcomes present; neither outcome one of τ²-bench's four labels for
  a run that died; the same seed in both episodes; exactly one row per cell per run; the
  same salt and target in both manifests. Every exclusion is counted and printed. Here
  none applied: 200 of 200 pairs are eligible.
- **Stopping.** Nothing stops on the disagreement rate. The 400 episodes were committed in
  advance. The only stops were on cost and on instrument failure, with thresholds stated,
  and none fired.
- **The seed contrast.** Episodes of the same task at different replicate indices share a
  configuration and differ in seed. Their disagreement rate is the reference for the
  same-seed rate.
- **Where divergence enters.** Align the two episodes' model calls in order and classify
  the first one that differs: an identical request with a different reply, or a request
  that already differs.

[`PASS-2-DECLARATION.md`](PASS-2-DECLARATION.md) holds the thresholds for the second pass
(clustering by task, position against outcome, the shape of the hazard), written after the
runs and before those numbers were computed.

The order of events on 2026-09-15, in UTC, from the commit times of the development
history and the run manifests:

| Time | Event |
|---|---|
| 20:20:55 | `scripts/repro_r1_agreement.py` committed |
| 20:58:36 | a one-episode canary run, in no analysis |
| 21:01:41 | arm R created |
| 21:03:57 | `scripts/repro_r1_spans.py` committed, while arm R was running |
| 21:11:49 | arm R′ created |
| 21:47:59 | `PASS-2-DECLARATION.md` committed |
| 21:51:56 | `scripts/repro_r1_spans2.py` and the second-pass table committed |

## What the post withdrew, and why

The pre-registration and its addenda are published as they were filed, including readings
the post withdrew or narrowed. Where the two differ, the post states the claim.

- **A differing backend fingerprint as a cause.** Addendum 2 declared, before the pair data
  existed, that a pair whose episodes carry different fingerprints at the same call had
  been served by different backend configurations, and that this would name a cause.
  Withdrawn in addendum 3 and in the post. The declaration named no rate to compare
  against. At call 0, where the request is identical by construction, the fingerprint
  already differs in 49.5% of pairs. At the first divergence it differs in 56.5%, Fisher
  p = 0.193. The post also does not conclude the reverse: this design could not detect a
  small association.
- **Divergence as immediate.** The first pass put the median first divergence at call
  index 1, and that was first read as divergence happening at once. Withdrawn. The user
  simulator makes call 0 and the agent makes call 1 in all 400 episodes, so index 1 is
  the agent's first turn. It records who speaks when.
- **The first-pass index distribution.** The first pass counted two identical tool calls as
  different because the provider gives every tool call a fresh random id. Corrected in the
  second pass. The hazard at call 3 went from 1.00 to 0.14. The 44 of 200 was never
  affected: it is counted from stored outcomes.
- **A per-call rate and independence.** Addendum 4 calls the hazard memoryless and describes
  a constant rate of about 50% per call that compounds over an episode. The post claims
  less: the hazard does not rise over the first three calls, which rules out drift, and
  independence between calls was not tested.
- **The rate as a floor.** Addendum 1 says a rate measured across ten minutes is the
  optimistic case and that a week can only be worse. The post does not carry that. It says
  the rate over longer windows is not known.
- **Routing as the explanation.** Addendum 3 reads the fingerprint result as "routing, not
  a cause". The post says only that the rate at the first divergence is not
  distinguishable from the base rate.
- **The seed parameter doing nothing.** The pre-registration words the seed contrast as the
  parameter "buying nothing". The post narrows it to this comparison: matching seeds did
  not measurably reduce disagreement here, and the provider documents the parameter as
  best-effort.
- **A threshold that did no work.** The second pass declared clustering present at p < 0.05
  and a between-task variance share of at least 0.10. The permutation null's own mean is
  0.247, so the 0.10 floor could not fail. The verdict rested on the p-value alone, and
  addendum 4 and the post both record that as a defect of the declaration.

## What this does not show

- A rate for any other model, provider, benchmark or week. It is 200 pairs on one model
  pin, one provider and one twenty-minute window.
- Why the replies differ. The first difference is a different reply to an identical
  request, and what produces it is inside the provider.
- Anything at the level of one task. Four pairs a task is too few.
- The 7 of 10 agreement the pre-registration's section 0 cites from an earlier ten-pair
  smoke run. Those runs are not in this repository, so that figure cannot be rerun here.
- A way to run the two arms again. The benchmark wrapper and the sweep file are not in this
  repository. Each manifest records the sweep's whole specification under `environment`.

## What is here

| Path | What |
|---|---|
| `runs/20260915T210140Z-4847/`, `runs/20260915T211148Z-965d/` | Arm R and arm R′ as stored: a `manifest.json` and 200 Parquet files each, one per episode, with every model call the episode made |
| `runs/SHA256SUMS` | The sha256 of each of the 402 files |
| `scripts/repro_r1_agreement.py` | The pre-registered analysis |
| `scripts/repro_r1_spans.py`, `scripts/repro_r1_spans2.py` | The first span pass, and the helpers of the second |
| `scripts/pass_rates.py`, `scripts/first_divergence.py` | Written for this repository on 2026-11-25: each arm's rate with the 2×2, and the driver of the second span pass |
| `scripts/pair-check.toml` | The declaration behind the refusal quoted above |
| `results/` | The two per-pair tables of 2026-09-15, and under `expected/` what each script prints |
| `PREREGISTRATION.md`, `PASS-2-DECLARATION.md` | What was filed before the run, and before the second pass |
| `tests/` | Reruns every script and compares with `results/` |

Each stored episode holds the full text of its conversation. The customers in it, their
names and their `@example.com` addresses are τ²-bench's synthetic data. The manifests'
`secrets` field holds the name of a secret at the compute provider and no key.

### What differs from the filed files

- `runs/`: nothing. The 402 files are byte-identical to the stored ones.
- `scripts/repro_r1_agreement.py`: three lines. The import of the package's store class
  uses the released package name, and two comments that cited private documents now
  describe what they cited. As filed, its sha256 was
  `b749760d65abda55fca4665f50399232ca02c8b43b0f27b0208e026be5f1b04d`.
- `scripts/repro_r1_spans.py`: the same import line. As filed,
  `aa5b22bc6bd006607099195d6345bfb1f327202715df45e8268c97e7892b522a`.
- `scripts/repro_r1_spans2.py`, `PASS-2-DECLARATION.md` (filed as `R1-P2-DECLARATION.md`)
  and the two tables in `results/`: nothing.
- `PREREGISTRATION.md`: 23 passages and the metadata block, listed at the top of that file.

## Tests

```console
python -m pip install pytest==9.2.0 ruff==0.17.6
python -m pytest
ruff check .
```

Eight tests, about fifteen seconds. They check the 402 checksums, rerun each script against
the stored runs and compare what it prints, and what it writes, with `results/`.

## License and citation

The scripts, the documents and the stored runs are under the MIT license ([`LICENSE`](LICENSE)).
[`NOTICE`](NOTICE) gives τ²-bench's license and citations and the terms on the model's
replies.

```bibtex
@misc{poissonlabs2026samerun,
  title        = {45.0\% and 44.0\%},
  author       = {{Poisson Labs}},
  year         = {2026},
  howpublished = {\url{https://poissonlabs.ai/research/the-same-run-twice/}},
  note         = {Runs and analysis: \url{https://github.com/poisson-labs/same-run-twice}}
}
```

Questions: work@poissonlabs.ai.
