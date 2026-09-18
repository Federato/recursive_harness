# Build Log, Plain English — Documenting How Commercial Property Insurance Is Rated

**Started 2026-08-19.**

This is the same diary as `BUILD-LOG.md`, written for someone who doesn't read code or insurance
rating rules. If you want the technical detail — file names, line numbers, formulas — that's the
other file. This one is about *what we're doing and why it matters*.

---

## What is this project?

ISO (a company that writes standard insurance rules used across the industry) publishes a giant,
machine-readable package of files that tell an insurance company's computer system exactly how to
calculate the price of a Commercial Property policy — what building type costs what, what discounts
apply, what happens if you pick a bigger deductible, and so on.

These files are not written for a human to read comfortably. They're rule files, spreadsheet-like
tables, and cross-references, spread across hundreds of documents. Our job is to **read that raw
material and write it up as something a person — or eventually another piece of software — can
actually follow**, step by step, without guessing at anything ISO didn't actually say.

Think of it like this: ISO handed us a very detailed, very technical assembly manual written in
a foreign dialect of engineering-speak. We're translating it into plain, verified English (and a
technical version for engineers), one section at a time.

## Why does this matter?

There's a related, bigger project — `Recursive_Harness_2.0` — that already did this same kind of
work for a different type of insurance (General Liability), and then went further: it built actual
software that calculates a premium the same way ISO does, and proved it agrees with ISO's own
system on every test case run so far (50 out of 50).

The property-line work we're doing here is the first step toward doing the same thing for Property
insurance. Before anyone can build software that rates a property policy correctly, someone has to
first *understand and write down*, accurately, how ISO says the pricing actually works. That's this
project.

## The rule we're following

The single most important rule, carried over from the General Liability project because it caused
real problems there before it was written down: **never guess based on what a file's name sounds
like — go open it and read it.**

For example: if a table is named "SpecialBuildingRate," don't assume it works the way a
similarly-named table for a different coverage works. Open it, read what's actually in it, and
write down what's *actually there* — including when something looks incomplete or missing, which
gets flagged as an open question rather than papered over.

## What's been done so far

