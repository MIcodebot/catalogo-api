import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Configurações lidas de variáveis de ambiente."""

    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./catalogo.db")
    )
    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "dev-apenas-troque-esta-chave-em-producao")
    )
    token_expire_minutes: int = field(
        default_factory=lambda: int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
    )
    admin_email: str | None = field(default_factory=lambda: os.getenv("ADMIN_EMAIL"))
    admin_password: str | None = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD"))


settings = Settings()
