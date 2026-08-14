# Why an interpreter

*14 Aug 2026*

From what I understand, there are two choices when it comes to executing on ISO ERC. Most companies
seem to repackage and re-code something similar to Rating As A Service, and updates to ISO ERC
require updates and re-coding.

Claude was suggesting to build an interpreter instead — essentially we store the ERC files, and the
interpreter runs by reading these files. We don't create a database with every ISO table etc., we
read from where the files are stored, Federato interprets it, and that's run every time we rate. I
measured it: about a second per rating, unoptimized. Fine for underwriting, and I still want to flag
the route.

According to Claude, this will enable us to simply drop in ERC updates and not have to re-write the
code for every release. For carrier deviations, they will need to be built similarly as ERC files
(but with some sort of friendly interface) that would act similarly to how state ERC files interact
with CW ERC files (as a layer).

The first set of tests have the rating engine matching ISO in 50 jurisdictions (49 states plus DC).
Two gaps: Hawaii isn't in our ERC delivery at all so we don't rate it yet, and we need bureau sign
off for that. Puerto Rico we do rate, but it's outside our ISO subscription so we can't check it —
I'm following up with ISO directly.