**Building coverage** (the core "how much does it cost to insure a building against fire, wind,
theft, and so on" calculation) is documented, in two files:

1. A full walkthrough of how the calculation works, covering all four ways a property owner can
   buy this coverage — a basic package, a slightly better basic package, a broader package, and
   an all-risk "special" package. It explains, step by step, what numbers get multiplied together,
   in what order, and why the four options differ from each other.
2. A checklist of every reference table the calculation needs, confirmed to actually exist in
   ISO's files (not just assumed to exist because a rule mentions it).

## What's next

Two more slices of the same coverage are being documented right now, using the identical method:

- **Personal Property** — insuring the *contents* of a building (furniture, inventory, equipment)
  rather than the building itself.
- **Special Class** — a scheduled/specialized property category with its own rating quirks.

After that, **Business Income** — coverage that replaces the money a business loses if it has to
shut down after a covered loss — is next in line, because it works on a fundamentally different
principle (insuring lost income, not property value) and deserves its own careful write-up.

## Open question so far

One thing came up while documenting Building coverage that's worth a human decision at some point:
one of the rate tables for the "Special" coverage option has no default nationwide value filed —
only a blank template. It's unclear yet whether that's intentional (meaning: every state has to
supply its own number, and there's no fallback) or a gap in the copy of the files we're working
from. It's not blocking anything right now, so it's just being tracked rather than chased down
immediately.

---

## Update — Personal Property and Special Class are done

Both write-ups are finished, and they turned up a few things worth explaining in plain terms.

**Personal Property works differently than Building in one important way:** a building policy rates
one building. A contents policy can rate a *list* of different types of contents at the same
location (say, office equipment and separately, retail stock) — so the calculation runs once per
item on that list, not once per location. Anyone building software off these documents needs to know
that going in, or they'll under-count.

**Special Class** (a category for specific, named types of property — things like stored aircraft or
certain agricultural goods) turned out to be missing a feature that Building and, presumably,
Personal Property have: there's no "limit of insurance" adjustment anywhere in its calculation. We
checked thoroughly rather than assuming that was an oversight in our reading — it's genuinely absent
from ISO's own files for this coverage.

## The most important thing we found today: a mistake in how we checked our own earlier work

When Personal Property's write-up was being done, whoever was working on it needed to look up the
same base-rate table that Building coverage uses (they're shared). When they opened it, **it was
essentially blank** — just a header row, no actual numbers in it, for the nationwide default.

That's a real, useful finding on its own. But it also exposed something more important: **our
original checklist for Building's tables said all the tables were "confirmed present," and that was
true — but "present" only meant the file existed, not that it had a usable number in it.** We'd been
checking that the paperwork existed, not that it was filled out.

That's now fixed — we went back and corrected the original document (with a visible note explaining
what was wrong and why, not a silent edit), and going forward, every table checklist will confirm
there's actually a usable value in the table, not just that the file is there. This is exactly the
kind of mistake the sibling GL project warned about: it's easy to accidentally measure "does this
thing exist" instead of "does this thing actually work," and the two can look identical until someone
checks.

**Practical consequence:** for this particular table, ISO's Countrywide edition doesn't supply a
default number — an individual state has to file its own. That's not necessarily a bug in ISO's
files; it may simply mean the countrywide edition intentionally leaves this to the states. We don't
know yet, so it's logged as an open question rather than assumed either way.

## Questions we can't answer ourselves, queued up for a person

1. Is it expected that some "nationwide default" rate tables are blank, with states expected to fill
   them in? Or is our copy of the files missing something?
2. Same question, now affecting two of the most commonly-used rate tables (the two "Basic" building
   and contents tables) across two different coverages.
3. One factor in Personal Property's calculation is copied in from somewhere else in the file
   structure, and it wasn't fully traced back to its source — needs another look, or a direct answer
   if it's already known.
4. Special Class's "Broad" coverage option appears to always use one specific construction type in
   its rate lookup, regardless of what the building is actually made of. Intentional simplification,
   or does it need fixing?

## What's next

Business Income (the coverage that replaces lost income after a covered loss) is next — it works on
a different principle than everything so far (insuring income, not property), so it gets its own
careful pass rather than being forced into the same template.

---

## Update — now every coverage gets a picture, not just words

A picture was made showing, for each of the twelve calculations documented so far, exactly how the
computer decides what to do: every "if this, then that" step, drawn out as a flowchart you can
click through — organized by coverage type and by pricing option, with color used on purpose (a gold
box means "here's a decision point," a red box means "the price comes out to zero," a green box
means "here's a real price," and a dashed gold-and-rust box means "we found something worth a second
look here").

That turned out to be a genuinely better way to spot problems than reading the technical write-up
alone — several of the open questions logged earlier are now visible sitting right at the exact
branch that caused them, instead of buried in a paragraph.

**Going forward, this is now a standing part of the process.** Every time a new part of the property
coverage gets documented, its decision flowchart gets added to that same picture — the picture grows
one section at a time rather than a new one being made from scratch each time. The written technical
document and the "does the table actually have numbers in it" checklist are still both required; the
picture is now a third required piece, not optional polish.

---

## Update — Business Income is done, and it works on a genuinely different principle

Business Income insurance replaces the money a business loses if it has to shut down after a
covered loss — it's a different kind of coverage from "insure this building" or "insure this
inventory," because what's being priced is lost income, not property value. That difference shows
up everywhere in how ISO's files calculate it.

**The biggest surprise: for two of five pricing options, this coverage doesn't calculate its own
starting price at all — it borrows the building's.** Instead of looking up a rate the way Building
coverage does, it reads the number the Building calculation already worked out, and then applies one
small adjustment on top. Rate the building first; the income coverage rides on its coattails for two
of its five options.

**A second surprise: "how earthquake coverage gets discounted for waiving a requirement" turned out
to be handled completely differently than everywhere else.** Two optional add-ons — one that lets a
business skip a coinsurance requirement, one that extends how long a payout lasts — don't charge
their full price. They only charge the *extra* amount over what was already being paid. That pattern
doesn't show up anywhere in Building or Personal Property coverage — those add-ons always charge
their full number, not just the difference.

**A third finding, consistent with what showed up before:** three more reference tables ISO would
need to actually price two of the five options are blank at the nationwide level — meaning, like the
gaps found earlier in Building and Personal Property, a state would have to supply its own numbers
for those specific options to be priceable at all under this particular file set.

**Earthquake coverage exists as a real calculation here** — the computer works out a price for it
right alongside everything else — but there's oddly no ordinary way to actually charge for it unless
the customer also buys a specific optional add-on ("Agreed Value"). Whether that's intentional (maybe
earthquake time-element coverage is only ever sold that way) or something else entirely wasn't
something the files could answer — logged as a new open question rather than guessed at.

The picture (the visual decision-tree page) now includes Business Income's five pricing paths too,
in the same style as everything before it — same link as before, it just grew five more sections.

---

## Update — a roster of every helper used so far, and two new specialist roles

A new document, `AGENTS.md`, now lists every AI "helper" that has been dispatched to do a piece of
this work — four so far, one per coverage type documented, each working independently in the
background and reporting back what it found. Think of it like a staffing sheet: who worked on what,
what they were told to follow as ground rules, and what they turned up.

Two new roles were also added to the plan, modeled on a pair of specialists that already exist and
work well in the related General Liability project next door: one whose only job is to be the
expert on the raw pricing files (the same files this whole project has been reading), and one whose
only job is to be the expert on ISO's official rulebook documents (the plain-English manual version
of those same rules, as opposed to the computer-readable version).

Honesty check, written directly into both new roles' job descriptions: the pricing-file expert has
plenty to work with — hundreds of files already sitting there. The rulebook expert has almost
nothing yet — six documents, all one broad nationwide version, none of the state-specific versions
collected. That's stated plainly rather than glossed over, because pretending otherwise would be
exactly the kind of unearned confidence this whole project has been trying to avoid.

---

## Update — the fourth coverage variant is done, and we started reading ISO's actual rulebook

**Special Class Business Income** (lost-income coverage for scheduled/specialized property) is now
documented. Short version: it mostly copies the pattern from plain Business Income rather than
inventing its own — but it leans on the coinsured item's own already-finished price even more
heavily than plain Business Income does for two of its five pricing paths, essentially charging
"whatever that item already costs, plus a tiny adjustment," rather than working anything out itself.

**The bigger news this update: we started reading ISO's official written rulebook for property
insurance for the first time**, instead of only the computer-readable pricing files. Six nationwide
rulebook documents were converted into searchable text — about 2,060 pages. State-specific versions
are on their way and will get added to the same reading pile once available.

**Something genuinely exciting happened almost immediately: the two independent sources agreed with
each other, on the very first real check.** Days ago, while reading the computer files, a citation
turned up referencing "bureau rule 71.E" for one part of the calculation — that citation was written
down without ever having read the rulebook itself. Now that the rulebook has actually been opened,
Rule 71 in the official table of contents is titled "Causes Of Loss – Broad Form" — exactly the
section that citation was pointing at. Two completely separate sources, read at two completely
separate times, landing on the same answer. That's the strongest kind of evidence this project can
produce, and it's a good early sign that the computer files and the official rulebook are describing
the same real insurance product consistently.

A few other things lined up by name too — the section covering buildings and their contents, the
section covering lost-income coverage, and the section covering earthquake coverage all match up
with what the computer-file reading already found. Nothing has been formula-checked line by line
yet — that's future work — but the high-level map is looking consistent.

---

## Update — catching up: the last several sessions in plain English

This log fell behind the technical one for a stretch while a lot happened quickly. Catching it up now
in one pass rather than one entry at a time, matching Entries 8 through 18 of the technical log.

**The picture (visual flowchart) now covers a fifth type of coverage.** After the "lost income for a
scheduled/specialized property" coverage was documented, its five pricing paths were added to the same
growing picture as everything else — same style, same link, just more sections.

**A full inventory was built of everything left to document.** Rather than keep documenting one thing
at a time and hoping to remember what's left, a complete sweep was run identifying every distinct
coverage or add-on in the pricing files that computes its own price. The headline: of roughly a
hundred such things, only five were fully documented at that point — the five described earlier in
this log. That's a genuinely useful map, even though it also revealed the sweep itself needed fixing
(see next point).

**A real mistake was found and fixed, not hidden.** When asked specifically about earthquake and flood
coverage, it turned out neither had been caught by the first sweep at all — they use a different
file-naming pattern than everything else, and the search pattern used was too narrow. Re-running with
a broader search found the true total was more than double the first estimate — about 240 distinct
coverages and add-ons, not 100. This was corrected openly in the document, with an explanation of what
went wrong, rather than quietly fixed and left unremarked. The lesson written down for the future:
when a search comes back empty for something you'd expect to find, that's a sign to search more
broadly, not a sign it doesn't exist.

**Then the real work of collecting ISO's official state-by-state rulebooks began, state by state, as
they were provided.** Over several rounds, rulebook documents for every U.S. state plus DC were
converted into searchable text — starting with a handful of states, then growing in bigger batches, up
to a final batch of 27 states added all at once. By the end, **every state except four** (Idaho,
Louisiana, Mississippi, and Washington State — each noted separately as "we don't have this yet,"
not "checked and found nothing") had its rulebook pages converted and given a first-pass read.

**A genuinely exciting confirmation happened early in this process and held up as more states were
added**: state-level rulebooks turned out to be short "exception" documents — usually just a few dozen
pages listing what's different from the national default — rather than full reprints of the whole
manual. That's a real, useful fact about how this insurance product is actually filed, not something
that was assumed going in.

**One state stood out as unusually interesting: Virginia.** Almost every state's rulebook exceptions
modify the more detailed, specific sections of the manual. Virginia's rulebook includes an exception
to Rule 1 — the very first, most basic "here's what this section of the manual covers" rule. That's
unusual enough that it's now the single most interesting thing flagged for a closer read, ahead of
everything else.

**As the volume of documents grew, the tracking method had to change, and that change was made
visible rather than silent.** Tracking every single document individually worked fine for the first
couple dozen rulebooks, but by the time 27 more states landed at once (nearly 400 documents total),
that level of detail stopped being practical to maintain by hand. From that point on, states are
tracked with one summary line each instead of one line per document — a real trade-off, written down
as a trade-off, not quietly downgraded.

A couple of small housekeeping items were also flagged along the way: two states had duplicate copies
of the same document accidentally saved, and one state has a rulebook file named slightly differently
than every other one, for no clear reason yet. Neither was fixed — just written down so nobody wastes
time rediscovering them.

---

**Then work shifted from documentation toward actually building a rating tool.** For the "Basic
Group I" building coverage — one of the four ways a commercial building's fire/lightning-type
coverage can be rated — the request was to pull together the reference lists an Excel rating sheet
would need as dropdowns: a list of every building class code and what it means, a list of the six
construction types (frame, masonry, etc.), and the actual base rates for every class code and
construction type combination, for every state.

**Pulling the class code list surfaced a real wrinkle worth knowing about:** a single class code
often covers several different, unrelated types of business. Code `0570`, for example, covers 33
different occupancies — hatcheries, florists, pet stores, paint stores — all rated exactly the same
way. So "pick a class code, get one description back" doesn't quite work as a simple lookup; "pick a
description, get one class code back" does, cleanly, since every description only belongs to one
code. That distinction was written down rather than papered over, since it changes how the dropdown
should actually be built.

**A second wrinkle: which of two rating methods applies to a given class code** — "Class rated" (rate
comes straight from a table) or "Specific rated" (rate is calculated from the building's actual
characteristics). Some codes only support one or the other; some support both. The rule for which one
to default to when both are available was set, then reversed once mid-build after further
direction — it now defaults to Class rating whenever a code is eligible for it, rather than defaulting
to Specific.

**The most significant finding of this pass: California doesn't use the same rate table as every
other state.** While pulling the actual base rates state-by-state, California turned out to have no
rate table at all under the name every other state uses. It turns out California splits Basic Group I
building rating into two entirely separate rate tables, and which one applies depends on a
California-only question the agent has to answer when entering a property — "District I" or
"District II" — a distinction the other states don't have at all. This has been written down as a
standing thing to watch for while building out the rating engine, in both the technical documentation
and the decision-chain diagram page, so it doesn't get silently missed later when California support
gets built.

**A quick follow-up check confirmed Alaska has the exact same two-table situation as California** —
same split into two rate tables, same underlying rule structure. The one real difference: California
has the agent directly choose "District I" or "District II" when entering the property. Alaska
figures it out automatically from the city the property is in (with one extra wrinkle for a
catch-all "Remainder of State" option). So the end result for the rating engine is the same either
way — two rate tables instead of one — but how that gets decided differs by state, which matters for
how the input form gets built later.

**Two follow-on corrections tightened up which states actually had usable data.** First, the "current
edition" rule for each state was formalized to mean "the latest filing that isn't dated after
September 1, 2026" rather than just "whatever's newest today" — a small change that turned out not to
move any state's answer this time, but pins the rule down for next time it might. Second, and more
significantly, every earlier state count turned out to be undercounted because the search had only
ever looked in one filing snapshot out of eight the source data actually has — states file updates on
their own schedule, not all at once, so a state's most current rulebook can be sitting in an older
snapshot folder while the newest folder has nothing for it at all. Re-searching all eight snapshots
found four states that had wrongly looked like they had no current filing at all, and five more states
that hadn't shown up anywhere in the single-snapshot search. Net result: 46 of the 51 states (plus
DC) now have at least one usable filing found in this data, with only Hawaii, Idaho, Louisiana,
Mississippi, and Washington State still needing to be tracked down (Puerto Rico set aside on
purpose, see below).

