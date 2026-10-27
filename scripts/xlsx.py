"""A minimal .xlsx writer, standard library only.

The engine has no third-party dependency and the workbook should not introduce
one. An .xlsx is a zip of XML; this writes the four parts Excel needs and uses
**inline strings** rather than a shared-string table, which costs some file size
and removes a whole class of index bug.

    from xlsx import Workbook
    wb = Workbook()
    wb.sheet("Fields", ["table", "column"], [["GeneralLiability", "Subline"]])
    wb.save("out.xlsx")

Numbers are written as numbers so Excel sorts and filters them properly;
everything else is an inline string. The first row of each sheet is frozen and
auto-filtered, because a 1,400-row reference sheet is unusable otherwise.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

_CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
{sheets}
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFE8EEF4"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>
</styleSheet>"""


def _esc(v: str) -> str:
    return (str(v).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _col_name(i: int) -> str:
    name = ""
    while i >= 0:
        name = chr(ord("A") + i % 26) + name
        i = i // 26 - 1
    return name


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class Workbook:
    def __init__(self):
        self._sheets: list[tuple[str, list, list]] = []

    def sheet(self, name: str, header: list, rows: list) -> None:
        """Add a sheet. `name` is truncated to Excel's 31-character limit."""
        self._sheets.append((name[:31], header, rows))

    def _sheet_xml(self, header: list, rows: list) -> str:
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<worksheet xmlns="http://schemas.openxmlformats.org/'
               'spreadsheetml/2006/main">',
               f'<sheetViews><sheetView workbookViewId="0">'
               f'<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" '
               f'state="frozen"/></sheetView></sheetViews>',
               "<sheetData>"]
        all_rows = [header] + list(rows)
        for r, row in enumerate(all_rows, start=1):
            cells = []
            for c, v in enumerate(row):
                ref = f"{_col_name(c)}{r}"
                style = ' s="1"' if r == 1 else ""
                if v is None or v == "":
                    continue
                if _is_number(v):
                    cells.append(f'<c r="{ref}"{style}><v>{v}</v></c>')
                else:
                    cells.append(f'<c r="{ref}"{style} t="inlineStr">'
                                 f"<is><t>{_esc(v)}</t></is></c>")
            out.append(f'<row r="{r}">' + "".join(cells) + "</row>")
        out.append("</sheetData>")
        if all_rows and header:
            last = f"{_col_name(len(header) - 1)}{len(all_rows)}"
            out.append(f'<autoFilter ref="A1:{last}"/>')
        out.append("</worksheet>")
        return "".join(out)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        n = len(self._sheets)
        overrides = "\n".join(
            f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
            f'ContentType="application/vnd.openxmlformats-officedocument.'
            f'spreadsheetml.worksheet+xml"/>' for i in range(n))
        sheets_xml = "".join(
            f'<sheet name="{_esc(nm)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>'
            for i, (nm, _, _) in enumerate(self._sheets))
        wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<workbook xmlns="http://schemas.openxmlformats.org/'
              'spreadsheetml/2006/main" xmlns:r="http://schemas.'
              'openxmlformats.org/officeDocument/2006/relationships">'
              f"<sheets>{sheets_xml}</sheets></workbook>")
        rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/'
                'package/2006/relationships">']
        for i in range(n):
            rels.append(f'<Relationship Id="rId{i + 1}" Type="http://schemas.'
                        f'openxmlformats.org/officeDocument/2006/relationships/'
                        f'worksheet" Target="worksheets/sheet{i + 1}.xml"/>')
        rels.append(f'<Relationship Id="rId{n + 1}" Type="http://schemas.'
                    f'openxmlformats.org/officeDocument/2006/relationships/'
                    f'styles" Target="styles.xml"/>')
        rels.append("</Relationships>")

        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", _CT.format(sheets=overrides))
            z.writestr("_rels/.rels", _ROOT_RELS)
            z.writestr("xl/workbook.xml", wb)
            z.writestr("xl/_rels/workbook.xml.rels", "".join(rels))
            z.writestr("xl/styles.xml", _STYLES)
            for i, (_, header, rows) in enumerate(self._sheets):
                z.writestr(f"xl/worksheets/sheet{i + 1}.xml",
                           self._sheet_xml(header, rows))
        return path
