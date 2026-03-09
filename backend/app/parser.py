import os
from lxml import etree
import logging
from typing import Any
import functools

logger = logging.getLogger(__name__)

# Data dir path relative to this backend module
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cwmp-data-models")
TARGET_PREFIXES = ["tr-181", "tr-196", "tr-262"]

@functools.lru_cache(maxsize=1)
def get_available_models():
    """Returns a list of available CWMP full XML models from the cwmp-data-models directory.
    Only returns the latest version of each TR number."""
    if not os.path.exists(DATA_DIR):
        return []
    
    latest_models = {}
    
    for f in os.listdir(DATA_DIR):
        # We target all XML files, but assign a priority weight to prefer 'full' models
        if f.endswith(".xml") and any(f.startswith(prefix) for prefix in TARGET_PREFIXES):
            # enforce -full.xml unless it's tr-262 which lacks one
            if not f.endswith("-full.xml") and not f.startswith("tr-262"):
                continue
                
            parts = f.split('-')
            if len(parts) >= 3 and parts[0] == 'tr':
                prefix = f"tr-{parts[1]}"
                
                # Extract version digits
                version_parts = []
                for p in parts[2:]:
                    if p.isdigit():
                        version_parts.append(int(p))
                    else:
                        break
                version_tuple = tuple(version_parts)
                
                # Priority: full > cwmp > others
                priority = 2 if "full.xml" in f else (1 if "cwmp.xml" in f else 0)
                cmp_key = (version_tuple, priority)
                
                # Keep the one with the highest version tuple, preferring full.xml if equal
                if prefix not in latest_models or cmp_key > latest_models[prefix][0]:
                    latest_models[prefix] = (cmp_key, f)
                    
    # Return just the filenames, sorted alphabetically
    return sorted([v[1] for v in latest_models.values()])

def _find_xml_file(model_name: str) -> str:
    path = os.path.join(DATA_DIR, model_name)
    if os.path.exists(path):
        return path
    return None

@functools.lru_cache(maxsize=10)
def parse_xml_to_dict(model_name: str) -> dict:
    file_path = _find_xml_file(model_name)
    if not file_path:
        raise FileNotFoundError(f"XML file not found for {model_name}")

    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        logger.error(f"Failed to parse XML: {e}")
        return None

    def get_elements_by_local_name(node, local_name):
        return list(node.iter(f"{{*}}{local_name}"))

    objects = get_elements_by_local_name(root, "object")

    # Create a virtual Root node
    root_json = {
        "name": "/",
        "node_type": "object",
        "access": "readOnly",
        "description": f"Root node for {model_name}",
        "children": []
    }

    # Helper to map CWMP paths (e.g., Device.DeviceInfo.) to the hierarchical JSON
    nodes_map = {"": root_json} # Map of path -> node

    for obj in objects:
        obj_name = obj.get("name", "")
        if not obj_name:
            continue
            
        access = obj.get("access", "readOnly")
        
        # safely extract description using wildcard namespace
        description = ""
        desc_elem = obj.find("{*}description")
        if desc_elem is not None and desc_elem.text:
            description = desc_elem.text.strip()

        # Normalize paths. In BBF, objects end with "." (e.g. Device.)
        is_list = "{i}" in obj_name
        # Remove trailing dot for the standard node name mapping
        clean_name = obj_name.rstrip(".")
        
        parts = clean_name.split(".")
        name = parts[-1]

        node = {
            "name": name,
            "node_type": "object",
            "access": "readWrite" if is_list else access,
            "detailed_type": "List" if is_list else "",
            "description": description,
            "children": []
        }

        # Ensure parent exists in our map, string it together
        current_path_builder = ""
        last_parent = root_json
        
        for p in parts[:-1]:
            current_path_builder += p
            if current_path_builder not in nodes_map:
                # Create intermediate missing node
                intermediate = {
                    "name": p,
                    "node_type": "object",
                    "access": "readOnly",
                    "description": "",
                    "children": []
                }
                last_parent["children"].append(intermediate)
                nodes_map[current_path_builder] = intermediate
            last_parent = nodes_map[current_path_builder]
            current_path_builder += "."

        # Link this object node
        nodes_map[clean_name] = node
        last_parent["children"].append(node)

        # Now parse its parameters
        params = get_elements_by_local_name(obj, "parameter")
        for p in params:
            p_name = p.get("name", "")
            p_access = p.get("access", "readOnly")
            
            p_desc = ""
            desc_elem = p.find("{*}description")
            if desc_elem is not None and desc_elem.text:
                p_desc = desc_elem.text.strip()
                
            syntax_elem = p.find("{*}syntax")
            
            # Syntax extraction
            data_type = "string"
            detailed_type = ""
            
            if syntax_elem is not None:
                # E.g. <string>, <unsignedInt>, <list>, <boolean>, <dataType>
                type_kids = list(syntax_elem)
                if type_kids:
                    type_elem = type_kids[0]
                    type_tag = etree.QName(type_elem).localname
                    if type_tag == "dataType":
                         ref = type_elem.get("ref", "")
                         if ref:
                             detailed_type = f"Resolved from {ref}"
                             data_type = "string" # Fallback mapping
                    elif type_tag == "list":
                         data_type = "string"
                         detailed_type = "Comma-separated list"
                    else:
                         data_type = type_tag # boolean, string, unsignedInt, dateTime
                         
                    # Check for constraints
                    constraints = []
                    for child in type_elem:
                        c_tag = etree.QName(child).localname
                        if c_tag == "size":
                            max_len = child.get("maxLength")
                            min_len = child.get("minLength")
                            if max_len and min_len:
                                constraints.append(f"length: {min_len}-{max_len}")
                            elif max_len:
                                constraints.append(f"max_length: {max_len}")
                        elif c_tag == "range":
                            min_val = child.get("minInclusive")
                            max_val = child.get("maxInclusive")
                            if min_val and max_val:
                                constraints.append(f"range: [{min_val}, {max_val}]")
                        elif c_tag == "enumeration":
                            val = child.get("value")
                            if val:
                                constraints.append(val)
                        elif c_tag == "pattern":
                            val = child.get("value")
                            if val:
                                constraints.append(f"pattern {val}")
                    
                    # If we found enumerations, group them
                    enums = [c for c in constraints if not c.startswith("length:") and not c.startswith("max_length:") and not c.startswith("range:") and not c.startswith("pattern ")]
                    other_constraints = [c for c in constraints if c not in enums]
                    
                    if enums:
                        detailed_type = "enum: " + ", ".join(enums)
                        if other_constraints:
                            detailed_type += " | " + " | ".join(other_constraints)
                    elif other_constraints:
                        detailed_type = " | ".join(other_constraints)

            param_node = {
                "name": p_name,
                "node_type": "parameter",
                "access": p_access,
                "data_type": data_type,
                "detailed_type": detailed_type,
                "description": p_desc
            }
            node["children"].append(param_node)

    return root_json

