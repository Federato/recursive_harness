#!/usr/bin/env python3
"""Chunk 9, C9-12 -- the golden case comes back with no unexplained
validation message: the 4 blanket-specific messages (C9-10) plus the
ordinary 5-group message set, same discipline chunks 1/3/4/5/6/7/8 all
DEFERRED (gate point 9 is `owed project-wide`, never closed by any prior
chunk -- confirmed directly by grepping every `docs/CF-CHUNKn-GATE.md`, not
assumed from this task's own framing).

Runs the golden case fresh (no assumption the count is still whatever a
prior doc recorded) and classifies each message: DESIGNED OUT (explained,
expected, harmless) or LOGGED (`CF_Algorithm/CF_Message_Register.md`,
M-001/M-002).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib
golden = importlib.import_module("68_chunk9_golden_case")

DESIGNED_OUT_OR_LOGGED = {
    "CP 03 20 Must Be Attached When Fixed Dollar Amount Deductible For Each Location "
    "Are Different Than Windstorm Or Hail Deductible Or Theft Deductible": (
        "LOGGED (M-001, CF_Message_Register.md) -- same rule, same class "
        "(Payload defect: deductible coherence never tested by our builders), "
        "already fully diagnosed for a different state (AL). Fires twice here "
        "(once per structure) because both structures inherit chunk 1's own "
        "risk, which never set TheftDeductible/WindstormOrHailDeductible "
        "coherently -- the golden case is testing blanket averaging, not "
        "deductible coherence, so this is expected repeat of a known cause, "
        "not a new one."
    ),
    "Either CP 10 75 Or CP 10 76 must be attached": (
        "LOGGED (M-002, CF_Message_Register.md, added this task) -- a "
        "policy-wide, always-on form-attachment check unrelated to blanket "
        "or to Basic Group I; fires on every CF golden case built so far "
        "(first noted narratively in CF-CHUNK1-GOLDEN-CASE.md Sec.5) because "
        "none schedules CP 10 75/76. Designed out: attaching either form "
        "solely to silence this message, on a case not testing either "
        "endorsement, risks the opposing 'should not be attached' rule."
    ),
}

# The 4 blanket-specific messages, confirmed by 76_chunk9_c9-10 not to fire
# on the golden case as built (2 structures, no EQ form, no PeakSeason
# indicator, no Business Income table) -- nothing to design out or log
# because none of them appear in this case's own message list.
FOUR_BLANKET_MESSAGES = [
    "Blanket Rating requires 2 or more risks to be valid",
    # (no literal text captured for the EQ-sprinkler-leakage and BI-indemnity
    # messages -- neither's gate is reachable without an EQ form / BI table
    # this golden case never carries; see 76_chunk9_c9-10's rule-condition
    # reads)
]


def main() -> int:
    print("=== 1. Run the golden case fresh, capture every message ===")
    _, ip = golden.run()
    messages = list(ip.messages)
    print(f"  Count: {len(messages)}")
    for m in messages:
        print(f"    - {m}")

    print("\n=== 2. Classify each ===")
    designed_out_or_logged = 0
    unexplained = []
    for m in messages:
        verdict = DESIGNED_OUT_OR_LOGGED.get(m)
        if verdict:
            designed_out_or_logged += 1
            print(f"\n  [{m[:70]}...]" if len(m) > 70 else f"\n  [{m}]")
            print(f"    -> {verdict}")
        else:
            unexplained.append(m)

    print("\n=== 3. The 4 blanket-specific messages (C9-10) ===")
    print("  None of the 4 (Requires2OrMoreRisks, RequiresSameEQSprinklerLeakage, "
          "PeakSeasonGeneralInfoRequired, BIIndemnityOptionConsistency) appear "
          "in this golden case's own message list -- confirmed in "
          "76_chunk9_c9-10_exclusion_messages.py by reading each rule's gate "
          "condition against this submission's actual fields (2 structures, "
          "no EQ form anywhere, no PeakSeasonIndicator, no Business Income "
          "table). Nothing to design out or log for THIS submission; "
          "'2 or more risks' was independently confirmed reachable on a "
          "deliberately-broken 1-structure variant, which is not this golden "
          "case and is not counted in this tally.")

    n_total = len(messages)
    n_designed_or_logged = designed_out_or_logged
    n_unexplained = len(unexplained)

    print(f"\n=== Final tally ===")
    print(f"  {n_total} messages on the golden case: "
          f"{n_designed_or_logged} designed-out/logged, "
          f"{n_unexplained} unexplained.")
    if unexplained:
        print("  UNEXPLAINED:")
        for m in unexplained:
            print(f"    - {m}")
        print("\nGate point 9 NOT met for this golden case.")
        return 1

    print("\nGate point 9 met for chunk 9's OWN golden case: every message "
          "either designed out or logged, 0 unexplained. This closes gate "
          "point 9 for chunk 9 specifically -- the project-wide backlog for "
          "chunks 1-8's own golden cases (docs/CF-CHUNKn-GATE.md, all "
          "'owed project-wide') is untouched by this task and remains open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
