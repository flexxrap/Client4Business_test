import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApprovalStatus, SourceType


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "idempotency_key", name="uq_workspace_idempotency_key"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False, length=32), nullable=False
    )
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewer_user_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, native_enum=False, length=32),
        nullable=False,
        default=ApprovalStatus.PENDING,
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    decisions: Mapped[list["ApprovalDecision"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
