"""THE SOURCE. Package discovery, identity, editions and tables."""
from .discovery import Package, PackageId, discover
from .tables import (Column, Population, Range, Shape, Table, TableDef,
                     list_tables, load_table, split_families)

__all__ = ["Package", "PackageId", "discover", "Table", "TableDef", "Column",
           "Range", "Shape", "Population", "load_table", "list_tables",
           "split_families"]
