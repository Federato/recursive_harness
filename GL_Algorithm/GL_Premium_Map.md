# GL premium map — every premium field, what feeds it, where it ends up

**The question this answers:** for General Liability, where does every premium number come
from, and how does it reach the one figure that is the account's premium?

**The answer in one line:**
`GeneralLiability.ErcCalculatedTotalPremium` is the account total, and **every one of the
571 groups that carry a premium reaches it** — through at most four levels of summation.

**Source:** `GL CW 20270401 V01`, countrywide, 572 rule files.
**Navigable version:** `GL_Algorithm/GL_Premium_Tree.html` — the same tree, collapsible and
searchable, with a jurisdiction selector that overlays what each of the 51 state packages adds
or rewrites.

**Companion data:** `GL_Algorithm/GL_Premium_Map.xlsx` — four sheets: `Summary`,
`RollUpTree` (571 rows, one per group), `PremiumSources` (322 rows, one per premium
calculation), `PremiumFields` (163 rows).

**Written:** 2026-09-17.

---

## 1. Three mechanisms, and only three

The whole premium architecture is three rule names repeated across the corpus:

| Rule | Count | What it does |
|---|---|---|
| `SetPremium` | **322** | turns a rate into dollars on one record |
| `SetPremiumIndicator` | **322** | says whether that record produced a premium at all |
| `CalculateTotalPremium` | **571** | collects premium upward, one level at a time |

There is no fourth mechanism and no special case at the top. The account total is produced
by the same rule name as every subtotal beneath it.

---

## 2. Rate and premium are separate phases

**Not one of the 322 `SetPremium` rules performs a table lookup.** Checked directly: zero
`MatrixDef` references across all of them.

By the time `SetPremium` runs, the rating chain has already resolved the record's
`FinalRate` and written it to the record. `SetPremium` only converts. The canonical case,
`GeneralLiabilityClassificationPremOpsCoverage`, reads exactly four values:

```
FinalRate                  the rate, already computed
PremiumBasis               which divisor applies (Admissions, Area, Gross Sales, Payroll …)
../PremOpsCovExposure      the exposure, from the parent classification
../Subline                 which subline is in force
```

and uses two operators — `Product` and `Divide`. That is the entire premium calculation:
**rate × exposure ÷ basis divisor.**

This split matters for anyone reading a wrong premium: a wrong number is either a wrong
*rate* (the rating chain) or a wrong *exposure/basis* (the premium chain). The two are
cleanly separable, and `FinalRate` is the seam.

---

## 3. How a premium climbs to the account total

### At a leaf — a coverage record

`CalculateTotalPremium` on a leaf is a gate, not a sum:

```
if PremiumIndicator = 1 AND Premium <> 0:
        contribute Premium
else:
        contribute 0
```

**Two conditions, not one.** A record with a premium but an indicator of 0 contributes
nothing, and so does a record whose premium is exactly zero. `PremiumIndicator` is what
distinguishes *"this coverage rated to zero"* from *"this coverage was not on the policy"* —
and both contribute the same 0, so the indicator is the only place that difference survives.

### At an aggregator — a location, a classification, the policy

```
ErcCalculatedTotalPremium = Sum(
    for each child record:  that child's CalculateTotalPremium
)
```

Children are reached two different ways, and **reading only one of them silently loses
premium**:

| Child kind | How it is summed | Payload form |
|---|---|---|
| repeating | `<rul:ForEach AtDataDef="XTable/X">` | JSON array |
| singleton | `<rul:Locate AtDataDef="X">` | JSON object |

This is the same array-vs-object distinction that governs the request format. At the root,
**400 children are repeating and 19 are singletons** — a reader that handled only `ForEach`
would miss 19 whole endorsement families.

### The spine

```
GeneralLiability                                   depth 0   419 children   ← ACCOUNT TOTAL
└── GeneralLiabilityLocation                       depth 1    18 children
    └── GeneralLiabilityClassification             depth 2    19 children
        ├── …PremOpsCoverage                       depth 3   leaf, SetPremium
        ├── …ProdsCompldOpsCoverage                depth 3   leaf, SetPremium
        ├── GeneralLiabilityTerrorism              depth 3    3 children
        │   └── …TerrorismPremOpsCoverage          depth 4   leaf, SetPremium
        └── GeneralLiabilityUnmannedAircraft       depth 3    3 children
            └── …UnmannedAircraftCovABIPDCoverage  depth 4   leaf, SetPremium
```

