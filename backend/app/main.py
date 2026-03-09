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
    """Retrieves the parsed hierarchical JSON for a given XML model name."""
    try:
        data = parser.parse_xml_to_dict(model_name)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/netconf/edit-config", response_model=models.EditMessageResponse)
def create_netconf_edit(payload: models.EditMessageRequest):
    """Generates a generic NETCONF edit-config fragment for the edited target paths."""
    xml_str = parser.generate_netconf_edit_config(payload.target_path, payload.value)
    return models.EditMessageResponse(xml_payload=xml_str)

