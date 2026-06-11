from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.db.base import InterviewStage
from app.schemas.interview import (
    AnswerReviewRequest,
    ChatRequest,
    ChatResponse,
    FollowupRequest,
    InterviewFinishResponse,
    InterviewCreateRequest,
    InterviewResponse,
)
from app.services.deepseek_service import DeepSeekAPIError, DeepSeekNotConfiguredError
from app.services.interview_chains import answer_review_chain, followup_chain, question_chain
from app.services.rag_service import rag_service

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _extract_asked_questions(conversation: str) -> str:
    questions: list[str] = []
    for raw_line in conversation.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("面试官：", "面试官:", "assistant：", "assistant:")) and ("?" in line or "？" in line):
            question = line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1]
            questions.append(question.strip())
    return "\n".join(f"- {question}" for question in questions) or "暂无"


def _build_candidate_profile(base_profile: str, document_ids: list[str], query: str) -> str:
    rag_context = rag_service.get_document_context(document_ids=document_ids, query=query)
    parts = [base_profile if base_profile and base_profile != "暂无" else ""]
    if rag_context:
        parts.append(f"候选人资料/RAG 检索结果：\n{rag_context}")
    return "\n\n".join(part for part in parts if part).strip() or "暂无"


@router.post("", response_model=InterviewResponse)
def create_interview(request: InterviewCreateRequest) -> InterviewResponse:
    return InterviewResponse(
        id=uuid4().hex,
        title=request.title,
        position=request.position,
        difficulty=request.difficulty,
        stage=InterviewStage.self_intro.value,
        status="active",
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        rag_query = request.content.strip()
        control_intents = {"继续", "下一题", "跳过", "换一个", "next", "skip"}
        if rag_query.lower() in control_intents:
            conversation_lines = [
                line.strip()
                for line in request.conversation.splitlines()
                if line.strip() and rag_query.lower() not in line.lower()
            ]
            rag_query = "\n".join(conversation_lines[-4:]) or request.content
        content = await question_chain.generate(
            content=request.content,
            position=request.position,
            difficulty=request.difficulty,
            candidate_profile=_build_candidate_profile(request.candidate_profile, request.document_ids, rag_query),
            conversation=request.conversation,
            asked_questions=_extract_asked_questions(request.conversation),
        )
    except DeepSeekNotConfiguredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DeepSeekAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(content=content, interview_id=request.interview_id)


@router.post("/{interview_id}/finish", response_model=InterviewFinishResponse)
def finish_interview(interview_id: str) -> InterviewFinishResponse:
    return InterviewFinishResponse(
        interview_id=interview_id,
        stage=InterviewStage.summary.value,
        status="finished",
        message="面试已结束，可以生成复盘报告。",
    )


@router.post("/followup", response_model=ChatResponse)
async def followup(request: FollowupRequest) -> ChatResponse:
    try:
        content = await followup_chain.generate(
            question=request.question,
            answer=request.answer,
            position=request.position,
            difficulty=request.difficulty,
            candidate_profile=_build_candidate_profile("", request.document_ids, f"{request.question}\n{request.answer}"),
        )
    except DeepSeekNotConfiguredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DeepSeekAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(content=content, interview_id=request.interview_id)


@router.post("/review", response_model=ChatResponse)
async def review_answer(request: AnswerReviewRequest) -> ChatResponse:
    try:
        content = await answer_review_chain.review(
            question=request.question,
            answer=request.answer,
            position=request.position,
            difficulty=request.difficulty,
            candidate_profile=_build_candidate_profile("", request.document_ids, f"{request.question}\n{request.answer}"),
        )
    except DeepSeekNotConfiguredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DeepSeekAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(content=content, interview_id=request.interview_id)
