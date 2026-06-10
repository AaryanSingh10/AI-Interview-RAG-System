import re
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.models.schemas import ResumeProfile

SKILL_KEYWORDS = {
    "python",
    "java",
    "c++",
    "r",
    "sql",
    "pandas",
    "numpy",
    "scikit-learn",
    "sklearn",
    "tensorflow",
    "pytorch",
    "keras",
    "xgboost",
    "lightgbm",
    "spark",
    "hadoop",
    "aws",
    "gcp",
    "azure",
    "docker",
    "kubernetes",
    "mlflow",
    "fastapi",
    "flask",
    "django",
    "react",
    "next.js",
    "nlp",
    "computer vision",
    "deep learning",
    "machine learning",
    "statistics",
    "regression",
    "classification",
    "clustering",
    "neural networks",
    "transformers",
    "bert",
    "gpt",
    "rag",
    "embeddings",
    "feature engineering",
    "cross-validation",
    "hyperparameter tuning",
    "a/b testing",
    "git",
    "linux",
}

TECH_PATTERNS = [
    r"\b(?:Python|Java|C\+\+|R|SQL|Scala|Julia)\b",
    r"\b(?:TensorFlow|PyTorch|Keras|scikit-learn|sklearn|XGBoost|LightGBM)\b",
    r"\b(?:Pandas|NumPy|Matplotlib|Seaborn|Plotly)\b",
    r"\b(?:AWS|GCP|Azure|Docker|Kubernetes)\b",
    r"\b(?:FastAPI|Flask|Django|React|Next\.js)\b",
    r"\b(?:Spark|Hadoop|Airflow|MLflow)\b",
]


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def extract_text_from_file(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(content)
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {suffix}. Use PDF or TXT.")


def parse_resume(text: str) -> ResumeProfile:
    normalized = re.sub(r"\s+", " ", text).strip()
    lower = normalized.lower()

    skills = sorted(
        {skill for skill in SKILL_KEYWORDS if skill in lower},
        key=str.lower,
    )

    technologies: set[str] = set()
    for pattern in TECH_PATTERNS:
        for match in re.findall(pattern, normalized, flags=re.IGNORECASE):
            technologies.add(match.strip())

    email_match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", normalized
    )
    name = _extract_name(normalized)
    experience_years = _extract_experience_years(lower)
    education = _extract_education(normalized)
    summary = normalized[:500] + ("..." if len(normalized) > 500 else "")

    return ResumeProfile(
        name=name,
        email=email_match.group(0) if email_match else None,
        skills=skills,
        technologies=sorted(technologies, key=str.lower),
        experience_years=experience_years,
        education=education,
        summary=summary,
    )


def _extract_name(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    candidate = lines[0]
    if "@" in candidate or len(candidate) > 60:
        return None
    return candidate


def _extract_experience_years(text: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*years?\s+(?:of\s+)?experience",
        r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\+?\s*years?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    return None


def _extract_education(text: str) -> list[str]:
    degrees = []
    patterns = [
        r"(?:B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?).{0,80}(?:Computer Science|Data Science|Machine Learning|Statistics|Engineering|Mathematics)",
        r"(?:Bachelor|Master|Doctor).{0,80}(?:Computer Science|Data Science|Machine Learning|Statistics|Engineering|Mathematics)",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            degrees.append(re.sub(r"\s+", " ", match).strip())
    return degrees[:3]
