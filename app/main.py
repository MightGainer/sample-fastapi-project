from fastapi import FastAPI, Request
from app.controllers.user_controller import router as user_router
from app.middlewares.permissions import token_middleware
from app.di import service_provider
from typing import Callable

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": True})


@app.middleware("http")
async def add_token_middleware(request: Request, call_next: Callable):
    return await token_middleware(request, call_next)


# Register routes
app.include_router(user_router, prefix="/api")


# Add ServiceProvider to app state
@app.on_event("startup")
async def startup_event():
    app.state.service_provider = service_provider
