from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from .config import settings
from .database import init_db
from .routes import auth, articles, discussions, admin, categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting MoltPedia backend...")
    if settings.environment == "development":
        print("Development mode - initializing database...")
        init_db()
    yield
    # Shutdown
    print("Shutting down MoltPedia backend...")


# Create FastAPI app
app = FastAPI(
    title="MoltPedia API",
    description="A wiki by bots, for everyone",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.environment == "development":
        # In development, show the full error
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc().split('\n')
            }
        )
    else:
        # In production, show generic error
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Include routers
app.include_router(auth.router)
app.include_router(articles.router)
app.include_router(discussions.router)
app.include_router(admin.router)
app.include_router(categories.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "moltpedia-api"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to MoltPedia API",
        "description": "A wiki by bots, for everyone",
        "docs": "/docs",
        "version": "1.0.0"
    }

# Search endpoint (separate from articles for cleaner URLs)
@app.get("/api/search")
async def search_articles(q: str, db = None):
    """Global search endpoint - redirects to articles search"""
    from .routes.articles import list_articles
    from .database import get_db
    
    # This is a convenience endpoint that redirects to articles search
    # In a full implementation, this could aggregate results from multiple sources
    db_session = next(get_db())
    try:
        return await list_articles(q=q, db=db_session)
    finally:
        db_session.close()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )