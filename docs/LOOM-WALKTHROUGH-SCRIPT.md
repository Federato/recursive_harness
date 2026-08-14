# Loom walkthrough

Four parts. What it is, why it's an interpreter, the code that matters, how we test and improve it.

**Setup:** `start.bat` run once with the browser tab open · a sample submission and a second from
another state · file explorer at `C:\Projects\ISO_ERC_Files\General_Liability` · editor with
`nodes.py`, `interpreter.py`, `resolver.py`, `tables.py`, `kernel.py` · `PROCESS_LOG.md`.

---

## 1. What it is

**Screen: the app.**

- A General Liability rating engine, written in Python. Input is a submission, output is a premium.
- Rate the sample. Show the premium.
- Show the step-by-step view: every factor that applied, in order, ending in the premium.
- Rate a second state. Same engine, no state-specific code.
- Facts to state:
  - It rates 51 jurisdictions.
  - 50 of those can be compared against ISO's live rating service. All 50 match, on the premium
    and on every published field.
  - Hawaii is not in our ISO delivery, so it isn't rated. Puerto Rico is rated but is not on our
    subscription, so it can't be compared.
  - About one second per rating. Not optimised.
  - The app is a viewer built to inspect engine output. It is not a product.

---

## 2. Why it's an interpreter

**Screen: file explorer, then a rate table opened in Excel.**

- ISO publishes its rating content as a program, not as a document: 20,673 rule files across 567
  packages.
- Two ways to use it:
  - Rewrite ISO's rules in our own code. Each ISO release then requires re-coding.
  - Read and execute ISO's files directly. Each ISO release is a file drop.
- We do the second.
- Show the folders: 89,065 files, under 1 GB. One folder per state, one folder per edition inside
  it. Old editions are retained, which is how backdated ratings resolve to the version in force at
  the time.
- Open a rate table in Excel: ISO's tables are CSVs. They are not copied into a database. The engine
  reads them where they sit.
- Consequences:
  - ISO updates require no code changes.
  - One engine covers all jurisdictions; there is no per-state code.
  - The cost is that every ISO instruction had to be specified before anything could run — 54 of
    them.

**Carriers on older editions** — state this, it comes up:

- Carriers don't all adopt every ERC edition. A carrier may be filed to use one from years ago.
- The engine never assumes the newest edition. It selects the edition in force, and it pairs each
  state package with the countrywide edition that package declares — not the newest one.
- So running a carrier on an older edition is configuration, not an engine change: pin the edition
  per carrier and per state, since a carrier can be current in one state and behind in another.
- Not built yet. The mechanism it needs is already there and already used for backdating.

---

## 3. The code that matters

**Screen: editor. Five files.**

| File | What it does |
|---|---|
| `interp/nodes.py` | ISO's 54 instructions, one function each — `if`, `and`, `or`, `equal`, `choose`, and the rest |
| `interp/interpreter.py` | Executes them. On an instruction it doesn't recognise it stops rather than continuing |
| `resolve/resolver.py` | Decides which ISO package applies for a jurisdiction and date, state layered over countrywide |
| `erc/tables.py` | Reads ISO's tables, typed from ISO's own definition files rather than inferred from the data |
| `rating/kernel.py` | Entry point. Submission in, rating out |

- Total engine: about 5,000 lines.
- No jurisdictional content is in the code. All of it is in ISO's files.

---

## 4. How we test and improve it

**Screen: `PROCESS_LOG.md`, then the backlog.**

- The build ran in six stages. Each stage had acceptance tests that had to pass before the next
  began. Thirteen test suites currently.
- Evidence rules, set before any code was written:
  - ISO's files are the only source of a value.
  - The manuals may confirm what something means. They may not supply anything the files lack.
  - Anything neither settles is escalated to a person.
  - Nothing is invented. If it can't be sourced, the engine returns a referral instead of a number.
- These are enforced in code, not by review: a value that cannot name its ISO source cannot be
  constructed.
- The harness is recursive — rules were added during the build, from the build:
  - When the same class of error recurred, it was written up as a standing rule with every instance
    listed underneath it.
  - 53 analysis steps preceded the engine code. 90 open items are tracked; resolved ones are marked,
    not deleted.
- Current testing method:
  - Every submission is rated by both our engine and ISO's live service, and the results compared
    field by field.
  - Until last week all comparisons used one risk shape. Widening began 2026-08-14: 17 variants
    across 7 groups, 31 of 31 comparable variants matching in Oklahoma and New York.
  - That widening found three defects, including one where our engine accepted a submission ISO
    rejects.
- Planned next:
  - Continue widening the comparison population until it stops finding defects.
  - Carrier deviations, which layer on top of ISO's content the same way a state layers over
    countrywide. Not built.
