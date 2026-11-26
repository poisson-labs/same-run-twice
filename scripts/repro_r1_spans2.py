"""R.1 pass 2: first-divergence analysis with provider-generated identifiers normalised out.

**Why this file exists.** Pass 1 compared `gen_ai.input.messages` / `gen_ai.output.messages`
byte-for-byte. OpenAI mints a fresh random ``call_<22 chars>`` id for every tool call, and
that id is echoed into the next request's tool-result message. So two episodes that emit the
*same tool call with the same arguments* differ in bytes and were scored as diverged. Measured
at index 3: of three inspected pairs, two differed ONLY in that id -- identical arguments,
identical function, identical length.

``canon`` removes it. ``user_id`` and every other id in the payload is DOMAIN DATA and is
left alone: normalising those would hide real divergence, which is the opposite error.
"""

from __future__ import annotations

import re

CALL_ID = re.compile(r"call_[A-Za-z0-9]{16,}")
_NORM = "call_<NORM>"


def canon(text: str | None) -> str | None:
    """Provider-minted tool-call ids replaced by a constant. Nothing else touched."""
    if text is None:
        return None
    return CALL_ID.sub(_NORM, text)


def first_divergence(sa, sb, attrs, in_key, out_key, *, normalise: bool = True):
    """(index, what) of the first differing span, or (None, None). ``what`` is
    'request' / 'response' / 'both'."""
    f = canon if normalise else (lambda x: x)
    n = min(len(sa), len(sb))
    for i in range(n):
        ra, rb = f(attrs(sa[i]).get(in_key)), f(attrs(sb[i]).get(in_key))
        oa, ob = f(attrs(sa[i]).get(out_key)), f(attrs(sb[i]).get(out_key))
        if ra == rb and oa == ob:
            continue
        if ra == rb:
            return i, "response"
        return i, ("both" if oa != ob else "request")
    return None, None
