# Property chunk 28, C28-16: the outcome layer (Sets B and E)

**Status: DESIGNED 2026-10-05 with the user's choices; the build (C28-17) awaits the user's go.** No engine code changed.

## In plain English

Every Property rating gets an **outcome** beside its premium and messages: *rated*, *refused*, or *refer to company*,
with the reasons. ISO's messages stay exactly as ISO returns them. Inputs that today price a policy at $0 without a
word are **refused**, at the user's choice (2026-10-05), even though ISO rates them silently. A minimum premium, which
ISO never applies, becomes a referral when the company supplies one.

## The user's decisions (2026-10-05)

1. A silent-zero input **refuses the policy** (recommended alternative, flag and keep the premium, not chosen). This is
   **stricter than ISO** on purpose and overrides C28-17's standing rule "never change a premium ISO agrees with" for
   exactly the checks below.
2. The outcome is **a separate field**, not extra rating messages, so ISO's message set is unchanged.
3. A missing Group II territory refuses **only when Group II is attached and priced $0**.

## The checks (Property only), with their measured reach

Each refuses with an outcome naming the record and field. Counts are stored requests ISO rated (1,705) that each check
would refuse (`C28-15`, `CF-CHUNK28-SILENT-ZEROS.md`; scans of 2026-10-05):

| Check | Why (C28-15) | Stored requests refused |
|---|---|---|
| a location whose `BasicGroupIIRatingTerr` is missing, where a building's Group II coverage is attached and priced $0 | Group II $0 at ISO, silently | **218** (507 more lack the field but price Group II above $0: not refused) |
| a building without `BCEG` | Group II $0 at ISO, silently | **23** |
| Arizona: a location without `BasicGroupIReductionCredit` | Group I $0 at ISO, silently | **12** |
| a Broad or Special building with a blank `Deductible` | the whole building $0 at ISO, silently | **2** (C28-15's own probes) |

About 250 stored requests (counts can overlap) move from "ISO prices it" to "ours refuses". Each is pinned in a
regression script, so C28-17 includes moving those pins to "refuses: invalid input", or correcting the incidental bad
input where the script tests something else (the C28-05 / C28-06 pattern).

## The outcome field

`Interpreter.outcome`, set on every Property rating:

* `{"status": "rated", "reasons": []}`
* `{"status": "refused", "reasons": [{"kind": "invalid input" | "no row", "record": …, "field" | "table": …, …}]}`: the
  four checks above, and the C28-05 `SingleResult` refusals (the existing error still raises; the outcome records it)
* `{"status": "refer to company", "reasons": [{"kind": "minimum premium", "minimum": …, "rated": …}]}`

## Refer to company (OI-113)

ISO's Property rating applies no minimum premium (no rule reads one in any in-force package), and the user ruled it
a company input (2026-09-24). So: an optional company input, `CompanyMinimumPremium` on the policy; when it is supplied
and the rated total is below it, the outcome is *refer to company*, with both figures. **The premium is still the rated
one**: the referral tells a human; it never replaces ISO's number. With no company minimum supplied, nothing changes.

## Build and confirm (C28-17, C28-18)

`206_ --check` (predicted: the ~250 requests above move to refused; nothing else), `157_ --all` (293 of 293: none of
those 293 is in the refused set, to be checked), the full `104_ --gate`, every C28-15 case returning its outcome, and
every golden case still rating, unchanged.
