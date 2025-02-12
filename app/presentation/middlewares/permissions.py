from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Coroutine

import jwt
from fastapi import HTTPException, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from starlette.responses import Response

from app.presentation.settings import load_settings

settings = load_settings()

anonymous_routes: set[str] = set()


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)}
    )
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> dict[str, object]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token has expired")
        return payload  # type: ignore
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def token_middleware(request: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]) -> Response:
    try:
        if request.url.path in anonymous_routes or request.url.path in [
            "/docs",
            "/openapi.json",
        ]:
            return await call_next(request)

        authorization: str | None = request.headers.get("Authorization")
        if authorization is None:
            raise HTTPException(status_code=403, detail="Authorization header missing")

        token = authorization.split(" ")[1] if len(authorization.split(" ")) == 2 else None

        if token is None:
            raise HTTPException(status_code=403, detail="Invalid Authorization header format")

        verify_token(token)

        request.state.token = token
        response: Response = await call_next(request)
        return response
    except HTTPException as exc:
        return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
    except Exception as exc:
        return JSONResponse(content={"detail": f"Error: {str(exc)}"}, status_code=500)


def get_credentials(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> HTTPAuthorizationCredentials:
    return credentials


def require_permissions(required_permissions: list[str]) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> object:
            request = kwargs.get("request")
            if not request:
                raise HTTPException(status_code=400, detail="Request object is missing")

            payload = verify_token(request.state.token)
            user_permissions = set(payload.get("permissions", []))  # type: ignore

            if not user_permissions.issuperset(set(required_permissions)):
                raise HTTPException(status_code=403, detail="Permission denied")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def allow_anonymous(route_path: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        anonymous_routes.add(route_path)

        @wraps(func)
        async def wrapper(*args, **kwargs) -> object:
            return await func(*args, **kwargs)

        return wrapper

    return decorator
