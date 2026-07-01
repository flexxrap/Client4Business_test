from fastapi import HTTPException, Request

from app.middleware.auth import AuthContext


def get_auth_context(request: Request) -> AuthContext:
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is None:
        raise HTTPException(status_code=401, detail="Missing auth context")
    return auth_context


def require_action(action: str):
    def dependency(request: Request) -> AuthContext:
        auth_context = get_auth_context(request)
        if not auth_context.has_action(action):
            raise HTTPException(
                status_code=403, detail=f"Missing required action: {action}"
            )
        return auth_context

    return dependency
