import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DecisionAction


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("approval_requests.id"), nullable=False, index=True
    )
    action: Mapped[DecisionAction] = mapped_column(
        Enum(DecisionAction, native_enum=False, length=32), nullable=False
    )
    actor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    request: Mapped["ApprovalRequest"] = relationship(back_populates="decisions")
