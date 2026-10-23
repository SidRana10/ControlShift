"""FastAPI app: GET /health, POST /ask, POST /compare, read-only GET /catalog/*."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager

import anyio.to_thread
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..generation.config import Settings
from ..generation.provider import ProviderError, ProviderTimeout
from ..store.queries import NotFoundError
from .catalog import router as catalog_router
from .schemas import AnswerResponse, AskRequest, CompareRequest, ErrorResponse, HealthResponse
from .services import Services, build_services

log = logging.getLogger("controlshift.api")
ERRORS = {502: {"model": ErrorResponse}, 504: {"model": ErrorResponse},
          422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}


def _err(status: int, code: str, message: str, details: list | None = None) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "message": message, "details": details}})


def create_app(services_factory: Callable[[], Services] = build_services,
               request_timeout: float | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.services = await anyio.to_thread.run_sync(services_factory)  # once per process
        yield

    app = FastAPI(title="ControlShift", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"][1:]), "problem": e["msg"]}
                   for e in exc.errors()]
        return _err(422, "invalid_request", "The request body is invalid.", details)

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception):
        log.exception("unhandled error")  # details stay in the server log
        return _err(500, "internal_error", "An internal error occurred.")

    async def run(request: Request, question: str, k: int, generate: bool, effective: str,
                  include_evidence: bool):
        svc: Services = request.app.state.services
        timeout = request_timeout or svc.settings.request_timeout_seconds
        try:
            bundle, result = await asyncio.wait_for(
                anyio.to_thread.run_sync(svc.answer, effective, k, generate), timeout)
        except TimeoutError:
            return _err(504, "request_timeout", f"The request exceeded {timeout:g}s.")
        except ProviderTimeout as exc:
            return _err(504, "provider_timeout", str(exc))
        except ProviderError as exc:
            return _err(502, exc.code, str(exc))
        except NotFoundError as exc:
            return _err(404, "not_found", str(exc))
        body = result.to_dict()
        return AnswerResponse(question=question, effective_question=effective,
                              evidence=bundle.to_dict() if include_evidence else None, **body)

    app.include_router(catalog_router)

    @app.get("/health", response_model=HealthResponse)
    async def health(request: Request):
        return await anyio.to_thread.run_sync(request.app.state.services.health)

    @app.post("/ask", response_model=AnswerResponse, responses=ERRORS)
    async def ask(req: AskRequest, request: Request):
        q = req.question
        if req.version and req.version not in q:
            q = f"In CSF {req.version}: {q}"
        return await run(request, req.question, req.retrieval_k, req.generate, q,
                         req.include_evidence)

    @app.post("/compare", response_model=AnswerResponse, responses=ERRORS)
    async def compare(req: CompareRequest, request: Request):
        ids = f" for {', '.join(req.control_ids)}" if req.control_ids else ""
        q = f"Compare CSF 1.1 and CSF 2.0{ids}: {req.question}"
        return await run(request, req.question, req.retrieval_k, req.generate, q,
                         req.include_evidence)

    return app


def app_factory() -> FastAPI:
    """`uvicorn controlshift.api.app:app_factory --factory` (loads .env if python-dotenv exists)."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:  # optional
        pass
    return create_app(lambda: build_services(Settings.from_env()))


def main() -> None:
    import os

    import uvicorn

    uvicorn.run("controlshift.api.app:app_factory", factory=True,
                host=os.environ.get("API_HOST", "127.0.0.1"),
                port=int(os.environ.get("API_PORT", "8000")))


if __name__ == "__main__":
    main()
