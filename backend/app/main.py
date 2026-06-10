from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.database.session import Base, engine
from app.services.llm_client import llm_client
from app.services.rag.ingest import ingest_documents
from app.services.rag.vector_store import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    if vector_store.count() == 0:
        try:
            result = await ingest_documents()
            app.state.ingest_result = result
        except FileNotFoundError as exc:
            app.state.ingest_result = {"error": str(exc)}
    else:
        app.state.ingest_result = {"collection_size": vector_store.count()}

    if not await llm_client.is_available():
        llm_client.use_mock = True
        app.state.mock_mode = True
    else:
        app.state.mock_mode = settings.use_mock_llm

    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "AI Candidate Screening API",
        "docs": "/docs",
    }