def get_unified_tree() -> dict:
    """Parses all available model files and unifies them under a single virtual Root."""
    models = get_available_models()
    root_node = {
        "name": "Root",
        "node_type": "object",
        "access": "readOnly",
        "description": "Unified view of all available BBF CWMP Models",
        "children": []
    }
    
    for m in models:
        try:
            data = parse_xml_to_dict(m)
            # data is the module node, we can append it directly
            root_node["children"].append(data)
        except Exception as e:
            logger.warning(f"Skipping {m} in unified tree due to error: {e}")
            
    return root_node

def generate_netconf_edit_config(target_path: str, value: Any, existing_xml: str = None, list_instances: Any = None) -> str:
    """
    Generates a basic NETCONF <edit-config> XML snippet.
    Appends to existing_xml if provided and valid.
    Properly handles multiple instances if index matches or diverges.
    """
    parts_raw = [p for p in target_path.split(".") if p]
    
    # Process {i} placeholders and remember which parts are lists
    parts = []
    list_node_indices = set()
    
    for p in parts_raw:
        if p == "{i}":
            if len(parts) > 0:
                list_node_indices.add(len(parts) - 1)
            continue
        parts.append(p)
        
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
                    is_list_node = (i in list_node_indices)
                    
                    for child in current:
                        if not isinstance(child.tag, str):
                            continue
                        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        
                        if tag == part:
                            # If this is a list node, ensure we only match if the index equals our list_instances
                            if is_list_node and list_instances is not None and str(list_instances).strip():
                                index_match = False
                                for sib in child:
                                    if isinstance(sib.tag, str) and sib.tag.endswith("index") and sib.text == str(list_instances):
                                        index_match = True
                                        break
                                if index_match:
                                    found = child
                                    break
                            else:
                                found = child
                                break
                                
                    if i == len(parts) - 1:
                        if found is not None:
                            found.text = str(value)
                        else:
                            new_node = etree.SubElement(current, part)
                            new_node.text = str(value)
                            # Note: The target_path for a parameter typically shouldn't end with `{i}` so it wouldn't be a list node
                    else:
                        if found is not None:
                            current = found
                        else:
                            current = etree.SubElement(current, part)
                            if is_list_node:
                                if list_instances is not None and str(list_instances).strip():
                                    idx_elem = etree.Element("index")
                                    idx_elem.text = str(list_instances)
                                    current.insert(0, idx_elem)
                                else:
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
        is_list_node = (i in list_node_indices)
        if i == len(parts) - 1:
            xml_str += f'{indent}<{part}>{value}</{part}>\n'
        else:
            xml_str += f'{indent}<{part}>\n'
            if is_list_node:
                if list_instances is not None and str(list_instances).strip():
                    xml_str += f'{indent}  <index>{list_instances}</index>\n'
                else:
                    xml_str += f'{indent}  <!-- [Insert Instance Keys Here, e.g. <index>1</index>] -->\n'
            closing_tags.insert(0, part)
            indent += "  "
            
    for tag in closing_tags:
        indent = indent[:-2]
        xml_str += f'{indent}</{tag}>\n'
        
    xml_str += '    </config>\n'
    xml_str += '  </edit-config>\n'
    xml_str += '</rpc>'
    
    return xml_str
