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

**Next update:** once the state-specific rulebook documents arrive, or the next coverage/endorsement
gets picked up.
