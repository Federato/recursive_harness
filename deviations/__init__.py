"""Carrier deviations: the files a writing company's filing lives in.

Phase P1 of `docs/DEVIATIONS-PLAN.md`. A deviation is CONTENT, not code (I1): a
filing is authored in a friendly JSON form, compiled into ISO's own table shape
(RateTable CSV + RateTableDef XML, D12), and the compiled form can be read back
into the rows people wrote (`show`).

Nothing here rates. The engine reads the compiled files in P2; this package
only guarantees that what reaches the engine says exactly what the filing says.

Layout under `CARRIERS_ROOT` (outside the repo and the ZIPs, like the corpus):

    <carrier>/carrier.json                       approval policy, shared class groups
    <carrier>/<company>/company.json             code, NAIC, edition pins, class groups
    <carrier>/<company>/workflow.jsonl           propose / sign-off / reject / withdraw
    <carrier>/<company>/authored/<filing>.v<n>.json
    <carrier>/<company>/compiled/<line>/<juris>/<filing>.v<n>/
        manifest.json
        GroupLCM.Company.RateTable.csv (+Def)     CF: group x rating basis x class (D17)
        LCM.Company.RateTable.csv (+Def)          GL: coverage x class
        Rate Tables/<ISO table>.Company.RateTable.csv + <ISO table>.CompanyDef.RateTableDef.xml

Run it as `python -m deviations <command>`; `python -m deviations -h` lists them.
"""
