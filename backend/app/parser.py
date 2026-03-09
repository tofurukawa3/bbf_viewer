import os
from lxml import etree
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Data dir path relative to this backend module
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

def get_available_models():
    """Returns a list of available XML models in the data directory."""
    models = []
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith(".xml"):
                models.append(f)
    return models

def parse_xml_to_dict(xml_file_name: str) -> dict:
    """
    Given an XML file name in the data directory, parses the CWMP Data Model
    and returns a nested dictionary representation.
    """
    file_path = os.path.join(DATA_DIR, xml_file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Model file {xml_file_name} not found.")

    tree = etree.parse(file_path)
    root = tree.getroot()

    # Find all <object> elements
    root_node = {
        "name": "Root",
        "node_type": "object",
        "access": "readOnly",
        "description": "Root of the data model",
        "children": []
    }

    for obj in root.xpath("//*[local-name()='object']"):
        obj_name = obj.get("name", obj.get("base", ""))
        obj_access = obj.get("access", "readOnly")
        
        # Build node
        node = {
            "name": obj_name,
            "node_type": "object",
            "access": obj_access,
            "description": _get_description(obj),
            "children": []
        }
        
        # Parse parameters for this object
        for param in obj.xpath("*[local-name()='parameter']"):
            param_name = param.get("name", param.get("base", ""))
            param_access = param.get("access", "readOnly")
            
            # get type
            syntax_nodes = param.xpath("*[local-name()='syntax']")
            data_type = "string"
            if syntax_nodes and len(syntax_nodes) > 0:
                syntax_node = syntax_nodes[0]
                type_node = syntax_node.find("*")
                if type_node is not None:
                    # e.g., <string>, <unsignedInt>
                    # Actually type_node.xpath("local-name()") returns a list of strings
                    type_names = type_node.xpath("local-name()")
                    if type_names and isinstance(type_names, str):
                        data_type = type_names
                    elif type_names and isinstance(type_names, list) and len(type_names) > 0:
                        data_type = type_names[0]
                    else:
                        # Fallback to tag without namespace
                        data_type = type_node.tag.split("}")[-1] if "}" in type_node.tag else type_node.tag
            
            p_node = {
                "name": param_name,
                "node_type": "parameter",
                "access": param_access,
                "description": _get_description(param),
                "data_type": data_type
            }
            
            # Extract default value if available
            default_nodes = param.xpath(".//*[local-name()='default']")
            if default_nodes and len(default_nodes) > 0:
                p_node["default_value"] = default_nodes[0].get("value", "")

            node["children"].append(p_node)

        _insert_into_tree(root_node, obj_name, node)

    return root_node

def _get_description(element) -> str:
    desc = element.xpath("*[local-name()='description']")
    if desc and len(desc) > 0:
        return desc[0].text.strip() if desc[0].text else ""
    return ""

def _insert_into_tree(root, path, node):
    """
    Very basic hierarchical inserter based on dot notation.
    """
    if not node["name"]:
        # Skip completely empty nodes (usually abstract base objects without names)
        return

    # Strip trailing dot from path strings like "Device." -> "Device" to prevent empty parts
    clean_path = path.rstrip(".")
    parts = [p for p in clean_path.split(".") if p]
    
    if len(parts) <= 1:
        root["children"].append(node)
        return
        
    current = root["children"]
    for i, part in enumerate(parts[:-1]):
        # Find existing node or create dummy
        # Append dot only for display logic, but checking without dot is safer
        found = next((n for n in current if n["name"] == part or n["name"] == part + "."), None)
        if not found:
            found = {
                "name": part + ".", 
                "node_type": "object",
                "access": "readOnly",
                "description": "",
                "children": []
            }
            current.append(found)
        if "children" not in found:
            found["children"] = []
        current = found["children"]
        
    # Overwrite dummy or just append
    existing = next((n for n in current if n["name"] == node["name"]), None)
    if existing:
        # Prevent appending children if this is an empty param shell
        if node["children"]:
             existing["children"].extend(node["children"])
        if node["description"]:
             existing["description"] = node["description"]
        existing["access"] = node["access"]
    else:
        current.append(node)

def generate_netconf_edit_config(target_path: str, value: Any) -> str:
    """
    Generates a basic NETCONF <edit-config> XML snippet.
    """
    parts = [p for p in target_path.split(".") if p and p != "{i}"]
    
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_str += '<rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">\n'
    xml_str += '  <edit-config>\n'
    xml_str += '    <target>\n'
    xml_str += '      <running/>\n'
    xml_str += '    </target>\n'
    xml_str += '    <config>\n'
    
    indent = "      "
    closing_tags = []
    
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            xml_str += f'{indent}<{part}>{value}</{part}>\n'
        else:
            xml_str += f'{indent}<{part}>\n'
            closing_tags.insert(0, part)
            indent += "  "
            
    for tag in closing_tags:
        indent = indent[:-2]
        xml_str += f'{indent}</{tag}>\n'
        
    xml_str += '    </config>\n'
    xml_str += '  </edit-config>\n'
    xml_str += '</rpc>'
    
    return xml_str