---

**Two more surcharges got the same investigate-then-build treatment: a "sub-standard condition"
charge and a "vacant building" charge.** Both are small add-on charges on top of a building's base
rate, and both got pulled into their own spreadsheet-ready reference tables the same way the Basic
Group I rates were.

**The sub-standard condition charge turned out to have a citation problem.** The data ties this
charge to a specific numbered rule in ISO's official rulebook, but that rule number was checked
against the actual rulebook on hand and doesn't match — the rulebook's real version of that rule
number covers a completely different topic. The citation is being treated as unverified from here on,
not as something safe to hand someone else as proof. A second, more practical trap was also found:
the nationwide "default" version of this rate table has been showing the same number since 2019 and
was never updated, while most individual states have since filed their own lower number. Reading the
nationwide default directly would silently give a wrong, years-out-of-date answer — the state-specific
numbers are the only trustworthy source now. States split three ways: a few states never adopted this
charge at all, a handful adopted it and then explicitly filed it as zero (a deliberate "we don't
charge this" rather than "we don't have an answer"), and the remaining majority have real, matching
numbers.

**A follow-up question — "what do the five sub-standard conditions actually mean?"** — turned out to
be answered, just not in an obvious place. The five conditions are only ever referred to by letter
(A through E) in the technical rate data, with no description anywhere in the obvious spots. The
actual plain-English labels (things like "unsafe wiring" and "building not in good repair") were
found tucked into a form-field reference table, not a rate table or a glossary — easy to miss. A
small lookup table mapping each letter to its label was built from that, so a user can now pick a
condition by name instead of having to already know the letter.

**The vacant-building charge works differently under the hood, and that difference matters.** Rather
than adding up several small charges like the sub-standard-condition one does, this charge is a
straight multiplication: a rate that depends on what the building's *previous or intended* use was
(not its current status) — a state, formerly, or company-provided classification code, times a
separate loss-cost adjustment factor. Because it depends on the *previous or intended* occupancy
specifically, it may need its own separate input field on the rating sheet rather than reusing
whatever field already captures the building's normal occupancy. Coverage here is much more complete
than the sub-standard-condition charge — every state that was checked has real numbers, with no
"never adopted" or "filed as zero" states found.

**Puerto Rico's exclusion had to be tightened up mid-session.** It had already been set aside once as
out of scope, but the instruction at the time still allowed including its numbers "for completeness"
in reference tables — and that's exactly the gap that let Puerto Rico's numbers slip back into both
of the new surcharge tables. After a second, firmer correction, the rule is now a clean exclusion:
Puerto Rico gets left out of new reference tables the same way a state with no filing at all would be,
not documented as an interesting outlier. Both new tables were cleaned up to match.

---

## Catch-up entry — 2026-09-04: seven Basic Group I Building pricing factors turned into reference workbooks

This was a long session working through the pieces that combine to set a Basic Group I building's
final price, one at a time. For each one, the same two-step approach was used: figure out exactly how
it's calculated by reading the raw filed data (not guessing from what seemed reasonable), then build a
standalone Excel workbook someone could actually use to look up the right number by hand. Nothing this
session was wired into the real rating spreadsheet itself — these are all reference workbooks sitting
next to it, waiting for an explicit go-ahead to be connected in.

**Territory** — where a building sits changes its price, and for most states that's a simple pick-a-
territory dropdown. The first attempt tried to build that dropdown out of city and county names, but
that was the wrong foundation — it was rebuilt to pull the options directly from the actual filed
territory list instead, which is more reliable and matches what the real filing offers.

**Three states split their base price table in two** (Alaska, California, New York) — a building in
"District I" gets a different starting price than one in "District II," and which one applies depends
on where exactly the building is. For Alaska specifically, there's no fine-grained ZIP-code map filed
anywhere — so a rough one was built by hand from the legal district boundary description in the
manual, and it's clearly labeled as a best-effort construction, not something ISO actually filed and
stands behind.

**Protection Class** — almost every state uses the same 28-code fire-protection scale, except North
Carolina, which files its own, different 12-code scale. That only came to light after specifically
asking whether the numbers were consistent everywhere — worth remembering that "looks universal" isn't
the same as "confirmed universal."

**Roof surfacing and sprinkler-leakage credits** — both got a close read of the actual rulebook
language. The sprinkler one included a real course-correction: a first explanation compared its
discount to a different, unrelated discount that gets baked into the price much earlier in the
calculation, but a closer look (prompted by a good "that doesn't feel right" pushback) showed the
sprinkler credit actually gets subtracted much later, after several other multipliers have already
applied — a materially different mechanism than the first explanation suggested.

**Coinsurance** — a four-way branching rule (there are situations where it doesn't apply at all,
standard percentage tiers, a shared calculation for policies covering multiple locations together, and
a flat penalty for skimping below 80% coverage). Florida turned out to have filed a price for a 70%
coinsurance option that the actual calculation logic can never reach — real filed data that's simply
dead on arrival, the same kind of "filed but unusable" quirk found once before with a roof-surfacing
override.

**Limit of Insurance factor — the session's biggest correction.** This factor blends smoothly between
filed price points rather than jumping in steps, and the manual describes the math for doing that blend
by hand. The first read of the underlying calculation logic concluded the blending was something a
human has to do manually, and the machine-readable filing itself doesn't do it. That turned out to be
wrong — a closer look at how the actual price table is structured showed the blending instruction is
built directly into the table itself, so the automated system already does this correctly on its own.
Good reminder that "the calculation logic doesn't mention it" isn't the same as "it doesn't happen" —
sometimes the behavior lives in how a table is defined, not in the rule that reads it.

**Deductible-by-location** — a flat, small discount (0.995) for policies that schedule different
deductibles at different locations, confirmed to stack multiplicatively on top of the regular
deductible discount, not replace it.

**Deductible amount** — the one that turned out to vary the most by state. Most factors reviewed this
session default to one nationwide table with occasional state exceptions; this one has both a
different *dropdown list* of available deductible amounts and a different underlying price table in
several states — seven genuinely different shapes across 47 states. There was also a real mistake
caught and fixed mid-session: an early pull of California's numbers accidentally used a future filing
that isn't in effect yet, making it look like California offered deductibles up to a million dollars.
Once corrected to use the actual currently-effective filing, California turned out to offer no special
options at all, capped like several other states. This is the same "wrong filing edition" mistake
flagged once before in this project — worth double-checking the effective-dates table any time
California's numbers look unusually generous.

**Next update:** whichever pricing factor gets picked up next in this same walkthrough, once Idaho,
Louisiana, Mississippi, Washington State, or Hawaii's rulebooks arrive, once Virginia's Rule 1 mystery
gets read directly, once California's (and Alaska's) building-rate district situation gets actually
resolved in the rating engine itself, or the next coverage/endorsement documentation pass gets picked
up.

