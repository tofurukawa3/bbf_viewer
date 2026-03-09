from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import models, parser

app = FastAPI(title="BBF DataModel Viewer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/models", response_model=models.ModelListResponse)
def list_models():
    """Lists available BBF Data models from the local data directory."""
    available = parser.get_available_models()
    return models.ModelListResponse(models=available)

@app.get("/models/{model_name}")
def get_model(model_name: str):
    """Retrieves the parsed hierarchical JSON for a given YANG model name. Or 'unified' to get all."""
    try:
        if model_name == "unified":
            # We no longer support unified virtual root for the massive CWMP XML files,
            # but keep the endpoint name for frontend compatibility if needed.
            # However, now we expect the frontend to query specific files again.
            return parser.parse_xml_to_dict("tr-181-2-16-0-cwmp-full.xml")

        # If the user requests a specific model
        data = parser.parse_xml_to_dict(model_name)
        if data is None:
            raise HTTPException(status_code=404, detail="Model file not found or failed to parse")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/netconf/edit-config", response_model=models.EditMessageResponse)
def create_netconf_edit(payload: models.EditMessageRequest):
    """Generates a generic NETCONF edit-config fragment for the edited target paths."""
    xml_str = parser.generate_netconf_edit_config(
        payload.target_path, 
        payload.value, 
        payload.existing_xml,
        payload.list_instances
    )
    return models.EditMessageResponse(xml_payload=xml_str)
