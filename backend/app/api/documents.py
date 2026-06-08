from fastapi import APIRouter, HTTPException, UploadFile

from app.schemas.document import (
    DocumentUploadResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
)
from app.services.rag_service import rag_service

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
SUPPORTED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def _validate_upload(file: UploadFile, content: bytes) -> None:
    filename = (file.filename or "").lower()
    has_supported_extension = any(filename.endswith(extension) for extension in SUPPORTED_EXTENSIONS)
    has_supported_content_type = file.content_type in SUPPORTED_CONTENT_TYPES
    if not has_supported_extension and not has_supported_content_type:
        raise HTTPException(status_code=400, detail="仅支持 txt、md、pdf、docx 类型资料上传。")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="上传文件不能超过 2MB。")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile) -> DocumentUploadResponse:
    content = await file.read()
    _validate_upload(file, content)
    result = rag_service.ingest_document(
        content=content,
        filename=file.filename or "untitled",
        content_type=file.content_type,
    )
    return DocumentUploadResponse.model_validate(result)


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_documents(request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    results = rag_service.search(request.query, limit=request.limit, document_ids=request.document_ids)
    return KnowledgeSearchResponse(
        query=request.query,
        results=[
            KnowledgeSearchResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                text=result.text,
                score=result.score,
                metadata=result.metadata,
            )
            for result in results
        ],
    )
