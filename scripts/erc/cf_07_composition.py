import os, re, json

PATH = r"C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\DataDefs\MasterCFCW.DataDef.xsd"
DATADEFS_DIR = r"C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\DataDefs"

size = os.path.getsize(PATH)
print(f"File size: {size} bytes ({size/1024/1024:.2f} MB)")

files_in_dir = os.listdir(DATADEFS_DIR)
print("Files in DataDefs dir:", files_in_dir)

complex_type_count = 0
simple_type_count = 0
element_count = 0
with open(PATH, encoding="utf-8", errors="ignore") as fh:
    for line in fh:
        complex_type_count += line.count("<xs:complexType")
        simple_type_count += line.count("<xs:simpleType")
        element_count += line.count("<xs:element ")

print("complexType occurrences:", complex_type_count)
print("simpleType occurrences:", simple_type_count)
print("element occurrences:", element_count)

# check for xs:include / xs:import (would indicate multi-file composition even if physically one file references others)
includes = 0
imports = 0
with open(PATH, encoding="utf-8", errors="ignore") as fh:
    content = fh.read()
includes = content.count("<xs:include")
imports = content.count("<xs:import")
print("xs:include occurrences:", includes)
print("xs:import occurrences:", imports)

json.dump({
    "file": PATH,
    "size_bytes": size,
    "size_mb": round(size/1024/1024, 2),
    "files_in_datadefs_dir": files_in_dir,
    "complexType_count": complex_type_count,
    "simpleType_count": simple_type_count,
    "element_count": element_count,
    "xs_include_count": includes,
    "xs_import_count": imports,
    "single_file_monolithic": len(files_in_dir) == 1,
}, open(r"C:\Projects\Recursive_Harness_2.0\scripts\erc\_cf_composition_survey.json", "w"), indent=2)
