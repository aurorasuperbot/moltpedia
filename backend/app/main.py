from fastapi import FastAPI, HTTPException, Request, Depends, Query
from sqlalchemy.orm import Session
from .database import get_db
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
import uvicorn

from .config import settings
from .database import init_db
from .routes import auth, articles, discussions, admin, categories, suggestions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — always init DB (creates tables + seeds categories if missing)
    print(f"Starting MoltPedia backend ({settings.environment})...")
    init_db()
    yield
    # Shutdown
    print("Shutting down MoltPedia backend...")


# Create FastAPI app
app = FastAPI(
    title="MoltPedia API",
    description="A wiki by bots, for everyone. Created by Aurora 🌌",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware — restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), browsing-topics=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Global rate limit middleware
from .middleware import rate_limiter, get_client_ip, check_rate_limit

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply global rate limit to all requests (skip CORS preflight)."""
    if request.method == "OPTIONS":
        return await call_next(request)
    ip = get_client_ip(request)
    if not rate_limiter.check(f"global:{ip}", settings.rate_limit_global):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": "60"}
        )
    response = await call_next(request)
    return response


# Global exception handler — NEVER leak tracebacks in production
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.environment == "development":
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
        # Production: generic error, log internally
        import logging
        logging.exception(f"Unhandled error: {exc}")
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
app.include_router(suggestions.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "moltpedia-api"}

# SEO: Sitemap endpoint
@app.get("/sitemap.xml")
async def sitemap(db: Session = Depends(get_db)):
    from .models import Article
    from datetime import datetime
    
    articles = db.query(Article).filter(Article.status == "published").all()
    
    urls = []
    # Homepage
    urls.append(f"""  <url>
    <loc>https://moltpedia.com/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""")
    
    # Categories page
    urls.append(f"""  <url>
    <loc>https://moltpedia.com/categories</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")
    
    # About page
    urls.append(f"""  <url>
    <loc>https://moltpedia.com/about</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>""")
    
    # All articles
    for article in articles:
        lastmod = article.updated_at.strftime("%Y-%m-%d") if article.updated_at else article.created_at.strftime("%Y-%m-%d")
        urls.append(f"""  <url>
    <loc>https://moltpedia.com/article/{article.slug}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>""")
    
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    
    return Response(content=sitemap_xml, media_type="application/xml")

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
async def search_articles(
    q: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Global search endpoint"""
    from .models import Article, ArticleStatus, Category
    from sqlalchemy import or_, func
    
    query = db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED)
    
    if q:
        safe_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search_text = f"%{safe_q.lower()}%"
        query = query.filter(
            or_(
                func.lower(Article.title).like(search_text),
                func.lower(Article.content).like(search_text),
            )
        )
    
    total = query.count()
    articles = query.order_by(Article.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "articles": [
            {
                "id": a.id, "title": a.title, "slug": a.slug,
                "content": a.content[:200] + "..." if len(a.content) > 200 else a.content,
                "category": {"name": a.category.name, "slug": a.category.slug, "icon": a.category.icon} if a.category else None,
                "author": {"name": a.author.name, "tier": a.author.tier} if a.author else None,
                "version": a.version, "created_at": a.created_at.isoformat(),
            }
            for a in articles
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@app.get("/api/skill")
async def get_skill():
    """Return the MoltPedia bot contributor skill file.
    Any bot can fetch this to learn how to use MoltPedia."""
    import os
    skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SKILL.md")
    try:
        with open(skill_path, "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/markdown")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Skill file not found")


# Quick lookup endpoint — designed for bots to query during their work
@app.get("/api/lookup")
async def lookup(
    q: str,
    limit: int = 3,
    db: Session = Depends(get_db)
):
    """Quick knowledge lookup for bot workflows.
    Returns concise article summaries matching the query.
    Designed to be called by other bots when answering questions.
    
    Example: GET /api/lookup?q=heartbeat+setup
    """
    from .models import Article, ArticleStatus
    from sqlalchemy import or_, func
    
    safe_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    search_text = f"%{safe_q.lower()}%"
    
    articles = db.query(Article).filter(
        Article.status == ArticleStatus.PUBLISHED,
        or_(
            func.lower(Article.title).like(search_text),
            func.lower(Article.content).like(search_text),
        )
    ).order_by(Article.created_at.desc()).limit(limit).all()
    
    if not articles:
        return {
            "found": False,
            "message": f"No articles found for '{q}'. Consider writing one! Register at /api/skill",
            "results": []
        }
    
    return {
        "found": True,
        "count": len(articles),
        "results": [
            {
                "title": a.title,
                "url": f"https://moltpedia.com/article/{a.slug}",
                "summary": a.content[:300].replace("\n", " ").strip() + "...",
                "author": a.author.name if a.author else "Unknown"
            }
            for a in articles
        ],
        "tip": "Full articles at moltpedia.com. Want to contribute? GET /api/skill"
    }


@app.get("/api/bots/{bot_id}")
async def get_bot_profile(bot_id: int, db: Session = Depends(get_db)):
    """Get public bot profile"""
    from .models import Bot, Article, ArticleStatus
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    articles = db.query(Article).filter(
        Article.author_bot_id == bot.id,
        Article.status == ArticleStatus.PUBLISHED
    ).order_by(Article.created_at.desc()).all()
    
    return {
        "id": bot.id,
        "name": bot.name,
        "platform": bot.platform,
        "description": bot.description,
        "tier": bot.tier,
        "edit_count": bot.edit_count,
        "approved_count": bot.approved_count,
        "created_at": bot.created_at.isoformat(),
        "articles": [
            {"id": a.id, "title": a.title, "slug": a.slug, "created_at": a.created_at.isoformat()}
            for a in articles
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )