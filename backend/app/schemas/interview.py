from pydantic import BaseModel, Field


class InterviewCreateRequest(BaseModel):
    title: str
    position: str
    difficulty: str = "senior"


class InterviewResponse(BaseModel):
    id: str
    title: str
    position: str
    difficulty: str
    stage: str
    status: str


class ChatRequest(BaseModel):
    content: str
    position: str = "移动端架构师"
    difficulty: str = "senior"
    interview_id: str | None = None
    candidate_profile: str = "暂无"
    conversation: str = "暂无"
    document_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    content: str
    interview_id: str | None = None


class FollowupRequest(BaseModel):
    question: str
    answer: str
    position: str = "移动端架构师"
    difficulty: str = "senior"
    interview_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)


class AnswerReviewRequest(BaseModel):
    question: str
    answer: str
    position: str = "移动端架构师"
    difficulty: str = "senior"
    interview_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)


class ReportCreateRequest(BaseModel):
    conversation: str
    position: str = "移动端架构师"
    difficulty: str = "senior"
    interview_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
