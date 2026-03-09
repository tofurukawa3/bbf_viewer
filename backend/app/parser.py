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
            detailed_type = None
            enum_values_list = []
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
                        
                    if data_type == "dataType":
                        ref = type_node.get("ref")
                        if ref:
                            # Use the referenced type name (e.g. "DiagnosticsState") instead of literal "dataType"
                            data_type = ref
                        
                    # Extract detailed constraints inside the type_node
                    constraints = []
                    
                    # 1. Size or Length
                    size_nodes = type_node.xpath("*[local-name()='size']")
                    for constraint_node in size_nodes:
                        min_len = constraint_node.get("minLength")
                        max_len = constraint_node.get("maxLength")
                        if min_len and max_len:
                            constraints.append(f"length: {min_len}-{max_len}")
                        elif max_len:
                            constraints.append(f"max_length: {max_len}")
                            
                    # 2. Range
                    range_nodes = type_node.xpath("*[local-name()='range']")
                    for constraint_node in range_nodes:
                        min_val = constraint_node.get("minInclusive")
                        max_val = constraint_node.get("maxInclusive")
                        if min_val and max_val:
                            constraints.append(f"range: [{min_val}, {max_val}]")
                            
                    # 3. Enumerations
                    enum_values_list = []
                    enum_nodes = type_node.xpath("*[local-name()='enumeration']")
                    if enum_nodes:
                        enum_values_list = [n.get("value") for n in enum_nodes if n.get("value")]
                        if enum_values_list:
                            # if there are too many, truncate for the friendly detailed_type
                            if len(enum_values_list) > 5:
                                constraints.append(f"enum: {', '.join(enum_values_list[:5])} ...")
                            else:
                                constraints.append(f"enum: {', '.join(enum_values_list)}")
                                
                    # 4. Pattern
                    pattern_nodes = type_node.xpath("*[local-name()='pattern']")
                    if pattern_nodes:
                        patterns = [n.get("value") for n in pattern_nodes if n.get("value")]
                        if patterns:
                            constraints.append("pattern")
                            
                    if constraints:
                        detailed_type = f"{data_type} ({'; '.join(constraints)})"
            
            p_node = {
                "name": param_name,
                "node_type": "parameter",
                "access": param_access,
                "description": _get_description(param),
                "data_type": data_type,
                "detailed_type": detailed_type
            }
            if enum_values_list:
                p_node["enum_values"] = enum_values_list
            
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

def generate_netconf_edit_config(target_path: str, value: Any, existing_xml: str = None, list_instances: Any = None) -> str:
    """
    Generates a basic NETCONF <edit-config> XML snippet.
    Appends to existing_xml if provided and valid.
    """
    parts = [p for p in target_path.split(".") if p]
    
    # Process {i} placeholders
    processed_parts = []
    has_instance = False
    for p in parts:
        if p == "{i}":
            has_instance = True
            continue
        processed_parts.append(p)
    parts = processed_parts
    
    if existing_xml:
        try:
            parser_obj = etree.XMLParser(remove_blank_text=True)
            root = etree.fromstring(existing_xml.encode('utf-8'), parser_obj)
            
            nsmap = {"nc": "urn:ietf:params:xml:ns:netconf:base:1.0"}
            config_node = root.xpath(".//nc:config", namespaces=nsmap)
            
            if config_node:
                config = config_node[0]
                current = config
                
                for i, part in enumerate(parts):
                    found = None
                    for child in current:
                        # Comments and ProcessingInstructions have non-string tags
                        if not isinstance(child.tag, str):
                            continue
                        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        if tag == part:
                            found = child
                            break
                            
                    if i == len(parts) - 1:
                        if found is not None:
                            found.text = str(value)
                        else:
                            new_node = etree.SubElement(current, part)
                            new_node.text = str(value)
                            if has_instance:
                                if list_instances is not None and str(list_instances).strip() != "":
                                    # Ensure we don't duplicate the index tag if it's already there
                                    has_idx = False
                                    for sib in current:
                                        if isinstance(sib.tag, str) and sib.tag.endswith("index") and sib.text == str(list_instances):
                                            has_idx = True
                                            break
                                    if not has_idx:
                                        idx_elem = etree.Element("index")
                                        idx_elem.text = str(list_instances)
                                        current.insert(0, idx_elem)
                                else:
                                    new_node.addprevious(etree.Comment(" [Insert Instance Keys Here, e.g. <index>1</index>] "))
                    else:
                        if found is not None:
                            current = found
                        else:
                            current = etree.SubElement(current, part)
                            if has_instance and i == len(parts) - 2:
                                current.append(etree.Comment(" [Insert Instance Keys Here, e.g. <index>1</index>] "))
                
                return etree.tostring(root, pretty_print=True, encoding="UTF-8").decode("utf-8")
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Failed to append to existing XML: {e}")

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
            if has_instance:
                xml_str += f'{indent}<!-- [Insert Instance Keys Here, e.g. <index>1</index>] -->\n'
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
