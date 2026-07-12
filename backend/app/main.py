from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.churn import router as churn_router
from app.api.credit import router as credit_router
from app.api.customers import router as customers_router
from app.api.datasets import router as datasets_router
from app.api.loans import router as loans_router
from app.api.retention import router as retention_router
from app.api.statements import router as statements_router
from app.config import settings
from app.core.exceptions import BaseAppException, handle_app_exception
from app.core.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Startup
    configure_logging()
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    
    # TODO: Initialize Kafka producer
    # TODO: Initialize Redis connection pool
    # TODO: Initialize Celery worker
    # TODO: Load ML models into memory
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")
    
    # TODO: Close Kafka connections
    # TODO: Close Redis connections
    # TODO: Graceful Celery shutdown


def create_application() -> FastAPI:
    
    app = FastAPI(
        title=settings.app_name,
        description="AI-Powered Customer Intelligence, Churn Prediction, and Loan Decisioning Platform for Kenyan Digital Lenders",
        version=settings.app_version,
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        openapi_url="/api/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted Hosts
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.kenyalend.co.ke", "kenyalend.co.ke"],
        )
 
    # Exception Handlers
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request, exc):
        http_exc = handle_app_exception(exc)
        return JSONResponse(
            status_code=http_exc.status_code,
            content=http_exc.detail,
        )

    api_prefix = "/api/v1"
    
    app.include_router(auth_router, prefix=f"{api_prefix}/auth")
    app.include_router(customers_router, prefix=f"{api_prefix}/customers")
    app.include_router(loans_router, prefix=f"{api_prefix}/loans")
    app.include_router(churn_router, prefix=f"{api_prefix}/churn")
    app.include_router(credit_router, prefix=f"{api_prefix}/credit")
    app.include_router(statements_router, prefix=f"{api_prefix}/statements")
    app.include_router(datasets_router, prefix=f"{api_prefix}/datasets")
    app.include_router(retention_router, prefix=f"{api_prefix}/retention")

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }
    
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "AI-Powered Customer Intelligence, Churn Prediction, and Loan Decisioning Platform",
            "documentation": "/api/docs" if settings.is_development else None,
        }
    
    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        workers=1 if settings.is_development else 4,
    )