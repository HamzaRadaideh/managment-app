from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.database import init_db
from app.api.routers.auths_routers import router as auth_router
from app.api.routers.tasks_routers import router as tasks_router
from app.api.routers.notes_routers import router as notes_router
from app.api.routers.collections_routers import router as collections_router
from app.api.routers.tags_routers import router as tags_router

from app.api.routers.search_routers import router as search_router

app = FastAPI(
    title="Task & Note Manager API",
    description="A powerful app to manage tasks and notes with collections and tags.",
    version="1.0.0",
)

# CORS (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(notes_router)
app.include_router(collections_router)
app.include_router(tags_router)

app.include_router(search_router)

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to Task & Note Manager API 🚀"}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}
