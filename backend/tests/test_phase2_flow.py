from fastapi.testclient import TestClient

from app.api import interviews, reports
from app.main import app

client = TestClient(app)


def test_chat_includes_uploaded_document_context(monkeypatch):
    captured = {}

    async def fake_generate(**kwargs):
        captured.update(kwargs)
        return "下一题"

    monkeypatch.setattr(interviews.question_chain, "generate", fake_generate)

    upload = client.post(
        "/api/documents/upload",
        files={"file": ("resume.txt", "候选人有 Flutter 架构治理经验", "text/plain")},
    )
    document_id = upload.json()["document_id"]

    response = client.post(
        "/api/interviews/chat",
        json={
            "content": "请开始面试",
            "conversation": "候选人：你好",
            "document_ids": [document_id],
        },
    )

    assert response.status_code == 200
    assert "Flutter 架构治理" in captured["candidate_profile"]
    assert "候选人：你好" in captured["conversation"]


def test_upload_rejects_unsupported_file_type():
    response = client.post(
        "/api/documents/upload",
        files={"file": ("resume.png", b"not text", "image/png")},
    )

    assert response.status_code == 400
    assert "仅支持" in response.json()["detail"]


def test_generate_report_uses_conversation_payload(monkeypatch):
    captured = {}

    async def fake_generate(**kwargs):
        captured.update(kwargs)
        return "完整报告"

    monkeypatch.setattr(reports.report_chain, "generate", fake_generate)

    response = client.post(
        "/api/reports/generate",
        json={"interview_id": "local-demo", "conversation": "问：A\n答：B"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "完整报告"
    assert captured["conversation"] == "问：A\n答：B"
