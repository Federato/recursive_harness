import re, sys, io
# usage: dump_rule.py <file> <RuleName> [RuleName...]
path = sys.argv[1]
s = open(path, encoding='utf-8-sig').read()
# split into rule blocks
blocks = {}
for m in re.finditer(r'\t<rul:Rule Name="([^"]+)"', s):
    name = m.group(1)
    start = m.start()
    end = s.index('\n\t</rul:Rule>', start) + len('\n\t</rul:Rule>')
    blocks.setdefault(name, []).append(s[start:end])
if len(sys.argv) == 2:
    for k, v in blocks.items():
        print(f'{k}\t{sum(len(x) for x in v)}')
    sys.exit()
for want in sys.argv[2:]:
    for b in blocks.get(want, [f'<<NOT FOUND: {want}>>']):
        print(b)
        print('-' * 100)
