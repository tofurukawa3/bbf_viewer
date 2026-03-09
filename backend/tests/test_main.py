from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_get_models():
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    # At minimum we expect tr-181, 196, 262
    assert any("tr-181" in m for m in data["models"])

def test_get_specific_model():
    # Attempt to load a known model
    response = client.get("/models")
    models = response.json().get("models", [])
    if not models:
        pytest.skip("No models found to test")
    
    first_model = models[0]
    response = client.get(f"/models/{first_model}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Root"
    assert "children" in data

def test_edit_config():
    # Minimal payload for editing a known object that theoretically exists
    payload = {
        "model_name": "tr-262-1-0-0.xml",
        "target_path": "FAP.FAP.GPS.ScanOnBoot",
        "value": "false"
    }
    response = client.post("/netconf/edit-config", json=payload)
    if response.status_code == 404:
        pytest.skip("tr-262 model not found locally during test")
        
    assert response.status_code == 200
    data = response.json()
    assert "xml_payload" in data
    assert "<edit-config>" in data["xml_payload"]
    assert "<ScanOnBoot>false</ScanOnBoot>" in data["xml_payload"]
