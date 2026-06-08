from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, InterviewStage, TimestampMixin, new_id


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(128), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(64), default="senior", nullable=False)
    stage: Mapped[str] = mapped_column(String(64), default=InterviewStage.self_intro.value, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
