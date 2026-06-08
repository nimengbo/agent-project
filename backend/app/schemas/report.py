from pydantic import BaseModel


class ReportResponse(BaseModel):
    interview_id: str
    summary: str
    scores: dict[str, int]
    recommendations: list[str]
