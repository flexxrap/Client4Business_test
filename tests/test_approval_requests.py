from app.models.approval_decision import ApprovalDecision
from tests.conftest import auth_header

REQUEST_BODY = {
    "source_type": "publication",
    "source_id": "pub_1",
    "title": "Quarterly report",
    "description": "Please review",
    "reviewer_user_ids": ["usr_9"],
}


def create_request(client, workspace_id="ws_1", idempotency_key="key-1"):
    return client.post(
        f"/api/v1/workspaces/{workspace_id}/approval-requests",
        json=REQUEST_BODY,
        headers={
            **auth_header(workspace_id, "usr_1"),
            "Idempotency-Key": idempotency_key,
        },
    )


def test_create_approval_request(client):
    response = create_request(client)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["workspace_id"] == "ws_1"
    assert body["title"] == "Quarterly report"


def test_idempotent_create_does_not_duplicate(client, db_session):
    first = create_request(client, idempotency_key="same-key")
    second = create_request(client, idempotency_key="same-key")

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    list_response = client.get(
        "/api/v1/workspaces/ws_1/approval-requests",
        headers=auth_header("ws_1", "usr_1"),
    )
    assert list_response.json()["total"] == 1


def test_workspace_isolation_returns_404_for_foreign_request(client):
    created = create_request(client, workspace_id="ws_1")
    request_id = created.json()["id"]

    response = client.get(
        f"/api/v1/workspaces/ws_2/approval-requests/{request_id}",
        headers=auth_header("ws_2", "usr_2"),
    )

    assert response.status_code == 404


def test_approve_twice_returns_conflict(client):
    created = create_request(client)
    request_id = created.json()["id"]

    first_approve = client.post(
        f"/api/v1/workspaces/ws_1/approval-requests/{request_id}/approve",
        json={"comment": "looks good"},
        headers=auth_header("ws_1", "usr_1"),
    )
    second_approve = client.post(
        f"/api/v1/workspaces/ws_1/approval-requests/{request_id}/approve",
        json={"comment": "again"},
        headers=auth_header("ws_1", "usr_1"),
    )

    assert first_approve.status_code == 200
    assert first_approve.json()["status"] == "approved"
    assert second_approve.status_code == 409


def test_audit_trail_created_on_decision(client, db_session):
    created = create_request(client)
    request_id = created.json()["id"]

    client.post(
        f"/api/v1/workspaces/ws_1/approval-requests/{request_id}/reject",
        json={"reason": "missing data"},
        headers=auth_header("ws_1", "usr_1"),
    )

    decisions = (
        db_session.query(ApprovalDecision)
        .filter(ApprovalDecision.request_id == request_id)
        .all()
    )
    assert len(decisions) == 1
    assert decisions[0].action.value == "reject"
    assert decisions[0].reason == "missing data"
    assert decisions[0].actor_user_id == "usr_1"


def test_missing_action_returns_403(client):
    response = client.post(
        "/api/v1/workspaces/ws_1/approval-requests",
        json=REQUEST_BODY,
        headers={
            **auth_header("ws_1", "usr_1", actions=["approval:read"]),
            "Idempotency-Key": "key-forbidden",
        },
    )

    assert response.status_code == 403
