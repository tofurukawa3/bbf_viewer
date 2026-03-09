from lxml import etree
import os

data_dir = "C:\\Users\\to-fu\\Documents\\project\\bbf_viewer\\data"
for file in os.listdir(data_dir):
    if not file.endswith(".xml"): continue
    tree = etree.parse(os.path.join(data_dir, file))
    root = tree.getroot()

    for param in root.xpath("//*[local-name()='parameter']"):
        syntax = param.xpath("*[local-name()='syntax']")
        if syntax:
            for ds in syntax[0].xpath("*[local-name()='dataType']"):
                ref = ds.get("ref")
                if ref:
                    enums = ds.xpath("*[local-name()='enumeration']")
                    if not enums:
                        print(f"File: {file} | Found empty dataType ref={ref} in parameter {param.get('name', param.get('base', ''))}")
