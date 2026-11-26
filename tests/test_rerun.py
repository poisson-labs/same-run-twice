"""Rerun every script against the stored runs and compare with what is recorded here.

Each test reads the two arms in ``runs/``. Nothing calls a model and nothing is written
into the repository.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
SCRIPTS = ROOT / "scripts"
EXPECTED = ROOT / "results" / "expected"
ARMS = ["20260915T210140Z-4847", "20260915T211148Z-965d"]


def run(args: list[str], **env: str) -> subprocess.CompletedProcess[str]:
    full_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **env}
    return subprocess.run(args, cwd=ROOT, env=full_env, capture_output=True, text=True, check=False)


def script(name: str, *args: str, **env: str) -> str:
    done = run([sys.executable, str(SCRIPTS / name), *args], **env)
    assert done.returncode == 0, done.stderr
    return done.stdout


def test_the_stored_runs_are_the_files_that_were_checksummed():
    listed = {}
    for line in (RUNS / "SHA256SUMS").read_text().splitlines():
        digest, path = line.split(maxsplit=1)
        listed[path] = digest
    on_disk = {
        p.relative_to(RUNS).as_posix()
        for arm in ARMS
        for p in (RUNS / arm).rglob("*")
        if p.is_file()
    }
    assert on_disk == set(listed)
    assert len(listed) == 402
    for path, digest in listed.items():
        assert hashlib.sha256((RUNS / path).read_bytes()).hexdigest() == digest, path


def test_pass_rates_prints_the_three_numbers():
    out = script("pass_rates.py")
    assert out == (EXPECTED / "pass_rates.txt").read_text()
    assert "solved 90/200 = 45.0%" in out
    assert "solved 88/200 = 44.0%" in out
    assert "Pairs whose two outcomes disagree: 44 of 200 = 22.0%" in out


def test_the_preregistered_analysis_prints_what_is_recorded():
    out = script("repro_r1_agreement.py", *ARMS, PROOFLOAD_STORE=str(RUNS))
    assert out == (EXPECTED / "repro_r1_agreement.txt").read_text()
    assert "D1 outcome disagreement 44/200 = 0.2200" in out
    assert "task-clustered boot   [0.1550, 0.2850]" in out
    assert "280/1200 = 0.2333" in out
    assert "$5.4494 (400 episodes, $0.01362/episode)" in out


def test_the_first_span_pass_rewrites_its_table(tmp_path):
    table = tmp_path / "spans.csv"
    out = script("repro_r1_spans.py", *ARMS, PROOFLOAD_STORE=str(RUNS), R1_SPANS_OUT=str(table))
    printed = out[: out.index("\nper-pair detail ->")]
    assert printed == (EXPECTED / "repro_r1_spans.txt").read_text()
    assert table.read_bytes() == (ROOT / "results" / "results-r1-spans.csv").read_bytes()


def test_the_second_span_pass_rewrites_its_table(tmp_path):
    table = tmp_path / "p2.csv"
    out = script("first_divergence.py", "--out", str(table))
    assert out == (EXPECTED / "first_divergence.txt").read_text()
    assert table.read_bytes() == (ROOT / "results" / "results-r1-p2.csv").read_bytes()


def test_the_pair_check_refuses_these_runs():
    done = run(
        [sys.executable, "-m", "poisson_prove", "--store", str(RUNS), "--plain",
         "paired", "--declaration", str(SCRIPTS / "pair-check.toml"), "--json"],
    )
    assert done.returncode == 1
    assert done.stderr.strip() == (EXPECTED / "pair_check.txt").read_text().strip()
    assert "retry_or_multicall 200" in done.stderr


def test_requirements_carry_the_pins_in_pyproject():
    pins = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]
    compiled = set(re.findall(r"^[A-Za-z0-9_.-]+==\S+", (ROOT / "requirements.txt").read_text(), re.MULTILINE))
    assert set(pins) <= compiled


def test_no_file_holds_a_local_path():
    skip = {".git", ".venv", "runs"}
    for path in ROOT.rglob("*"):
        if path.is_dir() or skip & set(path.relative_to(ROOT).parts):
            continue
        if path.suffix not in {".py", ".md", ".toml", ".txt", ".csv", ""}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        assert not re.search(r"/(Users|home)/[A-Za-z0-9_.-]+/", text), path
