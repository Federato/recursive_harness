# A3 — Endorsement And Sub-Coverage Catalog

Every endorsement form referenced by the countrywide manual, with the coverage part it
attaches to, the manual paragraph that governs it, and its premium treatment.

**Source:** `GL-MU-2027-RU-001-C.pdf` (CW 2027, 1st Edition 4-27), plus the latest Rules
notice for each of the 51 jurisdictions for the state-mandated lists.

**Extraction:** form numbers matched as `CG NN NN` / `IL NN NN` in reading-order text, then
attributed to the nearest preceding endorsement heading inside the rule section. Roles are
read off the heading, not inferred.

---

## A3.1 Counts

- **328 distinct forms** appear across the coverage rules.
- **447 (coverage part, form) placements** — a form can carry a different role in
  each part it appears in. The catalog key is therefore `(coverage_part, form)`, **not**
  `form`. This is a schema consequence, not a presentation detail.

| Role | Placements |
|---|---|
| `OPTIONAL_RTC` | 179 |
| `ADDITIONAL_OPTIONAL_RTC` | 125 |
| `ADDITIONAL_INSURED` | 53 |
| `REFERENCED` | 45 |
| `COVERAGE_FORM` | 26 |
| `MANDATORY_MULTISTATE` | 18 |
| `CONDITIONAL_MANDATORY_MULTISTATE` | 1 |

| Role | Meaning in the manual |
|---|---|
| `ADDITIONAL_INSURED` | Rule 16 additional insured endorsement, scoped to a coverage part |
| `ADDITIONAL_OPTIONAL_RTC` | Rule 36 additional optional endorsement; refer to company for rating |
| `CONDITIONAL_MANDATORY_MULTISTATE` | Mandatory at coverage-part level; removal/replacement is refer-to-company |
| `COVERAGE_FORM` | Coverage form — selects the coverage part, not an endorsement |
| `MANDATORY_MULTISTATE` | Attached on every policy for the part; loss cost contemplates it |
| `OPTIONAL_RTC` | Optional; manual states "Refer To Company For Rating" |
| `REFERENCED` | Referenced in rule text (cross-reference / do-not-attach-with), role not asserted |

> **Premium consequence.** Of the placements above, the overwhelming majority are
> `OPTIONAL_RTC` / `ADDITIONAL_OPTIONAL_RTC` — the manual names the endorsement, describes
> its effect, and then declines to rate it. The engine cannot price these from this corpus;
> it must model them as *rateable objects with a carrier-supplied factor or flat charge*.
> Only the mandatory families are already inside the loss cost.

---

## A3.2 Catalog by coverage part