---

## Session: Business Income mapped end-to-end, and a real pricing bug found and fixed in the live rater

**What Business Income is:** a separate coverage — pays the business for lost income and continued
expenses while it can't operate after a covered loss — rated alongside Building and Contents but with
its own rules. This session mapped how all five variants of it actually get priced, then opened the
real, in-use rating spreadsheet (with explicit permission, read-only, always confirmed closed first) to
check whether the documented rules and the actual spreadsheet agreed.

**The five variants, in short:** two of them ("Basic Group I" and "Basic Group II") mostly borrow the
Building's own numbers and add a small adjustment on top. A third ("Broad") turned out to price itself
completely independently — no borrowing at all. A fourth ("Special") turned out to be the most different
of all: even though Building's own version of Special is dead simple (one flat number for the whole
state), Business Income's version is the most detailed calculation in the whole coverage, factoring in
construction type, coverage type, and whether the building is an apartment or condo. The fifth
("Earthquake") exists as a real calculation but was left for a future session — flagged below.

**A shared discount, traced properly for the first time:** Business Income has one shared adjustment
("Factor") that both Basic Group I and Basic Group II use — same number for both, computed once. Earlier
notes said this discount had four possible outcomes depending on the policy. Tracing the actual
calculation logic directly turned up two more outcomes nobody had documented before: a blended discount
for businesses that mix two different types of operations (like manufacturing plus retail), and a
completely separate calculation for schools that doesn't use the main discount table at all. Both were
previously written off as "not supported" — both turned out to be fully priced and just never looked at
closely.

