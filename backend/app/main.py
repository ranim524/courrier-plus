from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.rate_limit import limiter
from app.routes import admin, config, delivery, letters, payments, pricing, tracking

settings = get_settings()

app = FastAPI(
    title="Courrier+ API",
    description="Digital registered mail platform for Tunisia — technical prototype.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):  # noqa: ANN001
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=429, content={"detail": "Too many requests, please slow down"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(letters.router)
app.include_router(payments.router)
app.include_router(tracking.router)
app.include_router(admin.router)
app.include_router(config.router)
app.include_router(pricing.router)
app.include_router(delivery.router)
app.include_router(delivery.providers_router)
app.include_router(delivery.agents_router)


@app.get("/api/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok", "environment": settings.environment}
