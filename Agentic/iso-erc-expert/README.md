# iso-erc-expert

A self-contained expert on the **ISO Electronic Rating Content (ERC) corpus for
General Liability**. It answers questions about the corpus with citations, and
reviews a rating engine's behaviour against what the content actually says.

Built from a clean-room analysis of the corpus itself — 567 distinct packages,
86,664 files, 12.85M table rows, 114,726 rule elements. No ISO manual, circular
PDF or outside knowledge of GL rating was used. See `docs/erc/01-` … `06-` for
the analysis and the build specification.

## Quick start

```
cd tools
python erc.py corpus
python smoke_test.py
```

Python 3.8+, **standard library only**. No install, no dependencies, no network.

## Worked examples

**What was in force in New Jersey on 1 June 2025, and against which
countrywide edition?**

```
$ python erc.py asof NJ 2025-06-01
NJ as of 2025-06-01
  in force      GL_NJ_20250301_V01
  edition       20250301  version V01
  countrywide   GL_CW_20231201_V02
  excluded      2 later edition(s) not yet effective
  [ERC-ED-001] selection is as-of, never latest
```

Two NJ editions were excluded because they are future-effective. 83 packages in
the corpus are dated after today; selecting `max(edition)` would rate against a
filing not yet in force.

**Profile a jurisdiction.**

```
$ python erc.py juris CA
CA: 6 packages, 20211101 .. 20241101
  latest        GL_CA_20241101_V01  parent GL_CW_20231201_V02
  sublines (10, resolved):
      - Electronic Data Liability
      - Liquor
      ...
      - Underground Storage Tank
  territory     11 codes, county/place scheme; no ZIP map needed [ERC-TER-001]
  overrides     77 rules overridden, 68 state-specific, of 191 total
  tables        22 state-only, 53 shadowing countrywide, 471 inherited only
```

Note two things. The sublines are **resolved** — CA's own package ships far
fewer, and 507 of 567 packages inherit the list entirely from countrywide. And
CA has **no ZIP→territory map because it does not use one** — it resolves
territory by county/place name (11 codes, 21 place names), and those tables are
in ERC. The engine needs the risk's county or place, not its ZIP.

**Resolve a table through the override chain.**

```
$ python erc.py table PremOpsSizeOfRiskRelativity
  Rate:PremOpsSizeOfRiskRelativity
    variation    sometimes-overridden   shape interpolated band
    keys         StateCode | PremOpsSizeOfRiskRelativityTableAssignment
                 | PremOpsExposureTimesThousand_From
                 | PremOpsExposureTimesThousand_ToLessThan
    values       Relativity_From | Relativity_ToLessThan
    -> resolve state-first; if absent, inherit countrywide [ERC-CMP-005]
```

`shape: interpolated band` is the warning: this is one of only 18 tables where
the cell is **not** its literal value — `Relativity_From`/`_ToLessThan` are the
endpoints of a linear interpolation across the exposure range.

**Get the resolver plan.**

```
$ python erc.py resolve PR 2027-06-01
  1. state package      GL_PR_20270401_V02  (edition 20270401 V02)
  2. countrywide parent GL_CW_20270401_V01  (from the single xs:import)
  3. layer sizes        state 35 rate / 3 domain / 184 rules
                        cw    272 rate / 265 domain / 4528 rules
  4. overlay countrywide then state, by name, state wins, no row merging
  5. KEEP BOTH LAYERS ADDRESSABLE — ProjectName dispatch needs the parent's copy
  6. entry points: GeneralLiabilityRules/ErcProcess then /ErcCalculateTotalPremium
```

The layer sizes make the composition model concrete: PR ships 35 rate tables
against countrywide's 272.

**What does ERC actually rate?**

```
$ python erc.py premium
  BaseRate  = Product(LossCost|ELP, LCM [, ClaimsMadeMultiplier])
  FinalRate = Product(BaseRate, FinalILF, PackageModFactor, ...)
  Premium(rated)   = Round(FinalRate * <Subline>CovExposure + MedicalPaymentsCharge, 0)
  Premium(capture) = Product(ManualPremium, PackageModFactor)

  420 schema tables write a Premium
  381 (90.7%) capture a user-entered ManualPremium
   19 (4.5%) compute a premium from rates
```

This is the finding most likely to surprise a sponsor: **the great majority of
ERC's coverage content does not compute a premium**. It defines the form, the
fields, the applicability condition and the statistical coding, then multiplies
a number the user typed by `PackageModFactor`.

**The invariant register.**