**A process lesson that changes how every future check should work:** early in the session, a table
looked like it was missing prices for 6 states out of 47. Pushed to double check specifically on
Florida, and it turned out Florida's current prices live in an older batch of filings that a newer batch
never replaced — the pricing data comes in about 8 separate "snapshots" over the years, and a state's
current, in-effect prices aren't guaranteed to be in the newest snapshot. The original check only looked
at the newest one. Re-checking every price table built this session against all 8 snapshots (not just
the latest) found real, current prices for 5 of those 6 "missing" states — only one was genuinely
unfiled. Every future price check in this project needs to look across all the snapshots, not just the
newest.

**Opening the real spreadsheet — the main event of the session.** With explicit permission, and only
after confirming the file wasn't open on the user's own screen, the actual live rating spreadsheet got
opened read-only for the first time this project. Two things came out of it:

1. A gap flagged earlier in the session (Basic Group II's windstorm/hail-exclusion pricing branch
   wasn't wired up — the pieces existed but weren't connected) got fixed by the user independently,
   mid-session. A later re-check confirmed the fix works correctly for both Building and Contents.
2. A real, currently-active pricing bug: Business Income has four sub-types, and each one is supposed to
   apply its own "Cyber Incident Exclusion" discount. The spreadsheet had all four sharing one sub-type's
   number instead of computing their own. Checking the actual filed prices confirmed this wasn't just a
   risk for later — one of the four sub-types ("Special") already has a genuinely different discount
   filed than the other three, so its premium has been coming out slightly wrong this whole time, not
   just exposed to a future risk. Reviewed a proposed fix formula, found the logic was backwards (it had
   the "normal case" and "special case" branches swapped), corrected it, and the user applied the fix.

