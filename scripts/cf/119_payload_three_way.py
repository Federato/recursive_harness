"""Payload generator Step 5 -- Excel vs ISO vs cf_engine, per record per form.

Reads `CFRater1.02.xlsb` **read-only with pyxlsb** (Excel must be closed; no COM),
straight from `IN - Schedule` (user decision 2026-09-22: no Payload Export sheet).
The field mapping is `CF_Payload_Schedule_Map.csv`, applied here in code.

For every state on the Schedule it:
  1. builds ONE ISO payload (ISO carries state in ProductName -- T-3),
  2. rates it on live ISO (`scripts/raas.py`),
  3. rates the same submission through `cf_engine` (the JSON with ERC's `...Table`
     wrappers restored),
  4. reads the rater's own premium for the same records,
and prints one line per record per form -- Building / Contents / BI / Special Class /
SC BI x Basic Group I / II / Broad / Special -- with all three numbers.

**It never invents a rating input** (decision 8): a value the Schedule or `Defaults`
does not hold is omitted and listed, never guessed. Records are matched by position:
the payload lists them in Schedule order and ISO and the engine answer in that order.

    python scripts/cf/119_payload_three_way.py [--state FL] [--no-iso] [--no-engine]

Writes every request, response and the comparison to results/cf-payload/<timestamp>/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

WORKBOOK = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
OUT_ROOT = REPO / "results" / "cf-payload"

SCH = "IN - Schedule"
#: block -> (first data row, header row)
BLOCKS = {"LOC": (5, 4), "BLD": (48, 47), "OCC": (91, 90), "CON": (134, 133),
          "BI": (177, 176), "SC": (220, 219), "SCBI": (263, 262)}
N = 40
BLANKS = {None, "", "Select", "Construction Symbol", "Severity", "BGII Territory", "State",
          "City", "N/A", "n/a"}

REC = {"BLD": "CommercialPropertyStructure", "OCC": "CommercialPropertyOccupClass",
       "CON": "CommercialPropertyPersonalProperty", "BI": "CommercialPropertyBusinessIncome",
       "SC": "CommercialPropertySpecialClass", "SCBI": "CommercialPropertySpecialClassBusnIncome"}
#: the rater's premium rows per coverage (per record column), by form
RATER = {
    "BLD": ("CALC - Bldg Rating", {"BGI": 32, "BGII": 62, "Broad": 86, "Special": 112}),
    "CON": ("CALC - Contents Rating", {"BGI": 30, "BGII": 58, "Broad": 81, "Special": 109}),
    "BI": ("CALC - BI Rating", {"BGI": 25, "BGII": 45, "Broad": 59, "Special": 75}),
    "SC": ("CALC - Special Class", {"BGI": 22, "BGII": 46, "Broad": 65, "Special": 86}),
    "SCBI": ("CALC - Special Class", {"BGI": 105, "BGII": 126, "Broad": 140, "Special": 157}),
}
FORMS = ("BGI", "BGII", "Broad", "Special")
LABEL = {"BLD": "Building", "CON": "Contents", "BI": "Bus. Income", "SC": "Special Class",
         "SCBI": "SC Bus. Income"}
COV = re.compile(r"^(?P<rec>CommercialProperty\w+?)(?:Building|PrsnlProp)?"
                 r"(?P<form>BasicGroupII|BasicGroupI|Broad|Special)Coverage$")
#: AdditionalInsurableIntOption.RateTable.csv (CW): description -> option code, inverted
AII = {"Option1": "General Lessees, Mgrs or Operators of Prem, in Policies Covering Tenants or "
                  "Lessees of Such Prem",
       "Option2": "Employees Other than Executive Officers or Partners in Policies Covering "
                  "Their Employers",
       "Option3": "Other", "Option4": "None"}
FORM_OF = {"BasicGroupI": "BGI", "BasicGroupII": "BGII", "Broad": "Broad", "Special": "Special"}


# ---------------------------------------------------------------------------- reading

def read_workbook():
    if WORKBOOK.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing the live rater.")
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n not in {"", "0"}:
        sys.exit(f"ABORT: {n} Excel process(es) running -- close Excel so the cached "
                 f"values on disk are the ones you see.")
    from pyxlsb import open_workbook
    sheets = {}
    want = [SCH, "IN - Policy", "Defaults", "TBL - Cyber"] + sorted({s for s, _ in RATER.values()})
    with open_workbook(str(WORKBOOK)) as wb:
        for name in want:
            with wb.get_sheet(name) as sh:
                sheets[name] = {(c.r + 1, c.c + 1): c.v for row in sh.rows() for c in row
                                if c.v is not None}
    return sheets


def records(g):
    """{block: [dict(header -> value) for each active record]} in Schedule order."""
    out = {}
    for blk, (r0, hdr) in BLOCKS.items():
        heads = {}
        c = 1
        while (hdr, c) in g:
            heads[c] = g[(hdr, c)]
            c += 1
        active_col = 2 if blk == "LOC" else 3
        rows = []
        for i in range(N):
            r = r0 + i
            if g.get((r, active_col)) != "Yes":
                continue
            rec = {h: g.get((r, c)) for c, h in heads.items()}
            rec["_col"] = 3 + i                           # its column on the calc sheets
            rows.append(rec)
        out[blk] = rows
    return out


def defaults(g):
    d, r = {}, 2
    while (r, 1) in g:
        d[g[(r, 1)]] = g.get((r, 2))
        r += 1
    need = ["LossCostMultiplier", "IncludedInBlkt", "EffectiveDate", "BlktRated", "MUBlktRated"]
    missing = [k for k in need if d.get(k) in (None, "")]
    if missing:
        sys.exit(f"ABORT: Defaults sheet is missing {missing} -- not inventing them.")
    return d


# ---------------------------------------------------------------------------- building

def pct(v):
    return f"{round(float(v) * 100)}%" if isinstance(v, (int, float)) else v


def txt(v, width=None):
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v)
    return s.zfill(width) if width and s.isdigit() else s


class Builder:
    def __init__(self, recs, policy, dflt, scc=None):
        self.r, self.pol, self.d = recs, policy, dflt
        self.scc = scc or {}                                  # CALC - Special Class values
        self.omitted: list[str] = []

    def put(self, obj, field, value, why=""):
        if value in BLANKS:
            self.omitted.append(f"{field}{' (' + why + ')' if why else ''}")
            return
        obj[field] = value

    def state_of(self, b):
        """The state of a building record (via its parent location)."""
        return next((l["State"] for l in self.r["LOC"] if l["ID"] == b.get("ParentID")), None)

    def kids(self, blk, parent_id):
        return [x for x in self.r[blk] if x.get("ParentID") == parent_id]

    def payloads(self):
        self.loc_perded = {l["ID"]: l.get("PerLocationDed") for l in self.r["LOC"]}
        states = {}
        for loc in self.r["LOC"]:
            states.setdefault(loc["State"], []).append(loc)
        out = {}
        for state, locs in states.items():
            self.order = []                               # (blk, record) in emission order
            body = self.policy(state, [self.location(l) for l in locs])
            out[state] = (body, list(self.order))
        return out

    def policy(self, state, locations):
        eff = dt.date.fromisoformat(str(self.d["EffectiveDate"]))
        cp = {"State": state,
              "IRPMFactor": float(self.pol.get((22, 3)) or self.d.get("IRPMFactor") or 1.0),
              "PolicyType": self.pol.get((3, 3)),
              "CommercialPropertyLocation": locations}
        if self.pol.get((3, 6)) == "Yes":
            cp["CommercialPropertyCyberIncidentExclusion"] = [{}]
        if self.pol.get((4, 6)) == "Yes":
            cp["CommercialPropertyCyberIncidentExclusionWithEnsuingCausesOfLossExceptions"] = [{
                "CyberLossOrDamageToCoveredPropertyCovLOI": int(self.pol.get((5, 6)) or 0),
                "CyberAggregateLOI": int(self.pol.get((6, 6)) or 0)}]
        return {"header": {"quoteback": "", "authorization": {}},
                "body": {"SchemeKeys": {"ProductName": f"Commercial Property {state}",
                                        "EffectiveDateTime": f"{eff.isoformat()}T00:00:00"},
                         "CommercialProperty": [cp]}}

    def location(self, loc):
        o = {}
        for f, h in (("ProtectClass", "ProtClass"), ("BasicGroupIRatingTerr", "BGITerr"),
                     ("BasicGroupIIRatingTerr", "BGIITerr"), ("SpecialRatingTerr", "SpecialTerr"),
                     ("City", "City"), ("MultipleResidentialPropSpecialCredit", "MultiResCredit")):
            self.put(o, f, txt(loc[h]) if loc.get(h) is not None else None)
        self.put(o, "ZipCode", txt(loc["ZipCode"], 5))
        if loc.get("District") not in (None, "Not Applicable"):
            self.put(o, "District", loc["District"])
        if loc.get("State") == "NY":
            # ISO NY takes the Group I territory from (City, County); the five borough counties
            # rate from the NYC table (D-1b). The rater holds County since 2026-09-23 (Schedule Q).
            if loc.get("County") in BLANKS:
                raise SystemExit(f"ABORT: New York location {loc['ID']} has no County (Schedule col Q)")
            o["County"] = loc["County"]
        if loc.get("State") == "AK":
            # ISO Alaska picks the Group I district table from the ISO RATING AREA
            # (`City` + `BasicGroupIDistrictTerritory` -> RatingTerrGroupICodeAK): District I
            # = 020/040/050/100, else District II. It never reads `District`. Since D-1a
            # (2026-09-23) the rater takes both as inputs (Schedule O / P) and derives its
            # district the same way, so send them as entered -- never invent one.
            area = loc.get("AKRatingArea")
            if area in BLANKS:
                raise SystemExit(f"ABORT: Alaska location {loc['ID']} has no ISO Rating Area (Schedule col O)")
            o["City"] = area
            east = loc.get("AKEastOf141st") if area == "Remainder of State" else "Not Applicable"
            if east not in ("Yes", "No", "Not Applicable"):
                raise SystemExit(f"ABORT: Alaska location {loc['ID']} (Remainder of State) needs "
                                 f"East of 141st Meridian = Yes / No (Schedule col P)")
            o["BasicGroupIDistrictTerritory"] = east
        blds = self.kids("BLD", loc["ID"])
        whd = loc.get("WindHailDed")
        if whd == "Not Applicable" and blds:
            whd = blds[0].get("Deductible")               # the rater's flat-deductible reading
        self.put(o, "WindstormOrHailDeductible", whd)
        if blds:
            o["CommercialPropertyStructure"] = [self.structure(b) for b in blds]
        scs = self.kids("SC", loc["ID"])
        if scs:
            o["CommercialPropertySpecialClass"] = [self.special_class(s) for s in scs]
        return o

    def structure(self, b):
        self.order.append(("BLD", b))
        o = {"RatingType": b["RatingType"], "ClassCode": txt(b["ClassCode"], 4)}
        self.put(o, "ClassificationDescription", b.get("ClassDesc"))
        self.put(o, "ConstructionType", b.get("ConstrType"))
        self.put(o, "CovType", b.get("CovType"))
        self.put(o, "CauseOfLoss", b.get("CauseOfLoss"))
        self.put(o, "Coinsurance", pct(b.get("Coinsurance")))
        o["Limit"] = int(b["Limit"] or 0)
        o["FullBldgValue"] = o["Limit"]                    # D-2
        self.put(o, "Deductible", b.get("Deductible"))
        self.put(o, "TheftDeductible", b.get("TheftDed"))
        whd = b.get("WindHailDed")
        self.put(o, "WindstormOrHailDeductible", b.get("Deductible") if whd == "Not Applicable" else whd)
        self.put(o, "NumStories", txt(b.get("NumStories")) if b.get("NumStories") is not None else None)
        self.put(o, "BCEG", txt(b.get("BCEG")) if b.get("BCEG") is not None else None)
        self.put(o, "ValuationType", b.get("Valuation"))
        self.put(o, "VacantBuilding", b.get("Vacancy"))
        self.put(o, "SprinklerSystem", b.get("SprinklerSystem"))
        self.put(o, "OpenSides", b.get("OpenSides"))
        self.put(o, "BasicGroupIISymbol", b.get("ConstrSymbol"))
        if self.state_of(b) == "NY" and b.get("ConstrSymbol") != "U":
            # NY-only `SetCompletedBldrsRiskBaseRate` runs a Builders Risk lookup unless this is
            # exactly "Not Applicable"; left blank, ISO refused every NY request. NY's domain
            # (BasicGroupIISymbolNYCompleted) allows only "Not Applicable" for any symbol but U.
            o["CompletedBasicGroupIISymbol"] = "Not Applicable"
        # The rater applies a specific rate to Group I only and always rates Group II
        # from the class tables -- ISO's "Class" basis. Step 3's Defaults #10 said
        # "= RatingType", and on a Specific building that made ISO price Group II at 0
        # (FL, 2026-09-22). Reproduce the rater, not the default.
        o["RatingTypeBasicGroupII"] = "Class"
        if b["RatingType"] == "Specific" and b.get("SpecificRate"):
            o["SpecificGroupIRate"] = float(b["SpecificRate"])
        for i, x in enumerate("ABCDE"):
            self.put(o, f"SubStdCondition{x}", b.get(f"SubStd{x}"))
        o.update(LossCostMultiplier=float(self.d["LossCostMultiplier"]),
                 IncludedInBlkt=self.d["IncludedInBlkt"],
                 PackageModFactor=float(self.pol.get((23, 3)) or 1.0),
                 MultiPremiumAndDispersionCreditFactor=float(self.pol.get((24, 3)) or 1.0))
        # Roof surfacing is an endorsement record, not a field. Step 3 marked it "omit v1";
        # the rater applies its ACV factor, so omitting it made ISO ~2-3% higher.
        if b.get("RoofSurfacing") in ("Paragraph A", "Paragraph B", "Paragraph A and B"):
            o["CommercialPropertyLimitationsOnCovForRoofSurfacing"] = [
                {"Applicability": b["RoofSurfacing"]}]
        if b.get("CovType") == "Legal Liability" and b.get("AddlInsurableIntOption") not in BLANKS:
            # ISO keys AdditionalInsurableIntOption on the DESCRIPTION and returns the
            # option code; the rater stores "Option N". Sending "Option1" was refused.
            opt = str(b["AddlInsurableIntOption"]).replace(" ", "")
            if opt not in AII:
                raise SystemExit(f"ABORT: unknown Additional Insurable Interest option {opt!r}")
            o["CommercialPropertyLegalLiabilityCoverageForm"] = [{"AddlInsurableInt": AII[opt]}]
        if self.loc_perded.get(b.get("ParentID")) == "Yes" and b.get("Deductible") not in BLANKS:
            o["CommercialPropertyDeductiblesByLocationBldg"] = [{"Deductible": b["Deductible"]}]
        self.records(o, b, {"WindHailExcl": "CommercialPropertyWindstormOrHailExclusion",
                            "VandalismExcl": "CommercialPropertyVandalismExclusion",
                            "TheftExcl": "CommercialPropertyTheftExclusion",
                            "SprinklerLeakageExcl": "CommercialPropertySprinklerLeakageExclusion"})
        occs = self.kids("OCC", b["ID"])
        if occs:
            o["CommercialPropertyOccupClass"] = [self.occupancy(x, b) for x in occs]
        bis = self.kids("BI", b["ID"])
        if bis:
            o["CommercialPropertyBusinessIncome"] = [
                self.business_income(x, b["CauseOfLoss"], b["RatingType"], b.get("SprinklerLeakageExcl"))
                for x in bis]
        return o

    def occupancy(self, oc, b):
        self.order.append(("OCC", oc))
        o = {"ClassCode": txt(oc["ClassCode"], 4)}
        self.put(o, "OccupCategory", oc.get("OccupCategory"))
        self.put(o, "CovForm", oc.get("CovForm"))
        # ISO's contents side reads the Additional Insurable Interest from its OWN record
        # on the Occupancy Class; without it the factor is 0.0 (Z-1). The rater applies
        # the building's option to its contents (Contents rows 25/53), so carry it here.
        if oc.get("CovForm") == "Legal Liability Coverage Form":
            opt = str(b.get("AddlInsurableIntOption") or "").replace(" ", "")
            if opt not in AII:
                raise SystemExit(f"ABORT: Legal Liability occupancy {oc['ID']} has no "
                                 f"Additional Insurable Interest option ({opt!r})")
            o["CommercialPropertyLegalLiabilityCoverageFormOccupClass"] = [
                {"AddlInsurableInt": AII[opt], "AddlInsurableIntOption": opt}]
        whd = b.get("WindHailDed")
        self.put(o, "WindstormOrHailDeductible", b.get("Deductible") if whd == "Not Applicable" else whd)
        # ISO's contents sprinkler-leakage rate reads the OCCUPANCY's own SprinklerSystem
        # (../../ from PersonalProperty, past the Table wrapper). The rater has no such
        # input and applies the building's (Contents row 10 = Bldg row 11) -- S-4.
        self.put(o, "SprinklerSystem", b.get("SprinklerSystem"))
        pps = self.kids("CON", oc["ID"])
        if pps:
            o["CommercialPropertyPersonalProperty"] = [self.contents(p, b) for p in pps]
        return o

    def contents(self, p, b):
        self.order.append(("CON", p))
        o = {"Limit": int(p["Limit"] or 0)}
        self.put(o, "CovType", p.get("CovType"))
        self.put(o, "Coinsurance", pct(p.get("Coinsurance")))
        self.put(o, "ValuationType", p.get("Valuation"))
        self.put(o, "CauseOfLoss", b.get("CauseOfLoss"))
        self.put(o, "Deductible", b.get("Deductible"))
        if b["RatingType"] == "Specific" and p.get("SpecificRate"):
            o["SpecificGroupIRate"] = float(p["SpecificRate"])   # rater Contents row 3
        o.update(IncludedInBlkt=self.d["IncludedInBlkt"],
                 LossCostMultiplier=float(self.d["LossCostMultiplier"]))
        self.records(o, p, {"WindHailExcl": "CommercialPropertyWindstormOrHailExclusionPrsnlProp",
                            "VandalismExcl": "CommercialPropertyVandalismExclusionPrsnlProp",
                            "TheftExcl": "CommercialPropertyTheftExclusionPrsnlProp"})
        if b.get("SprinklerLeakageExcl") == "Yes":        # one rater input drives both
            o["CommercialPropertySprinklerLeakageExclusionPrsnlProp"] = [{}]
        return o

    def business_income(self, x, col, rating_type=None, sprinkler_excl=None):
        self.order.append(("BI", x))
        o = {"Limit": int(x["Limit"] or 0)}
        if rating_type == "Specific" and x.get("SpecificRate"):
            o["SpecificGroupIRate"] = float(x["SpecificRate"])   # rater BI row 3
        for f, h in (("CovType", "CovType"), ("TypeOfRisk", "TypeOfRisk"),
                     ("MaxPeriod", "MaxPeriodIndemnity"),
                     ("MonthlyLimitOfIndemnity", "MonthlyLimitIndemnity"),
                     ("ExtraExpenseLimitOnLossPayment", "ExtraExpenseSchedule")):
            self.put(o, f, x.get(h))
        self.put(o, "Coinsurance", pct(x.get("Coinsurance")))
        self.put(o, "CauseOfLoss", col)
        o.update(IncludedInBlkt=self.d["IncludedInBlkt"],
                 LossCostMultiplier=float(self.d["LossCostMultiplier"]))
        self.records(o, x, {"WindHailExcl": "CommercialPropertyWindstormOrHailExclusionBusnIncome",
                            "VandalismExcl": "CommercialPropertyVandalismExclusionBusnIncome",
                            "TheftExcl": "CommercialPropertyTheftExclusionBusnIncome"})
        if sprinkler_excl == "Yes":                       # rater BI row 11 = the building's (S-4)
            o["CommercialPropertySprinklerLeakageExclusionBusnIncome"] = [{}]
        return o

    def special_class(self, s):
        self.order.append(("SC", s))
        o = {"CovType": "Bldg", "Limit": int(s["BuildingLimit"] or 0)}
        # ISO's Special Class ClassCode is an INPUT (no rule sets it); its vandalism rule
        # gates on it. The rater derives it from the description (Special Class row 173).
        cc = self.scc.get((173, s["_col"]))
        if cc not in BLANKS:
            o["ClassCode"] = txt(cc, 4)
        if s.get("DedByLocation") == "Yes" and s.get("Deductible") not in BLANKS:
            o["CommercialPropertyDeductiblesByLocationSpecialClass"] = [{"Deductible": s["Deductible"]}]
        o["FullSpecialClassValue"] = o["Limit"]            # D-2
        for f, h in (("ClassDescription", "ItemDesc"), ("CauseOfLoss", "CauseOfLoss"),
                     ("ValuationType", "ValuationType"), ("AgreedValueOption", "AgreedValue"),
                     ("IncludedInBuilding", "LimitInclInBuilding"), ("Deductible", "Deductible"),
                     ("TheftDeductible", "TheftDed"), ("BasicGroupIISymbol", "ConstrSymbol"),
                     ("BasicGroupIIRatingTerr", "BGIITerr")):
            self.put(o, f, s.get(h))
        whd = s.get("WindHailDed")
        self.put(o, "WindstormOrHailDeductible", s.get("Deductible") if whd == "Not Applicable" else whd)
        self.put(o, "Coinsurance", pct(s.get("BuildingCoins")))
        o.update(IncludedInBlkt=s.get("InclInBlanket") or self.d["IncludedInBlkt"],
                 LossCostMultiplier=float(self.d["LossCostMultiplier"]),
                 PackageModFactor=float(self.pol.get((23, 3)) or 1.0),
                 MultiPremiumAndDispersionCreditFactor=float(self.pol.get((24, 3)) or 1.0))
        self.records(o, s, {"WindHailExcl": "CommercialPropertyWindstormOrHailExclusionSpecialClass",
                            "VandalismExcl": "CommercialPropertyVandalismExclusionSpecialClass",
                            "TheftExcl": "CommercialPropertyTheftExclusionSpecialClass"})
        bis = self.kids("SCBI", s["ID"])
        if bis:
            o["CommercialPropertySpecialClassBusnIncome"] = [self.sc_business_income(x, s["CauseOfLoss"]) for x in bis]
        return o

    def sc_business_income(self, x, col):
        self.order.append(("SCBI", x))
        o = {"Limit": int(x["Limit"] or 0)}
        for f, h in (("CovType", "CovType"), ("TypeOfRisk", "TypeOfRisk"),
                     ("MaxPeriod", "MaxPeriodIndemnity"),
                     ("MonthlyLimitOfIndemnity", "MonthlyLimitIndemnity"),
                     ("ExtraExpenseLimitOnLossPayment", "ExtraExpenseSchedule")):
            self.put(o, f, x.get(h))
        self.put(o, "Coinsurance", pct(x.get("Coinsurance")))
        self.put(o, "CauseOfLoss", col)
        o.update(IncludedInBlkt=self.d["IncludedInBlkt"],
                 LossCostMultiplier=float(self.d["LossCostMultiplier"]))
        self.records(o, x, {"WindHailExcl": "CommercialPropertyWindstormOrHailExclusionSpclClassBusnIncome",
                            "VandalismExcl": "CommercialPropertyVandalismExclusionSpclClassBusnIncome",
                            "TheftExcl": "CommercialPropertyTheftExclusionSpclClassBusnIncome"})
        return o

    @staticmethod
    def records(o, src, names):
        for col, rec in names.items():
            if src.get(col) == "Yes":
                o[rec] = [{}]


# ---------------------------------------------------------------------------- rating

def iso_premiums(resp_body, order):
    """Per record (in `order`), {form: premium} from ISO's JSON response."""
    found = []

    def walk(node, rec_name):
        if isinstance(node, dict):
            forms = {}
            for k, v in node.items():
                m = COV.match(k)
                if m and m.group("rec") == rec_name and isinstance(v, dict) and "Premium" in v:
                    forms[FORM_OF[m.group("form")]] = float(v["Premium"] or 0)
            if rec_name:
                found.append((rec_name, forms))
            for k, v in node.items():
                if isinstance(v, list) and k in REC.values():
                    for item in v:
                        walk(item, k)
                elif isinstance(v, (list, dict)) and k not in REC.values():
                    walk(v, None) if isinstance(v, dict) else [walk(i, None) for i in v]
        elif isinstance(node, list):
            for i in node:
                walk(i, None)

    walk(resp_body, None)
    return align(found, order)


def align(found, order):
    """Match found (rec_name, forms) to the emitted order, record type by record type."""
    queues = {}
    for name, forms in found:
        queues.setdefault(name, []).append(forms)
    out = []
    for blk, rec in order:
        q = queues.get(REC[blk], [])
        out.append(q.pop(0) if q else None)
    return out


def to_tree(obj):
    """ISO JSON -> the engine's submission shape: `X: [..]` becomes `XTable: {X: [..]}`."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, list) and all(isinstance(i, dict) for i in v):
                out[f"{k}Table"] = {k: [to_tree(i) for i in v]}
            else:
                out[k] = to_tree(v)
        return out
    if isinstance(obj, float) and obj.is_integer():
        return str(int(obj)) if obj >= 1000 else str(obj)
    return obj if isinstance(obj, (dict, list)) else (None if obj is None else str(obj))


def engine_premiums(payload, state, order):
    from cf_engine.config import NULL_ARITHMETIC, ROUNDING
    from cf_engine.resolve import book_for
    from gl_engine.interp.interpreter import Interpreter
    from gl_engine.interp.tree import Node
    eff = payload["body"]["SchemeKeys"]["EffectiveDateTime"][:10]
    asof = eff.replace("-", "")
    cp = payload["body"]["CommercialProperty"][0]
    sub = {"EffDate": f"{eff[5:7]}/{eff[8:10]}/{eff[:4]}",
           "CommercialPropertyTable": {"CommercialProperty": [to_tree(cp)]}}
    book = book_for(state, asof)
    ip = Interpreter(book, rounding=ROUNDING, trace=False, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{state}", sub)
    ip.run(data)
    found = []

    def walk(node):
        name = node.tag
        if name in REC.values():
            forms = {}
            for tbl in node.children:
                for cov in (tbl.children if tbl.tag.endswith("Table") else [tbl]):
                    m = COV.match(cov.tag)
                    if m and m.group("rec") == name:
                        p = cov.first("Premium")
                        if p is not None and p.text not in (None, ""):
                            forms[FORM_OF[m.group("form")]] = float(p.text)
            found.append((name, forms))
        for c in node.children:
            walk(c)

    walk(data)
    return align(found, order), len(ip.messages)


def rater_premiums(sheets, order):
    out = []
    for blk, rec in order:
        if blk not in RATER:
            out.append(None)
            continue
        sheet, rows = RATER[blk]
        g = sheets[sheet]
        out.append({f: float(g.get((r, rec["_col"])) or 0) for f, r in rows.items()})
    return out


# ---------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state")
    ap.add_argument("--no-iso", action="store_true")
    ap.add_argument("--no-engine", action="store_true")
    ap.add_argument("--without-cyber", nargs="*", default=[], metavar="STATE",
                    help="also drop the Cyber records for these states. States with no rows in "
                         "'TBL - Cyber' (FL, NY) are dropped automatically: the rater applies none")
    a = ap.parse_args()

    sheets = read_workbook()
    cyber_states = {str(v).split("|")[0] for (r, c), v in sheets["TBL - Cyber"].items()
                    if c == 1 and r > 1}
    recs = records(sheets[SCH])
    b = Builder(recs, sheets["IN - Policy"], defaults(sheets["Defaults"]), sheets["CALC - Special Class"])
    payloads = b.payloads()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = OUT_ROOT / stamp
    out.mkdir(parents=True, exist_ok=True)
    print(f"Schedule: {', '.join(f'{len(v)} {k}' for k, v in recs.items())}")
    print(f"States: {', '.join(payloads)}   ->  {out}")
    if b.omitted:
        from collections import Counter
        print("Omitted (no value on the Schedule, never invented):",
              ", ".join(f"{k} x{n}" for k, n in Counter(b.omitted).items()))

    client = None
    if not a.no_iso:
        import raas as raas_mod
        raas_mod.load_env()
        client = raas_mod.RaaS()

    grand = {"Excel": 0.0, "ISO": 0.0, "Engine": 0.0}
    rows_out = []
    for state, (payload, order) in payloads.items():
        if a.state and state != a.state:
            continue
        # The rater applies no Cyber where ISO files none (`TBL - Cyber` has no rows for the
        # state: FL, NY -- user decision 2026-09-23). Send what the rater priced.
        cp = payload["body"]["CommercialProperty"][0]
        cyber = [k for k in cp if "Cyber" in k]
        if cyber and (state not in cyber_states or state in a.without_cyber):
            for k in cyber:
                del cp[k]
            why = ("the rater applies none here (ISO files no Cyber factor)" if state not in cyber_states
                   else "--without-cyber: Excel still applies Cyber, so expect it ~0.8% LOW-vs-ISO")
            print(f"\n  NOTE {state}: Cyber records dropped -- {why}")
        (out / f"{state}_request.json").write_text(json.dumps(payload, indent=2))
        excel = rater_premiums(sheets, order)
        iso = eng = [None] * len(order)
        iso_note = eng_note = ""
        if client:
            try:
                resp = client.rate(payload)
                (out / f"{state}_response.json").write_text(json.dumps(resp, indent=2))
                iso = iso_premiums(resp.get("Body", resp), order)
            except Exception as e:                        # noqa: BLE001
                iso_note = f"ISO REFUSED: {str(e)[:300]}"
                (out / f"{state}_refusal.txt").write_text(str(e) + "\n" + getattr(e, "body", ""))
        if not a.no_engine:
            try:
                eng, nmsg = engine_premiums(payload, state, order)
                eng_note = f"engine messages: {nmsg}"
            except Exception as e:                        # noqa: BLE001
                eng_note = f"ENGINE RAISED {type(e).__name__}: {str(e)[:200]}"
        print("\n" + "=" * 96)
        print(f"{state}   {iso_note or ''}   {eng_note}")
        print(f"  {'record':<22} {'form':<8} {'Excel':>8} {'ISO':>8} {'Engine':>8}   verdict")
        for (blk, rec), ex, io, en in zip(order, excel, iso, eng):
            if blk not in RATER:
                continue
            for f in FORMS:
                e = (ex or {}).get(f, 0.0)
                i = (io or {}).get(f) if io is not None else None
                n = (en or {}).get(f) if en is not None else None
                if not e and not i and not n:
                    continue
                if i is None:
                    verdict = "no ISO answer"
                elif e == i and (n is None or n == i):
                    verdict = "MATCH"
                else:
                    parts = []
                    if e != i:
                        parts.append(f"Excel {e - i:+g} vs ISO")
                    if n is not None and n != i:
                        parts.append(f"engine {n - i:+g} vs ISO")
                    verdict = "; ".join(parts)
                print(f"  {LABEL[blk] + ' ' + str(rec['ID']):<22} {f:<8} {e:>8g} "
                      f"{'' if i is None else f'{i:g}':>8} {'' if n is None else f'{n:g}':>8}   {verdict}")
                rows_out.append({"state": state, "coverage": LABEL[blk], "record": rec["ID"],
                                 "form": f, "excel": e, "iso": i, "engine": n, "verdict": verdict})
                grand["Excel"] += e
                grand["ISO"] += i or 0
                grand["Engine"] += n or 0
    (out / "comparison.json").write_text(json.dumps(rows_out, indent=2))
    print("\n" + "=" * 96)
    print(f"TOTAL   Excel {grand['Excel']:g}   ISO {grand['ISO']:g}   Engine {grand['Engine']:g}")
    matched = sum(1 for r in rows_out if r["verdict"] == "MATCH")
    print(f"{matched} of {len(rows_out)} record-forms match all three.   Detail: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
