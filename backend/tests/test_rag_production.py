from __future__ import annotations

import io

import pytest

from app.services.rag_service import (
    DocumentParser,
    HashingEmbeddingProvider,
    QdrantVectorStore,
    RagKnowledgeBaseService,
)


def test_docx_parser_extracts_paragraph_and_table_text():
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_paragraph("候选人擅长 Flutter 架构治理")
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "Android 性能优化"
    buffer = io.BytesIO()
    document.save(buffer)

    parsed = DocumentParser().parse(
        buffer.getvalue(),
        filename="resume.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert parsed.metadata["parser"] == "docx"
    assert "Flutter 架构治理" in parsed.text
    assert "Android 性能优化" in parsed.text


def test_pdf_parser_extracts_page_text():
    pytest.importorskip("pypdf")
    content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 64 >>
stream
BT /F1 18 Tf 72 720 Td (Candidate has RAG production experience) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000241 00000 n 
0000000311 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
425
%%EOF
"""

    parsed = DocumentParser().parse(content, filename="resume.pdf", content_type="application/pdf")

    assert parsed.metadata["parser"] == "pdf"
    assert "RAG production experience" in parsed.text


def test_qdrant_store_persists_chunks_across_service_instances(monkeypatch, tmp_path):
    pytest.importorskip("qdrant_client")
    monkeypatch.setattr("app.services.rag_service.settings.rag_use_qdrant", True)
    monkeypatch.setattr("app.services.rag_service.settings.qdrant_path", str(tmp_path / "qdrant"))
    monkeypatch.setattr("app.services.rag_service.settings.rag_collection_name", "test_interview_knowledge")
    monkeypatch.setattr("app.services.rag_service.settings.rag_embedding_provider", "hashing")
    monkeypatch.setattr("app.services.rag_service.settings.rag_embedding_dimension", 128)
    monkeypatch.setattr("app.services.rag_service.settings.rag_allow_memory_fallback", False)

    first = RagKnowledgeBaseService()
    ingest = first.ingest_document(
        b"Flutter architecture and Android performance optimization",
        filename="resume.txt",
        content_type="text/plain",
    )
    second = RagKnowledgeBaseService()
    results = second.search("Flutter architecture", document_ids=[ingest["document_id"]], limit=3)

    assert isinstance(second.vector_store, QdrantVectorStore)
    assert ingest["metadata"]["vector_store"] == "qdrant"
    assert ingest["metadata"]["embedding_provider"] == "hashing"
    assert results
    assert results[0].document_id == ingest["document_id"]


def test_embedding_provider_reports_consistent_dimension():
    provider = HashingEmbeddingProvider(dimension=64)

    embeddings = provider.embed_many(["Flutter 架构", "Android 性能"])

    assert provider.provider_name == "hashing"
    assert len(embeddings) == 2
    assert all(len(embedding) == 64 for embedding in embeddings)
