from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine
from .models import Base
from .routers import contacts, auth, users

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        swagger_ui_parameters={"defaultModelsExpandDepth": 0},
    )

    Base.metadata.create_all(bind=engine)

    # CORS
    origins = [o for o in settings.CORS_ORIGINS.split(",") if o]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(contacts.router)

    return app

app = create_app()