**What's still completely unmapped:** Earthquake pricing (a real, separate calculation that exists but
has a strange quirk — it computes a price but usually has nowhere to charge it, except under one
specific optional coverage); two "surcharge" add-ons that charge only the *extra* cost of an option
rather than the full price again; an entire second, parallel copy of all five Business Income variants
that applies to a different kind of coverage item; a similar parallel set for mining properties; and
roughly three dozen separate optional add-ons (covering things like civil authority shutdowns, utility
service interruptions, and coverage for income lost from a supplier or customer's own property, among
many others) — none of which have been opened yet.

**Next update:** likely Earthquake pricing next, since it's the biggest remaining piece with genuinely
different mechanics — or picking back up the Building rate walkthrough where it left off. Otherwise
unchanged: Idaho, Louisiana, Mississippi, Washington State, and Hawaii's rulebooks are still pending
access.

---

## Session: a full checklist of every pricing path, and a close call handled correctly

**What got built:** a single page listing every pricing path this project knows about — not just "is
Business Income built," but broken down to the level of "is Building's Basic Group I built for the
normal way of pricing it, and separately, is it built for the alternate way." Each one is marked as
actually confirmed built, confirmed missing, or honestly "haven't checked yet" — the last category
covers most of the page on purpose, since claiming something's missing without looking would be worse
than admitting it's unchecked.

**A real gap found along the way:** there's a second way to price several of these coverages — instead
of looking up a price based on class and construction type, an underwriter can enter a specific,
already-agreed-upon rate directly. Checking whether that alternate path exists anywhere in the
spreadsheet turned up nothing — not for Building, not for the contents coverage, not for any form. It's
a real, single, project-wide gap sitting inside otherwise fully-built pricing, not something missing
from just one place.

**The close call:** partway through the check, a technical error came back from a step that should have
been routine. Looking into it (carefully, without touching anything) found that the actual, real
spreadsheet program on the user's computer already had one of this session's own output files open —
completely harmless on its own, but a sign that the automated check could have accidentally interfered
with something the user was actively looking at. Rather than push through or retry, every further check
was switched to a completely different, lower-risk method that never opens the spreadsheet program at
all, just reads the file's raw contents directly. Flagged to the user immediately rather than
quietly working around it.

**Next update:** treat the new checklist page as a living document — pieces marked "haven't checked yet"
should get moved to "confirmed built" or "confirmed missing" over time as they're actually looked at,
not left unchecked forever.

---

## Session: zooming out from Business Income to the whole Property line — and catching two outdated notes along the way

**The ask:** stop looking at just Business Income and list every pricing path across the entire
commercial property line — every coverage, every variant, every way it can be rated (by class, by a
specific pre-agreed rate, blanket across many locations) — using both the official manuals and the raw
filing data as sources.

**The good surprise:** before building anything new, a check turned up that this project already did
this exact exercise, three weeks earlier, for the whole property line — not just Business Income. That
earlier pass swept every single pricing rule file in the entire filing package and found **243 separate
priceable items** across all of commercial property. Rather than build a second, competing list, that
existing document got updated with what's been learned since, in place.

**Two outdated notes caught and fixed while reconciling the two documents against each other:**
1. One document said a certain coverage variant ("Special Class Business Income") had never been looked
   into. Another document, from the same day, turned out to already have a complete, detailed writeup of
   exactly that coverage. The "never looked into" note was just never deleted after the real writeup got
   finished.
