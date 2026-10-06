import sys, json
from collections import Counter, defaultdict
sys.path.insert(0, r"F:\Recursive_Harness_2.0")
from gl_engine.resolve import EditionResolver, ResolvedBook
r=EditionResolver(); ASOF=sys.argv[1]
B=['Payroll','Area','Gross Sales','Units']
out={}
def rows(b,n,k='Rate'):
    t=b.table(n,k); rs=list(t.rows)
    if not rs:
        for s in b.sibling_tables(n,k): rs+= [ (s, x) for x in s.rows ]
        return [(s.header,x) for s,x in rs]
    return [(t.header,x) for x in rs]
for J in sorted(r.jurisdictions):
    if J=='CW': continue
    b=ResolvedBook(r.resolve(J,ASOF))
    def dom(n):
        rs=rows(b,n,'Domain'); m={}
        for h,x in rs:
            if x[h.index('StateCode')] in (J,): m[x[h.index('ClassCode') if 'ClassCode' in h else 1]]=x[h.index('DataValue')]
        if not m:
            for h,x in rs:
                if x[h.index('StateCode')]=='CW': m[x[h.index('ClassCode') if 'ClassCode' in h else 1]]=x[h.index('DataValue')]
        return m
    pb=dom('DomainPremiumBasisPremOpsClassCode'); cb=dom('DomainPremiumBasisProdsCompldOpsClassCode')
    def nz(n, cc='ClassCodeCGLProds', val='Rate'):
        s=set()
        for h,x in rows(b,n):
            ci=[i for i,c in enumerate(h) if c.startswith('ClassCode')][0]; vi=h.index(val) if val in h else len(h)-1
            try:
                if float(x[vi])!=0: s.add(str(x[ci]))
            except: pass
        return s
    po=nz('PremOpsLossCost'); pco=nz('ProdsCompldOpsLossCost'); pcoelp=nz('ProdsCompldOpsELPFactor')
    t=b.table('ProdsCompldOpsELPText'); h=t.header
    incl=sum(1 for x in t.rows if x[h.index('ProdsCompldOpsELP')]=='Not Applicable')
    o={'po':{k:sum(1 for c,v in pb.items() if v==k and str(c) in po) for k in B},
       'pco':{k:sum(1 for c,v in cb.items() if v==k and (str(c) in pco or str(c) in pcoelp)) for k in B},
       'po_other_bases': len({v for c,v in pb.items() if str(c) in po}-set(B)),
       'pco_included_classes': incl}
    out[J]=o
json.dump(out,open(r"C:/Users/droma/AppData/Local/Temp/claude/F--Recursive-Harness-2-0/0bb8a058-7f63-464a-bf7a-eaad9b793544/scratchpad/basis_%s.json"%ASOF,'w'),indent=0)
for J,o in out.items(): print(J,o)
