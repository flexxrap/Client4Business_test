from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ApprovalStatus, SourceType


class ApprovalRequestCreate(BaseModel):
    source_type: SourceType
    source_id: str
    title: str
    description: str | None = None
    reviewer_user_ids: list[str] = Field(default_factory=list)


class ApprovalRequestResponse(BaseModel):
    id: str
    workspace_id: str
    source_type: SourceType
    source_id: str
    title: str
    description: str | None
    reviewer_user_ids: list[str]
    status: ApprovalStatus
    created_by: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRequestListResponse(BaseModel):
    items: list[ApprovalRequestResponse]
    limit: int
    offset: int
    total: int


class ApproveRequestBody(BaseModel):
    comment: str | None = None


class RejectRequestBody(BaseModel):
    reason: str | None = None


class CancelRequestBody(BaseModel):
    reason: str | None = None