2. Yesterday's summary said Earthquake pricing for Business Income was "not looked at" — that's true
   only in the sense that nobody checked whether it's built in the actual spreadsheet. The pricing logic
   itself was already fully documented, and had actually been read closely earlier in the same session
   that made the claim. A subtle but real difference between "we haven't priced this out on paper" and
   "we haven't checked if the spreadsheet does it."

**What got built:** one page with two parts. The top part is the detailed checklist exactly as asked
for — one row per coverage per pricing form (22 rows total), checked against four different ways each
one can be priced. It confirmed something clean: the "specific pre-agreed rate" pricing option only ever
applies to one particular form within each coverage, not all of them — every other form correctly shows
"doesn't apply" rather than "missing." The bottom part zooms back out to the full 243-item picture:
5 fully documented, roughly 92 identified but not yet written up, another ~22 Earthquake/Flood-related
filings, and — the biggest number on the page — **about 146 priced items that exist in the filings but
haven't even been individually named yet.**

**Next update:** naming those ~146 unidentified items is now the single largest piece of unfinished
work anywhere in this project, bigger than anything found in Business Income specifically. Also worth
doing: go back and delete the outdated "not looked into" note now that it's been caught.

---

## Session: finally naming the ~146 mystery items from three weeks ago

**The ask:** a direct follow-up — "we need to identify those," pointing at the ~146 unnamed pricing
items flagged three weeks earlier as the biggest gap in the whole property-line inventory.

**What got done:** re-ran the same search that found those 146 in the first place, independently, without
looking at how it was done the first time — and landed on almost the exact same number (145), which is a
good sign both counts are measuring something real rather than an artifact of one particular way of
counting. Two of those turned out to be counting mistakes (accidentally counting one already-known item
twice under a stripped-down name), leaving 143 genuinely new, previously-unnamed items. Grouped them
into 14 themed clusters the same way the rest of the document is organized, and added them in as a new
section.

