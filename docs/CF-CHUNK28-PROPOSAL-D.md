# Property chunk 28, C28-12: proposal for OI-106 (Set D, form names)

**Status: PROPOSED 2026-10-05, awaiting the user's go.** No engine code changed. Form names and numbers only: no
premium or message moves (measured on every stored request ISO rated).

## In plain English

Every state files its own short list of form names (its `Pages` table), and ours uses that list instead of
countrywide's, so most forms come back named "Value Not Found". ISO uses the state's list *and* countrywide's, except
where the state files its own entry for the same coverage record, which then hides countrywide's. The proposal does
the same.

## The rule, as measured

For a `FormPage` table the state files: **the state's rows, then countrywide's rows for every record (`TableName`) the
state does not file a row for**, where a state row whose `Status` is "D" does not count as filing it. Rate and Domain
tables stay as they are (a state rate table with rows replaces countrywide's at ISO, C21-13 T8).

Each part is there because a measurement needed it (`253_`, 1,692 stored requests ISO rated):

| Reading | Form names / numbers equal to ISO (of 90,645 ISO gives) | Not equal |
|---|---|---|
| today (the state's table alone) | 13,455 | 77,190 "Value Not Found" |
| state rows + every countrywide row | 90,627 | 18: VA's CP 14 10, where **ISO itself says "Value Not Found"** (VA files its own "Virginia Changes - Additional Covered Property" row for the record, type "Form"; the lookup asks for type "Coverage", and ISO does not fall through to countrywide's row) |
| + a state row hides countrywide's for its record | 90,639 | 6: NC's CP 14 10, which ISO names from countrywide (NC's own rows for the record have `Status` "D") |
| **+ a "D" row hides nothing (proposed)** | **90,645 of 90,645** | **0**; premiums and messages moved on 0 requests |

## The change (Property only; GL untouched)

`CFResolvedBook.table`, for `kind == "FormPage"` when both the state and its parent file the table: return the state's
rows followed by the parent's rows for records (`TableName`) with no state row of `Status` other than "D", columns
matched by name.

## After the build (C28-13)

`206_ --check` (predicted: only `ErcFormName` / `ErcFormNumber` move, to ISO's values), `157_ --all` 293 of 293, the full
`104_ --gate`, and `253_` re-run with the change built in (every name equal to ISO's, as above).
