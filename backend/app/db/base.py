from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InterviewStage(str, Enum):
    self_intro = "SELF_INTRO"
    project_deep_dive = "PROJECT_DEEP_DIVE"
    technical_question = "TECHNICAL_QUESTION"
    follow_up = "FOLLOW_UP"
    summary = "SUMMARY"


class MessageRole(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


def new_id() -> str:
    return uuid4().hex


def utc_now() -> datetime:
    return datetime.utcnow()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
