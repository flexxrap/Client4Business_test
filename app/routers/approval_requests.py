from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import AuthContext
from app.middleware.dependencies import require_action
from app.models.enums import ApprovalStatus
from app.schemas.approval_request import (
    ApproveRequestBody,
    ApprovalRequestCreate,
    ApprovalRequestListResponse,
    ApprovalRequestResponse,
    CancelRequestBody,
    RejectRequestBody,
)
from app.services import approval_requests as service
from app.services.events import EventPublisher, get_event_publisher

router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}/approval-requests")


@router.post("", response_model=ApprovalRequestResponse)
def create_approval_request(
    workspace_id: str,
    data: ApprovalRequestCreate,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(require_action("approval:create")),
):
    existing = service.get_by_idempotency_key(db, workspace_id, idempotency_key)
    if existing is not None:
        response.status_code = 200
        return existing

    approval_request = service.create_approval_request(
        db,
        workspace_id=workspace_id,
        created_by=auth_context.user_id,
        idempotency_key=idempotency_key,
        data=data,
    )
    response.status_code = 201
    return approval_request


@router.get("", response_model=ApprovalRequestListResponse)
def list_approval_requests(
    workspace_id: str,
    status: ApprovalStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(require_action("approval:read")),
):
    items, total = service.list_approval_requests(
        db, workspace_id=workspace_id, status=status, limit=limit, offset=offset
    )
    return ApprovalRequestListResponse(
        items=items, limit=limit, offset=offset, total=total
    )


@router.get("/{request_id}", response_model=ApprovalRequestResponse)
def get_approval_request(
    workspace_id: str,
    request_id: str,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(require_action("approval:read")),
):
    return service.get_approval_request(db, workspace_id, request_id)


@router.post("/{request_id}/approve", response_model=ApprovalRequestResponse)
def approve_approval_request(
    workspace_id: str,
    request_id: str,
    data: ApproveRequestBody,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(require_action("approval:decide")),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    approval_request = service.get_approval_request(db, workspace_id, request_id)
    return service.approve_approval_request(
        db, approval_request, auth_context.user_id, data.comment, event_publisher
    )


@router.post("/{request_id}/reject", response_model=ApprovalRequestResponse)
def reject_approval_request(
    workspace_id: str,
    request_id: str,
    data: RejectRequestBody,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(require_action("approval:decide")),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    approval_request = service.get_approval_request(db, workspace_id, request_id)
    return service.reject_approval_request(
        db, approval_request, auth_context.user_id, data.reason, event_publisher
    )


@router.post("/{request_id}/cancel", response_model=ApprovalRequestResponse)
def cancel_approval_request(
    workspace_id: str,
    request_id: str,
    data: CancelRequestBody,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(require_action("approval:cancel")),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    approval_request = service.get_approval_request(db, workspace_id, request_id)
    return service.cancel_approval_request(
        db, approval_request, auth_context.user_id, data.reason, event_publisher
    )
