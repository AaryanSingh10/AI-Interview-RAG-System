from app.models.schemas import RoleInfo

ROLES: dict[str, RoleInfo] = {
    "ml_engineer": RoleInfo(
        id="ml_engineer",
        title="Machine Learning Engineer",
        description="Builds and deploys ML models, pipelines, and production systems.",
        topics=[
            "Supervised Learning",
            "Model Evaluation",
            "Feature Engineering",
            "Ensemble Methods",
            "MLOps Basics",
            "Regularization",
        ],
    ),
    "data_scientist": RoleInfo(
        id="data_scientist",
        title="Data Scientist",
        description="Analyzes data, builds models, and communicates insights to stakeholders.",
        topics=[
            "Exploratory Data Analysis",
            "Statistical Inference",
            "Classification",
            "Clustering",
            "Model Interpretability",
            "Experiment Design",
        ],
    ),
    "ml_researcher": RoleInfo(
        id="ml_researcher",
        title="ML Researcher",
        description="Develops novel algorithms and advances theoretical ML understanding.",
        topics=[
            "Learning Theory",
            "Optimization",
            "Neural Networks",
            "Probabilistic Models",
            "Generalization",
            "Research Methodology",
        ],
    ),
    "ai_engineer": RoleInfo(
        id="ai_engineer",
        title="AI Engineer",
        description="Integrates AI/LLM capabilities into products and scalable applications.",
        topics=[
            "NLP Fundamentals",
            "Embeddings & Retrieval",
            "Prompt Engineering",
            "Model Serving",
            "RAG Systems",
            "Evaluation Metrics",
        ],
    ),
}


def get_role(role_id: str) -> RoleInfo | None:
    return ROLES.get(role_id)


def list_roles() -> list[RoleInfo]:
    return list(ROLES.values())
