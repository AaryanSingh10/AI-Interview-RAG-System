from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Candidate Screening"
    database_url: str = "sqlite:///./data/interviews.db"
    chroma_path: str = "./data/chroma"
    knowledge_base_path: str = "../knowledge_base/documents"
    uploads_path: str = "./data/uploads"

    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"

    use_mock_llm: bool = False
    chunk_size: int = 800
    chunk_overlap: int = 150
    retrieval_top_k: int = 6
    questions_per_session: int = 5

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()

for path in [
    Path(settings.chroma_path),
    Path(settings.uploads_path),
    Path("./data"),
]:
    path.mkdir(parents=True, exist_ok=True)
