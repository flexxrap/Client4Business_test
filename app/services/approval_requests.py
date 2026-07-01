from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.approval_decision import ApprovalDecision
from app.models.approval_request import ApprovalRequest
from app.models.enums import ApprovalStatus, DecisionAction
from app.schemas.approval_request import ApprovalRequestCreate
from app.services.events import EventPublisher


def get_by_idempotency_key(
    db: Session, workspace_id: str, idempotency_key: str
) -> ApprovalRequest | None:
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.workspace_id == workspace_id,
        ApprovalRequest.idempotency_key == idempotency_key,
    )
    return db.execute(stmt).scalar_one_or_none()


def create_approval_request(
    db: Session,
    workspace_id: str,
    created_by: str,
    idempotency_key: str,
    data: ApprovalRequestCreate,
) -> ApprovalRequest:
    approval_request = ApprovalRequest(
        workspace_id=workspace_id,
        source_type=data.source_type,
        source_id=data.source_id,
        title=data.title,
        description=data.description,
        reviewer_user_ids=data.reviewer_user_ids,
        status=ApprovalStatus.PENDING,
        created_by=created_by,
        idempotency_key=idempotency_key,
    )
    db.add(approval_request)
    db.commit()
    db.refresh(approval_request)
    return approval_request


def list_approval_requests(
    db: Session,
    workspace_id: str,
    status: ApprovalStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[ApprovalRequest], int]:
    filters = [ApprovalRequest.workspace_id == workspace_id]
    if status is not None:
        filters.append(ApprovalRequest.status == status)

    total = db.execute(
        select(func.count()).select_from(ApprovalRequest).where(*filters)
    ).scalar_one()

    stmt = (
        select(ApprovalRequest)
        .where(*filters)
        .order_by(ApprovalRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = db.execute(stmt).scalars().all()
    return items, total


def get_approval_request(
    db: Session, workspace_id: str, request_id: str
) -> ApprovalRequest:
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.id == request_id,
        ApprovalRequest.workspace_id == workspace_id,
    )
    approval_request = db.execute(stmt).scalar_one_or_none()
    if approval_request is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return approval_request


def _apply_decision(
    db: Session,
    approval_request: ApprovalRequest,
    new_status: ApprovalStatus,
    action: DecisionAction,
    actor_user_id: str,
    comment: str | None,
    reason: str | None,
    event_publisher: EventPublisher,
    event_type: str,
) -> ApprovalRequest:
    if approval_request.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Approval request is already in a final state: {approval_request.status.value}",
        )

    approval_request.status = new_status
    decision = ApprovalDecision(
        request_id=approval_request.id,
        action=action,
        actor_user_id=actor_user_id,
        comment=comment,
        reason=reason,
    )
    db.add(decision)
    db.commit()
    db.refresh(approval_request)

    event_publisher.publish(
        event_type=event_type,
        request_id=approval_request.id,
        workspace_id=approval_request.workspace_id,
        actor_user_id=actor_user_id,
    )

    return approval_request


def approve_approval_request(
    db: Session,
    approval_request: ApprovalRequest,
    actor_user_id: str,
    comment: str | None,
    event_publisher: EventPublisher,
) -> ApprovalRequest:
    return _apply_decision(
        db,
        approval_request,
        ApprovalStatus.APPROVED,
        DecisionAction.APPROVE,
        actor_user_id,
        comment,
        None,
        event_publisher,
        "approval_request.approved",
    )


def reject_approval_request(
    db: Session,
    approval_request: ApprovalRequest,
    actor_user_id: str,
    reason: str | None,
    event_publisher: EventPublisher,
) -> ApprovalRequest:
    return _apply_decision(
        db,
        approval_request,
        ApprovalStatus.REJECTED,
        DecisionAction.REJECT,
        actor_user_id,
        None,
        reason,
        event_publisher,
        "approval_request.rejected",
    )


def cancel_approval_request(
    db: Session,
    approval_request: ApprovalRequest,
    actor_user_id: str,
    reason: str | None,
    event_publisher: EventPublisher,
) -> ApprovalRequest:
    return _apply_decision(
        db,
        approval_request,
        ApprovalStatus.CANCELLED,
        DecisionAction.CANCEL,
        actor_user_id,
        None,
        reason,
        event_publisher,
        "approval_request.cancelled",
    )
