# Property chunk 7, tasks C7-10 to C7-14 — the borrowed rate

2026-09-18. Script:
[`scripts/cf/54_chunk7_borrowed.py`](../scripts/cf/54_chunk7_borrowed.py).

---

## C7-10 · Basic Group I is a straight copy of the parent's finished rate

| Change | parent's rate | **BI Group I** | BI Group II | the item itself |
|---|---|---|---|---|
| — | 0.07 | **$39** | $123 | $66 |
| parent class → `Aircraft Stored in the Open` | **0.286** | **$157** | $123 | $267 |
| parent `LossCostMultiplier` → 2.0 | **0.14** | **$77** | $123 | $130 |

**Nothing in the Business Income record changed in either case.** The parent's
rate moved and the premium followed.

### The parent's LCM reaches the child; the parent's deductible does not

Two fields on the same record, one visible downstream and one not — because the
copy happens **after** the loss cost multiplier and **before** the deductible
factor. C7-03 and the ISO run already showed the other half: strip the parent's
deductible and the item prices at **$0** while the child holds at **$39**.

> **Correction note, 2026-10-06** (`CF_Algorithm/cf-bgi-chains.html`, SCBI review #44, #45; probes BI-7,
> BI-8, BI-9). The heading's word "finished" is wrong; the paragraph above has it right. The child copies
> the parent's `BasicGroupIRate`, which is base x LCM — the parent's **third** step, taken before its
> vandalism, policy-form, coinsurance and deductible factors. The parent's final rate is 0.066; the child
> uses 0.07. Re-probed in OH at CW 2023-08 V04 and CW 2026-06: parent coinsurance 100% or deductible 250
> moves the parent ($62, $70) and leaves the child at $39; parent LCM 2.0 takes the child to $77.

---

## C7-12 · Eleven values cross the boundary — and the count was wrong twice

| | said | by |
|---|---|---|
| opening census | **5** | a regex filtered to names containing Rate/Symbol/Terr/Factor |
| golden case | **6** | finding `BasicGroupIINumericValue` by hand |
| unfiltered regex | **11** | asking the question without the guess |

    BasicGroupIRate                  the FINISHED rate  (Basic Group I)
    EQRate                           the FINISHED rate  (Earthquake)
    BasicGroupIINumericValue         the parent's multiplier of 8
    BasicGroupIISymbol               an input, for this group's OWN lookup
    BasicGroupIIRatingTerr           an input, for this group's OWN lookup
    EQTerr                           an input
    EQDeductibleTier                 an input
    LossCostMultiplier               copied when this group's own is null
    ClassCode                        }
    SpecialClassDescConvertedOption  } read, not rated on
    UnitNumber                       }

**And `BasicGroupIBaseRate` is mentioned zero times in the entire ruleset** —
the claim that matters, and the one that was right all along.

> **Correction note, 2026-10-06** (`CF_Algorithm/cf-bgi-chains.html`, SCBI review #44). In the list above,
> `BasicGroupIRate` is the parent's base x LCM, not its "FINISHED" rate (see the note under C7-10). The
> `EQRate` line was not re-checked. `cf-bgii-chains.html` SCBI review #48: `BasicGroupIINumericValue` is 8
> only when the parent has no wind/hail exclusion; with one it is 1.0, and the child falls from $321 to
> $40 in OH (probe BI-14 in the Group II notes).

**The lesson is the count, not the list.** The census asked *"which borrowed
values look like rates, symbols, territories or factors?"* — a guess about
naming dressed as an enumeration. It cost five names, and one of the five it
kept mattering more than the filter knew: `BasicGroupIINumericValue` is why
removing the parent's `ClassDescription` reaches **two** child forms.

**A filtered enumeration is not an enumeration.** Same family as OI-100, one
level in: there the comparison basis was wrong, here the search was.

### One field, inert in one form and five-fold in another

| | Group I | Group II |
|---|---|---|
| baseline | $39 | $123 |
| **the child's own `LossCostMultiplier` = 5.0** | **$39 — unchanged** | **$616** |

Group I's rate step is a pure copy and never multiplies by anything, so its own
loss cost multiplier does nothing at all. Group II's rate step is
`base × LCM × the parent's numeric value` and takes the full 5×.

### And the borrowed *input*, moved

Setting the location's `BasicGroupIIRatingTerr` to `Portland` — a territory
Oregon files for Group I but not for Group II — takes **Group II to $0** and
leaves **Group I at $39**. One form borrows an answer, the other borrows an
input, and only the second one can miss.

> **Correction note, 2026-10-06** (`CF_Algorithm/cf-bgii-chains.html`, SC review #27 and the SC delta;
> probes SC-7, SC-9 in the Group II notes). Out of date for the engine. Since the C28-05 `SingleResult`
> rule, a territory the state does not file is **refused**, not priced at $0 (SC-9: OH, location territory
> "Bogus", no building). Only a **blank** territory on a location with no building still gives a silent
> $0, outcome "rated" (SC-7). "Borrows an answer" for Group I should read "borrows an intermediate rate"
> (note under C7-10).

---

## C7-11 · Earthquake borrows the rate and has nowhere to charge it

| | |
|---|---|
| Plain Earthquake coverage file | **does not exist** |
| Earthquake premium files that do | **2** — `AgreedValEarthquakeCoverageRules`, `ExtendedPeriodOfIndemnityCoverageEarthquakeCoverageRules` |

**A rate chain with nowhere to send its answer, for the second time.** Chunk 5
found exactly this asymmetry on plain Business Income. **Two instances make it a
pattern rather than a quirk:** in both groups Earthquake is a real form with a
real rate and charges only through endorsements.

---

## C7-13 · The parent's failures propagate

| | BI Group I |
|---|---|
| OR | **$39** |
| FL · NY · AZ | **$0** |

Settled inside the sweep and repeated here because it is the chunk's defining
consequence: **three jurisdictions where a perfectly well-formed Business Income
record prices at zero, for three reasons that all belong to a different
coverage** — Florida's frozen vocabulary, New York's deleted converter,
Arizona's rewritten rate step.

---

## C7-14 · The shared `Factor` — read by two forms, ignored by three

| | Factor | **Group I** |
|---|---|---|
| Mercantile and Non-manufacturing | 0.55 | **$39** |
| Manufacturing | 0.71 | **$50** |
| `MaxPeriod = "Yes"` | **1.15** | **$81** |
| `CovType = "Extra Expense Only"` | **1.7** | **$119** |

With max-period elected — a factor of **1.15**, more than double the default —
**Broad holds at $23 and Special at $47.** The `Factor` is computed for every
form and read by two, the same shape chunk 5 proved on plain Business Income.

**Only Florida files its own `BusnIncomeFactor`** (1 of 47).

### The extra-expense branch keys on a field the table column is not named after

The table column is `ExtraExpnLimitOnLossPymts`. **The datadef is
`ExtraExpenseLimitOnLossPayment`.** The first draft of this test supplied the
column name, so the factor came back **0** and the premium with it.

Chunk 4 met this same pair of names. It is now the second time a *column* name
has been mistaken for a *field* name in this project, and both times the symptom
was a silent zero rather than an error.
