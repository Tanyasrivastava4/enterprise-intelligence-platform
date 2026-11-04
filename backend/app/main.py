import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from sqlalchemy import select

# Routers
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.agent import router as agent_router
from app.api.analytics import router as analytics_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    await init_db()
    
    # Seed default user if not exists
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.username == "demo_admin")
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            admin_user = User(
                username="demo_admin",
                email="admin@enterprise.ai",
                hashed_password=get_password_hash("Enterprise2026!"),
                full_name="Enterprise AI Reviewer",
                is_admin=True
            )
            session.add(admin_user)
            await session.commit()
            print("Default admin created: user='demo_admin', pass='Enterprise2026!'")
            
    yield

app = FastAPI(
    title="Enterprise Intelligence Platform API",
    description="Production-ready AI Enterprise Intelligence Platform with Hybrid RAG, Multi-Model Fallback, Autonomous Agents, and Observability.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
api_prefix = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=api_prefix)
app.include_router(documents_router, prefix=api_prefix)
app.include_router(chat_router, prefix=api_prefix)
app.include_router(agent_router, prefix=api_prefix)
app.include_router(analytics_router, prefix=api_prefix)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "primary_model": settings.GROQ_MODEL if settings.GROQ_API_KEY else "unconfigured",
        "fallback_model": settings.GROQ_FALLBACK_MODEL
    }

# Serve Frontend static build if available
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    from fastapi.responses import FileResponse
    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{path_name}")
    async def serve_spa_page(path_name: str):
        if path_name in ["health", "docs", "redoc", "openapi.json"] or path_name.startswith("api"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(frontend_dist, path_name)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
