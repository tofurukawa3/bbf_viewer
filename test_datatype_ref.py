import sys
import os

# Set up path to import parser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'app')))
import parser

res = parser.parse_xml_to_dict("tr-181-2-18-0-cwmp.xml")

def find_diagnostics_state(node):
    if node["name"] == "DiagnosticsState" and "enum_values" in node:
        print(f"Found {node['name']} with detailed_type: {node.get('detailed_type')} and enum_values: {node.get('enum_values')}")
    if node.get("children"):
        for c in node["children"]:
            find_diagnostics_state(c)

find_diagnostics_state(res)
