from fastapi import APIRouter, HTTPException

from app.schemas.interview import ChatResponse, ReportCreateRequest
from app.schemas.report import ReportResponse
from app.services.deepseek_service import DeepSeekAPIError, DeepSeekNotConfiguredError
from app.services.interview_chains import report_chain
from app.services.rag_service import rag_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{interview_id}", response_model=ReportResponse)
def get_report(interview_id: str) -> ReportResponse:
    return ReportResponse(
        interview_id=interview_id,
        summary="MVP 阶段报告占位：后续接入 ReportChain 后生成完整复盘。",
        scores={
            "technical_accuracy": 0,
            "communication": 0,
            "project_depth": 0,
            "position_match": 0,
        },
        recommendations=[],
    )


@router.post("/generate", response_model=ChatResponse)
async def generate_report(request: ReportCreateRequest) -> ChatResponse:
    try:
        rag_context = rag_service.get_document_context(
            document_ids=request.document_ids,
            query=request.conversation,
        )
        content = await report_chain.generate(
            conversation=(
                f"{request.conversation}\n\n候选人资料/RAG 检索结果：\n{rag_context}"
                if rag_context
                else request.conversation
            ),
            position=request.position,
            difficulty=request.difficulty,
        )
    except DeepSeekNotConfiguredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DeepSeekAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(content=content, interview_id=request.interview_id)
