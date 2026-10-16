# Our rating graph and Product Studio's compute graph

**16 October 2026.** Plain language; no engineering background assumed. The technical record is
`docs/RATING-GRAPH-PLAN.md` (§3 for our model, §10 for the mapping).

**In short.** Federato's Product Studio and this engine both draw a premium as a graph: the values
that went in, the tables they were looked up in, the steps that combined them and the premium that
came out. Click any value and you see what it was made from. That part is the same. What differs is
which way round each graph is built and what it is held to. Product Studio's graph **is the program**:
built once from the actuary's Excel workbook, then run for every policy, and right when it matches the
workbook. Ours **is a record**: written down while ISO's own rules run for one risk, never run itself,
and right when the premium matches ISO's rating service.

## 1. What each one is

| | Product Studio's compute graph | Our rating graph |
|---|---|---|
| **In one line** | The product's rating logic, held natively in Product Studio | A record of how one rating was worked out |
| **Made from** | The actuary's Excel workbook, uploaded to a draft Product Version | ISO's filed rule programs, as our engine runs them for one risk |
| **When it is made** | Once per product version, at upload | During every rating that asks for it (off unless asked) |
| **What it is for** | Rating every policy, fast, and explaining each premium | Explaining a premium and showing what a carrier's filing changed |
| **Held to** | The workbook's answer (*"it gets Excel's answer"*) | ISO's rating service (technical premium exact in 96 of 96 states) |

## 2. What is the same

| | Both graphs |
|---|---|
| **The picture** | Values as boxes, arrows from what was read to what was computed from it |
| **Inputs** | What the submission supplies: class of business, state, exposure, limits, coverage choices |
| **Table lookups** | The rate or factor found for this risk is its own box, linked to the keys that found it |
| **Arithmetic** | Each step that combines values is a box with its value and how it was worked out |
| **Optional charges** | A charge that applies only when something is selected is tied to that selection |
| **Outputs** | The premiums on the quote are the end of the graph |
| **Explaining a premium** | Trace any premium back, step by step, to the rates and factors behind it |

## 3. What differs

### The pieces, side by side

Product Studio names six kinds of box. Ours has four kinds of box and three kinds of arrow.

| Product Studio | Ours | What is different |
|---|---|---|
| Policy information | `input` box | Nothing: a value the submission supplied and the rating read |
| Rate table | — | We have no box for a whole table. We record only the row that was found |
| Lookup | `table` box, with `lookup` arrows | Our `table` box *is* the row found (which package, table, keys, column and value). `lookup` arrows run from the keys to it and from it to the step that used it |
| Rating step | `write` box | Ours keeps every version: a value written twice is two boxes (`#1`, `#2`), so you see which one a later step used |
| Coverage condition | a `write` box with `control` arrows | Theirs is a kind of box. Ours is a kind of arrow, and any step can have one: it marks a value that *decided whether* the step ran, as opposed to a value that went into its number |
| Premium | `write` box on a premium field | No separate kind: a premium is the last step that wrote that field |
| — | `company` box | Ours only: the carrier filing row a changed value came from (for example a loss cost multiplier). In Product Studio a carrier's rates are simply the workbook's own tables |

### How they behave

| | Product Studio | Ours |
|---|---|---|
| **Direction** | Workbook → graph, ahead of time; the graph then rates | ISO's rules run; the graph is written down as they run |
| **One graph per** | Product version | Rating: a risk with three locations has three copies of the location steps |
| **Does it rate?** | Yes. It is the rating engine, about 100x faster than running the workbook | Never. A rating gives the same answer with it on or off |
| **Arrows** | One kind | Three: `data` (went into the number), `control` (decided whether the step ran), `lookup` (found a table row) |
| **Values written twice** | A cell holds one formula | Kept as versions. ISO's rules do this (California's recomputed fields, the minimum premium check) |
| **Carrier changes** | Belong to the workbook | Shown separately, from the filing row to every value it reached |
| **Size** | Not published | Iowa Property sample: 1,384 boxes and 1,733 arrows; about 5% more rating time when on |
| **Proof it is right** | It matches Excel's results on the sample workbook | It changes no rating; every one of 2,300 plain arithmetic steps re-computes exactly from its arrows; the premium matches ISO |

## 4. Their example, in our terms

Product Studio's documentation rates a simple liability product for a Texas contractor with $4.2M
revenue and a $2M limit, with terrorism selected. Here is what each of its boxes would be in our
graph. These are their figures, not a rating of ours.

| Their box | Value | Ours | Arrows into it |
|---|---|---|---|
| Policy: Business class, State, Annual revenue, Limit, Terrorism | Contractors, Texas, $4.2M, $2M, selected | five `input` boxes | — |
| Rate table: Base rates; Limit factors | — | none (only the rows found are kept) | — |
| Lookup: Base rate | $1.85 per $1K | `table` box: Base rates, keys Contractors + Texas | `lookup` from class and state |
| Rating step: Exposure | 4,200 (revenue ÷ $1K) | `write` box; the ÷ $1K is shown on the step | `data` from revenue |
| Lookup: Limit factor (ILF) | 1.52 | `table` box: Limit factors, key $2M | `lookup` from limit |
| Rating step: Base premium | $11,810 (1.85 × 4,200 × 1.52) | `write` box | `data` from base rate, exposure, ILF |
| Coverage condition: Terrorism charge | $118 (1% of base) | `write` box | `data` from base premium; **`control` from the terrorism selection** |
| Premium: Liability, Terrorism, Total | $11,810, $118, $11,928 | `write` boxes on the premium fields | `data` from the steps above |

The one real difference shows on the terrorism charge. In their picture, the terrorism selection and
the base premium both point at it the same way. In ours, the base premium is a `data` arrow (it went
into the $118) and the selection is a `control` arrow (it decided whether there was a charge at all).
If a carrier had filed its own terrorism rate, a `company` box would point at the step as well.

## 5. What this means for us

| | Decision |
|---|---|
| **Explaining a premium** | Done the same way in both. Our worksheet already does it: click a value, see its ancestry three levels deep, then every table row, input and filing row behind it |
| **Running our graph for speed** | Not doing it (B-33). Their speed gain is over running a spreadsheet. Our engine already rates a full risk in under a second, and re-running only part of a graph can drift from a full rating, because ISO's rules run in order, overwrite values and branch. A graph also holds only the branches one risk took, so it cannot rate a different risk |
| **Showing ours in their shape** | Possible (B-31, needs a go): an export that splits our `table` boxes into Rate table + Lookup, shows `control`-decided steps as Coverage conditions, and premiums as outputs. For demos and explanation only: Product Studio accepts nothing but an Excel upload |
| **Putting ISO GL into Product Studio** | Parked (B-34) until there is a business reason. It would mean workbooks their upload accepts, per state and edition, with our ISO comparison run over them, because a workbook can agree with itself and still disagree with ISO. One state's upload (B-32) would size it first, and answer whether a workbook can hold repeating groups (many locations, many classes) and values written twice |

## Sources

| What | Where |
|---|---|
| Product Studio's compute graph (transcribed 14 October 2026) | `docs/external/federato-compute-graphs_20261014.md`, from docs.federato.dev |
| Our rating graph: model, capture, gates, as built | `docs/RATING-GRAPH-PLAN.md` |
| The tasks named above (B-31 to B-34) | `docs/BACKLOG-2026-10-13.md`, RC-5 and RC-6 |
