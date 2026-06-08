from pathlib import Path

from fastapi.testclient import TestClient

from app.api import config as config_api
from app.main import app
from app.services import deepseek_service as deepseek_service_module
from app.services.model_config_service import ModelConfigService

client = TestClient(app)


def test_health_smoke_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_config_smoke_masks_api_key(monkeypatch, tmp_path: Path):
    service = ModelConfigService(str(tmp_path / "model_config.json"))
    monkeypatch.setattr(config_api, "model_config_service", service)

    save_response = client.post(
        "/api/config/model",
        json={
            "api_key": "local-test-secret-1234567890",
            "base_url": "https://api.deepseek.com",
            "chat_model": "deepseek-chat",
            "reasoner_model": "deepseek-reasoner",
        },
    )
    load_response = client.get("/api/config/model")

    assert save_response.status_code == 200
    assert save_response.json()["configured"] is True
    assert save_response.json()["api_key_preview"] == "loca...7890"
    assert "local-test-secret-1234567890" not in save_response.text
    assert load_response.status_code == 200
    assert load_response.json()["api_key_preview"] == "loca...7890"
    assert "local-test-secret-1234567890" not in load_response.text


def test_document_upload_and_search_smoke_returns_matching_chunk():
    upload_response = client.post(
        "/api/documents/upload",
        files={"file": ("resume.md", "候选人擅长 Android 性能优化和 Flutter 架构", "text/markdown")},
    )

    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    search_response = client.post(
        "/api/documents/search",
        json={"query": "Flutter 架构", "document_ids": [document_id], "limit": 3},
    )

    assert search_response.status_code == 200
    results = search_response.json()["results"]
    assert len(results) >= 1
    assert results[0]["document_id"] == document_id
    assert "Flutter 架构" in results[0]["text"]


def test_chat_without_api_key_returns_config_error(monkeypatch, tmp_path: Path):
    empty_service = ModelConfigService(str(tmp_path / "missing_model_config.json"))
    monkeypatch.setattr(deepseek_service_module.model_config_service, "load", empty_service.load)

    response = client.post("/api/interviews/chat", json={"content": "请开始面试"})

    assert response.status_code == 400
    assert "API Key 未配置" in response.json()["detail"]


def test_report_generate_without_api_key_returns_config_error(monkeypatch, tmp_path: Path):
    empty_service = ModelConfigService(str(tmp_path / "missing_model_config.json"))
    monkeypatch.setattr(deepseek_service_module.model_config_service, "load", empty_service.load)

    response = client.post(
        "/api/reports/generate",
        json={"interview_id": "local-demo", "conversation": "问：A\n答：B"},
    )

    assert response.status_code == 400
    assert "API Key 未配置" in response.json()["detail"]
