from pydantic import BaseModel
from typing import List, Optional, Any

class DataModelNode(BaseModel):
    name: str # Parameter or Object name
    node_type: str # "object" or "parameter"
    access: str # e.g. "readWrite", "readOnly"
    description: Optional[str] = None
    data_type: Optional[str] = None # e.g. "string", "unsignedInt" (only for parameters)
    children: Optional[List['DataModelNode']] = None

class ModelListResponse(BaseModel):
    models: List[str]

class EditMessageRequest(BaseModel):
    model_name: str
    target_path: str
    value: Any

class EditMessageResponse(BaseModel):
    xml_payload: str
