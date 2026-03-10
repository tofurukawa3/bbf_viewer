from pydantic import BaseModel
from typing import List, Optional, Any

class DataModelNode(BaseModel):
    name: str # Parameter or Object name
    node_type: str # "object" or "parameter"
    access: str # e.g. "readWrite", "readOnly"
    description: Optional[str] = None
    data_type: Optional[str] = None # e.g. "string", "unsignedInt" (only for parameters)
    detailed_type: Optional[str] = None # e.g., "string (max: 64)", "enum: Up, Down"
    enum_values: Optional[List[str]] = None
    default_value: Optional[str] = None
    children: Optional[List['DataModelNode']] = None

class ModelListResponse(BaseModel):
    models: List[str]

class EditMessageRequest(BaseModel):
    model_name: str
    target_path: str
    value: Any
    datatype: Optional[str] = "string" # Used for xsi:type in CWMP
    existing_xml: Optional[str] = None
    list_instances: Optional[Any] = None # e.g. list of {"i": "1"} strings or something, let's just make it Any or List[str]

class EditMessageResponse(BaseModel):
    xml_payload: str
