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

    # TR-106 Global DataType Parsing
    global_datatypes = {}
    for dt_elem in get_elements_by_local_name(root, "dataType"):
        dt_name = dt_elem.get("name")
        if not dt_name: # skip inner <dataType ref="...">
            continue
            
        dt_base = dt_elem.get("base")
        underlying_type = None
        constraints = []
        for child in dt_elem:
            c_tag = etree.QName(child).localname
            if c_tag in ["string", "unsignedInt", "int", "boolean", "dateTime", "base64", "hexBinary", "list", "unsignedLong", "long"]:
                underlying_type = c_tag
                for grand_child in child:
                    gc_tag = etree.QName(grand_child).localname
                    if gc_tag == "size":
                        max_len = grand_child.get("maxLength")
                        min_len = grand_child.get("minLength")
                        if max_len and min_len:
                            constraints.append(f"length: {min_len}-{max_len}")
                        elif max_len:
                            constraints.append(f"max_length: {max_len}")
                    elif gc_tag == "range":
                        min_val = grand_child.get("minInclusive")
                        max_val = grand_child.get("maxInclusive")
                        if min_val and max_val:
                            constraints.append(f"range: [{min_val}, {max_val}]")
                    elif gc_tag == "enumeration":
                        val = grand_child.get("value")
                        if val:
                            constraints.append(val)
                    elif gc_tag == "pattern":
                        val = grand_child.get("value")
                        if val:
                            constraints.append(f"pattern {val}")
                        
        global_datatypes[dt_name] = {
            "name": dt_name,
            "base": dt_base,
            "underlying_type": underlying_type,
            "constraints": constraints
        }
        
    # Resolve bases
    for _ in range(3):
        for dt_name, dt_info in global_datatypes.items():
            if dt_info["base"] and dt_info["base"] in global_datatypes:
                base_info = global_datatypes[dt_info["base"]]
                if dt_info["underlying_type"] is None:
                    dt_info["underlying_type"] = base_info["underlying_type"]
                # append base constraints before local constraints
                # Use a new list to prevent accumulating wildly in place
                combined_constraints = list(dict.fromkeys(base_info["constraints"] + dt_info["constraints"]))
                dt_info["constraints"] = combined_constraints
                dt_info["base"] = base_info["base"]

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
            default_value = ""
            data_type = "string"
            detailed_type = ""
            
            if syntax_elem is not None:
                default_elem = syntax_elem.find("{*}default")
                if default_elem is not None:
                    default_value = default_elem.get("value", "")
                    
                type_kids = [c for c in syntax_elem if etree.QName(c).localname != "default"]
                if type_kids:
                    type_elem = type_kids[0]
                    type_tag = etree.QName(type_elem).localname
                    constraints = []
                    
                    if type_tag == "dataType":
                         ref = type_elem.get("ref", "")
                         if ref and ref in global_datatypes:
                             dt_info = global_datatypes[ref]
                             data_type = dt_info["underlying_type"] or "string"
                             constraints = dt_info["constraints"].copy()
                             detailed_type = f"[{ref}]"
                         elif ref:
                             detailed_type = f"Resolved from {ref}"
                             data_type = "string"
                    elif type_tag == "list":
                         data_type = "string"
                         detailed_type = "Comma-separated list"
                    else:
                         data_type = type_tag # boolean, string, unsignedInt, dateTime
                         
                    # Check for constraints on parameter itself
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
                    
                    enums = []
                    other_constraints = []
                    for c in constraints:
                         if not c.startswith("length:") and not c.startswith("max_length:") and not c.startswith("range:") and not c.startswith("pattern "):
                             if c not in enums:
                                 enums.append(c)
                         else:
                             if c not in other_constraints:
                                 other_constraints.append(c)
                    
                    details_parts = []
                    if detailed_type:
                        details_parts.append(detailed_type)
                    if enums:
                        details_parts.append("enum: " + ", ".join(enums))
                    if other_constraints:
                        details_parts.append(" | ".join(other_constraints))
                        
                    detailed_type = " | ".join(details_parts) if details_parts else ""

            param_node = {
                "name": p_name,
                "node_type": "parameter",
                "access": p_access,
                "data_type": data_type,
                "detailed_type": detailed_type,
                "enum_values": enums if 'enums' in locals() else [],
                "default_value": default_value,
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

def _map_datatype_to_xsd(datatype: str) -> str:
    """Helper to map BBF data types to xsd types for xsi:type."""
    dt = (datatype or "string").lower()
    if dt == "boolean":
        return "xsd:boolean"
    elif dt == "unsignedint":
        return "xsd:unsignedInt"
    elif dt == "int":
        return "xsd:int"
    elif dt == "datetime":
        return "xsd:dateTime"
    elif dt == "base64":
        return "xsd:base64Binary"
    else:
        return "xsd:string"

def generate_cwmp_set_parameter_values(target_path: str, value: Any, datatype: str = "string", existing_xml: str = None, list_instances: Any = None) -> str:
    """
    Generates a CWMP SetParameterValues SOAP 1.1 XML snippet.
    Appends the new ParameterValueStruct to existing_xml if provided.
    Properly handles inserting list_instances into the path e.g. `{i}` -> `1`.
    """
    # Replace {i} with the actual instance number if provided
    actual_path = target_path
    if "{i}" in actual_path:
        if list_instances is not None and str(list_instances).strip():
            actual_path = actual_path.replace("{i}", str(list_instances))
        else:
            # Leave a placeholder if missing
            actual_path = actual_path.replace("{i}", "[INSERT_INSTANCE_INDEX]")
            
    # Ensure parameter path ends appropriately (mostly they don't have trailing dot for parameters, but BBF paths might just be correct as passed)

    xsd_type = _map_datatype_to_xsd(datatype)

    SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
    SOAP_ENC = "http://schemas.xmlsoap.org/soap/encoding/"
    XSD = "http://www.w3.org/2001/XMLSchema"
    XSI = "http://www.w3.org/2001/XMLSchema-instance"
    CWMP = "urn:dslforum-org:cwmp-1-0"

    nsmap = {
        "soapenv": SOAP_ENV,
        "soapenc": SOAP_ENC,
        "xsd": XSD,
        "xsi": XSI,
        "cwmp": CWMP
    }

    if existing_xml:
        try:
            parser_obj = etree.XMLParser(remove_blank_text=True)
            root = etree.fromstring(existing_xml.encode('utf-8'), parser_obj)
            
            # Find the ParameterList node
            param_list_nodes = root.xpath(".//ParameterList")
            
            if param_list_nodes:
                param_list = param_list_nodes[0]
                
                # Check if this parameter already exists, if so, update its Value
                existing_param = None
                for param_struct in param_list.findall("ParameterValueStruct"):
                    name_node = param_struct.find("Name")
                    if name_node is not None and name_node.text == actual_path:
                        existing_param = param_struct
                        break
                        
                if existing_param is not None:
                    value_node = existing_param.find("Value")
                    if value_node is not None:
                        value_node.text = str(value)
                        # Optionally update xsi:type here, but might just leave it
                else:
                    # Append new ParameterValueStruct
                    struct = etree.SubElement(param_list, "ParameterValueStruct")
                    name_elem = etree.SubElement(struct, "Name")
                    name_elem.text = actual_path
                    val_elem = etree.SubElement(struct, "Value")
                    # setting xsi:type
                    val_elem.set(f"{{{XSI}}}type", xsd_type)
                    val_elem.text = str(value)
                    
                    # Update arrayType count
                    current_count = len(param_list.findall("ParameterValueStruct"))
                    param_list.set(f"{{{SOAP_ENC}}}arrayType", f"cwmp:ParameterValueStruct[{current_count}]")
                
                return etree.tostring(root, pretty_print=True, encoding="UTF-8").decode("utf-8")
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Failed to append to existing CWMP XML: {e}")

    # Generate a new envelope from scratch
    root = etree.Element(f"{{{SOAP_ENV}}}Envelope", nsmap=nsmap)
    header = etree.SubElement(root, f"{{{SOAP_ENV}}}Header")
    cwmp_id = etree.SubElement(header, f"{{{CWMP}}}ID")
    cwmp_id.set(f"{{{SOAP_ENV}}}mustUnderstand", "1")
    cwmp_id.text = "1"
    
    body = etree.SubElement(root, f"{{{SOAP_ENV}}}Body")
    spv = etree.SubElement(body, f"{{{CWMP}}}SetParameterValues")
    
    param_list = etree.SubElement(spv, "ParameterList")
    param_list.set(f"{{{SOAP_ENC}}}arrayType", "cwmp:ParameterValueStruct[1]")
    
    struct = etree.SubElement(param_list, "ParameterValueStruct")
    name_elem = etree.SubElement(struct, "Name")
    name_elem.text = actual_path
    
    val_elem = etree.SubElement(struct, "Value")
    val_elem.set(f"{{{XSI}}}type", xsd_type)
    val_elem.text = str(value)
    
    param_key = etree.SubElement(spv, "ParameterKey")
    param_key.text = "Update"
    
    return etree.tostring(root, pretty_print=True, encoding="UTF-8", xml_declaration=True).decode("utf-8")
