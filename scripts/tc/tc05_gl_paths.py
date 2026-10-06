import sys, re, json
from collections import Counter, defaultdict
sys.path.insert(0, r"F:\Recursive_Harness_2.0")
from gl_engine.resolve import EditionResolver, ResolvedBook
ASOF = sys.argv[1] if len(sys.argv)>1 else '20261006'
r = EditionResolver()
RATE = ['PremOpsLossCost','PremOpsELP','PremOpsELPText','PremOpsLCM','PremOpsLCMCompany','LCM','LCMCompany','ILFPremOps','PremOpsIncrdLimitTableAssignment',
 'PremOpsMinPremium','PremOpsSizeOfRiskLossCost','PremOpsSizeOfRiskRelativity','PremOpsSizeOfRiskRelativityTableAssignment','SplitLimitWeightFactorPremOpsBI',
 'ProdsCompldOpsLossCost','ProdsCompldOpsELP','ProdsCompldOpsELPFactor','ProdsCompldOpsELPText','ProdsCompldOpsLCM','ProdsCompldOpsLCMCompany','ILFProds',
 'IncreasedLimitsTableAssignmentProdsCompldOps','ProdsCompldOpsMinPremium','ProdsCompldOpsSizeOfRiskLossCost','SpecialCombinedMinPremium','MinPremium','MinimumPremium',
 'MedPayFactor','IncreasedMedPayLimitFactor','PersonalAndAdvertisingInjuryLimit',
 'DedFactorPremOpsBI','DedFactorPremOpsPD','DedFactorPremOpsCSL','DedFactorProdsBI','DedFactorProdsPD','DedFactorProdsCSL','DeductibleNumeric',
 'PremOpsClaimsMadeMultiplier','ClaimsMadeMultiplierPremOps','GovernmentalUnitsPremOpsIncrdLimitFactor']
DOM = ['DomainPremiumBasisPremOpsClassCode','DomainPremiumBasisProdsCompldOpsClassCode','DomainProductsCompldOpsCov','DomainPremOpsBIPDDeductible','DomainPremOpsBIDeductibleFactor',
 'DomainPremOpsDed','DomainProdsCompldOpsDed','DomainProdsCompldOpsBIPDDeductible','DomainFinalPremOpsBIDed','DomainFinalPremOpsPDDed','DomainMedPayLimit','DomainMedPayLimitExcl',
 'DomainPersonalAndAdvertisingInjuryLimit','DomainPremLCMTier','DomainProdLCMTier','DomainPolicyWritingMinPremium']
KW = re.compile(r'Min(imum)?Prem|Ded|ILF|IncrdLimit|IncreasedLimit|LCM|MedicalPay|MedPay|BaseRate|FinalRate|SetPremium$|Exposure|PremiumBasis|LossCost|SizeOfRisk|PersonalAndAdvert|Personal',re.I)
GROUPS = ['GeneralLiabilityClassificationPremOpsCoverageRules','GeneralLiabilityClassificationProdsCompldOpsCoverageRules','GeneralLiabilityPremOpsPremiumToReachMinCoverageRules',
 'GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverageRules','GeneralLiabilitySpecialCombinedPremiumToReachMinCoverageRules','GeneralLiabilityRules','GeneralLiabilityClassificationRules','GeneralLiabilityLocationRules','GeneralLiabilityMedPayCoverageRules']
rx = re.compile(r'<rul:Rule Name="([^"]+)"[^>]*MetadataCodes="([^"]*)"')
def tinfo(b, n, kind, J):
    own = b.declares(n, kind)
    if own is None: return None
    t = b.table(n, kind)
    rows = list(t.rows)
    if not rows and kind=='Rate':
        for s in b.sibling_tables(n, kind): rows += s.rows
    sc = t.header.index('StateCode') if 'StateCode' in t.header else None
    c = Counter(x[sc] for x in rows) if sc is not None else Counter()
    d = dict(owner=own, pkg=t.package, rows=len(rows), stRows=c.get(J,0), cwRows=c.get('CW',0))
    if 'DataValue' in t.header:
        i=t.header.index('DataValue'); 
        pick=[x for x in rows if sc is None or x[sc]==J] or [x for x in rows if sc is None or x[sc]=='CW']
        d['values']=dict(Counter(str(x[i]) for x in pick))
    return d
out={}
for J in sorted(r.jurisdictions):
    if J=='CW': continue
    try: res=r.resolve(J, ASOF)
    except Exception as e: out[J]={'error':str(e)}; continue
    b=ResolvedBook(res)
    o=dict(state=res.state.pkg_id, parent=res.parent.pkg_id if res.parent else None, rate={}, dom={}, rules={})
    for n in RATE: o['rate'][n]=tinfo(b,n,'Rate',J)
    for n in DOM: o['dom'][n]=tinfo(b,n,'Domain',J)
    rd = res.state.content/'Rules'
    allst={}
    for f in rd.glob('*.Rule.xml'):
        g=f.name[:-9]
        txt=f.read_text(encoding='utf-8-sig',errors='replace')
        names=[(m.group(1),m.group(2)) for m in rx.finditer(txt)]
        allst[g]=names
    o['rule_files']=sorted(allst)
    for g in GROUPS:
        o['rules'][g]=[(n,m) for n,m in allst.get(g,[]) if n not in ('InitializeRuleSet',)]
    # state-only tables
    st=set(b.state.names('Rate')); cw=set(b.parent.names('Rate')) if b.parent else set()
    o['state_only_rate']=sorted(st-cw)
    out[J]=o
json.dump(out, open(r"C:/Users/droma/AppData/Local/Temp/claude/F--Recursive-Harness-2-0/0bb8a058-7f63-464a-bf7a-eaad9b793544/scratchpad/census_%s.json"%ASOF,'w'), indent=1, default=str)
print('done', len(out))
