import json
import re
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

WORKSPACE_PATH_PATTERN = re.compile(r"/workspaces/([^/]+)")

EXEMPT_PATHS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc"}


@dataclass
class AuthContext:
    workspace_id: str
    user_id: str
    actions: list[str]

    def has_action(self, action: str) -> bool:
        return action in self.actions


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        header_value = request.headers.get("X-Auth-Context")
        if not header_value:
            return JSONResponse(
                status_code=401, content={"detail": "Missing X-Auth-Context header"}
            )

        try:
            payload = json.loads(header_value)
            workspace_id = payload["workspace_id"]
            user_id = payload["user_id"]
            actions = payload["actions"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return JSONResponse(
                status_code=401, content={"detail": "Invalid X-Auth-Context header"}
            )

        path_match = WORKSPACE_PATH_PATTERN.search(request.url.path)
        if path_match and path_match.group(1) != workspace_id:
            return JSONResponse(
                status_code=403,
                content={"detail": "Workspace in path does not match auth context"},
            )

        request.state.auth_context = AuthContext(
            workspace_id=workspace_id, user_id=user_id, actions=actions
        )

        return await call_next(request)