**Location and Classification contribute their own `Premium` as well as their children's** —
they are not pure containers. A premium can be written at any level.

### Depth distribution

| Depth below the account total | Groups |
|---|---|
| 0 — the account itself | 1 |
| 1 | 419 |
| 2 | 110 |
| 3 | 34 |
| 4 — deepest | 7 |

**The tree is wide, not deep.** 419 of 571 groups hang directly off the policy — almost all
of them endorsements that price at policy level rather than against a classification. Only 7
groups sit four levels down: the three Terrorism coverages, the three Unmanned Aircraft
coverages, and Medical Payments Exclusion Coverage C.

**Every group reaches the root. Zero orphans** — no group computes a premium that the
account total fails to collect.

---

## 4. The premium fields themselves

**163 distinct premium-named fields exist in the DataDef. Only 22 are ever written by a
rule.** The other 141 are carried, not computed.

Twelve of them are declared on **all 1,025 datadef groups** — the standard premium block
every record carries whether or not it ever holds a premium:

`Premium` · `PremiumIndicator` · `AnnualPremium` · `PolicyTermPremium` · `ProRatedPremium` ·
`PriorPremium` · `ProRatedPriorPremium` · `ChangePremium` · `ProRatedChangePremium` ·
`TotalProRatedChangePremium` · `EvaluatedPremium` · `OverridePremium`

Of those twelve, **the rules write exactly two — `Premium` and `PremiumIndicator`.** The
other ten are policy-administration fields, and §5 measures just how inert they are: zero
writes and zero reads across all 52 jurisdictions. A reader who assumes `AnnualPremium` is
computed will find nothing computing it, in any state.

### What the rules actually write

| Field | Writes | Role |
|---|---|---|
| `PremiumIndicator` | 644 | did this record produce a premium |
| `Premium` | 393 | the record's own premium |
| `ErcCalculatedTotalPremium` | 112 | a subtotal, at each aggregating level |
| `BasicLimitPremium` | 9 | pre-ILF premium |
| `PremiumDiscountCharge` | 6 | |
| `PremiumBasis` | 6 | |
| `MinPremium` | 4 | |
| the remaining 15 | 1–3 each | coverage-specific totals |

`ErcCalculatedTotalPremium` being written 112 times against 571 participating groups is the
aggregator count: **112 groups hold a subtotal, 459 are leaves** that hand their `Premium`
upward without storing one.

---

## 5. Interim premium — written, pro-rata, endorsement: not in the ruleset

A fair question about any premium map is whether it covers the *transaction* side: written
premium, pro-rata, earned, endorsement change. **It does not, because ISO's ruleset does not
compute any of it.** That is a finding, not an omission in the map — and it was checked
rather than assumed.

Every record in the corpus carries a **fourteen-field policy-administration block**, declared
on all 1,025 datadef groups. Measured across **all 52 jurisdictions**, every one of the
fourteen is written **zero** times and read **zero** times by any rule:

| Field | Writes | Reads |
|---|---|---|
| `AnnualPremium` · `PolicyTermPremium` · `PriorPremium` | 0 | 0 |
| `ProRatedPremium` · `ProRatedPriorPremium` · `ProRatedChangePremium` · `TotalProRatedChangePremium` | 0 | 0 |
| `ChangePremium` · `EvaluatedPremium` · `OverridePremium` | 0 | 0 |
| `ProRateFactor` · `ProRateIndicator` · `TermFactorIndicator` · `EarnedInFullIndicator` | 0 | 0 |

Nothing computes them; nothing consumes them. They are **inert carriers** — a shape a policy
administration system is expected to fill, shipped inside ISO's schema so a round-tripped
record has somewhere to put them.