**What's in the 143, roughly:** the two biggest newly-named clusters are a "cost increase for green
building upgrades" endorsement that apparently gets filed separately for every single combination of
coverage type and cause-of-loss form (21 separate filings for what's conceptually one option), and a
tenant's scheduled building-property coverage split between glass and everything-else (20 filings). Both
are now bigger, by raw filing count, than the largest cluster found three weeks ago. Also in there:
several cannabis-related exclusions, food contamination coverage, radioactive contamination, a coverage
for property temporarily away from the premises, and a batch of smaller one-off items.

**What this doesn't do:** none of these 143 have actually been opened and read yet — this only answers
"what is it called," not "how does it price." That's explicitly the next step, not done here.

**Next update:** pick one of the two largest newly-named clusters and actually trace it, the same level
of depth given to the previously-known largest cluster (Ordinance or Law). The three-week-old "what's
still unidentified" gap is now closed as a naming exercise.

---

## Session: bundling all 161 items into clickable categories

**The ask:** a direct follow-up — "can we create some sort of architecture, which bundles these into
larger categories? Like Earthquake for example is the coverage, and be able to filter within that."
Same underlying data as the full grid built earlier the same day, just organized so someone can click
"Earthquake" and see only the Earthquake-related items instead of scrolling through all 161.

**What got done:** sorted all 161 endorsement items into 19 named groups (Earthquake, Flood, Business
Income time-element stuff, Ordinance or Law, Builders Risk, Cannabis, and so on) by matching patterns in
each item's name — anything that didn't match a pattern fell into a 20th "Miscellaneous" catch-all.
Built a new page with clickable filter buttons across the top, one per category with a count next to it
(e.g. "Business Income Time-Element & Dependent Properties (38)"), so clicking one narrows the table to
just that group. Business Income time-element items are the biggest bucket by far (38); Earthquake is 8.

**What this doesn't do:** the grouping is done by matching text patterns in the filenames, not by
someone actually reading each item and deciding where it belongs — so a few items are probably
mis-bucketed or arguably belong in two categories at once. Same "close enough for now, not verified one
by one" caveat that already applies to the underlying inventory itself.

**Next update:** same as last time — pick one category or cluster and actually trace it. This page is a
map for choosing where to start, not a replacement for reading the actual rule files.

## Session: Special Class traced start to finish, and three real state-filing surprises

**The ask:** figure out what Special Class actually is and how it rates, then help design its input page,
then help wire it into the live rater — a full day moving from "what is this coverage" to real formulas
against real cells.

**What got traced:** read Special Class's own rule file for the first time. Confirmed it has no
"Specific/Tentative" rating option at all (the earlier notes had this as "probably not, but not checked" —
now it's checked and confirmed absent). For its wind/hail coverage (Basic Group II), confirmed the base
rate comes from the exact same table Building already uses — so anything already fixed for Building's
base rate is automatically fixed for Special Class too. But the "how risky is this class of item" factor
is genuinely different — Special Class looks that up by the item's own name, not by construction type the
way Building does. Wrote up all of this as three how-it-works pages.

**What got mocked up, then discovered already built:** sketched out what an input page for Special Class
items could look like — including a "Location - Item" style ID scheme so multiple scheduled items at the
same location don't get confused with each other. Partway through, found the user had already built a
real version of this directly in the live rater, landing on almost the identical ID scheme independently.
From there the work shifted from mockups to reviewing the real, live tabs and suggesting actual formulas.

**Two real bugs caught along the way:**
- Every cell reference given early in this stretch was off by one, row and then column — the tool used to
  read the spreadsheet counts starting from zero, not one, and that wasn't accounted for until the user
  caught it by checking against the actual file twice.
- A live formula was silently returning 0 because a deductible amount was stored as text with a comma
  ("2,500") while the lookup table stored it as a plain number — they never matched. Small fix, but the
  kind of bug that just quietly gives a wrong answer instead of erroring.

**Three real state-filing surprises, and one process mistake worth remembering:**
- New York genuinely files different Special Class base rates than the countrywide default — not a
  rounding difference, some values are 4x off in either direction. The countrywide-only spreadsheet built
  earlier this session got a New York tab added.
- The windstorm/hail base rate table turns out to only ever be filed at the state level, never
  countrywide, going back to 2019 — every state has real data, only the countrywide file is (correctly)
  empty. Rebuilt that spreadsheet with real data from every state instead of showing empty tables.
- Florida is missing from the current data pull entirely (its last update is over a year old), and even
  that older version rates windstorm/hail completely differently — split by residential vs. non-residential
  occupancy, a mechanism no other state uses.
- **The mistake:** some of this had already been figured out and saved in an existing spreadsheet before
  today's session even started, and it got re-investigated from scratch instead of checked first. Real
  time wasted, called out directly, and worth remembering going forward: check what's already been built
  and saved before redoing the research.

**Next update:** figure out where a couple of the newer Special Class factors actually come from (one open
question never got resolved), and check whether the "how risky is this item" factor deviates by state the
same way the base rate does — that check hasn't been done yet.

## Session: Business Income finished for Special Class, and the Legal Liability path finally explained

**What got done.** The Special Class Business Income coverage is now traced all the way through — Basic
Group II, Broad and Special, on top of the Basic Group I work from last time. Three new explainer pages,
nine new data spreadsheets, and a new running list of shortcuts we have knowingly taken.

**The one that would have cost money.** Broad's base rate looks like it should be the same number for the
building and for business income — same table, same lookup. It is not. The building gets 0.015 and business
income gets either 0.011 or 0.023 depending on the coverage type. Pointing one at the other would have been
about a third too high on one and a third too low on the other, and it would have tested fine, because the
two agree on plenty of other risks.

**A whole category of trap, named.** Several places in ISO's files use the *same rule name and the same
field name* for two genuinely different things. Special's base rate and theft discount are different tables
on the building side versus the business income side, despite looking identical from the names alone. There
is now a page that goes value by value and says plainly: copy this one, share the table but not the switch,
or build your own.

**Legal Liability turns out not to be a different rate at all.** It runs exactly the same rate calculation
as any normal building right up to the last moment, and then the premium formula reaches back and grabs the
rate from three steps earlier — throwing away the limit, coinsurance and deductible adjustments completely —
and multiplies in two discounts that exist nowhere else. Buildings get 0.25, contents get 0.50. It also
turns out Legal Liability works differently for buildings than for contents, which is a trap if you build
one from the other.

**Something worth watching.** If a Legal Liability item does not have an "additional insurable interest"
option selected, ISO's rule produces a premium of **zero** — not a normal premium. There is a perfectly good
neutral value sitting in the table that the rule never reaches for. We are reproducing it exactly as filed,
but with a visible warning cell so nobody is surprised by a free policy.

**Two old questions closed.** A field we had been hunting for the source of turns out to have no source —
nothing calculates it, it is simply typed in on the submission. And a risk table we had not checked for
state differences turns out to differ in Florida, not in its numbers but in the *wording* of the descriptions
used to look it up — which would cause silent misses in Florida.

**The mistake.** Early in the session I said some of ISO's filed rates were dead data that no rule could
ever reach, and implied ISO had made a filing error. That was wrong, and I corrected it the same session:
those rates are used by other coverages, just not the one we were looking at. The lesson is specific — before
ever calling filed data unreachable, check every part of the package that reads that table, not just the part
in front of you.

**Next update:** Earthquake. It is the last remaining form, and roughly 29 other files are waiting on it.

**Later the same session — Legal Liability, looked at properly.**

Legal Liability turned out to be bigger and stranger than the first pass suggested. It is not one calculation
in two places; the same discount mechanism is bolted onto **21 different premium formulas** across four
families. We have written up eight of them (buildings and contents, four forms each). The rest sit behind
Earthquake, which is already next in the queue.

The most useful discovery is about how it gets *chosen*. On a building, someone ticks Legal Liability on that
building. On contents, nobody ticks anything on the contents record at all — the choice is made once for the
whole **occupancy class** and every contents item underneath simply inherits it. So you cannot have one
contents item on Legal Liability and the one next to it on ordinary coverage. For the spreadsheet that means
a dropdown per building, but only one dropdown per occupancy class for contents.

Two smaller but real ones. Buildings and contents disagree about a theft discount: if the insured excludes
theft, contents gets the credit and buildings does not, because the building formula reaches for the rate one
line too early. It only shows up on a risk that actually buys the theft exclusion, so it would pass any
ordinary test. And the four "additional insured" options finally have names — the last is literally "None",
which is worth knowing because leaving the field blank instead of choosing "None" drives the premium to zero.
That is a required field, not an optional one, and we had been describing it slightly wrong.

**Next update:** unchanged — Earthquake, which now also unblocks the remaining thirteen Legal Liability
formulas.
