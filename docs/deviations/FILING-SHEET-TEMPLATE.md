# Filing sheet: <carrier> <state> <line> — SERFF <tracking number>

*One per filing, written in the session from what you paste or pass (B-20). Kept beside the sources in
`Carriers\<carrier>\sources\<SERFF>\<SERFF>-filing-sheet.md`, listed in `source.json`, shown on the Carrier
Filings screen. It is our reading of the filing; the filed document wins where they disagree (D18).*

## In short

One paragraph anyone can read: who, what line and state, from when, what changes against ISO in percentages, the effect on typical businesses, and whether it is proven. No codes. The Carrier Filings screen shows it first.

**Stage:** Received → Mapped → Draft impact → Built → Proved  ·  **DEV number:** DEV-nnn (assigned when logged)

## The filing

| | |
|---|---|
| Carrier / writing companies | <carrier> · <company (code, NAIC)> … |
| Line / state | <CF or GL> · <state> |
| SERFF | <tracking #> (<filing type>; companions …) |
| Approved / filed | <date> |
| Effective | <new business date> new · <renewal date> renewal (which document says so) |
| ISO basis | <loss cost circular / edition the filing names> |
| What we received | <files, and whether the filed document itself is among them> |

## What was filed

The values the filing changes, exactly as filed, one row each.

| Company | Applies to | Target | Value | Mode | Cite |
|---|---|---|---|---|---|
| | | | | replace / multiply | |

## Where it does not apply

Classes, coverages or premiums the filing excludes, and what rates them instead.

## Other items in the filing

Filed but not rated by us (minimums, schedule rating bounds, expense constants, forms…), and why.

## Mapping

| Filing item | Maps to | Expressible? |
|---|---|---|
| | `LCM:<target>` / `TABLE:<name>.<column>`, scope | Yes / No: gap |

## Decisions needed

| # | Question | Options | Decided |
|---|---|---|---|

## Draft impact

`python -m deviations impact --draft <authored.json>`: technical vs the draft over the projected book (B-18), before
approval. Summary pasted here; full report in `results/impact/`.

## Built and proved

What was authored and compiled, the suite that proves it, and its result.
