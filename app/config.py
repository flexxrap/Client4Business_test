import os


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL", "sqlite:///./approval_service.db"
        )


settings = Settings()
