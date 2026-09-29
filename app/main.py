"""Agent service — điểm ráp nối của cả lab (CP1, CP3, CP4).

Luồng một request tới /ask:

    client ──► verify_api_key ──► rate_limiter ──► cost_guard
                                                       │
                              store.get_history ◄──────┘
                                       │
                                    ask_llm
                                       │
                              store.append × 2 ──► cost_guard.record ──► log_event
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from utils.mock_llm import ask_llm

from .auth import verify_api_key
from .config import get_settings
from .cost_guard import CostGuard
from .lifecycle import lifecycle
from .logging_utils import log_event
from .rate_limiter import RateLimiter
from .store import ConversationStore, get_redis_client


SERVICE_NAME = "day12-agent"
SERVICE_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────
# Providers
# ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_store() -> ConversationStore:
    """Tạo ConversationStore dùng Redis."""
    return ConversationStore(get_redis_client())


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    """Tạo RateLimiter dùng Redis."""
    return RateLimiter(
        get_redis_client(),
        get_settings().rate_limit_per_minute,
    )


@lru_cache(maxsize=1)
def get_cost_guard() -> CostGuard:
    """Tạo CostGuard dùng Redis."""
    return CostGuard(
        get_redis_client(),
        get_settings().monthly_budget_usd,
    )


# ─────────────────────────────────────────────────────────────
# Application lifecycle
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Chạy khi app khởi động và khi app tắt."""

    # Đăng ký signal handler / trạng thái lifecycle
    lifecycle.install()

    log_event(
        "service_started",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )

    yield

    log_event(
        "service_stopped",
        service=SERVICE_NAME,
    )


app = FastAPI(
    title="Day 12 Production Agent",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────
# Request model
# ─────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )


# ─────────────────────────────────────────────────────────────
# Health & readiness
# ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Liveness probe.

    /health chỉ kiểm tra process/app còn sống.
    Không gọi Redis hoặc database.

    Khi service đang graceful shutdown:
        503 {"status": "shutting_down"}

    Bình thường:
        200 {
            "status": "ok",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION
        }
    """

    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={
                "status": "shutting_down",
            },
        )

    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


@app.get("/ready")
def ready(
    store: ConversationStore = Depends(get_store),
):
    """Readiness probe.

    /ready kiểm tra dependency Redis.

    Khi service đang graceful shutdown:
        503 {"status": "shutting_down"}

    Khi Redis chết:
        503 {"status": "not ready", "redis": False}

    Khi Redis hoạt động:
        200 {"status": "ready", "redis": True}
    """

    # Đang graceful shutdown thì không nhận traffic mới
    if lifecycle.shutting_down:
        return JSONResponse(
            status_code=503,
            content={
                "status": "shutting_down",
            },
        )

    # Kiểm tra Redis
    redis_ready = store.ping()

    if not redis_ready:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "redis": False,
            },
        )

    return {
        "status": "ready",
        "redis": True,
    }


# ─────────────────────────────────────────────────────────────
# Main endpoint
# ─────────────────────────────────────────────────────────────

@app.post("/ask")
def ask(
    payload: AskRequest,
    user_id: str = Depends(verify_api_key),
    store: ConversationStore = Depends(get_store),
    limiter: RateLimiter = Depends(get_rate_limiter),
    guard: CostGuard = Depends(get_cost_guard),
):
    """Hỏi agent một câu.

    Thứ tự xử lý:

    1. limiter.check(user_id)
    2. guard.check(user_id)
    3. history = store.get_history(user_id)
    4. result = ask_llm(payload.question, history)
    5. store.append(... user ...)
    6. store.append(... assistant ...)
    7. guard.record(...)
    8. log_event(...)
    9. trả response
    """

    # 1. Rate limit
    limiter.check(user_id)

    # 2. Cost / budget guard
    guard.check(user_id)

    # 3. Lấy lịch sử hội thoại
    history = store.get_history(user_id)

    # 4. Gọi LLM
    result = ask_llm(
        payload.question,
        history,
    )

    # 5. Lưu câu hỏi của user
    store.append(
        user_id,
        "user",
        payload.question,
    )

    # 6. Lưu câu trả lời của assistant
    store.append(
        user_id,
        "assistant",
        result["answer"],
    )

    # 7. Ghi nhận cost
    guard.record(
        user_id,
        result["cost_usd"],
    )

    # 8. Logging
    log_event(
        "ask_completed",
        user_id=user_id,
        tokens_in=result["tokens_in"],
        tokens_out=result["tokens_out"],
        cost_usd=result["cost_usd"],
    )

    # 9. Response
    return {
        "answer": result["answer"],
        "user_id": user_id,
        "history_length": len(history),
        "cost_usd": result["cost_usd"],
        "tokens": {
            "in": result["tokens_in"],
            "out": result["tokens_out"],
        },
    }


# ─────────────────────────────────────────────────────────────
# Run directly
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
    )