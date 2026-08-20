# Commercial Fire / Property Rating Engine — Build Plan (First Pass)

**Status: item 1 of `docs/CF-PROPERTY-INTEGRATION-PROPOSAL.md`, complete. Nothing past this point
is authorized.** This document is deliberately smaller than
`docs/GL-RATING-ENGINE-BUILD-PLAN.md` — GL's plan came after sixteen build steps across five
stages; this comes after one blind ERC-side analysis and its first comparison against the
existing manual-side work. Treat it as a starting non-negotiables list, not a finished
architecture document — it should grow the way GL's did, one coverage gate at a time.

## What's established so far

- **The countrywide package holds method, not money**, for at least the Building/Special coverage
  path — confirmed two independent ways (`CF_Algorithm/ERC-VS-CIRCULAR-COMPARISON.md`). Expect
  the same pattern to hold for the other four documented coverage groups (Personal Property,
  Business Income, Special Class, Special Class Business Income) but this has not been checked
  coverage-by-coverage yet.
- **CF's corpus is missing five jurisdictions outright** — HI, ID, LA, MS, WA — not just unfiled
  in the current edition. Four of those were already known gaps on the manual side; Hawaii was
  not, until this comparison.
- **CF's multiply operator is `rul:Product`**, not `rul:Multiply` — a naming difference from
  whatever GL's engine assumes, worth checking before any code reuse between `gl_engine` and a
  future `cf_engine` is attempted.
- **CF's territory scheme looks structurally different from GL's** — county/place tables rather
  than ZIP-code tables, in every state sampled. If this holds across the rest of the corpus, GL's
  ZIP-code territory-resolution logic is not directly reusable for CF; a county/place resolver is
  a separate piece of work.
- **CF's master schema is a single monolithic file, same as GL's** — this was suspected to be a CF
  peculiarity and turned out not to be a real difference once checked against GL's own schema.
  Recorded so the assumption doesn't resurface uncorrected.

## Working non-negotiables (first pass — expect this list to grow)

Mirroring the discipline behind GL's eighteen, not the content — CF's traps are its own:

1. **Never read a countrywide rate table as authoritative without checking whether it's
   header-only.** 22.4% of CF's countrywide tables carry zero data rows; the multiply/lookup
   chain around them looks complete even when the table itself resolves nothing.
2. **Never assume a jurisdiction's absence is a licensing gap without checking the corpus
   directly.** The manual side tracked four known-missing states by name; a fifth (Hawaii) was
   invisible until someone counted what should exist and wasn't.
3. **Never assume GL's territory-resolution approach transfers.** CF's territory tables are keyed
   by county/place name in every state sampled so far, not by ZIP code.
4. **Cite the exact operator element, not the expected one.** An early grep for `rul:Multiply`
   found nothing; the real element is `rul:Product`. A rule model built on the assumed name would
   have silently under-counted CF's math.
5. **Distinguish an edition-specific gap from a corpus-wide one.** FL, IL, and NJ are missing from
   the current (20260601) edition specifically but exist in earlier editions — a different
   failure mode from Hawaii's, and one that needs its own explanation before it's trusted either
   way.

## What comes next, if and when authorized

Per the proposal, items 2–4 (a `cf_engine/` package reusing the interpreter architecture, a
coverage-by-coverage gated build order, and separated GL/CF testing and reporting) remain
unauthorized. The immediate useful next step within item 1's spirit, if this work continues, is
extending the ERC-side knowledge base's coverage — the state-level packages, the remaining four
coverage groups' rule chains, and a full (not sampled) territory-scheme survey — before treating
this plan as settled.

---

**Written 2026-08-20**, from `Agentic/cf-erc-expert/knowledge/*.json` and
`CF_Algorithm/ERC-VS-CIRCULAR-COMPARISON.md`.
