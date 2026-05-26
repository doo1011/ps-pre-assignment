from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://excel_user:excel_pass@db:5432/excel_db"
    excel_output_dir: str = "/app/excel_files"
    max_concurrent_jobs: int = 1

    model_config = {"env_file": ".env"}


settings = Settings()