```
$ python erc.py invariants --severity BLOCKER
  [BLOCKER] ERC-ID-001   Package identity comes from the XSD targetNamespace,
                         never the directory path
  [BLOCKER] ERC-CMP-003  RunRule@ProjectName must dispatch to the PARENT,
                         bypassing the overlay
  [BLOCKER] ERC-RAT-002  Rounding mode is undefined anywhere in the corpus
  ... 12 blockers in total

$ python erc.py invariants --id ERC-CMP-003 -v      # full evidence and check
```

Add `--json` to any subcommand for machine-readable output.

## Layout

```
AGENT.md              role, boundaries, evidence discipline, review protocol,
                      output contract
README.md             this file
knowledge/
  invariants.json     26 invariants (12 BLOCKER, 9 MAJOR, 5 MINOR): id, severity, statement, measured
                      evidence, executable check, impact
  corpus.json         headline counts (drift detection)
  packages.json       567 packages: identity, edition, parent, artefact counts
  jurisdictions.json  52 jurisdictions: timeline, resolved sublines,
                      territory, override volume
  table_catalogue.json 825 tables: variation class, shape, keys, values
  composition.json    the override mechanics and the 14 resolver rules
  rating.json         the premium chain, the 19 rating tables, value gotchas
  rule_model.json     52 operators, entry points, call-graph shape,
                      unspecified semantics
  territory.json      geographic mechanism and per-jurisdiction profile
tools/
  erc.py              retrieval CLI (11 subcommands)
  smoke_test.py       83 assertions against independently measured facts
```

## What it can answer

- Package identity, lineage and edition timeline for any package or jurisdiction
- What was in force in a jurisdiction on a given date, and against which
  countrywide edition
- The full resolver plan for a jurisdiction/date, with layer sizes
- Whether a table is countrywide-only, state-only, sometimes- or
  universally-overridden; its keys, values and shape
- Which sublines and coverages a jurisdiction has, **resolved**
- The premium chain, what genuinely rates, and what only captures
- The territory mechanism per jurisdiction — which of the three schemes applies
- The rule model: entry points, lifecycle, operators, call-graph shape
- The invariant register, with evidence and a concrete check for each

## What it cannot answer

- **It cannot compute a premium.** It describes the chain; it does not execute
  rules. Rounding mode alone makes a cent-accurate premium impossible from this
  corpus (see below).
- **It does not index individual instances.** Not the 114,726 rules, the 12.85M
  table rows, or the 30,449 form fields. Questions at that grain need the corpus.
- **It knows only ERC.** No manuals, no circular text beyond the 766 codes
  packages cite, no other rating product.

## Known limits of the underlying content

These are properties of the ERC corpus, not of this agent. The agent will say
`unverifiable` on all of them, which is the correct answer.

| Gap | Detail |
|---|---|
| **Rounding mode** | `@DecimalPlaces` declared **7,682 times**; the rule stated nowhere. The premium chain rounds at four stages. No premium can be asserted correct to the cent. |
| **Territory derivation** | ~~Resolved 2026-08-10.~~ All 51 resolve from ERC: **27** ZIP table, **20** single-territory (19 use `001`, NC `002`), **4** county/place (CA, FL, NY, TX). Only the last four need an input beyond the address's ZIP. |
| **`Status` A/C/D** | Empirically falsified as Add/Change/Delete. Static (99.55–100% stable across editions), `D` rows are 99.9% rateable. Store it; never act on it. |
| **`ErcCore`** | Imported by all 10 countrywide XSDs, absent from the corpus. |
| **`MessageHelper`** | 4,375 references, not shipped. The diagnostic channel must be invented. |
| **Operator semantics** | `FirstValue@Order`, `Lookup@ResultMode` against non-unique keys, `Locate@OutputAction`, `RunRule@ClearCache` — named, undefined. |
| **Semantic sufficiency** | Reference closure is 100.000% (excluding the two primitives above). That proves no dangling pointer. It does **not** prove a rating terminates with a premium. |

## Regenerating the knowledge base

If the corpus changes, `smoke_test.py` fails on the corpus-shape block. Rebuild:

```
python ../../scripts/erc/01_inventory.py        # and 02..23 as needed
python ../../scripts/erc/24_build_agent_knowledge.py
python tools/smoke_test.py
```

`knowledge/invariants.json` is hand-authored — each invariant needs a check no
script can infer. Review it manually after a corpus change.

## Provenance

Analysis: `scripts/erc/00_common.py` … `24_build_agent_knowledge.py`.
Reports: `docs/erc/01-CORPUS-AND-SCHEMA.md`,
`02-EDITIONS-AND-INTEGRITY.md`, `03-RATING-STRUCTURE.md`,
`04-BUILD-SCOPE-AND-RESOLVER.md`, `05-DATA-MODEL-AND-INGESTION.md`,
`06-VALIDATION-AND-BACKLOG.md`.

The source corpus is read-only. Nothing in this package writes to it.
