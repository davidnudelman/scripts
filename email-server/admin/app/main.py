import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func

from app.database import async_session
from app.models import Domain, User, Alias
from app.routes import (
    auth_routes,
    domain_routes,
    user_routes,
    alias_routes,
    dkim_routes,
    settings_routes,
    autodiscover_routes,
)
from app.auth import hash_password
from app.config import settings as app_settings

app = FastAPI(
    title="Mail Server Admin",
    description="Web administration panel for the containerized mail server",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# Register API routes
app.include_router(auth_routes.router)
app.include_router(domain_routes.router)
app.include_router(user_routes.router)
app.include_router(alias_routes.router)
app.include_router(dkim_routes.router)
app.include_router(settings_routes.router)
app.include_router(autodiscover_routes.router)


@app.on_event("startup")
async def create_default_admin():
    """Create a default admin user and domain on first run."""
    async with async_session() as db:
        result = await db.execute(select(func.count(User.id)).where(User.is_admin.is_(True)))
        admin_count = result.scalar()
        if admin_count == 0:
            # Create default domain
            domain_result = await db.execute(
                select(Domain).where(Domain.name == app_settings.mail_domain)
            )
            domain = domain_result.scalar_one_or_none()
            if domain is None:
                domain = Domain(name=app_settings.mail_domain, active=True)
                db.add(domain)
                await db.flush()

            # Create default admin user
            admin = User(
                domain_id=domain.id,
                email=f"admin@{app_settings.mail_domain}",
                password=hash_password("admin"),
                display_name="Administrator",
                is_admin=True,
                active=True,
            )
            db.add(admin)
            await db.commit()
            print(f"Created default admin: admin@{app_settings.mail_domain} / admin")
            print("** CHANGE THIS PASSWORD IMMEDIATELY **")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}