### Rule 15 — Deductibles

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 03 00` | Completed Operations Deductible Discount Factors Bodily Injury And Property Damage  F. Endorsement Use Deductible Liability Insurance Endorsement | `REFERENCED` | — |

### Rule 16 — CGL — Additional Insureds

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 20 01` | Primary And Noncontributory Other Insurance Condition Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 02` | Additional Insured Club Members Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 03` | Additional Insured Concessionaires Trading Under Your Name Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 05` | Additional Insured Controlling Interest Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 07` | Additional Insured Engineers, Architects Or Surveyors Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 10` | Additional Insured Owners, Lessees Or Contractors Scheduled Person Or Organization Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 11` | Additional Insured Managers Or Lessors Of Premises Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 12` | Additional Insured State Or Governmental Agency Or Subdivision Or Political Subdivision Permits Or Authorizations Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 13` | Additional Insured State Or Governmental Agency Or Subdivision Or Political Subdivision Permits Or Authorizations Relating To Premises Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 15` | Additional Insured Vendors Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 18` | Additional Insured Mortgagee, Assignee Or Receiver Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 20` | Additional Insured Charitable Institutions Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 22` | Additional Insured Church Or Other Similar House Of Religious Worship Members And Officers Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 23` | Additional Insured Executors, Administrators, Trustees Or Beneficiaries Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 24` | Additional Insured Owners Or Other Interests From Whom Land Has Been Leased Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 25` | Additional Insured Elective Or Appointive Executive Officers Of Public Corporations Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 26` | Additional Insured Designated Person Or Organization Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 27` | Additional Insured Co-owner Of Insured Premises Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 28` | Additional Insured Lessor Of Leased Equipment Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 29` | Additional Insured Grantor Of Franchise Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 30` | Oil Or Gas Operations Nonoperating, Working Interests Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 31` | Additional Insured Engineers, Architects Or Surveyors Endorsement | `ADDITIONAL_INSURED` | B. Owners And Contractors Protective Liability Coverage Pa |
| `CG 20 32` | Additional Insured Engineers, Architects Or Surveyors Not Engaged By The Named Insured Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 33` | Additional Insured Owners, Lessees Or Contractors Automatic Status When Required In A Written Construction Agreement With You Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 34` | Additional Insured Lessor Of Leased Equipment Automatic Status When Required In Lease Agreement With You Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 35` | Additional Insured Grantor Of Licenses Automatic Status When Required By Licensor Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 36` | Additional Insured Grantor Of Licenses Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 37` | Additional Insured Owners, Lessees Or Contractors Completed Operations Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 38` | Additional Insured Owners, Lessees Or Contractors Automatic Status For Other Parties When Required In Written Construction Agreement Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 39` | Insured Owners, Lessees Or Contractors Automatic Status When Required In Written Construction Agreement With You (Completed Operations) Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 40` | Owners, Lessees Or Contractors Automatic Status For Other Parties When Required In Written Construction Agreement (Completed Operations) Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 42` | Additional Insured Automatic Status For Designated Operations Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 43` | Additional Insured Automatic Status When Required In Written Contract Or Agreement Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 20 44` | Additional Insured Vendors Automatic Status When Required In Agreement Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 21 04` | Do not attach this endorsement if Exclusion Products-Completed Operations Hazard Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 21 39` | Do not attach this endorsement if Contractual Liability Limitation Endorsement | `ADDITIONAL_INSURED` | A. Commercial General Liability Coverage Part |
| `CG 29 35` | Additional Insured State Or Governmental Agency Or Subdivision Or Political Subdivision Permits Or Authorizations Endorsement | `ADDITIONAL_INSURED` | B. Owners And Contractors Protective Liability Coverage Pa |
| `CG 34 01` | Additional Insured Owners, Managers Or Lessors Of Premises Liquor Liability Endorsement | `ADDITIONAL_INSURED` | C. Liquor Liability Coverage Part |
| `CG 34 02` | Additional Insured Grantor Of Franchise Liquor Liability Endorsement | `ADDITIONAL_INSURED` | C. Liquor Liability Coverage Part |
| `CG 34 03` | Additional Insured State Or Governmental Agency Or Subdivision Or Political Subdivision Permits Or Authorizations Liquor Liability Endorsement | `ADDITIONAL_INSURED` | C. Liquor Liability Coverage Part |
| `CG 34 04` | Additional Insured Sponsor(s) Liquor Liability Endorsement | `ADDITIONAL_INSURED` | C. Liquor Liability Coverage Part |
| `CG 34 05` | Additional Insured Trusts Endorsement | `ADDITIONAL_INSURED` | D. Products/Completed Operations Liability Coverage Part |
| `CG 34 06` | Additional Insured Volunteer Workers Endorsement | `ADDITIONAL_INSURED` | C. Liquor Liability Coverage Part |
| `CG 34 07` | Additional Insured Volunteer Workers Endorsement | `ADDITIONAL_INSURED` | D. Products/Completed Operations Liability Coverage Part |
| `CG 34 08` | Additional Insured Volunteer Workers Endorsement | `ADDITIONAL_INSURED` | E. Pollution Liability Coverage Part |
| `CG 34 09` | Additional Insured Volunteer Workers Endorsement | `ADDITIONAL_INSURED` | E. Pollution Liability Coverage Part |
| `CG 00 39` | CG 34 08 This endorsement adds volunteer workers as additional insureds with respect to the Pollution Liability Coverage Part Designated Sites ( | `COVERAGE_FORM` | E. Pollution Liability Coverage Part |
| `CG 00 40` | This endorsement adds volunteer workers as additional insureds with respect to the Pollution Liability Limited Coverage Part Designated Sites ( | `COVERAGE_FORM` | E. Pollution Liability Coverage Part |

### Rule 20 — CGL

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 00 01` | Commercial General Liability Coverage Form (Occurrence) | `COVERAGE_FORM` | — |
| `CG 00 02` | Commercial General Liability Coverage Form (Claims-made) | `COVERAGE_FORM` | — |

### Rule 22 — CGL

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `IL 00 17` | Common Policy Conditions | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `IL 00 21` | Nuclear Energy Liability Exclusion Endorsement (Broad Form) | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |

### Rule 36 — CGL — Additional Optional

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 02 24` | B. Termination And Suspension Endorsements Earlier Notice Of Cancellation Provided By Us Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 22` | CG 21 49, CG 21 55, CG 21 65, CG 04 28, CG 04 29, CG 04 30, | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 24` | Coverage For Injury To Leased Workers Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 25` | Electronic Data of Coverage A. Do not attach Endorsement CG 21 85 to the policy if Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 28` | CG 21 49, CG 21 55, CG 21 65, | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 29` | CG 21 49, CG 21 55, CG 21 65, CG 04 28, | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 30` | CG 21 49, CG 21 55, CG 21 65, CG 04 28, CG 04 29, | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 36` | Limited Product Withdrawal Expense Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 37` | Electronic Data of Coverage A. Do not attach Endorsement CG 21 85 to the policy if Endorsement CG 04 25, CG 04 95, | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 71` | Electronic Data of Coverage A. Do not attach Endorsement CG 21 85 to the policy if Endorsement CG 04 25, CG 04 95, CG 04 37 or | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 04 95` | Electronic Data of Coverage A. Do not attach Endorsement CG 21 85 to the policy if Endorsement CG 04 25, | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 00` | Exclusion All Hazards In Connection With Designated Premises Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 01` | When this endorsement is attached to a policy, do not attach Exclusion Athletic Or Sports Participants Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 04` | Exclusion Products-Completed Operations Hazard Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 16` | Exclusion Designated Professional Services Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 31` | Limited Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 32` | Communicable Disease Exclusion Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 33` | Exclusion Designated Products Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 34` | Exclusion Designated Work Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 35` | Exclusion Coverage C Medical Payments Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 36` | Exclusion New Entities Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 37` | Exclusion Employees And Volunteer Workers As Insureds Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 38` | Exclusion Personal And Advertising Injury Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 39` | Contractual Liability Limitation Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 41` | When Endorsement CG 40 10 is attached to the policy, do not attach | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 42` | Exclusion Explosion, Collapse And Underground Property Damage Hazard (Specified Operations) Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 43` | Exclusion Explosion, Collapse And Underground Property Damage Hazard (Specified Operations Excepted) Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 44` | Limitation Of Coverage To Designated Premises, Project Or Operation Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 45` | Exclusion Damage To Premises Rented To You Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 49` | Total Pollution Exclusion Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 50` | Amendment Of Liquor Liability Exclusion Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 51` | Amendment Of Liquor Liability Exclusion Exception For Scheduled Premises Or Activities Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 52` | Exclusion Financial Services Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 53` | Exclusion Designated Ongoing Operations Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 54` | Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 55` | Total Pollution Exclusion With A Hostile Fire Exception Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 65` | Total Pollution Exclusion With A Building Heating, Cooling And Dehumidifying Equipment Exception And A Hostile Fire Exception Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 66` | Exclusion Volunteer Workers As Insureds Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 67` | Fungi Or Bacteria Exclusion Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 85` | Exclusion Electronic Data Deletion Of Bodily Injury Exception Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 86` | Exclusion Exterior Insulation And Finish Systems Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 21 96` | Silica Or Silica-related Dust Exclusion Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 24` | Exclusion Inspection, Appraisal And Survey Companies Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 28` | Limitation Of Coverage Territory For Designated Operations Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 31` | Exclusion Riot, Civil Commotion Or Mob Action Governmental Subdivisions Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 33` | Exclusion Testing Or Consulting Errors And Omissions Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 34` | Exclusion Construction Management Errors And Omissions Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 38` | Use Endorsement CG 21 52 in conjunction with Exclusion Fiduciary Or Representative Liability Of Financial Institutions Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 42` | Exclusion Existence Or Maintenance Of Streets, Roads, Highways Or Bridges Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 48` | Exclusion Insurance And Related Operations Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 51` | Exclusion Law Enforcement Activities Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 62` | Underground Resources And Equipment Coverage Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 64` | Pesticide, Herbicide, Fungicide Or Fertilizer Applicator Limited Pollution Coverage Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 68` | Operation Of Customers Autos On Your Premises Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 74` | Limited Contractual Liability Coverage For Personal And Advertising Injury Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 76` | Professional Liability Exclusion Physical Fitness Services Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 88` | Professional Liability Exclusion Computer, Telecommunication, Electronic Data Or Internet Services Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 92` | Snow Plow Operations Coverage Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 93` | Lawn Care Services Limited Pollution Coverage Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 94` | Exclusion Damage To Work Performed By Subcontractors On Your Behalf Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 95` | Exclusion Damage To Work Performed By Subcontractors On Your Behalf Designated Sites Or Operations Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 22 96` | Limited Exclusion Personal And Advertising Injury Lawyers Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 23 04` | Cannabis Activity Coverage Aggregate Limit Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 23 05` | Cannabis Exclusion With Hemp Exception Subject To Hemp Aggregate Limit Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 23 06` | Cannabis Exclusion With Designated Product Or Work Exception Subject To Cannabis ProductsCompleted Operations Aggregate Limit Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 01` | Non-binding Arbitration Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 02` | Binding Arbitration Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 03` | Waiver Of Charitable Immunity Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 04` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 05` | Financial Institutions Fiduciary Interest Only Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 06` | Liquor Liability Bring Your Own Alcohol Establishments Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 08` | Do not use Endorsement CG 21 50, CG 21 51 or CG 40 09 if Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 10` | Excess Provision Vendors Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 13` | Amendment Of Personal And Advertising Injury Definition Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 14` | Waiver Of Governmental Immunity Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 15` | CG 21 49, CG 21 55, CG 21 65, CG 04 28, CG 04 29, CG 04 30, CG 04 22 or | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 16` | Canoes Or Rowboats Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 17` | Contractual Liability Railroads Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 22` | This endorsement should not be used if any of the Amendment of Coverage Territory Endorsements | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 23` | This endorsement should not be used if any of the Amendment of Coverage Territory Endorsements CG 24 22, | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 24` | This endorsement should not be used if any of the Amendment of Coverage Territory Endorsements CG 24 22, CG 24 23 or | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 25` | Limited Fungi Or Bacteria Coverage Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 26` | Amendment Of Insured Contract Definition Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 27` | Limited Contractual Liability Railroads Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 53` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 54` | CG 21 36 is attached to the policy, do not attach Automatic Insured Status For Newly Acquired Or Formed Limited Liability Companies Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 24 56` | Excess Insurance Provision Order Of Response When You Are An Additional Insured On Other Insurance Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 25 02` | Amendment Of Limits Of Insurance Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 25 03` | Designated Construction Project(s) General Aggregate Limit Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 25 04` | Designated Location(s) General Aggregate Limit Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 25 45` | Designated Project(s) Products-Completed Operations Aggregate Limit Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 25 46` | Designated Location(s) Products-Completed Operations Aggregate Limit Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 01` | Genetically Modified Organism Exclusion Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 02` | Genetically Modified Organism Exclusion For Designated Operations Or Products Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 03` | Exclusion Athletic Or Sports Participants All Contests Or Exhibitions Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 04` | Exclusion Earth Movement Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 05` | Exclusion Earth Movement Completed Operations Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 06` | Earth Movement Exclusion For Designated Operation(s) Or Project(s) Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 07` | Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Limited Exception For Additional Insureds Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 08` | Limited Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Limited Exception For Additional Insureds Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 09` | Amendment Of Liquor Liability Exclusion Limited Exception For Bring Your Own Alcohol Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 10` | Exclusion Cross Suits Liability Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 11` | Exclusion Hired Auto Liability Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 12` | Exclusion All Hazards In Connection With An Electronic Smoking Device, Its Vapor, Component Parts, Equipment And Accessories Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 13` | Exclusion Health Hazards, Electronic Smoking Device Vapor Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 14` | Cannabis Exclusion Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 15` | Cannabis Exclusion With Hemp Exception Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 16` | Cannabis Exclusion With Hemp And Lessors Risk Exceptions Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 25` | Exclusion Designated Cannabis Products Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 26` | Exclusion Cannabis Products Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 27` | Exclusion Exterior Insulation And Finish Systems (EIFS) With Exception For Drainable EIFS Not Installed Over Wood Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 30` | Exclusion Exterior Insulation And Finish Systems With Exception For Designated Operations Or Projects Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 32` | Exclusion Perfluoroalkyl And Polyfluoroalkyl Substances (PFAS) Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 33` | Systems (EIFS) With Exception For Drainable EIFS Subject To Aggregate Limit With Option For Designated Operations Or Projects Limitation Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 40 34` | S) With Exception For Drainable EIFS Not Over Wood Subject To Aggregate Limit With Option For Designated Operations Or Projects Limitation Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 99 09` | H. Miscellaneous Endorsements Premium Audit Noncompliance Charge Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 09 11` | Supplement To Retrospective Premium Endorsement (Final Premium Computation) | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 09 18` | Retrospective Premium Endorsement One Year Plan Multiple Lines | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 09 19` | Retrospective Premium Endorsement Three Year Plan Multiple Lines | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 09 20` | Retrospective Premium Endorsement Long Term Construction Project Multiple Lines | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 09 21` | Retrospective Premium Endorsement Short Form | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 09 22` | Retrospective Premium Endorsement Exclusion Of Aviation Exposures | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 09 23` | Retrospective Premium Endorsement Exclusion Of Retrospective Development Factors | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 09 30` | Retrospective Premium Endorsement One- Or Three- Year Plan Multiple Lines Supplementary Agreements Regarding The Retrospective Rating Of CGL Policies | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `IL 12 01` | Policy Changes Endorsement | `ADDITIONAL_OPTIONAL_RTC` | A. Additional Optional Endorsements |
| `CG 00 01` | Liquor Liability Endorsement CG 24 08 This endorsement deletes the Liquor Liability exclusion in the Commercial General Liability Coverage Form | `COVERAGE_FORM` | A. Additional Optional Endorsements |
| `CG 00 33` | Liquor Liability Coverage Forms | `COVERAGE_FORM` | A. Additional Optional Endorsements |
| `CG 00 34` | Liquor Liability Coverage Forms CG 00 33 or | `COVERAGE_FORM` | A. Additional Optional Endorsements |

### Rule 37 — Unmanned Aircraft (370)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 21 09` | Exclusion Unmanned Aircraft Endorsement | `REFERENCED` | — |
| `CG 21 10` | Exclusion Unmanned Aircraft (Coverage A Only) Endorsement | `REFERENCED` | — |
| `CG 21 11` | Exclusion Unmanned Aircraft (Coverage B Only) Endorsement | `REFERENCED` | — |
| `CG 24 50` | Limited Coverage For Designated Unmanned Aircraft Endorsement | `REFERENCED` | — |
| `CG 24 51` | Limited Coverage For Designated Unmanned Aircraft (Coverage A Only) Endorsement | `REFERENCED` | — |
| `CG 24 52` | Limited Coverage For Designated Unmanned Aircraft (Coverage B Only) Endorsement | `REFERENCED` | — |
| `CG 24 55` | Unmanned Aircraft Endorsement | `REFERENCED` | — |

### Rule 40 — Cyber / Loss Of Electronic Data

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 04 25` | Cyber Incident Liability Coverage Subject To Each Cyber Incident Occurrence And Aggregate Limits Endorsement | `REFERENCED` | — |
| `CG 04 37` | The loss of electronic data provisions in this endorsement are similar to Endorsement | `REFERENCED` | — |
| `CG 04 71` | Loss Of Electronic Data Resulting From Physical Injury To Tangible Property Liability Coverage Deletion Of Bodily Injury Exception Endorsement | `REFERENCED` | — |
| `CG 04 95` | And Loss Of Electronic Data Liability Coverage Subject To Loss Of Electronic Data, Each Cyber Incident Occurrence And Aggregate Limits Endorsement | `REFERENCED` | — |
| `CG 21 85` | When Endorsement CG 04 25, CG 04 95, CG 04 37 or CG 04 71 is attached to the policy, do not attach Endorsement | `REFERENCED` | — |

### Rule 41 — Abuse Or Molestation

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 04 14` | Sexual Abuse Or Sexual Molestation Liability Coverage Endorsement | `REFERENCED` | — |
| `CG 04 15` | Sexual Abuse Or Sexual Molestation Of Any Person Committed By The Insured Liability Coverage Endorsement | `REFERENCED` | — |
| `CG 04 16` | Sexual Abuse Or Sexual Molestation Liability Coverage Endorsement | `REFERENCED` | — |
| `CG 04 17` | Sexual Abuse Or Sexual Molestation Of Any Person Committed By The Insured Liability Coverage Endorsement | `REFERENCED` | — |
| `CG 27 55` | Supplemental Extended Reporting Period Endorsement For Sexual Abuse Or Sexual Molestation Liability Coverage | `REFERENCED` | — |
| `CG 40 28` | Broad Abuse Or Molestation Exclusion Endorsement | `REFERENCED` | — |
| `CG 40 29` | Sexual Abuse Or Sexual Molestation Exclusion Endorsement | `REFERENCED` | — |

### Rule 42 — Electronic Data Liability (325)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 00 65` | Available coverage form: Electronic Data Liability Coverage Form | `COVERAGE_FORM` | — |
| `CG 31 99` | Nuclear Energy Liability Exclusion Endorsement (Broad Form) | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `CG 33 63` | Exclusion Access Or Disclosure Of Confidential Or Personal Material Or Information Endorsement | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `IL 00 17` | Common Policy Conditions | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `CG 24 01` | Non-binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 02` | Binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 04` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 53` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 31 73` | I. Extended Reporting Period Endorsement For Electronic Data Liability Coverage | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 10` | Exclusion Volunteer Workers As Insureds Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 11` | Exclusion Employees And Volunteer Workers As Insureds Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 35` | Automatic Insured Status For Newly Acquired Or Formed Limited Liability Companies Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 39` | Exclusion Cross Suits Liability Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 40` | Amendment Of Coverage Territory Worldwide Coverage Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 41` | Amendment Of Coverage Territory Worldwide Coverage With Specified Exceptions Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 52` | Cannabis Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 53` | Cannabis Exclusion With Hemp Exception Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 99` | Exclusion Cyber Incident Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 99 09` | Premium Audit Noncompliance Charge Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 31 98` | Use Calculation Of Premium Endorsement | `REFERENCED` | — |
| `IL 00 03` | Premium Computation The Calculation Of Premium Endorsement | `REFERENCED` | — |

### Rule 43 — Employee Benefits Liability (325)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 04 35` | EMPLOYEE BENEFITS LIABILITY COVERAGE (Subline Code 325) A. Employee Benefits Liability Coverage Endorsement | `REFERENCED` | — |
| `CG 27 15` | Extended Reporting Period Endorsement For Employee Benefits Liability Coverage | `REFERENCED` | — |

### Rule 44 — Product Withdrawal (365)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 00 66` | Available coverage form: Product Withdrawal Coverage Form | `COVERAGE_FORM` | — |
| `CG 31 99` | Nuclear Energy Liability Exclusion Endorsement (Broad Form) | `MANDATORY_MULTISTATE` | Multistate Endorsements |
| `IL 00 17` | Common Policy Conditions | `MANDATORY_MULTISTATE` | Multistate Endorsements |
| `CG 04 36` | Declarations, refer to company to determine any premium discount associated with such Cut-off Date.  B. Limited Product Withdrawal Expense Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 24 01` | Non-binding Arbitration Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 24 02` | Binding Arbitration Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 31 68` | Exclusion Coverage A Product Withdrawal Expense Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 31 69` | Exclusion Coverage B Product Withdrawal Liability Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 31 70` | Exclusion Product Tampering Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 31 71` | Exclusion Product Replacement, Repair Or Repurchase Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 31 72` | Coverage Extension Coverage A Product Restoration Expense Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 31 74` | Exclusion Of Newly Acquired Organizations As Insureds Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 31 98` | Use Calculation Of Premium Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 34 17` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 34 18` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 34 54` | Cannabis Exclusion Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `CG 34 55` | Cannabis Exclusion With Hemp Exception Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |
| `IL 00 03` | Premium Computation The Calculation Of Premium Endorsement | `OPTIONAL_RTC` | 3. Optional Endorsements Refer To Company For Rating |

### Rule 45 — Liquor Liability (332)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 00 33` | Liquor Liability Coverage Form | `COVERAGE_FORM` | — |
| `CG 00 34` | Liquor Liability Coverage Form | `COVERAGE_FORM` | — |
| `IL 00 17` | Common Policy Conditions | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `IL 00 21` | Nuclear Energy Liability Exclusion Endorsement (Broad Form) | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `CG 02 24` | Earlier Notice Of Cancellation Provided By Us Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 03 05` | Endorsement Use Deductible Liability Insurance Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 04 24` | Coverage For Injury To Leased Workers Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 21 50` | Refer to Rule 36.C.15. to use Amendment Of Liquor Liability Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 01` | Non-binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 02` | Binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 04` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 06` | Liquor Liability Bring Your Own Alcohol Establishments Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 53` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 25 14` | Designated Location(s) Aggregate Limit Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 03` | Supplemental Extended Reporting Period Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 06` | Limitation Of Coverage To Insured Premises Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 36` | Automatic Insured Status For Newly Acquired Or Formed Limited Liability Companies Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 45` | Exclusion Cross Suits Liability Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 99 09` | Premium Audit Noncompliance Charge Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |

### Rule 46 — OCP / Principals Protective (335)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 00 09` | Available coverage form: Owners And Contractors Protective Liability Coverage Form Coverage For Operations Of Designated Contractor | `COVERAGE_FORM` | — |
| `CG 34 92` | Do not attach Endorsement CG 34 97 to the policy when Endorsement | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `CG 34 97` | Exclusion Cyber Incident Endorsement | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `IL 00 21` | Nuclear Energy Liability Exclusion Endorsement (Broad Form) | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `CG 04 24` | Coverage For Injury To Leased Workers Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 22 57` | Exclusion Underground Resources And Equipment Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 01` | Non-binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 02` | Binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 14` | Waiver Of Governmental Immunity Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 04` | Earlier Notice Of Cancellation Provided By Us Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 05` | Personal Injury Liability Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 07` | G. Principals Protective Liability Coverage Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 12` | Pesticide Or Herbicide Applicator Limited Pollution Coverage Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 29 51` | Employment-related Practices Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 29 60` | Exclusion Unmanned Aircraft Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 29 88` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 31 15` | When Construction Project Management Protective Liability Coverage Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 31 31` | Fungi Or Bacteria Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 31 32` | Limited Fungi Or Bacteria Coverage Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 31 66` | Exclusion Exterior Insulation And Finish Systems Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 33 53` | Exclusion Access Or Disclosure Of Confidential Or Personal Material Or Information Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 33 70` | Silica Or Silica-related Dust Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 19` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 20` | Limited Coverage For Designated Unmanned Aircraft Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 23` | Exclusion Earth Movement Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 28` | Exclusion Cross Suits Liability Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 32` | Total Pollution Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 33` | Total Pollution Exclusion With A Hostile Fire Exception Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 34` | Total Pollution Exclusion With A Building Heating, Cooling And Dehumidifying Equipment Exception And A Hostile Fire Exception Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 46` | Cannabis Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 47` | Cannabis Exclusion With Hemp Exception Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 88` | Exclusion Exterior Insulation And Finish Systems (EIFS) With Exception For Drainable EIFS Not Installed Over Wood Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 90` | Exclusion Exterior Insulation And Finish Systems With Exception For Designated Operations Or Projects Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 95` | Exclusion Perfluoroalkyl And Polyfluoroalkyl Substances (PFAS) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 98` | Exclusion Electronic Data Deletion Of Bodily Injury Exception Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 99 10` | Premium Audit Noncompliance Charge Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `IL 00 17` | Is not used in conjunction with the Common Policy Conditions Endorsement | `REFERENCED` | — |

### Rule 47 — Pollution Liability (350)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 29 78` | Exclusion Underground Storage Tank Incidents Endorsement | `CONDITIONAL_MANDATORY_MULTISTATE` | 2. Conditional Mandatory Multistate Endorsements |
| `CG 00 39` | Pollution Liability Coverage Form Designated Sites | `COVERAGE_FORM` | — |
| `CG 00 40` | Pollution Liability Limited Coverage Form Designated Sites | `COVERAGE_FORM` | — |
| `CG 00 42` | Coverage for underground storage tank incidents is available under the Underground Storage Tank Policy Designated Tanks | `COVERAGE_FORM` | 2. Conditional Mandatory Multistate Endorsements |
| `IL 00 17` | Common Policy Conditions | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `IL 00 21` | Nuclear Energy Liability Exclusion Endorsement (Broad Form) | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `CG 02 24` | Earlier Notice Of Cancellation Provided By Us Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 04 24` | Coverage For Injury To Leased Workers Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 01` | Non-binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 02` | Binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 04` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 53` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 01` | Pollution Liability Limited Coverage CG 00 40 Code 90105 G. Premium Determination Refer to company.  H. Extended Reporting Period Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 02` | Insured Site Definition (Contractors) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 28 33` | Voluntary Clean-up Costs Reimbursement Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 29 51` | Employment-related Practices Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 29` | Exclusion Cross Suits Liability Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 30` | Exclusion Cross Suits Liability Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 37` | Automatic Insured Status For Newly Acquired Or Formed Limited Liability Companies Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 38` | Automatic Insured Status For Newly Acquired Or Formed Limited Liability Companies Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 50` | Cannabis Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 51` | Cannabis Exclusion With Hemp Exception Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 99 09` | Premium Audit Noncompliance Charge Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |

### Rule 48 — Products/Completed Operations (336)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 00 37` | Products/Completed Operations Liability Coverage Form | `COVERAGE_FORM` | — |
| `CG 00 38` | Products/Completed Operations Liability Coverage Form | `COVERAGE_FORM` | — |
| `IL 00 17` | Common Policy Conditions | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `IL 00 21` | Nuclear Energy Liability Exclusion Endorsement (Broad Form) | `MANDATORY_MULTISTATE` | 1. Multistate Endorsements |
| `CG 02 24` | Earlier Notice Of Cancellation Provided By Us Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 04 24` | Coverage For Injury To Leased Workers Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 04 25` | B.2. and Table 40.E. applicable to Cyber Incident Liability Coverage Subject To Each Cyber Incident Occurrence And Aggregate Limits Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 21 33` | Exclusion Designated Products Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 21 34` | Exclusion Designated Work Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 21 39` | Contractual Liability Limitation Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 21 54` | Insurance Program Endorsement CG 34 24 Based on Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 21 85` | Exclusion Electronic Data Deletion Of Bodily Injury Exception Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 21 98` | Total Pollution Exclusion Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 21 99` | Total Pollution Exclusion For Designated Products Or Work Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 24 01` | Non-binding Arbitration Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 24 02` | Binding Arbitration Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 24 03` | Waiver Of Charitable Immunity Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 24 04` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 24 10` | Excess Provision Vendors Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 24 26` | Amendment Of Insured Contract Definition Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 24 53` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 25 47` | Designated Project(s) Aggregate Limit Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 25 48` | Designated Location(s) Aggregate Limit Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 27 03` | Amendment Of Section V Extended Reporting Periods For Specific Accidents, Products, Work Or Location Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 27 05` | Exclusion Of Specific Accidents, Products, Work Or Location Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 28 34` | Supplemental Extended Reporting Period Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 28 35` | Supplemental Extended Reporting Period Endorsement For Specific Accidents, Products, Work Or Locations | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 29 52` | Amendment Of Liquor Liability Exclusion Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 29 53` | Amendment Of Liquor Liability Exclusion Exception For Scheduled Premises Or Activities Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 31 31` | Fungi Or Bacteria Exclusion Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 31 32` | Limited Fungi Or Bacteria Coverage Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 31 67` | Exclusion Exterior Insulation And Finish Systems Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 33 53` | Exclusion Access Or Disclosure Of Confidential Or Personal Material Or Information Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 33 70` | Silica Or Silica-related Dust Exclusion Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 33 76` | Communicable Disease Exclusion Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 12` | Amendment Of Coverage Territory Worldwide Coverage Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 13` | This endorsement should not be attached to the same policy with either Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 14` | This endorsement should not be attached to the same policy with either Endorsement CG 34 13 or | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 15` | Genetically Modified Organism Exclusion Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 16` | Genetically Modified Organism Exclusion For Designated Operations Or Products Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 24` | Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 25` | Limited Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 26` | Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Limited Exception For Additional Insureds Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 27` | Limited Exclusion Designated Operations Covered By A Controlled (Wrap-up) Insurance Program Limited Exception For Additional Insureds Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 38` | Automatic Insured Status For Newly Acquired Or Formed Limited Liability Companies Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 42` | Amendment Of Coverage Territory Worldwide Coverage Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 43` | This endorsement should not be attached to the same policy with either Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 44` | This endorsement should not be attached to the same policy with either Endorsement CG 34 43 or | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 76` | Defense Within Limits Products/Completed Operations Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 89` | Exclusion Exterior Insulation And Finish Systems (EIFS) With Exception For Drainable EIFS Not Installed Over Wood Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 91` | Exclusion Exterior Insulation And Finish Systems With Exception For Designated Operations Or Projects Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 92` | Cyber Incident Liability Coverage Subject To Each Cyber Incident Occurrence And Aggregate Limits Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 34 95` | Exclusion Perfluoroalkyl And Polyfluoroalkyl Substances (PFAS) Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 05` | Exclusion Earth Movement Completed Operations Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 06` | Earth Movement Exclusion For Designated Operation(s) Or Project(s) Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 12` | Exclusion All Hazards In Connection With An Electronic Smoking Device, Its Vapor, Component Parts, Equipment And Accessories Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 13` | Exclusion Health Hazards, Electronic Smoking Device Vapor Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 14` | Cannabis Exclusion Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 15` | Cannabis Exclusion With Hemp Exception Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 16` | Cannabis Exclusion With Hemp and Lessors Risk Exceptions Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 25` | Exclusion Designated Cannabis Products Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 40 26` | Exclusion Cannabis Products Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |
| `CG 99 09` | Premium Audit Noncompliance Charge Endorsement | `OPTIONAL_RTC` | C. Optional Endorsements Refer To Company For Rating |

### Rule 49 — Railroad Protective (335)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 00 35` | Available coverage form: Railroad Protective Liability Coverage Form | `COVERAGE_FORM` | — |
| `IL 00 21` | Multistate Endorsement Nuclear Energy Liability Exclusion Endorsement Broad Form | `MANDATORY_MULTISTATE` | C. Mandatory Endorsements |
| `CG 24 01` | Non-binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 02` | Binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 04` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 14` | Waiver Of Governmental Immunity Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 24 53` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 33 71` | Silica Or Silica-related Dust Exclusion | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 21` | Exclusion Unmanned Aircraft Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 22` | Limited Coverage For Designated Unmanned Aircraft Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 31` | Exclusion Cross Suits Liability Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 48` | Cannabis Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 49` | Cannabis Exclusion With Hemp Exception Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `CG 34 96` | Exclusion Perfluoroalkyl And Polyfluoroalkyl Substances (PFAS) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements Refer To Company For Rating |
| `IL 00 17` | Is not used in conjunction with the Common Policy Conditions Endorsement | `REFERENCED` | — |

### Rule 53 — Underground Storage Tank (350)

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 00 42` | Available coverage form: Underground Storage Tank Policy Designated Sites Form | `COVERAGE_FORM` | — |
| `IL 00 21` | Multistate Endorsement Nuclear Energy Liability Exclusion Endorsement (Broad Form) | `MANDATORY_MULTISTATE` | C. Mandatory Endorsements |
| `CG 04 26` | Coverage For Injury To Leased Workers Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 24 01` | Non-binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 24 02` | Binding Arbitration Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 24 04` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 24 53` | Waiver Of Transfer Of Rights Of Recovery Against Others To Us (Waiver Of Subrogation) Automatic Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 30 57` | Supplemental Extended Reporting Period Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 30 70` | Exclusion Cross Suits Liability Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 30 71` | Cannabis Exclusion Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 30 72` | Cannabis Exclusion With Hemp Exception Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `CG 99 09` | Premium Audit Noncompliance Charge Endorsement | `OPTIONAL_RTC` | D. Optional Endorsements |
| `IL 00 17` | Is not used in conjunction with the Common Policy Conditions Endorsement | `REFERENCED` | — |

### Rule 55 — Terrorism

| Form | Endorsement | Role | Governing paragraph |
|---|---|---|---|
| `CG 21 70` | Cap On Losses From Certified Acts Of Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 71` | Exclusion Of Other Acts Of Terrorism Committed Outside The United States; Cap On Losses From Certified Acts Of Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 73` | Exclusion Of Certified Acts Of Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 75` | Exclusion Of Certified Acts Of Terrorism And Exclusion Of Other Acts Of Terrorism Committed Outside The United States Endorsement | `REFERENCED` | — |
| `CG 21 76` | Exclusion Of Punitive Damages Related To A Certified Act Of Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 80` | Certified Acts Of Terrorism Aggregate Limit; Cap On Losses From Certified Acts Of Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 82` | Certified Acts Of Terrorism Aggregate Limit; Cap On Losses From Certified Acts Of Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 84` | Exclusion Of Certified Nuclear, Biological, Chemical Or Radiological Acts Of Terrorism; Cap On Losses From Certified Acts Of Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 87` | Conditional Exclusion Of Terrorism (Relating To Disposition Of Federal Terrorism Risk Insurance Act) Endorsement | `REFERENCED` | — |
| `CG 21 88` | Of Terrorism Involving Nuclear, Biological Or Chemical Terrorism (Relating To Disposition Of Federal Terrorism Risk Insurance Act) Endorsement | `REFERENCED` | — |
| `CG 21 89` | Limitation Of Coverage For Terrorism On An Annual Aggregate Basis (Relating To Disposition Of Federal Terrorism Risk Insurance Act) Endorsement | `REFERENCED` | — |
| `CG 21 90` | Exclusion Of Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 91` | Exclusion Of Terrorism Involving Nuclear, Biological Or Chemical Terrorism Endorsement | `REFERENCED` | — |
| `CG 21 92` | Limitation Of Coverage For Terrorism On An Annual Aggregate Basis Endorsement | `REFERENCED` | — |
| `CG 21 93` | Extended Reporting Period For Terrorism Coverage Endorsement | `REFERENCED` | — |
| `IL 09 85` | For Policies That Begin Prior To The Last Calendar Year Of Federal Program Use Disclosure Pursuant To Terrorism Risk Insurance Act Endorsement | `REFERENCED` | — |
| `IL 09 98` | Use Disclosure Of Premium Through End Of Year For Certified Acts Of Terrorism Coverage (Pursuant To Terrorism Risk Insurance Act) Endorsement | `REFERENCED` | — |
| `IL 09 99` | Use Disclosure Of Premium And Estimated Premium For Certified Acts Of Terrorism Coverage (Pursuant To Terrorism Risk Insurance Act) Endorsement | `REFERENCED` | — |

---

## A3.3 State-mandated endorsements

Every coverage rule ends its mandatory-endorsement paragraph with *"State Endorsements —
Refer to state exceptions."* The state notices then publish a block headed *"Refer to
mandatory state endorsements:"*. Counts below are from the latest Rules notice per
jurisdiction.

| Jurisdiction | Mandated forms | Forms |
|---|---|---|
| AK | 18 | `CG 21 05` `CG 21 23` `CG 21 25` `CG 21 30` `CG 26 70` `CG 29 43` `CG 32 71` `CG 32 72` `CG 32 74` `CG 32 91` `CG 34 58` `CG 34 59` `CG 34 60` `CG 34 61` `CG 34 62` `CG 34 63` `CG 34 75` `IL 02 80` |
| AL | 0 | *(none published in this notice)* |
| AR | 11 | `CG 00 02` `CG 01 42` `CG 01 43` `CG 01 88` `CG 04 62` `CG 26 08` `CG 29 23` `CG 31 47` `CG 31 77` `IL 01 99` `IL 02 31` |
| AZ | 0 | *(none published in this notice)* |
| CA | 0 | *(none published in this notice)* |
| CO | 7 | `CG 01 72` `CG 28 65` `CG 30 05` `CG 31 81` `CG 31 82` `IL 01 25` `IL 02 28` |
| CT | 8 | `CG 24 06` `CG 24 08` `CG 28 06` `CG 28 57` `CG 31 36` `IL 00 17` `IL 01 40` `IL 02 60` |
| DC | 0 | *(none published in this notice)* |
| DE | 4 | `CG 30 02` `CG 31 85` `IL 01 51` `IL 02 37` |
| FL | 3 | `CG 02 20` `CG 27 52` `CG 27 53` |
| GA | 3 | `CG 04 18` `CG 31 86` `CG 33 50` |
| IA | 0 | *(none published in this notice)* |
| ID | 0 | *(none published in this notice)* |
| IL | 9 | `CG 00 02` `CG 00 38` `CG 01 99` `CG 02 00` `CG 29 05` `CG 29 81` `CG 34 77` `IL 01 47` `IL 01 62` |
| IN | 7 | `CG 01 23` `CG 24 28` `CG 31 91` `CG 33 01` `IL 01 17` `IL 01 58` `IL 02 72` |
| KS | 3 | `CG 26 82` `CG 27 27` `CG 31 92` |
| KY | 3 | `CG 33 89` `CG 33 98` `IL 02 63` |
| LA | 9 | `CG 00 09` `CG 01 18` `CG 26 84` `CG 28 14` `CG 28 23` `CG 28 27` `CG 29 38` `CG 33 56` `CG 33 57` |
| MA | 0 | *(none published in this notice)* |
| MD | 3 | `CG 02 01` `CG 24 08` `CG 26 73` |
| ME | 0 | *(none published in this notice)* |
| MI | 2 | `CG 01 68` `CG 33 02` |
| MN | 8 | `CG 01 22` `CG 26 30` `CG 26 31` `CG 26 81` `CG 29 07` `CG 29 97` `CG 31 46` `CG 34 78` |
| MO | 6 | `CG 26 25` `CG 26 95` `CG 29 29` `CG 31 12` `CG 33 05` `CG 33 07` |
| MS | 0 | *(none published in this notice)* |
| MT | 7 | `CG 27 07` `CG 27 44` `CG 28 41` `CG 33 24` `IL 01 32` `IL 01 67` `IL 02 43` |
| NC | 0 | *(none published in this notice)* |
| ND | 0 | *(none published in this notice)* |
| NE | 0 | *(none published in this notice)* |
| NH | 15 | `CG 01 12` `CG 01 14` `CG 01 52` `CG 21 29` `CG 21 50` `CG 21 51` `CG 26 55` `CG 30 20` `CG 31 05` `CG 31 06` `CG 31 27` `CG 31 28` `CG 33 26` `CG 40 09` `IL 01 35` |
| NJ | 3 | `CG 29 87` `IL 01 41` `IL 02 08` |
| NM | 3 | `CG 29 36` `CG 34 80` `IL 02 98` |
| NV | 3 | `CG 24 08` `IL 01 15` `IL 02 51` |
| NY | 13 | `CG 01 04` `CG 01 63` `CG 03 05` `CG 26 03` `CG 26 11` `CG 26 21` `CG 26 35` `CG 26 36` `CG 34 12` `CG 34 13` `CG 34 14` `IL 00 23` `IL 02 68` |
| OH | 0 | *(none published in this notice)* |
| OK | 7 | `CG 01 09` `CG 27 47` `CG 27 48` `CG 27 49` `CG 34 81` `IL 01 79` `IL 02 36` |
| OR | 3 | `CG 33 83` `IL 01 42` `IL 02 79` |
| PA | 10 | `CG 01 10` `CG 01 11` `CG 01 75` `CG 01 77` `CG 28 49` `CG 29 76` `CG 33 16` `IL 01 20` `IL 02 46` `IL 09 10` |
| PR | 4 | `CG 01 07` `CG 28 21` `CG 33 53` `IL 01 36` |
| RI | 10 | `CG 00 42` `CG 30 12` `CG 33 18` `CG 33 84` `CG 33 86` `CG 34 83` `IL 01 28` `IL 01 61` `IL 01 97` `IL 02 73` |
| SC | 0 | *(none published in this notice)* |
| SD | 6 | `CG 01 44` `CG 29 14` `CG 29 15` `CG 33 20` `CG 33 51` `IL 02 32` |
| TN | 3 | `CG 31 48` `CG 31 51` `IL 02 50` |
| TX | 11 | `CG 01 01` `CG 01 03` `CG 01 36` `CG 01 56` `CG 26 39` `CG 28 55` `CG 31 07` `CG 31 21` `CG 34 23` `IL 01 68` `IL 02 75` |
| UT | 3 | `CG 01 86` `CG 33 22` `CG 33 23` |
| VA | 11 | `CG 00 39` `CG 00 40` `CG 01 79` `CG 32 33` `CG 32 35` `CG 32 39` `CG 32 47` `CG 32 48` `CG 32 64` `CG 33 88` `IL 01 38` |
| VT | 17 | `CG 00 01` `CG 00 02` `CG 01 54` `CG 01 61` `CG 04 28` `CG 04 29` `CG 04 30` `CG 21 55` `CG 21 65` `CG 28 25` `CG 31 41` `CG 33 52` `CG 33 70` `CG 34 95` `IL 01 09` `IL 01 26` `IL 02 19` |
| WA | 12 | `CG 01 81` `CG 01 97` `CG 04 42` `CG 28 01` `CG 29 57` `CG 29 79` `CG 29 99` `CG 31 49` `CG 31 50` `IL 01 23` `IL 01 46` `IL 01 98` |
| WI | 0 | *(none published in this notice)* |
| WV | 0 | *(none published in this notice)* |
| WY | 5 | `CG 01 85` `CG 29 89` `CG 34 84` `IL 01 14` `IL 02 52` |

> **21 of 51 jurisdictions publish no mandatory-endorsement block in their current Rules
> notice.** That is an absence of evidence in this corpus, **not** evidence that no state
> endorsement is required — those mandates may live in the Forms notices, which are outside
> this corpus. See `09-GAPS-AND-OPEN-QUESTIONS.md`.

---

## A3.4 Forms added and dropped between CW editions

**New in CW 2027** (40 forms) — absent from CW 2022:

> `CG 04 25` `CG 04 95` `CG 21 70` `CG 21 71` `CG 21 73` `CG 21 75` `CG 21 76` `CG 21 80` `CG 21 82` `CG 21 84` `CG 21 85` `CG 21 87` `CG 21 88` `CG 21 89` `CG 21 90` `CG 21 91` `CG 21 92` `CG 21 93` `CG 23 07` `CG 24 55` `CG 24 56` `CG 31 74` `CG 34 88` `CG 34 89` `CG 34 90` `CG 34 91` `CG 34 92` `CG 34 95` `CG 34 96` `CG 34 97` `CG 34 98` `CG 34 99` `CG 40 27` `CG 40 30` `CG 40 32` `CG 40 33` `CG 40 34` `IL 09 85` `IL 09 98` `IL 09 99`

**Present in CW 2022, absent from CW 2027** (21 forms):

> `CG 04 31` `CG 04 32` `CG 04 72` `CG 20 41` `CG 21 06` `CG 21 07` `CG 21 08` `CG 21 47` `CG 21 60` `CG 21 61` `CG 21 62` `CG 21 63` `CG 21 64` `CG 22 40` `CG 22 41` `CG 22 75` `CG 22 77` `CG 22 91` `CG 22 98` `CG 22 99` `CG 33 59`

This is the endorsement-level view of the edition problem described in
`12-VERSIONING-AND-EDITIONS.md`: a policy written against the 2022 edition can legitimately
carry a form the 2027 edition no longer lists. The catalog must be **edition-scoped**, and a
form must never be validated against the current edition when re-rating a prior-edition term.