**What this means in practice.** The engine produces **one number: the full-term premium at
the effective date supplied in `SchemeKeys`.** Proration, mid-term endorsement pricing,
written-vs-earned splits and cancellation return arithmetic are **entirely the calling
system's job.** Re-rating at a new effective date and differencing the results is the only
transaction mechanism ISO's content offers, and even that is the caller's construction.

> **One name that looks like an exception and is not.** `EndorsementPremium` *is* live — one
> write, two reads. But it sits on `GeneralLiabilityTerrorismEndorsementCoverage`, and
> `SetEndorsementPremium` sums the terrorism contributions of ~40 endorsement coverages.
> It means *"premium for the terrorism endorsement"*, not *"premium change from an
> endorsement transaction"*. Same word, unrelated concept — the same shared-name trap this
> project keeps hitting.

**Also worth knowing:** `ErcCalculatedTotalPremium` is written 200 times across the corpus and
**read zero times**. The roll-up passes values through `RunRule` return values, never by
reading the stored subtotal. Each level's stored total is an *output for the caller*, not an
input to the level above — so a caller may treat every subtotal as reportable without
worrying that something downstream depends on it.

---

## 6. Reading this for a specific premium

To trace any number on a GL result:

1. **Find the group in `RollUpTree`.** Its `Path to account total` column is the full chain
   of summations between that record and the account figure.
2. **If it is a leaf**, its `Premium` came from `SetPremium` — look it up in
   `PremiumSources` for the exact fields that rule reads.
3. **If it is an aggregator**, its `ErcCalculatedTotalPremium` is the sum of its children
   plus, where marked, its own `Premium`.
4. **If a premium is missing rather than wrong**, check `PremiumIndicator` before checking
   the arithmetic. A zero contribution and an absent coverage are indistinguishable in the
   total; the indicator is the only discriminator.

---

## 7. What the state packages do to this

The countrywide tree is the shape; the 51 state packages change it in two ways and, notably,
**never in a third**.

**They add.** **457 distinct premium-bearing groups exist only in state packages** — state
endorsements, each arriving with its own `CalculateTotalPremium` so it rolls up like any other
child. The heaviest: **WA 33, IL 27, MO 26, NY 25, NC 24, NH 23**; the lightest, WV with 4.
Every one of the 780 state `CalculateTotalPremium` rules is scoped `RuleTypeSystem` — machinery
that comes with the group, not a rewrite of countrywide's.

**They rewrite, but barely, and only in one place.** Exactly **12 `SetPremium` overrides** exist
across all 51 states, and **all 12 are Terrorism**:

| Group | States | CW size | State size |
|---|---|---|---|
| `…TerrorismAllOtherSublineCoverage` | AK, FL, NY, TX, VA, VT | 40,846 | 17,214 – 42,613 |
| `…TerrorismPremOpsCoverage` | FL, NY | 10,549 | 2,725 – 3,339 |
| `…TerrorismProdsCompldOpsCoverage` | FL, NY | 11,144 | 2,742 – 3,635 |
| `…UnmannedAircraftTerrorismCoverage` | FL, NY | 12,667 | 2,861 – 3,470 |

FL and NY replace the terrorism premium calculation with rules a quarter to a fifth the size —
substantially different logic, not a tweak. AK's is slightly *larger* than countrywide's.
**No other countrywide premium formula is rewritten by any state.**

**They never delete.** Zero empty-body premium overrides anywhere in the corpus. This is worth
stating because it is the opposite of CF's validation messages, where 316 countrywide rules are
switched off by a state override with an empty body. **Premium rules are only ever added to or
replaced — never silently removed.**

---

## 8. Limits of this map

- **Countrywide only.** State packages override rules, and a state may override
  `SetPremium` or `CalculateTotalPremium` — none of that is reflected here. The roll-up
  *shape* is unlikely to differ; the premium *formulas* may.
- **Structural, not evaluated.** The tree is read from the rule XML. No premium was
  computed, and no path was exercised against a live rating.
- **`SetPremium` inputs are the fields the rule reads**, flattened from nested conditions.
  A rule reading eight fields may only need two in any given branch.
- **`FinalRate` is where this map stops.** How a rate becomes `FinalRate` is the rating
  chain, which is a separate body of work — this map covers the rate-to-dollars half and the
  aggregation above it.
